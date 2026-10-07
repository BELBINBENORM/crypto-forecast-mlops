import json
from pathlib import Path


INPUT_PATH = Path(
    "data/raw/trades/binance/btcusdt_agg_trades.jsonl"
)


def load_trades():
    trades = []

    with INPUT_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            trades.append(json.loads(line))

    return trades


def validate_trades(trades):
    trade_ids = []
    timestamps = []

    for trade in trades:
        trade_ids.append(trade["aggregate_trade_id"])
        timestamps.append(trade["timestamp"])

        if trade["price"] <= 0:
            raise ValueError("Invalid trade price found.")

        if trade["quantity"] <= 0:
            raise ValueError("Invalid trade quantity found.")

    duplicates = len(trade_ids) - len(set(trade_ids))

    if duplicates:
        raise ValueError("Duplicate aggregate trade IDs found.")

    if timestamps != sorted(timestamps):
        raise ValueError("Trades are not chronologically ordered.")

    return True


def main():
    trades = load_trades()

    print(f"Total trades: {len(trades)}")

    validate_trades(trades)

    print("Validation passed.")


if __name__ == "__main__":
    main()