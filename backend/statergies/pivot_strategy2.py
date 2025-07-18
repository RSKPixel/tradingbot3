import os
import pandas as pd
import numpy as np

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

def calculate_supertrend(df, period=7, multiplier=3):
    """Original Supertrend calculation that produced ~305 signals"""
    # ATR Calculation
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    atr = true_range.rolling(period).mean()
    
    # Supertrend Bands
    hl2 = (df['high'] + df['low']) / 2
    upper_band = hl2 + (multiplier * atr)
    lower_band = hl2 - (multiplier * atr)
    
    # Initialize
    supertrend = pd.Series(index=df.index)
    direction = pd.Series(1, index=df.index)  # 1=bullish, -1=bearish
    
    # First value
    supertrend.iloc[0] = upper_band.iloc[0]
    direction.iloc[0] = -1
    
    # Calculate Supertrend
    for i in range(1, len(df)):
        if df['close'].iloc[i] > upper_band.iloc[i-1]:
            supertrend.iloc[i] = lower_band.iloc[i]
            direction.iloc[i] = 1
        elif df['close'].iloc[i] < lower_band.iloc[i-1]:
            supertrend.iloc[i] = upper_band.iloc[i]
            direction.iloc[i] = -1
        else:
            supertrend.iloc[i] = supertrend.iloc[i-1]
            direction.iloc[i] = direction.iloc[i-1]
            
            if supertrend.iloc[i] == upper_band.iloc[i-1] and df['close'].iloc[i] > supertrend.iloc[i]:
                supertrend.iloc[i] = lower_band.iloc[i]
                direction.iloc[i] = 1
            elif supertrend.iloc[i] == lower_band.iloc[i-1] and df['close'].iloc[i] < supertrend.iloc[i]:
                supertrend.iloc[i] = upper_band.iloc[i]
                direction.iloc[i] = -1
    
    return pd.DataFrame({
        'supertrend': supertrend,
        'direction': direction
    })

def pivot_strategy(file, csv_dir) -> pd.DataFrame:
    """Original strategy that generated ~305 signals"""
    try:
        df = pd.read_csv(os.path.join(csv_dir, file), parse_dates=["date"])
        df.set_index("date", inplace=True)
        
        # Get Supertrend values
        st = calculate_supertrend(df)
        atr = calculate_atr(df)
        df['supertrend'] = st['supertrend']
        df['supertrend_direction'] = st['direction']

        # Ema calculation
        df['ema_13'] = df['close'].ewm(span=13, adjust=False).mean()
        df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
        
        # Original Pivot Detection Logic
        n = 5
        df["pivot_high"] = df["high"][(df["high"].shift(1) < df["high"]) &
                                     (df["high"].shift(-1) < df["high"]) &
                                     (df["high"] == df["high"].rolling(2*n+1, center=True).max())]
        
        df["pivot_low"] = df["low"][(df["low"].shift(1) > df["low"]) &
                                   (df["low"].shift(-1) > df["low"]) &
                                   (df["low"] == df["low"].rolling(2*n+1, center=True).min())]

        # Original Signal Generation
        # df["Buy"] = df["pivot_low"].notna() & (df['supertrend_direction'] == 1)
        # df["Sell"] = df["pivot_high"].notna() & (df['supertrend_direction'] == -1)
        # Signal generation using ema and pivot
        df["Buy"] = df["pivot_low"].notna() & (df['ema_13'] > df['ema_50'])
        df["Sell"] = df["pivot_high"].notna() & (df['ema_13'] < df['ema_50']) 

        df["Signal"] = np.select([df["Buy"], df["Sell"]], ["Buy", "Sell"], default="")

        # Original Target Calculation
        df["entry_price"] = np.where(df["Buy"], df["high"], np.where(df["Sell"], df["low"], np.nan))

        # Traget Calculation using ATR for buy
        df['target1'] = np.where(df['Buy'], df['entry_price'] + (1 * atr), df['entry_price'] - (1 * atr))
        df['target2'] = np.where(df['Buy'], df['entry_price'] + (2 * atr), df['entry_price'] - (2 * atr))
        df['target3'] = np.where(df['Buy'], df['entry_price'] + (3 * atr), df['entry_price'] - (3 * atr))
        df['stop_loss'] = np.where(df['Buy'], df['entry_price'] - (1 * atr), df['entry_price'] + (1 * atr))

        # Target Calculation using ATR for sell
        df['target1'] = np.where(df['Sell'], df['entry_price']  - (1 * atr), df['entry_price'] + (1 * atr))
        df['target2'] = np.where(df['Sell'], df['entry_price'] - (2 * atr), df['entry_price'] + (2 * atr))
        df['target3'] = np.where(df['Sell'], df['entry_price'] - (3 * atr), df['entry_price'] + (3 * atr))     
        df['stop_loss'] = np.where(df['Sell'], df['entry_price'] + (1 * atr), df['entry_price'] - (1 * atr))


        # Filter signals
        signals = df[df["Signal"] != ""].copy()
        if signals.empty:
            return None
            
        signals = signals.round(2)
        signals['symbol'] = file.split('.')[0]
        
        return signals.reset_index()[['symbol', 'date', 'open', 'high', 'low', 'close',
                                    'supertrend', 'supertrend_direction',
                                    'Signal', 'entry_price', 'target1', 'target2', 'target3', 'stop_loss']]
    
    except Exception as e:
        print(f"Error processing {file}: {str(e)}")
        return None
    
def calculate_atr(df, period=14):
    """Calculate Average True Range (ATR)"""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(period).mean()

# def calculate_atr_targets(df, atr_multipliers=[1, 2, 3], stop_multiplier=1):
#     """
#     Calculate ATR-based targets and stop loss
#     Returns DataFrame with new target/stop columns
#     """
#     df = df.copy()
#     atr = calculate_atr(df)
    
#     # For Buy signals
#     buy_mask = df['Signal'] == 'Buy'
#     for i, mult in enumerate(atr_multipliers, start=1):
#         df[f'target{i}'] = np.where(buy_mask, 
#                                   df['entry_price'] + (atr * mult),
#                                   df['entry_price'] - (atr * mult))
    
#     df['stop_loss'] = np.where(buy_mask,
#                              df['entry_price'] - (atr * stop_multiplier),
#                              df['entry_price'] + (atr * stop_multiplier))
    
#     return df.round(2)

