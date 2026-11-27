---
name: media-extract
description: >-
  Get what is said and shown in a video or audio file: a timestamped transcript
  of the speech (faster-whisper, runs locally), contact sheets, key frames,
  single frames and slices. Use whenever the user gives a recording (mp4, mov,
  mkv, webm, mp3, m4a, wav and so on) and wants to know what is in it, or when
  another skill needs a transcript or frames from one.
---

# Working with a video or audio file

A recording carries two sources, and they answer different questions:

- **the sound** says what people said, in the order they said it;
- **the picture** shows what was on screen: slides, documents, code, names. It
  is the only place where text is spelled correctly.

Pull each one out on its own, then read them together. This skill gives the
tools for both and the order to use them in. What to do with the result (notes,
a summary, a word list) is up to the task or the skill that called this one.

## File resolution

`SKILL_DIR` is the absolute path of the folder that contains this SKILL.md.
Every command below goes through `SKILL_DIR/scripts/media.sh`; `--help` on each
command lists all options.

## Setup and the cache

The script needs `bash`, plus `ffmpeg` (built with libwebp), `ffprobe` and `uv`
on `PATH`. A system Python is not needed: `uv` downloads its own. When `mise`
has `ffmpeg` or `uv` installed but the current folder does not enable them, the
script takes them from `mise` itself. The plain `ffprobe` and `ffmpeg` commands
in this file do not: when one fails with `No version is set for shim`, run it
as `mise x ffmpeg -- ffprobe ...`. When `media.sh` stops and points here, ask
the user before installing the missing tool:

| Tool               | macOS                 | Debian, Ubuntu                                     |
| ------------------ | --------------------- | -------------------------------------------------- |
| `ffmpeg` `ffprobe` | `brew install ffmpeg` | `sudo apt install ffmpeg`                          |
| `uv`               | `brew install uv`     | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

Everything else the script builds itself on first use and keeps in one cache
folder:

    $MEDIA_EXTRACT_CACHE        default: ~/.cache/agentkit/media-extract
      venv/                     faster-whisper and its dependencies
      python/                   the interpreter the venv runs on
      models/                   speech models, HF_HOME points here

The cache is shared by every project and every skill that uses this one, so a
model downloads once. `large-v3-turbo` is about 1.6 GB, `large-v3` about 3 GB.
Never delete the cache and never install these packages anywhere else. On a
machine that is rebuilt often, such as a container, set `MEDIA_EXTRACT_CACHE`
to a folder that survives the rebuild.

The first `transcribe` builds the venv and downloads the model, which takes a
few minutes. A warning about `HF_TOKEN` during the download is harmless.

## Look at the file first

    ffprobe -v error -show_entries format=duration:stream=codec_type,width,height \
        -of compact <file>

It tells you how long the recording is and whether it has a picture at all.

## Order of work

1. Start `transcribe` in the background. It is the slowest step: an hour of
   speech takes about ten minutes on 8 CPU cores with the default model.
2. While it runs, make the contact sheets and read every one of them.
3. Make the key frames and open the ones the contact sheets point at.
4. Read the transcript end to end, with the frames in mind. Names and terms
   that the speech model garbled are usually readable on a frame.

For an audio file, only step 1 and step 4 apply.

## transcribe

    "SKILL_DIR/scripts/media.sh" transcribe <file> <out.txt> \
        [--language ru] [--model large-v3] [--start 720 --duration 180]

Writes one line per phrase, `[HH:MM:SS] text`. Times are from the start of the
file, also when `--start` is given. The transcript does not say who is
speaking; judge that by the sense of the phrase.

Pass `--language` whenever you know it. Without it the model guesses from the
first 30 seconds, and a silent or musical start leads to a wrong guess.

## contact-sheet

    "SKILL_DIR/scripts/media.sh" contact-sheet <video> <out-dir> \
        [--every 60] [--columns 4] [--rows 6]

Takes one frame every `--every` seconds, starting at half that interval, and
tiles them into `contact-sheet-N.webp`, left to right and top to bottom. It
prints the time range of each sheet. Text on the tiles is too small to read and
that is fine: a sheet is the map of the recording. It shows where the screen
changes, where a camera fills the screen, and which stretches are worth a
closer look.

## key-frames

    "SKILL_DIR/scripts/media.sh" key-frames <video> <out-dir> \
        [--step 10] [--threshold 6] [--crop 0,0.2,0.86,0.73] [--compare 0,0,0.86,1]

Looks at a frame every `--step` seconds and keeps it as `HH-MM-SS.webp` when it
differs from the last kept frame by more than `--threshold` (mean pixel
difference, 0-255). Regions are `left,top,width,height` as fractions:

- `--crop` keeps only that part of the frame, for example the shared window
  without the menu bar and the dock;
- `--compare` is the part of the cropped frame that decides what is new. Use it
  to leave out things that move all the time and mean nothing, such as a camera
  strip, a clock or a taskbar.

Check the crop on the contact sheet before a long run. Then curate the result:
delete near-duplicates and frames with nothing useful, and rename each keeper
so the name says what is on it.

## Plain ffmpeg for the rest

Put `-ss` before `-i`: ffmpeg then jumps to that point instead of decoding
everything before it, which matters on a file of several gigabytes.

    # one frame, at 15:50
    ffmpeg -v error -ss 950 -i <video> -frames:v 1 -vf "scale=1280:-2" \
        -c:v libwebp -quality 80 frame.webp -y

    # the same frame, cropped to a region in pixels: crop=width:height:x:y
    ffmpeg -v error -ss 950 -i <video> -frames:v 1 \
        -vf "crop=2980:1640:20:440,scale=1280:-2" -c:v libwebp -quality 80 frame.webp -y

    # a slice, three minutes from 12:00, without re-encoding
    ffmpeg -v error -ss 720 -t 180 -i <file> -c copy slice.mp4 -y

    # the sound only, in the format speech tools expect
    ffmpeg -v error -i <file> -vn -ac 1 -ar 16000 -c:a pcm_s16le audio.wav -y

A slice made with `-c copy` starts at the nearest key frame of the stream, so
it can begin a few seconds early. Drop `-c copy` when the cut must be exact.

## Known traps

1.  **`large-v3-turbo` drops dense passages.** It skips a few seconds where
    someone reads a fast list, which is often the part worth having. When a
    stretch reads as if something is missing, redo only that stretch with the
    full model: `--model large-v3 --start <s> --duration <s>`. Three minutes
    take about two minutes.
2.  **Memory.** `large-v3-turbo` peaks at about 2.8 GB on an hour of speech.
    `large-v3` peaks at about 5.6 GB and gets killed on anything longer than a
    few minutes on an 8 GB machine, which is why the step above cuts a stretch
    first.
3.  **Never force a language the speech is not mostly in.** The model then
    invents subtitle boilerplate in that language (`Υπότιτλοι AUTHORWAVE`) over
    the real speech. For mixed speech, pass the main language: words of the
    other one come out spelled in the main alphabet, as a guess. Do not trust
    their spelling; check them against a frame.
4.  **Key frames miss slow and small changes.** A slow scroll, or a whiteboard
    where a few words are added at a time, never crosses the threshold between
    two samples. When a contact sheet shows a screen you have no key frame for,
    grab that moment by hand with plain ffmpeg.
5.  **A screen recording catches everything on the screen.** Mail, chats,
    terminals and other windows show up whenever the recorder ran during a
    break. Spot them on the contact sheets, skip those frames, and never copy
    their content into the result.
