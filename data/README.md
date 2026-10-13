# Data sources – CNC milling machine

## Used: NASA Milling Data Set (`mill.mat`)

- Machine: **Matsuura MC-510V** machining center, experiments by UC Berkeley (A. Agogino, K. Goebel).
- Source: NASA Prognostics Center of Excellence data repository –
  https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/
- Direct download (used by `scripts/download_data.py`): https://phm-datasets.s3.amazonaws.com/NASA/3.+Milling.zip
- **Run-to-failure**: 16 tools (cases) used from new to worn, 167 cuts (runs) in total.
  After some cuts the tool flank wear **VB** was measured with a microscope.
- 6 sensors per cut, 9000 samples each: spindle motor current AC/DC, vibration (table, spindle),
  acoustic emission (table, spindle).
- Cutting conditions: depth of cut 0.75 / 1.5 mm, feed 0.25 / 0.5 mm/rev, material cast iron / steel.

Generated files:

- `milling_features.csv` – one row per cut, made by `notebooks/01_data_preparation.ipynb`.
- `historian.db` – SQLite historian written by the API (reset at each start).

## Other sources for the same kind of machine (not used)

- **AI4I 2020 Predictive Maintenance** (UCI): synthetic milling-machine snapshots with 5 failure modes.
  Good for failure *detection*, not for RUL (no time series). https://archive.ics.uci.edu/dataset/601
- **PHM Society 2010 Data Challenge – CNC milling cutter wear**: high-frequency force / vibration /
  acoustic signals, 6 cutters run to failure (several GB). https://phmsociety.org/phm_competition/2010-phm-society-conference-data-challenge/
- **CNC Mill Tool Wear (Univ. of Michigan, Kaggle)**: 18 experiments, worn vs unworn tools.
  https://www.kaggle.com/datasets/shasun/tool-wear-detection-in-cnc-mill
