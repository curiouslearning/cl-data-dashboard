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

Device attributes are taken from the user's earliest app_launch event within
that group, so they do not add to the grain (a user who upgrades their OS or
switches handsets still produces a single row).

study_user_id is the first non-null value across the user's launches, and is
NULL for users not enrolled in a study.

source / campaign_id (restored 2026-08-26) are read from user_properties, the
same place the historical attribution query read them -- NOT from a marketing
table as the removed pre-2026-06 columns did. Unlike that query, users WITHOUT
attribution are kept (the value is simply NULL) so this table's grain is
unchanged. Attribution is sparse: ~0.8% of users carry it.
===============================================================================
*/

CREATE OR REPLACE TABLE `dataexploration-193817.user_data.cr_app_launch`
AS
WITH
  base_events AS (
    SELECT
      (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'cr_user_id') AS cr_user_id,
      (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'study_user_id') AS study_user_id,
      -- Attribution lives in user_properties (NOT event_params), matching the
      -- historical attribution query. The IS NOT NULL guard inside the subquery
      -- skips property rows whose string_value is unset for this event.
      --
      -- Normalization (NOT in the historical query): some senders emit the
      -- literal string 'null', and some campaign ids arrive with stray
      -- whitespace. Both are mapped to a real NULL / trimmed value so that
      -- "source IS NOT NULL" is a trustworthy attributed-or-not test. Drop the
      -- NULLIF/TRIM wrapper if raw passthrough is ever wanted instead.
      NULLIF(NULLIF(TRIM(
        (SELECT up.value.string_value FROM UNNEST(user_properties) up
          WHERE up.key = 'source' AND up.value.string_value IS NOT NULL)
      ), 'null'), '') AS source,
      NULLIF(NULLIF(TRIM(
        (SELECT up.value.string_value FROM UNNEST(user_properties) up
          WHERE up.key = 'campaign_id' AND up.value.string_value IS NOT NULL)
      ), 'null'), '') AS campaign_id,
      user_pseudo_id,
      geo.country AS country,
      device.category AS device_category,
      device.mobile_brand_name AS device_mobile_brand_name,
      device.mobile_model_name AS device_mobile_model_name,
      device.mobile_marketing_name AS device_mobile_marketing_name,
      device.operating_system_version AS android_version,
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
      MIN(launch_ts) AS first_launch_ts,
      -- Device attributes as of the first launch, kept together so all five
      -- fields describe the same event rather than being mixed across events.
      ARRAY_AGG(
        STRUCT(
          device_category,
          device_mobile_brand_name,
          device_mobile_model_name,
          device_mobile_marketing_name,
          android_version
        )
        ORDER BY launch_ts
        LIMIT 1
      )[SAFE_OFFSET(0)] AS first_device,
      -- study_user_id is only stamped on some of a study user's launches, so take
      -- the first NON-NULL value rather than the value at the first launch. No
      -- cr_user_id has ever carried two different study_user_ids, so this is
      -- unambiguous. NULL for the vast majority of users, who are not in a study.
      ARRAY_AGG(study_user_id IGNORE NULLS ORDER BY launch_ts LIMIT 1)[SAFE_OFFSET(0)]
        AS study_user_id,
      -- Same first-non-null treatment: attribution is stamped on only a fraction
      -- of launches, and no user has ever carried two different values for either.
      ARRAY_AGG(source IGNORE NULLS ORDER BY launch_ts LIMIT 1)[SAFE_OFFSET(0)]
        AS source,
      ARRAY_AGG(campaign_id IGNORE NULLS ORDER BY launch_ts LIMIT 1)[SAFE_OFFSET(0)]
        AS campaign_id
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
  b.study_user_id,
  b.user_pseudo_id,
  b.country,
  b.app_language,
  b.first_open,
  b.first_launch_ts,
  b.first_device.device_category,
  b.first_device.device_mobile_brand_name,
  b.first_device.device_mobile_model_name,
  b.first_device.device_mobile_marketing_name,
  b.first_device.android_version,
  b.source,
  b.campaign_id,
  cg.cohort_name
FROM base_data b
LEFT JOIN `dataexploration-193817.user_data.cr_cohorts` cg
  ON b.cr_user_id = cg.cr_user_id
ORDER BY first_open DESC;
