"""Завдання 1: класи User, Admin, Session, AuditLog та UserAccount."""

import hashlib
import os
import re
from datetime import datetime, timedelta

SESSION_TIMEOUT = 900  # 15 хвилин

# шаблон для перевірки email
EMAIL_PATTERN = (
    r"^[A-Za-z][A-Za-z0-9_]{2,63}@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$"
)


class User:
    def __init__(self, username, email, password, role="user", active=True):
        self.username = username
        self.email = email  # тут спрацює сеттер з перевіркою
        self.role = role
        self.active = active
        self.__salt = os.urandom(16)
        self.__password_hash = self.__make_hash(password)

    # приватний метод для хешування пароля
    def __make_hash(self, password):
        return hashlib.sha256(self.__salt + password.encode()).hexdigest()

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        if not re.match(EMAIL_PATTERN, value):
            raise ValueError(f"Некоректний email: {value}")
        self._email = value

    def check_password(self, password):
        return self.__make_hash(password) == self.__password_hash

    def deactivate(self):
        self.active = False

    def __str__(self):
        if self.active:
            status = "активний"
        else:
            status = "деактивований"
        return f"Користувач {self.username} <{self.email}>, роль: {self.role}, {status}"


class Admin(User):
    def __init__(self, username, email, password, permissions=None):
        super().__init__(username, email, password, role="admin")
        if permissions is None:
            permissions = []
        self.permissions = set(permissions)

    def grant_permission(self, permission):
        self.permissions.add(permission)

    def revoke_permission(self, permission):
        if permission in self.permissions:
            self.permissions.remove(permission)

    def has_permission(self, permission):
        return permission in self.permissions

    def __str__(self):
        return super().__str__() + ", дозволи: " + ", ".join(sorted(self.permissions))


class Session:
    def __init__(self, ip):
        self.ip = ip
        self.login_time = datetime.now().astimezone()
        self.last_activity = datetime.now().astimezone()

    def touch(self):
        self.last_activity = datetime.now().astimezone()

    def is_active(self, timeout_sec):
        passed = datetime.now().astimezone() - self.last_activity
        return passed.total_seconds() < timeout_sec

    def __str__(self):
        return f"Сеанс з {self.ip}, вхід о {self.login_time:%H:%M:%S}"


class AuditLog:
    def __init__(self):
        self.records = []

    def add_log(self, username, action):
        time = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
        self.records.append(f"{time} | {username} | {action}")

    def show_all(self):
        if len(self.records) == 0:
            print("Журнал порожній")
        for record in self.records:
            print(record)


class UserAccount:
    def __init__(self, user, audit_log):
        self.user = user
        self.audit_log = audit_log
        self.session = None

    def login(self, username, password, ip):
        if (
            username == self.user.username
            and self.user.active
            and self.user.check_password(password)
        ):
            self.session = Session(ip)
            self.audit_log.add_log(username, "login_success")
            return True
        self.audit_log.add_log(username, "login_failure")
        return False

    def is_authenticated(self):
        if self.session is None:
            return False
        if self.session.is_active(SESSION_TIMEOUT):
            return True
        # сеанс прострочений
        self.session = None
        self.audit_log.add_log(self.user.username, "session_timeout")
        return False

    def logout(self):
        if self.session is None:
            return False
        self.session = None
        self.audit_log.add_log(self.user.username, "logout")
        return True

    # доступ через account["email"], account["role"] і т.д.
    def __getitem__(self, key):
        if key == "email":
            return self.user.email
        if key == "role":
            return self.user.role
        if key == "session":
            return self.session
        if key == "user":
            return self.user
        raise KeyError(key)

    def __setitem__(self, key, value):
        if key == "email":
            self.user.email = value
        elif key == "role":
            self.user.role = value
        elif key == "session":
            if not isinstance(value, Session):
                raise TypeError("session має бути об'єктом Session")
            self.session = value
        else:
            raise KeyError(key)

    def __str__(self):
        if self.session:
            return f"Акаунт {self.user.username} (в системі)"
        return f"Акаунт {self.user.username} (не в системі)"


def run_demo():
    audit = AuditLog()

    print("\n--- Створення користувачів ---")
    user = User("artem", "artem_ts@example.com", "S3cure!Passw0rd")
    admin = Admin(
        "root_admin",
        "admin@security.example.org",
        "Adm1n!Strong#Key",
        ["read_logs", "manage_users"],
    )
    print(user)
    print(admin)

    account = UserAccount(user, audit)
    admin_account = UserAccount(admin, audit)

    print("\n--- Вхід у систему ---")
    print("Неправильний пароль:", account.login("artem", "wrong-pass", "192.168.1.10"))
    print(
        "Неіснуючий користувач:",
        account.login("hacker", "S3cure!Passw0rd", "10.0.0.66"),
    )
    print(
        "Правильний пароль:", account.login("artem", "S3cure!Passw0rd", "192.168.1.10")
    )
    print("Автентифікований:", account.is_authenticated())
    print(account.session)

    print("\n--- Зміна email ---")
    for new_email in [
        "artem.new@example.com",
        "1bad@example.com",
        "artem_new@mail.example.com",
    ]:
        try:
            account["email"] = new_email
            print("Email змінено на", account["email"])
        except ValueError as e:
            print("Помилка:", e)

    print("\n--- Доступ через [] ---")
    print("account['role'] =", account["role"])
    try:
        print(account["password"])
    except KeyError:
        print("Ключ 'password' недоступний")
    try:
        account["session"] = "abc"
    except TypeError as e:
        print("Помилка:", e)

    print("\n--- Адміністратор ---")
    print(
        "Вхід адміна:",
        admin_account.login("root_admin", "Adm1n!Strong#Key", "10.0.0.1"),
    )
    admin.grant_permission("edit_firewall")
    print("Має edit_firewall:", admin.has_permission("edit_firewall"))
    admin.revoke_permission("manage_users")
    print("Має manage_users:", admin.has_permission("manage_users"))
    print(admin)

    print("\n--- Таймаут сеансу ---")
    # щоб не чекати 15 хвилин, зсуваємо час останньої активності назад
    account.session.last_activity -= timedelta(seconds=SESSION_TIMEOUT + 1)
    print("Автентифікований:", account.is_authenticated())
    print(account)

    print("\n--- Вихід ---")
    print("Вихід адміна:", admin_account.logout())
    print("Повторний вихід:", admin_account.logout())

    print("\n--- Деактивований користувач ---")
    user.deactivate()
    print(user)
    print("Вхід:", account.login("artem", "S3cure!Passw0rd", "192.168.1.10"))

    print("\n--- Журнал аудиту ---")
    audit.show_all()
