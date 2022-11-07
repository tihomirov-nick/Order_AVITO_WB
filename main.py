from aiogram import types
from aiogram.utils import executor

import client
import users
from create_bot import dp


async def on_startup(dp):
    print('Bot online...')
    users.sql_start()
    await dp.bot.set_my_commands([types.BotCommand("start", "Запустить бота"), types.BotCommand("admin", "Панель администратора")])


client.register_handlers_client(dp)
executor.start_polling(dp, skip_updates=True, on_startup=on_startup)