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

        # DEBUG: Print types
        st.write(f"--- {symbol} ---")
        st.write("RSI:", type(latest['RSI']), latest['RSI'])
        st.write("MACD:", type(latest['MACD']), latest['MACD'])
        st.write("Signal:", type(latest['Signal']), latest['Signal'])
        st.write("Volume:", type(latest['Volume']), latest['Volume'])

        # RSI
        try:
            rsi = float(latest['RSI'])
            if rsi > rsi_upper:
                alert += "📈 RSI Overbought\n"
            elif rsi < rsi_lower:
                alert += "📉 RSI Oversold\n"
        except Exception as e:
            st.error(f"RSI error for {symbol}: {e}")

        # Volume spike
        try:
            vol = float(latest['Volume'])
            avg_vol = float(indicators['Volume'].rolling(5).mean().iloc[-1])
            if vol > volume_spike_factor * avg_vol:
                alert += "🚨 Volume Spike\n"
        except Exception as e:
            st.error(f"Volume error for {symbol}: {e}")

        # MACD crossover
        try:
            macd_now = float(latest['MACD'])
            macd_prev = float(indicators['MACD'].iloc[-2])
            signal_now = float(latest['Signal'])
            signal_prev = float(indicators['Signal'].iloc[-2])
            if macd_now > signal_now and macd_prev < signal_prev:
                alert += "✅ MACD Bullish Crossover\n"
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
