import io
import logging
import os
import shutil
import tarfile
from datetime import datetime
from multiprocessing import Pool
from pathlib import Path
from typing import Union

import morecantile
from django.conf import settings
from rio_tiler.io import Reader

from ohmg.core.utils.s3 import (
    get_boto3_s3_client,
    upload_directory_to_bucket,
    upload_file_to_bucket,
)

logger = logging.getLogger(__name__)

TMS = morecantile.tms.get("WebMercatorQuad")


def extract_tile_for_multiprocessing(info):
    """This is a standalone function to be called within a multiprocessing iteration,
    and should only be used in that context. It needs to re-instantiate the Reader
    object, and also needs to recreate the s3 client. This is inefficient..."""

    src_url = info.get("src_url")
    tile_coords = info.get("tile_coords")
    prefix = info.get("prefix")

    with Reader(src_url) as src:
        tile = src.tile(tile_coords.x, tile_coords.y, tile_coords.z)

        ## only make a tile if there is valid data (skip empty tiles)
        if tile.data_as_image().any():
            rendered_bytes = tile.render()
            if settings.ENABLE_S3_STORAGE:
                s3 = get_boto3_s3_client()
                key = f"{prefix}/{tile_coords.z}/{tile_coords.x}/{tile_coords.y}.png"
                file_like = io.BytesIO(rendered_bytes)
                s3.upload_fileobj(
                    file_like,
                    settings.AWS_STORAGE_BUCKET_NAME,
                    key,
                )
            else:
                out_root = Path(settings.MEDIA_ROOT, prefix)
                out_dir = Path(out_root, str(tile_coords.z), str(tile_coords.x))
                out_dir.mkdir(parents=True, exist_ok=True)
                file_path = Path(out_dir, f"{tile_coords.y}.png")
                with open(file_path, "wb") as file:
                    file.write(rendered_bytes)


def make_xyz_tiles_with_multiprocessing(
    data_source: Union[str | Path],
    prefix: Union[str | Path],
    min_zoom: int = 13,
    max_zoom: int = 20,
):
    raise NotImplementedError("Tileset generation with multiprocessing is not fully implemented")
    start = datetime.now()

    logger.info(f"creating new tileset with multiprocessing {prefix}")

    with Reader(data_source) as src:
        zooms = range(min_zoom, max_zoom + 1)
        bounds = src.geographic_bounds
        tile_info_list = [
            {
                "src_url": data_source,
                "tile_coords": i,
                "prefix": prefix,
            }
            for i in TMS.tiles(*bounds, zooms=zooms)
        ]
        tiles_total_ct = len(tile_info_list)
        logger.info(f"{tiles_total_ct} tile coordinate sets")
        process_ct = os.cpu_count()
        logger.info(f"generating tiles using {process_ct} parallel processes")
        with Pool(process_ct) as p:
            p.map(extract_tile_for_multiprocessing, tile_info_list)

    logger.info(f"{prefix} completed, elapsed time: {datetime.now() - start}")


def make_xyz_tiles(
    data_source: Union[str | Path],
    prefix: Union[str | Path],
    min_zoom: int = 13,
    max_zoom: int = 20,
):
    start = datetime.now()
    logger.info(f"creating new tileset {prefix} from {data_source}")

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

    tmp_tileset_root = Path(settings.TEMP_DIR, prefix)
    with Reader(data_source) as src:
        zooms = range(min_zoom, max_zoom + 1)
        bounds = src.geographic_bounds
        tile_coords = list(TMS.tiles(*bounds, zooms=zooms))
        tiles_total_ct = len(tile_coords)
        logger.info(f"{tiles_total_ct} tile coordinate sets")
        tiles_written_ct = 0
        for coords in TMS.tiles(*bounds, zooms=zooms):
            tile = src.tile(coords.x, coords.y, coords.z)
            ## only make a tile if there is valid data (skip empty tiles)
            if tile.data_as_image().any():
                rendered_bytes = tile.render()
                out_dir = Path(tmp_tileset_root, str(coords.z), str(coords.x))
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

    logger.info(f"tileset {prefix} created, elapsed time: {datetime.now() - start}")

    start2 = datetime.now()
    logger.info(f"creating gzip archive for tileset {prefix}")

    tmp_gz_path = Path(tmp_tileset_root.parent, "archive.tar.gz")
    print(tmp_gz_path)
    print(tmp_tileset_root.name)
    with tarfile.open(tmp_gz_path, "w:gz") as tar:
        tar.add(tmp_tileset_root, arcname=tmp_tileset_root.name)
    logger.info(f"gzip {tmp_gz_path.name} created, elapsed time: {datetime.now() - start2}")

    logger.debug("copying tileset to final location")

    if settings.ENABLE_S3_STORAGE:
        s3 = get_boto3_s3_client()
        upload_directory_to_bucket(tmp_tileset_root, prefix, client=s3)
        # place the archive file within the top-level of the tileset itself,
        # alongside the z-level folders
        upload_file_to_bucket(tmp_gz_path, f"{prefix}/{tmp_gz_path.name}", client=s3)
    else:
        local_media_dest = Path(settings.MEDIA_ROOT, prefix)
        # local_media_dest.parent.mkdir(exist_ok=True, parents=True)
        shutil.copytree(tmp_tileset_root, local_media_dest, dirs_exist_ok=True)
        shutil.copyfile(tmp_gz_path, Path(local_media_dest, tmp_gz_path.name))

    os.remove(tmp_gz_path)
    shutil.rmtree(tmp_tileset_root)

    return prefix
