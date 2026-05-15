import asyncio
import logging
from io import BytesIO
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from openai import AsyncOpenAI
from pydub import AudioSegment

logging.basicConfig(level=logging.INFO)

# === Настройки из переменных окружения ===
bot = Bot(token=os.getenv("8944857956: AAEZXi21nWWej8QuXIpEnXpEuXfibROFA9k"))
dp = Dispatcher()
client = AsyncOpenAI(api_key=os.getenv(AQ6TAHdct4Bp_fCzFwxmfPRDM12W_RJAoWFqv0jrFC3wqvXGjM59lQ55NyUv8aLhLLo5R -
                     dHnaT3BlbkFJMfcjWMWLX8dhAtW6m_wems-fwd4KKdn4p0XuY5Jsy56DNBM-XQnh3W2jMfwleLZ4Y867QrUoMA))
# =========================================


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("👋 Кидай голосовые или аудио — переведу на русский!")


@dp.message(lambda m: m.voice or m.audio)
async def handle_audio(message: types.Message):
    await message.answer("🎙️ Обрабатываю...")

    try:
        # Получаем файл
        file_id = message.voice.file_id if message.voice else message.audio.file_id
        file = await bot.get_file(file_id)
        file_bytes = await bot.download_file(file.file_path)

        # Конвертируем в mp3
        audio = AudioSegment.from_file(BytesIO(file_bytes.getvalue()))
        mp3_io = BytesIO()
        audio.export(mp3_io, format="mp3")
        mp3_io.seek(0)

        # Транскрипция и перевод
        transcription = await client.audio.transcriptions.create(
            model="whisper-1",
            file=("audio.mp3", mp3_io, "audio/mpeg")
        )

        translation = await client.audio.translations.create(
            model="whisper-1",
            file=("audio.mp3", mp3_io, "audio/mpeg")
        )

        result = f"""🎤 **Оригинал:**\n{transcription.text}\n\n🇷🇺 **Перевод на русский:**\n{translation.text}"""

        await message.answer(result, parse_mode="Markdown")

    except Exception as e:
        logging.error(e)
        await message.answer("❌ Ошибка при обработке аудио. Попробуй ещё раз.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
