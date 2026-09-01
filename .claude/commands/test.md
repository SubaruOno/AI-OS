# Test

> The assistant checks its own work by actually using it. The substance lives in the mirrored **test skill**, which also fires whenever someone asks “is this working?” or after implement builds something.

Run the test skill now against whatever was just built or changed this session: identify the deliverable, pick the matching playbook (script, app, integration, document, or workspace change), exercise it for real, try to break it gently, fix what fails, and report plainly. Never report "done" on work that wasn't exercised.

---

## Finish with log (automatic)

Run the log workflow as the final step. It sweeps anything unlogged, checks context drift, then saves and backs up. The person should not have to remember a harness-specific shortcut after a build.
