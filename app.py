import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Stock Alert System",
    page_icon="📊",
    layout="wide"
)

# Title and description
st.title("📊 Stock Alert System")
st.markdown("Monitor stocks for technical indicators and get alerts for potential trading opportunities.")

# Sidebar for configuration
st.sidebar.header("Configuration")

# Stock symbols input
stocks_input = st.sidebar.text_area(
    "Enter Stock Symbols (one per line):",
    value="AAPL\nMSFT\nGOOGL\nTSLA\nNVDA",
    height=150
)

# Parse stock symbols
stocks = [symbol.strip().upper() for symbol in stocks_input.split('\n') if symbol.strip()]

# Alert thresholds
rsi_upper = st.sidebar.slider("RSI Overbought Threshold", 70, 85, 75)
rsi_lower = st.sidebar.slider("RSI Oversold Threshold", 15, 30, 25)
volume_spike_factor = st.sidebar.slider("Volume Spike Factor", 1.5, 5.0, 2.0)

# Function to calculate technical indicators
def calculate_indicators(df):
    """Calculate RSI, MACD, and other technical indicators"""
    if df.empty:
        return pd.DataFrame()
    
    # Calculate RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Calculate MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # Add volume
    df['Volume'] = df['Volume']
    
    return df

# Main analysis
if st.button("🔍 Analyze Stocks") and stocks:
    st.subheader("Analysis Results")
    
    # Initialize data containers
    data = []
    alerts_triggered = []
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, symbol in enumerate(stocks):
        try:
            status_text.text(f"Analyzing {symbol}...")
            
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

            # DEBUG: Show what's breaking
            st.write(f"--- {symbol} ---")
            st.write("RSI:", type(latest['RSI']), latest['RSI'])
            st.write("MACD:", type(latest['MACD']), latest['MACD'])
            st.write("Signal:", type(latest['Signal']), latest['Signal'])
            st.write("Volume:", type(latest['Volume']), latest['Volume'])

            try:
                rsi = float(latest['RSI'])
                if rsi > rsi_upper:
                    alert += "📈 RSI Overbought\\n"
                elif rsi < rsi_lower:
                    alert += "📉 RSI Oversold\\n"
            except Exception as e:
                st.error(f"RSI error for {symbol}: {e}")

            try:
                vol = float(latest['Volume'])
                avg_vol = float(indicators['Volume'].rolling(5).mean().iloc[-1])
                if vol > volume_spike_factor * avg_vol:
                    alert += "🚨 Volume Spike\\n"
            except Exception as e:
                st.error(f"Volume error for {symbol}: {e}")

            try:
                macd_now = float(latest['MACD'])
                macd_prev = float(indicators['MACD'].iloc[-2])
                signal_now = float(latest['Signal'])
                signal_prev = float(indicators['Signal'].iloc[-2])
                if macd_now > signal_now and macd_prev < signal_prev:
                    alert += "✅ MACD Bullish Crossover\\n"
            except Exception as e:
                st.error(f"MACD error for {symbol}: {e}")

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
            st.error(f"Top-level error loading {symbol}: {e}")
        
        # Update progress
        progress_bar.progress((i + 1) / len(stocks))
    
    status_text.text("Analysis complete!")
    
    # Display results
    if data:
        st.subheader("📋 All Stocks")
        df_results = pd.DataFrame(data)
        st.dataframe(df_results, use_container_width=True)
        
        if alerts_triggered:
            st.subheader("🚨 Alerts Triggered")
            df_alerts = pd.DataFrame(alerts_triggered)
            st.dataframe(df_alerts, use_container_width=True)
        else:
            st.info("No alerts triggered for the current settings.")
    else:
        st.warning("No data could be analyzed. Please check your stock symbols and try again.")

# Footer
st.markdown("---")
st.markdown("*Data provided by Yahoo Finance*")
