from aiogram import Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher

storage = MemoryStorage()

bot = Bot(token=('5640561409:AAFPuWXIIJNpTVkyoQengsR01fLkqhpQtKo'))
dp = Dispatcher(bot, storage=storage)
