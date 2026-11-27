"""Contact sheets and key frames of a video, with ffmpeg and nothing else.

Run it through media.sh.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

WEBP = ["-c:v", "libwebp", "-quality", "80"]
HASH_WIDTH, HASH_HEIGHT = 64, 40
WHOLE_FRAME = "0,0,1,1"

Region = tuple[float, float, float, float]


@dataclass(frozen=True)
class Probe:
    duration: float
    has_video: bool


def probe(path: Path) -> Probe:
    out = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(out.stdout)
    kinds = {stream.get("codec_type") for stream in data.get("streams", [])}
    return Probe(float(data["format"]["duration"]), "video" in kinds)


def stamp(seconds: float) -> str:
    hours, rest = divmod(int(seconds), 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def parse_region(text: str) -> Region:
    parts = [float(part) for part in text.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("expected left,top,width,height")
    left, top, width, height = parts
    if not (0 <= left < 1 and 0 <= top < 1 and 0 < width <= 1 - left and 0 < height <= 1 - top):
        raise argparse.ArgumentTypeError(f"{text} is not a region inside the frame")
    return left, top, width, height


def crop_filter(region: Region) -> str:
    left, top, width, height = region
    return f"crop=w=iw*{width}:h=ih*{height}:x=iw*{left}:y=ih*{top}"


def difference(first: bytes, second: bytes) -> float:
    return sum(abs(a - b) for a, b in zip(first, second, strict=True)) / len(first)


def grab(video: Path, second: float, dest: Path, vfilter: str) -> bool:
    # seeking before -i decodes one frame instead of the whole file, which
    # matters on recordings of several gigabytes
    result = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-ss",
            str(second),
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-vf",
            vfilter,
            *WEBP,
            str(dest),
            "-y",
        ],
        check=False,
        capture_output=True,
    )
    # a seek that lands past the last frame is normal at the end of a file
    return result.returncode == 0 and dest.exists()


def thumbprint(video: Path, second: float, vfilter: str) -> bytes | None:
    result = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-ss",
            str(second),
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-vf",
            f"{vfilter},scale={HASH_WIDTH}:{HASH_HEIGHT},format=gray",
            "-f",
            "rawvideo",
            "-",
        ],
        check=False,
        capture_output=True,
    )
    expected = HASH_WIDTH * HASH_HEIGHT
    return result.stdout if result.returncode == 0 and len(result.stdout) == expected else None


def contact_sheets(args: argparse.Namespace) -> None:
    info = probe(args.video)
    if not info.has_video:
        sys.exit(f"{args.video} has no video stream")
    args.out.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as scratch:
        tiles = Path(scratch)
        moments: list[float] = []
        second = args.every / 2
        while second < info.duration:
            if not grab(args.video, second, tiles / f"{len(moments):04d}.webp", f"scale={args.tile_width}:-2"):
                break
            moments.append(second)
            second += args.every

        per_sheet = args.columns * args.rows
        for number, first in enumerate(range(0, len(moments), per_sheet), start=1):
            sheet = args.out / f"contact-sheet-{number}.webp"
            subprocess.run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-start_number",
                    str(first),
                    "-i",
                    str(tiles / "%04d.webp"),
                    "-frames:v",
                    "1",
                    "-vf",
                    f"tile={args.columns}x{args.rows}:margin=4:padding=4:color=white",
                    *WEBP,
                    str(sheet),
                    "-y",
                ],
                check=True,
            )
            last = min(first + per_sheet, len(moments)) - 1
            print(f"{sheet}: {stamp(moments[first])} - {stamp(moments[last])}", flush=True)


def key_frames(args: argparse.Namespace) -> None:
    info = probe(args.video)
    if not info.has_video:
        sys.exit(f"{args.video} has no video stream")
    args.out.mkdir(parents=True, exist_ok=True)

    crop = crop_filter(args.crop)
    compare = f"{crop},{crop_filter(args.compare)}"
    previous: bytes | None = None
    kept = 0
    for second in range(0, int(info.duration), args.step):
        current = thumbprint(args.video, second, compare)
        if current is None:
            continue
        if previous is not None and difference(current, previous) <= args.threshold:
            continue
        dest = args.out / f"{stamp(second).replace(':', '-')}.webp"
        if grab(args.video, second, dest, f"{crop},scale='min({args.width},iw)':-2"):
            previous = current
            kept += 1
    print(f"{kept} key frames in {args.out}", flush=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="media.sh", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    sheets = commands.add_parser("contact-sheet", help="one tile per interval, tiled into sheets")
    sheets.add_argument("video", type=Path)
    sheets.add_argument("out", type=Path, help="folder for contact-sheet-N.webp")
    sheets.add_argument("--every", type=float, default=60.0, help="seconds between tiles")
    sheets.add_argument("--columns", type=int, default=4)
    sheets.add_argument("--rows", type=int, default=6)
    sheets.add_argument("--tile-width", type=int, default=560)
    sheets.set_defaults(handler=contact_sheets)

    frames = commands.add_parser("key-frames", help="frames that differ from the last kept one")
    frames.add_argument("video", type=Path)
    frames.add_argument("out", type=Path, help="folder for HH-MM-SS.webp")
    frames.add_argument("--step", type=int, default=10, help="seconds between sampled frames")
    frames.add_argument(
        "--threshold", type=float, default=6.0, help="mean pixel difference (0-255) a frame needs to be kept"
    )
    frames.add_argument(
        "--crop",
        type=parse_region,
        default=WHOLE_FRAME,
        help="part of the frame to keep: left,top,width,height as fractions",
    )
    frames.add_argument(
        "--compare",
        type=parse_region,
        default=WHOLE_FRAME,
        help="part of the cropped frame that decides what is new, same format",
    )
    frames.add_argument("--width", type=int, default=1280, help="max width of a saved frame")
    frames.set_defaults(handler=key_frames)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
