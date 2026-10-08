# Copyright (c) 2026, NPM2 Solutions Srl and contributors
"""Dove stanno le cose del marchio nel repo (brand/dottorcloud/): i generatori leggono e
scrivono qui. Nel kit consegnato erano le cartelle 01-marchio … 07-generatori."""

from pathlib import Path

MARCHIO = Path(__file__).resolve().parent.parent
LOGO = MARCHIO / "logo"
FONT = MARCHIO / "font"
ICONE = MARCHIO / "icone"
FORME = MARCHIO / "forme"
COMPOSIZIONI = MARCHIO / "composizioni"
ESPRESSO = MARCHIO / "design-system" / "espresso"
TOKEN = ESPRESSO / "tokens.json"
