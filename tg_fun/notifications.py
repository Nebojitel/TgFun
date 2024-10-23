"""Notifications."""

from tg_fun.settings import app_settings
from tg_fun.telegram_client import client

async def send_custom_channel_notify(message: str) -> None:
    """Send message to favorites chat in telegram."""
    if app_settings.custom_tg_channel:
        destination = await client.get_entity(app_settings.custom_tg_channel)
        if not destination:
            raise RuntimeError('Custom notify dialog "{0}" not found'.format(
                app_settings.custom_tg_channel,
            ))
        await client.send_message(
            destination,
            message=message,
            parse_mode='markdown',
        )
