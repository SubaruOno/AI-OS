#!/usr/bin/env python3
"""GameTime（WBSCの大会配信）の見逃し映像を1本のmp4に保存する道具。

GameTime の映像は Cloudflare Stream の HLS（2秒ずつの fMP4）で、再生リストに
EXT-X-DEFINE の置き換えが入るため ffmpeg では直接読めない。ここで置き換えて
小さな映像を並列で落とし、つないで音と合わせる。

再生リストの住所は、すばるのパスでログインしたページが読む `.../manifest` までを
ファイルに書いて渡す（住所には期限付きの鍵が入るので、リポジトリには入れない）。

    python3 gametime_dl.py <manifestまでの住所のファイル> <出力.mp4> [--res 1280x720] [--from 秒] [--to 秒]

映像は規約上チームの中だけで使う。保存先は ~/野球/U23ワールドカップ2026/04_対戦国/<国>/大会2026_映像/収録/。
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"


def get(url: str, tries: int = 6) -> bytes:
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://gametime.sport/"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            if i == tries - 1:
                raise
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(url)


def parse_playlist(url: str) -> tuple[str, list[tuple[float, str]]]:
    """(init の住所, [(長さ, 小さな映像の住所)]) を返す。EXT-X-DEFINE を置き換える。"""
    text = get(url).decode()
    defs = dict(re.findall(r'#EXT-X-DEFINE:NAME="([^"]+)",VALUE="([^"]*)"', text))

    def sub(s: str) -> str:
        return re.sub(r"\{\$([A-Za-z0-9_-]+)\}", lambda m: defs[m.group(1)], s)

    init = sub(re.search(r'#EXT-X-MAP:URI="([^"]+)"', text).group(1))
    segs, dur = [], None
    for line in text.splitlines():
        if line.startswith("#EXTINF:"):
            dur = float(line[8:].split(",")[0])
        elif line and not line.startswith("#"):
            segs.append((dur or 0.0, urllib.parse.urljoin(url, sub(line))))
            dur = None
    return urllib.parse.urljoin(url, init), segs


def fetch_track(url: str, out: Path, t0: float, t1: float | None, label: str) -> None:
    init, segs = parse_playlist(url)
    pos, pick = 0.0, []
    for d, u in segs:
        if pos + d > t0 and (t1 is None or pos < t1):
            pick.append(u)
        pos += d
    print(f"{label}: {len(pick)}/{len(segs)} 個（全体 {pos:.0f} 秒）", flush=True)
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)

        def one(i_u):
            i, u = i_u
            p = tdp / f"{i:06d}.m4s"
            p.write_bytes(get(u))
            return i

        done = 0
        with ThreadPoolExecutor(16) as ex:
            for _ in ex.map(one, enumerate(pick)):
                done += 1
                if done % 500 == 0:
                    print(f"  {label} {done}/{len(pick)}", flush=True)
        with open(out, "wb") as f:
            f.write(get(init))
            for i in range(len(pick)):
                f.write((tdp / f"{i:06d}.m4s").read_bytes())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("base_file")
    ap.add_argument("out")
    ap.add_argument("--res", default="1280x720")
    ap.add_argument("--from", dest="t0", type=float, default=0.0)
    ap.add_argument("--to", dest="t1", type=float, default=None)
    a = ap.parse_args()
    base = Path(a.base_file).read_text().strip().rstrip("/")
    master_url = f"{base}/video.m3u8?dvrEnabled=true"
    master = get(master_url).decode()
    lines = master.splitlines()
    vurl = None
    for i, l in enumerate(lines):
        if l.startswith("#EXT-X-STREAM-INF") and f"RESOLUTION={a.res}" in l:
            vurl = urllib.parse.urljoin(master_url, lines[i + 1])
    m = re.search(r'#EXT-X-MEDIA:TYPE=AUDIO[^\n]*URI="([^"]+)"', master)
    if not vurl:
        sys.exit(f"{a.res} の映像がない")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    v = out.with_suffix(".video.mp4")
    au = out.with_suffix(".audio.mp4")
    fetch_track(vurl, v, a.t0, a.t1, "映像")
    if m:
        fetch_track(urllib.parse.urljoin(master_url, m.group(1)), au, a.t0, a.t1, "音")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(v), "-i", str(au), "-map", "0:v", "-map", "1:a",
                        "-c", "copy", "-movflags", "+faststart", str(out)], check=True)
        au.unlink()
    else:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(v), "-c", "copy", "-movflags", "+faststart", str(out)], check=True)
    v.unlink()
    print("書き出し:", out, flush=True)


if __name__ == "__main__":
    main()
