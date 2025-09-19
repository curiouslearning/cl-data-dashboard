WITH all_events AS (
  SELECT
    user_pseudo_id,
    event_name,
    CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open,
    geo.country AS country,
    LOWER(REGEXP_EXTRACT(app_info.id, r'(?i)feedthemonster(.*)')) AS app_language,
    app_info.version AS app_version,
    event_date,
    PARSE_DATE('%Y%m%d', event_date) AS event_date_parsed,
    event_timestamp,
    TIMESTAMP_MICROS(event_timestamp) AS event_ts,
    b.max_level AS max_game_level,

    -- Add these for use in the outer query
    params.key AS params_key,
    params.value.string_value AS params_value_string_value,

    -- GamePlay Level Success date
    CASE
      WHEN event_name = 'GamePlay' AND params.key = 'action' AND params.value.string_value LIKE 'LevelSuccess%'
      THEN PARSE_DATE('%Y%m%d', event_date)
      ELSE NULL
    END AS level_success_date,

    -- Max user level
    CASE
      WHEN event_name = 'GamePlay' AND params.key = 'action' AND params.value.string_value LIKE 'LevelSuccess%'
      THEN CAST(SUBSTR(params.value.string_value, (STRPOS(params.value.string_value, '_') + 1)) AS INT64)
      ELSE NULL
    END AS user_level,

    -- Level completed count
    CASE
      WHEN event_name = 'GamePlay' AND params.value.string_value LIKE 'LevelSuccess%' THEN 1
      ELSE 0
    END AS level_completed_flag,

    -- Puzzle completed count
    CASE
      WHEN event_name = 'GamePlay' AND params.value.string_value LIKE 'SegmentSuccess%' THEN 1
      ELSE 0
    END AS puzzle_completed_flag,

    -- Session start count
    CASE
      WHEN event_name = 'session_start' THEN 1
      ELSE 0
    END AS session_start_flag

  FROM (
    SELECT * FROM `ftm-b9d99.analytics_159643920.events_20*`
    UNION ALL SELECT * FROM `ftm-afrikaans.analytics_177200876.events_20*`
    UNION ALL SELECT * FROM `ftm-hindi.analytics_174638281.events_20*`
    UNION ALL SELECT * FROM `ftm-brazilian-portuguese.analytics_161789655.events_20*`
    UNION ALL SELECT * FROM `ftm-english.analytics_152408808.events_20*`
    UNION ALL SELECT * FROM `ftm-french.analytics_173880465.events_20*`
    UNION ALL SELECT * FROM `ftm-isixhosa.analytics_180747962.events_20*`
    UNION ALL SELECT * FROM `ftm-kinayrwanda.analytics_177922191.events_20*`
    UNION ALL SELECT * FROM `ftm-oromo.analytics_167539175.events_20*`
    UNION ALL SELECT * FROM `ftm-swahili.analytics_160694316.events_20*`
    UNION ALL SELECT * FROM `ftm-somali.analytics_159630038.events_20*`
    UNION ALL SELECT * FROM `ftm-sepedi.analytics_180755978.events_20*`
    UNION ALL SELECT * FROM `ftm-zulu.analytics_155849122.events_20*`
    UNION ALL SELECT * FROM `ftm-southafricanenglish.analytics_173750850.events_20*`
    UNION ALL SELECT * FROM `ftm-spanish.analytics_158656398.events_20*`
  ) AS a
  CROSS JOIN UNNEST(event_params) AS params
  LEFT JOIN (
    SELECT app_language, max_level
    FROM `dataexploration-193817.user_data.language_max_level`
    GROUP BY app_language, max_level
  ) b
  ON b.app_language = LOWER(REGEXP_EXTRACT(app_info.id, r'(?i)feedthemonster(.*)'))
  WHERE
    (
      (event_name = 'GamePlay' AND params.key = 'action' AND
        (params.value.string_value LIKE 'LevelSuccess%' OR params.value.string_value LIKE 'SegmentSuccess%'))
      OR (event_name = 'session_start')
      OR (event_name = 'user_engagement')
    )
    AND LOWER(app_info.id) LIKE '%feedthemonster%'
    AND CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) BETWEEN '2021-01-01' AND CURRENT_DATE()
),

numbered_events AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY user_pseudo_id ORDER BY event_timestamp) AS rn
  FROM
    all_events
),

played_levels AS (
  SELECT
    user_pseudo_id,
    user_level
  FROM
    numbered_events
  WHERE
    user_level IS NOT NULL
),

max_level AS (
  SELECT
    user_pseudo_id,
    MAX(user_level) AS max_played_level
  FROM
    played_levels
  GROUP BY
    user_pseudo_id
),

level_check AS (
  SELECT
    m.user_pseudo_id,
    GENERATE_ARRAY(1, m.max_played_level) AS expected_levels,
    ARRAY_AGG(DISTINCT p.user_level) AS played_levels
  FROM
    max_level m
  LEFT JOIN
    played_levels p
  ON
    m.user_pseudo_id = p.user_pseudo_id
  GROUP BY
    m.user_pseudo_id, m.max_played_level
),

level_skips AS (
  SELECT
    user_pseudo_id,
    -- TRUE if any expected level is missing from played levels
    ARRAY_LENGTH(
      ARRAY(
        SELECT level FROM UNNEST(expected_levels) AS level
        WHERE level NOT IN UNNEST(played_levels)
      )
    ) > 0 AS skipped_level
  FROM
    level_check
),

with_deltas AS (
  SELECT
    *,
    LAG(event_ts) OVER (PARTITION BY user_pseudo_id ORDER BY rn) AS prev_event_ts,
    TIMESTAMP_DIFF(event_ts, LAG(event_ts) OVER (PARTITION BY user_pseudo_id ORDER BY rn), SECOND) AS seconds_since_last
  FROM
    numbered_events
),

marked_sessions AS (
  SELECT
    *,
    CASE
      WHEN seconds_since_last IS NULL OR seconds_since_last > 120 THEN 1
      ELSE 0
    END AS is_new_session
  FROM
    with_deltas
),

sessionized AS (
  SELECT
    *,
    SUM(is_new_session) OVER (PARTITION BY user_pseudo_id ORDER BY rn) AS session_id
  FROM
    marked_sessions
),

session_durations AS (
  SELECT
    user_pseudo_id,
    session_id,
    TIMESTAMP_DIFF(MAX(event_ts), MIN(event_ts), SECOND) AS session_duration_sec
  FROM
    sessionized
  GROUP BY
    user_pseudo_id, session_id
),

session_stats AS (
  SELECT
    user_pseudo_id,
    COUNT(*) AS engagement_event_count,
    ROUND(SUM(session_duration_sec) / 60.0, 1) AS total_time_minutes,
    ROUND(AVG(session_duration_sec) / 60.0, 1) AS avg_session_length_minutes
  FROM
    session_durations
  GROUP BY
    user_pseudo_id
)

SELECT
  a.user_pseudo_id,
  MIN(a.first_open) AS first_open,
  MAX(a.country) AS country,
  MAX(a.app_language) AS app_language,
  IFNULL(MAX(a.user_level), 0) AS max_user_level,
  MAX(a.max_game_level) AS max_game_level,
  MAX(a.app_version) AS app_version,
  MIN(a.level_success_date) AS la_date,
  NULL AS started_in_offline_mode,
  "Unity" as app,

  -- New: ra_date (date Level 25 reached) and days_to_ra
  MIN(CASE
        WHEN a.event_name = 'GamePlay'
          AND a.params_key = 'action'
          AND a.params_value_string_value = 'LevelSuccess_25'
        THEN a.event_date_parsed
      END) AS ra_date,

  DATE_DIFF(
    MIN(CASE
          WHEN a.event_name = 'GamePlay'
            AND a.params_key = 'action'
            AND a.params_value_string_value = 'LevelSuccess_25'
          THEN a.event_date_parsed
        END),
    MIN(a.first_open),
    DAY
  ) AS days_to_ra,

  -- First and last event dates
  MIN(a.event_date_parsed) AS first_event_date,
  MAX(a.event_date_parsed) AS last_event_date,

  -- Active span in days (min 1)
  GREATEST(DATE_DIFF(MAX(a.event_date_parsed), MIN(a.event_date_parsed), DAY), 1) AS active_span,

  -- Session-based event count and durations from calculated stats
  s.engagement_event_count,
  s.total_time_minutes,
  s.avg_session_length_minutes,

  -- Event counts
  SUM(a.level_completed_flag) AS level_completed_count,
  SUM(a.session_start_flag) AS total_sessions,

  CASE
    WHEN SUM(a.level_completed_flag) > 0 THEN 'level_completed'
    WHEN SUM(a.puzzle_completed_flag) > 0 THEN 'puzzle_completed'
    WHEN SUM(a.session_start_flag) > 0 THEN 'session_start'
    ELSE NULL
  END AS furthest_event,

  SAFE_DIVIDE(IFNULL(MAX(a.user_level),0), MAX(a.max_game_level)) * 100 AS gpc,
  -- User reached at least level 1 (Learner Acquired)
  CASE
    WHEN IFNULL(MAX(a.user_level), 0) >= 1 THEN 1
    ELSE 0
  END AS la_flag,

  -- User reached at least level 25 (Reader Acquired)
  CASE
    WHEN IFNULL(MAX(a.user_level), 0) >= 25 THEN 1
    ELSE 0
  END AS ra_flag,

  -- User reached at least level 1 AND gpc >= 90 (Game Completed)
  CASE
    WHEN IFNULL(MAX(a.user_level), 0) >= 1
         AND SAFE_DIVIDE(IFNULL(MAX(a.user_level), 0), MAX(a.max_game_level)) * 100 >= 90
      THEN 1
    ELSE 0
  END AS gc_flag,

  -- User was "Learner Reached" (just always 1 for cohort inclusion)
  1 AS lr_flag,

  -- Final skipped_level flag
  IFNULL(ls.skipped_level, FALSE) AS skipped_level

FROM
  all_events a
LEFT JOIN
  session_stats s
ON
  a.user_pseudo_id = s.user_pseudo_id
LEFT JOIN
  level_skips ls
ON
  a.user_pseudo_id = ls.user_pseudo_id
GROUP BY
  a.user_pseudo_id, s.engagement_event_count, s.total_time_minutes, s.avg_session_length_minutes, ls.skipped_level;
