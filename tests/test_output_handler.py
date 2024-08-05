from unittest.mock import patch, AsyncMock, MagicMock

import pytest
from aiogram.types import Message

from application.handlers.output_handler import print_profile_info


@pytest.mark.asyncio
@patch('application.database_owm.Consumer.get_by_telegram_id', new_callable=MagicMock)
@patch('application.handlers.output_handler.main_menu', new_callable=AsyncMock)
async def test_print_profile_info(mock_main_menu, mock_get_by_telegram_id):
    mock_user = MagicMock()
    mock_user.username = 'testuser'
    mock_user.email = 'testuser@example.com'
    mock_user.bonuses = 100

    mock_get_by_telegram_id.return_value = mock_user

    message = MagicMock(Message)
    message.answer = AsyncMock()

    telegram_id = 12345

    await print_profile_info(message, telegram_id)

    message.answer.assert_called_once_with(
        'Flavour Flow user information:'
        '\nUsername: testuser'
        '\nEmail: testuser@example.com'
        '\nBonuses: 100'
    )

    mock_main_menu.assert_called_once_with(message, telegram_id)
