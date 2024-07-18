import asyncio
import logging
import traceback

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import database_owm as database
from config import ADMIN_ID, ADMIN2_ID, TG_TOKEN
from main_directory.handlers.command_handler import register_command_handlers
from run1 import register_run1_handlers
from main_directory.handlers.callback_handler import register_callback_handlers
from dropbox_factory import register_dropbox_factory

API_TOKEN = TG_TOKEN


async def send_alarm(bot: Bot, admin_id: int, message: str):
    try:
        await bot.send_message(admin_id, message, parse_mode='html')
    except Exception as e:
        print(f"Failed to send message to {admin_id}: {e}")


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    while True:
        try:
            register_command_handlers(dp)
            register_run1_handlers(dp)
            register_callback_handlers(dp)
            register_dropbox_factory(dp)

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
