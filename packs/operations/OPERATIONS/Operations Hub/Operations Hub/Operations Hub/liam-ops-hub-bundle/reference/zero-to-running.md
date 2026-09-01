# Zero to running

*Updated 2026-07-28. Mac and Linux. Windows notes marked inline.*

Nothing in the source material covers this, and it's where a founder actually stalls. Every step
below was checked against a real working app, and the four landmines at the end were verified by
hand.

## The whole stack

Two packages. That's it.

```bash
pip install "fastapi>=0.115" "uvicorn[standard]>=0.30"
```

The database is SQLite, which ships inside Python. There's no build step, no npm, no bundler and no
frontend framework. The reference app serves plain HTML with plain `<script>` tags and has done for
two months across 23,000 lines of JavaScript.

**Do not run `pip freeze > requirements.txt`.** It writes about twenty exact-pinned transitive
packages you never chose. Hand-write the file instead, one line per package you actually installed,
with a comment saying what forced it:

```
fastapi>=0.115        # the web framework
uvicorn[standard]>=0.30   # runs the web framework
```

That habit is why the reference app can still explain all 31 of its packages after two months of
growth from three.

## The steps

**1. One folder, and everything lives in it.**

```bash
mkdir ~/myops && cd ~/myops
python3 -m venv .venv
source .venv/bin/activate
```

Your prompt now starts with `(.venv)`. You do that `source` line every time you open a new terminal.
On Windows it's `.venv\Scripts\activate`.

**2. This file tree.**

```
myops/
  main.py            all your routes, one file to start
  db.py              the connection helper, about 25 lines
  schema.sql         your CREATE TABLE statements
  static/
    index.html       the page
    app.js           the frontend
  data/
    app.db           your database. Created for you on first run
  requirements.txt
  .gitignore         must contain: .venv, data/, .env, __pycache__
  CLAUDE.md          the rules your AI agent reads
  run.sh
```

**3. The database goes at `myops/data/app.db`, inside the app folder.**

```python
# db.py
import os, sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(os.environ.get("APP_DB_PATH") or Path(__file__).resolve().parent / "data" / "app.db")

@contextmanager
def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

Note `.parent`, singular. The file sits **next to** your code. The reference app counts three parent
directories upward instead, because it lives inside a bigger repository, and that one decision cost
it a hard-coded guard that now refuses to open the database at all on a fresh machine.

The three settings all matter. Busy timeout means a second process waits instead of erroring.
Write-ahead logging means reading doesn't block writing. Foreign keys are **off by default** in
SQLite, which quietly lets broken links in. The reference app shipped without the first two and had
to add them five days later, the moment a second process appeared.

`APP_DB_PATH` is the throwaway-database switch. Set it and every write goes to a scratch file. Put it
in on day one, before you have tests or data. Retrofitting it later means auditing every place that
opens the database.

**4. Create the tables. This is the step everyone forgets.**

A booting app with an empty database file gives you a green health check and `no such table` on the
first real query, which is a genuinely confusing place to be. So apply the schema on startup:

```python
# in main.py, at import time
def init_db():
    with get_db() as conn:
        conn.executescript(Path(__file__).parent.joinpath("schema.sql").read_text())

init_db()
```

`schema.sql` uses `CREATE TABLE IF NOT EXISTS`, so it's safe to run every boot. The moment you need
to *change* a table, stop editing `schema.sql` and switch to a `migrations/` folder: one new
timestamped `.sql` file per change, applied in filename order, each filename recorded in a
`schema_migrations` table once it runs. The rule is absolute: **a schema change is a new file, never
an edit to a file that already ran.** Editing one means your machine and every other copy silently
disagree about what the database looks like.

**5. Serve the frontend, or step 8 shows you a 404.**

```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def index():
    return FileResponse("static/index.html")
```

**6. Add the health check before anything else.**

```python
@app.get("/healthz")
def healthz():
    try:
        with get_db() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "db": "ok"}
    except Exception as e:
        return JSONResponse({"status": "degraded", "db": str(e)}, status_code=503)
```

Your home page can't tell you the database died, because it never touches it. This can.

**7. `run.sh`, with a relative path.**

```bash
#!/usr/bin/env bash
exec "$(dirname "$0")/.venv/bin/python" "$(dirname "$0")/main.py"
```

Then `chmod +x run.sh`. On Windows, skip the script and run
`.venv\Scripts\python.exe main.py` directly.

And at the bottom of `main.py`:

```python
if __name__ == "__main__":
    import uvicorn, os
    uvicorn.run("main:app",
                host="127.0.0.1",
                port=int(os.getenv("APP_PORT", "8000")),
                reload=os.getenv("APP_DEV") == "1")
```

`127.0.0.1` keeps it on your machine until you deliberately decide otherwise. `APP_DEV=1 ./run.sh`
restarts the server every time you save a file, which is the single biggest day-to-day time saver
here. Don't create a second entry-point file that imports this one; the reference app has one purely
because an old launch path predates its current structure, and it's 45 lines of pure history.

**8. Run it.**

```bash
./run.sh
```

You should see `Uvicorn running on http://127.0.0.1:8000`. Open that address, and then
`http://127.0.0.1:8000/healthz`, which should say `ok`. If it says `degraded`, the web server is fine
and your database path is wrong, which is exactly what the endpoint is for.

**Stop it with Ctrl-C** in that terminal.

**9. Save it, and back it up.**

```bash
git init && git add . && git commit -m "first working app"
```

`data/` is git-ignored on purpose, so your business data isn't in your code history. Which means git
is **not** your backup. Copy the database somewhere else, on a schedule, dated:

```bash
sqlite3 data/app.db ".backup 'backups/app-$(date +%F).db'"
```

Use `.backup`, not `cp`. With write-ahead logging on, a plain copy of a live database can miss recent
writes. Then restore one, once, now, so you find out today whether your backup works.

**10. Write the rules file for your agent.** Highest-leverage file in the project.

```markdown
# CLAUDE.md
- Keep main.py in one file until about 500 lines, then split one file per feature.
- Every new package needs a comment saying what feature required it.
- Run ./verify.sh after every change.
- Never write to data/app.db directly. Go through get_db().
- A schema change is a NEW migration file. Never edit one that already ran.
- Never put a key in a file. Environment variables only.
```

**11. `verify.sh`, self-contained.**

```bash
#!/usr/bin/env bash
set -u
PORT=$(python3 -c "import socket;s=socket.socket();s.bind(('',0));print(s.getsockname()[1])")
TMP=$(mktemp -d); trap 'rm -rf "$TMP"; kill $PID 2>/dev/null' EXIT
APP_DB_PATH="$TMP/t.db" APP_PORT=$PORT ./run.sh & PID=$!
for i in $(seq 20); do sleep 0.5; kill -0 $PID 2>/dev/null || { echo "app died"; exit 1; }
  curl -sf "http://127.0.0.1:$PORT/healthz" >/dev/null && break; done
for p in / /healthz; do
  code=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT$p")
  echo "$code $p"; [ "$code" = 200 ] || FAIL=1; done
[ -z "${FAIL:-}" ] && echo "PASS" || { echo "FAIL"; exit 1; }
```

It boots the app on a free port against a throwaway database, checks two routes, and cleans up.
Run it after every change your agent makes.

## When the port is taken

The error is `Address already in use`. Three options, in order:

1. Use another port: `APP_PORT=8001 ./run.sh`. Nothing else changes.
2. Find what's holding it: `lsof -i :8000` on Mac and Linux, `netstat -ano | findstr :8000` on
   Windows. If it's your own app from an earlier run, close that terminal.
3. **Don't reach for `pkill` or `killall`.** It's a blunt instrument that will also kill things you
   didn't mean to kill.

## The four landmines, verified

These are real, in a real working app, and each one stops a copy from running.

| # | What | Why it bites |
|---|---|---|
| 1 | The AIOS template's dependency file has **no web framework and no server** in it. Seven packages, all for other things, and an empty `apps/` folder. | The recommended stack isn't installable from the template as shipped. Install the two packages yourself. |
| 2 | The reference app's launch script hardcodes **one machine's absolute path** to its Python. | It runs on exactly one computer. Use `$(dirname "$0")` as shown above. |
| 3 | Its database path is resolved by counting **three parent directories upward**. | The hop count silently encodes how deep the app sits. Nest your app differently and the database appears somewhere you didn't expect. Use `.parent`, once. |
| 4 | That same file has a guard that **hard-fails** when the database is at its own default path. | A naive copy doesn't misbehave, it refuses to start, with an error about infrastructure you don't have. Don't copy the guard. |
