# スイング→打球の変換効率の指標（2026-10-31）

BLASTのバットスピードと、RapsodoやTrackmanの打球速度を1球ずつ対応させたときに出せる指標をまとめる。U-23直前合宿（10/31）で初めて使った。大阪ガスのBLASTでも、打球のデータと時刻で対応させれば同じ計算ができる。

## 指標

| 指標 | 求め方 | 目安 |
|---|---|---|
| 打球速度÷バットスピード | 打球速度 ÷ バットスピード | 試合の投球を打つ場合はおよそ1.2〜1.4。球が遅いと低めに出る |
| 衝突効率 | (打球速度 − バットスピード) ÷ (バットスピード ＋ 球速) | 芯で捉えるとおよそ0.2 |
| スクエアアップ率 | 打球速度 ÷ (1.23×バットスピード ＋ 0.2116×球速) | MLBは80%以上を「スクエアアップ」と数える |
| 打球角度とアッパースイング度の差 | \|打球角度 − アッパースイング度\| | 小さいほど、スイングの向きのまま球の真ん中を打てている |

- 衝突効率の式は、打球速度＝衝突効率×球速＋(1＋衝突効率)×バットスピード（Alan Nathan）を逆に解いたもの。
- スクエアアップ率の係数は、FanGraphsのBen Clemensが公開した近似式。MLBの正式な計算式ではない。
- バットスピードと球速は、どちらもインパクトの時点の速さで考える。球速が分からないときは目安を置き、±10km/h動かして結果がどれだけ変わるかを添える。
- MLB（木製バット・試合の投球）を前提にした近似式なので、MLBの数値とそのまま比べず、チーム内の比較に使う。BLASTとStatcastではバットスピードの測り方が違い、100%を超える打球が出ることがある。

## 10/31に分かったこと

- 119球で、打球速度÷バットスピードは平均1.23、スクエアアップ率は平均86%（球速100km/hとして）。
- 効率といちばん関係していたのは、打球角度とアッパースイング度の差。同じ選手の中で比べても相関は−0.56だった。バットスピード、オンプレーン効率、アッパースイング度そのものとの関係は弱かった。
- 計算の実物は `~/野球/U23ワールドカップ2026/09_直前合宿_202610/` のエクセル（「変換効率」シート）と make_report.py にある。

## 出典

- [MLB Glossary: Squared-up Rate](https://www.mlb.com/glossary/statcast/squared-up)
- [FanGraphs: When Squaring It up Goes Sideways](https://blogs.fangraphs.com/when-squaring-it-up-goes-sideways)
- [The Hardball Times: The Physics of Batting Practice](https://tht.fangraphs.com/the-physics-of-batting-practice/)
- [SABR: The Influence of Swing Machines on Batted Ball Exit Velocity in MLB](https://sabr.org/journal/article/the-influence-of-swing-machines-on-batted-ball-exit-velocity-in-mlb/)
- [Blast Motion: What is attack angle in baseball](https://blastmotion.com/blog/what-is-attack-angle-in-baseball/)（アッパースイング度の目安は多くの打者で6〜14°）
