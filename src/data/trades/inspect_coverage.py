import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


INPUT_PATH = Path("data/raw/trades/binance/btcusdt_agg_trades.jsonl")


def to_datetime(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)


def find_missing_range(
    requested_start: datetime,
    requested_end: datetime,
    existing_start: datetime | None,
    existing_end: datetime | None,
) -> list[tuple[datetime, datetime]]:
    if existing_start is None or existing_end is None:
        return [(requested_start, requested_end)]

    missing_ranges = []
    if existing_start > requested_start:
        missing_ranges.append((requested_start, min(existing_start, requested_end)))
    if existing_end < requested_end:
        missing_ranges.append((max(existing_end, requested_start), requested_end))
    return missing_ranges


def get_existing_coverage(
    input_path: Path = INPUT_PATH,
) -> tuple[datetime | None, datetime | None]:
    if not input_path.exists() or input_path.stat().st_size == 0:
        return None, None

    first_timestamp = None
    last_timestamp = None
    with input_path.open("r", encoding="utf-8") as file:
        for line in file:
            timestamp = int(json.loads(line)["timestamp"])
            if first_timestamp is None:
                first_timestamp = timestamp
            last_timestamp = timestamp

    if first_timestamp is None:
        return None, None
    return to_datetime(first_timestamp), to_datetime(last_timestamp)


def get_present_minutes(input_path: Path = INPUT_PATH) -> set[datetime]:
    present = set()
    if not input_path.exists() or input_path.stat().st_size == 0:
        return present

    with input_path.open("r", encoding="utf-8") as file:
        for line in file:
            timestamp = int(json.loads(line)["timestamp"])
            present.add(to_datetime(timestamp).replace(second=0, microsecond=0))
    return present


def get_missing_ranges(
    requested_start: datetime,
    requested_end: datetime,
    input_path: Path = INPUT_PATH,
) -> list[tuple[datetime, datetime]]:
    present = get_present_minutes(input_path)
    if not present:
        return [(requested_start, requested_end)]

    current = requested_start.replace(second=0, microsecond=0)
    missing = []
    range_start = None
    step = timedelta(minutes=1)

    while current < requested_end:
        if current not in present:
            if range_start is None:
                range_start = current
        elif range_start is not None:
            missing.append((range_start, current))
            range_start = None
        current += step

    if range_start is not None:
        missing.append((range_start, requested_end))

    return missing


def inspect_coverage() -> None:
    requested_end = datetime.now(timezone.utc)
    requested_start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    existing_start, existing_end = get_existing_coverage()

    print("=== TRADE COVERAGE ===")
    print(f"Requested: {requested_start} -> {requested_end}")
    print(f"Existing:  {existing_start} -> {existing_end}")

    missing = get_missing_ranges(
        requested_start=requested_start,
        requested_end=requested_end,
    )

    print(f"Missing ranges: {len(missing)}")
    for start, end in missing[:20]:
        print(f"  {start} -> {end}")


if __name__ == "__main__":
    inspect_coverage()
