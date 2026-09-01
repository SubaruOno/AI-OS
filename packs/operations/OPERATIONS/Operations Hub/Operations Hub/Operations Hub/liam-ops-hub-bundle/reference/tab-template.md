# The one screen template

*Updated 2026-07-28.*

Every later screen is a copy of this one. It has to be written rather than pointed at, because in the
reference app **ten of its view files have no render guard at all**, so cloning any of them gives you
screens that flash and clobber each other.

Build screen one completely. Then clone.

Read `zero-to-running.md` first. This assumes you have a booting app, a database with tables in it,
and a `get_db()`.

---

## Part 1: the shell, built once

`static/index.html` has a nav and a single `<div id="view">`. Everything else is `app.js`.

**Render the nav from one array.** The reference app keeps a desktop menu and a mobile menu as two
hand-written blocks, and they have already drifted: one tab is live on desktop and unreachable from
the phone right now, with nothing anywhere reporting it. One array, both menus generated:

```js
const NAV = [
  { route: "tasks",  label: "To-dos" },
  { route: "people", label: "People" },
];
```

**The router, with the render token.** This is the load-bearing part:

```js
const views = {};
let renderSeq = 0;

function registerView(name, def) { views[name] = def; }

function parseHash() {
  const [name, ...params] = (location.hash.slice(2) || "tasks").split("/");
  return { name, params };
}

function router() {
  const { name, params } = parseHash();
  const view = views[name];
  const el = document.getElementById("view");
  const seq = String(++renderSeq);
  el.dataset.renderSeq = seq;          // stamp BEFORE rendering
  if (!view) { el.innerHTML = `<div class="empty">Page not found.</div>`; return; }
  view.render(el, params);
}

window.addEventListener("hashchange", router);
window.addEventListener("DOMContentLoaded", router);
```

**Why the token exists.** You click To-dos. Its fetch starts. You click People before it finishes.
The To-dos response arrives and writes itself into a container that's now showing People. The
reference app has a comment naming exactly this incident, on one screen overwriting another's
content. The token is how a render knows it's been superseded.

**Three more helpers in `app.js`:**

```js
async function api(method, path, body) {
  const res = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    let msg = res.statusText;
    try { const j = await res.json(); msg = j.detail || msg; } catch {}
    const err = new Error(msg); err.status = res.status;
    try { err.errors = (await res.clone().json()).errors; } catch {}
    throw err;
  }
  return res.status === 204 ? null : res.json();
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function toast(msg) { /* one div, fades after 3s */ }
```

## Part 2: the backend, one file per feature

`app/routers/things.py`. Every route carries its full path on the decorator, so nothing else in the
app needs editing when you add a feature.

```python
from fastapi import APIRouter, HTTPException
from db import get_db

router = APIRouter()

THING_FIELDS = {"title", "status", "notes", "due_date"}   # the ONLY writable columns
```

**Four endpoints, and no more.**

```python
@router.get("/api/things")
def list_things():
    with get_db() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM things ORDER BY created_at DESC")]

@router.get("/api/things/{tid}")
def get_thing(tid: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM things WHERE id=?", (tid,)).fetchone()
        if not row: raise HTTPException(404, "Not found")
        return {
            "thing": dict(row),
            "tasks": [dict(r) for r in conn.execute(
                "SELECT * FROM tasks WHERE thing_id=?", (tid,))],
            "people": [dict(r) for r in conn.execute(
                "SELECT p.* FROM people p JOIN thing_people tp ON tp.person_id=p.id "
                "WHERE tp.thing_id=?", (tid,))],
        }
```

**That second endpoint is the most important idea on this page.** One request returns the record plus
every attached list. Four plain SELECTs, one JSON object, one render. The default an AI agent reaches
for is six parallel fetches and six spinners, and unwinding that later is expensive.

```python
@router.post("/api/things")
def create_thing(payload: dict):
    fields = {k: v for k, v in payload.items() if k in THING_FIELDS}
    if not fields.get("title"): raise HTTPException(422, "Title is required")
    with get_db() as conn:
        cur = conn.execute(
            f"INSERT INTO things ({','.join(fields)}) VALUES ({','.join('?'*len(fields))}) RETURNING *",
            tuple(fields.values()))
        return dict(cur.fetchone())

@router.patch("/api/things/{tid}")
def update_thing(tid: int, payload: dict):
    fields = {k: v for k, v in payload.items() if k in THING_FIELDS}
    if not fields: raise HTTPException(422, "Nothing to update")
    sets = ", ".join(f"{k}=?" for k in fields) + ", updated_at=datetime('now')"
    with get_db() as conn:
        cur = conn.execute(f"UPDATE things SET {sets} WHERE id=? RETURNING *",
                           (*fields.values(), tid))
        row = cur.fetchone()
        if not row: raise HTTPException(404, "Not found")
        return dict(row)
```

`THING_FIELDS` is your entire authorization story for writes. A client can't set `id`, `created_at`,
or a status column you compute. Twenty lines, one constant per table, no auth system required.

**Both write endpoints return the saved row.** That's what lets the frontend repaint from memory
instead of refetching the whole list.

**Register it.** With three or four features, one explicit line each is clearer than machinery:

```python
from app.routers import things, people
app.include_router(things.router)
app.include_router(people.router)
```

Auto-discovery (loop the folder, include anything with a `router`) is eight lines and worth adding at
about file five. Not before. Note that the reference app's first split was **into 11 files, on the day
its single route file hit 1,364 lines**, four days after launch. Eleven is the number to picture, not
the 59 it has now.

## Part 3: the screen file

`static/js/things.js`. This is the file you clone.

```js
(function () {
  let rows = [];          // the warm cache
  let loaded = false;

  async function render(el, params) {
    const seq = el.dataset.renderSeq;
    const alive = () => el.dataset.renderSeq === seq;   // check before EVERY write

    // 1. Frame first. Heading and button are usable while data loads.
    el.innerHTML = `
      <div class="head">
        <h1>Things</h1>
        <button id="new-thing" class="btn">+ New</button>
      </div>
      <div id="body"></div>`;
    document.getElementById("new-thing").onclick = () => openThingModal(null, reload);

    // 2. Warm paint if we have data, cold "Loading…" if we don't.
    if (loaded) paint();
    else document.getElementById("body").innerHTML = `<div class="empty">Loading…</div>`;

    // 3. Fetch, guarded on both branches.
    try {
      const data = await api("GET", "/api/things");
      if (!alive()) return;
      rows = data; loaded = true;
      paint();
    } catch (err) {
      if (!alive()) return;
      if (loaded) return;                 // never replace good data with an error
      document.getElementById("body").innerHTML =
        `<div class="empty">Couldn't load things.<br><small>${esc(err.message)}</small></div>`;
    }

    function paint() {
      if (!alive()) return;
      const body = document.getElementById("body");
      if (!rows.length) {
        body.innerHTML = `<div class="empty">No things yet.<br>
          <small>Add your first one with the button above.</small></div>`;
        return;
      }
      body.innerHTML = rows.map(r => `
        <a class="card" href="#/things/${r.id}">
          <span class="card__title">${esc(r.title)}</span>
          <span class="chip">${esc(r.status)}</span>
        </a>`).join("");
    }

    async function reload() {
      const data = await api("GET", "/api/things");
      if (!alive()) return;
      rows = data; paint();
    }
  }

  registerView("things", { render });
})();
```

## The eight rules inside that file

1. **The guard is line one of every render**, and checked before every single write, including in the
   `catch`. Make it mechanical so it's never a thing to remember.
2. **Frame first, body second.** The heading and the New button work while data loads, and nothing
   jumps when it arrives.
3. **The warm cache is two variables and one `if`.** Stop there. No per-mode caches, no prefetching.
4. **Never replace good data with an error.** If a background refresh fails and you already have rows
   on screen, do nothing at all.
5. **Three states, one CSS class.** Loading, empty, error. The empty state names the next action; "No
   results" alone is a dead end. The error state includes the escaped server message, which is what
   makes a bug reportable instead of mysterious.
6. **Filters: decide once per control.** A search box narrowing rows you already hold calls `paint()`
   and touches the network zero times. A control that changes the question the server answers
   refetches. Write which one it is in a comment above it.
7. **Everything interpolated goes through `esc()`**, attributes included, and every attribute is
   quoted. Nothing in your app will catch a miss. A client named `O'Brien` is the cheap version of
   this bug; pasted markup is the expensive one.
8. **Don't repaint over the user.** Before any silent background repaint, bail out if a modal is open
   or the focus is inside a text input. A refresh nobody asked for should never interrupt typing.

## Adding screen two

One new backend file. One new frontend file. One `<script>` tag. One entry in `NAV`. Nothing else in
the app gets edited, which is exactly why an agent can work on screen two without breaking screen one.

## Where this runs

On your machine, at `127.0.0.1`, until you decide otherwise. That's a real answer, not a placeholder:
one person, one laptop, no login needed. The moment a second human needs it, you need a host and a
login, and that's a different afternoon. Don't build auth before then. The reference app has six
kinds of login principal and one user.
