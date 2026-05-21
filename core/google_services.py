import os
import io
import gspread
from datetime import datetime
from gspread_formatting import CellFormat, Color, format_cell_range
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

# Дозволи для роботи з Диском та Таблицями
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]


def get_authenticated_services():
    """Безкоштовна авторизація через OAuth 2.0 (використовує твої безкоштовні 15 ГБ)"""
    creds = None
    # Файл token.json створиться сам після першого логіну
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Використовує файл, який ми скачали на Кроці 1
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    drive_service = build('drive', 'v3', credentials=creds)
    gc = gspread.authorize(creds)
    return drive_service, gc


# Ініціалізуємо безкоштовні сервіси
drive_service, gc = get_authenticated_services()


def get_unprocessed_audio(folder_id):
    query = f"'{folder_id}' in parents and trashed = false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    return results.get('files', [])


def download_file(file_id, file_name):
    """Скачує файл локально у папку data/"""
    os.makedirs('data', exist_ok=True)
    file_path = os.path.join('data', file_name)
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.FileIO(file_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    return file_path


def move_file(file_id, target_folder_id):
    """Переносить оригінальне аудіо в робочу папку"""
    file = drive_service.files().get(fileId=file_id, fields='parents').execute()
    previous_parents = ",".join(file.get('parents', []))

    drive_service.files().update(
        fileId=file_id,
        addParents=target_folder_id,
        removeParents=previous_parents,
        fields='id, parents'
    ).execute()


def upload_transcript(text, original_name, folder_id):
    """СТВОРЮЄ .TXT ФАЙЛ ПОРЯД В ПАПЦІ (Тепер це працює безкоштовно!)"""
    base_name = os.path.splitext(original_name)[0]
    file_path = os.path.join('data', f"{base_name}.txt")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)

    file_metadata = {'name': f"{base_name}.txt", 'parents': [folder_id]}
    media = MediaFileUpload(file_path, mimetype='text/plain')
    drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()


def append_to_sheet(spreadsheet_id, file_name, data: dict, total_score: int):
    """Додає рядок у таблицю і фарбує коментар у червоний, якщо розмова не ОК"""
    sheet = gc.open_by_key(spreadsheet_id).sheet1
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    row = [
        current_date,  # A: Дата
        file_name,  # B: Назва файлу
        data.get("correspondence", ""),  # C: Відповідність стандартам
        "Так",  # D: Чи є запис
        data.get("work_type", ""),  # E: Тип робіт
        data.get("manager_evaluation", ""),  # F: Оцінка менеджера
        data.get("comment", ""),  # G: КРИТИЧНИЙ КОМЕНТАР
        data.get("greeting", 0),  # H: 1 або 0
        data.get("politeness", 0),  # I: 1 або 0
        data.get("competence", 0),  # J: 1 або 0
        data.get("closing", 0),  # K: 1 або 0
        total_score  # L: Сума балів
    ]

    sheet.append_row(row)

    # Якщо дзвінок НЕ ОК, фарбуємо клітинку з коментарем (стовпчик G) у червоний колір
    if not data.get("is_ok", True):
        last_row_index = len(sheet.get_all_values())
        fmt = CellFormat(backgroundColor=Color(1, 0.8, 0.8))
        format_cell_range(sheet, f"G{last_row_index}", fmt)