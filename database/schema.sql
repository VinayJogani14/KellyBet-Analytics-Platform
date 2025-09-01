-- Kelly Criterion Sports Betting App Database Schema

-- Bets table - stores all betting activity
CREATE TABLE IF NOT EXISTS bets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    sport TEXT NOT NULL CHECK (sport IN ('soccer', 'tennis', 'cricket', 'f1')),
    market_type TEXT NOT NULL,
    team1 TEXT,
    team2 TEXT,
    player_name TEXT,
    bet_type TEXT NOT NULL,
    odds INTEGER NOT NULL,
    stake REAL NOT NULL CHECK (stake >= 0),
    win_probability REAL NOT NULL CHECK (win_probability >= 0 AND win_probability <= 1),
    kelly_fraction REAL NOT NULL CHECK (kelly_fraction >= 0),
    expected_value REAL NOT NULL,
    edge REAL NOT NULL,
    result TEXT CHECK (result IN ('win', 'loss', 'cashout', 'void')),
    payout REAL DEFAULT 0 CHECK (payout >= 0),
    profit_loss REAL DEFAULT 0,
    bankroll_before REAL NOT NULL CHECK (bankroll_before >= 0),
    bankroll_after REAL NOT NULL CHECK (bankroll_after >= 0)
);

-- Bankroll history - tracks all bankroll changes
CREATE TABLE IF NOT EXISTS bankroll_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    amount REAL NOT NULL CHECK (amount >= 0),
    change_amount REAL NOT NULL,
    change_type TEXT NOT NULL CHECK (change_type IN ('bet_win', 'bet_loss', 'deposit', 'withdrawal', 'manual_adjustment')),
    description TEXT
);

-- Match data - stores historical match information
CREATE TABLE IF NOT EXISTS match_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sport TEXT NOT NULL CHECK (sport IN ('soccer', 'tennis', 'cricket', 'f1')),
    team1 TEXT NOT NULL,
    team2 TEXT NOT NULL,
    date TEXT NOT NULL,
    result TEXT,
    score TEXT,
    venue TEXT,
    league TEXT,
    season TEXT DEFAULT '2024-25',
    additional_info TEXT, -- JSON field for sport-specific data
    last_updated TEXT NOT NULL
);

-- Player statistics
CREATE TABLE IF NOT EXISTS player_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sport TEXT NOT NULL CHECK (sport IN ('soccer', 'tennis', 'cricket', 'f1')),
    player_name TEXT NOT NULL,
    team TEXT,
    season TEXT NOT NULL DEFAULT '2024-25',
    games_played INTEGER DEFAULT 0 CHECK (games_played >= 0),
    goals INTEGER DEFAULT 0 CHECK (goals >= 0),
    assists INTEGER DEFAULT 0 CHECK (assists >= 0),
    points INTEGER DEFAULT 0 CHECK (points >= 0),
    wins INTEGER DEFAULT 0 CHECK (wins >= 0),
    losses INTEGER DEFAULT 0 CHECK (losses >= 0),
    other_stats TEXT, -- JSON field for additional stats
    last_updated TEXT NOT NULL
);

-- Odds history - stores historical odds data
CREATE TABLE IF NOT EXISTS odds_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sport TEXT NOT NULL CHECK (sport IN ('soccer', 'tennis', 'cricket', 'f1')),
    match_id TEXT NOT NULL,
    bookmaker TEXT NOT NULL,
    market TEXT NOT NULL,
    odds INTEGER NOT NULL,
    timestamp TEXT NOT NULL
);

-- User settings and preferences
CREATE TABLE IF NOT EXISTS user_settings (
    id INTEGER PRIMARY KEY,
    setting_key TEXT UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    last_updated TEXT NOT NULL
);

-- Kelly simulation results
CREATE TABLE IF NOT EXISTS simulations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sport TEXT NOT NULL,
    simulation_type TEXT NOT NULL,
    initial_bankroll REAL NOT NULL,
    final_bankroll REAL NOT NULL,
    num_bets INTEGER NOT NULL,
    win_rate REAL NOT NULL,
    roi REAL NOT NULL,
    max_drawdown REAL NOT NULL,
    kelly_modifier REAL NOT NULL,
    parameters TEXT, -- JSON field for simulation parameters
    created_at TEXT NOT NULL
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_bets_sport_timestamp ON bets(sport, timestamp);
CREATE INDEX IF NOT EXISTS idx_bets_result ON bets(result);
CREATE INDEX IF NOT EXISTS idx_match_data_sport_date ON match_data(sport, date);
CREATE INDEX IF NOT EXISTS idx_match_data_teams ON match_data(team1, team2);
CREATE INDEX IF NOT EXISTS idx_player_stats_name_season ON player_stats(player_name, season);
CREATE INDEX IF NOT EXISTS idx_odds_history_match_timestamp ON odds_history(match_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_bankroll_history_timestamp ON bankroll_history(timestamp);

-- Insert default user settings
INSERT OR IGNORE INTO user_settings (setting_key, setting_value, last_updated) VALUES
('default_bankroll', '5000.00', datetime('now')),
('default_kelly_fraction', 'Half Kelly', datetime('now')),
('risk_tolerance', 'medium', datetime('now')),
('preferred_sports', '["soccer", "tennis"]', datetime('now')),
('theme', 'light', datetime('now'));

-- Create views for common queries
CREATE VIEW IF NOT EXISTS betting_summary AS
SELECT 
    sport,
    COUNT(*) as total_bets,
    SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) as losses,
    ROUND(AVG(CASE WHEN result IN ('win', 'loss') THEN 
        CASE WHEN result = 'win' THEN 1.0 ELSE 0.0 END END) * 100, 2) as win_percentage,
    ROUND(SUM(profit_loss), 2) as total_profit_loss,
    ROUND(AVG(stake), 2) as avg_stake,
    ROUND(AVG(odds), 0) as avg_odds,
    ROUND(SUM(profit_loss) / SUM(stake) * 100, 2) as roi_percentage
FROM bets 
WHERE result IN ('win', 'loss')
GROUP BY sport;

CREATE VIEW IF NOT EXISTS monthly_performance AS
SELECT 
    strftime('%Y-%m', timestamp) as month,
    sport,
    COUNT(*) as bets_count,
    SUM(profit_loss) as monthly_pnl,
    AVG(bankroll_after) as avg_bankroll
FROM bets
WHERE result IN ('win', 'loss')
GROUP BY strftime('%Y-%m', timestamp), sport
ORDER BY month DESC;

-- Triggers for data integrity
CREATE TRIGGER IF NOT EXISTS update_bankroll_history 
AFTER INSERT ON bets
WHEN NEW.result IN ('win', 'loss', 'cashout')
BEGIN
    INSERT INTO bankroll_history (timestamp, amount, change_amount, change_type, description)
    VALUES (
        NEW.timestamp,
        NEW.bankroll_after,
        NEW.profit_loss,
        CASE 
            WHEN NEW.result = 'win' THEN 'bet_win'
            WHEN NEW.result = 'loss' THEN 'bet_loss'
            ELSE 'bet_cashout'
        END,
        'Bet: ' || NEW.bet_type || ' (' || NEW.sport || ')'
    );
END;

-- Trigger to prevent negative bankroll
CREATE TRIGGER IF NOT EXISTS prevent_negative_bankroll
BEFORE INSERT ON bets
WHEN NEW.bankroll_after < 0
BEGIN
    SELECT RAISE(ABORT, 'Bankroll cannot be negative');
END;