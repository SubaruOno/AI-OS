# Explore: Petacot企業Brain

**Created:** 2026-09-19
**Status:** Explored
**Origin:** 3人で共有するPetacotの企業情報と作業記録を、既存のBrainリポジトリへ集約する。

---

## Vision

`~/Petacot/brain`を、Tursoの共有メモリ機能に加えて会社資料も扱うPetacotの共有ワークスペースにする。会社の正式情報、設立、戦略、営業、導入、財務、法務、会議、作業記録を3人が同じ場所から参照できる状態を作る。

## Problem Statement

Petacotの資料は現在、すばる個人のAI-OS内にあり、共同経営者が継続して参照・更新できない。Turso Brainには短い意思決定を保存できるが、提案書、設立書類、調査資料などのファイルを管理する場所がない。

## Proposed Solution

### What It Does

既存の`petacot-brain`リポジトリに会社資料用の分類、索引、作業記録ルールを追加する。AI-OSの原本は残し、今後の会社資料はPetacot側を正本にする。

### How It Works

3人は`~/Petacot/brain`で会社業務を行う。長期的な決定やTODOの背景はTursoへ保存し、完成した資料は用途別フォルダへ置き、作業の節目は`ledger/`へ記録する。すばるの作業は、利用可能な場合にAI-OSの個人ledgerへも短く記録する。

### What It Produces

会社資料の分類、入口となる`INDEX.md`、運用ルール、初期移行済み資料、重複を分けたarchive、3人分のledgerを作る。

## Scope

### Minimum Viable Version

会社資料用フォルダ、索引、運用ルール、AI-OSにある現行資料のコピー、旧版のarchive分離、リンク検査を用意する。

### Full Vision

営業、顧客導入、財務、法務、会議の資料を継続的に蓄積し、ファイルとTursoの記憶を使い分ける。各メンバーの作業履歴をledgerで追えるようにする。

### Components

- 共有フォルダ構成: Small
- 初期資料の選別とコピー: Medium
- 運用ルールと索引: Medium
- AI-OSへの記録連携: Small
- 検査と移行確認: Small

### Out of Scope

顧客の認証情報、APIキー、個人の就職活動資料は移行しない。Tursoデータベースの構造変更やGitHub権限変更も今回の対象外とする。

## Technical Considerations

既存リポジトリにはすばるの自動記録ルールに関する未コミット変更があるため、保持して統合する。`.env`と認証情報はGit対象外のままにする。バイナリ資料が多いためGit履歴は大きくなるが、初期移行分は約33MBで運用可能な範囲に収まる。AI-OSとの全ファイル自動同期は正本が分裂するため行わない。

## Integration Type

**Classification:** N/A（共有ワークスペースの構造変更）
**Reasoning:** 新しい外部連携ではなく、既存Gitリポジトリの資料管理範囲と運用ルールを広げる変更である。
**Location:** `~/Petacot/brain`
**Trigger keywords:** 該当なし

## Connections

Tursoの`memories`は短い意思決定、仕様、会議要約、TODOの背景を保持する。Git内のファイルは提案書、公式様式、調査、計測資料など本文を保持する。AI-OSは移行前資料とすばる個人の作業記録を保持する。

## Next Steps

合意済みの方針に基づき、実装計画を作成して初期移行を実施する。

## Discovery Notes

- 利用者はすばる、Shunさん、木村さんの3人。
- 法人設立だけでなく、提案、顧客、営業、財務、議事録まで対象にする。
- AI-OS側の資料は削除しない。
- `brain`自体を会社共有ワークスペースへ広げる案を採用した。
- Petacot側を今後の会社資料の正本とし、AI-OS側は個人記録と移行前資料を保持する。
