from datetime import datetime, timezone

from data.trades.inspect_coverage import find_missing_range


def test_find_missing_range():
    requested_start = datetime(
        2025, 10, 7, tzinfo=timezone.utc
    )

    requested_end = datetime(
        2026, 10, 7, tzinfo=timezone.utc
    )

    existing_start = datetime(
        2026, 10, 1, tzinfo=timezone.utc
    )

    existing_end = datetime(
        2026, 10, 2, tzinfo=timezone.utc
    )

    missing = find_missing_range(
        requested_start=requested_start,
        requested_end=requested_end,
        existing_start=existing_start,
        existing_end=existing_end,
    )

    assert missing == [
        (
            requested_start,
            existing_start,
        ),
        (
            existing_end,
            requested_end,
        ),
    ]