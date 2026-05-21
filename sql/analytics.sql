-- 1. Daily consumption.
SELECT
    date(ms.measured_at) AS day,
    ROUND(SUM(ms.consumption_kwh), 2) AS total_kwh
FROM measurements ms
GROUP BY date(ms.measured_at)
ORDER BY day
LIMIT 10;

-- 2. Weekly consumption.
SELECT
    strftime('%Y-W%W', ms.measured_at) AS week,
    ROUND(SUM(ms.consumption_kwh), 2) AS total_kwh
FROM measurements ms
GROUP BY strftime('%Y-W%W', ms.measured_at)
ORDER BY week
LIMIT 10;

-- 3. Monthly consumption.
SELECT
    strftime('%Y-%m', ms.measured_at) AS month,
    ROUND(SUM(ms.consumption_kwh), 2) AS total_kwh
FROM measurements ms
GROUP BY strftime('%Y-%m', ms.measured_at)
ORDER BY month;

-- 4. Consumption and cost by tariff zone.
SELECT
    tz.name AS tariff_zone,
    ROUND(SUM(ms.consumption_kwh), 2) AS total_kwh,
    ROUND(SUM(ms.consumption_kwh * tz.price_uah_per_kwh), 2) AS total_cost_uah
FROM measurements ms
JOIN tariff_zones tz ON tz.tariff_zone_id = ms.tariff_zone_id
GROUP BY tz.name
ORDER BY total_cost_uah DESC;

-- 5. Specific consumption indicator, kWh per square meter.
SELECT
    o.name AS object_name,
    ROUND(SUM(ms.consumption_kwh), 2) AS total_kwh,
    ROUND(SUM(ms.consumption_kwh) / o.area_m2, 2) AS kwh_per_m2
FROM measurements ms
JOIN meters m ON m.meter_id = ms.meter_id
JOIN objects o ON o.object_id = m.object_id
GROUP BY o.object_id, o.name, o.area_m2;

-- 6. Monthly baseline comparison.
SELECT
    strftime('%Y-%m', ms.measured_at) AS month,
    ROUND(SUM(ms.consumption_kwh), 2) AS actual_kwh,
    ROUND(b.baseline_kwh, 2) AS baseline_kwh,
    ROUND((SUM(ms.consumption_kwh) - b.baseline_kwh) * 100.0 / b.baseline_kwh, 2) AS deviation_percent
FROM measurements ms
JOIN meters m ON m.meter_id = ms.meter_id
JOIN objects o ON o.object_id = m.object_id
JOIN baselines b
    ON b.object_id = o.object_id
   AND b.month = CAST(strftime('%m', ms.measured_at) AS INTEGER)
GROUP BY strftime('%Y-%m', ms.measured_at), b.baseline_kwh;

-- 7. Hourly anomalies: deviation greater than 20 percent from average hourly consumption.
WITH hourly AS (
    SELECT
        measured_at,
        SUM(total_consumption_kwh) AS total_kwh
    FROM v_hourly_object_consumption
    GROUP BY measured_at
),
stats AS (
    SELECT AVG(total_kwh) AS avg_kwh FROM hourly
)
SELECT
    h.measured_at,
    ROUND(h.total_kwh, 2) AS total_kwh,
    ROUND(s.avg_kwh, 2) AS average_kwh,
    ROUND((h.total_kwh - s.avg_kwh) * 100.0 / s.avg_kwh, 2) AS deviation_percent
FROM hourly h
CROSS JOIN stats s
WHERE ABS((h.total_kwh - s.avg_kwh) * 100.0 / s.avg_kwh) > 20
ORDER BY ABS((h.total_kwh - s.avg_kwh) * 100.0 / s.avg_kwh) DESC
LIMIT 20;
