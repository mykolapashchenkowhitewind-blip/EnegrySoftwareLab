from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
GENERATED_DIR = DATA_DIR / "generated"
RESULTS_DIR = DATA_DIR / "results"
SQL_DIR = PROJECT_ROOT / "sql"
DB_PATH = DATA_DIR / "energy_management.db"

OBJECT = {
    "object_id": 1,
    "name": "University",
    "object_type": "educational",
    "area_m2": 5200.0,
    "installed_power_kw": 350.0,
    "operating_mode": "24/7",
    "solar_capacity_kw": 140.0,
    "battery_capacity_kwh": 110.0,
    "meter_count": 14,
    "average_load_kw": 85.0,
    "min_load_kw": 50.0,
    "max_load_kw": 130.0,
}

TARIFF_ZONES = [
    {
        "tariff_zone_id": 1,
        "name": "night",
        "start_hour": 23,
        "end_hour": 7,
        "price_uah_per_kwh": 2.64,
    },
    {
        "tariff_zone_id": 2,
        "name": "half_peak",
        "start_hour": 7,
        "end_hour": 23,
        "price_uah_per_kwh": 5.28,
    },
    {
        "tariff_zone_id": 3,
        "name": "peak",
        "start_hour": 8,
        "end_hour": 22,
        "price_uah_per_kwh": 7.92,
    },
]

PEAK_HOURS = set(range(8, 11)) | set(range(20, 22))
NIGHT_HOURS = set(range(23, 24)) | set(range(0, 7))
