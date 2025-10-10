#!/bin/bash
set -e

python add_ga.py
exec python -u -m streamlit run main.py --server.port=8501 --server.address=0.0.0.0
