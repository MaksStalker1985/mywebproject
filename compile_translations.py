"""Компилирует locale/*/LC_MESSAGES/django.po в .mo без GNU gettext.

На Windows `manage.py compilemessages` требует установленного gettext (msgfmt).
Этот скрипт делает то же самое на чистом Python через библиотеку polib:

    python compile_translations.py
"""
from pathlib import Path

import polib

BASE_DIR = Path(__file__).resolve().parent

for po_path in sorted((BASE_DIR / "locale").glob("*/LC_MESSAGES/*.po")):
    po = polib.pofile(str(po_path))
    po.save_as_mofile(str(po_path.with_suffix(".mo")))
    print(f"{po_path.relative_to(BASE_DIR)}: {po.percent_translated()}% переведено")
