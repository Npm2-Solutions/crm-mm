# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The body chart drawn: where it hurts, on the body's outline from the front and
from the back.

The outlines are DottorCloud's own (`sagome_corpo.json`, drawn by NPM2; the
browser's copy is `BODY_OUTLINES` in `frontend/src/utils/moduli.js`, kept equal by
a test). An answer keeps its points and strokes as fractions of an outline's width
and height (`schema.pulisci_corpo`): the same answer is drawn the same way on a
phone, on the desk's screen and in the signed PDF, where `svg()` makes it a
picture inside the page.

Pure: no database, no request.
"""

from __future__ import annotations

import base64
import json
from functools import cache
from html import escape
from pathlib import Path

from crm.moduli import schema as S

SAGOME = Path(__file__).parent / "sagome_corpo.json"
LARGO, ALTO = 200, 460
#: What the points and strokes are drawn in: a red that reads on white paper.
SEGNO = "#c2410c"
CARTA = "#ffffff"
CONTORNO = "#5f6368"
DENTRO = "#f3f4f6"
DETTAGLIO = "#a3a7ad"


@cache
def sagome() -> dict:
	return json.loads(SAGOME.read_text(encoding="utf-8"))


def _n(x: float) -> str:
	testo = f"{x:.1f}"
	return testo[:-2] if testo.endswith(".0") else testo


def percorso(punti: list, largo: float = LARGO, alto: float = ALTO) -> str:
	"""A stroke as a smooth line: through the middles of its points, as the
	signature pad draws one (`smoothPath` in the browser)."""
	xy = [(x * largo, y * alto) for x, y in punti]
	if not xy:
		return ""
	if len(xy) == 1:
		x, y = xy[0]
		return f"M{_n(x)} {_n(y)}l0.1 0"
	parti = [f"M{_n(xy[0][0])} {_n(xy[0][1])}"]
	for i in range(1, len(xy) - 1):
		(x1, y1), (x2, y2) = xy[i], xy[i + 1]
		parti.append(f"Q{_n(x1)} {_n(y1)} {_n((x1 + x2) / 2)} {_n((y1 + y2) / 2)}")
	parti.append(f"L{_n(xy[-1][0])} {_n(xy[-1][1])}")
	return "".join(parti)


def numerati(valore) -> list[dict]:
	"""The points with their number, 1 to n in the order they were put: the
	number on the outline is the one in the list of words."""
	segni = (valore or {}).get("marks") if isinstance(valore, dict) else None
	return [{**segno, "number": i + 1} for i, segno in enumerate(segni or []) if isinstance(segno, dict)]


def _figura(vista: str, valore, x0: float, parole: dict) -> str:
	forme = sagome()
	pezzi = [
		f'<g transform="translate({_n(x0)} 0)">',
		f'<path d="{forme["body"]}" fill="{DENTRO}" stroke="{CONTORNO}" stroke-width="1.4"/>',
		f'<path d="{forme["head"]}" fill="{DENTRO}" stroke="{CONTORNO}" stroke-width="1.4"/>',
	]
	pezzi += [f'<path d="{d}" fill="none" stroke="{DETTAGLIO}" stroke-width="1"/>' for d in forme[vista]]
	# from the front the person's right is on the reader's left; from the back, on the right
	sinistra, destra = (
		(parole["right"], parole["left"]) if vista == "front" else (parole["left"], parole["right"])
	)
	pezzi.append(
		f'<text x="8" y="40" font-size="13" fill="{DETTAGLIO}" font-family="sans-serif">{escape(sinistra)}</text>'
		f'<text x="192" y="40" font-size="13" fill="{DETTAGLIO}" font-family="sans-serif" '
		f'text-anchor="end">{escape(destra)}</text>'
	)
	for tratto in (valore or {}).get("strokes") or []:
		if isinstance(tratto, dict) and tratto.get("view") == vista:
			pezzi.append(
				f'<path d="{percorso(tratto.get("points") or [])}" fill="none" stroke="{SEGNO}" '
				'stroke-opacity="0.75" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
			)
	for segno in numerati(valore):
		if segno.get("view") != vista:
			continue
		cx, cy = float(segno["x"]) * LARGO, float(segno["y"]) * ALTO
		pezzi.append(
			f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="8" fill="{SEGNO}" stroke="{CARTA}" stroke-width="1.5"/>'
			f'<text x="{_n(cx)}" y="{_n(cy + 3.6)}" font-size="10" font-weight="bold" fill="{CARTA}" '
			f'text-anchor="middle" font-family="sans-serif">{segno["number"]}</text>'
		)
	pezzi.append(
		f'<text x="100" y="{ALTO + 16}" font-size="13" fill="{CONTORNO}" text-anchor="middle" '
		f'font-family="sans-serif">{escape(parole[vista])}</text></g>'
	)
	return "".join(pezzi)


def svg(campo: dict, valore, parole: dict) -> str:
	"""The outlines the question shows, side by side, with the answer on them.
	``parole``: the words under each outline and the two sides' letters, in the
	reader's language ("front", "back", "right", "left")."""
	viste = S.viste(campo)
	largo = LARGO * len(viste) + 20 * (len(viste) - 1)
	figure = "".join(_figura(vista, valore, i * (LARGO + 20), parole) for i, vista in enumerate(viste))
	return (
		f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {largo} {ALTO + 24}" '
		f'width="{largo}" height="{ALTO + 24}">{figure}</svg>'
	)


def come_immagine(campo: dict, valore, parole: dict) -> str:
	"""The drawing as a data URI: inside the PDF, never fetched."""
	return "data:image/svg+xml;base64," + base64.b64encode(svg(campo, valore, parole).encode()).decode()
