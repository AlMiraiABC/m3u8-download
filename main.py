import asyncio
import sys
from getopt import GetoptError, getopt

from playlist import PlayList

URL = "http://www--vipexam--cn--http.vipexam.hevttc.utuweb.utuedu.com:8089/web/videoPlay"


def start(account: str, category: str, cookies: str):
    pl = PlayList()
    pl.get_playlist(URL, account, category, cookies)
    asyncio.run(pl.get_m3u8s())
    asyncio.run(pl.download())


if __name__ == '__main__':
    try:
        opts, args = getopt(sys.argv[1:], "ha:c:x:", [
                            "help", "account=", "cookies=", "category="])
    except GetoptError as err:
        print(err)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ['-h', '--help']:
            print('-a --account\taccount when loged in')
            print('-x --cookies\tcookies when loged in')
            print('-c --category\tvideo code, category code for videos')
            sys.exit()
        elif opt in ("-a", "--account"):
            account = arg
        elif opt in ('-x', '--cookies'):
            cookies = arg
        elif opt in ('-c', '--category'):
            category = arg
    start(account, category, cookies)
