# Lab 4 API Reference

Run the server:

```powershell
python .\app\main.py
```

Open:

- Dashboard: `http://127.0.0.1:8000`
- API docs: `http://127.0.0.1:8000/docs`

## Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/health` | Backend and data-source status |
| GET | `/api/meta/object` | University variant metadata |
| GET | `/api/dashboard/summary` | Dashboard KPI summary |
| GET | `/api/consumption/history` | Historical meter-level consumption |
| GET | `/api/consumption/aggregate` | Aggregated consumption by hour/day/month |
| GET | `/api/baseline` | Monthly baseline and actual consumption |
| GET | `/api/forecast` | Lab 2 next-month forecast |
| GET | `/api/models/comparison` | Lab 2 model comparison metrics |
| GET | `/api/ems/results` | Lab 3 EMS simulation time series |
| GET | `/api/ems/metrics` | Lab 3 energy and economic metrics |
| GET | `/api/reports/summary` | Combined JSON report |
| GET | `/api/reports/export` | Create CSV report export |

## Query Examples

```text
/api/consumption/history?start=2025-04-07&end=2025-04-14&level=1
/api/consumption/aggregate?period=month
/api/consumption/aggregate?period=day&start=2025-01-01&end=2025-02-01
```

Valid aggregate periods:

- `hour`
- `day`
- `month`
