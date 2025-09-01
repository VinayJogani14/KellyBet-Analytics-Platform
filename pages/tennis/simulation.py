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
    """Display the tennis bankroll simulation page"""
    
    st.markdown("""
    <div class="main-header">
        <h1>Tennis Bankroll Simulation</h1>
        <p>Monte Carlo simulation of betting strategies in tennis matches</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize models
    kelly_calc = KellyCalculator()
    ml_model = SportsPredictionModel(sport='tennis')
    
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
            key="tennis_sim_bankroll"
        )
    
    with col2:
        num_bets = st.number_input(
            "Number of Bets:",
            min_value=10,
            max_value=1000,
            value=100,
            step=10,
            key="tennis_sim_bets"
        )
    
    with col3:
        num_simulations = st.number_input(
            "Number of Simulations:",
            min_value=1,
            max_value=1000,
            value=100,
            step=10,
            key="tennis_sim_sims"
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        kelly_fraction_type = st.selectbox(
            "Kelly Fraction:",
            list(config.KELLY_FRACTIONS.keys()),
            index=1,
            key="tennis_sim_kelly"
        )
        kelly_modifier = config.KELLY_FRACTIONS[kelly_fraction_type]
    
    with col2:
        max_bankroll_percent = st.slider(
            "Maximum Bankroll Percentage:",
            min_value=0,
            max_value=100,
            value=70,
            step=5,
            key="tennis_sim_bankroll_pct"
        ) / 100
    
    # Strategy settings
    st.subheader("Strategy Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        surface_weights = {
            'Hard Court': st.slider(
                "Hard Court Weight:",
                min_value=0,
                max_value=100,
                value=60,
                step=5,
                key="tennis_hard_weight"
            ) / 100,
            'Clay': st.slider(
                "Clay Court Weight:",
                min_value=0,
                max_value=100,
                value=20,
                step=5,
                key="tennis_clay_weight"
            ) / 100,
            'Grass': st.slider(
                "Grass Court Weight:",
                min_value=0,
                max_value=100,
                value=20,
                step=5,
                key="tennis_grass_weight"
            ) / 100
        }
    
    with col2:
        min_edge = st.slider(
            "Minimum Edge (%):",
            min_value=0,
            max_value=20,
            value=5,
            step=1,
            key="tennis_min_edge"
        )
        
        min_probability = st.slider(
            "Minimum Win Probability (%):",
            min_value=0,
            max_value=100,
            value=60,
            step=5,
            key="tennis_min_prob"
        ) / 100
    
    # Run simulation
    if st.button("Run Tennis Bankroll Simulation", type="primary"):
        with st.spinner("Running Monte Carlo simulation..."):
            simulation_results = run_tennis_simulation(
                initial_bankroll=initial_bankroll,
                num_bets=num_bets,
                num_simulations=num_simulations,
                kelly_modifier=kelly_modifier,
                max_bankroll_percent=max_bankroll_percent,
                surface_weights=surface_weights,
                min_edge=min_edge,
                min_probability=min_probability,
                kelly_calc=kelly_calc,
                ml_model=ml_model
            )
            
            # Display results
            display_simulation_results(simulation_results)

def run_tennis_simulation(initial_bankroll, num_bets, num_simulations, kelly_modifier,
                        max_bankroll_percent, surface_weights, min_edge, min_probability,
                        kelly_calc, ml_model):
    """Run tennis betting simulation"""
    
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
            match_data = generate_random_tennis_match(surface_weights)
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

def generate_random_tennis_match(surface_weights):
    """Generate random tennis match data"""
    
    # Sample players from different tiers
    tier1 = ['Novak Djokovic', 'Carlos Alcaraz', 'Daniil Medvedev', 'Jannik Sinner']
    tier2 = ['Alexander Zverev', 'Andrey Rublev', 'Stefanos Tsitsipas', 'Holger Rune']
    tier3 = ['Taylor Fritz', 'Frances Tiafoe', 'Karen Khachanov', 'Hubert Hurkacz']
    
    if random.random() < 0.3:
        player1 = random.choice(tier1)
        player2 = random.choice(tier2 + tier3)
    else:
        player1 = random.choice(tier2)
        player2 = random.choice(tier2 + tier3)
    
    # Select surface based on weights
    surfaces = list(surface_weights.keys())
    weights = list(surface_weights.values())
    surface = random.choices(surfaces, weights=weights)[0]
    
    # Generate random features
    features = {
        'player1_rank': random.randint(1, 20),
        'player2_rank': random.randint(5, 50),
        'player1_form': random.uniform(0.5, 0.9),
        'player2_form': random.uniform(0.4, 0.8),
        'surface': surface,
        'tournament_tier': random.choice(['Grand Slam', 'Masters 1000', 'ATP 500']),
        'h2h_ratio': random.uniform(0.4, 0.7)
    }
    
    return {
        'player1': player1,
        'player2': player2,
        'features': features
    }

def generate_random_odds():
    """Generate random tennis odds"""
    
    # Tennis odds tend to be more extreme than team sports
    if random.random() < 0.7:  # 70% chance of clear favorite
        if random.random() < 0.5:
            return -random.randint(200, 800)  # Strong favorite
        else:
            return random.randint(150, 600)  # Clear underdog
    else:
        return random.choice([-120, 110, -110, 120])  # Close match

def display_simulation_results(results):
    """Display tennis simulation results"""
    
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