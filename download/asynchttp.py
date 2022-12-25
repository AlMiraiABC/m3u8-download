import asyncio
import traceback
from asyncio import Semaphore
from typing import Any, Callable, Iterable, Optional, TypeVar, Union

import aiofiles
import aiohttp
from aiohttp.client import ClientTimeout
from al_utils.logger import Logger

from download.util import human_size

logger = Logger(__file__).logger

CBT = TypeVar('CBT')


class AsyncHTTP:
    """
    Asynchronous HTTP requests. Wrapper for :module:`aiohttp`
    """

    def __init__(self) -> None:
        pass

    async def async_download(self, index: int, semaphore: Semaphore, url: str, file_name: str, headers: Optional[dict[str, str]] = {}, proxy: Optional[str] = None, chunk_size: int = 1024*1024, retry: int = 3):
        if not retry or retry < 0:
            retry = 3
        async with semaphore:
            async with aiohttp.ClientSession(timeout=ClientTimeout(0)) as client:
                for i in range(retry):
                    try:
                        response = await client.get(
                            url=url, headers=headers, proxy=proxy)
                        if response.ok:
                            length = int(response.headers.get(
                                'Content-Length', '0'))
                            async with aiofiles.open(file_name, 'wb') as f:
                                async for chunk in response.content.iter_chunked(chunk_size):
                                    await f.write(chunk)
                            logger.info(
                                f'{index}, {url}, {human_size(length)}')
                            return
                        else:
                            logger.error(
                                f'{index}, {i}, {url}, {response.status}')
                    except Exception:
                        logger.error(
                            f'{index}, {i}, {url}', exc_info=True, stack_info=True)
                raise IOError(f'Download failed {url} in {retry} retries')

    async def async_get(self, index: int, semaphore: Semaphore, url: str, callback: Callable[[int, str, str], CBT], headers: Optional[dict[str, str]] = None, proxy: Optional[str] = None, retry: int = 3) -> Optional[CBT]:
        """
        Asynchronous get a :param:`url` and write message in loggers. Then invoke :param:`callback` when get response successfully.

        :param index: Specified id for :param:`url`
        :param semaphore: Concurrency controll.
        :param url: Request url
        :param callback: Invoke callback when get response successfully. `(index, url, response) -> CBT`
        :param headers: Request headers.
        :param proxy: Request proxy.
        """
        if not retry or retry < 0:
            retry = 3
        async with semaphore:
            async with aiohttp.ClientSession() as client:
                for i in range(retry):
                    try:
                        response = await client.get(
                            url=url, headers=headers, proxy=proxy)
                        if response.ok:
                            res = callback(index, url, await response.text())
                            logger.info(f'{index}, {url}, {res}')
                            return res
                        else:
                            logger.error(
                                f'{index}, {i}, {url}, {response.status}')
                    except Exception:
                        logger.error(
                            f'{index}, {i}, {url}', exc_info=True, stack_info=True)
                raise IOError(f'Download failed {url} in {retry} retries')

    def run(self, sem: int, callback: Callable[[int, str, str], Any], urls: Iterable[str], headers: Optional[dict[str, str]] = None, proxy: Optional[str] = None):
        """
        Run it.
        """
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.async_gets(
                sem, callback, urls, headers, proxy))
        except Exception:
            loop.close()
            logger.error('run failed', exc_info=True, stack_info=True)
            raise

    async def async_gets(self, sem: int, callback: Callable[[int, str, str], Any], urls: Iterable[Union[str, tuple[str, int]]], headers: Optional[dict[str, str]] = None, proxy: Optional[str] = None, retry: int = 3):
        """
        Asynchronous get multiple urls

        :param urls: Url string list and index will generated automatically based on zero. Or tuple(url, index) list
        """
        if not retry or retry < 0:
            retry = 3
        semaphore = Semaphore(sem)
        tasks = [self.async_get(index, semaphore, url, callback, headers, proxy, retry) if type(url) == str  # type: ignore
                 else self.async_get(url[1], semaphore, url[0], callback, headers, proxy, retry) # type: ignore
                 for index, url in enumerate(urls)]
        await asyncio.wait(tasks)

    async def async_downloads(self, sem: int,  urls: list[str], file_names: list[str], headers: Optional[dict[str, str]] = None, proxy: Optional[str] = None, retry: int = 3):
        """
        Asynchrounous download multiple urls

        :param sem: Max concurrency count.
        :param urls: Each of download url.
        :param file_names: Each of url saved file name.
        :param headers: Request headers.
        :param proxy: Request proxy.
        :param retry: Retry times if failed.
        """
        if not retry or retry < 0:
            retry = 3
        if len(urls) != len(file_names):
            raise ValueError(
                f'urls and file_names must have same length, bug got {len(urls)} {len(file_names)}')
        semaphore = Semaphore(sem)
        tasks = [self.async_download(index, semaphore, url, file_names[index], headers, proxy, retry=retry)
                 for index, url in enumerate(urls)]
        await asyncio.wait(tasks)
