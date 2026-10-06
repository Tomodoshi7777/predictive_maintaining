from pathlib import Path
import os

import pyodbc


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CONNECTION_STRING = os.getenv("MLOPS_SQL_CONNECTION")


def get_connection():
    """Create a SQL Server connection."""

    if CONNECTION_STRING:
        return pyodbc.connect(CONNECTION_STRING)

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


def calculate_alert_rate():
    """Calculate the percentage of predictions flagged as failures."""

    query = """
        SELECT
            COUNT(*) AS total_predictions,
            SUM(CAST(prediction AS INT)) AS failure_alerts
        FROM dbo.predictions
    """

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(query)

        row = cursor.fetchone()

    total_predictions = row[0] or 0
    failure_alerts = row[1] or 0

    if total_predictions == 0:
        return {
            "total_predictions": 0,
            "failure_alerts": 0,
            "alert_rate": 0.0,
        }

    alert_rate = failure_alerts / total_predictions

    return {
        "total_predictions": total_predictions,
        "failure_alerts": failure_alerts,
        "alert_rate": alert_rate,
    }


def main():
    result = calculate_alert_rate()

    print("Alert Rate Monitoring")
    print("=" * 40)
    print("Total predictions:", result["total_predictions"])
    print("Failure alerts:", result["failure_alerts"])
    print("Alert rate:", f"{result['alert_rate']:.2%}")
    print("\nMonitoring: PASS")


if __name__ == "__main__":
    main()