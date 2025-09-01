import numpy as np
import pandas as pd
from utils.helpers import american_to_decimal, implied_probability, calculate_edge
import config

class KellyCalculator:
    """Kelly Criterion calculator for optimal bet sizing"""
    
    def __init__(self):
        self.kelly_fractions = config.KELLY_FRACTIONS
        self.risk_thresholds = config.RISK_THRESHOLDS
    
    def calculate_kelly_fraction(self, win_probability, american_odds):
        """
        Calculate the Kelly Criterion fraction
        
        Args:
            win_probability (float): Probability of winning (0-1)
            american_odds (int): American odds format
            
        Returns:
            float: Kelly fraction (0-1)
        """
        if win_probability <= 0 or win_probability >= 1:
            return 0
        
        decimal_odds = american_to_decimal(american_odds)
        b = decimal_odds - 1  # Net odds received
        p = win_probability
        q = 1 - p
        
        kelly_fraction = (b * p - q) / b
        
        # Don't bet if Kelly is negative (no edge)
        return max(0, kelly_fraction)
    
    def calculate_recommended_stake(self, win_probability, american_odds, bankroll, 
                                  kelly_modifier=1.0, max_bankroll_percent=1.0):
        """
        Calculate recommended stake amount
        
        Args:
            win_probability (float): Probability of winning (0-1)
            american_odds (int): American odds
            bankroll (float): Available bankroll
            kelly_modifier (float): Kelly fraction modifier (0.25, 0.5, 1.0)
            max_bankroll_percent (float): Maximum bankroll percentage to use (0-1)
            
        Returns:
            dict: Calculation results
        """
        # Calculate Kelly fraction
        kelly_fraction = self.calculate_kelly_fraction(win_probability, american_odds)
        
        # Apply modifier (quarter Kelly, half Kelly, etc.)
        modified_kelly = kelly_fraction * kelly_modifier
        
        # Apply maximum bankroll constraint
        available_bankroll = bankroll * max_bankroll_percent
        
        # Calculate recommended stake
        recommended_stake = available_bankroll * modified_kelly
        
        # Calculate other metrics
        implied_prob = implied_probability(american_odds)
        edge = calculate_edge(win_probability, american_odds)
        expected_value = self.calculate_expected_value(win_probability, american_odds, recommended_stake)
        stake_percentage = (recommended_stake / bankroll) * 100 if bankroll > 0 else 0
        risk_assessment = self.assess_risk(stake_percentage)
        
        return {
            'win_probability': win_probability * 100,
            'implied_probability': implied_prob * 100,
            'edge': edge * 100,
            'kelly_fraction': kelly_fraction * 100,
            'modified_kelly': modified_kelly * 100,
            'recommended_stake': recommended_stake,
            'stake_percentage': stake_percentage,
            'expected_value': expected_value,
            'risk_assessment': risk_assessment,
            'available_bankroll': available_bankroll
        }
    
    def calculate_expected_value(self, win_probability, american_odds, stake):
        """Calculate expected value of a bet"""
        decimal_odds = american_to_decimal(american_odds)
        win_amount = stake * (decimal_odds - 1)
        lose_amount = -stake
        
        expected_value = (win_probability * win_amount) + ((1 - win_probability) * lose_amount)
        return expected_value
    
    def assess_risk(self, stake_percentage):
        """Assess risk level based on stake percentage"""
        if stake_percentage < self.risk_thresholds['LOW'] * 100:
            return "LOW RISK"
        elif stake_percentage < self.risk_thresholds['MEDIUM'] * 100:
            return "MEDIUM RISK"
        else:
            return "HIGH RISK"
    
    def generate_summary(self, results, bet_type, team1=None, team2=None):
        """Generate betting recommendation summary"""
        stake = results['recommended_stake']
        bankroll_percent = results['stake_percentage']
        win_prob = results['win_probability']
        edge = results['edge']
        risk = results['risk_assessment']
        
        if results['edge'] <= 0:
            return f"NO BET RECOMMENDED: No positive expected value detected. Model shows {edge:.1f}% edge."
        
        summary = f"Recommended bet: {bankroll_percent:.1f}% of bankroll (${stake:.2f}) on {bet_type}"
        
        if team1 and team2:
            summary += f" for {team1} vs {team2} match"
        
        summary += f".\n\nKey factors:\n"
        summary += f"• Win probability: {win_prob:.1f}%\n"
        summary += f"• Betting edge: {edge:.1f}%\n"
        summary += f"• Expected value: ${results['expected_value']:.2f}\n"
        summary += f"• Risk level: {risk}\n\n"
        
        if risk == "HIGH RISK":
            summary += "⚠️ HIGH RISK: Consider reducing to quarter Kelly for more conservative approach."
        elif risk == "MEDIUM RISK":
            summary += "⚡ MEDIUM RISK: Good value bet with moderate risk."
        else:
            summary += "✅ LOW RISK: Conservative bet with positive expected value."
            
        return summary
    
    def simulate_kelly_betting(self, win_probability, american_odds, initial_bankroll, 
                              num_bets=100, kelly_modifier=0.5):
        """
        Simulate Kelly betting strategy over multiple bets
        
        Args:
            win_probability (float): Probability of winning each bet
            american_odds (int): American odds for each bet
            initial_bankroll (float): Starting bankroll
            num_bets (int): Number of bets to simulate
            kelly_modifier (float): Kelly fraction modifier
            
        Returns:
            dict: Simulation results
        """
        bankroll_history = [initial_bankroll]
        current_bankroll = initial_bankroll
        wins = 0
        losses = 0
        max_drawdown = 0
        peak_bankroll = initial_bankroll
        
        for bet_num in range(num_bets):
            # Calculate Kelly stake
            kelly_fraction = self.calculate_kelly_fraction(win_probability, american_odds)
            stake = current_bankroll * kelly_fraction * kelly_modifier
            
            # Simulate bet outcome
            if np.random.random() < win_probability:
                # Win
                decimal_odds = american_to_decimal(american_odds)
                payout = stake * decimal_odds
                current_bankroll = current_bankroll - stake + payout
                wins += 1
            else:
                # Loss
                current_bankroll -= stake
                losses += 1
            
            # Track metrics
            bankroll_history.append(current_bankroll)
            
            if current_bankroll > peak_bankroll:
                peak_bankroll = current_bankroll
            
            current_drawdown = (peak_bankroll - current_bankroll) / peak_bankroll
            if current_drawdown > max_drawdown:
                max_drawdown = current_drawdown
            
            # Stop if bankroll is depleted
            if current_bankroll <= 0:
                break
        
        final_roi = ((current_bankroll - initial_bankroll) / initial_bankroll) * 100
        win_rate = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0
        
        return {
            'initial_bankroll': initial_bankroll,
            'final_bankroll': current_bankroll,
            'total_bets': wins + losses,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'roi': final_roi,
            'max_drawdown': max_drawdown * 100,
            'bankroll_history': bankroll_history
        }
    
    def optimize_kelly_fraction(self, win_probability, american_odds, bankroll, 
                               risk_tolerance='medium'):
        """
        Optimize Kelly fraction based on risk tolerance
        
        Args:
            win_probability (float): Probability of winning
            american_odds (int): American odds
            bankroll (float): Available bankroll
            risk_tolerance (str): 'low', 'medium', 'high'
            
        Returns:
            dict: Optimized recommendations
        """
        base_kelly = self.calculate_kelly_fraction(win_probability, american_odds)
        
        # Risk-adjusted Kelly fractions
        risk_multipliers = {
            'low': 0.25,      # Quarter Kelly
            'medium': 0.5,    # Half Kelly
            'high': 0.75      # Three-quarter Kelly
        }
        
        multiplier = risk_multipliers.get(risk_tolerance, 0.5)
        optimized_kelly = base_kelly * multiplier
        
        results = self.calculate_recommended_stake(
            win_probability, american_odds, bankroll, 
            kelly_modifier=multiplier
        )
        
        return {
            'base_kelly': base_kelly * 100,
            'optimized_kelly': optimized_kelly * 100,
            'multiplier': multiplier,
            'risk_tolerance': risk_tolerance,
            'results': results
        }
    
    def calculate_multiple_outcomes(self, scenarios, bankroll):
        """
        Calculate Kelly recommendations for multiple betting scenarios
        
        Args:
            scenarios (list): List of dicts with win_probability and odds
            bankroll (float): Available bankroll
            
        Returns:
            list: Sorted recommendations by expected value
        """
        recommendations = []
        
        for i, scenario in enumerate(scenarios):
            results = self.calculate_recommended_stake(
                scenario['win_probability'],
                scenario['odds'],
                bankroll
            )
            
            results['scenario_id'] = i
            results['scenario_name'] = scenario.get('name', f"Scenario {i+1}")
            recommendations.append(results)
        
        # Sort by expected value (descending)
        recommendations.sort(key=lambda x: x['expected_value'], reverse=True)
        
        return recommendations
    
    def validate_inputs(self, win_probability, american_odds, bankroll):
        """
        Validate Kelly calculation inputs
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not (0 < win_probability < 1):
            return False, "Win probability must be between 0 and 1"
        
        if american_odds == 0:
            return False, "Odds cannot be zero"
        
        if american_odds > -100 and american_odds < 100:
            return False, "American odds must be less than -100 or greater than +100"
        
        if bankroll <= 0:
            return False, "Bankroll must be positive"
        
        return True, "Valid inputs"