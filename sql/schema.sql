PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS energy_efficiency_metrics;
DROP TABLE IF EXISTS measurements;
DROP TABLE IF EXISTS weather_data;
DROP TABLE IF EXISTS baselines;
DROP TABLE IF EXISTS meters;
DROP TABLE IF EXISTS tariff_zones;
DROP TABLE IF EXISTS objects;

CREATE TABLE objects (
    object_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    object_type TEXT NOT NULL,
    area_m2 REAL NOT NULL CHECK (area_m2 > 0),
    installed_power_kw REAL NOT NULL CHECK (installed_power_kw > 0),
    operating_mode TEXT NOT NULL,
    solar_capacity_kw REAL NOT NULL DEFAULT 0 CHECK (solar_capacity_kw >= 0),
    battery_capacity_kwh REAL NOT NULL DEFAULT 0 CHECK (battery_capacity_kwh >= 0)
);

CREATE TABLE tariff_zones (
    tariff_zone_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    start_hour INTEGER NOT NULL CHECK (start_hour BETWEEN 0 AND 23),
    end_hour INTEGER NOT NULL CHECK (end_hour BETWEEN 0 AND 23),
    price_uah_per_kwh REAL NOT NULL CHECK (price_uah_per_kwh >= 0)
);

CREATE TABLE meters (
    meter_id INTEGER PRIMARY KEY,
    object_id INTEGER NOT NULL,
    serial_number TEXT NOT NULL UNIQUE,
    accounting_level INTEGER NOT NULL CHECK (accounting_level IN (1, 2, 3)),
    resource_type TEXT NOT NULL DEFAULT 'electricity',
    technical_params TEXT NOT NULL,
    installation_location TEXT NOT NULL,
    max_power_kw REAL NOT NULL CHECK (max_power_kw > 0),
    installed_at TEXT NOT NULL,
    FOREIGN KEY (object_id) REFERENCES objects(object_id) ON DELETE CASCADE
);

CREATE TABLE weather_data (
    weather_id INTEGER PRIMARY KEY,
    object_id INTEGER NOT NULL,
    measured_at TEXT NOT NULL,
    temperature_c REAL NOT NULL,
    irradiation_w_m2 REAL NOT NULL CHECK (irradiation_w_m2 >= 0),
    FOREIGN KEY (object_id) REFERENCES objects(object_id) ON DELETE CASCADE,
    UNIQUE (object_id, measured_at)
);

CREATE TABLE measurements (
    measurement_id INTEGER PRIMARY KEY,
    meter_id INTEGER NOT NULL,
    tariff_zone_id INTEGER NOT NULL,
    measured_at TEXT NOT NULL,
    consumption_kwh REAL NOT NULL CHECK (consumption_kwh >= 0),
    voltage_v REAL NOT NULL CHECK (voltage_v > 0),
    power_factor REAL NOT NULL CHECK (power_factor BETWEEN 0 AND 1),
    quality_flag TEXT NOT NULL DEFAULT 'valid',
    FOREIGN KEY (meter_id) REFERENCES meters(meter_id) ON DELETE CASCADE,
    FOREIGN KEY (tariff_zone_id) REFERENCES tariff_zones(tariff_zone_id),
    UNIQUE (meter_id, measured_at)
);

CREATE TABLE baselines (
    baseline_id INTEGER PRIMARY KEY,
    object_id INTEGER NOT NULL,
    month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    baseline_kwh REAL NOT NULL CHECK (baseline_kwh >= 0),
    method TEXT NOT NULL,
    FOREIGN KEY (object_id) REFERENCES objects(object_id) ON DELETE CASCADE,
    UNIQUE (object_id, month)
);

CREATE TABLE energy_efficiency_metrics (
    metric_id INTEGER PRIMARY KEY,
    object_id INTEGER NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    total_consumption_kwh REAL NOT NULL CHECK (total_consumption_kwh >= 0),
    kwh_per_m2 REAL NOT NULL CHECK (kwh_per_m2 >= 0),
    baseline_kwh REAL NOT NULL CHECK (baseline_kwh >= 0),
    deviation_percent REAL NOT NULL,
    FOREIGN KEY (object_id) REFERENCES objects(object_id) ON DELETE CASCADE
);

CREATE INDEX idx_meters_object_level ON meters(object_id, accounting_level);
CREATE INDEX idx_measurements_meter_time ON measurements(meter_id, measured_at);
CREATE INDEX idx_measurements_time ON measurements(measured_at);
CREATE INDEX idx_measurements_tariff_time ON measurements(tariff_zone_id, measured_at);
CREATE INDEX idx_weather_object_time ON weather_data(object_id, measured_at);
CREATE INDEX idx_metrics_object_period ON energy_efficiency_metrics(object_id, period_start, period_end);
