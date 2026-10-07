from datetime import datetime, timezone
import os

from dotenv import load_dotenv

load_dotenv()


def parse_utc_datetime(value: str, name: str) -> datetime:
    value = value.strip()
    if value.upper() == "TODAY":
        return datetime.now(timezone.utc)

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{name} must be ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS+00:00) or TODAY."
        ) from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def get_date_range() -> tuple[datetime, datetime]:
    start_value = os.getenv("DATA_START_DATE", "2024-01-01")
    end_value = os.getenv("DATA_END_DATE", "TODAY")

    start = parse_utc_datetime(start_value, "DATA_START_DATE")
    end = parse_utc_datetime(end_value, "DATA_END_DATE")

    if start >= end:
        raise ValueError("DATA_START_DATE must be earlier than DATA_END_DATE.")

    return start, end
