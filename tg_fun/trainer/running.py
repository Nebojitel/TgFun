import logging
from typing import Callable

from telethon import events, types

from tg_fun import stats
from tg_fun.plugins import manager
from tg_fun.settings import app_settings, game_bot_name
from tg_fun.telegram_client import client
from tg_fun.trainer import event_logging, loop
from tg_fun.trainer.handlers import common


async def main(execution_limit_minutes: int | None = None) -> None:
    """Running runner."""
    local_settings = {
        'execution_limit_minutes': execution_limit_minutes or 'infinite',
        'notifications_enabled': app_settings.notifications_enabled,
        'slow_mode': app_settings.slow_mode,
    }
    logging.info(f'start running ({local_settings})')

    logging.info('auth as %s', (await client.get_me()).username)

    game_user: types.InputPeerUser = await client.get_input_entity(game_bot_name)
    logging.info('game user is %s', game_user)

    await _setup_handlers(game_user_id=game_user.user_id)

    await loop.run_wait_loop(execution_limit_minutes)
    logging.info('end running')


async def _setup_handlers(game_user_id: int) -> None:
    if app_settings.self_manager_enabled:
        manager.setup(client)

    client.add_event_handler(
        callback=_message_handler,
        event=events.NewMessage(
            incoming=True,
            from_users=(game_user_id,),
        ),
    )
    client.add_event_handler(
        callback=_message_handler,
        event=events.MessageEdited(
            incoming=True,
            from_users=(game_user_id,),
        ),
    )


async def _message_handler(event: events.NewMessage.Event) -> None:
    await event_logging.log_event_information(event)
    stats.collector.inc_value('events')

    await event.message.mark_read()

    select_callback = _select_action_by_event(event)

    await select_callback(event)


def _select_action_by_event(event: events.NewMessage.Event) -> Callable:
    return common.skip_turn_handler
