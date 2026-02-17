/*
===============================================================================
CR_USER_PROGRESS

Unified per-user progress table for Feed The Monster across:
  - Curious Reader container (CR)
  - Standalone Android builds (<lang>-ftm-standalone.androidplatform.net)
  - WBS offline-capable build (appassets.androidplatform.net)

Attribution
-----------
- Attribution is resolved upstream in cr_app_launch
- This table only consumes:
    is_attributed
    attribution_source
    attribution_campaign_id
===============================================================================
*/

CREATE OR REPLACE TABLE `dataexploration-193817.user_data.cr_user_progress`
AS
WITH
  all_events AS (
    SELECT
      user_pseudo_id,
      (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'cr_user_id') AS cr_user_id,
      CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open,
      geo.country AS country,
      LOWER(REGEXP_EXTRACT(
        (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location'),
        r'[?&]cr_lang=([^&]+)'
      )) AS app_language,
      SAFE_CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'level_number') AS INT64) AS level_number,
      SAFE_CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'number_of_successful_puzzles') AS INT64) AS number_of_successful_puzzles,
      (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'success_or_failure') AS success_or_failure,
      event_name,
      CASE event_name
        WHEN 'session_start' THEN 0
        WHEN 'download_completed' THEN 1
        WHEN 'tapped_start' THEN 2
        WHEN 'selected_level' THEN 3
        WHEN 'puzzle_completed' THEN 4
        WHEN 'level_completed' THEN 5
        ELSE -1
      END AS funnel_stage,
      event_date,
      device.web_info.hostname AS hostname,
      event_timestamp
    FROM `ftm-b9d99.analytics_159643920.events_20*`
    WHERE event_name IN (
      'session_start',
      'download_completed',
      'tapped_start',
      'selected_level',
      'puzzle_completed',
      'level_completed'
    )
      AND (
        (device.web_info.hostname LIKE 'feedthemonster.curiouscontent.org%'
          AND (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location')
              LIKE '%https://feedthemonster.curiouscontent.org%')
        OR REGEXP_CONTAINS(device.web_info.hostname, r'^[a-z-]+-ftm-standalone\.androidplatform\.net$')
        OR device.web_info.hostname = 'appassets.androidplatform.net'
      )
      AND CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE)
            BETWEEN '2021-01-01' AND CURRENT_DATE()
      AND (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'cr_user_id') IS NOT NULL
      AND (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'cr_user_id') != ''
  ),

  joined_events AS (
    SELECT
      a.*,
      b.max_level AS max_game_level
    FROM all_events a
    LEFT JOIN `dataexploration-193817.user_data.language_max_level` b
      ON a.app_language = b.app_language
  ),

  aggregated AS (
    SELECT
      cr_user_id,
      country,
      app_language,
      ARRAY_AGG(user_pseudo_id ORDER BY event_date LIMIT 1)[OFFSET(0)] AS user_pseudo_id,
      MIN(first_open) AS first_open,
      ARRAY_AGG(hostname ORDER BY event_date LIMIT 1)[OFFSET(0)] AS hostname,
      MAX(max_game_level) AS max_game_level,

      MIN(CASE
        WHEN event_name = 'level_completed'
         AND number_of_successful_puzzles >= 3
         AND level_number IS NOT NULL
        THEN PARSE_DATE('%Y%m%d', event_date)
      END) AS la_date,

      MIN(CASE
        WHEN event_name = 'level_completed'
         AND number_of_successful_puzzles >= 3
         AND level_number = 24
        THEN PARSE_DATE('%Y%m%d', event_date)
      END) AS ra_date,

      MAX(CASE
        WHEN event_name = 'level_completed'
         AND number_of_successful_puzzles >= 3
         AND level_number IS NOT NULL
        THEN level_number + 1
        ELSE 0
      END) AS max_user_level,

      COUNTIF(event_name = 'level_completed'
        AND number_of_successful_puzzles >= 3
        AND level_number IS NOT NULL) AS level_completed_count,

      COUNTIF(event_name = 'puzzle_completed') AS puzzle_completed_count,
      COUNTIF(event_name = 'selected_level') AS selected_level_count,
      COUNTIF(event_name = 'tapped_start') AS tapped_start_count,
      COUNTIF(event_name = 'download_completed') AS download_completed_count,

      MAX(funnel_stage) AS furthest_stage,
      ARRAY_AGG(event_name ORDER BY funnel_stage DESC LIMIT 1)[OFFSET(0)] AS furthest_event
    FROM joined_events
    GROUP BY cr_user_id, country, app_language
  ),

  tagged_cohorts AS (
    SELECT
      a.*,
      cg.cohort_name
    FROM aggregated a
    LEFT JOIN `dataexploration-193817.user_data.cr_cohorts` cg
      ON a.cr_user_id = cg.cr_user_id
  ),

  last_events AS (
    SELECT
      cr_user_id,
      MAX(PARSE_DATE('%Y%m%d', event_date)) AS last_event_date
    FROM all_events
    GROUP BY cr_user_id
  ),

  -- ----------------------------------------------------------------------
  -- Sessionization for engagement metrics (restored)
  -- Session boundary rule: new session if > 120 seconds since prior event
  -- ----------------------------------------------------------------------
  ordered_events AS (
    SELECT
      cr_user_id,
      TIMESTAMP_MICROS(event_timestamp) AS event_ts
    FROM all_events
    WHERE cr_user_id IS NOT NULL AND cr_user_id != ''
  ),

  with_deltas AS (
    SELECT
      cr_user_id,
      event_ts,
      LAG(event_ts) OVER (PARTITION BY cr_user_id ORDER BY event_ts) AS prev_event_ts,
      TIMESTAMP_DIFF(
        event_ts,
        LAG(event_ts) OVER (PARTITION BY cr_user_id ORDER BY event_ts),
        SECOND
      ) AS seconds_since_last
    FROM ordered_events
  ),

  marked_sessions AS (
    SELECT
      *,
      CASE
        WHEN seconds_since_last IS NULL OR seconds_since_last > 120 THEN 1
        ELSE 0
      END AS is_new_session
    FROM with_deltas
  ),

  sessionized AS (
    SELECT
      *,
      SUM(is_new_session) OVER (PARTITION BY cr_user_id ORDER BY event_ts) AS session_id
    FROM marked_sessions
  ),

  session_durations AS (
    SELECT
      cr_user_id,
      session_id,
      TIMESTAMP_DIFF(MAX(event_ts), MIN(event_ts), SECOND) AS session_duration_sec
    FROM sessionized
    GROUP BY cr_user_id, session_id
  ),

  session_stats AS (
    SELECT
      cr_user_id,
      COUNT(*) AS session_count,
      -- keep engagement_event_count (matches your current output name)
      (SELECT COUNT(*) FROM ordered_events oe WHERE oe.cr_user_id = sd.cr_user_id) AS engagement_event_count,
      ROUND(SUM(session_duration_sec) / 60.0, 1) AS total_time_minutes,
      ROUND(AVG(session_duration_sec) / 60.0, 1) AS avg_session_length_minutes
    FROM session_durations sd
    GROUP BY cr_user_id
  ),

  attribution_flags AS (
    SELECT
      cr_user_id,
      country,
      app_language,
      is_attributed,
      attribution_source,
      attribution_campaign_id
    FROM `dataexploration-193817.user_data.cr_app_launch`
  )

SELECT
  a.user_pseudo_id,
  a.cr_user_id,
  a.first_open,
  a.country,
  a.app_language,
  a.cohort_name,

  CASE
    WHEN a.hostname = 'appassets.androidplatform.net' THEN 'WBS-standalone'
    WHEN REGEXP_CONTAINS(a.hostname, r'^([a-z-]+)-ftm-standalone\.androidplatform\.net$')
      THEN REGEXP_EXTRACT(a.hostname, r'^([a-z-]+)-ftm-standalone\.androidplatform\.net$') || '-standalone'
    ELSE 'CR'
  END AS app,

  a.max_user_level,
  a.max_game_level,
  a.la_date,
  a.ra_date,

  CASE
    WHEN a.ra_date IS NOT NULL THEN DATE_DIFF(a.ra_date, a.first_open, DAY) + 1
    ELSE NULL
  END AS days_to_ra,

  a.furthest_event,
  SAFE_DIVIDE(a.max_user_level, a.max_game_level) * 100 AS gpc,

  COALESCE(s.engagement_event_count, 0) AS engagement_event_count,
  COALESCE(s.total_time_minutes, 0) AS total_time_minutes,
  COALESCE(s.avg_session_length_minutes, 0) AS avg_session_length_minutes,

  le.last_event_date,
  DATE_DIFF(le.last_event_date, a.first_open, DAY) AS active_span,

  CASE WHEN a.max_user_level >= 1 THEN 1 ELSE 0 END AS la_flag,
  CASE WHEN a.max_user_level >= 25 THEN 1 ELSE 0 END AS ra_flag,
  CASE
    WHEN a.max_user_level >= 1
     AND SAFE_DIVIDE(a.max_user_level, a.max_game_level) * 100 >= 90
    THEN 1 ELSE 0
  END AS gc_flag,

  af.is_attributed,
  af.attribution_source,
  af.attribution_campaign_id,

  1 AS lr_flag

FROM tagged_cohorts a
LEFT JOIN last_events le
  ON a.cr_user_id = le.cr_user_id
LEFT JOIN session_stats s
  ON a.cr_user_id = s.cr_user_id
LEFT JOIN attribution_flags af
  ON  a.cr_user_id = af.cr_user_id
  AND a.country = af.country
  AND a.app_language = af.app_language
ORDER BY engagement_event_count DESC;
