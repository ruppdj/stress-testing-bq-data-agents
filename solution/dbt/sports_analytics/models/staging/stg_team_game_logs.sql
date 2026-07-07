with source as (
    select * from {{ source('raw', 'team_game_logs') }}
    -- 2 rows have null wl (BOS/IND APR 16, 2013 postponed game; never recorded a result)
    where wl is not null
),

crosswalk as (
    select * from {{ ref('team_crosswalk') }}
)

select
    -- identifiers
    source.team_id,
    source.game_id,
    -- game_date stored as STRING 'MMM DD, YYYY' in source; PARSE_DATE handles it
    parse_date('%b %d, %Y', source.game_date) as game_date,
    source.season,

    -- team abbreviations: raw table has no standalone columns; both extracted from matchup
    -- matchup format is always "AAA vs. BBB" (home) or "AAA @ BBB" (away)
    cw_team.canonical_abbrev as team_abbrev,
    cw_opp.canonical_abbrev  as opponent_team_abbrev,

    -- matchup rebuilt from canonical abbreviations so the string matches normalized team IDs
    case
        when source.matchup like '%vs.%'
            then cw_team.canonical_abbrev || ' vs. ' || cw_opp.canonical_abbrev
            else cw_team.canonical_abbrev || ' @ '   || cw_opp.canonical_abbrev
    end as matchup,

    -- home/away: "vs." = home, "@" = away
    source.matchup like '%vs.%' as is_home,

    -- outcome and running record
    source.wl,
    source.w,
    source.l,
    source.w_pct,

    -- box score totals
    source.min,
    source.fgm,
    source.fga,
    source.fg_pct,
    source.fg3m,
    source.fg3a,
    source.fg3_pct,
    source.ftm,
    source.fta,
    source.ft_pct,
    source.oreb,
    source.dreb,
    source.reb,
    source.ast,
    source.stl,
    source.blk,
    source.tov,
    source.pf,
    source.pts

from source
left join crosswalk as cw_team
    on left(source.matchup, 3) = cw_team.raw_value
left join crosswalk as cw_opp
    on right(source.matchup, 3) = cw_opp.raw_value
