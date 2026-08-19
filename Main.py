import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

# Page Configuration
st.set_page_config(page_title="Advanced Trading Signals", layout="wide")
st.title("📈 SMC Signal Engine: NSE, BSE FNO & MCX")

# Auto Refresh Switch
auto_refresh = st.sidebar.checkbox("Auto Refresh Data (Every 10s)", value=True)

# Market Options Presets Including BSE FNO
MARKET_PRESETS = {
    "BSE FNO & Indices": {
        "Sensex Index / Options": "^BSESN",
        "BSE BANKEX": "^NSEBANKEX"
    },
    "NSE FNO & Indices": {
        "Nifty 50 Index": "^NSEI",
        "Bank Nifty Index": "^NSEBANK",
        "FinNifty Index": "NIFTY_FIN_SERVICE.NS",
        "Midcap Nifty": "NIFTY_MID_SELECT.NS"
    },
    "Equity / Stocks": {
        "Reliance Industries": "RELIANCE.NS",
        "TCS": "TCS.NS",
        "HDFC Bank": "HDFCBANK.NS",
        "ICICI Bank": "ICICIBANK.NS",
        "Infosys": "INFY.NS",
        "State Bank of India": "SBIN.NS"
    },
    "MCX Commodities": {
        "Gold Futures": "GC=F",
        "Silver Futures": "SI=F",
        "Crude Oil Futures": "CL=F",
        "Natural Gas Futures": "NG=F"
    }
}

# Sidebar Controls
st.sidebar.header("🎯 Market Selection")
category = st.sidebar.selectbox("Market Category Choose Karein", list(MARKET_PRESETS.keys()))
preset_options = MARKET_PRESETS[category]
selected_preset_name = st.sidebar.selectbox("Symbol Choose Karein", list(preset_options.keys()))
default_symbol = preset_options[selected_preset_name]

symbol = st.sidebar.text_input("Custom Yahoo Ticker (Optional)", value=default_symbol)

st.sidebar.header("⚙️ Strategy Parameters")
timeframe = st.sidebar.selectbox("Select Timeframe", ["1m", "5m", "15m", "30m", "1h", "1d"], index=1)

period_map = {
    "1m": "1d",
    "5m": "5d",
    "15m": "5d",
    "30m": "1mo",
    "1h": "1mo",
    "1d": "6mo"
}
selected_period = period_map[timeframe]

# 1. SMC Structure Analysis
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

# 2. Trade Decision Logic
def generate_smc_trade(df):
    smc = analyze_smc_structure(df)
    current_price = df['Close'].iloc[-1]
    
    trade = {
        'signal': 'NO TRADE',
        'type': 'NEUTRAL',
        'entry': 0.0,
        'sl': 0.0,
        'target': 0.0,
        'reason': 'Liquidity Sweep ya Structure Break ka wait karein.'
    }
    
    if smc['sell_sweep'] or smc['bos_bullish']:
        entry = current_price
        sl = df['Low'].tail(5).min()
        risk = entry - sl
        target = entry + (risk * 2)
        
        trade = {
            'signal': 'BUY ENTRY / CALL (CE)',
            'type': 'BULLISH',
            'entry': round(float(entry), 2),
            'sl': round(float(sl), 2),
            'target': round(float(target), 2),
            'reason': 'Liquidity Swept below Key Low + Bullish Confirmation'
        }
        
    elif smc['buy_sweep'] or smc['bos_bearish']:
        entry = current_price
        sl = df['High'].tail(5).max()
        risk = sl - entry
        target = entry - (risk * 2)
        
        trade = {
            'signal': 'SELL ENTRY / PUT (PE)',
            'type': 'BEARISH',
            'entry': round(float(entry), 2),
            'sl': round(float(sl), 2),
            'target': round(float(target), 2),
            'reason': 'Liquidity Swept above Key High + Bearish Confirmation'
        }
        
    return trade

# Main Display Logic
try:
    df = yf.download(symbol, period=selected_period, interval=timeframe)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    if not df.empty:
        trade_setup = generate_smc_trade(df)
        
        st.subheader(f"📊 Live Data: {selected_preset_name} (`{symbol}`)")
        
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
        
        st.info(f"**Trade Reason:** {trade_setup['reason']}")
        
        st.subheader("Price Movement Chart")
        st.line_chart(df['Close'])
except Exception as e:
    st.error(f"Data Fetching Error: {e}")

# Auto Refresh loop
if auto_refresh:
    time.sleep(10)
    st.rerun()
