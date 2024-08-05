import logging
import re

from aiogram import Router, Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (Message)
from aiogram.utils.keyboard import InlineKeyboardBuilder

import application.database_owm as database
import application.dropbox_factory as dropbox
from application.config import GROUP_ID, TG_TOKEN
from application.handlers.display_handler import main_menu

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TG_TOKEN)
router = Router()


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
    answer = State()


@router.message(Form.product_title)
async def enter_product_title(message: Message, state: FSMContext):
    await state.set_state(Form.product_description)
    await message.reply('Enter product title:')


@router.message(Form.company_title)
async def enter_company_title(message: Message, country_id, category_id, image_way, state: FSMContext):
    values = {'type': 'COMPANY', 'image_way': image_way, 'country_id': country_id, 'category_id': category_id}
    await state.update_data(values=values)
    await message.reply('Enter company title:')
    await state.set_state(Form.company_description)


@router.message(Form.company_description)
async def enter_company_description(message: Message, state: FSMContext):
    data = await state.get_data()
    values = data.get('values', {})
    values['title'] = message.text
    await state.update_data(title=message.text)
    await message.answer('Enter company description:')
    await state.set_state(Form.image_link)


@router.message(Form.product_description)
async def enter_product_description(message: Message, state: FSMContext):
    data = await state.get_data()
    values = data.get('values', {})
    values['title'] = message.text
    await state.update_data(title=message.text)
    await state.set_state(Form.product_composition)
    await message.reply('Enter product description:')


@router.message(Form.product_composition)
async def enter_product_composition(message: Message, state: FSMContext):
    data = await state.get_data()
    values = data.get('values', {})
    values['description'] = message.text
    await state.update_data(description=message.text)
    await state.set_state(Form.product_price)
    await message.reply('Enter product composition:')


@router.message(Form.product_price)
async def enter_product_price(message: types.Message, state: FSMContext):
    data = await state.get_data()
    values = data.get('values', {})
    values['composition'] = message.text
    await state.update_data(composition=message.text)
    await state.set_state(Form.image_link)
    await message.reply('Enter price:')


@router.message(Form.image_link)
async def send_image_or_link(message: Message, state: FSMContext):
    data = await state.get_data()
    values = data.get('values', {})
    if values.get('type') == 'COMPANY':
        values.update({'description': message.text})
    else:
        try:
            values.update({'price': float(message.text)})
        except ValueError:
            await message.answer('I told you to use only numbers. Try again')
            await main_menu(message, message.from_user.id)
            return False

    await state.update_data(values=values)

    if values.get('image_way') == 'DROPBOX':
        await message.answer('Send here your image')
        await state.set_state(Form.upload_img)
    elif values.get('image_way') == 'LINK':
        await message.answer('Enter your link')
        await state.set_state(Form.add_item)


@router.message(Form.upload_img)
async def upload_image(message: Message, state: FSMContext):
    data = await state.get_data()
    values = data.get('values', {})
    try:
        photo_id = message.photo[-1].file_id
        photo_file = await bot.get_file(photo_id)
        photo_bytes = await bot.download_file(photo_file.file_path)
        photo_bytes = photo_bytes.read()
        await dropbox.upload_file(message, photo_bytes, values, state)
    except TypeError:
        await message.answer('It is not an image')
        await main_menu(message, message.from_user.id)


@router.message(Form.add_item)
async def add_item_with_link(message: Message, state: FSMContext):
    data = await state.get_data()
    values = data.get('values', {})
    item_type = values.get('type').lower()
    values.update({'image_link': message.text})
    values.pop('type')
    values.pop('image_way')
    if item_type == "company":
        await database.Company.add_new(values)
    else:
        await database.Product.add_new(values)
    await message.answer('Item added')
    await main_menu(message, message.from_user.id)


@router.message(Form.question)
async def send_question_to_support_group(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await message.reply("Your question was sent")
    await main_menu(message, message.from_user.id)
    await database.PendingUser.add_new_pending(user_id)
    markup = InlineKeyboardBuilder()
    markup.button(text='💬 Answer', callback_data=f"{message.chat.id}:{user_id}:{message.message_id}:answer")
    markup.button(text='❌ Ignore', callback_data=f"{message.chat.id}:{user_id}:{message.message_id}:ignore")
    markup.adjust(1, 1)

    await bot.send_message(GROUP_ID,
                           f"<b>New question was taken!</b>"
                           f"\n<b>From:</b> {message.from_user.first_name} (FFlow username: "
                           f"{database.Consumer.get_by_telegram_id(message.from_user.id).username})"
                           f"\nID: {message.chat.id}"
                           f"\n<b>Message:</b> \"{message.text}\"", reply_markup=markup.as_markup(), parse_mode='HTML')
    await state.clear()


@router.message(Form.enter_login_password)
async def enter_login_password(message: types.Message, state: FSMContext):
    await state.update_data(username=message.text)
    await state.set_state(Form.login_result)
    await message.reply("Enter password")


@router.message(Form.enter_email)
async def enter_email(message: types.Message, state: FSMContext):
    username = message.text
    await state.update_data(username=username)
    if not database.Consumer.is_username_already_exists(username) and re.search(r'^[a-zA-Z][a-zA-Z0-9_]*$',
                                                                                username) is not None:
        await state.set_state(Form.enter_registration_password)
        await message.reply("Enter email")

    elif database.Consumer.is_username_already_exists(username):
        await message.reply("This username is already in use")
        await main_menu(message, message.from_user.id)

    elif re.search(r'^[a-zA-Z][a-zA-Z0-9_]*$', username) is None:
        await message.reply("Username must start with a letter and contain only letters, numbers, and underscores")
        await main_menu(message, message.from_user.id)


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
        await main_menu(message, message.from_user.id)

    elif re.search(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email) is None:
        await message.reply("Incorrect email")
        await main_menu(message, message.from_user.id)


@router.message(Form.enter_confirm_password)
async def enter_confirm_password(message: types.Message, state: FSMContext):
    password = message.text
    await state.update_data(password=password)
    if re.search(r'^(?=.*[a-zA-Z])(?=.*\d)(?=.*[\W_]).{6,15}$', password) is not None:
        await message.reply("Confirm password")
        await state.set_state(Form.confirm_password)

    else:
        await message.answer("Password must be 6-15 characters long and contain at least one letter, "
                             "one digit, and one special character")
        await main_menu(message, message.from_user.id)


@router.message(Form.confirm_password)
async def registration_result(message: types.Message, state: FSMContext):
    confirm_password = message.text
    user_data = await state.get_data()
    password = user_data['password']
    username = user_data['email']

    if password == confirm_password and not database.Consumer.is_username_already_exists(username):
        user_data.update({'telegram_id': message.from_user.id})
        await database.Consumer.add_new(user_data)
        consumer = database.Consumer.get_by_telegram_id(message.from_user.id)
        await message.reply(
            f"Successful registration. Welcome {consumer.username}!")
        await main_menu(message, message.from_user.id)
    elif password != confirm_password:
        await message.reply("Passwords are different, try again")
        await main_menu(message, message.from_user.id)

    await state.clear()


@router.message(Form.login_result)
async def login_result(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    username = user_data['username']
    password = message.text

    is_correct_username = database.Consumer.is_username_already_exists(username)
    is_correct_password = database.Consumer.verify_password(username, password)

    if is_correct_username and is_correct_password:
        await database.Consumer.change_telegram_id(username, message.from_user.id)
        await message.reply(f"Success authorization. Welcome "
                            f"{database.Consumer.get_by_telegram_id(message.from_user.id).username}!")
        await main_menu(message, message.from_user.id)
    else:
        await message.reply("Username or password is incorrect")
        await main_menu(message, message.from_user.id)


@router.message(Form.answer)
async def send_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data.get('chat_id')
    user_id = data.get('user_id')
    question_message_id = data.get('question_message_id')
    message_id = data.get('message_id')

    await bot.send_message(chat_id, f'You have received an answer:\n<b>{message.text}</b>', parse_mode='HTML',
                           reply_to_message_id=question_message_id)
    await message.reply('Your answer was sent')
    await database.PendingUser.delete_pending(user_id)
    await bot.delete_message(GROUP_ID, message_id)
    await state.clear()


def register_input_handler(dp):
    dp.include_router(router)
