# Copyright (c) 2026, NPM2 Solutions Srl and contributors
"""Da design-system/espresso/tokens.json a tokens.css (variabili con i nomi di frappe-ui).
Uso: python3 genera_css.py [percorso-font-relativo-al-css]"""

import json
import re
import sys

from percorsi import ESPRESSO, TOKEN

T = json.loads(TOKEN.read_text())
font = sys.argv[1] if len(sys.argv) > 1 else "../../font/Inter-Variable-latin.woff2"


def v(x):
	return re.sub(r"^\{(.+)\}$", r"var(--\1)", x)


L, D = [], []
for t in T["color"]["tokens"]:
	L.append(f"  --{t['name']}: {v(t['value']['light'])};")
	if "dark" in t["value"]:
		D.append(f"  --{t['name']}: {v(t['value']['dark'])};")
for t in T["shadow"]["tokens"]:
	L.append(f"  --{t['name']}: {t['value']['light']};")
	D.append(f"  --{t['name']}: {t['value']['dark']};")
R = [f"  --{t['name']}: {t['value']};" for k in ["spacing", "radius", "size"] for t in T[k]["tokens"]]
R += [f"  --font-{k}: {s};" for k, s in T["type"]["families"].items()]
css = (
	"/* Copyright (c) 2026, NPM2 Solutions Srl and contributors\n   DottorCloud su Espresso (frappe-ui): i token. Generato da tokens.json. */\n"
	f"@font-face {{ font-family: 'Inter'; src: url('{font}') format('woff2'); font-weight: 100 900; font-display: swap; }}\n"
	":root, [data-theme='light'] {\n"
	+ "\n".join(L)
	+ "\n}\n[data-theme='dark'] {\n"
	+ "\n".join(D)
	+ "\n}\n:root {\n"
	+ "\n".join(R)
	+ "\n}\n"
)
(ESPRESSO / "tokens.css").write_text(css)
print("scritto design-system/espresso/tokens.css")
