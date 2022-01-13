import asyncio
import traceback
from asyncio import Semaphore
from typing import Any, Callable, Dict, Iterable, Tuple, Union

import aiofiles
import aiohttp
from aiohttp.client import ClientTimeout
from tqdm import tqdm

from download.logger import CFLogger
from download.util import human_size


class AsyncHTTP:
    """
    Asynchronous HTTP requests. Wrapper for :module:`aiohttp`
    """

    def __init__(self, log_dir='./log') -> None:
        self.logger_success = CFLogger(
            'success', '%(asctime)s:%(message)s', log_dir=log_dir).logger
        self.logger_error = CFLogger(
            'error', '%(asctime)s:%(message)s', log_dir=log_dir).logger

    async def async_download(self, index: int, semaphore: Semaphore, url: str, file_name: str, headers: Dict[str, str] = None, proxy: str = None):
        async with semaphore:
            async with aiohttp.ClientSession(timeout=ClientTimeout(0)) as client:
                try:
                    response = await client.get(
                        url=url, headers=headers, proxy=proxy)
                    if response.ok:
                        length = int(response.headers.get(
                            'Content-Length', '0'))
                        async with aiofiles.open(file_name, 'wb') as f:
                            with tqdm(total=length) as bar:
                                # 1M
                                async for chunk in response.content.iter_chunked(1024 * 1024):
                                    await f.write(chunk)
                                    bar.update(1024*1024)
                        self.logger_success.info(
                            f'{index}, {url}, {human_size(length)}')
                    else:
                        self.logger_error.error(
                            f'{index}, {url}, {response.status}')
                except Exception:
                    self.logger_error.error(
                        f'{index}, {url}, {traceback.format_exc()}')

    async def async_get(self, index: int, semaphore: Semaphore, url: str, callback: Callable[[int, str, str], Any], headers: Dict[str, str] = None, proxy: str = None):
        """
        Asynchronous get a :param:`url` and write message in loggers. Then invoke :param:`callback` when get response successfully.

        :param index: Specified id for :param:`url`
        :param semaphore: Concurrency controll.
        :param url: Request url
        :param callback: Invoke callback when get response successfully. `(index, url, response) -> Any`
        :param headers: Request headers.
        :param proxy: Request proxy.
        """
        async with semaphore:
            async with aiohttp.ClientSession() as client:
                try:
                    response = await client.get(
                        url=url, headers=headers, proxy=proxy)
                    if response.ok:
                        res = callback(index, url, await response.text())
                        self.logger_success.info(f'{index}, {url}, {res}')
                    else:
                        self.logger_error.error(
                            f'{index}, {url}, {response.status}')
                except Exception:
                    self.logger_error.error(
                        f'{index}, {url}, {traceback.format_exc()}')

    def run(self, sem: int, callback: Callable[[int, str, str], Any], urls: Iterable[str], headers: Dict[str, str] = None, proxy: str = None):
        """
        Run it.
        """
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.async_gets(
                sem, callback, urls, headers, proxy))
        except Exception:
            loop.close
            traceback.print_exc()
            raise

    async def async_gets(self, sem: int, callback: Callable[[int, str, str], Any], urls: Iterable[Union[str, Tuple[str, int]]], headers: Dict[str, str] = None, proxy: str = None):
        """
        Asynchronous get multiple urls

        :param urls: Url string list and index will generated automatically based on zero. Or tuple(url, index) list
        """
        semaphore = Semaphore(sem)
        tasks = [self.async_get(index, semaphore, url, callback, headers, proxy) if type(url) == str
                 else self.async_get(url[1], semaphore, url[0], callback, headers, proxy)
                 for index, url in enumerate(urls)]
        await asyncio.wait(tasks)

    async def async_downloads(self, sem: int,  urls: Iterable[str], file_names: Iterable[str], headers: Dict[str, str] = None, proxy: str = None):
        """
        Asynchrounous download multiple urls
        """
        if len(urls) != len(file_names):
            raise ValueError(
                f'urls and file_names must have same length, bug got {len(urls)} {len(file_names)}')
        semaphore = Semaphore(sem)
        tasks = [self.async_download(index, semaphore, url, file_names[index], headers, proxy)
                 for index, url in enumerate(urls)]
        await asyncio.wait(tasks)
