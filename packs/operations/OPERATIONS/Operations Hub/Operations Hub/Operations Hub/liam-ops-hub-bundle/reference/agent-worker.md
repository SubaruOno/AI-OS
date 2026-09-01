# The background AI worker

*Updated 2026-07-28.*

How a button in your app kicks off an AI agent that works for two minutes and files a result you can
check in the morning. This is the pattern the reference app has genuinely dialled in, and the version
below is the smallest honest one.

## The one rule everything hangs off

**The web request never runs the agent.** It does one INSERT and returns.

```python
@router.post("/api/leads/{lead_id}/enrich")
def enrich(lead_id: int):
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM jobs WHERE kind='lead_enrich' AND status IN ('queued','running') "
            "AND json_extract(payload,'$.lead_id')=?", (lead_id,)).fetchone()
        if existing:
            return {"job_id": existing["id"], "status": "already running"}
        jid = uuid.uuid4().hex
        conn.execute(
            "INSERT INTO jobs (id, kind, status, payload) VALUES (?,?,'queued',?)",
            (jid, "lead_enrich", json.dumps({"lead_id": lead_id})))
    return {"job_id": jid, "status": "queued"}
```

An agent run takes thirty seconds to several minutes. A web request can't wait that long, and an
in-process background task dies on every restart and redeploy, which is exactly when you're shipping.
One INSERT is instant, survives a restart and is trivial to retry.

**That duplicate check is five lines and saves real money.** A founder clicks Enrich three times.
Without it, that's three queued rows and three paid runs.

## The table

```sql
CREATE TABLE jobs (
  id         TEXT PRIMARY KEY,
  kind       TEXT NOT NULL,
  status     TEXT NOT NULL DEFAULT 'queued'
             CHECK (status IN ('queued','running','done','error')),
  payload    TEXT,          -- JSON in
  result     TEXT,          -- the RAW model output, verbatim, even on failure
  error      TEXT,
  attempts   INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);
```

`kind` is plain text, so a new type of AI work needs no schema change at all. That part is genuinely
free.

Honest note: the reference app's version of this table has been altered **eight times** since it was
created, adding cost, duration, turn count, token count and start/finish stamps. So don't believe
anyone (including the reference app's own docs) who tells you this table is write-once. Start here,
and expect to add a cost column the first week you care what it's costing you.

**Always write the raw model output into `result`, verbatim, even when the run failed.** On day one
you have no idea what shapes the model emits. That column is the only way you find out.

## The worker

A second process. Thirty lines of real logic.

```python
POLL_SECONDS = 3

def claim_one():
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM jobs WHERE status='queued' ORDER BY created_at LIMIT 1").fetchone()
        if not row: return None
        changed = conn.execute(
            "UPDATE jobs SET status='running', updated_at=datetime('now') "
            "WHERE id=? AND status='queued'", (row["id"],)).rowcount
        return dict(row) if changed else None      # someone else got it

def reconcile_orphans():
    """Anything still 'running' at startup was killed mid-flight. Nothing is running now."""
    with get_db() as conn:
        conn.execute("UPDATE jobs SET status='queued', attempts=attempts+1 "
                     "WHERE status='running' AND attempts < 3")
        conn.execute("UPDATE jobs SET status='error', error='gave up after 3 attempts' "
                     "WHERE status='running' AND attempts >= 3")

def main():
    reconcile_orphans()
    while True:
        job = claim_one()
        if job is None:
            time.sleep(POLL_SECONDS); continue
        try:
            result = HANDLERS[job["kind"]](job)
            finish(job["id"], "done", result=result)
        except Exception as e:
            logging.exception("job %s (%s) failed", job["id"], job["kind"])
            finish(job["id"], "error", error=str(e))
```

**`claim_one` is conditional on purpose.** The UPDATE only succeeds if the row is still `queued`, so
two workers can never run the same job.

**A failing job can never take the worker down.** The `except` catches everything, writes the reason
onto that job's own row, and the loop continues. The difference between "my automation broke and I
found out three weeks later" and "one row says error with the reason in it".

**Be deliberate about retries.** In the code above, a normal failure is **terminal on the first
attempt**. `attempts` only climbs when a crash left a row stuck in `running` and startup requeued it.
That's the reference app's actual behaviour, and it's a reasonable default: a job that failed because
the model returned nonsense will usually fail the same way again, and each retry costs money. If you
do want retries, write them explicitly, and cap them. What you must not do is write `attempts+1` on
error, no requeue path, and a cap that nothing checks. That's config that looks live and isn't.

## Where the worker actually runs

This is the step that quietly is the project, so pick one now:

- **Same laptop, second terminal.** `python worker.py`. Fine for day one, dies when you close the lid.
- **A background-worker service** on whatever platform hosts your app. Most have one. Same codebase,
  different start command.
- **One small always-on cloud machine**, running both the app and the worker.

**The web process and the worker must reach the same database.** An agent scaffolding this will
default to a SQLite file next to whichever process it's editing. The moment the worker is a separate
container or machine, the queue splits in half: the button inserts into one file, the worker polls
another and finds nothing, forever, with no error anywhere. If they're on different machines, you
need a shared database, not a shared file.

## The agent itself

Two things and no framework: a prompt, and a small output schema.

```python
LEAD_ENRICH_PROMPT = """You research companies. Given a name and a website, return ONE JSON object:
  {company, one_liner, employee_guess, industry, facts: [{claim, source_url}], confidence}
Do about 5 lookups, then STOP and emit. Leave a field out rather than guess.
If a tool errors, retry it once, then move on."""
```

Six or seven fields, not thirty. A turn cap and a spend cap on the run.

**Watch for dead config.** In the reference app, the model and turn-cap fields declared on each agent
definition are **never read**. They're passed in separately by the caller, so what a role says it uses
and what it actually uses have quietly diverged. Its zero-cost smoke-test job declares a cheap model
and a two-turn cap, and actually runs on the expensive default with a 25-turn cap. Every run of the
"free" health check is a real bill. Whatever you build, verify the settings against the invoice, not
against the config file.

**The API key lives in an environment variable.** Never in a file you commit. A non-technical founder
plus an AI agent is the exact recipe for a key pasted into the handler and pushed.

## The boundary that makes this safe

**Give the agent no write access at all.** No file writes, no database access, no shell commands
containing SQL writes. The agent returns JSON. The worker performs every write.

The reference app enforces this three ways: the role declares no write tools, a pattern check blocks
any shell command containing a SQL write, and a second hook applies the same rule again. Belt and
braces, on purpose.

This is the single most transferable idea here. If the model can only ever produce a JSON object, the
worst outcome of a bad run is a bad draft you reject, rather than a corrupted customer record.

## Structured output is not a contract

Treat it as unreliable, because it is. Three steps, in this order:

```python
def parse(raw_text, structured):
    if not structured:                       # happens constantly
        m = re.search(r"```json\s*(.+?)```", raw_text, re.S)
        structured = json.loads(m.group(1)) if m else None
        salvaged = True
    ok = validate_against_schema(structured, SCHEMA)   # best effort, never blocks
    return structured, salvaged, ok
```

1. If the structured channel came back empty, **pull the last fenced ```json block out of the final
   text**. This is the single most common failure and it's fully recoverable.
2. Validate against your schema and keep a boolean saying whether it passed. Store the boolean.
3. Alias the key variants you actually observe (`full_name` into `name`, and so on). This is a
   week-two task, which is why step 1 of this file says to store the raw output from day one.

The reference app's own notes name this as the biggest failure class in its runtime, with three
separate live bugs from one root cause: the model renaming a key, emitting a list where an object was
declared, and emitting a dictionary where an array was declared.

## Where the result goes, and an honest caveat

**Recommended:** the agent writes to a draft, never onto the live record. Add
`lead_enrichments (lead_id, job_id, data_json, status, created_at)` with status `needs_review`. Then
one review screen: proposed on the left, current on the right, Approve and Reject. Approve copies the
fields across and stamps who and when.

**The caveat, because it matters:** the reference app **does not do this on its main path.** Its
enrichment writes straight onto the live person record with no human gate. The review queue exists in
exactly one of its pipelines. So this is the lesson learned from watching it, not a pattern proven at
scale in it. Take the advice, and know where it came from.

## Closing the loop for the user

The button returns a job id. Something has to poll it, or you've shipped a button that visibly does
nothing for ninety seconds, which reads as broken:

```python
@router.get("/api/jobs/{jid}")
def job_status(jid: str):
    with get_db() as conn:
        row = conn.execute("SELECT id, kind, status, error FROM jobs WHERE id=?", (jid,)).fetchone()
        if not row: raise HTTPException(404)
        return dict(row)
```

Poll every two seconds, show a spinner, stop on `done` or `error`. A live event stream with a cursor
and redaction is a real thing the reference app built, and it's worth it when runs take minutes and
fan out. For a single ninety-second enrichment, a spinner and the final draft are enough.

## Your first automation should be this one

Enrich a new lead. It only ever appends information about a stranger. Nothing it produces touches
money, nothing leaves your building, and a bad result costs you thirty seconds of reading. Get that
working end to end before you let an agent near anything that sends, pays or deletes.

## Two things to add the first week

**Cost on the job row, written before you check whether the run failed.** Failed runs are the ones
that burn money invisibly. Then one page summing cost by day for the last 30 days. Four columns and
one query, and you have a real answer to "what is this costing me".

**A guard so your tests can't spend.** Your real API key is in your environment while tests run, so an
unmocked call doesn't fail, it succeeds and charges you. The symptom looks like a random flaky test.
Replace the model client with something that raises, in your test setup.
