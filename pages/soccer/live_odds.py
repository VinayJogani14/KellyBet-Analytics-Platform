import streamlit as st
import pandas as pd
from datetime import datetime
from data.odds_data import OddsDataCollector
import config

def show():
    """Display the soccer live odds page"""
    
    st.markdown("""
    <div class="main-header">
        <h1>Soccer Live Odds</h1>
        <p>Real-time odds from top 6 European leagues</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not config.THE_ODDS_API_KEY:
        st.warning("""
        ⚠️ Using mock data for demonstration. To get real odds:
        1. Sign up at https://the-odds-api.com
        2. Get your API key
        3. Add it to the .env file as THE_ODDS_API_KEY=your_key_here
        """, icon="⚠️")
    
    # Initialize odds collector
    odds_collector = OddsDataCollector()
    
    # League selection
    st.subheader("Select Leagues")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ucl_selected = st.checkbox("UEFA Champions League", value=True)
        epl_selected = st.checkbox("English Premier League", value=True)
    
    with col2:
        laliga_selected = st.checkbox("Spanish La Liga", value=True)
        serie_a_selected = st.checkbox("Italian Serie A", value=True)
    
    with col3:
        bundesliga_selected = st.checkbox("German Bundesliga", value=True)
        ligue1_selected = st.checkbox("French Ligue 1", value=True)
    
    # Build list of selected leagues
    selected_leagues = []
    if ucl_selected:
        selected_leagues.append('soccer_uefa_champions_league')
    if epl_selected:
        selected_leagues.append('soccer_epl')
    if laliga_selected:
        selected_leagues.append('soccer_spain_la_liga')
    if serie_a_selected:
        selected_leagues.append('soccer_italy_serie_a')
    if bundesliga_selected:
        selected_leagues.append('soccer_germany_bundesliga')
    if ligue1_selected:
        selected_leagues.append('soccer_france_ligue_one')
    
    # Refresh button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Refresh Odds", type="primary"):
            # Clear cache and fetch new odds
            if 'cache' in st.session_state and 'soccer_odds' in st.session_state.cache:
                del st.session_state.cache['soccer_odds']
            st.rerun()
    
    # Fetch and display odds
    if selected_leagues:
        with st.spinner("Fetching live odds..."):
            try:
                # Get odds data
                odds_data = odds_collector.get_cached_odds()
                
                # Filter by selected leagues
                filtered_odds = {k: v for k, v in odds_data.items() if k in selected_leagues}
                
                # Update cache
                odds_collector.update_odds_cache(odds_data)
                
                # Save to database
                odds_collector.save_odds_to_database(odds_data)
                
                # Display odds by league
                display_odds_by_league(filtered_odds, odds_collector)
                
            except Exception as e:
                st.error(f"Error fetching odds: {str(e)}")
                st.info("Please check your API key and try again.")
    
    else:
        st.info("Please select at least one league to view odds.")
    
    # Last updated timestamp
    st.markdown("---")
    current_time = datetime.now().strftime("%B %d, %Y at %H:%M:%S")
    st.caption(f"Last updated: {current_time}")

def display_odds_by_league(odds_data, odds_collector):
    """Display odds organized by league"""
    
    if not odds_data:
        st.info("No matches found for selected leagues.")
        return
    
    total_matches = sum(len(matches) for matches in odds_data.values())
    st.info(f"Found {total_matches} upcoming matches")
    
    for league_key, matches in odds_data.items():
        if not matches:
            continue
        
        # League header
        league_name = odds_collector.get_league_name_from_key(league_key)
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
            <h3 style="margin: 0; text-align: center;">{league_name}</h3>
            <p style="margin: 0; text-align: center; opacity: 0.8;">{len(matches)} upcoming matches</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display matches for this league
        for match in matches:
            display_match_card(match, odds_collector)
        
        st.markdown("<br>", unsafe_allow_html=True)

def display_match_card(match_data, odds_collector):
    """Display individual match card with odds"""
    
    # Format match for display
    formatted_match = odds_collector.format_match_for_display(match_data)
    
    # Create match card
    st.markdown(f"""
    <div class="match-info-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h4 style="margin: 0; color: #333;">{formatted_match['match_display']}</h4>
            <span style="color: #666; font-size: 0.9rem;">{formatted_match['date_time']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Odds display
    col1, col2, col3 = st.columns(3)
    
    with col1:
        home_odds = formatted_match['home_win_odds']
        home_bookmaker = formatted_match['best_bookmaker_home']
        if home_odds:
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: #e8f5e8; border-radius: 8px;">
                <div style="font-weight: bold; color: #2d5a2d;">{formatted_match['home_team']} Win</div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #1a4a1a;">
                    {'+' if home_odds > 0 else ''}{home_odds}
                </div>
                <div style="font-size: 0.8rem; color: #666;">Best: {home_bookmaker}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("No odds available")
    
    with col2:
        draw_odds = formatted_match['draw_odds']
        draw_bookmaker = formatted_match['best_bookmaker_draw']
        if draw_odds:
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: #fff3cd; border-radius: 8px;">
                <div style="font-weight: bold; color: #856404;">Draw</div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #533f03;">
                    {'+' if draw_odds > 0 else ''}{draw_odds}
                </div>
                <div style="font-size: 0.8rem; color: #666;">Best: {draw_bookmaker}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("No odds available")
    
    with col3:
        away_odds = formatted_match['away_win_odds']
        away_bookmaker = formatted_match['best_bookmaker_away']
        if away_odds:
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: #f8d7da; border-radius: 8px;">
                <div style="font-weight: bold; color: #721c24;">{formatted_match['away_team']} Win</div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #491217;">
                    {'+' if away_odds > 0 else ''}{away_odds}
                </div>
                <div style="font-size: 0.8rem; color: #666;">Best: {away_bookmaker}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("No odds available")
    
    # Calculate to Kelly button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button(f"📊 Analyze This Match", key=f"analyze_{formatted_match['match_id']}"):
            # Store match data in session state and navigate to Kelly calculator
            st.session_state.selected_match_data = {
                'team1': formatted_match['home_team'],
                'team2': formatted_match['away_team'],
                'home_odds': home_odds,
                'draw_odds': draw_odds,
                'away_odds': away_odds,
                'from_live_odds': True
            }
            st.session_state.selected_page = "kelly_calculator"
            st.rerun()
    
    st.markdown("---")

def display_odds_summary():
    """Display summary statistics of current odds"""
    st.subheader("Market Summary")
    
    # This would calculate summary stats from the odds
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Matches", "12")
    
    with col2:
        st.metric("Leagues Active", "6")
    
    with col3:
        st.metric("Avg Home Win Odds", "+145")
    
    with col4:
        st.metric("Bookmakers", "4")