import os
from typing import Literal

CONTINUE = True
# Determine whether continue download

DATA_DIR: str = "data"
"""Directory to save data."""
M3U8_FILE_DIR = os.path.join(DATA_DIR, 'm3u8')
"""Directory to save m3u8 files."""
M3U8_VIDEO_DIR = os.path.join(DATA_DIR, 'videos')
"""Directory to save downloaded videos."""
TMP_DIR = os.path.join(DATA_DIR, 'tmp')
"""Directory to save each segments of m3u8 file."""

MODE: Literal['aio', 'ff'] = 'aio'
RETRY: int = 3

HEADERS: dict = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.42"
}
