import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PIPELINES_DIR = PROJECT_ROOT / "05_mlops" / "pipelines"
LOGGING_DIR = PROJECT_ROOT / "05_mlops" / "logging"

sys.path.insert(0, str(PIPELINES_DIR))
sys.path.insert(0, str(LOGGING_DIR))

from feature_engineering import engineer_features
from model_loader import (
    load_feature_schema,
    load_metadata,
    load_model_artifact,
)


def test_model_artifact():
    artifact = load_model_artifact()

    assert artifact is not None
    assert artifact["model"] is not None
    assert artifact["model_name"] == "Gradient Boosting"
    assert len(artifact["feature_names"]) == 20

    print("PASS: Model artifact")


def test_metadata():
    metadata = load_metadata()

    assert metadata["model_version"] == "1.0.0"
    assert metadata["model_name"] == "Gradient Boosting"

    print("PASS: Metadata")


def test_feature_schema():
    schema = load_feature_schema()

    assert schema["model_version"] == "1.0.0"
    assert schema["feature_count"] == 20
    assert len(schema["features"]) == 20

    print("PASS: Feature schema")


def test_feature_engineering():
    machine = pd.DataFrame(
        [
            {
                "Air temperature [K]": 298.1,
                "Process temperature [K]": 308.6,
                "Rotational speed [rpm]": 1550,
                "Torque [Nm]": 42.8,
                "Tool wear [min]": 120,
                "Type": "M",
            }
        ]
    )

    features = engineer_features(machine)

    assert len(features) == 1
    assert len(features.columns) == 20

    print("PASS: Feature engineering")


def main():
    print("=" * 50)
    print("MLOps Test Suite")
    print("=" * 50)

    test_model_artifact()
    test_metadata()
    test_feature_schema()
    test_feature_engineering()

    print("=" * 50)
    print("ALL TESTS PASSED")
    print("=" * 50)


if __name__ == "__main__":
    main()