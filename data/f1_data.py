import pandas as pd
import requests
from datetime import datetime, timedelta
import fastf1
import warnings
warnings.filterwarnings('ignore')

class F1DataCollector:
    """Real Formula 1 data collection using FastF1 and Ergast API"""
    
    def __init__(self):
        self.ergast_base = "https://ergast.com/api/f1"
        self.current_year = datetime.now().year
        
        # Enable FastF1 cache for better performance
        fastf1.Cache.enable_cache('f1_cache')
    
    def get_current_season_schedule(self):
        """Get current F1 season schedule"""
        try:
            url = f"{self.ergast_base}/{self.current_year}.json"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                races = data['MRData']['RaceTable']['Races']
                
                schedule = []
                for race in races:
                    race_date = datetime.strptime(race['date'], '%Y-%m-%d')
                    
                    schedule.append({
                        'round': int(race['round']),
                        'race_name': race['raceName'],
                        'circuit_name': race['Circuit']['circuitName'],
                        'country': race['Circuit']['Location']['country'],
                        'date': race['date'],
                        'time': race.get('time', 'TBD'),
                        'circuit_id': race['Circuit']['circuitId'],
                        'race_date_obj': race_date
                    })
                
                return sorted(schedule, key=lambda x: x['round'])
            
        except Exception as e:
            print(f"Error fetching F1 schedule: {e}")
            return []
    
    def get_current_standings(self):
        """Get current driver and constructor standings"""
        try:
            # Driver standings
            drivers_url = f"{self.ergast_base}/{self.current_year}/driverStandings.json"
            drivers_response = requests.get(drivers_url, timeout=10)
            
            driver_standings = []
            if drivers_response.status_code == 200:
                data = drivers_response.json()
                standings = data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
                
                for standing in standings:
                    driver = standing['Driver']
                    constructor = standing['Constructors'][0]
                    
                    driver_standings.append({
                        'position': int(standing['position']),
                        'driver_id': driver['driverId'],
                        'given_name': driver['givenName'],
                        'family_name': driver['familyName'],
                        'full_name': f"{driver['givenName']} {driver['familyName']}",
                        'team': constructor['name'],
                        'points': int(standing['points']),
                        'wins': int(standing['wins']),
                        'nationality': driver['nationality']
                    })
            
            # Constructor standings
            constructors_url = f"{self.ergast_base}/{self.current_year}/constructorStandings.json"
            constructors_response = requests.get(constructors_url, timeout=10)
            
            constructor_standings = []
            if constructors_response.status_code == 200:
                data = constructors_response.json()
                standings = data['MRData']['StandingsTable']['StandingsLists'][0]['ConstructorStandings']
                
                for standing in standings:
                    constructor = standing['Constructor']
                    
                    constructor_standings.append({
                        'position': int(standing['position']),
                        'constructor_id': constructor['constructorId'],
                        'name': constructor['name'],
                        'nationality': constructor['nationality'],
                        'points': int(standing['points']),
                        'wins': int(standing['wins'])
                    })
            
            return {
                'drivers': driver_standings,
                'constructors': constructor_standings
            }
            
        except Exception as e:
            print(f"Error fetching standings: {e}")
            return []
    
    def get_race_results(self, year, round_number):
        """Get race results using FastF1"""
        try:
            # Load race session
            session = fastf1.get_session(year, round_number, 'R')
            session.load()
            
            # Get race results
            results = session.results
            
            race_data = []
            for idx, driver in results.iterrows():
                race_data.append({
                    'position': driver['Position'],
                    'driver_number': driver['DriverNumber'],
                    'driver_name': f"{driver['FirstName']} {driver['LastName']}",
                    'team': driver['TeamName'],
                    'grid_position': driver['GridPosition'],
                    'time': str(driver['Time']) if pd.notna(driver['Time']) else 'DNF',
                    'status': driver['Status'],
                    'points': driver['Points']
                })
            
            return race_data
            
        except Exception as e:
            print(f"Error fetching race results with FastF1: {e}")
            return []
    
    def get_qualifying_results(self, year, round_number):
        """Get qualifying results using FastF1"""
        try:
            session = fastf1.get_session(year, round_number, 'Q')
            session.load()
            
            results = session.results
            
            qualifying_data = []
            for idx, driver in results.iterrows():
                qualifying_data.append({
                    'position': driver['Position'],
                    'driver_name': f"{driver['FirstName']} {driver['LastName']}",
                    'team': driver['TeamName'],
                    'q1_time': str(driver['Q1']) if pd.notna(driver['Q1']) else 'No Time',
                    'q2_time': str(driver['Q2']) if pd.notna(driver['Q2']) else 'No Time',
                    'q3_time': str(driver['Q3']) if pd.notna(driver['Q3']) else 'No Time'
                })
            
            return qualifying_data
            
        except Exception as e:
            print(f"Error fetching qualifying results: {e}")
            return []
    
    def get_driver_performance_at_circuit(self, driver_id, circuit_id, years=5):
        """Get driver performance history at specific circuit"""
        try:
            performances = []
            current_year = datetime.now().year
            
            for year in range(current_year - years, current_year):
                url = f"{self.ergast_base}/{year}/circuits/{circuit_id}/drivers/{driver_id}/results.json"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    races = data['MRData']['RaceTable']['Races']
                    
                    for race in races:
                        if race['Results']:
                            result = race['Results'][0]
                            performances.append({
                                'year': year,
                                'race_name': race['raceName'],
                                'position': result['position'],
                                'grid': result['grid'],
                                'points': result['points'],
                                'status': result['status']
                            })
            
            return performances
            
        except Exception as e:
            print(f"Error fetching circuit performance: {e}")
            return []
    
    def get_lap_times(self, year, round_number, driver_number):
        """Get detailed lap times using FastF1"""
        try:
            session = fastf1.get_session(year, round_number, 'R')
            session.load()
            
            driver_laps = session.laps.pick_driver(driver_number)
            
            lap_data = []
            for idx, lap in driver_laps.iterrows():
                lap_data.append({
                    'lap_number': lap['LapNumber'],
                    'lap_time': str(lap['LapTime']),
                    'sector1': str(lap['Sector1Time']),
                    'sector2': str(lap['Sector2Time']), 
                    'sector3': str(lap['Sector3Time']),
                    'tire_compound': lap['Compound'],
                    'tire_life': lap['TyreLife']
                })
            
            return lap_data
            
        except Exception as e:
            print(f"Error fetching lap times: {e}")
            return []
    
    def get_weather_data(self, year, round_number):
        """Get race weekend weather data"""
        try:
            session = fastf1.get_session(year, round_number, 'R')
            session.load()
            
            weather = session.weather_data
            
            if not weather.empty:
                return {
                    'air_temp': weather['AirTemp'].mean(),
                    'track_temp': weather['TrackTemp'].mean(),
                    'humidity': weather['Humidity'].mean(),
                    'rainfall': weather['Rainfall'].any(),
                    'wind_speed': weather['WindSpeed'].mean()
                }
            
        except Exception as e:
            print(f"Error fetching weather data: {e}")
            
        return None
