import json
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database_factory import Database
from config import TG_TOKEN

database = Database()

bot = telebot.TeleBot(TG_TOKEN)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    req = call.data.split('_')

    if req[0] == 'unseen':
        bot.delete_message(call.message.chat.id, call.message.message_id)
    elif 'pagination' in req[0]:
        json_string = json.loads(req[0])
        page = json_string['NumberPage']

        sql_transaction = database.data_list_for_page(tables='product', order='title', page=page,
                                                      skip_size=1)  # SkipSize - display by one element
        data = sql_transaction[0][0]
        count = sql_transaction[2]

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text='Hide', callback_data='unseen'))
        if page == 1:
            markup.add(InlineKeyboardButton(text=f'{page}/{count}', callback_data=f' '),
                       InlineKeyboardButton(text=f'Forward --->',
                                            callback_data="{\"method\":\"pagination\",\"NumberPage\":" + str(
                                                page + 1) + ",\"CountPage\":" + str(count) + "}"))
        elif page == count:
            markup.add(InlineKeyboardButton(text=f'<--- Back',
                                            callback_data="{\"method\":\"pagination\",\"NumberPage\":" + str(
                                                page - 1) + ",\"CountPage\":" + str(count) + "}"),
                       InlineKeyboardButton(text=f'{page}/{count}', callback_data=f' '))
        else:
            markup.add(InlineKeyboardButton(text=f'<--- Back',
                                            callback_data="{\"method\":\"pagination\",\"NumberPage\":" + str(
                                                page - 1) + ",\"CountPage\":" + str(count) + "}"),
                       InlineKeyboardButton(text=f'{page}/{count}', callback_data=f' '),
                       InlineKeyboardButton(text=f'Forward --->',
                                            callback_data="{\"method\":\"pagination\",\"NumberPage\":" + str(
                                                page + 1) + ",\"CountPage\":" + str(count) + "}"))
        bot.edit_message_text(f'<b>{data[3]}</b>\n\n'
                              f'<b>Title:</b> <i>{data[4]}</i>\n'
                              f'<b>Email:</b><i>{data[5]}</i>\n'
                              f'<b>Site:</b><i> {data[6]}</i>',
                              parse_mode="HTML", reply_markup=markup, chat_id=call.message.chat.id,
                              message_id=call.message.message_id)


@bot.message_handler(content_types=['text'])
def start(m):
    page = 1
    sql_transaction = database.data_list_for_page(tables='product', order='title', page=page,
                                                  skip_size=1)  # SkipSize - display by one element
    data = sql_transaction[0][0]  # Rows data
    count = sql_transaction[2]  # Number of rows
    print()
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text='Hide', callback_data='unseen'))
    markup.add(InlineKeyboardButton(text=f'{page}/{count}', callback_data=f' '),
               InlineKeyboardButton(text=f'Forward --->',
                                    callback_data="{\"method\":\"pagination\",\"NumberPage\":" + str(
                                        page + 1) + ",\"CountPage\":" + str(count) + "}"))

    bot.send_message(m.from_user.id, f'<b>{data[3]}</b>\n\n'
                                     f'<b>Title:</b> <i>{data[4]}</i>\n'
                                     f'<b>Email:</b><i>{data[5]}</i>\n'
                                     f'<b>Site:</b><i> {data[6]}</i>',
                     parse_mode="HTML", reply_markup=markup)


if __name__ == '__main__':
    bot.polling(none_stop=True)
