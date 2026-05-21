import google.generativeai as genai
import json
import time
import os
import logging
from dotenv import load_dotenv, find_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- БРОНЕБІЙНИЙ ПОШУК .ENV ---
env_path = find_dotenv()
load_dotenv(env_path)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logging.error(f"🚨 Python так і не знайшов ключ! Шлях до .env: {env_path}")
else:
    logging.info("✅ Ключ успішно завантажено з .env!")

genai.configure(api_key=api_key)
# ------------------------------

def analyze_audio_with_gemini(audio_file_path):
    try:
        logging.info(f"Завантажую файл '{audio_file_path}' в Gemini API...")

        # 3. ФІКС MIME-ТИПУ: Примусово вказуємо, що .m4a - це аудіо, щоб Google не відхилив файл
        mime = "audio/mp4" if audio_file_path.endswith(".m4a") else None

        audio_file = genai.upload_file(path=audio_file_path, mime_type=mime)

        logging.info("Очікую, поки сервери Google завершать обробку аудіо...")
        while audio_file.state.name == "PROCESSING":
            time.sleep(2)  # Затримка 2 сек, щоб не перевантажувати API
            audio_file = genai.get_file(audio_file.name)

        if audio_file.state.name == "FAILED":
            logging.error("Google не зміг обробити цей аудіофайл.")
            return None

        logging.info("Файл успішно оброблено. Надсилаю аналітичний промпт...")
        model = genai.GenerativeModel('gemini-2.5-flash')

        prompt = """
                Ти — суворий аналітик контролю якості діалогів. Прослухай аудіозапис і проаналізуй розмову менеджера з клієнтом.

                ВАЖЛИВЕ ПРАВИЛО (ТЕХНІЧНИЙ БРАК): 
                Якщо на записі чути лише одного співрозмовника (наприклад, тільки клієнта, а голосу менеджера немає), ти НЕ МОЖЕШ оцінювати роботу. У такому разі:
                - is_ok: обов'язково false.
                - correspondence: напиши "Технічний брак".
                - усі критерії (greeting, politeness, competence, closing) СУВОРО став 0.
                - у comment напиши: "Технічний брак запису: відсутній голос менеджера, чути лише клієнта. Оцінка неможлива."

                Якщо розмова повноцінна (є обидва голоси), оціни роботу менеджера за 4 критеріями (1 - виконано, 0 - не виконано):
                1. greeting: Чи привітався менеджер коректно та назвав компанію?
                2. politeness: Чи був менеджер ввічливим протягом всієї розмови?
                3. competence: Чи чітко менеджер визначив тип робіт та відповів на питання?
                4. closing: Чи було лояльне завершення розмови?

                Також визнач загальний статус:
                - is_ok: true (успішна), false (менеджер погано відповідає, або є технічний брак).

                Сформулюй:
                - correspondence: Відповідність стандартам ("Відповідає", "Частково", "Не відповідає", або "Технічний брак").
                - work_type: Який тип робіт обговорювався.
                - manager_evaluation: Короткий аналіз роботи менеджера.
                - comment: Твій фінальний коментар із детальним поясненням помилок або браку.

                Поверни відповідь СТРОГО у форматі JSON із такими ключами:
                {
                  "is_ok": bool,
                  "correspondence": "string",
                  "work_type": "string",
                  "manager_evaluation": "string",
                  "comment": "string",
                  "greeting": int,
                  "politeness": int,
                  "competence": int,
                  "closing": int
                }
                """

        response = model.generate_content(
            [audio_file, prompt],
            generation_config={"response_mime_type": "application/json"}
        )

        logging.info(f"СИРА ВІДПОВІДЬ ШІ:\n{response.text}\n")

        try:
            genai.delete_file(audio_file.name)
        except Exception:
            pass

        return json.loads(response.text)

    except Exception as e:
        # exc_info=True виведе повний слід помилки червоним кольором!
        logging.error(f"КРИТИЧНА ПОМИЛКА: {e}", exc_info=True)
        return None