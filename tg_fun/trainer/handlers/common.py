"""Common handlers."""
import logging

from telethon import events

async def skip_turn_handler(_: events.NewMessage.Event) -> None:
    """Just skip event."""
    logging.info('skip event')
