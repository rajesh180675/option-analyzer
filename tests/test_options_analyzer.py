import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from calculations.greeks import calculate_iv, calculate_greeks_vectorized
from data.processor import DataProcessor

def test_calculate_iv():
    """Test IV calculation"""
    iv = calculate_iv('Call', 100, 100, 5, 0.25)
    assert 0 < iv < 2, "IV should be between 0 and 2"

def test_calculate_greeks_vectorized():
    """Test vectorized Greeks calculation"""
    iv_array = np.array([0.2, 0.25, 0.3])
    strikes = np.array([95, 100, 105])
    greeks = calculate_greeks_vectorized(iv_array, 'Call', 100, strikes, 0.25)
    
    assert len(greeks) == len(strikes), "Greeks output should match strikes length"
    assert all(-1 <= greeks['delta'].values) and all(greeks['delta'].values <= 1), "Delta should be between -1 and 1"

def test_validate_option_data():
    """Test option data validation"""
    # Valid data
    valid_df = pd.DataFrame({
        'strike_price': [100, 105, 110],
        'ltp': [5, 3, 1],
        'oi': [1000, 2000, 1500],
        'volume': [100, 200, 150]
    })
    assert DataProcessor.validate_option_data(valid_df) == True
    
    # Invalid data - missing columns
    invalid_df = pd.DataFrame({
        'strike_price': [100, 105, 110]
    })
    assert DataProcessor.validate_option_data(invalid_df) == False

if __name__ == "__main__":
    test_calculate_iv()
    test_calculate_greeks_vectorized()
    test_validate_option_data()
    print("All tests passed!")
