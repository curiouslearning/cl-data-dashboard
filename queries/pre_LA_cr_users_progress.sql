WITH
  all_events AS (
  SELECT
    user_pseudo_id,
    "org.curiouslearning.container" AS app_id,
    CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open,
    geo.country AS country,
    LOWER(REGEXP_EXTRACT(app_params.value.string_value, '[?&]cr_lang=([^&]+)')) AS app_language,
    SUM(CASE
        WHEN event_name = 'puzzle_completed' THEN 1
      ELSE
      0
    END
      ) AS puzzle_completed_count,
    SUM(CASE
        WHEN event_name = 'selected_level' THEN 1
      ELSE
      0
    END
      ) AS selected_level_count,
    SUM(CASE
        WHEN event_name = 'tapped_start' THEN 1
      ELSE
      0
    END
      ) AS tapped_start_count
  FROM
    `ftm-b9d99.analytics_159643920.events_20*` AS ga,
    UNNEST(event_params) AS app_params
  WHERE
    event_name IN ('tapped_start',
      'selected_level',
      'puzzle_completed')
    AND app_params.key = 'page_location'
    AND app_params.value.string_value LIKE '%https://feedthemonster.curiouscontent.org%'
  GROUP BY
    user_pseudo_id,
    app_id,
    first_open,
    country,
    app_language )
SELECT
  user_pseudo_id,
  app_id,
  first_open,
  country,
  app_language,
  CASE
    WHEN puzzle_completed_count > 0 THEN 'puzzle_completed'
    WHEN selected_level_count > 0 THEN 'selected_level'
    WHEN tapped_start_count > 0 THEN 'tapped_start'
  ELSE
  NULL
END
  AS furthest_event
FROM
  all_events