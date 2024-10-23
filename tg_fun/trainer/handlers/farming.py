"""Farming handlers."""
import logging
from typing import Dict, List

from telethon import events
import asyncio

from tg_fun import wait_utils
from tg_fun.game import parsers
from tg_fun.settings import app_settings, game_bot_name
from tg_fun.telegram_client import client
from tg_fun.game.buttons import TO_TOWN, TO_LOCATIONS, TO_DANGEONS, TO_FIGHT_ZONE, HEAL, ATTACK, FIND_MONSTER, YES, get_buttons_flat

available_buttons: Dict[str, List[str]] = {
    'town_buttons': [],
    'chose_location_buttons': [],
    'fight_zone_buttons': [],
    'dangeon_buttons': [],
}


async def init(event: events.NewMessage.Event) -> None:
    """Делаем переход инициализацию."""
    buttons = get_buttons_flat(event)

    if buttons:
        if any(HEAL in btn.text for btn in buttons):
            await in_town(event)
        elif any(TO_FIGHT_ZONE in btn.text for btn in buttons):
            await go_to_fight_zone(event)
        elif any(ATTACK in btn.text for btn in buttons):
            await start_fighting(event)
        elif any(TO_DANGEONS in btn.text for btn in buttons):
            await go_to_dangeon(event)
    else:
        logging.warning(f'Кнопки для категории не найдены. Инициализация не выполнена.')


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

        elif category == 'dangeon_buttons':
            for btn in buttons:
                available_buttons['dangeon_buttons'].append(btn.text)

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

    try:
        energy_level = parsers.get_energy_level(event.message.message)
    except Exception as e:
        logging.warning(f'Не удалось получить уровень энергии: {e}')
        energy_level = None 

    if energy_level is not None and energy_level <= 0:
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
    try:
        energy_level = parsers.get_energy_level(event.message.message)
        hp_level = parsers.get_hp_level(event.message.message)
    except Exception as e:
        logging.warning(f'Не удалось получить уровень энергии или здоровья: {e}')
        energy_level = None 
        hp_level = None 

    if hp_level is not None and hp_level <= app_settings.minimum_hp_level_for_grinding:
        logging.info('Мало хп, возвращаемся.')
        await return_to_town()
    elif energy_level is not None and energy_level <= 0:
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


async def go_to_locations(_: events.NewMessage.Event) -> None:
    """Возвращаемся в локации"""
    if any(TO_LOCATIONS in btn for btn in available_buttons['town_buttons']):
        logging.info('Возвращаемся в локации.')
        await wait_utils.wait_for()
        button_to_press = next(btn for btn in available_buttons['town_buttons'] if TO_LOCATIONS in btn)
        await handle_button_event(button_to_press, 'town_buttons')
    else:
        logging.warning('Не удалось найти кнопку для перехода в локации.')


async def pick_dangeon(_: events.NewMessage.Event) -> None:
    """Возвращаемся в данж"""
    if any(TO_DANGEONS in btn for btn in available_buttons['town_buttons']):
        logging.info('Возвращаемся в данж.')
        await wait_utils.wait_for()
        button_to_press = next(btn for btn in available_buttons['town_buttons'] if TO_DANGEONS in btn)
        await handle_button_event(button_to_press, 'town_buttons')
    else:
        logging.warning('Не удалось найти кнопку для перехода в данж.')


async def go_to_dangeon(event: events.NewMessage.Event) -> None:
    """Возвращаемся в данж"""
    await update_available_buttons(event, 'dangeon_buttons')
    if any(TO_DANGEONS in btn for btn in available_buttons['dangeon_buttons']):
        logging.info('Возвращаемся в данж.')
        await wait_utils.wait_for()
        button_to_press = next(btn for btn in available_buttons['dangeon_buttons'] if TO_DANGEONS in btn)
        await handle_button_event(button_to_press, 'dangeon_buttons')
    else:
        logging.warning('Не удалось найти кнопку отправиться в данж.')


async def choose_dangeon(_: events.NewMessage.Event) -> None:
    """Выбираем данж"""
    await wait_utils.wait_for()
    await client.send_message(game_bot_name, '/go_dange_10000')


async def start_dangeon(event: events.NewMessage.Event) -> None:
    """Подтвердить запуск данжа."""
    message = event.message
    if message.buttons:
        for row in message.buttons:
            for button in row:
                if button.text == '✅Да':
                    logging.info('Нажимаем inline-кнопку "✅Да".')
                    await button.click()
                    return
    
    logging.warning('Кнопка "✅Да" не найдена или она не является inline-кнопкой.')


async def relaxing(_: events.NewMessage.Event) -> None:
    """Отдыхаем."""
    logging.info('Отдыхаем час.')
    await asyncio.sleep(3600)
    await client.send_message(game_bot_name, '/buttons')

