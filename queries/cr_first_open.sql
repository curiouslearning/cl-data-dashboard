SELECT
 distinct user_pseudo_id,
 geo.country AS country,
 CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open
FROM
 `ftm-b9d99.analytics_159643920.events_20*` AS A
WHERE
 app_info.id = 'org.curiouslearning.container'
 AND event_name = 'first_open'
 AND CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) BETWEEN '2021-01-01'
 AND CURRENT_DATE()
GROUP BY
 1,
 2,
 3
