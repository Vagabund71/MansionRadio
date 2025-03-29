import telebot
import time
import requests
from flask import Flask, Response, jsonify
import os
from dotenv import load_dotenv
import threading
import random
import logging

# Настройка логирования для диагностики
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')
if not API_TOKEN:
    raise ValueError("Токен не найден в переменных окружения!")

bot = telebot.TeleBot(API_TOKEN)

app = Flask(__name__)
app.static_folder = 'static'

YANDEX_LINKS = [
    "https://getfile.dokpub.com/yandex/get/https://disk.yandex.ru/d/NoB7Q_cDuTHMWA",
    "https://getfile.dokpub.com/yandex/get/https://disk.yandex.ru/d/ZOwdB8zLx8UxkA",
    "https://getfile.dokpub.com/yandex/get/https://disk.yandex.ru/d/lCuYYmx2saV_sA",
    "https://getfile.dokpub.com/yandex/get/https://disk.yandex.ru/d/mUpzfeT9ybNvYA",
    "https://getfile.dokpub.com/yandex/get/https://disk.yandex.ru/d/quSS2HtPakaiBA",
    "https://getfile.dokpub.com/yandex/get/https://disk.yandex.ru/d/J793obwVEjgSXQ",
    "https://getfile.dokpub.com/yandex/get/https://disk.yandex.ru/d/TLdysYagdkD_EA",
    "https://getfile.dokpub.com/yandex/get/https://disk.yandex.ru/d/XT78X2RIuB8dHA",
    "https://getfile.dokpub.com/yandex/get/https://disk.yandex.ru/d/KGmfwWqVQ5gMrg",
    "https://getfile.dokpub.com/yandex/get/https://disk.yandex.ru/d/iRCiGtRnFXWjvw",
    "https://getfile.dokpub.com/yandex/get/https://disk.yandex.ru/d/UWxsiE-_Dl6DgA",
    "https://getfile.dokpub.com/yandex/get/https://disk.yandex.ru/d/v4D9MaO4LRCvXA",
    "https://getfile.dokpub.com/yandex/get/https://disk.yandex.ru/d/0RR9gqIx68CHLw",
    "https://getfile.dokpub.com/yandex/get/https://disk.yandex.ru/d/KFCc6UnLIjlKuw",
    "https://getfile.dokpub.com/yandex/get/https://disk.yandex.ru/d/h3xjuQJz408R3A",
    "https://getfile.dokpub.com/yandex/get/https://disk.yandex.ru/d/7kXxPa2r8x_WfQ",
    "https://getfile.dokpub.com/yandex/get/https://disk.yandex.ru/d/B-mB4AVpAPhhtg",
    "https://getfile.dokpub.com/yandex/get/https://disk.yandex.ru/d/7MrnIM_6numWwA",
    "https://getfile.dokpub.com/yandex/get/https://disk.yandex.ru/d/4uXBQsnqYdyEOg",
    "https://getfile.dokpub.com/yandex/get/https://disk.yandex.ru/d/Trk3M_Rugfeg6A",
    "https://getfile.dokpub.com/yandex/get/https://disk.yandex.ru/d/Hf_OQYIkxrWNlw"
]

# Устанавливаем случайный начальный индекс при запуске
current_song_index = random.randint(0, len(YANDEX_LINKS) - 1)
current_song_start_time = time.time()

@app.route('/')
def serve_index():
    return app.send_static_file('index.html')

@app.route('/current_song')
def get_current_song():
    global current_song_index, current_song_start_time
    elapsed_time = time.time() - current_song_start_time
    return jsonify({
        'song_url': YANDEX_LINKS[current_song_index],
        'elapsed_time': elapsed_time
    })

@app.route('/stream')
def stream_audio():
    def generate():
        global current_song_index, current_song_start_time
        if not YANDEX_LINKS:
            logger.error("Список YANDEX_LINKS пуст, стриминг невозможен.")
            return
        while True:
            yandex_link = YANDEX_LINKS[current_song_index]
            logger.info(f"Начало стриминга: {yandex_link}")
            try:
                response = requests.get(yandex_link, stream=True)
                response.raw.decode_content = True
                for data in response.iter_content(chunk_size=4096):
                    if data:
                        yield data
                logger.info(f"Конец стриминга: {yandex_link}")
            except Exception as e:
                logger.error(f"Ошибка стриминга {yandex_link}: {e}")
            current_song_index = (current_song_index + 1) % len(YANDEX_LINKS)
            current_song_start_time = time.time()
            time.sleep(0.05)
    return Response(generate(), mimetype='audio/mpeg')

def send_radio_button(chat_id):
    keyboard = telebot.types.InlineKeyboardMarkup()
    web_app_button = telebot.types.InlineKeyboardButton(
        text="▶️ Запустить радио",
        web_app=telebot.types.WebAppInfo(url="https://mansionradio.onrender.com")
    )
    keyboard.add(web_app_button)
    bot.send_message(
        chat_id,
        "🎧 Добро пожаловать в наше DJ-радио!\n\n"
        "Нажми кнопку ниже, чтобы запустить радио.",
        reply_markup=keyboard
    )

@bot.message_handler(commands=['start'])
def handle_start(message):
    logger.info(f"Команда /start от {message.from_user.id}")
    send_radio_button(message.chat.id)

@bot.message_handler(content_types=['text', 'photo', 'video', 'audio', 'document', 'sticker'])
def handle_all_messages(message):
    logger.info(f"Сообщение от {message.from_user.id}: {message.text if message.text else 'не текст'}")
    send_radio_button(message.chat.id)

def run_bot():
    logger.info("Запуск Telegram-бота...")
    bot.infinity_polling(skip_pending=True)

if __name__ == '__main__':
    logger.info("Приложение запускается...")
    # Запускаем Telegram-бот в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask-сервер
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)