  SELECT
    user_pseudo_id,
    geo.country AS country,
    app_info.id AS app_id,
    LOWER(REGEXP_EXTRACT(event_params.value.string_value, '[?&]cr_lang=([^&]+)')) AS app_language,
    CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open
  FROM
    `ftm-b9d99.analytics_159643920.events_20*` AS A,
    UNNEST (event_params )AS event_params

  WHERE
    app_info.id = 'org.curiouslearning.container'
    AND event_params.value.string_value LIKE '%feedthemonster.curiouscontent.org%'
    AND event_name = 'app_launch'
    AND event_params.key = 'web_app_url'
    AND CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) BETWEEN '2021-01-01'
    AND CURRENT_DATE()
Group by 1,2,3,4,5