# Implement

Execute an implementation plan created by create-plan. Read the plan thoroughly, execute each step in order, and report on the completed work.

## Variables

plan_path: $ARGUMENTS (path to the plan file, e.g., `plans/2026-01-28-add-stripe-integration.md`)

---

## Instructions

### Phase 1: Understand the Plan

1. **Read the plan file completely.** Do not skim — understand every section.
2. **Verify prerequisites:**
   - Are there open questions that need answers before proceeding?
   - Are there dependencies on external resources or user decisions?
   - If blockers exist, stop and ask the user before proceeding.
3. **Confirm the plan is ready:**
   - Status should be "Draft" or "Ready"
   - All sections should be filled out (no placeholder text remaining)

---

### Phase 2: Execute the Plan

1. **Follow the Step-by-Step Tasks in exact order.**
   - Complete each step fully before moving to the next
   - If a step involves creating a file, write the complete file — not a stub
   - If a step involves modifying a file, read the file first, then apply changes precisely

2. **For each task:**
   - Read any files that will be affected
   - Make the changes specified
   - Verify the change is correct before proceeding

3. **Handle issues gracefully:**
   - If a step can't be completed as written, note the issue and adapt if the intent is clear
   - If you're unsure how to proceed, ask the user rather than guessing
   - Document any deviations from the plan

---

### Phase 3: Validate

1. **Run through the Validation Checklist** from the plan
   - Check off each item
   - Note any that fail

2. **Verify Success Criteria** are met
   - Confirm each criterion is satisfied
   - Note any gaps

3. **Check cross-references and consistency:**
   - Ensure new files are referenced where they should be
   - Verify both `CLAUDE.md` and `AGENTS.md` are updated and identical if workspace structure changed
   - Verify mirrored skill folders match if a skill changed
   - Confirm naming conventions are followed

---

### Phase 4: Update Plan Status

After implementation, update the plan file:

1. Change `**Status:** Draft` to `**Status:** Implemented`
2. Add an Implementation Notes section at the end:

```markdown
---

## Implementation Notes

**Implemented:** <YYYY-MM-DD>

### Summary

<Brief summary of what was done>

### Deviations from Plan

<List any changes made during implementation, or "None">

### Issues Encountered

<List any problems hit and how they were resolved, or "None">
```

---

### Phase 5: Test, then log

1. **Run test** on what was just built. Exercise it for real, fix what fails, and report plainly. Never call an implementation done without it.

2. **If a new capability was built** that future sessions should know about, update both constitutions so they remain identical and match reality. Sync the skill folders when relevant.

3. **Run log.** The standard close handles ledger rows, context drift, save, and backup. Report in the person's language.

---

## Report

After implementation, provide:

1. **Summary:** Bulleted list of work completed
2. **Files changed:** List all files created, modified, or deleted
3. **Validation results:** Status of each checklist item
4. **Deviations:** Any changes from the original plan
5. **Next steps:** Any follow-up actions needed (if applicable)

Format:

```
## Implementation Complete

### Summary
- <What was done>
- <What was done>

### Files Changed
**Created:**
- `path/to/new-file.md`

**Modified:**
- `path/to/modified-file.md`

**Deleted:**
- (none)

### Validation
- [x] <Passed check>
- [x] <Passed check>

### Deviations from Plan
<None, or list deviations>

### Plan Status
Updated `plans/YYYY-MM-DD-{name}.md` status to "Implemented"
```

---

## Document it (automatic)

If this built or meaningfully changed a system, an integration or an app, run `/document` for it before finishing. That writes the doc and files a row in `docs/_index.md` so future sessions can find it. Don't ask, and don't do it for a one-line fix.

---

## Finish with log (automatic)

Run the log workflow as the final step. It sweeps anything unlogged, checks context drift, then saves and backs up.
