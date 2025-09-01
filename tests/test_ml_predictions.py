import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.ml_models import SportsPredictionModel
import numpy as np

def test_soccer_prediction_with_dict():
    model = SportsPredictionModel(sport='soccer')
    
    # Test with dictionary input
    features_dict = {
        'team1_win_rate': 0.75,
        'team1_goals_per_game': 2.5,
        'team1_goals_conceded': 0.8,
        'team1_clean_sheets': 0.4,
        'team2_win_rate': 0.45,
        'team2_goals_per_game': 1.2,
        'team2_goals_conceded': 1.8,
        'team2_clean_sheets': 0.2,
        'h2h_team1_wins': 3,
        'h2h_draws': 1,
        'h2h_team2_wins': 1,
        'h2h_avg_goals': 2.5,
        'home_advantage': 1,
        'match_importance': 1,
        'team1_rest_days': 5,
        'team2_rest_days': 3
    }
    
    probability = model.predict_outcome(features_dict)
    print(f"Probability with dict input: {probability}")
    assert 0 <= probability <= 1, "Probability should be between 0 and 1"
    
    # Test with array input
    features_array = np.array([
        0.75, 2.5, 0.8, 0.4, 0.45, 1.2, 1.8, 0.2,
        3, 1, 1, 2.5, 1, 1, 5, 3
    ]).reshape(1, -1)
    
    probability = model.predict_outcome(features_array)
    print(f"Probability with array input: {probability}")
    assert 0 <= probability <= 1, "Probability should be between 0 and 1"

if __name__ == "__main__":
    test_soccer_prediction_with_dict()
