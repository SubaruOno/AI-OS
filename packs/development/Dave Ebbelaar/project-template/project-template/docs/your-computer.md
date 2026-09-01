# Mac and Windows

Everything here works on both. A handful of differences bite, and they are the reason a step that worked for the person next to you does nothing on your machine.

Read the section for your machine, then the section that catches everyone.

## Windows

### Use Git Bash, not PowerShell

Every command in these documents is written for a Unix shell. PowerShell and Command Prompt cannot run `./scripts/preflight.sh`.

Git Bash comes with [Git for Windows](https://git-scm.com/download/win). Install it, then right-click your project folder and choose **Open Git Bash here**. Run everything there.

Tell your assistant you are on Windows using Git Bash, so it writes commands you can actually run.

WSL works too and is the better long-term choice. Git Bash is the fast one for today.

### Turn on symlinks before you clone

`.claude/skills` is a link to `.agents/skills`, so both Claude Code and Codex read the same files. Windows only creates links when it has permission.

Run this once, before cloning:

```bash
git config --global core.symlinks true
```

It also needs Developer Mode on, under Settings, then System, then For developers.

Already cloned and your assistant lists no skills? `.claude/skills` will be a text file rather than a folder. Fix the setting above, then clone again.

Everything still works without this: `AGENTS.md` names the real paths, so your assistant reads them directly.

### Windows hides file extensions

This one catches almost everyone. Windows hides known extensions by default, so saving a file as `.env.local` in Notepad silently produces `.env.local.txt`, which nothing reads.

Turn extensions on: File Explorer, then View, then tick **File name extensions**.

Better: ask your assistant to create the file, and paste your values in afterwards.

### Long paths

Installing packages creates deeply nested folders, and Windows historically stops at 260 characters. Keep your project near the root, like `C:\dev\my-app`, rather than inside Documents inside OneDrive.

If you see an error mentioning a path being too long:

```bash
git config --global core.longpaths true
```

### Python for the security check

`./scripts/check-rls.sh` needs Python 3. Windows does not include it, and typing `python3` on a machine without it opens the Microsoft Store instead of an error.

Install from [python.org](https://www.python.org/downloads/) and tick **Add python.exe to PATH** during setup. The script finds it under any of `python3`, `python`, or `py`.

### Installing the command-line tools

| Tool | Mac | Windows |
| --- | --- | --- |
| Node.js | [nodejs.org](https://nodejs.org) or `brew install node` | [nodejs.org](https://nodejs.org) installer |
| pnpm | `corepack enable` | `corepack enable` in Git Bash |
| Supabase | no install, use `pnpm dlx supabase@latest` | same |
| Vercel | no install, use `pnpm dlx vercel@latest` | same |
| Railway | `brew install railway` | `npm i -g @railway/cli` |

The recipes use `pnpm dlx` for Supabase and Vercel precisely so there is nothing to install.

### Generating a random secret

Level 1 needs two long random values. `openssl` is available in Git Bash:

```bash
openssl rand -hex 32
```

In PowerShell, if you must:

```powershell
-join ((1..64) | ForEach-Object { '{0:x}' -f (Get-Random -Max 16) })
```

## Mac

### The upper and lower case trap

This is the one that bites on deploy day, and only on deploy day.

Your Mac disk treats `Button.tsx` and `button.tsx` as the same file. Vercel and Railway run Linux, which does not. So an import written with the wrong case works perfectly on your machine and fails the moment you deploy, with an error saying a file cannot be found that you can plainly see.

When a build passes locally and fails live with a missing file, check the capitalisation in the import against the real filename.

Your assistant should match the case exactly every time. This is worth knowing anyway, because the error message does not explain itself.

### Command line tools

macOS ships without the developer tools until something asks for them. The first `git` command triggers a popup. Accept it and wait; it takes a few minutes.

To do it up front:

```bash
xcode-select --install
```

### Homebrew is optional

Only Railway at level 3 suggests `brew`. Everything else installs from a download or runs through `pnpm dlx`. Skip Homebrew unless you want it.

## Both machines

### Do not build inside a syncing folder

Dropbox, OneDrive, iCloud Drive, and Google Drive all try to sync `node_modules`, which is tens of thousands of small files. You get a slow machine, a hot laptop, corrupted installs, and occasionally a sync quota bill.

Keep projects somewhere plain: `~/dev/my-app` on Mac, `C:\dev\my-app` on Windows.

### Line endings

Windows ends lines differently from Mac and Linux. A shell script that arrives with Windows endings fails with `bad interpreter`, which reads like the file is corrupt.

The `.gitattributes` file in this repository handles it. If you see that error anyway, your editor rewrote the file. Set it back to LF, which VS Code shows in the bottom-right corner.

### Ports already in use

The website uses port 3000, and level 3 also uses 5173 and 8000. If one is busy, the app will not start.

```bash
lsof -ti:3000 | xargs kill        # Mac
npx kill-port 3000                # either
```

### Your terminal keeps the settings only until you close it

`export SUPABASE_ACCESS_TOKEN=...` lasts for that window. Open a new one and it is gone.

To keep it, add the line to `~/.zshrc` on Mac, or `~/.bashrc` in Git Bash on Windows. Then open a new terminal.

### Tell your assistant which machine you are on

Say it once at the start:

> I'm on Windows, using Git Bash.

It changes which commands you get. Without it you may be handed `brew install` on a machine that has no `brew`.
