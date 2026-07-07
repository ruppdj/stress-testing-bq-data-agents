with source as (
    select * from {{ source('raw', 'player_advanced') }}
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
    source.mp,

    -- efficiency / impact
    source.per,
    source.ts_pct,
    source.three_par,
    source.ftr,
    source.orb_pct,
    source.drb_pct,
    source.trb_pct,
    source.ast_pct,
    source.stl_pct,
    source.blk_pct,
    source.tov_pct,
    source.usg_pct,

    -- wins above replacement
    source.ows,
    source.dws,
    source.ws,
    source.ws_per_48,

    -- box plus/minus
    source.obpm,
    source.dbpm,
    source.bpm,

    -- value over replacement player
    source.vorp,

    -- awards / honors
    source.awards

from source
left join crosswalk
    on source.team_abbrev = crosswalk.raw_value
