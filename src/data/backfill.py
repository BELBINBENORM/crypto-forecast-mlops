from pathlib import Path

from data.config import get_date_range
from data.spot.binance_scraper import download_missing_kline_ranges
from data.trades.binance_trades import download_missing_trade_ranges


SYMBOL = "BTCUSDT"

SPOT_OUTPUT = Path("data/raw/spot/binance/btcusdt_15m.jsonl")
TRADES_OUTPUT = Path("data/raw/trades/binance/btcusdt_agg_trades.jsonl")


def get_requested_range():
    return get_date_range()


def main() -> None:
    requested_start, requested_end = get_requested_range()
    spot_end = requested_end.replace(
        minute=(requested_end.minute // 15) * 15,
        second=0,
        microsecond=0,
    )

    print(f"Requested range: {requested_start} -> {requested_end}")

    print("\n=== SPOT 15m ===")
    download_missing_kline_ranges(
        symbol=SYMBOL,
        output_path=SPOT_OUTPUT,
        requested_start=requested_start,
        requested_end=spot_end,
    )

    print("\n=== AGGREGATE TRADES ===")
    download_missing_trade_ranges(
        symbol=SYMBOL,
        output_path=TRADES_OUTPUT,
        requested_start=requested_start,
        requested_end=requested_end,
    )


if __name__ == "__main__":
    main()
