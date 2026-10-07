from datetime import datetime, timezone

from data.spot.binance_scraper import (
    fetch_historical_klines,
    fetch_klines,
    find_missing_kline_ranges,
)


def test_fetch_klines(monkeypatch):
    fake_response_data = [
        [
            1790812800000,
            "83623.59",
            "84000.00",
            "83500.00",
            "83800.00",
            "123.45",
            1790816399999,
            "10300000.00",
            500,
            "60.00",
            "5000000.00",
            "0",
        ]
    ]

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return fake_response_data

    monkeypatch.setattr(
        "data.spot.binance_scraper.requests.get",
        lambda *args, **kwargs: FakeResponse(),
    )

    candles = fetch_klines(symbol="BTCUSDT", interval="15m")

    assert len(candles) == 1
    candle = candles[0]
    assert candle["open"] == 83623.59
    assert candle["high"] == 84000.00
    assert candle["low"] == 83500.00
    assert candle["close"] == 83800.00
    assert candle["volume"] == 123.45
    assert candle["trade_count"] == 500
    assert candle["open_time"] == datetime(2026, 10, 1, tzinfo=timezone.utc)


def test_find_missing_kline_ranges():
    start = datetime(2026, 10, 1, tzinfo=timezone.utc)
    end = datetime(2026, 10, 1, 1, 0, tzinfo=timezone.utc)
    existing = {
        int(datetime(2026, 10, 1, 0, 0, tzinfo=timezone.utc).timestamp() * 1000),
        int(datetime(2026, 10, 1, 0, 45, tzinfo=timezone.utc).timestamp() * 1000),
    }

    assert find_missing_kline_ranges(start, end, existing) == [
        (
            datetime(2026, 10, 1, 0, 15, tzinfo=timezone.utc),
            datetime(2026, 10, 1, 0, 45, tzinfo=timezone.utc),
        )
    ]

def test_fetch_historical_klines_excludes_end_time(monkeypatch):
    candles = [
        {"open_time": datetime(2026, 10, 1, 23, 45, tzinfo=timezone.utc)},
        {"open_time": datetime(2026, 10, 2, 0, 0, tzinfo=timezone.utc)},
    ]

    def fake_fetch_klines(*args, **kwargs):
        first_candle_time = int(
            datetime(2026, 10, 1, 23, 45, tzinfo=timezone.utc).timestamp() * 1000
        )

        if kwargs["start_time"] <= first_candle_time:
            return candles

        return []

    monkeypatch.setattr(
        "data.spot.binance_scraper.fetch_klines",
        fake_fetch_klines,
    )

    result = fetch_historical_klines(
        symbol="BTCUSDT",
        interval="15m",
        start_time=int(datetime(2026, 10, 1, tzinfo=timezone.utc).timestamp() * 1000),
        end_time=int(datetime(2026, 10, 2, tzinfo=timezone.utc).timestamp() * 1000),
    )

    assert len(result) == 1
    assert result[0]["open_time"] == datetime(
        2026, 10, 1, 23, 45, tzinfo=timezone.utc
    )
    