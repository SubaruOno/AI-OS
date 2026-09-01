# 00: Setup

30 minutes, once. Do this before anything else.

---

## What you need

| Thing | Cost | Why |
|---|---|---|
| Claude Code | Included with your Claude plan | Runs the four skills |
| vidIQ | About $12 a month | **Optional.** Automates the research. Without it you do the same research by hand. |
| A phone | You have one | Posting and filming |

---

## Step 1: Claude Code

Skip if you already have it.

1. Go to claude.com/code and follow the install for your machine
2. Open a terminal and run `claude`
3. Sign in with your Claude account

You now have Claude Code. You will not need to write any code.

## Step 2: A folder for this

Make one folder that holds everything for this account. Anywhere you like.

```
mkdir instagram
cd instagram
claude
```

Run `claude` from inside that folder every time. Your research and scripts save there.

## Step 3: Install the skills

Copy the four skill folders from this pack into `.claude/skills/` inside your folder.

```
instagram/
  .claude/
    skills/
      ig-icp-research/
      ig-ideas/
      ig-script/
      ig-review/
```

Copy the whole folder for each skill, including its `references` subfolder. The skills break without those files.

Check it worked: type `/` in Claude Code. You should see all four listed.

## Step 4: vidIQ, optional

vidIQ automates the research. It finds the reels your buyer already watches, in about two minutes.

**You do not need it to use this pack.** Without vidIQ the research skill hands you a personalised list of exactly what to search on Instagram yourself, plus the method for spotting winning formats by eye. Same output file. It takes you 60 to 90 minutes instead of two.

**Run the manual searches even if you buy vidIQ.** A tool only finds what the query asked for. Your own eyes find what it missed.

1. Sign up at vidiq.com
2. Take the paid tier, around $12 a month. The free tier does not include enough credits.
3. Connect it to Claude Code as an MCP server. vidIQ's site has the current connection instructions and the exact command, follow those.
4. In Claude Code, ask: **"check my vidiq balance"**

If a number comes back, you are done.

### What it costs you in credits

| Action | Credits |
|---|---|
| One outlier search | 5 |
| One profile lookup | 5 |
| **Day 1 full research** | **20 to 30** |
| **Weekly ideas run** | **10 to 15** |
| **Per month** | **about 90 to 100** |

Check your plan covers roughly 100 a month. If you run out, the skill switches to manual mode rather than stopping.

---

## Step 5: Check it all works

In Claude Code, run:

```
/ig-icp-research
```

It should ask you what you sell and who you sell it to.

If it does, you are ready. Go to guide 01.

---

## If something breaks

**Skills do not show up.** They are in the wrong place. They must be in `.claude/skills/` inside the folder you launch `claude` from.

**vidIQ says no credits.** You are on the free tier. Upgrade, or run the research in manual mode. The skill handles both.

**A skill says it cannot find a reference file.** You copied the SKILL.md but not the `references` folder. Copy the whole skill folder.

**A skill says it cannot find icp.md.** Run `ig-icp-research` first. Everything depends on it.
