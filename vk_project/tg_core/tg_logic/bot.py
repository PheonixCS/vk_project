import os

from asgiref.sync import async_to_sync
from dotenv import load_dotenv
from telegram import Message, Bot

load_dotenv()

TOKEN = os.getenv('TG_TOKEN')


def get_bot(bot_token=TOKEN):
    return Bot(bot_token)


def send_message(*args, **kwargs):
    bot = Bot(TOKEN)

    result: Message = async_to_sync(bot.send_message)(*args, **kwargs)

    return result


def send_photo(*args, **kwargs):
    bot = Bot(TOKEN)

    result: Message = async_to_sync(bot.send_photo)(*args, **kwargs)

    return result


def get_chat_id(chat_url):
    bot = Bot(TOKEN)

    return async_to_sync(bot.get_chat)(chat_url)

