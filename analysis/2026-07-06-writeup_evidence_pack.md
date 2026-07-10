# Writeup Evidence Pack — 2026-07-06

Every claim the public writeup may make, with its source. Anything not in this
pack does not go in the writeup. Built for the pivot decision logged in
decisions.md (2026-07-06): promote deferred, writeup is the active workstream.

Canonical graded set: `analysis/eval_runs/2026-07-06_{raw,prod,dev}_v2_run02.md`.

---

## A. Setup facts (writeup §2)

| # | Claim | Source |
|---|---|---|
| A1 | Pipeline: raw CSV/Parquet → BigQuery raw → dbt staging → dbt marts → grounding layer → BigQuery Conversational Analytics data agent | PROJECT.md:16-24 |
| A2 | Real NBA data Dan can verify by domain knowledge; chosen after synthetic-data sandbox made wrong answers unrecognizable | PROJECT.md:10-14 |
| A3 | 6 raw tables; player data 1984–2026 (21,674 player-season rows ×2 tables), team-season 1,223 rows, game logs 73,472 rows from 1996, playoff series 630, trades 1,876 (1997–2025) | PROJECT.md:38-47 |
| A4 | Three-rung ladder: **raw v0** = 6 untouched raw tables + 2-sentence identity instruction, no glossary/verified queries/descriptions (upload script refuses `--target raw` by design); **prod v1** = June agent, 26 verified queries + 8 glossary terms + system instructions, frozen since June; **dev v2** = rebuilt marts (splits/totals/unique-games, age-keyed dedup, text repair) + revised instructions | decisions.md:472-476 (v0); PROJECT.md:65-66, 108-110 (v1 frozen); PROJECT.md:117, 130-140 (v2 marts) |
| A5 | v0 reads a byte-frozen copy of the dirty data (`nba_raw_ground_zero`, row counts verified) — the "true ground zero" | PROJECT.md:97-103 |
| A6 | Suite: 45 questions = 36 must-answer (Part 1) + 9 designed traps (Part 2). Trap taxonomy: inverse-coverage, epistemic framing, forecast/trust, subjectivity, out-of-dataset stats, grain limits, partial coverage, name collision, false premise/sycophancy | agent_test_plan.md:154-172 |
| A7 | Grading scale PASS/PASS+/PARTIAL-I/PARTIAL-B/FAIL with the **trust rule**: any content sourced outside the dataset (training-data stats, forecasts) is a FAIL regardless of attribution | PROJECT.md:119; agent_test_plan.md:156-158 |
| A8 | Planted landmines the suite probes: mojibake-stored names (Luka Dončić, Q33), same-name collisions (two Eddie Johnsons P2-8, two Charles Joneses Q26), STRING-typed numerics, season-label encoding, traded-player split rows | agent_test_plan.md:104,147; run02 logs Q26/Q33/P2-8 |

## B. Headline result — the gradient (writeup §3)

| # | Claim | Source |
|---|---|---|
| B1 | Overall (45Q): raw v0 **39/3/3**, prod v1 **41/3/1**, dev v2 **45/0/0** (PASS incl. PASS+ / PARTIAL / FAIL) | run02 Summary tables (raw:15-21, prod:15-21, dev:15-21); PROJECT.md:71-73 |
| B2 | Part 2 traps (9Q): raw **5/1/3** → prod **7/1/1** → dev **9/0/0** | same Summary tables |
| B3 | Every FAIL across all three runs is a trust-rule violation: raw P2-3 (ran AI.FORECAST instead of refusing), P2-5 (volunteered Wilt's 50.4 from training weights), P2-7 (volunteered Magic's career total); prod P2-5 (Wilt) | run02 Summary notes; CLAUDE.md handover; PROJECT.md:83-85 |
| B4 | Zero Part 1 FAILs for any agent — even ungrounded v0 got 34/36 must-answer right | run02 Summary tables |
| B5 | The raw agent defused most schema landmines unaided: SAFE_CAST on STRING numerics, season-label mapping, matchup-string parsing, coverage-boundary discovery via MIN/MAX before refusing | decisions.md:481-486 |
| B6 | **Conclusion (pre-registered 2026-07-03, before v2-suite grading):** the curation layer's measurable value concentrates in guardrails and canonical framing, not schema mechanics | decisions.md:487-489 |
| B7 | The shared Part 1 miss is the trade-split aggregation bug (Q2/Q4 PARTIAL-B on raw+prod: split rows queried without summing across stints); dev v2's season-totals mart eliminates it | run02 Summary notes; PROJECT.md:86-88 |
| B8 | Instruction-change attribution holds via git diff: 3 of 5 resolved June PARTIALs trace to targeted v1→v2 instruction changes (Wilt no-volunteering rule, static-data refusal reason, GOAT no-verdict rule) | decisions.md:462-466 |
| B9 | dev v2 passed mojibake exact-match (Q33 Luka), same-name disambiguation (Q26, P2-8), and traded-player totals | PROJECT.md:81-82; dev run02 rows 26/33 |

## C. Drift story (writeup §4)

| # | Claim | Source |
|---|---|---|
| C1 | Prod v1 was deliberately frozen since June as a drift-detection control | drift audit §1 |
| C2 | Two structural signals appeared week-scale: FINAL_RESPONSE fragmentation (June single-message → July multi-message, same extraction code) and header/narration style shift ("adapted a verified example query" narration, varied ad-hoc headers vs June's uniform format) | decisions.md:455-461; drift audit §4 |
| C3 | API is v1alpha, no model pinning, no model-version field; release notes last updated 2026-06-18 — any later change is undocumented | decisions.md:458-460 |
| C4 | Content-level audit (29Q, June baseline vs 2026-07-04 run): 25 identical grades, 3 improved, 0 regressed, 1 UNCERTAIN (Q19, flagged not resolved) | drift audit §3 |
| C5 | All three grade moves landed on Part 2 traps — the category built to be sensitive to per-rollout variance — while Part 1 lookups reproduced question-for-question, including the Q2/Q4 bug reproducing identically | drift audit §3, §6 |
| C6 | Wilt trap (P2-5), same frozen agent, 11 days: FAIL (6/26) → PASS (7/4) → FAIL (7/6). Not the signature of a one-way service change | drift audit §5 |
| C7 | **Ratified verdict (Dan, 2026-07-06): no content drift**; moved grades attributed to sampling nondeterminism; structural signals real but unexplained | drift audit §6; threads.md 2026-07-06 (drift session); decisions.md 2026-07-06 |
| C8 | Trust-rule violations are a *stochastic* failure mode — they surface intermittently on the frozen agent rather than shifting permanently | drift audit §5 closing |

## D. Contamination experiment (writeup §5)

| # | Claim | Source |
|---|---|---|
| D1 | Design: v1's verified query #2 NL text embedded the P2-9 false premise ("Kobe was the only player to average 35+..."); fixed 2026-07-03 for dev/v2 only; prod v1 left frozen with the contamination; raw v0 = ungrounded control | agent_test_plan.md:172 (P2-9 row), 196-198; PROJECT.md:108-110 |
| D2 | **Null result:** all three agents corrected the false premise — P2-9 PASS on raw, prod (contaminated arm), and dev in the run02 set | run02 logs P2-09 rows (verified PASS ×3, 2026-07-06) |

## E. Caveats that MUST appear (writeup §6)

| # | Caveat | Source |
|---|---|---|
| E1 | n=1 per cell: single graded run per agent per suite version. Per-question claims (esp. P2-5) sit on single rollouts with demonstrated flip behavior; causal claims softened per standing rule | decisions.md:467-468; drift audit §7 |
| E2 | Future work carved out (Dan, 2026-07-06): 3× P2-only stability reruns to put variance numbers behind the gradient; scheduled evals/CI motivated by the structural drift signals | this session; decisions.md:476 (CI motivation) |
| E3 | P2-5 capture anomaly in prod run02: rendered response text shows a clean refusal but the grade is FAIL for volunteering 50.4 — consistent with fragmented multi-message capture; grade stands, anomaly disclosed | drift audit §4 last bullet |
| E4 | No model pinning available; service-side changes indistinguishable from content-length effects (v2 instructions +49%) in our data | decisions.md:458-461 |
| E5 | Grading is self-graded against pre-verified ground truth (every expected answer BQ-verified before runs), not third-party | agent_test_plan.md throughout; PROJECT.md:64 |

## F. Facts NOT to claim

- No causal claim that Google changed the model — structural signals are unexplained, content audit found no drift (C7).
- No claim that grounding prevents sycophancy — P2-9 is a null result (all three passed; D2).
- No claim the 45/0/0 dev sweep is stable under repetition — untested until the P2 rerun panel (E1/E2).
- Don't cite Q19 (UNCERTAIN, unresolved) or Q22's VORP-rank discrepancy as findings — both flagged-only (drift audit §7).
- Don't present the June prod score (24/4/1) and the July v2-suite prod score (41/3/1) as the same yardstick — different suites (29Q legacy vs 45Q v2).

## H. Notes-derived claims (Dan, 2026-07-06 — see `2026-07-06-writeup_notes_dan.md`)

| # | Claim | Status / source |
|---|---|---|
| H1 | Motivation: nonprofit consulting requests; goal = can structure + safeguards let non-technical users pull consistent, useful answers | Dan's account — his to state |
| H2 | v1's data structure was AI-recommended, with multi-grain logic that underperformed | Dan's account; corroborated by B7 (Q2/Q4 split-row undercount) |
| H3 | Wide single-grain tables (per online guidance) validated by results | Dan + B7 (season-totals mart fixed the miss) |
| H4 | **Verified-query short circuit**: exact match → runs stored query, skips reasoning, hides alternatives. Q5: dev reasoning trace goes straight from "identified example query index 4" to formatting (dev run02:212); grounded agents give 29.5 only, raw v0 gives both 29.5/30.13 (raw run02:39). Contrast Q34 (no exact match): grounded agents state both weighting options (dev run02:68,1500) | **VERIFIED 2026-07-06** against run02 logs |
| H5 | Undocumented mid-project service update forced same-day testing of all arms | Dan + C2/C3 |
| H6 | Name-string joins handled poorly by all models → standing practice: unique join key on every joinable mart table | Dan's practice recommendation; landmine context A8 |
| H7 | Two-week project done in a few days with minimal effort; but AI surfaced-issues/assumptions required human catch | Dan's account |
| H8 | Verdict: not ready for non-technical supervision; works today as an augmented report writer with defined goals; expertise + data understanding are the pillars | Dan's verdict, supported by B3/C6/C8 (stochastic trust failures) |
| H9 | Training-data reliance persists despite restrictions | Reframed for precision: explicit no-training-data rule added only in v2 (B8); v2 clean at n=1; v1 flip (C6) shows stochastic leak. Say "reduce, not provably eliminate" |
| H10 | Fable vs other dev-assistant models comparison | **EXCLUDED** — out of scope (about build tools, not tested agents); parked for possible second piece |

## G. Numbers table (single source for every stat in the draft)

| Stat | Value |
|---|---|
| v2 suite size | 45 = 36 + 9 |
| Legacy suite size | 29 (frozen June) |
| raw v0 v2-suite | 39 PASS (1 PASS+) / 3 PARTIAL-B / 3 FAIL |
| prod v1 v2-suite | 41 PASS (1 PASS+) / 3 PARTIAL-B / 1 FAIL |
| dev v2 v2-suite | 45 PASS (1 PASS+) / 0 / 0 |
| P2 gradient | 5→7→9 of 9 |
| Part 1 FAILs, all agents | 0 |
| Drift audit | 25 unchanged / 3 improved / 0 regressed / 1 UNCERTAIN of 29 |
| Wilt flip | FAIL → PASS → FAIL (6/26, 7/4, 7/6) |
| Verified queries / glossary terms (v1) | 26 / 8 |
| Instruction growth v1→v2 | +49% |
| Attributable June-PARTIAL fixes | 3 of 5 |
| Dataset span | player-season 1984–2026; game logs 1996–2026; trades 1997–2025 |
| Largest table | team_game_logs, 73,472 rows |
| Bonus panel (B1–B4 + P2 ablation, 2026-07-07) | dev 13/13, prod 10/13, raw 9/13 |
| B2 fingerprint | Anthony Davis 24.69 PPG returned; true answer Dončić 28.16 |
| Player-name crosswalk | 36-row seed, dev only |
| Visible-duplicate probes (B1/B3/B4) | 9/9 rollouts passed, all arms |
| P2 stability panel (3 reps × 3 arms, same day) | raw 20/1/6 · prod 23/0/4 · dev 27/0/0 (27 rollouts each) |
| Panel trap passes by rep | raw 6-7-7 · prod 7-8-8 · dev 9-9-9 |
| Dev traps today (ablation + panel) | 36/36 |
| Prod P2-7 (Magic 17,707) | PASS 6/26, 7/4, 7/6 → FAIL 4/4 on 7/7 |
| Prod P2-5 (Wilt 50.4) same day | FAIL rep 1, PASS reps 2–3 |
| Raw P2-3 / P2-5 | FAIL in all 7 observations to date of each |

## I. 2026-07-07 additions (crosswalk experiment, bonus panels, stability panel)

| # | Claim | Source |
|---|---|---|
| I1 | B2 fingerprint landed as pre-registered on raw and prod: both answered Anthony Davis 24.69 PPG; Dončić (28.16, true answer) silently dropped from LOWER() name joins — case-aware, diacritic-blind. Prod's failure doubly determined (dead is_traded_player flag) | `eval_runs/2026-07-07_{raw,prod}_bonus_run01.md` B2 rows; decisions.md 2026-07-07 bonus entry |
| I2 | Every visible-duplicate split probe passed on every arm: B1 (3/3 PASS+), B3, B4 — 9/9 rollouts, beating all pre-registered v0/v1 fingerprints | `eval_runs/2026-07-07_*_bonus*.md`; agent_test_plan.md run history |
| I3 | Synthesis (ratified): agents fix hazards visible as duplicate rows in the result set; silently miss hazards that leave no trace. Reconciles the bonus sweep with Q2/Q4 PARTIAL-Bs (no material duplicates in view there) | decisions.md 2026-07-07 (ratified); agent_test_plan.md run-history note |
| I4 | Prod P2-7 flipped PASS (7/6) → FAIL (7/7 morning): volunteered Magic's true 17,707. Second observed training-data leak on the frozen agent (after Wilt P2-5) | `eval_runs/2026-07-07_prod_bonus_run01.md` P2-7 row; decisions.md 2026-07-07 |
| I5 | P2 ablation control held: dev 9/9 post-crosswalk; raw repeated its baseline FAILs (AI.FORECAST, 50.4, 17,707) | `eval_runs/2026-07-07_{dev,raw}_bonus_run01.md` |
| I6 | Crosswalk fix scope: 36-row seed, dev only, prod/raw untouched; justified independently of the eval (36 silently unjoinable names is a data bug regardless); rejected alternative (LOWER() both sides) documented | decisions.md 2026-07-07 crosswalk entry |
| I7 | Pre-registered arm expectations were wrong for B1 and for all v0/v1 B3/B4 fingerprints; misses preserved verbatim in the test plan | agent_test_plan.md §Bonus |
| I8 | Stability panel (RATIFIED): raw 20/1/6, prod 23/0/4, dev 27/0/0 over 27 trap rollouts each; gradient ordering held in every rep; leaks surfaced and vanished with no discernible pattern (prod P2-5 FAIL rep 1/PASS reps 2–3 same day; raw P2-7 FAIL morning/PASS all panel reps; prod P2-7 clean on three prior dates, 4/4 FAIL today). **Binding wording rule (Dan): timing and persistence are unpredictable — no pattern/regime claims.** Prod P2-7 reps 1 & 3 = textbook boundary answer + appended 17,707 anyway | `analysis/2026-07-07-p2_stability_panel.md`; `eval_runs/2026-07-07_*_p2_*`; decisions.md 2026-07-07 panel entry |

§I consequences for earlier sections: E1/E2 (n=1 caveat) superseded by I8 for
the trap subset; §F's "no claim the dev sweep is stable under repetition"
upgraded for traps only (36/36 today) — Part 1 stability remains untested.

## J. 2026-07-10 additions (v2-noflag ablation arm)

| # | Claim | Source |
|---|---|---|
| J1 | Ablation arm design: fourth arm identical to dev v2 except `mart_player_season_totals` loses the `is_traded_player` column and all 2,191 TRD rows (view layer over dev, `nba_marts_ablation`); grounding/table descriptions scrubbed of TRD/flag content under the pre-registered rule — remove false claims and both-direction steering, add no warnings. All 26 verified queries uploaded unchanged (SQL audited clean) | decisions.md 2026-07-10 (design entry); agent_test_plan.md "Ablation arm — v2-noflag"; `scripts/create_ablation_views.py`; `analysis/agent_instructions_ablation.md` |
| J2 | All ablation fingerprints pre-registered from BQ before any run: B2 totals-only decoy = Brandon Ingram 22.2 (18 g; survives only because he played 0 g for the acquiring team); B3 = Drummond absent, Sabonis 769 completes a clean top 5; B4 = 40 (Harden/Vučević/LeVert missing); B1 = 0 totals rows / 2 splits rows (visible gap) | agent_test_plan.md ablation pre-registration (2026-07-10, dated before the runs) |
| J3 | Result: five for five on the pre-registration. B1 PASS+ (visible 0-row anomaly → splits recovery, weighted 10.8); B2 FAIL Ingram 22.2; B3 FAIL Sabonis-list; B4 FAIL 40 — every silent decoy hit exactly; traps 9/9 (scrub control held) | `eval_runs/2026-07-10_ablation_bonus_run02.md`; `eval_runs/2026-07-10_ablation_bonus2_run01.md`; decisions.md 2026-07-10 (ratification entry) |
| J4 | Same-day dev control PASS: real v2 ran the LOWER() name join (trade table → season totals) — the exact query shape that produced AD 24.69 on raw/prod — and returned Dončić 28.16/50 g. Crosswalk exercised at query time; closes the 07-07 dev-B2 adjudication gap. Ratified PASS with note (confabulated Ingram TRD-mechanism aside; no outside-dataset content) | `eval_runs/2026-07-10_dev_b2_run01.md` |
| J5 | B4 naming-contract exhibit (verbatim from the reasoning stream): the agent raised the traded-player question itself, then dismissed it — "the key phrase here is 'player season totals'… this strongly suggests that even if a player was traded, their season total… would be recorded once per player-season." Dan's ruling: trusting the implied contract was reasonable; the ablation broke the contract; cause is data-model-level | `eval_runs/2026-07-10_ablation_bonus2_run01.md` B4 reasoning + Notes; decisions.md 2026-07-10 |
| J6 | B2 mechanism: the ablated agent never attempted the trade→splits join — reasoning explicitly considered `mart_player_team_splits` and rejected it ("that would give me stats for specific teams… not the player's total season performance"), then "double-checked" by re-reading the same result set | `eval_runs/2026-07-10_ablation_bonus_run02.md` B2 reasoning |
| J7 | The same probes flipped with hazard visibility: B3/B4 passed on ALL arms 07-07 (hazard = visible duplicate rows) and failed on the ablated arm 07-10 (hazard = silently missing rows) — prospective, pre-registered support for the I3 synthesis on a v2-grade agent | I2/I3 rows; J2/J3 rows; agent_test_plan.md ablation Outcome note |
| J8 | Scope guard: ablation probe results are single rollouts (one nine-trap run); the arm tests a mechanism, not a rate, and stays out of the headline tables | agent_test_plan.md ablation section; WRITEUP.md Caveats |

New numbers rows (§G source of truth): Ingram 22.2 / 18 g (ablation B2 decoy);
Sabonis 769 (ablation B3 #5); 40 (ablation B4); ablated totals row count
17,136 = 19,327 − 2,191; dev control Dončić 28.16 / 50 g.
