WITH
  combined_countries AS (
  SELECT
    country
  FROM
    dataexploration-193817.user_data.unity_user_progress
  UNION DISTINCT
  SELECT
    country
  FROM
    dataexploration-193817.user_data.cr_user_progress )
SELECT
  country
FROM
  combined_countries
ORDER BY
  country ASC;