import streamlit as st
import sys
import os
from pathlib import Path
import base64

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from streamlit_option_menu import option_menu
from database.db_manager import DatabaseManager
from utils.helpers import load_css, initialize_session_state
import config

# Page imports
from pages.soccer import live_odds as soccer_live_odds
from pages.soccer import kelly_calculator as soccer_kelly
from pages.soccer import simulation as soccer_simulation
from pages.soccer import bankroll_tracking as soccer_bankroll

from pages.tennis import kelly_calculator as tennis_kelly
from pages.tennis import simulation as tennis_simulation
from pages.tennis import bankroll_tracking as tennis_bankroll

from pages.cricket import kelly_calculator as cricket_kelly
from pages.cricket import simulation as cricket_simulation
from pages.cricket import bankroll_tracking as cricket_bankroll

from pages.f1 import kelly_calculator as f1_kelly
from pages.f1 import simulation as f1_simulation
from pages.f1 import bankroll_tracking as f1_bankroll

def set_page_config():
    st.set_page_config(
        page_title="Kelly Criterion Betting App",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def load_css():
    with open("static/css/style.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def create_sport_card(title, sport_key, image_path, description):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            if st.button(title, key=f"select_{sport_key}", use_container_width=True):
                st.session_state.selected_sport = sport_key
                st.session_state.selected_page = "kelly_calculator"
                st.rerun()
                
            st.markdown(f"""
                <div class="sport-card">
                    <img src="data:image/png;base64,{get_image_base64(image_path)}" alt="{title}">
                    <h3>{title}</h3>
                    <p>{description}</p>
                </div>
            """, unsafe_allow_html=True)

def get_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def main():
    set_page_config()
    load_css()
    initialize_session_state()
    
    # Header
    st.markdown("""
        <div class="stHeader">
            <h1 style="color: white; text-align: center;">Kelly Criterion Betting Analytics</h1>
            <p style="color: #E0E0E0; text-align: center;">Optimize your betting strategy with advanced analytics</p>
        </div>
    """, unsafe_allow_html=True)

    # Sports Selection
    st.subheader("Select Your Sport")
    
    # Check if a sport is selected
    if 'selected_sport' in st.session_state and st.session_state.selected_sport:
        show_sport_pages()
    else:
        # Sport Cards
        col1, col2 = st.columns(2)
        with col1:
            create_sport_card(
                "Cricket Betting",
                "cricket",
                "static/images/cricket_tile.png",
                "Advanced cricket betting analytics with Kelly Criterion optimization"
            )
            create_sport_card(
                "Formula 1 Betting",
                "f1",
                "static/images/f1_tile.png",
                "F1 race betting analysis and bankroll management"
            )
        
        with col2:
            create_sport_card(
                "Soccer Betting",
                "soccer",
                "static/images/soccer_tile.png",
                "Soccer match betting with live odds integration"
            )
            create_sport_card(
                "Tennis Betting",
                "tennis",
                "static/images/tennis_tile.png",
                "Tennis match betting analytics and simulations"
            )

    # Current bankroll display
    current_bankroll = st.session_state.get('bankroll', 5000.00)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div class="bankroll-display">
            <h2>Current Bankroll: ${current_bankroll:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Features overview
    st.markdown("""
    <div class="features-section">
        <h3>Key Features</h3>
        <div class="features-grid">
            <div class="feature-item">
                <h4>Kelly Criterion Calculator</h4>
                <p>Optimal bet sizing based on mathematical models and probability analysis</p>
            </div>
            <div class="feature-item">
                <h4>Live Odds Integration</h4>
                <p>Real-time odds from multiple bookmakers for accurate edge calculation</p>
            </div>
            <div class="feature-item">
                <h4>Machine Learning Models</h4>
                <p>Advanced ML models for win probability prediction across all sports</p>
            </div>
            <div class="feature-item">
                <h4>Bankroll Management</h4>
                <p>Comprehensive tracking and risk management tools</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_sport_pages():
    """Display sport-specific pages with navigation"""
    
    sport = st.session_state.selected_sport
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown(f"<h2>{sport.upper()} BETTING ANALYSIS</h2>", unsafe_allow_html=True)
        
        # Back to home button
        if st.button("← Back to Home"):
            st.session_state.selected_sport = None
            st.session_state.selected_page = None
            st.rerun()
        
        st.markdown("---")
        
        # Sport-specific navigation
        if sport == "soccer":
            selected = option_menu(
                menu_title=None,
                options=["Live Odds", "Kelly Calculator", "Simulation", "Bankroll Tracking"],
                icons=["broadcast", "calculator", "graph-up", "wallet2"],
                menu_icon="cast",
                default_index=0 if st.session_state.selected_page == "live_odds" else 
                             1 if st.session_state.selected_page == "kelly_calculator" else
                             2 if st.session_state.selected_page == "simulation" else 3,
                key="soccer_menu"
            )
            st.session_state.selected_page = selected.lower().replace(" ", "_")
            
        else:
            # Tennis, Cricket, F1 have 3 pages each
            selected = option_menu(
                menu_title=None,
                options=["Kelly Calculator", "Simulation", "Bankroll Tracking"],
                icons=["calculator", "graph-up", "wallet2"],
                menu_icon="cast",
                default_index=0 if st.session_state.selected_page == "kelly_calculator" else 
                             1 if st.session_state.selected_page == "simulation" else 2,
                key=f"{sport}_menu"
            )
            st.session_state.selected_page = selected.lower().replace(" ", "_")
    
    # Main content area
    page = st.session_state.selected_page
    
    # Route to appropriate page
    if sport == "soccer":
        if page == "live_odds":
            soccer_live_odds.show()
        elif page == "kelly_calculator":
            soccer_kelly.show()
        elif page == "simulation":
            soccer_simulation.show()
        elif page == "bankroll_tracking":
            soccer_bankroll.show()
            
    elif sport == "tennis":
        if page == "kelly_calculator":
            tennis_kelly.show()
        elif page == "simulation":
            tennis_simulation.show()
        elif page == "bankroll_tracking":
            tennis_bankroll.show()
            
    elif sport == "cricket":
        if page == "kelly_calculator":
            cricket_kelly.show()
        elif page == "simulation":
            cricket_simulation.show()
        elif page == "bankroll_tracking":
            cricket_bankroll.show()
            
    elif sport == "f1":
        if page == "kelly_calculator":
            f1_kelly.show()
        elif page == "simulation":
            f1_simulation.show()
        elif page == "bankroll_tracking":
            f1_bankroll.show()

if __name__ == "__main__":
    main()
