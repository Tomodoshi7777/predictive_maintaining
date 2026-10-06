-- ============================================
-- Industrial Predictive Maintenance - Schema
-- 3 Normalized Tables
-- ============================================

DROP VIEW IF EXISTS vw_machine_health;
DROP TABLE IF EXISTS failure_events;
DROP TABLE IF EXISTS sensor_readings;
DROP TABLE IF EXISTS machines;

-- 1. machines: static info
CREATE TABLE machines (
    machine_id      INTEGER PRIMARY KEY,           -- UID from raw
    product_id      VARCHAR(20) NOT NULL UNIQUE,   -- e.g., M14860
    type            CHAR(1) NOT NULL CHECK (type IN ('L','M','H')),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_machines_type ON machines(type);

-- 2. sensor_readings: time-series
CREATE TABLE sensor_readings (
    reading_id              INTEGER PRIMARY KEY,   -- same as UID
    machine_id              INTEGER NOT NULL,
    timestamp               DATETIME NOT NULL,     -- synthetic: 2020-01-01 + 5min*UID
    air_temperature_k       REAL NOT NULL CHECK (air_temperature_k BETWEEN 250 AND 400),
    process_temperature_k   REAL NOT NULL CHECK (process_temperature_k BETWEEN 250 AND 400),
    rotational_speed_rpm    INTEGER NOT NULL CHECK (rotational_speed_rpm > 0),
    torque_nm               REAL NOT NULL CHECK (torque_nm >= 0),
    tool_wear_min           INTEGER NOT NULL CHECK (tool_wear_min >= 0),
    power_w                 REAL,                  -- calculated: torque*rpm*2pi/60
    temp_diff_k             REAL,                  -- process - air
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (machine_id) REFERENCES machines(machine_id) ON DELETE CASCADE
);

CREATE INDEX idx_sensor_machine_id ON sensor_readings(machine_id);
CREATE INDEX idx_sensor_timestamp ON sensor_readings(timestamp);

-- 3. failure_events: only when failure happens
CREATE TABLE failure_events (
    event_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id      INTEGER NOT NULL,
    reading_id      INTEGER NOT NULL,
    timestamp       DATETIME NOT NULL,
    machine_failure INTEGER NOT NULL CHECK (machine_failure IN (0,1)),
    failure_type    TEXT NOT NULL CHECK (failure_type IN ('TWF','HDF','PWF','OSF','RNF','MULTI')),
    twf             INTEGER NOT NULL CHECK (twf IN (0,1)) DEFAULT 0,
    hdf             INTEGER NOT NULL CHECK (hdf IN (0,1)) DEFAULT 0,
    pwf             INTEGER NOT NULL CHECK (pwf IN (0,1)) DEFAULT 0,
    osf             INTEGER NOT NULL CHECK (osf IN (0,1)) DEFAULT 0,
    rnf             INTEGER NOT NULL CHECK (rnf IN (0,1)) DEFAULT 0,
    description     TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (machine_id) REFERENCES machines(machine_id) ON DELETE CASCADE,
    FOREIGN KEY (reading_id) REFERENCES sensor_readings(reading_id) ON DELETE CASCADE,
    UNIQUE (reading_id, failure_type)
);

CREATE INDEX idx_failure_type ON failure_events(failure_type);

-- View for easy JOIN
CREATE VIEW vw_machine_health AS
SELECT 
    m.machine_id, m.product_id, m.type,
    s.timestamp, s.air_temperature_k, s.process_temperature_k,
    s.rotational_speed_rpm, s.torque_nm, s.tool_wear_min,
    s.power_w, s.temp_diff_k,
    COALESCE(f.machine_failure, 0) AS machine_failure,
    COALESCE(f.failure_type, 'NONE') AS failure_type
FROM machines m
JOIN sensor_readings s ON m.machine_id = s.machine_id
LEFT JOIN failure_events f ON s.reading_id = f.reading_id;