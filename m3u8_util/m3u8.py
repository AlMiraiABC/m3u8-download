import asyncio
import os
import re
import subprocess
from typing import Literal

import m3u8
from al_utils.async_util import async_wrap
from al_utils.logger import Logger
from tqdm import tqdm

from download.asynchttp import AsyncHTTP
from download.util import format_fn

logger = Logger(__file__).logger


async def download(url: str, name: str, m3u8_dir="./m3u8", tmp_dir="./tmp", videos_dir: str = "./videos", headers: dict[str, str] = {}, mode: Literal['aio', 'ff'] = 'aio', override: bool = True, retry: int = 3):
    """
    download m3u8 video from url path.

    :param url: page url.
    :param name: video name.
    :param m3u8_dir: directory to save m3u8 files.
    :param tmp_dir: directory to save segments.
    :param videos_dir: directory to save output videos.
    :param mode: download mode.
    :param override: determine whether re-download if file has exists.
    :param retry: retry times when network error.
    :return: First item is saved filename. Second item is whether download(True: download, False: skip)
    """
    [AioM3U8.check_dir(d) for d in [m3u8_dir, tmp_dir, videos_dir]]
    if not url:
        raise ValueError(f"m3u8 url must be set.")
    m3u8_fn = os.path.join(m3u8_dir, name+".m3u8")
    m3u8_fn = format_fn(m3u8_fn)
    output_fn = os.path.join(videos_dir, name+".ts")
    if os.path.exists(output_fn) and not override:
        logger.info(f'Skip download {name} from {url} because {output_fn} exists and not override.')
        return output_fn, False
    if mode == 'aio':
        base_url = re.findall(r'(h.*/).*m3u8', url)[0]
        await AioM3U8.download(m3u8_fn, base_url, output_fn, url, tmp_dir, headers, retry=retry)
    elif mode == 'ff':
        async_wrap(FFM3U8.download(url, output_fn, headers, True, retry))
    return output_fn, True


class FFM3U8:
    """
    Download m3u8 video via ffmpeg

    ### NOTICE:
    * Make sure ffmpeg can be invoke in command line.
    """

    @staticmethod
    def download(url: str, output: str, headers: dict[str, str] = {}, override: bool = True, retry: int = 3, *options: str):
        """
        download m3u8 url to :param:`output`

        :param url: m3u8 file url.
        :param output: saved video file name.
        :param override: Determine whether override :param:`output` if exists.
        :param retry: Retry times.
        :param options: extra arguments when invoke ffmpeg.
        """
        if not url or not url.strip() or not url.lower().startswith('http'):
            raise ValueError("url must starts with http or https.")
        if not output:
            raise ValueError("please specified a output file name.")
        if headers:
            h = "\\r\\n".join([f"{k}:{v}" for k, v in headers.items()])
            options = (*options, '-headers', h)
        if override:
            options = (*options, '-y')
        else:
            options = (*options, '-n')
        for i in range(retry):
            command = f"ffmpeg -i {url} -c copy {' '.join(options)} {output}"
            logger.debug(command)
            with subprocess.Popen(command) as p:
                pass
            if p.returncode != 0:
                logger.error(f'{url}, {i}, {p.returncode}')
                continue
            logger.info(f'{url}, {p.returncode}')
            return output
        raise IOError(f'Download failed {url} in {retry} retries')


class AioM3U8:
    """
    Download m3u8 video via aiohttp
    """

    def __init__(self, m3u8_filename: str,  tmp_dir: str = 'tmp', headers: dict[str, str] = {}, retry: int = 3) -> None:
        """
        Create a :class:`M3U8` instance to download m3u8.

        :param m3u8_filename: m3u8 file name which will be download to ts.
        :param m3u8_url: If not empty, will download it to :param:``meu8_filename``.
        :param tmp_dir: Directory to save segments.
        :param headers: Request headers.
        :param retry: Retry times.
        """
        self.check_dir(tmp_dir)
        self.asynchttp = AsyncHTTP()
        self.tmp_dir = tmp_dir
        self.headers = headers
        self.m3u8_filename = m3u8_filename
        self.retry = retry if retry or retry > 0 else 3

    async def download_m3u8(self, url: str):
        await self.asynchttp.async_download(0, asyncio.Semaphore(1), url, self.m3u8_filename, self.headers, retry=self.retry)

    async def download_segs(self, base_url: str):
        """
        download m3u8 segment videos with :param:`base_url` to `self.tmp_dir`
        """
        playlist = m3u8.load(self.m3u8_filename)
        urls = [f'{base_url}{seg}' for seg in playlist.files]
        fns = [f'{os.path.join(self.tmp_dir,seg)}' for seg in playlist.files]
        await self.asynchttp.async_downloads(4, urls, fns, self.headers, retry=self.retry)

    def combine_segs(self, output: str):
        """
        combine m3u8 segment videos from :param:`segs_folder` to :param:`output`
        """
        playlist = m3u8.load(self.m3u8_filename)
        with open(output, 'wb') as video:
            with tqdm(playlist.files) as bar:
                for seg in bar:
                    bar.set_description(f"Combining {seg}")
                    segpath = os.path.join(self.tmp_dir, seg)
                    with open(segpath, 'rb') as temp:
                        content = temp.read()
                        video.write(content)
                    os.remove(segpath)

    @staticmethod
    async def download(m3u8_fn: str, base_url: str, output_fn: str, m3u8_url: str = '', tmp_dir: str = 'tmp', headers: dict[str, str] = {}, *args, **kwargs):
        """
        download m3u8 file to :param:``output``.

        :param m3u8_fn: File path of m3u8 file.
        :base_url: Base URL of each segment in m3u8 file.
        :output_fn: File path to save video file.
        :param m3u8_url: If not empty, will download it to :param:``m3u8_fn``.
        :tmp_dir: Temperate direcctory to save segments.
        :param *args *kwargs: Extra arguments to init :class:`M3U8`.
        """
        AioM3U8.check_dir(tmp_dir)
        md = AioM3U8(m3u8_fn, tmp_dir, headers, *args, **kwargs)
        if m3u8_url:
            AioM3U8.check_dir(os.path.dirname(m3u8_fn))
            await md.download_m3u8(m3u8_url)
            logger.info(
                f"successfully download m3u8 file {m3u8_fn} from {m3u8_url}.")
        await md.download_segs(base_url)
        md.combine_segs(output_fn)

    @staticmethod
    def check_dir(dir: str, create: bool = True, throw: bool = True) -> bool:
        if os.path.exists(dir) and not os.path.isdir(dir):
            if throw:
                raise IOError(f"{dir} is not a directory.")
            return False
        if create:
            if not os.path.exists(dir):
                os.makedirs(dir)
                logger.warn(f"{dir} not exist, create it.")
            return True
        return True
