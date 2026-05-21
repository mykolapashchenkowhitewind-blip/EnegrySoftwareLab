import csv
import math
import random
from datetime import datetime, timedelta

from config import GENERATED_DIR, NIGHT_HOURS, OBJECT, PEAK_HOURS


START = datetime(2025, 1, 1, 0, 0, 0)
HOURS_IN_YEAR = 8760
RANDOM_SEED = 51


def tariff_zone_id(hour: int) -> int:
    if hour in NIGHT_HOURS:
        return 1
    if hour in PEAK_HOURS:
        return 3
    return 2


def seasonal_factor(day_of_year: int) -> float:
    winter = 0.16 * math.cos(2 * math.pi * (day_of_year - 15) / 365)
    summer = 0.10 * math.cos(2 * math.pi * (day_of_year - 200) / 365)
    return 1.0 + winter + summer


def daily_factor(hour: int, weekday: int) -> float:
    if weekday >= 5:
        if 9 <= hour <= 18:
            return 0.78
        return 0.58

    if 8 <= hour <= 17:
        return 1.20
    if 18 <= hour <= 21:
        return 0.98
    if 0 <= hour <= 5:
        return 0.62
    return 0.82


def temperature(day_of_year: int, hour: int) -> float:
    annual = 10 + 15 * math.sin(2 * math.pi * (day_of_year - 100) / 365)
    daily = 4 * math.sin(2 * math.pi * (hour - 7) / 24)
    return annual + daily + random.uniform(-2.0, 2.0)


def irradiation(day_of_year: int, hour: int) -> float:
    daylight = max(0.0, math.sin(math.pi * (hour - 6) / 12))
    seasonal = 0.55 + 0.45 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
    return max(0.0, 850 * daylight * seasonal + random.uniform(-30, 30))


def meter_weight(index: int, total: int) -> float:
    raw = [1.45, 1.2, 1.1, 1.0, 0.95, 0.9, 0.85, 0.78, 0.72, 0.68, 0.62, 0.58, 0.58, 0.59]
    return raw[index] / sum(raw[:total])


def clipped_load(value: float) -> float:
    return max(OBJECT["min_load_kw"], min(OBJECT["max_load_kw"], value))


def generate() -> None:
    random.seed(RANDOM_SEED)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    weather_path = GENERATED_DIR / "weather_data.csv"
    measurements_path = GENERATED_DIR / "measurements.csv"

    weights = [meter_weight(i, OBJECT["meter_count"]) for i in range(OBJECT["meter_count"])]

    with weather_path.open("w", newline="", encoding="utf-8") as weather_file, measurements_path.open(
        "w", newline="", encoding="utf-8"
    ) as measurements_file:
        weather_writer = csv.writer(weather_file)
        measurements_writer = csv.writer(measurements_file)

        weather_writer.writerow(["object_id", "measured_at", "temperature_c", "irradiation_w_m2"])
        measurements_writer.writerow(
            ["meter_id", "tariff_zone_id", "measured_at", "consumption_kwh", "voltage_v", "power_factor", "quality_flag"]
        )

        for offset in range(HOURS_IN_YEAR):
            timestamp = START + timedelta(hours=offset)
            day_of_year = timestamp.timetuple().tm_yday
            hour = timestamp.hour
            weekday = timestamp.weekday()

            temp = temperature(day_of_year, hour)
            solar = irradiation(day_of_year, hour)
            weather_writer.writerow([OBJECT["object_id"], timestamp.isoformat(sep=" "), round(temp, 2), round(solar, 2)])

            base = OBJECT["average_load_kw"] * seasonal_factor(day_of_year) * daily_factor(hour, weekday)
            total_load = clipped_load(base * random.uniform(0.92, 1.08))

            for index, weight in enumerate(weights, start=1):
                meter_noise = random.uniform(0.95, 1.05)
                consumption = max(0.01, total_load * weight * meter_noise)
                measurements_writer.writerow(
                    [
                        index,
                        tariff_zone_id(hour),
                        timestamp.isoformat(sep=" "),
                        round(consumption, 4),
                        round(random.uniform(218, 232), 2),
                        round(random.uniform(0.91, 0.99), 3),
                        "valid",
                    ]
                )

    print(f"Generated weather data: {weather_path}")
    print(f"Generated measurements: {measurements_path}")


if __name__ == "__main__":
    generate()
