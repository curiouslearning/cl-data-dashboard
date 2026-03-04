-- =====================================================================================
-- Nightly Parquet export for cr_book_user_cohorts
-- Writes each run to a run_date partitioned folder to avoid shard collisions
-- =====================================================================================

DECLARE run_date DATE DEFAULT CURRENT_DATE("America/Los_Angeles");
DECLARE run_date_str STRING DEFAULT FORMAT_DATE('%Y-%m-%d', run_date);

DECLARE export_uri STRING;

SET export_uri = CONCAT(
  'gs://user_data_parquet_cache/cr_book_user_cohorts/run_date=',
  run_date_str,
  '/cr_book_user_cohorts_*.parquet'
);

EXECUTE IMMEDIATE FORMAT("""
EXPORT DATA OPTIONS (
  uri = '%s',
  format = 'PARQUET',
  overwrite = true
) AS
SELECT *
FROM `dataexploration-193817.user_data.cr_book_user_cohorts`
""", export_uri);