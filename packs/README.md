# Packs / パック

> English first, 日本語は下に続きます. The packs themselves are English and stay that way. Ask Claude or Codex in Japanese and it will explain them in Japanese.
> パックの中身は英語のままです。日本語で訊けば、日本語で読んで説明します。

One folder per subject from Operator Day. Each holds the skills, systems and notes from the people running that table.

All eight arrived and were slotted into place on 2026-08-03. The folder names are Liam's, shipped empty with the template in July; the contents are the eight table packs, distributed separately a few days after the event.

| Folder | Subject | Who contributed | Skills |
|---|---|---|---|
| `long-form/` | Content that keeps working after it's published | Shaz Mathew · Samin Yasar | 3 (loose .md) |
| `short-form/` | Turning one piece of work into a feed | Albert Olgaard | 7 |
| `development/` | Building real software without a dev team | Dave Ebbelaar · Mark Kashef | 15 |
| `automation/` | Work that runs while you sleep | Riccardo Vandra + the table | 1 |
| `sales-offers/` | Shaping what you sell and getting it in front of people | Serdar Bisi · Lauren Tickner · Oliver Rasmusen & Albert Bakhoj | 5 |
| `operations/` | How a small team runs like a big one | Adam Goodyer + the table | 13 |
| `compliance/` | Staying on the right side of the line | Taha El Harti | 2 |
| `sponsorships/` | Getting paid by brands | Akil Wade | 2 |

Forty-five distinct `SKILL.md` source definitions, plus Shaz Mathew's three loose markdown skills: 48 capabilities in all. The extracted folder now has 51 physical `SKILL.md` files because Dave's six definitions are ordinary-file copies under both `.agents/skills` and `.claude/skills`, replacing a symlink that Windows could lose. `short-form/` accounts for most of the kit's size, almost entirely Albert Olgaard's fonts, background music and rendered frames.

## The one rule worth understanding

**A pack is inventory. A skill is installed capability. Nothing in here is installed.**

There are three places a skill can live, and the difference matters more than it looks:

- **Global** — a harness-specific user folder, loaded across projects. This kit does not install there.
- **This workspace** (`.claude/skills/` for Claude and the mirrored `.agents/skills/` for Codex) — loaded only for this folder. For capabilities that belong here.
- **`packs/`** — not loaded at all. A library on a shelf.

The instinct on receiving forty-eight skills is to install them all. Resist it. Every installed skill competes for attention in every session, and a workspace carrying forty of them is worse than one carrying six. A skill moves out of `packs/` only after someone has decided it will be used and checked `COMPATIBILITY.md`. Put the reviewed copy in `.claude/skills/`, then run `python scripts/sync_harness_skills.py` to mirror it to Codex.

## How to use these

Ask to “review the packs” in Claude or Codex. Claude Code also offers `/pack-review` as a shortcut. The workflow reads your context, walks each pack, checks its portability, and tells you honestly whether it is a now, a later, or a not-for-you.

Each pack also carries its own `START-HERE.md`, written by the organisers and **addressed to Claude rather than to you**. Those files say to read `Table-0N-<Subject>/START-HERE.md`; now that the packs sit in their sockets, the path is `packs/<subject>/START-HERE.md`.

Anything the speakers add after the event lands in these same folders.

## What was changed on filling

The eight per-folder READMEs originally read "Empty right now is expected." Each has been replaced with a note describing what actually landed. Zipped kits have been extracted alongside their originals so the folders can be browsed without unpacking anything. Nothing else in the packs was edited.

---

# パック

Operator Day のテーマごとに一つのフォルダ。そのテーブルを担当した人が持ち寄ったスキル・仕組み・メモが入っています。

8つすべてが揃い、2026年8月3日に所定の位置に収めました。フォルダ名は7月にテンプレートと一緒に空のまま配られた Liam のもので、中身はイベントの数日後に別途配布された8つのテーブルパックです。

| フォルダ | テーマ | 提供者 | スキル数 |
|---|---|---|---|
| `long-form/` | 公開後も効き続けるコンテンツ | Shaz Mathew · Samin Yasar | 3（単体の .md） |
| `short-form/` | 一つの成果物をフィードに変える | Albert Olgaard | 7 |
| `development/` | 開発チームなしで実際のソフトを作る | Dave Ebbelaar · Mark Kashef | 15 |
| `automation/` | 寝ている間に回る仕事 | Riccardo Vandra ほか | 1 |
| `sales-offers/` | 売るものを形にし、届ける | Serdar Bisi · Lauren Tickner · Oliver Rasmusen & Albert Bakhoj | 5 |
| `operations/` | 少人数で大企業のように回す | Adam Goodyer ほか | 13 |
| `compliance/` | 一線を越えないための備え | Taha El Harti | 2 |
| `sponsorships/` | ブランドから報酬を得る | Akil Wade | 2 |

異なる `SKILL.md` の元スキルが45本、これに Shaz Mathew の単体スキル3本を足して計48本です。Windows で失われる可能性があるシンボリックリンクをやめ、Dave の6本を `.agents/skills` と `.claude/skills` の両方に実ファイルで置いたため、物理的な `SKILL.md` ファイル数は51本です。容量の大半は `short-form/` にある Albert Olgaard のフォント・BGM・書き出し済み映像素材です。

## 押さえるべき原則は一つだけ

**packs は在庫。スキルは導入済みの能力。ここにあるものは一つも導入されていません。**

スキルの置き場所は三つあり、その違いは見た目以上に重要です。

- **グローバル** — AI ごとのユーザーフォルダに置き、複数プロジェクトで読み込む方法。このキットはそこへインストールしません。
- **このワークスペース**（Claude は `.claude/skills/`、Codex は同じ内容の `.agents/skills/`）— このフォルダだけで読み込まれます。
- **`packs/`** — 読み込まれません。棚に並んだ蔵書です。

48本のスキルを受け取ると、つい全部入れたくなります。そこを我慢してください。導入したスキルは一つ残らず、毎回のセッションで注意を奪い合います。40本抱えたワークスペースは、6本のワークスペースより確実に悪くなります。`COMPATIBILITY.md` を確認し、使うと決めたものだけを `.claude/skills/` に置き、`python scripts/sync_harness_skills.py` で Codex 側へ同期します。

## 使い方

Claude または Codex に「パックを見直して」と伝えてください。Claude Code では `/pack-review` も短縮操作として使えます。コンテキストと互換性を確認し、「今やる」「あとで」「自分には不要」を率直に整理します。

各パックには主催者が書いた `START-HERE.md` も入っていますが、**これはあなたではなく Claude に宛てて書かれています**。中では `Table-0N-<Subject>/START-HERE.md` を読むよう指示していますが、差込口に収めた現在のパスは `packs/<subject>/START-HERE.md` です。

登壇者がイベント後に追加した資料も、同じフォルダに入ります。

## 収める際に変更した点

各フォルダの README 8本は元々「今は空で正解です」と書かれていたため、実際に届いたものを説明する内容に差し替えました。zip 形式の配布物は、元ファイルの隣に展開して、解凍せずに中身を見られるようにしてあります。パックの中身自体はそれ以外一切変更していません。
