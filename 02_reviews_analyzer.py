# Installing the necessary library -- Установка библиотеки (обязательно для Colab)
!pip install -q -U google-genai

import json
import gspread
import os
from google import genai
from google.colab import auth
from google.auth import default

# Libraries and authentication tools -- Инструменты и авторизация
auth.authenticate_user()
creds, _ = default()
gc = gspread.authorize(creds)

# Security: Replace these with your actual data for local testing -- Настройки доступа
API_KEY = "YOUR_API_KEY"
SPREADSHEET_URL = "YOUR_SPREADSHEET_URL"

# Loading source data from reviews.txt -- Загрузка отзывов из файла
if not os.path.exists("reviews.txt"):
    print("❌ Error: reviews.txt not found. Please upload it to Colab.")
else:
    with open("reviews.txt", "r", encoding="utf-8") as file:
        all_reviews = file.read()

    # Processing reviews with Gemini AI -- Анализ отзывов через нейросеть
    client = genai.Client(api_key=API_KEY)
    
    # Prompt engineering: requesting strict JSON -- Промпт с требованием чистого JSON
    my_prompt = f"""
    Ты - аналитик службы поддержки. Твоя задача - разобрать отзывы клиентов.
    Для каждого отзыва определи тональность, категорию и напиши ответ (reply).
    Результат выдай СТРОГО в формате JSON. Без лишнего текста.

    Отзывы для анализа:
    {all_reviews}
    """

    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=my_prompt
    )

    # Saving AI response for further processing -- Сохранение ответа для дальнейшей работы
    if response.text:
        with open("analysis_results.txt", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("✅ AI Analysis saved to analysis_results.txt")

        # Exporting formatted data to the sheet -- Перенос данных в таблицу
        try:
            sh = gc.open_by_url(SPREADSHEET_URL)
            worksheet = sh.get_worksheet(0)

            # Clean Markdown formatting and parse JSON -- Очистка и разбор JSON
            clean_content = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_content)
            
            # Identify the correct key in JSON -- Поиск ключа с данными
            key = 'reviews_analysis' if 'reviews_analysis' in data else list(data.keys())[0]
            
            rows_to_insert = []
            for review in data[key]:
                rows_to_insert.append([
                    review.get('id', ''),
                    review.get('sentiment', ''),
                    review.get('category', ''),
                    review.get('reply', '')
                ])

            # Bulk export to Google Sheets -- Массовая загрузка в таблицу
            worksheet.append_rows(rows_to_insert)
            print(f"✅ Success! Data is now in Google Sheets.")

        except json.JSONDecodeError:
            print("❌ Error: AI returned invalid JSON. Try running it again.")
        except Exception as e:
            print(f"❌ Error during export: {e}")
