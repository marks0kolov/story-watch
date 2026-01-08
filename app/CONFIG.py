import os
import logging

from dotenv import load_dotenv

load_dotenv()

# =================================== LOGGING ====================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("story_watcher")
logging.getLogger("telethon").setLevel(logging.WARNING)

# ==================================== TELEGRAM API ====================================
TG_API_ID = int(os.getenv("TG_API_ID"))
TG_API_HASH = os.getenv("TG_API_HASH")
TG_SESSION = os.getenv("TG_SESSION")

# ==================================== BEHAVIOUR FLAGS ====================================
WATCH_STORIES_ENABLED = True # master switch

READ_STORIES_ENABLED = False # if True, stories are marked as read

REACT_STORIES_ENABLED = False # if True, reacts to stories that were watched

REACTION_EMOJI = os.getenv("REACTION_EMOJI", os.getenv("REACTION_EMOJI_ID", "❤️")) # use a numeric id for custom emoji or a normal emoji character

CONTACTS_REFRESH_SECONDS = 86_400 # how often to refresh contacts when using the "contact" selector; set to 0 to disable

INCLUDED_USERS = [ # selectors: ints are peer ids and strings are entire groups of peers: can be either "user", "contact", "channel", "chat", "all"
    "all"
]

EXCLUDED_USERS = [ # selectors: ints are peer ids and strings are entire groups of peers: can be either "user", "contact", "channel", "chat", "all". excluded overrides included
]

REACTIONS_EXCLUDED = [ # exclusions for reactions only, same logic as EXCLUDED USERS
]
