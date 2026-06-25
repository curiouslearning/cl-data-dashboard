/*
================================================================================
Table: cr_app_launch

Purpose
-------
App launch table for Feed the Monster launched from the container app.

Grain
-----
One row per:
  (cr_user_id, user_pseudo_id, country, app_language, first_open)
===============================================================================
*/

CREATE OR REPLACE TABLE `dataexploration-193817.user_data.cr_app_launch`
AS
WITH
  base_events AS (
    SELECT
      (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'cr_user_id') AS cr_user_id,
      user_pseudo_id,
      geo.country AS country,
      LOWER(REGEXP_EXTRACT(
        (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'web_app_url'),
        r'[?&]cr_lang=([^&]+)'
      )) AS app_language,
      TIMESTAMP_MICROS(event_timestamp) AS launch_ts,
      CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open
    FROM `ftm-b9d99.analytics_159643920.events_20*`
    WHERE app_info.id = 'org.curiouslearning.container'
      AND event_name = 'app_launch'
      AND (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'web_app_url')
            LIKE 'https://feedthemonster.curiouscontent.org%'
      AND (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'cr_user_id') IS NOT NULL
      AND CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE)
            BETWEEN '2021-01-01' AND CURRENT_DATE()
  ),

  base_data AS (
    SELECT
      cr_user_id,
      user_pseudo_id,
      country,
      app_language,
      first_open,
      MIN(launch_ts) AS first_launch_ts
    FROM base_events
    GROUP BY
      cr_user_id,
      user_pseudo_id,
      country,
      app_language,
      first_open
  )

SELECT
  b.cr_user_id,
  b.user_pseudo_id,
  b.country,
  b.app_language,
  b.first_open,
  b.first_launch_ts,
  cg.cohort_name
FROM base_data b
LEFT JOIN `dataexploration-193817.user_data.cr_cohorts` cg
  ON b.cr_user_id = cg.cr_user_id
ORDER BY first_open DESC;