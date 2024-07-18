from aiogram.types import (InlineKeyboardMarkup, InlineKeyboardButton,
                           Message)

import main_directory.database_owm as database


async def main_menu(message: Message, user_id):
    inline_keyboard = []

    if database.Consumer.is_authenticated(user_id):
        profile_btn = InlineKeyboardButton(text='🎗️ Profile', callback_data='profile')
        orders_btn = InlineKeyboardButton(text='🧾 Orders', callback_data='orders')
        inline_keyboard.append([profile_btn, orders_btn])

    elif not database.Consumer.is_authenticated(user_id):
        login_btn = InlineKeyboardButton(text='👤 Login', callback_data='login')
        register_btn = InlineKeyboardButton(text='🆕 Registration', callback_data='register')
        inline_keyboard.append([login_btn, register_btn])

    catalog_btn = InlineKeyboardButton(text='🏪 Go to catalog', callback_data='1-companies')
    support_btn = InlineKeyboardButton(text='💬 Write to us', callback_data='help')
    site_btn = InlineKeyboardButton(text='🔗 Go to our site',
                                    url='http://flavourflow.eu-central-1.elasticbeanstalk.com')

    inline_keyboard.append([catalog_btn])
    inline_keyboard.append([support_btn])
    inline_keyboard.append([site_btn])
    markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    await message.answer("Main menu. Choose the option:", reply_markup=markup)
