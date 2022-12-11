import asyncio
import os
import re
from typing import Literal, Optional

from al_utils.async_util import async_wrap
from al_utils.console import ColoredConsole
from al_utils.logger import Logger

from download.asynchttp import AsyncHTTP
from m3u8_util.m3u8 import FFM3U8, AioM3U8

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


async def download(url: str, name: str, m3u8_dir="./m3u8", tmp_dir="./tmp", videos_dir: str = "./videos", headers: dict[str, str] = {}, mode: Literal['aio', 'ff'] = 'aio'):
    """
    download m3u8 video from url path.

    :param url: page url.
    :param name: video name.
    :param mode: download mode.
    """
    [AioM3U8.check_dir(d) for d in [m3u8_dir, tmp_dir, videos_dir]]
    link = await get_m3u8_url(url)
    if not link:
        logger.error(f"cannot get m3u8 link from {url}.")
        raise RuntimeError(f"cannot get m3u8 link from {url}.")
    m3u8_fn = os.path.join(m3u8_dir, name+".m3u8")
    output_fn = os.path.join(videos_dir, name+".ts")
    if mode == 'aio':
        base_url = re.findall(r'(h.*?/)index.m3u8', link, re.S)[0]
        return await AioM3U8.download(m3u8_fn, base_url, output_fn, link, tmp_dir, headers)
    elif mode == 'ff':
        return async_wrap(FFM3U8.download(link, output_fn))

if __name__ == "__main__":
    url = "https://91md.me/index.php/vod/play/id/6366/sid/1/nid/1.html"
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.42"
    }
    ColoredConsole.info(f"Start downloading video {url}")
    fn = asyncio.run(download(url, "TESTVIDEO"))
    ColoredConsole.success(f"Downloaded video {fn} from {url}.")
