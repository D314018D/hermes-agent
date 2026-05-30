#!/usr/bin/env python3
"""
Sydney Weather Forecast Scheduler
Runs daily at 8:00 AM to fetch and send Sydney's weather forecast.
"""

import sys
import os

# Explicitly set venv environment variable to activate it
os.environ['VIRTUAL_ENV'] = os.path.expanduser('~/.hermes/hermes-agent/venv')

import requests
from datetime import datetime


def openweather_api_key():
    """Load the OpenWeatherMap API key from local environment only."""
    try:
        from dotenv import load_dotenv

        load_dotenv(os.path.expanduser("~/.hermes/.env"))
    except Exception:
        pass
    api_key = os.environ.get("OPENWEATHER_API_KEY", "").strip()
    if not api_key:
        print("Error: OPENWEATHER_API_KEY is not set in the environment or ~/.hermes/.env")
        return None
    return api_key


def fetch_sydney_weather():
    """Fetch weather data from OpenWeatherMap API."""
    api_key = openweather_api_key()
    if not api_key:
        return None
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': 'Sydney, Australia',
        'appid': api_key,
        'units': 'metric'
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather: {e}")
        return None

def fetch_10_day_forecast():
    """Fetch 10-day forecast from OpenWeatherMap API."""
    api_key = openweather_api_key()
    if not api_key:
        return None
    base_url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        'q': 'Sydney, Australia',
        'appid': api_key,
        'units': 'metric'
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching forecast: {e}")
        return None

def format_weather_report(current_weather, forecast_data):
    """Format the weather report for the current session."""
    if not current_weather:
        print("❌ Unable to fetch current weather data")
        return None
    
    if not forecast_data:
        print("⚠️  No forecast data available")
        return None
    
    # Current weather
    current = current_weather
    current_temp = current['main']['temp']
    current_condition = current['weather'][0]['description']
    current_humidity = current['main']['humidity']
    current_wind = current['wind']['speed']
    
    # Generate daily forecast summary
    daily_forecasts = []
    for entry in forecast_data['list']:
        dt = datetime.fromtimestamp(entry['dt'])
        temp_min = entry['main']['temp_min']
        temp_max = entry['main']['temp_max']
        condition = entry['weather'][0]['description']
        daily_forecasts.append({
            'date': dt.strftime('%A, %d %B'),
            'min_temp': temp_min,
            'max_temp': temp_max,
            'condition': condition
        })
    
    # Format the report
    report = f"""🌤️  Sydney Weather Report
{'='*50}
Current Weather (as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
{'='*50}
    Temperature: {current_temp}°C
    Condition:   {current_condition.capitalize()}
    Humidity:   {current_humidity}%
    Wind:       {current_wind} m/s

📅  10-Day Forecast
{'='*50}
"""
    
    for i, day in enumerate(daily_forecasts[:7], 1):  # Show first 7 days
        report += f"""Day {i}: {day['date']}
   Min: {day['min_temp']}°C | Max: {day['max_temp']}°C
   Condition: {day['condition'].capitalize()}
"""
    
    report += f"""{'='*50}
Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    return report

if __name__ == '__main__':
    print("🌤️  Fetching Sydney weather...")
    print("-" * 50)
    
    weather = fetch_sydney_weather()
    forecast = fetch_10_day_forecast()
    
    report = format_weather_report(weather, forecast)
    
    if report:
        print("\n" + report)
        print("\n✓ Weather report generated successfully")
