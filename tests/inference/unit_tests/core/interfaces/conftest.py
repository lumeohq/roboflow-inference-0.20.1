import os.path

import pytest

ASSETS_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "assets"
))


@pytest.fixture
def local_video_path() -> str:
    return os.path.join(ASSETS_DIR, "example_video.mp4")
