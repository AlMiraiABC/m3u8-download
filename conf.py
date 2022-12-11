# determine whether continue download, downloaded m3u8 files will be ignored
# if set to False, DOWNLOADED_DIR have to be empty
from typing import Literal


CONTINUE = True

M3U8_FILE_DIR = './m3u8'
"""Directory to save m3u8 files."""
M3U8_VIDEO_DIR = './videos'
"""Directory to save downloaded videos."""
TMP_DIR = './tmp'
"""Directory to save each segments of m3u8 file."""

MODE: Literal['aio', 'ff'] = 'ff'
