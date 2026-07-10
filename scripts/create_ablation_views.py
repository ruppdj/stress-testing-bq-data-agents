"""Create the nba_marts_ablation dataset: views over nba_marts_dev with the
traded-player shortcut removed.

Ablation arm (agent_test_plan.md, pre-registered 2026-07-10):
mart_player_season_totals loses the is_traded_player column and all TRD
season-total rows (2,191 rows); every other mart passes through unchanged.
Table and column descriptions are copied from the dev marts with TRD/flag
language scrubbed per the pre-registered rule — remove claims the ablation
makes false and totals-vs-splits usage steering in both directions; add no
warning language (the hazard stays discoverable, not documented).

Idempotent: get-or-create dataset, CREATE OR REPLACE for views.

Run:  conda run -n base python scripts/create_ablation_views.py
      conda run -n base python scripts/create_ablation_views.py --verify-only
"""

import argparse
import sys

from google.cloud import bigquery

import agent_config

PROJECT_ID = agent_config.PROJECT_ID
SOURCE_DATASET = "nba_marts_dev"
ABLATION_DATASET = "nba_marts_ablation"

MARTS = [
    "mart_game_logs",
    "mart_player_season_totals",
    "mart_player_team_splits",
    "mart_playoff_series",
    "mart_team_crosswalk",
    "mart_team_season",
    "mart_trade_impact",
    "mart_unique_games",
]

# The one non-pass-through view: flag column and TRD season-total rows removed.
TOTALS_SQL = f"""
SELECT * EXCEPT (is_traded_player)
FROM `{PROJECT_ID}.{SOURCE_DATASET}.mart_player_season_totals`
WHERE team_abbrev != 'TRD'
"""

# Scrubbed descriptions. Anything not listed here is copied verbatim from the
# dev mart. Removed vs. dev: the one-row-per-player-per-season claim (false
# after the ablation — mid-season traded players have no row at all), the
# "safe for rankings / no deduplication" claim, all TRD row references, and
# the totals-vs-splits usage steering in both directions. Kept: unique-key
# facts, coverage bounds, and cross-domain routing (team/game tables), which
# are orthogonal to the hazard.
TABLE_DESC_OVERRIDES = {
    "mart_player_season_totals": (
        "Player season totals (unique key: player + season + age — the source "
        "data has no player IDs, so a handful of same-name players in the same "
        "season appear as separate rows distinguished by age). "
        "Coverage: 1984–2026. Season is encoded as YYYY (season = 2013 means "
        "the 2012-13 season).\n\n"
        "Do NOT use this model for team-level questions (use mart_team_season), "
        "game-by-game results (use mart_game_logs), or player data before 1984."
    ),
    "mart_player_team_splits": (
        "Player stats broken out by each team a player appeared for in a "
        "season. Coverage: 1984–2026. Season is encoded as YYYY."
    ),
}

COLUMN_DESC_OVERRIDES = {
    ("mart_player_season_totals", "team_abbrev"):
        "Canonical 3-letter team abbreviation.",
    ("mart_player_season_totals", "team"): (
        "Raw team code from the source data (may be a historical "
        "abbreviation, e.g. KCK). Prefer team_abbrev, which is canonical."
    ),
    ("mart_player_season_totals", "g"):
        "Games played.",
    ("mart_player_team_splits", "team_abbrev"): (
        "Canonical 3-letter team abbreviation. Each row represents one "
        "specific team stint."
    ),
    ("mart_player_team_splits", "is_traded_player"): (
        "True when the player appeared for more than one team that season — "
        "this row is a partial-season team split, not the player's full "
        "season. False for single-team seasons."
    ),
}


def ensure_dataset(client):
    src = client.get_dataset(f"{PROJECT_ID}.{SOURCE_DATASET}")
    ds_ref = bigquery.Dataset(f"{PROJECT_ID}.{ABLATION_DATASET}")
    ds_ref.location = src.location
    ds_ref.description = (
        "Ablation arm: v2 marts without the traded-player shortcut. "
        "Views over nba_marts_dev — see analysis/agent_test_plan.md "
        "(pre-registered 2026-07-10)."
    )
    client.create_dataset(ds_ref, exists_ok=True)
    print(f"dataset {ABLATION_DATASET} ready (location {src.location})")


def create_views(client):
    for mart in MARTS:
        if mart == "mart_player_season_totals":
            view_sql = TOTALS_SQL.strip()
        else:
            view_sql = f"SELECT * FROM `{PROJECT_ID}.{SOURCE_DATASET}.{mart}`"
        client.query(
            f"CREATE OR REPLACE VIEW `{PROJECT_ID}.{ABLATION_DATASET}.{mart}` "
            f"AS {view_sql}"
        ).result()
        apply_descriptions(client, mart)
        print(f"view {mart} created + descriptions applied")


def apply_descriptions(client, mart):
    source = client.get_table(f"{PROJECT_ID}.{SOURCE_DATASET}.{mart}")
    view = client.get_table(f"{PROJECT_ID}.{ABLATION_DATASET}.{mart}")
    src_col_desc = {f.name: f.description for f in source.schema}

    view.description = TABLE_DESC_OVERRIDES.get(mart, source.description)
    new_schema = []
    for field in view.schema:
        desc = COLUMN_DESC_OVERRIDES.get(
            (mart, field.name), src_col_desc.get(field.name)
        )
        new_schema.append(
            bigquery.SchemaField(
                field.name, field.field_type, mode=field.mode, description=desc
            )
        )
    view.schema = new_schema
    client.update_table(view, ["description", "schema"])


def verify(client):
    """Pre-registered verification checks (agent_test_plan.md 2026-07-10)."""
    failures = []

    def check(name, ok, detail=""):
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
        if not ok:
            failures.append(name)

    print("verification:")

    # 1. Schema: flag gone from totals, still present in splits (pass-through).
    totals = client.get_table(f"{PROJECT_ID}.{ABLATION_DATASET}.mart_player_season_totals")
    splits = client.get_table(f"{PROJECT_ID}.{ABLATION_DATASET}.mart_player_team_splits")
    totals_cols = {f.name for f in totals.schema}
    check("totals view has no is_traded_player column",
          "is_traded_player" not in totals_cols)
    check("splits view keeps is_traded_player (ratified pass-through)",
          "is_traded_player" in {f.name for f in splits.schema})

    # 2. Row counts: totals = dev minus exactly the 2,191 TRD rows; all other
    #    views match dev exactly.
    rows = list(client.query(f"""
        SELECT
          (SELECT COUNT(*) FROM `{PROJECT_ID}.{SOURCE_DATASET}.mart_player_season_totals`) AS dev_totals,
          (SELECT COUNT(*) FROM `{PROJECT_ID}.{SOURCE_DATASET}.mart_player_season_totals` WHERE team_abbrev = 'TRD') AS dev_trd,
          (SELECT COUNT(*) FROM `{PROJECT_ID}.{ABLATION_DATASET}.mart_player_season_totals`) AS abl_totals
    """).result())[0]
    check("totals rows = dev minus TRD rows",
          rows.abl_totals == rows.dev_totals - rows.dev_trd and rows.dev_trd == 2191,
          f"dev {rows.dev_totals} - TRD {rows.dev_trd} = {rows.abl_totals}")
    for mart in MARTS:
        if mart == "mart_player_season_totals":
            continue
        r = list(client.query(f"""
            SELECT
              (SELECT COUNT(*) FROM `{PROJECT_ID}.{SOURCE_DATASET}.{mart}`) AS dev_n,
              (SELECT COUNT(*) FROM `{PROJECT_ID}.{ABLATION_DATASET}.{mart}`) AS abl_n
        """).result())[0]
        check(f"{mart} row count matches dev", r.dev_n == r.abl_n,
              f"{r.abl_n} rows")

    # 3. Pre-registered spot checks: Harden 2021 (0 totals rows / 2 splits
    #    rows) and the forced B2 join returning Luka 28.16 over 50 g.
    r = list(client.query(f"""
        SELECT
          (SELECT COUNT(*) FROM `{PROJECT_ID}.{ABLATION_DATASET}.mart_player_season_totals`
           WHERE player = 'James Harden' AND season = 2021) AS harden_totals,
          (SELECT COUNT(*) FROM `{PROJECT_ID}.{ABLATION_DATASET}.mart_player_team_splits`
           WHERE player = 'James Harden' AND season = 2021) AS harden_splits
    """).result())[0]
    check("Harden 2021: 0 totals rows / 2 splits rows",
          r.harden_totals == 0 and r.harden_splits == 2,
          f"totals {r.harden_totals}, splits {r.harden_splits}")

    top = list(client.query(f"""
        SELECT s.player, ROUND(SUM(s.pts * s.g) / SUM(s.g), 2) AS ppg,
               CAST(SUM(s.g) AS INT64) AS g
        FROM `{PROJECT_ID}.{ABLATION_DATASET}.mart_player_team_splits` s
        JOIN (SELECT DISTINCT player_name
              FROM `{PROJECT_ID}.{ABLATION_DATASET}.mart_trade_impact`
              WHERE season = 2025) ti
          ON LOWER(s.player) = LOWER(ti.player_name)
        WHERE s.season = 2025
        GROUP BY s.player ORDER BY ppg DESC LIMIT 1
    """).result())[0]
    check("forced B2 join returns Luka Dončić 28.16 / 50 g",
          top.player == "Luka Dončić" and abs(top.ppg - 28.16) < 0.01 and top.g == 50,
          f"{top.player} {top.ppg} / {top.g} g")

    # 4. No TRD/flag language survives in any ablation description.
    dirty = []
    for mart in MARTS:
        t = client.get_table(f"{PROJECT_ID}.{ABLATION_DATASET}.{mart}")
        texts = [("table", t.description or "")] + [
            (f.name, f.description or "") for f in t.schema
        ]
        for where, text in texts:
            if "TRD" in text or "is_traded_player" in text:
                dirty.append(f"{mart}.{where}")
    check("no TRD/is_traded_player text in any view description",
          not dirty, ", ".join(dirty) if dirty else "all clean")

    if failures:
        print(f"\n{len(failures)} verification check(s) FAILED")
        return 1
    print("\nall verification checks passed")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Create/verify the nba_marts_ablation view layer.")
    parser.add_argument("--verify-only", action="store_true",
                        help="Run verification checks without (re)creating anything.")
    args = parser.parse_args()

    if not PROJECT_ID:
        raise SystemExit(
            "Set GCP_PROJECT to the GCP project id that holds your BigQuery "
            "datasets (export GCP_PROJECT=your-project-id)."
        )
    client = bigquery.Client(project=PROJECT_ID)
    if not args.verify_only:
        ensure_dataset(client)
        create_views(client)
    sys.exit(verify(client))


if __name__ == "__main__":
    main()
