-- ============================================
-- Analytical Queries for Industrial Predictive Maintenance
-- 12+ queries covering JOINs, CTEs, Window Functions, Aggregations
-- Compatible with SQLite (tested)
-- ============================================

-- ------------------------------------------------
-- Q1: Basic JOIN overview - 20 rows of full health view
-- Requirement: JOIN between three tables
-- ------------------------------------------------
SELECT 
    m.machine_id,
    m.product_id,
    m.type,
    s.timestamp,
    s.air_temperature_k,
    s.process_temperature_k,
    s.torque_nm,
    s.rotational_speed_rpm,
    s.tool_wear_min,
    COALESCE(f.machine_failure, 0) AS machine_failure,
    COALESCE(f.failure_type, 'NONE') AS failure_type
FROM machines m
JOIN sensor_readings s ON m.machine_id = s.machine_id
LEFT JOIN failure_events f ON s.reading_id = f.reading_id
ORDER BY s.timestamp DESC
LIMIT 20;

-- ------------------------------------------------
-- Q2: Failure ratio per Type (Aggregation)
-- Requirement: Aggregations: failure ratio per Type
-- ------------------------------------------------
SELECT 
    m.type,
    COUNT(*) AS total_readings,
    SUM(COALESCE(f.machine_failure,0)) AS total_failures,
    ROUND(100.0 * SUM(COALESCE(f.machine_failure,0)) / COUNT(*), 2) AS failure_rate_pct,
    ROUND(AVG(s.torque_nm),2) AS avg_torque,
    ROUND(AVG(s.tool_wear_min),2) AS avg_tool_wear
FROM machines m
JOIN sensor_readings s ON m.machine_id = s.machine_id
LEFT JOIN failure_events f ON s.reading_id = f.reading_id
GROUP BY m.type
ORDER BY failure_rate_pct DESC;

-- ------------------------------------------------
-- Q3: CTE - Failure rate by product type with detailed breakdown
-- Requirement: CTE (WITH) for failure rate by product type
-- ------------------------------------------------
WITH type_stats AS (
    SELECT 
        m.type,
        COUNT(*) AS total,
        SUM(COALESCE(f.machine_failure,0)) AS failures
    FROM machines m
    JOIN sensor_readings s ON m.machine_id = s.machine_id
    LEFT JOIN failure_events f ON s.reading_id = f.reading_id
    GROUP BY m.type
),
overall AS (
    SELECT COUNT(*) AS total_all, SUM(machine_failure) AS failures_all FROM failure_events
)
SELECT 
    ts.type,
    ts.total,
    ts.failures,
    ROUND(100.0 * ts.failures / ts.total, 2) AS failure_rate_pct,
    ROUND(100.0 * ts.failures / (SELECT failures_all FROM overall), 2) AS pct_of_all_failures
FROM type_stats ts
ORDER BY failure_rate_pct DESC;

-- ------------------------------------------------
-- Q4: Average Torque at Failure vs Normal (Aggregation)
-- Requirement: average Torque at failure vs normal
-- ------------------------------------------------
SELECT 
    CASE WHEN COALESCE(f.machine_failure,0)=1 THEN 'FAILURE' ELSE 'NORMAL' END AS status,
    COUNT(*) AS count,
    ROUND(AVG(s.torque_nm),2) AS avg_torque,
    ROUND(AVG(s.rotational_speed_rpm),2) AS avg_rpm,
    ROUND(AVG(s.tool_wear_min),2) AS avg_tool_wear,
    ROUND(AVG(s.air_temperature_k),2) AS avg_air_temp,
    ROUND(AVG(s.process_temperature_k),2) AS avg_process_temp,
    ROUND(AVG(s.power_w),2) AS avg_power,
    ROUND(AVG(s.temp_diff_k),2) AS avg_temp_diff
FROM sensor_readings s
LEFT JOIN failure_events f ON s.reading_id = f.reading_id
GROUP BY status;

-- ------------------------------------------------
-- Q5: Window Function - RANK top machines by tool wear and failure
-- Requirement: Window Functions RANK for top machines failure
-- ------------------------------------------------
SELECT 
    m.machine_id,
    m.product_id,
    m.type,
    s.tool_wear_min,
    s.torque_nm,
    COALESCE(f.machine_failure,0) AS failed,
    RANK() OVER (ORDER BY s.tool_wear_min DESC) AS wear_rank,
    RANK() OVER (PARTITION BY m.type ORDER BY s.tool_wear_min DESC) AS wear_rank_per_type
FROM machines m
JOIN sensor_readings s ON m.machine_id = s.machine_id
LEFT JOIN failure_events f ON s.reading_id = f.reading_id
ORDER BY wear_rank
LIMIT 20;

-- ------------------------------------------------
-- Q6: Window Function - Moving average of torque and temperature (AVG OVER)
-- Requirement: Window Functions AVG OVER for moving rates
-- ------------------------------------------------
SELECT 
    s.reading_id,
    s.machine_id,
    s.timestamp,
    s.torque_nm,
    ROUND(AVG(s.torque_nm) OVER (ORDER BY s.timestamp ROWS BETWEEN 9 PRECEDING AND CURRENT ROW),2) AS torque_10_moving_avg,
    s.air_temperature_k,
    ROUND(AVG(s.air_temperature_k) OVER (ORDER BY s.timestamp ROWS BETWEEN 19 PRECEDING AND CURRENT ROW),2) AS air_temp_20_moving_avg,
    s.process_temperature_k
FROM sensor_readings s
ORDER BY s.timestamp
LIMIT 50;

-- ------------------------------------------------
-- Q7: Window Function - LAG to detect temperature change before failure
-- Requirement: LAG example
-- ------------------------------------------------
WITH ordered_readings AS (
    SELECT 
        s.reading_id,
        s.machine_id,
        s.timestamp,
        s.air_temperature_k,
        s.process_temperature_k,
        s.temp_diff_k,
        COALESCE(f.machine_failure,0) AS machine_failure,
        LAG(s.air_temperature_k, 1) OVER (ORDER BY s.timestamp) AS prev_air_temp,
        LAG(s.process_temperature_k, 1) OVER (ORDER BY s.timestamp) AS prev_process_temp,
        LAG(s.temp_diff_k, 1) OVER (ORDER BY s.timestamp) AS prev_temp_diff
    FROM sensor_readings s
    LEFT JOIN failure_events f ON s.reading_id = f.reading_id
)
SELECT 
    reading_id,
    machine_id,
    timestamp,
    air_temperature_k,
    prev_air_temp,
    ROUND(air_temperature_k - prev_air_temp, 2) AS air_temp_delta,
    temp_diff_k,
    machine_failure
FROM ordered_readings
WHERE machine_failure = 1
ORDER BY timestamp
LIMIT 20;

-- ------------------------------------------------
-- Q8: Failure mode distribution (counts per failure_type)
-- JOIN + Aggregation
-- ------------------------------------------------
SELECT 
    f.failure_type,
    COUNT(*) AS occurrences,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM failure_events), 2) AS pct_of_failures,
    ROUND(AVG(s.tool_wear_min),1) AS avg_tool_wear_at_failure,
    ROUND(AVG(s.torque_nm),1) AS avg_torque_at_failure
FROM failure_events f
JOIN sensor_readings s ON f.reading_id = s.reading_id
JOIN machines m ON f.machine_id = m.machine_id
GROUP BY f.failure_type
ORDER BY occurrences DESC;

-- ------------------------------------------------
-- Q9: Tool wear bins and failure correlation
-- Aggregation with CASE binning
-- ------------------------------------------------
SELECT 
    CASE 
        WHEN s.tool_wear_min < 50 THEN '0-50 (New)'
        WHEN s.tool_wear_min < 100 THEN '50-100'
        WHEN s.tool_wear_min < 150 THEN '100-150'
        WHEN s.tool_wear_min < 200 THEN '150-200 (Worn)'
        ELSE '200+ (Critical - TWF risk)'
    END AS wear_bin,
    COUNT(*) AS total_readings,
    SUM(COALESCE(f.machine_failure,0)) AS failures,
    ROUND(100.0 * SUM(COALESCE(f.machine_failure,0)) / COUNT(*), 2) AS failure_rate_pct,
    COUNT(DISTINCT m.type) AS types_in_bin
FROM sensor_readings s
JOIN machines m ON s.machine_id = m.machine_id
LEFT JOIN failure_events f ON s.reading_id = f.reading_id
GROUP BY wear_bin
ORDER BY MIN(s.tool_wear_min);

-- ------------------------------------------------
-- Q10: Power analysis - PWF threshold check
-- Power = torque * rpm * 2π/60, failure if <3500 or >9000
-- ------------------------------------------------
SELECT 
    m.type,
    CASE 
        WHEN s.power_w < 3500 THEN 'LOW_POWER (<3500W)'
        WHEN s.power_w > 9000 THEN 'HIGH_POWER (>9000W)'
        ELSE 'NORMAL (3500-9000W)'
    END AS power_category,
    COUNT(*) AS count,
    SUM(COALESCE(f.machine_failure,0)) AS failures,
    SUM(COALESCE(f.pwf,0)) AS pwf_failures,
    ROUND(AVG(s.power_w),1) AS avg_power
FROM sensor_readings s
JOIN machines m ON s.machine_id = m.machine_id
LEFT JOIN failure_events f ON s.reading_id = f.reading_id
GROUP BY m.type, power_category
ORDER BY m.type, failures DESC;

-- ------------------------------------------------
-- Q11: Heat Dissipation Failure conditions verification
-- HDF if temp_diff <8.6K AND rpm <1380
-- ------------------------------------------------
SELECT 
    CASE 
        WHEN s.temp_diff_k < 8.6 AND s.rotational_speed_rpm < 1380 THEN 'HDF_RISK_CONDITION'
        ELSE 'NORMAL_CONDITION'
    END AS hdf_condition,
    COUNT(*) AS total,
    SUM(COALESCE(f.hdf,0)) AS hdf_failures,
    SUM(COALESCE(f.machine_failure,0)) AS any_failures,
    ROUND(100.0 * SUM(COALESCE(f.hdf,0)) / COUNT(*), 2) AS hdf_rate_pct,
    ROUND(AVG(s.temp_diff_k),2) AS avg_temp_diff,
    ROUND(AVG(s.rotational_speed_rpm),2) AS avg_rpm
FROM sensor_readings s
LEFT JOIN failure_events f ON s.reading_id = f.reading_id
GROUP BY hdf_condition;

-- ------------------------------------------------
-- Q12: Machines with multiple failure modes (overlap analysis)
-- JOIN all three tables + HAVING COUNT >1
-- ------------------------------------------------
SELECT 
    f.machine_id,
    m.product_id,
    m.type,
    s.timestamp,
    s.tool_wear_min,
    s.torque_nm,
    s.power_w,
    GROUP_CONCAT(f.failure_type, ',') AS failure_types_combined,
    COUNT(*) AS num_modes_in_same_reading,
    SUM(f.twf + f.hdf + f.pwf + f.osf + f.rnf) AS total_flags
FROM failure_events f
JOIN machines m ON f.machine_id = m.machine_id
JOIN sensor_readings s ON f.reading_id = s.reading_id
GROUP BY f.reading_id
HAVING COUNT(*) > 1 OR SUM(f.twf + f.hdf + f.pwf + f.osf + f.rnf) > 1
ORDER BY num_modes_in_same_reading DESC
LIMIT 20;

-- ------------------------------------------------
-- Q13: CTE + Window - Failure trend over synthetic time (monthly)
-- ------------------------------------------------
WITH monthly_stats AS (
    SELECT 
        strftime('%Y-%m', s.timestamp) AS month,
        COUNT(*) AS readings,
        SUM(COALESCE(f.machine_failure,0)) AS failures
    FROM sensor_readings s
    LEFT JOIN failure_events f ON s.reading_id = f.reading_id
    GROUP BY month
)
SELECT 
    month,
    readings,
    failures,
    ROUND(100.0 * failures / readings, 2) AS failure_rate,
    ROUND(AVG(failures) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW),2) AS failures_3m_moving_avg,
    LAG(failures) OVER (ORDER BY month) AS prev_month_failures
FROM monthly_stats
ORDER BY month;

-- ------------------------------------------------
-- Q14: Top 10 risky machines by combined risk score
-- Uses JOIN, aggregation, window RANK
-- ------------------------------------------------
WITH risk_calc AS (
    SELECT 
        m.machine_id,
        m.product_id,
        m.type,
        s.tool_wear_min,
        s.torque_nm,
        s.power_w,
        s.temp_diff_k,
        -- simple risk score: weighted proximity to thresholds
        (CASE WHEN s.tool_wear_min > 200 THEN 3 ELSE s.tool_wear_min / 100.0 END +
         CASE WHEN s.power_w < 3500 OR s.power_w > 9000 THEN 2 ELSE 0 END +
         CASE WHEN s.temp_diff_k < 8.6 AND s.rotational_speed_rpm < 1380 THEN 2 ELSE 0 END +
         (s.tool_wear_min * s.torque_nm / 10000.0)
        ) AS risk_score
    FROM machines m
    JOIN sensor_readings s ON m.machine_id = s.machine_id
)
SELECT 
    machine_id,
    product_id,
    type,
    tool_wear_min,
    torque_nm,
    power_w,
    ROUND(risk_score,2) AS risk_score,
    RANK() OVER (ORDER BY risk_score DESC) AS risk_rank
FROM risk_calc
ORDER BY risk_score DESC
LIMIT 15;

