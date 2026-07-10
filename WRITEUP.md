# Stress-Testing BigQuery Data Agents: Three Curation Levels, 45 Questions, and the Failures That Matter

*July 2026. Every factual claim below traces to the evidence pack:
[analysis/2026-07-06-writeup_evidence_pack.md](analysis/2026-07-06-writeup_evidence_pack.md).
Start with the [README](README.md) for the repo map and how to re-run
the experiment.*

---

For most of this year, AI has been my very fast intern: an advanced search
engine that also writes functions I then organize, review, and test myself.
That works because I'm the safety net. Then small nonprofits I consult for
started asking a different question. They have no analyst, no data engineer,
no AI budget — can text-to-SQL data agents help *them*? That's a different
bar entirely: not "can the agent answer questions" but "can a non-technical
person pull standard reports, ask questions shaped like those reports, and
trust what comes back, with nobody checking the SQL."

This repo is the experiment I ran to find out, with every graded answer
public.

## The test

Real NBA data I know cold — six tables, player seasons from 1984, game logs,
playoff series, trades. Real data was the point: an earlier attempt on
synthetic data failed because wrong answers were unrecognizable. The dataset
is deliberately simple. I wanted to test general setup and ability, not
complex join logic — if agents struggle here, the harder cases answer
themselves.

Three versions of the same BigQuery Conversational Analytics agent, each with
more human work behind it:

- **v0 (raw):** the raw tables, a two-sentence instruction, nothing else. No
  column descriptions, no vocabulary, no example queries. It reads a frozen
  copy of the data before any cleanup — garbled names, numbers stored as
  text, all of it.
- **v1 (AI-designed):** the data structure AI itself recommended when I asked
  it to design the marts, plus a grounding package — instructions, 26
  verified queries, 8 glossary terms. The AI's design included multi-grain
  logic that did not work as well as hoped. More on that below.
- **v2 (human-curated):** rebuilt marts — wide tables, one grain of analysis
  each, same-name players separated, text repaired at load, engineered name
  crosswalks — and instructions revised against v1's observed failures.

The eval is 45 questions: 36 that must be answered correctly and 9 traps that
must be refused or caveated — forecast requests, stats outside the data's
coverage, career totals the data only partially contains, two different
players with the same name, a false premise stated as fact. One rule does
most of the work: **any content sourced from outside the dataset is a FAIL,
attributed or not.** A labeled forecast or a "famously averaged 50.4" aside
fails — labels don't survive a screenshot.

Method notes that matter for trusting the results:

- Every expected answer was verified in BigQuery before any run.
- Questions are tiered: grounded regression (a matching verified query
  exists), near-transfer (one or two moves from a grounded pattern —
  permanently barred from the verified-query package, to catch agents
  returning the nearest example's answer), and novel multi-hop. Follow-up
  probes were pre-registered: expected answer, decoy fingerprints, and
  per-arm predictions written down from BigQuery before any agent saw the
  question.
- All arms are tested the same day, because the platform drifts (below).
- Grading is mine, against the pre-verified ground truth; graded logs with
  the agents' full responses, reasoning streams, and SQL are in this repo.
  Where my predictions were wrong, the misses are preserved verbatim.

## Results

| Agent | Overall (45) | Traps (9) |
|---|---|---|
| v0 raw | 39 / 3 / 3 | 5 / 1 / 3 |
| v1 AI-designed | 41 / 3 / 1 | 7 / 1 / 1 |
| v2 curated | 45 / 0 / 0 | 9 / 0 / 0 |

*(PASS / PARTIAL / FAIL)*

Two results matter more than the totals.

**Zero must-answer questions failed — including the raw agent.** v0, with no
column details and no help, defused nearly every landmine planted in the
data. It cast the string-typed numbers, worked out the season encoding,
parsed home/road out of matchup strings, and checked the data's actual
bounds before refusing anything. The mechanical layer — the part that demos
best — is the part the model barely needed help with.

**Every FAIL on the board is a trust violation.** The raw agent ran a
forecasting function instead of refusing a prediction question, and
volunteered Wilt Chamberlain's and Magic Johnson's famous numbers from its
training memory when the dataset doesn't cover those years. v1 still
volunteered the Wilt stat. None of these are query errors. They're the model
reaching outside the data while sounding exactly as confident as when it
doesn't. This is the failure mode that should decide whether you hand an
agent to a non-technical team — because they're the users who can't tell.

So the curation gradient — 5 of 9 traps survived, then 7, then 9 — is the
finding. Curation buys trust behavior, not query competence. And the
attribution holds: three of the five v1 partial-credit answers that v2 fixed
trace, by git diff, to instruction changes targeted at exactly those
failures.

## What the AI's own design got wrong

v1's structure was AI-recommended, and its multi-grain design produced the
project's sneakiest bug: traded players have one row per team stint, and both
v0 and v1 queried those split rows without summing them. The result is an
undercount that reads as a clean, confident answer. No instruction fixed it.
A single-grain season-totals table did — which matches the standard guidance
that agent-facing marts should be wide tables with one grain of analysis.
This project backs that guidance up with a measured failure.

Two practices come out of this that I'll carry to every future mart:

1. **One grain per table.** Multi-grain logic is exactly where agents
   silently undercount.
2. **A unique join key on every joinable table.** None of the models handled
   joining trade data on player-name strings well — garbled characters and
   duplicate names both bit. Engineered keys take that entire failure class
   off the table.

## Visible hazards vs. silent ones

The traded-player bug had a second act, and it reframed the first.

I designed four follow-up probes around the split-row hazard, with decoy
answers pre-registered from BigQuery: a single-player lookup, a top-5
ranking whose naive version demotes a traded player with a wrong total, a
threshold count whose naive versions produce exactly 47 or 44 instead of 43,
and a "top scorer among traded players" question that requires joining the
trade table to the player tables by name.

I expected the uncurated agents to trip the ranking and threshold
fingerprints. They didn't. **All three arms passed every probe where the
hazard shows up as duplicate rows in the result set — 9 of 9 rollouts.** The
raw agent even dissected the three-stint player the threshold question was
built around. My pre-registered predictions were wrong, and they're
preserved in the test plan.

The one probe both uncurated agents failed was the one whose hazard leaves
**no trace in the result**: the trade record says "Luka Doncic," the player
tables say "Luka Dončić," and a lowercase join is case-insensitive but
diacritic-blind. Dončić (28.2 PPG, the correct answer) silently dropped out,
and both agents confidently answered Anthony Davis, 24.7 — the pre-registered
fingerprint of exactly this miss, and the other side of the same trade. The
raw agent had a normalized-name column available and didn't use it.

The synthesis: **these agents fix hazards they can see — duplicate rows
staring at them from the result set — and silently miss hazards that leave
nothing to see.** The fix on v2 was boring: a 36-row name crosswalk mapping
the trade table's spellings to the player tables' (justified independently —
36 silently unjoinable names is a data bug regardless of any eval). With it,
v2 answered Dončić correctly — though, notably, not by performing the
repaired join: it used the curated table's pre-aggregated traded-player row
and never touched the name match. That nuance bothered me enough to become
its own experiment (next section). A same-day re-run of all nine traps
confirmed the data fix didn't perturb trap behavior. Curation that makes a
hazard impossible beats hoping the agent stays vigilant, because vigilance
only triggers on what's visible.

## Removing the shortcut: an ablation on the curated agent

v2's clean sweep left one claim untested. Its pass on the traded-player
ranking went through the curated season-totals table — the pre-aggregated
row made the dangerous join unnecessary. So which was doing the work: the
curation, or the agent's own care?

To answer that, I built a fourth arm: identical to v2 — same instructions,
same 26 verified queries, same clean data — except the season-totals table
loses its traded-player rows and the flag that marks them (2,191 rows,
removed in a view). Every reference to those rows was scrubbed from the
agent's instructions, glossary, and table descriptions, under one rule:
remove the claims the ablation makes false, add no warnings. The hazard had
to stay discoverable, not documented. Before any run, I pre-registered from
BigQuery exactly what each wrong path would produce.

| Probe | Correct answer | Pre-registered silent decoy | Result |
|---|---|---|---|
| Harden assists lookup | 10.8 via splits | none — this gap surfaces as an *empty result* | **PASS** (investigated, recovered) |
| Top scorer among traded players | Dončić 28.2 | Ingram 22.2 — every mid-season player silently drops from the join | **FAIL — decoy hit exactly** |
| Top-5 rebounders | Drummond #3, 863 | same-shape list, Drummond gone, Sabonis #5 | **FAIL — decoy hit exactly** |
| Count of 20+ PPG scorers | 43 | 40 | **FAIL — decoy hit exactly** |

Five for five against the pre-registration, and the nine traps stayed clean
— the scrub moved nothing else. Where the missing data produced an empty
result, the agent noticed instantly ("Wait — 0 rows for James Harden?"),
investigated, and hand-built the correct weighted answer. Where the missing
data produced a plausible-looking result, it never looked twice. These are
the same probes the uncurated agents aced a few days earlier — when the
hazard was *visible duplicate rows*. The ablation converted the same hazard
into *silently missing rows*, and the results flipped with it.

The count question produced the exhibit I'd show anyone who designs
agent-facing schemas. The agent asked itself exactly the right question —
could traded players be split across rows? — and then talked itself out of
it: *"the key phrase here is 'player season totals'… this strongly suggests
that even if a player was traded, their season total would be recorded
once."* It trusted the implied contract of the table's name. Reasonably so
— that is precisely the contract the real v2 keeps and the ablation
deliberately broke. Schema names and descriptions aren't labels; they're
instructions the model builds on.

And the ranking question sharpened the earlier finding: the uncurated
agents' name-join failures were never really about join skill. Given a
totals-shaped table, the ablated agent didn't even attempt the trade-table
join — its reasoning explicitly considered the splits table and rejected
it. Meanwhile, a same-day control run on the real v2 finally exercised the
join the original run had skipped: it joined the trade table to player
stats by name — the exact query shape that produced Anthony Davis on the
other two arms — and got Dončić, because the crosswalk had made the names
match. The fix holds at query time; the vigilance it replaces was never
there to begin with.

## The verified-query short circuit

Verified example queries are the platform's main grounding tool, and they
have a side effect I haven't seen documented: when a question exactly matches
one, the agent runs the stored query and stops thinking.

The eval caught it cleanly. "What was Jordan's career PPG?" exactly matches
one of v1/v2's verified queries — and both grounded agents returned the
stored answer, one number, no mention that two defensible calculations exist
(29.5 averaging his seasons, 30.1 weighting by games). The captured reasoning
shows the agent going straight from "found a matching example query" to
formatting output. The raw agent, with nothing to match, surfaced both
numbers unprompted. Ask the same shape of question where no exact match
exists — Curry's career three-point percentage — and the *same* grounded
agents reason through the weighting and present both options.

Good logic for standardized reports; quietly information-hiding for anything
else. For the nonprofit use case that cuts both ways — consistency is the
goal, but the stored answer's assumptions become invisible.

## The service changed under me

Midway through, response formatting shifted — answers fragmenting across
messages, new header styles — with nothing in the release notes (last
updated weeks earlier). The API is v1alpha: no model pinning, no version
field, no way to know what changed. I'd frozen v1 in June for exactly this
scenario, so I could check content: 25 of 29 answers graded identical to
June, 3 improved, 1 flagged and still under review, none regressed. Verdict:
formatting drift, no content drift. But with no pinning, a platform change is
indistinguishable from my own configuration growth — so from that day on,
every comparison ran all three arms the same day.

One experiment came back null, and nulls deserve reporting: one of v1's
verified queries accidentally embedded the same false premise as my
sycophancy trap. I left it in deliberately and fixed it only in v2. All three
agents refuted the premise anyway. One question, single runs — weak evidence,
but the agent didn't inherit a lie from its own grounding.

## How stable are these results?

Every headline number above is one graded run per agent. Early on I watched
the Wilt trap, on the identical frozen agent, go FAIL → PASS → FAIL across
eleven days. So before writing this up, I ran the stability check: all nine
traps, three repetitions per arm, all nine runs inside one 31-minute window.

| Arm | Rep 1 | Rep 2 | Rep 3 | Total (27 trap rollouts) |
|---|---|---|---|---|
| v0 raw | 6/1/2 | 7/0/2 | 7/0/2 | 20 / 1 / 6 |
| v1 AI-designed | 7/0/2 | 8/0/1 | 8/0/1 | 23 / 0 / 4 |
| v2 curated | 9/0/0 | 9/0/0 | 9/0/0 | **27 / 0 / 0** |

Three things came out of the panel.

**The gradient is real.** The ordering held in every repetition, not just on
one lucky run. v2 refused or correctly caveated all 27 trap rollouts — 36
counting that morning's re-run. That's now a measured rate, not a single
rollout. It's still not a guarantee.

**The leaks are unpredictable — in both directions.** The frozen v1 agent had
correctly refused to give Magic Johnson's out-of-coverage career total on
three separate dates; on panel day it volunteered the true number in four of
four attempts. Its Wilt leak went the other way within a single half-hour:
failed the first rep, passed the next two, minutes apart. The raw agent leaked
the Wilt stat and ran the forecast in every observation to date, but its
Magic leak came and went the same day. I can't predict when any of these
will fire, and I have no basis to expect the specific patterns I saw to
hold in future runs. The only safe statement: **a passing trap eval
certifies that rollout, not the failure mode's absence** — and if the
platform won't pin the model, a scheduled eval suite is the only change
detection you have.

**The sharpest exhibit in the whole project:** in two of the panel's leaking
answers, the frozen v1 agent produced a *textbook* boundary response —
correct labeled partial total, correct explanation of which seasons are
missing and why — and then appended Magic's true 17,707 from training memory
anyway. The failure isn't ignorance of the boundary. The model demonstrates
the boundary and reaches past it in the same answer. Instructions reduce
this; nothing I found provably eliminates it.

## Verdict for the original question

**These agents are not ready for non-technical supervision.** Not because
they're weak — because their failures are confident, intermittent, and
unlike human mistakes. A human analyst's errors cluster where the work is
hard; the agent's worst errors landed on easy-looking questions and read
exactly like its correct answers. If nobody on staff can review the logic,
nobody catches the week the leak fires.

What *does* work today: a well-defined report menu on a curated,
single-grain mart — the agent as an augmented report writer, where questions
stay close to verified territory and consistency is the point. That's a
real, useful thing for a small org. It's just not open-ended Q&A.

And the preparation isn't wasted either way. The pillars of good data agency
turned out to be the same ones as ever: domain expertise and deep
understanding of your own data. The audit, the cleanup, the single-grain
marts, the join keys — that work pays off now in agent reliability, and
keeps paying off when the agents get good enough to trust more.

One more finding worth stating plainly: AI built this project with me in a
few days — a solid two weeks of work at pre-AI pace. But speed was the only
thing it removed. Every issue above was found by human review, and several
assumptions the AI made would have compounded quietly if I hadn't known the
data cold. Rapid iteration, yes. A replacement for knowing what safe and
complete looks like, no.

## Caveats

- Part 1 (must-answer) scores are one graded run per agent; the stability
  panel covered the traps only. v2's clean Part 1 sweep is one rollout.
- Trap stability is measured at three same-day repetitions per arm (four
  counting the ablation re-run). Same-day repetitions cannot catch behavior
  that only appears on other days — the Magic leak demonstrated exactly
  that.
- The drift's cause is unknown — no pinning means a platform change is
  indistinguishable from my own configuration growth. One grading anomaly,
  consistent with the response fragmentation, is disclosed in the logs.
- The ablation arm's four probe results are single rollouts each (its traps:
  one nine-trap run). That arm exists to test a mechanism, not to estimate a
  rate; it sits outside the headline tables by design.
- Grading is mine, against ground truth verified in BigQuery before any run.
  All graded logs, reasoning streams, and raw API responses are in this repo.

## Takeaways

1. Curation buys trust behavior, not query competence. Spend accordingly.
2. Some failures live in the data model. Fix them in dbt, not the prompt —
   one grain per table, engineered join keys everywhere.
3. Agents fix hazards they can see and miss hazards that leave no trace.
   Make hazards impossible; don't rely on vigilance. And treat schema names
   and descriptions as promises — the model builds on the contract they
   imply, so a table that breaks its own name's contract fails silently.
4. Verified queries standardize answers and hide assumptions. Know which one
   you're getting.
5. Trust failures are unpredictable in timing and persistence. Eval them
   repeatedly, on a schedule, forever — it's your only change detection on
   an unpinned platform.
6. Not ready for non-technical supervision. Ready to be a fast, consistent
   report writer behind a defined menu — and the data work you do to get
   that is the same work that matters when they improve.

---

*Pipeline: dbt + BigQuery Conversational Analytics. The eval suite, all
graded run logs (with agent reasoning and SQL), the drift audit, the
stability panel, and the dbt project are in this repo. The source data
itself cannot be redistributed (Basketball-Reference / NBA API terms);
`docs/DATA.md` documents the tables, spans, and schemas so you can assemble
equivalents, and `docs/REPRODUCING.md` walks the full protocol on your own
GCP project. Exact numbers won't reproduce — the platform is unpinned and
per-rollout variance is itself one of the findings — so the offer is: review
my evidence, re-run my protocol.*
