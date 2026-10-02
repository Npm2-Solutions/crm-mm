# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The site's images, made from the brand's.

The product screens are the ones the video and the presentation use
(brand/presentazione/sorgenti/img, taken with brand/video/sorgenti/grab.mjs):
here they become WebP at twice the size the page shows them. The picture for
link previews is the brand's composition (brand/composizioni/condivisione-og.png).

    pip install pillow
    python3 sito/immagini.py

Writes sito/risorse/img/. Run it again when a screen in brand/ changes.
"""

from pathlib import Path

from PIL import Image

RADICE = Path(__file__).resolve().parent.parent
SCHERMATE = RADICE / "brand/presentazione/sorgenti/img"
USCITA = RADICE / "sito/risorse/img"

# name -> width in pixels: twice the widest the page shows it
LARGHEZZE = {
	# windows across the whole column
	"agenda": 2000,
	"auto": 2000,
	# windows and cards beside the text
	"chat": 1200,
	"clinica": 1200,
	"fattura": 1200,
	"servizi": 1200,
	"livelli-medico": 1200,
	"livelli-marketing": 1200,
	"ai": 1200,
	"chiamata": 1000,
	"social": 900,
	"lead": 900,
	"gdpr": 900,
	"muscoli": 700,
	"spesa": 700,
}


# smaller copies of the wide pictures, for phones and narrow columns:
# the build offers them in srcset as <name>-<width>.webp
RIDOTTE = (800, 1200)


# the phones, upright (brand/video/sorgenti/telefoni.mjs makes telefono-<name>.png)
TELEFONI = {nome: 640 for nome in ("login", "home", "firma", "dieta", "esercizio", "esercizi", "staff")}


def webp(sorgente: Path, destinazione: Path, larghezza: int) -> None:
	immagine = Image.open(sorgente).convert("RGBA")
	if immagine.width > larghezza:
		altezza = round(immagine.height * larghezza / immagine.width)
		immagine = immagine.resize((larghezza, altezza), Image.LANCZOS)
	immagine.save(destinazione, "WEBP", quality=82, method=6)


def condivisione() -> None:
	"""The brand's composition for shared links (brand/composizioni), at 1200x630."""
	og = Image.open(RADICE / "brand/composizioni/condivisione-og.png").convert("RGB")
	og.resize((1200, 630), Image.LANCZOS).save(
		USCITA / "condivisione.jpg", "JPEG", quality=88, optimize=True, progressive=True
	)
	# the same cover, smaller, as the poster of the video on the page
	poster = Image.open(RADICE / "brand/video/DottorCloud.jpg").convert("RGB")
	poster = poster.resize((1600, round(poster.height * 1600 / poster.width)), Image.LANCZOS)
	poster.save(USCITA / "video.webp", "WEBP", quality=80, method=6)


def main() -> None:
	USCITA.mkdir(parents=True, exist_ok=True)
	for nome, larghezza in LARGHEZZE.items():
		webp(SCHERMATE / f"{nome}.png", USCITA / f"{nome}.webp", larghezza)
		for ridotta in RIDOTTE:
			if ridotta < larghezza:
				webp(SCHERMATE / f"{nome}.png", USCITA / f"{nome}-{ridotta}.webp", ridotta)
	for nome, larghezza in TELEFONI.items():
		webp(SCHERMATE / f"telefono-{nome}.png", USCITA / f"{nome}.webp", larghezza)
	condivisione()
	for file in sorted(USCITA.iterdir()):
		print(f"{file.name:28} {file.stat().st_size // 1024:5} KB")


if __name__ == "__main__":
	main()
