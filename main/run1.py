import re
from time import sleep
import traceback
import asyncio
from aiogram import Router, Bot, Dispatcher, types, F
# from aiogram.utils import executor
from aiogram.filters import Command, CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import (InlineKeyboardMarkup, InlineKeyboardButton,
                           Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton)
import logging
import database_owm as database
import dropbox_factory as dropbox
from config import GROUP_ID, TG_TOKEN, ADMIN_ID, ADMIN2_ID

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TG_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)


@router.message(CommandStart())
async def start(message: Message):
    if message.chat.type != 'private':
        await message.answer("I don't work in groups")
        return

    if database.Consumer.is_authenticated(message.from_user.id):
        user = database.Consumer.get_by_telegram_id(message.from_user.id)
        await message.answer(f"Welcome. You are authorized as {user.enter_login_password}!")
    else:
        await message.answer("Welcome. You are not authorized! You can do it below")

    await main_menu(message)


@router.message(Command('menu'))
async def start(message: Message):
    if message.chat.type != 'private':
        await message.answer("I don't work in groups")
        return
    await main_menu(message)


@router.message(Command('logout'))
async def command_help(message: Message):
    if message.chat.type != 'private':
        await message.answer("I don't work in groups")
        return

    try:
        username = database.Consumer.get_by_telegram_id(message.from_user.id).enter_login_password
        database.Consumer.change_telegram_id(username, 0)
        await message.answer("Successfully logout")
        await main_menu(message)
    except AttributeError:
        await message.answer("You are not authorized!")
        await main_menu(message)


@router.message(Command('image'))
async def redirect(message: Message):
    builder = InlineKeyboardBuilder()

    builder.button(text='Go to our site', url='http://flavourflow.eu-central-1.elasticbeanstalk.com')
    builder.button(text='Delete', callback_data='delete')
    builder.button(text='Edit', callback_data='edit')
    builder.adjust(1, 2)

    await bot.send_photo(
        chat_id=message.chat.id,
        photo='https://dl.dropboxusercontent.com/scl/fi/3ydxuft93439s8klnjl6g/COMPANY2.jpg?rlkey=18aqwj4v50mozjjsfrcdc0pgg&dl=0',
        caption="text",
        reply_markup=builder.as_markup()
    )


class Form(StatesGroup):
    enter_login_password = State()
    login = State()
    enter_email = State()
    enter_registration_password = State()
    login_result = State()
    enter_confirm_password = State()
    confirm_password = State()
    question = State()
    product_title = State()
    company_title = State()
    product_description = State()
    product_composition = State()
    product_price = State()
    image_link = State()
    upload_img = State()
    add_item = State()
    company_description = State()


@router.callback_query(lambda call: True)
async def process_callback(callback_query: CallbackQuery, state: FSMContext):
    data = callback_query.data
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    if "answer" in data:
        await answer_message(callback_query)

    elif "ignore" in data:
        await ignore_message(callback_query)

    elif "companies" in data:
        await companies_catalog(callback_query)

    elif "products" in data:
        await products_catalog(callback_query)

    elif "add-basket" in data:
        product_id = int(data.split('-')[0])
        await bot.send_message(chat_id, database.BasketObject.add_new(product_id, user_id))

    elif "add-wish" in data:
        product_id = int(data.split('-')[0])
        await bot.send_message(chat_id, database.WishObject.add_new(product_id, user_id))

    elif data == "profile":
        await print_profile_info(callback_query.message)

    elif data == "orders":
        await print_orders_info(callback_query.message)

    elif data == "main menu":
        await bot.delete_message(chat_id, callback_query.message.message_id)
        await main_menu(callback_query.message)

    elif data == "login":
        await bot.delete_message(chat_id, callback_query.message.message_id)
        await state.set_state(Form.enter_login_password)
        await bot.send_message(chat_id, 'Enter your username from Flavour Flow site')

    elif data == "register":
        await bot.delete_message(chat_id, callback_query.message.message_id)
        await state.set_state(Form.enter_email)
        await bot.send_message(chat_id, 'Enter your username')

    elif data == "help":
        if not database.PendingUser.is_pending(user_id):
            await bot.send_message(chat_id, 'Enter your question')
            await state.set_state(Form.question)
        else:
            await bot.send_message(chat_id, 'You have already sent a message, please wait an answer')

    if "add product" in data:
        company_id = int(data.split('-')[0])
        await bot.delete_message(chat_id, callback_query.message.message_id)
        markup = InlineKeyboardBuilder()
        markup.button(text='MEAL', callback_data=f'{company_id}-meal')
        markup.button(text='DRINK', callback_data=f'{company_id}-drink')
        markup.adjust(1, 1)
        await bot.send_message(chat_id, 'Choose product category', reply_markup=markup.as_markup())

    elif "add company" in data:
        await bot.delete_message(chat_id, callback_query.message.message_id)
        await image_question(callback_query.message)

    elif "meal" in data:
        company_id = int(data.split('-')[0])
        await bot.delete_message(chat_id, callback_query.message.message_id)
        await image_question(callback_query.message, "MEAL", company_id)

    elif "drink" in data:
        company_id = int(data.split('-')[0])
        await bot.delete_message(chat_id, callback_query.message.message_id)
        await image_question(callback_query.message, "DRINK", company_id)

    elif "dropbox" in data:
        try:
            product_category = data.split('-')[0]
            company_id = int(data.split('-')[1])
            values = {'type': 'PRODUCT', 'product_category': product_category, 'image_way': 'DROPBOX', 'company_id': company_id}
            await state.update_data(values=values)
            await state.set_state(Form.product_title)
            await enter_product_title(callback_query.message, state)
        except ValueError:
            await choose_kitchen_category(callback_query.message, 'DROPBOX')

    elif "link" in data:
        try:
            company_id = int(data.split('-')[1])
            product_category = data.split('-')[0]
            values = {'type': 'PRODUCT', 'product_category': product_category, 'image_way': 'LINK', 'company_id': company_id}
            await state.update_data(values=values)
            await state.set_state(Form.product_title)
            await enter_product_title(callback_query.message, state)
        except ValueError:
            await choose_kitchen_category(callback_query.message, 'LINK')

    elif "category" in data:
        category_id = int(data.split('-')[0])
        image_way = data.split('-')[1]
        await choose_company_country(callback_query.message, category_id, image_way)

    elif "country" in data:
        category_id = int(data.split('-')[0])
        country_id = int(data.split('-')[1])
        image_way = data.split('-')[2]
        await state.set_state(Form.company_title)
        await enter_company_title(callback_query.message, category_id, country_id, image_way)

    elif "delete-product" in data:
        product_id = int(data.split('-')[0])
        await confirm_delete_product(callback_query.message, product_id)

    elif "delete-company" in data:
        company_id = int(data.split('-')[0])
        await confirm_delete_company(callback_query.message, company_id)

    elif "conf-del-prod" in data:
        product_id = int(data.split('-')[0])
        await delete_product(callback_query.message, product_id)

    elif "conf-del-comp" in data:
        company_id = int(data.split('-')[0])
        await delete_company(callback_query.message, company_id)

    elif "deny-delete" in data:
        await bot.delete_message(chat_id, callback_query.message.message_id)
        await main_menu(callback_query.message)


async def print_profile_info(message: Message):
    user_profile = database.Consumer.get_by_telegram_id(message.from_user.id)
    await bot.send_message(message.chat.id, f'Flavour Flow user information:'
                                      f'\nUsername: {user_profile.enter_login_password}'
                                      f'\nEmail: {user_profile.enter_email}'
                                      f'\nBonuses: {user_profile.bonuses}')
    await main_menu(message)


async def print_orders_info(message: Message):
    user_id = database.Consumer.get_by_telegram_id(message.from_user.id).id
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

    await main_menu(message)


async def confirm_delete_product(message: Message, product_id: int):
    await bot.delete_message(message.chat.id, message.message_id)
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='✅', callback_data=f'{product_id}-conf-del-prod'),
        InlineKeyboardButton(text='❌', callback_data='deny-delete')
    )
    await bot.send_message(message.chat.id, 'Do you really want to delete this product?',
                           reply_markup=builder.as_markup())


async def confirm_delete_company(message, company_id):
    await bot.delete_message(message.chat.id, message.message_id)
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='✅', callback_data=f'{company_id}-conf-del-comp'),
        InlineKeyboardButton(text='❌', callback_data='deny-delete')
    )
    await bot.send_message(message.chat.id, 'Do you really want to delete this company? All products inside will be deleted too', reply_markup=builder.as_markup())


async def delete_product(message, product_id):
    await bot.delete_message(message.chat.id, message.message_id)
    database.Product.delete(message, bot, product_id)
    await bot.send_message(message.chat.id, 'Deleted successfully')
    await main_menu(message)


async def delete_company(message, company_id):
    await bot.delete_message(message.chat.id, message.message_id)
    database.Company.delete(message, bot, company_id)


async def image_question(message, product_category=None, company_id=None):
    builder = InlineKeyboardBuilder()
    builder.button(text='DROPBOX', callback_data=f'{product_category}-{company_id}-dropbox')
    builder.button(text='LINK', callback_data=f'{product_category}-{company_id}-link')
    markup = builder.as_markup()

    await bot.send_message(message.chat.id, 'You will upload image from your PC or use link', reply_markup=markup)


@router.message(Form.product_title)
async def enter_product_title(message: Message, state: FSMContext):
    data = await state.get_data()
    values = data.get('values', {})
    await state.update_data(title=message.text)
    await state.set_state(Form.product_description)
    await message.reply('Enter product description:')


async def choose_kitchen_category(message: Message, image_way):
    await bot.delete_message(message.chat.id, message.message_id)
    categories = database.Kitchen.get_all()
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(text=category.title, callback_data=f'{category.id}-{image_way}-category')
    markup = builder.as_markup()
    await bot.send_message(message.chat.id, 'Choose company category:', reply_markup=markup)


async def choose_company_country(message, category_id, image_way):
    await bot.delete_message(message.chat.id, message.message_id)
    countries = database.Country.get_all()
    builder = InlineKeyboardBuilder()
    for country in countries:
        builder.add(InlineKeyboardButton(text=country.title, callback_data=f'{category_id}-{country.id}-{image_way}-country'))
    await bot.send_message(message.chat.id, 'Choose company country:', reply_markup=builder.as_markup())


@router.message(Form.company_title)
async def enter_company_title(message, country_id, category_id, image_way, state: FSMContext):
    values = {'type': 'COMPANY', 'image_way': image_way, 'country_id': country_id, 'category_id': category_id}
    await state.update_data(values=values)
    await bot.delete_message(message.chat.id, message.message_id)
    await message.reply('Enter company title:')
    await state.set_state(Form.company_description)


@router.message(Form.company_description)
async def enter_company_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await bot.send_message(message.chat.id, 'Enter company description:')
    await state.set_state(Form.image_link)


@router.message(Form.product_description)
async def enter_product_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(Form.product_composition)
    await message.reply('Enter product composition:')


@router.message(Form.product_composition)
async def enter_product_composition(message: Message, state: FSMContext):
    await state.update_data(composition=message.text)
    await state.set_state(Form.product_price)
    await message.reply('Enter product price (use only numbers):')


@router.message(Form.product_price)
async def enter_product_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await state.set_state(Form.image_link)
    await message.reply('Enter product composition:')


@router.message(Form.image_link)
async def send_image_or_link(message: Message, values: dict, state: FSMContext):
    if values.get('type') == 'COMPANY':
        values.update({'description': message.text})
    else:
        try:
            values.update({'price': float(message.text)})
        except ValueError:
            await message.answer('I told you to use only numbers. Try again')
            await main_menu(message)
            return False

    if values.get('image_way') == 'DROPBOX':
        await message.answer('Send here your image')
        await state.set_state(Form.upload_img)
        await state.update_data(values=values)
    elif values.get('image_way') == 'LINK':
        await message.answer('Enter your link')
        await state.set_state(Form.add_item)
        await state.update_data(values=values)


@router.message(Form.upload_img)
async def upload_image(message: Message, state: FSMContext):
    data = await state.get_data()
    values = data.get('values', {})
    try:
        photo_id = message.photo[-1].file_id
        photo_file = await bot.get_file(photo_id)
        photo_bytes = await bot.download_file(photo_file.file_path)
        dropbox.upload_file(message, photo_bytes, bot, values)
    except TypeError:
        await message.answer('It is not an image')
        await main_menu(message)


@router.message(Form.add_item)
async def add_item_with_link(message: Message, state: FSMContext):
    data = await state.get_data()
    values = data.get('values', {})
    item_type = values.get('type').lower()
    values.update({'image_link': message.text})
    values.pop('type')
    values.pop('image_way')
    if item_type == "company":
        database.Company.add_new(values)
    else:
        database.Product.add_new(values)
    await message.answer('Item added')
    await main_menu(message)


async def add_item_with_dropbox_link(message, values):
    item_type = values.get('type').lower()
    values.pop('type')
    values.pop('image_way')
    database.Company.add_new(values) if item_type == "company" else database.Product.add_new(values)
    await bot.send_message(message.chat.id, 'Item added')
    await main_menu(message)


async def main_menu(message: Message):
    # markup = types.InlineKeyboardMarkup(inline_keyboard=[])
    inline_keyboard = []

    if database.Consumer.is_authenticated(message.from_user.id):
        profile_btn = InlineKeyboardButton(text='🎗️ Profile', callback_data='profile')
        orders_btn = InlineKeyboardButton(text='🧾 Orders', callback_data='orders')
        inline_keyboard.append([profile_btn, orders_btn])

    elif not database.Consumer.is_authenticated(message.from_user.id):
        login_btn = InlineKeyboardButton(text='👤 Login', callback_data='login')
        register_btn = InlineKeyboardButton(text='🆕 Registration', callback_data='register')
        inline_keyboard.append([login_btn, register_btn])

    catalog_btn = InlineKeyboardButton(text='🏪 Go to catalog', callback_data='1-companies')
    support_btn = InlineKeyboardButton(text='💬 Write to us', callback_data='help')
    site_btn = InlineKeyboardButton(text='🔗 Go to our site',
                                    url='http://flavourflow.eu-central-1.elasticbeanstalk.com')

    inline_keyboard.append([catalog_btn])
    inline_keyboard.append([ support_btn])
    inline_keyboard.append([ site_btn])
    markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    await message.answer("Main menu. Choose the option:", reply_markup=markup)


@router.message(Form.question)
async def send_question_to_support_group(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await message.reply("Your question was sent")
    await main_menu(message)
    database.PendingUser.add_new_pending(user_id)
    markup = InlineKeyboardBuilder()
    markup.button(text='💬 Answer', callback_data=f"action:answer:{user_id}")
    markup.button(text='❌ Ignore', callback_data=f"action:ignore:{user_id}")
    markup.adjust(1, 1)

    await bot.send_message(GROUP_ID,
                           f"<b>New question was taken!</b>"
                           f"\n<b>From:</b> {message.from_user.first_name} (FFlow username: "
                           f"{database.Consumer.get_by_telegram_id(message.from_user.id).enter_login_password})"
                           f"\nID: {message.chat.id}"
                           f"\n<b>Message:</b> \"{message.text}\"", reply_markup=markup.as_markup(), parse_mode='HTML')
    # await state.clear()


@router.message(Form.enter_login_password)
async def enter_login_password(message: types.Message, state: FSMContext):
    await state.update_data(username=message.text)
    await state.set_state(Form.login_result)
    await message.reply("Enter password")


@router.message(Form.enter_email)
async def enter_email(message: types.Message, state: FSMContext):
    username = message.text
    await state.update_data(username=username)
    # username = message.text
    # values = {'username': username}
    if not database.Consumer.is_username_already_exists(username) and re.search(r'^[a-zA-Z][a-zA-Z0-9_]*$',
                                                                                username) is not None:
        await state.set_state(Form.enter_registration_password)
        await message.reply("Enter email")

    elif database.Consumer.is_username_already_exists(username):
        await bot.send_message(message.chat.id, "This username is already in use")
        await main_menu(message)

    elif re.search(r'^[a-zA-Z][a-zA-Z0-9_]*$', username) is None:
        await message.reply("Username must start with a letter and contain only letters, numbers, and underscores")
        await main_menu(message)


@router.message(Form.enter_registration_password)
async def enter_registration_password(message: types.Message, state: FSMContext):
    email = message.text
    await state.update_data(email=email)
    if not database.Consumer.is_email_already_exists(email) and re.search(r'^[^\s@]+@[^\s@]+\.[^\s@]+$',
                                                                          email) is not None:
        await state.set_state(Form.enter_confirm_password)
        await message.reply("Enter password")

    elif database.Consumer.is_email_already_exists(email):
        await message.reply("This email is already in use")
        await main_menu(message)

    elif re.search(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email) is None:
        await message.reply("Incorrect email")
        await main_menu(message)


@router.message(Form.enter_confirm_password)
async def enter_confirm_password(message: types.Message, state: FSMContext):
    password = message.text
    await state.update_data(password=password)
    # values.update({'password': password})
    if re.search(r'^(?=.*[a-zA-Z])(?=.*\d)(?=.*[\W_]).{6,15}$', password) is not None:
        await message.reply("Confirm password")
        await state.set_state(Form.confirm_password)

    else:
        await bot.send_message(message.chat.id,
                         "Password must be 6-15 characters long and contain at least one letter, "
                         "one digit, and one special character")
        await main_menu(message)


@router.message(Form.confirm_password)
async def registration_result(message: types.Message, state: FSMContext):
    confirm_password = message.text
    user_data = await state.get_data()
    password = user_data['password']
    username = user_data['email']

    if password == confirm_password and not database.Consumer.is_username_already_exists(username):
        user_data.update({'telegram_id': message.from_user.id})
        database.Consumer.add_new(user_data)
        await message.reply(
            f"Successful registration. Welcome " 
        f" {database.Consumer.get_by_telegram_id(message.from_user.id).enter_login_password}!")
        await main_menu(message)
    elif password != confirm_password:
        await message.reply("Passwords are different, try again")
        await main_menu(message)

    await state.clear()


@router.message(Form.login_result)
async def login_result(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    username = user_data['username']
    password = message.text

    is_correct_username = database.Consumer.is_username_already_exists(username)
    is_correct_password = database.Consumer.verify_password(username, password)

    if is_correct_username and is_correct_password:
        database.Consumer.change_telegram_id(username, message.from_user.id)
        await message.reply(f"Success authorization. Welcome "
                            f"{database.Consumer.get_by_telegram_id(message.from_user.id).enter_login_password}!")
        await main_menu(message)
    else:
        await message.reply("Username or password is incorrect")
        await main_menu(message)


async def send_answer(message: Message, chat_id: int, message_id: int, user_id: int, question_message_id: int):
    await bot.send_message(chat_id, f'Your have got an answer: \n<b>{message.text}</b>', parse_mode='HTML',
                           reply_to_message_id=question_message_id)
    await message.reply('Your answer was sent')
    database.PendingUser.delete_pending(user_id)
    await bot.delete_message(GROUP_ID, message_id)


async def answer_message(callback: CallbackQuery):
    text_split = callback.data.split("-")
    chat_id = text_split[0]
    user_id = text_split[1]
    question_message_id = text_split[2]
    message_id = callback.message.message_id
    await bot.send_message(callback.message.chat.id, "Enter your answer: ")
    dp.message.register(send_answer, F.chat.id == callback.message.chat.id, chat_id, message_id, user_id, question_message_id)


async def ignore_message(callback):
    text_split = callback.data.split("-")
    chat_id = text_split[0]
    user_id = text_split[1]
    question_message_id = text_split[2]
    message_id = callback.message.message_id
    await bot.send_message(chat_id, "Unfortunately, your question was denied", reply_to_message_id=question_message_id)
    await bot.delete_message(GROUP_ID, message_id)
    database.PendingUser.delete_pending(user_id)


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
    await bot.send_photo(callback.message.chat.id, photo=company.image_link, caption=f'<b>{company.title}</b>\n\n'
                                                                                     f'<b>Description:</b> '
                                                                                     f'<i>{company.description}</i>\n',
                         parse_mode="HTML", reply_markup=markup)


async def products_catalog(callback: CallbackQuery):
    text_split = callback.data.split('-')
    page = int(text_split[0])
    company_id = int(text_split[1])
    company_page = int(text_split[2])

    try:
        # Number of rows and data for 1 page
        product, count = database.Product.get_for_catalog(company_id, page, skip_size=1)

        buttons = [
            [InlineKeyboardButton(text='Return to main menu', callback_data='main menu')],
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
                InlineKeyboardButton(text='Forward --->', callback_data=f"{page + 1}-{company_id}-{company_page}-products")
            ])
        elif page == count:
            buttons.append([
                InlineKeyboardButton(text='<--- Back', callback_data=f"{page - 1}-{company_id}-{company_page}-products"),
                InlineKeyboardButton(text=f'{page}/{count}', callback_data=' ')
            ])
        else:
            buttons.append([
                InlineKeyboardButton(text='<--- Back', callback_data=f"{page - 1}-{company_id}-{company_page}-products"),
                InlineKeyboardButton(text=f'{page}/{count}', callback_data=' '),
                InlineKeyboardButton(text='Forward --->', callback_data=f"{page + 1}-{company_id}-{company_page}-products")
            ])

        markup = InlineKeyboardMarkup(inline_keyboard=buttons)

        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
        await bot.send_photo(callback.message.chat.id, photo=product.image_link, caption=f'<b>{product.title}</b>\n\n'
                                                                                         f'<b>Description:</b> '
                                                                                         f'<i>{product.description}</i>\n'
                                                                                         f'<b>Composition:</b> '
                                                                                         f'<i>{product.composition}</i>\n',
                             parse_mode="HTML", reply_markup=markup)
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
            await main_menu(callback.message)


async def send_alarm(bot: Bot, admin_id: int, message: str):
    try:
        await bot.send_message(admin_id, message, parse_mode='html')
    except Exception as e:
        print(f"Failed to send message to {admin_id}: {e}")


async def main():
    while True:
        try:
            await dp.start_polling(bot)
        except Exception as ex:
            traceback_str = ''.join(traceback.format_tb(ex.__traceback__))
            alarm_message = (f"<b>ALARM!!! ALARM!!! THE PROBLEM DETECTED!!!:</b>\n"
                             f"{traceback_str}")
            print(traceback_str)

            await send_alarm(bot, ADMIN_ID, alarm_message)
            await send_alarm(bot, ADMIN2_ID, alarm_message)

            database.session.rollback()
            await asyncio.sleep(15)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')