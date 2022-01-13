from unittest import TestCase

from download.logger import CFLogger


class TestLogger(TestCase):

    def setUp(self) -> None:
        self.err = CFLogger('error', '%(asctime)s:%(message)s',
                          log_dir='log/test').logger
        self.suc = CFLogger('success', '%(asctime)s:%(message)s',
                          log_dir='log/test').logger
        return super().setUp()

    def test_err(self):
        self.err.error('test error message')

    def test_suc(self):
        self.suc.info('test success message')

    def test_err_suc(self):
        self.err.error('test err')
        self.suc.info('test suc')
