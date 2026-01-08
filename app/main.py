import asyncio

from telethon import TelegramClient, events

from app.CONFIG import CONTACTS_REFRESH_SECONDS, TG_API_HASH, TG_API_ID, TG_SESSION, log
from app.parse_selectors import (
    init_policies,
    load_contact_user_ids,
    selectors_need_contacts,
)
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


async def refresh_contact_user_ids_periodically(
    client: TelegramClient,
    contact_user_ids,
) -> None:
    "periodically refresh contact ids when contact selectors are in use"
    if not selectors_need_contacts():
        return
    if not CONTACTS_REFRESH_SECONDS or CONTACTS_REFRESH_SECONDS <= 0:
        return

    while True:
        await asyncio.sleep(CONTACTS_REFRESH_SECONDS)
        latest_ids = await load_contact_user_ids(client)
        contact_user_ids.clear()
        contact_user_ids.update(latest_ids)
        log.info("Refreshed contacts (count=%d)", len(contact_user_ids))


async def main() -> None:
    client = TelegramClient(TG_SESSION, TG_API_ID, TG_API_HASH)

    async with client:
        init_policies()
        validate_reaction_settings()

        contact_user_ids = await load_contact_user_ids(client)
        asyncio.create_task(
            refresh_contact_user_ids_periodically(client, contact_user_ids)
        )

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
