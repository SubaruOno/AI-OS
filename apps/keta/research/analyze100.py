"""100問の難しさを、AIプレイヤーの回答から測る。"""
import json, math, glob, re
Q = {x['id']: x for x in json.load(open('../questions.json'))}
def sc(l, u, x):
    L, U, X = map(math.log10, (l, u, x)); s = U - L
    if X < L: s += 20 * (L - X)
    if X > U: s += 20 * (X - U)
    return 100 - 25 * s
P = {}
for f in sorted(glob.glob('p100_*.json')):
    t = open(f).read(); P[f[5:-5]] = {r['id']: r for r in json.loads(re.search(r'\[.*\]', t, re.S).group(0)) if r['id'] in Q and r['lo'] > 0 and r['hi'] > 0}
print("プレイヤー別: 的中率 / 平均点 / 幅の中央値(桁)")
for n, a in P.items():
    hits = [a[i]['lo'] <= Q[i]['answer'] <= a[i]['hi'] for i in a]
    pts = [sc(a[i]['lo'], a[i]['hi'], Q[i]['answer']) for i in a]
    ws = sorted(math.log10(a[i]['hi'] / a[i]['lo']) for i in a)
    print(f"  {n:8s} {sum(hits)}/{len(a)} ({sum(hits)/len(a):.0%})  平均{sum(pts)/len(pts):6.1f}点  幅{ws[len(ws)//2]:.2f}桁")
rows = []
for i, q in Q.items():
    rs = [p[i] for p in P.values() if i in p]
    if not rs: continue
    hit = sum(r['lo'] <= q['answer'] <= r['hi'] for r in rs) / len(rs)
    # 外れの大きさ: 中心の推測が何桁ずれたか
    err = sum(abs(math.log10(math.sqrt(r['lo'] * r['hi'])) - math.log10(q['answer'])) for r in rs) / len(rs)
    pts = sum(sc(r['lo'], r['hi'], q['answer']) for r in rs) / len(rs)
    rows.append((i, hit, err, pts, q['q']))
json.dump([{"id": i, "hit": h, "err": e, "pts": p} for i, h, e, p, _ in rows], open('difficulty.json', 'w'), indent=1)
rows.sort(key=lambda r: r[2])
print("\n易しすぎ候補(中心のずれが小さい順10問)")
for r in rows[:10]: print(f"  {r[0]:3d} ずれ{r[2]:.2f}桁 的中{r[1]:.0%} 平均{r[3]:6.1f}  {r[4][:36]}")
print("\n難しい問題(中心のずれが大きい順10問)")
for r in rows[-10:]: print(f"  {r[0]:3d} ずれ{r[2]:.2f}桁 的中{r[1]:.0%} 平均{r[3]:6.1f}  {r[4][:36]}")
import statistics
print("\nずれの分布: 中央値 %.2f桁 / 0.1桁未満 %d問 / 0.5桁以上 %d問" % (statistics.median(r[2] for r in rows), sum(r[2] < 0.1 for r in rows), sum(r[2] >= 0.5 for r in rows)))
