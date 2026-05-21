import json
import mimetypes
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services import data_service
from app.services.report_service import write_export_csv, write_summary_json


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
HOST = "127.0.0.1"
PORT = 8000


class Lab4Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        return

    def send_json(self, payload, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_text(self, text: str, content_type: str = "text/html; charset=utf-8", status: int = 200) -> None:
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self.send_text("Not found", "text/plain; charset=utf-8", 404)
            return
        body = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        try:
            if path == "/":
                self.send_file(STATIC_DIR / "index.html")
            elif path.startswith("/static/"):
                self.send_file(STATIC_DIR / path.removeprefix("/static/"))
            elif path == "/docs":
                self.send_text(api_docs_html())
            elif path == "/api/health":
                self.send_json(data_service.health())
            elif path == "/api/meta/object":
                self.send_json(data_service.OBJECT_META)
            elif path == "/api/dashboard/summary":
                self.send_json(data_service.dashboard_summary())
            elif path == "/api/consumption/history":
                self.send_json(data_service.consumption_history(params))
            elif path == "/api/consumption/aggregate":
                self.send_json(data_service.aggregate_consumption(params))
            elif path == "/api/baseline":
                self.send_json(data_service.baseline())
            elif path == "/api/forecast":
                self.send_json(data_service.forecast())
            elif path == "/api/models/comparison":
                self.send_json(data_service.model_comparison())
            elif path == "/api/ems/results":
                self.send_json(data_service.ems_results())
            elif path == "/api/ems/metrics":
                self.send_json(data_service.ems_metrics())
            elif path == "/api/reports/summary":
                write_summary_json()
                self.send_json(data_service.report_summary())
            elif path == "/api/reports/export":
                exported = write_export_csv()
                self.send_json({"status": "ok", "path": exported})
            else:
                self.send_json({"error": "Not found"}, 404)
        except ValueError as exc:
            self.send_json({"error": str(exc)}, 400)
        except FileNotFoundError as exc:
            self.send_json({"error": str(exc)}, 404)
        except Exception as exc:
            self.send_json({"error": f"Unexpected server error: {exc}"}, 500)


def api_docs_html() -> str:
    endpoints = [
        ("GET", "/api/health", "Backend and data-source status"),
        ("GET", "/api/meta/object", "University variant metadata"),
        ("GET", "/api/dashboard/summary", "Dashboard KPI summary"),
        ("GET", "/api/consumption/history?start=2025-01-01&end=2025-01-02&level=1", "Historical meter data"),
        ("GET", "/api/consumption/aggregate?period=day", "Aggregated consumption by hour/day/month"),
        ("GET", "/api/baseline", "Monthly baseline and actual consumption"),
        ("GET", "/api/forecast", "Lab 2 next-month forecast"),
        ("GET", "/api/models/comparison", "Lab 2 model metrics"),
        ("GET", "/api/ems/results", "Lab 3 EMS simulation series"),
        ("GET", "/api/ems/metrics", "Lab 3 energy and economic metrics"),
        ("GET", "/api/reports/summary", "Combined JSON report"),
        ("GET", "/api/reports/export", "Create CSV report export"),
    ]
    rows = "\n".join(f"<tr><td>{m}</td><td><code>{p}</code></td><td>{d}</td></tr>" for m, p, d in endpoints)
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Lab 4 API Docs</title>
<style>body{{font-family:Arial,sans-serif;margin:32px;line-height:1.5}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:8px}}th{{background:#f3f5f7;text-align:left}}code{{background:#eef2f5;padding:2px 4px}}</style>
</head><body>
<h1>Lab 4 API Docs</h1>
<p>Local REST-style API for the Energy Management dashboard.</p>
<table><thead><tr><th>Method</th><th>Endpoint</th><th>Description</th></tr></thead><tbody>{rows}</tbody></table>
<p><a href="/">Open dashboard</a></p>
</body></html>"""


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Lab4Handler)
    print(f"Lab 4 web app running at http://{HOST}:{PORT}")
    print(f"API docs: http://{HOST}:{PORT}/docs")
    server.serve_forever()


if __name__ == "__main__":
    main()
