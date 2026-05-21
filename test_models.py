import os
import google.generativeai as genai
from dotenv import load_dotenv

# Завантажуємо твій ключ
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("Доступні моделі для твого ключа:")
print("-" * 30)

# Запитуємо у Google список дозволених моделей
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Помилка доступу до API: {e}")