#!/usr/bin/env python3
"""Turn local photos into a still wallpaper or a silent crossfading MP4."""

import argparse
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageOps


FPS = 30


def dimensions(text):
    try:
        width, height = map(int, text.lower().split("x"))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("use WIDTHxHEIGHT") from exc
    if width < 1 or height < 1:
        raise argparse.ArgumentTypeError("width and height must be positive numbers")
    return width, height


def fit_image(path, size, center):
    with Image.open(path) as source:
        rgba = ImageOps.exif_transpose(source).convert("RGBA")
    crop = ImageOps.fit(rgba, size, Image.Resampling.LANCZOS, centering=center)
    result = Image.new("RGB", size, "#161319")
    result.paste(crop, (0, 0), crop)
    return result


def encode(images, target, seconds, fade, ffmpeg):
    directory = target.parent
    lines = ["ffconcat version 1.0"]
    slot_frames = round(seconds * FPS)
    fade_frames = round(fade * FPS) if len(images) > 1 else 0

    def append(path, frames):
        lines.extend((f"file '{path.name}'", f"option framerate {FPS}",
                      f"duration {frames / FPS:.9f}"))

    for index, current in enumerate(images):
        following = images[(index + 1) % len(images)]
        append(current, slot_frames - fade_frames)
        if fade_frames:
            with Image.open(current) as before, Image.open(following) as after:
                for step in range(1, fade_frames + 1):
                    fraction = step / fade_frames
                    opacity = fraction ** 2 * (3 - 2 * fraction)
                    frame = directory / f"fade-{index:04}-{step:04}.jpg"
                    Image.blend(before, after, opacity).save(frame, quality=95, subsampling=0)
                    append(frame, 1)
    append(images[0], 1)
    playlist = directory / "frames.ffconcat"
    playlist.write_text("\n".join(lines) + "\n", encoding="utf-8")
    subprocess.run([
        ffmpeg, "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(playlist),
        "-vf", f"fps={FPS},scale=in_range=pc:out_range=tv:in_color_matrix=bt601:out_color_matrix=bt709,format=yuv420p",
        "-frames:v", str(slot_frames * len(images)),
        "-c:v", "libx264", "-crf", "18", "-preset", "fast", "-an",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-movflags", "+faststart", str(target),
    ], check=True)


def deliver(source, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        with source.open("rb") as read, output.open("xb") as write:
            created = True
            shutil.copyfileobj(read, write)
    except BaseException:
        if created:
            output.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="+", type=Path, help="local images in playback order")
    parser.add_argument("--size", type=dimensions, required=True, help="WIDTHxHEIGHT in pixels")
    parser.add_argument("--output", type=Path, required=True, help="new JPG, PNG, or MP4 file")
    parser.add_argument("--center", type=float, nargs=2, default=(.5, .5), metavar=("X", "Y"),
                        help="crop position, each value from 0 to 1")
    parser.add_argument("--seconds", type=float, default=3, help="seconds per image, including the fade")
    parser.add_argument("--fade", type=float, default=.65, help="fade duration in seconds")
    parser.add_argument("--ffmpeg", default="ffmpeg", help="FFmpeg executable or command name")
    args = parser.parse_args()
    extension = args.output.suffix.lower()
    if extension not in (".jpg", ".jpeg", ".png", ".mp4"):
        parser.error("output must be JPG, PNG, or MP4")
    if args.output.exists():
        parser.error("output already exists")
    if not all(0 <= value <= 1 for value in args.center):
        parser.error("crop coordinates must be between 0 and 1")
    if extension == ".mp4":
        if any(side % 2 for side in args.size):
            parser.error("MP4 requires even width and height")
        if not (math.isfinite(args.seconds * FPS) and math.isfinite(args.fade * FPS)
                and 0 <= args.fade < args.seconds
                and round(args.seconds * FPS) > round(args.fade * FPS)):
            parser.error("each image must have at least one frame outside the fade")
        ffmpeg = shutil.which(args.ffmpeg)
        if not ffmpeg:
            parser.error("FFmpeg is required for MP4")
    elif len(args.images) != 1:
        parser.error("a still wallpaper requires one image")

    with tempfile.TemporaryDirectory(prefix="wallpaper-") as scratch:
        temp = Path(scratch)
        rendered = temp / ("wallpaper" + extension)
        if extension == ".mp4":
            frames = []
            for index, path in enumerate(args.images):
                frame = temp / f"photo-{index:04}.jpg"
                fit_image(path, args.size, args.center).save(frame, quality=96, subsampling=0)
                frames.append(frame)
            encode(frames, rendered, args.seconds, args.fade, ffmpeg)
        else:
            image = fit_image(args.images[0], args.size, args.center)
            if extension == ".png":
                image.save(rendered)
            else:
                image.save(rendered, quality=96, subsampling=0)
        deliver(rendered, args.output)


if __name__ == "__main__":
    main()
