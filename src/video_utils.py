"""
Video utilities (placeholder)
"""

import os


def check_ffmpeg():
    """Check if ffmpeg is installed."""
    import shutil
    return shutil.which('ffmpeg') is not None


if __name__ == '__main__':
    print('✓ Video utils module')
