SELECT
    raw_value,
    canonical_abbrev
FROM {{ ref('team_crosswalk') }}
WHERE raw_value != canonical_abbrev
