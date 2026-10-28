#!/usr/bin/env python3
"""ネット裏から撮りっぱなしの試合動画を、投球の場面だけにつなぐ道具（BASS入力用）。

手本は、台湾U23の日本遠征の動画など、すでにカットされて届く映像の切り方。
1球ごとに「打者が構えて投手が動き出すころ」から「捕って3秒ほど」まで残し、
打球が飛んだ球はカメラが追い終わるまで残す。投球と投球の間、イニング間の投球練習は落とす。

    python3 apps/pitch-cut/pitch_cut.py 動画.mp4                 # 全部（下ごしらえ→区切り→書き出し）
    python3 apps/pitch-cut/pitch_cut.py 動画.mp4 --out 出力.mp4
    python3 apps/pitch-cut/pitch_cut.py 動画.mp4 --no-voice      # 記録係の声（打者紹介・交代）を足さない

投球の見つけ方は、球審と捕手がしゃがむ時間（人物検出の枠が横長になる）。投球のたびに球審はしゃがみ、
投げ終わると立つので、しゃがみの終わりを投球とみなす。打者がいない時間のしゃがみ（イニング間の投球練習）は外す。
記録係の声は whisper で文字にして、「〇番」「代わり」「攻撃」などを含む行だけ数秒残す。

途中のファイル（人物検出の結果・文字起こし・区切りの一覧）は ~/.cache/pitch-cut/<動画名>/ に置く。
二度目からはそこを読むので、区切りの決まりを変えたときは書き出しだけやり直せる。
"""

from __future__ import annotations

import argparse
import bisect
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

YOLO_WEIGHTS = Path.home() / "野球" / "batting_analysis" / "yolo11n.pt"
WHISPER_MODEL = Path.home() / ".cache" / "whisper" / "ggml-large-v3-turbo.bin"
CACHE = Path.home() / ".cache" / "pitch-cut"
W, H = 960, 540
FPS = 4  # 人物検出のコマ数（1秒あたり）

# 区切りの決まり（台湾の動画で測った切り方と、日本通運ー新日鐵住金鹿島戦で目で確かめた値）
CROUCH = 0.62     # 枠の横幅÷高さがこれを超えたら「しゃがみ」
MIN_RUN = 0.75    # これより短いしゃがみは数えない（秒）
JOIN = 0.5        # しゃがみの途切れをつなぐ幅（秒）
SAME_PITCH = 2.0  # しゃがみ同士の間がこれより短ければ同じ投球
PRE = 1.5         # しゃがみ始めの何秒前から残すか
POST = 3.0        # 球審が立ってから何秒残すか
IN_PLAY_MAX = 30.0
BATTER = 0.25     # しゃがみの間に打者が映っているコマの割合がこれ未満なら投球練習とみなす（投球練習は0.17以下）
MERGE = 1.5       # 残す場面同士の間がこれより短ければ1つにつなぐ
# 残す声: 打者紹介・交代・攻守交代と、打席の結果（カメラが打球を追わず、結果が声でしか分からない打席がある）
VOICE = re.compile(r"[0-9一二三四五六七八九]番|代わり|交代|代打|代走|守ります|攻撃"
                   r"|フライ|ゴロ|ライナー|三振|ヒット|安打|アウト|ホームラン|四球|フォアボール|デッドボール|死球|エラー"
                   r"|犠打|犠飛|バント|併殺|ゲッツー|点追加|得点")
# 記録係の1球ごとの読み上げ（「4-1ボール」「2-7打ってショートゴロ」）。聞き違いの「スライト」「ボル」も拾う
CALL = re.compile(r"\d\s*[-ー−の]\s*\d|ボール|ボル|ストライク|スト?ライ|スライト|ファウル|ファール|空振り|から振り|見逃し|打って"
                  r"|ゴロ|フライ|ヒット|ライナー|三振|バント|牽制|けん制|デッド|パスボール|ワイルド")
HALLUCINATION = re.compile(r"ご視聴|お疲れ|おやすみ|次回予告|次の動画|ありがとう")


# ---------------------------------------------------------------- 下ごしらえ


def work_dir(video: Path) -> Path:
    path = CACHE / video.stem
    path.mkdir(parents=True, exist_ok=True)
    return path


def scan(video: Path, out: Path) -> None:
    """人物の枠（YOLO）と、コマ間の動きの大きさ（カメラが振られたか）を1秒4コマで記録する。"""
    from ultralytics import YOLO

    model = YOLO(str(YOLO_WEIGHTS))
    cmd = ["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps={FPS},scale={W}:{H}",
           "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 3 * 8)
    boxes, motion, prev, buf, t0 = [], [], None, [], time.time()

    def flush() -> None:
        for r in model.predict(buf, classes=[0], conf=0.2, verbose=False, imgsz=640, device="mps"):
            b = r.boxes
            boxes.append(np.c_[b.xyxy.cpu().numpy(), b.conf.cpu().numpy()].round(1).tolist())
        buf.clear()

    while True:
        raw = proc.stdout.read(W * H * 3)
        if len(raw) < W * H * 3:
            break
        frame = np.frombuffer(raw, np.uint8).reshape(H, W, 3)
        small = frame[::6, ::6].mean(axis=2).astype(np.float32)
        motion.append(0.0 if prev is None else float(np.abs(small - prev).mean()))
        prev = small
        buf.append(frame.copy())
        if len(buf) == 16:
            flush()
            if len(motion) % 4000 == 0:
                print(f"  人物検出 {len(motion) / FPS / 60:.0f}分まで（{time.time() - t0:.0f}秒）", flush=True)
    if buf:
        flush()
    np.savez_compressed(out, t=np.arange(len(motion)) / FPS, motion=np.array(motion),
                        boxes=np.array(json.dumps(boxes)))


def transcribe(video: Path, out: Path) -> None:
    """記録係の声を文字にする（whisper-cli）。音声は使い終わったら消す。"""
    wav = out.with_suffix(".wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(wav)], check=True)
    prompt = "1番、センター、田中。ピッチャー、キャッチャー、ファースト、セカンド、サード、ショート、レフト、ライト、指名打者、代打。"
    subprocess.run(["whisper-cli", "-m", str(WHISPER_MODEL), "-l", "ja", "-mc", "0", "-bs", "5", "-np",
                    "--prompt", prompt, "-f", str(wav), "-oj", "-of", str(out.with_suffix(""))],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    wav.unlink()


# ---------------------------------------------------------------- 区切り


def frame_features(boxes: list) -> tuple[float, int, float]:
    """しゃがみ度（中央付近の大きな枠の横幅÷高さの最大）、大きな枠の数、いちばん高い枠の高さ（画面比）。"""
    tall = [(x1, y1, x2, y2) for x1, y1, x2, y2, _ in boxes
            if (y2 - y1) >= 0.3 * H and 0.12 * W < (x1 + x2) / 2 < 0.88 * W]
    crouch = max(((x2 - x1) / (y2 - y1) for x1, y1, x2, y2 in tall), default=0.0)
    top = max(((y2 - y1) for x1, y1, x2, y2 in tall), default=0.0) / H
    return crouch, len(tall), top


def crouch_runs(t, crouch, n_tall, top) -> list[tuple[float, float]]:
    """球審（と捕手）がしゃがんでいる時間。打者がいない時間のもの（投球練習）は外す。"""
    on = (crouch > CROUCH) & (top >= 0.33)
    runs, i, n = [], 0, len(t)
    while i < n:
        if not on[i]:
            i += 1
            continue
        j = i
        while j + 1 < n:
            if on[j + 1]:
                j += 1
                continue
            k = j + 1
            while k < n and not on[k] and t[k] - t[j] <= JOIN + 1e-6:
                k += 1
            if k < n and on[k] and t[k] - t[j] <= JOIN + 1e-6:
                j = k
                continue
            break
        if t[j] - t[i] >= MIN_RUN and np.mean(n_tall[i:j + 1] >= 2) >= BATTER:
            runs.append((float(t[i]), float(t[j])))
        i = j + 1
    joined: list[list[float]] = []
    for a, e in runs:
        if joined and a - joined[-1][1] < SAME_PITCH:
            joined[-1][1] = e
        else:
            joined.append([a, e])
    return [(a, e) for a, e in joined]


def play_end(t, motion, top, end: float, next_start: float) -> float:
    """投球のあとカメラが打球を追ったら、本塁付近に戻って落ち着くまで残す。
    外野を映したまま止まった所で切ると、走者が還る場面が落ちる（日本通運戦の犠牲フライ）。
    ホームランのように、撮影者が打球を見送ってから数秒後にカメラを振ることもあるので、
    3〜8秒後でも1.5秒続けて大きく振れたら打球とみなす（日本通運戦3回裏の穴水のホームランは6秒後）。"""
    soon = np.where((t > end) & (t <= end + 3.0) & (motion > 15))[0]
    late = [k for k in np.where((t > end + 3.0) & (t <= end + 8.0))[0] if np.all(motion[k:k + 6] > 15)]
    if not len(soon) and not late:
        return end + POST
    k, quiet = int(soon[0] if len(soon) else late[0]), 0  # 落ち着いたかはカメラが振れ始めてから数える
    limit = min(end + IN_PLAY_MAX, next_start - 1.0)
    while k < len(t) and t[k] < limit:
        quiet = quiet + 1 if motion[k] < 8 and top[k] >= 0.35 else 0
        if quiet >= 8:
            return max(float(t[k]), end + POST)
        k += 1
    return max(limit, end + POST)


def voice_lines(words: Path) -> list[list]:
    lines, prev = [], None
    for s in json.loads(words.read_text(encoding="utf-8"))["transcription"]:
        text = s["text"].strip()
        if text != prev and VOICE.search(text):
            a = s["offsets"]["from"] / 1000
            lines.append([a - 1.0, min(s["offsets"]["to"] / 1000, a + 5.0) + 1.0, "声:" + text])
        prev = text
    return lines


def segment(scan_file: Path, words: Path | None, extra: Path | None = None) -> list[list]:
    z = np.load(scan_file)
    t, motion = z["t"], z["motion"]
    feats = np.array([frame_features(b) for b in json.loads(str(z["boxes"]))])
    runs = crouch_runs(t, feats[:, 0], feats[:, 1], feats[:, 2])
    parts = []
    for i, (a, e) in enumerate(runs):
        nxt = runs[i + 1][0] if i + 1 < len(runs) else float(t[-1])
        parts.append([a - PRE, play_end(t, motion, feats[:, 2], e, nxt), "投球"])
    if words is not None:
        parts += voice_lines(words)
    if extra is not None and extra.is_file():
        # 目で見つけた取りこぼしを手で足す: [[始まり, 終わり, "メモ"], ...]（元の動画の秒）
        parts += [[a, b, "手で追加:" + note] for a, b, note in json.loads(extra.read_text(encoding="utf-8"))]
    merged: list[list] = []
    for a, b, why in sorted(parts):
        a = max(0.0, a)
        if merged and a - merged[-1][1] < MERGE:
            merged[-1][1] = max(merged[-1][1], b)
            merged[-1][2].append(why)
        else:
            merged.append([a, b, [why]])
    return [[round(a, 2), round(b, 2), why] for a, b, why in merged]


# ---------------------------------------------------------------- 取りこぼしの確認


def check(video: Path, segs: list[list], folder: Path) -> list[str]:
    """切り落とした側の音声だけを文字にして、記録係の投球の読み上げが残っていないか探す。

    読み上げは投球の数秒後に来るので、切り落とし側の頭の数秒に出るのはたいてい直前の球のはみ出し。
    それより後ろに出たものは、その前後の元の動画を目で見て、抜けていれば 追加.json に足す。
    文字起こしの時刻は30秒の窓の単位で粗く、10秒ほど早く出ることがある。
    """
    import soundfile as sf

    full = folder / "音声.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(full)], check=True)
    y, sr = sf.read(full, dtype="float32")
    full.unlink()
    gaps, prev = [], 0.0
    for a, b, _ in segs:
        if a - prev >= 1.0:
            gaps.append((prev, a))
        prev = max(prev, b)
    if len(y) / sr - prev >= 1.0:
        gaps.append((prev, len(y) / sr))
    gap_sil = np.zeros(3 * sr, np.float32)  # 切れ目に3秒の無音を挟み、文字起こしの区切りを切れ目にそろえやすくする
    pieces, table, pos = [], [], 0.0
    for a, b in gaps:
        piece = y[int(a * sr):int(b * sr)]
        table.append((pos, a, b))
        pieces += [piece, gap_sil]
        pos += len(piece) / sr + 3.0
    cut = folder / "切り落とし.wav"
    sf.write(cut, np.concatenate(pieces), sr)
    prompt = "4-1ボール。4-0ストライク。2-7打って、ショートゴロ。1-1見逃しストライク。3-2ファウル。空振り三振。デッドボール。"
    subprocess.run(["whisper-cli", "-m", str(WHISPER_MODEL), "-l", "ja", "-mc", "0", "-bs", "5", "-np", "-ml", "20", "-sow",
                    "--prompt", prompt, "-f", str(cut), "-oj", "-of", str(folder / "切り落とし")],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    cut.unlink()
    found, prev_text = [], None
    starts = [p for p, _, _ in table]
    for s in json.loads((folder / "切り落とし.json").read_text(encoding="utf-8"))["transcription"]:
        text = s["text"].strip()
        if not text or text == prev_text or HALLUCINATION.search(text) or not CALL.search(text):
            prev_text = text
            continue
        prev_text = text
        at = s["offsets"]["from"] / 1000
        p, a, b = table[max(0, bisect.bisect_right(starts, at) - 1)]
        into = at - p
        if into <= b - a + 0.5:
            found.append(f"{a + into:8.1f}秒（{fmt(a + into)}）  切り落とし {fmt(a)}〜{fmt(b)} の {into:.0f}秒目  {text}")
    (folder / "確認.txt").write_text("\n".join(found) + "\n", encoding="utf-8")
    return found


def fmt(sec: float) -> str:
    return f"{int(sec // 3600)}:{int(sec % 3600 // 60):02d}:{int(sec % 60):02d}"


# ---------------------------------------------------------------- 書き出し


def render(video: Path, segs: list[list], out: Path, folder: Path, workers: int = 4) -> None:
    """場面ごとに書き出して（.ts）、最後に1本へつなぐ。select の式に数百の場面を並べると ffmpeg が受け付けない。"""
    from concurrent.futures import ThreadPoolExecutor

    parts = folder / "場面"
    if parts.exists():
        for old in parts.glob("*.ts"):
            old.unlink()
    parts.mkdir(exist_ok=True)

    def one(i: int) -> Path:
        a, b, _ = segs[i]
        ts = parts / f"{i:04d}.ts"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-i", str(video), "-t", f"{b - a:.3f}",
                        "-c:v", "h264_videotoolbox", "-b:v", "2000k", "-c:a", "aac", "-b:a", "128k",
                        "-f", "mpegts", str(ts)], check=True)
        return ts

    with ThreadPoolExecutor(workers) as pool:
        files = list(pool.map(one, range(len(segs))))
    listing = folder / "場面.txt"
    listing.write_text("".join(f"file '{f}'\n" for f in files), encoding="utf-8")
    tmp = out.with_name(out.stem + ".part.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-c", "copy", "-bsf:a", "aac_adtstoasc", "-movflags", "+faststart", str(tmp)], check=True)
    tmp.replace(out)
    for f in files:
        f.unlink()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--no-voice", action="store_true", help="記録係の声（打者紹介・交代）を足さない")
    ap.add_argument("--check", action="store_true",
                    help="書き出しの代わりに、切り落とした側の音声から投球の読み上げを探して 確認.txt に書く（1時間の動画で約15分）")
    args = ap.parse_args()
    video = args.video.expanduser().resolve()
    out = args.out or video.with_name(video.stem + "_投球カット.mp4")
    folder = work_dir(video)

    scan_file = folder / "人物検出.npz"
    if not scan_file.is_file():
        print("人物検出（全編、1時間の動画で約6分）")
        scan(video, folder / "人物検出.part.npz")
        (folder / "人物検出.part.npz").replace(scan_file)
    words = None
    if not args.no_voice:
        words = folder / "声.json"
        if not words.is_file():
            print("記録係の声の文字起こし（whisper）")
            transcribe(video, words)
    segs = segment(scan_file, words, folder / "追加.json")
    (folder / "区切り.json").write_text(json.dumps(segs, ensure_ascii=False, indent=0), encoding="utf-8")
    pitches = sum(1 for s in segs for w in s[2] if w == "投球")
    kept = sum(b - a for a, b, _ in segs)
    total = float(np.load(scan_file)["t"][-1])
    print(f"投球の候補 {pitches}、残す場面 {len(segs)} → {kept / 60:.0f}分（元 {total / 60:.0f}分）")
    if args.check:
        found = check(video, segs, folder)
        print(f"切り落とした側の読み上げ {len(found)}件 → {folder / '確認.txt'}")
        print("\n".join(found))
        return
    render(video, segs, out, folder)
    print(f"書き出し → {out}")


if __name__ == "__main__":
    sys.exit(main())
