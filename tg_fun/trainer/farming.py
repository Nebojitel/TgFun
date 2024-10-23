import logging
from typing import Callable

from telethon import events, types

from tg_fun import stats
from tg_fun.game import state
from tg_fun.plugins import manager
from tg_fun.settings import app_settings, game_bot_name
from tg_fun.telegram_client import client
from tg_fun.trainer import event_logging, loop
from tg_fun.trainer.handlers import common, farming


async def main(execution_limit_minutes: int | None = None) -> None:
    """Farming runner."""
    local_settings = {
        'execution_limit_minutes': execution_limit_minutes or 'infinite',
        'notifications_enabled': app_settings.notifications_enabled,
        'slow_mode': app_settings.slow_mode,
    }
    logging.info(f'start farming ({local_settings})')

    logging.info('auth as %s', (await client.get_me()).username)

    game_user: types.InputPeerUser = await client.get_input_entity(game_bot_name)
    logging.info('game user is %s', game_user)

    await client.send_message(game_bot_name, '/buttons')

    await _setup_handlers(game_user_id=game_user.user_id)

    await loop.run_wait_loop(execution_limit_minutes)
    logging.info('end farming')


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
    mapping = [
        (state.common_states.init, farming.init),

        (state.common_states.is_locations, farming.go_to_fight_zone),

        (state.common_states.is_monster_found, farming.start_fighting),
        (state.common_states.is_monster_not_found, farming.search_next),
        (state.common_states.is_win_state, farming.search_next),

        (state.common_states.is_town, farming.in_town),
        (state.common_states.is_alive, farming.in_town),
        (state.common_states.is_hp_recovered, lambda e: farming.go_to_locations(e) if not app_settings.farm_dangeons else farming.pick_dangeon(e)),
        (state.common_states.is_dangeon, farming.go_to_dangeon),
        (state.common_states.is_choose_dangeon, farming.choose_dangeon),
        (state.common_states.is_approve_dangeon, farming.start_dangeon),
        (state.common_states.is_dangeon_finished, farming.relaxing),

        (state.common_states.is_capcha_found, common.resolve_capcha),

        # (state.common_states.is_energy_recovered, to_be_done),
        (state.common_states.is_empty_energy, farming.relaxing),
    ]

    for check_function, callback_function in mapping:
        if check_function(event):
            logging.debug('is %s event', check_function.__name__)
            return callback_function
    return common.skip_turn_handler
