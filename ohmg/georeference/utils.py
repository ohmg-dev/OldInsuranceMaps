import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Union

import morecantile
from django.conf import settings
from rio_tiler.io import Reader

from ohmg.core.utils import get_boto3_s3_client

logger = logging.getLogger(__name__)


def make_xyz_tiles(
    data_source: Union[str | Path],
    prefix: Union[str | Path],
    min_zoom: int = 13,
    max_zoom: int = 20,
):
    start = datetime.now()

    tms = morecantile.tms.get("WebMercatorQuad")

    logger.info(f"creating new tileset {prefix}")

    progress_pct = {
        10: False,
        20: False,
        30: False,
        40: False,
        50: False,
        60: False,
        70: False,
        80: False,
        90: False,
    }

    if settings.ENABLE_S3_STORAGE:
        s3 = get_boto3_s3_client()

    with Reader(data_source) as src:
        zooms = range(min_zoom, max_zoom + 1)
        bounds = src.geographic_bounds
        tiles_total_ct = sum(1 for i in tms.tiles(*bounds, zooms=zooms))
        tiles_written_ct = 0
        for coords in tms.tiles(*bounds, zooms=zooms):
            tile = src.tile(coords.x, coords.y, coords.z)
            ## only make a tile if there is valid data (skip empty tiles)
            if tile.data_as_image().any():
                rendered_bytes = tile.render()
                if settings.ENABLE_S3_STORAGE:
                    key = f"{prefix}/{coords.z}/{coords.x}/{coords.y}.png"
                    file_like = io.BytesIO(rendered_bytes)
                    s3.upload_fileobj(
                        file_like,
                        settings.AWS_STORAGE_BUCKET_NAME,
                        key,
                    )
                else:
                    out_root = Path(settings.MEDIA_ROOT, prefix)
                    out_dir = Path(out_root, str(coords.z), str(coords.x))
                    out_dir.mkdir(parents=True, exist_ok=True)
                    file_path = Path(out_dir, f"{coords.y}.png")
                    with open(file_path, "wb") as file:
                        file.write(rendered_bytes)
            ## progress logging
            tiles_written_ct += 1
            pct = int((tiles_written_ct / tiles_total_ct) * 100)
            for k in progress_pct.keys():
                if pct > k and not progress_pct[k]:
                    logger.debug(f"{prefix} {k}% written")
                    progress_pct[k] = True

    logger.info(f"{prefix} completed, elapsed time: {datetime.now() - start}")

    return prefix
