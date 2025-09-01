import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import sqlite3
import os
import config

def load_css():
    """Load custom CSS styles"""
    css = """
    <style>
    /* Main header styling */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        font-size: 1.2rem;
        opacity: 0.9;
    }
    
    /* Bankroll display */
    .bankroll-display {
        text-align: center;
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #e9ecef;
        margin: 1rem 0;
    }
    
    .bankroll-display h2 {
        color: #28a745;
        font-weight: 700;
        margin: 0;
    }
    
    /* Sports header */
    .sports-header {
        text-align: center;
        margin: 2rem 0 1rem 0;
    }
    
    .sports-header h2 {
        color: #333;
        font-weight: 600;
    }
    
    /* Sport selection buttons */
    .stButton > button {
        width: 100%;
        height: 120px;
        font-size: 1.2rem;
        font-weight: 600;
        border-radius: 15px;
        border: none;
        background: linear-gradient(145deg, #f0f0f0, #cacaca);
        box-shadow: 5px 5px 10px #bebebe, -5px -5px 10px #ffffff;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 7px 7px 15px #bebebe, -7px -7px 15px #ffffff;
    }
    
    /* Features section */
    .features-section {
        margin-top: 3rem;
        padding: 2rem;
        background: #f8f9fa;
        border-radius: 15px;
    }
    
    .features-section h3 {
        text-align: center;
        color: #333;
        margin-bottom: 2rem;
        font-weight: 600;
    }
    
    .features-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
    }
    
    .feature-item {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .feature-item h4 {
        color: #667eea;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    
    .feature-item p {
        color: #666;
        line-height: 1.6;
    }
    
    /* Match info cards */
    .match-info-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    .match-result {
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 5px;
        font-weight: 500;
    }
    
    .match-win { background: #d4edda; color: #155724; }
    .match-draw { background: #fff3cd; color: #856404; }
    .match-loss { background: #f8d7da; color: #721c24; }
    
    /* Kelly results styling */
    .kelly-results {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
    }
    
    .kelly-results h3 {
        color: #333;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    
    .metric-row {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem 0;
        border-bottom: 1px solid #e9ecef;
    }
    
    .metric-label {
        font-weight: 600;
        color: #495057;
    }
    
    .metric-value {
        font-weight: 700;
        color: #28a745;
    }
    
    .risk-low { color: #28a745; }
    .risk-medium { color: #ffc107; }
    .risk-high { color: #dc3545; }
    
    /* Form styling */
    .stSelectbox > div > div {
        background-color: white;
    }
    
    .stNumberInput > div > div > input {
        background-color: white;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Hide streamlit menu and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'bankroll' not in st.session_state:
        st.session_state.bankroll = config.DEFAULT_BANKROLL
    
    if 'initial_bankroll' not in st.session_state:
        st.session_state.initial_bankroll = config.DEFAULT_BANKROLL
    
    if 'bet_history' not in st.session_state:
        st.session_state.bet_history = []
    
    if 'total_bets' not in st.session_state:
        st.session_state.total_bets = 0
    
    if 'total_wins' not in st.session_state:
        st.session_state.total_wins = 0
    
    if 'total_losses' not in st.session_state:
        st.session_state.total_losses = 0

def format_currency(amount):
    """Format amount as currency"""
    return f"${amount:,.2f}"

def format_percentage(value):
    """Format value as percentage"""
    return f"{value:.2f}%"

def american_to_decimal(american_odds):
    """Convert American odds to decimal odds"""
    if american_odds > 0:
        return (american_odds / 100) + 1
    else:
        return (100 / abs(american_odds)) + 1

def decimal_to_american(decimal_odds):
    """Convert decimal odds to American odds"""
    if decimal_odds >= 2.0:
        return int((decimal_odds - 1) * 100)
    else:
        return int(-100 / (decimal_odds - 1))

def implied_probability(american_odds):
    """Calculate implied probability from American odds"""
    decimal_odds = american_to_decimal(american_odds)
    return 1 / decimal_odds

def calculate_edge(win_probability, american_odds):
    """Calculate betting edge"""
    implied_prob = implied_probability(american_odds)
    return win_probability - implied_prob

def calculate_expected_value(win_probability, american_odds, stake):
    """Calculate expected value of a bet"""
    decimal_odds = american_to_decimal(american_odds)
    win_amount = stake * (decimal_odds - 1)
    lose_amount = -stake
    
    expected_value = (win_probability * win_amount) + ((1 - win_probability) * lose_amount)
    return expected_value

def kelly_criterion(win_probability, american_odds):
    """Calculate Kelly Criterion fraction"""
    decimal_odds = american_to_decimal(american_odds)
    b = decimal_odds - 1  # Net odds received on the wager
    p = win_probability   # Probability of winning
    q = 1 - p            # Probability of losing
    
    kelly_fraction = (b * p - q) / b
    return max(0, kelly_fraction)  # Don't bet if Kelly fraction is negative

def assess_risk(stake_percentage):
    """Assess risk level based on stake percentage"""
    if stake_percentage < config.RISK_THRESHOLDS['LOW']:
        return "LOW RISK"
    elif stake_percentage < config.RISK_THRESHOLDS['MEDIUM']:
        return "MEDIUM RISK"
    else:
        return "HIGH RISK"

def update_bankroll(amount, operation='add'):
    """Update bankroll in session state"""
    if operation == 'add':
        st.session_state.bankroll += amount
    elif operation == 'subtract':
        st.session_state.bankroll -= amount
    elif operation == 'set':
        st.session_state.bankroll = amount
    
    # Ensure bankroll doesn't go below 0
    st.session_state.bankroll = max(0, st.session_state.bankroll)

def record_bet(bet_data):
    """Record a bet in session state and database"""
    bet_data['timestamp'] = datetime.now()
    bet_data['bet_id'] = len(st.session_state.bet_history) + 1
    
    st.session_state.bet_history.append(bet_data)
    st.session_state.total_bets += 1
    
    # Save to database
    try:
        from database.db_manager import DatabaseManager
        db_manager = DatabaseManager()
        db_manager.save_bet(bet_data)
    except Exception as e:
        st.error(f"Error saving bet to database: {e}")

def get_team_logo_url(team_name):
    """Get team logo URL (placeholder function)"""
    # This would typically connect to a sports data API
    # For now, return a placeholder
    return f"https://via.placeholder.com/50x50?text={team_name[:2]}"

def validate_odds_input(odds_input):
    """Validate American odds input"""
    try:
        odds = int(odds_input)
        if odds == 0:
            return False, "Odds cannot be zero"
        if odds > -100 and odds < 100 and odds != 0:
            return False, "American odds must be less than -100 or greater than +100"
        return True, odds
    except ValueError:
        return False, "Please enter a valid integer"

def calculate_roi():
    """Calculate return on investment"""
    current_bankroll = st.session_state.bankroll
    initial_bankroll = st.session_state.initial_bankroll
    
    if initial_bankroll == 0:
        return 0
    
    roi = ((current_bankroll - initial_bankroll) / initial_bankroll) * 100
    return roi

def get_profit_loss():
    """Get total profit/loss"""
    return st.session_state.bankroll - st.session_state.initial_bankroll

def display_match_info(team1_matches, team2_matches, team1_name, team2_name):
    """Display formatted match information"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**{team1_name} - Last 5 Matches:**")
        for i, match in enumerate(team1_matches, 1):
            result_class = "match-win" if match['result'] == 'W' else "match-draw" if match['result'] == 'D' else "match-loss"
            result_icon = "✅" if match['result'] == 'W' else "⚪" if match['result'] == 'D' else "❌"
            
            st.markdown(f"""
            <div class="match-result {result_class}">
                Match {i}: {result_icon} {match['result_text']} vs {match['opponent']} ({'Home' if match['home'] else 'Away'})<br>
                Score: {match['score']} - Date: {match['date']}<br>
                Scorers: {match['scorers']}
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"**{team2_name} - Last 5 Matches:**")
        for i, match in enumerate(team2_matches, 1):
            result_class = "match-win" if match['result'] == 'W' else "match-draw" if match['result'] == 'D' else "match-loss"
            result_icon = "✅" if match['result'] == 'W' else "⚪" if match['result'] == 'D' else "❌"
            
            st.markdown(f"""
            <div class="match-result {result_class}">
                Match {i}: {result_icon} {match['result_text']} vs {match['opponent']} ({'Home' if match['home'] else 'Away'})<br>
                Score: {match['score']} - Date: {match['date']}<br>
                Scorers: {match['scorers']}
            </div>
            """, unsafe_allow_html=True)

def display_kelly_results(results):
    """Display Kelly Criterion calculation results"""
    st.markdown("""
    <div class="kelly-results">
        <h3>VALUE BET ANALYSIS</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Create metrics display
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Win Probability", f"{results['win_probability']:.1f}%")
        st.metric("Implied Probability", f"{results['implied_probability']:.1f}%")
        st.metric("Edge Percentage", f"{results['edge']:.1f}%")
    
    with col2:
        st.metric("Expected Value", format_currency(results['expected_value']))
        st.metric("Kelly Fraction", f"{results['kelly_fraction']:.1f}%")
        st.metric("Recommended Stake", format_currency(results['recommended_stake']))
    
    with col3:
        st.metric("Stake Percentage", f"{results['stake_percentage']:.1f}%")
        risk_color = "risk-low" if results['risk_assessment'] == "LOW RISK" else "risk-medium" if results['risk_assessment'] == "MEDIUM RISK" else "risk-high"
        st.markdown(f"""
        <div class="metric-row">
            <span class="metric-label">Risk Assessment:</span>
            <span class="metric-value {risk_color}">{results['risk_assessment']}</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Summary
    st.markdown("---")
    st.markdown("**SUMMARY:**")
    st.write(results['summary'])

def cache_data(key, data, duration_hours=1):
    """Cache data with expiration"""
    if 'cache' not in st.session_state:
        st.session_state.cache = {}
    
    expiration = datetime.now() + timedelta(hours=duration_hours)
    st.session_state.cache[key] = {
        'data': data,
        'expiration': expiration
    }

def get_cached_data(key):
    """Get cached data if not expired"""
    if 'cache' not in st.session_state:
        return None
    
    if key not in st.session_state.cache:
        return None
    
    cached_item = st.session_state.cache[key]
    if datetime.now() > cached_item['expiration']:
        del st.session_state.cache[key]
        return None
    
    return cached_item['data']

def safe_divide(numerator, denominator, default=0):
    """Safely divide two numbers"""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ValueError):
        return default

def truncate_text(text, max_length=50):
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def validate_bankroll_update(new_bankroll):
    """Validate bankroll update"""
    try:
        amount = float(new_bankroll)
        if amount < config.MIN_BANKROLL:
            return False, f"Minimum bankroll is {format_currency(config.MIN_BANKROLL)}"
        if amount > 1000000:  # 1 million max
            return False, "Maximum bankroll is $1,000,000"
        return True, amount
    except ValueError:
        return False, "Please enter a valid number"