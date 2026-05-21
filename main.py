import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

from core.google_services import get_unprocessed_audio, download_file, upload_transcript, append_to_sheet, move_file
from core.ai_services import analyze_audio_with_gemini

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SOURCE_FOLDER = os.getenv("SOURCE_DRIVE_FOLDER_ID")
WORK_FOLDER = os.getenv("WORK_DRIVE_FOLDER_ID")
SHEET_ID = os.getenv("SPREADSHEET_ID")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Привіт! Я бот для аналізу дзвінків. Натисни /process щоб почати обробку файлів.")


@dp.message(Command("process"))
async def process_handler(message: types.Message):
    await message.answer("Починаю пошук файлів на Google Drive...")

    files = get_unprocessed_audio(SOURCE_FOLDER)
    if not files:
        await message.answer("Аудіофайлів не знайдено.")
        return

    await message.answer(f"Знайдено файлів: {len(files)}. Починаю обробку...")

    for file in files:
        file_id = file['id']
        file_name = file['name']

        msg = await message.answer(f"⏳ Завантажую {file_name}...")

        try:
            # 1. Скачуємо локально
            local_path = download_file(file_id, file_name)

            await msg.edit_text(f"🧠 Аналізую {file_name} через AI...")

            # 2. Транскрибуємо та аналізуємо
            ai_data = analyze_audio_with_gemini(local_path)

            if not ai_data:
                await msg.edit_text(f"❌ Помилка аналізу {file_name}")
                continue

            # --- РАХУЄМО БАЛИ ТУТ ---
            # Використовуємо .get(), щоб код не падав, якщо ШІ пропустить якесь поле
            total_score = 1 if ai_data.get('is_ok') else 0

            # 3. Завантажуємо транскрипт на Drive
            transcript_text = ai_data.get('comment', 'Транскрибація відсутня')
            upload_transcript(transcript_text, file_name, WORK_FOLDER)
            move_file(file_id, WORK_FOLDER)

            # 4. Записуємо в таблицю
            # Переконайся, що всередині append_to_sheet ти теж рахуєш total_score або передаєш його туди
            append_to_sheet(SHEET_ID, file_name, ai_data, total_score)

            # Визначаємо статус для повідомлення (використовуємо .get() для безпеки)
            status_emoji = "✅" if ai_data.get('is_ok') else "🛑"

            # Виводимо пораховану суму total_score замість ai_data['score_sum']
            await msg.edit_text(f"{status_emoji} Успішно оброблено: {file_name}\nОцінка: {total_score} бал.")

            # Видаляємо локальний файл після обробки
            if os.path.exists(local_path):
                os.remove(local_path)

        except Exception as e:
            await msg.edit_text(f"❌ Помилка під час обробки {file_name}: {str(e)}")
async def main():
    print("Бот запущено!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())