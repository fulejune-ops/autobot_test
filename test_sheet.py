import os
from core.google_services import append_to_sheet

# Встав свій ID між лапками
SHEET_ID = "17EYbIp3wBcgmx7i-aQ_ze9TUCUbQZ9o1LOWOEloAIYM"

# --- РОЗУМНА ПЕРЕВІРКА ID ---
clean_id = SHEET_ID.strip()
if "http" in clean_id or "google.com" in clean_id:
    print("\n❌ ПОМИЛКА: Ти вставив повне посилання!")
    print("ID — це тільки набір букв і цифр між /d/ та /edit")
    exit()
elif len(clean_id) != 44:
    print(f"\n⚠️ УВАГА: Стандартний ID Google Таблиці має 44 символи, а твій має {len(clean_id)}.")
    print(f"Твій поточний ID: '{clean_id}'")
    print("Перевір, чи ти скопіював його повністю і без пробілів!\n")
# -----------------------------

# 1. Фейкові дані для успішного дзвінка
good_call = {
    "is_ok": True,
    "correspondence": "Відповідає",
    "work_type": "Планове ТО",
    "manager_evaluation": "Менеджер чітко дотримався всіх етапів скрипта.",
    "comment": "Клієнт записаний на завтра. Зауважень немає.",
    "greeting": 1,
    "politeness": 1,
    "competence": 1,
    "closing": 1
}

print("🚀 Запуск тесту таблиці...")

# 2. Фейкові дані для поганого дзвінка (або технічного браку)
bad_call = {
    "is_ok": False,
    "correspondence": "Не відповідає",
    "work_type": "Ремонт ходової",
    "manager_evaluation": "Відсутнє привітання та завершення розмови.",
    "comment": "Технічний брак запису: відсутній голос менеджера.",
    "greeting": 0,
    "politeness": 0,
    "competence": 1,
    "closing": 0
}

print("🚀 Запуск тесту таблиці...")

print("1. Відправляю успішний дзвінок (Оцінка: 1)...")
append_to_sheet(SHEET_ID, "test_good_voice.m4a", good_call, total_score=1)

print("2. Відправляю проблемний дзвінок (Оцінка: 0, має пофарбувати коментар)...")
append_to_sheet(SHEET_ID, "test_bad_voice.m4a", bad_call, total_score=0)

print("✅ Тест завершено! Відкривай таблицю в браузері та перевіряй стовпчики.")