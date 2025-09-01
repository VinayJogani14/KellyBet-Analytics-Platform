import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

def plot_bankroll_simulation(simulations):
    """Create an interactive plot of bankroll paths for multiple simulations"""
    
    # Extract data for plotting
    all_paths = []
    for sim in simulations:
        path = pd.DataFrame({
            'Bet Number': range(len(sim['bankroll_history'])),
            'Bankroll': sim['bankroll_history'],
            'Simulation': f"Sim {sim['sim_id']}"
        })
        all_paths.append(path)
    
    plot_data = pd.concat(all_paths, ignore_index=True)
    
    # Create plot
    fig = px.line(
        plot_data,
        x='Bet Number',
        y='Bankroll',
        color='Simulation',
        line_shape='linear',
        title='Bankroll Evolution Over Multiple Simulations'
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title="Number of Bets",
        yaxis_title="Bankroll ($)",
        hovermode='x unified',
        showlegend=False,  # Hide legend if too many simulations
        template='plotly_white'
    )
    
    # Show plot
    st.plotly_chart(fig, use_container_width=True)

def plot_bankroll_history(bet_history):
    """Plot historical bankroll performance"""
    
    # Convert bet history to DataFrame
    df = pd.DataFrame(bet_history)
    df['date'] = pd.to_datetime(df['date'])
    
    # Create figure
    fig = go.Figure()
    
    # Add bankroll line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['bankroll_after'],
        mode='lines+markers',
        name='Bankroll',
        hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br>" +
                      "<b>Bankroll:</b> $%{y:,.2f}<br>" +
                      "<extra></extra>"
    ))
    
    # Add win/loss markers
    wins = df[df['result'] == 'win']
    losses = df[df['result'] == 'loss']
    
    fig.add_trace(go.Scatter(
        x=wins['date'],
        y=wins['bankroll_after'],
        mode='markers',
        marker=dict(
            color='green',
            size=10,
            symbol='triangle-up'
        ),
        name='Win',
        showlegend=True,
        hovertemplate="<b>Win</b><br>" +
                      "<b>Date:</b> %{x|%Y-%m-%d}<br>" +
                      "<b>Profit:</b> $%{text:,.2f}<br>" +
                      "<extra></extra>",
        text=wins['profit_loss']
    ))
    
    fig.add_trace(go.Scatter(
        x=losses['date'],
        y=losses['bankroll_after'],
        mode='markers',
        marker=dict(
            color='red',
            size=10,
            symbol='triangle-down'
        ),
        name='Loss',
        showlegend=True,
        hovertemplate="<b>Loss</b><br>" +
                      "<b>Date:</b> %{x|%Y-%m-%d}<br>" +
                      "<b>Loss:</b> $%{text:,.2f}<br>" +
                      "<extra></extra>",
        text=losses['profit_loss']
    ))
    
    # Update layout
    fig.update_layout(
        title='Bankroll History',
        xaxis_title='Date',
        yaxis_title='Bankroll ($)',
        hovermode='x unified',
        template='plotly_white',
        height=500
    )
    
    return fig

def plot_win_probability_distribution(probabilities, edges):
    """Plot distribution of win probabilities and edges"""
    
    fig = go.Figure()
    
    # Add probability histogram
    fig.add_trace(go.Histogram(
        x=probabilities,
        name='Win Probability',
        opacity=0.75,
        marker_color='blue',
        nbinsx=20
    ))
    
    # Add edge histogram
    fig.add_trace(go.Histogram(
        x=edges,
        name='Edge %',
        opacity=0.75,
        marker_color='green',
        nbinsx=20
    ))
    
    # Update layout
    fig.update_layout(
        title='Distribution of Win Probabilities and Edges',
        xaxis_title='Value',
        yaxis_title='Count',
        barmode='overlay',
        template='plotly_white'
    )
    
    return fig

def plot_roi_by_sport(bet_history):
    """Plot ROI breakdown by sport"""
    
    # Calculate ROI by sport
    df = pd.DataFrame(bet_history)
    
    roi_by_sport = df.groupby('sport').agg({
        'profit_loss': 'sum',
        'stake': 'sum'
    }).reset_index()
    
    roi_by_sport['roi'] = (roi_by_sport['profit_loss'] / roi_by_sport['stake']) * 100
    
    # Create bar chart
    fig = go.Figure(data=[
        go.Bar(
            x=roi_by_sport['sport'],
            y=roi_by_sport['roi'],
            text=roi_by_sport['roi'].apply(lambda x: f"{x:.1f}%"),
            textposition='auto',
            marker_color=['blue' if x >= 0 else 'red' for x in roi_by_sport['roi']]
        )
    ])
    
    # Update layout
    fig.update_layout(
        title='Return on Investment by Sport',
        xaxis_title='Sport',
        yaxis_title='ROI %',
        template='plotly_white',
        showlegend=False
    )
    
    return fig

def plot_odds_value_chart(american_odds, win_probability):
    """Plot odds value chart showing expected value at different probabilities"""
    
    # Generate probability range
    prob_range = np.linspace(0, 1, 100)
    
    # Calculate expected values
    from utils.helpers import american_to_decimal
    decimal_odds = american_to_decimal(american_odds)
    expected_values = [(p * decimal_odds - 1) * 100 for p in prob_range]
    
    # Create figure
    fig = go.Figure()
    
    # Add EV line
    fig.add_trace(go.Scatter(
        x=prob_range,
        y=expected_values,
        mode='lines',
        name='Expected Value',
        line=dict(color='blue')
    ))
    
    # Add marker for current probability
    fig.add_trace(go.Scatter(
        x=[win_probability],
        y=[(win_probability * decimal_odds - 1) * 100],
        mode='markers',
        name='Current Probability',
        marker=dict(
            color='red',
            size=12,
            symbol='star'
        )
    ))
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    # Update layout
    fig.update_layout(
        title=f"Expected Value vs. Win Probability (Odds: {american_odds:+d})",
        xaxis_title="Win Probability",
        yaxis_title="Expected Value (%)",
        hovermode='x unified',
        template='plotly_white'
    )
    
    # Update axes
    fig.update_xaxes(range=[0, 1], tickformat=".0%")
    fig.update_yaxes(ticksuffix="%")
    
    return fig