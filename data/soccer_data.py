import pandas as pd
import requests
from datetime import datetime, timedelta
import random
import config
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from understatapi import UnderstatClient

class SoccerDataCollector:
    """Collect and process soccer data from various sources"""
    
    def scrape_fbref_team_stats(self, team_name):
        """Scrape team statistics from FBref"""
        try:
            # Setup Chrome driver
            driver = webdriver.Chrome()
            
            # Clean team name for search (keep special characters for matching)
            search_name = team_name.replace(".", "").strip()
            
            # Try different search variations
            search_variations = [
                search_name,
                search_name.replace("1. ", ""),  # For cases like "1. FC Koln"
                search_name.split()[-1],  # Last word only
                " ".join(search_name.split()[1:])  # Remove first word
            ]
            
            team_url = None
            for search_term in search_variations:
                try:
                    # Navigate to FBref team search
                    search_url = f"https://fbref.com/en/search/search.fcgi?search={search_term}"
                    driver.get(search_url)
                    
                    # Wait for and click first team result
                    team_link = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.search-item-name a"))
                    )
                    # Check if the found team name matches our target
                    found_team = team_link.text.strip()
                    if (search_name.lower() in found_team.lower() or 
                        found_team.lower() in search_name.lower()):
                        team_url = team_link.get_attribute('href')
                        break
                except Exception as e:
                    print(f"Error searching for variation {search_term}: {e}")
                    continue
            
            if not team_url:
                print(f"Could not find team {team_name} on FBref")
                return None
            
            # Navigate to team page
            driver.get(team_url)
            
            # Wait for stats table
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "stats_standard_squads"))
            )
            
            # Parse the page content
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Get basic stats table
            stats_table = soup.find('table', {'id': 'stats_standard_squads'})
            if not stats_table:
                print(f"No stats table found for {team_name}")
                return None
                
            # Parse team statistics
            team_stats = {}
            rows = stats_table.find_all('tr')
            for row in rows[1:]:  # Skip header row
                cols = row.find_all(['th', 'td'])
                if len(cols) > 0:
                    team_stats = {
                        'matches_played': int(cols[3].text if cols[3].text else 0),
                        'goals_scored': int(cols[8].text if cols[8].text else 0),
                        'goals_against': int(cols[9].text if cols[9].text else 0),
                        'goal_diff': int(cols[10].text if cols[10].text else 0),
                        'points': int(cols[11].text if cols[11].text else 0),
                        'xg_for': float(cols[12].text if cols[12].text else 0),
                        'xg_against': float(cols[13].text if cols[13].text else 0),
                        'xg_diff': float(cols[14].text if cols[14].text else 0)
                    }
                    break
            
            if not team_stats:
                print(f"No stats found for {team_name}")
                return None
                
            return team_stats
            
        except Exception as e:
            print(f"Error scraping FBref data for {team_name}: {e}")
            return None
            
        finally:
            driver.quit()

    def __init__(self):
        self.teams = config.SOCCER_TEAMS
        self.leagues = config.SOCCER_LEAGUES
        self.understat = UnderstatClient()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_recent_matches(self, team_name, limit=5):
        """Get recent matches for a team from Understat"""
        try:
            understat = UnderstatClient()
            
            # Get team ID from Understat
            teams = understat.league_teams("epl")  # Start with EPL
            team_id = None
            
            for team in teams:
                if team_name.lower() in team['title'].lower():
                    team_id = team['id']
                    break
            
            if not team_id:
                teams = understat.league_teams("bundesliga")  # Try Bundesliga
                for team in teams:
                    if team_name.lower() in team['title'].lower():
                        team_id = team['id']
                        break
            
            if not team_id:
                return []
            
            # Get team fixtures
            fixtures = understat.team_fixtures(team_id)
            recent_matches = []
            
            for match in fixtures[-limit:]:
                if match['isResult']:  # Only completed matches
                    home_team = match['h']['title']
                    away_team = match['a']['title']
                    
                    is_home = home_team.lower() == team_name.lower()
                    opponent = away_team if is_home else home_team
                    
                    goals_for = int(match['goals']['h']) if is_home else int(match['goals']['a'])
                    goals_against = int(match['goals']['a']) if is_home else int(match['goals']['h'])
                    
                    result = 'W' if goals_for > goals_against else 'D' if goals_for == goals_against else 'L'
                    
                    recent_matches.append({
                        'opponent': opponent,
                        'home': is_home,
                        'result': result,
                        'goals_for': goals_for,
                        'goals_against': goals_against,
                        'xg_for': float(match['xG']['h'] if is_home else match['xG']['a']),
                        'xg_against': float(match['xG']['a'] if is_home else match['xG']['h']),
                        'date': match['datetime']
                    })
            
            return recent_matches
            
        except Exception as e:
            print(f"Error fetching match data from Understat: {e}")
            return []
    
    def get_team_data(self, team_name):
        """Get comprehensive team data for ML model"""
        recent_matches = self.get_recent_matches(team_name, 10)
        
        # Calculate team statistics from recent matches
        wins = sum(1 for match in recent_matches if match['result'] == 'W')
        draws = sum(1 for match in recent_matches if match['result'] == 'D')
        losses = sum(1 for match in recent_matches if match['result'] == 'L')
        
        total_goals = sum(match['goals_for'] for match in recent_matches)
        total_conceded = sum(match['goals_against'] for match in recent_matches)
        clean_sheets = sum(1 for match in recent_matches if match['goals_against'] == 0)
        
        return {
            'team_name': team_name,
            'recent_form': {
                'matches_played': len(recent_matches),
                'wins': wins,
                'draws': draws, 
                'losses': losses,
                'win_rate': wins / len(recent_matches) if recent_matches else 0,
                'goals_per_game': total_goals / len(recent_matches) if recent_matches else 0,
                'goals_conceded_per_game': total_conceded / len(recent_matches) if recent_matches else 0,
                'clean_sheets_rate': clean_sheets / len(recent_matches) if recent_matches else 0
            },
            'season_stats': self._get_season_stats(team_name),
            'home_away_split': self._get_home_away_stats(team_name),
            'recent_matches': recent_matches
        }
    
    def get_head_to_head(self, team1, team2, limit=10):
        """Get head-to-head record between two teams from real data source"""
        raise NotImplementedError("Implement real H2H fetching from Understat, FBref, or other free sources.")
    
    def get_top_players(self, team_name, limit=7):
        """Get top players from a team based on goals and assists from FBref"""
        try:
            # First get the team's page URL
            driver = webdriver.Chrome()
            
            try:
                search_url = f"https://fbref.com/en/search/search.fcgi?search={team_name}"
                driver.get(search_url)
                
                # Wait for and click first team result
                team_link = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.search-item-name a"))
                )
                team_url = team_link.get_attribute('href')
                driver.get(team_url)
                
                # Wait for squad stats table
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "stats_standard_squads"))
                )
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Find the squad stats table
                stats_table = soup.find('table', {'id': 'stats_standard_squads'})
                if not stats_table:
                    return []
                
                players = []
                rows = stats_table.find('tbody').find_all('tr')
                
                for row in rows:
                    cols = row.find_all(['th', 'td'])
                    if len(cols) > 8:
                        player_name = cols[0].find('a').text.strip()
                        
                        player_stats = {
                            'name': player_name,
                            'team': team_name,
                            'goals': int(cols[8].text) if cols[8].text else 0,
                            'assists': int(cols[9].text) if cols[9].text else 0,
                            'matches': int(cols[3].text) if cols[3].text else 0,
                            'minutes': int(cols[4].text) if cols[4].text else 0
                        }
                        
                        player_stats['goals_assists'] = player_stats['goals'] + player_stats['assists']
                        players.append(player_stats)
                
                # Sort by goals + assists and return top players
                players.sort(key=lambda x: x['goals_assists'], reverse=True)
                return players[:limit]
                
            finally:
                driver.quit()
                
        except Exception as e:
            print(f"Error fetching top players: {e}")
            return []
    
    def get_league_standings(self, league_name):
        """Get current league standings from FBref"""
        try:
            # Map league names to FBref URLs
            league_urls = {
                'Premier League': 'https://fbref.com/en/comps/9/Premier-League-Stats',
                'La Liga': 'https://fbref.com/en/comps/12/La-Liga-Stats',
                'Bundesliga': 'https://fbref.com/en/comps/20/Bundesliga-Stats',
                'Serie A': 'https://fbref.com/en/comps/11/Serie-A-Stats',
                'Ligue 1': 'https://fbref.com/en/comps/13/Ligue-1-Stats'
            }
            
            if league_name not in league_urls:
                return []
                
            driver = webdriver.Chrome()
            try:
                driver.get(league_urls[league_name])
                
                # Wait for standings table
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "results2023-202491_overall"))
                )
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                standings_table = soup.find('table', {'id': 'results2023-202491_overall'})
                
                if not standings_table:
                    return []
                    
                standings = []
                rows = standings_table.find_all('tr')[1:]  # Skip header row
                
                for row in rows:
                    cols = row.find_all(['th', 'td'])
                    if len(cols) > 10:
                        team_name = cols[0].find('a').text.strip()
                        
                        standings.append({
                            'position': int(cols[0].text.strip()),
                            'team': team_name,
                            'matches_played': int(cols[3].text),
                            'wins': int(cols[4].text),
                            'draws': int(cols[5].text),
                            'losses': int(cols[6].text),
                            'goals_for': int(cols[7].text),
                            'goals_against': int(cols[8].text),
                            'goal_diff': int(cols[9].text),
                            'points': int(cols[10].text)
                        })
                
                return standings
                
            finally:
                driver.quit()
                
        except Exception as e:
            print(f"Error fetching league standings: {e}")
            return []
    
    def _get_season_stats(self, team_name):
        """Get season statistics from Understat"""
        try:
            understat = UnderstatClient()
            
            # Get team ID from Understat
            teams = understat.league_teams("epl")  # Start with EPL
            team_id = None
            
            for team in teams:
                if team_name.lower() in team['title'].lower():
                    team_id = team['id']
                    break
            
            if not team_id:
                teams = understat.league_teams("bundesliga")  # Try Bundesliga
                for team in teams:
                    if team_name.lower() in team['title'].lower():
                        team_id = team['id']
                        break
            
            if not team_id:
                return {}
            
            # Get team stats
            team_stats = understat.team(team_id)
            
            if not team_stats:
                return {}
            
            current_season = team_stats['history'][-1]  # Latest season data
            
            # Calculate clean sheets from game data
            matches = understat.team_fixtures(team_id)
            clean_sheets = sum(1 for match in matches if match['isResult'] and
                             ((match['h']['title'] == team_name and int(match['goals']['a']) == 0) or
                              (match['a']['title'] == team_name and int(match['goals']['h']) == 0)))
            
            return {
                'games_played': current_season['wins'] + current_season['draws'] + current_season['loses'],
                'wins': current_season['wins'],
                'draws': current_season['draws'],
                'losses': current_season['loses'],
                'goals_for': current_season['scored'],
                'goals_against': current_season['missed'],
                'clean_sheets': clean_sheets
            }
            
        except Exception as e:
            print(f"Error fetching season stats: {e}")
            return {}
    
    def _get_home_away_stats(self, team_name):
        """Get home/away statistics from Understat"""
        try:
            understat = UnderstatClient()
            
            # Get team ID from Understat
            teams = understat.league_teams("epl")  # Start with EPL
            team_id = None
            
            for team in teams:
                if team_name.lower() in team['title'].lower():
                    team_id = team['id']
                    break
            
            if not team_id:
                teams = understat.league_teams("bundesliga")  # Try Bundesliga
                for team in teams:
                    if team_name.lower() in team['title'].lower():
                        team_id = team['id']
                        break
            
            if not team_id:
                return {}
            
            # Get team fixtures
            fixtures = understat.team_fixtures(team_id)
            
            home_stats = {'played': 0, 'wins': 0, 'draws': 0, 'losses': 0, 'goals_for': 0, 'goals_against': 0}
            away_stats = {'played': 0, 'wins': 0, 'draws': 0, 'losses': 0, 'goals_for': 0, 'goals_against': 0}
            
            for match in fixtures:
                if not match['isResult']:
                    continue
                
                is_home = match['h']['title'] == team_name
                goals_for = int(match['goals']['h'] if is_home else match['goals']['a'])
                goals_against = int(match['goals']['a'] if is_home else match['goals']['h'])
                
                stats = home_stats if is_home else away_stats
                stats['played'] += 1
                stats['goals_for'] += goals_for
                stats['goals_against'] += goals_against
                
                if goals_for > goals_against:
                    stats['wins'] += 1
                elif goals_for < goals_against:
                    stats['losses'] += 1
                else:
                    stats['draws'] += 1
            
            return {
                'home': home_stats,
                'away': away_stats
            }
            
        except Exception as e:
            print(f"Error fetching home/away stats: {e}")
            return {'home': {}, 'away': {}}
    
    # All mock/random data generation methods removed. Implement real data fetching methods only.
    
    def get_understat_data(self, team_name):
        """Get xG data from Understat"""
        try:
            understat = UnderstatClient()
            
            # Get team ID from Understat
            teams = understat.league_teams("epl")  # Start with EPL
            team_id = None
            
            for team in teams:
                if team_name.lower() in team['title'].lower():
                    team_id = team['id']
                    break
            
            if not team_id:
                teams = understat.league_teams("bundesliga")  # Try Bundesliga
                for team in teams:
                    if team_name.lower() in team['title'].lower():
                        team_id = team['id']
                        break
            
            if not team_id:
                return {}
            
            # Get team stats
            team_stats = understat.team(team_id)
            
            if not team_stats:
                return {}
            
            return {
                'xg_for': round(float(team_stats['history'][-1]['xG']), 2),
                'xg_against': round(float(team_stats['history'][-1]['xGA']), 2),
                'xg_difference': round(float(team_stats['history'][-1]['xG']) - float(team_stats['history'][-1]['xGA']), 2)
            }
            
        except Exception as e:
            print(f"Error fetching Understat data: {e}")
            return {}