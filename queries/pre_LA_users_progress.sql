SELECT
  DISTINCT(user_pseudo_id),
  app_info.id AS app_id,
  CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open,
  geo.country AS country,
  LOWER(REGEXP_EXTRACT(app_info.id, r'feedthemonster(.*)')) AS app_language,
  event_name
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
  AND params.value.string_value LIKE 'SegmentSuccess%'
  AND CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) BETWEEN '2021-01-01'
  AND CURRENT_DATE()
UNION ALL (
  WITH
    all_events AS (
    SELECT
      user_pseudo_id,
      "org.curiouslearning.container" AS app_id,
      CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open,
      geo.country AS country,
      LOWER(REGEXP_EXTRACT(app_params.value.string_value, '[?&]cr_lang=([^&]+)')) AS app_language,
      event_name
    FROM
      `ftm-b9d99.analytics_159643920.events_20*` AS ga,
      UNNEST(event_params) AS app_params
    WHERE
      event_name IN ('tapped_start',
        'selected_level',
        'puzzle_completed')
      AND app_params.key = 'page_location'
      AND app_params.value.string_value LIKE '%https://feedthemonster.curiouscontent.org%' )
  SELECT
    a.user_pseudo_id,
    a.app_id,
    a.first_open,
    a.country,
    a.app_language,
    CASE
      WHEN MAX(CASE
        WHEN b.event_name = 'puzzle_completed' THEN 1
      ELSE
      0
    END
      ) = 1 THEN 'puzzle_completed'
      WHEN MAX(CASE
        WHEN b.event_name = 'selected_level' THEN 1
      ELSE
      0
    END
      ) = 1 THEN 'selected_level'
    ELSE
    'tapped_start'
  END
    AS furthest_event
  FROM
    all_events AS a
  LEFT JOIN
    all_events AS b
  ON
    a.user_pseudo_id = b.user_pseudo_id
  GROUP BY
    a.user_pseudo_id,
    a.app_id,
    a.first_open,
    a.country,
    a.app_language)