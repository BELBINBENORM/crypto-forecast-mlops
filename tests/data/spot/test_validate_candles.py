from data.spot.validate_candles import validate_candles


def make_candle(timestamp):
    return {
        "open_time": timestamp,
        "open": 100.0,
        "high": 110.0,
        "low": 90.0,
        "close": 105.0,
        "volume": 10.0,
    }


def test_valid_candles():
    candles = [
        make_candle("2026-10-01T00:00:00+00:00"),
        make_candle("2026-10-01T01:00:00+00:00"),
    ]

    assert validate_candles(candles) is True


def test_duplicate_timestamps():
    candles = [
        make_candle("2026-10-01T00:00:00+00:00"),
        make_candle("2026-10-01T00:00:00+00:00"),
    ]

    try:
        validate_candles(candles)
        assert False
    except ValueError as error:
        assert str(error) == "Duplicate timestamps found."


def test_invalid_ohlc():
    candles = [
        make_candle("2026-10-01T00:00:00+00:00"),
    ]

    candles[0]["low"] = 120.0

    try:
        validate_candles(candles)
        assert False
    except ValueError as error:
        assert str(error) == "Invalid OHLC/volume data found."


def test_negative_volume():
    candles = [
        make_candle("2026-10-01T00:00:00+00:00"),
    ]

    candles[0]["volume"] = -1.0

    try:
        validate_candles(candles)
        assert False
    except ValueError as error:
        assert str(error) == "Invalid OHLC/volume data found."