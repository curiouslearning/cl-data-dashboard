/*
Gets all Learners Acquired.  May have multiple entries for learners
who play multiple times on the same level
*/


SELECT
  event_name,
  PARSE_DATE('%Y%m%d', event_date) as event_date ,
  user_pseudo_id,
  device.language AS device_language,
  LOWER(REGEXP_EXTRACT(app_info.id, r'feedthemonster(.*)')) AS app_language,
  geo.country AS country,
  CAST(SUBSTR(params.value.string_value, (STRPOS(params.value.string_value, '_') + 1)) AS INT64) AS level,
  CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open,
  app_info.id AS appinfo

FROM (
  SELECT
    *
  FROM
    `ftm-b9d99.analytics_159643920.events_20*`
  UNION ALL
  SELECT
    *
  FROM
    `ftm-afrikaans.analytics_177200876.events_20*`
  UNION ALL
  SELECT
    *
  FROM
    `ftm-hindi.analytics_174638281.events_20*`
  UNION ALL
  SELECT
    *
  FROM
    `ftm-brazilian-portuguese.analytics_161789655.events_20*`
  UNION ALL
  SELECT
    *
  FROM
    `ftm-english.analytics_152408808.events_20*`
  UNION ALL
  SELECT
    *
  FROM
    `ftm-french.analytics_173880465.events_20*`
  UNION ALL
  SELECT
    *
  FROM
    `ftm-isixhosa.analytics_180747962.events_20*`
  UNION ALL
  SELECT
    *
  FROM
    `ftm-kinayrwanda.analytics_177922191.events_20*`
  UNION ALL
  SELECT
    *
  FROM
    `ftm-oromo.analytics_167539175.events_20*`
  UNION ALL
  SELECT
    *
  FROM
    `ftm-swahili.analytics_160694316.events_20*`
  UNION ALL
  SELECT
    *
  FROM
    `ftm-somali.analytics_159630038.events_20*`
  UNION ALL
  SELECT
    *
  FROM
    `ftm-sepedi.analytics_180755978.events_20*`
  UNION ALL
  SELECT
    *
  FROM
    `ftm-zulu.analytics_155849122.events_20*`
  UNION ALL
  SELECT
    *
  FROM
    `ftm-southafricanenglish.analytics_173750850.events_20*`
  UNION ALL
  SELECT
    *
  FROM
    `ftm-spanish.analytics_158656398.events_20*` )
CROSS JOIN
  UNNEST(event_params) AS params
WHERE
  event_name = 'GamePlay'
  AND params.key = 'action'
  AND params.value.string_value LIKE 'LevelSuccess%'
  AND PARSE_DATE('%Y%m%d', event_date) BETWEEN '2021-01-01'
  AND CURRENT_DATE() ;