from pathlib import Path
import json

import joblib


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_DIR = (
    PROJECT_ROOT
    / "models"
    / "predictive_maintenance"
    / "v1"
)


def load_model_artifact():
    """Load the versioned predictive-maintenance model artifact."""
    model_path = MODEL_DIR / "model.pkl"

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    return joblib.load(model_path)


def load_metadata():
    """Load model metadata."""
    metadata_path = MODEL_DIR / "metadata.json"

    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata not found: {metadata_path}")

    with open(metadata_path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_feature_schema():
    """Load the model feature schema."""
    schema_path = MODEL_DIR / "feature_schema.json"

    if not schema_path.exists():
        raise FileNotFoundError(f"Feature schema not found: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as file:
        return json.load(file)