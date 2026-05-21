DROP VIEW IF EXISTS v_level_1_consumption;
DROP VIEW IF EXISTS v_level_2_consumption;
DROP VIEW IF EXISTS v_level_3_consumption;
DROP VIEW IF EXISTS v_hourly_object_consumption;

CREATE VIEW v_level_1_consumption AS
SELECT
    o.name AS object_name,
    m.serial_number,
    m.installation_location,
    ms.measured_at,
    ms.consumption_kwh,
    tz.name AS tariff_zone
FROM measurements ms
JOIN meters m ON m.meter_id = ms.meter_id
JOIN objects o ON o.object_id = m.object_id
JOIN tariff_zones tz ON tz.tariff_zone_id = ms.tariff_zone_id
WHERE m.accounting_level = 1;

CREATE VIEW v_level_2_consumption AS
SELECT
    o.name AS object_name,
    m.serial_number,
    m.installation_location,
    ms.measured_at,
    ms.consumption_kwh,
    tz.name AS tariff_zone
FROM measurements ms
JOIN meters m ON m.meter_id = ms.meter_id
JOIN objects o ON o.object_id = m.object_id
JOIN tariff_zones tz ON tz.tariff_zone_id = ms.tariff_zone_id
WHERE m.accounting_level = 2;

CREATE VIEW v_level_3_consumption AS
SELECT
    o.name AS object_name,
    m.serial_number,
    m.installation_location,
    ms.measured_at,
    ms.consumption_kwh,
    tz.name AS tariff_zone
FROM measurements ms
JOIN meters m ON m.meter_id = ms.meter_id
JOIN objects o ON o.object_id = m.object_id
JOIN tariff_zones tz ON tz.tariff_zone_id = ms.tariff_zone_id
WHERE m.accounting_level = 3;

CREATE VIEW v_hourly_object_consumption AS
SELECT
    o.object_id,
    o.name AS object_name,
    ms.measured_at,
    SUM(ms.consumption_kwh) AS total_consumption_kwh
FROM measurements ms
JOIN meters m ON m.meter_id = ms.meter_id
JOIN objects o ON o.object_id = m.object_id
GROUP BY o.object_id, o.name, ms.measured_at;
