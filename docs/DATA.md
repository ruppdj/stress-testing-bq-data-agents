# The data (and why it isn't in this repo)

The experiment ran on six NBA tables scraped/pulled from
Basketball-Reference and the NBA Stats API. **Neither source's terms allow
redistributing the data**, so this repo ships everything *except* the data:
the loader, the expected schemas, and this guide to assembling equivalents.

Exact reproduction of pinned answers (e.g., "exactly 630 playoff series")
requires the original snapshot and is not the goal — see
[REPRODUCING.md](REPRODUCING.md) for what should and shouldn't replicate.

## Table inventory

| Table | Rows (original snapshot) | Grain | Coverage | Source |
|---|---|---|---|---|
| `player_advanced` | 21,674 | player-season (per team stint; no TOT rows) | 1984–2026 | Basketball-Reference: Advanced season pages |
| `player_pergame` | 21,674 | player-season (per team stint) | 1984–2026 | Basketball-Reference: Per Game season pages |
| `team_advanced` | 1,223 | team-season | 1984–2026 | Basketball-Reference: team season Advanced stats (incl. Arena/Attendance; teams named by era full name, no abbreviation column) |
| `team_game_logs` | 73,472 | team-game (two rows per game) | 1996–2026 (1995-96 onward) | NBA Stats API (`nba_api`): TeamGameLogs |
| `playoff_series` | 630 | series | 1984–2025 | Basketball-Reference: playoff series results |
| `trade_impact` | 1,876 | player-trade | 1997–2025 (earliest trade date 1996-11-02) | Derived: in-season trades with the acquiring team's NRtg in year −1/0/+1 and prior-season player stats (VORP/BPM/WS48) |

Tables deliberately do **not** share a common start date — the coverage gaps
(game logs from 1996, trades from 1997) are part of the trap design.

## Expected file layout

`scripts/load_to_bq.py` expects Parquet files under the data dir
(`./data` by default, or `NBA_DATA_DIR` / `--base-dir`):

```
data/
  nba-playoff-predictor/data/raw/
    bball_ref/player_stats/player_advanced_all.parquet
    bball_ref/player_stats/player_pergame_all.parquet
    bball_ref/team_stats/team_advanced_all.parquet
    nba_api/team_game_logs/team_game_logs_all.parquet
    bball_ref/playoff_series/playoff_series_all.parquet
  nba-trade-impact/data/processed/trade_dataset.parquet
```

(The nested paths mirror the upstream projects the files came from; edit
`get_tables_config()` in the loader if you prefer a flat layout.)

## Expected schemas

The dbt staging models select **every column explicitly** — they are the
authoritative schema reference:
[`solution/dbt/sports_analytics/models/staging/*.sql`](../solution/dbt/sports_analytics/models/staging/)
with descriptions in `sources.yml`.

The loader sanitizes source column names on load: lowercase; `%` → `_pct`;
`/` → `_per_`; `.` removed; leading digits spelled out (`3PAr` → `three_par`,
`2PA` → `two_pa`); duplicate columns dropped (keep first). If you scrape
Basketball-Reference's standard column headers, the sanitized names will
match what staging expects.

## Data quirks the experiment depends on (know them before you scrape)

- `team_game_logs.game_date` arrives as a STRING like `"APR 16, 2013"` —
  staging uses `PARSE_DATE`, not `CAST`.
- `team_advanced` numerics all load as STRING via pandas — staging
  `SAFE_CAST`s them.
- Two rows per game in game logs (one per team); one postponed 2013 BOS/IND
  game has a phantom null-result row.
- Player names on Basketball-Reference include diacritics (Dončić,
  Jokić, Valančiūnas). Depending on your scrape encoding you may or may not
  get mojibake — the original snapshot had 153 garbled names, which became
  the v0 arm's "ground zero" world and the name-join hazard probes.
- The trade table spells names plainly ("Luka Doncic") while the player
  tables carry diacritics — the silent-join hazard is real in the sources,
  not manufactured.
- Traded players have one row per team stint and **no TOT rows** in these
  scrapes; season totals must be computed (that's `mart_player_season_totals`).
- Historical team identity is messy: era abbreviations (KCK, SDC, WSB…),
  NBA-API dual vocabularies (GOS/GSW, PHL/PHI, SAN/SAS, UTH/UTA), and
  full-name-only team identification in `team_advanced`. The 85-row
  `team_crosswalk` seed handles all of it; expect to extend it if your
  snapshot spans different years.
