import telebot
import time
import requests
from flask import Flask, Response, jsonify
import os
from dotenv import load_dotenv
import threading
import random
import logging

# Настройка логирования с выводом в stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])
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

current_song_index = random.randint(0, len(YANDEX_LINKS) - 1)
current_song_start_time = time.time()

@app.route('/')
def serve_index():
    logger.info("Запрос главной страницы")
    return app.send_static_file('index.html')

@app.route('/current_song')
def get_current_song():
    global current_song_index, current_song_start_time
    elapsed_time = time.time() - current_song_start_time
    logger.info(f"Текущая песня: {YANDEX_LINKS[current_song_index]}, прошло времени: {elapsed_time}")
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
                with requests.get(yandex_link, stream=True, timeout=15) as response:
                    response.raise_for_status()
                    response.raw.decode_content = True
                    chunk_count = 0
                    for data in response.iter_content(chunk_size=8192):
                        if data:
                            chunk_count += 1
                            yield data
                            if chunk_count % 10 == 0:  # Логируем каждые 10 чанков
                                logger.info(f"Отправлено {chunk_count} чанков для {yandex_link}")
                        else:
                            logger.warning(f"Получены пустые данные для {yandex_link}")
                    logger.info(f"Конец стриминга: {yandex_link}, отправлено {chunk_count} чанков")
            except requests.RequestException as e:
                logger.error(f"Ошибка стриминга {yandex_link}: {e}")
                time.sleep(2)
            except Exception as e:
                logger.error(f"Неизвестная ошибка в стриминге {yandex_link}: {e}")
                break
            current_song_index = (current_song_index + 1) % len(YANDEX_LINKS)
            current_song_start_time = time.time()
            time.sleep(0.5)
    logger.info("Начало потока /stream")
    return Response(generate(), mimetype='audio/mpeg', headers={'Cache-Control': 'no-cache'})

def send_radio_button(chat_id):
    keyboard = telebot.types.InlineKeyboardMarkup()
    web_app_button = telebot.types.InlineKeyboardButton(
        text="▶️ Запустить радио",
        web_app=telebot.types.WebAppInfo(url="https://mansionradio.onrender.com")
    )
    keyboard.add(web_app_button)
    try:
        bot.send_message(
            chat_id,
            "🎧 Добро пожаловать в наше DJ-радио!\n\n"
            "Нажми кнопку ниже, чтобы запустить радио.",
            reply_markup=keyboard
        )
        logger.info(f"Сообщение с кнопкой отправлено в чат {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения в чат {chat_id}: {e}")

@bot.message_handler(commands=['start'])
def handle_start(message):
    logger.info(f"Команда /start от {message.from_user.id}")
    send_radio_button(message.chat.id)

@bot.message_handler(content_types=['text', 'photo', 'video', 'audio', 'document', 'sticker'])
def handle_all_messages(message):
    logger.info(f"Сообщение от {message.from_user.id}: {message.text if message.text else 'не текст'}")
    send_radio_button(message.chat.id)

def run_bot():
    while True:
        try:
            logger.info("Запуск Telegram-бота...")
            bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=50)
        except Exception as e:
            logger.error(f"Ошибка в polling: {e}")
            time.sleep(5)

# Пинг для поддержания активности сервиса
@app.route('/ping')
def ping():
    logger.info("Получен запрос /ping")
    return "Pong", 200

logger.info("Инициализация приложения и запуск бота...")
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()

if __name__ == '__main__':
    logger.info("Локальный запуск приложения...")
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)