#!/bin/bash
set -e

exec streamlit run main.py --server.port="$PORT" --server.address=0.0.0.0