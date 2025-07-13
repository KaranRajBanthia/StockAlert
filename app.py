import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime

st.set_page_config(page_title="Stock Alert Dashboard", layout="wide")

st.markdown("## 📊 Daily Stock Watchlist Dashboard")
st.markdown("Customize your technical alert thresholds and track top stocks in real time.")

# --- SETTINGS ---
stocks = ["INNOVANA.NS", "AVPINFRA.NS", "AMAL.BO", "EIEL.NS", "CIGNITITEC.NS"]
rsi_upper = st.sidebar.slider("RSI Upper Threshold", 50, 90, 70)
rsi_lower = st.sidebar.slider("RSI Lower Threshold", 10, 50, 30)
volume_spike_factor = st.sidebar.slider("Volume Spike Factor", 1.0, 5.0, 1.5)
start_date = st.sidebar.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=90))

alerts_triggered = []
data = []

# --- FUNCTIONS ---
def calculate_indicators(df):
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    delta = df['Close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=14).mean()
    avg_loss = pd.Series(loss).rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# --- MAIN LOOP ---
with st.container():
    st.success(f"Tracking {len(stocks)} stocks")

    for symbol in stocks:
        try:
            df = yf.download(symbol, start=start_date, progress=False)
            if df.empty:
                st.warning(f"No data found for {symbol}")
                continue

            df = calculate_indicators(df)
            latest = df.iloc[-1]

            rsi = float(latest['RSI'])
            macd = float(latest['MACD'])
            signal = float(latest['Signal'])
            volume = float(latest['Volume'])
            avg_volume = float(df['Volume'].rolling(5).mean().iloc[-1])

            alert = ""

            if rsi > rsi_upper:
                alert += "📈 RSI Overbought  \n"
            elif rsi < rsi_lower:
                alert += "📉 RSI Oversold  \n"

            if volume > volume_spike_factor * avg_volume:
                alert += "🚨 Volume Spike  \n"

            macd_prev = float(df['MACD'].iloc[-2])
            signal_prev = float(df['Signal'].iloc[-2])
            if macd > signal and macd_prev < signal_prev:
                alert += "✅ MACD Bullish Crossover  \n"

            row = {
                "Ticker": symbol,
                "Price": round(float(latest['Close']), 2),
                "RSI": round(rsi, 2),
                "MACD": round(macd, 2),
                "Signal": round(signal, 2),
                "Volume": int(volume),
                "Alert": alert.strip()
            }

            data.append(row)
            if alert:
                alerts_triggered.append(row)

        except Exception as e:
            st.error(f"Error loading {symbol}: {e}")

# --- DISPLAY ---
df_result = pd.DataFrame(data)
df_alerts = pd.DataFrame(alerts_triggered)

if not df_alerts.empty:
    st.subheader("🚨 Alerts Triggered")
    st.dataframe(df_alerts)
else:
    st.info("No alerts triggered today.")

st.subheader("📋 Full Stock Overview")
st.dataframe(df_result if not df_result.empty else pd.DataFrame({"empty": []}))
