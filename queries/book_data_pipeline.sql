/*
===============================================================================
Nightly Book Data Pipeline
===============================================================================
Runs the full book data pipeline in dependency order:

  1. cr_book_users              — raw GA4 event extract
  2. cr_book_user_book_summary  — per user×book aggregation (fixed)
  3. cr_book_user_summary_all   — per user rollup
  4. cr_book_user_cohorts       — joined with FTM outcomes + tiers
  5. Export cr_book_user_book_summary → GCS parquet
  6. Export cr_book_user_summary_all  → GCS parquet
  7. Export cr_book_user_cohorts      → GCS parquet

Schedule: nightly, after cr_user_progress export has completed.
===============================================================================
*/

DECLARE run_date DATE DEFAULT CURRENT_DATE("America/Los_Angeles");
DECLARE run_date_str STRING DEFAULT FORMAT_DATE('%Y-%m-%d', run_date);

DECLARE uri_book_summary STRING;
DECLARE uri_summary_all  STRING;
DECLARE uri_cohorts      STRING;

SET uri_book_summary = CONCAT(
  'gs://user_data_parquet_cache/cr_book_user_book_summary/run_date=',
  run_date_str,
  '/cr_book_user_book_summary_*.parquet'
);

SET uri_summary_all = CONCAT(
  'gs://user_data_parquet_cache/cr_book_user_summary_all/run_date=',
  run_date_str,
  '/cr_book_user_summary_all_*.parquet'
);

SET uri_cohorts = CONCAT(
  'gs://user_data_parquet_cache/cr_book_user_cohorts/run_date=',
  run_date_str,
  '/cr_book_user_cohorts_*.parquet'
);

-- ============================================================
-- Step 1: cr_book_users (raw event extract)
-- ============================================================
CREATE OR REPLACE TABLE `dataexploration-193817.user_data.cr_book_users` AS
WITH base AS (
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS event_date,
    TIMESTAMP_MICROS(event_timestamp) AS event_time,
    event_name,
    user_pseudo_id,
    (SELECT ep.value.string_value
     FROM UNNEST(event_params) ep
     WHERE ep.key = 'page_location') AS page_location
  FROM `ftm-b9d99.analytics_159643920.events_*`
  WHERE _TABLE_SUFFIX >= '20230101'
)
SELECT
  REGEXP_EXTRACT(
    page_location,
    r'[?&]cr_user_id=([a-z0-9]+20\d{2}\d{5,10})'
  ) AS cr_user_id,
  user_pseudo_id,
  event_name,
  event_date,
  event_time,
  page_location
FROM base
WHERE page_location IS NOT NULL
  AND REGEXP_CONTAINS(page_location, r'[\?&]book=')
  AND REGEXP_CONTAINS(page_location, r'[\?&]cr_user_id=');


-- ============================================================
-- Step 2: cr_book_user_book_summary (per user×book aggregation)
-- ============================================================
CREATE OR REPLACE TABLE `dataexploration-193817.user_data.cr_book_user_book_summary`
AS
WITH
  language_suffixes AS (
    SELECT * FROM UNNEST(
      [
        'CVPortuguese',
        'CVCreole',
        'IsiZulu',
        'Ukrainian',
        'Luganda',
        'Nepali',
        'Swahili',
        'Marathi',
        'Amharic',
        'Tigirigna',
        'Somali',
        'Oromo',
        'Hausa',
        'Wolof',
        'Bangla',
        'Hindi',
        'HIndi',    -- alternate casing observed in book_ids
        'Isizulu',  -- alternate casing of IsiZulu
        'Portuguese',
        'Ukr',
        'Nep',
        'Lug',
        'En'
      ]
    ) AS suffix
  ),

  base AS (
    SELECT
      cr_user_id,
      event_name,
      event_date,
      event_time,
      page_location,
      REGEXP_EXTRACT(page_location, r'[?&]book=([^&?]+)') AS book_id
    FROM `dataexploration-193817.user_data.cr_book_users`
    WHERE cr_user_id IS NOT NULL
      AND page_location IS NOT NULL
  ),

  parsed AS (
    SELECT
      cr_user_id,
      event_name,
      event_date,
      event_time,
      book_id,
      SAFE_CAST(REGEXP_EXTRACT(book_id, r'Lv(\d+)$') AS INT64) AS book_level,
      REGEXP_REPLACE(book_id, r'Lv\d+$', '') AS book_no_level
    FROM base
    WHERE book_id IS NOT NULL
  ),

  book_language_map AS (
    SELECT DISTINCT
      book_id,
      book_no_level,
      book_level,
      s.suffix AS language_code,
      CASE
        WHEN s.suffix IN ('IsiZulu', 'Isizulu') THEN 'Zulu'
        WHEN s.suffix IN ('Hindi', 'HIndi')   THEN 'Hindi'
        WHEN s.suffix IN ('En', 'English') THEN 'English'
        WHEN s.suffix = 'CVPortuguese'     THEN 'Portuguese'
        WHEN s.suffix = 'CVCreole'         THEN 'Creole'
        WHEN s.suffix = 'Nep'              THEN 'Nepali'
        WHEN s.suffix = 'Ukr'              THEN 'Ukrainian'
        WHEN s.suffix = 'Lug'              THEN 'Luganda'
        ELSE s.suffix
      END AS book_language,
      CASE
        WHEN s.suffix IS NOT NULL THEN
          REGEXP_REPLACE(
            REGEXP_REPLACE(book_id, r'Lv\d+$', ''),
            CONCAT(r'(', s.suffix, r')$'), ''
          )
        ELSE NULL
      END AS base_book_id
    FROM (SELECT DISTINCT book_id, book_no_level, book_level FROM parsed) p
    LEFT JOIN language_suffixes s
      ON ENDS_WITH(p.book_no_level, s.suffix)
    QUALIFY
      ROW_NUMBER() OVER (
        PARTITION BY p.book_id
        ORDER BY LENGTH(s.suffix) DESC
      ) = 1
  ),

  user_book AS (
    SELECT
      p.cr_user_id,
      p.book_id,
      m.base_book_id,
      m.language_code,
      m.book_language,
      m.book_level,
      COUNT(*)                      AS total_events,
      COUNT(DISTINCT p.event_date)  AS active_days_for_book,
      MIN(p.event_date)             AS first_access_date,
      MAX(p.event_date)             AS last_access_date,
      MIN(p.event_time)             AS first_access_time,
      MAX(p.event_time)             AS last_access_time
    FROM parsed p
    LEFT JOIN book_language_map m USING (book_id)
    GROUP BY
      p.cr_user_id, p.book_id, m.base_book_id,
      m.language_code, m.book_language, m.book_level
  )

SELECT
  *,
  CASE
    WHEN active_days_for_book >= 3 THEN 'Hooked'
    WHEN active_days_for_book = 2  THEN 'Returned'
    ELSE                                'Bounced'
  END AS stickiness
FROM user_book;


-- ============================================================
-- Step 3: cr_book_user_summary_all (per user rollup)
-- ============================================================
CREATE OR REPLACE TABLE `dataexploration-193817.user_data.cr_book_user_summary_all` AS
WITH base AS (
  SELECT
    cr_user_id,
    book_id,
    book_language,
    language_code,
    total_events,
    active_days_for_book,
    first_access_date,
    last_access_date,
    COUNT(*) OVER (PARTITION BY cr_user_id, book_language, language_code) AS cnt_pair
  FROM `dataexploration-193817.user_data.cr_book_user_book_summary`
),

user_rollup AS (
  SELECT
    cr_user_id,
    (ARRAY_AGG(STRUCT(book_language, language_code)
      ORDER BY cnt_pair DESC, book_language, language_code LIMIT 1
    ))[OFFSET(0)].book_language AS book_language,

    (ARRAY_AGG(STRUCT(book_language, language_code)
      ORDER BY cnt_pair DESC, book_language, language_code LIMIT 1
    ))[OFFSET(0)].language_code AS language_code,

    COUNT(DISTINCT book_id)          AS distinct_books_accessed,
    SUM(total_events)                AS total_book_events,
    SUM(active_days_for_book)        AS total_active_book_days,
    COUNTIF(active_days_for_book >= 2) AS books_with_2plus_days,
    MIN(first_access_date)           AS first_access_date,
    MAX(last_access_date)            AS last_access_date,
    DATE_DIFF(MAX(last_access_date), MIN(first_access_date), DAY) AS book_span_days
  FROM base
  GROUP BY cr_user_id
),

most_read AS (
  SELECT
    cr_user_id,
    book_id AS most_read_book_id,
    MAX(total_events) AS most_read_book_events
  FROM `dataexploration-193817.user_data.cr_book_user_book_summary`
  GROUP BY cr_user_id, book_id
  QUALIFY
    ROW_NUMBER() OVER (
      PARTITION BY cr_user_id
      ORDER BY most_read_book_events DESC, book_id
    ) = 1
)

SELECT
  u.cr_user_id,
  u.book_language,
  u.language_code,
  u.distinct_books_accessed,
  u.total_book_events,
  u.total_active_book_days,
  u.books_with_2plus_days,
  u.first_access_date,
  u.last_access_date,
  u.book_span_days,
  m.most_read_book_id,
  m.most_read_book_events
FROM user_rollup u
LEFT JOIN most_read m USING (cr_user_id);


-- ============================================================
-- Step 4: cr_book_user_cohorts (joined with FTM outcomes + tiers)
-- ============================================================
CREATE OR REPLACE TABLE `dataexploration-193817.user_data.cr_book_user_cohorts`
AS
WITH
  book_languages AS (
    SELECT DISTINCT book_language
    FROM `dataexploration-193817.user_data.cr_book_user_summary_all`
    WHERE book_language IS NOT NULL
  ),

  book_users AS (
    SELECT
      cr_user_id,
      book_language,
      language_code AS book_language_code,
      distinct_books_accessed,
      total_book_events,
      total_active_book_days,
      books_with_2plus_days,
      first_access_date,
      last_access_date,
      book_span_days,
      most_read_book_id,
      most_read_book_events
    FROM `dataexploration-193817.user_data.cr_book_user_summary_all`
  ),

  progress_norm AS (
    SELECT
      p.*,
      CASE
        WHEN LOWER(p.app_language) IN (
          'english','australianenglish','englishaus','englishindian','indianenglish',
          'englishwestafrican','saenglish'
        ) THEN 'English'
        WHEN LOWER(p.app_language) IN (
          'portuguese','brazilianportuguese','caboverdeportuguese'
        ) THEN 'Portuguese'
        WHEN LOWER(p.app_language) IN (
          'caboverdecreole','haitiancreole'
        ) THEN 'Creole'
        WHEN LOWER(p.app_language) = 'amharic'   THEN 'Amharic'
        WHEN LOWER(p.app_language) = 'bangla'    THEN 'Bangla'
        WHEN LOWER(p.app_language) = 'hausa'     THEN 'Hausa'
        WHEN LOWER(p.app_language) = 'hindi'     THEN 'Hindi'
        WHEN LOWER(p.app_language) = 'marathi'   THEN 'Marathi'
        WHEN LOWER(p.app_language) = 'nepali'    THEN 'Nepali'
        WHEN LOWER(p.app_language) = 'oromo'     THEN 'Oromo'
        WHEN LOWER(p.app_language) = 'somali'    THEN 'Somali'
        WHEN LOWER(p.app_language) = 'swahili'   THEN 'Swahili'
        WHEN LOWER(p.app_language) = 'tigrigna'  THEN 'Tigirigna'
        WHEN LOWER(p.app_language) = 'ukrainian' THEN 'Ukrainian'
        WHEN LOWER(p.app_language) = 'wolof'     THEN 'Wolof'
        WHEN LOWER(p.app_language) = 'zulu'      THEN 'Zulu'
        WHEN LOWER(p.app_language) IN ('lugandan','luganda','lug') THEN 'Luganda'
        ELSE NULL
      END AS app_language_book
    FROM `dataexploration-193817.user_data.cr_user_progress` p
  ),

  user_universe AS (
    SELECT
      p.user_pseudo_id,
      p.cr_user_id,
      p.first_open,
      p.country,
      p.app_language,
      p.app_language_book,
      p.app,
      p.max_user_level,
      p.max_game_level,
      p.la_date,
      p.ra_date,
      p.days_to_ra,
      p.furthest_event,
      p.gpc,
      p.engagement_event_count,
      p.total_time_minutes,
      p.avg_session_length_minutes,
      p.last_event_date,
      p.active_span,
      p.la_flag,
      p.ra_flag,
      p.gc_flag,
      p.lr_flag
    FROM progress_norm p
    LEFT JOIN book_languages bl ON p.app_language_book = bl.book_language
    LEFT JOIN book_users bu     ON p.cr_user_id = bu.cr_user_id
    WHERE p.cr_user_id IS NOT NULL
      AND (bl.book_language IS NOT NULL OR bu.cr_user_id IS NOT NULL)
  ),

  joined AS (
    SELECT
      u.*,
      bu.cr_user_id IS NOT NULL        AS is_book_user,
      bu.book_language,
      bu.book_language_code,
      COALESCE(bu.distinct_books_accessed, 0)  AS distinct_books_accessed,
      COALESCE(bu.total_book_events, 0)         AS total_book_events,
      COALESCE(bu.total_active_book_days, 0)    AS total_active_book_days,
      COALESCE(bu.books_with_2plus_days, 0)     AS books_with_2plus_days,
      bu.first_access_date,
      bu.last_access_date,
      COALESCE(bu.book_span_days, 0)            AS book_span_days,
      bu.most_read_book_id,
      bu.most_read_book_events
    FROM user_universe u
    LEFT JOIN book_users bu ON u.cr_user_id = bu.cr_user_id
  ),

  tiered AS (
    SELECT
      *,
      CASE
        WHEN NOT is_book_user THEN 0
        WHEN total_active_book_days = 1 THEN 1
        WHEN (
          total_active_book_days >= 3
          AND (
            distinct_books_accessed >= 3
            OR books_with_2plus_days >= 2
            OR book_span_days >= 3
          )
        ) THEN 3
        WHEN (
          total_active_book_days >= 2
          OR distinct_books_accessed >= 2
          OR books_with_2plus_days >= 1
        ) THEN 2
        ELSE 2
      END AS book_engagement_tier
    FROM joined
  )

SELECT * FROM tiered;



-- ============================================================
-- Step 5–7: Export all three tables to GCS parquet
-- Note: URIs use EXECUTE IMMEDIATE with FORMAT to inject today's
-- run_date string. Variables are inlined into the FORMAT call
-- directly to avoid scoping issues with EXECUTE IMMEDIATE.
-- ============================================================
EXECUTE IMMEDIATE FORMAT("""
EXPORT DATA OPTIONS (
  uri = 'gs://user_data_parquet_cache/cr_book_user_book_summary/run_date=%s/cr_book_user_book_summary_*.parquet',
  format = 'PARQUET',
  overwrite = true
) AS
SELECT * FROM `dataexploration-193817.user_data.cr_book_user_book_summary`
""", FORMAT_DATE('%Y-%m-%d', CURRENT_DATE("America/Los_Angeles")));

EXECUTE IMMEDIATE FORMAT("""
EXPORT DATA OPTIONS (
  uri = 'gs://user_data_parquet_cache/cr_book_user_summary_all/run_date=%s/cr_book_user_summary_all_*.parquet',
  format = 'PARQUET',
  overwrite = true
) AS
SELECT * FROM `dataexploration-193817.user_data.cr_book_user_summary_all`
""", FORMAT_DATE('%Y-%m-%d', CURRENT_DATE("America/Los_Angeles")));

EXECUTE IMMEDIATE FORMAT("""
EXPORT DATA OPTIONS (
  uri = 'gs://user_data_parquet_cache/cr_book_user_cohorts/run_date=%s/cr_book_user_cohorts_*.parquet',
  format = 'PARQUET',
  overwrite = true
) AS
SELECT * FROM `dataexploration-193817.user_data.cr_book_user_cohorts`
""", FORMAT_DATE('%Y-%m-%d', CURRENT_DATE("America/Los_Angeles")));