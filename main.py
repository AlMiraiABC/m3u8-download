import asyncio
import os
import sys
from getopt import GetoptError, getopt

from conf import ACCOUNT, CATEGORY, COOKIES
from playlist import PlayList

URL = "http://www--vipexam--cn--http.vipexam.hevttc.utuweb.utuedu.com:8089/web/videoPlay"


def start(account: str, category: str, cookies: str):
    pl = PlayList()
    pl.get_playlist(URL, account, category, cookies)
    asyncio.run(pl.get_m3u8s())
    asyncio.run(pl.download())


def check_args(*args: str):
    errinfo = '''
    ACCOUNT, COOKIES and CATEGORY have to be set.
    1. set from conf.py
    2. set from env
    3. set from args(see more 'main.py -h')
    args > env > conf.py
    '''
    for arg in args:
        if arg is not None and arg.strip():
            continue
        else:
            raise ValueError(errinfo)


if __name__ == '__main__':
    try:
        opts, args = getopt(sys.argv[1:], "ha:x:c:",
                            ["help", "account=", "cookies=", "category="])
    except GetoptError as err:
        print(err)
        sys.exit(2)
    # conf
    account = ACCOUNT
    cookies = COOKIES
    category = CATEGORY
    # env
    if os.environ.get('ACCOUNT'):
        account = os.environ.get('ACCOUNT')
    if os.environ.get('COOKIES'):
        cookies = os.environ.get('COOKIES')
    if os.environ.get('CATEGORY'):
        category = os.environ.get('CATEGORY')
    # arg
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
    check_args(account, category, cookies)
    start(account.strip(), category.strip(), cookies.strip())
