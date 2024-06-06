import telebot
import webbrowser
import dropbox_factory

with open("../token.txt") as f:
    TOKEN = f.read().strip()

bot = telebot.TeleBot(TOKEN)


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
    bot.send_photo(message.chat.id,
                   'https://dl.dropboxusercontent.com/scl/fi/3ydxuft93439s8klnjl6g/COMPANY2.jpg?rlkey=18aqwj4v50mozjjsfrcdc0pgg&dl=0')


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, f'Hello {message.from_user.first_name}')


@bot.message_handler(commands=['help'])
def command_help(message):
    bot.send_message(message.chat.id, '<b>Help</b> <em><u>information</u></em>', parse_mode='html')


@bot.message_handler()
def info(message):
    if message.text.lower() == "hi":
        bot.send_message(message.chat.id, f'Hello {message.from_user.first_name}')
    elif message.text.lower() == "id":
        bot.reply_to(message, f'ID: {message.from_user.id}')


bot.polling(non_stop=True)
