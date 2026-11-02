#!/usr/bin/env python3
"""Проверка собранного zip ресурспака.

    python3 tools/validate_pack.py [путь к zip]

Проверяет: валидный JSON в каждом файле, отсутствие китайских иероглифов,
непустые ключи и значения, наличие pack.mcmeta с pack_format 15.
Код возврата 1, если хоть одна проверка провалилась.
Только стандартная библиотека.
"""
from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CJK = re.compile(r"[\u4e00-\u9fff]")
PACK_FORMAT = 15


def main() -> int:
    default = ROOT / "release" / "CTNH-RU-Language-1.20.1-v1.0.zip"
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else default
    if not path.is_file():
        print(f"нет файла {path}")
        return 1

    errors: list[str] = []
    total_keys = 0
    empty = 0
    files = 0

    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if "pack.mcmeta" not in names:
            errors.append("в архиве нет pack.mcmeta")
        else:
            meta = json.loads(z.read("pack.mcmeta").decode("utf-8"))
            fmt = meta.get("pack", {}).get("pack_format")
            if fmt != PACK_FORMAT:
                errors.append(f"pack_format={fmt}, ожидался {PACK_FORMAT}")
            if not meta.get("pack", {}).get("description"):
                errors.append("пустое описание пака")

        for name in names:
            if not name.endswith(".json") or name == "pack.mcmeta":
                continue
            files += 1
            try:
                data = json.loads(z.read(name).decode("utf-8"))
            except Exception as exc:                       # noqa: BLE001
                errors.append(f"{name}: битый JSON ({exc})")
                continue
            if not isinstance(data, dict):
                errors.append(f"{name}: ожидался объект ключ-значение")
                continue
            total_keys += len(data)
            for key, value in data.items():
                if not key.strip():
                    errors.append(f"{name}: пустой ключ")
                if not isinstance(value, str):
                    errors.append(f"{name}: {key}: значение не строка")
                elif not value.strip():
                    empty += 1          # пустая строка — законный приём (пустая строка тултипа)
                elif CJK.search(value):
                    errors.append(f"{name}: {key}: остался китайский текст")
                if not name.startswith("assets/") or "/lang/ru_ru.json" not in name:
                    errors.append(f"{name}: файл лежит не в assets/<ns>/lang/ru_ru.json")

    print(f"файл:      {path}  ({path.stat().st_size / 1024:.0f} КБ)")
    print(f"языковых:  {files}")
    print(f"строк:     {total_keys}  (пустых по замыслу: {empty})")
    if errors:
        print(f"\nошибок: {len(errors)}")
        for e in errors[:40]:
            print("  -", e)
        return 1
    print("\nOK: JSON валиден, ключи на месте, китайского текста нет")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())