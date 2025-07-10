import streamlit as st
import pandas as pd
from datetime import datetime
import json
import logging
from io import BytesIO
from streamlit_autorefresh import st_autorefresh
import warnings
warnings.filterwarnings('ignore')

# Import modules
from app_config import config
from models import BreezeAPIError
from api.breeze_client import BreezeClient
from data.processor import DataProcessor
from calculations.metrics import calculate_dashboard_metrics
from visualization.charts import display_sentiment_gauge
from visualization.tables import display_options_chain_table
from ui.sidebar import create_sidebar, create_analysis_tabs
from utils import prepare_export_data

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Pro Options Analyzer", 
    page_icon="🚀", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("🚀 Pro Options & Greeks Analyzer")
    
    # Initialize session state
    if 'last_fetch_time' not in st.session_state:
        st.session_state.last_fetch_time = None
    if 'run_analysis' not in st.session_state:
        st.session_state.run_analysis = False
    if 'theme' not in st.session_state:
        st.session_state.theme = 'light'
    
    # Create sidebar and get configuration
    sidebar_config = create_sidebar()
    
    # Auto-refresh if enabled
    if sidebar_config['auto_refresh'] and sidebar_config['refresh_interval']:
        st_autorefresh(interval=sidebar_config['refresh_interval'] * 1000, key="datarefresh")
    
    # Main Content Area
    if not sidebar_config['session_token']:
        st.warning("⚠️ Please enter your session token to proceed")
        st.info("Get your session token from: https://api.icicidirect.com/apiuser/login")
        with st.expander("📖 How to get Session Token"):
            st.markdown("""
            1. Visit https://api.icicidirect.com/apiuser/login
            2. Login with your ICICI Direct credentials
            3. Copy the session token from the response
            4. Paste it in the Session Token field
            """)
        return
    
    # Initialize Breeze Client
    breeze_client = BreezeClient()
    breeze = breeze_client.initialize(
        sidebar_config['api_key'], 
        sidebar_config['api_secret'], 
        sidebar_config['session_token']
    )
    if not breeze:
        return
    
    # Fetch Expiry Dates
    try:
        expiry_map = breeze_client.get_expiry_map(breeze, sidebar_config['symbol'])
        if not expiry_map:
            st.error("Failed to fetch expiry dates. Please check your connection.")
            return
    except BreezeAPIError as e:
        st.error(str(e))
        return
    
    # Expiry Selection
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        selected_expiry = st.selectbox("📅 Select Expiry", list(expiry_map.keys()))
        st.session_state.selected_display_date = selected_expiry
    
    with col2:
        if st.session_state.last_fetch_time:
            time_diff = (datetime.now() - st.session_state.last_fetch_time).seconds
            st.info(f"Last updated: {st.session_state.last_fetch_time.strftime('%H:%M:%S')} ({time_diff}s ago)")
    
    with col3:
        if st.button("🔄 Refresh Data", type="primary", use_container_width=True):
            st.session_state.run_analysis = True
    
    # Fetch and analyze data
    if st.session_state.run_analysis or sidebar_config['auto_refresh']:
        try:
            api_expiry_date = expiry_map[selected_expiry]
            raw_data, spot_price = breeze_client.get_options_chain_data_with_retry(
                breeze, sidebar_config['symbol'], api_expiry_date
            )
            
            if raw_data and spot_price:
                # Process data
                data_processor = DataProcessor()
                full_chain_df = data_processor.process_and_analyze(raw_data, spot_price, selected_expiry)
                
                if not full_chain_df.empty:
                    # Calculate metrics
                    metrics = calculate_dashboard_metrics(full_chain_df, spot_price)
                    atm_strike = full_chain_df.iloc[(full_chain_df['Strike'] - spot_price).abs().argsort()[:1]]['Strike'].values[0]
                    
                    # Track historical data
                    data_processor.track_historical_data_efficient(
                        sidebar_config['symbol'], selected_expiry, metrics
                    )
                    
                    # Display Key Metrics
                    st.subheader("📊 Key Metrics Dashboard")
                    
                    # First row of metrics
                    col1, col2, col3, col4, col5, col6 = st.columns(6)
                    
                    with col1:
                        st.metric("Spot Price", f"₹{spot_price:,.2f}")
                    with col2:
                        st.metric("ATM Strike", f"₹{atm_strike:,.0f}")
                    with col3:
                        st.metric("Max Pain", f"₹{metrics['max_pain']:,.0f}")
                    with col4:
                        st.metric("PCR", f"{metrics['pcr']:.2f}")
                    with col5:
                        net_oi_delta = f"{metrics['net_oi_change']:+,.0f}"
                        st.metric("Net OI Δ", net_oi_delta)
                    with col6:
                        sentiment_text = "Bullish" if metrics['sentiment'] > 20 else "Bearish" if metrics['sentiment'] < -20 else "Neutral"
                        st.metric("Sentiment", sentiment_text, f"{metrics['sentiment']:.0f}")
                    
                    # Sentiment Gauge
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.plotly_chart(display_sentiment_gauge(metrics['sentiment']), use_container_width=True)
                    
                    with col2:
                        # Support & Resistance Levels
                        st.info(f"**🔴 Key Resistance:** {', '.join(map(str, metrics['resistance']))}")
                        st.success(f"**🟢 Key Support:** {', '.join(map(str, metrics['support']))}")
                        
                        # Additional insights
                        days_to_expiry = (datetime.strptime(selected_expiry, "%d-%b-%Y") - datetime.now()).days
                        st.warning(f"**📅 Days to Expiry:** {days_to_expiry}")
                    
                    # Create analysis tabs
                    create_analysis_tabs(
                        full_chain_df, spot_price, metrics, atm_strike, 
                        selected_expiry, sidebar_config['symbol'], sidebar_config
                    )
                    
                    # Options Chain Table
                    filtered_df = display_options_chain_table(full_chain_df, spot_price, sidebar_config['symbol'])
                    
                    # Export functionality
                    if st.sidebar.button("📥 Export Data", use_container_width=True):
                        export_df = prepare_export_data(full_chain_df, sidebar_config['export_format'])
                        if export_df is not None:
                            export_data_dict = {
                                'metadata': {
                                    'symbol': sidebar_config['symbol'],
                                    'expiry': selected_expiry,
                                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'spot_price': spot_price,
                                    'metrics': metrics
                                },
                                'chain_data': export_df.to_dict('records')
                            }
                            
                            if sidebar_config['export_format'] == "JSON":
                                json_str = json.dumps(export_data_dict, indent=2, default=str)
                                st.download_button(
                                    label="Download JSON",
                                    data=json_str,
                                    file_name=f"{sidebar_config['symbol']}_options_chain_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                    mime="application/json"
                                )
                            elif sidebar_config['export_format'] == "CSV":
                                csv = export_df.to_csv(index=False)
                                st.download_button(
                                    label="Download CSV",
                                    data=csv,
                                    file_name=f"{sidebar_config['symbol']}_options_chain_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv"
                                )
                            elif sidebar_config['export_format'] == "Excel":
                                output = BytesIO()
                                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                                    export_df.to_excel(writer, sheet_name='Options Chain', index=False)
                                    pd.DataFrame([metrics]).to_excel(writer, sheet_name='Metrics', index=False)
                                    if 'historical_data' in st.session_state and not st.session_state.historical_data.empty:
                                        st.session_state.historical_data.to_excel(
                                            writer, sheet_name='Historical', index=False
                                        )
                                excel_data = output.getvalue()
                                st.download_button(
                                    label="Download Excel",
                                    data=excel_data,
                                    file_name=f"{sidebar_config['symbol']}_options_chain_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                
                else:
                    st.error("No data to display. The options chain might be empty.")
            else:
                st.error("Failed to fetch options data. Please try again.")
                
        except BreezeAPIError as e:
            st.error(str(e))
            logger.error(f"API Error: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            logger.error(f"Unexpected error: {e}", exc_info=True)
    else:
        st.info("👆 Click 'Refresh Data' to load the options chain")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center'>
            <p>Built with ❤️ using Streamlit | Data from ICICI Direct Breeze API</p>
            <p style='font-size: 0.8em; color: gray;'>
                Disclaimer: This tool is for educational purposes only. 
                Please do your own research before making any trading decisions.
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )

# Run the application
if __name__ == "__main__":
    main()
