"""将信息和错误信息输出至控制台和对应日志文件"""
import logging
import os
from logging.handlers import RotatingFileHandler


def _package_name(path: str) -> str:
    path = path.replace('\\', '/')
    path = path[:path.rfind('.')]
    p = path.split('/')
    return '/'.join(p[p.index('ProxyCollect') + 1:])


_FORMATTER = '%(asctime)s:%(levelname)s:%(processName)s[%(process)s]:%(threadName)s[%(thread)s]:' \
    '%(pathname)s:%(funcName)s:%(message)s'  # 日志格式
_DATEFMT = '%Y/%m/%d %H:%M:%S'  # asctime格式


class CFLogger:
    """
    Write logger message to console and file.
    """

    def __init__(self, name: str = '', fmt: str = _FORMATTER, datefmt: str = _DATEFMT, log_dir='log',
                 encoding='utf-8', backup_count: int = 14, filesize: int = 10485760, level=logging.DEBUG):
        """
        Create a :class:`Logger` instance

        :param name: Logger name, same as log file name.
        :param fmt: Message formats.
        :param datefmt: Date formats.
        :param log_dir: Directory path to save log files.
        :param encoding: Message encoding.
        :param backup_count: Count number log files saved.
        :param filesize: Max bytes of each log file.
        :param level: Output level.
        """
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            # region set handler
            self.logger.setLevel(level)
            formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
            # region log to console
            log_console = logging.StreamHandler()
            log_console.setFormatter(formatter)
            # endregion
            # region log to file
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            filename: str = os.path.join(log_dir, name)+'.log'
            log_file = RotatingFileHandler(filename, backupCount=backup_count, maxBytes=filesize,
                                           encoding=encoding)
            log_file.setFormatter(formatter)
            # endregion
            # endregion
            self.logger.addHandler(log_console)
            self.logger.addHandler(log_file)
