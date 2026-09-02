-- =====================================================================================
-- Nightly sticky cohort upsert (multi-cohort + derived app cohorts + study cohorts)
--
-- Table: dataexploration-193817.user_data.cr_cohorts
-- Schema: (cr_user_id STRING/INT64, cohort_name STRING)
--
-- Behavior:
-- - Sticky: inserts new (cr_user_id, cohort_name) pairs; never removes existing rows
-- - Deterministic user base: picks exactly 1 row per cr_user_id (highest max_user_level, then latest last_event_date)
-- - Program cohorts: add/edit definitions in cohort_rules below (prefixed "program:")
-- - App cohorts: for any user with app != 'CR', inserts cohort_name = CONCAT('app:', app)
-- - Study cohorts: explicit ID lists from cr_study_cohort (prefixed "study:")   <-- ADDED 2026-08-26
-- - Study mode sub-cohorts: study cohort x partner roster mode                  <-- ADDED 2026-09-01
-- - MERGE prevents duplicates for (cr_user_id, cohort_name)
--
-- DEPENDENCY (added 2026-08-26): the study branch reads
-- `user_data.cr_study_cohort`, so queries/cr_study_cohort.sql must run BEFORE this.
-- If that table is missing this query fails loudly rather than silently skipping.
--
-- DEPENDENCY (added 2026-09-01): the study mode branch also reads
-- `user_data.cr_study_user_modes`, a static partner roster loaded once by
-- queries/adhoc/load_cr_study_user_modes.sql. It is not rebuilt nightly, but it must
-- EXIST or this query fails. Run order: cr_study_cohort.sql, then this.
--
-- NOTE: study participants now carry two cohort rows (parent + mode arm). cr_app_launch
-- LEFT JOINs cr_cohorts on cr_user_id without pre-aggregating, so those users fan out
-- one extra row there. Multi-cohort membership is already the norm (985 users at 2
-- cohorts, 62 at 3 as of 2026-09-01), so this changes the degree, not the kind -- but
-- do not COUNT(*) cr_app_launch and call it users.
-- =====================================================================================

MERGE `dataexploration-193817.user_data.cr_cohorts` AS tgt
USING (
  WITH base_users AS (
    SELECT
      cr_user_id,
      first_open,
      country,
      app_language,
      app,
      max_user_level,
      last_event_date
    FROM `dataexploration-193817.user_data.cr_user_progress`
    WHERE cr_user_id IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (
      PARTITION BY cr_user_id
      ORDER BY max_user_level DESC, last_event_date DESC
    ) = 1
  ),

  -- -------------------------------------------------------------------------------
  -- Cohort definitions (add more STRUCT rows)
  -- Conventions:
  -- - Use prefixes to avoid collisions: "program:" and "app:"
  -- - NULL means "no filter" for that field
  --
  -- NOTE: attribute rules can only ever match users present in cr_user_progress.
  -- For membership that is an explicit list of people (a research study), use the
  -- study_memberships branch below instead -- see the comment there for why.
  -- -------------------------------------------------------------------------------
  cohort_rules AS (
    SELECT * FROM UNNEST([
      STRUCT(
        'program:Congo - Brazzaville' AS cohort_name,
        DATE '2026-01-18'             AS first_open_after,
        ['Congo - Brazzaville']       AS countries,
        ['french','english']          AS languages,
        ['CR']                        AS apps
      )

    ,STRUCT(
      'program:WBS - Nigeria' AS cohort_name,
      NULL                   AS first_open_after,
      NULL                   AS countries,
      NULL                   AS languages,
      ['WBS-standalone']     AS apps
    )

      -- Example with no language filter:
      -- ,STRUCT(
      --   'program:Global CR since Feb' AS cohort_name,
      --   DATE '2026-02-01'             AS first_open_after,
      --   NULL                          AS countries,
      --   NULL                          AS languages,
      --   ['CR']                        AS apps
      -- )
    ])
  ),

  -- Program cohort memberships
  rule_memberships AS (
    SELECT
      u.cr_user_id,
      r.cohort_name
    FROM base_users u
    JOIN cohort_rules r
      ON (r.first_open_after IS NULL OR u.first_open > r.first_open_after)
     AND (r.countries       IS NULL OR u.country      IN UNNEST(r.countries))
     AND (r.languages       IS NULL OR u.app_language IN UNNEST(r.languages))
     AND (r.apps            IS NULL OR u.app          IN UNNEST(r.apps))
  ),

  -- Derived app cohorts (any non-CR app)
  app_memberships AS (
    SELECT
      cr_user_id,
      CONCAT('app:', app) AS cohort_name
    FROM base_users
    WHERE app IS NOT NULL
      AND app != 'CR'
  ),

  -- -------------------------------------------------------------------------------
  -- Study cohort memberships                                    ADDED 2026-08-26
  --
  -- Study membership is an explicit list of enrolled people, not an attribute
  -- predicate, so it cannot be expressed as a cohort_rules STRUCT.
  --
  -- Deliberately NOT joined to base_users. base_users comes from cr_user_progress,
  -- which holds only 185 of the 304 enrolled cr_user_ids -- the rest have no Feed
  -- the Monster gameplay (they are on Curious Reader, or played offline with events
  -- unsent). Gating on base_users would silently drop 39% of the study. Rows for
  -- users with no progress data are harmless: nothing joins to them until data
  -- arrives, and sticky MERGE means a late offline sync finds them already enrolled.
  --
  -- Note this is a DIFFERENT population from 'program:WBS - Nigeria' above, which
  -- selects WBS-standalone app users. Overlap with the study is currently zero:
  -- every study participant runs the CR container app.
  -- -------------------------------------------------------------------------------
  study_memberships AS (
    SELECT DISTINCT
      cr_user_id,
      'study:World Bank Nigeria June 2026' AS cohort_name
    FROM `dataexploration-193817.user_data.cr_study_cohort`
    WHERE cr_user_id IS NOT NULL
      AND confirmed_via_joined_study     -- drop this predicate to admit backup-only rows
  ),

  -- -------------------------------------------------------------------------------
  -- Study MODE sub-cohorts                                      ADDED 2026-09-01
  --
  -- Splits 'study:World Bank Nigeria June 2026' into three arms by the partner's
  -- recruitment/delivery mode:
  --   study:World Bank Nigeria June 2026 - In-person
  --   study:World Bank Nigeria June 2026 - Online
  --   study:World Bank Nigeria June 2026 - Phone
  --
  -- Mode is not in Firebase -- it exists only in the partner roster, loaded once into
  -- user_data.cr_study_user_modes (see queries/adhoc/load_cr_study_user_modes.sql).
  -- Only the roster is static; the study_user_id -> cr_user_id resolution happens here
  -- every night, so a participant whose events arrive late from an offline sync lands
  -- in their mode sub-cohort whenever the data shows up. That is the whole reason this
  -- is a nightly join and not a one-time INSERT.
  --
  -- Predicates deliberately mirror study_memberships above (confirmed_via_joined_study,
  -- cr_user_id IS NOT NULL) so an arm can never contain a user the parent cohort lacks.
  -- Like the parent, this is NOT gated on base_users -- see the note above for why.
  --
  -- ⚠ THE ARMS DO NOT SUM TO THE PARENT. As of 2026-09-01 the parent holds 307
  -- cr_user_ids (258 study ids) but the roster only names 164 participants, of whom
  -- 101 ever produced an enrollment event -> 108 cr_user_ids get a mode. The other
  -- 199 parent users have no roster entry and stay in the parent cohort only.
  -- Per-arm resolution is also very uneven -- In-person 45/50 and Phone 40/50 resolved,
  -- but Online only 16/64. The 63 unresolved ids are not a formatting problem (a
  -- last-9-digit fuzzy match recovers exactly zero of them); those participants simply
  -- never fired joined_study or app_launch. Treat cross-arm comparisons of raw counts
  -- as unsafe until that Online gap is explained.
  -- -------------------------------------------------------------------------------
  study_mode_memberships AS (
    SELECT DISTINCT
      s.cr_user_id,
      CONCAT('study:World Bank Nigeria June 2026 - ', m.mode) AS cohort_name
    FROM `dataexploration-193817.user_data.cr_study_cohort` s
    JOIN `dataexploration-193817.user_data.cr_study_user_modes` m
      ON s.study_user_id = m.study_user_id
    WHERE s.cr_user_id IS NOT NULL
      AND s.confirmed_via_joined_study
      AND m.mode IS NOT NULL
  ),

  -- Final source set
  src AS (
    SELECT DISTINCT cr_user_id, cohort_name
    FROM (
      SELECT cr_user_id, cohort_name FROM rule_memberships
      UNION ALL
      SELECT cr_user_id, cohort_name FROM app_memberships
      UNION ALL
      SELECT cr_user_id, cohort_name FROM study_memberships
      UNION ALL
      SELECT cr_user_id, cohort_name FROM study_mode_memberships
    )
  )

  SELECT * FROM src
) AS src
ON tgt.cr_user_id = src.cr_user_id
AND tgt.cohort_name = src.cohort_name
WHEN NOT MATCHED THEN
  INSERT (cr_user_id, cohort_name)
  VALUES (src.cr_user_id, src.cohort_name);
