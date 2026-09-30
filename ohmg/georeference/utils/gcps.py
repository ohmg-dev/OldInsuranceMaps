import math
from dataclasses import dataclass

import numpy as np
from osgeo import gdal

TRANSFORMATION_LOOKUP = {
    "helmert": {
        "id": "helmert",
        "gdal_code": None,
        "name": "Helmert",
        "desc": "implemented as four-parameter transformation",
    },
    "tps": {
        "id": "tps",
        "gdal_code": -1,
        "name": "Thin Plate Spline",
        "desc": "max distortion",
    },
    "poly": {
        "id": "poly",
        "gdal_code": 0,
        "name": "Highest Possible Polynomial",
        "desc": "uses highest possible polynomial order based on GCP count",
    },
    "poly1": {
        "id": "poly1",
        "gdal_code": 1,
        "name": "Polynomial 1",
        "desc": "uses polynomial 1",
    },
    "poly2": {
        "id": "poly2",
        "gdal_code": 2,
        "name": "Polynomial 2",
        "desc": "uses polynomial 2, requires 6 GCPs",
    },
    "poly3": {
        "id": "poly3",
        "gdal_code": 3,
        "name": "Polynomial 3",
        "desc": "uses polynomial 3, requires 10 GCPs (not recommended in GDAL docs)",
    },
}


@dataclass
class HelmertParams:
    """The four parameters of a Helmert (similarity) transformation that maps
    image pixel/line coordinates to geographic coordinates."""

    scale: float
    # rotation in degrees, measured as an azimuth from north (the positive Y axis)
    rotation: float
    # geographic coordinates that the image origin (pixel=0, line=0) maps to
    offset_x: float
    offset_y: float


def build_helmert_matrices(gcp_list: list[gdal.GCP]) -> tuple[np.array, np.array]:
    """Builds interleaved 'a' (2M, 4) and 'b' (2M,) matrices for a Rigid/Similarity transformation."""
    sources, targets = [], []
    for gcp in gcp_list:
        sources.append([gcp.GCPLine, -gcp.GCPPixel, 1, 0])
        targets.append(gcp.GCPX)
        sources.append([gcp.GCPPixel, gcp.GCPLine, 0, 1])
        targets.append(gcp.GCPY)
    return np.array(sources, dtype=float), np.array(targets, dtype=float)


def calculate_helmert_rmse(gcp_list: list[gdal.GCP]) -> float:
    sources, targets = build_helmert_matrices(gcp_list)

    x, *_ = np.linalg.lstsq(sources, targets, rcond=None)

    predictions = sources @ x
    rmse = np.sqrt(np.mean((targets - predictions) ** 2))

    def flat_list_to_pairs(flat_list: list) -> list[tuple[object, object]]:
        iterator = iter(flat_list)
        return list(zip(iterator, iterator))

    pred_coords = flat_list_to_pairs(predictions.tolist())
    target_coords = flat_list_to_pairs(targets.tolist())

    lines = list(zip(pred_coords, target_coords))

    return round(rmse, 5), pred_coords, lines


def get_helmert_params(gcp_list: list[gdal.GCP]) -> HelmertParams:
    """Fit a Helmert (four-parameter similarity) transformation to the GCPs
    using least squares, returning the scale, rotation, and offsets.

    The transformation maps image pixel/line coordinates to geographic
    coordinates as:

        geoX = offset_x + a * line - b * pixel
        geoY = offset_y + a * pixel + b * line

    where (a, b) = (scale * cos(angle), scale * sin(angle)). Because this is
    linear in the four unknowns (a, b, offset_x, offset_y), it can be solved
    directly from two equations per GCP -- exactly determined with two GCPs,
    and a best fit with more. This handles every orientation without any
    special-casing.
    """

    if len(gcp_list) < 2:
        raise Exception("At least two GCPs are needed to fit a Helmert transformation")

    # build two rows (the geoX and geoY equations) per GCP
    sources, targets = build_helmert_matrices(gcp_list)

    x, *_ = np.linalg.lstsq(sources, targets, rcond=None)
    scale_cos, scale_sin, offset_x, offset_y = x

    # convert the scale coefficients to a single measure
    scale = math.hypot(scale_cos, scale_sin)
    # convert the fitted angle to an azimuth in degrees from north
    rotation = (270 - math.degrees(math.atan2(scale_sin, scale_cos))) % 360

    return HelmertParams(
        scale=scale,
        rotation=rotation,
        offset_x=offset_x,
        offset_y=offset_y,
    )


def get_helmert_proj_pipeline(
    gcp_list: list[gdal.GCP] | None = None, params: HelmertParams | None = None
) -> str:
    if not params:
        params = get_helmert_params(gcp_list)

    ## convert the rotation to arcseconds for the proj pipeline
    arcseconds = (params.rotation + 90) * 3600

    pipeline = (
        "+proj=pipeline "
        "+step +proj=axisswap +order=2,1 "
        f"+step +proj=helmert +x={params.offset_x} +y={params.offset_y} "
        f"+theta={arcseconds} +s={params.scale}"
    )

    return pipeline


def build_affine_matrices(gcp_list: list[gdal.GCP]) -> tuple[np.array, np.array]:
    """Builds X (M, 3) and Y (M, 2) matrices for an Affine transformation."""
    sources = np.array([[gcp.GCPPixel, gcp.GCPLine, 1.0] for gcp in gcp_list])
    targets = np.array([[gcp.GCPX, gcp.GCPY] for gcp in gcp_list])
    return sources, targets


def calculate_affine_rmse(gcp_list: list[gdal.GCP]):
    """
    Calculates the overall RMSE and coordinate pairings
    using a first-degree Polynomial (Affine) transformation.
    """

    sources, targets = build_affine_matrices(gcp_list)

    x, *_ = np.linalg.lstsq(sources, targets, rcond=None)

    predictions = sources @ x
    rmse = np.sqrt(np.mean((targets - predictions) ** 2))

    pred_coords = [tuple(coord) for coord in predictions.tolist()]
    target_coords = [tuple(coord) for coord in targets.tolist()]

    lines = list(zip(pred_coords, target_coords))

    return round(rmse, 3), pred_coords, lines


def calculate_affine_distortion(gcp_list: list) -> tuple[float, float]:
    """Compute skew (°) and anisotropy from the fitted linear transformation.

    Returns:
        skew_deg: deviation from perpendicular axes (0° = perfectly orthogonal)
        aniso: scale_x / scale_y ratio (1.0 = isotropic scale)
    """
    sources, targets = build_affine_matrices(gcp_list)

    # Solve: sources @ result approx targets
    result, *_ = np.linalg.lstsq(sources, targets, rcond=None)

    # Basis vectors mapping unit step in pixel (x, y) to metric geo displacement
    v_x = result[0, :2]
    v_y = result[1, :2]

    scale_x = float(np.linalg.norm(v_x))
    scale_y = float(np.linalg.norm(v_y))

    if scale_x == 0 or scale_y == 0:
        return 0.0, 1.0

    aniso = scale_x / scale_y

    # Normalized dot product clipped to [-1.0, 1.0] for acos stability
    cos_angle = np.clip(np.dot(v_x, v_y) / (scale_x * scale_y), -1.0, 1.0)

    # Angle between axes minus 90 degrees
    skew_deg = math.degrees(math.acos(float(cos_angle))) - 90.0

    return round(skew_deg, 2), round(aniso, 3)
