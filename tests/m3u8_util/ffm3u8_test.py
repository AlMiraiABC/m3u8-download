import os
import tempfile
from unittest import TestCase

from m3u8_util.m3u8 import FFM3U8


class FFM3U8Tests(TestCase):
    def test_download_success(self):
        URL = "https://t20.cdn2020.com/video/m3u8/2022/12/06/c26392d0/index.m3u8"
        _, FN = tempfile.mkstemp(prefix='m3u8', suffix='.ts')
        FFM3U8.download(URL, FN)
        size = os.path.getsize(FN)
        self.assertTrue(size)

    def test_download_fail(self):
        URL = "https://example.com/unexist.m3u8"
        _, FN = tempfile.mkstemp(prefix='m3u8', suffix='.ts')
        with self.assertRaises(RuntimeError) as ex:
            FFM3U8.download(URL, FN)
        print(ex)

    def test_download_override_n(self):
        URL = "https://t20.cdn2020.com/video/m3u8/2022/12/06/c26392d0/index.m3u8"
        _, FN = tempfile.mkstemp(prefix='m3u8', suffix='.ts')
        with self.assertRaises(RuntimeError) as ex:
            FFM3U8.download(URL, FN, override=False)
        print(ex)
