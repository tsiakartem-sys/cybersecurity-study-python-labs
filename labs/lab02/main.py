"""Лабораторна робота №2: точка входу.

Запуск з кореня репозиторію:
    python -m labs.lab02.main demo
    python -m labs.lab02.main analyze [параметри]
"""

import argparse
import sys

from labs.lab02 import task1, task2
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m labs.lab02.main",
        description="ЛР №2: ООП-модель облікових записів та аналізатор DNS-журналів (Варіант 8).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="КОМАНДА")

    subparsers.add_parser("demo", help="демонстрація класів Завдання 1")

    analyze_parser = subparsers.add_parser(
        "analyze", help="аналіз журналу DNS-запитів (Завдання 2)"
    )
    task2.add_analyze_arguments(analyze_parser)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(f"Студент: {STUDENT_NAME}, група {GROUP_NAME}, варіант {VARIANT_NUMBER}")

    if args.command == "demo":
        task1.run_demo()
        return 0
    return task2.run_analysis(args)


if __name__ == "__main__":
    sys.exit(main())
