from typing import Iterable, Set

from telethon import TelegramClient, functions, types as ttypes

from app.CONFIG import EXCLUDED_USERS, INCLUDED_USERS, REACTIONS_EXCLUDED, log


# parsed, normalized policy sets (populated by init_policies())
_INCLUDED_PEER_IDS: Set[int] = set()
_INCLUDED_GROUPS: Set[str] = set()
_EXCLUDED_PEER_IDS: Set[int] = set()
_EXCLUDED_GROUPS: Set[str] = set()
_REACT_EXCLUDED_PEER_IDS: Set[int] = set()
_REACT_EXCLUDED_GROUPS: Set[str] = set()
_SUPPORTED_GROUPS: Set[str] = {"contact", "channel", "chat", "user"}




def _parse_selector_list(values: Iterable[object] = []) -> tuple[Set[int], Set[str]]:
    "filter out all unsupported values and return 2 separate lists of selectors: peer ids and groups"
    ids: Set[int] = set()
    groups: Set[str] = set()

    for x in values:
        if isinstance(x, int):
            ids.add(int(x))
            continue

        if isinstance(x, str):
            s = x.strip().lower()
            if not s:
                continue

            # accept plural forms; normalize to singular
            if s.endswith("s"):
                s = s[:-1]

            if s not in _SUPPORTED_GROUPS:
                log.warning("Ignoring unknown group selector: %r", x)
                continue

            groups.add(s)
            continue

        log.warning("Ignoring unsupported selector value (type=%s): %r", type(x).__name__, x)

    return ids, groups


def init_policies() -> None:
    "initialize separate lists for peer ids and groups for all selectors"
    global _INCLUDED_PEER_IDS, _INCLUDED_GROUPS
    global _EXCLUDED_PEER_IDS, _EXCLUDED_GROUPS
    global _REACT_EXCLUDED_PEER_IDS, _REACT_EXCLUDED_GROUPS

    _INCLUDED_PEER_IDS, _INCLUDED_GROUPS = _parse_selector_list(INCLUDED_USERS)
    _EXCLUDED_PEER_IDS, _EXCLUDED_GROUPS = _parse_selector_list(EXCLUDED_USERS)
    _REACT_EXCLUDED_PEER_IDS, _REACT_EXCLUDED_GROUPS = _parse_selector_list(REACTIONS_EXCLUDED)

    log.info(
        "Policy loaded | included_ids=%d included_groups=%s | excluded_ids=%d excluded_groups=%s | react_excluded_ids=%d react_excluded_groups=%s",
        len(_INCLUDED_PEER_IDS),
        sorted(_INCLUDED_GROUPS),
        len(_EXCLUDED_PEER_IDS),
        sorted(_EXCLUDED_GROUPS),
        len(_REACT_EXCLUDED_PEER_IDS),
        sorted(_REACT_EXCLUDED_GROUPS),
    )


def selectors_need_contacts() -> bool:
    "check whether or not should the code retrieve the contacts user id list"
    return (
        "contact" in _INCLUDED_GROUPS
        or "contact" in _EXCLUDED_GROUPS
        or "contact" in _REACT_EXCLUDED_GROUPS
    )


async def load_contact_user_ids(client: TelegramClient) -> Set[int | None]:
    "return contact user ids only when selectors require them"
    if selectors_need_contacts():
        contact_ids: Set[int] = set()

        result = await client(functions.contacts.GetContactsRequest(hash=0))

        contacts = getattr(result, "contacts", None)
        if contacts:
            for c in contacts:
                uid = getattr(c, "user_id", None)
                if uid is not None:
                    contact_ids.add(int(uid))
        else:
            users = getattr(result, "users", None) or []
            for u in users:
                uid = getattr(u, "id", None)
                if uid is not None:
                    contact_ids.add(int(uid))

        log.info("Loaded %d contacts", len(contact_ids))
        return contact_ids
    return set()


def _is_excluded_for_watch(peer: ttypes.TypePeer, contact_user_ids: Set[int]) -> bool:
    "check if a peer's story is excluded from watching"
    if isinstance(peer, ttypes.PeerUser):
        pid = int(peer.user_id)
        if pid in _EXCLUDED_PEER_IDS:
            return True
        if "user" in _EXCLUDED_GROUPS:
            return True
        if "contact" in _EXCLUDED_GROUPS and pid in contact_user_ids:
            return True
        return False

    if isinstance(peer, ttypes.PeerChannel):
        pid = int(peer.channel_id)
        if pid in _EXCLUDED_PEER_IDS:
            return True
        return "channel" in _EXCLUDED_GROUPS

    if isinstance(peer, ttypes.PeerChat):
        pid = int(peer.chat_id)
        if pid in _EXCLUDED_PEER_IDS:
            return True
        return "chat" in _EXCLUDED_GROUPS

    return True


def _is_included_for_watch(peer: ttypes.TypePeer, contact_user_ids: Set[int]) -> bool:
    "check if a peer's story is included for watching"
    if isinstance(peer, ttypes.PeerUser):
        pid = int(peer.user_id)
        if pid in _INCLUDED_PEER_IDS:
            return True
        if "user" in _INCLUDED_GROUPS:
            return True
        if "contact" in _INCLUDED_GROUPS and pid in contact_user_ids:
            return True
        return False

    if isinstance(peer, ttypes.PeerChannel):
        pid = int(peer.channel_id)
        if pid in _INCLUDED_PEER_IDS:
            return True
        return "channel" in _INCLUDED_GROUPS

    if isinstance(peer, ttypes.PeerChat):
        pid = int(peer.chat_id)
        if pid in _INCLUDED_PEER_IDS:
            return True
        return "chat" in _INCLUDED_GROUPS

    return False


def should_watch_peer(peer: ttypes.TypePeer, contact_user_ids: Set[int]) -> bool:
    "check if a peer's story should be watched"
    if _is_excluded_for_watch(peer, contact_user_ids):
        return False
    return _is_included_for_watch(peer, contact_user_ids)


def _is_excluded_for_react(peer: ttypes.TypePeer, contact_user_ids: Set[int]) -> bool:
    "check if a peer's story is excluded from reacting to"
    if isinstance(peer, ttypes.PeerUser):
        pid = int(peer.user_id)
        if pid in _REACT_EXCLUDED_PEER_IDS:
            return True
        if "user" in _REACT_EXCLUDED_GROUPS:
            return True
        if "contact" in _REACT_EXCLUDED_GROUPS and pid in contact_user_ids:
            return True
        return False

    if isinstance(peer, ttypes.PeerChannel):
        pid = int(peer.channel_id)
        if pid in _REACT_EXCLUDED_PEER_IDS:
            return True
        return "channel" in _REACT_EXCLUDED_GROUPS

    if isinstance(peer, ttypes.PeerChat):
        pid = int(peer.chat_id)
        if pid in _REACT_EXCLUDED_PEER_IDS:
            return True
        return "chat" in _REACT_EXCLUDED_GROUPS

    return True


def should_react_peer(peer: ttypes.TypePeer, contact_user_ids: Set[int]) -> bool:
    "check if a peer's story should be reacted to"
    return not _is_excluded_for_react(peer, contact_user_ids)
