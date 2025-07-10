


 WITH all_events AS (
  SELECT
    user_pseudo_id,
    (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'cr_user_id') AS cr_user_id,
    (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'version_number') AS app_version,
    CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open,
    geo.country AS country,
    LOWER(REGEXP_EXTRACT((SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location'), r'[?&]cr_lang=([^&]+)')) AS app_language,
    SAFE_CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'level_number') AS INT64) AS level_number,
    (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'success_or_failure') AS success_or_failure,
    event_name,
    event_date
  FROM
    `ftm-b9d99.analytics_159643920.events_20*`
  WHERE
    event_name IN (
      'download_completed', 'tapped_start', 'selected_level',
      'puzzle_completed', 'level_completed'
    )
    AND (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location')
        LIKE '%https://feedthemonster.curiouscontent.org%'
    AND device.web_info.hostname LIKE 'feedthemonster.curiouscontent.org%'
    AND CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) BETWEEN '2021-01-01' AND CURRENT_DATE()
    AND (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'cr_user_id') IS NOT NULL
    AND (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'cr_user_id') != ''
),

cr_app_launch_deduped AS (
  SELECT
    cr_user_id,
    MAX(active_span) AS active_span,
    MAX(total_time_minutes) AS total_time_minutes,
    AVG(avg_session_length_minutes) AS avg_session_length_minutes,
    MAX(engagement_event_count) AS total_sessions
  FROM
    `dataexploration-193817.user_data.cr_app_launch`
  WHERE
    cr_user_id IS NOT NULL
    AND cr_user_id != ''
  GROUP BY cr_user_id
),

joined_events AS (
  SELECT
    a.*,
    b.max_level AS max_game_level
  FROM all_events a
  LEFT JOIN (
    SELECT app_language, max_level
    FROM `dataexploration-193817.user_data.language_max_level`
    GROUP BY app_language, max_level
  ) b
  ON a.app_language = b.app_language
),

aggregated AS (
  SELECT
    user_pseudo_id,
    cr_user_id,
    app_version,
    first_open,
    country,
    app_language,
    max_game_level,
    MIN(CASE
      WHEN event_name = 'level_completed'
        AND success_or_failure = 'success'
        AND level_number IS NOT NULL
      THEN PARSE_DATE('%Y%m%d', event_date)
    END) AS la_date,
    MAX(CASE
      WHEN event_name = 'level_completed'
        AND success_or_failure = 'success'
        AND level_number IS NOT NULL
      THEN level_number + 1
    ELSE 0 END) AS max_user_level,
    COUNTIF(event_name = 'level_completed' AND success_or_failure = 'success' AND level_number IS NOT NULL) AS level_completed_count,
    COUNTIF(event_name = 'puzzle_completed') AS puzzle_completed_count,
    COUNTIF(event_name = 'selected_level') AS selected_level_count,
    COUNTIF(event_name = 'tapped_start') AS tapped_start_count,
    COUNTIF(event_name = 'download_completed') AS download_completed_count
  FROM joined_events
  WHERE cr_user_id IS NOT NULL AND cr_user_id != ''
  GROUP BY
    user_pseudo_id,
    cr_user_id,
    app_version,
    first_open,
    country,
    app_language,
    max_game_level
),

-- New CTE to get global min_la_date and max app_version per user
user_level_aggregates AS (
  SELECT
    cr_user_id,
    MIN(la_date) AS min_la_date,
    ARRAY_AGG(app_version ORDER BY SAFE_CAST(REGEXP_EXTRACT(app_version, r'(\d+)$') AS INT64) DESC LIMIT 1)[OFFSET(0)] AS max_app_version
  FROM aggregated
  GROUP BY cr_user_id
)

SELECT
  a.user_pseudo_id,
  a.cr_user_id,
  a.first_open,
  a.country,
  a.app_language,

  -- Use global max app_version per user
  u.max_app_version AS app_version,

  a.max_user_level,
  a.max_game_level,

  -- Use global min la_date per user
  u.min_la_date AS la_date,

  c.active_span,
  c.total_time_minutes,
  c.avg_session_length_minutes,
  c.total_sessions,

  CASE
    WHEN a.level_completed_count > 0 THEN 'level_completed'
    WHEN a.puzzle_completed_count > 0 THEN 'puzzle_completed'
    WHEN a.selected_level_count > 0 THEN 'selected_level'
    WHEN a.tapped_start_count > 0 THEN 'tapped_start'
    WHEN a.download_completed_count > 0 THEN 'download_completed'
    ELSE NULL
  END AS furthest_event,

  SAFE_DIVIDE(a.max_user_level, a.max_game_level) * 100 AS gpc

FROM
  aggregated a
JOIN
  user_level_aggregates u
ON
  a.cr_user_id = u.cr_user_id
INNER JOIN
  cr_app_launch_deduped c
ON
  a.cr_user_id = c.cr_user_id
ORDER BY
  c.total_time_minutes;
 
