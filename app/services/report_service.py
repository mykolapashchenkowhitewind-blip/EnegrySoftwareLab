import csv
import json

from .data_service import report_summary
from .paths import LAB4_DIR


def write_summary_json() -> str:
    LAB4_DIR.mkdir(parents=True, exist_ok=True)
    path = LAB4_DIR / "summary_report.json"
    path.write_text(json.dumps(report_summary(), ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def write_export_csv() -> str:
    LAB4_DIR.mkdir(parents=True, exist_ok=True)
    path = LAB4_DIR / "exported_report.csv"
    summary = report_summary()["dashboard"]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["metric", "value"])
        for key, value in summary.items():
            writer.writerow([key, value])
    return str(path)
