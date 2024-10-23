"""Check messages by patterns."""


from telethon import events

from tg_fun.game.buttons import get_buttons_flat
from tg_fun.game.parsers import strip_message


def is_win_state(event: events.NewMessage.Event) -> bool:
    """Is fight win state."""
    message = strip_message(event.message.message)
    return 'ты одержал победу' in message


def is_lose_state(event: events.NewMessage.Event) -> bool:
    """Is fight lose state."""
    message = strip_message(event.message.message)
    patterns = {
        'ты воскреснешь в',
        'к сожалению ты умер',
    }
    for pattern in patterns:
        if pattern in message:
            return True
    return False


def is_alive(event: events.NewMessage.Event) -> bool:
    """Is alive state."""
    message = strip_message(event.message.message)
    return 'ты снова жив' in message


def is_hp_recovered(event: events.NewMessage.Event) -> bool:
    """Is hp recovered state."""
    message = strip_message(event.message.message)
    return 'здоровье пополнено' in message


def is_empty_energy(event: events.NewMessage.Event) -> bool:
    """Is empty energy state."""
    message = strip_message(event.message.message)
    return 'недостаточно энергии' in message


def is_energy_recovered(event: events.NewMessage.Event) -> bool:
    """Is energy recovered state."""
    message = strip_message(event.message.message)
    return 'к энергии' in message


def is_locations(event: events.NewMessage.Event) -> bool:
    """Is location state."""
    message = strip_message(event.message.message)
    found_buttons = get_buttons_flat(event)
    if not found_buttons:
        return False
    return 'пора в бой' in message


def is_monster_found(event: events.NewMessage.Event) -> bool:
    """Is monster found state."""
    message = strip_message(event.message.message)

    patterns = {
        'на пути у вас встретился',
        'ты наткнулся на',
    }
    for pattern in patterns:
        if pattern in message:
            return True
    return False


def is_town(event: events.NewMessage.Event) -> bool:
    """Is town state."""
    message = strip_message(event.message.message)
    found_buttons = get_buttons_flat(event)
    if not found_buttons:
        return False
    return 'ты дошел до локации' in message

