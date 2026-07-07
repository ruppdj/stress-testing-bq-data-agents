-- Grouping is by (player, season, age), not just (player, season): the source data
-- has no player IDs, and 18 player-season groups are two different humans sharing a
-- name. Age (constant within a season) keeps them as separate rows instead of merging
-- them into fake TRD aggregates.
WITH player_season_counts AS (
    SELECT
        player,
        season,
        age,
        COUNT(*) AS split_count
    FROM {{ ref('mart_player_team_splits') }}
    GROUP BY player, season, age
),

single_team_players AS (
    SELECT mps.*
    FROM {{ ref('mart_player_team_splits') }} mps
    JOIN player_season_counts psc
        ON mps.player = psc.player
        AND mps.season = psc.season
        AND mps.age = psc.age
    WHERE psc.split_count = 1
),

multi_team_aggregates AS (
    SELECT
        mps.player,
        mps.season,
        'TRD' AS team_abbrev,
        -- Raw team codes of every stint, most games played first (source data has
        -- no trade chronology), e.g. "BRK / HOU". Source team column holds
        -- abbreviations, not full names, despite the staging docs.
        STRING_AGG(mps.team, ' / ' ORDER BY mps.g DESC, mps.team) AS team,
        MAX(mps.pos) AS pos,
        mps.age,
        SUM(mps.g) AS g,
        TRUE AS is_traded_player,
        MAX(mps.awards) AS awards,
        SUM(mps.gs) AS gs,
        -- Exact Minutes Per Game average
        SAFE_DIVIDE(SUM(mps.mp), SUM(mps.g)) AS mpg,
        SAFE_DIVIDE(SUM(mps.pts * mps.g), SUM(mps.g)) AS pts,
        SAFE_DIVIDE(SUM(mps.trb * mps.g), SUM(mps.g)) AS trb,
        SAFE_DIVIDE(SUM(mps.ast * mps.g), SUM(mps.g)) AS ast,
        SAFE_DIVIDE(SUM(mps.stl * mps.g), SUM(mps.g)) AS stl,
        SAFE_DIVIDE(SUM(mps.blk * mps.g), SUM(mps.g)) AS blk,
        SAFE_DIVIDE(SUM(mps.tov * mps.g), SUM(mps.g)) AS tov,
        SAFE_DIVIDE(SUM(mps.pf * mps.g), SUM(mps.g)) AS pf,
        SAFE_DIVIDE(SUM(mps.fg * mps.g), SUM(mps.g)) AS fg,
        SAFE_DIVIDE(SUM(mps.fga * mps.g), SUM(mps.g)) AS fga,
        SAFE_DIVIDE(SUM(mps.fg * mps.g), SUM(mps.fga * mps.g)) AS fg_pct,
        SAFE_DIVIDE(SUM(mps.three_p * mps.g), SUM(mps.g)) AS three_p,
        SAFE_DIVIDE(SUM(mps.three_pa * mps.g), SUM(mps.g)) AS three_pa,
        SAFE_DIVIDE(SUM(mps.three_p * mps.g), SUM(mps.three_pa * mps.g)) AS three_p_pct,
        SAFE_DIVIDE(SUM(mps.two_p * mps.g), SUM(mps.g)) AS two_p,
        SAFE_DIVIDE(SUM(mps.two_pa * mps.g), SUM(mps.g)) AS two_pa,
        SAFE_DIVIDE(SUM(mps.two_p * mps.g), SUM(mps.two_pa * mps.g)) AS two_p_pct,
        -- Exact Effective Field Goal %
        SAFE_DIVIDE(SUM(mps.fg * mps.g) + 0.5 * SUM(mps.three_p * mps.g), SUM(mps.fga * mps.g)) AS efg_pct,
        SAFE_DIVIDE(SUM(mps.ft * mps.g), SUM(mps.g)) AS ft,
        SAFE_DIVIDE(SUM(mps.fta * mps.g), SUM(mps.g)) AS fta,
        SAFE_DIVIDE(SUM(mps.ft * mps.g), SUM(mps.fta * mps.g)) AS ft_pct,
        SAFE_DIVIDE(SUM(mps.orb * mps.g), SUM(mps.g)) AS orb,
        SAFE_DIVIDE(SUM(mps.drb * mps.g), SUM(mps.g)) AS drb,
        SUM(mps.mp) AS mp,
        SAFE_DIVIDE(SUM(mps.per * mps.mp), SUM(mps.mp)) AS per,
        -- Exact True Shooting %: PTS / (2 * (FGA + 0.44 * FTA))
        SAFE_DIVIDE(SUM(mps.pts * mps.g), 2 * (SUM(mps.fga * mps.g) + 0.44 * SUM(mps.fta * mps.g))) AS ts_pct,
        -- Exact 3-Point Attempt Rate: 3PA / FGA
        SAFE_DIVIDE(SUM(mps.three_pa * mps.g), SUM(mps.fga * mps.g)) AS three_par,
        -- Exact Free Throw Rate: FTA / FGA
        SAFE_DIVIDE(SUM(mps.fta * mps.g), SUM(mps.fga * mps.g)) AS ftr,
        SAFE_DIVIDE(SUM(mps.orb_pct * mps.mp), SUM(mps.mp)) AS orb_pct,
        SAFE_DIVIDE(SUM(mps.drb_pct * mps.mp), SUM(mps.mp)) AS drb_pct,
        SAFE_DIVIDE(SUM(mps.trb_pct * mps.mp), SUM(mps.mp)) AS trb_pct,
        SAFE_DIVIDE(SUM(mps.ast_pct * mps.mp), SUM(mps.mp)) AS ast_pct,
        SAFE_DIVIDE(SUM(mps.stl_pct * mps.mp), SUM(mps.mp)) AS stl_pct,
        SAFE_DIVIDE(SUM(mps.blk_pct * mps.mp), SUM(mps.mp)) AS blk_pct,
        SAFE_DIVIDE(SUM(mps.tov_pct * mps.mp), SUM(mps.mp)) AS tov_pct,
        SAFE_DIVIDE(SUM(mps.usg_pct * mps.mp), SUM(mps.mp)) AS usg_pct,
        SUM(mps.ows) AS ows,
        SUM(mps.dws) AS dws,
        SUM(mps.ws) AS ws,
        -- Exact Win Shares per 48 minutes: WS / MP * 48
        SAFE_DIVIDE(SUM(mps.ws), SUM(mps.mp)) * 48 AS ws_per_48,
        -- BPM family: NULL-aware denominators. bpm can be NULL for a stint with very
        -- few games (below the BPM threshold); counting that stint's minutes in the
        -- denominator would bias the weighted average downward.
        SAFE_DIVIDE(SUM(mps.obpm * mps.mp), SUM(CASE WHEN mps.obpm IS NOT NULL THEN mps.mp END)) AS obpm,
        SAFE_DIVIDE(SUM(mps.dbpm * mps.mp), SUM(CASE WHEN mps.dbpm IS NOT NULL THEN mps.mp END)) AS dbpm,
        SAFE_DIVIDE(SUM(mps.bpm * mps.mp), SUM(CASE WHEN mps.bpm IS NOT NULL THEN mps.mp END)) AS bpm,
        SUM(mps.vorp) AS vorp
    FROM {{ ref('mart_player_team_splits') }} mps
    JOIN player_season_counts psc
        ON mps.player = psc.player
        AND mps.season = psc.season
        AND mps.age = psc.age
    WHERE psc.split_count > 1
    GROUP BY mps.player, mps.season, mps.age
)

SELECT * FROM single_team_players
UNION ALL
SELECT * FROM multi_team_aggregates
