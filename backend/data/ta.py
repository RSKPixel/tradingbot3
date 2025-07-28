import pandas_ta as ta
import pandas as pd
import numpy as np

def ta_data(df: pd.DataFrame) -> pd.DataFrame:

    # EMA Trend Filters
    df["ema_13"] = ta.ema(df['close'], length=13)
    df["ema_50"] = ta.ema(df['close'], length=50)
    df["ema_200"] = ta.ema(df['close'], length=200)

    # RSI (Standard 14-period)
    df['rsi_3'] = ta.rsi(df['close'], length=3)
    df['rsi_13'] = ta.rsi(df['close'], length=13)

    # ATR (14-period)
    df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)

    # Bullish and Bearish Candles
    df["bull_candle"] = (df["close"] > df["open"])
    df["bear_candle"] = (df["close"] < df["open"])

    # trend determination
    df["trend"] = "No Trend"
    df["trend"] = np.where((df["ema_13"] > df["ema_50"]) & (df["ema_50"] > df["ema_200"]), "Up", df["trend"])
    df["trend"] = np.where((df["ema_13"] < df["ema_50"]) & (df["ema_50"] < df["ema_200"]), "Down", df["trend"])
    df = df.join(ta.supertrend(df['high'], df['low'], df['close'], length=10, multiplier=3))

    # Pivot Points
    n=5
    df["pivot_high"] = df["high"] == df["high"].rolling(window=2*n+1, center=True).max()
    df["pivot_low"] = df["low"] == df["low"].rolling(window=2*n+1, center=True).min()

    df["close_max_20"] = df['close'].shift(1).rolling(window=20).max()
    df["volume_sma_20"] = df['volume'].rolling(window=20).mean()



    return df