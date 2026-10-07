import pytest

from data.trades.validate_trades import validate_trades


def make_trade(
    trade_id,
    timestamp,
    price=100.0,
    quantity=1.0,
):
    return {
        "aggregate_trade_id": trade_id,
        "price": price,
        "quantity": quantity,
        "first_trade_id": trade_id,
        "last_trade_id": trade_id,
        "timestamp": timestamp,
        "is_buyer_maker": True,
    }


def test_valid_trades():
    trades = [
        make_trade(1, 1000),
        make_trade(2, 2000),
    ]

    assert validate_trades(trades) is True


def test_duplicate_trade_ids():
    trades = [
        make_trade(1, 1000),
        make_trade(1, 2000),
    ]

    with pytest.raises(
        ValueError,
        match="Duplicate aggregate trade IDs found.",
    ):
        validate_trades(trades)


def test_out_of_order_timestamps():
    trades = [
        make_trade(1, 2000),
        make_trade(2, 1000),
    ]

    with pytest.raises(
        ValueError,
        match="Trades are not chronologically ordered.",
    ):
        validate_trades(trades)


def test_invalid_price():
    trades = [
        make_trade(1, 1000, price=0),
    ]

    with pytest.raises(
        ValueError,
        match="Invalid trade price found.",
    ):
        validate_trades(trades)


def test_invalid_quantity():
    trades = [
        make_trade(1, 1000, quantity=0),
    ]

    with pytest.raises(
        ValueError,
        match="Invalid trade quantity found.",
    ):
        validate_trades(trades)