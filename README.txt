Tamil Nadu fire-only standalone project.

This project now does three main jobs:
- download or reuse the latest NASA fire extract
- expand that extract into a synthetic 10-year Tamil Nadu fire history for ML training
- predict short-range fire risk for Tamil Nadu and show it in the fire dashboard

Refresh everything:

python run_fire_refresh.py

Start the API:

uvicorn app.main:app --reload

Open the fire dashboard:

frontend/fire.html

Important generated outputs:
- data/processed/fire_history_10y.csv
- data/training/training_data.csv
- ml/models/model.pkl
- data/processed/recent_fire_last5.csv
- data/processed/recent_fire_last5.geojson
- data/processed/tamil_nadu_fire_predictions.csv
- data/processed/grid_predictions_day1.csv
- data/processed/grid_predictions_day2.csv
- data/processed/grid_predictions_day3.csv
- data/processed/grid_predictions_day4.csv
- data/processed/grid_predictions_day5.csv
- data/processed/grid_risk.geojson
