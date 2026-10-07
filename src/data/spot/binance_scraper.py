from datetime import datetime, timezone
import json
from pathlib import Path

import requests


BINANCE_KLINES_URL = "https://data-api.binance.vision/api/v3/klines"


def fetch_klines(
    symbol: str,
    interval: str,
    start_time: int | None = None,
    end_time: int | None = None,
    limit: int = 1000,
) -> list[dict]:
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    if start_time is not None:
        params["startTime"] = start_time
    if end_time is not None:
        params["endTime"] = end_time

    response = requests.get(BINANCE_KLINES_URL, params=params, timeout=30)
    response.raise_for_status()

    candles = []
    for candle in response.json():
        candles.append(
            {
                "open_time": datetime.fromtimestamp(candle[0] / 1000, tz=timezone.utc),
                "open": float(candle[1]),
                "high": float(candle[2]),
                "low": float(candle[3]),
                "close": float(candle[4]),
                "volume": float(candle[5]),
                "close_time": datetime.fromtimestamp(candle[6] / 1000, tz=timezone.utc),
                "quote_volume": float(candle[7]),
                "trade_count": int(candle[8]),
                "taker_buy_base_volume": float(candle[9]),
                "taker_buy_quote_volume": float(candle[10]),
            }
        )
    return candles


def fetch_historical_klines(
    symbol: str,
    interval: str,
    start_time: int,
    end_time: int,
) -> list[dict]:
    all_candles = []
    current_start = start_time

    while current_start < end_time:
        candles = fetch_klines(
            symbol=symbol,
            interval=interval,
            start_time=current_start,
            end_time=end_time,
            limit=1000,
        )

        if not candles:
            break

        candles = [
            candle
            for candle in candles
            if int(candle["open_time"].timestamp() * 1000) < end_time
        ]

        if not candles:
            break

        all_candles.extend(candles)

        next_start = int(candles[-1]["open_time"].timestamp() * 1000) + 1

        if next_start <= current_start:
            raise RuntimeError("Scraper did not move forward.")

        current_start = next_start

    return all_candles


def load_existing_open_times(output_path: Path) -> set[int]:
    if not output_path.exists() or output_path.stat().st_size == 0:
        return set()
    result = set()
    with output_path.open("r", encoding="utf-8") as file:
        for line in file:
            row = json.loads(line)
            result.add(int(datetime.fromisoformat(row["open_time"]).timestamp() * 1000))
    return result


def find_missing_kline_ranges(
    requested_start: datetime,
    requested_end: datetime,
    existing_open_times: set[int],
    interval_minutes: int = 15,
) -> list[tuple[datetime, datetime]]:
    step = interval_minutes * 60 * 1000
    start_ms = int(requested_start.timestamp() * 1000)
    end_ms = int(requested_end.timestamp() * 1000)
    missing = []
    range_start = None

    current = start_ms
    while current < end_ms:
        if current not in existing_open_times:
            if range_start is None:
                range_start = current
        elif range_start is not None:
            missing.append((
                datetime.fromtimestamp(range_start / 1000, tz=timezone.utc),
                datetime.fromtimestamp(current / 1000, tz=timezone.utc),
            ))
            range_start = None
        current += step

    if range_start is not None:
        missing.append((
            datetime.fromtimestamp(range_start / 1000, tz=timezone.utc),
            requested_end,
        ))
    return missing


def download_missing_kline_ranges(
    symbol: str,
    output_path: Path,
    requested_start: datetime,
    requested_end: datetime,
) -> None:
    existing = load_existing_open_times(output_path)
    missing_ranges = find_missing_kline_ranges(
        requested_start=requested_start,
        requested_end=requested_end,
        existing_open_times=existing,
        interval_minutes=15,
    )

    if not missing_ranges:
        print("Spot 15m data is complete for the requested range.")
        return

    for range_start, range_end in missing_ranges:
        candles = fetch_historical_klines(
            symbol=symbol,
            interval="15m",
            start_time=int(range_start.timestamp() * 1000),
            end_time=int(range_end.timestamp() * 1000),
        )
        with output_path.open("a", encoding="utf-8") as file:
            for candle in candles:
                open_ms = int(candle["open_time"].timestamp() * 1000)
                if open_ms not in existing:
                    row = dict(candle)
                    row["open_time"] = candle["open_time"].isoformat()
                    row["close_time"] = candle["close_time"].isoformat()
                    file.write(json.dumps(row) + "\n")
                    existing.add(open_ms)
        print(f"Spot downloaded: {range_start} -> {range_end}")
