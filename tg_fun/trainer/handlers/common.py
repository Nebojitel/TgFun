"""Common handlers."""
import logging

from telethon import events

from tg_fun import notifications


async def skip_turn_handler(_: events.NewMessage.Event) -> None:
    """Just skip event."""
    logging.info('skip event')


async def resolve_capcha(_: events.NewMessage.Event) -> None:
    """Resolve capcha."""
    logging.info('Resolve capcha')
    await notifications.send_custom_channel_notify('capcha!')
