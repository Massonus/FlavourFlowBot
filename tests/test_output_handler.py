from unittest.mock import patch, AsyncMock, MagicMock

import pytest
from aiogram.types import Message

from application.handlers.output_handler import print_orders_info
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


@pytest.mark.asyncio
@patch('application.database_owm.Consumer.get_by_telegram_id', new_callable=MagicMock)
@patch('application.database_owm.Order.get_all_by_user_id', new_callable=MagicMock)
@patch('application.database_owm.Company.get_company_by_id', new_callable=MagicMock)
@patch('application.handlers.output_handler.main_menu', new_callable=AsyncMock)
async def test_print_orders_info(mock_main_menu, mock_get_company_by_id, mock_get_all_by_user_id,
                                 mock_get_by_telegram_id):
    mock_user = MagicMock()
    mock_user.id = 1
    mock_get_by_telegram_id.return_value = mock_user

    mock_order = MagicMock()
    mock_order.company_id = 2
    mock_order.earned_bonuses = 50
    mock_order.date = '2024-08-05'
    mock_order.time = MagicMock()
    mock_order.time.isoformat.return_value = '12:34'
    mock_order.address = '123 Example St'

    mock_get_all_by_user_id.return_value = [mock_order]

    mock_company = MagicMock()
    mock_company.title = 'Example Company'
    mock_get_company_by_id.return_value = mock_company

    message = MagicMock(Message)
    message.answer = AsyncMock()

    telegram_id = 12345

    await print_orders_info(message, telegram_id)

    message.answer.assert_any_call('Your orders:')
    message.answer.assert_any_call(
        'Company: Example Company\n'
        'Earned bonuses: 50\n'
        'Date and time: 2024-08-05, 12:34\n'
        'Address: 123 Example St'
    )

    mock_main_menu.assert_called_once_with(message, telegram_id)

    mock_get_by_telegram_id.assert_called_once_with(telegram_id)
    mock_get_all_by_user_id.assert_called_once_with(mock_user.id)
    mock_get_company_by_id.assert_called_once_with(mock_order.company_id)
