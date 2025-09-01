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
    """Display the tennis Kelly criterion calculator page"""
    
    st.markdown("""
    <div class="main-header">
        <h1>Tennis Kelly Criterion Calculator</h1>
        <p>Optimal bet sizing for tennis matches using surface-specific analysis</p>
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
    ml_model = SportsPredictionModel(sport='tennis')
    
    # Step 1: Match Type Selection
    st.subheader("1. Match Type Selection")
    
    match_type = st.radio(
        "Select match type:",
        ["Singles Match", "Doubles Match"],
        key="tennis_match_type"
    )
    
    # Step 2: Player Selection
    st.subheader("2. Player/Pair Selection")
    
    if match_type == "Singles Match":
        selected_players = select_singles_players()
    else:
        selected_players = select_doubles_pairs()
    
    if not selected_players:
        st.info("Please select players to continue with the analysis.")
        return
    
    # Step 3: Display Match Information
    st.subheader("3. Match Information")
    display_tennis_match_info(selected_players, match_type)
    
    # Step 4: Market Type Selection
    st.subheader("4. Market Type Selection")
    market_type = st.selectbox(
        "Select betting market:",
        config.TENNIS_MARKET_TYPES,
        key="tennis_market_type"
    )
    
    # Step 5: Surface Selection
    st.subheader("5. Surface & Tournament Info")
    
    col1, col2 = st.columns(2)
    with col1:
        surface = st.selectbox(
            "Court Surface:",
            ["Hard Court", "Clay Court", "Grass Court"],
            key="tennis_surface"
        )
    
    with col2:
        tournament_level = st.selectbox(
            "Tournament Level:",
            ["Grand Slam", "Masters 1000", "ATP 500", "ATP 250", "WTA 1000", "WTA 500"],
            key="tennis_tournament"
        )
    
    # Step 6: Odds Input
    st.subheader("6. Odds Input")
    odds_data = collect_tennis_odds_input(market_type, selected_players)
    
    if not odds_data:
        st.info("Please enter odds to continue.")
        return
    
    # Step 7: Kelly Calculation Settings
    st.subheader("7. Kelly Calculation Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        kelly_fraction_type = st.selectbox(
            "Kelly Fraction:",
            list(config.KELLY_FRACTIONS.keys()),
            index=1,
            key="tennis_kelly_fraction"
        )
        kelly_modifier = config.KELLY_FRACTIONS[kelly_fraction_type]
    
    with col2:
        max_bankroll_percent = st.slider(
            "Maximum Bankroll Percentage:",
            min_value=0,
            max_value=100,
            value=75,
            step=5,
            key="tennis_max_bankroll"
        ) / 100
    
    # Step 8: Calculate Results
    if st.button("Calculate Tennis Kelly Analysis", type="primary"):
        with st.spinner("Analyzing match probabilities..."):
            
            # Calculate win probability
            win_probability = calculate_tennis_win_probability(
                selected_players, market_type, surface, tournament_level, ml_model
            )
            
            # Get selected bet details
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
            
            # Add tennis-specific insights
            results['surface_analysis'] = get_surface_analysis(selected_players, surface)
            results['tournament_factor'] = get_tournament_factor(tournament_level)
            
            # Generate summary
            summary = generate_tennis_summary(results, selected_bet, selected_players, surface)
            results['summary'] = summary
            
            # Display results
            display_kelly_results(results)
            
            # Additional tennis insights
            display_tennis_insights(selected_players, surface, results)
            
            # Step 9: Bet Recording
            st.subheader("9. Record Bet")
            display_tennis_bet_recording(results, selected_players, market_type, 
                                       selected_bet, selected_odds, current_bankroll)

def select_singles_players():
    """Select singles players"""
    
    # ATP/WTA Top 100 players (mock data)
    atp_players = [
        "Novak Djokovic (ATP #1)", "Carlos Alcaraz (ATP #2)", "Daniil Medvedev (ATP #3)",
        "Jannik Sinner (ATP #4)", "Andrey Rublev (ATP #5)", "Stefanos Tsitsipas (ATP #6)",
        "Alexander Zverev (ATP #7)", "Holger Rune (ATP #8)", "Taylor Fritz (ATP #9)",
        "Tommy Paul (ATP #10)", "Casper Ruud (ATP #11)", "Alex de Minaur (ATP #12)",
        "Grigor Dimitrov (ATP #13)", "Ben Shelton (ATP #14)", "Ugo Humbert (ATP #15)",
        "Lorenzo Musetti (ATP #16)", "Sebastian Korda (ATP #17)", "Felix Auger-Aliassime (ATP #18)",
        "Arthur Fils (ATP #19)", "Frances Tiafoe (ATP #20)"
    ]
    
    wta_players = [
        "Aryna Sabalenka (WTA #1)", "Iga Swiatek (WTA #2)", "Coco Gauff (WTA #3)",
        "Jessica Pegula (WTA #4)", "Elena Rybakina (WTA #5)", "Jasmine Paolini (WTA #6)",
        "Zheng Qinwen (WTA #7)", "Emma Navarro (WTA #8)", "Daria Kasatkina (WTA #9)",
        "Barbora Krejcikova (WTA #10)", "Danielle Collins (WTA #11)", "Paula Badosa (WTA #12)",
        "Diana Shnaider (WTA #13)", "Beatriz Haddad Maia (WTA #14)", "Anna Kalinskaya (WTA #15)",
        "Marta Kostyuk (WTA #16)", "Donna Vekic (WTA #17)", "Madison Keys (WTA #18)",
        "Liudmila Samsonova (WTA #19)", "Mirra Andreeva (WTA #20)"
    ]
    
    all_players = atp_players + wta_players
    
    col1, col2 = st.columns(2)
    
    with col1:
        player1 = st.selectbox(
            "Player 1:",
            [""] + all_players,
            key="tennis_player1"
        )
    
    with col2:
        # Exclude selected player1
        player2_options = [p for p in all_players if p != player1]
        player2 = st.selectbox(
            "Player 2:",
            [""] + player2_options,
            key="tennis_player2"
        )
    
    if player1 and player2:
        return {
            'player1': player1,
            'player2': player2,
            'match_type': 'singles'
        }
    
    return None

def select_doubles_pairs():
    """Select doubles pairs"""
    
    # Top doubles pairs (mock data)
    doubles_pairs = [
        "Salisbury/Ram (ATP #1)", "Granollers/Zeballos (ATP #2)", 
        "Arevalo/Pavic (ATP #3)", "Bopanna/Ebden (ATP #4)",
        "Krejcikova/Siniakova (WTA #1)", "Hsieh/Mertens (WTA #2)",
        "Gauff/Siniakova (WTA #3)", "Dolehide/Krawczyk (WTA #4)"
    ]
    
    col1, col2 = st.columns(2)
    
    with col1:
        pair1 = st.selectbox(
            "Doubles Pair 1:",
            [""] + doubles_pairs,
            key="tennis_pair1"
        )
    
    with col2:
        pair2_options = [p for p in doubles_pairs if p != pair1]
        pair2 = st.selectbox(
            "Doubles Pair 2:",
            [""] + pair2_options,
            key="tennis_pair2"
        )
    
    if pair1 and pair2:
        return {
            'player1': pair1,
            'player2': pair2,
            'match_type': 'doubles'
        }
    
    return None

def display_tennis_match_info(selected_players, match_type):
    """Display tennis match information"""
    
    player1 = selected_players['player1']
    player2 = selected_players['player2']
    
    # Generate mock recent matches
    player1_matches = generate_tennis_matches(player1)
    player2_matches = generate_tennis_matches(player2)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**{player1} - Recent Matches:**")
        for i, match in enumerate(player1_matches, 1):
            result_icon = "✅" if match['result'] == 'W' else "❌"
            st.markdown(f"""
            <div class="match-result match-{'win' if match['result'] == 'W' else 'loss'}">
                Match {i}: {result_icon} {match['result_text']} vs {match['opponent']}<br>
                Score: {match['score']}<br>
                Surface: {match['surface']} - Tournament: {match['tournament']}<br>
                Date: {match['date']}
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"**{player2} - Recent Matches:**")
        for i, match in enumerate(player2_matches, 1):
            result_icon = "✅" if match['result'] == 'W' else "❌"
            st.markdown(f"""
            <div class="match-result match-{'win' if match['result'] == 'W' else 'loss'}">
                Match {i}: {result_icon} {match['result_text']} vs {match['opponent']}<br>
                Score: {match['score']}<br>
                Surface: {match['surface']} - Tournament: {match['tournament']}<br>
                Date: {match['date']}
            </div>
            """, unsafe_allow_html=True)
    
    # Head-to-Head Record
    h2h_record = generate_h2h_record(player1, player2)
    st.markdown(f"**Head-to-Head:** {h2h_record}")

def collect_tennis_odds_input(market_type, selected_players):
    """Collect odds input for tennis markets"""
    
    player1 = selected_players['player1'].split(' (')[0]  # Remove ranking info
    player2 = selected_players['player2'].split(' (')[0]
    
    if market_type == "Match Winner":
        return collect_match_winner_odds(player1, player2)
    elif market_type == "Set Betting":
        return collect_set_betting_odds(player1, player2)
    elif market_type == "Total Games Over/Under":
        return collect_total_games_odds()
    elif market_type == "Total Aces Over/Under":
        return collect_aces_odds(player1, player2)
    elif market_type == "Total Double Faults Over/Under":
        return collect_double_faults_odds(player1, player2)
    elif market_type == "Exact Number of Sets":
        return collect_exact_sets_odds()
    elif market_type == "Number of Tiebreaks":
        return collect_tiebreaks_odds()
    elif market_type == "Service Breaks":
        return collect_service_breaks_odds()
    elif market_type == "Same Game Parlay #1":
        return collect_parlay_odds(1, player1, player2)
    elif market_type == "Same Game Parlay #2":
        return collect_parlay_odds(2, player1, player2)
    
    return None

def collect_match_winner_odds(player1, player2):
    """Collect match winner odds"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        player1_odds = st.text_input(
            f"{player1} to Win:",
            help="American odds format",
            key="tennis_p1_odds"
        )
    
    with col2:
        player2_odds = st.text_input(
            f"{player2} to Win:",
            help="American odds format", 
            key="tennis_p2_odds"
        )
    
    valid_bets = []
    
    if player1_odds:
        is_valid, odds_value = validate_odds_input(player1_odds)
        if is_valid:
            valid_bets.append((f"{player1} to Win", odds_value))
        else:
            st.error(f"Invalid {player1} odds: {odds_value}")
    
    if player2_odds:
        is_valid, odds_value = validate_odds_input(player2_odds)
        if is_valid:
            valid_bets.append((f"{player2} to Win", odds_value))
        else:
            st.error(f"Invalid {player2} odds: {odds_value}")
    
    if valid_bets:
        selected_bet_option = st.selectbox(
            "Select your bet:",
            [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets],
            key="tennis_winner_selection"
        )
        
        selected_index = [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets].index(selected_bet_option)
        selected_bet, selected_odds = valid_bets[selected_index]
        
        return {
            'selected_bet': selected_bet,
            'selected_odds': selected_odds,
            'market_type': 'match_winner'
        }
    
    return None

def collect_set_betting_odds(player1, player2):
    """Collect set betting odds"""
    
    st.write("**Set Betting Markets:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        p1_2_0_odds = st.text_input(f"{player1} 2-0:", key="p1_2_0")
        p1_2_1_odds = st.text_input(f"{player1} 2-1:", key="p1_2_1")
    
    with col2:
        p2_2_0_odds = st.text_input(f"{player2} 2-0:", key="p2_2_0") 
        p2_2_1_odds = st.text_input(f"{player2} 2-1:", key="p2_2_1")
    
    valid_bets = []
    
    # Validate all inputs
    set_bets = [
        (f"{player1} 2-0", p1_2_0_odds),
        (f"{player1} 2-1", p1_2_1_odds),
        (f"{player2} 2-0", p2_2_0_odds),
        (f"{player2} 2-1", p2_2_1_odds)
    ]
    
    for bet_name, odds_input in set_bets:
        if odds_input:
            is_valid, odds_value = validate_odds_input(odds_input)
            if is_valid:
                valid_bets.append((bet_name, odds_value))
    
    if valid_bets:
        selected_bet_option = st.selectbox(
            "Select set betting option:",
            [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets],
            key="tennis_set_selection"
        )
        
        selected_index = [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets].index(selected_bet_option)
        selected_bet, selected_odds = valid_bets[selected_index]
        
        return {
            'selected_bet': selected_bet,
            'selected_odds': selected_odds,
            'market_type': 'set_betting'
        }
    
    return None

def collect_total_games_odds():
    """Collect total games over/under odds"""
    
    games_line = st.number_input("Games Line:", value=21.5, step=0.5, key="games_line")
    
    col1, col2 = st.columns(2)
    
    with col1:
        over_odds = st.text_input(f"Over {games_line} Games:", key="games_over")
    
    with col2:
        under_odds = st.text_input(f"Under {games_line} Games:", key="games_under")
    
    valid_bets = []
    
    if over_odds:
        is_valid, odds_value = validate_odds_input(over_odds)
        if is_valid:
            valid_bets.append((f"Over {games_line} Games", odds_value))
    
    if under_odds:
        is_valid, odds_value = validate_odds_input(under_odds)
        if is_valid:
            valid_bets.append((f"Under {games_line} Games", odds_value))
    
    if valid_bets:
        selected_bet_option = st.selectbox(
            "Select games bet:",
            [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets],
            key="tennis_games_selection"
        )
        
        selected_index = [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets].index(selected_bet_option)
        selected_bet, selected_odds = valid_bets[selected_index]
        
        return {
            'selected_bet': selected_bet,
            'selected_odds': selected_odds,
            'market_type': 'total_games'
        }
    
    return None

def collect_aces_odds(player1, player2):
    """Collect aces over/under odds"""
    
    selected_player = st.selectbox(
        "Select player for aces bet:",
        [player1, player2],
        key="aces_player_selection"
    )
    
    aces_line = st.number_input("Aces Line:", value=8.5, step=0.5, key="aces_line")
    
    col1, col2 = st.columns(2)
    
    with col1:
        over_aces = st.text_input(f"Over {aces_line} Aces:", key="aces_over")
    
    with col2:
        under_aces = st.text_input(f"Under {aces_line} Aces:", key="aces_under")
    
    valid_bets = []
    
    if over_aces:
        is_valid, odds_value = validate_odds_input(over_aces)
        if is_valid:
            valid_bets.append((f"{selected_player} Over {aces_line} Aces", odds_value))
    
    if under_aces:
        is_valid, odds_value = validate_odds_input(under_aces)
        if is_valid:
            valid_bets.append((f"{selected_player} Under {aces_line} Aces", odds_value))
    
    if valid_bets:
        selected_bet_option = st.selectbox(
            "Select aces bet:",
            [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets],
            key="tennis_aces_selection"
        )
        
        selected_index = [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets].index(selected_bet_option)
        selected_bet, selected_odds = valid_bets[selected_index]
        
        return {
            'selected_bet': selected_bet,
            'selected_odds': selected_odds,
            'market_type': 'aces'
        }
    
    return None

def collect_double_faults_odds(player1, player2):
    """Collect double faults over/under odds"""
    
    selected_player = st.selectbox(
        "Select player for double faults bet:",
        [player1, player2],
        key="df_player_selection"
    )
    
    df_line = st.number_input("Double Faults Line:", value=3.5, step=0.5, key="df_line")
    
    col1, col2 = st.columns(2)
    
    with col1:
        over_df = st.text_input(f"Over {df_line} Double Faults:", key="df_over")
    
    with col2:
        under_df = st.text_input(f"Under {df_line} Double Faults:", key="df_under")
    
    valid_bets = []
    
    if over_df:
        is_valid, odds_value = validate_odds_input(over_df)
        if is_valid:
            valid_bets.append((f"{selected_player} Over {df_line} Double Faults", odds_value))
    
    if under_df:
        is_valid, odds_value = validate_odds_input(under_df)
        if is_valid:
            valid_bets.append((f"{selected_player} Under {df_line} Double Faults", odds_value))
    
    if valid_bets:
        selected_bet_option = st.selectbox(
            "Select double faults bet:",
            [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets],
            key="tennis_df_selection"
        )
        
        selected_index = [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets].index(selected_bet_option)
        selected_bet, selected_odds = valid_bets[selected_index]
        
        return {
            'selected_bet': selected_bet,
            'selected_odds': selected_odds,
            'market_type': 'double_faults'
        }
    
    return None

def collect_exact_sets_odds():
    """Collect exact number of sets odds"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        two_sets_odds = st.text_input("Match goes 2 sets:", key="two_sets")
    
    with col2:
        three_sets_odds = st.text_input("Match goes 3 sets:", key="three_sets")
    
    valid_bets = []
    
    if two_sets_odds:
        is_valid, odds_value = validate_odds_input(two_sets_odds)
        if is_valid:
            valid_bets.append(("Match goes 2 sets", odds_value))
    
    if three_sets_odds:
        is_valid, odds_value = validate_odds_input(three_sets_odds)
        if is_valid:
            valid_bets.append(("Match goes 3 sets", odds_value))
    
    if valid_bets:
        selected_bet_option = st.selectbox(
            "Select sets bet:",
            [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets],
            key="tennis_sets_selection"
        )
        
        selected_index = [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets].index(selected_bet_option)
        selected_bet, selected_odds = valid_bets[selected_index]
        
        return {
            'selected_bet': selected_bet,
            'selected_odds': selected_odds,
            'market_type': 'exact_sets'
        }
    
    return None

def collect_tiebreaks_odds():
    """Collect tiebreaks odds"""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        zero_tb = st.text_input("0 Tiebreaks:", key="zero_tb")
    
    with col2:
        one_tb = st.text_input("1 Tiebreak:", key="one_tb")
    
    with col3:
        two_plus_tb = st.text_input("2+ Tiebreaks:", key="two_plus_tb")
    
    valid_bets = []
    
    tiebreak_bets = [
        ("0 Tiebreaks", zero_tb),
        ("1 Tiebreak", one_tb), 
        ("2+ Tiebreaks", two_plus_tb)
    ]
    
    for bet_name, odds_input in tiebreak_bets:
        if odds_input:
            is_valid, odds_value = validate_odds_input(odds_input)
            if is_valid:
                valid_bets.append((bet_name, odds_value))
    
    if valid_bets:
        selected_bet_option = st.selectbox(
            "Select tiebreaks bet:",
            [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets],
            key="tennis_tb_selection"
        )
        
        selected_index = [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets].index(selected_bet_option)
        selected_bet, selected_odds = valid_bets[selected_index]
        
        return {
            'selected_bet': selected_bet,
            'selected_odds': selected_odds,
            'market_type': 'tiebreaks'
        }
    
    return None

def collect_service_breaks_odds():
    """Collect service breaks odds"""
    
    breaks_line = st.number_input("Service Breaks Line:", value=4.5, step=0.5, key="breaks_line")
    
    col1, col2 = st.columns(2)
    
    with col1:
        over_breaks = st.text_input(f"Over {breaks_line} Breaks:", key="breaks_over")
    
    with col2:
        under_breaks = st.text_input(f"Under {breaks_line} Breaks:", key="breaks_under")
    
    valid_bets = []
    
    if over_breaks:
        is_valid, odds_value = validate_odds_input(over_breaks)
        if is_valid:
            valid_bets.append((f"Over {breaks_line} Service Breaks", odds_value))
    
    if under_breaks:
        is_valid, odds_value = validate_odds_input(under_breaks)
        if is_valid:
            valid_bets.append((f"Under {breaks_line} Service Breaks", odds_value))
    
    if valid_bets:
        selected_bet_option = st.selectbox(
            "Select service breaks bet:",
            [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets],
            key="tennis_breaks_selection"
        )
        
        selected_index = [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets].index(selected_bet_option)
        selected_bet, selected_odds = valid_bets[selected_index]
        
        return {
            'selected_bet': selected_bet,
            'selected_odds': selected_odds,
            'market_type': 'service_breaks'
        }
    
    return None

def collect_parlay_odds(parlay_number, player1, player2):
    """Collect same game parlay odds"""
    
    if parlay_number == 1:
        parlay_name = "Dominant Performance"
        parlay_description = f"{player1} Win + Under 20.5 Games + {player1} Over 6.5 Aces"
    else:
        parlay_name = "Close Match Special"
        parlay_description = f"Match goes 3 Sets + Over 23.5 Games + Both players 5+ Aces"
    
    st.write(f"**Same Game Parlay #{parlay_number}: {parlay_name}**")
    st.write(f"Combined bet: {parlay_description}")
    
    parlay_odds = st.text_input(
        f"Parlay #{parlay_number} Odds:",
        help="American odds for combined bet",
        key=f"tennis_parlay_{parlay_number}"
    )
    
    if parlay_odds:
        is_valid, odds_value = validate_odds_input(parlay_odds)
        if is_valid:
            return {
                'selected_bet': f"Parlay #{parlay_number}: {parlay_name}",
                'selected_odds': odds_value,
                'market_type': 'same_game_parlay'
            }
        else:
            st.error(f"Invalid parlay odds: {odds_value}")
    
    return None

def calculate_tennis_win_probability(selected_players, market_type, surface, tournament_level, ml_model):
    """Calculate tennis match win probability"""
    
    player1 = selected_players['player1']
    player2 = selected_players['player2']
    
    # Extract rankings
    try:
        p1_ranking = int(player1.split('#')[1].split(')')[0]) if '#' in player1 else 50
        p2_ranking = int(player2.split('#')[1].split(')')[0]) if '#' in player2 else 50
    except:
        p1_ranking = 50
        p2_ranking = 50
    
    # Generate mock player data
    player1_data = {
        'ranking': p1_ranking,
        'recent_form': 0.7 + random.uniform(-0.2, 0.2),
        'service_games_won': 0.85 + random.uniform(-0.1, 0.1),
        'return_games_won': 0.15 + random.uniform(-0.05, 0.05),
        'hard_win_rate': 0.75 + random.uniform(-0.15, 0.15),
        'clay_win_rate': 0.65 + random.uniform(-0.15, 0.15),
        'grass_win_rate': 0.70 + random.uniform(-0.15, 0.15)
    }
    
    player2_data = {
        'ranking': p2_ranking,
        'recent_form': 0.7 + random.uniform(-0.2, 0.2),
        'service_games_won': 0.85 + random.uniform(-0.1, 0.1),
        'return_games_won': 0.15 + random.uniform(-0.05, 0.05),
        'hard_win_rate': 0.75 + random.uniform(-0.15, 0.15),
        'clay_win_rate': 0.65 + random.uniform(-0.15, 0.15),
        'grass_win_rate': 0.70 + random.uniform(-0.15, 0.15)
    }
    
    # Match context
    match_info = {
        'surface': surface.lower().replace(' court', ''),
        'tournament_level': 3 if 'Grand Slam' in tournament_level else 
                           2 if 'Masters' in tournament_level else 1,
        'h2h_record': {'player1_wins': random.randint(0, 10), 'player2_wins': random.randint(0, 10)}
    }
    
    # Prepare features for ML model
    features = ml_model.prepare_tennis_features(player1_data, player2_data, match_info)
    
    # Get base probability
    base_probability = ml_model.predict_outcome(features)
    
    # Adjust for market type
    if market_type == "Match Winner":
        return base_probability
    elif market_type == "Set Betting":
        return 0.35  # Probability of 2-0 or 2-1 result
    elif market_type == "Total Games Over/Under":
        return 0.58  # Probability of over games
    elif market_type == "Total Aces Over/Under":
        return 0.45  # Probability of over aces
    elif market_type == "Total Double Faults Over/Under":
        return 0.40  # Probability of over double faults
    elif market_type == "Exact Number of Sets":
        return 0.65  # Probability of 2 sets vs 3 sets
    elif market_type == "Number of Tiebreaks":
        return 0.35  # Probability of specific number of tiebreaks
    elif market_type == "Service Breaks":
        return 0.55  # Probability of over breaks
    else:  # Parlays
        return 0.25  # Lower probability for combined bets
    
def generate_tennis_matches(player_name):
    """Generate mock recent tennis matches"""
    
    # Remove ranking info for opponent generation
    clean_name = player_name.split(' (')[0]
    
    opponents = [
        "Rafael Nadal", "Roger Federer", "Andy Murray", "Dominic Thiem", 
        "Alexander Zverev", "Stefanos Tsitsipas", "Daniil Medvedev",
        "Serena Williams", "Naomi Osaka", "Ashleigh Barty", "Simona Halep"
    ]
    
    # Remove self from opponents
    opponents = [opp for opp in opponents if opp != clean_name]
    
    matches = []
    surfaces = ["Hard Court", "Clay Court", "Grass Court"]
    tournaments = ["ATP Masters 1000 Miami", "French Open", "Wimbledon", "US Open", "ATP 500 Dubai"]
    
    for i in range(2):  # Last 2 matches
        opponent = random.choice(opponents)
        surface = random.choice(surfaces)
        tournament = random.choice(tournaments)
        
        # Generate realistic result
        win_prob = 0.6 if 'ATP #1' in player_name or 'WTA #1' in player_name else 0.5
        
        if random.random() < win_prob:
            result = 'W'
            result_text = 'WON'
            if random.random() < 0.6:  # 60% chance of 2-0 win
                score = f"{random.choice([6, 7])}-{random.randint(1, 6)}, {random.choice([6, 7])}-{random.randint(1, 6)}"
            else:  # 3-set win
                score = f"{random.choice([6, 7])}-{random.randint(1, 6)}, {random.randint(1, 6)}-{random.choice([6, 7])}, {random.choice([6, 7])}-{random.randint(1, 5)}"
        else:
            result = 'L'
            result_text = 'LOST'
            if random.random() < 0.6:  # 60% chance of 2-0 loss
                score = f"{random.randint(1, 6)}-{random.choice([6, 7])}, {random.randint(1, 6)}-{random.choice([6, 7])}"
            else:  # 3-set loss
                score = f"{random.choice([6, 7])}-{random.randint(1, 6)}, {random.randint(1, 6)}-{random.choice([6, 7])}, {random.randint(1, 5)}-{random.choice([6, 7])}"
        
        match_date = (datetime.now() - timedelta(days=7*(i+1))).strftime("%d %B %Y")
        
        matches.append({
            'opponent': opponent,
            'result': result,
            'result_text': result_text,
            'score': score,
            'surface': surface,
            'tournament': tournament,
            'date': match_date
        })
    
    return matches

def generate_h2h_record(player1, player2):
    """Generate head-to-head record"""
    
    p1_wins = random.randint(0, 8)
    p2_wins = random.randint(0, 8)
    
    player1_name = player1.split(' (')[0]
    player2_name = player2.split(' (')[0]
    
    if p1_wins > p2_wins:
        leader = player1_name
    elif p2_wins > p1_wins:
        leader = player2_name
    else:
        leader = "Series tied"
    
    return f"{player1_name} {p1_wins}-{p2_wins} {player2_name} ({leader} leads)" if leader != "Series tied" else f"{player1_name} {p1_wins}-{p2_wins} {player2_name} (Series tied)"

def get_surface_analysis(selected_players, surface):
    """Get surface-specific analysis"""
    
    surface_lower = surface.lower().replace(' court', '')
    
    # Mock surface performance data
    analysis = {
        'surface_name': surface,
        'player1_surface_record': f"{random.randint(15, 30)}-{random.randint(3, 10)}",
        'player2_surface_record': f"{random.randint(12, 25)}-{random.randint(5, 12)}",
        'surface_advantage': random.choice([selected_players['player1'].split(' (')[0], 
                                          selected_players['player2'].split(' (')[0], 
                                          'Even'])
    }
    
    return analysis

def get_tournament_factor(tournament_level):
    """Get tournament importance factor"""
    
    factors = {
        'Grand Slam': {'importance': 'Maximum', 'pressure': 'Very High', 'multiplier': 1.2},
        'Masters 1000': {'importance': 'High', 'pressure': 'High', 'multiplier': 1.1},
        'ATP 500': {'importance': 'Medium', 'pressure': 'Medium', 'multiplier': 1.0},
        'ATP 250': {'importance': 'Low', 'pressure': 'Low', 'multiplier': 0.9},
        'WTA 1000': {'importance': 'High', 'pressure': 'High', 'multiplier': 1.1},
        'WTA 500': {'importance': 'Medium', 'pressure': 'Medium', 'multiplier': 1.0}
    }
    
    return factors.get(tournament_level, {'importance': 'Medium', 'pressure': 'Medium', 'multiplier': 1.0})

def generate_tennis_summary(results, selected_bet, selected_players, surface):
    """Generate tennis-specific summary"""
    
    stake = results['recommended_stake']
    bankroll_percent = results['stake_percentage']
    win_prob = results['win_probability']
    edge = results['edge']
    risk = results['risk_assessment']
    
    player1_name = selected_players['player1'].split(' (')[0]
    player2_name = selected_players['player2'].split(' (')[0]
    
    if results['edge'] <= 0:
        return f"NO BET RECOMMENDED: No positive expected value detected for {selected_bet}."
    
    summary = f"Recommended bet: {bankroll_percent:.1f}% of bankroll ({format_currency(stake)}) on {selected_bet}.\n\n"
    summary += f"Key factors:\n"
    summary += f"• Match win probability: {win_prob:.1f}% (ML model)\n"
    summary += f"• Surface: {surface} court analysis included\n"
    summary += f"• Betting edge: {edge:.1f}%\n"
    summary += f"• Expected value: {format_currency(results['expected_value'])}\n"
    summary += f"• Head-to-head: Historical matchup considered\n\n"
    summary += f"Risk level: {risk} - "
    
    if risk == "HIGH RISK":
        summary += "Large stake required due to significant edge. Consider quarter Kelly for conservative approach."
    elif risk == "MEDIUM RISK":
        summary += "Moderate risk with solid value detected."
    else:
        summary += "Conservative bet with positive expected value and high confidence."
    
    return summary

def display_tennis_insights(selected_players, surface, results):
    """Display tennis-specific insights"""
    
    st.markdown("### Tennis-Specific Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Surface Analysis**")
        surface_data = get_surface_analysis(selected_players, surface)
        st.write(f"Surface: {surface_data['surface_name']}")
        st.write(f"Player 1 Record: {surface_data['player1_surface_record']}")
        st.write(f"Player 2 Record: {surface_data['player2_surface_record']}")
        st.write(f"Advantage: {surface_data['surface_advantage']}")
    
    with col2:
        st.markdown("**Confidence Factors**")
        confidence = 85 if results['edge'] > 5 else 70 if results['edge'] > 2 else 55
        st.metric("Model Confidence", f"{confidence}%")
        st.write("Based on:")
        st.write("- Recent form data")
        st.write("- Surface-specific performance")
        st.write("- Head-to-head history")
    
    with col3:
        st.markdown("**Value Rating**")
        stars = "⭐" * min(5, max(1, int(results['edge'])))
        st.write(f"Value: {stars}")
        st.write(f"Edge: {results['edge']:.1f}%")
        
        if results['edge'] > 10:
            st.success("Excellent value detected")
        elif results['edge'] > 5:
            st.info("Good value opportunity")
        else:
            st.warning("Marginal value - proceed with caution")

def display_tennis_bet_recording(results, selected_players, market_type, selected_bet, selected_odds, current_bankroll):
    """Display tennis bet recording options"""
    
    recommended_stake = results['recommended_stake']
    
    if results['edge'] <= 0:
        st.warning("No positive edge detected. Consider not placing this bet.")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Won Bet", type="primary", key="tennis_won"):
            from utils.helpers import american_to_decimal
            decimal_odds = american_to_decimal(selected_odds)
            payout = recommended_stake * decimal_odds
            profit = payout - recommended_stake
            
            new_bankroll = current_bankroll + profit
            update_bankroll(profit, 'add')
            
            bet_data = {
                'sport': 'tennis',
                'market_type': market_type,
                'player1': selected_players['player1'],
                'player2': selected_players['player2'],
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
            
            st.success(f"Tennis bet recorded as WON! Profit: {format_currency(profit)}")
            st.rerun()
    
    with col2:
        if st.button("Lost Bet", key="tennis_lost"):
            new_bankroll = current_bankroll - recommended_stake
            update_bankroll(recommended_stake, 'subtract')
            
            bet_data = {
                'sport': 'tennis',
                'market_type': market_type,
                'player1': selected_players['player1'],
                'player2': selected_players['player2'],
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
            
            st.error(f"Tennis bet recorded as LOST! Loss: {format_currency(recommended_stake)}")
            st.rerun()
    
    with col3:
        cashout_amount = st.number_input(
            "Cashout Amount:",
            min_value=0.0,
            max_value=float(recommended_stake * 5),
            step=1.0,
            key="tennis_cashout"
        )
        
        if st.button("Record Cashout", key="tennis_cashout_btn") and cashout_amount > 0:
            profit_loss = cashout_amount - recommended_stake
            new_bankroll = current_bankroll + profit_loss
            update_bankroll(profit_loss, 'add')
            
            bet_data = {
                'sport': 'tennis',
                'market_type': market_type,
                'player1': selected_players['player1'],
                'player2': selected_players['player2'],
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
            
            st.info(f"Tennis cashout recorded! Amount: {format_currency(cashout_amount)}")
            st.rerun()