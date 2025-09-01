import requests
import json
from datetime import datetime, timedelta
import pandas as pd
import config

class OddsDataCollector:
    """Collect live odds from The Odds API"""
    
    def __init__(self):
        self.api_key = config.THE_ODDS_API_KEY
        if not self.api_key:
            raise ValueError("The Odds API key is not set in config")
        self.base_url = config.THE_ODDS_API_URL
        self.leagues = config.SOCCER_LEAGUES
    
    def get_soccer_odds(self, league_keys=None):
        """
        Get current soccer odds for specified leagues
        
        Args:
            league_keys (list): List of league keys to fetch odds for
            
        Returns:
            dict: Odds data by league
        """
        
        if league_keys is None:
            league_keys = list(self.leagues.values())
        
        all_odds = {}
        
        for league_key in league_keys:
            try:
                url = f"{self.base_url}/odds"
                params = {
                    'api_key': self.api_key,
                    'sport': league_key,
                    'regions': 'us,uk,eu',
                    'markets': 'h2h,spreads,totals',
                    'oddsFormat': 'american',
                    'dateFormat': 'iso'
                }
                
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    all_odds[league_key] = self._process_soccer_odds(data)
                    
                    # Check for remaining requests in headers
                    remaining = response.headers.get('x-requests-remaining')
                    if remaining and int(remaining) < 10:
                        print(f"Warning: Only {remaining} API requests remaining")
                        
                elif response.status_code == 429:  # Rate limit exceeded
                    print(f"Rate limit exceeded for {league_key}. Using cached data if available.")
                    cached = self.get_cached_odds()
                    if cached and league_key in cached:
                        all_odds[league_key] = cached[league_key]
                    else:
                        all_odds[league_key] = []
                else:
                    print(f"Error fetching odds for {league_key}: {response.status_code}")
                    all_odds[league_key] = []
                    
            except requests.RequestException as e:
                print(f"Request error for {league_key}: {e}")
                all_odds[league_key] = []
            except Exception as e:
                print(f"Unexpected error for {league_key}: {e}")
                all_odds[league_key] = []
        
        return all_odds
    
    def _process_soccer_odds(self, raw_data):
        """Process raw odds data into structured format"""
        processed_matches = []
        
        if not raw_data or not isinstance(raw_data, list):
            print("No valid odds data received")
            return []
        
        for match in raw_data:
            try:
                # Validate required fields
                required_fields = ['id', 'home_team', 'away_team', 'commence_time']
                if not all(field in match for field in required_fields):
                    print(f"Skipping match with missing fields: {match.get('id', 'Unknown')}")
                    continue
                
                match_info = {
                    'match_id': match['id'],
                    'home_team': match['home_team'],
                    'away_team': match['away_team'],
                    'commence_time': match['commence_time'],
                    'bookmakers': {}
                }
                
                # Process bookmaker odds
                for bookmaker in match.get('bookmakers', []):
                    if not bookmaker.get('title'):
                        continue
                        
                    bookmaker_name = bookmaker['title']
                    match_info['bookmakers'][bookmaker_name] = {}
                    
                    for market in bookmaker.get('markets', []):
                        if market.get('key') != 'h2h':  # Only process match result odds
                            continue
                            
                        outcomes = {outcome['name']: outcome['price'] 
                                  for outcome in market.get('outcomes', [])
                                  if 'name' in outcome and 'price' in outcome}
                        
                        # Map outcomes to market types
                        if outcomes:
                            if match_info['home_team'] in outcomes:
                                match_info['bookmakers'][bookmaker_name]['home_win'] = outcomes[match_info['home_team']]
                            if match_info['away_team'] in outcomes:
                                match_info['bookmakers'][bookmaker_name]['away_win'] = outcomes[match_info['away_team']]
                            for outcome_name in outcomes:
                                if outcome_name not in [match_info['home_team'], match_info['away_team']]:
                                    match_info['bookmakers'][bookmaker_name]['draw'] = outcomes[outcome_name]
                
                # Only include matches with valid odds
                if any(odds for odds in match_info['bookmakers'].values()):
                    processed_matches.append(match_info)
                    
            except Exception as e:
                print(f"Error processing match: {e}")
                continue
        
        return processed_matches
    
    def _get_empty_odds_template(self):
        """Return empty odds data structure for when no matches are available"""
        return {
            'soccer_epl': [],
            'soccer_spain_la_liga': [],
            'soccer_germany_bundesliga': [], 
            'soccer_france_ligue_one': [],
            'soccer_uefa_champions_league': [],
            'soccer_italy_serie_a': []
        }
    
    def get_best_odds(self, match_data):
        """Get best odds from all bookmakers for a match"""
        best_odds = {
            'home_win': {'odds': None, 'bookmaker': None},
            'draw': {'odds': None, 'bookmaker': None},
            'away_win': {'odds': None, 'bookmaker': None}
        }
        
        for bookmaker, odds in match_data.get('bookmakers', {}).items():
            for market in ['home_win', 'draw', 'away_win']:
                if market in odds:
                    current_odds = odds[market]
                    
                    # For positive odds, higher is better
                    # For negative odds, closer to zero is better (less negative)
                    if best_odds[market]['odds'] is None:
                        best_odds[market] = {'odds': current_odds, 'bookmaker': bookmaker}
                    else:
                        current_better = False
                        best_odds_val = best_odds[market]['odds']
                        
                        if current_odds > 0 and best_odds_val > 0:
                            current_better = current_odds > best_odds_val
                        elif current_odds < 0 and best_odds_val < 0:
                            current_better = current_odds > best_odds_val  # Less negative
                        elif current_odds > 0 and best_odds_val < 0:
                            current_better = True
                        
                        if current_better:
                            best_odds[market] = {'odds': current_odds, 'bookmaker': bookmaker}
        
        return best_odds
    
    def format_match_for_display(self, match_data):
        """Format match data for display in the app"""
        commence_time = datetime.fromisoformat(match_data['commence_time'].replace('Z', '+00:00'))
        
        # Get best odds
        best_odds = self.get_best_odds(match_data)
        
        return {
            'match_display': f"{match_data['home_team']} vs {match_data['away_team']}",
            'home_team': match_data['home_team'],
            'away_team': match_data['away_team'],
            'date_time': commence_time.strftime("%B %d, %Y at %H:%M UTC"),
            'home_win_odds': best_odds['home_win']['odds'],
            'draw_odds': best_odds['draw']['odds'],
            'away_win_odds': best_odds['away_win']['odds'],
            'best_bookmaker_home': best_odds['home_win']['bookmaker'],
            'best_bookmaker_draw': best_odds['draw']['bookmaker'],
            'best_bookmaker_away': best_odds['away_win']['bookmaker'],
            'match_id': match_data['match_id']
        }
    
    def get_league_name_from_key(self, league_key):
        """Get display name for league key"""
        league_map = {v: k for k, v in self.leagues.items()}
        return league_map.get(league_key, league_key)
    
    def save_odds_to_database(self, odds_data):
        """Save odds data to database"""
        try:
            from database.db_manager import DatabaseManager
            db_manager = DatabaseManager()
            
            odds_list = []
            for league_key, matches in odds_data.items():
                for match in matches:
                    for bookmaker, odds in match.get('bookmakers', {}).items():
                        for market, odds_value in odds.items():
                            odds_list.append({
                                'sport': 'soccer',
                                'match_id': match['match_id'],
                                'bookmaker': bookmaker,
                                'market': market,
                                'odds': odds_value
                            })
            
            if odds_list:
                db_manager.save_odds_data(odds_list)
                
        except Exception as e:
            print(f"Error saving odds to database: {e}")
    
    def get_cached_odds(self):
        """Get cached odds from session state or database"""
        from database.db_manager import DatabaseManager
        from utils.helpers import get_cached_data, cache_data
        
        try:
            # First try memory cache
            cached = get_cached_data('soccer_odds')
            if cached:
                # Verify the cache is not too old (15 minutes)
                cache_time = get_cached_data('soccer_odds_time')
                if cache_time:
                    cache_age = (datetime.now() - cache_time).total_seconds() / 3600
                    if cache_age <= config.DATA_UPDATE_INTERVALS['live_odds']:
                        return cached
            
            # Try database cache
            db = DatabaseManager()
            db_odds = db.get_recent_odds('soccer')
            if db_odds:
                # Format database odds into API format
                formatted_odds = self._format_db_odds(db_odds)
                # Cache the formatted odds
                self.update_odds_cache(formatted_odds)
                return formatted_odds
            
            # If no valid cache, fetch new data
            odds_data = self.get_soccer_odds()
            if odds_data:
                self.update_odds_cache(odds_data)
                return odds_data
                
        except Exception as e:
            print(f"Error retrieving cached odds: {e}")
        
        # Return empty data structure if all else fails
        return self._get_empty_odds_template()
    
    def _format_db_odds(self, db_odds):
        """Format database odds into API response format"""
        matches = {}
        
        for odd in db_odds:
            match_id = odd['match_id']
            if match_id not in matches:
                matches[match_id] = {
                    'match_id': match_id,
                    'home_team': odd.get('home_team'),
                    'away_team': odd.get('away_team'),
                    'commence_time': odd.get('created_at'),
                    'bookmakers': {}
                }
            
            bookmaker = odd['bookmaker']
            if bookmaker not in matches[match_id]['bookmakers']:
                matches[match_id]['bookmakers'][bookmaker] = {}
            
            matches[match_id]['bookmakers'][bookmaker][odd['market']] = odd['odds']
        
        return list(matches.values())
    
    def update_odds_cache(self, odds_data):
        """Update odds cache in both memory and database"""
        try:
            # Update memory cache
            from utils.helpers import cache_data
            cache_data('soccer_odds', odds_data)
            cache_data('soccer_odds_time', datetime.now())
            
            # Update database
            self.save_odds_to_database(odds_data)
            
        except Exception as e:
            print(f"Error updating odds cache: {e}")
    
