/*
===============================================================================
Table: cr_study_cohort  (+ optional load into cr_cohorts)

Purpose
-------
Maps study_user_id (the participant's phone number, supplied by the partner)
to cr_user_id, so study participants can be pulled as a cohort in the
dashboards.

Source of truth
---------------
Per the "Set study_user_id via deep link feature" spec, the authoritative
record is the `joined_study` Firebase event, fired when the participant taps
the green confirm button. The study_user_id stamped onto `app_launch`
event_params is an explicit BACKUP for the case where joined_study never
reaches BigQuery.

This query UNIONs both, which is what the spec intends: joined_study first,
app_launch as the safety net. Building from app_launch alone misses ~24% of
participants (62 of 255 study ids as of 2026-08-26).

Grain
-----
One row per (study_user_id, cr_user_id). NOT one row per participant --
a participant who reinstalls or uses a second device gets a new cr_user_id
under the same phone number. As of 2026-08-26: 256 participants / 304 users.
===============================================================================
*/

CREATE OR REPLACE TABLE `dataexploration-193817.user_data.cr_study_cohort` AS
WITH study_events AS (
  SELECT
    (SELECT ep.value.string_value FROM UNNEST(event_params) ep WHERE ep.key = 'study_user_id') AS study_user_id,
    (SELECT ep.value.string_value FROM UNNEST(event_params) ep WHERE ep.key = 'cr_user_id')    AS cr_user_id,
    (SELECT ep.value.string_value FROM UNNEST(event_params) ep WHERE ep.key = 'study_consent') AS study_consent,
    event_name,
    PARSE_DATE('%Y%m%d', event_date) AS event_dt
  FROM `ftm-b9d99.analytics_159643920.events_20*`
  WHERE event_name IN ('joined_study', 'app_launch')
    AND (SELECT ep.value.string_value FROM UNNEST(event_params) ep WHERE ep.key = 'study_user_id') IS NOT NULL
    AND (SELECT ep.value.string_value FROM UNNEST(event_params) ep WHERE ep.key = 'cr_user_id')    IS NOT NULL
)
SELECT
  study_user_id,
  cr_user_id,
  -- Confirmed = the participant actually tapped the confirm button.
  -- backup-only rows were recovered from app_launch and never produced a
  -- joined_study event; treat them as lower-confidence enrollments.
  COUNTIF(event_name = 'joined_study') > 0 AS confirmed_via_joined_study,
  MAX(study_consent) AS study_consent,
  MIN(event_dt) AS first_seen,
  MAX(event_dt) AS last_seen
FROM study_events
GROUP BY study_user_id, cr_user_id;


-- ---------------------------------------------------------------------------
-- Loading into cr_cohorts
--
-- Do NOT insert here. queries/cr_cohorts_nightly.sql owns writes to cr_cohorts
-- and reads this table in its study_memberships branch, under the cohort name
--   study:World Bank Nigeria June 2026
--
-- That job uses a sticky MERGE (insert-only, never deletes), so a participant
-- who enrolls today stays enrolled even if their gameplay data arrives weeks
-- later from an offline sync. Run order: this file, then cr_cohorts_nightly.sql.
--
-- Only cr_user_id reaches cr_cohorts. Phone numbers stay in this table.
-- ---------------------------------------------------------------------------
