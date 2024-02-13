/*
Gets all Learners Acquired.  May have multiple entries for learners
who play multiple times on the same level
*/

SELECT
  ga.event_name,
  PARSE_DATE('%Y%m%d', event_date) as event_date,
   (ga.user_pseudo_id) AS user_pseudo_id,
  device.language AS device_language,
  LOWER(REGEXP_EXTRACT(app_params.value.string_value, '[?&]cr_lang=([^&]+)')) AS app_language,
  geo.country AS country,
  (level_params.value.int_value + 1) AS level,  /* CR levels are zero indexed */
   CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open,
  'org.curiouslearning.container' AS appinfo,
 
FROM
  `ftm-b9d99.analytics_159643920.events_20*` AS ga,
  UNNEST(event_params) AS level_params,
  UNNEST(event_params) AS app_params,
  UNNEST(event_params) AS success_params
WHERE
  ga.event_name = 'level_completed'
  AND level_params.key = 'level_number'
  AND app_params.key = 'page_location'
  and  app_params.value.string_value  like   '%https://feedthemonster.curiouscontent.org%'

  AND success_params.key = 'success_or_failure'
  AND success_params.value.string_value = 'success'
  AND PARSE_DATE('%Y%m%d', event_date) BETWEEN '2021-01-01'
  AND CURRENT_DATE()

 ORDER BY event_date DESC