# Petacot企業Brain

> Petacotの3人が、会社資料、意思決定、作業記録を共有するためのワークスペース。

## What it does

Petacot企業Brainは、private GitHubリポジトリに置く会社資料と、Tursoに置く短い長期記憶を組み合わせています。会社情報、設立、事業計画、営業、顧客導入、財務、法務、会議、雛形を3人が同じ場所から参照できます。

会社資料の正本は[PetacotのINDEX](../../Petacot/brain/INDEX.md)です。AI-OSの[移行前資料](../private/terakoya-ai-consulting/company.md)は削除せず残していますが、2026年9月19日以降は両方を同時に編集しません。

## How it works

GitとTursoとledgerで、情報の役割を分けています。

| 情報 | 保存先 |
|---|---|
| 長い本文、PDF、PowerPoint、表、公式様式 | `~/Petacot/brain`の用途別フォルダ |
| 決定、仕様、会議要約、TODOの背景 | Tursoの`ai-brain` |
| 作業の節目 | `~/Petacot/brain/ledger/<name>.md` |
| すばる個人の作業履歴 | AI-OSの[ledger](../ledger/subaru.md) |
| APIキーとアクセストークン | `~/Petacot/brain/.env`（Git対象外） |

資料の入口は`~/Petacot/brain/INDEX.md`です。会社資料は`company/`、共同経営は`governance/`、設立は`incorporation/`、事業計画は`strategy/`、提案と営業は`sales/`へ置きます。

顧客への診断、計測、導入、効果報告は`delivery/`です。予算と実績は`finance/`、契約と専門家への確認は`legal/`、会議記録は`meetings/`、再利用する雛形は`templates/`に置きます。古い版は`archive/`です。

## Setup

リポジトリは`~/Petacot/brain`にあります。GitHubの`shun-petacot/petacot-brain`へアクセスできるアカウントが必要です。

Turso Brainの初期設定は、リポジトリで次を実行します。

```bash
./setup.sh
```

認証情報は`.env`に入り、Gitには追加されません。Tursoへ直接接続できる人は`scripts/brain.mjs`で検索と保存ができます。

```bash
node scripts/brain.mjs status
node scripts/brain.mjs search "料金" --project petacot
```

## Using it

会社の作業を始めるときは`INDEX.md`から対象フォルダを選びます。資料を更新したら、そのファイルを正本として保存し、重要な決定だけをTurso Brainへ1トピックずつ記録します。

意味のある作業が終わったら、本人のledgerへ次の形式で一行追加します。

```text
- YYYY-MM-DD HH:MM · <name> · <area>/<type> · <one-line summary>
```

すばるがPetacotリポジトリで作業する場合、利用可能ならAI-OSの`ledger/subaru.md`にも一行だけ残します。会社資料の本文はAI-OSへ自動複製しません。

## When it breaks

### 資料のリンクが切れる

ファイルを別フォルダへ移したときに起きます。Markdownのリンクは、リンクを書いたファイルからの相対パスで直します。初期移行時は18件を修正し、リンク切れ0件を確認しています。

### 同じ資料が二つに分かれる

AI-OSの移行前資料とPetacot側を両方で編集すると起きます。Petacot側を正本として更新し、AI-OS側は履歴として残します。

### Tursoへ保存できない

まず`node scripts/brain.mjs status`を実行します。トークンの期限が近い場合は、Turso CLIへログイン済みなら自動更新されます。直接接続できない場合は、利用可能なMCPまたはLINEのPetacot Brainを使います。

### 顧客の機密情報を置けない

現在のGitリポジトリは3人共有ですが、顧客データの保存条件は未確定です。契約、アクセス範囲、保管期間が決まるまで、個人情報、認証情報、顧客の原本データは追加しません。
