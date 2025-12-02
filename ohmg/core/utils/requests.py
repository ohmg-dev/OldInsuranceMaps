import json
import logging
import shutil
import time
from json.decoder import JSONDecodeError
from pathlib import Path

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def download_image(url: str, out_path: Path, retries: int = 3, use_cache: bool = True):
    if out_path.is_file() and use_cache:
        print(f"using cached file: {out_path}")
        return out_path

    # basic download code: https://stackoverflow.com/a/18043472/3873885
    while True:
        logger.debug(f"request {url}")
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(out_path, "wb") as out_file:
                shutil.copyfileobj(response.raw, out_file)
            return out_path
        else:
            logger.warning(f"response code: {response.status_code} retries left: {retries}")
            time.sleep(5)
            retries -= 1
            if retries == 0:
                logger.warning("request failed, cancelling")
                return None


class CacheableRequest:
    def __init__(
        self, url: str, cache_subdir: str = "requests", verbose: bool = False, delay: int = 0
    ):
        self.url: str = url
        self.cache_dir: Path = settings.CACHE_DIR / cache_subdir
        self.cache_path: Path = self.cache_dir / self.url.replace("/", "__")
        self.verbose: bool = verbose
        self.delay: int = delay

        self.cache_dir.mkdir(exist_ok=True)

    def get_response(self):
        try:
            if self.verbose and self.delay > 0:
                logger.info(f"waiting {self.delay} seconds before making a request...")
            time.sleep(self.delay)
            logger.info("making request...")
            response = requests.get(self.url)
            if response.status_code in [500, 503]:
                msg = f"{response.status_code} error, retrying in 5 seconds..."
                logger.warning(msg)
                if self.verbose:
                    print(msg)
                time.sleep(5)
                if self.verbose:
                    print("making request")
                response = requests.get(self.url)
            return response
        except (
            ConnectionError,
            ConnectionRefusedError,
            ConnectionAbortedError,
            ConnectionResetError,
        ) as e:
            msg = f"Request error: {e}"
            print(msg)
            logger.warning(e)
            return

    def get_content(self, use_cache=True) -> str:
        ## run the request if necessary
        if not use_cache or not self.cache_path.is_file():
            response = self.get_response()
            if not response:
                return
            content = response.content.decode("utf-8")
            ## ideally this would be async so the response can be returned
            ## without having to wait for the file cache to be written
            with open(self.cache_path, "w") as o:
                o.write(content)
            return content
        else:
            with open(self.cache_path, "r") as o:
                return o.read()

    def get_json_content(self, use_cache=True) -> dict:
        ## run the request if necessary
        if not use_cache or not self.cache_path.is_file():
            response = self.get_response()
            if not response:
                return
            try:
                content = json.loads(response.content)
            except JSONDecodeError:
                msg = f"Can't decode this JSON: {content}"
                print(msg)
                logger.warning(msg)
                return

            ## ONLY SAVE TO CACHE AFTER JSON IS SUCCESSFULLY PARSED.
            ## also, ideally this would be async so the response can be returned
            ## without having to wait for the file cache to be written
            with open(self.cache_path, "w") as o:
                json.dump(content, o, indent=2)
            return content
        ## otherwise load content from file
        else:
            with open(self.cache_path, "r") as o:
                return json.load(o)
