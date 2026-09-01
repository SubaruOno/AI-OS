# Gap Taxonomy

Every gap in the extraction has a root cause that determines the correct resolution path.
Misclassifying a gap wastes client time or misses information already available.

## Type A — Never Communicated

**Definition:** The information was genuinely never described in any session, document, email, SMS, or call material available for this client. Nobody in the room ever mentioned it.

**Test:** Search all available source material for any mention of this information. If nothing is found anywhere, it is Type A.

**Resolution:** Only Type A gaps generate follow-up questions to the client.

**Common examples:**
- The volume of transactions at a particular step was never mentioned
- A specific role was referenced ("our ops person") but the name and exact responsibilities were never stated
- A decision criterion was implied ("we have a threshold") but the actual threshold was never stated

## Type B — Industry Shorthand

**Definition:** The information WAS communicated, but using industry jargon, assumed knowledge, or shorthand that the extractor did not fully unpack. The speaker assumed the listener understood.

**Test:** Is there a phrase in the source material that implies this information but does not state it explicitly? Does the industry context explain what was left unsaid?

**Resolution:** Internal resolution — research the industry term, look up the standard process behind the shorthand, or apply industry knowledge. Do NOT ask the client for information they believe they already communicated.

**Common examples:**
- "We just do a BAS lodgement" — the 12-step ATO reporting process was never described step by step
- "We run the payroll" — whether this means TimeTarget → Xero → manual bank transfer or something else was not spelled out
- "We do our WHS checks" — which specific checks, forms, or systems are standard for this industry were assumed known

**How to resolve:** Look up the standard process for this industry operation. Document it as MEDIUM confidence with a note: "Standard [industry] process assumed." Flag for client confirmation at next session (low priority).

## Type C — Missed in Extraction

**Definition:** The information IS present in the source material but was not captured by the extraction sub-agent. It exists in a transcript, email, or document but was overlooked, misclassified, or attributed to the wrong step.

**Test:** Re-read the relevant source passages carefully. Is the information there but under a different framing or in a different context than expected?

**Resolution:** Internal resolution — re-scan source material for the specific value. Use the [RQ] Resolve Questions capability if available. Do NOT ask the client for information they have already provided.

**Common examples:**
- A tool name was mentioned in passing early in the transcript and not linked to the step it belongs to
- A duration was mentioned in a different context ("it takes about an hour") but not connected to the step it applies to
- A volume was stated ("we do about 30 jobs a week") but not linked to the specific decision gateway it informs

## Classification Rules for the Sub-Agent

When populating `_gaps.gap_type` on a step:

1. Did the client or any source material mention this information, even vaguely? → Check Type B or C first
2. If mentioned in vague shorthand without explanation → **Type B**
3. If mentioned somewhere in source material but not captured in this step → **Type C**
4. If never mentioned anywhere → **Type A**
5. If unsure between B and C → classify as **Type B** (less harmful than generating unnecessary questions)

## Impact on Question Generation

Only **Type A** gaps generate follow-up questions to the client.
**Type B** gaps are annotated with a research note (to be resolved before next session).
**Type C** gaps are flagged for re-scan of source material (the [RQ] capability handles this).
