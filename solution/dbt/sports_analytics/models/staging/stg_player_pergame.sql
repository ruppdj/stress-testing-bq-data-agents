with source as (
    select * from {{ source('raw', 'player_pergame') }}
),

crosswalk as (
    select * from {{ ref('team_crosswalk') }}
)

select
    -- identifiers
    source.player,
    source.season,
    -- raw tables are split-only: no TOT/aggregate rows exist (confirmed 2026-06-26);
    -- traded-player season totals are built downstream in mart_player_season_totals
    crosswalk.canonical_abbrev as team_abbrev,
    source.team,
    source.pos,
    source.age,

    -- playing time
    source.g,
    source.gs,
    source.mp,

    -- shooting
    source.fg,
    source.fga,
    source.fg_pct,
    source.three_p,
    source.three_pa,
    source.three_p_pct,
    source.two_p,
    source.two_pa,
    source.two_p_pct,
    source.efg_pct,
    source.ft,
    source.fta,
    source.ft_pct,

    -- rebounds
    source.orb,
    source.drb,
    source.trb,

    -- playmaking / defense
    source.ast,
    source.stl,
    source.blk,
    source.tov,
    source.pf,

    -- scoring
    source.pts

from source
left join crosswalk
    on source.team_abbrev = crosswalk.raw_value
