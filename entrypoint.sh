#!/bin/bash
set -e

python add_ga.py
exec streamlit run main.py --server.port="$PORT" --server.address=0.0.0.0