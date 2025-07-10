import streamlit as st
from app_config import config
from utils.helpers import load_credentials

# This callback function is triggered whenever the user changes the symbol
def handle_symbol_change():
    """Sets flags to indicate the symbol has changed and an analysis should run."""
    st.session_state.symbol_changed = True
    st.session_state.run_analysis = True

def create_sidebar():
    """Create and configure the sidebar"""
    with st.sidebar:
        st.header("⚙️ Configuration")

        # API Credentials
        with st.expander("🔐 API Credentials", expanded=True):
            api_key, api_secret = load_credentials()
            session_token = st.text_input("Session Token", type="password",
                                        help="Get from https://api.icicidirect.com/apiuser/login")

        # Symbol Selection with on_change callback
        st.subheader("📊 Symbol Selection")
        st.info("Common Indices: " + ", ".join(config.SYMBOLS))
        
        symbol_input = st.text_input(
            "Enter Symbol (e.g., NIFTY, RELIANCE, ITC)",
            value=st.session_state.get('symbol_input_value', 'NIFTY'), # Persist value across runs
            help="Enter any F&O symbol and press Enter to load data.",
            on_change=handle_symbol_change, # *** THIS IS THE KEY CHANGE ***
            key='symbol_input' # A key is needed for on_change to work reliably
        )
        # Store the current input value in session state
        st.session_state.symbol_input_value = symbol_input
        
        # Ensure the symbol is uppercase and stripped of whitespace for API consistency
        symbol = symbol_input.upper().strip()

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
        risk_free_rate = st.number_input("Risk-Free Rate (%)", value=7.0, step=0.1, min_value=0.0, max_value=20.0) / 100

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
    }
