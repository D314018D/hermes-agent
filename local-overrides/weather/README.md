# Local Weather Overrides

This folder keeps Richard's local Sydney weather cron notes and captured weather
output outside the live Hermes source root.

These files are local operational artifacts, not upstream Hermes source:

- `sydney_crontab.txt`
- `sydney-weather-may-18-2026.txt`

The weather script reads its OpenWeatherMap key from `OPENWEATHER_API_KEY` or
`/Users/rl_home/.hermes/.env`; do not store API keys in this folder.

Rollback: move the files back to the repository root if an existing local cron
entry expects those exact paths.
