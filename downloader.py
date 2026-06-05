import os
import logging
import threading
from typing import Callable
from urllib.request import urlopen

logger = logging.getLogger(__name__)

cache_dir = os.path.join(os.path.dirname(__file__), ".cache")
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)


def download(url: str, callback: Callable[[bytes | Exception], None]):
    '''Downloads file in background and calls a callback when done.
       Also caches files in the '.cache' directory.'''

    def _download():
        filename = os.path.join(cache_dir, os.path.basename(url))
        if not os.path.exists(filename):
            logger.info(f"Downloading {url} to {filename}")
            try:
                with urlopen(url) as response, open(filename, "wb") as out_file:
                    data = response.read()
                    out_file.write(data)
                    logger.debug(f"Downloaded {url} ({len(data)} bytes)")
            except Exception as e:
                logger.warning(f"Failed to download {url}: {e}")
                callback(e)
                return
        else:
            logger.debug(f"Using cached file for {url} at {filename}")
            try:
                with open(filename, "rb") as f:
                    data = f.read()
            except Exception as e:
                callback(e)
                return
        callback(data)

    threading.Thread(target=_download).start()
