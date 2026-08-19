import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. Market Structure & Liquidity Detection Engine
def analyze_smc_structure(df):
    # Swing Highs and Swing Lows (Pivot Points)
    df['Swing_High'] = df['High'][(df['High'] > df['High'].shift(1)) & (df['High'] > df['High'].shift(-1))]
    df['Swing_Low'] = df['Low'][(df['Low'] < df['Low'].shift(1)) & (df['Low'] < df['Low'].shift(-1))]
    
    # Identify recent Liquidity levels
    recent_high = df['High'].rolling(20).max().iloc[-2]
    recent_low = df['Low'].rolling(20).min().iloc[-2]
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Liquidity Sweeps Detection
    buy_liquidity_sweep = (current['High'] > recent_high) and (current['Close'] < recent_high)
    sell_liquidity_sweep = (current['Low'] < recent_low) and (current['Close'] > recent_low)
    
    # Structure Break (BOS / CHOCH)
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
    
    # Bullish Entry Logic: Buy Liquidity Sweep or Bullish BOS Confirmation
    if smc['sell_sweep'] or smc['bos_bullish']:
        entry = current_price
        sl = df['Low'].tail(5).min()  # Recent low as SL
        risk = entry - sl
        target = entry + (risk * 2)   # 1:2 Risk to Reward
        
        trade = {
            'signal': 'BUY ENTRY / CALL',
            'type': 'BULLISH',
            'entry': round(entry, 2),
            'sl': round(sl, 2),
            'target': round(target, 2),
            'reason': 'Liquidity Swept below Key Low + Structure Confirmation'
        }
        
    # Bearish Entry Logic: Sell Liquidity Sweep or Bearish BOS Confirmation
    elif smc['buy_sweep'] or smc['bos_bearish']:
        entry = current_price
        sl = df['High'].tail(5).max()  # Recent high as SL
        risk = sl - entry
        target = entry - (risk * 2)   # 1:2 Risk to Reward
        
        trade = {
            'signal': 'SELL ENTRY / PUT',
            'type': 'BEARISH',
            'entry': round(entry, 2),
            'sl': round(sl, 2),
            'target': round(target, 2),
            'reason': 'Liquidity Swept above Key High + Structure Breakdown'
        }
        
    return trade

# Example Usage in Streamlit:
# df = yf.download("^NSEI", period="5d", interval="5m") # Fetch 5-min Intraday Data
# trade_setup = generate_smc_trade(df)
