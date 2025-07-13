import pandas as pd

def calculate_indicators(df):
    df = df.copy()

    # Ensure only 'Close' and 'Volume' exist to avoid misalignment
    df = df[['Close', 'Volume']]

    # --- MACD ---
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()

    # --- RSI ---
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=14, min_periods=14).mean()
    avg_loss = loss.rolling(window=14, min_periods=14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    # --- Append to DataFrame ---
    df['MACD'] = macd
    df['Signal'] = signal
    df['RSI'] = rsi

    return df
