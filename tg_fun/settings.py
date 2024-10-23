"""Application settings."""
import os
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings

APP_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        '..',
    ),
)


class AppSettings(BaseSettings):
    """Application settings class."""

    # required customer settings
    telegram_api_id: int = 123456
    telegram_api_hash: str = 'u_api_hash'

    # optional customer settings
    minimum_hp_level_for_grinding: int = Field(default=60, ge=1, le=100)
    notifications_enabled: bool = False
    custom_tg_channel: str = ''
    self_manager_enabled: bool = False
    farm_dangeons: bool = Field(default=False)

    # developer section
    fast_mode: bool = Field(default=False)
    slow_mode: bool = Field(default=False, description='Used for fresh telegram accounts.')
    ping_commands: str = ',.-+=/0'
    game_username: str = 'rf_telegram_bot'
    tlg_client_retries: int = 30
    tlg_client_retry_delay: int = 15
    debug: bool = Field(default=False)
    message_log_limit: int = 1000
    wait_loop_iteration_seconds: int = 3
    show_stats_every_seconds: int = 30 * 60

app_settings = AppSettings(
    _env_file=os.path.join(APP_PATH, '.env'),  # type: ignore
)

game_bot_name = app_settings.game_username
