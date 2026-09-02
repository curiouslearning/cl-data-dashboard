-- =====================================================================================
-- ONE-TIME load of the World Bank Nigeria June 2026 mode roster.
--
-- Table: dataexploration-193817.user_data.cr_study_user_modes
-- Grain: one row per study_user_id (164 rows, all 11-digit Nigerian mobile numbers).
--
-- Purpose
-- -------
-- The partner assigned every enrolled participant one of three recruitment/delivery
-- modes -- 'In-person', 'Online', 'Phone'. That assignment exists ONLY in the
-- partner's roster spreadsheet; nothing in Firebase carries it. This table is the
-- bridge, and queries/cr_cohorts_nightly.sql joins it to cr_study_cohort on
-- study_user_id to emit the three "study:... - <mode>" sub-cohorts.
--
-- Source file: kano_study_users.csv  (columns: respondent_id, mode, study_user_id)
-- Loaded 2026-09-01. Roster counts: Online 64, In-person 50, Phone 50.
--
-- PII
-- ---
-- study_user_id is the participant's phone number, so the roster data is NOT
-- committed to this repo -- same rule cr_study_cohort.sql follows ("phone numbers
-- stay in this table"). Only cr_user_id ever reaches cr_cohorts. To rebuild, re-run
-- the bq load below against the partner CSV; do not paste the numbers into git.
--
-- Static
-- ------
-- The roster is closed -- 164 participants, no new enrollments expected. Re-run this
-- only if the partner reissues the spreadsheet. The study_user_id -> cr_user_id
-- resolution is what stays dynamic, and that lives in the nightly job.
-- =====================================================================================

-- Rebuild step 1 -- load the roster from the partner CSV (run in a shell, not BigQuery):
--
--   bq load \
--     --project_id=dataexploration-193817 \
--     --source_format=CSV \
--     --skip_leading_rows=1 \
--     --replace \
--     user_data.cr_study_user_modes \
--     ~/Downloads/kano_study_users.csv \
--     respondent_id:STRING,mode:STRING,study_user_id:STRING
--
-- Note the CSV column order is respondent_id, mode, study_user_id -- the schema string
-- above matches the file, not the logical column order. study_user_id MUST load as
-- STRING: these numbers carry a leading zero that an INT64 column would silently eat,
-- breaking every join to cr_study_cohort.

-- Rebuild step 2 -- verify. Expect: 164 / 164 / 3, and zero malformed ids.
SELECT
  COUNT(*)                        AS n_rows,          -- expect 164
  COUNT(DISTINCT study_user_id)   AS n_ids,           -- expect 164 (no dupes)
  COUNT(DISTINCT mode)            AS n_modes,         -- expect 3
  COUNTIF(NOT REGEXP_CONTAINS(study_user_id, r'^0[0-9]{10}$')) AS malformed_ids  -- expect 0
FROM `dataexploration-193817.user_data.cr_study_user_modes`;

-- Rebuild step 3 -- coverage against the resolved study cohort. As of 2026-09-01 only
-- 101 of the 164 roster ids ever produced an enrollment event, and the shortfall is
-- overwhelmingly in the Online arm (see the caveat block in cr_cohorts_nightly.sql).
SELECT
  m.mode,
  COUNT(DISTINCT m.study_user_id) AS roster_ids,
  COUNT(DISTINCT s.study_user_id) AS resolved_ids,
  COUNT(DISTINCT s.cr_user_id)    AS cr_user_ids
FROM `dataexploration-193817.user_data.cr_study_user_modes` m
LEFT JOIN `dataexploration-193817.user_data.cr_study_cohort` s
  USING (study_user_id)
GROUP BY ROLLUP(m.mode)
ORDER BY m.mode;
