"""Speech of a video or audio file to "[HH:MM:SS] text" lines.

Run it through media.sh, which keeps the virtualenv and the models in one
cache folder.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
import time
import wave
from pathlib import Path

import numpy as np
from faster_whisper import BatchedInferencePipeline, WhisperModel
from media import stamp


def extract_audio(source: Path, dest: Path, start: float, duration: float | None) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-ss",
            str(start),
            "-i",
            str(source),
            *(["-t", str(duration)] if duration else []),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            str(dest),
            "-y",
        ],
        check=True,
    )


def read_wav(audio: Path) -> np.ndarray:
    # faster-whisper would otherwise decode the path through PyAV, whose 19.x
    # release dropped the metadata_errors argument it passes
    with wave.open(str(audio)) as handle:
        if (handle.getnchannels(), handle.getsampwidth(), handle.getframerate()) != (1, 2, 16000):
            raise ValueError(f"{audio} is not 16 kHz mono 16-bit PCM")
        frames = handle.readframes(handle.getnframes())
    return np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0


def transcribe(args: argparse.Namespace) -> None:
    started = time.time()
    with tempfile.TemporaryDirectory() as scratch:
        audio = Path(scratch) / "audio.wav"
        extract_audio(args.source, audio, args.start, args.duration)
        samples = read_wav(audio)

    model = WhisperModel(args.model, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 4)
    # the batched pipeline has its own VAD; vad_filter=True on plain
    # transcribe() turns the output into repeated hallucinated lines
    segments, info = BatchedInferencePipeline(model=model).transcribe(
        samples,
        language=args.language,
        batch_size=4,
        beam_size=5,
        condition_on_previous_text=False,
    )
    if args.language is None:
        print(f"detected language: {info.language} ({info.language_probability:.0%})", flush=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as out:
        for seg in segments:
            out.write(f"[{stamp(args.start + seg.start)}] {seg.text.strip()}\n")
            out.flush()
    print(f"{args.out} in {time.time() - started:.0f}s", flush=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="media.sh transcribe", description=__doc__)
    parser.add_argument("source", type=Path, help="video or audio file")
    parser.add_argument("out", type=Path, help="transcript file to write")
    parser.add_argument(
        "--model", default="large-v3-turbo", help="large-v3 is more accurate and about five times slower"
    )
    parser.add_argument("--language", help="ISO code such as en or ru; detected when omitted")
    parser.add_argument("--start", type=float, default=0.0, help="second to start from")
    parser.add_argument("--duration", type=float, help="seconds to transcribe")
    return parser


if __name__ == "__main__":
    transcribe(build_parser().parse_args())
