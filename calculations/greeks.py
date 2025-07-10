import numpy as np
import pandas as pd
from scipy.stats import norm
from scipy.optimize import minimize_scalar
import streamlit as st
import logging

logger = logging.getLogger(__name__)

def black_scholes_price(volatility: float, option_type: str, spot: float, 
                       strike: float, t: float, r: float) -> float:
    """Calculate Black-Scholes option price"""
    if t <= 0 or volatility <= 0:
        return 0
    
    try:
        d1 = (np.log(spot / strike) + (r + 0.5 * volatility**2) * t) / (volatility * np.sqrt(t))
        d2 = d1 - volatility * np.sqrt(t)
        
        if option_type == 'Call':
            return spot * norm.cdf(d1) - strike * np.exp(-r * t) * norm.cdf(d2)
        else:
            return strike * np.exp(-r * t) * norm.cdf(-d2) - spot * norm.cdf(-d1)
    except:
        return 0

@st.cache_data(max_entries=1000)
def calculate_iv(option_type: str, spot: float, strike: float, 
                market_price: float, t: float, r: float = 0.07) -> float:
    """Calculate implied volatility using optimization"""
    if t <= 0 or market_price <= 0 or spot <= 0 or strike <= 0:
        return 0
    
    try:
        objective = lambda vol: abs(black_scholes_price(vol, option_type, spot, strike, t, r) - market_price)
        result = minimize_scalar(objective, bounds=(0.001, 5.0), method='bounded')
        return result.x
    except:
        return 0

def calculate_greeks_vectorized(iv_array: np.ndarray, option_type: str, spot: float, 
                               strikes: np.ndarray, t: float, r: float = 0.07) -> pd.DataFrame:
    """Vectorized Greeks calculation for better performance"""
    iv_array = np.array(iv_array)
    strikes = np.array(strikes)
    
    results = pd.DataFrame(index=range(len(strikes)), 
                          columns=['delta', 'gamma', 'vega', 'theta', 'rho'])
    results.fillna(0, inplace=True)
    
    mask = (iv_array > 0) & (t > 0) & (strikes > 0)
    if not mask.any():
        return results
    
    valid_iv = iv_array[mask]
    valid_strikes = strikes[mask]
    
    try:
        d1 = (np.log(spot / valid_strikes) + (r + 0.5 * valid_iv**2) * t) / (valid_iv * np.sqrt(t))
        d2 = d1 - valid_iv * np.sqrt(t)
        
        gamma = norm.pdf(d1) / (spot * valid_iv * np.sqrt(t))
        vega = spot * norm.pdf(d1) * np.sqrt(t) / 100
        
        if option_type == 'Call':
            delta = norm.cdf(d1)
            theta = (-spot * norm.pdf(d1) * valid_iv / (2 * np.sqrt(t)) - 
                     r * valid_strikes * np.exp(-r * t) * norm.cdf(d2)) / 365
            rho = valid_strikes * t * np.exp(-r * t) * norm.cdf(d2) / 100
        else:
            delta = norm.cdf(d1) - 1
            theta = (-spot * norm.pdf(d1) * valid_iv / (2 * np.sqrt(t)) + 
                     r * valid_strikes * np.exp(-r * t) * norm.cdf(-d2)) / 365
            rho = -valid_strikes * t * np.exp(-r * t) * norm.cdf(-d2) / 100
        
        results.loc[mask, 'delta'] = delta
        results.loc[mask, 'gamma'] = gamma
        results.loc[mask, 'vega'] = vega
        results.loc[mask, 'theta'] = theta
        results.loc[mask, 'rho'] = rho
    except Exception as e:
        logger.error(f"Error calculating Greeks: {e}")
    
    return results.round(4)
