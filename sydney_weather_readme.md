# Sydney Weather Forecast Scheduler

This scheduler fetches Sydney's weather forecast and sends it to the current session every day at 8:00 AM.

## Files

- `sydney_weather_fetcher.py` - Python script that fetches and formats weather data
- `sydney_weather_crontab` - Cron job entry for scheduled execution
- `sydney_weather_systemd_service.sh` - Systemd service file (alternative to cron)
- `sydney_weather_readme.md` - This file

## Quick Setup

### Option 1: Using Cron (Simplest)

```bash
crontab /Users/rl_home/.hermes/hermes-agent/sydney_weather_crontab
```

### Option 2: Using Systemd (More Reliable)

```bash
# Copy service file to systemd directory
cp /Users/rl_home/.hermes/hermes-agent/sydney_weather_systemd_service.sh /etc/systemd/system/

# Enable and start the service
systemctl enable sydney-weather.service
systemctl start sydney-weather.service

# Set up the timer
# Create the timer file and enable it
```

## Dependencies

- Python 3.x
- requests library (`pip install requests`)

## API Key Required

You'll need an OpenWeatherMap API key. Edit `sydney_weather_fetcher.py` and replace:

```python
'YOUR_API_KEY_HERE'  # Add your OpenWeatherMap API key
```

Get one at: https://openweathermap.org/api

## Testing

Before enabling the scheduler, test the script manually:

```bash
cd /Users/rl_home/.hermes/hermes-agent
python3 sydney_weather_fetcher.py
```

## Logs

Check the execution log:
```bash
tail -f /Users/rl_home/.hermes/hermes-agent/sydney_weather.log
```

## Output Format

The script outputs a formatted weather report including:
- Current temperature, condition, humidity, wind speed
- 7-day forecast with min/max temperatures and conditions

## Cron Schedule

- **Time**: 08:00 AM daily
- **Cron entry**: `0 8 * * *`

## Troubleshooting

If the script fails:
1. Check the log file for errors
2. Verify your API key is correct
3. Ensure the script has execute permissions
4. Check cron job is installed: `crontab -l`
