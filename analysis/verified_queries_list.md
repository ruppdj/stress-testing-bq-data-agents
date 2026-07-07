# Verified Queries Reference List

Use this file to easily copy and paste verified queries into the BigQuery Conversational Analytics console.

### Query 1: What did LeBron James average in points, rebounds, and assists per game in the 2012-13 season?
**Table:** `mart_player_season_totals`

```sql
SELECT pts, trb, ast
FROM `nba-data-agent-testing.nba_marts.mart_player_season_totals`
WHERE player = 'LeBron James'
  AND season = 2013
```

---

### Query 2: Who was the only player to average 35 or more points per game in a season since 1984?
**Table:** `mart_player_season_totals`

```sql
SELECT player, season, team_abbrev, pts
FROM `nba-data-agent-testing.nba_marts.mart_player_season_totals`
WHERE pts >= 35
ORDER BY pts DESC
```

---

### Query 3: What was Stephen Curry's 3-point field goal percentage in the 2015-16 season?
**Table:** `mart_player_season_totals`

```sql
SELECT three_p_pct
FROM `nba-data-agent-testing.nba_marts.mart_player_season_totals`
WHERE player = 'Stephen Curry'
  AND season = 2016
```

---

### Query 4: Which player had the highest single-season VORP in the dataset since 1984?
**Table:** `mart_player_season_totals`

```sql
SELECT player, season, team_abbrev, vorp
FROM `nba-data-agent-testing.nba_marts.mart_player_season_totals`
ORDER BY vorp DESC
LIMIT 5
```

---

### Query 5: How many seasons did Michael Jordan appear in the dataset, and what was his average points per game across those seasons?
**Table:** `mart_player_season_totals`

```sql
SELECT
    COUNT(DISTINCT season)      AS seasons_in_dataset,
    ROUND(AVG(pts), 1)          AS career_avg_ppg
FROM `nba-data-agent-testing.nba_marts.mart_player_season_totals`
WHERE player = 'Michael Jordan'
```

---

### Query 6: Which team had the best Net Rating in the 2015-16 season?
**Table:** `mart_team_season`

```sql
SELECT team_abbrev, team, nrtg, w, l
FROM `nba-data-agent-testing.nba_marts.mart_team_season`
WHERE season = 2016
ORDER BY nrtg DESC
LIMIT 5
```

---

### Query 7: Which team had the highest SRS (Simple Rating System) in any single season in the dataset?
**Table:** `mart_team_season`

```sql
SELECT team_abbrev, team, season, srs, w, l
FROM `nba-data-agent-testing.nba_marts.mart_team_season`
ORDER BY srs DESC
LIMIT 5
```

---

### Query 8: How has league average pace changed from the 1994-95 season to the 2018-19 season?
**Table:** `mart_team_season`

```sql
SELECT season, ROUND(AVG(pace), 1) AS avg_pace
FROM `nba-data-agent-testing.nba_marts.mart_team_season`
WHERE season IN (1995, 2000, 2005, 2010, 2015, 2019)
GROUP BY season
ORDER BY season
```

---

### Query 9: What were the top 3 teams by offensive rating in the 2015-16 season?
**Table:** `mart_team_season`

```sql
SELECT team_abbrev, team, ortg, nrtg
FROM `nba-data-agent-testing.nba_marts.mart_team_season`
WHERE season = 2016
ORDER BY ortg DESC
LIMIT 3
```

---

### Query 10: What was the Net Rating of the Chicago Bulls in the 1995-96 season?
**Table:** `mart_team_season`

```sql
SELECT team_abbrev, team, nrtg, ortg, drtg, w, l, srs
FROM `nba-data-agent-testing.nba_marts.mart_team_season`
WHERE team_abbrev = 'CHI' AND season = 1996
```

---

### Query 11: How many wins did the Golden State Warriors have in the 2015-16 regular season?
**Table:** `mart_game_logs`

```sql
-- season = 2016 is the 2015-16 season (YYYY format)
SELECT COUNT(*) AS wins
FROM `nba-data-agent-testing.nba_marts.mart_game_logs`
WHERE team_abbrev = 'GSW'
  AND season = 2016
  AND wl = 'W'
```

---

### Query 12: What was the Chicago Bulls' win-loss record in the 1995-96 season?
**Table:** `mart_game_logs`

```sql
-- The 1995-96 season IS in the data (season = 1996 in YYYY format).
-- Expected: 72 wins, 10 losses.
SELECT
    SUM(CASE WHEN wl = 'W' THEN 1 ELSE 0 END) AS wins,
    SUM(CASE WHEN wl = 'L' THEN 1 ELSE 0 END) AS losses
FROM `nba-data-agent-testing.nba_marts.mart_game_logs`
WHERE team_abbrev = 'CHI' AND season = 1996
```

---

### Query 13: What was the Chicago Bulls' win-loss record in the 1994-95 season?
**Table:** `mart_game_logs`

```sql
-- Coverage check: game logs start at season = 1996 (1995-96 season).
-- The 1994-95 season is season = 1995, which is NOT in this table.
-- This query returns 0 rows; the agent must acknowledge the coverage gap.
SELECT COUNT(*) AS game_count
FROM `nba-data-agent-testing.nba_marts.mart_game_logs`
WHERE team_abbrev = 'CHI' AND season = 1995
```

---

### Query 14: How many road wins did the Miami Heat record in the 2012-13 regular season?
**Table:** `mart_game_logs`

```sql
SELECT COUNT(*) AS road_wins
FROM `nba-data-agent-testing.nba_marts.mart_game_logs`
WHERE team_abbrev = 'MIA'
  AND season = 2013
  AND wl = 'W'
  AND is_home = false
```

---

### Query 15: What was the Golden State Warriors' home record in the 2015-16 season?
**Table:** `mart_game_logs`

```sql
SELECT
    SUM(CASE WHEN wl = 'W' THEN 1 ELSE 0 END) AS home_wins,
    SUM(CASE WHEN wl = 'L' THEN 1 ELSE 0 END) AS home_losses
FROM `nba-data-agent-testing.nba_marts.mart_game_logs`
WHERE team_abbrev = 'GSW'
  AND season = 2016
  AND is_home = true
```

---

### Query 16: Which team had the most wins in any single season in the game log data?
**Table:** `mart_game_logs`

```sql
SELECT team_abbrev, season, COUNT(*) AS wins
FROM `nba-data-agent-testing.nba_marts.mart_game_logs`
WHERE wl = 'W'
GROUP BY team_abbrev, season
ORDER BY wins DESC
LIMIT 5
```

---

### Query 17: How many games did the 2016 NBA Finals last, and who won?
**Table:** `mart_playoff_series`

```sql
-- season = 2016 = 2015-16 playoffs
SELECT team_a, team_b, team_a_wins, team_b_wins, series_winner, series_length
FROM `nba-data-agent-testing.nba_marts.mart_playoff_series`
WHERE season = 2016 AND round = 'Finals'
```

---

### Query 18: How many consecutive NBA Finals appearances did the Golden State Warriors make starting in 2015?
**Table:** `mart_playoff_series`

```sql
SELECT season, series_winner,
       CASE WHEN team_a = 'GSW' THEN team_b ELSE team_a END AS opponent
FROM `nba-data-agent-testing.nba_marts.mart_playoff_series`
WHERE round = 'Finals'
  AND (team_a = 'GSW' OR team_b = 'GSW')
  AND season BETWEEN 2015 AND 2022
ORDER BY season
```

---

### Query 19: Which team did the Detroit Pistons defeat in the 2004 NBA Finals, and what was the series length?
**Table:** `mart_playoff_series`

```sql
SELECT team_a, team_b, team_a_wins, team_b_wins, series_winner, series_length
FROM `nba-data-agent-testing.nba_marts.mart_playoff_series`
WHERE season = 2004 AND round = 'Finals'
```

---

### Query 20: How many total playoff series are in the dataset?
**Table:** `mart_playoff_series`

```sql
SELECT COUNT(*) AS total_series
FROM `nba-data-agent-testing.nba_marts.mart_playoff_series`
```

---

### Query 21: Which teams reached the NBA Finals in the 2012-13 season?
**Table:** `mart_playoff_series`

```sql
SELECT team_a, team_b, series_winner, series_length
FROM `nba-data-agent-testing.nba_marts.mart_playoff_series`
WHERE season = 2013 AND round = 'Finals'
```

---

### Query 22: Which team acquired James Harden in an in-season trade, and when?
**Table:** `mart_trade_impact`

```sql
SELECT player_name, acquiring_team, trading_team, trade_date, season
FROM `nba-data-agent-testing.nba_marts.mart_trade_impact`
WHERE player_name LIKE '%Harden%'
ORDER BY trade_date DESC
LIMIT 5
```

---

### Query 23: Which team did Pau Gasol join after his February 2008 trade, and which team traded him?
**Table:** `mart_trade_impact`

```sql
SELECT player_name, acquiring_team, trading_team, trade_date
FROM `nba-data-agent-testing.nba_marts.mart_trade_impact`
WHERE player_name LIKE '%Gasol%'
  AND season = 2008
```

---

### Query 24: Which team showed the largest improvement in Net Rating from the season before a trade to the season after?
**Table:** `mart_trade_impact`

```sql
-- nrtg columns are for the ACQUIRING team; yr1 - yr_minus1 = two-year delta around the trade
SELECT player_name, acquiring_team, season,
       ROUND(nrtg_yr_minus1, 1) AS nrtg_before,
       ROUND(nrtg_yr1, 1)        AS nrtg_after,
       ROUND(nrtg_yr1 - nrtg_yr_minus1, 1) AS nrtg_delta
FROM `nba-data-agent-testing.nba_marts.mart_trade_impact`
WHERE nrtg_yr1 IS NOT NULL AND nrtg_yr_minus1 IS NOT NULL
ORDER BY nrtg_yr1 - nrtg_yr_minus1 DESC
LIMIT 10
```

---

### Query 25: How many trades are in the dataset where the acquiring team won the championship in the same season as the trade?
**Table:** `mart_trade_impact`

```sql
SELECT COUNT(*) AS championship_trades
FROM `nba-data-agent-testing.nba_marts.mart_trade_impact`
WHERE won_championship_yr0 = true
```

---

### Query 26: Which players traded in the dataset were acquired by teams that then won the championship that season?
**Table:** `mart_trade_impact`

```sql
SELECT player_name, acquiring_team, trading_team, trade_date, season
FROM `nba-data-agent-testing.nba_marts.mart_trade_impact`
WHERE won_championship_yr0 = true
ORDER BY trade_date
```

---

