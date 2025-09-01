import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from models.kelly_calculator import KellyCalculator
from models.ml_models import SportsPredictionModel
from utils.visualization import plot_bankroll_simulation
from utils.helpers import american_to_decimal
from data.cricket_data import CricketDataCollector
import config

def show():
    """Display the cricket bankroll simulation page"""
    
    st.markdown("""
    <div class="main-header">
        <h1>Cricket Bankroll Simulation</h1>
        <p>Monte Carlo simulation of betting strategies in cricket matches</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize models
    kelly_calc = KellyCalculator()
    ml_model = SportsPredictionModel(sport='cricket')
    
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
            key="cricket_sim_bankroll"
        )
    
    with col2:
        num_bets = st.number_input(
            "Number of Bets:",
            min_value=10,
            max_value=1000,
            value=100,
            step=10,
            key="cricket_sim_bets"
        )
    
    with col3:
        num_simulations = st.number_input(
            "Number of Simulations:",
            min_value=1,
            max_value=1000,
            value=100,
            step=10,
            key="cricket_sim_sims"
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        kelly_fraction_type = st.selectbox(
            "Kelly Fraction:",
            list(config.KELLY_FRACTIONS.keys()),
            index=1,
            key="cricket_sim_kelly"
        )
        kelly_modifier = config.KELLY_FRACTIONS[kelly_fraction_type]
    
    with col2:
        max_bankroll_percent = st.slider(
            "Maximum Bankroll Percentage:",
            min_value=0,
            max_value=100,
            value=70,
            step=5,
            key="cricket_sim_bankroll_pct"
        ) / 100
    
    # Strategy settings
    st.subheader("Strategy Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        format_weights = {
            'Test Match': st.slider(
                "Test Match Weight:",
                min_value=0,
                max_value=100,
                value=30,
                step=5,
                key="cricket_test_weight"
            ) / 100,
            'ODI': st.slider(
                "ODI Weight:",
                min_value=0,
                max_value=100,
                value=35,
                step=5,
                key="cricket_odi_weight"
            ) / 100,
            'T20': st.slider(
                "T20 Weight:",
                min_value=0,
                max_value=100,
                value=35,
                step=5,
                key="cricket_t20_weight"
            ) / 100
        }
    
    with col2:
        min_edge = st.slider(
            "Minimum Edge (%):",
            min_value=0,
            max_value=20,
            value=5,
            step=1,
            key="cricket_min_edge"
        )
        
        min_probability = st.slider(
            "Minimum Win Probability (%):",
            min_value=0,
            max_value=100,
            value=55,
            step=5,
            key="cricket_min_prob"
        ) / 100
    
    # Run simulation
    if st.button("Run Cricket Bankroll Simulation", type="primary"):
        with st.spinner("Running Monte Carlo simulation..."):
            simulation_results = run_cricket_simulation(
                initial_bankroll=initial_bankroll,
                num_bets=num_bets,
                num_simulations=num_simulations,
                kelly_modifier=kelly_modifier,
                max_bankroll_percent=max_bankroll_percent,
                format_weights=format_weights,
                min_edge=min_edge,
                min_probability=min_probability,
                kelly_calc=kelly_calc,
                ml_model=ml_model
            )
            
            # Display results
            display_simulation_results(simulation_results)

def run_cricket_simulation(initial_bankroll, num_bets, num_simulations, kelly_modifier,
                         max_bankroll_percent, format_weights, min_edge, min_probability,
                         kelly_calc, ml_model):
    """Run cricket betting simulation"""
    
    # Convert format_weights to lists for random.choices
    formats = list(format_weights.keys())
    weights = list(format_weights.values())
    
    simulation_data = []
    successful_sims = 0
    total_bets = 0
    
    for sim in range(num_simulations):
        bankroll = initial_bankroll
        bankroll_history = [bankroll]
        bets_placed = 0
        
        # Simulate bets
        while bets_placed < num_bets and bankroll > 0:
            # Get real match and odds data
            match_data = get_cricket_match(format_weights)
            if not match_data:
                continue
                
            odds = get_match_odds(match_data)
            if not odds:
                continue
                
            # Calculate win probability using ML model
            features = np.array(list(match_data['features'].values())).reshape(1, -1)
            win_probability = ml_model.predict_outcome(features)
            
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
            
            # Use real match result if available, otherwise simulate
            cricket_data = CricketDataCollector()
            match_result = cricket_data.get_team_recent_matches(match_data['team1'], format_type=match_data['format'], limit=1)
            
            if match_result and match_result[0]['opponent'] == match_data['team2']:
                # Use real result
                win = match_result[0]['result'] == 'Won'
            else:
                # If match hasn't happened yet, simulate based on model probability
                win = random.random() < win_probability
            
            if win:
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

def get_cricket_match(format_weights):
    """Get real cricket match data from ESPN and The Odds API"""
    cricket_data = CricketDataCollector()
    
    # Get all current matches
    all_matches = cricket_data.get_current_matches('all')
    if not all_matches:
        return None
    
    # Filter matches based on format weights
    valid_matches = []
    for match in all_matches:
        match_format = match['format'].upper()
        for format_name, weight in format_weights.items():
            if format_name.upper() in match_format and weight > 0:
                valid_matches.append(match)
                break
    
    if not valid_matches:
        return None
    
    # Select a random match from valid matches
    match = random.choice(valid_matches)
    
    # Get real odds
    odds = cricket_data.get_match_odds(match)
    if not odds:
        return None
    
    # Get team rankings
    rankings = cricket_data.get_international_team_rankings()
    format_rankings = rankings.get(match['format'].replace(' ', ''), [])
    
    team1_rank = next((rank for name, rank, _ in format_rankings if match['team1'] in name), 10)
    team2_rank = next((rank for name, rank, _ in format_rankings if match['team2'] in name), 10)
    
    # Get match-specific features
    team1_recent = cricket_data.get_team_recent_matches(match['team1'], match['format'])
    team2_recent = cricket_data.get_team_recent_matches(match['team2'], match['format'])
    
    team1_form = len([m for m in team1_recent if m['result'] == 'Won']) / len(team1_recent) if team1_recent else 0.5
    team2_form = len([m for m in team2_recent if m['result'] == 'Won']) / len(team2_recent) if team2_recent else 0.5
    
    # Return real match data with feature-engineered attributes
    return {
        'team1': match['team1'],
        'team2': match['team2'],
        'format': match['format'],
        'venue': match['venue'],
        'team1_rank': team1_rank,
        'team2_rank': team2_rank,
        'team1_form': team1_form,
        'team2_form': team2_form,
        'team1_matches': team1_recent,
        'team2_matches': team2_recent,
        'series': match.get('series', 'Unknown Series'),
        'odds': odds,
        'start_time': match.get('start_time'),
        'features': {
            'rank_diff': team2_rank - team1_rank,
            'form_diff': team1_form - team2_form,
            'home_advantage': 1 if match['venue'] and match['team1'] in match['venue'] else 0
        }
    }

def get_match_odds(match_data):
    """Get real match odds from The Odds API"""
    try:
        # This would need to be implemented to fetch real odds from your odds data source
        from data.odds_data import OddsDataCollector
        odds_collector = OddsDataCollector()
        
        # Build the game key based on match data
        game_key = f"cricket_{match_data['team1']}_{match_data['team2']}".lower().replace(' ', '_')
        
        # Get odds for the match
        odds_data = odds_collector.get_match_odds('cricket', game_key)
        
        if odds_data:
            return odds_data['team1_odds']  # Return odds for team1 winning
            
        # If no odds available, return None so the simulation can skip this match
        return None
        
    except Exception as e:
        print(f"Error fetching match odds: {e}")
        return None

def display_simulation_results(results):
    """Display cricket simulation results"""
    
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