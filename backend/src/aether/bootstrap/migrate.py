"""Simple, robust migration runner executing schema SQL scripts sequentially in alphanumeric order."""

from __future__ import annotations

import os

from sqlalchemy import text

from aether.bootstrap.database import create_engine, create_session_factory


async def run_migrations(database_url: str, schema_dir: str) -> None:
    print(f"Connecting to database: {database_url.split('@')[-1]} (obfuscated)")
    engine = create_engine(database_url)
    session_factory = create_session_factory(engine)

    async with session_factory() as session:
        # Create migrations metadata ledger table
        await session.execute(
            text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename varchar(255) PRIMARY KEY,
                applied_at timestamptz DEFAULT now()
            )
            """)
        )
        await session.commit()

        # Find migration SQL files
        if not os.path.exists(schema_dir):
            print(f"Error: Schema directory {schema_dir} does not exist.")
            return

        sql_files = sorted([f for f in os.listdir(schema_dir) if f.endswith(".sql")])
        print(f"Found {len(sql_files)} migration files in {schema_dir}")

        for filename in sql_files:
            # Check if applied
            row = (
                await session.execute(
                    text("SELECT filename FROM schema_migrations WHERE filename = :f"),
                    {"f": filename},
                )
            ).scalar_one_or_none()

            if row:
                print(f"Migration {filename} is already applied. Skipping.")
                continue

            print(f"Applying migration: {filename} ...")
            path = os.path.join(schema_dir, filename)
            with open(path, encoding="utf-8") as f_obj:
                sql_content = f_obj.read()

            # Split statements by semicolon, ignoring empty ones and comments
            statements = []
            current = []
            for line in sql_content.splitlines():
                if line.strip().startswith("--"):
                    continue
                current.append(line)
                if ";" in line:
                    statements.append("\n".join(current))
                    current = []
            if current:
                stmt = "\n".join(current).strip()
                if stmt:
                    statements.append(stmt)

            try:
                for stmt in statements:
                    if stmt.strip():
                        await session.execute(text(stmt))
                # Insert migration log
                await session.execute(
                    text("INSERT INTO schema_migrations (filename) VALUES (:f)"),
                    {"f": filename},
                )
                await session.commit()
                print(f"Successfully applied {filename}")
            except Exception as e:
                await session.rollback()
                print(f"Error applying migration {filename}: {e}")
                raise


if __name__ == "__main__":
    import asyncio
    import sys

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL is not configured in environment.")
        sys.exit(1)

    # Standardize scheme
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    target_dir = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "..",
            "database",
            "schema",
        )
    )

    asyncio.run(run_migrations(db_url, target_dir))
