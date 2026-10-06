IF DB_ID('PredictiveMaintenance') IS NULL
BEGIN
    CREATE DATABASE PredictiveMaintenance;
END
GO

USE PredictiveMaintenance;
GO

IF OBJECT_ID('dbo.predictions', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.predictions (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        timestamp_utc DATETIME2 NOT NULL,
        model_version VARCHAR(50) NOT NULL,

        air_temperature FLOAT NOT NULL,
        process_temperature FLOAT NOT NULL,
        rotational_speed FLOAT NOT NULL,
        torque FLOAT NOT NULL,
        tool_wear FLOAT NOT NULL,
        machine_type VARCHAR(10) NOT NULL,

        failure_probability FLOAT NOT NULL,
        threshold FLOAT NOT NULL,
        prediction BIT NOT NULL
    );
END
GO