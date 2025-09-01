import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import warnings
warnings.filterwarnings('ignore')

class SportsPredictionModel:
    """Machine learning models for sports outcome prediction"""
    
    def __init__(self, sport='soccer'):
        self.sport = sport
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_names = []
        self.is_trained = False
        
    def prepare_soccer_features(self, team1_data, team2_data, match_info):
        """Prepare features for soccer prediction"""
        features = []
        
        # Team form features (last 5 matches)
        team1_form = self._calculate_team_form(team1_data)
        team2_form = self._calculate_team_form(team2_data)
        
        features.extend([
            team1_form['win_rate'],
            team1_form['goals_per_game'],
            team1_form['goals_conceded_per_game'],
            team1_form['clean_sheets_rate'],
            team2_form['win_rate'],
            team2_form['goals_per_game'],
            team2_form['goals_conceded_per_game'],
            team2_form['clean_sheets_rate']
        ])
        
        # Head-to-head features
        h2h_stats = self._calculate_h2h_stats(team1_data, team2_data)
        features.extend([
            h2h_stats['team1_wins'],
            h2h_stats['draws'],
            h2h_stats['team2_wins'],
            h2h_stats['avg_goals']
        ])
        
        # Match context features
        features.extend([
            1 if match_info.get('venue') == 'home' else 0,  # Home advantage
            match_info.get('importance', 1),  # Match importance
            match_info.get('rest_days_team1', 3),  # Rest days
            match_info.get('rest_days_team2', 3)
        ])
        
        self.feature_names = [
            'team1_win_rate', 'team1_goals_per_game', 'team1_goals_conceded',
            'team1_clean_sheets', 'team2_win_rate', 'team2_goals_per_game',
            'team2_goals_conceded', 'team2_clean_sheets', 'h2h_team1_wins',
            'h2h_draws', 'h2h_team2_wins', 'h2h_avg_goals', 'home_advantage',
            'match_importance', 'team1_rest_days', 'team2_rest_days'
        ]
        
        return np.array(features).reshape(1, -1)
    
    def prepare_tennis_features(self, player1_data, player2_data, match_info):
        """Prepare features for tennis prediction"""
        features = []
        
        # Player form and ranking
        features.extend([
            player1_data.get('ranking', 100),
            player1_data.get('recent_form', 0.5),  # Win rate last 10
            player1_data.get('service_games_won', 0.85),
            player1_data.get('return_games_won', 0.15),
            player2_data.get('ranking', 100),
            player2_data.get('recent_form', 0.5),
            player2_data.get('service_games_won', 0.85),
            player2_data.get('return_games_won', 0.15)
        ])
        
        # Surface-specific stats
        surface = match_info.get('surface', 'hard')
        features.extend([
            player1_data.get(f'{surface}_win_rate', 0.5),
            player2_data.get(f'{surface}_win_rate', 0.5)
        ])
        
        # Head-to-head
        h2h = match_info.get('h2h_record', {'player1_wins': 0, 'player2_wins': 0})
        total_h2h = h2h['player1_wins'] + h2h['player2_wins']
        h2h_rate = h2h['player1_wins'] / total_h2h if total_h2h > 0 else 0.5
        features.append(h2h_rate)
        
        # Match context
        features.extend([
            1 if surface == 'clay' else 0,
            1 if surface == 'grass' else 0,
            1 if surface == 'hard' else 0,
            match_info.get('tournament_level', 1)  # 1-4 scale
        ])
        
        self.feature_names = [
            'player1_ranking', 'player1_form', 'player1_service_rate',
            'player1_return_rate', 'player2_ranking', 'player2_form',
            'player2_service_rate', 'player2_return_rate', 'player1_surface_rate',
            'player2_surface_rate', 'h2h_rate', 'surface_clay', 'surface_grass',
            'surface_hard', 'tournament_level'
        ]
        
        return np.array(features).reshape(1, -1)
    
    def prepare_cricket_features(self, team1_data, team2_data, match_info):
        """Prepare features for cricket prediction"""
        features = []
        
        # Team batting stats
        features.extend([
            team1_data.get('avg_score', 250),
            team1_data.get('strike_rate', 85),
            team1_data.get('top_order_avg', 35),
            team2_data.get('avg_score', 250),
            team2_data.get('strike_rate', 85),
            team2_data.get('top_order_avg', 35)
        ])
        
        # Team bowling stats
        features.extend([
            team1_data.get('bowling_avg', 30),
            team1_data.get('economy_rate', 5.5),
            team2_data.get('bowling_avg', 30),
            team2_data.get('economy_rate', 5.5)
        ])
        
        # Venue and format specific
        format_type = match_info.get('format', 'odi')
        features.extend([
            1 if format_type == 'test' else 0,
            1 if format_type == 'odi' else 0,
            1 if format_type == 't20' else 0,
            1 if match_info.get('venue_type') == 'spinning' else 0,
            1 if match_info.get('home_team') == 'team1' else 0
        ])
        
        self.feature_names = [
            'team1_avg_score', 'team1_strike_rate', 'team1_top_order',
            'team2_avg_score', 'team2_strike_rate', 'team2_top_order',
            'team1_bowling_avg', 'team1_economy', 'team2_bowling_avg',
            'team2_economy', 'format_test', 'format_odi', 'format_t20',
            'spinning_track', 'home_advantage'
        ]
        
        return np.array(features).reshape(1, -1)
    
    def prepare_f1_features(self, driver1_data, driver2_data, race_info):
        """Prepare features for F1 prediction"""
        features = []
        
        # Driver stats
        features.extend([
            driver1_data.get('championship_position', 10),
            driver1_data.get('points', 0),
            driver1_data.get('avg_finish_position', 10),
            driver1_data.get('podium_rate', 0.1),
            driver2_data.get('championship_position', 10),
            driver2_data.get('points', 0),
            driver2_data.get('avg_finish_position', 10),
            driver2_data.get('podium_rate', 0.1)
        ])
        
        # Team/car performance
        features.extend([
            driver1_data.get('team_points', 0),
            driver1_data.get('car_pace_ranking', 5),
            driver2_data.get('team_points', 0),
            driver2_data.get('car_pace_ranking', 5)
        ])
        
        # Circuit-specific
        circuit_type = race_info.get('circuit_type', 'mixed')
        features.extend([
            driver1_data.get(f'{circuit_type}_performance', 0.5),
            driver2_data.get(f'{circuit_type}_performance', 0.5),
            1 if race_info.get('qualifying_advantage') == 'driver1' else 0,
            race_info.get('overtaking_difficulty', 5)  # 1-10 scale
        ])
        
        self.feature_names = [
            'driver1_championship_pos', 'driver1_points', 'driver1_avg_finish',
            'driver1_podium_rate', 'driver2_championship_pos', 'driver2_points',
            'driver2_avg_finish', 'driver2_podium_rate', 'driver1_team_points',
            'driver1_car_pace', 'driver2_team_points', 'driver2_car_pace',
            'driver1_circuit_performance', 'driver2_circuit_performance',
            'qualifying_advantage', 'overtaking_difficulty'
        ]
        
        return np.array(features).reshape(1, -1)
    
    def _calculate_team_form(self, team_data):
        """Calculate team form metrics"""
        if not team_data or len(team_data) == 0:
            return {
                'win_rate': 0.5,
                'goals_per_game': 1.5,
                'goals_conceded_per_game': 1.5,
                'clean_sheets_rate': 0.3
            }
        
        wins = sum(1 for match in team_data if match.get('result') == 'W')
        total_games = len(team_data)
        total_goals = sum(match.get('goals_for', 0) for match in team_data)
        total_conceded = sum(match.get('goals_against', 0) for match in team_data)
        clean_sheets = sum(1 for match in team_data if match.get('goals_against', 0) == 0)
        
        return {
            'win_rate': wins / total_games if total_games > 0 else 0.5,
            'goals_per_game': total_goals / total_games if total_games > 0 else 1.5,
            'goals_conceded_per_game': total_conceded / total_games if total_games > 0 else 1.5,
            'clean_sheets_rate': clean_sheets / total_games if total_games > 0 else 0.3
        }
    
    def _calculate_h2h_stats(self, team1_data, team2_data):
        """Calculate head-to-head statistics"""
        # This would normally fetch actual H2H data
        # For now, return default values
        return {
            'team1_wins': 3,
            'draws': 2,
            'team2_wins': 2,
            'avg_goals': 2.5
        }
    
    def train_model(self, training_data=None, target_variable='result'):
        """Train the prediction model"""
        if training_data is None or len(training_data) == 0:
            # Get real training data from collector
            if self.sport == 'cricket':
                from data.cricket_data import CricketDataCollector
                collector = CricketDataCollector()
                matches = collector.get_current_matches('all')
                if matches:
                    training_data = pd.DataFrame(matches)
                else:
                    training_data = self._generate_mock_training_data()
            else:
                training_data = self._generate_mock_training_data()
        
        X = training_data.drop(columns=[target_variable])
        y = training_data[target_variable]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train ensemble model
        models = {
            'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingClassifier(random_state=42),
            'logistic_regression': LogisticRegression(random_state=42)
        }
        
        best_score = 0
        best_model = None
        
        for name, model in models.items():
            if name == 'logistic_regression':
                model.fit(X_train_scaled, y_train)
                predictions = model.predict(X_test_scaled)
            else:
                model.fit(X_train, y_train)
                predictions = model.predict(X_test)
            
            accuracy = accuracy_score(y_test, predictions)
            
            if accuracy > best_score:
                best_score = accuracy
                best_model = model
        
        self.model = best_model
        self.is_trained = True
        
        return {
            'accuracy': best_score,
            'model_type': type(best_model).__name__
        }
    
    def predict_outcome(self, features):
        """Predict match outcome probability"""
        if not self.is_trained or self.model is None:
            # Train with mock data if not trained
            self.train_model(None)
        
        # Convert dictionary to array if needed
        if isinstance(features, dict):
            feature_values = [features.get(name, 0) for name in self.feature_names]
            features = np.array(feature_values)
        
        # Convert to numpy array if not already
        if not isinstance(features, np.ndarray):
            features = np.array(features)
        
        # Ensure features is the right shape
        if len(features.shape) == 1:
            features = features.reshape(1, -1)
        
        # Scale features if using logistic regression
        if isinstance(self.model, LogisticRegression):
            features = self.scaler.transform(features)
        
        # Get probabilities
        try:
            probabilities = self.model.predict_proba(features)[0]
            
            # For binary classification (win/loss), return win probability
            if len(probabilities) == 2:
                return probabilities[1]  # Probability of winning
            else:
                # For multi-class (win/draw/loss), return win probability
                return probabilities[2] if len(probabilities) == 3 else probabilities[0]
        
        except Exception as e:
            # Fallback to simple probability calculation
            return self._calculate_simple_probability(features)
    
    def _calculate_simple_probability(self, features):
        """Simple probability calculation as fallback"""
        if self.sport == 'soccer':
            return 0.45 + (features[0][0] - features[0][4]) * 0.1  # Based on team form difference
        elif self.sport == 'tennis':
            ranking_diff = (features[0][4] - features[0][0]) / 100  # Ranking difference
            return 0.5 + ranking_diff * 0.3
        elif self.sport == 'cricket':
            batting_diff = (features[0][0] - features[0][3]) / 50  # Batting average difference
            return 0.5 + batting_diff * 0.2
        elif self.sport == 'f1':
            points_diff = (features[0][1] - features[0][5]) / 100  # Points difference
            return 0.5 + points_diff * 0.3
        else:
            return 0.5  # Default 50%
    
    def _generate_mock_training_data(self):
        """Generate mock training data for demonstration"""
        np.random.seed(42)
        n_samples = 1000
        
        if self.sport == 'soccer':
            data = {
                'team1_win_rate': np.random.normal(0.5, 0.15, n_samples),
                'team1_goals_per_game': np.random.normal(1.5, 0.5, n_samples),
                'team1_goals_conceded': np.random.normal(1.2, 0.4, n_samples),
                'team1_clean_sheets': np.random.beta(2, 5, n_samples),
                'team2_win_rate': np.random.normal(0.45, 0.15, n_samples),
                'team2_goals_per_game': np.random.normal(1.3, 0.5, n_samples),
                'team2_goals_conceded': np.random.normal(1.4, 0.4, n_samples),
                'team2_clean_sheets': np.random.beta(2, 5, n_samples),
                'home_advantage': np.random.choice([0, 1], n_samples)
            }
            
            # Generate results based on team strength
            results = []
            for i in range(n_samples):
                team1_strength = data['team1_win_rate'][i] + data['team1_goals_per_game'][i] - data['team1_goals_conceded'][i]
                team2_strength = data['team2_win_rate'][i] + data['team2_goals_per_game'][i] - data['team2_goals_conceded'][i]
                
                if data['home_advantage'][i]:
                    team1_strength += 0.1
                
                if team1_strength > team2_strength + 0.2:
                    results.append(1)  # Team1 win
                elif team2_strength > team1_strength + 0.2:
                    results.append(0)  # Team2 win
                else:
                    results.append(np.random.choice([0, 1]))  # Random
            
            data['result'] = results
            
        else:
            # Similar mock data generation for other sports
            data = {
                'feature_1': np.random.normal(0, 1, n_samples),
                'feature_2': np.random.normal(0, 1, n_samples),
                'result': np.random.choice([0, 1], n_samples)
            }
        
        return pd.DataFrame(data)
    
    def get_feature_importance(self):
        """Get feature importance from trained model"""
        if not self.is_trained or self.model is None:
            return {}
        
        if hasattr(self.model, 'feature_importances_'):
            importance_dict = dict(zip(self.feature_names, self.model.feature_importances_))
            return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
        else:
            return {}
    
    def save_model(self, filepath):
        """Save trained model to file"""
        if self.is_trained:
            joblib.dump({
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'sport': self.sport
            }, filepath)
    
    def load_model(self, filepath):
        """Load trained model from file"""
        data = joblib.load(filepath)
        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_names = data['feature_names']
        self.sport = data['sport']
        self.is_trained = True
    
    def _generate_historical_odds(self, features):
        """Generate reasonable odds based on historical data and features"""
        if self.sport == 'cricket':
            # Use ranking difference and form for odds calculation
            rank_diff = features.get('rank_diff', 0)
            form_diff = features.get('form_diff', 0)
            home_advantage = features.get('home_advantage', 0)
            
            # Base odds of 100 (even)
            base_odds = 100
            odds_adjustment = (rank_diff * -10) + (form_diff * 20) + (home_advantage * 15)
            return base_odds + odds_adjustment
            
        elif self.sport == 'tennis':
            # Use ranking difference for tennis
            rank_diff = features.get('rank_diff', 0)
            surface_advantage = features.get('surface_advantage', 0)
            h2h_ratio = features.get('h2h_ratio', 0.5)
            
            base_odds = 100
            odds_adjustment = (rank_diff * -15) + (surface_advantage * 25) + ((h2h_ratio - 0.5) * 40)
            return base_odds + odds_adjustment
            
        elif self.sport == 'f1':
            # Use championship position and car performance
            pos_diff = features.get('championship_pos_diff', 0)
            car_diff = features.get('car_performance_diff', 0)
            track_suitability = features.get('track_suitability', 0)
            
            base_odds = 100
            odds_adjustment = (pos_diff * -8) + (car_diff * 30) + (track_suitability * 20)
            return base_odds + odds_adjustment
            
        else:
            return 100  # Even odds as fallback