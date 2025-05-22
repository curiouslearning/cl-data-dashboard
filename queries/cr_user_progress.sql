WITH all_events AS (
  SELECT
    user_pseudo_id,
    "org.curiouslearning.container" AS app_id,
    CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open,
    geo.country AS country,

    -- Extract cr_user_id
    (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'cr_user_id') AS cr_user_id,

    -- App language
    LOWER(REGEXP_EXTRACT((SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location'), r'[?&]cr_lang=([^&]+)')) AS app_language,

    -- Extract app version
    (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'version_number') AS app_version,
  
    -- Level data (only used when event_name = 'level_completed')
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
),

-- Join in max level per language
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

-- Aggregate per user
aggregated AS (
  SELECT
    user_pseudo_id,
    cr_user_id,
    app_version,
    first_open,
    country,
    app_language,
    max_game_level,

    -- Dates and levels only for successful completions
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

    -- Event counts
    COUNTIF(event_name = 'level_completed' AND success_or_failure = 'success' AND level_number IS NOT NULL) AS level_completed_count,
    COUNTIF(event_name = 'puzzle_completed') AS puzzle_completed_count,
    COUNTIF(event_name = 'selected_level') AS selected_level_count,
    COUNTIF(event_name = 'tapped_start') AS tapped_start_count,
    COUNTIF(event_name = 'download_completed') AS download_completed_count
  FROM joined_events
  GROUP BY
    user_pseudo_id,
    cr_user_id,
    app_version,
    first_open,
    country,
    app_language,
    max_game_level
)

-- Final selection + furthest logic
SELECT
  user_pseudo_id,
  cr_user_id,
  first_open,
  country,
  app_language,
  app_version,
  max_user_level,
  max_game_level,
  la_date,
  CASE
    WHEN level_completed_count > 0 THEN 'level_completed'
    WHEN puzzle_completed_count > 0 THEN 'puzzle_completed'
    WHEN selected_level_count > 0 THEN 'selected_level'
    WHEN tapped_start_count > 0 THEN 'tapped_start'
    WHEN download_completed_count > 0 THEN 'download_completed'
    ELSE NULL
  END AS furthest_event,
  SAFE_DIVIDE(max_user_level, max_game_level) * 100 AS gpc
FROM aggregated
