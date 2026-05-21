import sqlite3

from config import DATA_DIR, DB_PATH, SQL_DIR


def execute_script(connection: sqlite3.Connection, script_name: str) -> None:
    script_path = SQL_DIR / script_name
    connection.executescript(script_path.read_text(encoding="utf-8"))


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        DB_PATH.unlink()

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON;")
        execute_script(connection, "schema.sql")
        execute_script(connection, "views.sql")

    print(f"Created database: {DB_PATH}")


if __name__ == "__main__":
    main()
