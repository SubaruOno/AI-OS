# development

Building real software without a dev team. Filled 2026-08-03 from Table 03, Operator Day.

**Dave Ebbelaar** — `project-template`, a starting skeleton for building actual software.
**Mark Kashef** — `Portable Agent Runtime Pack`: a six-layer AI operating system architecture that ships CLAUDE.md, AGENTS.md *and* GEMINI.md, so it runs across harnesses. Fifteen skills between the two. Also `Agentic OS Field Guide - Six Layers.pptx` and an asset-links handoff document.

Dave's nested repository metadata was removed from this distribution so backups include the files. Its relative `.claude/skills` symlink was replaced with an ordinary copy of `.agents/skills` so Windows extraction keeps both folders. The delivered revision was `692f6f1db8aaf188dc0c222361c9638267a98e26` from `daveebbelaar/project-template`; the untouched original zip remains beside the adapted extracted folder.

Kashef's pack is the closest thing in the kit to a rival design for the same problem Liam's template solves. Worth reading against it rather than alongside it.

Read `START-HERE.md` first: it is addressed to Claude, not to you.

Nothing here is installed. Review `../COMPATIBILITY.md` first. Put an adapted skill in `.claude/skills/`, then run `python scripts/sync_harness_skills.py` from the workspace root so Claude and Codex receive the same copy.
