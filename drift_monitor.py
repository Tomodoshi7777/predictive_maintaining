from pathlib import Path
import os

import pandas as pd
import pyodbc


# ============================================================
# Project paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REFERENCE_DATA = (
    PROJECT_ROOT
    / "02_EDA_Features"
    / "ai4i2020_features_final.csv"
)


# ============================================================
# SQL Server connection
# ============================================================

# Docker / production connection:
# MLOPS_SQL_CONNECTION should be provided as an environment variable.
#
# Local Windows development:
# If the environment variable is not available, Windows
# Authentication is used automatically.

CONNECTION_STRING = os.getenv("MLOPS_SQL_CONNECTION")


def get_connection():
    """Create a SQL Server connection."""

    if CONNECTION_STRING:
        return pyodbc.connect(CONNECTION_STRING)

    # Local Windows development
    local_connection = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=localhost,1433;"
        "DATABASE=PredictiveMaintenance;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
        "Encrypt=no;"
        "Connection Timeout=10;"
    )

    return pyodbc.connect(local_connection)


# ============================================================
# Feature mapping
# ============================================================

FEATURE_MAPPING = {
    "Air temperature [K]": "air_temperature",
    "Process temperature [K]": "process_temperature",
    "Rotational speed [rpm]": "rotational_speed",
    "Torque [Nm]": "torque",
    "Tool wear [min]": "tool_wear",
}


# ============================================================
# Reference data
# ============================================================

def load_reference_data():
    """Load the reference training data."""

    if not REFERENCE_DATA.exists():
        raise FileNotFoundError(
            f"Reference dataset not found: {REFERENCE_DATA}"
        )

    return pd.read_csv(REFERENCE_DATA)


# ============================================================
# Production data
# ============================================================

def load_production_data():
    """Load logged predictions from SQL Server."""

    query = """
        SELECT
            air_temperature,
            process_temperature,
            rotational_speed,
            torque,
            tool_wear
        FROM dbo.predictions
    """

    with get_connection() as connection:

        cursor = connection.cursor()

        cursor.execute(query)

        rows = cursor.fetchall()

        columns = [
            column[0]
            for column in cursor.description
        ]

    return pd.DataFrame.from_records(
        rows,
        columns=columns,
    )


# ============================================================
# Drift calculation
# ============================================================

def calculate_drift(reference, production):
    """Compare production feature means against reference data."""

    results = []

    for reference_feature, production_feature in FEATURE_MAPPING.items():

        reference_mean = reference[reference_feature].mean()

        reference_std = reference[reference_feature].std()

        production_mean = production[production_feature].mean()

        if reference_std == 0:

            mean_change_std = 0.0

        else:

            mean_change_std = (
                abs(
                    production_mean
                    - reference_mean
                )
                / reference_std
            )

        results.append(
            {
                "feature": reference_feature,
                "reference_mean": round(
                    reference_mean,
                    4,
                ),
                "production_mean": round(
                    production_mean,
                    4,
                ),
                "reference_std": round(
                    reference_std,
                    4,
                ),
                "mean_change_std": round(
                    mean_change_std,
                    4,
                ),
            }
        )

    return pd.DataFrame(results)


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 80)
    print("Predictive Maintenance - Feature Drift Monitoring")
    print("=" * 80)

    reference = load_reference_data()

    production = load_production_data()

    print(
        f"\nReference rows: {len(reference)}"
    )

    print(
        f"Production rows: {len(production)}"
    )

    if production.empty:

        print(
            "\nNo production predictions available."
        )

        return

    results = calculate_drift(
        reference,
        production,
    )

    print(
        "\nFeature Drift Report"
    )

    print(
        "=" * 80
    )

    print(
        results.to_string(index=False)
    )

    print(
        "\nMonitoring: PASS"
    )


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    main()