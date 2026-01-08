# Story Watch
Telegram story watcher built on Telethon. It can sweep your active feed, mark stories as watched (optionally read), and  react with a configurable emoji based on include/exclude selectors. Always be the first one to view your friends' stories!

## Quick start
1) Install requirements: `pip3 install -r requirements.txt`
2) Copy `.env.example` → `.env` and fill `TG_API_ID`, `TG_API_HASH`, `TG_SESSION` (and `REACTION_EMOJI` if needed)
3) Edit `CONFIG.py` to enable watching/reading/reacting and set selectors
4) Run: `python3 -m app.main`

## Configuration
- `WATCH_STORIES_ENABLED`, `READ_STORIES_ENABLED`, `REACT_STORIES_ENABLED` toggle behavior
- `CONTACTS_REFRESH_SECONDS` controls how often contact ids refresh when using `contact` selectors
- `INCLUDED_USERS`, `EXCLUDED_USERS`, `REACTIONS_EXCLUDED` accept user ids or groups: `user`, `contact`, `channel`, `chat`, `all` (expands to user+contact+channel+chat)
- `REACTION_EMOJI` can be a normal emoji or a custom emoji id
