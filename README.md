# Stress-Testing BigQuery Data Agents

Three versions of the same BigQuery Conversational Analytics agent — raw data
with no help, an AI-designed setup, and a human-curated one — stress-tested
against 45 questions with pre-verified answers, including 9 traps that must
be refused. Real NBA data was used so every wrong answer is recognizable.
This repo contains the full experiment: the test plan, every graded run log
(with the agents' reasoning and SQL), the dbt curation layer, and the
scripts to re-run the protocol on your own GCP project.

**Read the story: [WRITEUP.md](WRITEUP.md).**

## Headline results

45-question suite (PASS / PARTIAL / FAIL):

| Agent | Overall (45) | Traps (9) |
|---|---|---|
| v0 raw | 39 / 3 / 3 | 5 / 1 / 3 |
| v1 AI-designed | 41 / 3 / 1 | 7 / 1 / 1 |
| v2 curated | 45 / 0 / 0 | 9 / 0 / 0 |

Trap stability panel (3 same-day repetitions per agent, 27 trap rollouts each):

| Agent | Total |
|---|---|
| v0 raw | 20 / 1 / 6 |
| v1 AI-designed | 23 / 0 / 4 |
| v2 curated | **27 / 0 / 0** |

Every FAIL on either board is a trust violation — the agent confidently
sourcing content from outside the dataset. Zero must-answer questions failed
on any agent. The details, and why the failures matter more than the scores,
are in the [writeup](WRITEUP.md).

There is also a fourth, deliberately broken variant of the curated agent —
an ablation built to test *why* curation works. With its traded-player
shortcut removed (and nothing warning it), it fell into every pre-registered
silent trap while acing the visible one — see the writeup's ablation
section.

## Repo map

| Path | What |
|---|---|
| [WRITEUP.md](WRITEUP.md) | The full experiment writeup |
| [analysis/agent_test_plan.md](analysis/agent_test_plan.md) | The 45-question suite: rubrics, tiers, trust rule, pre-registered probes, run history |
| [analysis/eval_runs/](analysis/eval_runs/) | Every graded run log + raw API responses (agent answers, reasoning streams, SQL) |
| [analysis/2026-07-06-writeup_evidence_pack.md](analysis/2026-07-06-writeup_evidence_pack.md) | Claim-by-claim source map for the writeup |
| [analysis/2026-07-07-p2_stability_panel.md](analysis/2026-07-07-p2_stability_panel.md) | The stability panel: grade matrix, per-question history |
| [analysis/2026-07-06-v1_drift_audit.md](analysis/2026-07-06-v1_drift_audit.md) | Drift audit of the frozen agent (service changed mid-project) |
| [analysis/evaluation_log.md](analysis/evaluation_log.md), [_dev](analysis/evaluation_log_dev.md), [_raw](analysis/evaluation_log_raw.md) | June legacy-suite graded logs (drift baselines) |
| [analysis/agent_instructions.md](analysis/agent_instructions.md), [verified_queries.json](analysis/verified_queries.json) | The grounding package the curated agents received ([agent_instructions_ablation.md](analysis/agent_instructions_ablation.md) is the ablation arm's scrubbed variant) |
| [analysis/agent_setup_guide.md](analysis/agent_setup_guide.md) | Programmatic agent configuration via the Conversational Analytics API (incl. the regional-endpoint 403 gotcha) |
| [solution/dbt/sports_analytics/](solution/dbt/sports_analytics/) | The curation layer itself: staging + marts + seeds (team & player-name crosswalks) + tests |
| [scripts/](scripts/) | Loader, agent creation/config/upload, evaluation runner |
| [docs/REPRODUCING.md](docs/REPRODUCING.md) | End-to-end protocol to re-run on your own GCP project |
| [docs/DATA.md](docs/DATA.md) | Data sources, expected schemas, and why the data itself isn't in this repo |

## Reviewing vs. reproducing

- **Review (no GCP needed):** the full grading trail is here — questions and
  rubrics written before any run, expected answers verified in BigQuery
  first, per-question grades, the agents' verbatim responses and reasoning,
  and the raw JSON. Where pre-registered predictions were wrong, the misses
  are preserved.
- **Re-run (GCP + your own data):** see [docs/REPRODUCING.md](docs/REPRODUCING.md).
  The source data cannot be redistributed
  ([docs/DATA.md](docs/DATA.md)), and the platform is unpinned v1alpha, so
  exact numbers will not reproduce — per-rollout variance is itself one of
  the findings. What should replicate is the shape: the curation gradient
  and the visible-vs-silent hazard split.

## Quick start

```bash
pip install -r requirements.txt          # or a fresh venv/conda env, Python 3.11
export GCP_PROJECT=your-gcp-project-id
cp docs/profiles.example.yml ~/.dbt/profiles.yml   # then edit the project id

python scripts/load_to_bq.py --base-dir ./data     # after assembling data per docs/DATA.md
cd solution/dbt/sports_analytics && dbt build       # dev target by default
python scripts/create_agent.py --target dev         # then record the id in scripts/agent_config.py
python scripts/upload_nba_agent.py --target dev     # grounding: instructions + verified queries + glossary
python scripts/run_evaluation.py --target dev --suite v2
```

Granting a tester read access:
`gcloud projects add-iam-policy-binding $GCP_PROJECT --member=user:TESTER_EMAIL --role=roles/bigquery.jobUser`
(plus `bigquery.dataViewer` on the marts dataset).

## Notes for readers

- Two scripts are historical artifacts, kept for the honest record, not part
  of the reproduction path: `scripts/populate_grades.py` (a one-time grading
  stamper with a documented bug history — see its docstring) and
  `scripts/audit_grain.py` (the one-time grain audit that drove the
  season-totals mart design).
- Some analysis documents cite `decisions.md` / `PROJECT.md` line numbers —
  those are the project's private lab-notebook files. The public evidence
  (test plan, graded logs, dbt code) stands on its own.
- Grading scale and the trust rule are defined in
  [analysis/agent_test_plan.md](analysis/agent_test_plan.md); grading is the
  author's, against ground truth verified in BigQuery before any run.

## License

[MIT](LICENSE). The evaluation logs quote NBA statistics as returned by the
agents; the underlying source data (Basketball-Reference, NBA API) is not
included — see [docs/DATA.md](docs/DATA.md).
