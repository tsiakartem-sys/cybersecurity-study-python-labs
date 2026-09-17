"""Завдання 3: Безпечне хешування, CSV-база та JSON-логування з винятками.

Варіант 8: алгоритм хешування sha256, мінімальна довжина пароля — 11.
Персональні дані (номер варіанту) імпортуються з shared/student.py.
"""

import csv
import hashlib
import json
import os
from datetime import datetime
from functools import wraps

# ---------------------------------------------------------------------------
# ВАРІАНТ (підставити власні значення)
# ---------------------------------------------------------------------------
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from shared.student import VARIANT_NUMBER
except ImportError:
    VARIANT_NUMBER = 8  # Варіант 8

PERSONAL_SALT = str(VARIANT_NUMBER).zfill(5)  # "00008" для варіанту 8
HASH_ALGORITHM = "sha256"                     # Варіант 8: sha256
MIN_PASSWORD_LENGTH = 11                      # Варіант 8: мінімальна довжина 11

DATA_DIR = os.path.join("labs", "lab01", "data")
USERS_CSV_PATH = os.path.join(DATA_DIR, "users.csv")
LOG_JSON_PATH = os.path.join(DATA_DIR, "log.json")


# ---------------------------------------------------------------------------
# Власні винятки
# ---------------------------------------------------------------------------
class ValidationError(Exception):
    """Викликається, коли пароль не проходить власну валідацію (напр. довжина)."""
    pass


# ---------------------------------------------------------------------------
# 1. Хешування
# ---------------------------------------------------------------------------
def generate_hash(password: str, salt: str = "00000") -> str:
    """
    Повертає шістнадцятковий хеш конкатенації пароля та солі.

    :raises ValueError: якщо password або salt порожні / None.
    :raises ValidationError: якщо password коротший за MIN_PASSWORD_LENGTH.
    """
    if password is None or password == "" or salt is None or salt == "":
        raise ValueError("Пароль та сіль не можуть бути порожніми (None або '').")

    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"Пароль занадто короткий: мінімальна довжина — {MIN_PASSWORD_LENGTH} символів."
        )

    raw = f"{password}{salt}".encode("utf-8")
    hasher = hashlib.new(HASH_ALGORITHM)
    hasher.update(raw)
    return hasher.hexdigest()


# ---------------------------------------------------------------------------
# 3. Реєстрація користувачів
# ---------------------------------------------------------------------------
users_to_register = (
    ("artem", "Passw0rd!2024"),
    ("olena", "Secure123!Pass"),
    ("dmytro", "Qwerty99!Strong"),
    ("iryna", "P@ssword1234"),
    ("bohdan", "HunterX2Secure"),
    ("kateryna", "SunnyDay7!Pass"),
    ("taras", "Kh4rkiv!!Strong"),
    ("nadiya", "Nadiya2024Pass"),
    ("orest", "Or3st$ecure123"),
    ("solomiya", "Sol0miya!Pass1"),
)


def create_user(username: str, password: str) -> tuple:
    """Створює запис (username, hash_value), використовуючи персональну сіль."""
    hash_value = generate_hash(password, PERSONAL_SALT)
    return username, hash_value


def create_users(users_list) -> None:
    """
    Обробляє список (username, password), формує хеші та записує їх
    у файл users.csv у форматі: логін,хеш_пароля.
    Папка data створюється автоматично, якщо її немає.
    """
    try:
        os.makedirs(DATA_DIR, exist_ok=True)

        rows = []
        for username, password in users_list:
            try:
                rows.append(create_user(username, password))
            except (ValueError, ValidationError) as e:
                print(f"[Пропущено] Користувач '{username}': {e}")

        with open(USERS_CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        print(f"Записано {len(rows)} користувача(ів) у {USERS_CSV_PATH}")

    except PermissionError as e:
        print(f"Помилка доступу під час запису CSV: {e}")
    except IOError as e:
        print(f"Помилка вводу/виводу під час запису CSV: {e}")


# ---------------------------------------------------------------------------
# 4. Читання бази даних
# ---------------------------------------------------------------------------
def read_users_db() -> list:
    """Зчитує users.csv у список [(login, hash), ...] та повертає його."""
    users_db = []
    try:
        with open(USERS_CSV_PATH, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) == 2:
                    users_db.append((row[0], row[1]))
    except FileNotFoundError as e:
        print(f"Файл бази даних не знайдено: {e}")
    except PermissionError as e:
        print(f"Немає доступу до файлу бази даних: {e}")
    except IOError as e:
        print(f"Помилка вводу/виводу під час читання CSV: {e}")

    return users_db


def print_users_table(users_db: list) -> None:
    """Виводить users_db у вигляді структурованої таблиці."""
    if not users_db:
        print("База користувачів порожня.")
        return

    login_width = max(len("Логін"), max(len(u) for u, _ in users_db))
    hash_width = max(len("Хеш пароля"), max(len(h) for _, h in users_db))

    header = f"{'Логін'.ljust(login_width)} | {'Хеш пароля'.ljust(hash_width)}"
    print(header)
    print("-" * len(header))
    for login, hash_value in users_db:
        print(f"{login.ljust(login_width)} | {hash_value.ljust(hash_width)}")


# ---------------------------------------------------------------------------
# 6. Декоратор логування подій
# ---------------------------------------------------------------------------
def log_event(func):
    """
    Декоратор, що записує кожну спробу входу у log.json у форматі:
    {"event": "login", "user": ..., "result": "success"/"failure",
     "timestamp": "...", "args": [...], "kwargs": {...}}
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        username = args[0] if args else kwargs.get("username", "")
        # Для логу беремо лише логін/пароль (username, password), не службові
        # параметри на кшталт users_db, щоб log.json лишався компактним.
        loggable_args = args[:2]
        loggable_kwargs = {k: v for k, v in kwargs.items() if k in ("username", "password")}

        result = "failure"
        try:
            success = func(*args, **kwargs)
            result = "success" if success else "failure"
            return success
        except (ValueError, ValidationError):
            result = "failure"
            raise
        finally:
            entry = {
                "event": "login",
                "user": username,
                "result": result,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "args": [str(a) for a in loggable_args],
                "kwargs": {k: str(v) for k, v in loggable_kwargs.items()},
            }
            _append_log_entry(entry)

    return wrapper


def _append_log_entry(entry: dict) -> None:
    """Дописує один запис у JSON-масив у файлі log.json."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)

        logs = []
        if os.path.exists(LOG_JSON_PATH):
            try:
                with open(LOG_JSON_PATH, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        logs = json.loads(content)
            except (json.JSONDecodeError, IOError):
                logs = []

        logs.append(entry)

        with open(LOG_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

    except PermissionError as e:
        print(f"Помилка доступу під час запису у log.json: {e}")
    except IOError as e:
        print(f"Помилка вводу/виводу під час запису у log.json: {e}")


# ---------------------------------------------------------------------------
# 5. Автентифікація
# ---------------------------------------------------------------------------
@log_event
def login(username: str, password: str) -> bool:
    """
    Перевіряє, чи існує користувач у users_db та чи збігається хеш
    введеного пароля (з урахуванням персональної солі) зі збереженим.

    :raises ValueError: якщо username або password порожні.
    """
    if username is None or username == "" or password is None or password == "":
        raise ValueError("Логін та пароль не можуть бути порожніми.")

    users_db = read_users_db()

    try:
        entered_hash = generate_hash(password, PERSONAL_SALT)
    except ValidationError:
        # Пароль занадто короткий -> точно не пройде автентифікацію
        return False

    for stored_login, stored_hash in users_db:
        if stored_login == username:
            return stored_hash == entered_hash

    return False


# ---------------------------------------------------------------------------
# 8. Головна функція
# ---------------------------------------------------------------------------
def main():
    print(f"Персональна сіль: {PERSONAL_SALT}")
    print(f"Алгоритм хешування: {HASH_ALGORITHM}")
    print(f"Мінімальна довжина пароля: {MIN_PASSWORD_LENGTH}\n")

    # 1) Реєстрація користувачів і запис у CSV
    print("=== Реєстрація користувачів ===")
    create_users(users_to_register)

    # 2) Зчитування бази та виведення таблиці
    print("\n=== База користувачів (users.csv) ===")
    users_db = read_users_db()
    print_users_table(users_db)

    # 3) Демонстрація автентифікації (успішна та неуспішна спроби)
    print("\n=== Автентифікація ===")
    test_attempts = [
        ("artem", "Passw0rd!2024"),  # правильний пароль
        ("artem", "wrongpassword"),  # неправильний пароль
        ("no_such_user", "abc12345678"),  # неіснуючий користувач
        ("", ""),                    # порожні дані -> ValueError
    ]

    for username, password in test_attempts:
        try:
            success = login(username, password)
            status = "успішно" if success else "невдало"
            print(f"Спроба входу '{username}': {status}")
        except ValueError as e:
            print(f"Спроба входу '{username}': помилка вводу — {e}")
        except ValidationError as e:
            print(f"Спроба входу '{username}': помилка валідації — {e}")

    print(f"\nЛог подій записано у файл: {LOG_JSON_PATH}")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(f"Файл не знайдено: {e}")
    except PermissionError as e:
        print(f"Немає прав доступу: {e}")
    except IOError as e:
        print(f"Помилка вводу/виводу: {e}")
    except ValidationError as e:
        print(f"Помилка валідації: {e}")
    except ValueError as e:
        print(f"Помилка значення: {e}")