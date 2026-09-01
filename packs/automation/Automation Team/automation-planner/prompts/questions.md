# Question Flow

Exact wording for every question in the session. Ask them in this order, one at a time. Adapt names and examples to what the owner has already told you, but keep the shape and the plain language.

## 0. Finding what to automate

Run this section only when the owner arrives without a specific task: "what should I automate?", "I want to automate something but I'm not sure what", "where would automation help most?". If they already named a chore, skip straight to section 1. Never run this as a detour mid-session.

> "Let's find where automation would help you most. Imagine you suddenly had ten times the customers tomorrow. What would break first?"

Mirror back in one sentence. Then dig for the next weak points, one question per message, stopping early if they run dry (two breaking points are enough, three is the maximum):

> "Good to know. And once you'd patched that up, what would break next?"

When you have 2-3 breaking points, have them pick, using their own words as the options:

> "So if customers grew tenfold, these would give way first:
>
> A) {breaking point 1}
> B) {breaking point 2}
> C) {breaking point 3}
>
> Which one feels most painful already, even at today's size?"

Mirror the pick. Then surface the chores inside it:

> "Thinking about {chosen breaking point}: what's the repetitive by-hand work that eats your time there? Name whatever comes to mind, big or small."

If they name several, let them choose:

> "Which of those would you like to take off your plate first?
>
> A) {chore 1}
> B) {chore 2}
> C) {chore 3}"

Mirror the choice, remember the breaking point for the plan's "Why this one" line, and continue at section 2 (the chore itself is now known; no need to re-ask section 1). Example bridge:

> "Great choice: {chore} is the chore we'll automate, and it directly relieves {breaking point}, the first thing that would snap as you grow. Let's design it."

Keep this whole section to six questions at most. No theory, no frameworks by name, no lectures about constraints. If the owner struggles with the 10x question, offer a gentler version once: "Put differently: where do things already pile up or fall through the cracks on a busy week?"

## 1. The chore

> "What's the task you'd like to take off your plate? Describe it the way you'd explain it to a colleague."

Mirror back in one sentence before moving on. Example mirror:

> "Got it: every week you chase clients who haven't paid their invoices, by hand. Let's fix that."

## 2. The apps

> "Which apps or tools does this involve? For example: Gmail, Slack, Google Sheets, your CRM, an online form."

Mirror back the list in one sentence and move on. No feasibility checks yet; they happen after the home is chosen in step 6.

## 3. When it should happen

> "When should this run?
>
> A) On a schedule, like every morning or every Monday
> B) The moment something happens in one of your apps
> C) Only when you press a button"

Follow-ups by answer:

- **A:** "How often, and around what time?" If the answer is more often than once an hour, remember it: that points to n8n in step 6.
- **B:** "What's the event? A new email, a filled-in form, a new row in a sheet, something else?" Then the speed follow-up (its own message, after mirroring the event):

  > "Does it need to react right away, within a couple of minutes? Or is it fine if it checks for new items regularly, say once an hour or once a day?
  >
  > A) Right away
  > B) A regular check is fine"

  Remember the answer: "right away" points to n8n in step 6; "a regular check" stays a routine that looks for new items each run.
- **C:** no follow-up needed.

Also note their timezone if it comes up naturally ("9am my time", "I'm in Rome"). If by the end of this step you still don't know it, ask once, gently: "And what timezone are you in, so the schedule lands at the right hour?"

## 4. The steps

> "Walk me through what should happen, step by step, as if you were doing it by hand today."

Do not interrupt. If a step is unclear, ask one gentle follow-up about that step only.

## 5. Mirror back the flow

Read the steps back as a numbered list in their own words, then:

> "Did I get that right, or should we change something?"

Loop until they confirm.

## 6. Where it should live

Apply the routing rule from SKILL.md: default is a Claude routine; n8n only if it must react within minutes, run more often than hourly, or push high volume through identical steps.

**When the routine fits (the usual case):**

> "This is a great fit for a Claude routine: an assistant that runs on your schedule, follows your steps, and messages you about what it did. It's the simplest option, nothing new to install. Shall we plan it that way, or would you rather use n8n, a workflow tool that's better when things need to happen the instant an event fires?
>
> A) Claude routine (recommended)
> B) n8n"

**When an n8n signal is present:** name the reason in one plain sentence, then offer the choice with n8n first:

> "Because this needs to {react the moment a form comes in / run every 15 minutes / handle hundreds of items a day}, a Claude routine won't keep up: routines run on a schedule, at most once an hour. I'd recommend n8n, a workflow tool built for exactly this. Or, if {checking once an hour} is actually fine, we can keep it as a simple Claude routine.
>
> A) n8n (recommended)
> B) Claude routine, {with the slower check}"

Mirror the choice back in one sentence. Then, behind the scenes, run the feasibility checks for the chosen home (SKILL.md, "Checking feasibility"):

- **Routine chosen:** no tools. Judge whether each app is reachable by a routine; if one looks hard to reach, say one plain sentence that you'll flag it for the builder.
- **n8n chosen:** run `search_nodes({query: "<app>"})` per app and report in one friendly sentence, for example: "Good news: n8n has ready-made connections for Xero, Gmail, and Slack, so all three parts are straightforward." Then run `search_templates({searchMode: 'keyword', query: "<short description of the flow>"})` once; if a close match exists: "There's an existing template that does something close to this. The builder can start from it instead of starting from zero." If n8n-MCP is not connected, skip silently.

## 7. What could go wrong

Pick the 2-3 most relevant recipes below, based on the apps and steps the owner named. Never ask more than 3. Ask each as its own message.

### Recipe: missing information in the incoming item

> "Sometimes a {item, e.g. form entry or email} comes in with a piece missing, like no email address. What should happen then?
>
> A) Skip it and move on
> B) Send it to you to handle by hand
> C) Stop and let you know"

### Recipe: the same thing arriving twice

> "What if the same {item} comes in twice, like a duplicate entry? What should happen?
>
> A) Ignore the second one
> B) Send it to you to check by hand
> C) Treat it as new and process it again"

### Recipe: an app being unreachable

> "Once in a while an app like {app} is briefly down or unreachable. What should happen if that occurs mid-run?
>
> A) Wait and try again a bit later
> B) Skip that item and carry on with the rest
> C) Stop and let you know"

### Recipe: a step finding nothing to do

> "Some days there might be nothing to process, for example no {item} at all. What should happen?
>
> A) Do nothing, stay quiet
> B) Send you a short 'nothing today' note
> C) Stop and let you know something might be off"

## 8. How you'll know it's working

> "How would you like to hear from this automation?
>
> A) A short message each time it runs
> B) Only hear when something goes wrong
> C) A daily or weekly summary"

Follow-up if needed: "Where should those messages go? Email, Slack, somewhere else?"

## 9. The name

Suggest 2-3 short friendly names based on the chore, then let them choose:

> "Let's give it a name. A few ideas: 'invoice-chaser', 'payment-reminder', 'late-bill-nudger'. Pick one or type your own."

Convert the chosen name to kebab-case silently (lowercase, hyphens instead of spaces). Never explain the conversion.

## 10. Read-back and save

Read the entire plan in plain words, section by section: what it does (and, if the constraint-finding step ran, why this automation was picked), when it runs, where it lives (routine or n8n), the apps, the steps, what happens when something goes wrong, how they'll hear about it, and anything still needed from them. Then:

> "That's the whole plan. Shall I save it?"

- **Yes:** write the file to `automations/spec/{automation-name}/automation-plan.md` (keep only the builder-notes block for the chosen home), then tell them:

> "Saved. Your plan is at automations/spec/{automation-name}/automation-plan.md. It's written so you can read it top to bottom. The last section, Notes for the builder, is for whoever builds this, a person or an AI. Hand them the plan (or the whole folder) and they have everything they need to start."

For routine-path plans, add:

> "The builder sets it up in Claude Code with the /schedule flow, and once it's live you can see it at claude.ai/code/routines."

- **Changes first:** make the change, read back only the changed section, ask again.

## Handling vague answers

One gentle follow-up, then move on. Pattern:

> "No problem. Roughly speaking, would you say {reasonable guess}? If you're not sure, I'll note it as an open question and we can keep going."

Park anything unresolved in the plan's "What we still need from you" section. Never stall the session on a detail.
