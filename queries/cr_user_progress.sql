WITH
  -- -------------------------------
  -- 1. Extract raw events
  -- -------------------------------
  all_events AS (
  SELECT
    user_pseudo_id,
    (
    SELECT
      value.string_value
    FROM
      UNNEST(event_params)
    WHERE
      KEY = 'cr_user_id' ) AS cr_user_id,
    CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open,
    geo.country AS country,
    LOWER(REGEXP_EXTRACT((
        SELECT
          value.string_value
        FROM
          UNNEST(event_params)
        WHERE
          KEY = 'page_location' ), r'[?&]cr_lang=([^&]+)')) AS app_language,
    SAFE_CAST((
      SELECT
        value.int_value
      FROM
        UNNEST(event_params)
      WHERE
        KEY = 'level_number' ) AS INT64) AS level_number,
    SAFE_CAST((
      SELECT
        value.int_value
      FROM
        UNNEST(event_params)
      WHERE
        KEY = 'number_of_successful_puzzles' ) AS INT64) AS number_of_successful_puzzles,
    (
    SELECT
      value.string_value
    FROM
      UNNEST(event_params)
    WHERE
      KEY = 'success_or_failure' ) AS success_or_failure,
    event_name,
    CASE event_name
      WHEN 'session_start' THEN 0
      WHEN 'download_completed' THEN 1
      WHEN 'tapped_start' THEN 2
      WHEN 'selected_level' THEN 3
      WHEN 'puzzle_completed' THEN 4
      WHEN 'level_completed' THEN 5
      ELSE -1
  END
    AS funnel_stage,
    event_date,
    device.web_info.hostname AS hostname,
    event_timestamp
  FROM
    `ftm-b9d99.analytics_159643920.events_20*`
  WHERE
    event_name IN ('session_start',
      'download_completed',
      'tapped_start',
      'selected_level',
      'puzzle_completed',
      'level_completed')
    AND ( (device.web_info.hostname LIKE 'feedthemonster.curiouscontent.org%'
        AND (
        SELECT
          value.string_value
        FROM
          UNNEST(event_params)
        WHERE
          KEY = 'page_location' ) LIKE '%https://feedthemonster.curiouscontent.org%')
      OR REGEXP_CONTAINS(device.web_info.hostname, r'^[a-z-]+-ftm-standalone\.androidplatform\.net$')
      OR device.web_info.hostname = 'appassets.androidplatform.net' )
    AND CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) BETWEEN '2021-01-01'
    AND CURRENT_DATE()
    AND (
    SELECT
      value.string_value
    FROM
      UNNEST(event_params)
    WHERE
      KEY = 'cr_user_id' ) IS NOT NULL
    AND (
    SELECT
      value.string_value
    FROM
      UNNEST(event_params)
    WHERE
      KEY = 'cr_user_id' ) != '' ),
  -- -------------------------------
  -- 2. Join with language max level
  -- -------------------------------
  joined_events AS (
  SELECT
    a.*,
    b.max_level AS max_game_level
  FROM
    all_events a
  LEFT JOIN (
    SELECT
      app_language,
      max_level
    FROM
      `dataexploration-193817.user_data.language_max_level`
    GROUP BY
      app_language,
      max_level ) b
  ON
    a.app_language = b.app_language ),
  -- -------------------------------
  -- 3. Aggregate user-level metrics
  -- -------------------------------
  aggregated AS (
  SELECT
    cr_user_id,
    country,
    app_language,
    ARRAY_AGG(user_pseudo_id
    ORDER BY
      event_date
    LIMIT
      1)[
  OFFSET
    (0)] AS user_pseudo_id,
    MIN(first_open) AS first_open,
    ARRAY_AGG(hostname
    ORDER BY
      event_date
    LIMIT
      1)[
  OFFSET
    (0)] AS hostname,
    MAX(max_game_level) AS max_game_level,
    MIN(CASE
        WHEN event_name = 'level_completed' AND number_of_successful_puzzles >= 3 AND level_number IS NOT NULL THEN PARSE_DATE('%Y%m%d', event_date)
    END
      ) AS la_date,
    MIN(CASE
        WHEN event_name = 'level_completed' AND number_of_successful_puzzles >= 3 AND level_number = 24 THEN PARSE_DATE('%Y%m%d', event_date)
    END
      ) AS ra_date,
    MAX(CASE
        WHEN event_name = 'level_completed' AND number_of_successful_puzzles >= 3 AND level_number IS NOT NULL THEN level_number + 1
        ELSE 0
    END
      ) AS max_user_level,
    COUNTIF(event_name = 'level_completed'
      AND number_of_successful_puzzles >= 3
      AND level_number IS NOT NULL) AS level_completed_count,
    COUNTIF(event_name = 'puzzle_completed') AS puzzle_completed_count,
    COUNTIF(event_name = 'selected_level') AS selected_level_count,
    COUNTIF(event_name = 'tapped_start') AS tapped_start_count,
    COUNTIF(event_name = 'download_completed') AS download_completed_count,
    MAX(funnel_stage) AS furthest_stage,
    ARRAY_AGG(event_name
    ORDER BY
      funnel_stage DESC
    LIMIT
      1)[
  OFFSET
    (0)] AS furthest_event
  FROM
    joined_events
  WHERE
    cr_user_id IS NOT NULL
    AND cr_user_id != ''
  GROUP BY
    cr_user_id,
    country,
    app_language ),
  -- -------------------------------
  -- 4. Cohort tagging join
  -- -------------------------------
  tagged_cohorts AS (
  SELECT
    a.*,
    cg.cohort_group
  FROM
    aggregated a
  LEFT JOIN
    `dataexploration-193817.user_data.cohort_groups` cg
  ON
    a.cr_user_id = cg.cr_user_id ),
  -- -------------------------------
  -- 5. Supporting aggregates
  -- -------------------------------
  user_level_aggregates AS (
  SELECT
    cr_user_id,
    country,
    app_language,
    MIN(la_date) AS min_la_date
  FROM
    aggregated
  GROUP BY
    cr_user_id,
    country,
    app_language ),
  last_events AS (
  SELECT
    cr_user_id,
    MAX(PARSE_DATE('%Y%m%d', event_date)) AS last_event_date
  FROM
    all_events
  WHERE
    cr_user_id IS NOT NULL
    AND cr_user_id != ''
  GROUP BY
    cr_user_id ),
  -- -------------------------------
  -- 6. Sessionization (fixed analytics)
  -- -------------------------------
  ordered_events AS (
  SELECT
    cr_user_id,
    event_timestamp,
    TIMESTAMP_MICROS(event_timestamp) AS event_ts
  FROM
    all_events
  WHERE
    cr_user_id IS NOT NULL
    AND cr_user_id != '' ),
  with_deltas AS (
  SELECT
    *,
    LAG(event_ts) OVER (PARTITION BY cr_user_id ORDER BY event_ts) AS prev_event_ts,
    TIMESTAMP_DIFF(event_ts, LAG(event_ts) OVER (PARTITION BY cr_user_id ORDER BY event_ts), SECOND) AS seconds_since_last
  FROM
    ordered_events ),
  marked_sessions AS (
  SELECT
    *,
    CASE
      WHEN seconds_since_last IS NULL OR seconds_since_last > 120 THEN 1
      ELSE 0
  END
    AS is_new_session
  FROM
    with_deltas ),
  sessionized AS (
  SELECT
    *,
    SUM(is_new_session) OVER (PARTITION BY cr_user_id ORDER BY event_ts) AS session_id
  FROM
    marked_sessions ),
  session_durations AS (
  SELECT
    cr_user_id,
    session_id,
    TIMESTAMP_DIFF(MAX(event_ts), MIN(event_ts), SECOND) AS session_duration_sec
  FROM
    sessionized
  GROUP BY
    cr_user_id,
    session_id ),
  session_stats AS (
  SELECT
    cr_user_id,
    COUNT(*) AS engagement_event_count,
    ROUND(SUM(session_duration_sec) / 60.0, 1) AS total_time_minutes,
    ROUND(AVG(session_duration_sec) / 60.0, 1) AS avg_session_length_minutes
  FROM
    session_durations
  GROUP BY
    cr_user_id )
  -- -------------------------------
  -- 7. Final output
  -- -------------------------------
SELECT
  a.user_pseudo_id,
  a.cr_user_id,
  a.first_open,
  a.country,
  a.app_language,
  a.cohort_group,
  -- ✅ new column
  CASE
    WHEN a.hostname = 'appassets.androidplatform.net' THEN 'WBS-standalone'
    WHEN REGEXP_CONTAINS(a.hostname, r'^([a-z-]+)-ftm-standalone\.androidplatform\.net$') THEN REGEXP_EXTRACT(a.hostname, r'^([a-z-]+)-ftm-standalone\.androidplatform\.net$') || '-standalone'
    ELSE 'CR'
END
  AS app,
  a.max_user_level,
  a.max_game_level,
  u.min_la_date AS la_date,
  a.ra_date,
  CASE
    WHEN a.ra_date IS NOT NULL THEN DATE_DIFF(a.ra_date, a.first_open, DAY) + 1
    ELSE NULL
END
  AS days_to_ra,
  a.furthest_event,
  SAFE_DIVIDE(a.max_user_level, a.max_game_level) * 100 AS gpc,
  COALESCE(s.engagement_event_count, 0) AS engagement_event_count,
  COALESCE(s.total_time_minutes, 0) AS total_time_minutes,
  COALESCE(s.avg_session_length_minutes, 0) AS avg_session_length_minutes,
  le.last_event_date,
  DATE_DIFF(le.last_event_date, a.first_open, DAY) AS active_span,
  CASE
    WHEN a.max_user_level >= 1 THEN 1
    ELSE 0
END
  AS la_flag,
  CASE
    WHEN a.max_user_level >= 25 THEN 1
    ELSE 0
END
  AS ra_flag,
  CASE
    WHEN a.max_user_level >= 1 AND SAFE_DIVIDE(a.max_user_level, a.max_game_level) * 100 >= 90 THEN 1
    ELSE 0
END
  AS gc_flag,
  1 AS lr_flag
FROM
  tagged_cohorts a
JOIN
  user_level_aggregates u
ON
  a.cr_user_id = u.cr_user_id
  AND a.country = u.country
  AND a.app_language = u.app_language
LEFT JOIN
  session_stats s
ON
  a.cr_user_id = s.cr_user_id
LEFT JOIN
  last_events le
ON
  a.cr_user_id = le.cr_user_id
ORDER BY
  engagement_event_count DESC;