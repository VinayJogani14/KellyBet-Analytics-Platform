import sqlite3
import pandas as pd
from datetime import datetime
import os
import config

class DatabaseManager:
    def __init__(self):
        self.db_path = config.DATABASE_PATH
        self.ensure_db_directory()
    
    def ensure_db_directory(self):
        """Ensure database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def initialize_db(self):
        """Initialize database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create bets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                sport TEXT NOT NULL,
                market_type TEXT NOT NULL,
                team1 TEXT,
                team2 TEXT,
                player_name TEXT,
                bet_type TEXT NOT NULL,
                odds INTEGER NOT NULL,
                stake REAL NOT NULL,
                win_probability REAL NOT NULL,
                kelly_fraction REAL NOT NULL,
                expected_value REAL NOT NULL,
                edge REAL NOT NULL,
                result TEXT,
                payout REAL DEFAULT 0,
                profit_loss REAL DEFAULT 0,
                bankroll_before REAL NOT NULL,
                bankroll_after REAL NOT NULL
            )
        ''')
        
        # Create bankroll history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bankroll_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                amount REAL NOT NULL,
                change_amount REAL NOT NULL,
                change_type TEXT NOT NULL,
                description TEXT
            )
        ''')
        
        # Create match data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS match_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sport TEXT NOT NULL,
                team1 TEXT NOT NULL,
                team2 TEXT NOT NULL,
                date TEXT NOT NULL,
                result TEXT,
                score TEXT,
                venue TEXT,
                league TEXT,
                last_updated TEXT NOT NULL
            )
        ''')
        
        # Create player stats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sport TEXT NOT NULL,
                player_name TEXT NOT NULL,
                team TEXT,
                season TEXT NOT NULL,
                games_played INTEGER DEFAULT 0,
                goals INTEGER DEFAULT 0,
                assists INTEGER DEFAULT 0,
                points INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                other_stats TEXT,
                last_updated TEXT NOT NULL
            )
        ''')
        
        # Create odds history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS odds_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sport TEXT NOT NULL,
                match_id TEXT NOT NULL,
                bookmaker TEXT NOT NULL,
                market TEXT NOT NULL,
                odds INTEGER NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_bet(self, bet_data):
        """Save a bet to the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO bets (
                timestamp, sport, market_type, team1, team2, player_name,
                bet_type, odds, stake, win_probability, kelly_fraction,
                expected_value, edge, bankroll_before, bankroll_after
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            bet_data['timestamp'].isoformat(),
            bet_data.get('sport', ''),
            bet_data.get('market_type', ''),
            bet_data.get('team1', ''),
            bet_data.get('team2', ''),
            bet_data.get('player_name', ''),
            bet_data.get('bet_type', ''),
            bet_data.get('odds', 0),
            bet_data.get('stake', 0),
            bet_data.get('win_probability', 0),
            bet_data.get('kelly_fraction', 0),
            bet_data.get('expected_value', 0),
            bet_data.get('edge', 0),
            bet_data.get('bankroll_before', 0),
            bet_data.get('bankroll_after', 0)
        ))
        
        conn.commit()
        conn.close()
    
    def update_bet_result(self, bet_id, result, payout, profit_loss, new_bankroll):
        """Update bet result"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE bets 
            SET result = ?, payout = ?, profit_loss = ?, bankroll_after = ?
            WHERE id = ?
        ''', (result, payout, profit_loss, new_bankroll, bet_id))
        
        conn.commit()
        conn.close()
    
    def get_bet_history(self, sport=None, limit=None):
        """Get bet history"""
        conn = self.get_connection()
        
        query = "SELECT * FROM bets"
        params = []
        
        if sport:
            query += " WHERE sport = ?"
            params.append(sport)
        
        query += " ORDER BY timestamp DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def get_bankroll_history(self, limit=None):
        """Get bankroll history"""
        conn = self.get_connection()
        
        query = "SELECT * FROM bankroll_history ORDER BY timestamp DESC"
        params = []
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def save_bankroll_change(self, amount, change_amount, change_type, description=""):
        """Save bankroll change to history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO bankroll_history (timestamp, amount, change_amount, change_type, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), amount, change_amount, change_type, description))
        
        conn.commit()
        conn.close()
    
    def get_betting_stats(self, sport=None):
        """Get betting statistics"""
        conn = self.get_connection()
        
        query = "SELECT * FROM bets WHERE result IS NOT NULL"
        params = []
        
        if sport:
            query += " AND sport = ?"
            params.append(sport)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if df.empty:
            return {
                'total_bets': 0,
                'total_wins': 0,
                'total_losses': 0,
                'win_rate': 0,
                'total_profit_loss': 0,
                'average_odds': 0,
                'average_stake': 0,
                'roi': 0
            }
        
        stats = {
            'total_bets': len(df),
            'total_wins': len(df[df['result'] == 'win']),
            'total_losses': len(df[df['result'] == 'loss']),
            'win_rate': len(df[df['result'] == 'win']) / len(df) * 100,
            'total_profit_loss': df['profit_loss'].sum(),
            'average_odds': df['odds'].mean(),
            'average_stake': df['stake'].mean(),
            'roi': (df['profit_loss'].sum() / df['stake'].sum()) * 100 if df['stake'].sum() > 0 else 0
        }
        
        return stats
    
    def save_match_data(self, match_data):
        """Save match data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO match_data 
            (sport, team1, team2, date, result, score, venue, league, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            match_data.get('sport', ''),
            match_data.get('team1', ''),
            match_data.get('team2', ''),
            match_data.get('date', ''),
            match_data.get('result', ''),
            match_data.get('score', ''),
            match_data.get('venue', ''),
            match_data.get('league', ''),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_team_matches(self, team_name, sport, limit=5):
        """Get recent matches for a team"""
        conn = self.get_connection()
        
        query = '''
            SELECT * FROM match_data 
            WHERE (team1 = ? OR team2 = ?) AND sport = ?
            ORDER BY date DESC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=[team_name, team_name, sport, limit])
        conn.close()
        
        return df
    
    def save_player_stats(self, player_data):
        """Save player statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO player_stats 
            (sport, player_name, team, season, games_played, goals, assists, 
             points, wins, losses, other_stats, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            player_data.get('sport', ''),
            player_data.get('player_name', ''),
            player_data.get('team', ''),
            player_data.get('season', ''),
            player_data.get('games_played', 0),
            player_data.get('goals', 0),
            player_data.get('assists', 0),
            player_data.get('points', 0),
            player_data.get('wins', 0),
            player_data.get('losses', 0),
            player_data.get('other_stats', ''),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_player_stats(self, player_name, sport):
        """Get player statistics"""
        conn = self.get_connection()
        
        query = '''
            SELECT * FROM player_stats 
            WHERE player_name = ? AND sport = ?
            ORDER BY last_updated DESC
            LIMIT 1
        '''
        
        df = pd.read_sql_query(query, conn, params=[player_name, sport])
        conn.close()
        
        return df.iloc[0] if not df.empty else None
    
    def save_odds_data(self, odds_data):
        """Save odds data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for odds in odds_data:
            cursor.execute('''
                INSERT INTO odds_history 
                (sport, match_id, bookmaker, market, odds, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                odds.get('sport', ''),
                odds.get('match_id', ''),
                odds.get('bookmaker', ''),
                odds.get('market', ''),
                odds.get('odds', 0),
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
    
    def get_latest_odds(self, sport, match_id):
        """Get latest odds for a match"""
        conn = self.get_connection()
        
        query = '''
            SELECT * FROM odds_history 
            WHERE sport = ? AND match_id = ?
            ORDER BY timestamp DESC
        '''
        
        df = pd.read_sql_query(query, conn, params=[sport, match_id])
        conn.close()
        
        return df
    
    def get_recent_odds(self, sport, hours=24):
        """Get recent odds data within the specified hours"""
        conn = self.get_connection()
        
        cutoff_time = (datetime.now() - pd.Timedelta(hours=hours)).isoformat()
        
        query = '''
            SELECT DISTINCT match_id, sport, bookmaker, market, odds, timestamp
            FROM odds_history 
            WHERE sport = ? AND timestamp > ?
            ORDER BY timestamp DESC
        '''
        
        df = pd.read_sql_query(query, conn, params=[sport, cutoff_time])
        conn.close()
        
        odds_data = []
        for _, row in df.iterrows():
            odds_data.append({
                'sport': row['sport'],
                'match_id': row['match_id'],
                'bookmaker': row['bookmaker'],
                'market': row['market'],
                'odds': row['odds'],
                'timestamp': row['timestamp']
            })
        
        return odds_data
    
    def cleanup_old_data(self, days_to_keep=365):
        """Cleanup old data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - pd.Timedelta(days=days_to_keep)).isoformat()
        
        # Clean old odds data
        cursor.execute('DELETE FROM odds_history WHERE timestamp < ?', (cutoff_date,))
        
        # Clean old match data (keep more recent)
        match_cutoff = (datetime.now() - pd.Timedelta(days=days_to_keep//2)).isoformat()
        cursor.execute('DELETE FROM match_data WHERE last_updated < ?', (match_cutoff,))
        
        conn.commit()
        conn.close()
    
    def export_data(self, table_name, file_path):
        """Export table data to CSV"""
        conn = self.get_connection()
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()
        
        df.to_csv(file_path, index=False)
        return len(df)
    
    def get_database_stats(self):
        """Get database statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        tables = ['bets', 'bankroll_history', 'match_data', 'player_stats', 'odds_history']
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    
    def get_bets_by_sport(self, sport):
        """Get bet history for a specific sport"""
        conn = self.get_connection()
        
        query = "SELECT * FROM bets WHERE sport = ? ORDER BY timestamp DESC"
        df = pd.read_sql_query(query, conn, params=[sport])
        conn.close()
        
        # Convert to list of dictionaries
        bets = []
        for _, row in df.iterrows():
            bet = {
                'id': row['id'],
                'date': pd.to_datetime(row['timestamp']).strftime('%Y-%m-%d'),
                'sport': row['sport'],
                'market_type': row['market_type'],
                'team1': row['team1'],
                'team2': row['team2'],
                'bet_type': row['bet_type'],
                'odds': row['odds'],
                'stake': row['stake'],
                'win_probability': row['win_probability'],
                'kelly_fraction': row['kelly_fraction'],
                'expected_value': row['expected_value'],
                'edge': row['edge'],
                'result': row['result'],
                'payout': row['payout'],
                'profit_loss': row['profit_loss'],
                'bankroll_before': row['bankroll_before'],
                'bankroll_after': row['bankroll_after']
            }
            bets.append(bet)
        
        return bets