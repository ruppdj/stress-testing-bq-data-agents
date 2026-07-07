"""HISTORICAL — one-time data-grain audit (2026-06-28), kept for the record.

Confirmed the raw player tables contain zero TOT rows (traded players appear
only as per-team split rows), which drove the season-totals mart design. The
queries reference the original project id inline; if you re-run it, set
GCP_PROJECT and the SQL will be rewritten to your project.
"""

import os
from google.cloud import bigquery
import pandas as pd

PROJECT = os.environ.get("GCP_PROJECT", "nba-data-agent-testing")

def _repoint(query: str) -> str:
    """Rewrite the original project id in the inline SQL to PROJECT."""
    return query.replace("nba-data-agent-testing", PROJECT)

def run_query(client, title, query):
    print(f"\n=== {title} ===")
    df = client.query(_repoint(query)).to_dataframe()
    print(df.to_string(index=False))

def main():
    client = bigquery.Client(project=PROJECT)
    
    # 1. How many rows per player-season? Flag multi-row seasons in player_advanced
    q1 = """
    SELECT player, season, COUNT(*) AS row_count, ARRAY_AGG(team_abbrev ORDER BY team_abbrev) AS teams
    FROM `nba-data-agent-testing.nba_raw.player_advanced`
    GROUP BY player, season
    HAVING COUNT(*) > 1
    ORDER BY season DESC, player
    LIMIT 10
    """
    run_query(client, "Multi-row seasons in player_advanced", q1)
    
    # 2. How many rows per player-season in player_pergame?
    q2 = """
    SELECT player, season, COUNT(*) AS row_count, ARRAY_AGG(team_abbrev ORDER BY team_abbrev) AS teams
    FROM `nba-data-agent-testing.nba_raw.player_pergame`
    GROUP BY player, season
    HAVING COUNT(*) > 1
    ORDER BY season DESC, player
    LIMIT 10
    """
    run_query(client, "Multi-row seasons in player_pergame", q2)
    
    # 3. Spot check: James Harden in 2021
    q3 = """
    SELECT player, season, team_abbrev, g, mp, pts, ast, trb
    FROM `nba-data-agent-testing.nba_raw.player_pergame`
    WHERE player LIKE '%Harden%' AND season = 2021
    ORDER BY season, team_abbrev
    """
    run_query(client, "James Harden 2020-21 (season = 2021) in player_pergame", q3)

if __name__ == "__main__":
    main()
