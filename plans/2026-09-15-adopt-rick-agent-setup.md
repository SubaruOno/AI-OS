# Plan: Rick さんの設定メモから AI-OS に取り入れる

**Created:** 2026-09-15
**Status:** Implemented
**Request:** Rick さんの AI エージェント設定メモから、AI-OS に合う部分を取り入れる
**Purpose:** 記録の置き場を分野ごとにはっきりさせ、取り返しのつかない git 操作を仕組みで止める

---

## Overview

### What This Plan Accomplishes

Rick さんのメモの 4 項目（ファイル共有の方法、記憶の置き場、危険操作の hook、画像の置き場）を AI-OS の現状と照らし合わせ、合うものだけ入れます。入れるのは「情報の置き場ルール」「危険な git 操作を止める hook」「画像の置き場と命名ルール」の 3 つです。CLAUDE.md と AGENTS.md の symlink 化は見送ります。

### Why This Matters

すばるさんは大阪ガス、就活、SHIGABASE、walk-town を 1 つのワークスペースで扱っています。置き場のルールがないと、大阪ガスの内部情報がアプリのドキュメントに混ざるなど、分野をまたいだ誤記録が起きます。また Stop hook が毎ターン自動で commit と push をするため、force push や `git reset --hard` を誤って実行すると被害が大きくなります。

---

## Current State

### Relevant Existing Structure

- [CLAUDE.md](../CLAUDE.md) / [AGENTS.md](../AGENTS.md): 中身が同一のコピー。[verify_distribution.py](../scripts/verify_distribution.py) で一致を確認
- [build_distribution.py](../scripts/build_distribution.py): 配布物に symlink があるとエラーを出す（47 行目）
- [.claude/settings.json](../.claude/settings.json): Stop hook のみ。未 commit の変更があれば log workflow を強制する
- `context/`: you.md、people.md、tech-stack.md
- `private/`: job-hunt/、osakagas-worklog.md（Git 管理外）
- `docs/`: shigabase.md、walk-town.md
- `ledger/subaru.md`: 作業記録
- auto-memory: `~/.claude/projects/-Users-subaruono-AI-OS/memory/`
- 画像の置き場: 決まっていない

### Gaps or Problems Being Addressed

1. 分野ごとの置き場（大阪ガス・就活・アプリ）が constitution に書かれていない
2. auto-memory と context/ と private/ の役割分担が書かれていない
3. 危険な git 操作を止める仕組みがない
4. スクショや比較画像が scratchpad や outputs/ にばらばらに置かれる

---

## Integration Type

**Classification:** Constitution のルール追加と hook script
**Reasoning:** 新しい workflow は増やしません。置き場のルールは constitution に書き、危険操作の防止は hook で機械的に行います
**Location:** `CLAUDE.md`、`AGENTS.md`、`.claude/settings.json`、`.claude/hooks/guard-dangerous-bash.py`
**Auto-discovery:** 該当なし

---

## Proposed Changes

### Summary of Changes

- constitution に「情報の置き場」節を追加する（分野 × 情報の種類の表）
- constitution に「画像の置き場」節を追加する
- PreToolUse hook で危険な Bash コマンドを止める
- symlink 化は行わない（理由は Design Decisions に記載）

### New Files to Create

| File Path | Purpose |
|-----------|---------|
| `.claude/hooks/guard-dangerous-bash.py` | Bash コマンドを検査し、危険なものを exit 2 で止める |

### Files to Modify

| File Path | Changes |
|-----------|---------|
| `CLAUDE.md` | 「情報の置き場」「画像の置き場」「hook」の節を追加し、map に `.claude/hooks/` を追記 |
| `AGENTS.md` | CLAUDE.md と同じ内容にする |
| `.claude/settings.json` | PreToolUse (Bash) に hook を登録 |
| `INDEX.md` | hooks と画像フォルダへのリンクを追加 |
| `ledger/subaru.md` | 作業記録を追記 |

---

## Design Decisions

### Key Decisions Made

1. **symlink 化は見送る。** `build_distribution.py` が symlink を配布エラーにしており、Windows の teammate seat では symlink が壊れやすいためです。一致確認は既存の検証スクリプトで足ります。
2. **main への push は止めない。** Rick さんは main への直接 push を禁止していますが、この AI-OS は Stop hook で毎ターン main に push する設計です（auto-memory の feedback_auto_log_hook で決定済み）。止めるのは次の操作に絞ります。
   - `git push --force` / `-f` / `--force-with-lease`
   - `git reset --hard`
   - `git clean -f`（`-fd` などを含む）
   - `git checkout -- .` / `git restore .`（未 commit の変更をまとめて破棄する操作）
   - `git branch -D`
   - `rm -rf` のうち、対象が `/`、`~`、`$HOME`、ワークスペース直下、`.git` のもの
3. **hook は Python で書く。** scripts/ が Python で統一されており、Mac でも Windows でも動くためです。
4. **置き場は「分野」と「共有してよいか」の 2 軸で決める。**

| 情報 | 置き場 |
|---|---|
| すばるさん本人の経歴・好み・働き方 | [context/you.md](../context/you.md) |
| 就活の ES・選考状況・企業ごとのメモ | `private/job-hunt/` |
| 大阪ガスの勤怠・選手データ・チーム内部情報 | `private/`（`private/osakagas-worklog.md` など）。tracked なファイルには書かない |
| アプリ（SHIGABASE、walk-town）の設計・使い方 | `docs/<app>.md`。コードの正本は各アプリのリポジトリ |
| 完了した作業 | `ledger/subaru.md`（1 行、日付付き） |
| 進行中の計画 | `plans/` |
| assistant への作業上のフィードバック | auto-memory。恒久的なルールになったら constitution に移し、memory からは消す |

   auto-memory には作業ログや進捗を書きません（ledger と重複するため）。
5. **画像の置き場は `~/Pictures/ai/`、1 階層だけ。** ファイル名は `YYYYMMDD-HHMM-<project>-<what>.<ext>`（JST）。成果物そのもの（App Store 用スクショなど）はアプリのリポジトリが正本で、ここにはコピーを置きます。不要になったら消します。
6. **constitution に数値や件数を書かない。** 数値は、どのファイルを見れば分かるかだけを書きます。

### Alternatives Considered

- **分野ごとにワークスペースを分ける:** 今の量なら 1 つのワークスペースで管理できます。分けると prime と ledger が 2 系統になり、手間が増えるので見送ります。
- **hook をルールだけで代用する:** Rick さんのメモのとおり、ルールだけでは実行されてしまうことがあるので、hook にします。

### Open Questions (if any)

- 画像の置き場を `~/Pictures/ai/` にしてよいか（ワークスペース外なので Git には入りません）

---

## Step-by-Step Tasks

### Step 1: hook script を作る

**Actions:**

- `.claude/hooks/guard-dangerous-bash.py` を作る。stdin の JSON から `tool_input.command` を読み、Design Decision 2 のパターンに正規表現で一致したら、理由を stderr に日本語で出して exit 2 で終了する。一致しなければ exit 0
- 誤検知を避けるため、`git push origin main` のような通常の push や `rm -rf node_modules` は通す

**Files affected:** `.claude/hooks/guard-dangerous-bash.py`

### Step 2: hook を登録する

**Actions:**

- `.claude/settings.json` に `PreToolUse`、matcher `Bash`、command `python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/guard-dangerous-bash.py"` を追加する。既存の Stop hook は残す

**Files affected:** `.claude/settings.json`

### Step 3: constitution を更新する

**Actions:**

- CLAUDE.md の「Working with the ledger」の前に「Where information lives」節を追加し、Design Decision 4 の表と auto-memory のルールを書く
- 「Images for review」節を追加し、Design Decision 5 を書く
- 「Guardrails」節を追加し、hook の場所と止める操作の種類を書く
- map に `.claude/hooks/` の行を追加する
- CLAUDE.md を AGENTS.md にコピーする

**Files affected:** `CLAUDE.md`、`AGENTS.md`

### Step 4: INDEX.md を更新する

**Actions:**

- hook script へのリンクを追加する

**Files affected:** `INDEX.md`

### Step 5: 検証する

**Actions:**

- hook に危険なコマンドの例を JSON で渡し、exit 2 になることを確認する（force push、reset --hard、clean -fd、branch -D、rm -rf ~）
- 通常のコマンド（git status、git push origin main、rm -rf node_modules）が exit 0 になることを確認する
- `python3 scripts/verify_distribution.py` を実行して通ることを確認する
- 新しいセッションで無害なコマンドを実行し、hook が作業を妨げないことを確かめる

### Step 6: 記録する

**Actions:**

- `ledger/subaru.md` に build 行を追記し、log workflow を実行する

---

## Connections & Dependencies

### Files That Reference This Area

- [.claude/commands/log.md](../.claude/commands/log.md): commit と push を行う。hook は force を使わないので影響なし
- [scripts/verify_distribution.py](../scripts/verify_distribution.py): CLAUDE.md と AGENTS.md の一致を確認

### Updates Needed for Consistency

- CLAUDE.md と AGENTS.md の同時更新
- INDEX.md

### Impact on Existing Workflows

Stop hook による自動 commit と push はこれまでどおり動きます。止まるのは破壊的な git 操作と危険な削除だけです。

---

## Validation Checklist

- [ ] 危険コマンド 5 種で hook が exit 2 を返す
- [ ] 通常コマンド 3 種で hook が exit 0 を返す
- [ ] verify_distribution.py が通る
- [ ] CLAUDE.md と AGENTS.md が一致している
- [ ] constitution 内の新しいリンクがすべて実在するファイルを指している

## Success Criteria

1. force push と `git reset --hard` が assistant から実行できない
2. 新しい情報をどこに書くか、constitution の表を見れば 1 か所に決まる
3. レビュー用の画像が `~/Pictures/ai/` に命名ルールどおり保存される

## Notes

- Rick さんの ja-lint（不自然な日本語の NG 辞書を使う hook）は、[writing-style](../reference/writing-style.md) と役割が重なるので今回は見送ります。ES の文体で同じ指摘が繰り返されるようなら、改めて検討します。
- 元のメモ: `~/Downloads/ai-workflow-handout.md`（ワークスペース外）
