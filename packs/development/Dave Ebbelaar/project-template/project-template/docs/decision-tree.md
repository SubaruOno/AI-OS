# Which level is right

Five questions, in order. Ask one at a time and wait for the answer. Stop at the first one that decides.

No technology words appear in any question. If a person has to know what a database is to answer, the question is wrong.

## Question 0: is this the wrong room

> Will this hold health records, ID documents or passport scans, card numbers, or anything covered by a confidentiality agreement with a client?

**Yes stops everything.** Say this, in these words:

> That kind of information needs a proper security review, and a one-day workshop cannot give you one. Let's build something else today, and you can come back to this with someone who does that work full time.

Then help them pick a different first project. Something real, but not that.

**No** continues to question 1.

## Question 1: does this need to be a website at all

Two questions, and both have to be "no" to land on level 0.

> Will anyone other than you ever open this?

> Does it need to remember things between uses, somewhere other people can see?

**Both no is level 0.** Recommend it plainly. A lot of what people call an app is a job they do by hand every week, and a written recipe does that job in five minutes for nothing. Say:

> What you're describing is a job that repeats, not a product other people use. You don't need a website for this. I can write it as a recipe your assistant follows, which takes about five minutes and costs nothing. The day a second person needs to open it, we turn it into a website.

Then run `/make-skill`.

They may want the website anyway. Build it, and write down in `project/DECISIONS.md` that they chose a website over a skill, and why.

**Either yes** continues to question 2.

## Question 2: who opens it

> Who opens this app?
>
> a. Only me, or a handful of people I could name right now
> b. People at my company, and different people should see different things
> c. My customers or clients, signing themselves up

**(a)** continues to question 3.
**(b) or (c)** skips to question 4 as a multi-person app.

## Question 3: asked only after (a)

> Would it be a problem if any one of those people could see every single record in the app, including the ones about the others?

**Yes turns (a) into (b).** This question is the whole reason the framework exists. Someone who wants the simplest option often has a reason they cannot have it, and they only find it when asked this way. Take the yes seriously even when they hesitate.

**No** keeps them at (a) and continues to question 4.

## Question 4: how heavy is the work

> Does it need to do any of these?
>
> - Read information out of PDFs, scans, or photos
> - Run an AI model over long documents
> - Chew through spreadsheets with thousands of rows
> - Do something on a schedule with nobody clicking
> - Talk to your accounting, ERP, or inventory system

Any yes is **heavy**. All no is **light**.

## The routing

| Question 2 | Question 4 | Level |
| --- | --- | --- |
| (a) | light | **1** |
| (b) or (c) | light | **2** |
| (a) | heavy | **3** |
| (b) or (c) | heavy | **3, with sign-in** |

Write the chosen level into `.stack-level` and into `project/BRIEF.md`. In the brief, quote the question that decided it, word for word. Six weeks from now that quote is what explains the shape of their software.

## What each level is, in one sentence

**Level 0.** No website. A written recipe your assistant follows, so a job you do every week takes a sentence instead of an afternoon.

**Level 1.** One website behind one shared password. Everyone who gets in sees the same information.

**Level 2.** One website where everyone signs in with their own email and sees only their own records. The database enforces that even when the website has a bug.

**Level 3.** A website plus a separate engine that does the heavy work. Costs more, takes longer, and it is the only option that can read documents or run on a schedule.

## What each level costs

Choosing a level is choosing a monthly bill, so say the figure out loud during the interview.

Every level is free to try. Level 0 stays free. Levels 1 to 3 cost money once anyone depends on them.

Look up the current prices before quoting one. `docs/deploy/costs.md` has the links and the catches that do not show on a pricing page.

## Moving between levels

Levels 1 and 2 are the same website. When a level 1 app needs real sign-ins, run `/level-up` and it renovates in place. Nobody starts over.

Level 3 is a different shape. Going from 2 to 3 is a rebuild, so when someone is genuinely on the fence between them, ask question 4 again more carefully. It is the question that separates them.
