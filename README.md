# ASU Housing Bot

A Python + Selenium automation bot that logs into the ASU StarRez housing
portal, continuously checks room availability, and fires off real-time
alerts (voice + text) the moment a spot opens up — so you don't have to
sit there refreshing the page.

## Why

ASU housing assignments open up once a year and the good units disappear
within minutes. Manually refreshing the portal isn't a real strategy, so
this bot does the watching for you and tells you the second something
changes.

## How it works

1. Logs into the housing portal via ASU SSO (handles the Duo 2FA wait)
2. Navigates to the room change / availability page
3. Refreshes on an interval and checks the page for a "no rooms available"
   message
4. As soon as that message disappears, it fires a local voice alert and
   sends a text message via an SMS-to-email carrier gateway

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in your real values
```

Download the [chromedriver](https://googlechromelabs.github.io/chrome-for-testing/)
that matches your installed Chrome version and place it in this folder
(or point `CHROMEDRIVER_PATH` in `.env` at wherever you keep it).

## Run

```bash
python check_housing.py
```

## Notes

- Built and used in April 2025 to catch a high-demand housing assignment
  in real time instead of manually refreshing.
- All credentials and personal info are pulled from environment variables
  — nothing is hardcoded in the script.