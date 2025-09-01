import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from models.kelly_calculator import KellyCalculator
from models.ml_models import SportsPredictionModel
from utils.visualization import plot_bankroll_simulation
import config

def show():
    """Display the F1 bankroll simulation page"""
    
    st.markdown("""
    <div class="main-header">
        <h1>F1 Bankroll Simulation</h1>
        <p>Monte Carlo simulation of betting strategies in Formula 1 races</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize models
    kelly_calc = KellyCalculator()
    ml_model = SportsPredictionModel(sport='f1')
    
    # Simulation settings
    st.subheader("Simulation Settings")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        initial_bankroll = st.number_input(
            "Initial Bankroll ($):",
            min_value=100,
            max_value=1000000,
            value=10000,
            step=1000,
            key="f1_sim_bankroll"
        )
    
    with col2:
        num_bets = st.number_input(
            "Number of Bets:",
            min_value=10,
            max_value=1000,
            value=100,
            step=10,
            key="f1_sim_bets"
        )
    
    with col3:
        num_simulations = st.number_input(
            "Number of Simulations:",
            min_value=1,
            max_value=1000,
            value=100,
            step=10,
            key="f1_sim_sims"
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        kelly_fraction_type = st.selectbox(
            "Kelly Fraction:",
            list(config.KELLY_FRACTIONS.keys()),
            index=1,
            key="f1_sim_kelly"
        )
        kelly_modifier = config.KELLY_FRACTIONS[kelly_fraction_type]
    
    with col2:
        max_bankroll_percent = st.slider(
            "Maximum Bankroll Percentage:",
            min_value=0,
            max_value=100,
            value=70,
            step=5,
            key="f1_sim_bankroll_pct"
        ) / 100
    
    # Strategy settings
    st.subheader("Strategy Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Track type weights
        track_weights = {
            'Street': st.slider(
                "Street Circuit Weight:",
                min_value=0,
                max_value=100,
                value=30,
                step=5,
                key="f1_street_weight"
            ) / 100,
            'Traditional': st.slider(
                "Traditional Circuit Weight:",
                min_value=0,
                max_value=100,
                value=50,
                step=5,
                key="f1_traditional_weight"
            ) / 100,
            'High Speed': st.slider(
                "High Speed Circuit Weight:",
                min_value=0,
                max_value=100,
                value=20,
                step=5,
                key="f1_highspeed_weight"
            ) / 100
        }
        
        # Market type weights
        market_weights = {
            'Race Winner': st.slider(
                "Race Winner Bets:",
                min_value=0,
                max_value=100,
                value=40,
                step=5,
                key="f1_winner_weight"
            ) / 100,
            'Podium': st.slider(
                "Podium Finish Bets:",
                min_value=0,
                max_value=100,
                value=30,
                step=5,
                key="f1_podium_weight"
            ) / 100,
            'Points Finish': st.slider(
                "Points Finish Bets:",
                min_value=0,
                max_value=100,
                value=30,
                step=5,
                key="f1_points_weight"
            ) / 100
        }
    
    with col2:
        min_edge = st.slider(
            "Minimum Edge (%):",
            min_value=0,
            max_value=20,
            value=5,
            step=1,
            key="f1_min_edge"
        )
        
        min_probability = st.slider(
            "Minimum Win Probability (%):",
            min_value=0,
            max_value=100,
            value=55,
            step=5,
            key="f1_min_prob"
        ) / 100
        
        weather_impact = st.slider(
            "Weather Impact (%):",
            min_value=0,
            max_value=50,
            value=20,
            step=5,
            key="f1_weather_impact"
        ) / 100
    
    # Run simulation
    if st.button("Run F1 Bankroll Simulation", type="primary"):
        with st.spinner("Running Monte Carlo simulation..."):
            simulation_results = run_f1_simulation(
                initial_bankroll=initial_bankroll,
                num_bets=num_bets,
                num_simulations=num_simulations,
                kelly_modifier=kelly_modifier,
                max_bankroll_percent=max_bankroll_percent,
                track_weights=track_weights,
                market_weights=market_weights,
                min_edge=min_edge,
                min_probability=min_probability,
                weather_impact=weather_impact,
                kelly_calc=kelly_calc,
                ml_model=ml_model
            )
            
            # Display results
            display_simulation_results(simulation_results)

def run_f1_simulation(initial_bankroll, num_bets, num_simulations, kelly_modifier,
                     max_bankroll_percent, track_weights, market_weights, min_edge,
                     min_probability, weather_impact, kelly_calc, ml_model):
    """Run F1 betting simulation"""
    
    simulation_data = []
    successful_sims = 0
    total_bets = 0
    
    for sim in range(num_simulations):
        bankroll = initial_bankroll
        bankroll_history = [bankroll]
        bets_placed = 0
        
        # Simulate bets
        while bets_placed < num_bets and bankroll > 0:
            # Generate random race and odds
            race_data = generate_random_f1_race(track_weights, weather_impact)
            market_type = select_market_type(market_weights)
            odds = generate_random_odds(market_type)
            
            # Calculate win probability using ML model
            features = np.array(list(race_data['features'].values())).reshape(1, -1)
            win_probability = ml_model.predict_outcome(features)
            
            # Adjust probability based on weather and market type
            if race_data['weather'] == 'Rain':
                win_probability = adjust_rain_probability(win_probability, weather_impact)
            
            win_probability = adjust_market_probability(win_probability, market_type)
            
            # Check strategy conditions
            edge = kelly_calc.calculate_edge(win_probability, odds)
            
            if edge <= 0 or edge < min_edge or win_probability < min_probability:
                continue
            
            # Calculate Kelly recommendation
            results = kelly_calc.calculate_recommended_stake(
                win_probability=win_probability,
                american_odds=odds,
                bankroll=bankroll,
                kelly_modifier=kelly_modifier,
                max_bankroll_percent=max_bankroll_percent
            )
            
            stake = results['recommended_stake']
            
            # Simulate bet outcome
            win = random.random() < win_probability
            
            if win:
                from utils.helpers import american_to_decimal
                decimal_odds = american_to_decimal(odds)
                payout = stake * decimal_odds
                bankroll = bankroll - stake + payout
            else:
                bankroll = bankroll - stake
            
            bankroll_history.append(bankroll)
            bets_placed += 1
        
        # Record simulation data
        if bankroll > 0:
            successful_sims += 1
            
        simulation_data.append({
            'sim_id': sim + 1,
            'final_bankroll': bankroll,
            'bankroll_history': bankroll_history,
            'num_bets_placed': bets_placed,
            'roi': ((bankroll - initial_bankroll) / initial_bankroll) * 100
        })
        
        total_bets += bets_placed
    
    return {
        'simulations': simulation_data,
        'success_rate': successful_sims / num_simulations,
        'avg_bets_per_sim': total_bets / num_simulations
    }

def generate_random_f1_race(track_weights, weather_impact):
    """Generate random F1 race data"""
    
    # Select track type based on weights
    track_types = list(track_weights.keys())
    weights = list(track_weights.values())
    track_type = random.choices(track_types, weights=weights)[0]
    
    # Weather conditions
    if random.random() < weather_impact:
        weather = 'Rain'
    else:
        weather = random.choice(['Clear', 'Cloudy', 'Mixed'])
    
    # Teams and drivers (2023 season)
    teams = {
        'Red Bull': ['Max Verstappen', 'Sergio Perez'],
        'Ferrari': ['Charles Leclerc', 'Carlos Sainz'],
        'Mercedes': ['Lewis Hamilton', 'George Russell'],
        'McLaren': ['Lando Norris', 'Oscar Piastri'],
        'Aston Martin': ['Fernando Alonso', 'Lance Stroll'],
        'Alpine': ['Pierre Gasly', 'Esteban Ocon'],
        'Williams': ['Alex Albon', 'Logan Sargeant'],
        'AlphaTauri': ['Daniel Ricciardo', 'Yuki Tsunoda'],
        'Alfa Romeo': ['Valtteri Bottas', 'Zhou Guanyu'],
        'Haas': ['Kevin Magnussen', 'Nico Hulkenberg']
    }
    
    # Select random team and driver
    team = random.choice(list(teams.keys()))
    driver = random.choice(teams[team])
    
    # Generate random features
    features = {
        'driver': driver,
        'team': team,
        'track_type': track_type,
        'weather': weather,
        'grid_position': random.randint(1, 20),
        'car_performance': random.uniform(0.5, 1.0),
        'driver_form': random.uniform(0.5, 1.0),
        'team_reliability': random.uniform(0.8, 1.0)
    }
    
    return {
        'circuit': f"{track_type} Circuit",
        'features': features,
        'weather': weather
    }

def select_market_type(market_weights):
    """Select market type based on weights"""
    
    markets = list(market_weights.keys())
    weights = list(market_weights.values())
    return random.choices(markets, weights=weights)[0]

def generate_random_odds(market_type):
    """Generate random F1 odds based on market type"""
    
    if market_type == 'Race Winner':
        # Race winner odds tend to be more extreme
        if random.random() < 0.3:  # Top team/driver
            return random.choice([-250, -200, -150])
        elif random.random() < 0.6:  # Mid-field
            return random.choice([200, 300, 400])
        else:  # Longshots
            return random.choice([500, 750, 1000])
    
    elif market_type == 'Podium':
        # Podium finish odds are more moderate
        if random.random() < 0.4:
            return random.choice([-150, -120, 120, 150])
        else:
            return random.choice([200, 250, 300])
    
    else:  # Points finish
        # Points finish odds are tighter
        if random.random() < 0.5:
            return random.choice([-130, -110, 110, 130])
        else:
            return random.choice([150, 180, 200])

def adjust_rain_probability(base_probability, weather_impact):
    """Adjust probability for rain conditions"""
    
    # Rain increases variability
    variance = weather_impact / 2
    adjustment = random.uniform(-variance, variance)
    return max(0.1, min(0.9, base_probability + adjustment))

def adjust_market_probability(base_probability, market_type):
    """Adjust probability based on market type"""
    
    if market_type == 'Podium':
        # Higher probability for podium vs race win
        return min(0.9, base_probability * 1.3)
    elif market_type == 'Points Finish':
        # Even higher for points finish
        return min(0.9, base_probability * 1.5)
    else:
        return base_probability

def display_simulation_results(results):
    """Display F1 simulation results"""
    
    simulations = results['simulations']
    
    # Summary metrics
    final_bankrolls = [sim['final_bankroll'] for sim in simulations]
    rois = [sim['roi'] for sim in simulations]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Success Rate",
            f"{results['success_rate']:.1%}",
            help="Percentage of simulations ending with positive bankroll"
        )
    
    with col2:
        st.metric(
            "Average ROI",
            f"{np.mean(rois):.1f}%",
            help="Average return on investment across all simulations"
        )
    
    with col3:
        st.metric(
            "Best Case ROI",
            f"{max(rois):.1f}%",
            help="Highest ROI achieved in simulations"
        )
    
    with col4:
        st.metric(
            "Worst Case ROI",
            f"{min(rois):.1f}%",
            help="Lowest ROI in simulations"
        )
    
    # Bankroll paths plot
    st.subheader("Bankroll Evolution")
    plot_bankroll_simulation(simulations)
    
    # Distribution table
    st.subheader("Results Distribution")
    
    distribution_df = pd.DataFrame({
        'Metric': [
            'Final Bankroll (Mean)',
            'Final Bankroll (Median)',
            'Final Bankroll (95th Percentile)',
            'Final Bankroll (5th Percentile)',
            'ROI (Mean)',
            'ROI (Standard Deviation)',
            'Average Bets per Simulation'
        ],
        'Value': [
            f"{np.mean(final_bankrolls):.2f}",
            f"{np.median(final_bankrolls):.2f}",
            f"{np.percentile(final_bankrolls, 95):.2f}",
            f"{np.percentile(final_bankrolls, 5):.2f}",
            f"{np.mean(rois):.1f}%",
            f"{np.std(rois):.1f}%",
            f"{results['avg_bets_per_sim']:.1f}"
        ]
    })
    
    st.dataframe(
        distribution_df,
        hide_index=True,
        column_config={
            "Metric": "Metric",
            "Value": st.column_config.NumberColumn("Value")
        }
    )