import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from models.kelly_calculator import KellyCalculator
from utils.visualization import plot_bankroll_simulation
from models.ml_models import SportsPredictionModel
from utils.helpers import format_currency
import config

def show():
    """Display the soccer bankroll simulation page"""
    
    st.markdown("""
    <div class="main-header">
        <h1>Soccer Bankroll Simulation</h1>
        <p>Monte Carlo simulation of betting strategies in soccer matches</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize models
    kelly_calc = KellyCalculator()
    ml_model = SportsPredictionModel(sport='soccer')
    
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
            key="sim_init_bankroll"
        )
    
    with col2:
        num_bets = st.number_input(
            "Number of Bets:",
            min_value=10,
            max_value=1000,
            value=100,
            step=10,
            key="sim_num_bets"
        )
    
    with col3:
        num_simulations = st.number_input(
            "Number of Simulations:",
            min_value=1,
            max_value=1000,
            value=100,
            step=10,
            key="sim_num_sims"
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        kelly_fraction_type = st.selectbox(
            "Kelly Fraction:",
            list(config.KELLY_FRACTIONS.keys()),
            index=1,
            key="sim_kelly_fraction"
        )
        kelly_modifier = config.KELLY_FRACTIONS[kelly_fraction_type]
    
    with col2:
        max_bankroll_percent = st.slider(
            "Maximum Bankroll Percentage:",
            min_value=0,
            max_value=100,
            value=80,
            step=5,
            key="sim_max_bankroll"
        ) / 100
    
    # Strategy settings
    st.subheader("Strategy Settings")
    
    betting_strategies = {
        "Kelly Only Positive EV": "Only place bets with positive expected value",
        "Kelly with Min Edge": "Only bet when edge is above minimum threshold",
        "Kelly with Min Probability": "Only bet when win probability is above threshold"
    }
    
    strategy = st.selectbox(
        "Select betting strategy:",
        list(betting_strategies.keys()),
        help="Choose a betting strategy to simulate",
        key="sim_strategy"
    )
    
    if strategy == "Kelly with Min Edge":
        min_edge = st.slider(
            "Minimum Edge (%):",
            min_value=0,
            max_value=20,
            value=5,
            step=1,
            key="sim_min_edge"
        )
    else:
        min_edge = 0
    
    if strategy == "Kelly with Min Probability":
        min_probability = st.slider(
            "Minimum Win Probability (%):",
            min_value=0,
            max_value=100,
            value=55,
            step=5,
            key="sim_min_prob"
        ) / 100
    else:
        min_probability = 0
    
    # Run simulation
    if st.button("Run Soccer Bankroll Simulation", type="primary"):
        with st.spinner("Running Monte Carlo simulation..."):
            simulation_results = run_soccer_simulation(
                initial_bankroll=initial_bankroll,
                num_bets=num_bets,
                num_simulations=num_simulations,
                kelly_modifier=kelly_modifier,
                max_bankroll_percent=max_bankroll_percent,
                min_edge=min_edge,
                min_probability=min_probability,
                kelly_calc=kelly_calc,
                ml_model=ml_model
            )
            
            # Display results
            display_simulation_results(simulation_results)

def run_soccer_simulation(initial_bankroll, num_bets, num_simulations, kelly_modifier,
                        max_bankroll_percent, min_edge, min_probability, kelly_calc, ml_model):
    """Run soccer betting simulation"""
    
    simulation_data = []
    successful_sims = 0
    total_bets = 0
    
    for sim in range(num_simulations):
        bankroll = initial_bankroll
        bankroll_history = [bankroll]
        bets_placed = 0
        
        # Simulate bets
        while bets_placed < num_bets and bankroll > 0:
            # Generate random match and odds
            match_data = generate_random_match()
            odds = generate_random_odds()
            
            # Calculate win probability using ML model
            win_probability = ml_model.predict_outcome(
                match_data['features']
            )
            
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

def generate_random_match():
    """Generate random soccer match data"""
    
    # Get all teams from all leagues
    all_teams = []
    for league_teams in config.SOCCER_TEAMS.values():
        all_teams.extend(league_teams)
    
    # Sample teams from the same league
    leagues = list(config.SOCCER_TEAMS.keys())
    selected_league = random.choice(leagues)
    teams = list(config.SOCCER_TEAMS[selected_league])
    team1 = random.choice(teams)
    team2 = random.choice([t for t in teams if t != team1])
    
    # Random match features
    features = {
        'home_form': random.uniform(0.3, 0.8),
        'away_form': random.uniform(0.2, 0.7),
        'goal_difference': random.randint(-20, 20),
        'head_to_head': random.uniform(0.3, 0.7),
        'home_xG': random.uniform(1.0, 2.5),
        'away_xG': random.uniform(0.8, 2.2)
    }
    
    return {
        'team1': team1,
        'team2': team2,
        'features': features
    }

def generate_random_odds():
    """Generate random American odds"""
    
    # Simulate realistic odds distribution
    if random.random() < 0.7:  # 70% chance of favorite/underdog
        if random.random() < 0.5:
            return -random.randint(150, 500)  # Favorite
        else:
            return random.randint(120, 400)  # Underdog
    else:
        return random.choice([-110, 100, -105, 105])  # Near even odds

def display_simulation_results(results):
    """Display simulation results"""
    
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