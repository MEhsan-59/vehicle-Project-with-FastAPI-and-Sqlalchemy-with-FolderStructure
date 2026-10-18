from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from core.config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def initialize_database() -> None:
    if settings.DATABASE_URL.startswith("sqlite"):
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        with engine.begin() as connection:
            if "accounts" in tables:
                account_columns = {
                    column["name"]
                    for column in inspect(connection).get_columns("accounts")
                }
                if "created_at" not in account_columns:
                    connection.execute(
                        text("ALTER TABLE accounts ADD COLUMN created_at DATETIME")
                    )
                connection.execute(
                    text(
                        "UPDATE accounts SET created_at = CURRENT_TIMESTAMP "
                        "WHERE created_at IS NULL"
                    )
                )
                connection.execute(
                    text(
                        "CREATE TRIGGER IF NOT EXISTS "
                        "trg_accounts_created_at AFTER INSERT ON accounts "
                        "WHEN NEW.created_at IS NULL BEGIN "
                        "UPDATE accounts SET created_at = CURRENT_TIMESTAMP "
                        "WHERE id = NEW.id; END"
                    )
                )

            if "vehicles" in tables:
                vehicle_columns = {
                    column["name"]
                    for column in inspect(connection).get_columns("vehicles")
                }
                if "created_at" not in vehicle_columns:
                    connection.execute(
                        text("ALTER TABLE vehicles ADD COLUMN created_at DATETIME")
                    )
                connection.execute(
                    text(
                        "UPDATE vehicles SET created_at = CURRENT_TIMESTAMP "
                        "WHERE created_at IS NULL"
                    )
                )
                connection.execute(
                    text(
                        "CREATE TRIGGER IF NOT EXISTS "
                        "trg_vehicles_created_at AFTER INSERT ON vehicles "
                        "WHEN NEW.created_at IS NULL BEGIN "
                        "UPDATE vehicles SET created_at = CURRENT_TIMESTAMP "
                        "WHERE id = NEW.id; END"
                    )
                )

            legacy_parts = False
            if "parts" in tables:
                part_columns = inspect(connection).get_columns("parts")
                user_id = next(
                    (column for column in part_columns if column["name"] == "user_id"),
                    None,
                )
                if user_id is not None and user_id["nullable"] is False:
                    connection.execute(
                        text("ALTER TABLE parts RENAME TO parts_legacy")
                    )
                    legacy_parts = True

        Base.metadata.create_all(bind=engine)

        if legacy_parts:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO parts "
                        "(id, user_id, part, km_life, month_life, km_limit, day_limit) "
                        "SELECT id, user_id, part, km_life, month_life, km_limit, day_limit "
                        "FROM parts_legacy"
                    )
                )
                connection.execute(text("DROP TABLE parts_legacy"))
    else:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        with engine.begin() as connection:
            if "accounts" in tables:
                account_columns = {
                    column["name"]
                    for column in inspect(connection).get_columns("accounts")
                }
                if "created_at" not in account_columns:
                    connection.execute(
                        text(
                            "ALTER TABLE accounts ADD COLUMN created_at "
                            "TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP"
                        )
                    )

            if "vehicles" in tables:
                vehicle_columns = {
                    column["name"]
                    for column in inspect(connection).get_columns("vehicles")
                }
                if "created_at" not in vehicle_columns:
                    connection.execute(
                        text(
                            "ALTER TABLE vehicles ADD COLUMN created_at "
                            "TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP"
                        )
                    )

            if "parts" in tables:
                user_id = next(
                    (
                        column
                        for column in inspect(connection).get_columns("parts")
                        if column["name"] == "user_id"
                    ),
                    None,
                )
                if user_id is not None and user_id["nullable"] is False:
                    connection.execute(
                        text("ALTER TABLE parts ALTER COLUMN user_id DROP NOT NULL")
                    )
        Base.metadata.create_all(bind=engine)
