# Glossary

The words used throughout this repository, in plain English.

Use these exactly. Each entry ends with an _Avoid_ line naming the near-synonyms to skip, so the same word always means the same thing.

## Slice

One thing a person can actually do, start to finish: a screen they look at, the rule that decides what happens, and the place the answer is stored. "Log a complaint and see it in the list" is a slice. "Build the complaints system" is not.

Work is always one slice at a time.

_Avoid_: feature, story, ticket, requirement

## Brief

The written answer to who this is for, what problem it solves, and what "working" means. It lives in `project/BRIEF.md` and it is the thing your assistant reads before every session.

A brief is short. If it takes more than a page, the project is too big for a first build.

_Avoid_: requirements, spec, PRD, scope document

## Seam

The place where two parts of your software meet, arranged so you can replace one side without touching the other. Your app talks to email through a seam, so switching email providers changes one file instead of forty.

Seams are where the cost of change is decided. Put one where something is genuinely likely to vary.

_Avoid_: boundary, layer, integration point

## Deep module

One door into a big room: a small number of things you can ask for, hiding a lot of work behind them. "Send the customer their invoice" is one door; behind it sits formatting, attaching, sending, and recording that it was sent.

The opposite is fifty doors into a broom cupboard, where every caller has to know all fifty. When something feels hard to use, it usually has too many doors.

_Avoid_: service, component, API, class

## The deletion test

Imagine deleting a file. If nothing gets harder, it was doing nothing and should go. If the same work reappears in five other places, it was earning its keep.

This is how to tell useful structure from structure that only looks tidy. Use it whenever you are wondering whether something should exist.

_Avoid_: refactor, cleanup, tech debt

## Guardrail

A rule the computer enforces, so a mistake cannot turn into a disaster. Not a note in a document, not a good intention: something that fails loudly and stops the work.

The check that refuses to create a table without row security is a guardrail. "Remember to turn on row security" is not.

_Avoid_: best practice, policy, security measure, convention

## Level

How much machinery your app needs: 0, 1, 2, or 3. Set once during the interview, recorded in `.stack-level`, and changed only by `/level-up`.

_Avoid_: tier, architecture, stack, plan

## Live

Reachable on the internet by someone who is not you, on a machine that is not yours. Running on your laptop is not live.

_Avoid_: deployed, shipped, in production, released

## Migration

A written, replayable change to the shape of your database, saved as a file you keep. Every table and every column arrives through one.

Because they are files, your database can be rebuilt from nothing by replaying them in order, and every change has a date and a reason.

_Avoid_: schema change, updating the database, DB change

## Row security

The database's own rule about which rows a given person is allowed to see. It sits underneath your website, so it still holds when the website has a bug.

This is the difference between "the screen does not show other people's records" and "other people's records cannot be read." Only the second one is true security.

_Avoid_: permissions, access control, authorization

## Renovation

Changing an app you keep living in, rather than knocking it down and starting again. Going from level 1 to level 2 is a renovation: same building, new front door and new locks on the internal rooms.

_Avoid_: rewrite, v2, migration (that word is taken)

## Recipe

A written procedure your assistant follows the same way every time. A level 0 project is a recipe. So is every skill in this repository.

A recipe is worth writing when the job repeats and you care that it comes out the same each time.

_Avoid_: prompt, script, automation, workflow

## Where these come from

The vocabulary for deep modules, seams, and the deletion test is adapted from [Matt Pocock's codebase-design skill](https://github.com/mattpocock/skills), which draws on John Ousterhout's *A Philosophy of Software Design* and Michael Feathers' *Working Effectively with Legacy Code*. The originals are written for engineers. These are the same ideas in the words a business owner already has.
