import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from visualization import charts
from visualization.tables import display_options_chain_table

def create_analysis_tabs(full_chain_df, spot_price, metrics, atm_strike, selected_expiry, 
                        symbol, sidebar_config):
    """Create and populate analysis tabs"""
    tabs = ["📊 OI Analysis", "🔥 Heatmap", "😊 IV Analysis", "📈 Volume", 
            "🧮 Greeks", "📉 Strategy", "⏳ History"]
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(tabs)
    
    with tab1:
        st.plotly_chart(charts.create_oi_chart(full_chain_df, atm_strike, spot_price, 
                                              metrics['max_pain']), use_container_width=True)
        
        # OI Change Analysis
        oi_change_df = full_chain_df[['Strike', 'Call Chng OI', 'Put Chng OI']].copy()
        oi_change_df = oi_change_df[(oi_change_df['Call Chng OI'] != 0) | 
                                    (oi_change_df['Put Chng OI'] != 0)]
        
        if not oi_change_df.empty:
            fig_oi_change = go.Figure()
            fig_oi_change.add_trace(go.Bar(x=oi_change_df['Strike'], 
                                          y=oi_change_df['Call Chng OI'], 
                                          name='Call OI Change', marker_color='red'))
            fig_oi_change.add_trace(go.Bar(x=oi_change_df['Strike'], 
                                          y=oi_change_df['Put Chng OI'], 
                                          name='Put OI Change', marker_color='green'))
            fig_oi_change.update_layout(title='Open Interest Changes', 
                                       barmode='group', height=300)
            st.plotly_chart(fig_oi_change, use_container_width=True)
    
    with tab2:
        st.plotly_chart(charts.create_heatmap(full_chain_df), use_container_width=True)
    
    with tab3:
        if sidebar_config['show_iv_smile'] and 'Call IV' in full_chain_df.columns:
            iv_chart = charts.create_iv_smile_chart(full_chain_df, spot_price)
            if iv_chart:
                st.plotly_chart(iv_chart, use_container_width=True)
                
                # IV Statistics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Avg Call IV", f"{full_chain_df['Call IV'].mean():.1f}%")
                    st.metric("ATM Call IV", 
                             f"{full_chain_df.loc[full_chain_df['Strike'] == atm_strike, 'Call IV'].values[0]:.1f}%")
                with col2:
                    st.metric("Avg Put IV", f"{full_chain_df['Put IV'].mean():.1f}%")
                    st.metric("ATM Put IV", 
                             f"{full_chain_df.loc[full_chain_df['Strike'] == atm_strike, 'Put IV'].values[0]:.1f}%")
            else:
                st.info("IV Smile chart not available")
    
    with tab4:
        if sidebar_config['show_volume']:
            st.plotly_chart(charts.create_volume_profile(full_chain_df), use_container_width=True)
            
            # Volume Statistics
            total_call_vol = full_chain_df['Call Volume'].sum()
            total_put_vol = full_chain_df['Put Volume'].sum()
            vol_ratio = total_put_vol / total_call_vol if total_call_vol > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Call Volume", f"{total_call_vol:,.0f}")
            with col2:
                st.metric("Total Put Volume", f"{total_put_vol:,.0f}")
            with col3:
                st.metric("Put/Call Volume Ratio", f"{vol_ratio:.2f}")
    
    with tab5:
        if sidebar_config['show_greeks'] and 'call_delta' in full_chain_df.columns:
            # Greeks visualization options
            greek_col1, greek_col2 = st.columns(2)
            with greek_col1:
                selected_greek = st.selectbox("Select Greek", 
                                            ["delta", "gamma", "vega", "theta", "rho"])
            with greek_col2:
                greek_option_type = st.radio("Option Type", ["Call", "Put"], horizontal=True)
            
            # Display Greeks table
            greeks_cols = ['Strike', 'call_delta', 'call_gamma', 'call_vega', 
                          'call_theta', 'call_rho', 'put_delta', 'put_gamma', 
                          'put_vega', 'put_theta', 'put_rho']
            available_cols = [col for col in greeks_cols if col in full_chain_df.columns]
            greeks_df = full_chain_df[available_cols].copy()
            
            # Rename columns for display
            display_names = {
                'call_delta': 'Call Δ', 'call_gamma': 'Call Γ', 'call_vega': 'Call V', 
                'call_theta': 'Call Θ', 'call_rho': 'Call ρ',
                'put_delta': 'Put Δ', 'put_gamma': 'Put Γ', 'put_vega': 'Put V', 
                'put_theta': 'Put Θ', 'put_rho': 'Put ρ'
            }
            greeks_df.rename(columns=display_names, inplace=True)
            
            # Filter for near ATM strikes
            atm_idx = (greeks_df['Strike'] - spot_price).abs().idxmin()
            start_idx = max(0, atm_idx - 10)
            end_idx = min(len(greeks_df), atm_idx + 11)
            
            # Style the dataframe
            styled_greeks = greeks_df.iloc[start_idx:end_idx].style.format({
                'Strike': '{:.0f}',
                **{col: '{:.4f}' for col in greeks_df.columns if col != 'Strike'}
            }).background_gradient(subset=[col for col in greeks_df.columns if 'Δ' in col], 
                                 cmap='RdYlGn')
            
            st.dataframe(styled_greeks, use_container_width=True)
            
            # Greeks visualization
            greek_surface = charts.create_greeks_surface(full_chain_df, selected_greek, 
                                                        greek_option_type)
            if greek_surface:
                st.plotly_chart(greek_surface, use_container_width=True)
    
    with tab6:
        if sidebar_config['show_strategy']:
            st.subheader("Strategy Analysis")
            
            # Strategy selector
            strategy = st.selectbox("Select Strategy", 
                                  ["Long Straddle", "Short Straddle", "Long Strangle", 
                                   "Short Strangle", "Bull Call Spread", "Bear Put Spread"])
            
            # Display strategy payoff
            payoff_chart = charts.create_strategy_payoff(full_chain_df, spot_price)
            st.plotly_chart(payoff_chart, use_container_width=True)
            
            # Strategy metrics
            atm_idx = (full_chain_df['Strike'] - spot_price).abs().idxmin()
            call_premium = full_chain_df.loc[atm_idx, 'Call LTP']
            put_premium = full_chain_df.loc[atm_idx, 'Put LTP']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Premium", f"₹{call_premium + put_premium:.2f}")
            with col2:
                upper_be = atm_strike + call_premium + put_premium
                st.metric("Upper Breakeven", f"₹{upper_be:.2f}")
            with col3:
                lower_be = atm_strike - call_premium - put_premium
                st.metric("Lower Breakeven", f"₹{lower_be:.2f}")
    
    with tab7:
        if 'historical_data' in st.session_state and not st.session_state.historical_data.empty:
            hist_df = st.session_state.historical_data
            
            # Sentiment & PCR Trend
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist_df['timestamp'], y=hist_df['sentiment'], 
                                   mode='lines+markers', name='Sentiment', yaxis='y'))
            fig.add_trace(go.Scatter(x=hist_df['timestamp'], y=hist_df['pcr'], 
                                   mode='lines+markers', name='PCR', yaxis='y2'))
            
            fig.update_layout(
                title='Historical Sentiment & PCR',
                xaxis_title='Time',
                yaxis=dict(title='Sentiment', side='left'),
                yaxis2=dict(title='PCR', side='right', overlaying='y'),
                hovermode='x unified',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Max Pain Trend
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=hist_df['timestamp'], y=hist_df['max_pain'], 
                                    mode='lines+markers', name='Max Pain'))
            fig2.update_layout(
                title='Max Pain Movement',
                xaxis_title='Time',
                yaxis_title='Max Pain',
                height=300
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Historical data will be tracked during this session.")
