SELECT
  DISTINCT (user_pseudo_id),
  first_open,
  country,
  app_language,
  app_id
FROM (
   SELECT #ftm-b9d99 Unity users
    user_pseudo_id,
    geo.country AS country,
    app_info.id AS app_id,
    LOWER(REGEXP_EXTRACT(app_info.id, r'feedthemonster(.*)')) AS app_language,
    CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open
  FROM
    `ftm-b9d99.analytics_159643920.events_20*`
  WHERE
    event_name = 'session_start'
    AND app_info.id LIKE '%feedthemonster%'
  AND  CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) BETWEEN '2021-01-01'
  AND CURRENT_DATE()
  UNION ALL
    SELECT #ftm-b9d99 CR users
    user_pseudo_id,
    geo.country AS country,
    app_info.id AS app_id,
    LOWER(REGEXP_EXTRACT(event_params.value.string_value, '[?&]cr_lang=([^&]+)')) AS app_language,
    CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open
  FROM
    `ftm-b9d99.analytics_159643920.events_20*` as A,
  UNNEST (event_params )as event_params
  WHERE
    app_info.id = 'org.curiouslearning.container'
    and event_params.value.string_value like '%feedthemonster.curiouscontent.org%'
    AND event_name = 'app_launch'
    AND event_params.key = 'web_app_url'
  AND  CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) BETWEEN '2021-01-01'
  AND CURRENT_DATE()
  UNION ALL
  SELECT
    user_pseudo_id,
    geo.country AS country,
    app_info.id AS app_id,
    LOWER(REGEXP_EXTRACT(app_info.id, r'feedthemonster(.*)')) AS app_language,
    CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open
  FROM
    `ftm-afrikaans.analytics_177200876.events_20*`
  WHERE
    event_name = 'session_start'
    AND app_info.id LIKE '%feedthemonster%'
  AND  CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) BETWEEN '2021-01-01'
  AND CURRENT_DATE()
  UNION ALL
  SELECT
    user_pseudo_id,
    geo.country AS country,
    app_info.id AS app_id,
    LOWER(REGEXP_EXTRACT(app_info.id, r'feedthemonster(.*)')) AS app_language,
    CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open
  FROM
    `ftm-hindi.analytics_174638281.events_20*`
  WHERE
    event_name = 'session_start'
    AND app_info.id LIKE '%feedthemonster%'
  AND  CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) BETWEEN '2021-01-01'
  AND CURRENT_DATE()
  UNION ALL
  SELECT
    user_pseudo_id,
    geo.country AS country,
    app_info.id AS app_id,
    LOWER(REGEXP_EXTRACT(app_info.id, r'feedthemonster(.*)')) AS app_language,
    CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open
  FROM
    `ftm-brazilian-portuguese.analytics_161789655.events_20*`
  WHERE
    event_name = 'session_start'
    AND app_info.id LIKE '%feedthemonster%'
  AND  CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) BETWEEN '2021-01-01'
  AND CURRENT_DATE()
  UNION ALL
  SELECT
    user_pseudo_id,
    geo.country AS country,
    app_info.id AS app_id,
    LOWER(REGEXP_EXTRACT(app_info.id, r'feedthemonster(.*)')) AS app_language,
    CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open
  FROM
    `ftm-english.analytics_152408808.events_20*`
  WHERE
    event_name = 'session_start'
    AND app_info.id LIKE '%feedthemonster%'
  AND  CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) BETWEEN '2021-01-01'
  AND CURRENT_DATE()
  UNION ALL
  SELECT
    user_pseudo_id,
    geo.country AS country,
    app_info.id AS app_id,
    LOWER(REGEXP_EXTRACT(app_info.id, r'feedthemonster(.*)')) AS app_language,
    CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open
  FROM
    `ftm-french.analytics_173880465.events_20*`
  WHERE
    event_name = 'session_start'
    AND app_info.id LIKE '%feedthemonster%'
  AND  CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) BETWEEN '2021-01-01'
  AND CURRENT_DATE()
  UNION ALL
  SELECT
    user_pseudo_id,
    geo.country AS country,
    app_info.id AS app_id,
    LOWER(REGEXP_EXTRACT(app_info.id, r'feedthemonster(.*)')) AS app_language,
    CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open
  FROM
    `ftm-isixhosa.analytics_180747962.events_20*`
  WHERE
    event_name = 'session_start'
    AND app_info.id LIKE '%feedthemonster%'
  AND  CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) BETWEEN '2021-01-01'
  AND CURRENT_DATE()
  UNION ALL
  SELECT
    user_pseudo_id,
    geo.country AS country,
    app_info.id AS app_id,
    LOWER(REGEXP_EXTRACT(app_info.id, r'feedthemonster(.*)')) AS app_language,
    CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open
  FROM
    `ftm-kinayrwanda.analytics_177922191.events_20*`
  WHERE
    event_name = 'session_start'
    AND app_info.id LIKE '%feedthemonster%'
  AND  CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) BETWEEN '2021-01-01'
  AND CURRENT_DATE()
  UNION ALL
  SELECT
    user_pseudo_id,
    geo.country AS country,
    app_info.id AS app_id,
    LOWER(REGEXP_EXTRACT(app_info.id, r'feedthemonster(.*)')) AS app_language,
    CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open
  FROM
    `ftm-oromo.analytics_167539175.events_20*`
  WHERE
    event_name = 'session_start'
    AND app_info.id LIKE '%feedthemonster%'
  AND  CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) BETWEEN '2021-01-01'
  AND CURRENT_DATE()
  UNION ALL
  SELECT
    user_pseudo_id,
    geo.country AS country,
    app_info.id AS app_id,
    LOWER(REGEXP_EXTRACT(app_info.id, r'feedthemonster(.*)')) AS app_language,
    CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open
  FROM
    `ftm-swahili.analytics_160694316.events_20*`
  WHERE
    event_name = 'session_start'
    AND app_info.id LIKE '%feedthemonster%'
  AND  CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) BETWEEN '2021-01-01'
  AND CURRENT_DATE()
  UNION ALL
  SELECT
    user_pseudo_id,
    geo.country AS country,
    app_info.id AS app_id,
    LOWER(REGEXP_EXTRACT(app_info.id, r'feedthemonster(.*)')) AS app_language,
    CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open
  FROM
    `ftm-somali.analytics_159630038.events_20*`
  WHERE
    event_name = 'session_start'
    AND app_info.id LIKE '%feedthemonster%'
  AND  CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) BETWEEN '2021-01-01'
  AND CURRENT_DATE()
  UNION ALL
  SELECT
    user_pseudo_id,
    geo.country AS country,
    app_info.id AS app_id,
    LOWER(REGEXP_EXTRACT(app_info.id, r'feedthemonster(.*)')) AS app_language,
    CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open
  FROM
    `ftm-sepedi.analytics_180755978.events_20*`
  WHERE
    event_name = 'session_start'
    AND app_info.id LIKE '%feedthemonster%'
  AND  CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) BETWEEN '2021-01-01'
  AND CURRENT_DATE()
  UNION ALL
  SELECT
    user_pseudo_id,
    geo.country AS country,
    app_info.id AS app_id,
    LOWER(REGEXP_EXTRACT(app_info.id, r'feedthemonster(.*)')) AS app_language,
    CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open
  FROM
    `ftm-zulu.analytics_155849122.events_20*`
  WHERE
    event_name = 'session_start'
    AND app_info.id LIKE '%feedthemonster%'
  AND  CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) BETWEEN '2021-01-01'
  AND CURRENT_DATE()
 UNION ALL
  SELECT
    user_pseudo_id,
    geo.country AS country,
    app_info.id AS app_id,
    LOWER(REGEXP_EXTRACT(app_info.id, r'feedthemonster(.*)')) AS app_language,
    CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open
  FROM
    `ftm-southafricanenglish.analytics_173750850.events_20*`
  WHERE
    event_name = 'session_start'
    AND app_info.id LIKE '%feedthemonster%'
  AND  CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) BETWEEN '2021-01-01'
  AND CURRENT_DATE()
  UNION ALL
  SELECT
    user_pseudo_id,
    geo.country AS country,
    app_info.id AS app_id,
    LOWER(REGEXP_EXTRACT(app_info.id, r'feedthemonster(.*)')) AS app_language,
    CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open
  FROM
    `ftm-spanish.analytics_158656398.events_20*`
  WHERE
    event_name = 'session_start'
    AND app_info.id LIKE '%feedthemonster%'
  AND  CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) BETWEEN '2021-01-01'
  AND CURRENT_DATE()
)