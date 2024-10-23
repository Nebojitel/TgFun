import logging
from typing import Callable

from telethon import events, types
import asyncio

from tg_fun import stats, wait_utils
from tg_fun.game import action, parsers, state
from tg_fun.plugins import manager
from tg_fun.settings import app_settings, game_bot_name
from tg_fun.telegram_client import client
from tg_fun.trainer import event_logging, loop
from tg_fun.trainer.handlers import common
from tg_fun.game.buttons import TO_TOWN, TO_LOCATIONS, TO_FIGHT_ZONE, HEAL, ATTACK, FIND_MONSTER, get_buttons_flat


available_buttons = {
    'town_buttons': [],
    'chose_location_buttons': [],
    'fight_zone_buttons': [],
}

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
    mapping = [
        (state.common_states.is_locations, go_to_fight_zone),

        (state.common_states.is_monster_found, start_fighting),
        (state.common_states.is_win_state, search_next),

        (state.common_states.is_town, in_town),
        (state.common_states.is_alive, in_town),
        (state.common_states.is_hp_recovered, go_to_locations),

        # (state.common_states.is_energy_recovered, to_be_done),
        # (state.common_states.is_empty_energy, to_be_done),
    ]

    for check_function, callback_function in mapping:
        if check_function(event):
            logging.debug('is %s event', check_function.__name__)
            return callback_function
    return common.skip_turn_handler


async def update_available_buttons(event: events.NewMessage.Event, category: str) -> None:
    """Обновляем доступные кнопки по указанной категории."""
    global available_buttons
    buttons = get_buttons_flat(event)

    if buttons:
        if category == 'town_buttons':
            for btn in buttons:
                available_buttons['town_buttons'].append(btn.text)

        elif category == 'chose_location_buttons':
            for btn in buttons:
                available_buttons['chose_location_buttons'].append(btn.text)

        elif category == 'fight_zone_buttons':
            for btn in buttons:
                available_buttons['fight_zone_buttons'].append(btn.text)

        available_buttons = {key: list(set(val)) for key, val in available_buttons.items()}
    else:
        logging.warning(f'Кнопки для категории {category} не найдены. Обновление не выполнено.')


async def handle_button_event(button_symbol: str, category: str) -> bool:
    """Обрабатываем нажатие кнопки по символу из указанной категории."""
    global available_buttons
    buttons = available_buttons.get(category, [])
    button = next((btn for btn in buttons if button_symbol in btn), None)
    
    if button:
        await wait_utils.wait_for()
        await client.send_message(game_bot_name, button)
        return True
    logging.warning(f'Кнопка с символом "{button_symbol}" не найдена в категории {category}.')
    return False


async def go_to_fight_zone(event: events.NewMessage.Event) -> None:
    """Выбираем локацию для боя"""
    await update_available_buttons(event, 'chose_location_buttons')
    if any(TO_FIGHT_ZONE in btn for btn in available_buttons['chose_location_buttons']):
        logging.info('Идем в локацию.')
        await wait_utils.wait_for()
        button_to_press = next(btn for btn in available_buttons['chose_location_buttons'] if TO_FIGHT_ZONE in btn)
        await handle_button_event(button_to_press, 'chose_location_buttons')
    else:
        logging.warning('Не удалось найти кнопку для перехода в локацию.')


async def start_fighting(event: events.NewMessage.Event) -> None:
    """Начинаем бой."""
    await update_available_buttons(event, 'fight_zone_buttons')
    energy_level = parsers.get_energy_level(event.message.message)
    if (energy_level <= 0):
        logging.info('Мало энергии, ждем 1 час.')
        await asyncio.sleep(3600)

    if any(ATTACK in btn for btn in available_buttons['fight_zone_buttons']):
        logging.info('Начинаем бой.')
        await wait_utils.wait_for()
        button_to_press = next(btn for btn in available_buttons['fight_zone_buttons'] if ATTACK in btn)
        await handle_button_event(button_to_press, 'fight_zone_buttons')
    else:
        logging.warning('Не удалось найти кнопку начать бой.')


async def search_next(event: events.NewMessage.Event) -> None:
    """Начинаем поиск монстра или возвращаемся в город если нет энергии или мало хп."""
    energy_level = parsers.get_energy_level(event.message.message)
    hp_level = parsers.get_hp_level(event.message.message)

    if hp_level <= app_settings.minimum_hp_level_for_grinding:
        logging.info('Мало хп, возвращаемся.')
        await return_to_town()
    elif energy_level <= 0:
        logging.info('Мало энергии, ждем 1 час.')
        await asyncio.sleep(3600)
        await handle_button_event(FIND_MONSTER, 'fight_zone_buttons')
    else:
        await wait_utils.wait_for()
        await handle_button_event(FIND_MONSTER, 'fight_zone_buttons')


async def return_to_town() -> None:
    """Возвращаемся в город после завершения."""
    if any(TO_TOWN in btn for btn in available_buttons['fight_zone_buttons']):
        logging.info('Возвращаемся в город.')
        await wait_utils.wait_for()
        button_to_press = next(btn for btn in available_buttons['fight_zone_buttons'] if TO_TOWN in btn)
        await handle_button_event(button_to_press, 'fight_zone_buttons')
    else:
        logging.warning('Не удалось найти кнопку возвращения в город.')


async def in_town(event: events.NewMessage.Event) -> None:
    """Мы в городе. Лечимся и возвращаемся в локации"""
    await update_available_buttons(event, 'town_buttons')
    if any(HEAL in btn for btn in available_buttons['town_buttons']):
        logging.info('Лечимся.')
        await wait_utils.wait_for()
        button_to_press = next(btn for btn in available_buttons['town_buttons'] if HEAL in btn)
        await handle_button_event(button_to_press, 'town_buttons')
    else:
        logging.warning('Не удалось найти кнопку восстановления здоровья.')


async def go_to_locations(event: events.NewMessage.Event) -> None:
    """Возвращаемся в локации"""
    if any(TO_LOCATIONS in btn for btn in available_buttons['town_buttons']):
        logging.info('Возвращаемся в локации.')
        await wait_utils.wait_for()
        button_to_press = next(btn for btn in available_buttons['town_buttons'] if TO_LOCATIONS in btn)
        await handle_button_event(button_to_press, 'town_buttons')
    else:
        logging.warning('Не удалось найти кнопку для перехода в локации.')
