import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict, Any
from app_config import config

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


def create_strategy_payoff(chain_df: pd.DataFrame, spot_price: float, strategy_name: str, atm_strike: float, symbol: str) -> Tuple[Optional[go.Figure], Dict[str, Any]]:
    """Create strategy payoff diagram and calculate metrics."""
    try:
        df = chain_df.set_index('Strike')
        atm_idx = df.index.get_loc(atm_strike)
        strike_step = config.get_strike_step(symbol)

        spot_range = np.linspace(df.index.min(), df.index.max(), 200)
        payoff = np.zeros_like(spot_range)
        metrics = {}
        legs = []

        # --- Strategy Logic ---

        if strategy_name in ["Long Straddle", "Short Straddle"]:
            k = atm_strike
            c = df.loc[k, 'Call LTP']
            p = df.loc[k, 'Put LTP']
            
            call_payoff = np.maximum(spot_range - k, 0) - c
            put_payoff = np.maximum(k - spot_range, 0) - p
            
            if strategy_name == "Long Straddle":
                payoff = call_payoff + put_payoff
                net_premium = -(c + p)
                metrics = {
                    "Max Profit": "Unlimited",
                    "Max Loss": f"₹{abs(net_premium):,.2f}",
                    "Breakevens": f"₹{k - abs(net_premium):,.2f} & ₹{k + abs(net_premium):,.2f}"
                }
                legs.append(f"Buy Call @ {k}")
                legs.append(f"Buy Put @ {k}")
            else: # Short Straddle
                payoff = -call_payoff - put_payoff
                net_premium = c + p
                metrics = {
                    "Max Profit": f"₹{net_premium:,.2f}",
                    "Max Loss": "Unlimited",
                    "Breakevens": f"₹{k - net_premium:,.2f} & ₹{k + net_premium:,.2f}"
                }
                legs.append(f"Sell Call @ {k}")
                legs.append(f"Sell Put @ {k}")

        elif strategy_name in ["Long Strangle", "Short Strangle"]:
            k_call = df.index[min(atm_idx + 1, len(df) - 1)]
            k_put = df.index[max(atm_idx - 1, 0)]
            c = df.loc[k_call, 'Call LTP']
            p = df.loc[k_put, 'Put LTP']

            call_payoff = np.maximum(spot_range - k_call, 0) - c
            put_payoff = np.maximum(k_put - spot_range, 0) - p

            if strategy_name == "Long Strangle":
                payoff = call_payoff + put_payoff
                net_premium = -(c + p)
                metrics = {
                    "Max Profit": "Unlimited",
                    "Max Loss": f"₹{abs(net_premium):,.2f}",
                    "Breakevens": f"₹{k_put - abs(net_premium):,.2f} & ₹{k_call + abs(net_premium):,.2f}"
                }
                legs.append(f"Buy Call @ {k_call}")
                legs.append(f"Buy Put @ {k_put}")
            else: # Short Strangle
                payoff = -call_payoff - put_payoff
                net_premium = c + p
                metrics = {
                    "Max Profit": f"₹{net_premium:,.2f}",
                    "Max Loss": "Unlimited",
                    "Breakevens": f"₹{k_put - net_premium:,.2f} & ₹{k_call + net_premium:,.2f}"
                }
                legs.append(f"Sell Call @ {k_call}")
                legs.append(f"Sell Put @ {k_put}")

        elif strategy_name == "Bull Call Spread":
            k_long = atm_strike
            k_short = atm_strike + strike_step
            c_long = df.loc[k_long, 'Call LTP']
            c_short = df.loc[k_short, 'Call LTP']
            net_premium = -(c_long - c_short)

            long_call_payoff = np.maximum(spot_range - k_long, 0) - c_long
            short_call_payoff = -(np.maximum(spot_range - k_short, 0) - c_short)
            payoff = long_call_payoff + short_call_payoff

            metrics = {
                "Max Profit": f"₹{(k_short - k_long) - abs(net_premium):,.2f}",
                "Max Loss": f"₹{abs(net_premium):,.2f}",
                "Breakevens": f"₹{k_long + abs(net_premium):,.2f}"
            }
            legs.append(f"Buy Call @ {k_long}")
            legs.append(f"Sell Call @ {k_short}")

        elif strategy_name == "Bear Put Spread":
            k_long = atm_strike
            k_short = atm_strike - strike_step
            p_long = df.loc[k_long, 'Put LTP']
            p_short = df.loc[k_short, 'Put LTP']
            net_premium = -(p_long - p_short)

            long_put_payoff = np.maximum(k_long - spot_range, 0) - p_long
            short_put_payoff = -(np.maximum(k_short - spot_range, 0) - p_short)
            payoff = long_put_payoff + short_put_payoff

            metrics = {
                "Max Profit": f"₹{(k_long - k_short) - abs(net_premium):,.2f}",
                "Max Loss": f"₹{abs(net_premium):,.2f}",
                "Breakevens": f"₹{k_long - abs(net_premium):,.2f}"
            }
            legs.append(f"Buy Put @ {k_long}")
            legs.append(f"Sell Put @ {k_short}")

        metrics["Net Premium"] = f"₹{net_premium:,.2f} {'(Debit)' if net_premium < 0 else '(Credit)'}"
        metrics["Legs"] = " | ".join(legs)

        # --- Plotting ---
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=spot_range,
            y=payoff,
            mode='lines',
            name=strategy_name,
            line=dict(width=3)
        ))
        
        # Highlight profit/loss areas
        fig.add_trace(go.Scatter(
            x=spot_range, y=payoff,
            fill='tozeroy',
            mode='none',
            fillcolor='rgba(255, 82, 82, 0.2)', # Loss
            showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=spot_range, y=np.maximum(payoff, 0),
            fill='tozeroy',
            mode='none',
            fillcolor='rgba(0, 176, 246, 0.2)', # Profit
            showlegend=False
        ))

        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        fig.add_vline(x=spot_price, line_dash="solid", line_color="blue", annotation_text="Current Spot")

        fig.update_layout(
            title=f'{strategy_name} Payoff Diagram',
            xaxis_title='Spot Price at Expiry',
            yaxis_title='Profit / Loss',
            height=400,
            hovermode='x unified'
        )

        return fig, metrics

    except (KeyError, IndexError) as e:
        # This can happen if strikes for the strategy don't exist in the data
        print(f"Error creating strategy chart for {strategy_name}: {e}")
        return None, {}
