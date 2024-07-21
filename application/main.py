import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from application.config import TG_TOKEN
from application.dropbox_factory import register_dropbox_factory
from application.handlers.callback_handler import register_callback_handlers
from application.handlers.command_handler import register_command_handler
from application.handlers.input_handler import register_input_handler

API_TOKEN = TG_TOKEN


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    register_command_handler(dp)
    register_input_handler(dp)
    register_callback_handlers(dp)
    register_dropbox_factory(dp)

    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
