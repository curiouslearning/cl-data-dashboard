  -- Step 1: Base User Metadata
WITH
  base_data AS (
  SELECT
    (
    SELECT
      value.string_value
    FROM
      UNNEST(event_params)
    WHERE
      KEY = 'cr_user_id') AS cr_user_id,
    user_pseudo_id,
    geo.country AS country,
    LOWER(REGEXP_EXTRACT( (
        SELECT
          value.string_value
        FROM
          UNNEST(event_params)
        WHERE
          KEY = 'web_app_url'), '[?&]cr_lang=([^&]+)' )) AS app_language,
    CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open
  FROM
    `ftm-b9d99.analytics_159643920.events_20*`
  WHERE
    app_info.id = 'org.curiouslearning.container'
    AND event_name = 'app_launch'
    AND (
    SELECT
      value.string_value
    FROM
      UNNEST(event_params)
    WHERE
      KEY = 'web_app_url') LIKE 'https://feedthemonster.curiouscontent.org%'
    AND (
    SELECT
      value.string_value
    FROM
      UNNEST(event_params)
    WHERE
      KEY = 'cr_user_id') IS NOT NULL
    AND CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) BETWEEN '2021-01-01'
    AND CURRENT_DATE()
  GROUP BY
    cr_user_id,
    user_pseudo_id,
    country,
    app_language,
    first_open )
  -- Step 2: Add cohort tag via join
SELECT
  b.*,
  cg.cohort_group  -- ✅ new column
FROM
  base_data b
LEFT JOIN
  `dataexploration-193817.user_data.cohort_groups` cg
ON
  b.cr_user_id = cg.cr_user_id
ORDER BY
  first_open DESC;