# Tamil Nadu Fire Intelligence Platform 🔥

An interactive geospatial predictive analytics platform designed to monitor recent forest fire activities and forecast wildfire risks across the state of Tamil Nadu, India, using satellite telemetry and machine learning.

---

## 🚀 Key Features

* **Real-time Fire Heatmap**: Visualizes observed fire hotspots from the **last 5 days** using active telemetry extracts from NASA.
* **Predictive Risk Forecast (Days 1–5)**: Projects upcoming regional fire susceptibility using a trained machine learning model, helping authorities allocate resources proactively.
* **Geospatial Analytics Dashboard**: Leaflet-based interactive mapping interface displaying grids, district boundaries, observed counts, and forecast scores.
* **Automated Data Refresher**: Ingests fresh telemetry, builds a synthetic 10-year historical training dataset, trains the model, and outputs new predictions with a single script execution.

---

## 🛠️ Tech Stack

* **Backend**: FastAPI (Python)
* **Data Engineering & ETL**: Pandas, NumPy, Geopandas, Shapely, Requests
* **Machine Learning**: Scikit-Learn (Random Forest Classifier), Joblib
* **Frontend**: HTML5, Vanilla CSS, JavaScript, Leaflet.js, Leaflet Heatmap Layer
* **Data Sources**: NASA FIRMS (Near Real-Time Active Fire Data / VIIRS S-NRT)

---

## 📁 Project Structure

```text
fire_only/
├── 📁 app/                    # FastAPI backend codebase
│   ├── 📁 core/               # Grid generation and basic risk engines
│   ├── 📁 services/           # Data refresh sync controllers
│   ├── 📁 api/                # REST endpoints (prediction & risk summaries)
│   └── main.py                # Server entry point
├── 📁 data/                   # Data storage directory (Generated dynamically)
│   ├── 📁 raw/                # NASA FIRMS raw extracts
│   ├── 📁 processed/          # Cached forecast grids and geoJSON layers
│   └── 📁 training/           # Pre-processed tabular training files
├── 📁 frontend/               # Dashboard templates & static assets
│   ├── fire.html              # Main Tamil Nadu fire dashboard view
│   ├── tamil_nadu_districts.geojson
│   └── 📁 js/                 # Map and API fetching script layers
├── 📁 ml/                     # Machine learning workflows
│   ├── 📁 training/           # Data preparation & model training scripts
│   ├── 📁 inference/          # Batch prediction execution modules
│   └── 📁 models/             # Serialized model binaries (model.pkl)
├── 📁 pipelines/              # Telemetry extraction scripts
│   ├── 📁 fetch/              # NASA FIRMS API ingestion script
│   └── 📁 processing/         # Historical synthesis & weather simulator
├── run_fire_refresh.py        # Pipeline orchestrator (Fetch -> Prep -> Train -> Predict)
└── requirements.txt           # Python dependencies list
```

---

## ⚙️ Setup & Installation

### 1. Prerequisites
Ensure you have **Python 3.9+** installed on your system.

### 2. Clone and Setup Environment
Navigate to the project root directory and create a virtual environment:
```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

---

## 🏃 Running the Application

### 1. Ingest Data, Train, & Predict
Execute the orchestrator script to download raw NASA data, expand the historical dataset, train the RandomForest model, and compute the 5-day predictive grids:
```bash
python run_fire_refresh.py
```

### 2. Start the Backend API Server
Launch the FastAPI server using Uvicorn:
```bash
uvicorn app.main:app --reload
```
*The API will be available at:* `http://127.0.0.1:8000`

### 3. Launch the Dashboard
Simply open the dashboard file in a web browser:
- Main Interface: `frontend/fire.html`
- Or access via the served backend endpoints if configured.

---

## 🧠 Machine Learning Details

The predictive risk model determines fire susceptibility using:
1. **Spatial Proximity (`hotspot_score`)**: A Gaussian-decay kernel scoring mechanism estimating the geographic distance to historical fire hubs.
2. **Recent Fire Influence (`recent_fire_score`)**: Captures short-range persistence based on active clusters over the last 5 days.
3. **Synthetic Weather Matrices**: Simulates temperature (`temp_c`), humidity (`humidity`), and wind speed (`wind_kph`) using seasonal sine waves combined with local coordinates.
4. **Ensemble Classifier**: A Random Forest Classifier with 240 estimators optimized using class balancing to handle high-imbalance spatial prediction grids.

---

## ⚖️ License & Disclaimers

This project is a decision-support prototype tool utilizing satellite telemetry and synthesized features. It is intended for monitoring and early-risk visualization purposes, and should not be used as an official emergency warning system.
