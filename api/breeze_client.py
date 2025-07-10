import streamlit as st
from breeze_connect import BreezeConnect
from typing import Dict, List, Tuple, Optional, Any
import logging
import time
from datetime import datetime
from models import BreezeAPIError
from app_config import config

logger = logging.getLogger(__name__)

class BreezeClient:
    def __init__(self):
        self.breeze = None

    def handle_api_error(self, response: Dict[str, Any]) -> List[Dict]:
        """Centralized API error handling"""
        if not response.get('Success'):
            error_msg = response.get('Error', 'Unknown API error')
            if 'session' in error_msg.lower():
                raise BreezeAPIError("Session expired. Please refresh your session token.")
            elif 'rate limit' in error_msg.lower():
                raise BreezeAPIError("Rate limit exceeded. Please wait before retrying.")
            else:
                raise BreezeAPIError(f"API Error: {error_msg}")
        return response['Success']

    @st.cache_resource(show_spinner="Connecting to Breeze API...")
    def initialize(_self, api_key: str, api_secret: str, session_token: str) -> Optional[BreezeConnect]:
        """Initialize Breeze API connection"""
        try:
            logger.info("Initializing Breeze connection")
            _self.breeze = BreezeConnect(api_key=api_key)
            _self.breeze.generate_session(api_secret=api_secret, session_token=session_token)
            st.success("API Connection Successful!")
            return _self.breeze
        except Exception as e:
            logger.error(f"Failed to initialize Breeze: {e}")
            st.error(f"Connection Failed: {e}")
            return None

    @st.cache_data(ttl=config.CACHE_TTL, show_spinner="Fetching expiry dates...")
    def get_expiry_map(_self, _breeze: BreezeConnect, symbol: str) -> Dict[str, str]:
        """Fetch and sort available expiry dates for the symbol"""
        from utils.helpers import robust_date_parse

        try:
            logger.info(f"Fetching expiry dates for {symbol}")

            spot_data = _breeze.get_quotes(stock_code=symbol, exchange_code="NSE", product_type="cash")
            spot_data = _self.handle_api_error(spot_data)
            spot_price = float(spot_data[0]['ltp'])

            step = config.get_strike_step(symbol)
            nearby_strike = round(spot_price / step) * step

            data = _breeze.get_option_chain_quotes(
                stock_code=symbol, exchange_code="NFO", product_type="options",
                right="Call", expiry_date=None, strike_price=nearby_strike
            )
            data = _self.handle_api_error(data)

            # --- MODIFICATION: Robust chronological sorting ---
            raw_dates = list(set(item['expiry_date'] for item in data))

            # Create a list of tuples with parsed dates to sort correctly
            parsed_dates_list = []
            for d in raw_dates:
                parsed_date = robust_date_parse(d)
                if parsed_date and parsed_date.date() >= datetime.now().date():
                    # Tuple format: (datetime_object, display_string, api_string)
                    parsed_dates_list.append((parsed_date, parsed_date.strftime("%d-%b-%Y"), d))
            
            # Sort the list based on the datetime object (the first element of the tuple)
            parsed_dates_list.sort(key=lambda x: x[0])

            # Create the final map from the sorted list, preserving the order
            expiry_map = {display_str: api_str for dt_obj, display_str, api_str in parsed_dates_list}

            logger.info(f"Found {len(expiry_map)} sorted expiry dates for {symbol}")
            return expiry_map

        except BreezeAPIError as e:
            st.error(str(e))
            return {}
        except Exception as e:
            logger.error(f"Error fetching expiry dates for {symbol}: {e}")
            st.error(f"Could not fetch expiry dates for '{symbol}': {e}")
            return {}

    def fetch_data_with_progress(self, _breeze: BreezeConnect, symbol: str,
                               api_expiry_date: str) -> Tuple[Optional[List], Optional[float]]:
        """Fetch options chain data with progress indicator"""
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            status_text.text("Fetching spot price...")
            progress_bar.progress(25)

            spot_data = _breeze.get_quotes(stock_code=symbol, exchange_code="NSE", product_type="cash")
            spot_data = self.handle_api_error(spot_data)
            spot_price = float(spot_data[0]['ltp'])

            status_text.text("Fetching call options...")
            progress_bar.progress(50)

            call_data = _breeze.get_option_chain_quotes(
                stock_code=symbol, exchange_code="NFO", product_type="options",
                right="Call", expiry_date=api_expiry_date
            )
            call_data = self.handle_api_error(call_data)

            status_text.text("Fetching put options...")
            progress_bar.progress(75)

            put_data = _breeze.get_option_chain_quotes(
                stock_code=symbol, exchange_code="NFO", product_type="options",
                right="Put", expiry_date=api_expiry_date
            )
            put_data = self.handle_api_error(put_data)

            status_text.text("Complete!")
            progress_bar.progress(100)

            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()

            st.session_state.last_fetch_time = datetime.now()
            return call_data + put_data, spot_price

        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            raise e

    def get_options_chain_data_with_retry(self, _breeze: BreezeConnect, symbol: str,
                                        api_expiry_date: str, max_retries: int = 3) -> Tuple[Optional[List], Optional[float]]:
        """Fetch options chain data with retry logic"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching options chain for {symbol}, attempt {attempt + 1}")
                return self.fetch_data_with_progress(_breeze, symbol, api_expiry_date)
            except BreezeAPIError as e:
                st.error(str(e))
                return None, None
            except Exception as e:
                logger.error(f"Error fetching data (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    st.error(f"Failed to fetch options chain after {max_retries} attempts: {e}")
                    return None, None
                time.sleep(1 * (2 ** attempt))
