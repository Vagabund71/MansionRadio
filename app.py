import telebot
import time
import requests
from flask import Flask, Response
import os
from dotenv import load_dotenv
import threading
import random

load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')
if not API_TOKEN:
    raise ValueError("Токен не найден в переменных окружения!")

bot = telebot.TeleBot(API_TOKEN)

app = Flask(__name__)
app.static_folder = '.'

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

@app.route('/')
def serve_index():
    return app.send_static_file('index.html')

@app.route('/stream')
def stream_audio():
    def generate():
        if not YANDEX_LINKS:
            print("Список YANDEX_LINKS пуст, стриминг невозможен.")
            return
        
        start_index = random.randint(0, len(YANDEX_LINKS) - 1)
        print(f"Случайный стартовый индекс: {start_index}")
        
        while True:
            for i in range(start_index, len(YANDEX_LINKS)):
                yandex_link = YANDEX_LINKS[i]
                start_time = time.time()
                print(f"Начало стриминга: {yandex_link} в {time.strftime('%H:%M:%S')}")
                try:
                    response = requests.get(yandex_link, stream=True)
                    response.raw.decode_content = True
                    while True:
                        data = response.raw.read(4096)
                        if not data:
                            break
                        yield data
                    end_time = time.time()
                    print(f"Конец стриминга: {yandex_link}, время перехода: {(end_time - start_time):.2f} сек")
                except Exception as e:
                    print(f"Ошибка стриминга {yandex_link}: {e}")
                    continue
                time.sleep(0.05)
            start_index = 0
    return Response(generate(), mimetype='audio/mpeg')

def send_radio_button(chat_id):
    """Отправляет сообщение с кнопкой Web App."""
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
    """Обрабатывает команду /start."""
    print(f"Команда /start от {message.from_user.id}")
    send_radio_button(message.chat.id)

@bot.message_handler(content_types=['text', 'photo', 'video', 'audio', 'document', 'sticker'])
def handle_all_messages(message):
    """Обрабатывает любые сообщения и отправляет кнопку."""
    print(f"Сообщение от {message.from_user.id}: {message.text if message.text else 'не текст'}")
    send_radio_button(message.chat.id)

if __name__ == '__main__':
    print("Приложение запускается...")
    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)