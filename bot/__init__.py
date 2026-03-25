# Copyright @Am_itachiuchiha
#  𝗫𝗣 𝗧𝗢𝗢𝗟𝗦™ - Telegram Utility Bot for Smart Features Bot 
#  Copyright (C) 2024-present 𝗫𝗣 𝗧𝗢𝗢𝗟𝗦™ <https://github.com/XPTOOLS> 
import asyncio
import logging

# Fix for Python 3.14 asyncio issue
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from config import BOT_TOKEN, API_ID, API_HASH, SESSION_STRING
from bot.helpers.logger import LOGGER
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from pyrogram import Client

logging.basicConfig(level=logging.INFO)

LOGGER.info("Creating Bot Client From BOT_TOKEN")
SmartAIO = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
SmartPyro = Client(
    name="𝗫𝗣 𝗧𝗢𝗢𝗟𝗦™",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=1000
)
LOGGER.info("Creating User Client From SESSION_STRING")
SmartUserBot = Client(
    "SmartUser",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
    workers=1000
)
LOGGER.info("User Client Created Successfully !")
LOGGER.info("Bot Client Created Successfully!")

__all__ = ["SmartAIO", "dp", "SmartPyro", "SmartUserBot"]
