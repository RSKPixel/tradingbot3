import pandas as pd
import numpy as np
import os


def check_signals() -> dict:
    # get all files in the nse/15m directory
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    csv_dir = os.path.join(BASE_DIR, "..", "data", "nfo", "15m")
    csv_dir = os.path.abspath(csv_dir)  # Normalize path

    files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
    if not files:
        # print("No CSV files found")
        return {"message": "No CSV files found in nse/15m directory.", "status": "error", "data": []}

    # Example usage
    completed_signals = []
    for file in files:
        # print(f"Processing {file}...               \r", end="\r")
        signals = pivot_strategy(file, csv_dir)
        if signals is not None:
            completed_signals.append(signals)

    if completed_signals:
        all_signals = pd.concat(completed_signals, ignore_index=True)
        all_signals = all_signals[all_signals['date']
                                  == all_signals['date'].max()]
        export_dir = os.path.join(BASE_DIR, "all_signals.csv")
        all_signals.to_csv(export_dir, index=False)
        return {"message": "Signals processed successfully.", "status": "success", "signals": all_signals.to_dict(orient='records')}
    else:
        return {"message": "No signals generated.", "status": "error", "data": []}


def pivot_strategy(file, csv_dir) -> pd.DataFrame:
    # === Load your 15-minute data ===
    df = pd.read_csv(os.path.join(csv_dir, file), parse_dates=["date"])
    df.set_index("date", inplace=True)

    def rolling_linreg(series, period):
        return series.rolling(period).apply(
            lambda x: np.polyval(np.polyfit(range(len(x)), x, 1), len(x) - 1), raw=True
        )

    # Linear regression line values (not slopes!)
    df["TL1"] = rolling_linreg(df["close"], 20)
    df["TL2"] = df["TL1"].ewm(span=5, adjust=False).mean()

    df["TL3"] = rolling_linreg(df["close"], 80)
    df["TL4"] = df["TL3"].ewm(span=20, adjust=False).mean()

    # Short and Long Trend
    df["ShortTrend"] = np.where(df["TL1"] > df["TL2"], "Uptrend", "Downtrend")
    df["LongTrend"] = np.where(df["TL3"] > df["TL4"], "Uptrend", "Downtrend")

    # === Indicators ===
    df["EMA20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["EMA40"] = df["close"].ewm(span=40, adjust=False).mean()
    df["ATR"] = (df["high"] - df["low"]).rolling(window=10).mean()

    # === Donchian Channels (shifted 1 bar like AFL) ===
    df["DonchianUpper"] = df["high"].shift(1).rolling(window=20).max()
    df["DonchianLower"] = df["low"].shift(1).rolling(window=20).min()

    # === Trend Filters (for future use)
    df["UpTrend"] = (df["close"] > (df["low"].rolling(
        20).min() + 2 * df["ATR"])) & (df["EMA20"] > df["EMA40"])
    df["DnTrend"] = (df["close"] < (df["high"].rolling(
        20).max() - 2 * df["ATR"])) & (df["EMA20"] < df["EMA40"])

    # === Pivot Detection (N-bar High/Low pivots) ===
    n = 5
    df["pivot_high"] = df["high"][(df["high"].shift(1) < df["high"]) &
                                  (df["high"].shift(-1) < df["high"]) &
                                  (df["high"] == df["high"].rolling(2 * n + 1, center=True).max())]

    df["pivot_low"] = df["low"][(df["low"].shift(1) > df["low"]) &
                                (df["low"].shift(-1) > df["low"]) &
                                (df["low"] == df["low"].rolling(2 * n + 1, center=True).min())]

    # === Generate Buy/Sell Signals ===
    df["Buy"] = df["pivot_low"].notna()
    df["Sell"] = df["pivot_high"].notna()
    df["Signal"] = np.select([df["Buy"], df["Sell"]], [
                             "Buy", "Sell"], default="")

    # === Entry Price
    df["entry_price"] = np.where(df["Buy"], df["high"],
                                 np.where(df["Sell"], df["low"], np.nan))

    # === Targets and Stop Loss ===
    df["target1"] = np.where(df["Buy"],
                             df["entry_price"] * (1 + 0.0050),
                             df["entry_price"] * (1 - 0.0050))

    df["target2"] = np.where(df["Buy"],
                             df["entry_price"] * (1 + 0.0092),
                             df["entry_price"] * (1 - 0.0112))

    df["target3"] = np.where(df["Buy"],
                             df["entry_price"] * (1 + 0.0179),
                             df["entry_price"] * (1 - 0.0212))

    df["stop_loss"] = np.where(df["Buy"],
                               df["entry_price"] * (1 - 0.0050),
                               df["entry_price"] * (1 + 0.0050))

    # === Filter final signals ===
    signals = df[df["Signal"] != ""].copy()
    signals = signals.round(2)
    signals["ShortTrend"] = df["ShortTrend"]
    signals["LongTrend"] = df["LongTrend"]
    signals['symbol'] = file.split('.')[0]
    signals = signals.reset_index()

    signals = signals[['symbol', "date", "open", "high", "low", "close",
                       "Signal", "entry_price", "target1", "target2", "target3", "stop_loss"]]

    # === Export ===
    return signals
