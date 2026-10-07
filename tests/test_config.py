from datetime import datetime, timezone

import pytest

from data.config import get_date_range, parse_utc_datetime


def test_parse_utc_datetime_date():
    assert parse_utc_datetime("2024-01-01", "TEST") == datetime(
        2024, 1, 1, tzinfo=timezone.utc
    )


def test_parse_utc_datetime_today(monkeypatch):
    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 10, 7, 14, 30, tzinfo=tz)

    monkeypatch.setattr("data.config.datetime", FakeDatetime)

    assert parse_utc_datetime("TODAY", "TEST") == datetime(
        2026, 10, 7, 14, 30, tzinfo=timezone.utc
    )


def test_get_date_range_from_environment(monkeypatch):
    monkeypatch.setenv("DATA_START_DATE", "2024-01-01")
    monkeypatch.setenv("DATA_END_DATE", "2026-10-07")

    start, end = get_date_range()

    assert start == datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert end == datetime(2026, 10, 7, tzinfo=timezone.utc)


def test_get_date_range_rejects_invalid_order(monkeypatch):
    monkeypatch.setenv("DATA_START_DATE", "2026-10-07")
    monkeypatch.setenv("DATA_END_DATE", "2024-01-01")

    with pytest.raises(ValueError, match="must be earlier"):
        get_date_range()
