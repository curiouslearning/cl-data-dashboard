/*
===============================================================================
Table: ftm_event_timeline_all

Purpose
-------
Full event timeline rebuild for Feed the Monster gameplay events (web + standalone)
plus container-app attribution audit events (attribution_status).

Key points
----------
- Gameplay events are filtered to FTM web + standalone hostnames (existing behavior).
- attribution_status events are sourced separately from the container app
  (app_info.id = 'org.curiouslearning.container') and UNION ALL into the timeline.
- attribution_status rows carry extracted attribution fields for dashboard audits.
- row_id is stable for gameplay events and collision-resistant for attribution rows.
===============================================================================
*/

CREATE OR REPLACE TABLE `dataexploration-193817.user_data.ftm_event_timeline_all`
AS
WITH
  events_gameplay AS (
    SELECT
      PARSE_DATE('%Y%m%d', event_date) AS event_date,
      TIMESTAMP_MICROS(event_timestamp) AS event_ts,
      event_name,

      SAFE_CAST((
        SELECT value.int_value
        FROM UNNEST(event_params)
        WHERE key = 'level_number'
      ) AS INT64) + 1 AS level_number,

      SAFE_CAST((
        SELECT value.int_value
        FROM UNNEST(event_params)
        WHERE key = 'puzzle_number'
      ) AS INT64) AS puzzle_number,

      SAFE_CAST((
        SELECT value.int_value
        FROM UNNEST(event_params)
        WHERE key = 'number_of_successful_puzzles'
      ) AS INT64) AS number_of_successful_puzzles,

      (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'success_or_failure') AS raw_success_or_failure,

      geo.country AS country,

      LOWER(REGEXP_EXTRACT((
        SELECT value.string_value
        FROM UNNEST(event_params)
        WHERE key = 'page_location'
      ), r'[?&]cr_lang=([^&]+)')) AS app_language,

      (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'ftm_language') AS ftm_language,
      (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'version_number') AS app_version,
      (SELECT value.double_value FROM UNNEST(event_params) WHERE key = 'json_version_number') AS json_version,

      device.web_info.hostname AS hostname,

      CASE
        WHEN device.web_info.hostname = 'appassets.androidplatform.net' THEN 'WBS-standalone'
        WHEN REGEXP_CONTAINS(device.web_info.hostname, r'^([a-z0-9_-]+)-ftm-standalone\.androidplatform\.net$')
          THEN REGEXP_EXTRACT(device.web_info.hostname, r'^([a-z0-9_-]+)-ftm-standalone\.androidplatform\.net$') || '-standalone'
        ELSE 'CR'
      END AS app,

      user_pseudo_id,

      (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'cr_user_id') AS cr_user_id,

      CAST(NULL AS STRING) AS attribution_status,
      CAST(NULL AS STRING) AS attribution_referral_url,
      CAST(NULL AS STRING) AS attribution_source,
      CAST(NULL AS STRING) AS attribution_campaign_id,
      CAST(NULL AS STRING) AS attribution_cached_attribution,
      CAST(NULL AS STRING) AS attribution_raw_referrer_url,
      CAST(NULL AS INT64)  AS attribution_attempt_count,
      CAST(NULL AS INT64)  AS attribution_max_retries

    FROM `ftm-b9d99.analytics_159643920.events_*`
    WHERE event_name IN (
      'session_start',
      'session_end',
      'download_completed',
      'tapped_start',
      'selected_level',
      'puzzle_completed',
      'level_completed'
    )
    AND (
      (
        device.web_info.hostname LIKE 'feedthemonster.curiouscontent.org%'
        AND (
          SELECT value.string_value
          FROM UNNEST(event_params)
          WHERE key = 'page_location'
        ) LIKE '%https://feedthemonster.curiouscontent.org%'
      )
      OR REGEXP_CONTAINS(device.web_info.hostname, r'^[a-z0-9_-]+-ftm-standalone\.androidplatform\.net$')
      OR device.web_info.hostname = 'appassets.androidplatform.net'
    )
  ),

  events_attrib AS (
    SELECT
      PARSE_DATE('%Y%m%d', event_date) AS event_date,
      TIMESTAMP_MICROS(event_timestamp) AS event_ts,
      event_name,

      CAST(NULL AS INT64) AS level_number,
      CAST(NULL AS INT64) AS puzzle_number,
      CAST(NULL AS INT64) AS number_of_successful_puzzles,
      CAST(NULL AS STRING) AS raw_success_or_failure,

      geo.country AS country,
      CAST(NULL AS STRING) AS app_language,
      CAST(NULL AS STRING) AS ftm_language,
      CAST(NULL AS STRING) AS app_version,
      CAST(NULL AS FLOAT64) AS json_version,

      CAST(NULL AS STRING) AS hostname,
      'CR-container' AS app,

      user_pseudo_id,
      (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'cr_user_id') AS cr_user_id,

      (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'status') AS attribution_status,
      (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'referral_url') AS attribution_referral_url,
      (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'source') AS attribution_source,
      (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'campaign_id') AS attribution_campaign_id,
      (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'cached_attribution') AS attribution_cached_attribution,
      (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'raw_referrer_url') AS attribution_raw_referrer_url,
      (SELECT value.int_value    FROM UNNEST(event_params) WHERE key = 'attempt_count') AS attribution_attempt_count,
      (SELECT value.int_value    FROM UNNEST(event_params) WHERE key = 'max_retries') AS attribution_max_retries

    FROM `ftm-b9d99.analytics_159643920.events_*`
    WHERE event_name = 'attribution_status'
      AND app_info.id = 'org.curiouslearning.container'
  ),

  events AS (
    SELECT * FROM events_gameplay
    UNION ALL
    SELECT * FROM events_attrib
  ),

  normalized AS (
    SELECT
      *,
      CASE
        WHEN event_name = 'level_completed'
          AND SAFE_CAST(number_of_successful_puzzles AS INT64) >= 3
        THEN 'success'
        ELSE raw_success_or_failure
      END AS success_or_failure
    FROM events
  ),

  deduped_levels AS (
    SELECT
      ARRAY_AGG(n
        ORDER BY
          CASE WHEN n.success_or_failure = 'success' THEN 1 ELSE 2 END,
          n.event_ts ASC
        LIMIT 1
      )[OFFSET(0)] AS row
    FROM normalized n
    WHERE n.event_name = 'level_completed'
    GROUP BY n.cr_user_id, n.level_number
  ),

  combined AS (
    SELECT * FROM normalized WHERE event_name != 'level_completed'
    UNION ALL
    SELECT row.* FROM deduped_levels
  ),

  success_intervals AS (
    SELECT
      cr_user_id,
      event_ts,
      level_number,
      ROUND(
        TIMESTAMP_DIFF(
          event_ts,
          LAG(event_ts) OVER (PARTITION BY cr_user_id ORDER BY event_ts),
          SECOND
        ) / 60.0,
        2
      ) AS minutes_since_prev_success
    FROM combined
    WHERE event_name = 'level_completed'
      AND success_or_failure = 'success'
  ),

  final_with_spans AS (
    SELECT
      c.*,
      si.minutes_since_prev_success
    FROM combined c
    LEFT JOIN success_intervals si
    USING (cr_user_id, event_ts, level_number)
  )

SELECT
  TO_HEX(MD5(CONCAT(
    CAST(UNIX_MICROS(event_ts) AS STRING), '|',
    COALESCE(cr_user_id, ''), '|',
    COALESCE(event_name, ''), '|',
    CAST(COALESCE(level_number, -1) AS STRING), '|',
    CAST(COALESCE(puzzle_number, -1) AS STRING), '|',
    CASE
      WHEN event_name = 'attribution_status' THEN CONCAT(
        COALESCE(attribution_status, ''), '|',
        COALESCE(attribution_source, ''), '|',
        COALESCE(attribution_campaign_id, ''), '|',
        CAST(COALESCE(attribution_attempt_count, -1) AS STRING), '|',
        CAST(COALESCE(attribution_max_retries, -1) AS STRING)
      )
      ELSE ''
    END
  ))) AS row_id,

  event_date,
  event_ts,
  event_name,
  level_number,
  puzzle_number,
  number_of_successful_puzzles,
  success_or_failure,
  minutes_since_prev_success,
  country,
  app_language,
  ftm_language,
  hostname,

  CASE
    WHEN hostname = 'appassets.androidplatform.net' THEN 'WBS-standalone'
    WHEN REGEXP_CONTAINS(hostname, r'^([a-z0-9_-]+)-ftm-standalone\.androidplatform\.net$')
      THEN REGEXP_EXTRACT(hostname, r'^([a-z0-9_-]+)-ftm-standalone\.androidplatform\.net$') || '-standalone'
    ELSE app
  END AS app,

  user_pseudo_id,
  cr_user_id,

  attribution_status,
  attribution_referral_url,
  attribution_source,
  attribution_campaign_id,
  attribution_cached_attribution,
  attribution_raw_referrer_url,
  attribution_attempt_count,
  attribution_max_retries

FROM final_with_spans
WHERE cr_user_id IS NOT NULL
ORDER BY cr_user_id, event_ts;
