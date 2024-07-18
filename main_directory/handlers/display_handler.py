from aiogram import Bot
from aiogram.types import (CallbackQuery)
from aiogram.types import (InlineKeyboardMarkup, InlineKeyboardButton,
                           Message)

import main_directory.database_owm as database
from main_directory.config import TG_TOKEN

bot = Bot(token=TG_TOKEN)


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


async def companies_catalog(callback: CallbackQuery):
    page = int(callback.data.split('-')[0])

    # Number of rows and data for 1 page
    company, count = database.Company.get_for_catalog(page, skip_size=1)  # skip_size - display by one element

    buttons = [
        [InlineKeyboardButton(text='Return to main menu', callback_data='main menu')],
        [InlineKeyboardButton(text='Products of this company', callback_data=f"1-{company.id}-{page}-products")]
    ]

    if database.Consumer.is_admin(callback.from_user.id):
        buttons.append([InlineKeyboardButton(text='Add item', callback_data='add company')])
        buttons.append([InlineKeyboardButton(text='Delete item', callback_data=f'{company.id}-delete-company')])

    if page == 1:
        buttons.append([
            InlineKeyboardButton(text=f'{page}/{count}', callback_data=' '),
            InlineKeyboardButton(text='Forward --->', callback_data=f"{page + 1}-companies")
        ])
    elif page == count:
        buttons.append([
            InlineKeyboardButton(text='<--- Back', callback_data=f"{page - 1}-companies"),
            InlineKeyboardButton(text=f'{page}/{count}', callback_data=' ')
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text='<--- Back', callback_data=f"{page - 1}-companies"),
            InlineKeyboardButton(text=f'{page}/{count}', callback_data=' '),
            InlineKeyboardButton(text='Forward --->', callback_data=f"{page + 1}-companies")
        ])

    markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await bot.send_photo(callback.message.chat.id, photo=company.image_link,
                         caption=f'<b>{company.title}</b>\n\n'
                                 f'<b>Description:</b> '
                                 f'<i>{company.description}</i>\n', parse_mode="HTML", reply_markup=markup)


async def products_catalog(callback: CallbackQuery):
    text_split = callback.data.split('-')
    page = int(text_split[0])
    company_id = int(text_split[1])
    company_page = int(text_split[2])

    try:
        # Number of rows and data for 1 page
        product, count = database.Product.get_for_catalog(company_id, page, skip_size=1)

        buttons = [
            [InlineKeyboardButton(text='Return to main_directory menu', callback_data='main_directory menu')],
            [InlineKeyboardButton(text='Back to companies', callback_data=f"{company_page}-companies")]
        ]

        if database.Consumer.is_admin(callback.from_user.id):
            buttons.append([InlineKeyboardButton(text='Add item', callback_data=f'{company_id}-add product')])
            buttons.append([InlineKeyboardButton(text='Delete item', callback_data=f'{product.id}-delete-product')])

        if database.Consumer.is_authenticated(callback.from_user.id):
            buttons.append([
                InlineKeyboardButton(text='Add to basket', callback_data=f'{product.id}-add-basket'),
                InlineKeyboardButton(text='Add to wishlist', callback_data=f'{product.id}-add-wish')
            ])

        if page == 1:
            buttons.append([
                InlineKeyboardButton(text=f'{page}/{count}', callback_data=' '),
                InlineKeyboardButton(text='Forward --->',
                                     callback_data=f"{page + 1}-{company_id}-{company_page}-products")
            ])
        elif page == count:
            buttons.append([
                InlineKeyboardButton(text='<--- Back',
                                     callback_data=f"{page - 1}-{company_id}-{company_page}-products"),
                InlineKeyboardButton(text=f'{page}/{count}', callback_data=' ')
            ])
        else:
            buttons.append([
                InlineKeyboardButton(text='<--- Back',
                                     callback_data=f"{page - 1}-{company_id}-{company_page}-products"),
                InlineKeyboardButton(text=f'{page}/{count}', callback_data=' '),
                InlineKeyboardButton(text='Forward --->',
                                     callback_data=f"{page + 1}-{company_id}-{company_page}-products")
            ])

        markup = InlineKeyboardMarkup(inline_keyboard=buttons)

        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
        await bot.send_photo(callback.message.chat.id, photo=product.image_link,
                             caption=f'<b>{product.title}</b>\n\n'
                                     f'<b>Description:</b> '
                                     f'<i>{product.description}</i>\n'
                                     f'<b>Composition:</b> '
                                     f'<i>{product.composition}</i>\n', parse_mode="HTML", reply_markup=markup)
    except AttributeError:
        if database.Consumer.is_admin(callback.from_user.id):
            buttons = [
                [InlineKeyboardButton(text='Add item', callback_data=f'{company_id}-add product')],
                [InlineKeyboardButton(text='Return to companies', callback_data='1-companies')]
            ]
            markup = InlineKeyboardMarkup(inline_keyboard=buttons)
            await bot.send_message(callback.message.chat.id,
                                   "The product list of this company is empty or not enough. But you can add a product",
                                   reply_markup=markup)
        else:
            await bot.send_message(callback.message.chat.id,
                                   "The product list of this company is empty or not enough. "
                                   "Wait until administrator add products")
            await main_menu(callback.message, callback.from_user.id)
