/*
===============================================================================
Ad-hoc: rows active in the last 30 days carrying source, campaign_id, or
study_user_id.

Note on the date filter: "last month" is interpreted as ACTIVE in the last 30
days (last_event_date), not newly acquired. Swap to first_open for the
new-users reading -- the two differ a lot (3,182 rows vs 130 as of 2026-08-26).
===============================================================================
*/

-- Detail rows -----------------------------------------------------------
SELECT
  cr_user_id,
  study_user_id,
  source,
  campaign_id,
  country,
  app_language,
  app,
  first_open,
  last_event_date,
  max_user_level,
  total_time_minutes,
  la_flag,
  ra_flag
FROM `dataexploration-193817.user_data.cr_user_progress`
WHERE last_event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  AND (source IS NOT NULL OR campaign_id IS NOT NULL OR study_user_id IS NOT NULL)
ORDER BY last_event_date DESC, total_time_minutes DESC;


-- Rolled up by campaign -------------------------------------------------
-- SELECT
--   source,
--   campaign_id,
--   COUNT(*) AS users,
--   COUNTIF(study_user_id IS NOT NULL) AS with_study_id,
--   ROUND(AVG(total_time_minutes), 1) AS avg_minutes,
--   SUM(la_flag) AS la_users,
--   SUM(ra_flag) AS ra_users
-- FROM `dataexploration-193817.user_data.cr_user_progress`
-- WHERE last_event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
--   AND (source IS NOT NULL OR campaign_id IS NOT NULL OR study_user_id IS NOT NULL)
-- GROUP BY source, campaign_id
-- ORDER BY users DESC;


-- Same question against cr_app_launch (device data, no progress metrics) --
-- SELECT
--   cr_user_id, study_user_id, source, campaign_id, country, app_language,
--   device_category, device_mobile_marketing_name, android_version,
--   first_open, first_launch_ts
-- FROM `dataexploration-193817.user_data.cr_app_launch`
-- WHERE DATE(first_launch_ts) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
--   AND (source IS NOT NULL OR campaign_id IS NOT NULL OR study_user_id IS NOT NULL)
-- ORDER BY first_launch_ts DESC;
