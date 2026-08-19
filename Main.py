import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

# Page Configuration
st.set_page_config(page_title="Advanced SMC Signal Engine", layout="wide")
st.title("📈 Advanced SMC Trading Engine (OB, FVG, CHOCH, Liquidity)")

# Auto Refresh Switch
auto_refresh = st.sidebar.checkbox("Auto Refresh Data (Every 10s)", value=True)

# Market Presets
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

# --- ADVANCED SMC LOGIC ENGINE ---

def detect_fvg(df):
    """Fair Value Gap (FVG) Detection"""
    bullish_fvg = (df['Low'].iloc[-1] > df['High'].iloc[-3])
    bearish_fvg = (df['High'].iloc[-1] < df['Low'].iloc[-3])
    return bullish_fvg, bearish_fvg

def detect_choch_and_bos(df):
    """Change of Character (CHOCH) & Break of Structure (BOS) Detection"""
    recent_high = df['High'].rolling(20).max().iloc[-2]
    recent_low = df['Low'].rolling(20).min().iloc[-2]
    prev_high = df['High'].rolling(40).max().iloc[-20]
    prev_low = df['Low'].rolling(40).min().iloc[-20]
    
    current_close = df['Close'].iloc[-1]
    
    # CHOCH (Reversal Detection)
    choch_bullish = (current_close > recent_high) and (df['Close'].iloc[-5] < prev_low)
    choch_bearish = (current_close < recent_low) and (df['Close'].iloc[-5] > prev_high)
    
    # BOS (Continuation)
    bos_bullish = (current_close > recent_high)
    bos_bearish = (current_close < recent_low)
    
    return choch_bullish, choch_bearish, bos_bullish, bos_bearish, recent_high, recent_low

def check_discount_premium_zone(df):
    """Fibonacci Premium vs Discount Zone (50% Equilibrium)"""
    max_p = df['High'].tail(30).max()
    min_p = df['Low'].tail(30).min()
    eq = (max_p + min_p) / 2
    current_price = df['Close'].iloc[-1]
    
    is_discount = current_price < eq  # Best for BUY
    is_premium = current_price > eq   # Best for SELL
    return is_discount, is_premium, eq

def analyze_advanced_smc(df):
    bull_fvg, bear_fvg = detect_fvg(df)
    choch_bull, choch_bear, bos_bull, bos_bear, rec_high, rec_low = detect_choch_and_bos(df)
    is_discount, is_premium, eq = check_discount_premium_zone(df)
    
    current = df.iloc[-1]
    
    # Liquidity Sweeps
    buy_sweep = (current['High'] > rec_high) and (current['Close'] < rec_high)
    sell_sweep = (current['Low'] < rec_low) and (current['Close'] > rec_low)
    
    # Order Block (OB) Logic
    bullish_ob = df['Low'].tail(10).min()
    bearish_ob = df['High'].tail(10).max()
    
    current_price = current['Close']
    
    trade = {
        'signal': 'NO TRADE / WAITING ZONE',
        'type': 'NEUTRAL',
        'entry': 0.0,
        'sl': 0.0,
        'target': 0.0,
        'confluences': []
    }
    
    confluences = []
    
    # BULLISH ENTRY SETUP
    if (sell_sweep or choch_bull or bos_bull or bull_fvg) and is_discount:
        if sell_sweep: confluences.append("Liquidity Sweep Below Key Low")
        if choch_bull: confluences.append("CHOCH Reversal Confirmed")
        if bos_bull: confluences.append("Bullish Structure Break (BOS)")
        if bull_fvg: confluences.append("Fair Value Gap (FVG) Tapped")
        confluences.append("Price in Discount Zone (< 50% Eq)")
        
        entry = current_price
        sl = bullish_ob
        risk = entry - sl
        target = entry + (risk * 2.5)  # 1:2.5 Risk-Reward
        
        trade = {
            'signal': 'HIGH PROBABILITY BUY (CALL / CE)',
            'type': 'BULLISH',
            'entry': round(float(entry), 2),
            'sl': round(float(sl), 2),
            'target': round(float(target), 2),
            'confluences': confluences
        }
        
    # BEARISH ENTRY SETUP
    elif (buy_sweep or choch_bear or bos_bear or bear_fvg) and is_premium:
        if buy_sweep: confluences.append("Liquidity Sweep Above Key High")
        if choch_bear: confluences.append("CHOCH Bearish Shift")
        if bos_bear: confluences.append("Bearish Structure Breakdown (BOS)")
        if bear_fvg: confluences.append("Bearish Imbalance/FVG Present")
        confluences.append("Price in Premium Zone (> 50% Eq)")
        
        entry = current_price
        sl = bearish_ob
        risk = sl - entry
        target = entry - (risk * 2.5)  # 1:2.5 Risk-Reward
        
        trade = {
            'signal': 'HIGH PROBABILITY SELL (PUT / PE)',
            'type': 'BEARISH',
            'entry': round(float(entry), 2),
            'sl': round(float(sl), 2),
            'target': round(float(target), 2),
            'confluences': confluences
        }
        
    return trade

# Main Execution Flow
try:
    df = yf.download(symbol, period=selected_period, interval=timeframe)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    if not df.empty:
        trade_setup = analyze_advanced_smc(df)
        
        st.subheader(f"⚡ SMC Full Engine Output: {selected_preset_name} (`{symbol}`)")
        
        if trade_setup['type'] == 'BULLISH':
            st.success(f"### Signal: {trade_setup['signal']}")
        elif trade_setup['type'] == 'BEARISH':
            st.error(f"### Signal: {trade_setup['signal']}")
        else:
            st.warning(f"### Signal: {trade_setup['signal']}")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Live Market Price", round(float(df['Close'].iloc[-1]), 2))
        col2.metric("Optimal Entry", trade_setup['entry'])
        col3.metric("Order Block SL", trade_setup['sl'])
        col4.metric("Target (1:2.5 RR)", trade_setup['target'])
        
        st.subheader("🔥 SMC Trade Confluences (Reasons):")
        if trade_setup['confluences']:
            for reason in trade_setup['confluences']:
                st.write(f"✅ {reason}")
        else:
            st.write("⌛ Market Structure build ho raha hai. Abhi proper SMC Entry Confirmation nahi hai.")
            
        st.subheader("Chart Visualizer")
        st.line_chart(df['Close'])
except Exception as e:
    st.error(f"Data Processing Error: {e}")

# Auto Refresh loop
if auto_refresh:
    time.sleep(10)
    st.rerun()
