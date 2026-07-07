with source as (
    select * from {{ source('raw', 'team_advanced') }}
),

crosswalk as (
    select * from {{ ref('team_crosswalk') }}
)

select
    -- identifiers
    source.team,
    crosswalk.canonical_abbrev                      as team_abbrev,
    source.season,
    safe_cast(source.age      as float64)           as age,

    -- record (BQ loaded these as STRING; cast to correct types)
    safe_cast(source.w        as int64)             as w,
    safe_cast(source.l        as int64)             as l,
    safe_cast(source.pw       as float64)           as pw,
    safe_cast(source.pl       as float64)           as pl,

    -- pace / efficiency ratings
    safe_cast(source.pace     as float64)           as pace,
    safe_cast(source.ortg     as float64)           as ortg,
    safe_cast(source.drtg     as float64)           as drtg,
    safe_cast(source.nrtg     as float64)           as nrtg,

    -- strength of schedule / simple rating
    safe_cast(source.sos      as float64)           as sos,
    safe_cast(source.srs      as float64)           as srs,
    safe_cast(source.mov      as float64)           as mov,

    -- four factors — offense
    safe_cast(source.efg_pct      as float64)       as efg_pct,
    safe_cast(source.tov_pct      as float64)       as tov_pct,
    safe_cast(source.orb_pct      as float64)       as orb_pct,
    safe_cast(source.ft_per_fga   as float64)       as ft_per_fga,
    safe_cast(source.ts_pct       as float64)       as ts_pct,
    safe_cast(source.three_par    as float64)       as three_par,
    safe_cast(source.ftr          as float64)       as ftr,

    -- four factors — defense
    safe_cast(source.opp_efg_pct      as float64)  as opp_efg_pct,
    safe_cast(source.opp_tov_pct      as float64)  as opp_tov_pct,
    safe_cast(source.drb_pct          as float64)  as drb_pct,
    safe_cast(source.opp_ft_per_fga   as float64)  as opp_ft_per_fga,

    -- venue / attendance
    source.arena,
    safe_cast(source.attend       as int64)         as attend,
    safe_cast(source.attend_per_g as int64)         as attend_per_g

from source
left join crosswalk
    on source.team_abbrev = crosswalk.raw_value
