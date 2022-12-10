import asyncio
import os

from download.asynchttp import AsyncHTTP
from tqdm import tqdm

import m3u8

from download.logger import CFLogger


class M3U8:
    """
    Download each segments of m3u8 file and combine theme as Transport Stream(MPEG2-TS)
    """

    def __init__(self, m3u8_filename: str, m3u8_url: str = '',  tmp_dir: str = 'tmp', log='./log', *args, **kwargs) -> None:
        """
        Create a :class:`M3U8` instance to download m3u8.

        :param m3u8_filename: m3u8 file name which will be download to ts.
        :param m3u8_url: If not empty, will download it to :param:``meu8_filename``.
        :param tmp_dir: Directory to save segments.
        :param log: Directory to save logs.
        """
        if not os.path.exists(tmp_dir):
            os.mkdir(tmp_dir)
        self.asynchttp = AsyncHTTP(*args, **kwargs)
        self.tmp_dir = tmp_dir
        self.m3u8_filename = m3u8_filename
        self.m3u8_url = m3u8_url
        self.logger = CFLogger(
            'm3u8', '%(asctime)s:%(message)s', log_dir=log).logger
        asyncio.run(self.download_m3u8())

    async def download_m3u8(self):
        if self.m3u8_url:
            AsyncHTTP().async_download(0, 1, self.m3u8_url, self.m3u8_filename)

    async def download_segs(self, base_url: str):
        """
        download m3u8 segment videos with :param:`base_url` to `self.tmp_dir`
        """
        playlist = m3u8.load(self.m3u8_filename)
        urls = [f'{base_url}{seg}' for seg in playlist.files]
        fns = [f'{os.path.join(self.tmp_dir,seg)}' for seg in playlist.files]
        await self.asynchttp.async_downloads(4, urls, fns)

    def combine_segs(self, output: str) -> str:
        """
        combine m3u8 segment videos from :param:`segs_folder` to :param:`output`
        """
        playlist = m3u8.load(self.m3u8_filename)
        # file name too long exception, linux supported file name length is 255 bytes, but encoding utf-8 char is 1~4 bytes
        if len(output.encode()) >= 200:
            self.logger.info(f'filename too long to cut.')
        f, e = os.path.splitext(os.path.basename(output))
        d = os.path.dirname(output)
        o = os.path.join(d, f[:200//3-len(e)-1]+e)  # utf-8 has 1~3 bytes
        self.logger.info(f"Save as {o} from {output}")
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
    async def download(m3u8_filename: str, base_url: str, output: str, m3u8_url: str = '', tmp_dir: str = 'tmp', *args, **kwargs):
        """
        download m3u8 file to :param:``output``.

        :param m3u8_filename: Path of m3u8 file.
        :base_url: Base URL of each segment in m3u8 file.
        :output: Path to save video.
        :param m3u8_url: If not empty, will download it to :param:``meu8_filename``.
        :tmp_dir: Temperate direcctory to save segments.
        :param *args *kwargs: Extra arguments to init :class:`M3U8`.
        """
        md = M3U8(m3u8_filename, tmp_dir, *args, **kwargs)
        await md.download_segs(base_url)
        return md.combine_segs(output)
