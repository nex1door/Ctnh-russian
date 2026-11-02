#!/usr/bin/env python3
"""Сборка релизного zip ресурспака из исходников в assets/.

    python3 tools/build_pack.py [--version v1.0] [--out release/CTNH-RU-Language-1.20.1-v1.0.zip]

Сборка детерминированная: записи в архиве сортируются, дата фиксирована,
поэтому повторный запуск без изменений даёт побайтно тот же файл.
Только стандартная библиотека.
"""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXED_DATE = (2026, 1, 1, 0, 0, 0)          # (year, month, day, hour, min, sec)
EXTRA = ("pack.mcmeta", "pack.png", "README.md", "LICENSE")


def collect(version: str) -> list[tuple[str, bytes]]:
    """Пути внутри архива (posix, от корня) и их содержимое."""
    entries: list[tuple[str, bytes]] = []

    meta_path = ROOT / "pack.mcmeta"
    if not meta_path.is_file():
        sys.exit("нет pack.mcmeta в корне репозитория")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["pack"]["description"] = f"Русская локализация Create: New Horizon (CTNH) {version}"
    entries.append(("pack.mcmeta", json.dumps(meta, ensure_ascii=False, indent=2).encode()))

    for name in EXTRA[1:]:
        p = ROOT / name
        if p.is_file():
            entries.append((name, p.read_bytes()))

    assets = ROOT / "assets"
    if not assets.is_dir():
        sys.exit("нет папки assets/")
    for p in sorted(assets.rglob("ru_ru.json")):
        rel = p.relative_to(ROOT).as_posix()
        json.loads(p.read_text(encoding="utf-8"))      # падаем сразу, если файл битый
        entries.append((rel, p.read_bytes()))
    return entries


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="v1.0")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    out = Path(args.out) if args.out else ROOT / "release" / f"CTNH-RU-Language-1.20.1-{args.version}.zip"
    out.parent.mkdir(parents=True, exist_ok=True)

    entries = collect(args.version)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in entries:
            info = zipfile.ZipInfo(name, date_time=FIXED_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, data)

    langs = [n for n, _ in entries if n.endswith("ru_ru.json")]
    print(f"собрано: {out}")
    print(f"файлов: {len(entries)} (языковых: {len(langs)}), размер: {out.stat().st_size / 1024:.0f} КБ")


if __name__ == "__main__":
    main()