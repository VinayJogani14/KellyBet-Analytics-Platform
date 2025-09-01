import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from models.kelly_calculator import KellyCalculator
from models.ml_models import SportsPredictionModel
from utils.helpers import (format_currency, validate_odds_input, display_kelly_results, 
                          update_bankroll, record_bet)
import config

def show():
    """Display the cricket Kelly criterion calculator page"""
    
    st.markdown("""
    <div class="main-header">
        <h1>Cricket Kelly Criterion Calculator</h1>
        <p>Format-specific betting analysis across Test, ODI, T20, and domestic cricket</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Current bankroll display
    current_bankroll = st.session_state.get('bankroll', config.DEFAULT_BANKROLL)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div class="bankroll-display">
            <h2>Current Bankroll: {format_currency(current_bankroll)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Initialize calculator and model
    kelly_calc = KellyCalculator()
    ml_model = SportsPredictionModel(sport='cricket')
    
    # Step 1: Format Selection
    st.subheader("1. Match Format Selection")
    
    match_format = st.radio(
        "Select cricket format:",
        list(config.CRICKET_FORMATS.keys()),
        key="cricket_format",
        format_func=lambda x: f"{x} ({config.CRICKET_FORMATS[x]})"
    )
    
    # Step 2: Tournament Selection
    st.subheader("2. Tournament Selection")
    tournament = select_cricket_tournament(match_format)
    
    # Step 3: Team Selection
    st.subheader("3. Team Selection")
    selected_teams = select_cricket_teams(match_format, tournament)
    
    if not selected_teams:
        st.info("Please select teams to continue with the analysis.")
        return
    
    # Step 4: Display Match Information
    st.subheader("4. Match Information")
    display_cricket_match_info(selected_teams, match_format)
    
    # Step 5: Market Selection
    st.subheader("5. Market Type Selection")
    market_type = select_cricket_market(match_format)
    
    # Step 6: Venue Information
    st.subheader("6. Venue & Conditions")
    venue_info = collect_venue_info(match_format)
    
    # Step 7: Odds Input
    st.subheader("7. Odds Input")
    odds_data = collect_cricket_odds_input(market_type, selected_teams, match_format)
    
    if not odds_data:
        st.info("Please enter odds to continue.")
        return
    
    # Step 8: Kelly Settings
    st.subheader("8. Kelly Calculation Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        kelly_fraction_type = st.selectbox(
            "Kelly Fraction:",
            list(config.KELLY_FRACTIONS.keys()),
            index=1,
            key="cricket_kelly_fraction"
        )
        kelly_modifier = config.KELLY_FRACTIONS[kelly_fraction_type]
    
    with col2:
        max_bankroll_percent = st.slider(
            "Maximum Bankroll Percentage:",
            min_value=0,
            max_value=100,
            value=70,
            step=5,
            key="cricket_max_bankroll"
        ) / 100
    
    # Step 9: Calculate Results
    if st.button("Calculate Cricket Kelly Analysis", type="primary"):
        with st.spinner("Analyzing cricket match probabilities..."):
            
            # Calculate win probability
            win_probability = calculate_cricket_win_probability(
                selected_teams, market_type, match_format, venue_info, ml_model
            )
            
            # Get bet details
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
            
            # Generate cricket-specific summary
            summary = generate_cricket_summary(results, selected_bet, selected_teams, match_format, venue_info)
            results['summary'] = summary
            
            # Display results
            display_kelly_results(results)
            
            # Cricket-specific insights
            display_cricket_insights(selected_teams, match_format, venue_info, results)
            
            # Step 10: Bet Recording
            st.subheader("10. Record Bet")
            display_cricket_bet_recording(results, selected_teams, market_type, 
                                        selected_bet, selected_odds, current_bankroll)

def select_cricket_tournament(match_format):
    """Select tournament based on format"""
    
    if match_format == "Test Match":
        tournaments = config.CRICKET_TOURNAMENTS['Test']
    elif match_format == "ODI":
        tournaments = config.CRICKET_TOURNAMENTS['ODI']
    elif match_format in ["T20 International", "T10"]:
        tournaments = config.CRICKET_TOURNAMENTS['T20']
    else:
        tournaments = config.CRICKET_TOURNAMENTS['Domestic']
    
    tournament = st.selectbox(
        "Select tournament:",
        tournaments,
        key="cricket_tournament"
    )
    
    return tournament

def select_cricket_teams(match_format, tournament):
    """Select cricket teams based on format and tournament"""
    
    # Determine team pool based on tournament
    if 'IPL' in tournament or 'BBL' in tournament or 'PSL' in tournament:
        teams = config.CRICKET_TEAMS['IPL']  # Use IPL teams as example
    else:
        teams = config.CRICKET_TEAMS['International']
    
    col1, col2 = st.columns(2)
    
    with col1:
        team1 = st.selectbox(
            "Team 1:",
            [""] + teams,
            key="cricket_team1"
        )
    
    with col2:
        team2_options = [team for team in teams if team != team1]
        team2 = st.selectbox(
            "Team 2:",
            [""] + team2_options,
            key="cricket_team2"
        )
    
    if team1 and team2:
        return {
            'team1': team1,
            'team2': team2,
            'tournament': tournament
        }
    
    return None

def select_cricket_market(match_format):
    """Select market type based on cricket format"""
    
    if match_format == "Test Match":
        markets = [
            "Match Result", "First Innings Lead", "Total Match Runs Over/Under",
            "Individual Batsman Match Runs", "Individual Bowler Match Wickets", "Session Betting"
        ]
    elif match_format == "ODI":
        markets = [
            "Match Winner", "Total Match Runs Over/Under", "Individual Batsman Runs", 
            "Method of Dismissal", "Powerplay Runs Over/Under", "Team Total Runs"
        ]
    else:  # T20 formats
        markets = [
            "Match Winner", "Total Match Runs Over/Under", "Individual Batsman Runs",
            "Powerplay Runs", "Death Overs Runs", "Same Game Parlay"
        ]
    
    market_type = st.selectbox(
        f"Select {match_format} betting market:",
        markets,
        key="cricket_market"
    )
    
    return market_type

def collect_venue_info(match_format):
    """Collect venue and conditions information"""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        venue = st.selectbox(
            "Venue:",
            ["Lord's (London)", "Eden Gardens (Kolkata)", "MCG (Melbourne)", 
             "Wankhede (Mumbai)", "The Oval (London)", "Dubai International"],
            key="cricket_venue"
        )
    
    with col2:
        pitch_type = st.selectbox(
            "Pitch Type:",
            ["Batting Paradise", "Balanced", "Spin-Friendly", "Pace-Friendly", "Low & Slow"],
            key="cricket_pitch"
        )
    
    with col3:
        weather = st.selectbox(
            "Weather:",
            ["Sunny", "Overcast", "Light Rain Expected", "Windy"],
            key="cricket_weather"
        )
    
    # Additional format-specific conditions
    if match_format in ["ODI", "T20 International", "T10"]:
        dew_factor = st.checkbox("Dew Factor (Evening Match)", key="dew_factor")
    else:
        dew_factor = False
    
    return {
        'venue': venue,
        'pitch_type': pitch_type,
        'weather': weather,
        'dew_factor': dew_factor
    }

def collect_cricket_odds_input(market_type, selected_teams, match_format):
    """Collect odds for cricket markets"""
    
    team1 = selected_teams['team1']
    team2 = selected_teams['team2']
    
    if market_type == "Match Result" and match_format == "Test Match":
        return collect_test_match_odds(team1, team2)
    elif market_type in ["Match Winner", "Match Result"]:
        return collect_match_winner_odds_cricket(team1, team2)
    elif "Total Match Runs" in market_type:
        return collect_total_runs_odds(match_format)
    elif "Individual Batsman" in market_type:
        return collect_batsman_runs_odds(selected_teams)
    elif "Individual Bowler" in market_type:
        return collect_bowler_wickets_odds(selected_teams)
    elif market_type == "Session Betting":
        return collect_session_betting_odds()
    elif market_type == "Same Game Parlay":
        return collect_cricket_parlay_odds(team1, team2, match_format)
    
    return None

def collect_test_match_odds(team1, team2):
    """Collect Test match odds (includes draw option)"""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        team1_odds = st.text_input(f"{team1} Win:", key="test_team1_odds")
    
    with col2:
        draw_odds = st.text_input("Draw:", key="test_draw_odds")
    
    with col3:
        team2_odds = st.text_input(f"{team2} Win:", key="test_team2_odds")
    
    valid_bets = []
    
    if team1_odds:
        is_valid, odds_value = validate_odds_input(team1_odds)
        if is_valid:
            valid_bets.append((f"{team1} Win", odds_value))
    
    if draw_odds:
        is_valid, odds_value = validate_odds_input(draw_odds)
        if is_valid:
            valid_bets.append(("Draw", odds_value))
    
    if team2_odds:
        is_valid, odds_value = validate_odds_input(team2_odds)
        if is_valid:
            valid_bets.append((f"{team2} Win", odds_value))
    
    if valid_bets:
        selected_bet_option = st.selectbox(
            "Select your bet:",
            [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets],
            key="cricket_winner_selection"
        )
        
        selected_index = [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets].index(selected_bet_option)
        selected_bet, selected_odds = valid_bets[selected_index]
        
        return {
            'selected_bet': selected_bet,
            'selected_odds': selected_odds,
            'market_type': 'match_winner'
        }
    
    return None

def collect_total_runs_odds(match_format):
    """Collect total runs over/under odds"""
    
    # Format-specific run lines
    default_lines = {
        'Test Match': 1150.5,
        'ODI': 590.5,
        'T20 International': 320.5,
        'T10': 180.5,
        'The Hundred': 280.5
    }
    
    runs_line = st.number_input(
        "Total Runs Line:",
        value=default_lines.get(match_format, 300.5),
        step=0.5,
        key="cricket_runs_line"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        over_runs = st.text_input(f"Over {runs_line} Runs:", key="cricket_over_runs")
    
    with col2:
        under_runs = st.text_input(f"Under {runs_line} Runs:", key="cricket_under_runs")
    
    valid_bets = []
    
    if over_runs:
        is_valid, odds_value = validate_odds_input(over_runs)
        if is_valid:
            valid_bets.append((f"Over {runs_line} Total Runs", odds_value))
    
    if under_runs:
        is_valid, odds_value = validate_odds_input(under_runs)
        if is_valid:
            valid_bets.append((f"Under {runs_line} Total Runs", odds_value))
    
    if valid_bets:
        selected_bet_option = st.selectbox(
            "Select total runs bet:",
            [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets],
            key="cricket_runs_selection"
        )
        
        selected_index = [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets].index(selected_bet_option)
        selected_bet, selected_odds = valid_bets[selected_index]
        
        return {
            'selected_bet': selected_bet,
            'selected_odds': selected_odds,
            'market_type': 'total_runs'
        }
    
    return None

def collect_batsman_runs_odds(selected_teams):
    """Collect individual batsman runs odds"""
    
    # Get top batsmen from both teams
    team1_batsmen = get_top_batsmen(selected_teams['team1'])
    team2_batsmen = get_top_batsmen(selected_teams['team2'])
    all_batsmen = team1_batsmen + team2_batsmen
    
    selected_batsman = st.selectbox(
        "Select batsman:",
        all_batsmen,
        key="cricket_batsman"
    )
    
    runs_line = st.number_input(
        f"{selected_batsman} Runs Line:",
        value=47.5,
        step=0.5,
        key="batsman_runs_line"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        over_runs = st.text_input(f"Over {runs_line} Runs:", key="batsman_over")
    
    with col2:
        under_runs = st.text_input(f"Under {runs_line} Runs:", key="batsman_under")
    
    valid_bets = []
    
    if over_runs:
        is_valid, odds_value = validate_odds_input(over_runs)
        if is_valid:
            valid_bets.append((f"{selected_batsman} Over {runs_line} Runs", odds_value))
    
    if under_runs:
        is_valid, odds_value = validate_odds_input(under_runs)
        if is_valid:
            valid_bets.append((f"{selected_batsman} Under {runs_line} Runs", odds_value))
    
    if valid_bets:
        selected_bet_option = st.selectbox(
            "Select batsman runs bet:",
            [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets],
            key="cricket_batsman_selection"
        )
        
        selected_index = [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets].index(selected_bet_option)
        selected_bet, selected_odds = valid_bets[selected_index]
        
        return {
            'selected_bet': selected_bet,
            'selected_odds': selected_odds,
            'market_type': 'batsman_runs'
        }
    
    return None

def collect_bowler_wickets_odds(selected_teams):
    """Collect individual bowler wickets odds"""
    
    # Get top bowlers from both teams
    team1_bowlers = get_top_bowlers(selected_teams['team1'])
    team2_bowlers = get_top_bowlers(selected_teams['team2'])
    all_bowlers = team1_bowlers + team2_bowlers
    
    selected_bowler = st.selectbox(
        "Select bowler:",
        all_bowlers,
        key="cricket_bowler"
    )
    
    wickets_line = st.number_input(
        f"{selected_bowler} Wickets Line:",
        value=2.5,
        step=0.5,
        key="bowler_wickets_line"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        over_wickets = st.text_input(f"Over {wickets_line} Wickets:", key="bowler_over")
    
    with col2:
        under_wickets = st.text_input(f"Under {wickets_line} Wickets:", key="bowler_under")
    
    valid_bets = []
    
    if over_wickets:
        is_valid, odds_value = validate_odds_input(over_wickets)
        if is_valid:
            valid_bets.append((f"{selected_bowler} Over {wickets_line} Wickets", odds_value))
    
    if under_wickets:
        is_valid, odds_value = validate_odds_input(under_wickets)
        if is_valid:
            valid_bets.append((f"{selected_bowler} Under {wickets_line} Wickets", odds_value))
    
    if valid_bets:
        selected_bet_option = st.selectbox(
            "Select bowler wickets bet:",
            [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets],
            key="cricket_bowler_selection"
        )
        
        selected_index = [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets].index(selected_bet_option)
        selected_bet, selected_odds = valid_bets[selected_index]
        
        return {
            'selected_bet': selected_bet,
            'selected_odds': selected_odds,
            'market_type': 'bowler_wickets'
        }
    
    return None

def collect_session_betting_odds():
    """Collect session betting odds (Test matches only)"""
    
    session = st.selectbox(
        "Select session:",
        ["Day 1 Session 1", "Day 1 Session 2", "Day 1 Session 3", 
         "Day 2 Session 1", "Day 2 Session 2", "Day 2 Session 3"],
        key="cricket_session"
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        team1_session = st.text_input("Team 1 Wins Session:", key="session_team1")
    
    with col2:
        draw_session = st.text_input("Session Draw:", key="session_draw")
    
    with col3:
        team2_session = st.text_input("Team 2 Wins Session:", key="session_team2")
    
    valid_bets = []
    
    if team1_session:
        is_valid, odds_value = validate_odds_input(team1_session)
        if is_valid:
            valid_bets.append((f"Team 1 Wins {session}", odds_value))
    
    if draw_session:
        is_valid, odds_value = validate_odds_input(draw_session)
        if is_valid:
            valid_bets.append((f"{session} Draw", odds_value))
    
    if team2_session:
        is_valid, odds_value = validate_odds_input(team2_session)
        if is_valid:
            valid_bets.append((f"Team 2 Wins {session}", odds_value))
    
    if valid_bets:
        selected_bet_option = st.selectbox(
            "Select session bet:",
            [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets],
            key="cricket_session_selection"
        )
        
        selected_index = [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets].index(selected_bet_option)
        selected_bet, selected_odds = valid_bets[selected_index]
        
        return {
            'selected_bet': selected_bet,
            'selected_odds': selected_odds,
            'market_type': 'session_betting'
        }
    
    return None

def collect_cricket_parlay_odds(team1, team2, match_format):
    """Collect cricket same game parlay odds"""
    
    if match_format == "T20 International":
        parlay_description = f"{team1} Win + Total Over 180.5 + Top Scorer 30+ Runs"
    elif match_format == "ODI":
        parlay_description = f"{team1} Win + Total Over 300 + Century Scored"
    else:
        parlay_description = f"{team1} Win + First Innings Lead + 400+ Total"
    
    st.write(f"**Same Game Parlay: {match_format} Special**")
    st.write(f"Combined bet: {parlay_description}")
    
    parlay_odds = st.text_input(
        "Same Game Parlay Odds:",
        help="American odds for combined bet",
        key="cricket_parlay_odds"
    )
    
    if parlay_odds:
        is_valid, odds_value = validate_odds_input(parlay_odds)
        if is_valid:
            return {
                'selected_bet': f"{match_format} Same Game Parlay",
                'selected_odds': odds_value,
                'market_type': 'same_game_parlay'
            }
    
    return None

def display_cricket_match_info(selected_teams, match_format):
    """Display cricket match information"""
    
    team1 = selected_teams['team1']
    team2 = selected_teams['team2']
    
    # Get real match data
    from data.cricket_data import CricketDataCollector
    cricket_data = CricketDataCollector()
    
    # Get recent matches from ESPN API
    team1_matches = cricket_data.get_team_recent_matches(team1, match_format)
    team2_matches = cricket_data.get_team_recent_matches(team2, match_format)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**{team1} - Recent {match_format} Matches:**")
        for i, match in enumerate(team1_matches, 1):
            result_icon = "✅" if match['result'] == 'W' else "⚪" if match['result'] == 'D' else "❌"
            st.markdown(f"""
            <div class="match-result match-{'win' if match['result'] == 'W' else 'draw' if match['result'] == 'D' else 'loss'}">
                Match {i}: {result_icon} {match['result_text']} vs {match['opponent']}<br>
                {match['score_details']}<br>
                Venue: {match['venue']} ({match['pitch_type']})<br>
                Date: {match['date']}
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"**{team2} - Recent {match_format} Matches:**")
        for i, match in enumerate(team2_matches, 1):
            result_icon = "✅" if match['result'] == 'W' else "⚪" if match['result'] == 'D' else "❌"
            st.markdown(f"""
            <div class="match-result match-{'win' if match['result'] == 'W' else 'draw' if match['result'] == 'D' else 'loss'}">
                Match {i}: {result_icon} {match['result_text']} vs {match['opponent']}<br>
                {match['score_details']}<br>
                Venue: {match['venue']} ({match['pitch_type']})<br>
                Date: {match['date']}
            </div>
            """, unsafe_allow_html=True)
    
    # Head-to-head record
    h2h_record = generate_cricket_h2h(team1, team2, match_format)
    st.markdown(f"**Head-to-Head ({match_format}):** {h2h_record}")

def generate_cricket_matches(team_name, match_format):
    """Generate mock cricket matches by format"""
    
    opponents = get_cricket_opponents(team_name)
    matches = []
    
    venues = ["Lord's", "Eden Gardens", "MCG", "Wankhede", "The Oval", "Dubai International"]
    pitch_types = ["Batting Paradise", "Spin-Friendly", "Pace-Friendly", "Balanced"]
    
    num_matches = 2 if match_format == "Test Match" else 2
    
    for i in range(num_matches):
        opponent = random.choice(opponents)
        venue = random.choice(venues)
        pitch_type = random.choice(pitch_types)
        
        # Generate format-specific results
        result, score_details = generate_cricket_result(team_name, opponent, match_format)
        
        match_date = (datetime.now() - timedelta(days=14*(i+1))).strftime("%d %B %Y")
        
        matches.append({
            'opponent': opponent,
            'result': result,
            'result_text': 'WON' if result == 'W' else 'DRAW' if result == 'D' else 'LOST',
            'score_details': score_details,
            'venue': venue,
            'pitch_type': pitch_type,
            'date': match_date
        })
    
    return matches

def generate_cricket_result(team_name, opponent, match_format):
    """Generate realistic cricket match result"""
    
    # Team strength assessment
    strong_teams = ['India', 'England', 'Australia', 'New Zealand', 'Mumbai Indians', 'Chennai Super Kings']
    team_strength = 0.6 if team_name in strong_teams else 0.4
    
    result_rand = random.random()
    
    if match_format == "Test Match":
        if result_rand < team_strength:
            result = 'W'
            if random.random() < 0.6:
                score_details = f"Won by {random.randint(50, 300)} runs"
            else:
                score_details = f"Won by {random.randint(3, 8)} wickets"
        elif result_rand < team_strength + 0.2:  # 20% draw chance
            result = 'D'
            score_details = "Match drawn (rain affected)" if random.random() < 0.5 else "Match drawn"
        else:
            result = 'L'
            if random.random() < 0.6:
                score_details = f"Lost by {random.randint(50, 250)} runs"
            else:
                score_details = f"Lost by {random.randint(3, 8)} wickets"
    
    else:  # Limited overs
        if result_rand < team_strength:
            result = 'W'
            if random.random() < 0.7:
                score_details = f"Won by {random.randint(3, 8)} wickets ({random.randint(6, 30)} balls remaining)"
            else:
                score_details = f"Won by {random.randint(10, 80)} runs"
        else:
            result = 'L'
            if random.random() < 0.7:
                score_details = f"Lost by {random.randint(3, 8)} wickets"
            else:
                score_details = f"Lost by {random.randint(10, 60)} runs"
    
    return result, score_details

def get_cricket_opponents(team_name):
    """Get potential opponents for cricket team"""
    if team_name in config.CRICKET_TEAMS['International']:
        return [team for team in config.CRICKET_TEAMS['International'] if team != team_name]
    else:
        return [team for team in config.CRICKET_TEAMS['IPL'] if team != team_name]

def get_top_batsmen(team_name):
    """Get top batsmen for a team"""
    
    batsmen_by_team = {
        'India': ['Virat Kohli', 'Rohit Sharma', 'KL Rahul', 'Shubman Gill'],
        'England': ['Joe Root', 'Ben Stokes', 'Harry Brook', 'Jos Buttler'],
        'Australia': ['Steve Smith', 'David Warner', 'Marnus Labuschagne', 'Travis Head'],
        'Mumbai Indians': ['Rohit Sharma', 'Ishan Kishan', 'Suryakumar Yadav', 'Tilak Varma'],
        'Chennai Super Kings': ['MS Dhoni', 'Ruturaj Gaikwad', 'Devon Conway', 'Ambati Rayudu']
    }
    
    return batsmen_by_team.get(team_name, ['Batsman A', 'Batsman B', 'Batsman C', 'Batsman D'])

def get_top_bowlers(team_name):
    """Get top bowlers for a team"""
    
    bowlers_by_team = {
        'India': ['Jasprit Bumrah', 'Mohammed Shami', 'Ravichandran Ashwin', 'Kuldeep Yadav'],
        'England': ['James Anderson', 'Stuart Broad', 'Mark Wood', 'Adil Rashid'],
        'Australia': ['Pat Cummins', 'Josh Hazlewood', 'Mitchell Starc', 'Nathan Lyon'],
        'Mumbai Indians': ['Jasprit Bumrah', 'Trent Boult', 'Lasith Malinga', 'Rahul Chahar'],
        'Chennai Super Kings': ['Deepak Chahar', 'Dwayne Bravo', 'Ravindra Jadeja', 'Imran Tahir']
    }
    
    return bowlers_by_team.get(team_name, ['Bowler A', 'Bowler B', 'Bowler C', 'Bowler D'])

def generate_cricket_h2h(team1, team2, match_format):
    """Generate cricket head-to-head record"""
    
    team1_wins = random.randint(2, 8)
    team2_wins = random.randint(2, 8) 
    draws = random.randint(0, 3) if match_format == "Test Match" else 0
    
    if team1_wins > team2_wins:
        leader = f"{team1} leads"
    elif team2_wins > team1_wins:
        leader = f"{team2} leads"
    else:
        leader = "Series tied"
    
    if draws > 0:
        return f"{team1} {team1_wins}-{team2_wins}-{draws} {team2} ({leader})"
    else:
        return f"{team1} {team1_wins}-{team2_wins} {team2} ({leader})"

def calculate_cricket_win_probability(selected_teams, market_type, match_format, venue_info, ml_model):
    """Calculate cricket match win probability"""
    
    # Generate mock team data
    team1_data = {
        'avg_score': random.randint(220, 300),
        'strike_rate': random.randint(80, 95),
        'top_order_avg': random.randint(30, 45),
        'bowling_avg': random.randint(25, 35),
        'economy_rate': random.uniform(4.5, 6.5)
    }
    
    team2_data = {
        'avg_score': random.randint(200, 280),
        'strike_rate': random.randint(75, 90),
        'top_order_avg': random.randint(25, 40),
        'bowling_avg': random.randint(28, 38),
        'economy_rate': random.uniform(5.0, 7.0)
    }
    
    match_info = {
        'format': match_format.lower().replace(' ', '_'),
        'venue_type': 'spinning' if venue_info['pitch_type'] == 'Spin-Friendly' else 'pace',
        'home_team': 'team1'
    }
    
    features = ml_model.prepare_cricket_features(team1_data, team2_data, match_info)
    base_probability = ml_model.predict_outcome(features)
    
    # Adjust for market type and format
    if market_type in ["Match Winner", "Match Result"]:
        return base_probability
    elif "Total Runs" in market_type:
        return 0.52  # Slightly favor over in cricket
    elif "Batsman" in market_type:
        return 0.45  # Conservative for individual performance
    elif "Bowler" in market_type:
        return 0.48  # Slightly under for wickets
    elif market_type == "Session Betting":
        return 0.35  # Session betting more unpredictable
    else:
        return 0.30  # Parlays have lower probability
    
def generate_cricket_summary(results, selected_bet, selected_teams, match_format, venue_info):
    """Generate cricket-specific betting summary"""
    
    if results['edge'] <= 0:
        return f"NO BET RECOMMENDED: No positive expected value for {selected_bet} in {match_format}."
    
    team1 = selected_teams['team1']
    team2 = selected_teams['team2']
    venue = venue_info['venue']
    pitch = venue_info['pitch_type']
    
    summary = f"Recommended bet: {results['stake_percentage']:.1f}% of bankroll ({format_currency(results['recommended_stake'])}) on {selected_bet}.\n\n"
    summary += f"Key factors:\n"
    summary += f"• {match_format} win probability: {results['win_probability']:.1f}%\n"
    summary += f"• Venue: {venue} ({pitch} pitch)\n"
    summary += f"• Betting edge: {results['edge']:.1f}%\n"
    summary += f"• Expected value: {format_currency(results['expected_value'])}\n"
    
    if venue_info.get('dew_factor'):
        summary += f"• Dew factor: Favors team batting second\n"
    
    summary += f"\nRisk level: {results['risk_assessment']} - "
    
    if results['risk_assessment'] == "HIGH RISK":
        summary += f"Significant edge detected but requires large stake. {match_format} can be unpredictable."
    elif results['risk_assessment'] == "MEDIUM RISK":
        summary += f"Good value with manageable risk for {match_format}."
    else:
        summary += f"Conservative bet with positive expected value in {match_format}."
    
    return summary

def display_cricket_insights(selected_teams, match_format, venue_info, results):
    """Display cricket-specific insights"""
    
    st.markdown("### Cricket Format Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Format Insights**")
        format_insights = get_format_insights(match_format)
        st.write(f"Format: {match_format}")
        st.write(f"Duration: {format_insights['duration']}")
        st.write(f"Key Factor: {format_insights['key_factor']}")
        st.write(f"Variance: {format_insights['variance']}")
    
    with col2:
        st.markdown("**Venue Analysis**")
        st.write(f"Venue: {venue_info['venue']}")
        st.write(f"Pitch: {venue_info['pitch_type']}")
        st.write(f"Weather: {venue_info['weather']}")
        if venue_info.get('dew_factor'):
            st.write("🌙 Dew factor in play")
    
    with col3:
        st.markdown("**Value Assessment**")
        confidence = 80 if results['edge'] > 8 else 65 if results['edge'] > 4 else 50
        st.metric("Model Confidence", f"{confidence}%")
        
        edge = results['edge']
        if edge > 10:
            st.success("Excellent value")
        elif edge > 5:
            st.info("Good value")
        else:
            st.warning("Marginal value")

def get_format_insights(match_format):
    """Get format-specific insights"""
    
    insights = {
        'Test Match': {
            'duration': '5 days maximum',
            'key_factor': 'Pitch deterioration',
            'variance': 'High (weather dependent)'
        },
        'ODI': {
            'duration': '7-8 hours',
            'key_factor': 'Batting order strategy',
            'variance': 'Medium (chase pressure)'
        },
        'T20 International': {
            'duration': '3-4 hours',
            'key_factor': 'Powerplay performance',
            'variance': 'Very High (explosive format)'
        },
        'T10': {
            'duration': '90 minutes',
            'key_factor': 'Boundary hitting',
            'variance': 'Extremely High'
        },
        'The Hundred': {
            'duration': '2.5 hours',
            'key_factor': 'Strategic timeouts',
            'variance': 'High (new format)'
        }
    }
    
    return insights.get(match_format, {'duration': 'Variable', 'key_factor': 'Team strength', 'variance': 'Medium'})

def display_cricket_bet_recording(results, selected_teams, market_type, selected_bet, selected_odds, current_bankroll):
    """Display cricket bet recording options"""
    
    recommended_stake = results['recommended_stake']
    
    if results['edge'] <= 0:
        st.warning("No positive edge detected. Consider avoiding this bet.")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Won Bet", type="primary", key="cricket_won"):
            from utils.helpers import american_to_decimal
            decimal_odds = american_to_decimal(selected_odds)
            payout = recommended_stake * decimal_odds
            profit = payout - recommended_stake
            
            new_bankroll = current_bankroll + profit
            update_bankroll(profit, 'add')
            
            bet_data = {
                'sport': 'cricket',
                'market_type': market_type,
                'team1': selected_teams['team1'],
                'team2': selected_teams['team2'],
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
            
            st.success(f"Cricket bet recorded as WON! Profit: {format_currency(profit)}")
            st.rerun()
    
    with col2:
        if st.button("Lost Bet", key="cricket_lost"):
            new_bankroll = current_bankroll - recommended_stake
            update_bankroll(recommended_stake, 'subtract')
            
            bet_data = {
                'sport': 'cricket',
                'market_type': market_type,
                'team1': selected_teams['team1'],
                'team2': selected_teams['team2'],
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
            
            st.error(f"Cricket bet recorded as LOST! Loss: {format_currency(recommended_stake)}")
            st.rerun()
    
    with col3:
        cashout_amount = st.number_input(
            "Cashout Amount:",
            min_value=0.0,
            max_value=float(recommended_stake * 8),
            step=1.0,
            key="cricket_cashout"
        )
        
        if st.button("Record Cashout", key="cricket_cashout_btn") and cashout_amount > 0:
            profit_loss = cashout_amount - recommended_stake
            new_bankroll = current_bankroll + profit_loss
            update_bankroll(profit_loss, 'add')
            
            bet_data = {
                'sport': 'cricket',
                'market_type': market_type,
                'team1': selected_teams['team1'],
                'team2': selected_teams['team2'],
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
            
            st.info(f"Cricket cashout recorded! Amount: {format_currency(cashout_amount)}")
            st.rerun()
    
    return None

def collect_match_winner_odds_cricket(team1, team2):
    """Collect limited overs match winner odds"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        team1_odds = st.text_input(f"{team1} Win:", key="cricket_team1_odds")
    
    with col2:
        team2_odds = st.text_input(f"{team2} Win:", key="cricket_team2_odds")
    
    valid_bets = []
    
    if team1_odds:
        is_valid, odds_value = validate_odds_input(team1_odds)
        if is_valid:
            valid_bets.append((f"{team1} Win", odds_value))
    
    if team2_odds:
        is_valid, odds_value = validate_odds_input(team2_odds)
        if is_valid:
            valid_bets.append((f"{team2} Win", odds_value))
    
    if valid_bets:
        selected_bet_option = st.selectbox(
            "Select your bet:",
            [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets],
            key="cricket_limited_selection"
        )
        
        selected_index = [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets].index(selected_bet_option)
        selected_bet, selected_odds = valid_bets[selected_index]
        
        return {
            'selected_bet': selected_bet,
            'selected_odds': selected_odds,
            'market_type': 'match_winner'
        }