-- Step 1: Base User Metadata
WITH
  base_data AS (
    SELECT
      cr_user_id_params.value.string_value AS cr_user_id,
      user_pseudo_id,
      geo.country AS country,
      device.category AS device_category,
      device.operating_system AS device_operating_system,
      device.mobile_brand_name AS device_mobile_brand_name,
      device.mobile_model_name AS device_mobile_model_name,
      device.mobile_marketing_name AS device_mobile_marketing_name,
      traffic_source.medium AS traffic_source_medium,
      traffic_source.source AS traffic_source,
      LOWER(REGEXP_EXTRACT(language_params.value.string_value, '[?&]cr_lang=([^&]+)')) AS app_language,
      CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open
    FROM
      `ftm-b9d99.analytics_159643920.events_20*` AS A,
      UNNEST(event_params) AS language_params,
      UNNEST(event_params) AS cr_user_id_params
    WHERE
      app_info.id = 'org.curiouslearning.container'
      AND language_params.value.string_value LIKE 'https://feedthemonster.curiouscontent.org%'
      AND event_name = 'app_launch'
      AND language_params.key = 'web_app_url'
      AND cr_user_id_params.key = 'cr_user_id'
      AND CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) BETWEEN '2021-01-01'
      AND CURRENT_DATE()
    GROUP BY
      1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
  ),

-- Step 2: Ordered Events with Extracted cr_user_id
  ordered_events AS (
    SELECT
      TIMESTAMP_MICROS(event_timestamp) AS event_ts,
      event_timestamp,
      (
        SELECT
          value.string_value
        FROM
          UNNEST(event_params)
        WHERE
          KEY = 'cr_user_id'
      ) AS cr_user_id
    FROM
      `ftm-b9d99.analytics_159643920.events_*`
    WHERE
      _TABLE_SUFFIX BETWEEN '20210101' AND FORMAT_DATE('%Y%m%d', CURRENT_DATE())
      AND EXISTS (
        SELECT 1
        FROM UNNEST(event_params) AS p
        WHERE p.key = 'cr_user_id'
      )
  ),

-- Step 3: Add Row Number per cr_user_id for Ordered Deltas
  numbered_events AS (
    SELECT
      *,
      ROW_NUMBER() OVER (PARTITION BY cr_user_id ORDER BY event_timestamp) AS rn
    FROM
      ordered_events
  ),

-- Step 4: Calculate Time Differences Between Events
  with_deltas AS (
    SELECT
      *,
      LAG(event_ts) OVER (PARTITION BY cr_user_id ORDER BY rn) AS prev_event_ts,
      TIMESTAMP_DIFF(event_ts, LAG(event_ts) OVER (PARTITION BY cr_user_id ORDER BY rn), SECOND) AS seconds_since_last
    FROM
      numbered_events
  ),

-- Step 5: Mark New Sessions Based on 2-Minute Gap
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

-- Step 6: Create Session IDs via Running Total of New Sessions
  sessionized AS (
    SELECT
      *,
      SUM(is_new_session) OVER (PARTITION BY cr_user_id ORDER BY rn) AS session_id
    FROM
      marked_sessions
  ),

-- Step 7: Calculate Session Durations per cr_user_id
  session_durations AS (
    SELECT
      cr_user_id,
      session_id,
      TIMESTAMP_DIFF(MAX(event_ts), MIN(event_ts), SECOND) AS session_duration_sec
    FROM
      sessionized
    GROUP BY
      cr_user_id, session_id
  ),

-- Step 8: Aggregate Stats per cr_user_id
  session_stats AS (
    SELECT
      cr_user_id,
      COUNT(*) AS cl_session_count,
      ROUND(SUM(session_duration_sec) / 60.0, 1) AS total_engagement_minutes
    FROM
      session_durations
    GROUP BY
      cr_user_id
  )

-- Step 9: Final Join with session_stats and cr_user_progress
SELECT
  b.*,
  s.cl_session_count,
  s.total_engagement_minutes,
  COALESCE(p.app_version, 'unknown') AS app_version
FROM
  base_data b
LEFT JOIN
  session_stats s
ON
  b.cr_user_id = s.cr_user_id
LEFT JOIN
  `dataexploration-193817.user_data.cr_user_progress` p
ON
  b.cr_user_id = p.cr_user_id
ORDER BY
  total_engagement_minutes DESC
