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

# ==================================== TELEGRAM API ====================================
TG_API_ID = int(os.getenv("TG_API_ID"))
TG_API_HASH = os.getenv("TG_API_HASH")
TG_SESSION = os.getenv("TG_SESSION")

# ==================================== BEHAVIOUR FLAGS ====================================
WATCH_STORIES_ENABLED = True # master switch

READ_STORIES_ENABLED = False # if True, stories are marked as read

REACT_STORIES_ENABLED = False # if True, reacts to stories that were watched

REACTION_EMOJI = os.getenv("REACTION_EMOJI", os.getenv("REACTION_EMOJI_ID", "❤️")) # use a numeric id for custom emoji or a normal emoji character

INCLUDED_USERS = [ # selectors: ints are peer ids and strings are entire groups of peers: can be either "user", "contact", "channel", "chat"
    "contacts"
]

EXCLUDED_USERS = [ # selectors: ints are peer ids and strings are entire groups of peers: can be either "user", "contact", "channel", "chat". excluded overrides included
]

REACTIONS_EXCLUDED = [ # exclusions for reactions only, same logic as EXCLUDED USERS
]
