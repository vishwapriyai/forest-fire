import joblib
import pandas as pd


bundle = joblib.load("ml/models/model.pkl")
model = bundle["model"]
feature_columns = bundle["features"]


def predict_risk_frame(df):
    probs = model.predict_proba(df[feature_columns])
    if probs.shape[1] == 1:
        return probs[:, 0]
    return probs[:, 1]


def predict_risk(features):
    df = pd.DataFrame([features], columns=feature_columns)
    return float(predict_risk_frame(df)[0])
