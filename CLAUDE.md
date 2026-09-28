# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Curious Learning's **external** Streamlit dashboard. It reports funnel/engagement metrics for
Feed the Monster (FTM) across two app families: the Curious Reader container app (`CR`, plus
`*-standalone` builds) and the older Unity app (`Unity`). Python 3.12.

## Commands

```bash
pip install -r requirements.txt
streamlit run main.py          # README still says Engagement.py — that file no longer exists

# container image (deployed to GCP)
docker build --no-cache --platform linux/amd64 -t gcr.io/dataexploration-193817/cl-data-dashboard:latest .
docker push gcr.io/dataexploration-193817/cl-data-dashboard:latest
```

There is no test suite, linter config, or CI in this repo. Formatting is black (VS Code setting only).

Note the Dockerfile does **not** COPY the working tree — it `git clone`s `main` from GitHub. Local
edits do not reach an image until they are pushed.

## Architecture

Two loosely coupled halves:

### 1. `queries/` — BigQuery SQL (project `dataexploration-193817`, dataset `user_data`)

This directory is the **shared** home for dashboard SQL across all the Curious Learning dashboard
repos (`cl-dashboard-internal`, `cl-dashboard-cohorts`, `cl-dashboard-engagement`, …). Do not create
per-repo copies — a divergent copy of `cr_cohorts_nightly.sql` silently kept a study cohort out of
the nightly MERGE.

Files here are the source of truth for BigQuery **scheduled queries**, but editing a file does not
deploy it. Push a change with:

```bash
bq update --transfer_config --params='{"query":"<file contents>"}' <config_id>
```

`queries/adhoc/` holds one-time and destructive scripts that are not scheduled (static cohort
rebuilds, roster loads, investigation queries).

Pipeline shape: a `*.sql` builds a table with `CREATE OR REPLACE TABLE`, and a paired `*_export.sql`
runs `EXPORT DATA` to `gs://user_data_parquet_cache/<table>/run_date=YYYY-MM-DD/<table>_*.parquet`.
The run-date folder exists to avoid shard collisions between runs; the dashboard reads only the
newest one.

Core tables: `cr_app_launch` (CR container launches, the LR source), `cr_user_progress` (FTM
gameplay per user), `unity_user_progress`, `cr_cohorts` (sticky cohort membership),
`cr_study_cohort` / `cr_study_user_modes` (study participants), plus the book pipeline
(`book_data_pipeline.sql`) and `ftm_event_timeline_full.sql`.

**Build order matters.** `cr_app_launch` must be rebuilt before `cr_user_progress` (which reads
`study_user_id` from it) and `cr_study_cohort` before `cr_cohorts_nightly` — the nightly job fails
loudly rather than skipping. Each SQL file's header comment records its grain, dependencies, and the
dated reasons for past schema changes; read it before editing.

**Grain traps.** `cr_app_launch` is one row per `(cr_user_id, user_pseudo_id, country, app_language,
first_open)` — never `COUNT(*)` it and call the result users, and never join it on `cr_user_id`
without collapsing to one row first (measured ~+61% fan-out). `cr_cohorts` is multi-row per user by
design (a study participant carries both a parent and a mode sub-cohort row).

**Attribution** (`source`, `campaign_id`) comes from GA4 `user_properties`, and is sparse (<1% of
users). Some comments in `cr_user_progress.sql` still credit the `raw_referrer_url` event param;
`cr_app_launch.sql` (the actual source) reads `user_properties`.

### 2. Python dashboard

Data flow: **GCS parquet → session_state dataframes → filtered cohort → funnel counts → charts.**
No BigQuery query runs on the hot path; BQ is used only for small lookup lists (languages,
countries, app versions) and marketing spend.

- `main.py` — entry point. Pages come from `.streamlit/pages.toml` via `st-pages`; add a page by
  creating `app_pages/<name>.py` and registering it there.
- `settings.py` — GCP credentials pulled from Secret Manager (not a keyfile), cached BigQuery
  client, `initialize()`, and campaign-data bootstrap.
- `users.py` — loads the three parquet caches into `st.session_state` as `df_cr_users`,
  `df_unity_users`, `df_cr_app_launch` via `ensure_user_data_initialized()`. Every page calls
  `initialize()` then `ensure_user_data_initialized()` first. This module also holds the messy
  reconciliation: `clean_cr_users_to_single_language()` collapses users who appear under multiple
  language/country combinations down to the row representing their furthest progress, and keeps
  `df_cr_app_launch` in sync with that choice (including overwriting CR `first_open`, which differs
  between the two tables).
- `metrics.py` — all counting. `select_user_dataframe()` decides which session dataframe an app
  selection maps to; `get_filtered_cohort()` returns `(cohort_df, cohort_df_LR)`;
  `get_cohort_totals_by_metric()` turns a filtered cohort into a single stat. Key asymmetry: for
  `CR`, **LR is counted from `df_cr_app_launch`** (app_launch is the first CR event carrying a
  language) while every later funnel step comes from `df_cr_users` — hence the second `_LR`
  dataframe threaded through nearly every function. Unity keys on `user_pseudo_id`; everything else
  on `cr_user_id`. "All apps" is computed by looping real apps and summing, with GPP/GCA weighted
  by LR — never by concatenating and recounting.
- `ui_components.py` — plotly figures (choropleth, top-10 bars, funnels), all built on
  `metrics.get_sorted_funnel_df`.
- `ui_widgets.py` — reusable sidebar selectors (each needs a unique `key=`), the definitions tables,
  and metric tiles.
- `campaigns.py` — Google + Facebook ad spend from BigQuery marketing tables. Country and language
  are **parsed out of the campaign name** by regex, which assumes the naming convention
  `"... : <language> - <country>"` in use since 2024-05-01.
- `add_ga.py` — injects a GA tag into Streamlit's own `index.html`. Standalone, not imported.

Funnel stats: `LR` reached, `DC`/`TS`/`SL` (CR-only intermediate events), `PC` puzzle completed,
`LA` ≥1 level, `RA` ≥25 levels, `GC` ≥90% game progress, `GPP` mean progress, `GCA` % of LA users
completing. The CR-only "large" funnel adds DC/TS/SL; Unity, standalones, and "All" use the compact
one (`ui_widgets.is_compact`).

Caching is `@st.cache_data(ttl="1d")` nearly everywhere, so data refreshes daily and a code change
to a cached function may not visibly take effect until the cache is cleared.
