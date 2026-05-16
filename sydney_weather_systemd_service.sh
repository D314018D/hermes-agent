# Sydney Weather Scheduler - Systemd Service and Timer
# Install daily at 8:00 AM

# Service file: /etc/systemd/system/sydney-weather.service
[Unit]
Description=Sydney Weather Forecast Scheduler
After=network.target

[Service]
Type=oneshot
User=rl_home
WorkingDirectory=/Users/rl_home/.hermes/hermes-agent
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/bin/python3 sydney_weather_fetcher.py
RemainAfterExit=no

[Install]
WantedBy=multi-user.target

# Timer file: /etc/systemd/system/sydney-weather.timer
[Unit]
Description=Run Sydney Weather Forecast at 8:00 AM daily
TimerStartTimeCalendar=many

[Timer]
OnCalendar=*:08:00
Unit=sydney-weather.service
Persistent=true

[Install]
WantedBy=timers.target
