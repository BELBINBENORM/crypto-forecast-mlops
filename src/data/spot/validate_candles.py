import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


INPUT_PATH = Path(
    "data/raw/spot/binance/btcusdt_15m.jsonl"
)


def load_candles():
    candles = []

    with INPUT_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            candles.append(json.loads(line))

    return candles

def validate_candles(candles):
    timestamps = [
        datetime.fromisoformat(candle["open_time"])
        for candle in candles
    ]

    duplicates = len(timestamps) - len(set(timestamps))

    if timestamps != sorted(timestamps):
        raise ValueError("Candles are not chronologically ordered.")

    invalid_ohlc = []

    for candle in candles:
        open_price = candle["open"]
        high = candle["high"]
        low = candle["low"]
        close = candle["close"]
        volume = candle["volume"]

        if (
            low > high
            or open_price < low
            or open_price > high
            or close < low
            or close > high
            or volume < 0
        ):
            invalid_ohlc.append(candle["open_time"])

    if duplicates:
        raise ValueError("Duplicate timestamps found.")

    if invalid_ohlc:
        raise ValueError("Invalid OHLC/volume data found.")

    return True


def main():
    candles = load_candles()

    print(f"Total candles: {len(candles)}")

    timestamps = [
        datetime.fromisoformat(candle["open_time"])
        for candle in candles
    ]

    duplicates = len(timestamps) - len(set(timestamps))

    print(f"Duplicate timestamps: {duplicates}")

    if timestamps != sorted(timestamps):
        raise ValueError("Candles are not chronologically ordered.")

    gaps = []

    for previous, current in zip(timestamps, timestamps[1:]):
        if current - previous != timedelta(hours=1):
            gaps.append((previous, current))

    print(f"Missing/irregular gaps: {len(gaps)}")

    invalid_ohlc = []

    for candle in candles:
        open_price = candle["open"]
        high = candle["high"]
        low = candle["low"]
        close = candle["close"]
        volume = candle["volume"]

        if (
            low > high
            or open_price < low
            or open_price > high
            or close < low
            or close > high
            or volume < 0
        ):
            invalid_ohlc.append(candle["open_time"])

    print(f"Invalid OHLC/volume rows: {len(invalid_ohlc)}")

    print(f"First candle: {candles[0]['open_time']}")
    print(f"Last candle: {candles[-1]['open_time']}")

    if duplicates:
        raise ValueError("Duplicate timestamps found.")

    if invalid_ohlc:
        raise ValueError("Invalid OHLC/volume data found.")

    print("Validation passed.")


if __name__ == "__main__":
    main()