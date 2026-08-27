# cl-data-dashboard
Curious Learning External Dashboard

**To run locally**

1. Install python 3.12.0 - https://www.python.org/downloads/release/python-3123/
2. git clone https://github.com/curiouslearning/cl-data-dashboard.git
3. cd to ./cl-data-dashboard
4. pip install -r requirements.txt
5. streamlit run Engagement.py

OR 
docker build --no-cache --platform linux/amd64  -t gcr.io/dataexploration-193817/cl-data-dashboard:latest .
docker push gcr.io/dataexploration-193817/cl-data-dashboard:latest

**Queries**

`queries/` is the single home for dashboard SQL across all the Curious Learning
dashboard repos (`cl-dashboard-internal`, `cl-dashboard-cohorts`,
`cl-dashboard-engagement`, …). Do not keep per-repo copies — a divergent copy of
`cr_cohorts_nightly.sql` in `cl-dashboard-cohorts` is what silently kept the
`study:World Bank Nigeria June 2026` cohort out of the nightly MERGE.

Files here are the source of truth for the BigQuery **scheduled queries**; editing
one does not deploy it. Push a change with:

    bq update --transfer_config --params='{"query":"<file contents>"}' <config_id>

`queries/adhoc/` holds one-time and destructive scripts that are not scheduled.
