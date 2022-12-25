import asyncio
import csv
import os
import re
from typing import Optional

from al_utils.console import ColoredConsole
from al_utils.logger import Logger

from conf import *
from download.asynchttp import AsyncHTTP
from download.resume import Resume
from m3u8_util.m3u8 import download

FILE: str = os.path.join(DATA_DIR, "index.csv")

logger = Logger(__file__).logger


async def get_m3u8_url(url: str, headers: dict[str, str] = {}):
    """
    get m3u8 link from url page.

    :param url: page url.
    """
    def parse_link(html: str) -> Optional[str]:
        p = re.compile(r'var player_aaaa=.*?"url":"(.*?)",', re.S)
        links: list[str] = p.findall(html)
        if links:
            link = links[0].replace('\\', '')
            return link

    return await AsyncHTTP().async_get(0, asyncio.Semaphore(1), url, lambda _, __, t: parse_link(t), headers)


async def main():
    BASE_URL = "https://91md.me"

    async def callback(link: str, name: str):
        try:
            url = await get_m3u8_url(link)
            if not url:
                raise ValueError(f"cannot get m3u8 url from {link}")
            fn: str = str(await download(url, name, M3U8_FILE_DIR, TMP_DIR, M3U8_VIDEO_DIR, HEADERS, MODE))
            logger.info(
                f'download video {name} successfully to {fn} from {url}')
            ColoredConsole.success(
                f"Download successfully of {name} to {fn} from {link}")
            return True
        except:
            ColoredConsole.error(f"Download failed of {name} from {link}.")
            raise
    with open(FILE, "r", newline="", encoding="utf-8") as f:
        rows = csv.reader(f)
        next(rows)
        async with Resume() as resume:
            for name, _, link in rows:
                link = f"{BASE_URL}{link}"
                await resume.run(link, lambda _: callback(link, name))

if __name__ == "__main__":
    m = main()
    try:
        asyncio.run(m)
    except KeyboardInterrupt:
        m.close()
        logger.info("Stopped by user")
        ColoredConsole.warn('Stopped by user.')
