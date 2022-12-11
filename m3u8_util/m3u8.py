import asyncio
import os
import re
import subprocess
from typing import Literal

from al_utils.async_util import async_wrap
from al_utils.logger import Logger
from tqdm import tqdm

import m3u8
from download.asynchttp import AsyncHTTP

logger = Logger(__file__).logger


async def download(url: str, name: str, m3u8_dir="./m3u8", tmp_dir="./tmp", videos_dir: str = "./videos", headers: dict[str, str] = {}, mode: Literal['aio', 'ff'] = 'aio'):
    """
    download m3u8 video from url path.

    :param url: page url.
    :param name: video name.
    :param m3u8_dir: directory to save m3u8 files.
    :param tmp_dir: directory to save segments.
    :param videos_dir: directory to save output videos.
    :param mode: download mode.
    """
    [AioM3U8.check_dir(d) for d in [m3u8_dir, tmp_dir, videos_dir]]
    if not url:
        raise ValueError(f"m3u8 url must be set.")
    m3u8_fn = os.path.join(m3u8_dir, name+".m3u8")
    output_fn = os.path.join(videos_dir, name+".ts")
    if mode == 'aio':
        base_url = re.findall(r'(h.*/).*m3u8', url)[0]
        return await AioM3U8.download(m3u8_fn, base_url, output_fn, url, tmp_dir, headers)
    elif mode == 'ff':
        return async_wrap(FFM3U8.download(url, output_fn))


class FFM3U8:
    """
    Download m3u8 video via ffmpeg

    ### NOTICE:
    * Make sure ffmpeg can be invoke in command line.
    """

    @staticmethod
    def download(url: str, output: str, headers: dict[str, str] = {},override:bool=True, *options:str):
        """
        download m3u8 url to :param:`output`

        :param url: m3u8 file url.
        :param output: saved video file name.
        :param override: Determine whether override :param:`output` if exists.
        :param options: extra arguments when invoke ffmpeg.
        """
        if not url or not url.strip() or not url.lower().startswith('http'):
            raise ValueError("url must starts with http or https.")
        if not output:
            raise ValueError("please specified a output file name.")
        h: str = ''
        if headers:
            h = "\\r\\n".join([f"{k}:{v}" for k, v in headers.items()])
            options = (*options, '-headers', h)
        if override:
            options = (*options, '-y')
        else:
            options = (*options, '-n')
        command = f"ffmpeg -i {url} -c copy {' '.join(options)} {output}"
        logger.debug(command)
        with subprocess.Popen(command) as p:
            pass
        if p.returncode != 0:
            raise RuntimeError(f"Occurred return code {p.returncode} of {url}")
        return output


class AioM3U8:
    """
    Download m3u8 video via aiohttp
    """

    def __init__(self, m3u8_filename: str,  tmp_dir: str = 'tmp', headers: dict[str, str] = {}, *args, **kwargs) -> None:
        """
        Create a :class:`M3U8` instance to download m3u8.

        :param m3u8_filename: m3u8 file name which will be download to ts.
        :param m3u8_url: If not empty, will download it to :param:``meu8_filename``.
        :param tmp_dir: Directory to save segments.
        :param log: Directory to save logs.
        """
        self.check_dir(tmp_dir)
        self.asynchttp = AsyncHTTP(*args, **kwargs)
        self.tmp_dir = tmp_dir
        self.headers = headers
        self.m3u8_filename = m3u8_filename

    async def download_m3u8(self, url: str):
        await AsyncHTTP().async_download(0, asyncio.Semaphore(1), url, self.m3u8_filename, self.headers)

    async def download_segs(self, base_url: str):
        """
        download m3u8 segment videos with :param:`base_url` to `self.tmp_dir`
        """
        playlist = m3u8.load(self.m3u8_filename)
        urls = [f'{base_url}{seg}' for seg in playlist.files]
        fns = [f'{os.path.join(self.tmp_dir,seg)}' for seg in playlist.files]
        await self.asynchttp.async_downloads(4, urls, fns, self.headers)

    def combine_segs(self, output: str) -> str:
        """
        combine m3u8 segment videos from :param:`segs_folder` to :param:`output`
        """
        playlist = m3u8.load(self.m3u8_filename)
        # file name too long exception, linux supported file name length is 255 bytes, but encoding utf-8 char is 1~4 bytes
        if len(output.encode()) >= 200:
            logger.info(f'filename too long to cut.')
        f, e = os.path.splitext(os.path.basename(output))
        d = os.path.dirname(output)
        o = os.path.join(d, f[:200//3-len(e)-1]+e)  # utf-8 has 1~3 bytes
        logger.info(f"Save as {o} from {output}")
        with open(o, 'wb') as video:
            with tqdm(playlist.files) as bar:
                for seg in bar:
                    bar.set_description(f"Combining {seg}")
                    segpath = os.path.join(self.tmp_dir, seg)
                    with open(segpath, 'rb') as temp:
                        content = temp.read()
                        video.write(content)
                    os.remove(segpath)
        return o

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
        return md.combine_segs(output_fn)

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
