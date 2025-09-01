import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from models.kelly_calculator import KellyCalculator
from models.ml_models import SportsPredictionModel
from data.soccer_data import SoccerDataCollector
from utils.helpers import (format_currency, validate_odds_input, display_kelly_results, 
                          update_bankroll, record_bet, display_match_info)
import config

def show():
    """Display the soccer Kelly criterion calculator page"""
    
    st.markdown("""
    <div class="main-header">
        <h1>Soccer Kelly Criterion Calculator</h1>
        <p>Optimal bet sizing for soccer matches using advanced probability models</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Current bankroll display
    current_bankroll = st.session_state.get('bankroll', config.DEFAULT_BANKROLL)
    
    st.markdown(f"""
        <div class="bankroll-display">
            <h2>Current Bankroll: {format_currency(current_bankroll)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Initialize calculator and model
    kelly_calc = KellyCalculator()
    ml_model = SportsPredictionModel(sport='soccer')
    soccer_data = SoccerDataCollector()
    
    # Step 1: Match Selection
    st.subheader("1. Match Selection")
    
    match_source = st.radio(
        "Select match source:",
        ["Live Odds Matches", "Manual Team Selection"],
        key="match_source"
    )
    
    if match_source == "Live Odds Matches":
        selected_match = select_from_live_odds()
    else:
        selected_match = select_teams_manually()
    
    if not selected_match:
        st.info("Please select teams to continue with the analysis.")
        return
    
    # Step 2: Display Match Information
    st.subheader("2. Match Information")
    display_selected_match_info(selected_match, soccer_data)
    
    # Step 3: Market Type Selection
    st.subheader("3. Market Type Selection")
    market_type = st.selectbox(
        "Select betting market:",
        config.SOCCER_MARKET_TYPES,
        key="market_type"
    )
    
    # Step 4: Odds Input Based on Market Type
    st.subheader("4. Odds Input")
    odds_data = collect_odds_input(market_type, selected_match)
    
    if not odds_data:
        st.info("Please enter odds to continue.")
        return
    
    # Step 5: Kelly Calculation Settings
    st.subheader("5. Kelly Calculation Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        kelly_fraction_type = st.selectbox(
            "Kelly Fraction:",
            list(config.KELLY_FRACTIONS.keys()),
            index=1,  # Default to Half Kelly
            key="kelly_fraction"
        )
        kelly_modifier = config.KELLY_FRACTIONS[kelly_fraction_type]
    
    with col2:
        max_bankroll_percent = st.slider(
            "Maximum Bankroll Percentage:",
            min_value=0,
            max_value=100,
            value=80,
            step=5,
            key="max_bankroll"
        ) / 100
    
    # Step 6: Calculate and Display Results
    if st.button("🧮 Calculate Kelly Analysis", type="primary"):
        with st.spinner("Calculating optimal bet size..."):
            
            # Calculate win probability using ML model
            win_probability = calculate_win_probability(
                selected_match, market_type, ml_model, soccer_data
            )
            
            # Get the selected bet from odds_data
            selected_bet = odds_data['selected_bet']
            selected_odds = odds_data['selected_odds']
            
            # Calculate Kelly recommendation
            results = kelly_calc.calculate_recommended_stake(
                win_probability=win_probability,
                american_odds=selected_odds,
                bankroll=current_bankroll,
                kelly_modifier=kelly_modifier,
                max_bankroll_percent=max_bankroll_percent
            )
            
            # Generate summary
            summary = kelly_calc.generate_summary(
                results, selected_bet, selected_match['team1'], selected_match['team2']
            )
            results['summary'] = summary
            
            # Display results
            display_kelly_results(results)
            
            # Step 7: Bet Recording Options
            st.subheader("7. Record Bet")
            display_bet_recording_options(results, selected_match, market_type, 
                                        selected_bet, selected_odds, current_bankroll)

def collect_player_odds(selected_match):
    """Collect odds for player to score or assist"""
    
    from data.soccer_data import SoccerDataCollector
    soccer_data = SoccerDataCollector()
    
    # Get top players from both teams
    team1_players = soccer_data.get_top_players(selected_match['team1'], limit=4)
    team2_players = soccer_data.get_top_players(selected_match['team2'], limit=3)
    
    all_players = team1_players + team2_players
    
    st.write("**Top Players (Goals + Assists in last 10 games):**")
    
    player_odds = {}
    for i, player in enumerate(all_players, 1):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write(f"{i}. {player['name']} ({player['team']}): {player['goals_assists']} combined")
        with col2:
            odds_input = st.text_input(
                "Odds:",
                key=f"player_odds_{i}",
                help="American odds format"
            )
            if odds_input:
                is_valid, odds_value = validate_odds_input(odds_input)
                if is_valid:
                    player_odds[player['name']] = odds_value
    
    if player_odds:
        selected_player = st.selectbox(
            "Select player bet:",
            list(player_odds.keys()),
            key="player_bet_selection"
        )
        
        if selected_player:
            return {
                'selected_bet': f"{selected_player} to Score or Assist",
                'selected_odds': player_odds[selected_player],
                'market_type': 'player_performance'
            }
    
    return None

def collect_over_under_odds(goals_line):
    """Collect over/under goals odds"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        over_odds_input = st.text_input(
            f"Over {goals_line} Goals:",
            key=f"over_{goals_line}_odds",
            help="American odds format"
        )
    
    with col2:
        under_odds_input = st.text_input(
            f"Under {goals_line} Goals:",
            key=f"under_{goals_line}_odds", 
            help="American odds format"
        )
    
    valid_bets = []
    
    if over_odds_input:
        is_valid, odds_value = validate_odds_input(over_odds_input)
        if is_valid:
            valid_bets.append((f"Over {goals_line} Goals", odds_value))
        else:
            st.error(f"Invalid over odds: {odds_value}")
    
    if under_odds_input:
        is_valid, odds_value = validate_odds_input(under_odds_input)
        if is_valid:
            valid_bets.append((f"Under {goals_line} Goals", odds_value))
        else:
            st.error(f"Invalid under odds: {odds_value}")
    
    if valid_bets:
        selected_bet_option = st.selectbox(
            "Select your bet:",
            [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets],
            key=f"ou_{goals_line}_bet_selection"
        )
        
        selected_index = [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets].index(selected_bet_option)
        selected_bet, selected_odds = valid_bets[selected_index]
        
        return {
            'selected_bet': selected_bet,
            'selected_odds': selected_odds,
            'market_type': 'total_goals'
        }
    
    return None

def collect_btts_odds():
    """Collect both teams to score odds"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        yes_odds_input = st.text_input(
            "Both Teams Score - Yes:",
            key="btts_yes_odds",
            help="American odds format"
        )
    
    with col2:
        no_odds_input = st.text_input(
            "Both Teams Score - No:",
            key="btts_no_odds",
            help="American odds format"
        )
    
    valid_bets = []
    
    if yes_odds_input:
        is_valid, odds_value = validate_odds_input(yes_odds_input)
        if is_valid:
            valid_bets.append(("Both Teams to Score - Yes", odds_value))
        else:
            st.error(f"Invalid yes odds: {odds_value}")
    
    if no_odds_input:
        is_valid, odds_value = validate_odds_input(no_odds_input)
        if is_valid:
            valid_bets.append(("Both Teams to Score - No", odds_value))
        else:
            st.error(f"Invalid no odds: {odds_value}")
    
    if valid_bets:
        selected_bet_option = st.selectbox(
            "Select your bet:",
            [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets],
            key="btts_bet_selection"
        )
        
        selected_index = [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets].index(selected_bet_option)
        selected_bet, selected_odds = valid_bets[selected_index]
        
        return {
            'selected_bet': selected_bet,
            'selected_odds': selected_odds,
            'market_type': 'both_teams_score'
        }
    
    return None

def calculate_win_probability(selected_match, market_type, ml_model, soccer_data):
    """Calculate win probability using ML model"""
    
    # Get team data
    team1_data = soccer_data.get_team_data(selected_match['team1'])
    team2_data = soccer_data.get_team_data(selected_match['team2'])
    
    # Match info
    match_info = {
        'venue': 'home',  # Assuming team1 is home
        'importance': 1,
        'rest_days_team1': 3,
        'rest_days_team2': 3
    }
    
    # Prepare features
    features = ml_model.prepare_soccer_features(team1_data, team2_data, match_info)
    
    # Get base win probability
    base_probability = ml_model.predict_outcome(features)
    
    # Adjust probability based on market type
    if market_type == "Moneyline":
        # Base probability is already for team1 win
        return base_probability
    elif market_type == "To Score or Assist":
        # Player-specific probability (simplified)
        return 0.25  # 25% chance for a specific player
    elif market_type in ["Over/Under 1.5 Goals", "Over/Under 2.5 Goals"]:
        # Goals-based probability
        if "1.5" in market_type:
            return 0.75  # 75% chance of over 1.5 goals
        else:
            return 0.55  # 55% chance of over 2.5 goals
    elif market_type == "Both Teams to Score":
        return 0.6  # 60% chance both teams score
    
    return 0.5  # Default 50%

def display_bet_recording_options(results, selected_match, market_type, selected_bet, selected_odds, current_bankroll):
    """Display bet recording options"""
    
    recommended_stake = results['recommended_stake']
    
    if results['edge'] <= 0:
        st.warning("No positive edge detected. Consider not placing this bet.")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Won Bet", type="primary"):
            # Calculate payout
            from utils.helpers import american_to_decimal
            decimal_odds = american_to_decimal(selected_odds)
            payout = recommended_stake * decimal_odds
            profit = payout - recommended_stake
            
            # Update bankroll
            new_bankroll = current_bankroll + profit
            update_bankroll(profit, 'add')
            
            # Record bet
            bet_data = {
                'sport': 'soccer',
                'market_type': market_type,
                'team1': selected_match['team1'],
                'team2': selected_match['team2'],
                'bet_type': selected_bet,
                'odds': selected_odds,
                'stake': recommended_stake,
                'win_probability': results['win_probability'],
                'kelly_fraction': results['kelly_fraction'],
                'expected_value': results['expected_value'],
                'edge': results['edge'],
                'result': 'win',
                'payout': payout,
                'profit_loss': profit,
                'bankroll_before': current_bankroll,
                'bankroll_after': new_bankroll
            }
            record_bet(bet_data)
            
            st.success(f"Bet recorded as WON! Profit: {format_currency(profit)}")
            st.success(f"New bankroll: {format_currency(new_bankroll)}")
            st.rerun()
    
    with col2:
        if st.button("Lost Bet"):
            # Update bankroll
            new_bankroll = current_bankroll - recommended_stake
            update_bankroll(recommended_stake, 'subtract')
            
            # Record bet
            bet_data = {
                'sport': 'soccer',
                'market_type': market_type,
                'team1': selected_match['team1'],
                'team2': selected_match['team2'],
                'bet_type': selected_bet,
                'odds': selected_odds,
                'stake': recommended_stake,
                'win_probability': results['win_probability'],
                'kelly_fraction': results['kelly_fraction'],
                'expected_value': results['expected_value'],
                'edge': results['edge'],
                'result': 'loss',
                'payout': 0,
                'profit_loss': -recommended_stake,
                'bankroll_before': current_bankroll,
                'bankroll_after': new_bankroll
            }
            record_bet(bet_data)
            
            st.error(f"Bet recorded as LOST! Loss: {format_currency(recommended_stake)}")
            st.error(f"New bankroll: {format_currency(new_bankroll)}")
            st.rerun()
    
    with col3:
        cashout_amount = st.number_input(
            "Cashout Amount:",
            min_value=0.0,
            max_value=float(recommended_stake * 10),
            step=1.0,
            key="cashout_amount"
        )
        
        if st.button("Record Cashout") and cashout_amount > 0:
            # Calculate profit/loss
            profit_loss = cashout_amount - recommended_stake
            new_bankroll = current_bankroll + profit_loss
            update_bankroll(profit_loss, 'add')
            
            # Record bet
            bet_data = {
                'sport': 'soccer',
                'market_type': market_type,
                'team1': selected_match['team1'],
                'team2': selected_match['team2'],
                'bet_type': selected_bet,
                'odds': selected_odds,
                'stake': recommended_stake,
                'win_probability': results['win_probability'],
                'kelly_fraction': results['kelly_fraction'],
                'expected_value': results['expected_value'],
                'edge': results['edge'],
                'result': 'cashout',
                'payout': cashout_amount,
                'profit_loss': profit_loss,
                'bankroll_before': current_bankroll,
                'bankroll_after': new_bankroll
            }
            record_bet(bet_data)
            
            st.info(f"Cashout recorded! Amount: {format_currency(cashout_amount)}")
            st.info(f"New bankroll: {format_currency(new_bankroll)}")
            st.rerun()
    with col2:
        st.markdown(f"""
        <div class="bankroll-display">
            <h2>Current Bankroll: {format_currency(current_bankroll)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
def select_from_live_odds():
    """Select match from live odds data"""
    
    # Check if we have match data from live odds page
    if 'selected_match_data' in st.session_state and st.session_state.selected_match_data.get('from_live_odds'):
        match_data = st.session_state.selected_match_data
        
        st.success(f"Match selected: {match_data['team1']} vs {match_data['team2']}")
        
        return {
            'team1': match_data['team1'],
            'team2': match_data['team2'],
            'live_odds': {
                'home_win': match_data.get('home_odds'),
                'draw': match_data.get('draw_odds'),
                'away_win': match_data.get('away_odds')
            }
        }
    
    # Otherwise show available matches from live odds
    try:
        from data.odds_data import OddsDataCollector
        odds_collector = OddsDataCollector()
        odds_data = odds_collector.get_cached_odds()
        
        # Flatten all matches
        all_matches = []
        for league, matches in odds_data.items():
            for match in matches:
                formatted = odds_collector.format_match_for_display(match)
                all_matches.append({
                    'display': formatted['match_display'],
                    'team1': formatted['home_team'],
                    'team2': formatted['away_team'],
                    'live_odds': {
                        'home_win': formatted['home_win_odds'],
                        'draw': formatted['draw_odds'],
                        'away_win': formatted['away_win_odds']
                    }
                })
        
        if all_matches:
            match_options = [match['display'] for match in all_matches]
            selected_option = st.selectbox(
                "Select match:",
                [""] + match_options,
                key="live_match_selection"
            )
            
            if selected_option:
                selected_match = next(match for match in all_matches if match['display'] == selected_option)
                return selected_match
        else:
            st.info("No live matches available. Please use manual team selection.")
    
    except Exception as e:
        st.error(f"Error loading live odds: {e}")
        st.info("Please use manual team selection.")
    
    return None

def select_teams_manually():
    """Manual team selection interface"""
    
    col1, col2 = st.columns(2)
    
    # Get all teams from all leagues
    all_teams = []
    for league, teams in config.SOCCER_TEAMS.items():
        all_teams.extend(teams)
    all_teams = sorted(list(set(all_teams)))  # Remove duplicates and sort
    
    with col1:
        team1 = st.selectbox(
            "Team 1 (Home):",
            [""] + all_teams,
            key="team1_selection",
            help="Search or select home team"
        )
    
    with col2:
        # Filter out selected team1 from team2 options
        team2_options = [team for team in all_teams if team != team1]
        team2 = st.selectbox(
            "Team 2 (Away):",
            [""] + team2_options,
            key="team2_selection",
            help="Search or select away team"
        )
    
    if team1 and team2:
        # Validate teams exist in our database
        if team1 in all_teams and team2 in all_teams:
            return {
                'team1': team1,
                'team2': team2,
                'live_odds': None
            }
        else:
            if team1 not in all_teams:
                st.error(f"{team1} is not in the list of supported teams")
            if team2 not in all_teams:
                st.error(f"{team2} is not in the list of supported teams")
    
    return None

def display_selected_match_info(selected_match, soccer_data):
    """Display information about the selected match"""
    
    team1 = selected_match['team1']
    team2 = selected_match['team2']
    
    # Get recent matches for both teams
    team1_matches = soccer_data.get_recent_matches(team1)
    team2_matches = soccer_data.get_recent_matches(team2)
    
    # Display match info
    display_match_info(team1_matches, team2_matches, team1, team2)
    
    # Head-to-head record
    h2h_record = soccer_data.get_head_to_head(team1, team2)
    
    st.markdown(f"""
    **Head-to-Head Record:** Last 10 meetings - {team1} {h2h_record['team1_wins']}-{h2h_record['draws']}-{h2h_record['team2_wins']} {team2}
    """)

def collect_odds_input(market_type, selected_match):
    """Collect odds input based on market type"""
    
    if market_type == "Moneyline":
        return collect_moneyline_odds(selected_match)
    elif market_type == "To Score or Assist":
        return collect_player_odds(selected_match)
    elif market_type == "Over/Under 1.5 Goals":
        return collect_over_under_odds("1.5")
    elif market_type == "Over/Under 2.5 Goals":
        return collect_over_under_odds("2.5")
    elif market_type == "Both Teams to Score":
        return collect_btts_odds()
    
    return None

def collect_moneyline_odds(selected_match):
    """Collect moneyline odds"""
    
    team1 = selected_match['team1']
    team2 = selected_match['team2']
    live_odds = selected_match.get('live_odds', {})
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        home_odds_input = st.text_input(
            f"{team1} Win Odds:",
            key="home_odds",
            help="American odds format"
        )
    
    with col2:
        draw_odds_input = st.text_input(
            "Draw Odds:",
            key="draw_odds",
            help="American odds format"
        )
    
    with col3:
        away_odds_input = st.text_input(
            f"{team2} Win Odds:",
            key="away_odds",
            help="American odds format"
        )
    
    valid_bets = []
    
    if home_odds_input:
        is_valid, odds_value = validate_odds_input(home_odds_input)
        if is_valid:
            valid_bets.append((f"{team1} Win", odds_value))
        else:
            st.error(f"Invalid home win odds: {odds_value}")
    
    if draw_odds_input:
        is_valid, odds_value = validate_odds_input(draw_odds_input)
        if is_valid:
            valid_bets.append(("Draw", odds_value))
        else:
            st.error(f"Invalid draw odds: {odds_value}")
    
    if away_odds_input:
        is_valid, odds_value = validate_odds_input(away_odds_input)
        if is_valid:
            valid_bets.append((f"{team2} Win", odds_value))
        else:
            st.error(f"Invalid away win odds: {odds_value}")
    
    if valid_bets:
        selected_bet_option = st.selectbox(
            "Select your bet:",
            [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets],
            key="moneyline_bet_selection"
        )
        
        # Extract bet details
        selected_index = [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets].index(selected_bet_option)
        selected_bet, selected_odds = valid_bets[selected_index]
        
        return {
            'selected_bet': selected_bet,
            'selected_odds': selected_odds,
            'market_type': 'moneyline'
        }
    
    return None