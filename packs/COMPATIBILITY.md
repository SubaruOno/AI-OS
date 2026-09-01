# Pack compatibility / パック互換性

## English

The core AI OS is designed for Claude Code and Codex. The files under `packs/`
are third-party source material delivered by their authors, so they must be
reviewed before promotion. This page records a source audit, not a promise that
every pack has been executed on every product and operating system.

| Pack | Source assessment | What to check before promotion |
|---|---|---|
| `long-form` | Likely portable after packaging | The three skills are loose markdown files. Give each a valid skill folder and frontmatter, then test its expected inputs and outputs. |
| `short-form` | Claude-oriented production workspace | It includes a separate Claude workspace, `.skill` bundles, media assets, fonts, and video-tool assumptions. Adapt one selected skill at a time and check external binaries on Windows and macOS. |
| `development` | Mixed; Mark Kashef's runtime is intentionally portable | Keep a chosen project's own constitutions and skill layout intact. Check setup commands and dependencies on the target OS. |
| `automation` | Mixed | Review Claude command names, scheduling assumptions, n8n links, and the Windows-origin handoff material. |
| `sales-offers` | Mostly markdown workflows, with external-service assumptions | Check referenced tools, authentication, file paths, and any Claude-only tool names before use. |
| `operations` | Several Claude-native systems | The audit plugin and related systems can rely on Claude settings, hooks, subagents, Bash, `WebSearch`, or `WebFetch`. Port the workflow deliberately instead of copying the whole plugin. |
| `compliance` | Claude-oriented complete system | Review its settings, live-research tools, jurisdiction data, and legal disclaimers. Test research and outputs in the chosen harness. |
| `sponsorships` | Likely portable standard skills | Validate frontmatter, source links, expected output paths, and one representative run in each harness. |

### Promotion rule

1. Run pack-review and choose one specific capability.
2. Read the whole candidate, including scripts, references, settings, and assets.
3. Replace harness-specific tool names or paths where necessary.
4. Put the reviewed skill in `.claude/skills/<name>/`.
5. Run `python scripts/sync_harness_skills.py` to create the identical Codex copy.
6. Run its realistic test on the current operating system. Test the other OS
   before describing it as cross-platform.
7. Run `python scripts/verify_distribution.py`.

Do not copy all 48 source skills into the working skill folders. Installed
skills compete for attention, and several packs are full systems rather than
single drop-in skills.

---

## 日本語

中核の AI OS は Claude Code と Codex の両方に対応するよう設計されています。一方、
`packs/` 以下は第三者が作成した配布資料です。導入前に一つずつ確認してください。
このページはソースを読んだ結果であり、すべてのパックを全製品・全 OS で実行済みだと
保証するものではありません。

| パック | ソース上の判定 | 導入前に確認すること |
|---|---|---|
| `long-form` | スキル形式に整えれば移植しやすい | 3本とも単体の Markdown です。正しいスキル用フォルダと frontmatter を付け、入力と出力をテストします。 |
| `short-form` | Claude 向けの制作ワークスペース | 別の Claude ワークスペース、`.skill`、動画素材、フォント、動画ツールの前提があります。必要なスキルだけを選び、Windows と macOS の外部コマンドを確認します。 |
| `development` | 混在。Mark Kashef の runtime は複数 AI を意識した構成 | 選んだプロジェクト固有の憲法とスキル配置を尊重し、対象 OS で設定コマンドと依存関係を確認します。 |
| `automation` | 混在 | Claude のコマンド名、スケジュール機能、n8n の参照先、Windows 由来の引き継ぎ資料を確認します。 |
| `sales-offers` | Markdown 中心だが外部サービスの前提あり | 使用ツール、認証、ファイルパス、Claude 固有のツール名を確認します。 |
| `operations` | Claude 固有の仕組みが複数 | audit plugin などは Claude の settings、hooks、subagents、Bash、`WebSearch`、`WebFetch` を使う場合があります。全体コピーではなく、必要な流れを移植します。 |
| `compliance` | Claude 向けの一式 | settings、最新情報の調査ツール、法域データ、法的注意事項を確認し、選んだ AI で出力をテストします。 |
| `sponsorships` | 標準的なスキルで、比較的移植しやすい | frontmatter、参照リンク、出力先を確認し、両方の AI で代表的なテストを行います。 |

### 導入のルール

1. pack-review を実行し、必要な機能を一つ選びます。
2. スクリプト、参照資料、settings、素材を含め、候補全体を読みます。
3. 必要に応じて、特定の AI や OS に依存するツール名・パスを直します。
4. 確認済みスキルを `.claude/skills/<name>/` に置きます。
5. `python scripts/sync_harness_skills.py` を実行し、Codex 側にも同じ実ファイルを作ります。
6. 現在の OS で実際のテストを行います。別の OS でもテストするまでは、両 OS 対応とは説明しません。
7. `python scripts/verify_distribution.py` を実行します。

48個すべてを作業用スキルフォルダへ入れないでください。導入済みスキルは毎回の判断に
影響し、パックの中には単体スキルではなくシステム全体として作られたものもあります。
