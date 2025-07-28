import pandas as pd
import numpy as np
import os
import pandas_ta as ta
from data.ta import ta_data


def check_signals() -> dict:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    csv_dir = os.path.join(BASE_DIR, "..", "data", "nfo", "15m")
    csv_dir = os.path.abspath(csv_dir)

    files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
    if not files:
        return {"message": "No CSV files found.", "status": "error", "data": []}

    completed_signals = []
    for file in files:
        signals = strategy(file, csv_dir)
        if signals is not None and not signals.empty:
            completed_signals.append(signals)

    if not completed_signals:
        return {"message": "No signals generated.", "status": "error", "data": []}

    all_signals = pd.concat(completed_signals, ignore_index=True)
    
    if not all_signals.empty:
        latest_date = all_signals['date'].dt.date.max()
        all_signals = all_signals[all_signals['date'].dt.date == latest_date]
        all_signals = all_signals[all_signals['Signal'] != '']  # Ensure no empty signals
    
    all_signals = all_signals.sort_values(by=['Signal'])
    export_dir = os.path.join(BASE_DIR, "all_signals.csv")

    json_ready_signals = []
    for _, row in all_signals.iterrows():
        signal_data = {
            "symbol": str(row['symbol']),
            "date": row['date'].strftime('%Y-%m-%d %H:%M:%S'),
            "open": float(row['open']),
            "high": float(row['high']),
            "low": float(row['low']),
            "close": float(row['close']),
            "Signal": str(row['Signal']),
            "rsi_3": float(row['rsi_3']),
            "ema_13": float(row['ema_13']),
            "ema_50": float(row['ema_50']),
            "ema_200": float(row['ema_200']),
            "entry_price": float(row['entry_price']),
            "target1": float(row['target1']),
            "target2": float(row['target2']),
            "target3": float(row['target3']),
            "stop_loss": float(row['stop_loss']),
            "atr": float(row['atr'])
        }
        json_ready_signals.append(signal_data)

    all_signals = pd.DataFrame(json_ready_signals)
    all_signals.to_csv(export_dir, index=False, float_format='%.2f')

    return {
        "message": f"Found {len(all_signals)} signals",
        "status": "success",
        "signals": all_signals.to_dict(orient='records'),
        "count": len(all_signals)  # Added count for verification
    }

def strategy(file, csv_dir) -> pd.DataFrame:
    try:
        df = pd.read_csv(os.path.join(csv_dir, file), parse_dates=["date"])
        df.set_index("date", inplace=True)

        # Techinical Data
        df = ta_data(df)

        conditions_buy = (
            (df["bull_candle"]) &
            (df["bull_candle"].shift(1)) &
            (df['close'] > df['high'].shift(1)) &
            (df['close'] > df['ema_13']) &
            (df["trend"] == "Up") &
            (df["rsi_3"] > 80))
        
        conditions_sell = (
            (df["bear_candle"]) &
            (df["bear_candle"].shift(1)) &
            (df['close'] < df['low'].shift(1)) &
            (df['close'] < df['ema_13']) &
            (df["trend"] == "Down") &
            (df["rsi_3"] < 20))

        df["Signal"] = np.where(conditions_buy, "Buy",
                          np.where(conditions_sell, "Sell", ""))
        df['symbol'] = file.split('.')[0]
        df['entry_price'] = np.where(df["Signal"] == "Buy", df['high'], np.where(df["Signal"] == "Sell", df['low'], np.nan))
        df['target1'] = np.where(df["Signal"] == "Buy", df['entry_price'] + (1.5 * df['atr']), df['entry_price'] - (1.5 * df['atr']))
        df['target2'] = np.where(df["Signal"] == "Buy", df['entry_price'] + (2.5 * df['atr']), df['entry_price'] - (2.5 * df['atr']))
        df['target3'] = np.where(df["Signal"] == "Buy", df['entry_price'] + (3.5 * df['atr']), df['entry_price'] - (3.5 * df['atr']))
        df['stop_loss'] = np.where(df["Signal"] == "Buy", df['entry_price'] - (1.5 * df['atr']), df['entry_price'] + (1.5 * df['atr']))

        df.reset_index(inplace=True)
        df.to_clipboard(index=False, float_format='%.2f')
        return df[["symbol", "date", "open", "high", "low", "close", "Signal", "ema_13", "ema_50", "ema_200", "rsi_3", "atr", "entry_price", "target1", "target2", "target3", "stop_loss"]].dropna()

    except Exception as e:
        print(f"Error reading {file}: {e}")
        return pd.DataFrame()
