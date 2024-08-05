import html
import traceback

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import (InlineKeyboardButton,
                           Message, CallbackQuery)
from aiogram.utils.keyboard import InlineKeyboardBuilder

import application.database_owm as database
from application.config import TG_TOKEN, GROUP_ID
from application.handlers.display_handler import main_menu
from application.handlers.input_handler import Form

bot = Bot(token=TG_TOKEN)


async def print_profile_info(message: Message, telegram_id: int):
    user_profile = database.Consumer.get_by_telegram_id(telegram_id)
    await message.answer(f'Flavour Flow user information:'
                         f'\nUsername: {user_profile.username}'
                         f'\nEmail: {user_profile.email}'
                         f'\nBonuses: {user_profile.bonuses}')
    await main_menu(message, telegram_id)


async def print_orders_info(message: Message, telegram_id: int):
    user_id = database.Consumer.get_by_telegram_id(telegram_id).id
    orders = database.Order.get_all_by_user_id(user_id)
    await message.answer('Your orders:')
    for order in orders:
        company = database.Company.get_company_by_id(order.company_id).title
        earned_bonuses = order.earned_bonuses
        date = order.date
        time = order.time.isoformat(timespec="minutes")
        address = order.address

        await message.answer(
            f'Company: {company}\n'
            f'Earned bonuses: {earned_bonuses}\n'
            f'Date and time: {date}, {time}\n'
            f'Address: {address}'
        )

    await main_menu(message, telegram_id)


async def confirm_delete_product(message: Message, product_id: int):
    await message.delete()
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='✅', callback_data=f'{product_id}-conf-del-prod'),
        InlineKeyboardButton(text='❌', callback_data='deny-delete')
    )
    await message.answer('Do you really want to delete this product?',
                         reply_markup=builder.as_markup())


async def confirm_delete_company(message: Message, company_id: int):
    await message.delete()
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='✅', callback_data=f'{company_id}-conf-del-comp'),
        InlineKeyboardButton(text='❌', callback_data='deny-delete')
    )
    await message.answer('Do you really want to delete this company? All products inside will be deleted too',
                         reply_markup=builder.as_markup())


async def delete_product(message: Message, state: FSMContext, product_id: int):
    await message.delete()
    await database.Product.delete(message, state, product_id)


async def delete_company(message: Message, state: FSMContext, company_id: int):
    await message.delete()
    await database.Company.delete(message, state, company_id)


async def image_question(message: Message, product_category: str = None, company_id: int = None):
    builder = InlineKeyboardBuilder()
    builder.button(text='DROPBOX', callback_data=f'{product_category}-{company_id}-dropbox')
    builder.button(text='LINK', callback_data=f'{product_category}-{company_id}-link')
    markup = builder.as_markup()

    await message.answer('You will upload image from your PC or use link', reply_markup=markup)


async def choose_kitchen_category(message: Message, image_way: str):
    await message.delete()
    categories = database.Kitchen.get_all()
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(text=category.title, callback_data=f'{category.id}-{image_way}-category')
    markup = builder.as_markup()
    await message.answer('Choose company category:', reply_markup=markup)


async def choose_company_country(message: Message, category_id: int, image_way: str):
    await message.delete()
    countries = database.Country.get_all()
    builder = InlineKeyboardBuilder()
    for country in countries:
        builder.add(
            InlineKeyboardButton(text=country.title, callback_data=f'{category_id}-{country.id}-{image_way}-country'))
    await message.answer('Choose company country:', reply_markup=builder.as_markup())


async def add_item_with_dropbox_link(message: Message, values: dict):
    item_type = values.get('type').lower()
    values.pop('type')
    values.pop('image_way')
    if item_type == "company":
        await database.Company.add_new(values)
    else:
        await database.Product.add_new(values)
    await message.answer('Item added')
    await main_menu(message, message.from_user.id)


async def answer_message(callback: CallbackQuery, state: FSMContext):
    text_split = callback.data.split(":")
    chat_id = int(text_split[0])
    user_id = int(text_split[1])
    question_message_id = int(text_split[2])
    message_id = callback.message.message_id
    await bot.send_message(callback.message.chat.id, "Enter your answer: ")
    await state.set_state(Form.answer)
    await state.update_data(chat_id=chat_id, user_id=user_id, question_message_id=question_message_id,
                            message_id=message_id)


async def ignore_message(callback: CallbackQuery):
    text_split = callback.data.split(":")
    chat_id = text_split[0]
    user_id = text_split[1]
    question_message_id = int(text_split[2])
    message_id = callback.message.message_id
    await bot.send_message(chat_id, "Unfortunately, your question was denied", reply_to_message_id=question_message_id)
    await bot.delete_message(GROUP_ID, message_id)
    await database.PendingUser.delete_pending(int(user_id))


async def send_alarm(admin_id: int, error: Exception):
    traceback_str = ''.join(traceback.format_tb(error.__traceback__))
    traceback_str = html.escape(traceback_str)

    alarm_message = (f"<b>ALARM!!! ALARM!!! THE PROBLEM DETECTED!!!:</b>\n"
                     f"{traceback_str}")

    max_message_length = 4096
    while len(alarm_message) > max_message_length:
        part = alarm_message[:max_message_length]
        alarm_message = alarm_message[max_message_length:]
        try:
            await bot.send_message(admin_id, part, parse_mode='HTML')
        except Exception as e:
            print(f"Can't send a part of the message {admin_id}: {e}")

    if alarm_message:
        try:
            await bot.send_message(admin_id, alarm_message, parse_mode='HTML')
        except Exception as e:
            print(f"Can't send the last part of the message {admin_id}: {e}")
