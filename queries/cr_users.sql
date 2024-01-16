/*
Gets all Learners Acquired.  May have multiple entries for learners
who play multiple times on the same level
*/

SELECT
  ga.event_name,
  PARSE_DATE('%Y%m%d', event_date) as event_date,
  ga.user_pseudo_id AS user_pseudo_id,
  device.language AS device_language,
  language_params.value.string_value AS app_language,
  geo.country AS country,
  (level_params.value.int_value + 1) AS level,  /* CR levels are zero indexed */
  CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open,
  app_info.id AS appinfo
FROM
  `ftm-b9d99.analytics_159643920.events_20*` AS ga,
  UNNEST(event_params) AS level_params,
  UNNEST(event_params) AS success_params,
  UNNEST(event_params) AS language_params
WHERE
  ga.event_name = 'level_completed'
  AND level_params.key = 'level_number'
  AND success_params.key = 'success_or_failure'
  AND success_params.value.string_value = 'success'
  AND language_params.key = 'ftm_language'
  AND PARSE_DATE('%Y%m%d', event_date) BETWEEN '2021-01-01'
  AND CURRENT_DATE()
