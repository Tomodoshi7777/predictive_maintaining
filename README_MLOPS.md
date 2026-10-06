# MLOps --- Industrial Predictive Maintenance

## 1. Overview

This directory contains the MLOps layer for the Industrial Predictive
Maintenance project.

The MLOps implementation provides:

-   Versioned ML model artifact
-   Model metadata and feature schema
-   Reproducible inference pipeline
-   Feature engineering during inference
-   Prediction logging to SQL Server
-   Feature drift monitoring
-   Failure alert-rate monitoring
-   Streamlit machine-health dashboard
-   Dockerized execution
-   Reproducible dependency management
-   Basic MLOps tests

The deployed/champion model is the **Gradient Boosting** classifier from
the ML pipeline.

------------------------------------------------------------------------

# 2. MLOps Architecture

``` text
                    Industrial Sensor Input
                             |
                             v
                    Streamlit Application
                             |
                             v
                       Inference API
                             |
                 +-----------+-----------+
                 |                       |
                 v                       v
        Feature Engineering        Versioned Model
                 |                       |
                 +-----------+-----------+
                             |
                             v
                    Failure Probability
                             |
                             v
                       Threshold
                             |
                    +--------+--------+
                    |                 |
                    v                 v
              Prediction        SQL Logging
                                      |
                                      v
                           SQL Server / predictions
                                      |
                         +------------+------------+
                         |                         |
                         v                         v
                 Drift Monitoring          Alert Monitoring
```

------------------------------------------------------------------------

# 3. Project Structure

``` text
Final Project (1)/
│
├── 01_Data_Engineering/
├── 02_EDA_Features/
├── 03_ML/
├── 04_DL/
│
├── 05_mlops/
│   ├── logging/
│   │   ├── prediction_logger.py
│   │   └── prediction_schema.sql
│   │
│   ├── monitoring/
│   │   ├── drift_monitor.py
│   │   └── alert_monitor.py
│   │
│   ├── pipelines/
│   │   ├── feature_engineering.py
│   │   ├── model_loader.py
│   │   └── inference.py
│   │
│   └── tests/
│       └── test_mlops.py
│
├── models/
│   └── predictive_maintenance/
│       └── v1/
│           ├── model.pkl
│           ├── metadata.json
│           └── feature_schema.json
│
├── app/
│   └── streamlit_app.py
│
├── cloud/
│   ├── README.md
│   └── deployment.md
│
├── Dockerfile
├── requirements.txt
├── requirements-mlops.txt
├── .gitignore
└── README.md
```

------------------------------------------------------------------------

# 4. Model Versioning

The production inference artifact is stored at:

``` text
models/predictive_maintenance/v1/model.pkl
```

Associated metadata:

``` text
models/predictive_maintenance/v1/metadata.json
models/predictive_maintenance/v1/feature_schema.json
```

Current model metadata:

``` text
Model: Gradient Boosting
Version: 1.0.0
Task: Binary Classification
Target: Machine failure
Framework: scikit-learn
Artifact format: joblib
```

The model artifact contains the trained model, threshold, feature names,
and model configuration required by the inference pipeline.

------------------------------------------------------------------------

# 5. Requirements

The MLOps environment uses:

``` text
numpy
pandas
scikit-learn==1.9.0
joblib
pyodbc
streamlit
```

Install the MLOps dependencies with:

``` powershell
pip install -r requirements-mlops.txt
```

For the complete project environment:

``` powershell
pip install -r requirements.txt
```

------------------------------------------------------------------------

# 6. SQL Server Setup

The MLOps system stores prediction history in SQL Server.

Expected database:

``` text
PredictiveMaintenance
```

Expected table:

``` text
dbo.predictions
```

The schema is provided in:

``` text
05_mlops/logging/prediction_schema.sql
```

## Step 6.1 --- Create the database/table

Open SQL Server Management Studio (SSMS), connect to the SQL Server
instance, and run the SQL script:

``` text
05_mlops/logging/prediction_schema.sql
```

Make sure the `dbo.predictions` table exists before running inference.

## Step 6.2 --- Database connection

The application uses:

``` text
MLOPS_SQL_CONNECTION
```

This keeps database configuration outside the source code.

Example PowerShell configuration:

``` powershell
$env:MLOPS_SQL_CONNECTION="DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost,1433;DATABASE=PredictiveMaintenance;UID=mlops_user;PWD=YOUR_PASSWORD;TrustServerCertificate=yes;Encrypt=no;Connection Timeout=10;"
```

Replace `YOUR_PASSWORD` with the actual local password.

**Never commit the real password to GitHub.**

For local Windows-authenticated monitoring, if `MLOPS_SQL_CONNECTION` is
not set, `drift_monitor.py` and related local monitoring logic can use
the configured local Windows authentication fallback.

------------------------------------------------------------------------

# 7. Step-by-Step: Run MLOps Locally

## Step 1 --- Open the project

``` powershell
cd "C:\Users\munzi\Desktop\Final Project (1)"
```

## Step 2 --- Verify Python

``` powershell
python --version
```

Python should be compatible with the installed project dependencies.

## Step 3 --- Install MLOps dependencies

``` powershell
pip install -r requirements-mlops.txt
```

## Step 4 --- Verify the model artifact

``` powershell
Test-Path "models\predictive_maintenance\v1\model.pkl"
```

Expected:

``` text
True
```

Also verify metadata:

``` powershell
Test-Path "models\predictive_maintenance\v1\metadata.json"
Test-Path "models\predictive_maintenance\v1\feature_schema.json"
```

Both should return:

``` text
True
```

## Step 5 --- Configure SQL Server

Set the SQL connection:

``` powershell
$env:MLOPS_SQL_CONNECTION="DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost,1433;DATABASE=PredictiveMaintenance;UID=mlops_user;PWD=YOUR_PASSWORD;TrustServerCertificate=yes;Encrypt=no;Connection Timeout=10;"
```

Do not put the real password inside source files.

## Step 6 --- Test inference

Run:

``` powershell
python 05_mlops\pipelines\inference.py
```

A successful run should report a successful prediction and return values
including:

``` text
prediction
failure_probability
threshold
model_name
```

The prediction is also written to:

``` text
dbo.predictions
```

------------------------------------------------------------------------

# 8. Run the Streamlit Dashboard

The Streamlit application is:

``` text
app/streamlit_app.py
```

Start it with:

``` powershell
streamlit run app\streamlit_app.py
```

The application will start a local web server.

Open the displayed local address in a browser.

## Dashboard workflow

1.  Enter machine sensor values.
2.  Select machine type (`L`, `M`, or `H`).
3.  Click the prediction button.
4.  The application loads model version `1.0.0`.
5.  Features are engineered using the same inference pipeline.
6.  The model calculates failure probability.
7.  The stored decision threshold is applied.
8.  The result is displayed.
9.  The prediction is logged to SQL Server.

------------------------------------------------------------------------

# 9. Verify Prediction Logging

After making a prediction, open SSMS and run:

``` sql
SELECT TOP 20
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
FROM dbo.predictions
ORDER BY timestamp_utc DESC;
```

A new row should appear after each successful prediction.

------------------------------------------------------------------------

# 10. Feature Drift Monitoring

The drift monitor compares production prediction features against the
reference dataset.

Run:

``` powershell
python 05_mlops\monitoring\drift_monitor.py
```

The report contains:

-   Reference row count
-   Production row count
-   Reference mean
-   Production mean
-   Reference standard deviation
-   Mean change measured in standard deviations

Example output format:

``` text
Predictive Maintenance - Feature Drift Monitoring

Reference rows: ...
Production rows: ...

Feature Drift Report

feature                     reference_mean   production_mean   ...
Air temperature [K]         ...
Process temperature [K]     ...
Rotational speed [rpm]      ...
Torque [Nm]                 ...
Tool wear [min]             ...

Monitoring: PASS
```

`Monitoring: PASS` means the monitoring script executed successfully. It
does **not** mean that every feature has zero drift.

The reference dataset is:

``` text
02_EDA_Features/ai4i2020_features_final.csv
```

------------------------------------------------------------------------

# 11. Failure Alert-Rate Monitoring

The alert monitor calculates the percentage of logged predictions
classified as failures.

Run:

``` powershell
python 05_mlops\monitoring\alert_monitor.py
```

Example:

``` text
Alert Rate Monitoring
========================================
Total predictions: 6
Failure alerts: 1
Alert rate: 16.67%

Monitoring: PASS
```

The calculation is based on:

``` text
failure alerts / total predictions
```

This metric can be used as a production monitoring signal.

------------------------------------------------------------------------

# 12. Run MLOps Tests

Run the test suite from the project root.

If using pytest:

``` powershell
pytest 05_mlops\tests -v
```

The tests cover core MLOps components such as:

-   Model artifact availability
-   Model metadata
-   Feature schema
-   Feature engineering
-   Inference pipeline components

A successful test run should finish without test failures.

------------------------------------------------------------------------

# 13. Docker

The project includes a Dockerfile for reproducible MLOps execution.

## Step 13.1 --- Build the image

From the project root:

``` powershell
docker buildx build --load -t predictive-maintenance-mlops:1.1.0 .
```

Verify:

``` powershell
docker images | findstr predictive-maintenance
```

## Step 13.2 --- Run Streamlit

First configure the SQL connection in PowerShell:

``` powershell
$env:MLOPS_SQL_CONNECTION="DRIVER={ODBC Driver 18 for SQL Server};SERVER=host.docker.internal,1433;DATABASE=PredictiveMaintenance;UID=mlops_user;PWD=YOUR_PASSWORD;TrustServerCertificate=yes;Encrypt=no;Connection Timeout=10;"
```

Run:

``` powershell
docker run --rm `
  -p 8501:8501 `
  -e MLOPS_SQL_CONNECTION="$env:MLOPS_SQL_CONNECTION" `
  predictive-maintenance-mlops:1.1.0
```

Open:

``` text
http://localhost:8501
```

The Dockerized Streamlit dashboard should be able to run inference and
log predictions to SQL Server.

------------------------------------------------------------------------

# 14. Docker Inference Test

If testing the inference container directly rather than Streamlit:

``` powershell
docker run --rm `
  -e MLOPS_SQL_CONNECTION="$env:MLOPS_SQL_CONNECTION" `
  predictive-maintenance-mlops:1.1.0
```

A successful inference run should produce a prediction result similar
to:

``` text
prediction: 0
failure_probability: ...
threshold: ...
model_name: Gradient Boosting
```

------------------------------------------------------------------------

# 15. Complete End-to-End Test

For a complete local validation, use this order:

## 1. Start SQL Server

Make sure SQL Server is running and the database is available.

## 2. Set the connection

``` powershell
$env:MLOPS_SQL_CONNECTION="DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost,1433;DATABASE=PredictiveMaintenance;UID=mlops_user;PWD=YOUR_PASSWORD;TrustServerCertificate=yes;Encrypt=no;Connection Timeout=10;"
```

## 3. Run inference

``` powershell
python 05_mlops\pipelines\inference.py
```

## 4. Verify SQL logging

``` sql
SELECT TOP 10 *
FROM dbo.predictions
ORDER BY timestamp_utc DESC;
```

## 5. Run Streamlit

``` powershell
streamlit run app\streamlit_app.py
```

## 6. Create a few test predictions

Use both normal-looking and high-risk sensor combinations.

## 7. Run drift monitoring

``` powershell
python 05_mlops\monitoring\drift_monitor.py
```

## 8. Run alert monitoring

``` powershell
python 05_mlops\monitoring\alert_monitor.py
```

## 9. Run tests

``` powershell
pytest 05_mlops\tests -v
```

## 10. Build Docker

``` powershell
docker buildx build --load -t predictive-maintenance-mlops:1.1.0 .
```

## 11. Run Docker

``` powershell
docker run --rm `
  -p 8501:8501 `
  -e MLOPS_SQL_CONNECTION="$env:MLOPS_SQL_CONNECTION" `
  predictive-maintenance-mlops:1.1.0
```

------------------------------------------------------------------------

# 16. Monitoring Interpretation

The monitoring layer currently provides two production signals.

### Feature Drift

Measures changes between reference feature distributions and production
prediction inputs.

Large values indicate that the current production sample is
substantially different from the reference data.

### Alert Rate

Measures the percentage of predictions classified as machine failures.

A sudden increase in alert rate can indicate:

-   A change in machine operating conditions
-   A change in incoming sensor data
-   A model behavior change
-   A genuine increase in machine failures

These signals should be interpreted together with operational context.

------------------------------------------------------------------------

# 17. Security

Never commit:

``` text
.env
database passwords
API keys
SQL credentials
```

Use:

``` text
MLOPS_SQL_CONNECTION
```

as an environment variable or a production secret.

Before publishing the repository, rotate any database password that was
previously exposed during local development or testing.

------------------------------------------------------------------------

# 18. Cloud & Big Data Readiness

The current AI4I 2020 dataset is relatively small, so Apache Spark is
not required for the current implementation.

The architecture can be extended for larger industrial datasets:

``` text
Object Storage
      |
      v
Apache Spark
      |
      v
Distributed Feature Engineering
      |
      v
Training / Batch Inference
      |
      v
Model Registry
      |
      v
Production Serving
      |
      v
Monitoring
```

Potential cloud deployment targets include:

-   AWS ECS / Fargate
-   Google Cloud Run
-   Azure Container Apps
-   Kubernetes

The current implementation provides the main building blocks needed for
migration:

-   Docker containerization
-   Versioned model artifacts
-   Configurable database connection
-   Reproducible dependencies
-   Prediction logging
-   Monitoring

Cloud deployment itself is documented separately and is not claimed as
completed unless explicitly deployed.

See:

``` text
cloud/README.md
cloud/deployment.md
```

------------------------------------------------------------------------

# 19. Reproducibility Checklist

Before submission, verify:

``` text
[ ] requirements-mlops.txt exists
[ ] model.pkl exists
[ ] metadata.json exists
[ ] feature_schema.json exists
[ ] SQL schema exists
[ ] SQL Server connection works
[ ] inference works
[ ] predictions are logged
[ ] Streamlit starts
[ ] drift monitoring works
[ ] alert monitoring works
[ ] MLOps tests pass
[ ] Docker image builds
[ ] Docker container runs
[ ] .gitignore exists
[ ] .mypy_cache is removed
[ ] __pycache__ directories are removed
[ ] real credentials are not committed
```

------------------------------------------------------------------------

# 20. Final MLOps Status

The MLOps layer covers the required production-oriented components:

``` text
Model Versioning             PASS
Feature Schema               PASS
Inference Pipeline           PASS
Prediction Logging           PASS
SQL Server Integration       PASS
Streamlit Dashboard          PASS
Feature Drift Monitoring     PASS
Alert Rate Monitoring        PASS
Docker Support               PASS
Cloud/Big Data Documentation PASS
```

The system is designed so that the trained ML model can be used
reproducibly for inference, predictions can be stored for historical
analysis, and basic production monitoring can be performed without
retraining the model.
