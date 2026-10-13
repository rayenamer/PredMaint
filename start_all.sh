#!/usr/bin/env bash
# Starts everything: Python env, model training (if needed), FastAPI and the React dashboard.
# Usage: ./start_all.sh          (Ctrl+C stops both services)
#        ./start_all.sh --retrain (re-run the notebooks even if models exist)
set -e
cd "$(dirname "$0")"

echo "==> 1/4 Python environment"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt

echo "==> 2/4 Dataset"
python scripts/download_data.py

echo "==> 3/4 Models"
if [ "$1" == "--retrain" ] || [ ! -f models/rul_predictor.joblib ] || [ ! -f data/milling_features.csv ]; then
  mkdir -p models
  for notebook in notebooks/*.ipynb; do
    echo "    running $notebook"
    jupyter nbconvert --to notebook --execute --inplace "$notebook" --log-level=WARN
  done
else
  echo "    models already trained (use --retrain to train again)"
fi

echo "==> 4/4 Dashboard dependencies"
if [ ! -d dashboard/node_modules ]; then
  (cd dashboard && npm install)
fi

# Stop both services when this script stops
trap 'echo; echo "Stopping..."; kill $API_PID $UI_PID 2>/dev/null' EXIT INT TERM

uvicorn api.main:app --port 8000 &
API_PID=$!

(cd dashboard && npm run dev -- --host) &
UI_PID=$!

echo
echo "  API        -> http://localhost:8000/docs"
echo "  Dashboard  -> http://localhost:5173"
echo "  Notebooks  -> source .venv/bin/activate && jupyter lab notebooks/"
echo

wait
