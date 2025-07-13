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
        df = yf.download(symbol, period="3mo", interval="1d", progress=False)
        if df.empty:
            st.warning(f"No data found for {symbol}")
            continue

        indicators = calculate_indicators(df)
        if indicators.empty:
            st.warning(f"Indicators empty for {symbol}")
            continue

        latest = indicators.iloc[-1]
        alert = ""

        # --- RSI Alerts ---
        rsi = float(latest['RSI'])
        if rsi > rsi_upper:
            alert += "📈 RSI Overbought\n"
        elif rsi < rsi_lower:
            alert += "📉 RSI Oversold\n"

        # --- Volume Spike ---
        avg_vol = indicators['Volume'].rolling(5).mean().iloc[-1]
        vol = float(latest['Volume'])
        if vol > volume_spike_factor * avg_vol:
            alert += "🚨 Volume Spike\n"

        # --- MACD Bullish Crossover ---
        try:
            macd_now = float(latest['MACD'])
            macd_prev = float(indicators['MACD'].iloc[-2])
            signal_now = float(latest['Signal'])
            signal_prev = float(indicators['Signal'].iloc[-2])

            if macd_now > signal_now and macd_prev < signal_prev:
                alert += "✅ MACD Bullish Crossover\n"
        except Exception as e:
            st.error(f"MACD logic failed for {symbol}: {e}")

        row = {
            "Ticker": symbol,
            "Price": round(float(latest['Close']), 2),
            "RSI": round(rsi, 2),
            "MACD": round(macd_now, 2),
            "Signal": round(signal_now, 2),
            "Volume": int(vol),
            "Alert": alert.strip()
        }

        data.append(row)
        if alert:
            alerts_triggered.append(row)

    except Exception as e:
        st.error(f"Error loading {symbol}: {e}")

# --- Display Table ---
if data:
    st.dataframe(pd.DataFrame(data))
else:
    st.warning("No data to display. Check ticker symbols or connection.")

# --- Send Alerts ---
if alerts_triggered:
    send_email_alert(alerts_triggered)
    st.sidebar.success(f"Email alerts sent for {len(alerts_triggered)} stock(s)")
else:
    st.sidebar.info("No alerts triggered today")
