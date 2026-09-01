# What this folder is / このフォルダについて

## English

This is a shareable AI operating-system workspace assembled from Liam Ottley's
AI Makeover template and the materials distributed at Operator Day in Porto
Montenegro, 29–31 July 2026.

The **core workspace supports Claude Code and Codex on Windows and macOS**.
`CLAUDE.md` and `AGENTS.md` are identical constitutions. The working skills are
also identical real-file mirrors:

- Claude Code loads `.claude/skills/`.
- Codex loads `.agents/skills/`.
- `scripts/sync_harness_skills.py` keeps them matched inside the project.

Nothing needs to be installed into a user's home folder. Natural-language
requests work in both tools; Claude Code's slash commands remain optional
shortcuts.

The workspace can be installed for a business or for one person. Both modes use
the same work rhythm, ledger, build loop, and capabilities. A personal setup can
add business context later without starting again.

### Language support

The static user install guides are written in English and Japanese. During
setup and normal work, the assistant replies in the language used by the person.
The third-party source packs and their skills remain in their authors' original
language. Translating those skill bodies is a separate editorial decision; this
edition does not silently rewrite them.

### What is included

- The core template, context structure, ledger, scripts, and 26 project skills.
  Eleven of those skills expose the shared workflow playbooks to both harnesses.
- Eight Operator Day pack folders containing 45 distinct `SKILL.md` source
  definitions and three loose markdown skills, 48 source skills in total. The
  extracted folder contains 51 physical `SKILL.md` files because Dave's six
  definitions are duplicated into real Claude and Codex folders for Windows.
- Original zip archives beside extracted source folders where supplied.

The optional packs are **inventory, not installed capability**. They vary in
portability. Some are ordinary markdown skills; others assume Claude-specific
hooks, commands, tools, or complete workspaces. Read
[`packs/COMPATIBILITY.md`](packs/COMPATIBILITY.md) and run the pack-review
workflow before promoting one. The core kit is dual-harness by design; no claim
is made that every third-party pack runs unchanged in both products.

### Start

Read [`START-HERE.md`](START-HERE.md). Open the extracted folder in Claude Code
or Codex and say:

> Set up this AI OS for me.

The core setup takes about 45 to 60 minutes. Optional integrations can make the
full session longer, and setup can be resumed later.

---

## 日本語

このフォルダは、Liam Ottley 氏の AI Makeover テンプレートと、2026年7月29日〜31日に
モンテネグロのポルトモンテネグロで配布された Operator Day の資料をまとめた、
配布可能な AI オペレーティングシステムです。

**中核のワークスペースは、Windows と macOS の Claude Code・Codex の両方に対応しています。**
`CLAUDE.md` と `AGENTS.md` は同一の憲法ファイルです。作業用スキルも、実ファイルとして
同じ内容を二か所に持ちます。

- Claude Code は `.claude/skills/` を読み込みます。
- Codex は `.agents/skills/` を読み込みます。
- `scripts/sync_harness_skills.py` が、プロジェクト内の両方を同期します。

ユーザーのホームフォルダにスキルをコピーする必要はありません。普通の日本語や英語で
依頼すれば、どちらでも同じ作業手順が使えます。Claude Code のスラッシュコマンドは、
任意の短縮操作として残しています。

このワークスペースは、事業用と個人用のどちらでも設定できます。作業のリズム、台帳、
構築手順、機能は共通です。個人用で始めたあと、最初からやり直さずに事業用の情報を
追加できます。

### 言語対応

ユーザー向けのインストール案内は英語と日本語で用意しています。設定中と通常の作業中は、
ユーザーが使った言語で AI が返答します。第三者が提供した packs とスキル本文は、
作者の原文のままです。スキル本文の翻訳は別の編集判断になるため、この版では自動的に
書き換えていません。

### 含まれるもの

- 中核テンプレート、コンテキスト構造、台帳、スクリプト、プロジェクトスキル26個。
  そのうち11個は、共通の作業手順を両方の AI で使えるようにするスキルです。
- Operator Day の8つのパック。異なる `SKILL.md` の元スキル45個と、単体 Markdown
  スキル3個の合計48個です。Windows でも展開できるよう、Dave の6個は Claude 用と
  Codex 用の実フォルダに複製しているため、物理的な `SKILL.md` ファイル数は51個です。
- 元の zip が提供されていたものは、展開済みフォルダの横に原本も残しています。

追加パックは、**在庫であり、まだ導入された機能ではありません**。通常の Markdown
スキルもあれば、Claude 固有のフック、コマンド、ツール、ワークスペース全体を前提とする
ものもあります。導入前に [`packs/COMPATIBILITY.md`](packs/COMPATIBILITY.md) を読み、
pack-review を実行してください。中核キットは最初から両方に対応していますが、第三者の
全パックが修正なしで両方に動くとは説明していません。

### 始め方

最初に [`START-HERE.md`](START-HERE.md) を読んでください。展開したフォルダを
Claude Code または Codex で開き、次のように伝えます。

> このAI OSをセットアップしてください。

基本設定の目安は45〜60分です。任意の外部サービスまで設定すると長くなる場合があります。
途中で止めても、あとから再開できます。
