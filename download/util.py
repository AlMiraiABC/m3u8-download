import os
import re


def human_size(length: float) -> str:
    """
    Convert bytes with storage unit.

    :param length: bytes count.
    :return: storage unit.
    """
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    radix = 1024.0
    for i in range(len(units)):
        if (length / radix) < 1:
            return "%.2f%s" % (length, units[i])
        length = length / radix
    return "%.2f%s" % (length, units[-1])


def format_fn(filename: str) -> str:
    """
    format :param:`filename` to legitimate.
    support unicode, such as chinese, emoji.

    :param filename: filename, could include directory and extension.

    ### Example:
    >>> # filename is 376 bytes.
    >>> format_fn('a/b/c/1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ甲乙丙丁戊己庚辛壬癸1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ甲乙丙丁戊己庚辛壬癸1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ甲乙丙丁戊己庚辛壬癸1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ甲乙丙丁戊己庚辛壬癸.mp4.mp4')
    >>> # >>> a/b/c/abc/def\\1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ甲乙丙丁戊己庚辛壬癸1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ甲乙丙丁戊己庚辛壬癸1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ甲.mp4
    >>> # return 253 bytes.
    """
    if not filename:
        return ''
    fn = os.path.basename(filename)
    f, e = os.path.splitext(fn)
    d = os.path.dirname(filename)
    if os.name == 'nt':
        CHARS = re.compile('[\\/:*?"<>|]')
        f = CHARS.sub('', fn)
    elif os.name == 'posix':
        CHARS = re.compile('[\\/*?-]')
        f = CHARS.sub('', fn)
    try:
        f = f.encode()[:255-len(e.encode())].decode()  # 255 + '\0'
    except UnicodeDecodeError as ex:
        f = f.encode()[:ex.args[2]].decode()
    fn = f+e
    o = os.path.join(d, fn)
    return o
