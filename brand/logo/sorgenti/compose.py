import json

M = json.load(open("mark.json"))
W = json.load(open("word.json"))
mx0, my0, mx1, my1 = M["bounds"]
mw, mh = mx1 - mx0, my1 - my0
TEAL = "#12a594"
TEALD = "#0b6f64"
INK = "#16201e"
MINT = "#5fe0cc"


def mark_g(x, y, h, fill):
	s = h / mh
	return f'<path transform="translate({x:.2f} {y:.2f}) scale({s:.4f}) translate({-mx0} {-my0})" d="{M["mark"]}" fill="{fill}"/>'


CAP = 72.7  # Inter cap height at 100px ≈ 72.7


def word_g(x, base, size, c1, c2):
	s = size / 100
	return f'<g transform="translate({x:.2f} {base:.2f}) scale({s:.4f})"><path d="{W["dottor"]}" fill="{c1}"/><path d="{W["cloud"]}" fill="{c2}"/></g>'


def svg(w, h, body, bg=None):
	b = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
	return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{b}{body}</svg>\n'


def horiz(c1, c2, mf, bg=None):
	H = 100
	size = H * 0.62
	capH = size * CAP / 100
	mx = mark_g(0, 0, H, mf)
	wx = H * mw / mh + H * 0.26
	base = H - (H - capH) / 2 - 0.0 * H
	base = H * 0.5 + capH / 2
	w = wx + W["w"] * size / 100 + 2
	return svg(round(w), H, mx + word_g(wx, base, size, c1, c2), bg)


def stacked(c1, c2, mf, bg=None):
	size = 100
	ww = W["w"]
	mhh = 150
	mww = mhh * mw / mh
	w = max(ww, mww) + 4
	mxx = (w - mww) / 2
	body = mark_g(mxx, 0, mhh, mf) + word_g((w - ww) / 2, mhh + 40 + 72.7, size, c1, c2)
	return svg(round(w), round(mhh + 40 + 100), body, bg)


def icon(bg1, bg2, mf, size=512, r=112):
	mhh = size * 0.5
	mww = mhh * mw / mh
	g = f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{bg1}"/><stop offset="1" stop-color="{bg2}"/></linearGradient></defs><rect width="{size}" height="{size}" rx="{r}" fill="url(#g)"/>'
	# optical centre: the cross sits a bit right/low, nudge left/up
	return svg(
		size, size, g + mark_g((size - mww) / 2 - size * 0.015, (size - mhh) / 2 - size * 0.01, mhh, mf)
	)


out = {
	"dottorcloud-orizzontale.svg": horiz(INK, TEAL, TEAL),
	"dottorcloud-orizzontale-negativo.svg": horiz("#ffffff", MINT, MINT),
	"dottorcloud-verticale.svg": stacked(INK, TEAL, TEAL),
	"dottorcloud-verticale-negativo.svg": stacked("#ffffff", MINT, MINT),
	"dottorcloud-marchio.svg": svg(round(mw * 5), round(mh * 5), mark_g(0, 0, mh * 5, TEAL)),
	"dottorcloud-marchio-bianco.svg": svg(round(mw * 5), round(mh * 5), mark_g(0, 0, mh * 5, "#ffffff")),
	"dottorcloud-icona-app.svg": icon("#17b8a4", TEALD, "#ffffff"),
	"dottorcloud-orizzontale-nero.svg": horiz("#000000", "#000000", "#000000"),
}
for k, v in out.items():
	open("../" + k, "w").write(v)
print("\n".join(out))
