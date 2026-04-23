# Hermes Native Gateway Integration

For external channels, prefer Hermes Agent's built-in messaging gateway.

## Use Hermes Native Platforms

- Weixin for personal WeChat
- WeCom for Enterprise WeChat
- Email for inbound/outbound mail

These are already present in the installed Hermes codebase under:

- `/Users/rl_home/.hermes/hermes-agent/gateway/platforms/weixin.py`
- `/Users/rl_home/.hermes/hermes-agent/gateway/platforms/wecom.py`
- `/Users/rl_home/.hermes/hermes-agent/gateway/platforms/email.py`

## Why

- session lifecycle is already handled by Hermes
- message delivery and retries already exist
- media, voice, and gateway hooks are already part of Hermes
- avoids duplicating transport logic in the MVP layer

## Recommended Topology

- Browser GUI:
  `GUI -> router_server.py -> hermes_supervisor.py -> oMLX`
- External messaging:
  `Weixin / WeCom / Email -> Hermes Gateway -> Hermes -> oMLX`

## Hermes Commands

Use Hermes to configure and manage the gateway:

```bash
hermes gateway setup
hermes gateway install
hermes gateway start
hermes gateway status
```

## Relevant Environment Variables

Examples seen in the Hermes gateway config:

- WeCom:
  `WECOM_BOT_ID`
  `WECOM_SECRET`
  `WECOM_WEBSOCKET_URL`
- WeCom Callback:
  `WECOM_CALLBACK_CORP_ID`
  `WECOM_CALLBACK_CORP_SECRET`
- Weixin:
  `WEIXIN_TOKEN`
  `WEIXIN_ACCOUNT_ID`
  `WEIXIN_BASE_URL`
- Email:
  configured through Hermes gateway config and setup flow

## Practical Rule

If the traffic comes from a public or external channel, let Hermes Gateway own the connection.

If the traffic comes from the local browser MVP, let the lightweight router own the request normalization.
