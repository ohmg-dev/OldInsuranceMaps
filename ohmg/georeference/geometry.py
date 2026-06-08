import math
from typing import Tuple

from django.contrib.gis.geos import LineString


def angle_from_coords(pt1: Tuple[float, float], pt2: Tuple[float, float]) -> float:
    """
    Calculates the absolute Cartesian angle (in degrees) of the vector
    pointing from p1 to p2, relative to the positive Y-axis.
    """

    # Calculate differences
    dx = pt2[0] - pt1[0]
    dy = pt2[1] - pt1[1]

    # Calculate angle in radians (-pi to pi)
    radians = math.atan2(dx, dy)

    degrees = math.degrees(radians)

    return degrees


def extend_vector(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    distance: float,
) -> Tuple[float, float]:
    """https://math.stackexchange.com/a/3346108 (credit to Oliver Roche)
    takes the two input points, which represent a vector, and creates a
    third point that would extend that vector by the given distance."""

    x1, y1 = p1
    x2, y2 = p2
    rise = y2 - y1
    run = x2 - x1

    norm = math.sqrt((run**2) + (rise**2))

    # if negative coords are used norm will be 0.0, silently return original point
    if norm == 0.0:
        return (x2, y2)

    x3 = x2 + distance * (run / norm)
    y3 = y2 + distance * (rise / norm)

    return (x3, y3)


def extend_linestring(linestring: LineString, distance: int = 10) -> LineString:
    """takes the input GEOS LineString and extends it in both directions
    (following the trajectory of each end segment) by the given distance."""

    coord_list = list(linestring.coords)

    new_start = extend_vector(coord_list[1], coord_list[0], distance)
    new_end = extend_vector(coord_list[-2], coord_list[-1], distance)

    coord_list.insert(0, new_start)
    coord_list.append(new_end)

    return LineString(coord_list)
