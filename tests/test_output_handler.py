import traceback
from unittest.mock import patch, AsyncMock, MagicMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, Chat, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from application.config import GROUP_ID
from application.handlers.output_handler import Form
from application.handlers.output_handler import (confirm_delete_company, confirm_delete_product, delete_company,
                                                 delete_product, print_orders_info, print_profile_info, image_question,
                                                 choose_kitchen_category, choose_company_country,
                                                 add_item_with_dropbox_link, answer_message, ignore_message, send_alarm)


@pytest.mark.asyncio
@patch('application.database_owm.Consumer.get_by_telegram_id', new_callable=MagicMock)
@patch('application.handlers.output_handler.main_menu', new_callable=AsyncMock)
async def test_print_profile_info(mock_main_menu, mock_get_by_telegram_id):
    mock_user = MagicMock()
    mock_user.username = 'test_user'
    mock_user.email = 'testuser@example.com'
    mock_user.bonuses = 100

    mock_get_by_telegram_id.return_value = mock_user

    message = MagicMock(Message)
    message.answer = AsyncMock()

    telegram_id = 12345

    await print_profile_info(message, telegram_id)

    message.answer.assert_called_once_with(
        'Flavour Flow user information:'
        '\nUsername: test_user'
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


@pytest.mark.asyncio
async def test_confirm_delete_product():
    message = MagicMock(Message)
    message.delete = AsyncMock()
    message.answer = AsyncMock()

    product_id = 123

    await confirm_delete_product(message, product_id)

    message.delete.assert_called_once()

    expected_markup = InlineKeyboardBuilder().row(
        InlineKeyboardButton(text='✅', callback_data=f'{product_id}-conf-del-prod'),
        InlineKeyboardButton(text='❌', callback_data='deny-delete')
    ).as_markup()

    message.answer.assert_called_once_with(
        'Do you really want to delete this product?',
        reply_markup=expected_markup
    )


@pytest.mark.asyncio
async def test_confirm_delete_company():
    message = MagicMock(Message)
    message.delete = AsyncMock()
    message.answer = AsyncMock()

    company_id = 123

    await confirm_delete_company(message, company_id)

    message.delete.assert_called_once()

    expected_markup = InlineKeyboardBuilder().row(
        InlineKeyboardButton(text='✅', callback_data=f'{company_id}-conf-del-comp'),
        InlineKeyboardButton(text='❌', callback_data='deny-delete')
    ).as_markup()

    message.answer.assert_called_once_with(
        'Do you really want to delete this company? All products inside will be deleted too',
        reply_markup=expected_markup
    )


@pytest.mark.asyncio
@patch('application.database_owm.Product.delete', new_callable=AsyncMock)
async def test_delete_product(mock_delete_product):
    message = MagicMock(Message)
    message.delete = AsyncMock()

    state = MagicMock(FSMContext)

    product_id = 123

    await delete_product(message, state, product_id)

    message.delete.assert_called_once()
    mock_delete_product.assert_called_once()


@pytest.mark.asyncio
@patch('application.database_owm.Company.delete', new_callable=AsyncMock)
async def test_delete_product(mock_delete_company):
    message = MagicMock(Message)
    message.delete = AsyncMock()

    state = MagicMock(FSMContext)

    company_id = 123

    await delete_company(message, state, company_id)

    message.delete.assert_called_once()
    mock_delete_company.assert_called_once()


@pytest.mark.asyncio
async def test_image_question():
    message = MagicMock(Message)
    message.answer = AsyncMock()
    product_category = 'category_test'
    company_id = 123

    await image_question(message, product_category, company_id)

    builder = InlineKeyboardBuilder()
    builder.button(text='DROPBOX', callback_data=f'{product_category}-{company_id}-dropbox')
    builder.button(text='LINK', callback_data=f'{product_category}-{company_id}-link')
    expected_markup = builder.as_markup()

    message.answer.assert_called_once_with(
        'You will upload image from your PC or use link',
        reply_markup=expected_markup
    )


@pytest.mark.asyncio
@patch('application.database_owm.Kitchen.get_all', new_callable=MagicMock)
async def test_choose_kitchen_category(mock_kitchen_get_all):
    message = MagicMock(Message)
    message.answer = AsyncMock()
    message.delete = AsyncMock()
    image_way = 'LINK'

    mock_category1 = MagicMock()
    mock_category1.title = 'Category 1'
    mock_category1.id = 1

    mock_category2 = MagicMock()
    mock_category2.title = 'Category 2'
    mock_category2.id = 2

    mock_kitchen_get_all.return_value = [mock_category1, mock_category2]

    await choose_kitchen_category(message, image_way)

    message.delete.assert_called_once()

    expected_markup = InlineKeyboardBuilder()
    expected_markup.button(text=mock_category1.title, callback_data=f'{mock_category1.id}-{image_way}-category')
    expected_markup.button(text=mock_category2.title, callback_data=f'{mock_category2.id}-{image_way}-category')
    expected_markup = expected_markup.as_markup()

    message.answer.assert_called_once_with(
        'Choose company category:',
        reply_markup=expected_markup
    )


@pytest.mark.asyncio
@patch('application.database_owm.Country.get_all', new_callable=MagicMock)
async def test_choose_company_country(mock_country_get_all):
    message = MagicMock(Message)
    message.answer = AsyncMock()
    message.delete = AsyncMock()
    image_way = 'LINK'
    category_id = 1

    mock_country1 = MagicMock()
    mock_country1.title = 'Country 1'
    mock_country1.id = 1

    mock_country2 = MagicMock()
    mock_country2.title = 'Country 2'
    mock_country2.id = 2

    mock_country_get_all.return_value = [mock_country1, mock_country2]

    await choose_company_country(message, category_id, image_way)

    message.delete.assert_called_once()

    expected_markup = InlineKeyboardBuilder()
    expected_markup.button(text=mock_country1.title,
                           callback_data=f'{category_id}-{mock_country1.id}-{image_way}-country')
    expected_markup.button(text=mock_country2.title,
                           callback_data=f'{category_id}-{mock_country2.id}-{image_way}-country')
    expected_markup = expected_markup.as_markup()

    message.answer.assert_called_once_with(
        'Choose company country:',
        reply_markup=expected_markup
    )


@pytest.mark.asyncio
@patch('application.database_owm.Company.add_new', new_callable=MagicMock)
@patch('application.database_owm.Product.add_new', new_callable=MagicMock)
@patch('application.handlers.output_handler.main_menu', new_callable=AsyncMock)
async def test_add_item_with_dropbox_link(mock_main_menu, mock_add_product, mock_add_company):
    message = MagicMock(Message)
    message.answer = AsyncMock()

    message.from_user = MagicMock()
    message.from_user.id = 14562

    values_company = {
        'type': 'company',
        'name': 'Test Company',
        'description': 'A test company',
        'image_way': 'path/to/image'
    }

    await add_item_with_dropbox_link(message, values_company)

    mock_add_company.assert_called_once_with({
        'name': 'Test Company',
        'description': 'A test company'
    })

    message.answer.assert_called_once_with('Item added')
    mock_main_menu.assert_called_once_with(message, message.from_user.id)

    mock_add_company.reset_mock()
    message.answer.reset_mock()
    mock_main_menu.reset_mock()

    values_product = {
        'type': 'product',
        'name': 'Test Product',
        'price': 10.0,
        'description': 'A test product',
        'image_way': 'path/to/image'
    }

    await add_item_with_dropbox_link(message, values_product.copy())

    mock_add_product.assert_called_once_with({
        'name': 'Test Product',
        'price': 10.0,
        'description': 'A test product'
    })

    message.answer.assert_called_once_with('Item added')
    mock_main_menu.assert_called_once_with(message, message.from_user.id)


@pytest.mark.asyncio
@patch('application.handlers.output_handler.bot.send_message', new_callable=AsyncMock)
async def test_answer_message(mock_send_message):
    chat_id = 12345
    user_id = 67890
    question_message_id = 111213

    callback = MagicMock(CallbackQuery)
    callback.data = f"{chat_id}:{user_id}:{question_message_id}"
    callback.message = MagicMock(Message)
    callback.message.chat = MagicMock(Chat)
    callback.message.chat.id = 54321
    callback.message.message_id = 131415

    state = MagicMock(FSMContext)
    state.set_state = AsyncMock()
    state.update_data = AsyncMock()

    await answer_message(callback, state)

    mock_send_message.assert_called_once_with(callback.message.chat.id, "Enter your answer: ")

    state.set_state.assert_called_once_with(Form.answer)

    state.update_data.assert_called_once_with(
        chat_id=chat_id,
        user_id=user_id,
        question_message_id=question_message_id,
        message_id=callback.message.message_id
    )


@pytest.mark.asyncio
@patch('application.handlers.output_handler.bot.send_message', new_callable=AsyncMock)
@patch('application.handlers.output_handler.bot.delete_message', new_callable=AsyncMock)
@patch('application.database_owm.PendingUser.delete_pending', new_callable=MagicMock)
async def test_ignore_message(mock_delete_pending, mock_delete_message, mock_send_message):
    chat_id = 12345
    user_id = 67890
    question_message_id = 111213

    callback = MagicMock(CallbackQuery)
    callback.data = f"{chat_id}:{user_id}:{question_message_id}"
    callback.message = MagicMock(Message)
    callback.message.chat = MagicMock(Chat)
    callback.message.chat.id = 54321
    callback.message.message_id = 131415

    await ignore_message(callback)

    mock_send_message.assert_called_once_with(
        "12345", "Unfortunately, your question was denied", reply_to_message_id=question_message_id
    )

    mock_delete_message.assert_called_once_with(GROUP_ID, callback.message.message_id)

    mock_delete_pending.assert_called_once_with(user_id)


@pytest.mark.asyncio
@patch('application.handlers.output_handler.bot.send_message', new_callable=AsyncMock)
async def test_send_alarm(mock_send_message):
    admin_id = 12345
    try:
        raise ValueError("Test error")
    except ValueError as error:
        await send_alarm(admin_id, error)
        error_test = error

    traceback_str = ''.join(traceback.format_tb(error_test.__traceback__))
    alarm_message = (f"<b>ALARM!!! ALARM!!! THE PROBLEM DETECTED!!!:</b>\n"
                     f"{traceback_str}")

    mock_send_message.assert_called_once_with(admin_id, alarm_message, parse_mode='html')


@pytest.mark.asyncio
@patch('application.handlers.output_handler.bot.send_message', new_callable=AsyncMock)
async def test_send_alarm_exception(mock_send_message):
    admin_id = 12345
    error_message = "Test error"

    mock_send_message.side_effect = Exception("Failed to send message")

    try:
        raise ValueError(error_message)
    except ValueError as error:
        await send_alarm(admin_id, error)
        error_test = error

    traceback_str = ''.join(traceback.format_tb(error_test.__traceback__))
    alarm_message = (f"<b>ALARM!!! ALARM!!! THE PROBLEM DETECTED!!!:</b>\n"
                     f"{traceback_str}")

    mock_send_message.assert_called_once_with(admin_id, alarm_message, parse_mode='html')
