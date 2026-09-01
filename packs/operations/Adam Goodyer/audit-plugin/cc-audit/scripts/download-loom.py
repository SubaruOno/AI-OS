#!/usr/bin/env python3
"""
Download a Loom video and its transcript/subtitles via yt-dlp.

Usage:
    python3 download-loom.py --url <loom-share-url> --output-dir <path>
    python3 download-loom.py --url <loom-share-url> --output-dir <path> --no-video

Outputs:
    <output-dir>/video.mp4          (unless --no-video)
    <output-dir>/transcript.vtt     (VTT subtitles if available)
    <output-dir>/metadata.json      (title, duration, url)

Exit codes:
    0 = success
    1 = download failed
    2 = yt-dlp not installed
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def check_ytdlp() -> None:
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
    except FileNotFoundError:
        print("ERROR: yt-dlp is not installed. Run: pip install yt-dlp", file=sys.stderr)
        sys.exit(2)
    except subprocess.CalledProcessError:
        print("ERROR: yt-dlp check failed", file=sys.stderr)
        sys.exit(2)


def download_loom(url: str, output_dir: Path, download_video: bool = True) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Fetch metadata first
    meta_result = subprocess.run(
        ["yt-dlp", "--dump-json", "--no-playlist", url],
        capture_output=True,
        text=True
    )
    if meta_result.returncode != 0:
        print(f"ERROR: Failed to fetch Loom metadata: {meta_result.stderr}", file=sys.stderr)
        sys.exit(1)

    meta = json.loads(meta_result.stdout)
    duration = meta.get("duration")
    title = meta.get("title", "Untitled")

    metadata = {
        "url": url,
        "title": title,
        "duration_seconds": duration,
        "loom_id": meta.get("id"),
        "uploader": meta.get("uploader"),
        "upload_date": meta.get("upload_date")
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    print(f"Metadata saved: {title} ({duration}s)")

    # Download VTT subtitles (transcript)
    sub_result = subprocess.run(
        [
            "yt-dlp",
            "--write-subs",
            "--sub-langs", "en.*",
            "--skip-download",
            "--output", str(output_dir / "transcript"),
            "--no-playlist",
            url
        ],
        capture_output=True,
        text=True
    )
    vtt_files = list(output_dir.glob("transcript*.vtt"))
    if vtt_files:
        vtt_files[0].rename(output_dir / "transcript.vtt")
        print(f"VTT subtitles saved: transcript.vtt")
    else:
        print("Note: No VTT subtitles found — will need DeepGram transcription instead")

    # Download video
    if download_video:
        video_result = subprocess.run(
            [
                "yt-dlp",
                "--format", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "--output", str(output_dir / "video.%(ext)s"),
                "--no-playlist",
                url
            ],
            capture_output=True,
            text=True
        )
        if video_result.returncode != 0:
            print(f"WARNING: Video download failed: {video_result.stderr}", file=sys.stderr)
        else:
            mp4_files = list(output_dir.glob("video.mp4"))
            if mp4_files:
                print(f"Video saved: video.mp4")
            else:
                # Try any extension that was downloaded
                video_files = [f for f in output_dir.iterdir() if f.stem == "video"]
                if video_files:
                    print(f"Video saved: {video_files[0].name}")

    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Download a Loom video and subtitles")
    parser.add_argument("--url", required=True, help="Loom share URL")
    parser.add_argument("--output-dir", required=True, help="Directory to save files")
    parser.add_argument("--no-video", action="store_true", help="Skip video download, subtitles only")
    args = parser.parse_args()

    check_ytdlp()
    output_dir = Path(args.output_dir)
    metadata = download_loom(args.url, output_dir, download_video=not args.no_video)

    print(json.dumps({
        "success": True,
        "output_dir": str(output_dir),
        "title": metadata["title"],
        "duration_seconds": metadata["duration_seconds"],
        "video_path": str(output_dir / "video.mp4") if not args.no_video else None,
        "vtt_path": str(output_dir / "transcript.vtt") if (output_dir / "transcript.vtt").exists() else None
    }))


if __name__ == "__main__":
    main()
