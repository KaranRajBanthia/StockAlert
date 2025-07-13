
# app.py
import streamlit as st
import pandas as pd
import yfinance as yf
from utils.indicators import calculate_indicators
from email_alerts import send_email_alert

st.set_page_config(page_title="📈 Stock Alert Dashboard", layout="wide")

st.title("📊 Daily Stock Watchlist Dashboard")
st.markdown("Customize your technical alert thresholds and track top stocks in real time.")

# --- Sidebar Configuration ---
st.sidebar.header("📌 Settings")
rsi_upper = st.sidebar.slider("RSI Overbought Threshold", 60, 90, 70)
rsi_lower = st.sidebar.slider("RSI Oversold Threshold", 10, 40, 30)
volume_spike_factor = st.sidebar.slider("Volume Spike Threshold (x Avg Volume)", 1.0, 5.0, 2.0)
uploaded_file = st.sidebar.file_uploader("Upload new stock list (CSV with 'Ticker' column)")

# --- Load Stock List ---
def load_tickers():
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        return df['Ticker'].dropna().unique().tolist()
    else:
        df = pd.read_csv("data/default_stock_list.csv")
        return df['Ticker'].dropna().unique().tolist()

stocks = load_tickers()
st.success(f"Tracking {len(stocks)} stocks")

# --- Fetch & Display Data ---
data = []
alerts_triggered = []

for symbol in stocks:
    try:
        df = yf.download(symbol, period="3mo", interval="1d")
        if df.empty:
            continue
        indicators = calculate_indicators(df)
        latest = indicators.iloc[-1]

        alert = ""
        if latest['RSI'] > rsi_upper:
            alert += "📈 RSI Overbought\n"
        if latest['RSI'] < rsi_lower:
            alert += "📉 RSI Oversold\n"
        if latest['Volume'] > volume_spike_factor * indicators['Volume'].rolling(5).mean().iloc[-1]:
            alert += "🚨 Volume Spike\n"
        if float(latest['MACD']) > float(latest['Signal']) and float(indicators['MACD'].iloc[-2]) < float(indicators['Signal'].iloc[-2]):
            alert += "✅ MACD Bullish Crossover\n"

        row = {
            "Ticker": symbol,
            "Price": latest['Close'],
            "RSI": round(latest['RSI'], 2),
            "MACD": round(latest['MACD'], 2),
            "Signal": round(latest['Signal'], 2),
            "Volume": int(latest['Volume']),
            "Alert": alert.strip()
        }

        data.append(row)
        if alert:
            alerts_triggered.append(row)

    except Exception as e:
        st.error(f"Error loading {symbol}: {e}")

# --- Display Table ---
st.dataframe(pd.DataFrame(data))

# --- Send Alerts ---
if alerts_triggered:
    send_email_alert(alerts_triggered)
    st.sidebar.success(f"Email alerts sent for {len(alerts_triggered)} stock(s)")
else:
    st.sidebar.info("No alerts triggered today")
