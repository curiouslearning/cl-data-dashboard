-- =====================================================================================
-- Nightly Parquet export for cr_app_launch
-- Writes each run to a run_date partitioned folder to avoid shard collisions
-- =====================================================================================

DECLARE run_date DATE DEFAULT CURRENT_DATE("America/Los_Angeles");
DECLARE run_date_str STRING DEFAULT FORMAT_DATE('%Y-%m-%d', run_date);

DECLARE export_uri STRING;

SET export_uri = CONCAT(
  'gs://user_data_parquet_cache/cr_app_launch/run_date=',
  run_date_str,
  '/cr_app_launch_*.parquet'
);

EXECUTE IMMEDIATE FORMAT("""
EXPORT DATA OPTIONS (
  uri = '%s',
  format = 'PARQUET',
  overwrite = true
) AS
SELECT *
FROM `dataexploration-193817.user_data.cr_app_launch`
""", export_uri);