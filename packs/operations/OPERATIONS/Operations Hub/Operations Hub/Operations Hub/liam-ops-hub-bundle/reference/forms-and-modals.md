# Forms and modals

*Updated 2026-07-28.*

The bulk of a real ops app, and the thing every survey of the reference codebase missed. Day one is
"add a person". Day two is "change this person". Day three is "why did my save do nothing".

## Do this in the right order

**Write two forms the dumb way first, then extract the helper.** Not the other way round.

You can't design the right abstraction before you've seen two instances of it, and an AI agent asked
to build a thirteen-responsibility helper from a paragraph of prose will produce something you can't
debug and won't understand. Build the person form. Build the task form. Notice the nine things you
wrote twice. *Then* say "pull the shared parts of these two into one function."

Budget about 150 lines for the extracted helper once it does everything below. If you budget 80 and
land on 150, you'll think you did it wrong. You didn't.

## The one error shape

Pick this before you write either form, because three different error shapes reaching the same
`catch` is a guaranteed afternoon:

```json
{ "detail": "That email is already on file",
  "errors": { "email": "That email is already on file" } }
```

`detail` is always present and always human-readable. `errors` is optional, keyed by field name.
Web frameworks emit `detail` by default, so this shape costs nothing and your catch handles both
cases with one branch.

**Never pass raw database text through.** A constraint failure produces something like
`CHECK constraint failed: things_status_check`, and the reference app puts exactly that in the user's
face. Map it once, at the app level:

```python
@app.exception_handler(sqlite3.IntegrityError)
def on_integrity(request, exc):
    m = str(exc)
    if "UNIQUE" in m:   detail = "That already exists."
    elif "NOT NULL" in m: detail = "Something required was left blank."
    else:               detail = "That change isn't allowed."
    return JSONResponse({"detail": detail}, status_code=422)
```

Register it inside your app factory, not as a bare module-level decorator. Copying a decorator
without its surrounding function is a real and confusing failure.

## Five field helpers, and stop

Each returns a string. Note the error paragraph, empty and hidden, present from day one so any field
can show an error without you touching the helper again.

```js
const text = ({ name, label, value = "", required }) => `
  <div class="field" data-field="${name}">
    <label for="f-${name}">${esc(label)}${required ? " *" : ""}</label>
    <input id="f-${name}" name="${name}" class="input" value="${esc(value)}">
    <p class="field__error" hidden></p>
  </div>`;
```

`textarea`, `date`, `select` and `checkbox` follow the same shape. Resist a sixth. The reference app
has about ten form helpers plus a hand-rolled dropdown replacement with a ninety-line controller
behind it, and native form controls would have been fine.

**Dates cross the wire as `YYYY-MM-DD` text.** Never a timestamp, never a JavaScript `Date`. Use
`<input type="date">`, which speaks exactly that format. This one line prevents the bug where
everything shifts by a day for anyone not on UTC.

## Declare each form as data

```js
const PERSON_FORM = [
  { name: "name",    label: "Name",    type: "text", required: true },
  { name: "company", label: "Company", type: "text" },
  { name: "email",   label: "Email",   type: "text" },
  { name: "notes",   label: "Notes",   type: "textarea" },
];
```

Create and edit use the **same array**. The only differences are whether you pass existing values and
what the button says.

## The helper

```js
function openRecordForm({ title, fields, values = {}, onSubmit, onDelete }) {
  const back = document.createElement("div");
  back.className = "modal-backdrop";
  back.innerHTML = `
    <form class="modal" novalidate>
      <h2>${esc(title)}</h2>
      ${fields.map(f => RENDERERS[f.type]({ ...f, value: values[f.name] ?? "" })).join("")}
      <p class="form__error" hidden></p>
      <footer>
        ${onDelete ? '<button type="button" class="btn btn--danger" data-del>Delete</button>' : ""}
        <button type="button" class="btn" data-cancel>Cancel</button>
        <button type="submit" class="btn btn--primary">Save</button>
      </footer>
    </form>`;
  document.body.appendChild(back);

  const form   = back.querySelector("form");
  const save   = form.querySelector('[type="submit"]');
  const banner = form.querySelector(".form__error");
  let dirty = false;

  form.addEventListener("input", () => { dirty = true; });
  form.querySelector("input, textarea")?.focus();

  function clearErrors() {
    banner.hidden = true;
    form.querySelectorAll(".field__error").forEach(p => { p.hidden = true; p.textContent = ""; });
  }
  function showFieldError(name, msg) {
    const p = form.querySelector(`[data-field="${name}"] .field__error`);
    if (p) { p.textContent = msg; p.hidden = false; }
    else { banner.textContent = msg; banner.hidden = false; }
  }

  function close(force) {
    if (dirty && !force && !confirm("Discard your changes?")) return;
    document.removeEventListener("keydown", onKey);
    back.remove();
  }
  function onKey(e) {
    if (e.key === "Escape") close();
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) form.requestSubmit();
  }
  document.addEventListener("keydown", onKey);
  back.addEventListener("pointerdown", e => { if (e.target === back) close(); });
  form.querySelector("[data-cancel]").onclick = () => close();

  form.addEventListener("submit", async e => {
    e.preventDefault();
    if (save.disabled) return;                       // double-submit guard
    clearErrors();

    const data = Object.fromEntries(new FormData(form));
    const missing = fields.find(f => f.required && !String(data[f.name] ?? "").trim());
    if (missing) {
      showFieldError(missing.name, `${missing.label} is required`);
      form.querySelector(`[data-field="${missing.name}"] input`)?.focus();
      return;
    }

    save.disabled = true;
    try {
      await onSubmit(data);
      close(true);                                   // success: nothing to re-enable
      toast("Saved");
    } catch (err) {
      save.disabled = false;                         // re-enable ONLY on failure
      if (err.errors) Object.entries(err.errors).forEach(([k, v]) => showFieldError(k, v));
      else { banner.textContent = err.message; banner.hidden = false; }
    }
  });

  if (onDelete) form.querySelector("[data-del]").onclick = async () => {
    if (!confirm(onDelete.confirm)) return;
    await onDelete.run();
    close(true);
  };
}
```

## Wiring it to a screen

Two callers per entity, both passing the same repaint function. Without this, you end up with a
beautiful form helper and no route to it:

```js
document.getElementById("new-person").onclick = () => openPersonForm(null);
body.addEventListener("click", e => {
  const card = e.target.closest("[data-person-id]");
  if (card) openPersonForm(rows.find(r => r.id === +card.dataset.personId));
});

function openPersonForm(person) {
  openRecordForm({
    title:  person ? "Edit person" : "New person",
    fields: PERSON_FORM,
    values: person || {},
    onSubmit: async data => {
      const saved = person
        ? await api("PATCH", `/api/people/${person.id}`, data)
        : await api("POST", "/api/people", data);
      if (person) Object.assign(person, saved);      // repaint from memory
      else rows.unshift(saved);
      paint();
    },
    onDelete: person && {
      confirm: `Delete ${person.name}? This can't be undone.`,
      run: async () => { await api("DELETE", `/api/people/${person.id}`);
                         rows = rows.filter(r => r.id !== person.id); paint(); },
    },
  });
}
```

## The nine rules baked into that code

1. **Double-submit guard lives in the helper**, not at the call site. A founder clicking Save twice
   on a slow connection should never create two records. In the reference app, **no modal save button
   anywhere disables while the request is in flight.**
2. **Re-enable only in the `catch`.** On success the modal closes, so there's nothing to re-enable.
3. **Every interpolated value goes through `esc()`.** This is the single most likely day-one bug and
   nothing in your app will catch a miss.
4. **Required checks show a message**, not a silent focus jump. Eight lines, and it's the difference
   between "the app is broken" and "oh, I missed a field".
5. **Clear all errors at the top of every submit**, or stale messages from the last attempt linger.
6. **Unsaved-changes protection.** Escape and backdrop-click both close instantly. Someone types 300
   words of notes, taps slightly outside, and loses everything. The reference app has this bug. Track
   one `dirty` flag and confirm.
7. **Writes return the saved row; repaint from memory.** Don't refetch the whole list. Only refetch
   when the mutation changes *which rows belong on screen*, like editing something out of the current
   filter.
8. **Delete confirms, and counts the damage out loud** when it cascades: "This deletes the project,
   its 4 tasks and 2 files." Skip the undo toast. Re-inserting a deleted row gives it a new id and
   silently orphans anything that referenced the old one, which is why the reference app needed a
   whole server-side journal table to do undo properly.
9. **Whitelist writable columns on the server** (see `tab-template.md`). Client-side validation is
   for humans. The allow-list is what actually protects the data.

## Testing, later

When your agent offers to write tests (it will), make sure the second one exists:

- Open the page, click Add, fill the required field, Save, assert the toast and assert the row is in
  the database.
- **Submit it blank.** Assert no row was created, the modal is still open, and the field's error
  paragraph is visible with text in it.

Nobody writes the second one, and it's the one that catches the failure that matters. Do this once
the app is real and you're afraid to change it, not on day one; a browser test harness is its own
multi-session project.
