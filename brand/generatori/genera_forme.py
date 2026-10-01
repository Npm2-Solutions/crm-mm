# Copyright (c) 2026, NPM2 Solutions Srl and contributors
"""Le forme e le composizioni del marchio DottorCloud, in SVG.

Legge i colori da ../design-system/espresso/tokens.json e scrive:
  ../forme/          la croce, il motivo delle croci, la nuvola-D, la gobba, l'avatar a nuvola
  ../composizioni/   copertina, hero del sito, chiusura, stato vuoto, immagine di condivisione

Uso:  python3 genera_forme.py
Poi, per i PNG:  python3 rendi_png.py   (richiede playwright)
"""

import json
from pathlib import Path

from percorsi import COMPOSIZIONI, FORME, MARCHIO, TOKEN

T = json.loads(TOKEN.read_text())
CARTELLE = {"03-forme": FORME, "04-composizioni": COMPOSIZIONI}
COL = {t["name"]: t["value"] for t in T["color"]["tokens"]}


def col(name, theme="light"):
	v = COL[name].get(theme) or COL[name]["light"]
	while v.startswith("{"):
		v = COL[v[1:-1]].get(theme) or COL[v[1:-1]]["light"]
	return v


TEAL700, TEAL500, MINT, TEAL100 = col("teal-700"), col("teal-500"), col("mint-300"), col("teal-100")
INK, NIGHT, TEAL950 = col("ink-900"), col("night-950"), col("teal-950")
BG = "#f6f8f7"

# La croce del marchio: bracci uguali, larghi un terzo (come nel logo)
CROSS = "M4 0h4v4h4v4H8v4H4V8H0V4h4z"


def cross(x, y, s, fill):
	k = s / 12
	return f'<path transform="translate({x:.1f} {y:.1f}) scale({k:.4f})" d="{CROSS}" fill="{fill}"/>'


def cloud(x, y, w, h, r, tail, fill, extra=""):
	"""Rettangolo a nuvola-D: tre angoli a r, quello in basso a sinistra a tail."""
	r = min(r, w / 2, h / 2)
	t = min(tail, r)
	d = (
		f"M{x + r},{y} H{x + w - r} A{r},{r} 0 0 1 {x + w},{y + r} V{y + h - r} "
		f"A{r},{r} 0 0 1 {x + w - r},{y + h} H{x + t} A{t},{t} 0 0 1 {x},{y + h - t} "
		f"V{y + r} A{r},{r} 0 0 1 {x + r},{y} Z"
	)
	return f'<path d="{d}" fill="{fill}"{extra}/>'


def bump(cx, cy, r, fill):
	"""La gobba: mezzo disco che sporge sopra un blocco (base su cy)."""
	return f'<path d="M{cx - r},{cy} A{r},{r} 0 0 1 {cx + r},{cy} Z" fill="{fill}"/>'


def crosses(x, y, w, h, pitch, size, fill, clip=None):
	out = []
	n = 0
	yy = y + (pitch - size) / 2
	while yy + size <= y + h:
		xx = x + (pitch - size) / 2
		while xx + size <= x + w:
			out.append(cross(xx, yy, size, fill))
			n += 1
			xx += pitch
		yy += pitch
	g = "".join(out)
	return f'<g clip-path="url(#{clip})">{g}</g>' if clip else f"<g>{g}</g>"


def svg(w, h, body, bg=None, defs=""):
	b = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
	return (
		f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
		f"<defs>{defs}</defs>{b}{body}</svg>\n"
	)


def font_style():
	return (
		"<style>@font-face{font-family:Inter;src:url(../font/Inter-Variable-latin.woff2);font-weight:100 900}"
		".t{font-family:Inter,-apple-system,Segoe UI,sans-serif}</style>"
	)


def write(folder, name, content):
	p = CARTELLE[folder] / name
	p.parent.mkdir(parents=True, exist_ok=True)
	p.write_text(content)
	print("scritto", p.relative_to(MARCHIO))


# ---------- 03-forme ----------
write("03-forme", "croce.svg", svg(12, 12, f'<path d="{CROSS}" fill="{TEAL500}"/>'))
write("03-forme", "croce-bianca.svg", svg(12, 12, f'<path d="{CROSS}" fill="#ffffff"/>'))
write("03-forme", "croce-menta.svg", svg(12, 12, f'<path d="{CROSS}" fill="{MINT}"/>'))
# la piastrella del motivo: 40x40, croce di 20px al centro (passo 40, come sul sito)
write(
	"03-forme",
	"motivo-croci-piastrella.svg",
	svg(40, 40, '<path d="M16.5 10h7v6.5H30v7h-6.5V30h-7v-6.5H10v-7h6.5z" fill="#000"/>'),
)
write(
	"03-forme",
	"motivo-croci-esempio.svg",
	svg(320, 200, cloud(0, 0, 320, 200, 28, 4, TEAL700) + crosses(0, 0, 320, 200, 40, 20, MINT)),
)
# nuvola-D: i raggi usati
body = ""
x = 0
for w, h, r, t, lab in [
	(120, 44, 14, 4, "pulsante sito 14/4"),
	(120, 32, 8, 2, "pulsante gestionale 8/2"),
	(160, 110, 20, 4, "carta sito 20/4"),
	(160, 110, 12, 2, "carta gestionale 12/2"),
]:
	body += (
		cloud(x, 10, w, h, r, t, TEAL700)
		+ f'<text class="t" x="{x}" y="{h + 34}" font-size="12" fill="{INK}">{lab}</text>'
	)
	x += w + 30
write("03-forme", "nuvola-d.svg", svg(x, 170, font_style() + body, bg="#ffffff"))
# l'avatar e i segni a nuvola: border-radius 50% 50% 50% 22%
av = (
	f'<path d="M48,0 A48,48 0 0 1 96,48 A48,48 0 0 1 48,96 H21.1 A21.1,21.1 0 0 1 0,74.9 V48 A48,48 0 0 1 48,0 Z" fill="{TEAL100}"/>'
	f'<text class="t" x="48" y="58" font-size="30" font-weight="700" text-anchor="middle" fill="{TEAL700}">MR</text>'
)
write("03-forme", "avatar-nuvola.svg", svg(96, 96, font_style() + av))
write("03-forme", "gobba.svg", svg(240, 180, cloud(0, 40, 240, 140, 24, 4, MINT) + bump(80, 40, 40, MINT)))

# ---------- 04-composizioni ----------
# copertina (come nel design system): 960x288
cov = (
	font_style()
	+ f'<rect width="960" height="288" fill="{BG}"/>'
	+ cloud(520, 0, 176, 288, 16, 4, TEAL700)
	+ "".join(cross(548 + c * 48, 40 + r * 64, 24, MINT) for r in range(4) for c in range(3))
	+ cloud(712, -24, 280, 168, 12, 4, TEAL500)
	+ cloud(712, 160, 160, 128, 12, 4, MINT)
	+ bump(792, 160, 40, MINT)
	+ cloud(888, 160, 96, 128, 12, 4, INK)
	+ f'<circle cx="944" cy="96" r="32" fill="{TEAL100}"/>'
	+ f'<text class="t" x="40" y="214" font-size="64" font-weight="700" letter-spacing="-2.2" fill="{INK}">DottorCloud</text>'
	+ '<text class="t" x="40" y="248" font-size="14" fill="#5f6b69">Il gestionale che tiene tutto il centro medico in un posto solo.</text>'
)
write("04-composizioni", "copertina.svg", svg(960, 288, cov))

# hero del sito: i blocchi dietro allo screenshot (la finestra è un segnaposto)
W, H = 1200, 640
hero = '<clipPath id="slab"><path d="M60,180 H332 A28,28 0 0 1 360,208 V560 A28,28 0 0 1 332,588 H64 A4,4 0 0 1 60,584 V208 A28,28 0 0 1 88,180 Z"/></clipPath>'
herob = (
	cloud(60, 180, 300, 408, 28, 4, TEAL700)
	+ crosses(60, 180, 300, 408, 40, 20, MINT, "slab")
	+ cloud(880, 110, 300, 360, 28, 4, MINT)
	+ bump(1080, 110, 44, MINT)
	+ cloud(140, 60, 900, 460, 12, 4, "#ffffff", ' stroke="#e1e6e4"')
	+ '<rect x="160" y="80" width="860" height="22" rx="6" fill="#f1f4f3"/>'
	+ "".join(
		f'<rect x="{180 + i * 210}" y="130" width="190" height="{360 - i * 40}" rx="8" fill="#f6f8f7"/>'
		for i in range(4)
	)
	+ cloud(200, 440, 330, 64, 16, 4, TEAL950)
	+ cloud(212, 450, 44, 44, 12, 4, MINT)
	+ cloud(960, 250, 170, 330, 28, 4, "#111413")
)
write("04-composizioni", "hero-sito.svg", svg(W, H, herob, bg=BG, defs=hero))

# chiusura: blocchi che scendono dall'alto a destra, motivo in basso a sinistra
ch = (
	f'<rect width="1200" height="520" fill="{NIGHT}"/>'
	+ f'<path d="M960,0 H1200 V320 H988 A28,28 0 0 1 960,292 Z" fill="{TEAL700}"/>'
	+ f'<path d="M840,0 H930 V140 A28,28 0 0 1 902,168 H844 A4,4 0 0 1 840,164 Z" fill="{MINT}"/>'
	+ f'<g opacity="0.22">{crosses(0, 340, 360, 180, 40, 20, TEAL500)}</g>'
	+ font_style()
	+ '<text class="t" x="600" y="250" font-size="56" font-weight="800" letter-spacing="-2" text-anchor="middle" fill="#ffffff">Vediamolo sul tuo centro.</text>'
	+ cloud(510, 300, 180, 52, 14, 4, MINT)
	+ f'<text class="t" x="600" y="332" font-size="17" font-weight="700" text-anchor="middle" fill="{NIGHT}">Richiedi una demo</text>'
)
write("04-composizioni", "chiusura-sito.svg", svg(1200, 520, ch))

# stato vuoto (96x60, ingrandito 4 volte)
ev = (
	cloud(0, 10, 36, 50, 10, 2, TEAL700)
	+ cross(11, 23, 14, MINT)
	+ cloud(42, 0, 54, 28, 10, 2, TEAL500)
	+ cloud(42, 34, 30, 26, 10, 2, MINT)
	+ bump(57, 34, 8, MINT)
	+ cloud(78, 34, 18, 26, 7, 2, INK)
)
write("04-composizioni", "stato-vuoto.svg", svg(96, 60, ev))

# immagine di condivisione (og:image) 1200x630
og = (
	font_style()
	+ f'<rect width="1200" height="630" fill="{BG}"/>'
	+ cloud(700, 0, 220, 630, 28, 4, TEAL700)
	+ "".join(cross(736 + c * 60, 60 + r * 80, 28, MINT) for r in range(7) for c in range(3))
	+ cloud(940, -30, 300, 330, 28, 4, TEAL500)
	+ cloud(940, 320, 200, 310, 28, 4, MINT)
	+ bump(1040, 320, 52, MINT)
	+ cloud(1160, 320, 80, 310, 20, 4, INK)
	+ '<image href="../logo/dottorcloud-orizzontale.svg" x="72" y="250" width="541" height="110"/>'
	+ '<text class="t" x="76" y="420" font-size="28" fill="#5f6b69">Il gestionale per il tuo centro medico.</text>'
)
write("04-composizioni", "condivisione-og.svg", svg(1200, 630, og))
