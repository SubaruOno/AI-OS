# Installation guide / インストールガイド

## English

### 1. Choose either Claude or Codex

Both use the same workspace and the same workflows. You only need one to begin.

| Your computer | Claude | Codex |
|---|---|---|
| Windows | Install the [Claude desktop app](https://claude.ai/download), open Claude Code, then open this folder. | Install the [ChatGPT desktop app](https://chatgpt.com/download), open Codex, then open this folder. |
| macOS | Install the [Claude desktop app](https://claude.ai/download), open Claude Code, then open this folder. | Install the [ChatGPT desktop app](https://chatgpt.com/download), open Codex, then open this folder. |

Sign in with an account that has access to the product you chose. If your plan
does not include Claude Code or Codex, the app will tell you before setup begins.

### 2. Open the extracted folder

- **Windows:** right-click the downloaded zip, choose **Extract All**, then open
  the extracted folder in your chosen app.
- **macOS:** double-click the zip, then open the new extracted folder in your
  chosen app.

Do not open a file by itself. Open the whole folder so the assistant can see
`CLAUDE.md` or `AGENTS.md`, the skills, and the setup playbook.

### 3. Start the conversation

Send the same message in either app:

> Set up this AI OS for me.

Claude Code also offers `/install` as a shortcut. Plain language works in both
harnesses and is the recommended path for new users.

The assistant will:

1. detect the app and operating system;
2. ask whether the workspace is personal or for a business;
3. build the context through a guided interview;
4. set up local Git history and offer an optional private GitHub backup;
5. offer optional external tools and test each one you choose;
6. verify that Claude and Codex files still match.

The core interview normally takes 45 to 60 minutes. Completing every optional
integration and demonstration can take up to about three hours. Setup is
resumable.

### Passwords and API keys

Never paste a password, recovery code, token, or API key into the chat. When a
key is needed, the assistant should run:

```text
python scripts/set_secret.py KEY_NAME
```

On a Mac where `python` is not available, it may use `python3`. Enter the value
in the local terminal prompt. The input is hidden and saved only to `.env`,
which is excluded from Git.

### Switching later

The two apps share the same files. Close one app before editing the same work in
the other, then open the folder in the other app and say:

> Prime this workspace and catch me up.

You do not need to reinstall or copy skills into your home folder.

---

## 日本語

### 1. Claude または Codex を選びます

どちらを選んでも、同じワークスペースと同じ作業手順を使います。最初は片方だけで構いません。

| お使いのパソコン | Claude | Codex |
|---|---|---|
| Windows | [Claude デスクトップアプリ](https://claude.ai/download)をインストールし、Claude Code を開いてから、このフォルダを開きます。 | [ChatGPT デスクトップアプリ](https://chatgpt.com/download)をインストールし、Codex を開いてから、このフォルダを開きます。 |
| macOS | [Claude デスクトップアプリ](https://claude.ai/download)をインストールし、Claude Code を開いてから、このフォルダを開きます。 | [ChatGPT デスクトップアプリ](https://chatgpt.com/download)をインストールし、Codex を開いてから、このフォルダを開きます。 |

選んだ製品を利用できるアカウントでログインしてください。現在のプランで Claude Code
または Codex を利用できない場合は、設定を始める前にアプリ側で案内が表示されます。

### 2. 展開したフォルダを開きます

- **Windows:** ダウンロードした zip を右クリックし、「すべて展開」を選びます。
  展開後のフォルダを、選んだアプリで開いてください。
- **macOS:** zip をダブルクリックし、新しく作られたフォルダを選んだアプリで開きます。

ファイルを一つだけ開かないでください。`CLAUDE.md` または `AGENTS.md`、スキル、
設定手順を AI が読めるように、フォルダ全体を開きます。

### 3. 対話を始めます

どちらのアプリでも、同じメッセージを送ります。

> このAI OSをセットアップしてください。

Claude Code では `/install` も短縮操作として使えます。初めての方には、
両方で使える普通の日本語での依頼をおすすめします。

AI は次の順番で進めます。

1. 使用中のアプリと OS を確認します。
2. 個人用か事業用かを質問します。
3. 対話を通じて必要なコンテキストを作ります。
4. ローカルの Git 履歴を設定し、必要であれば非公開の GitHub バックアップを案内します。
5. 希望する外部サービスだけを接続し、一つずつ動作確認します。
6. Claude 用と Codex 用のファイルが一致していることを検証します。

基本の対話は通常45〜60分です。任意の外部サービスをすべて接続し、実演まで行うと、
合計で3時間ほどかかる場合があります。途中で止めても再開できます。

### パスワードと API キー

パスワード、復旧コード、トークン、API キーは、チャットに貼り付けないでください。
キーが必要になった場合、AI は次のコマンドを実行します。

```text
python scripts/set_secret.py KEY_NAME
```

Mac で `python` が使えない場合は `python3` を使います。表示されたローカルの
ターミナル画面に値を入力してください。入力内容は画面に表示されず、Git の対象外である
`.env` だけに保存されます。

### 後からアプリを切り替える場合

Claude と Codex は同じファイルを使います。同じ作業を二つのアプリで同時に編集せず、
一方を閉じてから、もう一方でフォルダを開き、次のように伝えてください。

> このワークスペースを読み込み、今の状況を教えてください。

再インストールや、ホームフォルダへのスキルのコピーは必要ありません。
