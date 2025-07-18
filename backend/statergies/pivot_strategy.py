import pandas as pd
import numpy as np
import os


def check_signals() -> dict:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    csv_dir = os.path.join(BASE_DIR, "..", "data", "nfo", "15m")
    csv_dir = os.path.abspath(csv_dir)

    files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
    if not files:
        return {"message": "No CSV files found.", "status": "error", "data": []}

    completed_signals = []
    for file in files:
        signals = pivot_strategy(file, csv_dir)
        if signals is not None and not signals.empty:
            completed_signals.append(signals)

    if not completed_signals:
        return {"message": "No signals generated.", "status": "error", "data": []}

    all_signals = pd.concat(completed_signals, ignore_index=True)
    
    # STRICT date filtering (same as before)
    if not all_signals.empty:
        latest_date = all_signals['date'].dt.date.max()
        all_signals = all_signals[all_signals['date'].dt.date == latest_date]
    
    all_signals = all_signals.sort_values(by=['Signal'])
    
    # Export to CSV (original format)
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
            # "supertrend": float(row['supertrend']),
            # "supertrend_direction": str(row['supertrend_direction']),
            "entry_price": float(row['entry_price']),
            "target1": float(row['target1']),
            "target2": float(row['target2']),
            "target3": float(row['target3']),
            "stop_loss": float(row['stop_loss'])
        }
        json_ready_signals.append(signal_data)

    all_signals = pd.DataFrame(json_ready_signals)
    all_signals.to_csv(export_dir, index=False, float_format='%.2f')
    all_signals.to_clipboard(index=False, float_format='%.2f')  # Copy to clipboard for easy access
    
    # JSON-compatible preparation (ONLY for the response)
    # json_data = all_signals.copy()
    # json_data['date'] = json_data['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
    # json_data = json_data.replace([np.inf, -np.inf, np.nan], None)
    # all_signals = json_data.copy()
    
    return {
        "message": f"Found {len(all_signals)} signals",
        "status": "success",
        "signals": all_signals.to_dict(orient='records'),
        "count": len(all_signals)  # Added count for verification
    }

def pivot_strategy(file, csv_dir) -> pd.DataFrame:
    # === Load data ===
    df = pd.read_csv(os.path.join(csv_dir, file), parse_dates=["date"])
    df.set_index("date", inplace=True)

    # === Supertrend Implementation ===
    atr_period = 10
    multiplier = 3
    
    # Calculate ATR
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    atr = true_range.rolling(atr_period).mean()
    
    # Supertrend calculation
    supertrend_df = calculate_supertrend(df)
    df['supertrend'] = supertrend_df['supertrend']
    df['supertrend_direction'] = supertrend_df['direction']
    
    # === Pivot Detection ===
    n = 5
    df["pivot_high"] = df["high"][(df["high"].shift(1) < df["high"]) &
                                (df["high"].shift(-1) < df["high"]) &
                                (df["high"] == df["high"].rolling(2 * n + 1, center=True).max())]

    df["pivot_low"] = df["low"][(df["low"].shift(1) > df["low"]) &
                              (df["low"].shift(-1) > df["low"]) &
                              (df["low"] == df["low"].rolling(2 * n + 1, center=True).min())]

    # === Generate Signals with Supertrend Confirmation ===
    df["Buy"] = df["pivot_low"].notna() & (df['supertrend_direction'] == 1)
    df["Sell"] = df["pivot_high"].notna() & (df['supertrend_direction'] == -1)
    
    df["Signal"] = np.select([df["Buy"], df["Sell"]], ["Buy", "Sell"], default="")

    # === Entry and Exit Levels ===
    df["entry_price"] = np.where(df["Buy"], df["high"],
                               np.where(df["Sell"], df["low"], np.nan))
    
    # Dynamic targets based on ATR
    df["target1"] = np.where(df["Buy"],
                           df["entry_price"] + (1 * atr),
                           df["entry_price"] - (1 * atr))
    df["target2"] = np.where(df["Buy"],
                           df["entry_price"] + (2 * atr),
                           df["entry_price"] - (2 * atr))
    df["target3"] = np.where(df["Buy"],
                           df["entry_price"] + (3 * atr),
                           df["entry_price"] - (3 * atr))
    df["stop_loss"] = np.where(df["Buy"],
                             df["entry_price"] - (1 * atr),
                             df["entry_price"] + (1 * atr))

    # === Filter and return signals ===
    signals = df[df["Signal"] != ""].copy()
    signals = signals.round(2)
    signals['symbol'] = file.split('.')[0]
    signals = signals.reset_index()

    output_cols = ['symbol', 'date', 'open', 'high', 'low', 'close',
                  'supertrend', 'supertrend_direction',
                  'Signal', 'entry_price', 'target1', 'target2', 'target3', 'stop_loss']
    
    return signals[output_cols]

def calculate_supertrend(df, period=7, multiplier=3):
    """
    Calculate Supertrend indicator with proper pandas indexing
    Returns DataFrame with 'supertrend' and 'direction' columns
    """
    # Calculate ATR
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.ewm(alpha=1/period, adjust=False).mean()
    
    # Calculate basic bands
    hl2 = (df['high'] + df['low']) / 2
    upper_band = hl2 + multiplier * atr
    lower_band = hl2 - multiplier * atr
    
    # Initialize columns
    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(1, index=df.index)  # 1 = bullish, -1 = bearish
    
    # First value initialization
    supertrend.iloc[0] = upper_band.iloc[0]
    direction.iloc[0] = -1  # Start with bearish
    
    # Calculate Supertrend
    for i in range(1, len(df)):
        prev_idx = df.index[i-1]
        curr_idx = df.index[i]
        
        if direction.iloc[i-1] == 1:  # Previous was bullish
            if df.loc[curr_idx, 'close'] > supertrend.loc[prev_idx]:
                supertrend.loc[curr_idx] = max(lower_band.loc[curr_idx], supertrend.loc[prev_idx])
                direction.loc[curr_idx] = 1
            else:
                supertrend.loc[curr_idx] = upper_band.loc[curr_idx]
                direction.loc[curr_idx] = -1
        else:  # Previous was bearish
            if df.loc[curr_idx, 'close'] < supertrend.loc[prev_idx]:
                supertrend.loc[curr_idx] = min(upper_band.loc[curr_idx], supertrend.loc[prev_idx])
                direction.loc[curr_idx] = -1
            else:
                supertrend.loc[curr_idx] = lower_band.loc[curr_idx]
                direction.loc[curr_idx] = 1
    
    return pd.DataFrame({
        'supertrend': supertrend,
        'direction': direction
    })

def calculate_supertrend(df, period=10, multiplier=2.5):
    """
    Enhanced Supertrend with smoother trend confirmation
    Returns DataFrame with 'supertrend' and 'direction' columns
    """
    # Calculate ATR with EMA smoothing
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.ewm(span=period, adjust=False).mean()
    
    # Calculate bands
    hl2 = (df['high'] + df['low']) / 2
    upper_band = hl2 + (multiplier * atr)
    lower_band = hl2 - (multiplier * atr)
    
    # Initialize with NaN
    supertrend = pd.Series(np.nan, index=df.index)
    direction = pd.Series(0, index=df.index)  # 0=neutral
    
    # Warm-up period (no signals)
    for i in range(period, len(df)):
        curr, prev = df.index[i], df.index[i-1]
        
        # Trend continuation rules
        if direction[prev] == 1:  # Previous bullish
            if df.loc[curr, 'close'] > supertrend[prev]:
                supertrend[curr] = max(lower_band[curr], supertrend[prev])
                direction[curr] = 1
            else:
                supertrend[curr] = upper_band[curr]
                direction[curr] = -1
        elif direction[prev] == -1:  # Previous bearish
            if df.loc[curr, 'close'] < supertrend[prev]:
                supertrend[curr] = min(upper_band[curr], supertrend[prev])
                direction[curr] = -1
            else:
                supertrend[curr] = lower_band[curr]
                direction[curr] = 1
        else:  # Neutral start
            supertrend[curr] = upper_band[curr] if df.loc[curr, 'close'] < hl2[curr] else lower_band[curr]
            direction[curr] = -1 if df.loc[curr, 'close'] < hl2[curr] else 1
    
    # Require 2-period confirmation
    confirmed_direction = direction.rolling(2).mean()
    return pd.DataFrame({
        'supertrend': supertrend,
        'direction': np.where(confirmed_direction > 0.5, 1, np.where(confirmed_direction < -0.5, -1, 0))
    })

