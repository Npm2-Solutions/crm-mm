# Copyright (c) 2026, NPM2 Solutions Srl and contributors
"""Rende in PNG (2x) le forme e le composizioni SVG. Richiede: pip install playwright && playwright install chromium"""

import re
from pathlib import Path

from percorsi import COMPOSIZIONI, FORME, MARCHIO
from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
	b = pw.chromium.launch(args=["--allow-file-access-from-files"])
	for f in sorted(FORME.glob("*.svg")) + sorted(COMPOSIZIONI.glob("*.svg")):
		w, h = (float(n) for n in re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', f.read_text()).groups())
		scale = 4 if w < 100 else 2
		p = b.new_page(viewport={"width": int(w), "height": int(h)}, device_scale_factor=scale)
		p.goto(f.as_uri())
		p.wait_for_timeout(400)
		out = f.with_suffix(".png")
		p.screenshot(path=str(out), omit_background=True)
		print("reso", out.relative_to(MARCHIO))
		p.close()
	b.close()
