-- mart_unique_games has one row per physical game; mart_game_logs has one row per
-- team per game. The self-join that builds mart_unique_games must therefore produce
-- exactly half the game-log rows — any other ratio means dropped or fanned-out games.
WITH counts AS (
    SELECT
        (SELECT COUNT(*) FROM {{ ref('mart_unique_games') }}) AS unique_games,
        (SELECT COUNT(*) FROM {{ ref('mart_game_logs') }})    AS game_log_rows
)

SELECT *
FROM counts
WHERE unique_games * 2 != game_log_rows
