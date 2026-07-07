with source as (
    select * from {{ source('raw', 'trade_impact') }}
),

crosswalk as (
    select * from {{ ref('team_crosswalk') }}
),

player_crosswalk as (
    select * from {{ ref('player_name_crosswalk') }}
)

select
    -- identifiers (player name resolved to the player tables' canonical
    -- Basketball-Reference spelling; unmapped names — draft-and-stash players
    -- with no NBA player-table rows — pass through unchanged)
    coalesce(pcw.canonical_name, source.player_name) as player_name,
    source.season,
    cast(source.trade_date as date) as trade_date,

    -- teams (full names resolved to canonical abbreviations)
    cw_acq.canonical_abbrev as acquiring_team,
    cw_trd.canonical_abbrev as trading_team,

    source.conference,

    -- player profile at time of trade
    source.player_age,
    source.player_position,
    source.player_tier,
    source.player_allstar,
    source.player_games_trade_yr,

    -- player performance in the season prior to the trade
    source.player_vorp_prior,
    source.player_bpm_prior,
    source.player_ws48_prior,
    source.player_per_prior,
    source.player_usg_prior,
    source.player_ws_prior,
    source.player_games_prior,

    -- acquiring team record that season around the trade
    source.win_pct_at_trade,
    source.conf_rank_yr0,
    source.pre_games,
    source.pre_wins,
    source.pre_win_pct,
    source.post_games,
    source.post_wins,
    source.post_win_pct,

    -- contender flags at time of trade
    source.contender_500,
    source.contender_top6,
    source.contender_top4,
    source.contender_top2,

    -- acquiring team net rating: year before (yr-1), trade year (yr0), year after (yr+1)
    source.nrtg_yr_minus1,
    source.nrtg_yr0,
    source.nrtg_yr1,

    -- acquiring team playoff outcomes
    source.playoff_round_yr_minus1,
    source.playoff_round_yr0,
    source.playoff_round_yr1,
    source.playoff_seed_yr0,
    source.made_playoffs_yr0,
    source.won_championship_yr0,
    source.won_championship_yr1,
    source.seed_adj_round_yr0,

    -- raw text (useful for agent lookup/context)
    source.transaction_text

from source
left join crosswalk as cw_acq
    on source.acquiring_team = cw_acq.raw_value
left join crosswalk as cw_trd
    on source.trading_team = cw_trd.raw_value
left join player_crosswalk as pcw
    on source.player_name = pcw.raw_value
