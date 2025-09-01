import pandas as pd
import requests
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import time
from functools import lru_cache

class CricketDataCollector:
    """Real cricket data collection from ESPNCricinfo"""
    
    def __init__(self):
        self.cricinfo_base = "https://www.espncricinfo.com"
        self.espn_api_base = "https://site.api.espn.com/apis/site/v2/sports/cricket"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self._cache = {}
        self.cache_duration = timedelta(minutes=15)  # Cache duration for API responses
    
    def _cached_get(self, url, timeout=15):
        """Make a GET request with caching"""
        now = datetime.now()
        
        # Check if cached response exists and is still valid
        if url in self._cache:
            cached_time, cached_response = self._cache[url]
            if now - cached_time < self.cache_duration:
                return cached_response
        
        # Make new request
        response = self.session.get(url, timeout=timeout)
        if response.status_code == 200:
            self._cache[url] = (now, response.json())
            return response.json()
        return None
    
    def get_current_matches(self, format_type='all'):
        """Get current/upcoming matches from ESPN API"""
        try:
            # Get all live and upcoming matches
            url = f"{self.espn_api_base}/scoreboard"
            data = self._cached_get(url)
            
            if data:
                matches = []
                
                for event in data.get('events', []):
                    try:
                        competition = event.get('competitions', [])[0]
                        teams = competition.get('competitors', [])
                        venue = competition.get('venue', {})
                        
                        if len(teams) >= 2:
                            match_format = self._get_match_format(event.get('name', ''))
                            
                            # Filter by format if specified
                            if format_type != 'all' and format_type.upper() != match_format.upper():
                                continue
                                
                            matches.append({
                                'team1': teams[0].get('team', {}).get('name', 'Unknown'),
                                'team2': teams[1].get('team', {}).get('name', 'Unknown'),
                                'format': match_format,
                                'venue': venue.get('fullName', 'Unknown'),
                                'status': event.get('status', {}).get('type', {}).get('detail', 'Unknown'),
                                'start_time': event.get('date', 'Unknown'),
                                'series': event.get('season', {}).get('name', 'Unknown')
                            })
                    except Exception as e:
                        print(f"Error parsing match data: {e}")
                        continue
                
                return matches
            return []
                
        except Exception as e:
            print(f"Error fetching current matches: {e}")
            return []
    
    def get_team_recent_matches(self, team_name, format_type='Test', limit=5):
        """Get recent matches for a cricket team using ESPN API"""
        try:
            # Search for team
            search_url = f"{self.espn_api_base}/teams/search?query={team_name.replace(' ', '+')}"
            response = self._cached_get(search_url, timeout=15)
            
            if not response or response.get('status', {}).get('code') != 200:
                return []
                
            search_data = response
            if not search_data.get('items'):
                return []
                
            # Get team ID from search results
            team = next((item for item in search_data['items'] 
                        if item['name'].lower() == team_name.lower()), None)
            if not team:
                return []
                
            team_id = team['id']
            
            # Get team's recent matches
            matches_url = f"{self.espn_api_base}/teams/{team_id}/schedule"
            matches_response = self._cached_get(matches_url, timeout=15)
            
            if not matches_response or matches_response.get('status', {}).get('code') != 200:
                return []
                
            matches_data = matches_response
            matches = []
            
            for event in matches_data.get('events', [])[:limit]:
                try:
                    competition = event.get('competitions', [])[0]
                    teams = competition.get('competitors', [])
                    
                    if len(teams) < 2:
                        continue
                        
                    # Get match format
                    match_format = self._get_match_format(event.get('name', ''))
                    
                    # Filter by format if specified
                    if format_type != 'all' and format_type.upper() != match_format.upper():
                        continue
                        
                    # Determine opponent
                    opponent = next((team.get('team', {}).get('name')
                                  for team in teams
                                  if team.get('team', {}).get('name', '').lower() != team_name.lower()),
                                  'Unknown')
                    
                    # Determine result
                    team_result = next((team.get('winner', False)
                                     for team in teams
                                     if team.get('team', {}).get('name', '').lower() == team_name.lower()),
                                     None)
                    
                    result = 'Won' if team_result else 'Lost' if team_result is False else 'Draw'
                    
                    matches.append({
                        'opponent': opponent,
                        'format': match_format,
                        'result': result,
                        'venue': competition.get('venue', {}).get('fullName', 'Unknown'),
                        'date': event.get('date', 'Unknown'),
                        'series': event.get('season', {}).get('name', 'Unknown Series')
                    })
                    
                except Exception as e:
                    print(f"Error parsing match data: {e}")
                    continue
            
            return matches
            
        except Exception as e:
            print(f"Error fetching team matches: {e}")
            return []
    
    def get_player_stats(self, player_name, format_type='Test'):
        """Get cricket player statistics from ESPN"""
        try:
            # Search for player
            search_url = f"{self.espn_api_base}/athletes/search?query={player_name.replace(' ', '+')}"
            response = self._cached_get(search_url, timeout=15)
            
            if not response or response.get('status', {}).get('code') != 200:
                return None
                
            search_data = response
            if not search_data.get('items'):
                return None
                
            # Get first matching player
            player = search_data['items'][0]
            player_id = player['id']
            
            # Get detailed player stats
            stats_url = f"{self.espn_api_base}/athletes/{player_id}/stats"
            stats_response = self._cached_get(stats_url, timeout=15)
            
            if not stats_response or stats_response.get('status', {}).get('code') != 200:
                return None
                
            stats_data = stats_response.json()
            
            # Find stats for the requested format
            format_stats = None
            for category in stats_data.get('categories', []):
                if format_type.lower() in category.get('name', '').lower():
                    format_stats = category
                    break
            
            if not format_stats:
                return None
                
            batting_stats = {}
            bowling_stats = {}
            
            # Process batting stats
            for stat in format_stats.get('stats', []):
                name = stat.get('name', '').lower()
                value = stat.get('value', 0)
                
                if 'innings' in name:
                    batting_stats['innings'] = int(value)
                elif 'runs' in name:
                    batting_stats['runs'] = int(value)
                elif 'average' in name:
                    batting_stats['average'] = float(value)
                elif 'strike rate' in name:
                    batting_stats['strike_rate'] = float(value)
                elif 'centuries' in name or '100s' in name:
                    batting_stats['hundreds'] = int(value)
                elif 'fifties' in name or '50s' in name:
                    batting_stats['fifties'] = int(value)
                elif 'wickets' in name:
                    bowling_stats['wickets'] = int(value)
                elif 'economy' in name:
                    bowling_stats['economy'] = float(value)
                elif 'bowling average' in name:
                    bowling_stats['average'] = float(value)
                elif 'best bowling' in name:
                    bowling_stats['best_figures'] = value
            
            return {
                'batting': {
                    'matches': format_stats.get('matches', 0),
                    'innings': batting_stats.get('innings', 0),
                    'runs': batting_stats.get('runs', 0),
                    'average': batting_stats.get('average', 0.0),
                    'strike_rate': batting_stats.get('strike_rate', 0.0) if format_type != 'Test' else None,
                    'hundreds': batting_stats.get('hundreds', 0),
                    'fifties': batting_stats.get('fifties', 0)
                },
                'bowling': {
                    'wickets': bowling_stats.get('wickets', 0),
                    'average': bowling_stats.get('average', 0.0),
                    'economy': bowling_stats.get('economy', 0.0) if format_type != 'Test' else None,
                    'best_figures': bowling_stats.get('best_figures', 'N/A')
                }
            }
            
        except Exception as e:
            print(f"Error fetching player stats: {e}")
            return None
    
    def scrape_cricinfo_match_data(self, match_url):
        """Scrape detailed match data from Cricinfo"""
        try:
            response = self.session.get(match_url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract match details
                match_data = {
                    'teams': [],
                    'scores': [],
                    'result': '',
                    'venue': '',
                    'toss': '',
                    'player_performances': []
                }
                
                # Parse team names
                team_elements = soup.find_all('span', class_='team-name')
                for team in team_elements:
                    match_data['teams'].append(team.get_text(strip=True))
                
                # Parse scores
                score_elements = soup.find_all('div', class_='score-detail')
                for score in score_elements:
                    match_data['scores'].append(score.get_text(strip=True))
                
                # Parse result
                result_elem = soup.find('div', class_='match-result')
                if result_elem:
                    match_data['result'] = result_elem.get_text(strip=True)
                
                return match_data
                
        except Exception as e:
            print(f"Error scraping match data: {e}")
            return None
    
    def get_ipl_team_data(self, team_name):
        """Get IPL team data using ESPN API"""
        try:
            # Get current IPL season standings
            url = f"{self.espn_api_base}/leagues/18799/standings"  # 18799 is IPL's league ID
            response = self._cached_get(url, timeout=15)
            
            if not response or response.get('status', {}).get('code') != 200:
                return None
                
            data = response.json()
            standings = data.get('standings', {}).get('entries', [])
            
            # Find team in standings
            team_stats = next((entry for entry in standings 
                             if team_name.lower() in entry.get('team', {}).get('name', '').lower()),
                            None)
            
            if not team_stats:
                return None
                
            stats = team_stats.get('stats', [])
            
            # Helper function to get stat value
            def get_stat(key):
                stat = next((s for s in stats if s.get('name') == key), {})
                return stat.get('value', 0)
            
            matches = int(get_stat('gamesPlayed'))
            wins = int(get_stat('wins'))
            
            return {
                'matches_played': matches,
                'wins': wins,
                'losses': int(get_stat('losses')),
                'points': int(get_stat('points')),
                'nrr': float(get_stat('netRunRate')),
                'position': int(team_stats.get('position', 0))
            }
            
        except Exception as e:
            print(f"Error fetching IPL data: {e}")
            return {}
    
    def _get_match_format(self, match_name):
        """Determine match format from match name"""
        match_name = match_name.upper()
        if 'TEST' in match_name:
            return 'TEST'
        elif 'T20' in match_name or 'TWENTY20' in match_name:
            return 'T20'
        elif 'ODI' in match_name or '50 OVER' in match_name:
            return 'ODI'
        else:
            return 'Unknown'

    def get_international_team_rankings(self):
        """Get international team rankings from ESPN"""
        try:
            # ESPN API endpoints for different formats
            format_endpoints = {
                'Test': '/rankings/102/team',
                'ODI': '/rankings/100/team',
                'T20I': '/rankings/103/team'
            }
            
            rankings = {}
            
            for format_name, endpoint in format_endpoints.items():
                url = f"{self.espn_api_base}{endpoint}"
                data = self._cached_get(url)
                
                if data and 'rankings' in data:
                    format_rankings = []
                    
                    for rank_data in data['rankings'][:5]:  # Get top 5 teams
                        team_name = rank_data.get('team', {}).get('name', 'Unknown')
                        rank = rank_data.get('pos', 0)
                        points = rank_data.get('points', 0)
                        format_rankings.append((team_name, rank, points))
                    
                    rankings[format_name] = format_rankings
            
            return rankings
            
        except Exception as e:
            print(f"Error fetching rankings: {e}")
            return {}
    
    def get_match_odds(self, match_data):
        """Get cricket match odds from database"""
        try:
            from database.db_manager import DatabaseManager
            db_manager = DatabaseManager()
            
            # Get odds from database only for cricket
            db_odds = db_manager.get_recent_odds('cricket')
            for odd in db_odds:
                if (match_data['team1'].lower() in odd['match_id'].lower() and
                    match_data['team2'].lower() in odd['match_id'].lower()):
                    return odd['odds']
            
            # If no odds found, estimate based on rankings
            rankings = self.get_international_team_rankings()
            format_rankings = rankings.get(match_data['format'].replace(' ', ''), [])
            
            team1_rank = next((rank for name, rank, _ in format_rankings if match_data['team1'] in name), 10)
            team2_rank = next((rank for name, rank, _ in format_rankings if match_data['team2'] in name), 10)
            
            # Simple odds calculation based on rankings
            rank_diff = team1_rank - team2_rank
            base_odds = 100  # Even odds
            odds_adjustment = rank_diff * 10  # 10 points per rank difference
            
            return base_odds + odds_adjustment
            
        except Exception as e:
            print(f"Error in get_match_odds: {e}")
            return None
