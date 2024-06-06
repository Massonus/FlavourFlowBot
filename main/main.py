import telebot
import webbrowser
import dropbox_factory
from config import GROUP_ID, TG_TOKEN

from telebot import types

bot = telebot.TeleBot(TG_TOKEN)


@bot.message_handler(commands=['site', 'website'])
def redirect(message):
    webbrowser.open_new_tab('http://flavourflow.eu-central-1.elasticbeanstalk.com')


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


@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    if callback.data == 'delete':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
    elif callback.data == 'edit':
        bot.edit_message_caption('Edit', callback.message.chat.id, callback.message.message_id)


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Go to our site')
    markup.row(btn1)
    btn2 = types.KeyboardButton('Delete')
    btn3 = types.KeyboardButton('Edit')
    markup.row(btn2, btn3)
    bot.send_message(message.chat.id, f'Hello {message.from_user.first_name}', reply_markup=markup)
    bot.register_next_step_handler(message, on_click)


def on_click(message):
    if message.text == 'Go to our site':
        bot.send_message(message.chat.id, 'Website is open')
    elif message.text == 'Delete':
        bot.send_message(message.chat.id, 'Deleted')


@bot.message_handler(commands=['help'])
def command_help(message):
    bot.send_message(message.chat.id, message.chat.id)
    # bot.send_message(message.from_user.id, message.chat.id)
    bot.send_message(message.chat.id, 'Enter your question')
    bot.register_next_step_handler(message, next_step)


def next_step(message):
    bot.reply_to(message, "Your question was sent")
    bot.send_message(GROUP_ID,
                     f"User {message.from_user.id} sent a question: '{message.text}'. Enter <code>/answer "
                     f"{message.from_user.id} 'answer'</code> to answer", parse_mode='HTML')


@bot.message_handler()
def info(message):
    if message.text.lower() == "hi":
        bot.send_message(message.chat.id, f'Hello {message.from_user.first_name}')
    elif message.text.lower() == "id":
        bot.reply_to(message, f'ID: {message.from_user.id}')
    elif "/answer" in message.text:
        text_split = message.text.split(" ")
        user_id = text_split[1]
        text = ' '.join(text_split[2:])
        bot.send_message(user_id, f'Your have got an answer {text}')
        bot.reply_to(message, 'Your answer was sent')


bot.polling(non_stop=True)
