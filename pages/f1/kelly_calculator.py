import streamlit as st
import random
from datetime import datetime, timedelta
from models.kelly_calculator import KellyCalculator
from models.ml_models import SportsPredictionModel
from utils.helpers import (format_currency, validate_odds_input, display_kelly_results, 
                          update_bankroll, record_bet)
import config

def show():
    """Display the F1 Kelly criterion calculator page"""
    
    st.markdown("""
    <div class="main-header">
        <h1>Formula 1 Kelly Criterion Calculator</h1>
        <p>Circuit-specific analysis for F1 race betting with driver performance models</p>
    </div>
    """, unsafe_allow_html=True)
    
    current_bankroll = st.session_state.get('bankroll', config.DEFAULT_BANKROLL)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div class="bankroll-display">
            <h2>Current Bankroll: {format_currency(current_bankroll)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    kelly_calc = KellyCalculator()
    ml_model = SportsPredictionModel(sport='f1')
    
    # Step 1: Race Type Selection
    st.subheader("1. Race Type Selection")
    race_type = st.radio(
        "Select race type:",
        ["Grand Prix (Race)", "Sprint Race", "Qualifying Session"],
        key="f1_race_type"
    )
    
    # Step 2: Driver Selection
    st.subheader("2. Driver Selection")
    selected_drivers = select_f1_drivers()
    
    if not selected_drivers:
        st.info("Please select drivers to continue.")
        return
    
    # Step 3: Circuit Information
    st.subheader("3. Circuit Information")
    circuit_info = display_f1_circuit_info(selected_drivers)
    
    # Step 4: Display Driver Information
    st.subheader("4. Driver Performance Analysis")
    display_f1_driver_info(selected_drivers, circuit_info)
    
    # Step 5: Market Selection
    st.subheader("5. Market Type Selection")
    market_type = st.selectbox(
        "Select F1 betting market:",
        config.F1_MARKET_TYPES,
        key="f1_market"
    )
    
    # Step 6: Odds Input
    st.subheader("6. Odds Input")
    odds_data = collect_f1_odds_input(market_type, selected_drivers, race_type)
    
    if not odds_data:
        st.info("Please enter odds to continue.")
        return
    
    # Step 7: Kelly Settings
    st.subheader("7. Kelly Calculation Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        kelly_fraction_type = st.selectbox(
            "Kelly Fraction:",
            list(config.KELLY_FRACTIONS.keys()),
            index=1,
            key="f1_kelly_fraction"
        )
        kelly_modifier = config.KELLY_FRACTIONS[kelly_fraction_type]
    
    with col2:
        max_bankroll_percent = st.slider(
            "Maximum Bankroll Percentage:",
            min_value=0,
            max_value=100,
            value=70,
            step=5,
            key="f1_max_bankroll"
        ) / 100
    
    # Step 8: Calculate Results
    if st.button("Calculate F1 Kelly Analysis", type="primary"):
        with st.spinner("Analyzing F1 race probabilities..."):
            
            win_probability = calculate_f1_win_probability(
                selected_drivers, market_type, race_type, circuit_info, ml_model
            )
            
            selected_bet = odds_data['selected_bet']
            selected_odds = odds_data['selected_odds']
            
            results = kelly_calc.calculate_recommended_stake(
                win_probability=win_probability,
                american_odds=selected_odds,
                bankroll=current_bankroll,
                kelly_modifier=kelly_modifier,
                max_bankroll_percent=max_bankroll_percent
            )
            
            summary = generate_f1_summary(results, selected_bet, selected_drivers, circuit_info, race_type)
            results['summary'] = summary
            
            display_kelly_results(results)
            display_f1_insights(selected_drivers, circuit_info, race_type, results)
            
            # Step 9: Bet Recording
            st.subheader("9. Record Bet")
            display_f1_bet_recording(results, selected_drivers, market_type, 
                                   selected_bet, selected_odds, current_bankroll)

def select_f1_drivers():
    """Select F1 drivers for comparison"""
    
    drivers = config.F1_DRIVERS
    
    col1, col2 = st.columns(2)
    
    with col1:
        driver1 = st.selectbox(
            "Driver 1:",
            [""] + drivers,
            key="f1_driver1"
        )
    
    with col2:
        driver2_options = [d for d in drivers if d != driver1]
        driver2 = st.selectbox(
            "Driver 2:",
            [""] + driver2_options,
            key="f1_driver2"
        )
    
    if driver1 and driver2:
        return {
            'driver1': driver1,
            'driver2': driver2
        }
    
    return None

def display_f1_circuit_info(selected_drivers):
    """Display and collect F1 circuit information"""
    
    circuit = st.selectbox(
        "Upcoming Circuit:",
        config.F1_CIRCUITS,
        index=6,  # Monaco Circuit as default
        key="f1_circuit"
    )
    
    # Circuit characteristics
    circuit_data = get_circuit_characteristics(circuit)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Circuit Type**")
        st.write(f"Type: {circuit_data['type']}")
        st.write(f"Length: {circuit_data['length']}")
        st.write(f"Laps: {circuit_data['laps']}")
    
    with col2:
        st.markdown("**Key Characteristics**")
        st.write(f"Overtaking: {circuit_data['overtaking']}")
        st.write(f"DRS Zones: {circuit_data['drs_zones']}")
        st.write(f"Tire Strategy: {circuit_data['tire_strategy']}")
    
    with col3:
        st.markdown("**Weather Forecast**")
        st.write(f"Condition: {circuit_data['weather']}")
        st.write(f"Temperature: {circuit_data['temperature']}")
        st.write(f"Rain Chance: {circuit_data['rain_chance']}")
    
    return {
        'circuit': circuit,
        'characteristics': circuit_data
    }

def display_f1_driver_info(selected_drivers, circuit_info):
    """Display F1 driver performance information"""
    
    driver1_name = selected_drivers['driver1'].split(' (')[0]
    driver2_name = selected_drivers['driver2'].split(' (')[0]
    
    # Generate recent race results
    driver1_races = generate_f1_races(driver1_name)
    driver2_races = generate_f1_races(driver2_name)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**{driver1_name} - Recent Races:**")
        for i, race in enumerate(driver1_races, 1):
            position_icon = get_f1_position_icon(race['position'])
            st.markdown(f"""
            <div class="match-result match-{'win' if race['position'] <= 3 else 'loss'}">
                Race {i}: {position_icon} {race['position_text']} - {race['race_name']}<br>
                Qualifying: P{race['qualifying_pos']} ({race['qualifying_time']})<br>
                Race Result: {race['result_details']}<br>
                Circuit: {race['circuit']}<br>
                Date: {race['date']}
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"**{driver2_name} - Recent Races:**")
        for i, race in enumerate(driver2_races, 1):
            position_icon = get_f1_position_icon(race['position'])
            st.markdown(f"""
            <div class="match-result match-{'win' if race['position'] <= 3 else 'loss'}">
                Race {i}: {position_icon} {race['position_text']} - {race['race_name']}<br>
                Qualifying: P{race['qualifying_pos']} ({race['qualifying_time']})<br>
                Race Result: {race['result_details']}<br>
                Circuit: {race['circuit']}<br>
                Date: {race['date']}
            </div>
            """, unsafe_allow_html=True)
    
    # Head-to-head record
    h2h = generate_f1_h2h(driver1_name, driver2_name, circuit_info['circuit'])
    st.markdown(f"**Head-to-Head (Last 10 races):** {h2h}")
    
    # Circuit-specific performance
    st.markdown("**Circuit-Specific Performance:**")
    display_f1_circuit_performance(driver1_name, driver2_name, circuit_info)

def collect_f1_odds_input(market_type, selected_drivers, race_type):
    """Collect odds for F1 markets"""
    
    driver1_name = selected_drivers['driver1'].split(' (')[0]
    driver2_name = selected_drivers['driver2'].split(' (')[0]
    
    if market_type == "Race Winner":
        return collect_f1_race_winner_odds()
    elif market_type == "Podium Finish":
        return collect_f1_podium_odds(driver1_name, driver2_name)
    elif market_type == "Head-to-Head Battle":
        return collect_f1_h2h_odds(driver1_name, driver2_name)
    elif market_type == "Qualifying Position":
        return collect_f1_qualifying_odds(driver1_name, driver2_name)
    elif market_type == "Points Finish":
        return collect_f1_points_odds(driver1_name, driver2_name)
    elif market_type == "Fastest Lap":
        return collect_f1_fastest_lap_odds()
    elif market_type == "Same Race Parlay":
        return collect_f1_parlay_odds(driver1_name, driver2_name)
    
    return None

def collect_f1_race_winner_odds():
    """Collect race winner odds for multiple drivers"""
    
    st.write("**Race Winner Market:**")
    
    top_drivers = [
        "Max Verstappen", "Lewis Hamilton", "Charles Leclerc", 
        "Lando Norris", "George Russell", "Carlos Sainz"
    ]
    
    driver_odds = {}
    
    for driver in top_drivers:
        odds_input = st.text_input(
            f"{driver}:",
            key=f"race_winner_{driver.replace(' ', '_')}"
        )
        if odds_input:
            is_valid, odds_value = validate_odds_input(odds_input)
            if is_valid:
                driver_odds[driver] = odds_value
    
    if driver_odds:
        selected_driver = st.selectbox(
            "Select driver to bet on:",
            list(driver_odds.keys()),
            key="f1_race_winner_selection"
        )
        
        return {
            'selected_bet': f"{selected_driver} to Win Race",
            'selected_odds': driver_odds[selected_driver],
            'market_type': 'race_winner'
        }
    
    return None

def collect_f1_h2h_odds(driver1, driver2):
    """Collect head-to-head battle odds"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        driver1_odds = st.text_input(
            f"{driver1} beats {driver2}:",
            key="f1_h2h_driver1"
        )
    
    with col2:
        driver2_odds = st.text_input(
            f"{driver2} beats {driver1}:",
            key="f1_h2h_driver2"
        )
    
    valid_bets = []
    
    if driver1_odds:
        is_valid, odds_value = validate_odds_input(driver1_odds)
        if is_valid:
            valid_bets.append((f"{driver1} beats {driver2}", odds_value))
    
    if driver2_odds:
        is_valid, odds_value = validate_odds_input(driver2_odds)
        if is_valid:
            valid_bets.append((f"{driver2} beats {driver1}", odds_value))
    
    if valid_bets:
        selected_bet_option = st.selectbox(
            "Select H2H bet:",
            [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets],
            key="f1_h2h_selection"
        )
        
        selected_index = [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets].index(selected_bet_option)
        selected_bet, selected_odds = valid_bets[selected_index]
        
        return {
            'selected_bet': selected_bet,
            'selected_odds': selected_odds,
            'market_type': 'head_to_head'
        }
    
    return None

def collect_f1_podium_odds(driver1, driver2):
    """Collect podium finish odds"""
    
    selected_driver = st.selectbox(
        "Select driver for podium bet:",
        [driver1, driver2],
        key="f1_podium_driver"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        podium_yes = st.text_input(f"{selected_driver} to finish Top 3:", key="podium_yes")
    
    with col2:
        podium_no = st.text_input(f"{selected_driver} NOT to finish Top 3:", key="podium_no")
    
    valid_bets = []
    
    if podium_yes:
        is_valid, odds_value = validate_odds_input(podium_yes)
        if is_valid:
            valid_bets.append((f"{selected_driver} Top 3 Finish", odds_value))
    
    if podium_no:
        is_valid, odds_value = validate_odds_input(podium_no)
        if is_valid:
            valid_bets.append((f"{selected_driver} NOT Top 3", odds_value))
    
    if valid_bets:
        selected_bet_option = st.selectbox(
            "Select podium bet:",
            [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets],
            key="f1_podium_selection"
        )
        
        selected_index = [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets].index(selected_bet_option)
        selected_bet, selected_odds = valid_bets[selected_index]
        
        return {
            'selected_bet': selected_bet,
            'selected_odds': selected_odds,
            'market_type': 'podium_finish'
        }
    
    return None

def collect_f1_qualifying_odds(driver1, driver2):
    """Collect qualifying position odds"""
    
    selected_driver = st.selectbox(
        "Select driver for qualifying bet:",
        [driver1, driver2],
        key="f1_quali_driver"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        quali_top3 = st.text_input(f"{selected_driver} Top 3 Qualifying:", key="quali_top3")
    
    with col2:
        quali_not_top3 = st.text_input(f"{selected_driver} NOT Top 3 Qualifying:", key="quali_not_top3")
    
    valid_bets = []
    
    if quali_top3:
        is_valid, odds_value = validate_odds_input(quali_top3)
        if is_valid:
            valid_bets.append((f"{selected_driver} Top 3 Qualifying", odds_value))
    
    if quali_not_top3:
        is_valid, odds_value = validate_odds_input(quali_not_top3)
        if is_valid:
            valid_bets.append((f"{selected_driver} NOT Top 3 Qualifying", odds_value))
    
    if valid_bets:
        selected_bet_option = st.selectbox(
            "Select qualifying bet:",
            [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets],
            key="f1_quali_selection"
        )
        
        selected_index = [f"{bet[0]} ({'+' if bet[1] > 0 else ''}{bet[1]})" for bet in valid_bets].index(selected_bet_option)
        selected_bet, selected_odds = valid_bets[selected_index]
        
        return {
            'selected_bet': selected_bet,
            'selected_odds': selected_odds,
            'market_type': 'qualifying_position'
        }
    
    return None

def collect_f1_fastest_lap_odds():
    """Collect fastest lap odds"""
    
    st.write("**Fastest Lap Market:**")
    
    top_drivers = ["Max Verstappen", "Lewis Hamilton", "Charles Leclerc", "Lando Norris"]
    
    driver_odds = {}
    
    for driver in top_drivers:
        odds_input = st.text_input(
            f"{driver} Fastest Lap:",
            key=f"fastest_lap_{driver.replace(' ', '_')}"
        )
        if odds_input:
            is_valid, odds_value = validate_odds_input(odds_input)
            if is_valid:
                driver_odds[driver] = odds_value
    
    # Any other driver option
    other_odds = st.text_input("Any Other Driver:", key="fastest_lap_other")
    if other_odds:
        is_valid, odds_value = validate_odds_input(other_odds)
        if is_valid:
            driver_odds["Any Other Driver"] = odds_value
    
    if driver_odds:
        selected_driver = st.selectbox(
            "Select fastest lap bet:",
            list(driver_odds.keys()),
            key="f1_fastest_lap_selection"
        )
        
        return {
            'selected_bet': f"{selected_driver} Fastest Lap",
            'selected_odds': driver_odds[selected_driver],
            'market_type': 'fastest_lap'
        }
    
    return None

def collect_f1_parlay_odds(driver1, driver2):
    """Collect same race parlay odds"""
    
    parlay_options = [
        f"{driver1} Win + {driver1} Pole + {driver1} Fastest Lap",
        f"{driver2} Win + {driver2} Podium + Points Finish",
        f"Both drivers finish + Combined Top 6"
    ]
    
    selected_parlay = st.selectbox(
        "Select parlay combination:",
        parlay_options,
        key="f1_parlay_type"
    )
    
    parlay_odds = st.text_input(
        "Same Race Parlay Odds:",
        help="American odds for combined bet",
        key="f1_parlay_odds"
    )
    
    if parlay_odds:
        is_valid, odds_value = validate_odds_input(parlay_odds)
        if is_valid:
            return {
                'selected_bet': f"F1 Parlay: {selected_parlay}",
                'selected_odds': odds_value,
                'market_type': 'same_race_parlay'
            }
    
    return None

def generate_f1_races(driver_name):
    """Generate mock F1 race results"""
    
    circuits = ["Albert Park Circuit", "Jeddah Corniche Circuit", "Bahrain International Circuit"]
    races = []
    
    # Driver performance tiers
    top_tier = ["Max Verstappen", "Lewis Hamilton", "Charles Leclerc"]
    mid_tier = ["Lando Norris", "George Russell", "Carlos Sainz"]
    
    for i in range(2):
        circuit = random.choice(circuits)
        race_name = f"{circuit.split()[0]} GP"
        
        # Generate realistic positions based on driver tier
        if driver_name in top_tier:
            position = random.choices([1, 2, 3, 4, 5], weights=[40, 25, 20, 10, 5])[0]
        elif driver_name in mid_tier:
            position = random.choices([3, 4, 5, 6, 7, 8], weights=[15, 25, 25, 20, 10, 5])[0]
        else:
            position = random.choices([6, 7, 8, 9, 10, 11], weights=[10, 20, 25, 25, 15, 5])[0]
        
        qualifying_pos = max(1, position + random.randint(-2, 3))
        
        # Generate times and results
        base_time = 76.5 + random.uniform(-0.5, 0.5)
        quali_time = f"{int(base_time//60)}:{base_time%60:05.3f}"
        
        if position == 1:
            result_details = f"Winner (+{random.uniform(5, 25):.3f}s ahead)"
        else:
            gap = random.uniform(0.2, 45)
            result_details = f"{get_position_suffix(position)} (+{gap:.3f}s behind)"
        
        race_date = (datetime.now() - timedelta(days=14*(i+1))).strftime("%d %B %Y")
        
        races.append({
            'position': position,
            'position_text': f"{get_position_suffix(position)} Place",
            'race_name': race_name,
            'qualifying_pos': qualifying_pos,
            'qualifying_time': quali_time,
            'result_details': result_details,
            'circuit': circuit,
            'date': race_date
        })
    
    return races

def get_f1_position_icon(position):
    """Get icon for F1 position"""
    if position == 1:
        return "🏆"
    elif position == 2:
        return "🥈"
    elif position == 3:
        return "🥉"
    elif position <= 6:
        return "📈"
    else:
        return "📉"

def get_position_suffix(position):
    """Get position suffix (1st, 2nd, etc.)"""
    if position in [11, 12, 13]:
        return f"{position}th"
    elif position % 10 == 1:
        return f"{position}st"
    elif position % 10 == 2:
        return f"{position}nd"
    elif position % 10 == 3:
        return f"{position}rd"
    else:
        return f"{position}th"

def get_circuit_characteristics(circuit_name):
    """Get characteristics for F1 circuit"""
    
    circuit_data = {
        'Monaco Circuit': {
            'type': 'Street Circuit',
            'length': '3.337 km',
            'laps': '78 laps',
            'overtaking': 'Extremely Difficult',
            'drs_zones': '1 zone',
            'tire_strategy': 'Low degradation',
            'weather': 'Sunny',
            'temperature': '22°C',
            'rain_chance': '0%'
        },
        'Albert Park Circuit': {
            'type': 'Permanent Circuit',
            'length': '5.278 km', 
            'laps': '58 laps',
            'overtaking': 'Moderate',
            'drs_zones': '3 zones',
            'tire_strategy': 'Medium degradation',
            'weather': 'Partly Cloudy',
            'temperature': '26°C',
            'rain_chance': '15%'
        },
        'Silverstone Circuit': {
            'type': 'Permanent Circuit',
            'length': '5.891 km',
            'laps': '52 laps', 
            'overtaking': 'High',
            'drs_zones': '2 zones',
            'tire_strategy': 'High degradation',
            'weather': 'Variable',
            'temperature': '18°C',
            'rain_chance': '40%'
        }
    }
    
    return circuit_data.get(circuit_name, {
        'type': 'Mixed Circuit',
        'length': '4.5 km',
        'laps': '60 laps',
        'overtaking': 'Moderate',
        'drs_zones': '2 zones',
        'tire_strategy': 'Medium degradation',
        'weather': 'Clear',
        'temperature': '25°C',
        'rain_chance': '10%'
    })

def display_f1_circuit_performance(driver1, driver2, circuit_info):
    """Display circuit-specific driver performance"""
    
    circuit = circuit_info['circuit']
    
    # Mock circuit-specific stats
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**{driver1} at {circuit}:**")
        d1_wins = random.randint(0, 3)
        d1_podiums = random.randint(d1_wins, 5)
        st.write(f"Wins: {d1_wins}, Podiums: {d1_podiums}")
        st.write(f"Average finish: P{random.uniform(2.0, 8.0):.1f}")
        st.write(f"Best result: P{random.randint(1, 3)}")
    
    with col2:
        st.markdown(f"**{driver2} at {circuit}:**")
        d2_wins = random.randint(0, 4)
        d2_podiums = random.randint(d2_wins, 6)
        st.write(f"Wins: {d2_wins}, Podiums: {d2_podiums}")
        st.write(f"Average finish: P{random.uniform(3.0, 10.0):.1f}")
        st.write(f"Best result: P{random.randint(1, 4)}")
    
    # Circuit advantage
    if d1_podiums > d2_podiums:
        advantage = f"{driver1} (+{((d1_podiums - d2_podiums) / 5 * 15):.0f}% advantage)"
    elif d2_podiums > d1_podiums:
        advantage = f"{driver2} (+{((d2_podiums - d1_podiums) / 5 * 15):.0f}% advantage)"
    else:
        advantage = "Even performance history"
    
    st.write(f"**Circuit Advantage:** {advantage}")

def generate_f1_h2h(driver1, driver2, circuit):
    """Generate F1 head-to-head record"""
    
    driver1_better = random.randint(3, 7)
    driver2_better = 10 - driver1_better
    
    if driver1_better > driver2_better:
        leader = f"{driver1} leads"
    elif driver2_better > driver1_better:
        leader = f"{driver2} leads"
    else:
        leader = "Even"
    
    return f"{driver1} {driver1_better}-{driver2_better} {driver2} ({leader})"

def calculate_f1_win_probability(selected_drivers, market_type, race_type, circuit_info, ml_model):
    """Calculate F1 win probability"""
    
    driver1_name = selected_drivers['driver1']
    driver2_name = selected_drivers['driver2']
    
    # Mock driver data
    driver1_data = generate_f1_driver_data(driver1_name)
    driver2_data = generate_f1_driver_data(driver2_name)
    
    race_info = {
        'circuit_type': get_circuit_type(circuit_info['circuit']),
        'qualifying_advantage': 'driver1' if random.random() > 0.5 else 'driver2',
        'overtaking_difficulty': get_overtaking_difficulty(circuit_info['circuit'])
    }
    
    features = ml_model.prepare_f1_features(driver1_data, driver2_data, race_info)
    base_probability = ml_model.predict_outcome(features)
    
    # Adjust for market type
    if market_type == "Race Winner":
        return base_probability * 0.3  # Adjusted for field of 20 drivers
    elif market_type == "Podium Finish":
        return base_probability * 0.7  # Higher chance of top 3
    elif market_type == "Head-to-Head Battle":
        return base_probability
    elif market_type == "Points Finish":
        return base_probability * 0.9  # High chance of top 10
    elif market_type == "Qualifying Position":
        return base_probability * 0.6  # Top 3 qualifying
    elif market_type == "Fastest Lap":
        return 0.15  # 15% chance for specific driver
    else:  # Parlay
        return 0.08  # 8% for combined outcomes
    
def generate_f1_driver_data(driver_name):
    """Generate mock F1 driver data"""
    
    # Driver tier system for realistic stats
    top_tier = ["Max Verstappen", "Lewis Hamilton", "Charles Leclerc"]
    mid_tier = ["Lando Norris", "George Russell", "Carlos Sainz"]
    
    if any(name in driver_name for name in top_tier):
        base_stats = {
            'championship_position': random.randint(1, 3),
            'points': random.randint(150, 300),
            'avg_finish_position': random.uniform(2.0, 5.0),
            'podium_rate': random.uniform(0.6, 0.9),
            'team_points': random.randint(300, 500),
            'car_pace_ranking': random.randint(1, 3)
        }
    elif any(name in driver_name for name in mid_tier):
        base_stats = {
            'championship_position': random.randint(4, 8),
            'points': random.randint(80, 180),
            'avg_finish_position': random.uniform(5.0, 8.0),
            'podium_rate': random.uniform(0.3, 0.6),
            'team_points': random.randint(150, 300),
            'car_pace_ranking': random.randint(3, 6)
        }
    else:
        base_stats = {
            'championship_position': random.randint(9, 20),
            'points': random.randint(10, 80),
            'avg_finish_position': random.uniform(8.0, 15.0),
            'podium_rate': random.uniform(0.0, 0.3),
            'team_points': random.randint(20, 150),
            'car_pace_ranking': random.randint(6, 10)
        }
    
    # Add circuit-specific performance
    base_stats.update({
        'street_performance': random.uniform(0.3, 0.8),
        'high_speed_performance': random.uniform(0.4, 0.9),
        'technical_performance': random.uniform(0.4, 0.8)
    })
    
    return base_stats

def get_circuit_type(circuit_name):
    """Categorize circuit type"""
    
    street_circuits = ['Monaco Circuit', 'Jeddah Corniche Circuit', 'Baku City Circuit']
    high_speed = ['Monza Circuit', 'Spa-Francorchamps', 'Silverstone Circuit']
    technical = ['Hungaroring', 'Suzuka Circuit', 'Circuit de Barcelona-Catalunya']
    
    if circuit_name in street_circuits:
        return 'street'
    elif circuit_name in high_speed:
        return 'high_speed'
    elif circuit_name in technical:
        return 'technical'
    else:
        return 'mixed'

def get_overtaking_difficulty(circuit_name):
    """Get overtaking difficulty score (1-10)"""
    
    difficulty_map = {
        'Monaco Circuit': 10,
        'Hungaroring': 9,
        'Zandvoort Circuit': 8,
        'Albert Park Circuit': 6,
        'Silverstone Circuit': 4,
        'Monza Circuit': 2
    }
    
    return difficulty_map.get(circuit_name, 5)  # Default medium difficulty

def generate_f1_summary(results, selected_bet, selected_drivers, circuit_info, race_type):
    """Generate F1-specific summary"""
    
    if results['edge'] <= 0:
        return f"NO BET RECOMMENDED: No positive expected value for {selected_bet} at {circuit_info['circuit']}."
    
    driver1_name = selected_drivers['driver1'].split(' (')[0]
    driver2_name = selected_drivers['driver2'].split(' (')[0]
    circuit = circuit_info['circuit']
    
    summary = f"Recommended bet: {results['stake_percentage']:.1f}% of bankroll ({format_currency(results['recommended_stake'])}) on {selected_bet}.\n\n"
    summary += f"Key factors:\n"
    summary += f"• {race_type} win probability: {results['win_probability']:.1f}%\n"
    summary += f"• Circuit: {circuit} ({circuit_info['characteristics']['type']})\n"
    summary += f"• Overtaking difficulty: {circuit_info['characteristics']['overtaking']}\n"
    summary += f"• Weather conditions: {circuit_info['characteristics']['weather']}\n"
    summary += f"• Betting edge: {results['edge']:.1f}%\n"
    summary += f"• Expected value: {format_currency(results['expected_value'])}\n\n"
    
    summary += f"Risk level: {results['risk_assessment']} - "
    
    if results['risk_assessment'] == "HIGH RISK":
        summary += "F1 races are unpredictable. Large edge detected but consider quarter Kelly due to variance."
    elif results['risk_assessment'] == "MEDIUM RISK":
        summary += "Solid F1 betting opportunity with manageable risk."
    else:
        summary += "Conservative F1 bet with positive expected value."
    
    return summary

def display_f1_insights(selected_drivers, circuit_info, race_type, results):
    """Display F1-specific insights"""
    
    st.markdown("### Formula 1 Race Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Circuit Analysis**")
        circuit_char = circuit_info['characteristics']
        st.write(f"Circuit: {circuit_info['circuit']}")
        st.write(f"Type: {circuit_char['type']}")
        st.write(f"Overtaking: {circuit_char['overtaking']}")
        st.write(f"Strategy: {circuit_char['tire_strategy']}")
    
    with col2:
        st.markdown("**Weather Impact**")
        st.write(f"Condition: {circuit_char['weather']}")
        st.write(f"Temperature: {circuit_char['temperature']}")
        st.write(f"Rain chance: {circuit_char['rain_chance']}")
        
        if "Rain" in circuit_char['rain_chance'] or int(circuit_char['rain_chance'].replace('%', '')) > 30:
            st.warning("Weather variable - increases outcome variance")
    
    with col3:
        st.markdown("**Value Assessment**")
        confidence = 75 if results['edge'] > 5 else 60 if results['edge'] > 2 else 45
        st.metric("Model Confidence", f"{confidence}%")
        
        edge = results['edge']
        if edge > 8:
            st.success("Strong F1 value")
        elif edge > 3:
            st.info("Decent F1 value")
        else:
            st.warning("Marginal F1 value")

def display_f1_bet_recording(results, selected_drivers, market_type, selected_bet, selected_odds, current_bankroll):
    """Display F1 bet recording options"""
    
    recommended_stake = results['recommended_stake']
    
    if results['edge'] <= 0:
        st.warning("No positive edge detected for this F1 bet.")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Won Bet", type="primary", key="f1_won"):
            from utils.helpers import american_to_decimal
            decimal_odds = american_to_decimal(selected_odds)
            payout = recommended_stake * decimal_odds
            profit = payout - recommended_stake
            
            new_bankroll = current_bankroll + profit
            update_bankroll(profit, 'add')
            
            bet_data = {
                'sport': 'f1',
                'market_type': market_type,
                'team1': selected_drivers['driver1'],
                'team2': selected_drivers['driver2'],
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
            
            st.success(f"F1 bet recorded as WON! Profit: {format_currency(profit)}")
            st.rerun()
    
    with col2:
        if st.button("Lost Bet", key="f1_lost"):
            new_bankroll = current_bankroll - recommended_stake
            update_bankroll(recommended_stake, 'subtract')
            
            bet_data = {
                'sport': 'f1',
                'market_type': market_type,
                'team1': selected_drivers['driver1'],
                'team2': selected_drivers['driver2'],
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
            
            st.error(f"F1 bet recorded as LOST! Loss: {format_currency(recommended_stake)}")
            st.rerun()
    
    with col3:
        cashout_amount = st.number_input(
            "Cashout Amount:",
            min_value=0.0,
            max_value=float(recommended_stake * 10),
            step=1.0,
            key="f1_cashout"
        )
        
        if st.button("Record Cashout", key="f1_cashout_btn") and cashout_amount > 0:
            profit_loss = cashout_amount - recommended_stake
            new_bankroll = current_bankroll + profit_loss
            update_bankroll(profit_loss, 'add')
            
            bet_data = {
                'sport': 'f1',
                'market_type': market_type,
                'team1': selected_drivers['driver1'],
                'team2': selected_drivers['driver2'],
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
            
            st.info(f"F1 cashout recorded! Amount: {format_currency(cashout_amount)}")
            st.rerun()