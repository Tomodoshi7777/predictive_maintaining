import os
from datetime import datetime, timezone

import pyodbc


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


def log_prediction(machine_data: dict, result: dict) -> None:
    """Store a model prediction in SQL Server."""

    query = """
        INSERT INTO dbo.predictions (
            timestamp_utc,
            model_version,
            air_temperature,
            process_temperature,
            rotational_speed,
            torque,
            tool_wear,
            machine_type,
            failure_probability,
            threshold,
            prediction
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    values = (
        datetime.now(timezone.utc),
        "1.0.0",
        float(machine_data["Air temperature [K]"]),
        float(machine_data["Process temperature [K]"]),
        float(machine_data["Rotational speed [rpm]"]),
        float(machine_data["Torque [Nm]"]),
        float(machine_data["Tool wear [min]"]),
        machine_data["Type"],
        float(result["failure_probability"]),
        float(result["threshold"]),
        int(result["prediction"]),
    )

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(query, values)
        connection.commit()


if __name__ == "__main__":
    print("Prediction logger module: PASS")