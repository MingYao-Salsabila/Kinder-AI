from __future__ import annotations

from pathlib import Path

from app.db.database import seed_demo_content


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    sqlite_path = root / "app" / "db" / "kinderai.sqlite3"
    seed_demo_content(sqlite_path)
    print(f"Seeded demo data into {sqlite_path}")


if __name__ == "__main__":
    main()
