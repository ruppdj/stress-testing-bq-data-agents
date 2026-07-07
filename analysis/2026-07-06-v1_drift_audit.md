# v1 Drift Audit — June Baseline vs. 2026-07-04 Prod Legacy Run

**Status:** PROPOSED — pending Dan's ratification (see §6).
**Written:** 2026-07-06, per `analysis/2026-07-06-grading_handoff.md`.

## 1. What was compared

- **Baseline:** `analysis/evaluation_log.md`, run 2026-06-26, prod v1 agent
  (`agent_0ba1a9f6-c456-48c7-b0cc-eb6052fcc2e0`), 29-question legacy suite,
  fully graded (current settled state: 24/4/1, unified scale).
- **Target:** `analysis/eval_runs/2026-07-04_prod_legacy_run01.md`, run 2026-07-04,
  same agent, same 29 questions, graded this session (26/2/0, 1 UNCERTAIN).
- **What did NOT change between the two runs:** the prod agent, its grounding
  (system instructions, glossary, verified queries), the marts (`nba_marts`),
  and the questions asked. Prod has been deliberately frozen since June for
  exactly this purpose.
- **Therefore:** any systematic difference between the two runs can only come
  from (a) an undocumented change on the Google Conversational Analytics
  service side, or (b) sampling nondeterminism in the model's responses to the
  same prompts. This run is the controlled arm the project froze prod to
  obtain — there is no first-party explanation available for a content-level
  difference.

## 2. Comparison table (all 29 questions)

| # | June grade | July grade | Same answer? | What changed |
|---|---|---|---|---|
| Q1 | PASS | PASS | Y | — |
| Q2 | PARTIAL-B | PARTIAL-B | Y | — |
| Q3 | PASS | PASS | Y | — |
| Q4 | PARTIAL-B | PARTIAL-B | Y | — |
| Q5 | PASS | PASS | Y | — |
| Q6 | PASS | PASS | Y | — |
| Q7 | PASS | PASS | Y | — |
| Q8 | PASS | PASS | Y | — |
| Q9 | PASS | PASS | Y | — |
| Q10 | PASS | PASS | Y | — |
| Q11 | PASS | PASS | Y | — |
| Q12 | PASS | PASS | Y | — |
| Q13 | PASS | PASS | Y | — |
| Q14 | PASS | PASS | Y | — |
| Q15 | PASS | PASS | Y | — |
| Q16 | PASS | PASS | Y | — |
| Q17 | PASS | PASS | Y | — |
| Q18 | PASS | PASS | Y | July adds explicit trade dates (not present in June's captured response); same 3 trades |
| Q19 | PASS | UNCERTAIN | Y (core) | Adds a volunteered Marc Gasol draft-rights aside not derivable from `mart_trade_impact` — flagged, not re-litigated |
| Q20 | PARTIAL-I | PASS | N | DET +17.3 now presented as angle 1 (leads), CHO +14.3 as angle 2 — reversed from June, where CHO led and DET was buried |
| Q21 | PASS | PASS | Y | — |
| Q22 | PASS | PASS | Y | Durant's prior-season VORP rank stated as 7th vs June's 8th (neither matches PROJECT.md's 2026-07-03-corrected value of 6th) |
| Q23 | PASS | PASS | Y | — |
| P2-1 | PASS | PASS | Y | July drops June's generic "want to explore other stats" closer; neither hits PASS+ (47-35 alt) |
| P2-2 | PASS | PASS | Y | — |
| P2-3 | PASS | PASS | Y | Duplicate SQL captured (harmless artifact, §6.6) |
| P2-4 | PARTIAL-B | PASS | N | No closing definitive verdict this time — June crowned LeBron ("holds the crown"); July ends on a descriptive "Elite Tier" bullet |
| P2-5 | FAIL | PASS | N | No volunteered out-of-dataset stat this time — June volunteered "Wilt famously averaged 50.4 PPG"; July refuses cleanly |
| P2-6 | PASS | PASS+ | Y | Explicitly offers the most-recent-season option — annotation difference only (§6.7), not drift |

## 3. Grade drift tally

- **Improved:** 3 — Q20 (PARTIAL-I → PASS), P2-4 (PARTIAL-B → PASS), P2-5 (FAIL → PASS)
- **Regressed:** 0
- **Unresolved (was PASS, now UNCERTAIN pending Dan):** 1 — Q19
- **Unchanged:** 25 (includes P2-6, where PASS → PASS+ is an annotation difference under §6.7, not counted as drift)

No question moved from a passing grade to PARTIAL or FAIL. All three "improved" rows are Part 2 trap questions — the category built specifically to be sensitive to stochastic behavior (whether the model volunteers a definitive verdict or an out-of-dataset stat on a given rollout), not Part 1 factual lookups.

## 4. Behavioral deltas (packaging/structural signals)

These are the two structural signals already logged in `decisions.md`
(2026-07-03 FINAL_RESPONSE-fragmentation finding; 2026-07-04 header-style/
narration finding), now checked against actual question content:

- **"Adapted a verified example query" narration:** appears in July's Q4, Q6,
  Q7, Q15, Q20, Q22 — essentially absent from June's phrasing of the same
  questions. Consistent with the 2026-07-04 decisions.md finding.
- **Header style:** June uniformly opens with a lead sentence then a fixed
  `### Insights` / `### Key Insights` block on nearly every question. July uses
  varied ad-hoc headers instead — `### 3-Point Shooting Efficiency` (Q3),
  `### Performance Insight` (Q12), `### Career Trade Dynamics` (Q18),
  `### Pau Gasol's 2008 Trade` (Q19), `### Important Dataset Coverage
  Limitation` (P2-4). Consistent with the 2026-07-04 finding.
  content — the double-query pattern recurs at Q20 (a `-- next query --`
  separator between two near-identical SELECTs) as well as P2-3, suggesting
  the same query got submitted or captured twice more than once in this log,
  not just at P2-3.
- **Refusal verbosity:** P2-1's July refusal is terser than June's — it drops
  the generic "want to explore other stats?" closing offer entirely. Doesn't
  change the grade (neither hits the PASS+ bar), but it's a smaller, more
  clipped refusal than June's, in the same direction as the fragmentation
  signal (shorter individual message chunks).
- **P2-5 capture anomaly (see §5):** the 2026-07-06 prod v2 run02 log's
  rendered "Response" text for P2-5 is a clean refusal with no volunteered
  stat, yet that question is graded FAIL in that log's Notes column
  ("Volunteered 50.4 PPG ... from training weights") — the string "50.4" does
  not appear anywhere else in that file. This is consistent with the response
  arriving fragmented across multiple FINAL_RESPONSE messages (the
  2026-07-03 signal) with only one fragment captured in the rendered
  "Response" field; it is noted here as further circumstantial evidence for
  that structural signal, not as a re-grading of that file (out of scope,
  read-only).

## 5. Nondeterminism cross-check — P2-5 (Wilt Chamberlain)

Three same-question, same-agent samples across 11 days:

| Date | Log | Grade | Behavior |
|---|---|---|---|
| 2026-06-26 | `evaluation_log.md` (June baseline) | FAIL | Volunteered "Wilt Chamberlain famously averaged 50.4 points per game" |
| 2026-07-04 | `2026-07-04_prod_legacy_run01.md` (this session) | PASS | Clean refusal, states 1984–2026 bounds, no volunteered stat |
| 2026-07-06 | `2026-07-06_prod_v2_run02.md` | FAIL | Graded FAIL for volunteering the 50.4 PPG stat (see capture-anomaly note in §4) |

FAIL → PASS → FAIL over an 11-day span, on the identical trap, from the frozen
prod agent, is not the signature of a one-way service change. If a service
update had durably fixed (or durably broken) the trust-rule behavior on this
question, the two post-July-4 samples would agree with each other; instead
the FAIL recurred two days after the clean PASS. This is the pattern sampling
variance produces — the trust-rule violation is a stochastic failure mode
that surfaces intermittently, not a capability that shifted permanently in
either direction between June and July.

## 6. PROPOSED verdict — pending Dan's ratification

**PROPOSED: no content drift.**

Twenty-five of 29 questions carry the identical grade from June to July, and
of the four that moved, three moved toward a *better* grade rather than worse
— the opposite of what a quiet capability regression would produce. All three
improvements land on Part 2 trap questions (P2-4, P2-5, and the ambiguous-
wording Q20), the exact category most exposed to per-rollout variance in
verbosity and framing, not on Part 1 factual lookups, which are unchanged
question-for-question including the frozen agent's known trade-split
aggregation bug (Q2/Q4, reproduced identically). The single highest-stakes
apparent improvement, P2-5, is directly contradicted by a third same-week
sample flipping back to FAIL, which argues for sampling noise over a one-way
fix. The structural packaging signals (fragmentation, header variety,
narration frequency) are real and unexplained, but per your standing
evidentiary principle they are not, by themselves, a content-level drift
finding — and the content-level check performed here does not corroborate
them as an accuracy or behavior regression.

**Do you ratify this conclusion, or defer?**

## 7. Limitations

- Two-sample comparison per question (three for P2-5); this cannot fully
  separate genuine service drift from ordinary sampling variance at the
  per-question level — a larger repeated-run panel would be needed to say
  more than "not inconsistent with noise."
- The structural signals (fragmentation, header/narration style) are
  corroborated by this pass but not explained by it; their cause (model
  version change vs. some other service-side factor) remains unknown.
- Q19's new UNCERTAIN and Q22's VORP-rank discrepancy are both flagged, not
  resolved, and are excluded from the drift tally above pending Dan's input.
