import os
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def load_credentials() -> Tuple[str, str]:
    """Load API credentials from secrets or environment"""
    if 'BREEZE_API_KEY' in st.secrets:
        return st.secrets["BREEZE_API_KEY"], st.secrets["BREEZE_API_SECRET"]
    else:
        load_dotenv()
        return os.getenv("BREEZE_API_KEY"), os.getenv("BREEZE_API_SECRET")

def robust_date_parse(date_string: str) -> Optional[datetime]:
    """Parse dates in multiple formats"""
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ", 
        "%d-%b-%Y", 
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%Y%m%d"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except (ValueError, TypeError):
            continue
    return None
