# Tamil Nadu Fire Intelligence: Client Explanation

## 1. What this solution shows

This solution has two main views of fire activity in Tamil Nadu:

- **Observed fire heatmap**: shows the regions where fire activity was detected in the **last 5 days**
- **Predicted fire risk view**: shows the regions that the model estimates may be more fire-prone for the selected **forecast horizon day** from **Day 1 to Day 5**

So the platform is combining:

- what has **already happened recently**
- what the system thinks is **more likely to happen next**

---

## 2. How many days of data are used

There are two different time windows in this project:

### A. Recent observed fire data for the map

- The map heat layer uses **last 5 days of fire detections**
- This is taken from the latest NASA fire extract and filtered to the most recent 5-day period

### B. Historical data for ML model training

- The ML model is trained on a **10-year historical dataset**
- Important note:
  This is **not a direct 10-year NASA archive download**
- The current project creates a **synthetic 10-year training history** from the latest NASA extract by expanding it across prior years with controlled variations in date, location, fire intensity, and environmental conditions

This means:

- the **5-day heatmap** is based on recent observed fire data
- the **10-year dataset** is used to help train the prediction model

---

## 3. What data is used

The base fire source comes from the NASA fire extract stored in:

- `data/raw/fire/fire_raw.csv`

From this source, the system uses fire-related fields such as:

- `latitude`
- `longitude`
- `acq_date`
- `acq_time`
- `bright_ti4`
- `scan`
- `track`
- `confidence`
- `frp`
- `daynight`

The project then builds additional derived datasets such as:

- `data/processed/recent_fire_last5.csv`
- `data/processed/recent_fire_last5.geojson`
- `data/processed/fire_history_10y.csv`
- `data/training/training_data.csv`
- `data/processed/grid_predictions_day1.csv` to `grid_predictions_day5.csv`

---

## 4. Where the data comes from

The fire detections are fetched from:

- **NASA FIRMS** fire data feed

In this project, the fetch script is:

- [fetch_fire.py](</D:/Vish/AI_agent/Forest/fire_only/pipelines/fetch/fetch_fire.py>)

NASA FIRMS provides near-real-time satellite-based fire hotspot detections. These detections are commonly used to identify active or recent fire events.

---

## 5. What parameters the system uses

The prediction model uses these feature parameters:

- `latitude`
- `longitude`
- `month`
- `day_of_year`
- `is_daytime`
- `frp`
- `brightness`
- `scan`
- `track`
- `temp_c`
- `humidity`
- `wind_kph`
- `hotspot_score`
- `recent_fire_score`
- `seasonal_dryness`

### Meaning of the main parameters

- **latitude / longitude**:
  geographic location of the fire point or prediction cell

- **month / day_of_year**:
  seasonal time information used to capture dry or hotter periods

- **is_daytime**:
  whether the observation happened during day or night

- **frp**:
  Fire Radiative Power, which indicates how intense the fire is

- **brightness**:
  thermal brightness captured by the satellite sensor

- **scan / track**:
  sensor footprint dimensions that describe how the satellite observed that location

- **temp_c**:
  estimated temperature in degrees Celsius

- **humidity**:
  estimated atmospheric moisture level

- **wind_kph**:
  estimated wind speed in kilometers per hour

- **hotspot_score**:
  engineered score describing how close a location is to strong known fire hotspots

- **recent_fire_score**:
  engineered score describing how strongly recent fire activity influences that location

- **seasonal_dryness**:
  engineered score representing dry and fire-favorable conditions

---

## 6. What ML model is used

The current project uses:

- **Random Forest Classifier**

This is implemented in:

- [train_model.py](</D:/Vish/AI_agent/Forest/fire_only/ml/training/train_model.py>)

Random Forest is an ensemble machine learning model that combines many decision trees. It is often used when:

- there are multiple input factors
- relationships are non-linear
- we want a robust model without heavy tuning

### Does this solution use weather data?

Yes, **weather-related parameters are used in the prediction logic**.

In the current version of this project, the model uses these weather-style variables:

- `temp_c`
- `humidity`
- `wind_kph`
- `seasonal_dryness`

Important implementation note:

- the current standalone fire-only project does **not** depend on a live external weather feed for prediction
- instead, it generates **synthetic weather features** during training and forecasting based on:
  - date and season
  - location
  - hotspot intensity
  - recent fire influence

So weather is used as a modeling input, but in this version it is **derived inside the pipeline** rather than directly fetched from a production weather source during every prediction run.

This weather generation logic is in:

- [build_fire_history.py](</D:/Vish/AI_agent/Forest/fire_only/pipelines/processing/build_fire_history.py>)

---

## 7. How weather is used in prediction

Weather-related variables help the system estimate whether a place is more or less favorable for fire spread.

### How each weather parameter contributes

- **Temperature (`temp_c`)**
  Higher temperature generally increases dryness and fire susceptibility

- **Humidity**
  Lower humidity usually means vegetation and surrounding conditions are drier, which can increase fire risk

- **Wind speed (`wind_kph`)**
  Stronger wind can support faster spread and make a fire-prone area more risky

- **Seasonal dryness**
  This is a combined dryness indicator derived from temperature, humidity, and wind tendency

### In simple terms

The system does not predict risk from fire points alone. It also asks:

- is the area seasonally dry?
- is the area warm?
- is the air less humid?
- are recent fire patterns nearby?

That combination helps estimate whether a grid cell is more likely to become a fire-prone zone.

---

## 8. How the model predicts fire-prone zones

The prediction flow is:

1. Recent NASA fire detections are downloaded
2. The system prepares a 10-year historical training dataset
3. The Random Forest model is trained using the engineered features
4. Tamil Nadu is divided into grid cells
5. For each grid cell and each forecast day, the system calculates:
   - historical hotspot influence
   - recent fire influence
   - seasonal dryness
   - synthetic weather-like conditions
6. The ML model predicts a fire risk probability for each cell
7. That probability is combined with heuristic fire-risk signals to produce the final predicted fire risk

The forecast output is stored as:

- `grid_predictions_day1.csv`
- `grid_predictions_day2.csv`
- `grid_predictions_day3.csv`
- `grid_predictions_day4.csv`
- `grid_predictions_day5.csv`

---

## 9. How Random Forest predicts the fire risk

Random Forest does **not** predict fire using one single rule. It learns patterns from many examples.

### Simple explanation

The model is trained on many historical rows where each row contains:

- location
- seasonal timing
- fire intensity related values
- weather-related values
- hotspot influence values
- final label of whether that row is considered a fire-occurrence case

Random Forest then builds many separate decision trees.

Each tree asks questions such as:

- is the location in a historically hotter zone?
- is recent fire influence high?
- is humidity low?
- is FRP or hotspot strength high?
- is seasonal dryness high?

Each tree makes its own classification decision.

The forest then combines the results from all trees and returns a final probability-like risk score.

### In this project

The model output is treated as a fire-risk probability for each Tamil Nadu grid cell.

That risk is then blended with additional engineered fire-risk signals such as:

- historical hotspot score
- recent fire score
- seasonal dryness

This gives the final predicted fire-risk layer shown in the dashboard.

---

## 10. How the heat zones are created

There are two different map zone concepts:

### A. Observed heat zones

These are based on **actual recent fire detections** from the last 5 days.

The frontend converts those recent points into a **heatmap layer**, where:

- more concentrated detections create stronger heat intensity
- isolated or weaker areas create lighter heat intensity

This helps users quickly see where fire activity has recently happened.

### B. Predicted fire zones

These are based on model output over Tamil Nadu grid cells.

The system:

- divides Tamil Nadu into spatial cells
- predicts risk per cell
- shows those cells as forecast areas
- adds small hotspot markers only for stronger predicted cells so the map does not become visually cluttered

---

## 11. What is shown in the frontend

The frontend currently displays:

- **Last 5 days fire heatmap**
- **Predicted fire markers**
- **Prediction grid cells**
- **Forecast horizon slider** from Day 1 to Day 5
- **Observed fire count**
- **Average forecast risk**
- **High-risk zone count**
- **Latest observed day**
- **Top predicted zones list**
- **Recent fire notes list**

So the client sees both:

- observed situation
- short-range forecast situation

in one interface

---

## 12. Explanation of technical terms

### FRP

**FRP** means **Fire Radiative Power**.

Simple explanation:

- it measures how much energy the fire is radiating
- higher FRP usually means a stronger or more intense fire

In the dashboard, FRP is helpful because it gives an idea of how severe a fire detection may be.

### Confidence

**Confidence** is the confidence level of the satellite fire detection.

Simple explanation:

- it tells us how sure the source system is that the hotspot is truly a fire-related detection

In the source data, confidence is usually expressed as categories such as:

- `l` = low
- `n` = nominal
- `h` = high

Higher confidence means the detection is more likely to be a true fire signal.

### Hotspot

A **hotspot** means a location where the satellite observed thermal activity consistent with fire.

### Heatmap

A **heatmap** is a visual layer that uses color intensity to show where events are concentrated.

### Forecast horizon

The **forecast horizon** means how many days ahead the prediction is being shown.

For example:

- Day 1 = tomorrow or next immediate prediction window
- Day 5 = farther short-range prediction window

---

## 13. Important business note for the client

The solution is a **decision-support tool**, not a certified fire-warning system.

It should be presented as:

- a fire monitoring and early-risk visualization platform
- a way to prioritize attention and identify likely risk zones

It should not be presented as:

- an official emergency alert system
- a guaranteed fire-occurrence predictor

Also, the current 10-year training history is **synthetically expanded** from the available NASA extract. If the client wants a stronger production-grade model, the next step would be to train on a true long-term historical archive plus validated weather and land-cover data.

---

## 14. Short client summary

This platform uses NASA satellite fire detection data to show:

- where fire activity occurred in the **last 5 days**
- where fire risk is **predicted** across Tamil Nadu for the **next 5 forecast days**

It trains a **Random Forest machine learning model** on a generated 10-year historical fire-risk dataset built from the NASA extract and derived fire-risk parameters. The frontend shows both observed fire heat and predicted fire-prone regions in a simple operational map view.
