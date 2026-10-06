import sys
from pathlib import Path

import pandas as pd

from feature_engineering import engineer_features
from model_loader import load_model_artifact

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "logging"))

from prediction_logger import log_prediction


def predict(machine_data: dict) -> dict:
    """Run predictive-maintenance inference for one machine record."""

    input_data = pd.DataFrame([machine_data])

    artifact = load_model_artifact()

    features = engineer_features(input_data)

    expected_features = artifact["feature_names"]

    if features.columns.tolist() != expected_features:
        raise ValueError("Feature schema mismatch")

    model = artifact["model"]
    threshold = artifact["threshold"]

    failure_probability = float(
        model.predict_proba(features)[0, 1]
    )

    prediction = int(failure_probability >= threshold)

    result = {
        "prediction": prediction,
        "failure_probability": round(failure_probability, 4),
        "threshold": float(threshold),
        "model_name": artifact["model_name"],
    }

    log_prediction(machine_data, result)

    return result


if __name__ == "__main__":
    sample_machine = {
        "Air temperature [K]": 298.1,
        "Process temperature [K]": 308.6,
        "Rotational speed [rpm]": 1550,
        "Torque [Nm]": 42.8,
        "Tool wear [min]": 120,
        "Type": "M",
    }

    result = predict(sample_machine)

    print("Inference: PASS")
    print(result)