# Writes the logo pieces the video animates (mark, silhouette, cross, letters)
# into ../../video/sorgenti/brand.js. Run after build.py.
import json
from pathlib import Path

here = Path(__file__).parent
mark = json.loads((here / "mark.json").read_text())
pieces = json.loads((here / "pieces.json").read_text())
data = {"mark": mark["mark"], "sil": pieces["sil"], "cross": pieces["cross"], "letters": pieces["letters"], "w": pieces["w"]}
out = here.parent.parent / "video" / "sorgenti" / "brand.js"
out.write_text("window.BRAND=" + json.dumps(data) + ";")
print("written", out)
