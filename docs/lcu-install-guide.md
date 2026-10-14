# Claude Code で Codex の Computer Use を使う（LCU）導入手順

この文書は、受け取った人の AI エージェント（Claude Code）が読んで実行するためのもの。
人間は下の「AI に渡す一文」を Claude Code に貼るだけでよい。

```text
~/Downloads/lcu-computer-use-install.md を読んで、この手順どおりに LCU を入れて。
macOS の権限許可など、私が手で操作する必要があるところは都度教えて。
```

---

## これは何か

- **LCU** は OSS で、ChatGPT デスクトップアプリに同梱された Codex の Computer Use の実行環境を Claude Code の MCP ツールとして呼べるようにする。
  リポジトリは https://github.com/amontlabs/lcu 。
- 入れると Claude Code に `mcp__lcu__js` / `mcp__lcu__js_reset` が増え、デスクトップアプリの画面取得・クリック・入力ができる。
- ChatGPT へのサインインと Codex の認証は**要らない**。ただし ChatGPT アプリ本体はインストールしておく必要がある（実行環境がアプリの中にあるため）。
- 送り主（rick）の環境では v0.11.3 を Claude Code に登録して動かしている（2026-10-14 時点）。Chrome 操作と音声録音はオフ、承認モードは既定の `ask`。

---

## エージェント向け：実行手順

### 0. 前提チェック（満たさなければ止めて人間に報告）

1. **Apple Silicon の Mac か**: `uname -sm` が `Darwin arm64`。Intel Mac は非対応。
2. **ChatGPT デスクトップアプリがあるか**: `/Applications/ChatGPT.app` が存在する。
   無ければ https://chatgpt.com/download/ から入れてもらう。LCU はアプリを自動で入れない。
3. **Claude Code のバージョン**: `claude --version` が 2.1.287 以上（Claude アプリの Code タブなら同梱版で可）。
   古いと承認ペイン（後述）が出ないので、先に更新してもらう。
4. **ホームフォルダのパス長**: `/Users/` の後ろが **13 文字以内**か確認する（`echo $HOME`）。
   長いと ChatGPT 側の署名済みヘルパーがソケットを作れず、全呼び出しが `Sky Computer Use native pipe startup failed` で失敗する。LCU 側では直せない。

### 1. 最新リリースを落として SHA-256 を検証する

ターミナルで（作業用の空ディレクトリで）実行する。checksum が **OK** と出たときだけ先へ進む。

```sh
LCU_TARGET=darwin-arm64
LCU_TAG=$(curl -fsSI -o /dev/null -w '%{redirect_url}' https://github.com/amontlabs/lcu/releases/latest)
LCU_TAG=${LCU_TAG##*/}
LCU_ARCHIVE="lcu-${LCU_TAG#v}-${LCU_TARGET}.tar.gz"
LCU_URL="https://github.com/amontlabs/lcu/releases/download/$LCU_TAG"
mkdir -p lcu-release && cd lcu-release &&
curl -fLO "$LCU_URL/$LCU_ARCHIVE" &&
curl -fLO "$LCU_URL/$LCU_ARCHIVE.sha256" &&
shasum -a 256 -c "$LCU_ARCHIVE.sha256" &&
tar -xzf "$LCU_ARCHIVE" &&
cd "${LCU_ARCHIVE%.tar.gz}"
```

GitHub の「Source code」zip はインストールできない。必ずリリースの tar.gz を使う。

### 2. インストールして Claude Code に登録する

展開したディレクトリの中で、**デスクトップにログインしている本人のアカウント**で実行する。

```sh
./scripts/install.sh --agent claude-code
```

- 対話式で走らせるのが基本。登録のあと、macOS の権限（アクセシビリティ / 画面収録）の案内が出る。
- エージェントが非対話で走らせる場合は `--yes` を付け、終わったら人間にデスクトップのターミナルで次を実行してもらう:
  ```sh
  ~/.local/share/lcu/current/bin/lcu doctor
  ```
- Chrome 操作（`--chrome`）・音声録音（`--audio`）は**本人が頼んだときだけ**付ける。
- `--approval auto` は無人の VM / CI 向け。普通の Mac では付けない。

インストール先は `~/.local/share/lcu`。`lcu` コマンドは PATH に入らないので、常に `~/.local/share/lcu/current/bin/lcu` で呼ぶ。

このとき次のものが入る:
- `~/.claude.json` の MCP サーバー `lcu`
- `~/.claude/settings.json` の LCU 用 hook
- `~/.claude/skills/lcu-approve`（アプリ操作の承認を Claude Code 内のペインで出す mod）

### 3. macOS の権限を許可する（人間の作業）

システム設定 → プライバシーとセキュリティ で、セットアップが表示した ChatGPT アプリ / Computer Use ヘルパーに対して以下を許可する。

- **アクセシビリティ**
- **画面収録とシステムオーディオ録音**（OS によっては「画面収録」）

`lcu doctor` は権限が付いているかまでは判定できない（「verifiable でない」と出るのは正常）。exit 0 なら次へ。

### 4. Claude Code を再起動して動作確認

1. Claude Code を完全に終了して起動し直す（MCP と hook を読み直すため）。
2. テキストエディットで空の書類を開いておく。
3. Claude Code にこう頼む: 「LCU を使ってテキストエディットのウインドウのスクリーンショットを撮って」
4. 初回はアプリごとの承認ペイン（**Computer use approval**）が出る。人間が選ぶ:
   - **Allow this conversation**: この会話だけ許可
   - **Always allow**: そのアプリを常に許可
   - **Deny**: 拒否
5. 返ってきた画像が実際の画面と一致すれば完了。

**インストールと登録が通っただけでは「動いた」と報告しない。** 4 の画像確認までやって初めて完了。

---

## 使い方の補足

| やりたいこと | コマンド / 操作 |
|---|---|
| 常に許可したアプリの一覧 | `~/.local/share/lcu/current/bin/lcu apps` |
| アプリを常に許可 / 取り消し | `lcu apps allow <アプリ名>` / `lcu apps revoke <アプリ名>`（Touch ID かパスワードを求められる） |
| 承認済みアプリのパネル | Claude Code で `/computer-use-apps` |
| 状態確認 | `lcu status` / `lcu doctor` |
| 更新 | `lcu update`（そのあと Claude Code を再起動、古い版は `lcu prune --yes` で掃除） |
| ターンをまたいで使う（バックグラウンドのサブエージェント等） | `lcu cross-turn on`（既定はオフ。rick もオフ） |

- ターミナル（Terminal.app / iTerm2）は Computer Use の対象外。エージェントを動かしているアプリ自身も承認されない。
- Claude アプリを使う場合も、登録は Claude Code 経由（上の手順）で行う。設定 → コネクタ（`claude_desktop_config.json`）に `lcu` を足すと承認が壊れる。

## よくある詰まり

| 症状 | 対処 |
|---|---|
| `Sky Computer Use native pipe startup failed` | ① ホームのパス長が 13 文字を超えていないか確認。② ChatGPT アプリの自動更新直後なら、数分待つか、アクティビティモニタで `SkyComputerUseService` を終了して再試行 |
| `Computer Use was not approved` | Claude Code が 2.1.287 未満か、`~/.claude/skills/lcu-approve` が無い。Claude Code を更新して `lcu setup --agent claude-code` を再実行 |
| `Computer Use is unavailable because the current turn ended` | バックグラウンドのサブエージェントから呼んでいる。必要なら `lcu cross-turn on` |
| ツールが出てこない | Claude Code を再起動したか確認。`claude mcp list` に `lcu` があるか確認 |

## アンインストール

1. `claude mcp remove lcu`
2. `rm -r ~/.claude/skills/lcu-approve`
3. `~/.claude/settings.json` から LCU の hook と `mcp__lcu__*` の権限を削除
4. `rm -rf ~/.local/share/lcu ~/.local/state/lcu`

ChatGPT アプリ側は何も変更されていないので、戻す作業は無い。

## 一次資料

- README: https://github.com/amontlabs/lcu
- インストールガイド（この文書の元）: https://raw.githubusercontent.com/amontlabs/lcu/main/docs/INSTALLATION.md

この手順と公式ガイドが食い違ったら、公式ガイドを優先すること。
