import streamlit as st
import pandas as pd
from datetime import datetime
from utils.visualization import plot_bankroll_history, plot_win_probability_distribution, plot_roi_by_sport
from utils.helpers import format_currency
from database.db_manager import DatabaseManager

def show():
    """Display F1 bankroll tracking page"""
    # Initialize database manager
    db = DatabaseManager()
    
    st.markdown("""
    <div class="main-header">
        <h1>F1 Bankroll Tracking</h1>
        <p>Track and analyze your Formula 1 betting performance</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get F1 betting history
    bet_history = db.get_bets_by_sport('f1')
    
    if not bet_history:
        st.info("No F1 bets recorded yet. Use the F1 Kelly Calculator to start betting.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(bet_history)
    
    # Calculate key metrics
    total_bets = len(df)
    winning_bets = len(df[df['result'] == 'win'])
    win_rate = winning_bets / total_bets if total_bets > 0 else 0
    total_profit = df['profit_loss'].sum()
    roi = (total_profit / df['stake'].sum()) * 100 if df['stake'].sum() > 0 else 0
    
    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total F1 Bets",
            str(total_bets),
            help="Total number of F1 bets placed"
        )
    
    with col2:
        st.metric(
            "Win Rate",
            f"{win_rate:.1%}",
            help="Percentage of winning bets"
        )
    
    with col3:
        st.metric(
            "Total Profit",
            format_currency(total_profit),
            delta=format_currency(total_profit),
            help="Total profit/loss from F1 betting"
        )
    
    with col4:
        st.metric(
            "Return on Investment",
            f"{roi:.1f}%",
            delta=f"{roi:.1f}%",
            help="ROI percentage from F1 betting"
        )
    
    # Bankroll history chart
    st.subheader("F1 Bankroll History")
    bankroll_fig = plot_bankroll_history(bet_history)
    st.plotly_chart(bankroll_fig, use_container_width=True)
    
    # Market type analysis
    st.subheader("Performance by Market Type")
    
    market_analysis = df.groupby('market_type').agg({
        'profit_loss': ['sum', 'count'],
        'stake': 'sum'
    }).round(2)
    
    market_analysis.columns = ['Total P/L', 'Number of Bets', 'Total Stake']
    market_analysis['ROI %'] = (market_analysis['Total P/L'] / market_analysis['Total Stake'] * 100).round(2)
    market_analysis = market_analysis.reset_index()
    
    # Format currency columns
    market_analysis['Total P/L'] = market_analysis['Total P/L'].apply(format_currency)
    market_analysis['Total Stake'] = market_analysis['Total Stake'].apply(format_currency)
    
    st.dataframe(
        market_analysis,
        hide_index=True,
        column_config={
            "market_type": "Market Type",
            "Total P/L": "Total Profit/Loss",
            "Number of Bets": "Number of Bets",
            "Total Stake": "Total Stake",
            "ROI %": st.column_config.NumberColumn(
                "ROI %",
                help="Return on Investment percentage",
                format="%.2f%%"
            )
        }
    )
    
    # Distribution analysis
    st.subheader("Probability and Edge Distribution")
    
    # Extract probabilities and edges
    probabilities = df['win_probability'].tolist()
    edges = df['edge'].tolist()
    
    distribution_fig = plot_win_probability_distribution(probabilities, edges)
    st.plotly_chart(distribution_fig, use_container_width=True)
    
    # Monthly analysis
    st.subheader("Monthly Performance")
    
    df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
    monthly_analysis = df.groupby('month').agg({
        'profit_loss': 'sum',
        'stake': 'sum',
        'result': 'count'
    }).reset_index()
    
    monthly_analysis['ROI %'] = (monthly_analysis['profit_loss'] / monthly_analysis['stake'] * 100).round(2)
    monthly_analysis['month'] = monthly_analysis['month'].astype(str)
    
    # Format currency columns
    monthly_analysis['profit_loss'] = monthly_analysis['profit_loss'].apply(format_currency)
    monthly_analysis['stake'] = monthly_analysis['stake'].apply(format_currency)
    
    st.dataframe(
        monthly_analysis,
        hide_index=True,
        column_config={
            "month": "Month",
            "profit_loss": "Profit/Loss",
            "stake": "Total Stake",
            "result": "Number of Bets",
            "ROI %": st.column_config.NumberColumn(
                "ROI %",
                help="Return on Investment percentage",
                format="%.2f%%"
            )
        }
    )
    
    # Additional insights
    display_f1_insights(df)

def display_f1_insights(df):
    """Display additional F1 betting insights"""
    
    st.subheader("F1 Betting Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Analyze most profitable circuits
        circuit_analysis = df.groupby('team1').agg({
            'profit_loss': 'sum',
            'result': 'count'
        }).reset_index()
        
        circuit_analysis = circuit_analysis.sort_values('profit_loss', ascending=False)
        circuit_analysis = circuit_analysis.head(5)
        
        st.write("Most Profitable Circuits:")
        st.dataframe(
            circuit_analysis,
            hide_index=True,
            column_config={
                "team1": "Circuit",
                "profit_loss": st.column_config.NumberColumn(
                    "Profit/Loss",
                    format="$%.2f"
                ),
                "result": "Number of Bets"
            }
        )
    
    with col2:
        # Analyze bet type performance
        bet_type_analysis = df.groupby('bet_type').agg({
            'profit_loss': 'sum',
            'result': 'count'
        }).reset_index()
        
        bet_type_analysis = bet_type_analysis.sort_values('profit_loss', ascending=False)
        bet_type_analysis = bet_type_analysis.head(5)
        
        st.write("Most Profitable Bet Types:")
        st.dataframe(
            bet_type_analysis,
            hide_index=True,
            column_config={
                "bet_type": "Bet Type",
                "profit_loss": st.column_config.NumberColumn(
                    "Profit/Loss",
                    format="$%.2f"
                ),
                "result": "Number of Bets"
            }
        )
    
    # Kelly fraction analysis
    st.write("Kelly Fraction Analysis:")
    kelly_analysis = df.groupby('kelly_fraction').agg({
        'profit_loss': ['sum', 'mean'],
        'result': 'count',
        'edge': 'mean'
    }).round(2)
    
    kelly_analysis.columns = ['Total P/L', 'Average P/L', 'Number of Bets', 'Average Edge']
    kelly_analysis = kelly_analysis.reset_index()
    
    st.dataframe(
        kelly_analysis,
        hide_index=True,
        column_config={
            "kelly_fraction": "Kelly Fraction",
            "Total P/L": st.column_config.NumberColumn(
                "Total P/L",
                format="$%.2f"
            ),
            "Average P/L": st.column_config.NumberColumn(
                "Average P/L",
                format="$%.2f"
            ),
            "Number of Bets": "Number of Bets",
            "Average Edge": st.column_config.NumberColumn(
                "Average Edge",
                format="%.2f%%"
            )
        }
    )
    
    # Risk level analysis
    st.write("Risk Level Analysis:")
    risk_analysis = df.groupby('risk_assessment').agg({
        'profit_loss': ['sum', 'mean'],
        'result': 'count'
    }).round(2)
    
    risk_analysis.columns = ['Total P/L', 'Average P/L', 'Number of Bets']
    risk_analysis = risk_analysis.reset_index()
    
    st.dataframe(
        risk_analysis,
        hide_index=True,
        column_config={
            "risk_assessment": "Risk Level",
            "Total P/L": st.column_config.NumberColumn(
                "Total P/L",
                format="$%.2f"
            ),
            "Average P/L": st.column_config.NumberColumn(
                "Average P/L",
                format="$%.2f"
            ),
            "Number of Bets": "Number of Bets"
        }
    )