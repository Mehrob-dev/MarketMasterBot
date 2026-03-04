import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from user import user_router
from admin import admin_router

load_dotenv()
TOKEN = os.getenv('TOKEN')

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    dp.include_router(admin_router)
    dp.include_router(user_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
