"""Завдання 2: Багаторівнева система контролю доступу (Варіант 8)."""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from shared.student import VARIANT_NUMBER
except ImportError:
    VARIANT_NUMBER = 8


# Вхідні дані (Варіант 8)
users = {
    "crypto_specialist": {
        "role": "cryptographer",
        "clearance": 4,
        "department": "Cryptography",
        "active": True,
    },
    "privacy_officer": {
        "role": "privacy_analyst",
        "clearance": 3,
        "department": "Privacy",
        "active": True,
    },
    "data_scientist": {
        "role": "data_analyst",
        "clearance": 2,
        "department": "Analytics",
        "active": True,
    },
    "field_engineer": {
        "role": "field_support",
        "clearance": 2,
        "department": "Field Ops",
        "active": True,
    },
    "test_account": {
        "role": "testing",
        "clearance": 1,
        "department": "QA",
        "active": False,
    },
}

resources = [
    ("encryption_keys", 4),
    ("privacy_policies", 3),
    ("anonymized_data", 2),
    ("field_reports", 2),
    ("crypto_algorithms", 4),
    ("consent_forms", 1),
    ("data_classification", 3),
    ("key_management", 4),
    ("statistical_models", 2),
    ("public_datasets", 1),
]

security_levels = ("Unclassified", "For Official Use", "Confidential", "Secret")

blocked_users = {"test_account", "gdpr_violation", "data_breach_user"}


# 2. Список ресурсів із текстовою назвою рівня безпеки
def print_resources(resources_list, levels):
    """Виводить перелік ресурсів, замінюючи числовий рівень на текстовий."""
    print("=== Список ресурсів системи ===")
    for name, level in resources_list:
        level_name = levels[level - 1]
        print(f"{name} -> рівень безпеки: {level_name} ({level})")
    print()


# 3. Алгоритм перевірки доступу
def check_access(username, resource_name, resource_level, users_dict, blocked):
    """
    Повертає кортеж (allowed: bool, reason: str | None) для пари
    (користувач, ресурс) відповідно до алгоритму розмежування доступу.
    """
    if username not in users_dict:
        return False, "User not found"

    if username in blocked:
        return False, "User is blocked"

    user_info = users_dict[username]

    if not user_info["active"]:
        return False, "Account inactive"

    if user_info["clearance"] >= resource_level:
        return True, None

    return False, "Insufficient clearance"


# 4. Виведення результатів перевірки
def run_access_checks(usernames, resources_list, users_dict, blocked):
    """
    Перевіряє доступ кожного логіна з usernames до кожного ресурсу.

    Вивід групується по користувачах: для кожного логіна спершу друкується
    заголовок з його роллю/рівнем допуску (якщо він є в системі), потім
    результат по кожному ресурсу, а наприкінці — короткий підсумок
    ALLOW/DENY по цьому користувачу.
    """
    print("=== Результати перевірки доступу ===\n")

    for username in usernames:
        user_info = users_dict.get(username)
        if user_info is not None:
            header = (
                f"--- {username} "
                f"(role={user_info['role']}, clearance={user_info['clearance']}, "
                f"active={user_info['active']}) ---"
            )
        else:
            header = f"--- {username} (немає в системі users) ---"
        print(header)

        allow_count = 0
        deny_count = 0

        for resource_name, resource_level in resources_list:
            allowed, reason = check_access(
                username, resource_name, resource_level, users_dict, blocked
            )
            if allowed:
                status = "ALLOW"
                allow_count += 1
            else:
                status = f"DENY ({reason})"
                deny_count += 1
            print(f"  user={username} resource={resource_name} -> {status}")

        print(f"  Підсумок: ALLOW={allow_count}, DENY={deny_count}\n")


def main():
    print(f"Варіант: {VARIANT_NUMBER}\n")

    print_resources(resources, security_levels)

    # Перевіряємо всіх зареєстрованих користувачів (усі 5 зі словника users),
    # а також:
    #  - unknown_user       -> демонструє причину "User not found";
    #  - gdpr_violation,
    #    data_breach_user   -> ці логіни є в blocked_users, але їх НЕМАЄ
    #                          у users, тож алгоритм (перевірка "not found"
    #                          виконується першою) все одно поверне
    #                          "User not found", а не "User is blocked".
    usernames_to_check = list(users.keys()) + [
        "unknown_user",
        "gdpr_violation",
        "data_breach_user",
    ]

    run_access_checks(usernames_to_check, resources, users, blocked_users)


if __name__ == "__main__":
    main()