import streamlit as st
from app_config import config
from utils.helpers import load_credentials

def create_sidebar():
    """Create and configure the sidebar"""
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Credentials
        with st.expander("🔐 API Credentials", expanded=True):
            api_key, api_secret = load_credentials()
            session_token = st.text_input("Session Token", type="password", 
                                        help="Get from https://api.icicidirect.com/apiuser/login")
        
        # Symbol Selection
        symbol = st.selectbox("📊 Select Symbol", config.SYMBOLS)
        
        # Auto-refresh Settings
        st.subheader("🔄 Auto-Refresh")
        auto_refresh = st.checkbox("Enable Auto-Refresh")
        refresh_interval = None
        if auto_refresh:
            refresh_interval = st.slider("Refresh Interval (seconds)", 10, 300, 60)
        
        # Display Settings
        st.subheader("📈 Display Options")
        show_greeks = st.checkbox("Show Greeks", value=True)
        show_iv_smile = st.checkbox("Show IV Smile", value=True)
        show_volume = st.checkbox("Show Volume Profile", value=True)
        show_strategy = st.checkbox("Show Strategy Analysis", value=False)
        
        # Risk Parameters
        st.subheader("⚡ Risk Parameters")
        risk_free_rate = st.number_input("Risk-Free Rate (%)", value=7.0, step=0.1) / 100
        
        # Export Options
        st.subheader("💾 Export Data")
        export_format = st.selectbox("Export Format", ["JSON", "CSV", "Excel"])
    
    return {
        'api_key': api_key,
        'api_secret': api_secret,
        'session_token': session_token,
        'symbol': symbol,
        'auto_refresh': auto_refresh,
        'refresh_interval': refresh_interval,
        'show_greeks': show_greeks,
        'show_iv_smile': show_iv_smile,
        'show_volume': show_volume,
        'show_strategy': show_strategy,
        'risk_free_rate': risk_free_rate,
        'export_format': export_format
    }
