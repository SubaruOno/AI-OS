import json, math, glob, re
Q={x['id']:x for x in json.load(open('../questions.json'))}
def sc(l,u,x):
    L,U,X=map(math.log10,(l,u,x)); s=U-L
    if X<L: s+=20*(L-X)
    if X>U: s+=20*(X-U)
    return round(100-25*s)
players={}
for f in sorted(glob.glob('play_*.json')):
    t=open(f).read(); m=re.search(r'\[.*\]',t,re.S); players[f[5:-5]]=json.loads(m.group(0))
perq={i:[] for i in Q}
print("プレイヤー別: 的中率 / 平均点 / 幅の中央値(倍)")
for n,a in players.items():
    h=0;pts=[];w=[]
    for r in [r for r in a if r["id"] in Q]:
        x=Q[r['id']]['answer']; hit=r['lo']<=x<=r['hi']; h+=hit; p=sc(r['lo'],r['hi'],x); pts.append(p); w.append(r['hi']/r['lo'])
        perq[r['id']].append((hit,p))
    w.sort(); print(f"  {n:8s} {h}/{len(pts)} ({h/len(pts):.0%})  平均{sum(pts)/len(pts):6.1f}点  幅{w[len(w)//2]:.1f}倍")
print("\n問題別: 的中人数 / 平均点")
for i,v in perq.items():
    print(f"  {i:2d} {sum(h for h,_ in v)}/{len(v)} {sum(p for _,p in v)/len(v):7.1f}  {Q[i]['q'][:30]}")
