"""Game buttons and utils."""

import itertools

from telethon import events, types

TO_LOCATIONS = '☠'
HEAL = '💖'

TO_FIGHT_ZONE = '🐣'

TO_TOWN = '🏛'
ATTACK = '🔪'
FIND_MONSTER = '🐺'

def get_buttons_flat(event: events.NewMessage.Event) -> list[types.TypeKeyboardButton]:
    """Get all available buttons from event message."""
    if not event.message.buttons:
        return []
    return list(itertools.chain(*event.message.buttons))
