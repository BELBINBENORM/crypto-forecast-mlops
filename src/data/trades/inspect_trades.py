import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

INPUT_PATH = Path(
    "data/raw/trades/binance/btcusdt_agg_trades.jsonl"
)


def inspect_trades():
    total = 0
    first_timestamp = None
    last_timestamp = None
    previous_timestamp = None

    unique_trade_ids = set()
    duplicate_ids = 0
    out_of_order = 0

    min_price = None
    max_price = None
    min_quantity = None
    max_quantity = None

    buyer_maker_counts = Counter()

    with INPUT_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            trade = json.loads(line)
            total += 1

            trade_id = trade["aggregate_trade_id"]
            timestamp = trade["timestamp"]
            price = trade["price"]
            quantity = trade["quantity"]

            if trade_id in unique_trade_ids:
                duplicate_ids += 1
            unique_trade_ids.add(trade_id)

            if previous_timestamp is not None:
                if timestamp < previous_timestamp:
                    out_of_order += 1

            previous_timestamp = timestamp

            if first_timestamp is None:
                first_timestamp = timestamp

            last_timestamp = timestamp

            min_price = price if min_price is None else min(min_price, price)
            max_price = price if max_price is None else max(max_price, price)

            min_quantity = (
                quantity
                if min_quantity is None
                else min(min_quantity, quantity)
            )
            max_quantity = (
                quantity
                if max_quantity is None
                else max(max_quantity, quantity)
            )

            buyer_maker_counts[trade["is_buyer_maker"]] += 1

    print("=== TRADE DATASET INSPECTION ===")
    print(f"Rows: {total}")
    print(f"Unique aggregate trade IDs: {len(unique_trade_ids)}")
    print(f"Duplicate trade IDs: {duplicate_ids}")
    print(f"Out-of-order timestamps: {out_of_order}")

    print(
        "First timestamp:",
        datetime.fromtimestamp(
            first_timestamp / 1000,
            tz=timezone.utc,
        ),
    )

    print(
        "Last timestamp:",
        datetime.fromtimestamp(
            last_timestamp / 1000,
            tz=timezone.utc,
        ),
    )

    print("\nPrice range:")
    print(f"  {min_price} -> {max_price}")

    print("\nQuantity range:")
    print(f"  {min_quantity} -> {max_quantity}")

    print("\nBuyer maker:")
    print(f"  True:  {buyer_maker_counts[True]}")
    print(f"  False: {buyer_maker_counts[False]}")


if __name__ == "__main__":
    inspect_trades()
