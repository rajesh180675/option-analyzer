import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional
import logging
from calculations.greeks import calculate_iv, calculate_greeks_vectorized

logger = logging.getLogger(__name__)

class DataProcessor:
    @staticmethod
    def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names from Breeze API response"""
        column_mapping = {
            'open_interest': 'oi',
            'openInterest': 'oi',
            'open_int': 'oi',
            'oi_change': 'oi_change',
            'change_oi': 'oi_change',
            'changeInOI': 'oi_change',
            'last_traded_price': 'ltp',
            'lastPrice': 'ltp',
            'last_price': 'ltp',
            'total_qty_traded': 'volume',
            'totalTradedVolume': 'volume',
            'traded_volume': 'volume',
            'volume_traded': 'volume',
            'strike': 'strike_price',
            'strikePrice': 'strike_price',
            'option_type': 'right',
            'optionType': 'right',
            'call_put': 'right'
        }
        
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        df.rename(columns=column_mapping, inplace=True)
        
        required_columns = ['oi', 'oi_change', 'ltp', 'volume', 'strike_price', 'right']
        for col in required_columns:
            if col not in df.columns:
                logger.warning(f"Column '{col}' not found, creating with default value 0")
                df[col] = 0
        
        return df
    
    @staticmethod
    def validate_option_data(df: pd.DataFrame) -> bool:
        """Validate option chain data integrity"""
        required_cols = ['strike_price', 'ltp', 'oi', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            logger.warning(f"Missing columns in data: {missing_cols}")
            return False
        
        if df['ltp'].isna().all() or (df['ltp'] == 0).all():
            st.warning("No valid LTP data found")
            return False
        
        return True
    
    @staticmethod
    def process_and_analyze(raw_data: List[Dict], spot_price: float, expiry_date: str) -> pd.DataFrame:
        """Process raw options data and calculate Greeks"""
        if not raw_data:
            st.warning("No options data received.")
            return pd.DataFrame()
        
        df = pd.DataFrame(raw_data)
        
        # Normalize column names first
        df = DataProcessor.normalize_column_names(df)
        
        # Validate data after normalization
        if not DataProcessor.validate_option_data(df):
            return pd.DataFrame()
        
        # Convert to numeric
        numeric_columns = ['oi', 'oi_change', 'ltp', 'volume', 'strike_price']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Separate calls and puts
        calls = df[df['right'].str.upper() == 'CALL'].copy()
        puts = df[df['right'].str.upper() == 'PUT'].copy()
        
        # Merge into chain
        chain = pd.merge(calls, puts, on="strike_price", suffixes=('_call', '_put'), how="outer")
        chain = chain.sort_values("strike_price").fillna(0)
        
        # Calculate Time to Expiry in years
        t = max((datetime.strptime(expiry_date, "%d-%b-%Y") - datetime.now()).total_seconds() / (365 * 24 * 3600), 0)
        
        if t > 0:
            # Vectorized IV calculation
            chain['Call IV'] = chain.apply(
                lambda row: calculate_iv('Call', spot_price, row['strike_price'], 
                                       row['ltp_call'], t) * 100 if row['ltp_call'] > 0 else 0, 
                axis=1
            )
            chain['Put IV'] = chain.apply(
                lambda row: calculate_iv('Put', spot_price, row['strike_price'], 
                                       row['ltp_put'], t) * 100 if row['ltp_put'] > 0 else 0, 
                axis=1
            )
            
            # Calculate Greeks using vectorized function
            strikes = chain['strike_price'].values
            call_ivs = chain['Call IV'].values / 100
            put_ivs = chain['Put IV'].values / 100
            
            call_greeks = calculate_greeks_vectorized(call_ivs, 'Call', spot_price, strikes, t)
            put_greeks = calculate_greeks_vectorized(put_ivs, 'Put', spot_price, strikes, t)
            
            # Add Greeks to chain
            chain = pd.concat([chain, 
                              call_greeks.add_prefix('call_'), 
                              put_greeks.add_prefix('put_')], axis=1)
        
        # Rename columns for display
        chain.rename(columns={
            'oi_call': 'Call OI', 'oi_change_call': 'Call Chng OI', 'ltp_call': 'Call LTP',
            'strike_price': 'Strike', 'ltp_put': 'Put LTP', 'oi_change_put': 'Put Chng OI',
            'oi_put': 'Put OI', 'volume_call': 'Call Volume', 'volume_put': 'Put Volume'
        }, inplace=True)
        
        return chain
    
    @staticmethod
    def track_historical_data_efficient(symbol: str, expiry: str, metrics: Dict[str, Any]) -> None:
        """Efficient historical data tracking with compression"""
        from app_config import config
        
        if 'historical_data' not in st.session_state:
            st.session_state.historical_data = pd.DataFrame()
        
        new_row = pd.DataFrame([{
            'timestamp': datetime.now(),
            'symbol': symbol,
            'expiry': expiry,
            **metrics
        }])
        
        st.session_state.historical_data = pd.concat([
            st.session_state.historical_data, 
            new_row
        ], ignore_index=True).tail(config.MAX_HISTORICAL_RECORDS)
