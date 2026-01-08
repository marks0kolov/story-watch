from typing import Iterable, Set

from telethon import TelegramClient, functions, types as ttypes

from app.CONFIG import (
    REACT_STORIES_ENABLED,
    READ_STORIES_ENABLED,
    REACTION_EMOJI,
    WATCH_STORIES_ENABLED,
    log,
)
from app.parse_selectors import should_react_peer, should_watch_peer


def extract_story_ids(peer_stories: ttypes.stories.PeerStories) -> Iterable[int]:
    "extract story ids from PeerStories object"
    items = getattr(peer_stories, "stories", None) or []
    for it in items:
        story_id = getattr(it, "id", None)
        if isinstance(story_id, int):
            yield story_id


def validate_reaction_settings() -> None:
    "validate reaction settings against config"
    if not REACT_STORIES_ENABLED:
        return

    value = (REACTION_EMOJI or "").strip()
    if not value or value == "0":
        raise ValueError(
            "REACTION_EMOJI must be set to a custom emoji id or a normal emoji when REACT_STORIES_ENABLED=True"
        )

    if value.isdigit() and int(value) <= 0:
        raise ValueError(
            "REACTION_EMOJI must be a positive custom emoji id when set to a number"
        )


def _build_reaction(reaction_value: str) -> ttypes.TypeReaction:
    "build a reaction object from a numeric id or emoji string"
    value = (reaction_value or "").strip()
    if value.isdigit():
        return ttypes.ReactionCustomEmoji(document_id=int(value))
    return ttypes.ReactionEmoji(emoticon=value)


async def watch_story_ids_for_peer(
    client: TelegramClient,
    input_peer: ttypes.TypeInputPeer,
    story_ids: Iterable[int],
) -> None:
    "watch all stories in `story_ids` and read them if needed"
    ids = sorted({int(x) for x in story_ids if isinstance(x, int)})
    if not ids:
        return

    # increment view counters
    await client(functions.stories.IncrementStoryViewsRequest(
        peer=input_peer,
        id=ids,
    ))

    # mark read up to max_id if needed
    if READ_STORIES_ENABLED:
        await client(functions.stories.ReadStoriesRequest(
            peer=input_peer,
            max_id=ids[-1],
        ))

    log.info(
        "Watched %d stories for peer_id=%s (read=%s)",
        len(ids),
        getattr(input_peer, 'user_id', getattr(input_peer, 'channel_id', getattr(input_peer, 'chat_id', 'unknown'))),
        bool(READ_STORIES_ENABLED),
    )


async def react_to_story_ids_for_peer(
    client: TelegramClient,
    input_peer: ttypes.TypeInputPeer,
    story_ids: Iterable[int],
    reaction_value: str,
) -> None:
    "react to each story with an emoji"
    ids = sorted({int(x) for x in story_ids if isinstance(x, int)})
    if not ids:
        return

    reaction = _build_reaction(reaction_value)

    for sid in ids:
        await client(functions.stories.SendReactionRequest(
            peer=input_peer,
            story_id=int(sid),
            reaction=reaction,
            add_to_recent=None,
        ))

    log.info(
        "Reacted to %d stories for peer_id=%s",
        len(ids),
        getattr(input_peer, 'user_id', getattr(input_peer, 'channel_id', getattr(input_peer, 'chat_id', 'unknown'))),
    )


async def handle_story_update(
    client: TelegramClient,
    update: ttypes.TypeUpdate,
    contact_user_ids: Set[int],
) -> None:
    "handle story updates and watch/react if eligible"
    # ignore if it's not a story update, story watching is disabled or peer isn't selected
    if not isinstance(update, ttypes.UpdateStory):
        return

    if not WATCH_STORIES_ENABLED:
        return

    peer = getattr(update, "peer", None)
    story = getattr(update, "story", None)
    if peer is None or story is None:
        return

    if not isinstance(peer, (ttypes.PeerUser, ttypes.PeerChannel, ttypes.PeerChat)):
        return

    if not should_watch_peer(peer, contact_user_ids):
        return

    story_id = getattr(story, "id", None)
    if not isinstance(story_id, int):
        return

    input_peer = await client.get_input_entity(peer)
    await watch_story_ids_for_peer(client, input_peer, [story_id]) # watch/read story
    if REACT_STORIES_ENABLED and should_react_peer(peer, contact_user_ids):
        await react_to_story_ids_for_peer(client, input_peer, [story_id], REACTION_EMOJI) # react to story


async def watch_all_active_stories(
    client: TelegramClient,
    contact_user_ids: Set[int],
) -> None:
    "fetch active stories feed, apply included/excluded policy, and watch/react to them"

    if not WATCH_STORIES_ENABLED:
        log.info("Story watching disabled (WATCH_STORIES_ENABLED=False); skipping initial sweep.")
        return

    all_stories = await client(functions.stories.GetAllStoriesRequest(
        next=False,
        hidden=False,
        state=None,
    ))

    peer_stories_list = getattr(all_stories, "peer_stories", None) or []
    if not peer_stories_list:
        log.info("No active stories in feed.")
        return

    watched_peers = 0
    watched_total = 0

    for ps in peer_stories_list:
        # ps is stories.PeerStories: it has .peer (Peer*) and .stories (StoryItem[])
        peer = getattr(ps, "peer", None)
        if not isinstance(peer, (ttypes.PeerUser, ttypes.PeerChannel, ttypes.PeerChat)):
            continue

        if not should_watch_peer(peer, contact_user_ids):
            continue

        # resolve to InputPeer to call stories.* methods
        input_peer = await client.get_input_entity(peer)

        story_ids = list(extract_story_ids(ps))
        if not story_ids:
            continue

        await watch_story_ids_for_peer(client, input_peer, story_ids)
        if REACT_STORIES_ENABLED and should_react_peer(peer, contact_user_ids):
            await react_to_story_ids_for_peer(client, input_peer, story_ids, REACTION_EMOJI)
        watched_peers += 1
        watched_total += len(set(story_ids))

    log.info("Initial sweep watched %d stories across %d peers", watched_total, watched_peers)
