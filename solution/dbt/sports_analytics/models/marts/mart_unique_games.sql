SELECT
    home.game_id,
    home.game_date,
    home.season,
    home.team_abbrev                AS home_team,
    home.pts                        AS home_pts,
    away.team_abbrev                AS away_team,
    away.pts                        AS away_pts,
    home.wl = 'W'                   AS home_win,
    (home.pts + away.pts)           AS total_pts,
    
    -- Home box score counting stats
    home.ast                        AS home_ast,
    home.reb                        AS home_reb,
    home.oreb                       AS home_oreb,
    home.dreb                       AS home_dreb,
    home.stl                        AS home_stl,
    home.blk                        AS home_blk,
    home.tov                        AS home_tov,
    home.pf                         AS home_pf,
    home.fgm                        AS home_fgm,
    home.fga                        AS home_fga,
    home.fg3m                       AS home_fg3m,
    home.fg3a                       AS home_fg3a,
    home.ftm                        AS home_ftm,
    home.fta                        AS home_fta,
    
    -- Away box score counting stats
    away.ast                        AS away_ast,
    away.reb                        AS away_reb,
    away.oreb                       AS away_oreb,
    away.dreb                       AS away_dreb,
    away.stl                        AS away_stl,
    away.blk                        AS away_blk,
    away.tov                        AS away_tov,
    away.pf                         AS away_pf,
    away.fgm                        AS away_fgm,
    away.fga                        AS away_fga,
    away.fg3m                       AS away_fg3m,
    away.fg3a                       AS away_fg3a,
    away.ftm                        AS away_ftm,
    away.fta                        AS away_fta
FROM {{ ref('stg_team_game_logs') }} home
JOIN {{ ref('stg_team_game_logs') }} away
    ON  home.game_id   = away.game_id
    AND away.is_home   = false
WHERE home.is_home = true
