import pandas as pd
import requests
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import os
from io import StringIO

class TennisDataCollector:
    """Real tennis data collection from multiple sources"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.base_url = "https://api.sportradar.com/tennis-t2/en"  # Use SportRadar API
        self.rankings_url = f"{self.base_url}/rankings"
        self.players_url = f"{self.base_url}/players"
        self.tournaments_url = f"{self.base_url}/tournaments"
    
    def get_atp_rankings(self, limit=100):
        """Get current ATP rankings from SportRadar API"""
        try:
            # Get ATP rankings
            url = f"{self.rankings_url}/ATP"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                # Format for application
                rankings = []
                for player in data.get('rankings', [])[:limit]:
                    ranking_pos = player.get('rank', 999)
                    name = player.get('name', 'Unknown Player')
                    
                    rankings.append({
                        'name': name,
                        'ranking': ranking_pos,
                        'points': player.get('points', 0),
                        'player_id': player.get('id', ''),
                        'display_name': f"{name} (ATP #{ranking_pos})"
                    })
                
                return rankings
            
        except Exception as e:
            print(f"Error fetching ATP rankings: {e}")
            return []
    
    def get_wta_rankings(self, limit=100):
        """Get current WTA rankings from SportRadar API"""
        try:
            # Get WTA rankings
            url = f"{self.rankings_url}/WTA"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                # Format for application
                rankings = []
                for player in data.get('rankings', [])[:limit]:
                    ranking_pos = player.get('rank', 999)
                    name = player.get('name', 'Unknown Player')
                    
                    rankings.append({
                        'name': name,
                        'ranking': ranking_pos,
                        'points': player.get('points', 0),
                        'player_id': player.get('id', ''),
                        'display_name': f"{name} (WTA #{ranking_pos})"
                    })
                
                return rankings
                
        except Exception as e:
            print(f"Error fetching WTA rankings: {e}")
            return []
    
    def get_player_match_history(self, player_id, limit=10):
        """Get recent match history for a player using SportRadar API"""
        try:
            # Get player's recent matches from SportRadar API
            url = f"{self.players_url}/{player_id}/summary"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                recent_matches = data.get('matches', [])[:limit]
                
                matches = []
                for match in recent_matches:
                    tournament = match.get('tournament', {})
                    opponent = None
                    is_winner = False
                    
                    # Determine if the player won and who their opponent was
                    if match.get('winner', {}).get('id') == player_id:
                        is_winner = True
                        opponent = match.get('loser', {}).get('name', 'Unknown')
                    else:
                        opponent = match.get('winner', {}).get('name', 'Unknown')
                    
                    matches.append({
                        'opponent': opponent,
                        'result': 'W' if is_winner else 'L',
                        'score': match.get('score', {}).get('summary', 'N/A'),
                        'surface': tournament.get('surface', 'Hard'),
                        'tournament': tournament.get('name', 'Unknown'),
                        'date': match.get('scheduled', ''),
                        'round': match.get('round', {}).get('name', '')
                    })
                
                return matches
            else:
                print(f"Failed to fetch match history from SportRadar API: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error fetching match history from SportRadar API: {e}")
            return []
    
    def get_h2h_record(self, player1_id, player2_id):
        """Get head-to-head record between two players using SportRadar API"""
        try:
            # Get head-to-head data from SportRadar API
            url = f"{self.players_url}/{player1_id}/versus/{player2_id}/matches"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                h2h_matches = data.get('matches', [])
                
                player1_wins = 0
                player2_wins = 0
                recent_matches = []
                
                for match in h2h_matches:
                    winner_id = match.get('winner', {}).get('id')
                    tournament = match.get('tournament', {})
                    
                    if winner_id == player1_id:
                        player1_wins += 1
                    elif winner_id == player2_id:
                        player2_wins += 1
                        
                    recent_matches.append({
                        'tournament': tournament.get('name', 'Unknown'),
                        'surface': tournament.get('surface', 'Hard'),
                        'date': match.get('scheduled', ''),
                        'score': match.get('score', {}).get('summary', 'N/A'),
                        'round': match.get('round', {}).get('name', ''),
                        'winner_name': match.get('winner', {}).get('name', 'Unknown'),
                        'loser_name': match.get('loser', {}).get('name', 'Unknown')
                    })
                
                # Sort matches by date and get most recent ones
                recent_matches.sort(key=lambda x: x['date'], reverse=True)
                recent_matches = recent_matches[:3]
                
                return {
                    'player1_wins': player1_wins,
                    'player2_wins': player2_wins,
                    'total_matches': len(h2h_matches),
                    'recent_matches': recent_matches
                }
            else:
                print(f"Failed to fetch H2H data from SportRadar API: {response.status_code}")
                return {'player1_wins': 0, 'player2_wins': 0, 'total_matches': 0, 'recent_matches': []}
            
        except Exception as e:
            print(f"Error fetching H2H data from SportRadar API: {e}")
            return {'player1_wins': 0, 'player2_wins': 0, 'total_matches': 0, 'recent_matches': []}
    
    def get_surface_stats(self, player_id, surface, years=2):
        """Get player performance on specific surface using SportRadar API"""
        try:
            # Get player's matches from SportRadar API
            url = f"{self.players_url}/{player_id}/summary"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                all_matches = data.get('matches', [])
                
                wins = 0
                losses = 0
                
                # Filter matches by surface and time period
                cutoff_date = (datetime.now() - timedelta(days=years*365)).strftime('%Y-%m-%d')
                
                for match in all_matches:
                    match_surface = match.get('tournament', {}).get('surface', '').lower()
                    match_date = match.get('scheduled', '').split('T')[0]
                    
                    if match_surface == surface.lower() and match_date >= cutoff_date:
                        if match.get('winner', {}).get('id') == player_id:
                            wins += 1
                        else:
                            losses += 1
                
                total = wins + losses
                win_rate = wins / total if total > 0 else 0.5
                
                return {
                    'wins': wins,
                    'losses': losses,
                    'win_rate': win_rate,
                    'total_matches': total
                }
            else:
                print(f"Failed to fetch surface stats from SportRadar API: {response.status_code}")
                return {'wins': 0, 'losses': 0, 'win_rate': 0, 'total_matches': 0}
            
        except Exception as e:
            print(f"Error fetching surface stats from SportRadar API: {e}")
            return {'wins': 0, 'losses': 0, 'win_rate': 0, 'total_matches': 0}