"""Завдання 1: Комплексний аналізатор надійності паролів (Варіант 8)."""

import os
import random
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# ---------------------------------------------------------------------------
# 1. Персональні дані студента
# ---------------------------------------------------------------------------
try:
    from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER
except ImportError:
    STUDENT_NAME = "Невідомо"
    GROUP_NAME = "Невідомо"
    VARIANT_NUMBER = 8


# ---------------------------------------------------------------------------
# 2. Вхідні дані (Варіант 8)
# ---------------------------------------------------------------------------
passwords = [
    "ThreatH@nt3r",
    "weak123",
    "P3n3trat10n@Test",
    "visitor",
    "Cyber@Defense2023",
    "normal",
    "Incident@R3sp0nse",
    "standard",
    "Risk@Analys1s",
    "typical",
]

criteria = {
    "min_length": 10,
    "require_digits": True,
    "require_upper": True,
    "require_special": True,
}

forbidden_passwords = {"weak123", "visitor", "normal", "standard", "typical", "admin"}


# ---------------------------------------------------------------------------
# 3. Імітація повторного використання паролів
# ---------------------------------------------------------------------------
def add_duplicate_passwords(passwords_list):
    """
    Обирає 3 випадкові індекси зі списку паролів та дублює відповідні
    паролі в кінець списку (імітація повторного використання паролів).
    """
    random_indices = random.sample(range(len(passwords_list)), 3)
    duplicated = [passwords_list[i] for i in random_indices]
    passwords_list.extend(duplicated)
    return random_indices


# ---------------------------------------------------------------------------
# 4. Оцінка надійності пароля
# ---------------------------------------------------------------------------
def evaluate_password(password, criteria, forbidden_passwords, passwords_list):
    """
    Оцінює надійність одного пароля та повертає текстову оцінку:
    "Заборонений" / "Слабкий" / "Середній" / "Сильний" / "Дуже сильний".
    """
    min_length = criteria["min_length"]

    # -- Заборонений --------------------------------------------------
    if password in forbidden_passwords or len(password) < min_length:
        return "Заборонений"

    has_digit = any(ch.isdigit() for ch in password)
    has_upper = any(ch.isupper() for ch in password)
    has_lower = any(ch.islower() for ch in password)
    has_special = any(not ch.isalnum() for ch in password)

    # Критерії безпеки з варіанту (довжина + цифра/велика літера/спецсимвол,
    # залежно від того, які з них увімкнені в criteria).
    required_checks = []
    if criteria.get("require_digits"):
        required_checks.append(has_digit)
    if criteria.get("require_upper"):
        required_checks.append(has_upper)
    if criteria.get("require_special"):
        required_checks.append(has_special)

    all_criteria_met = len(password) >= min_length and all(required_checks)

    # -- Сильний / Дуже сильний ----------------------------------------
    if all_criteria_met:
        is_unique = passwords_list.count(password) == 1
        if len(password) >= min_length + 4 and is_unique:
            return "Дуже сильний"
        return "Сильний"

    # -- Середній / Слабкий ----------------------------------------------
    # Групи символів: цифра, велика літера, спецсимвол, мала літера.
    groups_satisfied = sum([has_digit, has_upper, has_special, has_lower])

    if groups_satisfied >= 2:
        return "Середній"

    return "Слабкий"


# ---------------------------------------------------------------------------
# 5. Виведення результату у табличному форматі
# ---------------------------------------------------------------------------
def print_analysis_table(passwords_list, ratings):
    """Виводить результати аналізу паролів у структурованій таблиці."""
    number_width = len(str(len(passwords_list)))
    password_width = max(len("Пароль"), max(len(p) for p in passwords_list))
    length_width = len("Довжина")
    rating_width = max(len("Оцінка"), max(len(r) for r in ratings))

    header = (
        f"{'№'.rjust(number_width)} | "
        f"{'Пароль'.ljust(password_width)} | "
        f"{'Довжина'.rjust(length_width)} | "
        f"{'Оцінка'.ljust(rating_width)}"
    )
    print(header)
    print("-" * len(header))

    for idx, (password, rating) in enumerate(zip(passwords_list, ratings), start=1):
        row = (
            f"{str(idx).rjust(number_width)} | "
            f"{password.ljust(password_width)} | "
            f"{str(len(password)).rjust(length_width)} | "
            f"{rating.ljust(rating_width)}"
        )
        print(row)


# ---------------------------------------------------------------------------
# Головна функція
# ---------------------------------------------------------------------------
def main():
    print(f"Студент: {STUDENT_NAME}")
    print(f"Група: {GROUP_NAME}")
    print(f"Варіант: {VARIANT_NUMBER}\n")

    print("Вихідний список паролів:")
    print(passwords)
    print()

    duplicated_indices = add_duplicate_passwords(passwords)
    print(f"Індекси, обрані для дублювання (імітація повторного використання): "
          f"{duplicated_indices}")
    print("Список паролів після додавання дублікатів:")
    print(passwords)
    print()

    ratings = [
        evaluate_password(password, criteria, forbidden_passwords, passwords)
        for password in passwords
    ]

    print("=== Результати аналізу надійності паролів ===")
    print_analysis_table(passwords, ratings)


if __name__ == "__main__":
    main()