from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import (Message)

import application.database_owm as database
from application.handlers.input_handler import main_menu

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    if message.chat.type != 'private':
        await message.answer(f"I don't work in groups {message.chat.id}")
        return

    if database.Consumer.is_authenticated(message.from_user.id):
        consumer = database.Consumer.get_by_telegram_id(message.from_user.id)
        await message.answer(f"Welcome. You are authorized as {consumer.username}!")
    else:
        await message.answer("Welcome. You are not authorized! You can do it below")

    await main_menu(message, message.from_user.id)


@router.message(Command('menu'))
async def start(message: Message):
    if message.chat.type != 'private':
        await message.answer("I don't work in groups")
        return
    await main_menu(message, message.from_user.id)


@router.message(Command('logout'))
async def command_help(message: Message):
    if message.chat.type != 'private':
        await message.answer("I don't work in groups")
        return

    try:
        username = database.Consumer.get_by_telegram_id(message.from_user.id).username
        await database.Consumer.change_telegram_id(username, 0)
        await message.answer("Successfully logout")
        await main_menu(message, message.from_user.id)
    except AttributeError:
        await message.answer("You are not authorized!")
        await main_menu(message, message.from_user.id)


def register_command_handler(dp):
    dp.include_router(router)
