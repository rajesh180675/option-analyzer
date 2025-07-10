import pandas as pd
import numpy as np
import streamlit as st
from typing import Optional

def prepare_export_data(df: pd.DataFrame, format_type: str) -> Optional[pd.DataFrame]:
    """Prepare and validate data for export"""
    if df.empty:
        st.error("No data to export")
        return None
    
    # Remove any infinite or NaN values
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.fillna(0)
    
    # Format based on export type
    if format_type == "Excel":
        # Ensure numeric columns are properly formatted
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].round(2)
    
    return df
