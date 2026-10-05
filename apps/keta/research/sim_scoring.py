"""採点ルールの検証: 正直な90%幅が平均点で最も得するか。"""
import math, random
random.seed(1)
A = 0.1
def interval_score(l, u, x):  # log10空間のWinkler区間スコア(小さいほど良い)
    s = u - l
    if x < l: s += 2/A*(l-x)
    if x > u: s += 2/A*(x-u)
    return s
def points(l, u, x, c): return 100*math.exp(-interval_score(l, u, x)/c)
def run(c, n=200000):
    strategies = {"点で当てる(±0.05z)":0.05,"自信過剰(±0.67σ,当たり50%)":0.67,"やや過剰(±1.0σ)":1.0,
                  "正直な90%(±1.645σ)":1.645,"慎重(±2.5σ)":2.5}
    res = {k:[0,0] for k in strategies}
    for _ in range(n):
        sigma = random.choice([0.15,0.3,0.5,0.8])   # 問題ごとの知識のあいまいさ(桁)
        mu = random.gauss(0, sigma)                 # 本人の推測(真値=0)
        for k, z in strategies.items():
            l, u = mu - z*sigma, mu + z*sigma
            res[k][0] += points(l, u, 0, c); res[k][1] += (l <= 0 <= u)
    print(f"c={c}")
    for k,(p,h) in res.items(): print(f"  {k:28s} 平均{p/n:5.1f}点 的中率{h/n:5.1%}")
for c in (1, 2, 3): run(c, 60000)

print("\n--- 直線変換: 点 = 100 - k*区間スコア (下限なし) ---")
def run_lin(k, n=60000):
    zs = {"自信過剰±0.67":0.67,"やや過剰±1.0":1.0,"±1.3":1.3,"正直な90%±1.645":1.645,"±2.0":2.0,"慎重±2.5":2.5}
    tot = {z:0 for z in zs}
    for _ in range(n):
        sigma = random.choice([0.15,0.3,0.5,0.8]); mu = random.gauss(0, sigma)
        for name,z in zs.items(): tot[name] += 100 - k*interval_score(mu-z*sigma, mu+z*sigma, 0)
    print(f"k={k}: " + " / ".join(f"{n}:{v/n_:.1f}" for n,v,n_ in [(a,b,n) for a,b in tot.items()]))
run_lin(25)
