#!/usr/bin/env python3
"""スタッフ共有サイトの使い方動画（3本）を、撮った画面から組み立てる。

    python3 howto_video.py            # 3本とも作る
    python3 howto_video.py --only 3   # 3本目だけ
    python3 howto_video.py --still 3  # 3本目の各場面の静止画だけ（確かめ用）

画面は日本語のiPhoneシミュレーター（U23 使い方動画）で撮った 1206x2622 のPNGで、
~/野球/U23ワールドカップ2026/07_サイト/使い方動画/下書き/画面/ にある（録画は 下書き/録画/）。
出来上がりは 使い方動画/ に置く。縦長 1080x1920・30コマ/秒・声なし（無音の音声を入れる）。

1つの場面は、画面の一部を窓のように切り出して大きく見せ、押す場所や見てほしい所に赤い枠を付け、
下に字幕を出す。窓は場面のあいだに少しずつ寄る。合言葉の入ったアドレスは、元の画面でぼかしてから使う。
"""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path.home() / "野球" / "U23ワールドカップ2026" / "07_サイト" / "使い方動画"
SHOTS = ROOT / "下書き" / "画面"
RECS = ROOT / "下書き" / "録画"
W, H, FPS = 1080, 1920, 30
NAVY, RED, INK = (11, 17, 32), (208, 16, 58), (20, 24, 32)
FONT = "/System/Library/Fonts/ヒラギノ角ゴシック W{}.ttc"
SRC_W, SRC_H = 1206, 2622
WIN = (60, 150, 1020, 1500)  # 画面の窓（キャンバス上）
CAP = (40, 1540, 1040, 1880)  # 字幕の札
FADE = 8  # 場面のつなぎ（コマ）

# 場面: kind は shot（画面）・card（文字だけ）・clip（録画）。
#   box は赤い枠（元の画面の座標）、shape は rect か circle、blur はぼかす所、focus_y は枠がないときの窓の中心の高さ
VIDEOS = {
    1: {
        "file": "U23サイトの使い方1_はじめの設定.mp4",
        "label": "① はじめの設定",
        "scenes": [
            {"kind": "card", "text": "U-23W杯\nスタッフ共有サイト", "big": "① はじめの設定", "sub": "最初に1回だけ。ホテルのWi-Fiなど電波のよい所で", "sec": 3.5},
            {"kind": "card", "text": "LINEで届いたリンクは\nSafariで開き直してください", "sub": "LINEの中で開くと、保存が効かないことがあります", "sec": 4.5},
            {"kind": "shot", "img": "1-01_safari_top", "cap": "Safariで開いたら\n右下の「…」を押します", "box": (960, 2378, 1104, 2518), "shape": "circle",
             "blur": [(269, 2379, 937, 2517)]},
            {"kind": "shot", "img": "1-01b_menu", "cap": "「共有」を押します", "box": (433, 612, 1052, 710)},
            {"kind": "shot", "img": "1-02_share", "cap": "「表示を増やす」を押します", "box": (900, 2235, 1100, 2430), "shape": "circle",
             "blur": [(330, 1560, 520, 1618)]},
            {"kind": "shot", "img": "1-03_more", "cap": "「ホーム画面に追加」を押します", "box": (52, 1847, 1153, 1991),
             "blur": [(315, 332, 500, 386)]},
            {"kind": "shot", "img": "1-04_add", "cap": "右上の「追加」を押します", "box": (960, 240, 1160, 420), "shape": "circle",
             "blur": [(262, 642, 1179, 747)]},
            {"kind": "shot", "img": "1-05_home", "cap": "ホーム画面にアイコンができました\n次からはここから開きます", "box": (610, 530, 875, 830), "shape": "circle"},
            {"kind": "shot", "img": "1-06_app_top", "cap": "アイコンから開くと\nアドレス欄のない全画面で開きます", "focus_y": 900},
            {"kind": "shot", "img": "1-07_save_button", "cap": "トップの一番下の\n「全ページを端末に保存」を押します", "box": (80, 1270, 780, 1430)},
            {"kind": "shot", "img": "1-09_saved", "cap": "「保存しました」と出たら完了\n電波がなくても開けます", "box": (80, 1425, 660, 1500)},
            {"kind": "card", "text": "次は", "big": "② ページの見方", "sec": 2.5},
        ],
    },
    2: {
        "file": "U23サイトの使い方2_ページの見方.mp4",
        "label": "② ページの見方",
        "scenes": [
            {"kind": "card", "text": "U-23W杯\nスタッフ共有サイト", "big": "② ページの見方", "sub": "どこに何があるか", "sec": 3.0},
            {"kind": "shot", "img": "2-01_top", "cap": "トップには、次の日本戦まで\nあと何日かが出ます", "box": (300, 596, 505, 662)},
            {"kind": "shot", "img": "2-02_today_standings", "cap": "下には今日の試合と順位表\n日本の組（グループB）が先です", "box": (48, 1310, 1157, 2181)},
            {"kind": "shot", "img": "2-01_top", "cap": "上の帯は、最後に更新した時刻と\nどの試合まで結果が入ったか", "box": (8, 352, 1198, 462)},
            {"kind": "shot", "img": "2-01_top", "cap": "行き先は上の4つ\n日本・相手国・日程・大会方式", "box": (550, 216, 1185, 301)},
            {"kind": "shot", "img": "2-03_schedule", "cap": "日程：日付を押すとその日へ\n時刻は日本時間（下に現地）", "box": (40, 900, 1166, 1340)},
            {"kind": "shot", "img": "2-04_teams", "cap": "相手国：11チーム\n日本の組が先、対戦順です", "focus_y": 1100},
            {"kind": "shot", "img": "2-05_country", "cap": "国のページ：世界ランク・名簿・監督\n下に注目選手や日本との対戦", "box": (48, 845, 1157, 1094)},
            {"kind": "shot", "img": "2-06_japan", "cap": "日本：24人と首脳陣\n日本戦の日程", "focus_y": 1000},
            {"kind": "shot", "img": "2-07_format", "cap": "大会方式：スーパーラウンドと\n持ち越し、日本の順位ごとの相手", "focus_y": 1000},
            {"kind": "shot", "img": "2-08_offline", "cap": "電波が弱いときは、保存した内容を出し\n黄色の帯で知らせます", "box": (0, 334, 1206, 478)},
            {"kind": "card", "text": "次は", "big": "③ 台湾の映像ページ", "sec": 2.5},
        ],
    },
    3: {
        "file": "U23サイトの使い方3_台湾の映像ページ.mp4",
        "label": "③ 台湾の映像ページ",
        "scenes": [
            {"kind": "card", "text": "U-23W杯\nスタッフ共有サイト", "big": "③ 台湾の映像ページ", "sub": "日本遠征の打席を、選手ごとに", "sec": 3.0},
            {"kind": "shot", "img": "3-01_tpe_card", "cap": "「相手国」から\n「チャイニーズタイペイ」を開きます", "box": (616, 1565, 1155, 2155)},
            {"kind": "shot", "img": "3-02_video_section", "cap": "「日本遠征の打席の映像」で\n選手を選びます", "box": (46, 589, 600, 655)},
            {"kind": "shot", "img": "3-03_player", "cap": "打席ごとの動画です\n見出しは回と結果", "box": (80, 1527, 480, 1600)},
            {"kind": "shot", "img": "3-04_before5", "cap": "下のボタンは1球ごと\n「5球目」を押すと…", "box": (81, 1892, 367, 2023),
             "blur": [(470, 2480, 736, 2584)]},
            {"kind": "clip", "rec": "3-chip5.mp4", "from": 0.6, "to": 7.2, "cap": "その球の投げる前から\n流れます", "focus_y": 1500,
             "tap": (224, 1957, 1.6), "blur": [(470, 2480, 736, 2584)]},
            {"kind": "shot", "img": "3-03_player", "cap": "灰色の点線のボタンは、映像の時刻が\n分からない球（打席の動画には入っています）", "box": (934, 2282, 1086, 2412)},
            {"kind": "shot", "img": "3-05_filter", "cap": "上のボタンで、安打・凡打・\n三振と四死球に絞れます", "box": (275, 1218, 441, 1343)},
            {"kind": "card", "text": "動画は端末に保存されません", "sub": "見るときは電波のある所で", "sec": 3.5},
            {"kind": "card", "text": "サイトのリンクは\n外に回さないでください", "sec": 3.0},
        ],
    },
}


def font(weight: int, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT.format(weight), size)


def text_center(d: ImageDraw.ImageDraw, cx: float, y: float, text: str, f, fill, gap: int = 18) -> float:
    for line in text.split("\n"):
        w = d.textlength(line, font=f)
        d.text((cx - w / 2, y), line, font=f, fill=fill)
        y += f.size + gap
    return y


def scene_secs(sc: dict) -> float:
    if "sec" in sc:
        return sc["sec"]
    if sc["kind"] == "clip":
        return sc["to"] - sc["from"]
    return max(3.2, len(sc["cap"].replace("\n", "")) / 7.0 + 1.3)


def load_shot(sc: dict) -> Image.Image:
    return blurred(Image.open(SHOTS / f"{sc['img']}.png").convert("RGB"), sc)


def blurred(im: Image.Image, sc: dict) -> Image.Image:
    for box in sc.get("blur", []):
        im.paste(im.crop(box).filter(ImageFilter.GaussianBlur(30)), box[:2])
    return im


def window(sc: dict, t: float) -> tuple[float, float, float, float]:
    """元の画面のどこを窓に出すか。場面のあいだに8%寄る。"""
    ww, wh = WIN[2] - WIN[0], WIN[3] - WIN[1]
    zoom = 1.0 + 0.08 * min(1.0, t)
    w = SRC_W / zoom
    h = w * wh / ww
    if sc.get("box"):
        bx0, by0, bx1, by1 = sc["box"]
        cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
    else:
        cx, cy = SRC_W / 2, sc.get("focus_y", h / 2)
    cx = SRC_W / 2 + (cx - SRC_W / 2) * min(1.0, t)
    x0 = min(max(0.0, cx - w / 2), SRC_W - w)
    y0 = min(max(0.0, cy - h / 2), SRC_H - h)
    return x0, y0, x0 + w, y0 + h


def base_canvas(label: str, step: str) -> Image.Image:
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    d.ellipse((60, 52, 92, 84), fill="white")
    d.ellipse((66, 58, 86, 78), fill=RED)
    d.text((110, 46), f"サイトの使い方　{label}", font=font(6, 36), fill="white")
    sw = d.textlength(step, font=font(5, 32))
    d.text((W - 60 - sw, 50), step, font=font(5, 32), fill=(150, 160, 180))
    return im


def phone_mask() -> Image.Image:
    m = Image.new("L", (WIN[2] - WIN[0], WIN[3] - WIN[1]), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, m.width - 1, m.height - 1), radius=36, fill=255)
    return m


MASK = None


def draw_frame(label: str, step: str, sc: dict, src: Image.Image, t: float, life: float) -> Image.Image:
    """t は場面の中の割合（0〜1）、life は場面の頭からの秒。"""
    global MASK
    MASK = MASK or phone_mask()
    im = base_canvas(label, step)
    x0, y0, x1, y1 = window(sc, t)
    view = src.crop((round(x0), round(y0), round(x1), round(y1))).resize((WIN[2] - WIN[0], WIN[3] - WIN[1]), Image.BILINEAR)
    d = ImageDraw.Draw(view)
    sx = view.width / (x1 - x0)
    if sc.get("box") and life >= 0.35:
        bx0, by0, bx1, by1 = sc["box"]
        b = ((bx0 - x0) * sx, (by0 - y0) * sx, (bx1 - x0) * sx, (by1 - y0) * sx)
        pulse = (life * 1.6) % 1.0
        pad = 6 + 14 * pulse
        glow = tuple(int(c + (255 - c) * pulse) for c in RED)
        outer = (b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad)
        if sc.get("shape") == "circle":
            d.ellipse(outer, outline=glow, width=4)
            d.ellipse(b, outline=RED, width=10)
        else:
            d.rounded_rectangle(outer, radius=22, outline=glow, width=4)
            d.rounded_rectangle(b, radius=18, outline=RED, width=10)
    if sc.get("tap"):
        tx, ty, at = sc["tap"]
        if at - 0.4 <= life <= at + 0.6:
            k = (life - (at - 0.4)) / 1.0
            r = 40 + 60 * k
            cx, cy = (tx - x0) * sx, (ty - y0) * sx
            d.ellipse((cx - 38, cy - 38, cx + 38, cy + 38), fill=(255, 255, 255))
            d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=RED, width=8)
    im.paste(view, (WIN[0], WIN[1]), MASK)
    d2 = ImageDraw.Draw(im)
    d2.rounded_rectangle(CAP, radius=28, fill="white")
    f = font(6, 52 if max(len(s) for s in sc["cap"].split("\n")) <= 17 else 44)
    lines = sc["cap"].split("\n")
    y = (CAP[1] + CAP[3]) / 2 - (len(lines) * (f.size + 18) - 18) / 2 - 6
    text_center(d2, W / 2, y, sc["cap"], f, INK)
    return im


def draw_card(label: str, step: str, sc: dict) -> Image.Image:
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    if step:
        sw = d.textlength(step, font=font(5, 32))
        d.text((W - 60 - sw, 50), step, font=font(5, 32), fill=(150, 160, 180))
    blocks = [(sc["text"], font(6, 64), "white")]
    if sc.get("big"):
        blocks.append((sc["big"], font(8, 84), (255, 255, 255)))
    if sc.get("sub"):
        blocks.append((sc["sub"], font(4, 40), (190, 200, 215)))
    total = sum(len(t.split("\n")) * (f.size + 22) for t, f, _ in blocks) + 60 * (len(blocks) - 1)
    y = H / 2 - total / 2 - 40
    for i, (t, f, fill) in enumerate(blocks):
        if i and blocks[i][1].size == 84:
            d.rounded_rectangle((W / 2 - 60, y - 34, W / 2 + 60, y - 26), radius=4, fill=RED)
        y = text_center(d, W / 2, y, t, f, fill, gap=22) + 60
    return im


def clip_frames(sc: dict, tmp: Path) -> list[Path]:
    out = tmp / "clip"
    out.mkdir(exist_ok=True)
    # シミュレーターの録画は画面が変わったときだけコマがある。頭から一定のコマにしてから切る（先に飛ばすと、
    # 止まっていた所のコマが落ちて、押す前の場面が詰まる）
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(RECS / sc["rec"]), "-vf",
                    f"fps={FPS},trim=start={sc['from']:.2f}:end={sc['to']:.2f},setpts=PTS-STARTPTS",
                    str(out / "f_%04d.png")], check=True)
    return sorted(out.glob("f_*.png"))


def frames(no: int):
    v = VIDEOS[no]
    n = len(v["scenes"])
    for i, sc in enumerate(v["scenes"], 1):
        step = f"{i}/{n}"
        secs = scene_secs(sc)
        count = round(secs * FPS)
        if sc["kind"] == "card":
            still = draw_card(v["label"], "" if i == 1 else step, sc)
            for k in range(count):
                yield i, still
        elif sc["kind"] == "shot":
            src = load_shot(sc)
            for k in range(count):
                life = k / FPS
                yield i, draw_frame(v["label"], step, sc, src, min(1.0, life / max(1.0, secs - 0.5)), life)
        else:
            with tempfile.TemporaryDirectory() as tmp:
                paths = clip_frames(sc, Path(tmp))
                for k, p in enumerate(paths):
                    src = blurred(Image.open(p).convert("RGB"), sc)
                    yield i, draw_frame(v["label"], step, dict(sc, box=None), src, 1.0, k / FPS)


def build(no: int) -> Path:
    v = VIDEOS[no]
    out = ROOT / v["file"]
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-shortest",
           "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "32k",
           "-movflags", "+faststart", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    last, held, scene, since, total = None, None, 0, 0, 0
    for i, fr in frames(no):
        if i != scene:
            scene, since, held = i, 0, last
        if held is not None and since < FADE:
            fr = Image.blend(held, fr, (since + 1) / (FADE + 1))
        p.stdin.write(fr.tobytes())
        last, since, total = fr, since + 1, total + 1
    p.stdin.close()
    if p.wait() != 0:
        raise SystemExit(f"{out.name} の書き出しに失敗しました")
    print(f"{out.name}: {total / FPS:.1f}秒")
    return out


def stills(no: int, dest: Path) -> None:
    """各場面の真ん中のコマを1枚ずつ（確かめ用）。"""
    v = VIDEOS[no]
    n = len(v["scenes"])
    dest.mkdir(parents=True, exist_ok=True)
    for i, sc in enumerate(v["scenes"], 1):
        step = f"{i}/{n}"
        if sc["kind"] == "card":
            im = draw_card(v["label"], "" if i == 1 else step, sc)
        elif sc["kind"] == "shot":
            im = draw_frame(v["label"], step, sc, load_shot(sc), 0.8, 1.0)
        else:
            with tempfile.TemporaryDirectory() as tmp:
                paths = clip_frames(sc, Path(tmp))
                im = draw_frame(v["label"], step, dict(sc, box=None), blurred(Image.open(paths[len(paths) // 2]).convert("RGB"), sc), 1.0, 9.0)
        im.save(dest / f"{no}-{i:02d}.png")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", type=int, choices=sorted(VIDEOS))
    ap.add_argument("--still", type=int, choices=sorted(VIDEOS))
    ap.add_argument("--out", type=Path, default=ROOT / "下書き" / "静止画")
    a = ap.parse_args()
    if a.still:
        stills(a.still, a.out)
        return
    for no in [a.only] if a.only else sorted(VIDEOS):
        build(no)


if __name__ == "__main__":
    main()
