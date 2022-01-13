import json
from asyncio.locks import Semaphore
from unittest.async_case import IsolatedAsyncioTestCase

from download.asynchttp import AsyncHTTP

GET = 'https://getman.cn/mock/route/to/demo'
DOWNLOAD = 'https://cdn.office.store.zhuazi.com/channel/4.2.4.1/MicrosoftOffice_InstallationComponent_zywz_a02.exe'


def parse(i, url, res):
    print(i, url, res)
    return res, json.loads(res)['message']


class TestAsync(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.asynchttp = AsyncHTTP()
        return super().setUp()

    async def test_async_get(self):
        result = await self.asynchttp.async_get(0, Semaphore(4), GET, parse)
        self.assertEquals(result, 'Hello world!')

    async def test_async_gets_default_index(self):
        """生成5条日志，index为0~4，顺序不固定"""
        await self.asynchttp.async_gets(4, parse, [GET]*5)

    async def test_async_gets_special_index(self):
        """生成6条日志，index为9~14，顺序不固定"""
        await self.asynchttp.async_gets(4, parse, [(GET, i) for i in range(9, 15)])

    def test_run(self):
        self.asynchttp.run(4, parse, [GET]*5)

    async def test_async_download(self):
        await self.asynchttp.async_download(0, Semaphore(4), DOWNLOAD, '1.bin')
