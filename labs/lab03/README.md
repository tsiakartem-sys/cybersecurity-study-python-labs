# Лабораторна робота №3 — Прикладні бібліотеки Python для побудови вебзастосунків

**Студент:** Цяк Артем Андрійович, група КБ-205
**Варіант 8:** Облік часу відновлення сервісів

## Предметна область

Web API для обліку навчальних вимірювань часу відновлення сервісів після збою.

| Поле | Значення |
|---|---|
| `categories` | сервіс: `database`, `web_service`, `file_storage` |
| `code` | унікальний код вимірювання, наприклад `V08-01` |
| `title` | назва вимірювання, наприклад `Вимірювання відновлення 01` |
| `value` | час відновлення у хвилинах (`minutes`), `float`, не менше 0, без `inf`/`NaN` |
| `status` | стан перевірки: `new`, `in_progress`, `done` |
| Поріг | **60.0 хв**: записи, що досягли порога, — `GET /records?min_value=60` |

Дані навчальні й не описують реальну інфраструктуру.

## Структура

```
labs/lab03/
├── main.py          # FastAPI-застосунок, lifespan, /ping, /student, обробники помилок
├── database.py      # з'єднання (PRAGMA foreign_keys = ON) та виконання schema.sql
├── schema.sql       # готова схема для варіантів 7–9
├── repository.py    # параметризовані SQL-запити, транзакції
├── schemas.py       # Pydantic-моделі запитів і відповідей
├── config.py        # одиниця вимірювання, поріг, межі value
├── seed.py          # початкове заповнення з data/seed.json
├── routers/
│   ├── __init__.py  # перетворення помилок шару даних на 404/409
│   ├── categories.py
│   └── records.py
└── data/
    ├── seed.json    # 3 категорії та 8 записів варіанта 8
    └── lab3.sqlite3 # створюється програмою, у Git не додається
```

## Встановлення та запуск

Усі команди виконуються з кореня репозиторію:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows (PowerShell)
# source .venv/bin/activate         # Linux / macOS
python -m pip install -r requirements.txt

python -m labs.lab03.database       # створити таблиці (необов'язково: це робить і seed, і API)
python -m labs.lab03.seed           # заповнити порожню базу початковими даними
uvicorn labs.lab03.main:app --reload --host 127.0.0.1 --port 8000
```

- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI-схема: http://127.0.0.1:8000/openapi.json

Повторний запуск `seed` не змінює непорожню базу. Щоб почати з чистої бази,
видаліть `labs/lab03/data/lab3.sqlite3` і знову запустіть `seed`.

## Маршрути

| Метод і маршрут | Успіх | Помилки |
|---|---|---|
| `GET /ping` | 200 | — |
| `GET /student` | 200 | — |
| `GET /categories` | 200 | — |
| `POST /categories` | 201 | 409, 422 |
| `DELETE /categories/{category_id}` | 204 | 404, 409, 422 |
| `GET /records` | 200 | 422 |
| `GET /records/{record_id}` | 200 | 404, 422 |
| `POST /records` | 201 | 404, 409, 422 |
| `PUT /records/{record_id}` | 200 | 404, 409, 422 |
| `DELETE /records/{record_id}` | 204 | 404, 422 |
| `POST /records/bulk` | 201 | 404, 409, 422 |

Параметри `GET /records`: `category_id` (> 0), `status`, `min_value` (≥ 0),
`q` (1–120 символів, буквальний підрядок у `title` з урахуванням регістру),
`limit` (1–100, типово 20), `offset` (≥ 0, типово 0). Фільтри об'єднуються
через `AND`, результат відсортовано за `id`.

## Приклади запитів (Bash)

```bash
curl -i "http://127.0.0.1:8000/ping"
curl -i "http://127.0.0.1:8000/student"
curl -i "http://127.0.0.1:8000/records?category_id=1&status=new&limit=5&offset=0"
curl -i "http://127.0.0.1:8000/records?min_value=60"

curl -i -X POST "http://127.0.0.1:8000/records" \
  -H "Content-Type: application/json" \
  -d '{"code":"V08-TEST","title":"Тестове вимірювання","category_id":1,"value":42.5,"status":"new"}'

curl -i -X PUT "http://127.0.0.1:8000/records/9" \
  -H "Content-Type: application/json" \
  -d '{"code":"V08-TEST","title":"Тестове вимірювання (оновлено)","category_id":3,"value":61.0,"status":"done"}'

curl -i -X DELETE "http://127.0.0.1:8000/records/9"

# Скасування пакета: V08-01 вже є в базі -> 409, V08-ROLLBACK не збережено
curl -i -X POST "http://127.0.0.1:8000/records/bulk" \
  -H "Content-Type: application/json" \
  -d '[{"code":"V08-ROLLBACK","title":"Перший елемент","category_id":1,"value":4.0,"status":"new"},{"code":"V08-01","title":"Дублікат коду","category_id":2,"value":5.0,"status":"new"}]'

# Спроба SQL-ін'єкції обробляється як звичайний текст -> 200, []
curl -i -G "http://127.0.0.1:8000/records" --data-urlencode "q=' OR 1=1 --"
```

У Windows ті самі запити зручно виконувати через Swagger UI: `curl` у консолі
Windows може передати кирилицю в тілі запиту не в UTF-8.

## Перевірка стилю

```bash
ruff check labs/lab03
ruff format --check labs/lab03
ruff check .
ruff format --check .
```
