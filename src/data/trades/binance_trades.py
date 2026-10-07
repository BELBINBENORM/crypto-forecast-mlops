import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests


BINANCE_TRADES_URL = "https://data-api.binance.vision/api/v3/aggTrades"


def fetch_aggregate_trades(
    symbol: str,
    start_time: int | None = None,
    end_time: int | None = None,
    from_id: int | None = None,
    limit: int = 1000,
) -> list[dict]:
    params = {"symbol": symbol, "limit": limit}
    if from_id is not None:
        params["fromId"] = from_id
    else:
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time

    response = requests.get(BINANCE_TRADES_URL, params=params, timeout=30)
    response.raise_for_status()
    return [
        {
            "aggregate_trade_id": int(t["a"]),
            "price": float(t["p"]),
            "quantity": float(t["q"]),
            "first_trade_id": int(t["f"]),
            "last_trade_id": int(t["l"]),
            "timestamp": int(t["T"]),
            "is_buyer_maker": bool(t["m"]),
        }
        for t in response.json()
    ]


def load_existing_trade_ids(output_path: Path) -> set[int]:
    if not output_path.exists() or output_path.stat().st_size == 0:
        return set()
    ids = set()
    with output_path.open("r", encoding="utf-8") as file:
        for line in file:
            ids.add(int(json.loads(line)["aggregate_trade_id"]))
    return ids


def get_existing_trade_coverage(output_path: Path) -> tuple[datetime | None, datetime | None]:
    if not output_path.exists() or output_path.stat().st_size == 0:
        return None, None
    first = last = None
    with output_path.open("r", encoding="utf-8") as file:
        for line in file:
            ts = int(json.loads(line)["timestamp"])
            if first is None:
                first = ts
            last = ts
    if first is None:
        return None, None
    return (
        datetime.fromtimestamp(first / 1000, tz=timezone.utc),
        datetime.fromtimestamp(last / 1000, tz=timezone.utc),
    )


def find_missing_trade_ranges(
    requested_start: datetime,
    requested_end: datetime,
    existing_timestamps: set[int],
    bucket_minutes: int = 1,
) -> list[tuple[datetime, datetime]]:
    """Find time buckets with no existing trade.

    Trade streams are irregular, so this uses time buckets rather than expecting
    a fixed interval between individual trades. Empty buckets are candidates for
    recovery; Binance may legitimately return no trades for a bucket.
    """
    step = timedelta(minutes=bucket_minutes)
    current = requested_start.replace(second=0, microsecond=0)
    present = {
        datetime.fromtimestamp(ts / 1000, tz=timezone.utc).replace(second=0, microsecond=0)
        for ts in existing_timestamps
    }
    missing = []
    range_start = None
    while current < requested_end:
        bucket_end = min(current + step, requested_end)
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


def download_trade_range(
    symbol: str,
    start_time: int,
    end_time: int,
    output_path: Path,
    existing_ids: set[int] | None = None,
) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    existing_ids = existing_ids if existing_ids is not None else load_existing_trade_ids(output_path)
    current_start = start_time
    next_from_id = None
    written = 0

    with output_path.open("a", encoding="utf-8") as file:
        while current_start < end_time:
            if next_from_id is None:
                trades = fetch_aggregate_trades(
                    symbol=symbol,
                    start_time=current_start,
                    end_time=end_time,
                    limit=1000,
                )
            else:
                trades = fetch_aggregate_trades(
                    symbol=symbol,
                    from_id=next_from_id,
                    limit=1000,
                )

            if not trades:
                break

            for trade in trades:
                trade_id = trade["aggregate_trade_id"]
                timestamp = trade["timestamp"]
                if timestamp < start_time or timestamp >= end_time:
                    continue
                if trade_id in existing_ids:
                    continue
                file.write(json.dumps(trade) + "\n")
                existing_ids.add(trade_id)
                written += 1

            last_id = trades[-1]["aggregate_trade_id"]
            next_from_id = last_id + 1
            last_timestamp = trades[-1]["timestamp"]
            if next_from_id <= last_id:
                raise RuntimeError("Trade scraper did not move forward.")
            if last_timestamp >= end_time:
                break
            current_start = max(current_start, last_timestamp)

    return written


def fetch_historical_aggregate_trades(
    symbol: str,
    start_time: int,
    end_time: int,
    output_path: Path,
) -> None:
    download_trade_range(symbol, start_time, end_time, output_path)


def download_missing_trade_ranges(
    symbol: str,
    output_path: Path,
    requested_start: datetime,
    requested_end: datetime,
) -> None:
    existing_ids = load_existing_trade_ids(output_path)
    existing_timestamps = set()
    if output_path.exists() and output_path.stat().st_size:
        with output_path.open("r", encoding="utf-8") as file:
            for line in file:
                existing_timestamps.add(int(json.loads(line)["timestamp"]))

    missing_ranges = find_missing_trade_ranges(
        requested_start=requested_start,
        requested_end=requested_end,
        existing_timestamps=existing_timestamps,
        bucket_minutes=1,
    )

    if not missing_ranges:
        print("Trade data is complete for the requested minute coverage.")
        return

    for range_start, range_end in missing_ranges:
        written = download_trade_range(
            symbol=symbol,
            start_time=int(range_start.timestamp() * 1000),
            end_time=int(range_end.timestamp() * 1000),
            output_path=output_path,
            existing_ids=existing_ids,
        )
        print(f"Trades downloaded: {range_start} -> {range_end}; rows={written}")


def save_trades(trades: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        for trade in trades:
            file.write(json.dumps(trade) + "\n")
