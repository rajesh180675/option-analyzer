import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Optional

def create_oi_chart(chain_df: pd.DataFrame, atm_strike: float, spot_price: float, 
                   max_pain: Optional[float] = None) -> go.Figure:
    """Create Open Interest distribution chart"""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=chain_df['Strike'], 
        y=chain_df['Call OI'], 
        name='Call OI', 
        marker_color='rgba(239, 83, 80, 0.7)',
        hovertemplate='Strike: %{x}<br>Call OI: %{y:,.0f}<extra></extra>'
    ))
    
    fig.add_trace(go.Bar(
        x=chain_df['Strike'], 
        y=chain_df['Put OI'], 
        name='Put OI', 
        marker_color='rgba(46, 125, 50, 0.7)',
        hovertemplate='Strike: %{x}<br>Put OI: %{y:,.0f}<extra></extra>'
    ))
    
    # Add reference lines
    fig.add_vline(x=spot_price, line_width=2, line_dash="solid", line_color="blue", 
                  annotation_text="Spot", annotation_position="top left")
    fig.add_vline(x=atm_strike, line_width=2, line_dash="dash", line_color="black", 
                  annotation_text="ATM", annotation_position="top right")
    if max_pain:
        fig.add_vline(x=max_pain, line_width=2, line_dash="dot", line_color="purple", 
                      annotation_text="Max Pain")
    
    fig.update_layout(
        title_text='Open Interest Distribution', 
        xaxis_title='Strike Price', 
        yaxis_title='Open Interest', 
        barmode='group', 
        height=400, 
        hovermode='x unified',
        showlegend=True,
        legend=dict(x=0.7, y=0.95)
    )
    
    return fig

def create_heatmap(df: pd.DataFrame) -> go.Figure:
    """Create premium heatmap"""
    heat_df = df.set_index('Strike')[['Call LTP', 'Put LTP']].sort_index(ascending=False)
    
    fig = go.Figure(data=go.Heatmap(
        z=heat_df.values,
        x=heat_df.columns,
        y=heat_df.index,
        colorscale="Viridis",
        hovertemplate='Strike: %{y}<br>Type: %{x}<br>Premium: %{z:,.2f}<extra></extra>',
        colorbar=dict(title="Premium")
    ))
    
    fig.update_layout(
        title_text='Premium Heatmap', 
        yaxis_title='Strike Price', 
        height=500,
        xaxis=dict(side='top')
    )
    
    return fig

def create_iv_smile_chart(chain_df: pd.DataFrame, spot_price: float) -> Optional[go.Figure]:
    """Create IV smile chart"""
    iv_data = []
    for _, row in chain_df.iterrows():
        if row['Call IV'] > 0:
            iv_data.append({'Strike': row['Strike'], 'IV': row['Call IV'], 'Type': 'Call'})
        if row['Put IV'] > 0:
            iv_data.append({'Strike': row['Strike'], 'IV': row['Put IV'], 'Type': 'Put'})
    
    if not iv_data:
        return None
    
    iv_df = pd.DataFrame(iv_data)
    
    fig = go.Figure()
    for option_type in ['Call', 'Put']:
        data = iv_df[iv_df['Type'] == option_type]
        if not data.empty:
            fig.add_trace(go.Scatter(
                x=data['Strike'], 
                y=data['IV'],
                mode='lines+markers',
                name=f'{option_type} IV',
                line=dict(width=2),
                hovertemplate='Strike: %{x}<br>IV: %{y:.1f}%<extra></extra>'
            ))
    
    # Add spot price line
    fig.add_vline(x=spot_price, line_width=1, line_dash="dash", line_color="gray", 
                  annotation_text="Spot")
    
    fig.update_layout(
        title='Implied Volatility Smile',
        xaxis_title='Strike Price',
        yaxis_title='Implied Volatility (%)',
        height=400,
        hovermode='x unified',
        showlegend=True
    )
    
    return fig

def create_volume_profile(chain_df: pd.DataFrame) -> go.Figure:
    """Create volume profile chart"""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=chain_df['Strike'],
        y=chain_df['Call Volume'],
        name='Call Volume',
        marker_color='rgba(239, 83, 80, 0.7)',
        hovertemplate='Strike: %{x}<br>Call Volume: %{y:,.0f}<extra></extra>'
    ))
    
    fig.add_trace(go.Bar(
        x=chain_df['Strike'],
        y=chain_df['Put Volume'],
        name='Put Volume',
        marker_color='rgba(46, 125, 50, 0.7)',
        hovertemplate='Strike: %{x}<br>Put Volume: %{y:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Volume Profile',
        xaxis_title='Strike Price',
        yaxis_title='Volume',
        barmode='group',
        height=400,
        hovermode='x unified',
        showlegend=True
    )
    
    return fig

def display_sentiment_gauge(sentiment_score: float) -> go.Figure:
    """Create sentiment gauge chart"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=sentiment_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Market Sentiment", 'font': {'size': 24}},
        delta={'reference': 0, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
        gauge={
            'axis': {'range': [-100, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [-100, -50], 'color': "darkred"},
                {'range': [-50, -20], 'color': "lightcoral"},
                {'range': [-20, 20], 'color': "lightgray"},
                {'range': [20, 50], 'color': "lightgreen"},
                {'range': [50, 100], 'color': "darkgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 0
            }
        }
    ))
    
    fig.update_layout(height=300)
    return fig

def create_greeks_surface(chain_df: pd.DataFrame, greek: str, option_type: str) -> go.Figure:
    """Create 3D surface plot for Greeks"""
    greek_col = f"{option_type.lower()}_{greek}"
    if greek_col not in chain_df.columns:
        return None
    
    # Create meshgrid for surface plot
    strikes = chain_df['Strike'].values
    greek_values = chain_df[greek_col].values
    
    fig = go.Figure(data=[go.Scatter3d(
        x=strikes,
        y=[1] * len(strikes),  # Single expiry
        z=greek_values,
        mode='markers+lines',
        marker=dict(size=5, color=greek_values, colorscale='Viridis'),
        line=dict(color='darkblue', width=2),
        name=f'{option_type} {greek.capitalize()}'
    )])
    
    fig.update_layout(
        title=f'{option_type} {greek.capitalize()} Profile',
        scene=dict(
            xaxis_title='Strike Price',
            yaxis_title='Time',
            zaxis_title=greek.capitalize()
        ),
        height=500
    )
    
    return fig

def create_strategy_payoff(chain_df: pd.DataFrame, spot_price: float) -> go.Figure:
    """Create strategy payoff diagram"""
    strikes = chain_df['Strike'].values
    
    # Example: Long Straddle at ATM
    atm_idx = (chain_df['Strike'] - spot_price).abs().idxmin()
    atm_strike = chain_df.loc[atm_idx, 'Strike']
    call_premium = chain_df.loc[atm_idx, 'Call LTP']
    put_premium = chain_df.loc[atm_idx, 'Put LTP']
    
    # Calculate payoff
    spot_range = np.linspace(strikes.min(), strikes.max(), 100)
    straddle_payoff = np.maximum(spot_range - atm_strike, 0) + np.maximum(atm_strike - spot_range, 0) - (call_premium + put_premium)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=spot_range,
        y=straddle_payoff,
        mode='lines',
        name='Long Straddle',
        line=dict(width=3)
    ))
    
    # Add breakeven lines
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.add_vline(x=spot_price, line_dash="dash", line_color="blue", annotation_text="Current Spot")
    
    fig.update_layout(
        title=f'Long Straddle Payoff (Strike: {atm_strike})',
        xaxis_title='Spot Price at Expiry',
        yaxis_title='Profit/Loss',
        height=400,
        hovermode='x unified'
    )
    
    return fig
