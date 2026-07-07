with source as (
    select * from {{ source('raw', 'playoff_series') }}
),

crosswalk as (
    select * from {{ ref('team_crosswalk') }}
)

select
    -- identifiers
    source.season,
    source.round,

    -- teams (full names resolved to canonical abbreviations)
    cw_a.canonical_abbrev  as team_a,
    cw_b.canonical_abbrev  as team_b,

    -- series result
    source.team_a_wins,
    source.team_b_wins,
    cw_w.canonical_abbrev  as series_winner,
    source.series_length

from source
left join crosswalk as cw_a
    on source.team_a = cw_a.raw_value
left join crosswalk as cw_b
    on source.team_b = cw_b.raw_value
left join crosswalk as cw_w
    on source.series_winner = cw_w.raw_value
