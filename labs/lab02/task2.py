"""Завдання 2 (Варіант 8): аналізатор журналу DNS-запитів."""

import csv
import logging
import math
import os
import re
import sys
from collections import Counter

DATA_DIR = os.path.join("labs", "lab02", "data", "data_v08")

# підозрілі домени верхнього рівня
SUSPICIOUS_TLDS = [
    "xyz",
    "top",
    "zip",
    "mov",
    "tk",
    "ml",
    "ga",
    "cf",
    "gq",
    "click",
    "buzz",
    "work",
]

logger = logging.getLogger("dns_analyzer")

IP_PATTERN = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
DOMAIN_PATTERN = r"^[a-z0-9_-]+(\.[a-z0-9_-]+)*\.[a-z]{2,}$"


def add_analyze_arguments(parser):
    parser.add_argument(
        "--dns-log",
        default=os.path.join(DATA_DIR, "dns_queries.csv"),
        help="CSV-файл з DNS-запитами",
    )
    parser.add_argument(
        "--blacklist",
        default=os.path.join(DATA_DIR, "blacklist.txt"),
        help="файл з чорним списком доменів",
    )
    parser.add_argument(
        "--out-csv",
        default=os.path.join(DATA_DIR, "dns_alerts.csv"),
        help="куди зберегти підозрілі запити",
    )
    parser.add_argument(
        "--min-domain-len",
        type=int,
        default=50,
        help="з якої довжини домен вважається довгим",
    )
    parser.add_argument(
        "--log-file",
        default=os.path.join(DATA_DIR, "dns_analyzer.log"),
        help="файл для логів",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="рівень логування",
    )


def read_blacklist(path):
    domains = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.split("#")[0].strip().lower()
            if line != "":
                domains.append(line)
    return domains


def read_dns_log(path):
    records = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ip = row["ClientIP"].strip()
            domain = row["Domain"].strip().lower()
            if not re.match(IP_PATTERN, ip) or not re.match(DOMAIN_PATTERN, domain):
                logger.warning(f"Пропущено некоректний рядок: {row}")
                continue
            records.append(
                {
                    "time": row["Timestamp"].strip(),
                    "ip": ip,
                    "domain": domain,
                    "type": row["QueryType"].strip().upper(),
                }
            )
    return records


# ентропія Шеннона: чим більше, тим "випадковіший" рядок
def entropy(text):
    result = 0
    for count in Counter(text).values():
        p = count / len(text)
        result -= p * math.log2(p)
    return result


def check_record(record, blacklist, min_len):
    """Повертає список знайдених проблем у вигляді (тег, опис)."""
    domain = record["domain"]
    parts = domain.split(".")
    problems = []

    # 1. чорний список (сам домен або його піддомен)
    for bad in blacklist:
        if domain == bad or domain.endswith("." + bad):
            problems.append(("BLACKMATCH", f"домен у чорному списку ({bad})"))

    # 2. DGA: довга мітка з цифрами і високою ентропією
    for part in parts[:-1]:
        if len(part) >= 12 and re.match(r"^[a-z0-9]+$", part):
            digits = sum(1 for ch in part if ch.isdigit())
            if digits / len(part) >= 0.25 and entropy(part) >= 3.0:
                problems.append(
                    (
                        "DGA-DETECT",
                        f"схоже на DGA: {part} (ентропія {entropy(part):.2f})",
                    )
                )
                break

    # 3. довгий домен або довгий піддомен
    long_domain = len(domain) >= min_len
    longest_part = max(len(p) for p in parts)

    if record["type"] == "TXT" and (long_domain or longest_part > 30):
        problems.append(("DNS-TUNNEL", "довгий TXT-запит, можливе DNS-тунелювання"))
    if long_domain:
        problems.append(("LONG-DOMAIN", f"довжина домену {len(domain)} >= {min_len}"))
    if longest_part > 30:
        problems.append(("LONG-DOMAIN", f"піддомен довжиною {longest_part} > 30"))

    # 4. підозрілий TLD
    if parts[-1] in SUSPICIOUS_TLDS:
        problems.append(("SUSPICIOUS-TLD", f"підозрілий TLD .{parts[-1]}"))

    return problems


def save_alerts(alerts, path):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["timestamp", "client_ip", "domain", "query_type", "tags", "details"]
        )
        for record, problems in alerts:
            tags = ";".join(p[0] for p in problems)
            details = "; ".join(p[1] for p in problems)
            writer.writerow(
                [
                    record["time"],
                    record["ip"],
                    record["domain"],
                    record["type"],
                    tags,
                    details,
                ]
            )


def run_analysis(args):
    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(args.log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    if args.min_domain_len <= 0:
        logger.error("--min-domain-len має бути більше 0")
        return 1

    try:
        records = read_dns_log(args.dns_log)
        blacklist = read_blacklist(args.blacklist)
    except FileNotFoundError as e:
        logger.error(f"Файл не знайдено: {e.filename}")
        return 1
    except KeyError as e:
        logger.error(f"У CSV немає колонки {e}")
        return 1

    logger.info(
        f"Прочитано {len(records)} DNS-записів, у чорному списку {len(blacklist)} доменів"
    )

    # статистика за типами запитів
    stats = Counter(r["type"] for r in records)
    print("\n=== Типи запитів ===")
    for query_type, count in stats.most_common():
        print(f"{query_type:<6} {count}")

    # пошук аномалій
    print("\n=== Підозрілі запити ===")
    alerts = []
    for record in records:
        problems = check_record(record, blacklist, args.min_domain_len)
        if problems:
            alerts.append((record, problems))
            tag = problems[0][0]  # перший тег — найважливіший
            logger.warning(
                f"[{tag}] Клієнт {record['ip']} -> {record['domain']} ({record['type']})"
            )
            for _, detail in problems:
                print("    -", detail)

    print(f"\nПідозрілих запитів: {len(alerts)} з {len(records)}")

    try:
        save_alerts(alerts, args.out_csv)
    except OSError as e:
        logger.error(f"Не вдалося записати {args.out_csv}: {e}")
        return 1

    logger.info(f"Результат збережено у {args.out_csv}")
    return 0
