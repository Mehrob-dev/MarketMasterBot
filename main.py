import asyncio
from aiogram import Bot, Dispatcher, filters
from aiogram.types import Message
from dotenv import load_dotenv
import os
from db import engine, Users, Products, Categories, Reviews, OrderItems, Orders, CartItems, Carts
from sqlalchemy.orm import sessionmaker

load_dotenv()
my_token = os.getenv('TOKEN')

dp = Dispatcher()

Session = sessionmaker(engine)
session = Session()


@dp.message(filters.Command('start'))
async def start(message: Message):
    await message.answer('Bot is running. Database tables were created.')


async def main():
    bot = Bot(token=my_token)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
