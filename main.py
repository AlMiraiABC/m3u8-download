import asyncio
import re
from typing import Optional

from al_utils.console import ColoredConsole
from al_utils.logger import Logger

from download.asynchttp import AsyncHTTP
from m3u8_util.m3u8 import download

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

if __name__ == "__main__":
    url = "https://91md.me/index.php/vod/play/id/6366/sid/1/nid/1.html"
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.42"
    }
    ColoredConsole.info(f"Start downloading video {url}")
    fn = asyncio.run(download(url, "TESTVIDEO", mode='ff'))
    ColoredConsole.success(f"Downloaded video {fn} from {url}.")
