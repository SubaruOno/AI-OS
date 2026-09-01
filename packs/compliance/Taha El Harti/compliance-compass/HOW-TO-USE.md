# How to use Compliance Compass

Three steps. That's the whole thing.

```
┌─────────────────────────────────────────────────────────┐
│  1. OPEN A TERMINAL *IN THIS FOLDER*                    │
│                                                         │
│     Mac:      right-click this folder                   │
│               → "New Terminal at Folder"                │
│     Windows:  open this folder, click the address bar,  │
│               type  cmd  and press Enter                │
├─────────────────────────────────────────────────────────┤
│  2. TYPE:   claude        (say yes if it asks to trust  │
│                            the folder)                  │
├─────────────────────────────────────────────────────────┤
│  3. TYPE:   begin                                       │
└─────────────────────────────────────────────────────────┘
```

Then just talk. Answer in plain language — **"I don't know" is always a fine answer.**

## What happens next

```
 begin
   │
   ▼
 It interviews you about your business        ← ~10 min quick version,
   │                                            ~30 min if you go deep
   ▼
 It researches the rules that fit YOUR
 answers (you'll see it search the web —
 approve those, it's checking laws,
 not you)
   │
   ▼
 It reads back a summary:
 what applies · what doesn't · what's unknown
   │
   ▼
 You say "looks right"
   │
   ▼
 YOU type:  /generate-report
   │
   ▼
 output/  →  your report appears here.
             Double-click it. Print it for
             your lawyer. Use its copy button
             to save your session for later.
```

## Two optional power-ups

- **Before you start**, drop any compliance-ish documents into the `knowledge/` folder
  (privacy policy, a customer's security questionnaire, a contract someone sent you).
  The interview reads them and gets sharper.
- **Any time — even months later** — you can just ask it questions: *"what's a DPA?"*,
  *"help me with item 1 from my report"*. It's a compliance research assistant, not
  just an interview.

## Don't have Claude Code yet?

1. Install it from **https://claude.com/claude-code** (needs a paid Claude plan, Pro or
   above). Run `claude` once anywhere and log in — then start at step 1 above.
2. **No terminal / no paid plan / it's just not working?** Open `lite/MEGA-PROMPT.md`,
   copy everything in it into a chat at **claude.ai**, and you'll get a lighter version
   of the same interview with the report as a downloadable artifact.

## If it seems confused

- Type `/context`. If you don't see this folder's files listed, you opened the terminal
  in the wrong place — quit (Ctrl+C twice) and redo step 1.
- Make sure you actually **unzipped** the folder first (don't run it from inside the
  zip preview).
- It keeps asking permission for web searches → normal on first run; approve them.

> Everything stays on your computer. And remember: this is **triage, not legal advice** —
> the report ends with the exact questions to bring to a real lawyer.
