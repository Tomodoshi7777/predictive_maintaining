"""
Industrial Predictive Maintenance - MLOps Setup

Run this script from the project root:

    python setup.py

Workflow:
    1. Create .venv
    2. Install requirements-mlops.txt
    3. Check required project files
    4. Check SQL/ODBC
    5. Configure MLOPS_SQL_CONNECTION
    6. Check model
    7. Run MLOps tests
    8. Report READY
    9. Launch Streamlit

Notes:
- SQL Server and Microsoft ODBC Driver 18 must be installed separately.
- The SQL password is requested interactively and is NOT saved to a project file.
- The configured connection is available to this setup process and the Streamlit
  process it launches.
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
REQUIREMENTS = ROOT / "requirements-mlops.txt"

if os.name == "nt":
    PYTHON = VENV / "Scripts" / "python.exe"
else:
    PYTHON = VENV / "bin" / "python"

REQUIRED_FILES = [
    ROOT / "requirements-mlops.txt",
    ROOT / "Dockerfile",
    ROOT / "app" / "streamlit_app.py",
    ROOT / "05_mlops" / "pipelines" / "inference.py",
    ROOT / "05_mlops" / "pipelines" / "feature_engineering.py",
    ROOT / "05_mlops" / "pipelines" / "model_loader.py",
    ROOT / "05_mlops" / "logging" / "prediction_logger.py",
    ROOT / "05_mlops" / "monitoring" / "drift_monitor.py",
    ROOT / "05_mlops" / "monitoring" / "alert_monitor.py",
    ROOT / "models" / "predictive_maintenance" / "v1" / "model.pkl",
    ROOT / "models" / "predictive_maintenance" / "v1" / "metadata.json",
    ROOT / "models" / "predictive_maintenance" / "v1" / "feature_schema.json",
]


def header() -> None:
    print("=" * 62)
    print(" Industrial Predictive Maintenance")
    print(" MLOps Setup")
    print("=" * 62)
    print()


def run(
    command: list[str],
    *,
    check: bool = True,
) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=ROOT, check=check)


def step(number: int, total: int, text: str) -> None:
    print(f"[{number}/{total}] {text}")


def create_venv() -> None:
    if VENV.exists() and PYTHON.exists():
        print("      Existing .venv found.")
        return

    print("      Creating virtual environment...")
    run([sys.executable, "-m", "venv", str(VENV)])


def install_requirements() -> None:
    if not REQUIREMENTS.exists():
        raise FileNotFoundError(
            f"Missing requirements file: {REQUIREMENTS}"
        )

    print("      Installing MLOps requirements...")
    run([str(PYTHON), "-m", "pip", "install", "--upgrade", "pip"])
    run(
        [
            str(PYTHON),
            "-m",
            "pip",
            "install",
            "-r",
            str(REQUIREMENTS),
        ]
    )


def check_required_files() -> None:
    missing = [
        str(path.relative_to(ROOT))
        for path in REQUIRED_FILES
        if not path.exists()
    ]

    if missing:
        print()
        print("Missing required files:")
        for item in missing:
            print(f"  - {item}")
        raise RuntimeError("Required project files are missing.")

    print("      All required project files found.")


def check_sql_odbc() -> None:
    print("      Checking pyodbc and installed ODBC drivers...")

    check_code = """
import pyodbc

print("      pyodbc: PASS")

drivers = pyodbc.drivers()
print("      Installed ODBC drivers:")
for driver in drivers:
    print(f"        - {driver}")

if not any(
    "ODBC Driver 18 for SQL Server" in driver
    for driver in drivers
):
    raise SystemExit(
        "ODBC Driver 18 for SQL Server was not found."
    )
"""

    run([str(PYTHON), "-c", check_code])


def configure_sql_connection() -> None:
    print()
    print("SQL Server configuration")
    print("-" * 40)
    print(
        "Enter the SQL Server connection details below."
    )
    print(
        "The password is used only for this setup session "
        "and is NOT saved to the project."
    )
    print()

    existing = os.environ.get("MLOPS_SQL_CONNECTION")

    if existing:
        answer = (
            input(
                "Existing MLOPS_SQL_CONNECTION found. "
                "Use it? [Y/n]: "
            )
            .strip()
            .lower()
        )

        if answer != "n":
            test_sql_connection()
            return

    server = (
        input("SQL Server host [localhost,1433]: ").strip()
        or "localhost,1433"
    )

    database = (
        input(
            "Database [PredictiveMaintenance]: "
        ).strip()
        or "PredictiveMaintenance"
    )

    username = (
        input("SQL username [mlops_user]: ").strip()
        or "mlops_user"
    )

    # Intentionally visible so the setup works reliably in VS Code
    # terminals and Code Runner-style environments.
    password = input("SQL password: ")

    if not password:
        raise RuntimeError(
            "SQL password cannot be empty."
        )

    connection = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
        "Encrypt=no;"
        "Connection Timeout=10;"
    )

    # Keep the connection only in the current Python process and
    # child processes launched by this script. Nothing is written
    # to a source file or project configuration file.
    os.environ["MLOPS_SQL_CONNECTION"] = connection

    print()
    test_sql_connection()


def test_sql_connection() -> None:
    test_code = """
import os
import pyodbc

connection = pyodbc.connect(
    os.environ["MLOPS_SQL_CONNECTION"]
)

cursor = connection.cursor()
cursor.execute(
    "SELECT DB_NAME(), SUSER_SNAME()"
)
row = cursor.fetchone()

print("SQL connection: PASS")
print(f"      Database: {row[0]}")
print(f"      Login: {row[1]}")

connection.close()
"""

    run([str(PYTHON), "-c", test_code])


def check_model() -> None:
    model_path = (
        ROOT
        / "models"
        / "predictive_maintenance"
        / "v1"
        / "model.pkl"
    )

    metadata_path = (
        ROOT
        / "models"
        / "predictive_maintenance"
        / "v1"
        / "metadata.json"
    )

    code = f"""
import json
import joblib

model_path = r"{model_path}"
metadata_path = r"{metadata_path}"

artifact = joblib.load(model_path)

with open(metadata_path, encoding="utf-8") as file:
    metadata = json.load(file)

assert isinstance(artifact, dict)
assert "model" in artifact
assert "feature_names" in artifact
assert "threshold" in artifact

assert metadata["model_version"] == "1.0.0"

print("Model artifact: PASS")
print("      Model:", metadata["model_name"])
print("      Version:", metadata["model_version"])
print("      Task:", metadata["task"])
"""

    run([str(PYTHON), "-c", code])


def run_tests() -> None:
    tests_dir = ROOT / "05_mlops" / "tests"

    if not tests_dir.exists():
        print(
            "      WARNING: 05_mlops/tests not found; "
            "test suite skipped."
        )
        return

    result = run(
        [
            str(PYTHON),
            "-m",
            "pytest",
            str(tests_dir),
            "-v",
        ],
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "MLOps tests failed. Fix the failing tests "
            "before using the dashboard."
        )


def launch_streamlit() -> None:
    app = ROOT / "app" / "streamlit_app.py"

    if not app.exists():
        raise FileNotFoundError(
            f"Streamlit application not found: {app}"
        )

    print()
    print("=" * 62)
    print(" MLOps setup complete")
    print("=" * 62)
    print()
    print("Dashboard:")
    print("  http://localhost:8501")
    print()
    print("Starting Streamlit...")
    print("Press Ctrl+C to stop the dashboard.")
    print()

    run(
        [
            str(PYTHON),
            "-m",
            "streamlit",
            "run",
            str(app),
            "--server.address=localhost",
            "--server.port=8501",
        ]
    )


def main() -> None:
    header()

    try:
        step(1, 9, "Creating .venv")
        create_venv()
        print("      PASS\n")

        step(2, 9, "Installing requirements")
        install_requirements()
        print("      PASS\n")

        step(3, 9, "Checking required files")
        check_required_files()
        print("      PASS\n")

        step(4, 9, "Checking SQL/ODBC")
        check_sql_odbc()
        print("      PASS\n")

        step(5, 9, "Configuring MLOPS_SQL_CONNECTION")
        configure_sql_connection()
        print("      PASS\n")

        step(6, 9, "Checking model")
        check_model()
        print("      PASS\n")

        step(7, 9, "Running MLOps tests")
        run_tests()
        print("      PASS\n")

        step(8, 9, "MLOps setup")
        print("      READY\n")

        step(9, 9, "Launching Streamlit")
        launch_streamlit()

    except KeyboardInterrupt:
        print("\nSetup cancelled by user.")
        raise SystemExit(1)

    except Exception as exc:
        print()
        print("=" * 62)
        print(" SETUP FAILED")
        print("=" * 62)
        print(f"\n{type(exc).__name__}: {exc}")
        print()
        print(
            "Fix the issue above and run "
            "'python setup.py' again."
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
