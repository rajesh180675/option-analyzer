import streamlit as st
import pandas as pd
from app_config import config

def display_options_chain_table(full_chain_df: pd.DataFrame, spot_price: float, symbol: str):
    """Display the options chain table with filters"""
    st.subheader("📋 Options Chain Data")
    
    # Advanced Filters
    with st.expander("🔍 Advanced Filters", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            strike_range = st.slider("Strike Range", 
                                   int(full_chain_df['Strike'].min()), 
                                   int(full_chain_df['Strike'].max()),
                                   (int(spot_price - 1000), int(spot_price + 1000)))
        with col2:
            oi_filter = st.number_input("Min OI Filter", value=0, step=1000)
        with col3:
            volume_filter = st.number_input("Min Volume Filter", value=0, step=100)
        with col4:
            moneyness = st.selectbox("Moneyness", ["All", "ITM", "ATM", "OTM"])
    
    # Apply filters
    filtered_df = full_chain_df[
        (full_chain_df['Strike'] >= strike_range[0]) & 
        (full_chain_df['Strike'] <= strike_range[1]) &
        ((full_chain_df['Call OI'] >= oi_filter) | (full_chain_df['Put OI'] >= oi_filter)) &
        ((full_chain_df['Call Volume'] >= volume_filter) | (full_chain_df['Put Volume'] >= volume_filter))
    ].copy()
    
    # Apply moneyness filter
    if moneyness == "ITM":
        filtered_df = filtered_df[
            ((filtered_df['Strike'] < spot_price) & (filtered_df['Put LTP'] > 0)) |
            ((filtered_df['Strike'] > spot_price) & (filtered_df['Call LTP'] > 0))
        ]
    elif moneyness == "ATM":
        atm_range = config.get_strike_step(symbol) * 2
        filtered_df = filtered_df[
            (filtered_df['Strike'] >= spot_price - atm_range) & 
            (filtered_df['Strike'] <= spot_price + atm_range)
        ]
    elif moneyness == "OTM":
        filtered_df = filtered_df[
            ((filtered_df['Strike'] > spot_price) & (filtered_df['Put LTP'] > 0)) |
            ((filtered_df['Strike'] < spot_price) & (filtered_df['Call LTP'] > 0))
        ]
    
    # Display columns
    display_cols = ['Call OI', 'Call Chng OI', 'Call LTP', 'Call Volume', 'Strike', 
                  'Put LTP', 'Put Volume', 'Put Chng OI', 'Put OI']
    
    if 'Call IV' in filtered_df.columns:
        display_cols.extend(['Call IV', 'Put IV'])
    
    # Add moneyness indicator
    filtered_df['Moneyness'] = filtered_df.apply(
        lambda row: 'ITM' if (row['Strike'] < spot_price and row['Put LTP'] > 0) or 
                           (row['Strike'] > spot_price and row['Call LTP'] > 0)
        else 'OTM' if (row['Strike'] > spot_price and row['Put LTP'] > 0) or 
                     (row['Strike'] < spot_price and row['Call LTP'] > 0)
        else 'ATM', axis=1
    )
    
    # Style the dataframe
    def highlight_moneyness(row):
        if row['Moneyness'] == 'ITM':
            return ['background-color: #e8f5e9'] * len(row)
        elif row['Moneyness'] == 'ATM':
            return ['background-color: #fff3e0'] * len(row)
        else:
            return [''] * len(row)
    
    styled_df = filtered_df[display_cols + ['Moneyness']].style.format({
        'Call OI': '{:,.0f}',
        'Call Chng OI': '{:+,.0f}',
        'Call LTP': '{:,.2f}',
        'Call Volume': '{:,.0f}',
        'Strike': '{:,.0f}',
        'Put LTP': '{:,.2f}',
        'Put Chng OI': '{:+,.0f}',
        'Put OI': '{:,.0f}',
        'Put Volume': '{:,.0f}',
        'Call IV': '{:.1f}%',
        'Put IV': '{:.1f}%'
    }).background_gradient(subset=['Call OI', 'Put OI'], cmap='YlOrRd'
    ).apply(highlight_moneyness, axis=1)
    
    # Display the table
    st.dataframe(styled_df, use_container_width=True, height=600)
    
    # Summary statistics
    with st.expander("📊 Summary Statistics"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Call Options Summary:**")
            st.write(f"- Total OI: {filtered_df['Call OI'].sum():,.0f}")
            st.write(f"- Total Volume: {filtered_df['Call Volume'].sum():,.0f}")
            st.write(f"- Avg IV: {filtered_df['Call IV'].mean():.1f}%" if 'Call IV' in filtered_df.columns else "")
            st.write(f"- Max OI Strike: {filtered_df.loc[filtered_df['Call OI'].idxmax(), 'Strike']:,.0f}")
        
        with col2:
            st.write("**Put Options Summary:**")
            st.write(f"- Total OI: {filtered_df['Put OI'].sum():,.0f}")
            st.write(f"- Total Volume: {filtered_df['Put Volume'].sum():,.0f}")
            st.write(f"- Avg IV: {filtered_df['Put IV'].mean():.1f}%" if 'Put IV' in filtered_df.columns else "")
            st.write(f"- Max OI Strike: {filtered_df.loc[filtered_df['Put OI'].idxmax(), 'Strike']:,.0f}")
    
    return filtered_df
