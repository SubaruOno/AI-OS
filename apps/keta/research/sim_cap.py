"""1問の最低点に下限(キャップ)を付けても、正直な90%幅が最も得をするか。
知識のあいまいさに加え、桁ごと勘違いしている問題(推測の中心が大きくずれる)も混ぜる。"""
import math, random
random.seed(7)
def pts(l, u, x, cap):
    s = u - l + (20 * (l - x) if x < l else 0) + (20 * (x - u) if x > u else 0)
    return max(cap, 100 - 25 * s)
zs = {"自信過剰±0.67σ": 0.67, "やや過剰±1.0σ": 1.0, "±1.3σ": 1.3, "正直±1.645σ": 1.645, "±2.0σ": 2.0, "慎重±2.5σ": 2.5}
for cap in (-1e9, -300, -200, -100, 0):
    tot = {k: 0.0 for k in zs}; N = 120000
    for _ in range(N):
        sigma = random.choice([0.15, 0.3, 0.5, 0.8, 1.2])   # 1.2桁: 桁の見当がつかない問題
        mu = random.gauss(0, sigma)
        for k, z in zs.items(): tot[k] += pts(mu - z * sigma, mu + z * sigma, 0, cap)
    best = max(tot, key=tot.get)
    print(f"下限{'なし' if cap < -1e8 else cap:>5}: " + " / ".join(f"{k}:{v/N:6.1f}" for k, v in tot.items()) + f"  → 最高は {best}")
