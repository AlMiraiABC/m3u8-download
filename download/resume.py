import os
from typing import Awaitable, Callable

import aiofiles
from al_utils.logger import Logger

_logger = Logger(__file__).logger


class Resume:
    def __init__(self, success_log: str = "./logs/downloaded.log", error_log: str = "./logs/errors.log", current_log: str = './logs/current.log', current: str = '') -> None:
        self._suc = success_log
        self._err = error_log
        self._cur = current_log
        self._current = current
        self._failed: set[str] = set()
        self._bp: bool = False

    async def _set_current(self, cur: str):
        async with aiofiles.open(self._cur, 'w', encoding='utf-8') as f:
            await f.write(cur)

    @property
    def current(self) -> str:
        return self._current

    async def _read(self, fn: str) -> list[str]:
        if not fn:
            return []
        # create if not exist
        async with aiofiles.open(fn, 'w') as f:
            pass
        async with aiofiles.open(fn) as f:
            return await f.readlines()

    async def run(self, key: str, callback: Callable[[str], Awaitable[bool]]):
        if self._bp or key in self._failed:
            return await self._run(key, callback)
        # skipped until current
        if self._current:
            if key != self._current:
                _logger.info(f"callback skipped of key {key}")
                return
        else:
            self._bp = True

    async def _run(self, key: str, callback: Callable[[str], Awaitable[bool]]):
        try:
            ret = await callback(key)
            if ret:
                await self._set_current(key)
                _logger.info(f"callback successfully of key {key}")
                await self._sf.write(key+os.linesep)
                return
            raise RuntimeError(f"Callback failed of key {key}")
        except:
            _logger.error(f"callback failed of key {key}")
            self._failed.add(key)
            await self._ff.write(key+os.linesep)

    async def __aenter__(self):
        if self._current:
            await self._set_current(self._current)
        else:
            c = await self._read(self._cur)
            self._current = c[0] if c else ''
        if self._current:
            self._failed = set(await self._read(self._err))
        self._ff = await aiofiles.open(self._err, 'a', encoding='utf-8')
        self._sf = await aiofiles.open(self._suc, 'a', encoding='utf-8')

        return self

    async def __aexit__(self, *_):
        await self.close()

    async def close(self):
        await self._ff.close()
        await self._sf.close()
