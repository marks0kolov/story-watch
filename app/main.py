import asyncio

from telethon import TelegramClient, events

from app.CONFIG import TG_API_HASH, TG_API_ID, TG_SESSION, log
from app.parse_selectors import init_policies, load_contact_user_ids
from app.story_intercations import (
    watch_all_active_stories,
    handle_story_update,
    validate_reaction_settings,
)


def create_update_handler(
    client: TelegramClient,
    contact_user_ids,
):
    "create a handler that listens for story updates and watches/reacts to them"
    async def _handler(update):
        await handle_story_update(client, update, contact_user_ids)

    return _handler


async def main() -> None:
    client = TelegramClient(TG_SESSION, TG_API_ID, TG_API_HASH)

    async with client:
        init_policies()
        validate_reaction_settings()

        contact_user_ids = await load_contact_user_ids(client)

        # initial sweep
        await watch_all_active_stories(client, contact_user_ids)

        # realtime updates
        handler = create_update_handler(client, contact_user_ids)
        client.add_event_handler(handler, events.Raw)

        log.info("Listening for new story updates...")
        await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
