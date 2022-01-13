from unittest.async_case import IsolatedAsyncioTestCase
from m3u8_util.m3u8 import M3U8

BASE_URL = 'http://video.vipexam.net//vedio/ve05001019ys4114kclx01ly04xs02hz01js0396/ve05001019ys4114kclx01ly04xs02hz01js0396zj133/'
FILE_NAME = './m3u8_util/test.m3u8'


class TestM3U8(IsolatedAsyncioTestCase):
    async def test_download_segs(self):
        md = M3U8(FILE_NAME)
        await md.download_segs(BASE_URL)

    def test_combine_segs(self):
        md = M3U8(FILE_NAME)
        md.combine_segs('result/abc.ts')

    async def test_download(self):
        await M3U8.download(FILE_NAME, BASE_URL, 'result/abc2.ts')
