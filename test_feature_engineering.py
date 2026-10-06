from pathlib import Path

import joblib
import pandas as pd

from feature_engineering import engineer_features


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "predictive_maintenance"
    / "v1"
    / "model.pkl"
)


def main():
    sample = pd.DataFrame([{
        "Air temperature [K]": 298.1,
        "Process temperature [K]": 308.6,
        "Rotational speed [rpm]": 1550,
        "Torque [Nm]": 42.8,
        "Tool wear [min]": 120,
        "Type": "M",
    }])

    artifact = joblib.load(MODEL_PATH)

    features = engineer_features(sample)
    expected = artifact["feature_names"]

    if features.columns.tolist() != expected:
        raise ValueError("Feature schema mismatch")

    model = artifact["model"]
    threshold = artifact["threshold"]

    probability = model.predict_proba(features)[0, 1]
    prediction = int(probability >= threshold)

    print("Feature contract: PASS")
    print("Features:", len(features.columns))
    print("Failure probability:", round(probability, 4))
    print("Threshold:", threshold)
    print("Prediction:", prediction)
    print("Inference test: PASS")


if __name__ == "__main__":
    main()