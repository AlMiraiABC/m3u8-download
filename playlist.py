import csv
import os
import shutil
from typing import Dict
from urllib.parse import quote, urlencode

import requests

from download.asynchttp import AsyncHTTP
from download.logger import CFLogger
from download.util import human_size
from m3u8_util.m3u8 import M3U8


class PlayList:
    def __init__(self, save: str = 'playlist.csv', log_dir='./log', downloaded_dir='./downloaded', c: bool = True) -> None:
        """
        Create a :class:`PlayList` instance.

        :param save: File which saved play lists.
        :param log_dir: Directory path to save logs.
        :param downloaded_dir: Directory path to save downloaded m3u8 files.
        :param rd: Ditermine whether remove downloaded source m3u8 files from
        :param c: Continue download, will ignore files which stored in :param:`downloaded_dir`
        """
        self.save = save
        self.logger_success = CFLogger(
            'playlist', '%(asctime)s:%(message)s', log_dir=log_dir).logger
        self.dllogger = CFLogger(
            'dllist', '%(asctime)s:%(message)s', log_dir=log_dir).logger
        self.downloaded_dir = downloaded_dir
        PlayList.check_dir(downloaded_dir)
        self.c = c
        if not c:
            if len(os.listdir(downloaded_dir)) != 0:
                raise ValueError(
                    f"downloaded directory is not empty if you want to re-download.")
        self.downloaded_files = os.listdir(downloaded_dir) if c else []

    def get_playlist(self, url: str, account: str, category: str, cookies: str, data: dict = {}, headers: Dict[str, str] = {}):
        """Download playlist which belong to :param:`category`"""
        DATA = {
            "data": {
                "account": account,
                "token": "",
                "videoCode": category
            }
        }
        DATA["data"].update(data)
        HEADERS = {
            "Cookie": cookies,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "http://www--vipexam--cn--http.vipexam.hevttc.utuweb.utuedu.com:8089",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36 Edg/96.0.1054.53",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        HEADERS.update(headers)
        CSV_HEADER = ["subject_Name", "videoLength", "videoName",
                      "parentCode", "videoCode", "updateTime", "orderNum"]
        response = requests.post(url=url, headers=HEADERS,
                                 data=urlencode(DATA, quote_via=quote)).json()
        if response["code"] == str(1):
            contents = response["list"]
            with open(self.save, "w", encoding="utf-8", newline="") as f:
                cw = csv.writer(f)
                cw.writerow(CSV_HEADER)
                for content in contents:
                    row = [content[h] for h in CSV_HEADER]
                    cw.writerow(row)
        else:
            raise ConnectionError("Cannot get play list. Please try again.")

    async def get_m3u8s(self, headers: Dict[str, str] = None, save_dir: str = 'm3u8'):
        """Download m3u8 files that u get from :method:`get_playlist`"""
        if headers is None:
            headers = {
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "http://www--vipexam--cn--http.vipexam.hevttc.utuweb.utuedu.com:8089/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36 Edg/96.0.1054.53"
            }
        PlayList.check_dir(save_dir)
        with open(self.save, "r", encoding='utf-8') as f:
            reader = csv.reader(f)
            li = list(reader)
            http = AsyncHTTP()
            urls = [
                f"http://video.vipexam.net//vedio/{row[3]}/{row[4]}/index.m3u8" for row in li[1:]]
            fns = [os.path.join(save_dir, f'{row[6]}.m3u8') for row in li[1:]]
            await http.async_downloads(4, urls, fns, headers)

    async def download(self, save: str = 'ts', *args, **kwargs):
        """
        Download m3u8 files which downloaded from :method:`get_m3u8s` as Transport Stream(MPEG2-TS).

        :param save: saved directory
        """
        PlayList.check_dir(save)
        with open(self.save, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            li = list(reader)[1:]
            for row in li:
                parentCode = row[3]
                videoCode = row[4]
                video_name = row[2]
                order = row[6]
                base_url = f"http://video.vipexam.net//vedio/{parentCode}/{videoCode}/"
                m3u8_filename = f'{order}.m3u8'
                if m3u8_filename in self.downloaded_files:
                    self.logger_success.warn(f'{m3u8_filename} founded in {self.downloaded_dir}, skip it.')
                    continue
                m3u8_filepath = os.path.join('./m3u8', m3u8_filename)
                save_filepath = os.path.join(save, f'{video_name}.ts')
                self.logger_success.info(f'start download {video_name}')
                await M3U8.download(m3u8_filepath, base_url, save_filepath, *args, **kwargs)
                size = os.path.getsize(save_filepath)
                self.logger_success.info(f'{video_name}, {human_size(size)}')
                shutil.move(m3u8_filepath, os.path.join(
                    self.downloaded_dir, m3u8_filename))
                self.dllogger.info(m3u8_filename)

    @staticmethod
    def check_dir(dir: str, create: bool = True, throw: bool = True) -> bool:
        if os.path.exists(dir) and not os.path.isdir(dir):
            if throw:
                raise IOError(f"{dir} is not a directory.")
            return False
        if create:
            if not os.path.exists(dir):
                os.makedirs(dir)
                print(f"{dir} not exist, create it.")
            return True
