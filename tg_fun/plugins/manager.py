"""Managers commands plugin."""
import logging

from telethon import TelegramClient, events, types

from tg_fun import shared_state, telegram_client
from tg_fun.game import action
from tg_fun.game.parsers import strip_message
from tg_fun.settings import app_settings
from tg_fun.trainer import loop

logger = logging.getLogger(__file__)


def setup(tg_client: TelegramClient) -> None:
    """Set up telegram handlers."""
    tg_client.add_event_handler(
        callback=_handler,
        event=events.NewMessage(
            chats=['me'],
            pattern='!(stop|start|exit|help)',
            func=lambda event: event.is_private,
        ),
    )


async def _handler(event: events.NewMessage.Event) -> None:  # noqa: WPS110
    """Got possible self-management commands."""
    logger.info('got self-management command "{0}"'.format(
        strip_message(event.message.message),
    ))

    command = strip_message(event.message.message).lower().strip()
    response_message = 'unknown command!'
    match command:
        case '!help':
            response_message = '\n'.join([
                '!exit - force exit',
                '!stop - pause farming',
                '!start - resume farming',
            ])

        case '!exit':
            loop.exit_request(message='Force exit')
            response_message = 'exit request sent'

        case '!stop':
            response_message = 'farming was paused'
            shared_state.PAUSED = True

        case '!start':
            response_message = 'farming was resume'
            shared_state.PAUSED = False
            game_user: types.InputPeerUser = await telegram_client.client.get_input_entity(app_settings.game_username)
            await action.common_actions.ping(game_user.user_id)

    await event.message.mark_read()
    await event.client.send_message('me', message=response_message)
