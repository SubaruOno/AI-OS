#!/usr/bin/env python3
"""
Extract key frames from a video at regular intervals using ffmpeg.

Usage:
    python3 extract-frames.py --video <path> --output-dir <path>
    python3 extract-frames.py --video <path> --output-dir <path> --interval 8 --max-frames 24

Outputs:
    <output-dir>/frame_0001.jpg
    <output-dir>/frame_0002.jpg
    ...
    <output-dir>/frame-index.json   (list of {frame_number, timestamp_seconds, path})

Exit codes:
    0 = success
    1 = ffmpeg failed or video not found
    2 = ffmpeg not installed
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def check_ffmpeg() -> None:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except FileNotFoundError:
        print("ERROR: ffmpeg is not installed. Run: brew install ffmpeg", file=sys.stderr)
        sys.exit(2)
    except subprocess.CalledProcessError:
        print("ERROR: ffmpeg check failed", file=sys.stderr)
        sys.exit(2)


def get_duration(video_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "json",
            str(video_path)
        ],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"ERROR: Could not probe video: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def extract_frames(
    video_path: Path,
    output_dir: Path,
    interval_seconds: int = 8,
    max_frames: int = 24,
    quality: int = 4
) -> list:
    output_dir.mkdir(parents=True, exist_ok=True)
    duration = get_duration(video_path)

    # Compute actual interval so we don't exceed max_frames
    n_frames_at_interval = int(duration / interval_seconds)
    if n_frames_at_interval > max_frames:
        interval_seconds = int(duration / max_frames)
        print(f"Adjusted interval to {interval_seconds}s to stay within {max_frames} frames")

    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", f"fps=1/{interval_seconds}",
            "-q:v", str(quality),
            str(output_dir / "frame_%04d.jpg")
        ],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"ERROR: ffmpeg failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    frames = sorted(output_dir.glob("frame_*.jpg"))
    frame_index = []
    for i, frame_path in enumerate(frames):
        timestamp = i * interval_seconds
        frame_index.append({
            "frame_number": i + 1,
            "timestamp_seconds": timestamp,
            "path": str(frame_path)
        })

    (output_dir / "frame-index.json").write_text(json.dumps(frame_index, indent=2))
    print(f"Extracted {len(frames)} frames from {duration:.0f}s video (1 frame every {interval_seconds}s)")
    return frame_index


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract key frames from a video")
    parser.add_argument("--video", required=True, help="Path to video file")
    parser.add_argument("--output-dir", required=True, help="Directory to save frames")
    parser.add_argument("--interval", type=int, default=8, help="Seconds between frames (default: 8)")
    parser.add_argument("--max-frames", type=int, default=24, help="Maximum frames to extract (default: 24)")
    parser.add_argument("--quality", type=int, default=4, help="JPEG quality 2-5, 2=best (default: 4)")
    args = parser.parse_args()

    check_ffmpeg()
    video_path = Path(args.video)
    if not video_path.exists():
        print(f"ERROR: Video file not found: {video_path}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir)
    frame_index = extract_frames(
        video_path, output_dir,
        interval_seconds=args.interval,
        max_frames=args.max_frames,
        quality=args.quality
    )

    print(json.dumps({
        "success": True,
        "frames_extracted": len(frame_index),
        "output_dir": str(output_dir),
        "frame_index_path": str(output_dir / "frame-index.json")
    }))


if __name__ == "__main__":
    main()
