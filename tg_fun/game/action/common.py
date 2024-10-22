"""Common game actions."""
import logging
import random

from telethon import events

from tg_fun.settings import app_settings
from tg_fun.telegram_client import client
from tg_fun.wait_utils import wait_for


async def ping(entity: int | events.NewMessage.Event) -> None:
    """Random short message for update current location state."""
    logging.info('call ping command')

    if isinstance(entity, events.NewMessage.Event):
        game_bot_id = entity.chat_id
    else:
        game_bot_id = entity

    message = random.choice(
        seq=app_settings.ping_commands,
    )
    logging.info(f'call ping command debug {game_bot_id} {message}')
    await wait_for()
    await client.send_message(
        entity=game_bot_id,
        message=message,
    )

async def execute_command(entity: int, command: str) -> None:
    """Execute custom command."""
    logging.info('call command execution {0}'.format(command))
    await wait_for()
    await client.send_message(
        entity=entity,
        message=command,
    )