# Reproducing the experiment

This walks the full protocol on your own GCP project. Read
[DATA.md](DATA.md) first — you must assemble the source data yourself.

**Set expectations before you start.** The agent platform (BigQuery
Conversational Analytics, Gemini Data Analytics API v1alpha) offers no model
pinning and no version field. Answers vary between rollouts on identical,
frozen configurations — that variance is one of the writeup's findings. Your
data snapshot will also differ from the original (different scrape date =
different row counts). So the goal is not to match numbers like "630 playoff
series"; it is to re-run the protocol and see whether the *shape* holds: the
trap-handling gradient across curation levels, and the visible-vs-silent
hazard split.

## Prerequisites

- A GCP project with billing, and the **BigQuery** and **Gemini Data
  Analytics** (`geminidataanalytics.googleapis.com`) APIs enabled.
- `gcloud auth application-default login`, with the quota project set to
  your project (`gcloud auth application-default set-quota-project ...`).
- Python 3.11 with `pip install -r requirements.txt` (pinned versions).
- `export GCP_PROJECT=your-project-id` — every script reads it.
- dbt profile: copy [profiles.example.yml](profiles.example.yml) to
  `~/.dbt/profiles.yml` and set your project id.

## Costs (rough)

The dataset is tiny by BigQuery standards (~100k rows total): storage and
query costs are cents. The meaningful cost is Conversational Analytics API
calls — one per question, so a full 45-question run is 45 calls and the
9-trap stability panel (3 reps × 3 agents) is 81. Check current Gemini Data
Analytics pricing before large panels.

## 1. Data

Assemble the six source tables per [DATA.md](DATA.md) and place them under
`./data` (or point `NBA_DATA_DIR` / `--base-dir` elsewhere).

## 2. Load raw tables

```bash
python scripts/load_to_bq.py --base-dir ./data
```

Creates/overwrites the `nba_raw` tables (WRITE_TRUNCATE — safe to re-run).
Text repair (fixing mojibake-encoded player names at load) is on by default.

**Optional — the v0 "ground zero" arm:** the original experiment froze a
byte-identical copy of the *dirty* pre-repair data so the raw agent
permanently reads the world before any cleanup:

```bash
python scripts/load_to_bq.py --base-dir ./data --no-text-repair --dataset nba_raw_ground_zero
python scripts/load_to_bq.py --base-dir ./data          # then load the clean nba_raw
```

(If your source data is clean UTF-8 to begin with, the mojibake landmines —
and the questions that probe them — won't reproduce; note it and move on.)

## 3. Build the curation layer

```bash
cd solution/dbt/sports_analytics
dbt build                # dev target: nba_staging_dev / nba_marts_dev
dbt build --target prod  # the "live" datasets, once dev verifies
```

`dbt build` runs seeds (team + player-name crosswalks), models, and all
tests. Datasets are created automatically. Expected: all tests pass; row
counts will differ from the originals with a different snapshot.

## 4. Create the three agents

```bash
python scripts/create_agent.py --target raw
python scripts/create_agent.py --target dev
python scripts/create_agent.py --target prod
```

Record each returned agent id in `scripts/agent_config.py` (`TARGETS`). The
raw agent gets only the two-sentence system instruction hardcoded there —
that asymmetry is the experiment. Agent data sources can be re-pointed later
(e.g., raw → the frozen ground-zero dataset) with
`scripts/update_agent_datasources.py`. See
[../analysis/agent_setup_guide.md](../analysis/agent_setup_guide.md) for the
API details, including the regional-endpoint requirement (write calls
against the global endpoint return 403).

## 5. Upload grounding (curated agents only)

```bash
python scripts/extract_queries.py            # marts.yml -> analysis/verified_queries.json
python scripts/upload_nba_agent.py --target dev
python scripts/upload_nba_agent.py --target prod
```

Uploads system instructions, 26 verified queries, and glossary terms. The
script refuses `--target raw` by design — the raw arm must stay ungrounded.

## 6. Run the evaluation

```bash
python scripts/test_chat.py --target dev                 # one-question smoke test
python scripts/run_evaluation.py --target dev --suite v2 # full 45-question suite
```

Suites: `v2` (the 45-question suite), `legacy` (frozen June suite, for drift
comparison), `bonus` / `bonus2` (the split-hazard probes), `p2` (the 9 traps
only, for stability panels). Logs land in `analysis/eval_runs/` — dated,
indexed, never overwritten — with a companion raw-JSON dump including the
agents' reasoning streams.

**Protocol rules that mattered:**

- Run all agents you intend to compare **on the same day**. The platform
  drifts; same-day runs are the only way to keep comparisons clean.
- Verify every expected answer in BigQuery **before** any agent run, and
  write rubrics down first (see
  [../analysis/agent_test_plan.md](../analysis/agent_test_plan.md) for the
  grading scale and the trust rule).
- Grade traps over repeated runs, not once. Single trap results are
  rollout samples; the original stability panel was 3 reps × 3 agents
  within one 31-minute window.

## 7. Grade

Grading is manual, question by question, against your pre-verified answers.
The run logs have empty Pass/Fail columns for exactly this. The grading
scale (PASS / PASS+ / PARTIAL-I / PARTIAL-B / FAIL) and the trust rule (any
content sourced outside the dataset fails, attributed or not) are defined in
the test plan. Publish your misses too.
