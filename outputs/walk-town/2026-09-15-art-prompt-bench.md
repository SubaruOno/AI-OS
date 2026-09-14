# てくてくまち 絵のタッチ決め用プロンプト(木のベンチ)

[MVP計画書](../../plans/2026-09-15-walk-town-app-mvp.md)のStep 2で使う。ChatGPTの画像生成に貼る。

## 1回目(タッチ違いを4案)

```
Create 4 different style variations of a single game item icon for a cozy iOS app called "Teku Teku Machi", a tiny lakeside town diorama.

Item: a small wooden park bench.

Requirements for every variation:
- Isometric view, 3/4 top-down, the same angle as a tile in an isometric grid
- The item sits on one square tile footprint, centered
- Transparent background, no ground shadow outside the tile, no text
- Soft, calm, warm mood, like a quiet walk by a lake in the late afternoon
- Readable at small size (about 80px on a phone)

Style variations:
1. Soft 3D clay / miniature figure look
2. Flat pastel illustration with thin outlines
3. Watercolor / hand-painted picture book look
4. Clean low-poly 3D

Show the 4 variations side by side, labeled 1-4 below each image.
```

## 決定(2026-09-15)

- タッチは案1(粘土のミニチュア風)。
- 足元の草の台ごと1マスとして使う。何も置いていないマス用に「草の台だけ」の絵も作る。

## 2回目(残りの小物を1枚ずつ)

基準のベンチ画像(案1)を毎回添付して貼る。

```
Use the attached bench image as the exact style reference (variation 1: soft 3D clay miniature).
Create ONE image of: [ITEM].

Keep identical to the reference:
- Same isometric angle and camera height
- Same square grass tile base: same size, shape, rounded edges, thickness, color, and small grass tufts
- The item stands centered on the tile and does not extend beyond the tile edges (tall items may go upward)
- Same soft clay material, rounded edges, warm afternoon light from the upper left, soft shadows
- Same color saturation and level of detail

Transparent background outside the tile. No text, no labels, no extra objects. Square 1024x1024.
```

[ITEM]に入れる英語(13枚):

1. empty tile only (the grass tile base with nothing on it)
2. a round leafy tree
3. a clump of lakeside reeds
4. a small flower bed with simple flowers
5. a street lamp with a round glass globe
6. a red cylindrical Japanese mailbox
7. a bicycle with a front basket, parked
8. a small wooden signpost with two blank arrow boards
9. a small lakeside coffee stand with an awning (rare)
10. a small soft-serve ice cream kiosk (rare)
11. a small wooden rowboat resting on a display stand (rare)
12. a small clock tower that fits on one tile (very rare)
13. event overlay: a sleeping cat curled up, no tile, transparent background, same clay style, sized to sit on the bench

紙袋の演出はMVPの2つ目の出来事用に後で作る。

## チェック項目

- 台の大きさ・角度がベンチと同じか(重ねて比べる)
- 小さく(80px)表示しても何か分かるか
- 色の濃さが1枚だけ浮いていないか
- 台の外にはみ出していないか

## 注意

- 任天堂作品の画風に似せる指示は入れない。
