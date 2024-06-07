import telebot
import dropbox_factory
import database_factory
from config import GROUP_ID, TG_TOKEN
from database_factory import Database

from telebot import types

database = Database()

bot = telebot.TeleBot(TG_TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id in database_factory.get_authorization_users():
        bot.send_message(message.chat.id, "Welcome. You are authorized!")
    else:
        bot.send_message(message.chat.id, "Welcome. You are not authorized! You can do it below")
    main_menu(message)


@bot.message_handler(commands=['help'])
def command_help(message):
    # bot.send_message(message.chat.id, message.chat.id)
    # bot.send_message(message.from_user.id, message.chat.id)
    if str(message.from_user.id) in database_factory.get_pending_users():
        bot.send_message(message.chat.id, 'You have already sent a message, please wait an answer')
    else:
        bot.send_message(message.chat.id, 'Enter your question')
        bot.register_next_step_handler(message, after_question, message.from_user.id)


@bot.message_handler(content_types=['photo'])
def handle_docs_photo(message):
    photo_id = bot.get_file(message.photo[len(message.photo) - 1].file_id).file_id
    photo_file = bot.get_file(photo_id)
    photo_bytes = bot.download_file(photo_file.file_path)
    dropbox_factory.upload_file(photo_bytes)


@bot.message_handler(commands=['image'])
def redirect(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Go to our site', url='http://flavourflow.eu-central-1.elasticbeanstalk.com')
    markup.row(btn1)
    btn2 = types.InlineKeyboardButton('Delete', callback_data='delete')
    btn3 = types.InlineKeyboardButton('Edit', callback_data='edit')
    markup.row(btn2, btn3)
    bot.send_photo(message.chat.id,
                   'https://dl.dropboxusercontent.com/scl/fi/3ydxuft93439s8klnjl6g/COMPANY2.jpg?rlkey=18aqwj4v50mozjjsfrcdc0pgg&dl=0',
                   reply_markup=markup, caption="text")


@bot.callback_query_handler(func=lambda call: True)
def callback_query(callback):
    if callback.data == 'delete':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)

    elif callback.data == 'edit':
        bot.edit_message_caption('Edit', callback.message.chat.id, callback.message.message_id)

    elif "answer" in callback.data:
        answer_message(callback)

    elif "ignore" in callback.data:
        ignore_message(callback)

    elif callback.data == "unseen":
        bot.delete_message(callback.message.chat.id, callback.message.message_id)

    elif "companies" in callback.data:
        companies_catalog(callback)

    elif "products" in callback.data:
        products_catalog(callback)

    elif callback.data == "login":
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        bot.send_message(callback.message.chat.id, 'Enter your username from Flavour Flow site')
        bot.register_next_step_handler(callback.message, after_login_username)

    elif callback.data == "register":
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        bot.send_message(callback.message.chat.id, 'Enter your username')
        bot.register_next_step_handler(callback.message, after_registration_username)


def main_menu(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Go to our site', url='http://flavourflow.eu-central-1.elasticbeanstalk.com')
    markup.add(btn1)
    if message.from_user.id in database_factory.get_authorization_users():
        btn2 = types.InlineKeyboardButton('Go to catalog', callback_data='1-companies')
        markup.add(btn2)
    else:
        btn2 = types.InlineKeyboardButton('Registration', callback_data='register')
        btn3 = types.InlineKeyboardButton('Login', callback_data='login')
        markup.row(btn2, btn3)
    bot.send_message(message.chat.id, "Main menu:", reply_markup=markup)


def after_question(message, user_id):
    bot.reply_to(message, "Your question was sent")
    database_factory.add_pending_user(user_id)
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('💬 Answer',
                                      callback_data=f'{message.chat.id}-{message.from_user.id}-{message.message_id}'
                                                    f'-answer')
    btn2 = types.InlineKeyboardButton('❎ Ignore',
                                      callback_data=f'{message.chat.id}-{message.from_user.id}-{message.message_id}'
                                                    f'-ignore')
    markup.row(btn1, btn2)
    bot.send_message(GROUP_ID,
                     f"<b>New question was taken!</b>"
                     f"\n<b>From:</b> @{message.from_user.username} ({message.from_user.first_name})"
                     f"\nID: {message.chat.id}"
                     f"\n<b>Message:</b> \"{message.text}\"", reply_markup=markup, parse_mode='HTML')


def after_login_username(message):
    username = message.text
    bot.send_message(message.chat.id, "Enter password")
    bot.register_next_step_handler(message, after_login_password, username)


def after_registration_username(message):
    username = message.text
    if username in database_factory.get_consumers_usernames():
        bot.send_message(message.chat.id, "This username is already in use")
        main_menu(message)
    else:
        bot.send_message(message.chat.id, "Enter email")
        bot.register_next_step_handler(message, after_registration_email, username)


def after_registration_email(message, username):
    email = message.text
    if email in database_factory.get_consumers_emails():
        bot.send_message(message.chat.id, "This email is already in use")
        main_menu(message)
    else:
        bot.send_message(message.chat.id, "Enter password")
        bot.register_next_step_handler(message, after_registration_password, username, email)


def after_registration_password(message, username, email):
    password = message.text
    bot.send_message(message.chat.id, "Confirm password")
    bot.register_next_step_handler(message, registration_result, username, email, password)


def registration_result(message, username, email, password):
    confirm_password = message.text
    if password == confirm_password and username not in database_factory.get_consumers_usernames():
        bot.send_message(message.chat.id, "Successful registration")
        database_factory.add_new_consumer(username, email, password, message.from_user.id)
        main_menu(message)

    elif not password == confirm_password:
        bot.send_message(message.chat.id, "Passwords are different, try again")
        main_menu(message)


def after_login_password(message, username):
    result, is_correct_username = database_factory.get_user_by_username(username)
    is_correct_password = database_factory.verify_password(result, message.text)

    if is_correct_username and is_correct_password:
        database_factory.add_consumer_telebot_id(result, message.from_user.id)
        bot.send_message(message.chat.id, "Success authorization")
        main_menu(message)
    else:
        bot.send_message(message.chat.id, "Username or password is incorrect")


def after_answer(message, chat_id, message_id, user_id, question_message_id):
    bot.send_message(chat_id, f'Your have got an answer: \n<b>{message.text}</b>', parse_mode='HTML',
                     reply_to_message_id=question_message_id)
    bot.reply_to(message, 'Your answer was sent')
    database_factory.delete_pending_user(user_id)
    bot.delete_message(GROUP_ID, message_id)


def answer_message(callback):
    text_split = callback.data.split("-")
    chat_id = text_split[0]
    user_id = text_split[1]
    question_message_id = text_split[2]
    message_id = callback.message.message_id
    bot.send_message(callback.message.chat.id, "Enter your answer: ")
    bot.register_next_step_handler(callback.message, after_answer, chat_id, message_id, user_id, question_message_id)


def ignore_message(callback):
    text_split = callback.data.split("-")
    chat_id = text_split[0]
    user_id = text_split[1]
    question_message_id = text_split[2]
    message_id = callback.message.message_id
    bot.send_message(chat_id, "Unfortunately, your question was denied", reply_to_message_id=question_message_id)
    bot.delete_message(GROUP_ID, message_id)
    database_factory.delete_pending_user(user_id)


def companies_catalog(callback):
    page = int(callback.data.split('-')[0])

    # Number of rows and data for 1 page
    data, count = database.data_list_for_page(tables='company', order='title', page=page,
                                              skip_size=1)  # SkipSize - display by one element

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Hide', callback_data='unseen'))

    markup.add(
        types.InlineKeyboardButton(text='Products of this company', callback_data=f"1-{data[3]}-{page}-products"))

    if page == 1:
        markup.add(types.InlineKeyboardButton(text=f'{page}/{count}', callback_data=f' '),
                   types.InlineKeyboardButton(text=f'Forward --->', callback_data=f"{page + 1}-companies"))

    elif page == count:
        markup.add(types.InlineKeyboardButton(text=f'<--- Back', callback_data=f"{page - 1}-companies"),
                   types.InlineKeyboardButton(text=f'{page}/{count}', callback_data=f' '))
    else:
        markup.add(types.InlineKeyboardButton(text=f'<--- Back', callback_data=f"{page - 1}-companies"),
                   types.InlineKeyboardButton(text=f'{page}/{count}', callback_data=f' '),
                   types.InlineKeyboardButton(text=f'Forward --->', callback_data=f"{page + 1}-companies"))

    bot.delete_message(callback.message.chat.id, callback.message.message_id)
    bot.send_photo(callback.message.chat.id, photo=data[5], caption=f'<b>{data[6]}</b>\n\n'
                                                                    f'<b>Description:</b> <i>{data[4]}</i>\n',
                   parse_mode="HTML", reply_markup=markup)


def products_catalog(callback):
    text_split = callback.data.split('-')
    page = int(text_split[0])
    company_id = int(text_split[1])
    company_page = int(text_split[2])

    # Number of rows and data for 1 page
    data, count = database.data_list_for_page(tables='product', order='title', page=page,
                                              skip_size=1,  # SkipSize - display by one element
                                              wheres=f"WHERE company_id = {company_id}")

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Hide', callback_data='unseen'))
    markup.add(types.InlineKeyboardButton(text='Bask to companies', callback_data=f"{company_page}-companies"))

    add_to_basket = types.InlineKeyboardButton('Add to basket', callback_data=' ')
    add_to_wishlist = types.InlineKeyboardButton('Add to wishlist', callback_data=' ')
    markup.row(add_to_basket, add_to_wishlist)

    if page == 1:
        markup.add(types.InlineKeyboardButton(text=f'{page}/{count}', callback_data=f' '),
                   types.InlineKeyboardButton(text=f'Forward --->',
                                              callback_data=f"{page + 1}-{company_id}-{company_page}-products"))

    elif page == count:
        markup.add(
            types.InlineKeyboardButton(text=f'<--- Back',
                                       callback_data=f"{page - 1}-{company_id}-{company_page}-products"),
            types.InlineKeyboardButton(text=f'{page}/{count}', callback_data=f' '))
    else:
        markup.add(
            types.InlineKeyboardButton(text=f'<--- Back',
                                       callback_data=f"{page - 1}-{company_id}-{company_page}-products"),
            types.InlineKeyboardButton(text=f'{page}/{count}', callback_data=f' '),
            types.InlineKeyboardButton(text=f'Forward --->',
                                       callback_data=f"{page + 1}-{company_id}-{company_page}-products"))

    bot.delete_message(callback.message.chat.id, callback.message.message_id)
    bot.send_photo(callback.message.chat.id, photo=data[5], caption=f'<b>{data[6]}</b>\n\n'
                                                                    f'<b>Description:</b> <i>{data[4]}</i>\n',
                   parse_mode="HTML", reply_markup=markup)


@bot.message_handler()
def info(message):
    if message.text.lower() == "hi":
        bot.send_message(message.chat.id, f'Hello {message.from_user.first_name}')
    elif message.text.lower() == "id":
        bot.reply_to(message, f'ID: {message.from_user.id}')


if __name__ == '__main__':
    bot.polling(none_stop=True)
