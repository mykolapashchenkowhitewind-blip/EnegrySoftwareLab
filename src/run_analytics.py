import sqlite3

from config import DB_PATH, RESULTS_DIR, SQL_DIR


def split_sql_statements(sql_text: str) -> list[str]:
    statements = []
    current = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(current).rstrip(";"))
            current = []
    if current:
        statements.append("\n".join(current))
    return statements


def write_result(index: int, cursor: sqlite3.Cursor) -> str:
    path = RESULTS_DIR / f"query_{index:02d}.csv"
    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()

    with path.open("w", encoding="utf-8", newline="") as file:
        file.write(",".join(columns) + "\n")
        for row in rows:
            file.write(",".join(str(value) for value in row) + "\n")

    return f"{path.name}: {len(rows)} rows"


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database does not exist: {DB_PATH}. Run create_database.py and load_data.py first.")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    statements = split_sql_statements((SQL_DIR / "analytics.sql").read_text(encoding="utf-8"))

    outputs = []
    with sqlite3.connect(DB_PATH) as connection:
        for index, statement in enumerate(statements, start=1):
            cursor = connection.execute(statement)
            outputs.append(write_result(index, cursor))

    print("Analytics results:")
    for output in outputs:
        print(f"- {output}")


if __name__ == "__main__":
    main()
