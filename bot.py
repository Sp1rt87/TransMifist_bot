import asyncio
import logging
from io import BytesIO
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from openai import AsyncOpenAI
from pydub import AudioSegment
AudioSegment.converter = r"D:\whisper-telegram-bot\bin\ffmpeg.exe"

# Настройка логирования, чтобы видеть ошибки в консоли
logging.basicConfig(level=logging.INFO)

# === ТВОИ ДАННЫЕ (БЕЗ ЛИШНИХ ПРОБЕЛОВ И ОБЕРТОК) ===
BOT_TOKEN = "8944857956:AAEZXi21nWWej8QuXIpEnXpEuXfibROFA9k"
OPENAI_KEY = "AQ6TAHdct4Bp_fCzFwxmfPRDM12W_RJAoWFqv0jrFC3wqvXGjM59lQ55NyUv8aLhLLo5R-dHnaT3BlbkFJMfcjWMWLX8dhAtW6m_wems-fwd4KKdn4p0XuY5Jsy56DNBM-XQnh3W2jMfwleLZ4Y867QrUoMA"

# Инициализация бота и клиента OpenAI
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
client = AsyncOpenAI(api_key=OPENAI_KEY)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("👋 Привет! Пришли мне голосовое сообщение или аудиофайл (WAV, MP3), и я переведу его на русский язык.")


@dp.message(F.voice | F.audio | F.document)
async def handle_audio(message: types.Message):
    status_msg = await message.answer("🎙️ Обрабатываю аудио, подождите...")

    try:
        # 1. Определяем, откуда брать file_id (голос, аудио или документ)
        if message.voice:
            file_id = message.voice.file_id
        elif message.audio:
            file_id = message.audio.file_id
        elif message.document and (message.document.file_name.endswith('.wav') or message.document.file_name.endswith('.mp3')):
            file_id = message.document.file_id
        else:
            await status_msg.edit_text("❌ Пожалуйста, отправь именно аудиофайл (wav, mp3) или голосовое сообщение.")
            return

        # 2. Скачиваем файл в оперативную память
        file = await bot.get_file(file_id)
        file_bytes = await bot.download_file(file.file_path)

        # 3. Конвертируем в mp3 через pydub
        audio = AudioSegment.from_file(BytesIO(file_bytes.getvalue()))
        mp3_io = BytesIO()
        audio.export(mp3_io, format="mp3")
        mp3_io.seek(0)

        # 4. Отправляем в OpenAI Whisper
        response = await client.audio.transcriptions.create(
            model="whisper-1",
            file=("audio.mp3", mp3_io, "audio/mpeg"),
            prompt="Translate this audio to Russian language, please."
        )

        # 5. Отправляем результат пользователю
        if response.text.strip():
            await status_msg.edit_text(f"📝 **Перевод:**\n\n{response.text}")
        else:
            await status_msg.edit_text("🤷‍♂️ В аудиозаписи не удалось распознать речь.")

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await status_msg.edit_text("❌ Произошла ошибка. Проверь баланс OpenAI ключа или формат аудио.")


async def main():
    logging.info("Бот запущен и готов к работе...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")
