import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Page Configuration
st.set_page_config(page_title="Advanced Trading Signals", layout="wide")
st.title("📈 Advanced Smart Money Concept (SMC) Trading Signals")

# Sidebar for Inputs
st.sidebar.header("User Inputs")
symbol = st.sidebar.text_input("Enter Ticker Symbol (e.g., ^NSEI, RELIANCE.NS, AAPL, BTC-USD)", "^NSEI")
timeframe = st.sidebar.selectbox("Select Timeframe", ["1m", "2m", "5m", "15m", "30m", "1h", "1d"], index=2)
period = st.sidebar.selectbox("Select Period", ["1d", "5d", "1mo", "3mo", "6mo"], index=1)

# 1. Market Structure & Liquidity Detection Engine
def analyze_smc_structure(df):
    df['Swing_High'] = df['High'][(df['High'] > df['High'].shift(1)) & (df['High'] > df['High'].shift(-1))]
    df['Swing_Low'] = df['Low'][(df['Low'] < df['Low'].shift(1)) & (df['Low'] < df['Low'].shift(-1))]
    
    recent_high = df['High'].rolling(20).max().iloc[-2]
    recent_low = df['Low'].rolling(20).min().iloc[-2]
    
    current = df.iloc[-1]
    
    buy_liquidity_sweep = (current['High'] > recent_high) and (current['Close'] < recent_high)
    sell_liquidity_sweep = (current['Low'] < recent_low) and (current['Close'] > recent_low)
    
    bos_bullish = (current['Close'] > recent_high)
    bos_bearish = (current['Close'] < recent_low)
    
    return {
        'buy_sweep': buy_liquidity_sweep,
        'sell_sweep': sell_liquidity_sweep,
        'bos_bullish': bos_bullish,
        'bos_bearish': bos_bearish,
        'recent_high': recent_high,
        'recent_low': recent_low
    }

# 2. Complete Trade Decision Engine
def generate_smc_trade(df):
    smc = analyze_smc_structure(df)
    current_price = df['Close'].iloc[-1]
    
    trade = {
        'signal': 'NO TRADE',
        'type': 'NEUTRAL',
        'entry': 0.0,
        'sl': 0.0,
        'target': 0.0,
        'reason': 'Waiting for Liquidity Sweep / Structure Break'
    }
    
    if smc['sell_sweep'] or smc['bos_bullish']:
        entry = current_price
        sl = df['Low'].tail(5).min()
        risk = entry - sl
        target = entry + (risk * 2)
        
        trade = {
            'signal': 'BUY ENTRY / CALL',
            'type': 'BULLISH',
            'entry': round(float(entry), 2),
            'sl': round(float(sl), 2),
            'target': round(float(target), 2),
            'reason': 'Liquidity Swept below Key Low + Structure Confirmation'
        }
        
    elif smc['buy_sweep'] or smc['bos_bearish']:
        entry = current_price
        sl = df['High'].tail(5).max()
        risk = sl - entry
        target = entry - (risk * 2)
        
        trade = {
            'signal': 'SELL ENTRY / PUT',
            'type': 'BEARISH',
            'entry': round(float(entry), 2),
            'sl': round(float(sl), 2),
            'target': round(float(target), 2),
            'reason': 'Liquidity Swept above Key High + Structure Breakdown'
        }
        
    return trade

# Main Execution Flow
if st.sidebar.button("Analyze & Fetch Signal"):
    with st.spinner("Fetching Data and Analyzing Market Structure..."):
        try:
            df = yf.download(symbol, period=period, interval=timeframe)
            if df.empty:
                st.error("No data found! Please check the Ticker Symbol or Timeframe.")
            else:
                trade_setup = generate_smc_trade(df)
                
                # Signal Output Cards
                st.subheader(f"Analysis Results for {symbol}")
                
                if trade_setup['type'] == 'BULLISH':
                    st.success(f"### Signal: {trade_setup['signal']}")
                elif trade_setup['type'] == 'BEARISH':
                    st.error(f"### Signal: {trade_setup['signal']}")
                else:
                    st.warning(f"### Signal: {trade_setup['signal']}")
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Current Price", round(float(df['Close'].iloc[-1]), 2))
                col2.metric("Entry Price", trade_setup['entry'])
                col3.metric("Stop Loss (SL)", trade_setup['sl'])
                col4.metric("Target (1:2 R&R)", trade_setup['target'])
                
                st.info(f"**Reason:** {trade_setup['reason']}")
                
                # Chart Display
                st.subheader("Price Chart")
                st.line_chart(df['Close'])
                
        except Exception as e:
            st.error(f"Error fetching data: {e}")
else:
    st.info("Sidebar me symbol select karke **Analyze & Fetch Signal** button par click karein.")
