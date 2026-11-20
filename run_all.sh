#!/usr/bin/env bash
# Reproduce every output from the raw MTO file. Python 3.10+, pandas, numpy, openpyxl.
set -euo pipefail
mkdir -p out docs
python3 src/prepare.py data/bridge_condition_open_data_2020_en.csv
python3 src/analyse.py > out/analysis_log.txt
python3 src/backtest.py
python3 src/build_report.py
cp out/index.html docs/index.html
python3 -m unittest discover -s tests
