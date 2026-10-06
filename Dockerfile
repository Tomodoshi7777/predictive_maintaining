FROM python:3.13-slim-bookworm

WORKDIR /app

# System dependencies for SQL Server ODBC
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        gnupg \
        ca-certificates \
        unixodbc \
        unixodbc-dev \
        gcc \
        g++ \
    && curl https://packages.microsoft.com/keys/microsoft.asc \
        | gpg --dearmor \
        > /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" \
        > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements-mlops.txt .

RUN pip install --no-cache-dir -r requirements-mlops.txt

# Project files
COPY models ./models
COPY 05_mlops ./05_mlops
COPY app ./app

# Python module paths
ENV PYTHONPATH=/app/05_mlops/pipelines:/app/05_mlops/logging

# Run inference
CMD ["streamlit", "run", "app/streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]