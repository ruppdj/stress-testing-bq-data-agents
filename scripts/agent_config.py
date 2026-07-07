"""Per-target configuration for the NBA data agent scripts.

Targets mirror the dbt convention: `dev` is the default and points at the
nba_marts_dev dataset; `prod` is the live agent (what testers see) and must
be requested explicitly with --target prod.

`raw` is the v0 baseline experiment: a bare-bones agent reading the 6
nba_raw tables directly, with only the minimal system_instruction below —
no glossary, no verified queries, no curated descriptions.
upload_nba_agent.py refuses this target to keep it that way.

Set GCP_PROJECT to your project id before running anything. LOCATION and
API_BASE assume US multi-region data; see analysis/agent_setup_guide.md for
the regional-endpoint requirement if your data lives elsewhere.
"""

import os
import re

PROJECT_ID = os.environ.get("GCP_PROJECT")  # checked in resolve()
LOCATION = "us"
API_BASE = "https://geminidataanalytics.us.rep.googleapis.com/v1alpha"

MART_TABLES = [
    "mart_player_season_totals",
    "mart_player_team_splits",
    "mart_unique_games",
    "mart_team_season",
    "mart_game_logs",
    "mart_playoff_series",
    "mart_trade_impact",
    "mart_team_crosswalk",
]

RAW_TABLES = [
    "player_advanced",
    "player_pergame",
    "team_advanced",
    "team_game_logs",
    "playoff_series",
    "trade_impact",
]

RAW_SYSTEM_INSTRUCTION = (
    "You are an NBA data agent. You answer questions about NBA basketball "
    "using the BigQuery tables available to you, which contain player season "
    "statistics, team season statistics, team game logs, playoff series "
    "results, and player trade records. Answer questions by querying the data."
)

TARGETS = {
    "dev": {
        # Created via scripts/create_agent.py 2026-07-02; update here if recreated.
        "agent_id": "nba-dev-agent-v2",
        "dataset": "nba_marts_dev",
        "eval_log": "evaluation_log_dev.md",
        "tables": MART_TABLES,
    },
    "prod": {
        # Set to your prod agent's id after creating it (via create_agent.py
        # or BigQuery Studio). resolve() below gives a clear error until then.
        "agent_id": None,
        "dataset": "nba_marts",
        "eval_log": "evaluation_log.md",
        "tables": MART_TABLES,
    },
    "raw": {
        # Created via scripts/create_agent.py 2026-07-03 (v0 baseline experiment).
        # Repointed 2026-07-03 from nba_raw to the frozen ground-zero copy so the
        # dirty pre-cleanup world stays testable after nba_raw was reloaded with
        # text repair (decisions.md 2026-07-03, run-gate supersede entry).
        "agent_id": "nba-raw-agent-v0",
        "dataset": "nba_raw_ground_zero",
        "eval_log": "evaluation_log_raw.md",
        "tables": RAW_TABLES,
        "system_instruction": RAW_SYSTEM_INSTRUCTION,
    },
}


def add_target_arg(parser):
    parser.add_argument(
        "--target",
        choices=sorted(TARGETS),
        default="dev",
        help="Which agent/dataset to use (default: dev; prod is the live agent)",
    )


def resolve(target):
    """Return the config dict for a target, with derived fields filled in."""
    if not PROJECT_ID:
        raise SystemExit(
            "Set GCP_PROJECT to the GCP project id that holds your BigQuery "
            "datasets and data agents (export GCP_PROJECT=your-project-id)."
        )
    cfg = dict(TARGETS[target])
    if cfg["agent_id"] is None:
        raise SystemExit(
            f"No agent_id configured for target '{target}'. "
            "Create the agent with scripts/create_agent.py, then record its ID "
            "in scripts/agent_config.py."
        )
    cfg["target"] = target
    cfg["agent_name"] = (
        f"projects/{PROJECT_ID}/locations/{LOCATION}/dataAgents/{cfg['agent_id']}"
    )
    cfg["chat_url"] = f"{API_BASE}/projects/{PROJECT_ID}/locations/{LOCATION}:chat"
    return cfg


def rewrite_dataset(text, cfg):
    """Repoint project/dataset references in agent-visible text at the target.

    Source files (agent_instructions.md, verified_queries.json, marts.yml
    verified queries) are canonical on the original experiment's project id
    and prod dataset name — they are historical artifacts and stay verbatim
    in the repo. Both get rewritten here, only at upload time: the project
    id to your GCP_PROJECT, and (for non-prod targets) `nba_marts` to the
    target dataset. \\b keeps nba_marts_dev itself from matching, so the
    rewrite is idempotent.
    """
    text = text.replace("nba-data-agent-testing", PROJECT_ID)
    if cfg["dataset"] == "nba_marts":
        return text
    return re.sub(r"\bnba_marts\b", cfg["dataset"], text)
