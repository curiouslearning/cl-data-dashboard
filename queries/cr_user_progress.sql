/* ===============================================================================
CR_USER_PROGRESS

Unified per-user progress table for Feed the Monster gameplay.

This table aggregates GA4 event data to a single row per user and provides:

• Normalized level progression (1-based levels)
• LA (Level Achieved) and RA (Reader Acquired) milestone dates
• Stable days_to_ra calculation
• Game completion metrics
• Engagement session metrics
• Cohort tagging
• Attribution flags
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

    CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open,

    geo.country AS country,

    LOWER(REGEXP_EXTRACT(
      (SELECT value.string_value
       FROM UNNEST(event_params)
       WHERE key = 'page_location'),
      r'[?&]cr_lang=([^&]+)'
    )) AS app_language,

    SAFE_CAST(
      (SELECT value.int_value
       FROM UNNEST(event_params)
       WHERE key = 'level_number')
      AS INT64
    ) AS level_number_raw,

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

    PARSE_DATE('%Y%m%d', event_date) AS event_dt,
    event_timestamp,

    device.web_info.hostname AS hostname

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

    MIN(CASE
          WHEN event_name = 'level_completed'
           AND number_of_successful_puzzles >= 3
           AND level_number_1b IS NOT NULL
          THEN event_dt
        END) AS la_date,

    MIN(CASE
          WHEN event_name = 'level_completed'
           AND number_of_successful_puzzles >= 3
           AND level_number_1b = 25
          THEN event_dt
        END) AS ra_date_exact,

    MIN(CASE
          WHEN event_name = 'level_completed'
           AND number_of_successful_puzzles >= 3
           AND level_number_1b >= 26
          THEN event_dt
        END) AS ra_date_fallback,

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
-- 6) Last event date
-- ----------------------------------------------------------------------
last_events AS (
  SELECT
    cr_user_id,
    MAX(event_dt) AS last_event_date
  FROM all_events
  GROUP BY cr_user_id
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

  CASE
    WHEN a.ra_date IS NOT NULL
      THEN DATE_DIFF(a.ra_date,
                     LEAST(a.first_open, a.first_event_date),
                     DAY) + 1
    ELSE NULL
  END AS days_to_ra,

  a.furthest_event,

  SAFE_DIVIDE(a.max_user_level, a.max_game_level) * 100 AS gpc,

  le.last_event_date,
  DATE_DIFF(le.last_event_date,
            LEAST(a.first_open, a.first_event_date),
            DAY) AS active_span,

  CASE WHEN a.max_user_level >= 1 THEN 1 ELSE 0 END AS la_flag,
  CASE WHEN a.max_user_level >= 25 THEN 1 ELSE 0 END AS ra_flag,

  CASE
    WHEN a.max_user_level >= 1
     AND SAFE_DIVIDE(a.max_user_level, a.max_game_level) * 100 >= 90
    THEN 1 ELSE 0
  END AS gc_flag,

  1 AS lr_flag

FROM tagged_cohorts a
LEFT JOIN last_events le
  ON a.cr_user_id = le.cr_user_id

ORDER BY max_user_level DESC;