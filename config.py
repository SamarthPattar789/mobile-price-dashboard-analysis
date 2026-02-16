import os


def get_config() -> dict:
    database_uri = os.getenv(
        "DATABASE_URI",
        # Default to SQLite file for easy local run
        f"sqlite:///{os.path.abspath('app.db')}",
    )
    return {
        "SECRET_KEY": os.getenv("SECRET_KEY", "dev-secret-key-change"),
        "DATABASE_URI": database_uri,
        # Power BI: supply these if using secure embed with token
        "PBI_EMBED_URL": os.getenv("PBI_EMBED_URL", ""),
        "PBI_REPORT_URL": os.getenv("PBI_REPORT_URL", ""),
    }


