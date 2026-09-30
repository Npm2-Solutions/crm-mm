import io

import pathops
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

K = 0.5522847498


def circle(cx, cy, r):
	p = pathops.Path()
	k = K * r
	p.moveTo(cx + r, cy)
	p.cubicTo(cx + r, cy + k, cx + k, cy + r, cx, cy + r)
	p.cubicTo(cx - k, cy + r, cx - r, cy + k, cx - r, cy)
	p.cubicTo(cx - r, cy - k, cx - k, cy - r, cx, cy - r)
	p.cubicTo(cx + k, cy - r, cx + r, cy - k, cx + r, cy)
	p.close()
	return p


def rrect(x, y, w, h, r):
	r = min(r, w / 2, h / 2)
	p = pathops.Path()
	k = K * r
	p.moveTo(x + r, y)
	p.lineTo(x + w - r, y)
	p.cubicTo(x + w - r + k, y, x + w, y + r - k, x + w, y + r)
	p.lineTo(x + w, y + h - r)
	p.cubicTo(x + w, y + h - r + k, x + w - r + k, y + h, x + w - r, y + h)
	p.lineTo(x + r, y + h)
	p.cubicTo(x + r - k, y + h, x, y + h - r + k, x, y + h - r)
	p.lineTo(x, y + r)
	p.cubicTo(x, y + r - k, x + r - k, y, x + r, y)
	p.close()
	return p


def op(a, b, o):
	return pathops.op(a, b, o)


U, D, I = pathops.PathOp.UNION, pathops.PathOp.DIFFERENCE, pathops.PathOp.INTERSECTION


def mark():
	# a cloud with a flat base and a flat left side (the stem of a D);
	# both lobes are tangent to the edges, so every join is smooth
	body = rrect(12, 40, 56, 48, 0)
	for c in (circle(38, 40, 26), circle(68, 60, 28)):
		body = op(body, c, U)
	body = op(body, rrect(12, 0, 200, 88, 12), I)  # rounds only the bottom-left corner
	cx, cy, L, T = 53, 61, 32, 12
	cross = op(rrect(cx - T / 2, cy - L / 2, T, L, 3.5), rrect(cx - L / 2, cy - T / 2, L, T, 3.5), U)
	return op(body, cross, D)


def d_of(p):
	pen = SVGPathPen(None)
	p.draw(pen)
	return pen.getCommands()


m = mark()
b = m.bounds
print("mark bounds", b)
# ---- wordmark from Inter at wght 700
f = TTFont("inter.woff2")
f = instancer.instantiateVariableFont(
	f, {"wght": 700, "opsz": 32} if "opsz" in [a.axisTag for a in f["fvar"].axes] else {"wght": 700}
)
gs = f.getGlyphSet()
cmap = f.getBestCmap()
upm = f["head"].unitsPerEm


def text_path(s, size, x0, base, track=-0.03):
	sc = size / upm
	x = x0
	out = []
	for ch in s:
		g = cmap[ord(ch)]
		pen = SVGPathPen(gs)
		tp = TransformPen(pen, (sc, 0, 0, -sc, x, base))
		gs[g].draw(tp)
		out.append(pen.getCommands())
		x += gs[g].width * sc + track * size
	return " ".join(out), x


import json

json.dump({"mark": d_of(m), "bounds": b}, open("mark.json", "w"))
t1, x1 = text_path("Dottor", 100, 0, 0)
t2, x2 = text_path("Cloud", 100, x1 + 2, 0)
json.dump({"dottor": t1, "cloud": t2, "w": x2}, open("word.json", "w"))
print("word width", x2)


# ---- pieces for animation: silhouette, cross, per-letter outlines
def sil():
	body = rrect(12, 40, 56, 48, 0)
	for c in (circle(38, 40, 26), circle(68, 60, 28)):
		body = op(body, c, U)
	return op(body, rrect(12, 0, 200, 88, 12), I)


cx, cy, L, T = 53, 61, 32, 12
cr = op(rrect(cx - T / 2, cy - L / 2, T, L, 3.5), rrect(cx - L / 2, cy - T / 2, L, T, 3.5), U)
letters = []
x = 0
for ch in "DottorCloud":
	g = cmap[ord(ch)]
	pen = SVGPathPen(gs)
	sc = 100 / upm
	gs[g].draw(TransformPen(pen, (sc, 0, 0, -sc, 0, 0)))
	letters.append({"d": pen.getCommands(), "x": x})
	x += gs[g].width * sc - 3
	if ch == "r":
		x += 2
json.dump({"sil": d_of(sil()), "cross": d_of(cr), "letters": letters, "w": x}, open("pieces.json", "w"))
print("pieces ok", x)
