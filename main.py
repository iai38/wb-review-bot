# main.py
import os
import logging
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# --- Парсинг отзывов Wildberries ---
def extract_nm_id(url: str) -> int:
    try:
        return int(url.split("/catalog/")[1].split("/")[0])
    except Exception:
        return None

def get_wb_reviews(nm_id: int, limit: int = 5):
    api_url = f"https://feedbacks.wb.ru/feedbacks/v1/product?nmId={nm_id}&limit={limit}&skip=0"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=5)  # добавили timeout
        response.raise_for_status()  # выбросит ошибку, если код ответа не 200
    except requests.RequestException as e:
        print(f"Ошибка запроса к WB API: {e}")
        return []

    try:
        data = response.json()
    except Exception as e:
        print(f"Ошибка парсинга JSON: {e}")
        return []

    reviews = []
    for item in data.get("feedbacks", []):
        reviews.append({
            "text": item.get("text"),
            "rating": item.get("productValuation"),
            "date": item.get("createdDate"),
            "likes": item.get("likeCount", 0),
            "dislikes": item.get("dislikeCount", 0)
        })

    return reviews

# --- Обработчики Telegram ---
@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply(
        "👋 Привет! Я бот для анализа отзывов конкурентов.\n\n"
        "Просто пришли мне ссылку на товар с Wildberries, и я покажу тебе отзывы покупателей."
    )

@dp.message_handler()
async def handle_link(message: Message):
    url = message.text.strip()

    if "wildberries.ru/catalog/" not in url:
        await message.reply("❗️Пришли, пожалуйста, корректную ссылку на товар с Wildberries.")
        return

    await message.reply("🔍 Ищу отзывы...")

    nm_id = extract_nm_id(url)
    if not nm_id:
        await message.reply("❗️Не удалось извлечь ID товара. Проверь ссылку.")
        return

    reviews = get_wb_reviews(nm_id)
    if not reviews:
        await message.reply("😔 Не удалось найти отзывы. Возможно, у товара их пока нет.")
        return

    reply_text = "📝 Вот последние отзывы:\n\n"
    for r in reviews:
        reply_text += f"⭐️ {r['rating']} | {r['date'][:10]}\n{r['text'][:200]}...\n\n"

    await message.reply(reply_text)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
