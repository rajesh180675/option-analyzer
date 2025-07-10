import numpy as np
import pandas as pd
from typing import Dict, Any

def calculate_dashboard_metrics(chain_df: pd.DataFrame, spot_price: float) -> Dict[str, Any]:
    """Calculate key metrics from options chain"""
    # Vectorized Max Pain calculation
    strikes = chain_df['Strike'].values
    call_oi = chain_df['Call OI'].values
    put_oi = chain_df['Put OI'].values
    
    strike_matrix = strikes[:, np.newaxis]
    call_pain = np.sum(np.maximum(strike_matrix - strikes, 0) * call_oi, axis=1)
    put_pain = np.sum(np.maximum(strikes - strike_matrix, 0) * put_oi, axis=1)
    total_pain = call_pain + put_pain
    max_pain = strikes[np.argmin(total_pain)] if len(total_pain) > 0 else 0
    
    # PCR and other metrics
    total_call_oi = chain_df['Call OI'].sum()
    total_put_oi = chain_df['Put OI'].sum()
    pcr = round(total_put_oi / total_call_oi if total_call_oi > 0 else 0, 2)
    net_oi_change = chain_df['Put Chng OI'].sum() - chain_df['Call Chng OI'].sum()
    
    # Enhanced Sentiment Score
    sentiment_score = 0
    
    # PCR Analysis
    if pcr > 1.2:
        sentiment_score += 30
    elif pcr < 0.8:
        sentiment_score -= 30
    else:
        sentiment_score += (pcr - 1) * 75
    
    # OI Change Analysis
    if net_oi_change > 0:
        sentiment_score += 25
    elif net_oi_change < 0:
        sentiment_score -= 25
    
    # Max Pain Analysis
    if spot_price < max_pain:
        sentiment_score += 20
    elif spot_price > max_pain:
        sentiment_score -= 20
    
    # Volume Analysis
    if 'Call Volume' in chain_df.columns and 'Put Volume' in chain_df.columns:
        call_volume = chain_df['Call Volume'].sum()
        put_volume = chain_df['Put Volume'].sum()
        volume_ratio = put_volume / call_volume if call_volume > 0 else 0
        if volume_ratio > 1.1:
            sentiment_score += 15
        elif volume_ratio < 0.9:
            sentiment_score -= 15
    
    # IV Skew Analysis
    if 'Call IV' in chain_df.columns and 'Put IV' in chain_df.columns:
        atm_idx = (chain_df['Strike'] - spot_price).abs().idxmin()
        if atm_idx > 0 and atm_idx < len(chain_df) - 1:
            call_iv_skew = chain_df.loc[atm_idx, 'Call IV'] - chain_df['Call IV'].mean()
            put_iv_skew = chain_df.loc[atm_idx, 'Put IV'] - chain_df['Put IV'].mean()
            if put_iv_skew > call_iv_skew:
                sentiment_score += 10
            else:
                sentiment_score -= 10
    
    return {
        'max_pain': max_pain,
        'resistance': chain_df.nlargest(3, 'Call OI')['Strike'].tolist(),
        'support': chain_df.nlargest(3, 'Put OI')['Strike'].tolist(),
        'pcr': pcr,
        'net_oi_change': net_oi_change,
        'sentiment': max(-100, min(100, sentiment_score)),
        'total_call_oi': total_call_oi,
        'total_put_oi': total_put_oi
    }
