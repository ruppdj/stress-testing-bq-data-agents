SELECT
    -- Identity columns
    adv.player,
    adv.season,
    adv.team_abbrev,
    adv.team,
    adv.pos,
    -- Source age is FLOAT64 (pandas load); INT64 here so it can key windows and joins
    CAST(adv.age AS INT64) AS age,
    adv.g,
    -- True when the player has more than one team stint this season.
    -- Partitioned by age as well: same-name players in the same season are
    -- different humans (source data has no player IDs; age disambiguates).
    COUNT(*) OVER (PARTITION BY adv.player, adv.season, CAST(adv.age AS INT64)) > 1 AS is_traded_player,
    adv.awards,

    -- Per-game box score stats (from stg_player_pergame)
    pg.gs,
    pg.mp                 AS mpg,
    pg.pts,
    pg.trb,
    pg.ast,
    pg.stl,
    pg.blk,
    pg.tov,
    pg.pf,
    pg.fg,
    pg.fga,
    pg.fg_pct,
    pg.three_p,
    pg.three_pa,
    pg.three_p_pct,
    pg.two_p,
    pg.two_pa,
    pg.two_p_pct,
    pg.efg_pct,
    pg.ft,
    pg.fta,
    pg.ft_pct,
    pg.orb,
    pg.drb,

    -- Advanced / efficiency stats (from stg_player_advanced)
    adv.mp,
    adv.per,
    adv.ts_pct,
    adv.three_par,
    adv.ftr,
    adv.orb_pct,
    adv.drb_pct,
    adv.trb_pct,
    adv.ast_pct,
    adv.stl_pct,
    adv.blk_pct,
    adv.tov_pct,
    adv.usg_pct,
    adv.ows,
    adv.dws,
    adv.ws,
    adv.ws_per_48,
    adv.obpm,
    adv.dbpm,
    adv.bpm,
    adv.vorp

FROM {{ ref('stg_player_advanced') }} adv
LEFT JOIN {{ ref('stg_player_pergame') }} pg
    ON  adv.player      = pg.player
    AND adv.season      = pg.season
    AND adv.team_abbrev = pg.team_abbrev
    -- age disambiguates same-name players (e.g., both Charles Joneses on WAS in 1989,
    -- which would otherwise fan out 2x2 and mix stats across the two people)
    AND adv.age         = pg.age
