"""Event message parsers."""
import base64
import re
from io import BytesIO
from math import ceil

from telethon import events, types

from tg_fun.exceptions import InvalidMessageError
from tg_fun.telegram_client import client

_hp_level_pattern = re.compile(r'❤(\d+)/(\d+)')
_energy_level_pattern = re.compile(r'🔋(\d+)/(\d+)')

def strip_message(original_message: str) -> str:
    """Return message content without EOL symbols."""
    return original_message.replace('\n', ' ').strip().lower()


async def get_photo_base64(event: events.NewMessage.Event) -> str | None:
    """Return message photo as base64 decoded string."""
    image_bytes = BytesIO()
    await client.download_media(
        message=event.message,
        file=image_bytes,
        thumb=-1,
    )
    image_str_base64 = base64.b64encode(image_bytes.getvalue()).decode('utf-8')
    return image_str_base64.replace('data:image/png;', '').replace('base64,', '')


def get_hp_level(message_content: str) -> int:
    """Get current HP in percent."""
    current_level, max_level = get_character_hp(message_content)
    return ceil(int(current_level) / int(max_level) * 100)


def get_character_hp(message_content: str) -> tuple[int, int]:
    """Get character HP level."""
    found = _hp_level_pattern.search(strip_message(message_content), re.MULTILINE)
    if not found:
        raise InvalidMessageError('HP not found')

    current_level, max_level = found.group(1, 2)
    return int(current_level), int(max_level)


def get_energy_level(message_content: str) -> int:
    """Get current energy level."""
    current_level, _ = get_character_energy(message_content)
    return int(current_level)


def get_character_energy(message_content: str) -> tuple[int, int]:
    """Get character energy level."""
    found = _energy_level_pattern.search(strip_message(message_content), re.MULTILINE)
    if not found:
        raise InvalidMessageError('Energy not found')

    current_level, max_level = found.group(1, 2)
    return int(current_level), int(max_level)
