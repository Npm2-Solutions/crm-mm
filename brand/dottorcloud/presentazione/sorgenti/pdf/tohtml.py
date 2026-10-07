# Rebuilds each slide of DottorCloud.pptx as an HTML page, for printing to PDF
# with Chromium (LibreOffice is not usable in this environment).
# Usage: python3 tohtml.py DottorCloud.pptx deck.html
import base64
import html
import io
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter
from pptx import Presentation
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE, MSO_SHAPE_TYPE

IN = 914400
prs = Presentation(sys.argv[1])
W, H = prs.slide_width / IN, prs.slide_height / IN


def inch(e):
	return f"{e / IN:.4f}in"


DPI = 150
PAD = 0.4  # inches of room around the shape for the blur


def shadow(mask, w_in, h_in, left, top):
	"""A soft two-layer drop shadow under a shape, as a pre-blurred PNG.

	Chromium prints CSS box-shadow poorly to PDF, so the shadow is an image:
	a wide, faint ambient layer plus a tight contact layer, offset downwards.
	"""
	W, H = round(w_in * DPI), round(h_in * DPI)
	p = round(PAD * DPI)
	m = mask.resize((max(1, W), max(1, H)))
	out = Image.new("L", (W + 2 * p, H + 2 * p), 0)
	for blur, dy, alpha in ((26, 16, 0.17), (7, 4, 0.06)):
		layer = Image.new("L", out.size, 0)
		layer.paste(m.point(lambda v: int(v * alpha)), (p, p + dy))
		out = ImageChops.add(out, layer.filter(ImageFilter.GaussianBlur(blur)))
	rgba = Image.new("RGBA", out.size, (11, 59, 53, 0))
	rgba.putalpha(out)
	buf = io.BytesIO()
	rgba.save(buf, "PNG")
	b = base64.b64encode(buf.getvalue()).decode()
	return (
		f'<img class="e" style="left:{left / IN - PAD:.4f}in;top:{top / IN - PAD:.4f}in;'
		f'width:{w_in + 2 * PAD:.4f}in;height:{h_in + 2 * PAD:.4f}in" src="data:image/png;base64,{b}">'
	)


def rounded_mask(w_in, h_in, r_in):
	W, H = round(w_in * DPI), round(h_in * DPI)
	m = Image.new("L", (W, H), 0)
	ImageDraw.Draw(m).rounded_rectangle([0, 0, W - 1, H - 1], radius=round(r_in * DPI), fill=255)
	return m


out = [
	f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:Carlito;src:url(carlito-regular.ttf);font-weight:400}}
@font-face{{font-family:Carlito;src:url(carlito-bold.ttf);font-weight:700}}
@page{{size:{W}in {H}in;margin:0}}*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Carlito,Calibri,sans-serif;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.s{{position:relative;width:{W}in;height:{H}in;overflow:hidden;break-after:page}}
.e{{position:absolute}} .t{{position:absolute;display:flex;flex-direction:column}}
.t p{{line-height:1.2;white-space:pre-wrap}}
</style></head><body>"""
]
count = 0
for sl in prs.slides:
	count += 1
	try:
		bg = "#" + str(sl.background.fill.fore_color.rgb)
	except Exception:
		bg = "#fff"
	out.append(f'<div class="s" style="background:{bg}">')
	rgb = tuple(int(bg[k : k + 2], 16) for k in (1, 3, 5)) if len(bg) == 7 else (255, 255, 255)
	light = sum(rgb) / 3 > 160
	for sh in sl.shapes:
		pos = f"left:{inch(sh.left)};top:{inch(sh.top)};width:{inch(sh.width)};height:{inch(sh.height)}"
		if sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
			w_in, h_in = sh.width / IN, sh.height / IN
			if light and w_in > 1.2 and h_in > 1.2:  # product screenshots, not icons or logos
				im = Image.open(io.BytesIO(sh.image.blob)).convert("RGBA")
				# the screenshot already carries a faint baked shadow: keep only the solid shape
				mask = im.getchannel("A").point(lambda v: 255 if v > 200 else 0)
				out.append(shadow(mask, w_in, h_in, sh.left, sh.top))
			data = base64.b64encode(sh.image.blob).decode()
			out.append(f'<img class="e" style="{pos}" src="data:{sh.image.content_type};base64,{data}">')
			continue
		if sh.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE:
			try:
				color = "#" + str(sh.fill.fore_color.rgb)
			except Exception:
				color = None
			if color:
				style = f"{pos};background:{color}"
				if sh.auto_shape_type == MSO_AUTO_SHAPE_TYPE.OVAL:
					style += ";border-radius:50%"
				elif sh.auto_shape_type == MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE:
					adj = sh.adjustments[0] if len(sh.adjustments) else 0.16
					style += f";border-radius:{adj * min(sh.width, sh.height) / IN:.3f}in"
					if color.upper() == "#FFFFFF":
						r_in = adj * min(sh.width, sh.height) / IN
						out.append(
							shadow(
								rounded_mask(sh.width / IN, sh.height / IN, r_in),
								sh.width / IN,
								sh.height / IN,
								sh.left,
								sh.top,
							)
						)
						style += ";border:0.75pt solid #E6ECEA"
				out.append(f'<div class="e" style="{style}"></div>')
		if sh.has_text_frame and sh.text_frame.text.strip():
			tf = sh.text_frame
			middle = tf.vertical_anchor is not None and int(tf.vertical_anchor) == 3
			paras = []
			for para in tf.paragraphs:
				if not para.runs:
					continue
				run = para.runs[0]
				size = run.font.size.pt if run.font.size else 18
				weight = 700 if run.font.bold else 400
				try:
					col = "#" + str(run.font.color.rgb)
				except Exception:
					col = "#000"
				al = para.alignment
				align = (
					"center"
					if al is not None and int(al) == 2
					else "right"
					if al is not None and int(al) == 3
					else "left"
				)
				# every run keeps its own colour (a title's highlighted words)
				parts = []
				for r in para.runs:
					try:
						rc = "#" + str(r.font.color.rgb)
					except Exception:
						rc = col
					parts.append(
						html.escape(r.text)
						if rc == col
						else f'<span style="color:{rc}">{html.escape(r.text)}</span>'
					)
				text = "".join(parts)
				paras.append(
					f'<p style="font-size:{size}pt;font-weight:{weight};color:{col};text-align:{align}">{text}</p>'
				)
			out.append(
				f'<div class="t" style="{pos};justify-content:{"center" if middle else "flex-start"}">{"".join(paras)}</div>'
			)
	out.append("</div>")
out.append("</body></html>")
# nosemgrep: frappe-security-file-traversal — a tool run by hand: it writes where its command line says
open(sys.argv[2], "w").write("".join(out))
print("slides", count)
