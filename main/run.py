import re
from time import sleep

import telebot
from telebot import types

import database_owm as database
import dropbox_factory as dropbox
from config import GROUP_ID, TG_TOKEN, ADMIN_ID

bot = telebot.TeleBot(TG_TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    if not message.chat.type == 'private':
        bot.send_message(message.chat.id, "I don't work in groups")
        return False

    if database.Consumer.is_authenticated(message.from_user.id):
        bot.send_message(message.chat.id,
                         f"Welcome. You are authorized as "
                         f"{database.Consumer.get_by_telegram_id(message.from_user.id).username}!")
    else:
        bot.send_message(message.chat.id, "Welcome. You are not authorized! You can do it below")

    main_menu(message)


@bot.message_handler(commands=['menu'])
def start(message):
    if not message.chat.type == 'private':
        bot.send_message(message.chat.id, "I don't work in groups")
        return False
    main_menu(message)


@bot.message_handler(commands=['logout'])
def command_help(message):
    if not message.chat.type == 'private':
        bot.send_message(message.chat.id, "I don't work in groups")
        return False

    try:
        username = database.Consumer.get_by_telegram_id(message.from_user.id).username
        database.Consumer.change_telegram_id(username, 0)
        bot.send_message(message.from_user.id, "Successfully logout")
        main_menu(message)
    except AttributeError:
        bot.send_message(message.from_user.id, "You are not authorized!")
        main_menu(message)


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
    if "answer" in callback.data:
        answer_message(callback)

    elif "ignore" in callback.data:
        ignore_message(callback)

    elif "companies" in callback.data:
        companies_catalog(callback)

    elif "products" in callback.data:
        products_catalog(callback)

    elif "add-basket" in callback.data:
        product_id = int(callback.data.split('-')[0])
        bot.send_message(callback.message.chat.id, database.BasketObject.add_new(product_id, callback.from_user.id))

    elif "add-wish" in callback.data:
        product_id = int(callback.data.split('-')[0])
        bot.send_message(callback.message.chat.id, database.WishObject.add_new(product_id, callback.from_user.id))

    elif callback.data == "profile":
        callback.message.from_user.id = callback.from_user.id
        print_profile_info(callback.message)

    elif callback.data == "orders":
        callback.message.from_user.id = callback.from_user.id
        print_orders_info(callback.message)

    elif callback.data == "main menu":
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        callback.message.from_user.id = callback.from_user.id
        main_menu(callback.message)

    elif callback.data == "login":
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        bot.send_message(callback.message.chat.id, 'Enter your username from Flavour Flow site')
        bot.register_next_step_handler(callback.message, enter_login_password)

    elif callback.data == "register":
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        bot.send_message(callback.message.chat.id, 'Enter your username')
        bot.register_next_step_handler(callback.message, enter_email)

    elif callback.data == "help":

        if not database.PendingUser.is_pending(callback.from_user.id):
            bot.send_message(callback.message.chat.id, 'Enter your question')
            bot.register_next_step_handler(callback.message, send_question_to_support_group, callback.from_user.id)
        else:
            bot.send_message(callback.message.chat.id, 'You have already sent a message, please wait an answer')

    elif "add product" in callback.data:
        company_id = int(callback.data.split('-')[0])
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        markup = types.InlineKeyboardMarkup()
        meal_btn = types.InlineKeyboardButton('MEAL', callback_data=f'{company_id}-meal')
        drink_btn = types.InlineKeyboardButton('DRINK', callback_data=f'{company_id}-drink')
        markup.row(meal_btn, drink_btn)
        bot.send_message(callback.message.chat.id, 'Choose product category', reply_markup=markup)

    elif "add company" in callback.data:
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        image_question(callback.message)

    elif "meal" in callback.data:
        company_id = int(callback.data.split('-')[0])
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        image_question(callback.message, "MEAL", company_id)

    elif "drink" in callback.data:
        company_id = int(callback.data.split('-')[0])
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        image_question(callback.message, "DRINK", company_id)

    elif "dropbox" in callback.data:
        try:
            product_category = callback.data.split('-')[0]
            company_id = int(callback.data.split('-')[1])
            values = {'type': 'PRODUCT', 'product_category': product_category, 'image_way': 'DROPBOX',
                      'company_id': company_id}
            enter_product_title(callback.message, values)
        except ValueError:
            choose_kitchen_category(callback.message, 'DROPBOX')

    elif "link" in callback.data:
        try:
            company_id = int(callback.data.split('-')[1])
            product_category = callback.data.split('-')[0]
            values = {'type': 'PRODUCT', 'product_category': product_category, 'image_way': 'LINK',
                      'company_id': company_id}
            enter_product_title(callback.message, values)
        except ValueError:
            choose_kitchen_category(callback.message, 'LINK')

    elif "category" in callback.data:
        category_id = int(callback.data.split('-')[0])
        image_way = callback.data.split('-')[1]
        choose_company_country(callback.message, category_id, image_way)

    elif "country" in callback.data:
        category_id = int(callback.data.split('-')[0])
        country_id = int(callback.data.split('-')[1])
        image_way = callback.data.split('-')[2]
        enter_company_title(callback.message, category_id, country_id, image_way)

    elif "delete-product" in callback.data:
        product_id = int(callback.data.split('-')[0])
        confirm_delete_product(callback.message, product_id)

    elif "delete-company" in callback.data:
        company_id = int(callback.data.split('-')[0])
        confirm_delete_company(callback.message, company_id)

    elif "conf-del-prod" in callback.data:
        product_id = int(callback.data.split('-')[0])
        callback.message.from_user.id = callback.from_user.id
        delete_product(callback.message, product_id)

    elif "conf-del-comp" in callback.data:
        company_id = int(callback.data.split('-')[0])
        callback.message.from_user.id = callback.from_user.id
        delete_company(callback.message, company_id)

    elif "deny-delete" in callback.data:
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        callback.message.from_user.id = callback.from_user.id
        main_menu(callback.message)


def print_profile_info(message):
    user_profile = database.Consumer.get_by_telegram_id(message.from_user.id)
    bot.send_message(message.chat.id, f'Flavour Flow user information:'
                                      f'\nUsername: {user_profile.username}'
                                      f'\nEmail: {user_profile.email}'
                                      f'\nBonuses: {user_profile.bonuses}')
    main_menu(message)


def print_orders_info(message):
    user_id = database.Consumer.get_by_telegram_id(message.from_user.id).id
    orders = database.Order.get_all_by_user_id(user_id)
    bot.send_message(message.chat.id, f'Your orders:')
    for order in orders:
        bot.send_message(message.chat.id, f'Company: {database.Company.get_company_by_id(order.company_id).title}'
                                          f'\nEarned bonuses: {order.earned_bonuses}'
                                          f'\nDate and time: {order.date}, '
                                          f'{order.time.isoformat(timespec='minutes')}'
                                          f'\nAddress: {order.address}')

    main_menu(message)


def confirm_delete_product(message, product_id):
    bot.delete_message(message.chat.id, message.message_id)
    markup = types.InlineKeyboardMarkup()
    dbx_btn = types.InlineKeyboardButton('✅', callback_data=f'{product_id}-conf-del-prod')
    link_btn = types.InlineKeyboardButton('❌', callback_data=f'deny-delete')
    markup.row(dbx_btn, link_btn)
    bot.send_message(message.chat.id, 'Do you really want to delete this product?', reply_markup=markup)


def confirm_delete_company(message, company_id):
    bot.delete_message(message.chat.id, message.message_id)
    markup = types.InlineKeyboardMarkup()
    dbx_btn = types.InlineKeyboardButton('✅', callback_data=f'{company_id}-conf-del-comp')
    link_btn = types.InlineKeyboardButton('❌', callback_data=f'deny-delete')
    markup.row(dbx_btn, link_btn)
    bot.send_message(message.chat.id,
                     'Do you really want to delete this company? All products inside will be deleted too',
                     reply_markup=markup)


def delete_product(message, product_id):
    bot.delete_message(message.chat.id, message.message_id)
    database.Product.delete(message, bot, product_id)
    bot.send_message(message.chat.id, 'Deleted successfully')
    main_menu(message)


def delete_company(message, company_id):
    bot.delete_message(message.chat.id, message.message_id)
    database.Company.delete(message, bot, company_id)


def image_question(message, product_category=None, company_id=None):
    markup = types.InlineKeyboardMarkup()
    dbx_btn = types.InlineKeyboardButton('DROPBOX', callback_data=f'{product_category}-{company_id}-dropbox')
    link_btn = types.InlineKeyboardButton('LINK', callback_data=f'{product_category}-{company_id}-link')
    markup.row(dbx_btn, link_btn)
    bot.send_message(message.chat.id, 'You will upload image from your PC or use link', reply_markup=markup)


def enter_product_title(message, values):
    bot.delete_message(message.chat.id, message.message_id)
    bot.send_message(message.chat.id, 'Enter product title:')
    bot.register_next_step_handler(message, enter_product_description, values)


def choose_kitchen_category(message, image_way):
    bot.delete_message(message.chat.id, message.message_id)
    categories = database.Kitchen.get_all()
    markup = types.InlineKeyboardMarkup()
    for category in categories:
        category_btn = types.InlineKeyboardButton(category.title, callback_data=f'{category.id}-{image_way}-category')
        markup.add(category_btn)
    bot.send_message(message.chat.id, 'Choose company category:', reply_markup=markup)


def choose_company_country(message, category_id, image_way):
    bot.delete_message(message.chat.id, message.message_id)
    countries = database.Country.get_all()
    markup = types.InlineKeyboardMarkup()
    for country in countries:
        category_btn = types.InlineKeyboardButton(country.title,
                                                  callback_data=f'{category_id}-{country.id}-{image_way}-country')
        markup.add(category_btn)
    bot.send_message(message.chat.id, 'Choose company category:', reply_markup=markup)


def enter_company_title(message, country_id, category_id, image_way):
    values = {'type': 'COMPANY', 'image_way': image_way, 'country_id': country_id, 'category_id': category_id}
    bot.delete_message(message.chat.id, message.message_id)
    bot.send_message(message.chat.id, 'Enter company title:')
    bot.register_next_step_handler(message, enter_company_description, values)


def enter_company_description(message, values):
    values.update({'title': message.text})
    bot.send_message(message.chat.id, 'Enter company description:')
    bot.register_next_step_handler(message, send_image_or_link, values)


def enter_product_description(message, values):
    values.update({'title': message.text})
    bot.send_message(message.chat.id, 'Enter product description:')
    bot.register_next_step_handler(message, enter_product_composition, values)


def enter_product_composition(message, values):
    values.update({'description': message.text})
    bot.send_message(message.chat.id, 'Enter product composition:')
    bot.register_next_step_handler(message, enter_product_price, values)


def enter_product_price(message, values):
    values.update({'composition': message.text})
    bot.send_message(message.chat.id, 'Enter product price (use only numbers):')
    bot.register_next_step_handler(message, send_image_or_link, values)


def send_image_or_link(message, values):
    if values.get('type') == 'COMPANY':
        values.update({'description': message.text})
    else:
        try:
            values.update({'price': float(message.text)})
        except ValueError:
            bot.send_message(message.chat.id, 'I told you to use only numbers. Try again')
            main_menu(message)
            return False

    if values.get('image_way') == 'DROPBOX':
        bot.send_message(message.chat.id, 'Send here your image')
        bot.register_next_step_handler(message, upload_image, values)
    elif values.get('image_way') == 'LINK':
        bot.send_message(message.chat.id, 'Enter your link')
        bot.register_next_step_handler(message, add_item_with_link, values)


def upload_image(message, values):
    try:
        photo_id = bot.get_file(message.photo[len(message.photo) - 1].file_id).file_id
        photo_file = bot.get_file(photo_id)
        photo_bytes = bot.download_file(photo_file.file_path)
        dropbox.upload_file(message, photo_bytes, bot, values)
    except TypeError:
        bot.send_message(message.chat.id, 'It is not an image')
        main_menu(message)


def add_item_with_link(message, values):
    item_type = values.get('type').lower()
    values.update({'image_link': message.text})
    values.pop('type')
    values.pop('image_way')
    database.Company.add_new(values) if item_type == "company" else database.Product.add_new(values)
    bot.send_message(message.chat.id, 'Item added')
    main_menu(message)


def add_item_with_dropbox_link(message, values):
    item_type = values.get('type').lower()
    values.pop('type')
    values.pop('image_way')
    database.Company.add_new(values) if item_type == "company" else database.Product.add_new(values)
    bot.send_message(message.chat.id, 'Item added')
    main_menu(message)


def main_menu(message):
    markup = types.InlineKeyboardMarkup()

    if database.Consumer.is_authenticated(message.from_user.id):
        profile_btn = types.InlineKeyboardButton('🎗️ Profile', callback_data='profile')
        orders_btn = types.InlineKeyboardButton('🧾 Orders', callback_data='orders')
        markup.add(profile_btn)
        markup.add(orders_btn)

    elif not database.Consumer.is_authenticated(message.from_user.id):
        login_btn = types.InlineKeyboardButton('👤 Login', callback_data='login')
        register_btn = types.InlineKeyboardButton('🆕 Registration', callback_data='register')
        markup.row(login_btn, register_btn)

    catalog_btn = types.InlineKeyboardButton('🏪 Go to catalog', callback_data='1-companies')
    support_btn = types.InlineKeyboardButton('💬 Write to us', callback_data='help')
    site_btn = types.InlineKeyboardButton('🔗 Go to our site',
                                          url='http://flavourflow.eu-central-1.elasticbeanstalk.com')

    markup.add(catalog_btn)
    markup.add(support_btn)
    markup.add(site_btn)

    bot.send_message(message.chat.id, "Main menu. Choose the option:", reply_markup=markup)


def send_question_to_support_group(message, user_id):
    bot.reply_to(message, "Your question was sent")
    main_menu(message)
    database.PendingUser.add_new_pending(user_id)
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('💬 Answer',
                                      callback_data=f'{message.chat.id}-{message.from_user.id}-{message.message_id}'
                                                    f'-answer')
    btn2 = types.InlineKeyboardButton('❌ Ignore',
                                      callback_data=f'{message.chat.id}-{message.from_user.id}-{message.message_id}'
                                                    f'-ignore')
    markup.row(btn1, btn2)
    bot.send_message(GROUP_ID,
                     f"<b>New question was taken!</b>"
                     f"\n<b>From:</b> {message.from_user.first_name} (FFlow username: "
                     f"{database.Consumer.get_by_telegram_id(message.from_user.id).username})"
                     f"\nID: {message.chat.id}"
                     f"\n<b>Message:</b> \"{message.text}\"", reply_markup=markup, parse_mode='HTML')


def enter_login_password(message):
    username = message.text
    bot.send_message(message.chat.id, "Enter password")
    bot.register_next_step_handler(message, login_result, username)


def enter_email(message):
    username = message.text
    values = {'username': username}
    if not database.Consumer.is_username_already_exists(username) and re.search(r'^[a-zA-Z][a-zA-Z0-9_]*$',
                                                                                username) is not None:
        bot.send_message(message.chat.id, "Enter email")
        bot.register_next_step_handler(message, enter_registration_password, values)

    elif database.Consumer.is_username_already_exists(username):
        bot.send_message(message.chat.id, "This username is already in use")
        main_menu(message)

    elif re.search(r'^[a-zA-Z][a-zA-Z0-9_]*$', username) is None:
        bot.send_message(message.chat.id,
                         "Username must start with a letter and contain only letters, numbers, and underscores")
        main_menu(message)


def enter_registration_password(message, values):
    email = message.text
    values.update({'email': email})
    if not database.Consumer.is_email_already_exists(email) and re.search(r'^[^\s@]+@[^\s@]+\.[^\s@]+$',
                                                                          email) is not None:
        bot.send_message(message.chat.id, "Enter password")
        bot.register_next_step_handler(message, enter_confirm_password, values)

    elif database.Consumer.is_email_already_exists(email):
        bot.send_message(message.chat.id, "This email is already in use")
        main_menu(message)

    elif re.search(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email) is None:
        bot.send_message(message.chat.id, "Incorrect email")
        main_menu(message)


def enter_confirm_password(message, values):
    password = message.text
    values.update({'password': password})
    if re.search(r'^(?=.*[a-zA-Z])(?=.*\d)(?=.*[\W_]).{6,15}$', password) is not None:
        bot.send_message(message.chat.id, "Confirm password")
        bot.register_next_step_handler(message, registration_result, values)

    else:
        bot.send_message(message.chat.id,
                         "Password must be 6-15 characters long and contain at least one letter, "
                         "one digit, and one special character")
        main_menu(message)


def registration_result(message, values):
    confirm_password = message.text
    if values.get('password') == confirm_password and not database.Consumer.is_username_already_exists(
            values.get('username')):
        values.update({'telegram_id': message.from_user.id})
        database.Consumer.add_new(values)
        bot.send_message(message.chat.id,
                         f"Successful registration. Welcome "
                         f"{database.Consumer.get_by_telegram_id(message.from_user.id).username}!")
        main_menu(message)

    elif not values.get('password') == confirm_password:
        bot.send_message(message.chat.id, "Passwords are different, try again")
        main_menu(message)


def login_result(message, username):
    is_correct_username = database.Consumer.is_username_already_exists(username)
    is_correct_password = database.Consumer.verify_password(username, message.text)

    if is_correct_username and is_correct_password:
        database.Consumer.change_telegram_id(username, message.from_user.id)
        bot.send_message(message.chat.id, f"Success authorization. Welcome "
                                          f"{database.Consumer.get_by_telegram_id(message.from_user.id).username}!")
        main_menu(message)

    else:
        bot.send_message(message.chat.id, "Username or password is incorrect")
        main_menu(message)


def send_answer(message, chat_id, message_id, user_id, question_message_id):
    bot.send_message(chat_id, f'Your have got an answer: \n<b>{message.text}</b>', parse_mode='HTML',
                     reply_to_message_id=question_message_id)
    bot.reply_to(message, 'Your answer was sent')
    database.PendingUser.delete_pending(user_id)
    bot.delete_message(GROUP_ID, message_id)


def answer_message(callback):
    text_split = callback.data.split("-")
    chat_id = text_split[0]
    user_id = text_split[1]
    question_message_id = text_split[2]
    message_id = callback.message.message_id
    bot.send_message(callback.message.chat.id, "Enter your answer: ")
    bot.register_next_step_handler(callback.message, send_answer, chat_id, message_id, user_id, question_message_id)


def ignore_message(callback):
    text_split = callback.data.split("-")
    chat_id = text_split[0]
    user_id = text_split[1]
    question_message_id = text_split[2]
    message_id = callback.message.message_id
    bot.send_message(chat_id, "Unfortunately, your question was denied", reply_to_message_id=question_message_id)
    bot.delete_message(GROUP_ID, message_id)
    database.PendingUser.delete_pending(user_id)


def companies_catalog(callback):
    page = int(callback.data.split('-')[0])

    # Number of rows and data for 1 page
    company, count = database.Company.get_for_catalog(page, skip_size=1)  # skip_size - display by one element

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Return to main menu', callback_data='main menu'))

    markup.add(
        types.InlineKeyboardButton(text='Products of this company', callback_data=f"1-{company.id}-{page}-products"))

    if database.Consumer.is_admin(callback.from_user.id):
        add_btn = types.InlineKeyboardButton('Add item', callback_data='add company')
        delete_btn = types.InlineKeyboardButton('Delete item', callback_data=f'{company.id}-delete-company')

        markup.add(add_btn)
        markup.add(delete_btn)

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
    bot.send_photo(callback.message.chat.id, photo=company.image_link, caption=f'<b>{company.title}</b>\n\n'
                                                                               f'<b>Description:</b> '
                                                                               f'<i>{company.description}</i>\n',
                   parse_mode="HTML", reply_markup=markup)


def products_catalog(callback):
    text_split = callback.data.split('-')
    page = int(text_split[0])
    company_id = int(text_split[1])
    company_page = int(text_split[2])
    try:
        # Number of rows and data for 1 page
        product, count = database.Product.get_for_catalog(company_id, page, skip_size=1)

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text='Return to main menu', callback_data='main menu'))
        markup.add(types.InlineKeyboardButton(text='Bask to companies', callback_data=f"{company_page}-companies"))

        if database.Consumer.is_admin(callback.from_user.id):
            add_btn = types.InlineKeyboardButton('Add item', callback_data=f'{company_id}-add product')
            delete_btn = types.InlineKeyboardButton('Delete item', callback_data=f'{product.id}-delete-product')

            markup.add(add_btn)
            markup.add(delete_btn)

        if database.Consumer.is_authenticated(callback.from_user.id):
            add_to_basket = types.InlineKeyboardButton('Add to basket', callback_data=f'{product.id}-add-basket')
            add_to_wishlist = types.InlineKeyboardButton('Add to wishlist', callback_data=f'{product.id}-add-wish')
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
        bot.send_photo(callback.message.chat.id, photo=product.image_link, caption=f'<b>{product.title}</b>\n\n'
                                                                                   f'<b>Description:</b> '
                                                                                   f'<i>{product.description}</i>\n'
                                                                                   f'<b>Composition:</b> '
                                                                                   f'<i>{product.composition}</i>\n',
                       parse_mode="HTML", reply_markup=markup)
    except AttributeError:
        if database.Consumer.is_admin(callback.from_user.id):
            markup = types.InlineKeyboardMarkup()
            add_btn = types.InlineKeyboardButton('Add item', callback_data=f'{company_id}-add product')
            companies_btn = types.InlineKeyboardButton('Return to companies', callback_data='1-companies')
            markup.add(add_btn)
            markup.add(companies_btn)
            bot.send_message(callback.message.chat.id,
                             "The product list of this company is empty or not enough. But you can add a product",
                             reply_markup=markup)
        else:
            bot.send_message(callback.message.chat.id,
                             "The product list of this company is empty or not enough. "
                             "Wait until administrator add products")
            callback.message.from_user.id = callback.from_user.id
            main_menu(callback.message)


if __name__ == '__main__':
    """this code will catch every exception and reload the bot due 15 seconds"""
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as ex:
            bot.send_message(ADMIN_ID, f"<b>ALARM!!! ALARM!!! THE PROBLEM DETECTED!!!:</b>\n"
                                       f"{ex}", parse_mode='html')
            database.session.rollback()
            sleep(15)
