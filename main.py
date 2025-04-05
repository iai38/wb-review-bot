# main.py

import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import CommandStart
import asyncpg
from dotenv import load_dotenv

load_dotenv()

# Config
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- DB Init ---
async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            product_url TEXT,
            created_at TIMESTAMP DEFAULT now()
        );
    ''')
    await conn.close()


# --- Handlers ---
@dp.message(CommandStart())
async def handle_start(message: Message):
    await message.answer("Привет! Отправь мне ссылку на товар с Wildberries, и я проанализирую отзывы 🕵️")

@dp.message()
async def handle_link(message: Message):
    url = message.text.strip()
    if "wildberries.ru" not in url:
        await message.answer("Пожалуйста, отправь корректную ссылку на товар с Wildberries.")
        return

    # Сохраняем в БД
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute(
        "INSERT INTO requests (user_id, product_url) VALUES ($1, $2)",
        message.from_user.id,
        url
    )
    await conn.close()

    await message.answer("Спасибо! Я получил ссылку. Начинаю анализ... 🔍 (анализ пока в разработке)")

# --- Main ---
async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
