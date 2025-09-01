import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
THE_ODDS_API_KEY = os.getenv('THE_ODDS_API_KEY', '')
THE_ODDS_API_URL = 'https://api.the-odds-api.com/v4'

CRICAPI_KEY=os.getenv('CRICAPI_KEY', '')

# Database Configuration
DATABASE_PATH = 'database/kelly_betting.db'

# Default Settings
DEFAULT_BANKROLL = 5000.00
MIN_BANKROLL = 100.00
MAX_BANKROLL_PERCENTAGE = 100

# Soccer Configuration
SOCCER_LEAGUES = {
    'UEFA Champions League': 'soccer_uefa_champions_league',
    'English Premier League': 'soccer_epl',
    'Spanish La Liga': 'soccer_spain_la_liga',
    'Italian Serie A': 'soccer_italy_serie_a', 
    'German Bundesliga': 'soccer_germany_bundesliga',
    'French Ligue 1': 'soccer_france_ligue_one'
}

SOCCER_TEAMS = {
    'Premier League': [
        'Arsenal', 'Aston Villa', 'Bournemouth', 'Brentford', 'Brighton', 
        'Burnley', 'Chelsea', 'Crystal Palace', 'Everton', 'Fulham',
        'Liverpool', 'Luton Town', 'Manchester City', 'Manchester United',
        'Newcastle United', 'Nottingham Forest', 'Sheffield United', 
        'Tottenham', 'West Ham', 'Wolverhampton'
    ],
    'La Liga': [
        'Athletic Bilbao', 'Atletico Madrid', 'Barcelona', 'Celta Vigo',
        'Getafe', 'Girona', 'Granada', 'Las Palmas', 'Mallorca', 
        'Osasuna', 'Rayo Vallecano', 'Real Betis', 'Real Madrid',
        'Real Sociedad', 'Sevilla', 'Valencia', 'Villarreal', 'Alaves'
    ],
    'Serie A': [
        'AC Milan', 'AS Roma', 'Atalanta', 'Bologna', 'Cagliari',
        'Empoli', 'Fiorentina', 'Frosinone', 'Genoa', 'Inter Milan',
        'Juventus', 'Lazio', 'Lecce', 'Monza', 'Napoli', 'Salernitana',
        'Sassuolo', 'Torino', 'Udinese', 'Verona'
    ],
    'Bundesliga': [
        'Bayern Munich', 'Borussia Dortmund', 'RB Leipzig', 'Union Berlin',
        'SC Freiburg', 'Bayer Leverkusen', 'Eintracht Frankfurt', 
        'VfL Wolfsburg', 'FC Augsburg', 'VfB Stuttgart', 'Borussia Monchengladbach',
        'FSV Mainz 05', '1. FC Koln', 'TSG Hoffenheim', 'Werder Bremen',
        'VfL Bochum', 'FC Heidenheim', 'SV Darmstadt'
    ],
    'Ligue 1': [
        'Paris Saint Germain', 'AS Monaco', 'Lille', 'Nice', 'Lens',
        'Marseille', 'Rennes', 'Lyon', 'Montpellier', 'Toulouse',
        'Strasbourg', 'Nantes', 'Reims', 'Brest', 'Le Havre',
        'Clermont Foot', 'Lorient', 'Metz'
    ]
}

SOCCER_MARKET_TYPES = [
    'Moneyline',
    'To Score or Assist', 
    'Over/Under 1.5 Goals',
    'Over/Under 2.5 Goals',
    'Both Teams to Score'
]

# Tennis Configuration
TENNIS_TOURNAMENTS = {
    'ATP': ['ATP Masters 1000', 'ATP 500', 'ATP 250', 'Grand Slam'],
    'WTA': ['WTA 1000', 'WTA 500', 'WTA 250', 'Grand Slam'],
    'Grand Slams': ['Australian Open', 'French Open', 'Wimbledon', 'US Open']
}

TENNIS_MARKET_TYPES = [
    'Match Winner',
    'Set Betting', 
    'Total Games Over/Under',
    'Total Aces Over/Under',
    'Total Double Faults Over/Under',
    'Exact Number of Sets',
    'Number of Tiebreaks',
    'Service Breaks',
    'Same Game Parlay #1',
    'Same Game Parlay #2'
]

# Cricket Configuration
CRICKET_FORMATS = {
    'Test Match': '5 days, unlimited overs',
    'ODI': '50 overs per side',
    'T20 International': '20 overs per side', 
    'T10': '10 overs per side',
    'The Hundred': '100 balls per side'
}

CRICKET_TOURNAMENTS = {
    'Test': ['World Test Championship', 'Bilateral Series'],
    'ODI': ['Cricket World Cup', 'Champions Trophy', 'Bilateral Series'],
    'T20': ['T20 World Cup', 'IPL', 'BBL', 'PSL', 'CPL'],
    'Domestic': ['First-Class', 'List A', 'T20 Leagues']
}

CRICKET_TEAMS = {
    'International': [
        'India', 'England', 'Australia', 'New Zealand', 'South Africa',
        'Pakistan', 'West Indies', 'Sri Lanka', 'Bangladesh', 'Afghanistan'
    ],
    'IPL': [
        'Mumbai Indians', 'Chennai Super Kings', 'Royal Challengers Bangalore',
        'Kolkata Knight Riders', 'Delhi Capitals', 'Punjab Kings',
        'Rajasthan Royals', 'Sunrisers Hyderabad', 'Gujarat Titans', 'Lucknow Super Giants'
    ]
}

CRICKET_MARKET_TYPES = [
    'Match Result', 'First Innings Lead', 'Total Match Runs Over/Under',
    'Individual Batsman Match Runs', 'Individual Bowler Match Wickets', 
    'Session Betting', 'Match Winner', 'Total Match Runs Over/Under',
    'Individual Batsman Runs', 'Method of Dismissal', 'Match Winner',
    'Same Game Parlay'
]

# Formula 1 Configuration
F1_DRIVERS = [
    'Max Verstappen (Red Bull)', 'Sergio Perez (Red Bull)',
    'Lewis Hamilton (Mercedes)', 'George Russell (Mercedes)',
    'Charles Leclerc (Ferrari)', 'Carlos Sainz (Ferrari)',
    'Lando Norris (McLaren)', 'Oscar Piastri (McLaren)',
    'Fernando Alonso (Aston Martin)', 'Lance Stroll (Aston Martin)',
    'Esteban Ocon (Alpine)', 'Pierre Gasly (Alpine)',
    'Alex Albon (Williams)', 'Logan Sargeant (Williams)',
    'Valtteri Bottas (Alfa Romeo)', 'Zhou Guanyu (Alfa Romeo)',
    'Kevin Magnussen (Haas)', 'Nico Hulkenberg (Haas)',
    'Yuki Tsunoda (AlphaTauri)', 'Nyck de Vries (AlphaTauri)'
]

F1_CIRCUITS = [
    'Bahrain International Circuit', 'Jeddah Corniche Circuit',
    'Albert Park Circuit', 'Baku City Circuit', 'Miami International Autodrome',
    'Imola Circuit', 'Monaco Circuit', 'Circuit de Barcelona-Catalunya',
    'Circuit Gilles Villeneuve', 'Red Bull Ring', 'Silverstone Circuit',
    'Hungaroring', 'Spa-Francorchamps', 'Zandvoort Circuit',
    'Monza Circuit', 'Marina Bay Street Circuit', 'Suzuka Circuit',
    'Losail International Circuit', 'Circuit of the Americas', 'Autodromo Hermanos Rodriguez',
    'Interlagos Circuit', 'Las Vegas Strip Circuit', 'Yas Marina Circuit'
]

F1_MARKET_TYPES = [
    'Race Winner',
    'Podium Finish',
    'Head-to-Head Battle',
    'Qualifying Position',
    'Points Finish',
    'Fastest Lap',
    'Same Race Parlay'
]

# Kelly Criterion Settings
KELLY_FRACTIONS = {
    'Quarter Kelly': 0.25,
    'Half Kelly': 0.5,
    'Full Kelly': 1.0
}

# Risk Assessment Thresholds
RISK_THRESHOLDS = {
    'LOW': 0.05,      # < 5% of bankroll
    'MEDIUM': 0.15,   # 5-15% of bankroll
    'HIGH': 0.15      # > 15% of bankroll
}

# Machine Learning Model Settings
ML_MODEL_CONFIG = {
    'test_size': 0.2,
    'random_state': 42,
    'cross_validation_folds': 5,
    'feature_importance_threshold': 0.01
}

# Visualization Settings
CHART_COLORS = {
    'primary': '#1f77b4',
    'success': '#2ca02c',
    'danger': '#d62728',
    'warning': '#ff7f0e',
    'info': '#17becf'
}

# Cache Settings
CACHE_DURATION = 3600  # 1 hour in seconds
MAX_CACHE_SIZE = 100

# Data Update Intervals (in hours)
DATA_UPDATE_INTERVALS = {
    'live_odds': 0.25,  # 15 minutes
    'match_data': 24,   # 1 day
    'player_stats': 168  # 1 week
}
