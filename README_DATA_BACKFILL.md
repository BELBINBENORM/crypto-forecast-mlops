# BTCUSDT Data Backfill

This package backfills two separate raw datasets from Binance public market-data endpoints:

- Spot BTCUSDT OHLCV at **15-minute** resolution
- BTCUSDT aggregate trades

## Date range configuration

The requested range is controlled by `.env`:

```text
DATA_START_DATE=2024-01-01
DATA_END_DATE=TODAY
```

`TODAY` is resolved to the current UTC date when the backfill starts. You can also set an explicit UTC date, for example:

```text
DATA_END_DATE=2026-10-07
```

The `.env` file is local configuration and is ignored by Git. `.env.example` is provided as the safe template to copy for another machine.

## Existing data is preserved

The backfill does not overwrite the existing raw files.

Spot output:

`data/raw/spot/binance/btcusdt_15m.jsonl`

Trade output:

`data/raw/trades/binance/btcusdt_agg_trades.jsonl`

If these files already exist, the code scans them and downloads only missing coverage. Duplicate trade IDs and duplicate spot candle open times are skipped when writing.


## Run tests

```powershell
pytest -v
```

## Run backfill

Install dependencies first:

```powershell
pip install -r requirements.txt
```

Then:

```powershell
python src/data/backfill.py
```

The first run may take a long time, especially for aggregate trades. The script writes each batch to disk rather than keeping the full dataset in memory.

## Important

Do not commit `.env` or generated raw data files to Git. Keep raw-data versioning separate from source-code versioning (for example, with DVC as planned for the project).
