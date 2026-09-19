# Plan: Petacot企業Brainの初期構築

**Created:** 2026-09-19
**Status:** Implemented
**Request:** 既存のPetacot Brainを3人で使う会社共有ワークスペースへ広げ、AI-OSの関連資料を整理してコピーする。
**Purpose:** Petacotの会社情報と実務資料を共同経営者が同じ場所から参照・更新でき、意思決定と作業経緯も残る状態を作る。

---

## Overview

### What This Plan Accomplishes

`~/Petacot/brain`に会社資料用の分類、索引、ledger、運用ルールを追加する。AI-OSにあるPetacot関連資料は現行版と旧版を分けてコピーし、今後はPetacot側を会社資料の正本として扱う。

### Why This Matters

現在の資料はすばる個人のAI-OSに偏っている。3人が共通の資料と決定履歴を使えるようにすることで、設立、営業、顧客導入の引き継ぎが会話や個人PCに依存しなくなる。

## Current State

### Relevant Existing Structure

- `~/Petacot/brain`はprivate GitHubリポジトリで、Turso Brainの設定、プラグイン、CLIを管理している。
- `AGENTS.md`と`AI_BRAIN.md`には、すばるの重要事項と進捗をTursoへ自動保存する未コミットの追記がある。
- `private/terakoya-ai-consulting/`に約33MBの会社情報、設立、提案、調査、営業候補、公式様式、生成スクリプトがある。
- 設立書類は旧所在地版、北本市版、作業用複製があり、提案書も複数世代ある。

### Gaps or Problems Being Addressed

- 会社資料を共同編集するフォルダと索引がない。
- ファイル本文とTursoの短い記憶の使い分けが定義されていない。
- 現行版と旧版が混在している。
- Petacotでの作業をAI-OSの個人ledgerへ残す方法が明文化されていない。

## Integration Type

**Classification:** N/A（共有ワークスペースの構造変更）
**Reasoning:** 既存Brainリポジトリに会社資料管理を追加するもので、新しいSkillや外部API連携ではない。
**Location:** `~/Petacot/brain`
**Auto-discovery:** `AGENTS.md`と`CLAUDE.md`を各ハーネスが自動で読む。

## Proposed Changes

### Summary of Changes

- 会社資料用の10分類と`archive/`を作る。
- `INDEX.md`に正本、用途、更新ルールを記載する。
- AI-OSから現行資料と旧版資料を分類してコピーする。
- `AGENTS.md`と`CLAUDE.md`を同一内容にし、会社資料とledgerの運用を追加する。
- `README.md`へ企業Brainとしての使い方を追加する。
- `ledger/`に3人の記録ファイルを作る。
- 認証情報、個人情報、生成物の扱いを`.gitignore`と運用文書で明確にする。

### New Files to Create

| File Path | Purpose |
|-----------|---------|
| `INDEX.md` | 会社情報の入口と正本の案内 |
| `company/README.md` | 会社情報の管理範囲 |
| `governance/README.md` | 役割、持分、会議、意思決定の管理範囲 |
| `incorporation/README.md` | 設立手続きと公式様式の案内 |
| `strategy/README.md` | 事業計画、調査、価格、収支の案内 |
| `sales/README.md` | 提案、候補企業、商談資料の案内 |
| `delivery/README.md` | 診断、計測、導入、報告の案内 |
| `finance/README.md` | 予算、経費、売上の案内 |
| `legal/README.md` | 契約、データ取扱い、専門家確認の案内 |
| `meetings/README.md` | 会議資料と議事録の命名規則 |
| `templates/README.md` | 再利用する雛形の案内 |
| `archive/README.md` | 旧版を残す理由と参照上の注意 |
| `ledger/README.md` | 作業記録の形式と書き分け |
| `ledger/subaru.md` | すばるのPetacot作業記録 |
| `ledger/shun.md` | ShunさんのPetacot作業記録 |
| `ledger/rick.md` | 木村さんのPetacot作業記録 |

### Files to Modify

| File Path | Changes |
|-----------|---------|
| `AGENTS.md` | 企業Brainの構成、情報の置き場所、ledger、すばるのAI-OS記録を追加 |
| `CLAUDE.md` | `AGENTS.md`と同じ内容に統一 |
| `README.md` | Turso専用という説明を企業Brain全体の説明へ広げる |
| `.gitignore` | macOSの不要ファイルと一時生成物を除外 |
| AI-OSの`docs/_index.md` | Petacot企業Brainの参照先を追加 |
| AI-OSの`ledger/すばる.md` | 初期構築の完了記録を追加 |

### Files to Delete (if any)

なし。AI-OS側の原本も削除しない。

## Design Decisions

### Key Decisions Made

1. **既存Brainを会社ワークスペースへ広げる**: Tursoの記憶と会社資料を同じGitリポジトリから扱える。
2. **Petacot側を今後の正本にする**: AI-OSとの双方向ファイル同期を避け、版の食い違いを防ぐ。
3. **ファイルとTursoを使い分ける**: 長文・成果物はGit、短い決定・仕様・TODO背景はTursoへ置く。
4. **すばるだけAI-OSにも進捗を残す**: 会社の本文を複製せず、個人ledgerへ一行を追加する。
5. **旧版は削除せずarchiveへ置く**: 意思決定の経緯を追える状態を保つ。

### Alternatives Considered

`~/Petacot/company`を別リポジトリにする案は、Brainと会社資料の入口が分かれるため採用しない。AI-OSとの全ファイル自動同期は、同時編集時に正本が分裂するため採用しない。

### Open Questions (if any)

なし。利用者、対象範囲、正本、実装まで進めることは本人確認済み。

## Step-by-Step Tasks

### Step 1: 既存変更を保護する

作業前のGit状態を記録し、`AGENTS.md`と`AI_BRAIN.md`の未コミット変更を維持する。

**Actions:**

- 現在の差分とHEADを確認する。
- 認証情報を表示・コピーしない。

**Files affected:**

- なし

### Step 2: 共有フォルダと運用文書を作る

会社情報の分類と各フォルダの役割を定義する。

**Actions:**

- 10分類、archive、ledgerを作る。
- `INDEX.md`と各READMEを書く。
- 正本、命名、機密情報、Tursoとの使い分けを記載する。

**Files affected:**

- `INDEX.md`
- 各分類の`README.md`
- `ledger/*.md`

### Step 3: AI-OSの資料を整理してコピーする

現行版を用途別に置き、旧版と旧所在地向け書類をarchiveへ分ける。

**Actions:**

- 会社情報と設立判断を`company/`と`governance/`へコピーする。
- 北本市版の公式様式と設立ガイドを`incorporation/`へコピーする。
- 最新の事業計画、調査、提案書、営業候補、計測資料を対応する分類へコピーする。
- 古い提案書、旧所在地版、生成スクリプトを`archive/initial-import-2026-09-19/`へコピーする。
- `.DS_Store`とZIPの重複は移行対象から外す。

**Files affected:**

- `company/`
- `governance/`
- `incorporation/`
- `strategy/`
- `sales/`
- `delivery/`
- `archive/initial-import-2026-09-19/`

### Step 4: リポジトリの指示と入口を更新する

今後のセッションが同じルールで作業できるようにする。

**Actions:**

- `AGENTS.md`へ企業Brainの運用規則を追加する。
- `CLAUDE.md`を同一内容にする。
- `README.md`を企業Brain全体の説明へ更新する。
- `.gitignore`へ`.DS_Store`と一般的な一時ファイルを追加する。

**Files affected:**

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `.gitignore`

### Step 5: AI-OSとの接続を記録する

AI-OSからPetacotの正本へ辿れるようにする。

**Actions:**

- `docs/_index.md`へPetacot企業Brainの行を追加する。
- AI-OSのledgerへ初期構築を記録する。
- Petacotの`ledger/subaru.md`にも初期移行を記録する。

**Files affected:**

- AI-OSの`docs/_index.md`
- AI-OSの`ledger/すばる.md`
- `ledger/subaru.md`

### Step 6: 検証する

共有ワークスペースとして実際に辿れるか、不要情報が混入していないか確認する。

**Actions:**

- `INDEX.md`から全リンクを辿る。
- `AGENTS.md`と`CLAUDE.md`の一致を確認する。
- `.env`、APIキー、Git管理対象の`.DS_Store`がないことを確認する。
- 現行資料とarchiveの分離を確認する。
- 2回目のコピーを想定して、同名ファイルの扱いが明確か確認する。

**Files affected:**

- なし

## Connections & Dependencies

### Files That Reference This Area

- AI-OSの`docs/_index.md`
- AI-OSの`private/terakoya-ai-consulting/`
- Petacotの`AGENTS.md`、`CLAUDE.md`、`AI_BRAIN.md`、`README.md`

### Updates Needed for Consistency

Petacot側の`AGENTS.md`と`CLAUDE.md`を一致させる。AI-OS側は会社資料の正本がPetacotへ移ったことを索引に反映する。

### Impact on Existing Workflows

Turso Brainの保存・検索方法は変わらない。会社資料を扱うセッションでは、Git内の本文とTursoの要点を併用し、意味のある作業完了後にPetacotのledgerへ記録する。

## Validation Checklist

- [ ] 予定した全フォルダとREADMEが存在する。
- [ ] 現行の会社情報、設立資料、事業計画、提案、営業候補、計測資料が正しい分類にある。
- [ ] 旧版と旧所在地資料がarchiveに分離されている。
- [ ] `INDEX.md`の全リンクが解決する。
- [ ] `AGENTS.md`と`CLAUDE.md`が同一である。
- [ ] 認証情報と`.DS_Store`がGit管理対象に入っていない。
- [ ] AI-OSとPetacotの両ledgerに初期構築が記録されている。

## Success Criteria

1. 3人が`INDEX.md`からPetacotの主要資料へ到達できる。
2. 今後の資料の保存場所と正本が運用文書だけで判断できる。
3. Turso、Petacot ledger、すばるのAI-OS ledgerの役割が分離されている。
4. 既存のBrain機能と未コミット変更が失われていない。

## Notes

顧客案件が始まったら、顧客ごとのフォルダには契約上共有可能な情報だけを置く。機密性が高い資料の暗号化やアクセス分離は、実顧客データを保存する前に別途決める。

---

## Implementation Notes

**Implemented:** 2026-09-19

### Summary

Petacot Brainに会社資料用の分類、INDEX、3人分のledger、運用ルールを追加した。AI-OSの約33MBの資料から、現行資料を用途別に、旧提案書・旧所在地書類・生成スクリプトをarchiveへ整理して移行した。Tursoには進捗を#50として保存した。

### Deviations from Plan

`AGENTS.md`と`CLAUDE.md`はハーネス固有の記法とセットアップ説明が異なるため、完全一致にはせず、会社資料の運用ルールだけを両方へ追加した。重複ZIPと同一内容の作業用複製は移行せず、展開済みの正本だけを残した。

### Issues Encountered

初回検査で、移動したMarkdown資料に18件の相対リンク切れが見つかった。新しい分類に合わせてリンクを直し、再検査で0件になった。
