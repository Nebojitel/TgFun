"""Custom logging functions."""
import logging

from telethon import events

from tg_fun.game import parsers
from tg_fun.game.buttons import get_buttons_flat
from tg_fun.settings import app_settings


async def log_event_information(event: events.NewMessage.Event) -> None:
    """Log event."""
    message_content = parsers.strip_message(event.message.message)
    media = event.message.media
    logging.info(
        'handle event message="%s"; buttons="%s"; photos="%s"',
        message_content[:app_settings.message_log_limit],
        [button.text for button in get_buttons_flat(event)],
        media,
    )
