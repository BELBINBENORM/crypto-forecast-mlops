import json
from collections import Counter
from datetime import datetime
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


def inspect_candles(candles):
    print("=== DATASET INSPECTION ===")

    print(f"Rows: {len(candles)}")

    if not candles:
        raise ValueError("Dataset is empty.")

    print(f"Columns: {list(candles[0].keys())}")

    timestamps = [
        datetime.fromisoformat(candle["open_time"])
        for candle in candles
    ]

    print(f"Minimum timestamp: {min(timestamps)}")
    print(f"Maximum timestamp: {max(timestamps)}")

    print(f"Duplicate timestamps: {len(timestamps) - len(set(timestamps))}")

    print(
        f"Chronological order: "
        f"{timestamps == sorted(timestamps)}"
    )

    frequencies = [
        current - previous
        for previous, current in zip(timestamps, timestamps[1:])
    ]

    frequency_counts = Counter(frequencies)

    print("Most common time intervals:")

    for interval, count in frequency_counts.most_common(5):
        print(f"  {interval}: {count}")

    print("\nMissing values:")

    for column in candles[0].keys():
        missing = sum(
            1
            for candle in candles
            if candle.get(column) is None
        )

        print(f"  {column}: {missing}")

    print("\nPrice/volume ranges:")

    print(
        f"  Open:   {min(c['open'] for c in candles)} "
        f"-> {max(c['open'] for c in candles)}"
    )

    print(
        f"  High:   {min(c['high'] for c in candles)} "
        f"-> {max(c['high'] for c in candles)}"
    )

    print(
        f"  Low:    {min(c['low'] for c in candles)} "
        f"-> {max(c['low'] for c in candles)}"
    )

    print(
        f"  Close:  {min(c['close'] for c in candles)} "
        f"-> {max(c['close'] for c in candles)}"
    )

    print(
        f"  Volume: {min(c['volume'] for c in candles)} "
        f"-> {max(c['volume'] for c in candles)}"
    )

    print("\nSample row:")
    for key, value in candles[0].items():
        print(f"  {key}: {value} ({type(value).__name__})")


def main():
    candles = load_candles()
    inspect_candles(candles)


if __name__ == "__main__":
    main()