# SHIGABASE試合記録機能の進捗

**更新日:** 2026-09-29 00:18 JST
**作業先:** `~/Projects/TerakoyaAI/ShigabaseiOS`

## 作ったもの

- `supabase/config.toml` を追加し、既存の `intern-info-deno` とポートが重ならないよう API 55421、DB 55422、Studio 55423 などに設定しました。
- production 型 snapshot からローカル専用 baseline migration を作成しました。players、opponent_teams、games、pitches、profiles、user_roles、app_role、has_role と既存 migration に要る周辺表を含みます。ファイル冒頭に本番へ push しない注意を書きました。
- 既存 migration の初期適用を成立させるため documents を baseline に追加し、投手集計関数の返却列変更をローカル migration 内の `DROP FUNCTION` + `CREATE` に変更しました。
- scoring マスタ、試合、lineup、play、substitution、audit log と RLS を追加しました。試合中の正本は入力イベントです。
- seed に結果39、作戦53、画面表示球種13、牽制詳細19、メモ15、天気18、守備位置16、ダミーチーム2、ダミー選手24と経歴24を追加しました。実名は入れていません。
- `lib/scoring/engine.ts` に prototype の純粋状態計算を移し、`lib/scoring/export191.ts` に保存ファイル順の191列ヘッダーと行出力を追加しました。

## ローカルでの実行

```sh
cd ~/Projects/TerakoyaAI/ShigabaseiOS
supabase start
supabase db reset
npm test
```

ローカル Supabase は 55421/55422/55423 を使います。別プロジェクトの `intern-info-deno` は停止していません。

## 検証

- `supabase db reset`: 成功。baseline、既存 migration、scoring schema、seed が最後まで適用されました。
- SQL counts: results 39、plans 53、ball types 13、pickoff details 19、memos 15、weather 18、positions 16、dummy roster 24。
- `npm test`: 2ファイル14テスト成功。交代と四球、代走、盗塁/牽制アウト、申告敬遠、ボーク、打撃妨害警告、野手選択、単打、本塁打、タイブレーク、3アウト、191列の順と出力を確認しました。
- `npx tsc --noEmit`: 既存の `app/opponent-pitchers/[name].tsx` の型アサーション1件と、既存 Supabase Edge Function の Deno URL import / `Deno` 未定義で失敗します。今回追加した scoring ファイルからの型エラーは表示されませんでした。

## 未完了と判断待ち

- Git の branch 参照・index 更新が OS sandbox で `Operation not permitted` となり、`feature/scoring-local` の作成と小刻み commit ができていません。作業ファイルは現時点で main の未コミット変更です。権限が直ったら feature branch を作って変更を commit してください。push/merge は行っていません。
- BASS球種37件のうち、調査ノートには入力画面の13件と集計項目しか残っておらず、残り24件の正確な名前・属性が未確認です。seed は13件に留めています。元のBASS管理データまたは完全なリストが必要です。
- plan 53件は調査表が全項目を載せていないため、メニュー16件とノート記載の詳細・代表値を組み合わせています。個別の旧Excelラベルや成功/失敗フラグは再照合が要ります。
- `scoring_games` の表示番号と season/kind/week/day/game_number の一意性が同時に必須になっています。大会外の練習試合や番号体系を決める際に、これらの採番方法を確認してください。
- `games` と `pitches` へ scoring から同期する実装は未作成です。設計では正本を scoring 側に置くことが決まっていますが、要件本文の「same-shape write」への変換は次段階です。
- RLS は analyst/admin 書込、認証済み閲覧の初期形です。`scoring_is_team_member` はチーム単位のユーザー所属表が未設計なため、現在 own-team または analyst/admin に閲覧を許しています。誰をチームメンバーとみなすか、人の決定が必要です。
- 191列の出力は基本の状態・スタメン・scoreboard を実装しました。交代後の最新守備履歴、H/R表記、全列の旧語彙変換と守備名表示は未完成です。
