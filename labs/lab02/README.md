# Лабораторна робота №2 — Розробка консольних утиліт для задач кібербезпеки

**Студент:** Цяк Артем Андрійович, група КБ-205
**Варіант 8:** Фільтр та аналізатор журналів DNS-запитів

## Встановлення

Усі команди виконуються з кореня репозиторію в активованому віртуальному середовищі з ЛР №1:

```powershell
.venv\Scripts\Activate.ps1          # Windows (PowerShell)
# source .venv/bin/activate         # Linux / macOS
pip install -r requirements.txt
```

Сторонніх залежностей, крім `ruff`, немає. Використовується лише стандартна бібліотека Python 3.10+.

## Структура

```
labs/lab02/
├── __init__.py
├── main.py          # точка входу: команди demo та analyze
├── task1.py         # Завдання 1: User, Admin, Session, AuditLog, UserAccount
├── task2.py         # Завдання 2: аналізатор DNS-журналу (варіант 8)
├── README.md
└── data/
    └── data_v08/            # каталог варіанта з архіву lab2_data.zip
        ├── dns_queries.csv  # вхід: журнал DNS-транзакцій
        ├── blacklist.txt    # вхід: локальний чорний список доменів
        ├── dns_alerts.csv   # вихід: знайдені аномальні запити (створюється утилітою)
        └── dns_analyzer.log # вихід: журнал роботи утиліти (створюється утилітою)
```

### Вхідні файли

`data/data_v08/dns_queries.csv`: CSV із заголовком `Timestamp,ClientIP,Domain,QueryType`.

```csv
Timestamp,ClientIP,Domain,QueryType
2026-09-27T08:00:01,10.0.0.10,intranet.example.com,A
2026-09-27T08:03:00,10.0.0.20,bad-domain.example.invalid,A
```

`data/data_v08/blacklist.txt` містить по одному домену на рядок. Порожні рядки й коментарі після `#` пропускаються.
Збіг рахується і для самого домену, і для його піддоменів (`x.bad-domain.example.invalid` теж збігається).

## Запуск

### Завдання 1: демонстрація ООП

```powershell
python -m labs.lab02.main demo
```

Демонстрація показує успішний і невдалий вхід, зміну email із валідацією, доступ через `account["..."]`,
права адміністратора, завершення сеансу за таймаутом, вихід із системи та вміст `AuditLog`.

### Завдання 2: аналіз DNS-журналу

```powershell
# з типовими шляхами (data/data_v08/...)
python -m labs.lab02.main analyze

# з явними параметрами
python -m labs.lab02.main analyze `
    --dns-log labs/lab02/data/data_v08/dns_queries.csv `
    --blacklist labs/lab02/data/data_v08/blacklist.txt `
    --out-csv labs/lab02/data/data_v08/dns_alerts.csv `
    --min-domain-len 50

# довідка
python -m labs.lab02.main analyze --help
```

### Параметри CLI команди `analyze`

| Параметр | Типове значення | Опис |
|---|---|---|
| `--dns-log` | `labs/lab02/data/data_v08/dns_queries.csv` | CSV-журнал DNS-запитів |
| `--blacklist` | `labs/lab02/data/data_v08/blacklist.txt` | файл чорного списку доменів |
| `--out-csv` | `labs/lab02/data/data_v08/dns_alerts.csv` | куди записати підозрілі запити |
| `--min-domain-len` | `50` | з якої довжини домен вважається аномально довгим |
| `--log-file` | `labs/lab02/data/data_v08/dns_analyzer.log` | файл журналу роботи утиліти |
| `--log-level` | `INFO` | рівень логування: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

## Правила виявлення аномалій

| Тег | Умова |
|---|---|
| `BLACKMATCH` | домен або його батьківський домен є в чорному списку |
| `DGA-DETECT` | мітка з ≥ 12 символів `[a-z0-9]`, цифр ≥ 25 %, ентропія Шеннона ≥ 3.0 |
| `DNS-TUNNEL` | запит типу `TXT` до довгого домену або домену з піддоменом > 30 символів |
| `LONG-DOMAIN` | довжина домену ≥ `--min-domain-len` або піддомен довший за 30 символів |
| `SUSPICIOUS-TLD` | TLD зі списку `.xyz .top .zip .mov .tk .ml .ga .cf .gq .click .buzz .work` |

Один запит може мати кілька тегів. У консолі показується перший (найважливіший) тег і всі пояснення,
у CSV (`timestamp,client_ip,domain,query_type,tags,details`) записуються всі теги через `;`.
Статистика типів запитів рахується через `collections.Counter`.

## Поведінка при помилках

| Ситуація | Результат |
|---|---|
| вхідний файл не існує, у CSV немає потрібної колонки, `--min-domain-len` ≤ 0 | `[ERROR] ...`, код **1** |
| рядок CSV з некоректною IP-адресою або доменом | `[WARNING] Пропущено некоректний рядок`, аналіз триває |
| не вдалося записати `--out-csv` | `[ERROR] ...`, код **1** |
| усе гаразд | звіт у консолі, CSV і лог-файл, код **0** |

## Перевірка коду

```powershell
ruff check labs/lab02
ruff format --check labs/lab02
```
