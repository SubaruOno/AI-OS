---
name: test
description: Check completed work by actually using it the way a person would. Runs at the end of implement and whenever the user asks test it, is this working, check my app, verify, did that work, make sure it works, something is broken, 「テストして」「動くか確認して」「検証して」, or before calling work done. Never report done on work that was not exercised.
---

# Test

The rule this skill exists to enforce: **"it should work" is not a test result.** Something is done when it's been used, for real, and behaved.

## The loop

1. **Identify the deliverable.** What was built or changed this session (or in the plan just implemented)? What is it supposed to do, in one sentence?
2. **Pick the right playbook below and exercise it for real.**
3. **Try to break it, gently**: the two or three most likely failure cases.
4. **Fix what failed**: small fixes on the spot, then re-test that exact case. Structural problems: explain plainly, propose the fix, then do it.
5. **Report in plain English** (format at the bottom).

## Playbooks by what was built

### A script or automation
- Run it with realistic input, show the actual output.
- Run it a second time (finds the "works once" bugs: files already existing, duplicate rows).
- Break-checks: empty input, a missing key in .env, a wrong path.

### An app or page
- Start it and open it, don't just read the code.
- Click through the one flow that matters end to end, as the intended user. Say exactly what rendered.
- Break-checks: refresh mid-flow, empty form submit, a phone-narrow window if it'll be used on phones.

### An integration (a new-capability build)
- Make a live call against the real account and show real data coming back ("here are your last five deals").
- Test a write only if the integration writes, and only against something safe; say what you're about to touch first.
- Break-checks: a wrong/expired key (does it fail with a plain-English message?), an empty result set.

### A document, plan, or context file
- Read it end to end as its intended reader.
- Check every referenced file and path actually exists.
- Check it against reference/writing-style.md.

### A change to the workspace itself (commands, skills, or constitutions)
- Dry-run the changed instruction as if a fresh session were following it: do the steps work in order, do the referenced files exist?
- If a constitution changed: do `CLAUDE.md` and `AGENTS.md` match exactly and still describe the workspace as it actually is?
- If a skill changed: do `.claude/skills/` and `.agents/skills/` pass the sync check?

## Reporting

```
Tested: <what>
- <check>: worked
- <check>: fixed (was: <problem, one line>)
Verdict: working / working with a caveat: <caveat>
```

Keep it honest. A caveat named now is cheaper than a surprise later. If something can't be tested yet (needs a key, needs real data), say exactly that and what would make it testable, don't quietly skip it.
