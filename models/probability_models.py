import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pandas as pd
from data.soccer_data import SoccerDataCollector
from data.cricket_data import CricketDataCollector
from data.tennis_data import TennisDataCollector
from data.f1_data import F1DataCollector

class BaseWinProbabilityModel:
    """Base class for win probability models"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        
    def preprocess_data(self, data):
        """Preprocess input data"""
        return self.scaler.fit_transform(data)
        
    def train_model(self, X, y):
        """Train the model"""
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        self.model.fit(X_train, y_train)
        return self.model.score(X_test, y_test)

class SoccerWinProbabilityModel(BaseWinProbabilityModel):
    """Soccer win probability model"""
    
    def __init__(self):
        super().__init__()
        self.model = GradientBoostingClassifier()
        self.data_collector = SoccerDataCollector()
        
    def get_feature_vector(self, team1, team2, market_type='moneyline'):
        """Get feature vector for prediction"""
        features = []
        
        # Get team stats
        team1_stats = self.data_collector.get_team_stats(team1)
        team2_stats = self.data_collector.get_team_stats(team2)
        
        # Recent form
        team1_form = self.data_collector.get_team_recent_matches(team1)
        team2_form = self.data_collector.get_team_recent_matches(team2)
        
        # Head to head
        h2h = self.data_collector.get_head_to_head(team1, team2)
        
        # Create feature vector based on market type
        if market_type == 'moneyline':
            features.extend([
                team1_stats['win_rate'],
                team1_stats['goals_scored_avg'],
                team1_stats['goals_conceded_avg'],
                team2_stats['win_rate'],
                team2_stats['goals_scored_avg'],
                team2_stats['goals_conceded_avg'],
                h2h['team1_wins'] / max(h2h['total_matches'], 1),
                h2h['team2_wins'] / max(h2h['total_matches'], 1)
            ])
        elif 'over_under' in market_type:
            features.extend([
                team1_stats['goals_scored_avg'],
                team1_stats['goals_conceded_avg'],
                team2_stats['goals_scored_avg'],
                team2_stats['goals_conceded_avg'],
                h2h['avg_total_goals']
            ])
        
        return np.array(features).reshape(1, -1)
    
    def predict_probability(self, team1, team2, market_type='moneyline'):
        """Predict win probability"""
        features = self.get_feature_vector(team1, team2, market_type)
        return self.model.predict_proba(features)[0]

class CricketWinProbabilityModel(BaseWinProbabilityModel):
    """Cricket win probability model"""
    
    def __init__(self):
        super().__init__()
        self.model = RandomForestClassifier()
        self.data_collector = CricketDataCollector()
    
    def get_feature_vector(self, team1, team2, format_type='Test'):
        """Get feature vector for prediction"""
        features = []
        
        # Get team stats
        team1_stats = self.data_collector.get_team_stats(team1, format_type)
        team2_stats = self.data_collector.get_team_stats(team2, format_type)
        
        # Recent form
        team1_form = self.data_collector.get_team_recent_matches(team1, format_type)
        team2_form = self.data_collector.get_team_recent_matches(team2, format_type)
        
        # Create feature vector based on format
        features.extend([
            team1_stats['win_rate'],
            team1_stats['batting_avg'],
            team1_stats['bowling_avg'],
            team2_stats['win_rate'],
            team2_stats['batting_avg'],
            team2_stats['bowling_avg']
        ])
        
        return np.array(features).reshape(1, -1)
    
    def predict_probability(self, team1, team2, format_type='Test'):
        """Predict win probability"""
        features = self.get_feature_vector(team1, team2, format_type)
        return self.model.predict_proba(features)[0]

class TennisWinProbabilityModel(BaseWinProbabilityModel):
    """Tennis win probability model"""
    
    def __init__(self):
        super().__init__()
        self.model = GradientBoostingClassifier()
        self.data_collector = TennisDataCollector()
    
    def get_feature_vector(self, player1, player2, surface='hard'):
        """Get feature vector for prediction"""
        features = []
        
        # Get player stats
        player1_stats = self.data_collector.get_player_stats(player1, surface)
        player2_stats = self.data_collector.get_player_stats(player2, surface)
        
        # Recent form
        player1_form = self.data_collector.get_recent_matches(player1)
        player2_form = self.data_collector.get_recent_matches(player2)
        
        # Head to head
        h2h = self.data_collector.get_head_to_head(player1, player2)
        
        # Create feature vector
        features.extend([
            player1_stats['win_rate'],
            player1_stats['service_points_won'],
            player1_stats['return_points_won'],
            player2_stats['win_rate'],
            player2_stats['service_points_won'],
            player2_stats['return_points_won'],
            h2h['player1_wins'] / max(h2h['total_matches'], 1)
        ])
        
        return np.array(features).reshape(1, -1)
    
    def predict_probability(self, player1, player2, surface='hard'):
        """Predict win probability"""
        features = self.get_feature_vector(player1, player2, surface)
        return self.model.predict_proba(features)[0]

class F1WinProbabilityModel(BaseWinProbabilityModel):
    """Formula 1 win probability model"""
    
    def __init__(self):
        super().__init__()
        self.model = GradientBoostingClassifier()
        self.data_collector = F1DataCollector()
    
    def get_feature_vector(self, driver1, driver2, circuit):
        """Get feature vector for prediction"""
        features = []
        
        # Get driver stats
        driver1_stats = self.data_collector.get_driver_stats(driver1)
        driver2_stats = self.data_collector.get_driver_stats(driver2)
        
        # Get circuit history
        circuit_stats = self.data_collector.get_circuit_stats(circuit)
        
        # Recent form
        driver1_form = self.data_collector.get_recent_results(driver1)
        driver2_form = self.data_collector.get_recent_results(driver2)
        
        # Create feature vector
        features.extend([
            driver1_stats['win_rate'],
            driver1_stats['podium_rate'],
            driver1_stats['qualifying_avg'],
            driver2_stats['win_rate'],
            driver2_stats['podium_rate'],
            driver2_stats['qualifying_avg'],
            circuit_stats[driver1]['avg_finish'],
            circuit_stats[driver2]['avg_finish']
        ])
        
        return np.array(features).reshape(1, -1)
    
    def predict_probability(self, driver1, driver2, circuit):
        """Predict win probability"""
        features = self.get_feature_vector(driver1, driver2, circuit)
        return self.model.predict_proba(features)[0]

def calculate_kelly_stake(bankroll, win_prob, odds, kelly_fraction=1.0, max_bankroll_pct=1.0):
    """Calculate Kelly Criterion stake"""
    # Convert odds to decimal
    if odds > 0:
        decimal_odds = (odds / 100) + 1
    else:
        decimal_odds = (100 / abs(odds)) + 1
    
    # Calculate full Kelly stake
    b = decimal_odds - 1  # Decimal odds minus 1
    p = win_prob  # Probability of winning
    q = 1 - p  # Probability of losing
    
    if p * b > q:  # Only bet if there's positive expected value
        kelly_stake = (p * b - q) / b
        kelly_stake *= kelly_fraction  # Apply Kelly fraction
        
        # Apply maximum bankroll percentage
        max_stake = bankroll * max_bankroll_pct
        recommended_stake = min(kelly_stake * bankroll, max_stake)
        
        # Calculate metrics
        expected_value = (p * b - q) * 100  # Expected value per $100 bet
        edge = p - (1 / decimal_odds)  # Edge percentage
        
        return {
            'stake': recommended_stake,
            'stake_percentage': (recommended_stake / bankroll) * 100,
            'expected_value': expected_value,
            'edge_percentage': edge * 100,
            'kelly_fraction': kelly_stake
        }
    else:
        return {
            'stake': 0,
            'stake_percentage': 0,
            'expected_value': 0,
            'edge_percentage': 0,
            'kelly_fraction': 0
        }