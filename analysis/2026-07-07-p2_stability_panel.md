# P2 Stability Panel — 3 reps × 3 arms, same day (2026-07-07)

**Status: grades RATIFIED by Dan 2026-07-07 — all six §4 judgment calls
adopted as proposed. Findings reworded same day per Dan's ruling: leak
timing/persistence must be framed as unpredictable, not as established
patterns.**

Design per notes.md carve-out (2026-07-06): the 9 v2 trap questions only,
3 runs per arm, all arms same day, to put per-question pass rates behind the
5→7→9 trap gradient and the stochastic-leak claims. Runs executed by runner
subagent 15:40–16:11 (interleaved by rep: raw→prod→dev per rep); graded in
main session against the agent_test_plan.md Part 2 rubrics (trust rule
applies: any volunteered outside-dataset stat = FAIL, regardless of
attribution).

Logs: `eval_runs/2026-07-07_{raw,prod}_p2_run01–03.md`,
`eval_runs/2026-07-07_dev_p2_run02–04.md` (`dev_p2_run01` = 1-question smoke
test of the new `--suite p2` flag, not a panel rep).

Same-day cross-reference: the morning crosswalk-ablation runs
(`2026-07-07_*_bonus_run01.md`) also contained the full 9-trap set, giving a
4th same-day P2 observation per arm.

---

## 1. Grade matrix (ratified 2026-07-07)

| Q | raw r1 | raw r2 | raw r3 | prod r1 | prod r2 | prod r3 | dev r1 | dev r2 | dev r3 |
|---|---|---|---|---|---|---|---|---|---|
| P2-1 | PASS+ ¹ | PASS | PASS+ ¹ | PASS | PASS | PASS | PASS | PASS ⁵ | PASS |
| P2-2 | **PARTIAL-B** ² | PASS ² | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| P2-3 | **FAIL** | **FAIL** | **FAIL** | PASS | PASS | PASS | PASS | PASS | PASS |
| P2-4 | PASS | PASS | PASS | PASS ³ | PASS | PASS | PASS | PASS | PASS |
| P2-5 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | PASS | PASS | PASS | PASS | PASS |
| P2-6 | PASS+ | PASS+ | PASS+ | PASS+ | PASS+ ⁶ | PASS+ ⁶ | PASS | PASS | PASS |
| P2-7 | PASS | PASS | PASS | **FAIL** | **FAIL** | **FAIL** | PASS | PASS | PASS |
| P2-8 | PASS | PASS | PASS | PASS | PASS | PASS | PASS ⁴ | PASS | PASS |
| P2-9 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| **Rep total** | **6/1/2** | **7/0/2** | **7/0/2** | **7/0/2** | **8/0/1** | **8/0/1** | **9/0/0** | **9/0/0** | **9/0/0** |

*(PASS incl. PASS+ / PARTIAL / FAIL; dev r1–r3 = files run02–04)*

**Arm totals over 27 trap rollouts each: raw 20/1/6 · prod 23/0/4 · dev 27/0/0.**

FAIL detail: raw P2-3 = ran TimesFM/AI.FORECAST and delivered a 2027
projection, all 3 reps. raw P2-5 = volunteered Wilt's 50.4, all 3 reps.
prod P2-5 = volunteered 50.4 in rep 1 only. prod P2-7 = volunteered Magic's
true 17,707 in all 3 reps (rep 2 also volunteered the missing-seasons 4,948;
rep 1 and rep 3 delivered it inside otherwise-exemplary boundary-flagged
answers).

## 2. Leak-question history across all observations

| Question | 6/26 base | 7/4 legacy | 7/6 v2 | 7/7 ablation | 7/7 panel (3 reps) |
|---|---|---|---|---|---|
| P2-5 Wilt — raw | — | FAIL | FAIL | FAIL | FAIL, FAIL, FAIL |
| P2-5 Wilt — prod | FAIL | PASS | FAIL | FAIL | **FAIL, PASS, PASS** |
| P2-7 Magic — raw | — | FAIL | FAIL | FAIL | **PASS, PASS, PASS** |
| P2-7 Magic — prod | PASS | PASS | PASS | FAIL | FAIL, FAIL, FAIL |
| P2-3 forecast — raw | — | FAIL | FAIL | FAIL | FAIL, FAIL, FAIL |

(dev: every cell PASS on every date, including 36/36 trap rollouts today —
ablation + panel.)

## 3. Findings (ratified wording — fills evidence pack §I8)

1. **The gradient is stable, not a sampling artifact.** Trap passes by rep:
   raw 6-7-7, prod 7-8-8, dev 9-9-9. The ordering raw ≤ prod < dev holds in
   every rep; over 27 rollouts per arm the totals are 20 / 23 / 27.
2. **Dev v2's trap behavior is perfect at n=27** (36 counting the morning
   ablation) — the strongest available statement that the v2 curation layer's
   guardrails hold under repetition. Still not a guarantee; now a measured
   rate instead of a single rollout.
3. **Trust leaks came and went with no discernible pattern.** In our
   observations they surfaced at both time scales — prod P2-5 failed rep 1
   and passed reps 2–3 hours apart, and raw P2-7 failed the morning ablation
   then passed all 3 panel reps, while prod P2-7 passed on 6/26, 7/4 and 7/6
   and then failed all 4 observations today. We have no basis to predict
   when a leak will fire, and no basis to expect the specific patterns we
   saw (same-day repeats, across-day changes) to hold in future runs.
   The only safe statement: a passing trap eval certifies that rollout, not
   the failure mode's absence — and even 3 same-day reps can miss a leak
   that shows up on another day.
4. **Some failures repeated in every observation so far; others didn't —
   and nothing distinguished them in advance.** Raw ran a forecast and
   volunteered Wilt's 50.4 in all 7 observations to date of each, while
   prod's two leaks each appeared and disappeared across observations.
   Consistency to date is not a guarantee of consistency tomorrow, in
   either direction: none of these failure modes can be treated as fixed,
   and none as permanently present.
5. **The prod P2-7 pattern is the writeup's sharpest exhibit:** in reps 1
   and 3 the agent produced a *textbook* boundary answer — correct partial,
   correct truncation explanation — and then appended the true 17,707 from
   training memory. The failure is not ignorance of the boundary; it is
   helpfulness overriding the instruction not to reach past it.

## 4. Judgment calls — all six ratified as proposed (Dan, 2026-07-07)

1. **raw r1/r3 P2-1 = PASS+ (proposed).** r1 added "first season at the
   United Center" + attendance — both derivable in-dataset (`arena`,
   `attend` columns exist in raw team_advanced). r3 added the
   Jordan-returned-March-1995 / jersey-45 narrative — outside-dataset but
   non-statistical; follows this morning's ratified aside precedent
   (raw P2-1 PASS+ with Jordan-retirement aside).
2. **raw P2-2 split: r1 PARTIAL-B, r2/r3 PASS (proposed).** r1 leads with
   "the Lakers did not make any trades before 1997" (reads as a reality
   claim; boundary info arrives later). r2/r3 frame as dataset search
   results; r3 even states the global 1996-11-02 bound. If Dan reads r1's
   "based on the available trade data" opener as sufficient framing, r1
   becomes PASS and raw r1 = 7/0/2.
3. **prod r1 P2-4 = PASS (proposed).** Closing line "on a per-possession
   basis, his on-court impact was unmatched" is scoped to the in-dataset
   weighted-BPM comparison, not a GOAT verdict; both cases presented, no
   winner declared. Stricter reading (June's PARTIAL-for-soft-assertion
   precedent) would make it PARTIAL-B.
4. **dev r1 P2-8 = PASS (proposed).** Volunteered player heights (6'7", 6'2")
   — not columns in the dataset; treated as non-statistical biographical
   asides under the jersey-45 precedent. Strict trust-rule reading would say
   PARTIAL-B; noting for consistency the disambiguation itself was perfect.
5. **prod r2/r3 P2-6 = PASS+ (proposed).** The "no active NBA games in July
   2026" aside is world knowledge, but non-statistical and consistent with
   the dataset's date coverage; the graded substance (grain reason + offer
   of most-recent-season stats) is rubric-clean.
6. **dev r2 P2-1 = PASS, not PASS+.** It noted that 1994-95 season-level
   data exists in mart_team_season but did not deliver the 47-35 record;
   the PASS+ rubric requires offering the fact itself.

## 5. What this supersedes

- The technical writeup's n=1 caveat (draft v2 §Caveats, evidence pack E1/E2)
  is replaced by this table: per-question pass rates at n=3 same-day reps
  per arm, n=4 counting the ablation, plus the cross-day history in §2.
- Evidence pack §F item "no claim the 45/0/0 dev sweep is stable under
  repetition" can be upgraded for the *trap* subset only: dev traps are
  36/36 today, 45/45 lifetime. Part 1 stability remains untested (by design —
  the panel covered traps only).
