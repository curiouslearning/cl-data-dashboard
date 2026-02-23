/*
===============================================================================
CR_USER_PROGRESS (Revised)

Unified per-user progress table for Feed The Monster across:
  - Curious Reader container (CR)
  - Standalone Android builds (<lang>-ftm-standalone.androidplatform.net)
  - WBS offline-capable build (appassets.androidplatform.net)

Key Fixes in this revision
--------------------------
1) Level numbering normalization (FTM quirk)
   - In FTM event data, level_number = 0 is actually the first level.
   - We normalize ALL level logic to 1-based by defining:
       level_number_1b = level_number_raw + 1
   - All downstream level calculations use level_number_1b.

2) RA date fallback logic (offline / missing level events)
   - Primary RA event (exact):
       first date of qualifying completion of level 25 (1-based)
       => level_number_1b = 25
   - Fallback RA event (if exact missing but progression proves RA happened):
       if max_user_level >= 26 (1-based),
       set ra_date to the first qualifying completion at level >= 26 (1-based)

3) days_to_ra stability
   - Some users can show days_to_ra = 0 if first_open (first_touch date) is later
     than early gameplay events (reinstall / device mismatch / ingestion quirks).
   - To avoid zero/negative artifacts, we compute:
       first_event_date = MIN(event_dt)
       start_date_for_days = LEAST(first_open, first_event_date)
   - days_to_ra uses start_date_for_days (inclusive counting with +1)

Attribution
-----------
- Attribution is resolved upstream in cr_app_launch
- This table consumes:
    is_attributed
    attribution_source
    attribution_campaign_id
===============================================================================
*/

CREATE OR REPLACE TABLE `dataexploration-193817.user_data.cr_user_progress`
AS
WITH
  -- ----------------------------------------------------------------------
  -- 1) Pull relevant events and normalize:
  --    - event_dt (DATE)
  --    - level_number_1b (1-based level)
  -- ----------------------------------------------------------------------
  all_events AS (
    SELECT
      user_pseudo_id,
      (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'cr_user_id') AS cr_user_id,

      -- First touch date from GA4 user_first_touch_timestamp
      CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open,

      geo.country AS country,

      -- Language extracted from page_location param
      LOWER(REGEXP_EXTRACT(
        (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location'),
        r'[?&]cr_lang=([^&]+)'
      )) AS app_language,

      -- Raw level_number from event params (FTM quirk: 0 = first level)
      SAFE_CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'level_number') AS INT64) AS level_number_raw,

      -- Normalized 1-based level number used everywhere downstream
      CASE
        WHEN SAFE_CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'level_number') AS INT64) IS NULL THEN NULL
        ELSE SAFE_CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'level_number') AS INT64) + 1
      END AS level_number_1b,

      SAFE_CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'number_of_successful_puzzles') AS INT64) AS number_of_successful_puzzles,
      (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'success_or_failure') AS success_or_failure,
      event_name,

      -- Funnel stage ordering (kept from prior version)
      CASE event_name
        WHEN 'session_start' THEN 0
        WHEN 'download_completed' THEN 1
        WHEN 'tapped_start' THEN 2
        WHEN 'selected_level' THEN 3
        WHEN 'puzzle_completed' THEN 4
        WHEN 'level_completed' THEN 5
        ELSE -1
      END AS funnel_stage,

      -- GA4 event_date is yyyymmdd string; parse once and use as DATE everywhere
      PARSE_DATE('%Y%m%d', event_date) AS event_dt,

      -- Keep raw event_date string too if you still want it
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

  -- ----------------------------------------------------------------------
  -- 2) Join language max level reference
  -- ----------------------------------------------------------------------
  joined_events AS (
    SELECT
      a.*,
      b.max_level AS max_game_level
    FROM all_events a
    LEFT JOIN `dataexploration-193817.user_data.language_max_level` b
      ON a.app_language = b.app_language
  ),

  -- ----------------------------------------------------------------------
  -- 3) Aggregate to user grain:
  --    - LA date: first qualifying level_completed (any level)
  --    - RA date:
  --       * exact: first qualifying level_completed at level 25 (1-based)
  --       * fallback: if exact missing but max_user_level >= 26,
  --                   first qualifying level_completed at level >= 26
  --    - max_user_level: max qualifying completed level (1-based)
  --    - first_event_date: earliest event_dt observed for the user
  -- ----------------------------------------------------------------------
  aggregated AS (
    SELECT
      cr_user_id,
      country,
      app_language,

      ARRAY_AGG(user_pseudo_id ORDER BY event_dt LIMIT 1)[OFFSET(0)] AS user_pseudo_id,

      MIN(first_open) AS first_open,

      -- Earliest observed event date for the user (stabilizes days_to_ra)
      MIN(event_dt) AS first_event_date,

      ARRAY_AGG(hostname ORDER BY event_dt LIMIT 1)[OFFSET(0)] AS hostname,
      MAX(max_game_level) AS max_game_level,

      -- LA: first qualifying level_completed anywhere (>= 3 successful puzzles)
      MIN(CASE
        WHEN event_name = 'level_completed'
         AND number_of_successful_puzzles >= 3
         AND level_number_1b IS NOT NULL
        THEN event_dt
      END) AS la_date,

      -- RA exact: first qualifying completion at level 25 (1-based)
      MIN(CASE
        WHEN event_name = 'level_completed'
         AND number_of_successful_puzzles >= 3
         AND level_number_1b = 25
        THEN event_dt
      END) AS ra_date_exact,

      -- RA fallback: first qualifying completion AFTER level 25 => level >= 26 (1-based)
      MIN(CASE
        WHEN event_name = 'level_completed'
         AND number_of_successful_puzzles >= 3
         AND level_number_1b >= 26
        THEN event_dt
      END) AS ra_date_fallback,

      -- Max completed level (1-based) from qualifying level_completed events
      MAX(CASE
        WHEN event_name = 'level_completed'
         AND number_of_successful_puzzles >= 3
         AND level_number_1b IS NOT NULL
        THEN level_number_1b
        ELSE 0
      END) AS max_user_level,

      COUNTIF(event_name = 'level_completed'
        AND number_of_successful_puzzles >= 3
        AND level_number_1b IS NOT NULL) AS level_completed_count,

      COUNTIF(event_name = 'puzzle_completed') AS puzzle_completed_count,
      COUNTIF(event_name = 'selected_level') AS selected_level_count,
      COUNTIF(event_name = 'tapped_start') AS tapped_start_count,
      COUNTIF(event_name = 'download_completed') AS download_completed_count,

      MAX(funnel_stage) AS furthest_stage,
      ARRAY_AGG(event_name ORDER BY funnel_stage DESC LIMIT 1)[OFFSET(0)] AS furthest_event

    FROM joined_events
    GROUP BY cr_user_id, country, app_language
  ),

  -- ----------------------------------------------------------------------
  -- 4) Apply RA date fallback logic at the user grain
  -- ----------------------------------------------------------------------
  aggregated_with_ra AS (
    SELECT
      a.*,

      -- Final RA date:
      --   1) Use exact level 25 completion if present
      --   2) Else if max_user_level >= 26, use earliest completion at level >= 26
      --   3) Else NULL
      CASE
        WHEN a.ra_date_exact IS NOT NULL THEN a.ra_date_exact
        WHEN a.ra_date_exact IS NULL AND a.max_user_level >= 26 THEN a.ra_date_fallback
        ELSE NULL
      END AS ra_date

    FROM aggregated a
  ),

  -- ----------------------------------------------------------------------
  -- 5) Cohort tagging
  -- ----------------------------------------------------------------------
  tagged_cohorts AS (
    SELECT
      a.*,
      cg.cohort_name
    FROM aggregated_with_ra a
    LEFT JOIN `dataexploration-193817.user_data.cr_cohorts` cg
      ON a.cr_user_id = cg.cr_user_id
  ),

  -- ----------------------------------------------------------------------
  -- 6) Last observed event date per user
  -- ----------------------------------------------------------------------
  last_events AS (
    SELECT
      cr_user_id,
      MAX(event_dt) AS last_event_date
    FROM all_events
    GROUP BY cr_user_id
  ),

  -- ----------------------------------------------------------------------
  -- 7) Sessionization for engagement metrics
  --    Session boundary rule: new session if > 120 seconds since prior event
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
      sd.cr_user_id,
      COUNT(*) AS session_count,

      -- matches your current output name
      (SELECT COUNT(*) FROM ordered_events oe WHERE oe.cr_user_id = sd.cr_user_id) AS engagement_event_count,

      ROUND(SUM(session_duration_sec) / 60.0, 1) AS total_time_minutes,
      ROUND(AVG(session_duration_sec) / 60.0, 1) AS avg_session_length_minutes
    FROM session_durations sd
    GROUP BY sd.cr_user_id
  ),

  -- ----------------------------------------------------------------------
  -- 8) Attribution flags from upstream table
  -- ----------------------------------------------------------------------
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

-- ----------------------------------------------------------------------
-- Final output
-- ----------------------------------------------------------------------
SELECT
  a.user_pseudo_id,
  a.cr_user_id,
  a.first_open,
  a.first_event_date,  -- useful for debugging / validation
  a.country,
  a.app_language,
  a.cohort_name,

  -- App labeling based on hostname
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

  -- Use the earlier of first_open and first_event_date to avoid 0/negative artifacts
  CASE
    WHEN a.ra_date IS NOT NULL THEN DATE_DIFF(a.ra_date, LEAST(a.first_open, a.first_event_date), DAY) + 1
    ELSE NULL
  END AS days_to_ra,

  a.furthest_event,

  -- Game progress completion percentage
  SAFE_DIVIDE(a.max_user_level, a.max_game_level) * 100 AS gpc,

  COALESCE(s.engagement_event_count, 0) AS engagement_event_count,
  COALESCE(s.total_time_minutes, 0) AS total_time_minutes,
  COALESCE(s.avg_session_length_minutes, 0) AS avg_session_length_minutes,

  le.last_event_date,
  DATE_DIFF(le.last_event_date, LEAST(a.first_open, a.first_event_date), DAY) AS active_span,

  -- Flags:
  -- LA = reached any completed level (>= 1 in 1-based system)
  CASE WHEN a.max_user_level >= 1 THEN 1 ELSE 0 END AS la_flag,

  -- RA = reached level 25 or above (1-based)
  CASE WHEN a.max_user_level >= 25 THEN 1 ELSE 0 END AS ra_flag,

  -- "GC" = reached >=90% of max game level
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