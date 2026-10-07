import json

from data.trades.binance_trades import (
    fetch_aggregate_trades,
    fetch_historical_aggregate_trades,
    download_trade_range,
    find_missing_trade_ranges,
)


def test_fetch_aggregate_trades(monkeypatch):
    fake_response_data = [{"a": 123456, "p": "83623.59", "q": "0.0015", "f": 987654, "l": 987654, "T": 1790812800000, "m": True}]

    class FakeResponse:
        def raise_for_status(self): pass
        def json(self): return fake_response_data

    monkeypatch.setattr("data.trades.binance_trades.requests.get", lambda *args, **kwargs: FakeResponse())
    trades = fetch_aggregate_trades("BTCUSDT", start_time=1790812800000, end_time=1790812860000)

    assert len(trades) == 1
    assert trades[0]["aggregate_trade_id"] == 123456
    assert trades[0]["price"] == 83623.59
    assert trades[0]["quantity"] == 0.0015
    assert trades[0]["timestamp"] == 1790812800000


def test_fetch_historical_aggregate_trades(monkeypatch, tmp_path):
    calls = []

    def fake_fetch(symbol, start_time=None, end_time=None, from_id=None, limit=1000):
        calls.append((start_time, from_id))
        if len(calls) == 1:
            return [{"aggregate_trade_id": 1, "price": 100.0, "quantity": 1.0, "first_trade_id": 10, "last_trade_id": 10, "timestamp": 1000, "is_buyer_maker": True}]
        if len(calls) == 2:
            return [{"aggregate_trade_id": 2, "price": 101.0, "quantity": 2.0, "first_trade_id": 11, "last_trade_id": 11, "timestamp": 2000, "is_buyer_maker": False}]
        return []

    monkeypatch.setattr("data.trades.binance_trades.fetch_aggregate_trades", fake_fetch)
    output_path = tmp_path / "trades.jsonl"
    fetch_historical_aggregate_trades("BTCUSDT", 0, 3000, output_path)

    with output_path.open(encoding="utf-8") as file:
        saved = [json.loads(line) for line in file]

    assert [x["aggregate_trade_id"] for x in saved] == [1, 2]
    assert calls == [(0, None), (None, 2), (None, 3)]


def test_download_trade_range_skips_existing_ids(monkeypatch, tmp_path):
    output_path = tmp_path / "trades.jsonl"
    output_path.write_text(json.dumps({"aggregate_trade_id": 1, "timestamp": 1000}) + "\n", encoding="utf-8")
    calls = []

    calls = []

    def fake_fetch(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return [
                {"aggregate_trade_id": 1, "price": 100, "quantity": 1, "timestamp": 1000},
                {"aggregate_trade_id": 2, "price": 101, "quantity": 1, "timestamp": 2000},
            ]
        return []

    monkeypatch.setattr("data.trades.binance_trades.fetch_aggregate_trades", fake_fetch)
    written = download_trade_range("BTCUSDT", 0, 3000, output_path)

    assert written == 1
    rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert [row["aggregate_trade_id"] for row in rows] == [1, 2]


def test_find_missing_trade_ranges():
    from datetime import datetime, timezone
    start = datetime(2026, 10, 1, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 10, 1, 0, 4, tzinfo=timezone.utc)
    existing = {
        int(datetime(2026, 10, 1, 0, 0, 10, tzinfo=timezone.utc).timestamp() * 1000),
        int(datetime(2026, 10, 1, 0, 2, 10, tzinfo=timezone.utc).timestamp() * 1000),
        int(datetime(2026, 10, 1, 0, 3, 10, tzinfo=timezone.utc).timestamp() * 1000),
    }
    assert find_missing_trade_ranges(start, end, existing) == [
        (datetime(2026, 10, 1, 0, 1, tzinfo=timezone.utc), datetime(2026, 10, 1, 0, 2, tzinfo=timezone.utc))
    ]
