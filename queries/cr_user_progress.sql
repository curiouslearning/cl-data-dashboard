/* ===============================================================================
CR_USER_PROGRESS

Unified per-user progress table for Feed the Monster gameplay.

This table aggregates GA4 event data to a single row per user and provides:
• Normalized level progression (1-based levels)
• LA (Level Achieved) and RA (Reader Acquired) milestone dates
• Stable days_to_ra calculation
• Game completion metrics
• Engagement session metrics (sessions, event count, time)
• Cohort tagging
• Attribution flags (from upstream cr_app_launch)
• App labeling (CR vs <prefix>-standalone builds)

App labeling logic:
- Hostnames matching:
    <prefix>_cr-ftm-standalone.androidplatform.net
  are labeled:
    <prefix>-standalone
- All other supported hostnames are labeled:
    CR

Level normalization:
- FTM events store first level as 0
- We normalize to 1-based numbering (level_number_raw + 1)

RA logic:
- Exact: first completion of level 25 (1-based)
- Fallback: if max_user_level >= 26, use first completion at level >= 26

days_to_ra:
- Uses the earlier of first_open and first_event_date
  to avoid negative or zero artifacts.

================================================================================ */

CREATE OR REPLACE TABLE `dataexploration-193817.user_data.cr_user_progress` AS
WITH

-- ----------------------------------------------------------------------
-- 1) Pull relevant events and normalize level numbering
-- ----------------------------------------------------------------------
all_events AS (
  SELECT
    user_pseudo_id,

    (SELECT value.string_value
     FROM UNNEST(event_params)
     WHERE key = 'cr_user_id') AS cr_user_id,

    -- First touch date from GA4 user_first_touch_timestamp
    CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open,

    geo.country AS country,

    -- Language extracted from page_location param
    LOWER(REGEXP_EXTRACT(
      (SELECT value.string_value
       FROM UNNEST(event_params)
       WHERE key = 'page_location'),
      r'[?&]cr_lang=([^&]+)'
    )) AS app_language,

    -- Raw level_number from event params (FTM quirk: 0 = first level)
    SAFE_CAST(
      (SELECT value.int_value
       FROM UNNEST(event_params)
       WHERE key = 'level_number')
      AS INT64
    ) AS level_number_raw,

    -- Normalized 1-based level number used everywhere downstream
    CASE
      WHEN SAFE_CAST(
             (SELECT value.int_value
              FROM UNNEST(event_params)
              WHERE key = 'level_number') AS INT64
           ) IS NULL THEN NULL
      ELSE SAFE_CAST(
             (SELECT value.int_value
              FROM UNNEST(event_params)
              WHERE key = 'level_number') AS INT64
           ) + 1
    END AS level_number_1b,

    SAFE_CAST(
      (SELECT value.int_value
       FROM UNNEST(event_params)
       WHERE key = 'number_of_successful_puzzles')
      AS INT64
    ) AS number_of_successful_puzzles,

    (SELECT value.string_value
     FROM UNNEST(event_params)
     WHERE key = 'success_or_failure') AS success_or_failure,

    event_name,

    -- Funnel stage ordering
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
     AND (SELECT value.string_value
          FROM UNNEST(event_params)
          WHERE key = 'page_location')
         LIKE '%https://feedthemonster.curiouscontent.org%')

    OR REGEXP_CONTAINS(
         device.web_info.hostname,
         r'^(.+)_cr-ftm-standalone\.androidplatform\.net$'
       )
  )

  AND CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE)
      BETWEEN '2021-01-01' AND CURRENT_DATE()

  AND (SELECT value.string_value
       FROM UNNEST(event_params)
       WHERE key = 'cr_user_id') IS NOT NULL

  AND (SELECT value.string_value
       FROM UNNEST(event_params)
       WHERE key = 'cr_user_id') != ''
),

-- ----------------------------------------------------------------------
-- 2) Join max game level reference
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
-- 3) Aggregate to user grain
-- ----------------------------------------------------------------------
aggregated AS (
  SELECT
    cr_user_id,
    country,
    app_language,

    ARRAY_AGG(user_pseudo_id ORDER BY event_dt LIMIT 1)[OFFSET(0)] AS user_pseudo_id,
    MIN(first_open) AS first_open,
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
-- 4) Apply RA fallback
-- ----------------------------------------------------------------------
aggregated_with_ra AS (
  SELECT
    a.*,
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
  a.first_event_date,
  a.country,
  a.app_language,
  a.cohort_name,

  -- App labeling based on hostname
  CASE
    WHEN REGEXP_CONTAINS(a.hostname,
         r'^(.+)_cr-ftm-standalone\.androidplatform\.net$')
      THEN REGEXP_EXTRACT(a.hostname,
           r'^(.+)_cr-ftm-standalone\.androidplatform\.net$')
           || '-standalone'
    ELSE 'CR'
  END AS app,

  a.max_user_level,
  a.max_game_level,
  a.la_date,
  a.ra_date,

  -- Use the earlier of first_open and first_event_date to avoid 0/negative artifacts
  CASE
    WHEN a.ra_date IS NOT NULL
      THEN DATE_DIFF(a.ra_date, LEAST(a.first_open, a.first_event_date), DAY) + 1
    ELSE NULL
  END AS days_to_ra,

  a.furthest_event,

  -- Game progress completion percentage
  SAFE_DIVIDE(a.max_user_level, a.max_game_level) * 100 AS gpc,

  COALESCE(s.session_count, 0) AS session_count,
  COALESCE(s.engagement_event_count, 0) AS engagement_event_count,
  COALESCE(s.total_time_minutes, 0) AS total_time_minutes,
  COALESCE(s.avg_session_length_minutes, 0) AS avg_session_length_minutes,

  le.last_event_date,
  DATE_DIFF(le.last_event_date, LEAST(a.first_open, a.first_event_date), DAY) AS active_span,

  -- Flags
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