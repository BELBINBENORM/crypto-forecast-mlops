from datetime import datetime, timezone

from data import backfill


def test_get_requested_range_reads_config():
    start, end = backfill.get_requested_range()

    assert start == datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert end.tzinfo == timezone.utc
    assert end >= start


def test_main_uses_completed_15m_boundary_for_spot(monkeypatch):
    calls = []

    monkeypatch.setattr(
        backfill,
        "get_requested_range",
        lambda: (
            datetime(2024, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 10, 7, 8, 51, 44, tzinfo=timezone.utc),
        ),
    )
    monkeypatch.setattr(
        backfill,
        "download_missing_kline_ranges",
        lambda **kwargs: calls.append(("spot", kwargs)),
    )
    monkeypatch.setattr(
        backfill,
        "download_missing_trade_ranges",
        lambda **kwargs: calls.append(("trades", kwargs)),
    )

    backfill.main()

    assert [name for name, _ in calls] == ["spot", "trades"]

    spot_end = calls[0][1]["requested_end"]
    assert spot_end == datetime(
        2026, 10, 7, 8, 45, tzinfo=timezone.utc
    )

    trade_end = calls[1][1]["requested_end"]
    assert trade_end == datetime(
        2026, 10, 7, 8, 51, 44, tzinfo=timezone.utc
    )

    assert calls[0][1]["symbol"] == "BTCUSDT"
    assert calls[0][1]["output_path"].name == "btcusdt_15m.jsonl"
    assert calls[1][1]["output_path"].name == "btcusdt_agg_trades.jsonl"
