#!/usr/bin/env python3
"""全チームの先発と継投の型を数え、次の試合の先発と継投を予想する（U-23W杯2026）

    python3 apps/wbsc-collect/relief_forecast.py                    # まだやっていない一番早い日の試合
    python3 apps/wbsc-collect/relief_forecast.py --date 2026-11-13
    python3 apps/wbsc-collect/relief_forecast.py --starter PUR=29 --starter JPN=16   # 発表された先発（背番号か名前の一部）。
                                                                    # 06_レポート/継投予測/発表された先発.json にたまり、次から自動で使う
    python3 apps/wbsc-collect/relief_forecast.py --no-check         # 当たり方の確かめ（約10秒）を省く

材料は WBSC の公式記録（collect.py が落とした plays.csv・pitching.csv・games.json・rosters.csv）だけ。
- 学習（先発の選び方・次に出る救援の選び方・その日に投げるか）は、U-23W杯の2022年・2024年・2026年の全試合を合わせて使う。
  チームを問わない決まり（何球投げたら何日あけるか、前の日に投げた投手は出にくい、など）を数を増やして学ぶため
- チームごとの型（先発の球数、交代のきっかけ、救援の順番）は今大会の試合だけで数える
- 出力は ~/野球/U23ワールドカップ2026/06_レポート/継投予測/。選手のデータなのでこのリポジトリには入れない
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gt_clips import COUNTRY  # noqa: E402

DATA = Path.home() / "野球/U23ワールドカップ2026/05_収集データ"
OUT = Path.home() / "野球/U23ワールドカップ2026/06_レポート/継投予測"
ANN = OUT / "発表された先発.json"   # {"2026-11-12": {"PUR": "29", ...}}。--starter で入れたものがたまる
EVENTS = ["u23-wc-2022", "u23-wc-2024", "u23-wc-2026"]
NOW_EVENT = "u23-wc-2026"
LATE_INN = 6          # 7回制なので6回からを終盤とする
E = html.escape


# ---------------------------------------------------------------- 読み込み

@dataclass
class App:
    """1試合1投手の登板"""
    event: str
    gameid: str
    date: date
    start: str
    team: str            # IOC
    opp: str
    pid: str
    name: str
    uniform: str
    hand: str            # L / R
    order: int           # 1 = 先発
    entry_inning: int
    entry_outs: int
    entry_runners: int   # 塁上の走者の数
    entry_diff: int      # 登板したときの点差（自分のチーム − 相手）
    first_bats: str      # 最初の打者の打席（L/R/S）
    pitches: int = 0
    bf: int = 0
    ip: str = "0"
    r: int = 0
    er: int = 0
    h: int = 0
    bbhbp: int = 0
    so: int = 0
    finished: bool = False       # その試合のチームの最後の投手
    exit_kind: str = ""          # 回の頭 / 回の途中 / 試合終了
    exit_inning: int = 0
    exit_outs: int = 0
    exit_runners: int = 0
    exit_diff: int = 0
    exit_inning_runs: int = 0    # 最後に投げた回に取られた点（その投手のあいだ）
    next_bats: str = ""          # 交代したときの次の打者の打席
    last_inning: int = 0
    inn_runs: dict = field(default_factory=dict)


@dataclass
class Game:
    event: str
    gameid: str
    date: date
    start: str
    away: str
    home: str
    away_runs: int | None
    home_runs: int | None
    final: bool
    label: str
    innings: int
    apps: dict = field(default_factory=lambda: {"home": [], "away": []})


def ioc_of(g: dict, side: str) -> str:
    return g.get(f"{side}ioc") or g.get(f"{side}label") or ""


def throws_of(player_field: str) -> str:
    s = player_field or ""
    i = s.find("'throws': '")
    return s[i + 11:i + 12] if i >= 0 else ""


def runners(r: dict) -> int:
    return sum(1 for k in ("runner1", "runner2", "runner3") if (r.get(k) or "0") not in ("", "0"))


def load_event(ev: str):
    d = DATA / ev
    games_raw = json.load(open(d / "games.json", encoding="utf-8"))
    games: dict[str, Game] = {}
    for g in games_raw:
        if not g.get("start"):
            continue
        st = str(g.get("gamestatustext") or "")
        games[str(g["id"])] = Game(
            event=ev, gameid=str(g["id"]), date=date.fromisoformat(g["start"][:10]), start=g["start"],
            away=ioc_of(g, "away"), home=ioc_of(g, "home"), away_runs=g.get("awayruns"), home_runs=g.get("homeruns"),
            final=st.startswith("F"), label=g.get("gametypelabel") or "", innings=int(g.get("innings") or 0))
    pit = {}
    with open(d / "pitching.csv", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            pit[(row["gameid"], row["playerid"])] = row
    plays = defaultdict(list)
    with open(d / "plays.csv", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            plays[row["gameid"]].append(row)
    roster = defaultdict(dict)   # IOC -> pid -> (name, uniform, hand)
    rp = d / "rosters.csv"
    if rp.exists():
        with open(rp, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                if "P" in (row.get("position") or "").split("/"):
                    roster[row["ioc"]][row["playerid"]] = (nice_name(row["lastname"], row["firstname"]), row["uniform"], row["throws"])

    for gid, rows in plays.items():
        g = games.get(gid)
        if g is None or not g.final:
            continue
        score = {"top": 0, "bot": 0}         # 表＝ビジターの得点、裏＝ホームの得点
        cur: dict[str, App | None] = {"home": None, "away": None}
        half_seen = set()
        last_key = None
        for r in rows:
            pid = r.get("pitcherid") or "0"
            half = r["half"]
            side = "home" if half == "top" else "away"    # 守っている側
            key = (r["inning"], half)
            usable = pid not in ("", "0") and r.get("nopitch") != "2"
            if usable:
                inn = int(r["inning"] or 0)
                outs = int(r["outs"] or 0)
                ru = runners(r)
                mine = score["bot"] if side == "home" else score["top"]
                theirs = score["top"] if side == "home" else score["bot"]
                c = cur[side]
                if c is None or c.pid != pid:
                    if c is not None:
                        fresh = outs == 0 and ru == 0 and key not in half_seen
                        c.exit_kind = "回の頭" if fresh else "回の途中"
                        c.exit_inning, c.exit_outs, c.exit_runners = inn, outs, ru
                        c.exit_diff = mine - theirs
                        c.next_bats = r.get("batter_bats") or ""
                    team = g.home if side == "home" else g.away
                    opp = g.away if side == "home" else g.home
                    pr = pit.get((gid, pid), {})
                    nm = nice_name(pr.get("lastname", ""), pr.get("firstname", "")) if pr else pid
                    hand = (r.get("pitcher_throws") or throws_of(pr.get("player", "")) or "?")[:1]
                    a = App(event=ev, gameid=gid, date=g.date, start=g.start, team=team, opp=opp, pid=pid, name=nm,
                            uniform=str(pr.get("uniform", "")), hand=hand, order=len(g.apps[side]) + 1,
                            entry_inning=inn, entry_outs=outs, entry_runners=ru, entry_diff=mine - theirs,
                            first_bats=r.get("batter_bats") or "")
                    if pr:
                        a.pitches = int(pr.get("pitch_pitches") or 0)
                        a.bf = int(pr.get("pitch_bf") or 0)
                        a.ip = pr.get("pitch_ip") or "0"
                        a.r = int(pr.get("pitch_r") or 0)
                        a.er = int(pr.get("pitch_er") or 0)
                        a.h = int(pr.get("pitch_h") or 0)
                        a.bbhbp = int(pr.get("pitch_bb") or 0) + int(pr.get("pitch_hbp") or 0)
                        a.so = int(pr.get("pitch_so") or 0)
                    g.apps[side].append(a)
                    cur[side] = a
                cur[side].last_inning = inn
                half_seen.add(key)
            n = int(r.get("runs") or 0)
            score[half] += n
            c = cur[side]
            if n and c is not None:
                inn = int(r["inning"] or 0)
                c.inn_runs[inn] = c.inn_runs.get(inn, 0) + n
        for side in ("home", "away"):
            if g.apps[side]:
                last = g.apps[side][-1]
                last.finished = True
                last.exit_kind = "試合終了"
            for x in g.apps[side]:
                x.exit_inning_runs = x.inn_runs.get(x.last_inning, 0)
    return games, roster


def nice_name(last: str, first: str) -> str:
    def t(s: str) -> str:
        # 大文字が多い語だけ頭の1文字を残して小文字にする（PéREZ のように一部だけ小文字のものも直す）
        def one(w: str) -> str:
            up = sum(c.isupper() for c in w)
            return w[:1].upper() + w[1:].lower() if up > len(w) / 2 else w
        return " ".join(one(w) for w in s.split())
    fn = (first or "").split()
    return f"{t(fn[0]) if fn else ''} {t(last)}".strip()


# ---------------------------------------------------------------- 投手ごとの履歴

class History:
    def __init__(self, games: dict[str, Game]):
        self.by_pid = defaultdict(list)
        for g in games.values():
            for side in ("home", "away"):
                for a in g.apps[side]:
                    self.by_pid[(a.event, a.pid)].append(a)
        for v in self.by_pid.values():
            v.sort(key=lambda a: (a.date, a.start))

    def before(self, ev: str, pid: str, d: date) -> list[App]:
        return [a for a in self.by_pid.get((ev, pid), []) if a.date < d]


def hist(prev: list[App], d: date) -> dict:
    last = prev[-1] if prev else None
    rest = (d - last.date).days if last else 9
    starts = [a for a in prev if a.order == 1]
    relief = [a for a in prev if a.order > 1]
    nr = len(relief)
    return {
        "n": len(prev),
        "rest": rest,
        "last_p": last.pitches if last else 0,
        "p2": sum(a.pitches for a in prev if (d - a.date).days <= 2),
        "p3": sum(a.pitches for a in prev if (d - a.date).days <= 3),
        "ns": len(starts),
        "start_rest": (d - starts[-1].date).days if starts else 9,
        "maxp": max((a.pitches for a in prev), default=0),
        "nr": nr,
        "first_share": sum(a.order == 2 for a in relief) / nr if nr else 0.0,
        "late_share": sum(a.entry_inning >= LATE_INN for a in relief) / nr if nr else 0.0,
        "close_late_share": sum(a.entry_inning >= LATE_INN and 0 < a.entry_diff <= 3 for a in relief) / nr if nr else 0.0,
        "finish_share": sum(a.finished for a in relief) / nr if nr else 0.0,
    }


def rest_dummies(h: dict) -> list[float]:
    r = h["rest"]
    return [float(r == 1), float(r == 2), float(r == 3), float(h["n"] == 0)]


# 先発の選び方
A_NAMES = ["前日に投げた", "中1日", "中2日", "まだ投げていない", "先発したことがある", "先発の回数", "前の先発から中3日以内",
           "1試合の最多球数", "直近3日の球数", "救援の回数", "先発したことがあり中3日以上"]


def feat_starter(h: dict) -> list[float]:
    return rest_dummies(h) + [float(h["ns"] > 0), min(h["ns"], 3), float(h["ns"] > 0 and h["start_rest"] <= 4),
                              h["maxp"] / 50, h["p3"] / 50, math.log1p(h["nr"]), float(h["ns"] > 0 and h["rest"] >= 4)]


# 次に出る救援の選び方
B_NAMES = ["前日に投げた", "中1日", "中2日", "まだ投げていない", "直近2日の球数", "先発したことがある", "前の先発から中3日以内",
           "救援の回数", "終盤×終盤に出た割合", "最初の交代×2番手に出た割合", "終盤リード3点以内×その場面の割合",
           "終盤リード3点以内×最後を投げた割合", "次の打者と同じ側の腕", "序盤×先発したことがある", "大差×まだ投げていない"]


def feat_relief(h: dict, ctx: dict, hand: str) -> list[float]:
    late = float(ctx["inning"] >= LATE_INN)
    first = float(ctx["order"] == 2)
    close_late = float(ctx["inning"] >= LATE_INN and 0 < ctx["diff"] <= 3)
    nb = ctx.get("bats", "")
    same = float(nb in ("L", "R") and hand == nb)
    early = float(ctx["inning"] <= 3)
    blow = float(abs(ctx["diff"]) >= 5)
    return rest_dummies(h) + [h["p2"] / 50, float(h["ns"] > 0), float(h["ns"] > 0 and h["start_rest"] <= 4),
                              math.log1p(h["nr"]), late * h["late_share"], first * h["first_share"],
                              close_late * h["close_late_share"], close_late * h["finish_share"], same,
                              early * float(h["ns"] > 0), blow * float(h["n"] == 0)]


# その日に投げるか
D_NAMES = ["前日に投げた", "中1日", "中2日", "まだ投げていない", "前回の球数", "直近3日の球数", "先発したことがある",
           "前の先発から中3日以内", "救援の回数"]


def feat_pitch(h: dict) -> list[float]:
    return rest_dummies(h) + [h["last_p"] / 50, h["p3"] / 50, float(h["ns"] > 0),
                              float(h["ns"] > 0 and h["start_rest"] <= 4), math.log1p(h["nr"])]


# ---------------------------------------------------------------- 学習（条件付きロジット）

def fit_clogit(sets: list[tuple[np.ndarray, int]], l2: float = 1.0) -> dict:
    k = sets[0][0].shape[1]
    allx = np.vstack([x for x, _ in sets])
    mu, sd = allx.mean(0), allx.std(0)
    sd[sd == 0] = 1
    z = [((x - mu) / sd, y) for x, y in sets]

    def f(w):
        nll, gr = 0.0, np.zeros(k)
        for x, y in z:
            s = x @ w
            s -= s.max()
            p = np.exp(s)
            p /= p.sum()
            nll -= math.log(p[y] + 1e-12)
            gr -= x[y] - p @ x
        return nll + l2 * w @ w / 2, gr + l2 * w

    res = minimize(f, np.zeros(k), jac=True, method="L-BFGS-B")
    return {"w": res.x, "mu": mu, "sd": sd}


def clogit_prob(m: dict, x: np.ndarray) -> np.ndarray:
    s = ((x - m["mu"]) / m["sd"]) @ m["w"]
    s -= s.max()
    p = np.exp(s)
    return p / p.sum()


def fit_logit(x: np.ndarray, y: np.ndarray, l2: float = 1.0) -> dict:
    mu, sd = x.mean(0), x.std(0)
    sd[sd == 0] = 1
    z = np.hstack([(x - mu) / sd, np.ones((len(x), 1))])

    def f(w):
        p = 1 / (1 + np.exp(-(z @ w)))
        eps = 1e-12
        nll = -np.sum(y * np.log(p + eps) + (1 - y) * np.log(1 - p + eps))
        gr = z.T @ (p - y)
        reg = w.copy()
        reg[-1] = 0
        return nll + l2 * reg @ reg / 2, gr + l2 * reg

    res = minimize(f, np.zeros(z.shape[1]), jac=True, method="L-BFGS-B")
    return {"w": res.x, "mu": mu, "sd": sd}


def logit_prob(m: dict, x: np.ndarray) -> np.ndarray:
    z = np.hstack([(x - m["mu"]) / m["sd"], np.ones((len(x), 1))])
    return 1 / (1 + np.exp(-(z @ m["w"])))


# ---------------------------------------------------------------- 学習用のデータ

def team_games(games: dict[str, Game]) -> dict[tuple[str, str], list[tuple[Game, str]]]:
    out = defaultdict(list)
    for g in games.values():
        if not g.final:
            continue
        for side, t in (("home", g.home), ("away", g.away)):
            if g.apps[side]:
                out[(g.event, t)].append((g, side))
    for v in out.values():
        v.sort(key=lambda x: x[0].start)
    return out


def pool_of(ev: str, team: str, tg: dict, rosters: dict) -> dict[str, tuple[str, str, str]]:
    """その大会でチームの投手として数える人：登録名簿の投手と、実際に投げた人"""
    pool = dict(rosters.get(ev, {}).get(team, {}))
    for g, side in tg.get((ev, team), []):
        for a in g.apps[side]:
            pool.setdefault(a.pid, (a.name, a.uniform, a.hand))
    return pool


def find_pitcher(pool: dict, key: str) -> str | None:
    """名前の一部か背番号で投手を探す。背番号が合う人を先にする"""
    key = (key or "").strip().strip('"').lower()
    if not key:
        return None
    for p, (nm, uni, _) in pool.items():
        if key == str(uni).lower():
            return p
    hits = [p for p, (nm, _, _) in pool.items() if key in nm.lower()]
    return hits[0] if len(hits) == 1 else None


def build_sets(all_games: dict, hist_obj: History, rosters: dict, skip: set | None = None,
               ann: dict | None = None, before: date | None = None):
    """ann（発表された先発）のうち、before より前の日で、試合がまだ記録に入っていないものも先発の学習に足す"""
    tg = team_games(all_games)
    A, B, Dx, Dy = [], [], [], []
    meta_a, meta_b = [], []
    for (ev, team), lst in tg.items():
        pool = pool_of(ev, team, tg, rosters)
        pids = list(pool)
        for i, (g, side) in enumerate(lst):
            if skip and g.gameid in skip and ev == NOW_EVENT:
                continue
            apps = g.apps[side]
            hs = {p: hist(hist_obj.before(ev, p, g.date), g.date) for p in pids}
            # 大会の最初の試合は履歴がないので、先発とその日に投げるかの学習には使わない
            if i > 0:
                y = pids.index(apps[0].pid) if apps[0].pid in pids else None
                if y is not None:
                    A.append((np.array([feat_starter(hs[p]) for p in pids]), y))
                    meta_a.append((ev, team, g.gameid))
                used = {a.pid for a in apps}
                for p in pids:
                    Dx.append(feat_pitch(hs[p]))
                    Dy.append(float(p in used))
            used_so_far = {apps[0].pid}
            for j, a in enumerate(apps[1:], start=2):
                prev = apps[j - 2]
                ctx = {"inning": a.entry_inning, "diff": a.entry_diff, "order": j, "bats": prev.next_bats or a.first_bats}
                cands = [p for p in pids if p not in used_so_far]
                if a.pid in cands and len(cands) > 1:
                    x = np.array([feat_relief(hs[p], ctx, pool[p][2]) for p in cands])
                    B.append((x, cands.index(a.pid)))
                    meta_b.append((ev, team, g.gameid))
                used_so_far.add(a.pid)
    for ds, teams in (ann or {}).items():
        dd = date.fromisoformat(ds)
        if before and dd >= before:
            continue
        for team, key in teams.items():
            if any(g.event == NOW_EVENT and g.final and g.date == dd and team in (g.home, g.away) for g in all_games.values()):
                continue   # 試合が記録に入っていれば、上で記録の方を使っている
            pool = pool_of(NOW_EVENT, team, tg, rosters)
            pids = list(pool)
            y = find_pitcher(pool, key)
            if y is None:
                continue
            hs = {p: hist(hist_obj.before(NOW_EVENT, p, dd), dd) for p in pids}
            A.append((np.array([feat_starter(hs[p]) for p in pids]), pids.index(y)))
            meta_a.append((NOW_EVENT, team, f"発表{ds}"))
    return A, B, (np.array(Dx), np.array(Dy)), meta_a, meta_b


# ---------------------------------------------------------------- 確かめ（今大会の試合を1つずつ抜いて当てる）

def check(all_games, hist_obj, rosters):
    now_games = [g for g in all_games.values() if g.event == NOW_EVENT and g.final]
    tg = team_games(all_games)
    hitA = [0, 0, 0]   # 1番目に当たり、3番以内、数
    baseA = [0, 0]
    hitB = [0, 0, 0]
    baseB = [0, 0]
    for g in sorted(now_games, key=lambda x: x.start):
        A, B, _, _, _ = build_sets(all_games, hist_obj, rosters, skip={g.gameid})
        ma, mb = fit_clogit(A), fit_clogit(B)
        for side, team in (("home", g.home), ("away", g.away)):
            lst = tg[(NOW_EVENT, team)]
            idx = [x[0].gameid for x in lst].index(g.gameid)
            pool = pool_of(NOW_EVENT, team, tg, rosters)
            pids = list(pool)
            hs = {p: hist(hist_obj.before(NOW_EVENT, p, g.date), g.date) for p in pids}
            apps = g.apps[side]
            if idx > 0:
                pa = clogit_prob(ma, np.array([feat_starter(hs[p]) for p in pids]))
                rank = [pids[i] for i in np.argsort(-pa)]
                hitA[0] += rank[0] == apps[0].pid
                hitA[1] += apps[0].pid in rank[:3]
                hitA[2] += 1
                # 比べる相手：先発したことがある投手のうち一番休んでいる人（同じなら球数の多い人）
                base = sorted(pids, key=lambda p: (hs[p]["ns"] > 0, hs[p]["rest"], hs[p]["maxp"]), reverse=True)
                baseA[0] += base[0] == apps[0].pid
                baseA[1] += apps[0].pid in base[:3]
            used = {apps[0].pid}
            for j, a in enumerate(apps[1:], start=2):
                prev = apps[j - 2]
                ctx = {"inning": a.entry_inning, "diff": a.entry_diff, "order": j, "bats": prev.next_bats or a.first_bats}
                cands = [p for p in pids if p not in used]
                pb = clogit_prob(mb, np.array([feat_relief(hs[p], ctx, pool[p][2]) for p in cands]))
                rank = [cands[i] for i in np.argsort(-pb)]
                hitB[0] += rank[0] == a.pid
                hitB[1] += a.pid in rank[:3]
                hitB[2] += 1
                base = sorted(cands, key=lambda p: (hs[p]["rest"] > 1, hs[p]["nr"]), reverse=True)
                baseB[0] += base[0] == a.pid
                baseB[1] += a.pid in base[:3]
                used.add(a.pid)
    out = {"starter": {"n": hitA[2], "top1": hitA[0], "top3": hitA[1], "base_top1": baseA[0], "base_top3": baseA[1]},
           "relief": {"n": hitB[2], "top1": hitB[0], "top3": hitB[1], "base_top1": baseB[0], "base_top3": baseB[1]}}
    out["sr"] = check_super_round(all_games, hist_obj, rosters)
    return out


def check_super_round(all_games, hist_obj, rosters):
    """2022年・2024年のスーパーラウンドと順位決定戦。その大会のその日からあとを学習から外して当てる"""
    tg = team_games(all_games)
    hit = {"n": 0, "top1": 0, "top3": 0, "base_top1": 0, "base_top3": 0, "rn": 0, "r1": 0, "r3": 0}
    for ev in EVENTS:
        if ev == NOW_EVENT:
            continue
        sr = sorted([g for g in all_games.values() if g.event == ev and g.final and g.label != "Opening Round"], key=lambda g: g.start)
        if not sr:
            continue
        d0 = min(g.date for g in sr)
        sub = {k: v for k, v in all_games.items() if not (v.event == ev and v.date >= d0)}
        A, B, _, _, _ = build_sets(sub, History(sub), rosters)
        ma, mb = fit_clogit(A), fit_clogit(B)
        for g in sr:
            for side, team in (("home", g.home), ("away", g.away)):
                apps = g.apps[side]
                if not apps:
                    continue
                pool = pool_of(ev, team, tg, rosters)
                pids = list(pool)
                hs = {p: hist(hist_obj.before(ev, p, g.date), g.date) for p in pids}
                pa = clogit_prob(ma, np.array([feat_starter(hs[p]) for p in pids]))
                rank = [pids[i] for i in np.argsort(-pa)]
                base = sorted(pids, key=lambda p: (hs[p]["ns"] > 0, hs[p]["rest"], hs[p]["maxp"]), reverse=True)
                hit["n"] += 1
                hit["top1"] += rank[0] == apps[0].pid
                hit["top3"] += apps[0].pid in rank[:3]
                hit["base_top1"] += base[0] == apps[0].pid
                hit["base_top3"] += apps[0].pid in base[:3]
                used = {apps[0].pid}
                for j, a in enumerate(apps[1:], start=2):
                    prev = apps[j - 2]
                    ctx = {"inning": a.entry_inning, "diff": a.entry_diff, "order": j, "bats": prev.next_bats or a.first_bats}
                    cands = [p for p in pids if p not in used]
                    pb = clogit_prob(mb, np.array([feat_relief(hs[p], ctx, pool[p][2]) for p in cands]))
                    rk = [cands[i] for i in np.argsort(-pb)]
                    hit["rn"] += 1
                    hit["r1"] += rk[0] == a.pid
                    hit["r3"] += a.pid in rk[:3]
                    used.add(a.pid)
    return hit


# ---------------------------------------------------------------- チームの型（今大会）

def ip_outs(ip: str) -> int:
    if not ip:
        return 0
    w, _, f = str(ip).partition(".")
    return int(w or 0) * 3 + int(f or 0)


def outs_ip(o: float) -> str:
    return f"{int(o // 3)}.{int(round(o % 3))}" if o % 3 else f"{int(o // 3)}"


def team_profile(team: str, lst: list[tuple[Game, str]]) -> dict:
    starts, reliefs, games_rows = [], [], []
    for g, side in lst:
        apps = g.apps[side]
        mine = g.home_runs if side == "home" else g.away_runs
        theirs = g.away_runs if side == "home" else g.home_runs
        res = "勝" if mine > theirs else "負"
        games_rows.append({"g": g, "side": side, "apps": apps, "res": res, "mine": mine, "theirs": theirs})
        starts.append(apps[0])
        reliefs += apps[1:]
    sp = [a.pitches for a in starts]
    so = [ip_outs(a.ip) for a in starts]
    pulled = [a for a in starts if a.exit_kind != "試合終了"]
    mid = [a for a in pulled if a.exit_kind == "回の途中"]
    same = [a for a in reliefs if a.first_bats in ("L", "R") and a.first_bats == a.hand]
    known = [a for a in reliefs if a.first_bats in ("L", "R")]
    # 救援の連投：前日に投げた救援
    by = defaultdict(list)
    for g, side in lst:
        for a in g.apps[side]:
            by[a.pid].append(a)
    b2b = 0
    for v in by.values():
        ds = sorted({a.date for a in v})
        b2b += sum(1 for x, y in zip(ds, ds[1:]) if (y - x).days == 1)
    return {
        "games": games_rows,
        "n": len(lst),
        "sp_med": statistics.median(sp) if sp else 0, "sp_min": min(sp, default=0), "sp_max": max(sp, default=0),
        "so_med": statistics.median(so) if so else 0,
        "pulled": len(pulled), "mid": len(mid), "mid_runners": sum(1 for a in mid if a.exit_runners > 0),
        "pulled_after_runs": sum(1 for a in pulled if a.exit_inning_runs > 0),
        "exit_inn_med": statistics.median([a.exit_inning for a in pulled]) if pulled else 0,
        "per_game": statistics.mean(len(x["apps"]) for x in games_rows) if games_rows else 0,
        "relief_p_med": statistics.median([a.pitches for a in reliefs]) if reliefs else 0,
        "same_hand": (len(same), len(known)),
        "b2b": b2b,
        "used": len(by),
        # 終盤の接戦（6回以降・3点差以内）で出てきた救援と、2番手で出た救援
        "late_close": Counter((a.pid, a.name, a.uniform, a.hand) for a in reliefs if a.entry_inning >= LATE_INN and abs(a.entry_diff) <= 3),
        "second": Counter((a.pid, a.name, a.uniform, a.hand) for a in reliefs if a.order == 2),
        "closer": Counter((a.pid, a.name, a.uniform, a.hand) for x in games_rows if x["res"] == "勝" and x["mine"] - x["theirs"] <= 3
                          for a in x["apps"][-1:] if a.order > 1),
    }


# ---------------------------------------------------------------- 次の試合の予想

def forecast(team: str, d: date, all_games, hist_obj, rosters, models, fixed_starter: str | None):
    tg = team_games(all_games)
    lst = tg.get((NOW_EVENT, team), [])
    pool = pool_of(NOW_EVENT, team, tg, rosters)
    pids = list(pool)
    hs = {p: hist(hist_obj.before(NOW_EVENT, p, d), d) for p in pids}
    ma, mb, md = models
    pa = clogit_prob(ma, np.array([feat_starter(hs[p]) for p in pids]))
    pd_ = logit_prob(md, np.array([feat_pitch(hs[p]) for p in pids]))
    starter_rank = sorted(zip(pids, pa), key=lambda x: -x[1])
    st = find_pitcher(pool, fixed_starter) if fixed_starter else None
    if fixed_starter and st is None:
        print(f"注意：{team} の先発「{fixed_starter}」が名簿の投手に見つからない")
    fixed_rank = [x[0] for x in starter_rank].index(st) + 1 if st else None
    if st is None:
        st = starter_rank[0][0]
    prof = team_profile(team, lst) if lst else None
    exit_inn = int(round(prof["exit_inn_med"])) if prof and prof["exit_inn_med"] else 4
    cands = [p for p in pids if p != st]

    def rank(ctx):
        out = {}
        for bats in ("R", "L"):
            c = dict(ctx, bats=bats)
            p = clogit_prob(mb, np.array([feat_relief(hs[q], c, pool[q][2]) for q in cands]))
            out[bats] = sorted(zip(cands, p), key=lambda x: -x[1])
        return out

    scen = {
        "first": rank({"inning": max(exit_inn, 2), "diff": 0, "order": 2}),
        "late": rank({"inning": LATE_INN, "diff": 2, "order": 4}),
        "behind": rank({"inning": 5, "diff": -5, "order": 3}),
    }
    rows = []
    for p in pids:
        nm, uni, hand = pool[p]
        prev = hist_obj.before(NOW_EVENT, p, d)
        rows.append({"pid": p, "name": nm, "uniform": uni, "hand": hand, "h": hs[p], "prev": prev,
                     "p_start": float(pa[pids.index(p)]), "p_pitch": float(pd_[pids.index(p)])})
    rows.sort(key=lambda x: (-x["p_pitch"]))
    return {"team": team, "date": d, "pool": pool, "rows": rows, "starter_rank": starter_rank[:4],
            "starter": st, "starter_fixed": bool(fixed_starter and st), "fixed_rank": fixed_rank,
            "fixed_p": float(pa[pids.index(st)]) if st else 0.0, "scen": scen, "prof": prof, "exit_inn": exit_inn}


# ---------------------------------------------------------------- 書き出し

CSS = """
:root{--bg:#fff;--fg:#1d2433;--sub:#5b6474;--line:#d9dee7;--soft:#f3f5f9;--accent:#1f5fbf;--warn:#b3261e;--ok:#1e7d4f}
@media (prefers-color-scheme: dark){:root{--bg:#14171d;--fg:#e6e9ef;--sub:#a3abb9;--line:#323946;--soft:#1d2129;--accent:#7fb0ff;--warn:#ff8a80;--ok:#7fd1a6}}
body{background:var(--bg);color:var(--fg);font-family:-apple-system,"Hiragino Sans","Noto Sans JP",sans-serif;margin:0;padding:16px;line-height:1.55;font-size:14px}
h1{font-size:20px;margin:0 0 4px} h2{font-size:18px;margin:28px 0 6px;padding-top:10px;border-top:2px solid var(--line)}
h3{font-size:15px;margin:16px 0 6px}.sub{color:var(--sub);font-size:12.5px}
nav a{display:inline-block;margin:0 6px 6px 0;padding:3px 9px;border:1px solid var(--line);border-radius:12px;color:var(--fg);text-decoration:none;font-size:13px}
table{border-collapse:collapse;width:100%;margin:4px 0 10px;font-size:13px}th,td{border-bottom:1px solid var(--line);padding:4px 6px;text-align:left;vertical-align:top}
th{background:var(--soft);font-weight:600;white-space:nowrap}.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.bar{display:inline-block;height:8px;background:var(--accent);border-radius:2px;vertical-align:middle;margin-right:4px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px}.card{border:1px solid var(--line);border-radius:8px;padding:8px 10px;background:var(--soft)}
.card b{font-size:13px}.warn{color:var(--warn)}.ok{color:var(--ok)}.wrap{overflow-x:auto}
.seq span{white-space:nowrap}.tag{font-size:11px;border:1px solid var(--line);border-radius:4px;padding:0 4px;margin-left:3px;color:var(--sub)}
"""


def jp(t: str) -> str:
    return COUNTRY.get(t, t)


def md(d: date) -> str:
    return f"{d.month}/{d.day}"


def who(pool, p) -> str:
    nm, uni, hand = pool[p]
    return f"#{uni} {nm}（{'左' if hand == 'L' else '右' if hand == 'R' else '?'}）"


def rest_txt(h: dict) -> str:
    if h["n"] == 0:
        return "今大会まだ投げていない"
    r = h["rest"]
    return "前日に投げた" if r == 1 else f"中{r - 1}日"


def pct(x: float) -> str:
    return f"{round(x * 100):d}%"


def bar(x: float) -> str:
    return f'<span class="bar" style="width:{max(2, round(x * 60))}px"></span>{pct(x)}'


def app_line(a: App) -> str:
    sit = "同点" if a.entry_diff == 0 else (f"{a.entry_diff}点リード" if a.entry_diff > 0 else f"{-a.entry_diff}点ビハインド")
    if a.order == 1:
        where = "先発"
    else:
        where = f"{a.entry_inning}回{'' if a.entry_outs == 0 and a.entry_runners == 0 else f'{a.entry_outs}死'}" + \
                ("" if a.entry_runners == 0 else f"走者{a.entry_runners}") + f"・{sit}"
    return f"<span>#{E(a.uniform)} {E(a.name)}（{'左' if a.hand == 'L' else '右'}）{where} {a.ip}回{a.pitches}球{'' if a.r == 0 else f' {a.r}失'}</span>"


def render(fcs: list[dict], d: date, chk: dict | None, others: list[str], all_games) -> str:
    out = [f"<!doctype html><html lang=ja><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
           f"<title>継投の予想 {md(d)}</title><style>{CSS}</style></head><body>"]
    out.append(f"<h1>先発と継投の予想（{d.year}年{md(d)}の試合）</h1>")
    out.append(f"<div class=sub>今大会の{sum(1 for g in all_games.values() if g.event == NOW_EVENT and g.final)}試合の公式記録から数えた。"
               f"確率は、2022年・2024年・2026年のU-23W杯の全試合で学んだ選び方に、各投手のこれまでの登板を当てはめたもの。作成 {datetime.now().strftime('%m/%d %H:%M')}（現地）</div>")
    if chk:
        s, r = chk["starter"], chk["relief"]
        out.append(f"<div class=card style='margin-top:8px'><b>当たり方（今大会の試合を1つずつ抜いて当てた）</b><br>"
                   f"先発：1番目の候補が当たり {s['top1']}/{s['n']}、3番目までに入る {s['top3']}/{s['n']}"
                   f"（一番休んでいる先発経験者を選ぶだけだと {s['base_top1']}/{s['n']}・{s['base_top3']}/{s['n']}）<br>"
                   f"次に出る救援：1番目が当たり {r['top1']}/{r['n']}、3番目まで {r['top3']}/{r['n']}"
                   f"（前日に投げていない救援の多い順だと {r['base_top1']}/{r['n']}・{r['base_top3']}/{r['n']}）<br>"
                   f"2022年・2024年のスーパーラウンドと順位決定戦（その日からあとを学習から外した）：先発は1番目が当たり {chk['sr']['top1']}/{chk['sr']['n']}、"
                   f"3番目まで {chk['sr']['top3']}/{chk['sr']['n']}（一番休んでいる先発経験者だと {chk['sr']['base_top1']}/{chk['sr']['n']}・{chk['sr']['base_top3']}/{chk['sr']['n']}）、"
                   f"次に出る救援は1番目 {chk['sr']['r1']}/{chk['sr']['rn']}・3番目まで {chk['sr']['r3']}/{chk['sr']['rn']}</div>")
    out.append("<nav style='margin-top:10px'>" + "".join(f"<a href='#{f['team']}'>{jp(f['team'])}</a>" for f in fcs) + "</nav>")
    for f in fcs:
        out += render_team(f, d)
    if others:
        out.append(f"<p class=sub>{md(d)}に試合がないチーム：{'・'.join(jp(t) for t in others)}</p>")
    out.append("</body></html>")
    return "\n".join(out)


def render_team(f: dict, d: date) -> list[str]:
    t, pool, prof = f["team"], f["pool"], f["prof"]
    o = [f"<h2 id='{t}'>{jp(t)}</h2>"]
    nx = f.get("next")
    if nx:
        o.append(f"<div class=sub>{md(d)} {nx['start'][11:16]} 対{jp(nx['opp'])}（{'後攻' if nx['side'] == 'home' else '先攻'}）</div>")
    # 先発
    o.append("<h3>先発</h3>")
    if f["starter_fixed"]:
        o.append(f"<p>発表された先発：<b>{E(who(pool, f['starter']))}</b>"
                 f"<span class=sub>（発表前の予想では{f['fixed_rank']}番目・{pct(f['fixed_p'])}）</span></p>")
    o.append(f"<div class=wrap><table><tr><th>先発の候補{'（発表前の予想）' if f['starter_fixed'] else ''}</th><th>確率</th><th>今大会の登板</th></tr>")
    for p, x in f["starter_rank"][:3]:
        prev = [r for r in f["rows"] if r["pid"] == p][0]
        o.append(f"<tr><td>{E(who(pool, p))}</td><td class=num>{bar(x)}</td><td>{E(prev_txt(prev['prev']))}・{rest_txt(prev['h'])}</td></tr>")
    o.append("</table></div>")
    if prof:
        o.append(f"<p class=sub>今大会の先発{prof['n']}人：球数の真ん中 {prof['sp_med']:.0f}球（{prof['sp_min']}〜{prof['sp_max']}）、"
                 f"投球回の真ん中 {outs_ip(prof['so_med'])}回。交代{prof['pulled']}回のうち回の途中が{prof['mid']}回（走者を残して{prof['mid_runners']}回）、"
                 f"その回か直前の回に点を取られての交代 {prof['pulled_after_runs']}回。降板した回の真ん中は{prof['exit_inn_med']:.0f}回。</p>")
    # 救援
    o.append("<h3>先発の次に出てくる投手</h3><div class=grid>")
    labels = {"first": f"{max(f['exit_inn'], 2)}回・同点で最初の交代", "late": f"{LATE_INN}回・2点リード", "behind": "5回・5点ビハインド"}
    for k in ("first", "late", "behind"):
        o.append(f"<div class=card><b>{labels[k]}</b>")
        r3, l3 = f["scen"][k]["R"][:3], f["scen"][k]["L"][:3]
        same = [p for p, _ in r3] == [p for p, _ in l3]
        for bats, nm in ((("R", "次の打者の左右に関係なく"),) if same else (("R", "次が右打者"), ("L", "次が左打者"))):
            top = f["scen"][k][bats][:3]
            o.append(f"<div class=sub style='margin-top:4px'>{nm}</div>" +
                     "<br>".join(f"{E(who(pool, p))} {pct(x)}" for p, x in top))
        o.append("</div>")
    o.append("</div>")
    # 投手ごと
    o.append("<h3>投手ごとの状態</h3><div class=wrap><table><tr><th>投手</th><th>この日に投げる見込み</th><th>前回</th><th>今大会の登板</th></tr>")
    for r in f["rows"]:
        h = r["h"]
        cls = " class=warn" if h["rest"] == 1 else ""
        tag = "" if r["pid"] != f["starter"] else "<span class=tag>先発（発表）</span>" if f["starter_fixed"] else "<span class=tag>先発の予想1番目</span>"
        chance = "先発" if r["pid"] == f["starter"] and f["starter_fixed"] else bar(r["p_pitch"])
        o.append(f"<tr><td>{E(who(pool, r['pid']))}{tag}</td><td class=num>{chance}</td>"
                 f"<td{cls}>{rest_txt(h)}{'' if h['n'] == 0 else '（' + str(h['last_p']) + '球）'}</td><td>{E(prev_txt(r['prev']))}</td></tr>")
    o.append("</table></div>")
    # 試合ごとの継投
    if prof:
        sh, kn = prof["same_hand"]
        o.append(f"<h3>今大会の継投</h3><p class=sub>1試合の投手の数 平均{prof['per_game']:.1f}人、投げた投手{prof['used']}人。"
                 f"救援の球数の真ん中 {prof['relief_p_med']:.0f}球。救援が最初の打者と同じ側の腕だったのは {sh}/{kn}。連投{prof['b2b']}回。</p>")
        def cnt(c):
            return "、".join(f"#{u} {E(n)}（{'左' if h == 'L' else '右'}）{k}回" for (_, n, u, h), k in c.most_common()) or "なし"
        o.append(f"<p class=sub>2番手で出た救援：{cnt(prof['second'])}<br>6回以降・3点差以内で出た救援：{cnt(prof['late_close'])}<br>"
                 f"3点差以内で勝った試合の最後の投手：{cnt(prof['closer'])}</p>")
        o.append("<div class=wrap><table><tr><th>日</th><th>相手</th><th>結果</th><th>継投（出てきた場面・投球回・球数）</th></tr>")
        for x in prof["games"]:
            g = x["g"]
            opp = g.away if x["side"] == "home" else g.home
            seq = " → ".join(app_line(a) for a in x["apps"])
            o.append(f"<tr><td>{md(g.date)}</td><td>{jp(opp)}</td><td>{x['res']} {x['mine']}-{x['theirs']}</td><td class=seq>{seq}</td></tr>")
        o.append("</table></div>")
    return o


def prev_txt(prev: list[App]) -> str:
    if not prev:
        return "なし"
    return "、".join(f"{md(a.date)}{'先' if a.order == 1 else '救'}{a.pitches}球" for a in prev)


# ---------------------------------------------------------------- 本体

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--starter", action="append", default=[], help='IOC=名前か背番号（例 PUR="Laboy"）')
    ap.add_argument("--no-check", action="store_true", help="当たり方の確かめを省く（速くなる）")
    a = ap.parse_args()

    all_games, rosters = {}, {}
    for ev in EVENTS:
        g, r = load_event(ev)
        all_games.update({(f"{ev}:{k}" if ev != NOW_EVENT else k): v for k, v in g.items()})
        rosters[ev] = r
    hist_obj = History(all_games)

    upcoming = sorted([g for g in all_games.values() if g.event == NOW_EVENT and not g.final and g.home and g.away
                       and g.home in COUNTRY and g.away in COUNTRY], key=lambda g: g.start)
    d = date.fromisoformat(a.date) if a.date else (upcoming[0].date if upcoming else date.today())

    ann = json.loads(ANN.read_text(encoding="utf-8")) if ANN.exists() else {}
    day = ann.setdefault(d.isoformat(), {})
    for s in a.starter:
        k, _, v = s.partition("=")
        day[k.strip().upper()] = v.strip().strip('"')
    if a.starter:
        OUT.mkdir(parents=True, exist_ok=True)
        ANN.write_text(json.dumps(ann, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    fixed = day

    # 予想の日とそれより後の発表は学習に入れない（発表前の予想として比べられるように）
    A, B, (dx, dy), _, _ = build_sets(all_games, hist_obj, rosters, ann=ann, before=d)
    models = (fit_clogit(A), fit_clogit(B), fit_logit(dx, dy))
    print(f"学習：先発の選択 {len(A)}回、救援の選択 {len(B)}回、その日に投げるか {len(dy)}件")
    for nm, m, names in (("先発", models[0], A_NAMES), ("救援", models[1], B_NAMES), ("登板", models[2], D_NAMES)):
        w = m["w"][:len(names)]
        print(f"  {nm}: " + "、".join(f"{n} {v:+.2f}" for n, v in sorted(zip(names, w), key=lambda x: -abs(x[1]))[:6]))

    chk = None
    if not a.no_check:
        chk = check(all_games, hist_obj, rosters)
        print("確かめ:", json.dumps(chk, ensure_ascii=False))

    day_games = [g for g in upcoming if g.date == d]
    teams_today = []
    for g in day_games:
        for side, t in (("away", g.away), ("home", g.home)):
            teams_today.append((t, {"start": g.start, "opp": g.home if side == "away" else g.away, "side": side}))
    # 日本の相手を先に
    teams_today.sort(key=lambda x: (x[1]["opp"] != "JPN", x[0] == "JPN", x[1]["start"]))
    fcs = []
    for t, nx in teams_today:
        pend = [g for g in upcoming if g.date < d and t in (g.home, g.away)]
        f = forecast(t, d, all_games, hist_obj, rosters, models, fixed.get(t))
        f["next"] = nx
        f["pending"] = len(pend)
        fcs.append(f)
    others = sorted({t for t in COUNTRY} - {t for t, _ in teams_today})
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"継投予測_{d.strftime('%Y%m%d')}.html"
    path.write_text(render(fcs, d, chk, others, all_games), encoding="utf-8")
    print(path)
    if any(f["pending"] for f in fcs):
        print("注意：この日より前に、まだ終わっていない試合があるチームがある（その試合の登板は入っていない）:",
              "、".join(jp(f["team"]) for f in fcs if f["pending"]))


if __name__ == "__main__":
    main()
