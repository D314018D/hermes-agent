# Local Weather API Key

Date: 2026-05-30

## Reason

`sydney_weather_fetcher.py` is a local utility for Richard's Mac mini weather cron workflow. The OpenWeatherMap credential must not be stored in source code, committed to Git, or copied into upstream Hermes.

## Files changed

- `sydney_weather_fetcher.py`
- `docs/local-weather-api-key.md`

## Local configuration

Set the key outside source control:

```bash
OPENWEATHER_API_KEY=...
```

The script also tries to load `/Users/rl_home/.hermes/.env`, so the preferred local setup is:

```bash
OPENWEATHER_API_KEY=<stored locally, not committed>
```

## Upgrade impact

Low. This is a local utility change on `richard/hermes-local`; it removes a secret from source and does not change Hermes core routing, gateway behavior, provider configuration, or plugin loading.

## Rollback

Restore the prior script from Git if needed, but do not reintroduce a hardcoded key. If the cron job stops fetching weather, confirm `OPENWEATHER_API_KEY` exists in the cron environment or in `/Users/rl_home/.hermes/.env`.
