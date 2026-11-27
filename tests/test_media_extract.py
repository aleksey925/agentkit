import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest
from repo_paths import REPO_ROOT

SCRIPT = REPO_ROOT / "plugins/common/skills/media-extract/scripts/media.py"
SPEC = importlib.util.spec_from_file_location("media", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
media = importlib.util.module_from_spec(SPEC)
sys.modules["media"] = media
SPEC.loader.exec_module(media)

COLORS = ("red", "blue", "green")
SCENE_SECONDS = 20


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [(0, "00:00:00"), (75.9, "00:01:15"), (3725, "01:02:05")],
    ids=["zero", "drops-fraction", "over-an-hour"],
)
def test_stamp(seconds: float, expected: str) -> None:
    # act
    result = media.stamp(seconds)

    # assert
    assert result == expected


def test_parse_region__inside_frame__returns_fractions() -> None:
    # act
    region = media.parse_region("0.1,0.2,0.5,0.8")

    # assert
    assert region == (0.1, 0.2, 0.5, 0.8)


@pytest.mark.parametrize(
    "text",
    ["0,0,1", "0.6,0,0.5,1", "0,0,0,1", "-0.1,0,0.5,0.5"],
    ids=["three-parts", "past-right-edge", "zero-width", "negative-left"],
)
def test_parse_region__invalid__raises(text: str) -> None:
    # act & assert
    with pytest.raises(argparse.ArgumentTypeError):
        media.parse_region(text)


def test_crop_filter() -> None:
    # act
    result = media.crop_filter((0.1, 0.2, 0.5, 0.75))

    # assert
    assert result == "crop=w=iw*0.5:h=ih*0.75:x=iw*0.1:y=ih*0.2"


def test_difference() -> None:
    # act
    result = media.difference(bytes([0, 10, 255]), bytes([4, 0, 255]))

    # assert
    assert result == 14 / 3


@pytest.mark.parametrize(
    "extra",
    [[], ["--crop", "0.25,0.25,0.5,0.5", "--compare", "0,0,0.5,1"]],
    ids=["whole-frame", "cropped"],
)
def test_key_frames__scene_changes__keeps_one_frame_per_scene(clip: Path, tmp_path: Path, extra: list[str]) -> None:
    # arrange
    out = tmp_path / "frames"

    # act
    run_media("key-frames", str(clip), str(out), "--step", "5", *extra)

    # assert
    assert sorted(path.name for path in out.iterdir()) == [
        f"{media.stamp(index * SCENE_SECONDS).replace(':', '-')}.webp" for index in range(len(COLORS))
    ]


def test_contact_sheet__more_tiles_than_a_sheet__splits_into_sheets(clip: Path, tmp_path: Path) -> None:
    # act
    result = run_media("contact-sheet", str(clip), str(tmp_path), "--every", "10", "--columns", "4", "--rows", "1")

    # assert
    assert (sorted(path.name for path in tmp_path.iterdir()), result.stdout.splitlines()) == (
        ["contact-sheet-1.webp", "contact-sheet-2.webp"],
        [
            f"{tmp_path / 'contact-sheet-1.webp'}: 00:00:05 - 00:00:35",
            f"{tmp_path / 'contact-sheet-2.webp'}: 00:00:45 - 00:00:55",
        ],
    )


@pytest.mark.usefixtures("ffmpeg_ready")
def test_key_frames__audio_only__exits_with_error(tmp_path: Path) -> None:
    # arrange
    audio = tmp_path / "tone.wav"
    ffmpeg("-f", "lavfi", "-i", "sine=440:d=2", str(audio))

    # act
    result = run_media("key-frames", str(audio), str(tmp_path / "frames"), check=False)

    # assert
    assert (result.returncode, result.stderr) == (1, f"{audio} has no video stream\n")


def ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-v", "error", *args, "-y"], check=True)


def run_media(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, check=check)


@pytest.fixture(name="ffmpeg_ready", scope="module")
def ffmpeg_ready_fixture() -> None:
    try:
        runnable = subprocess.run(["ffmpeg", "-version"], check=False, capture_output=True).returncode == 0
    except FileNotFoundError:
        runnable = False
    if not runnable:
        pytest.skip("ffmpeg is not runnable")


@pytest.fixture(name="clip", scope="module")
def clip_fixture(ffmpeg_ready: None, tmp_path_factory: pytest.TempPathFactory) -> Path:
    clip = tmp_path_factory.mktemp("media") / "clip.mp4"
    sources = [
        arg for color in COLORS for arg in ("-f", "lavfi", "-i", f"color={color}:s=320x180:d={SCENE_SECONDS}:r=5")
    ]
    inputs = "".join(f"[{index}]" for index in range(len(COLORS)))
    ffmpeg(
        *sources,
        "-filter_complex",
        f"{inputs}concat=n={len(COLORS)}:v=1:a=0",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(clip),
    )
    return clip
