# Copyright (c) 2026, NPM2 Solutions Srl and contributors
"""Fotografa le pagine del sito (servite in locale) a pagina intera.
Uso: python3 screenshot_sito.py <cartella-sito> <cartella-uscita> "/:home:1366,/funzioni/:funzioni:1366,/:home-telefono:390"
Richiede playwright e Pillow."""

import http.server
import os
import socketserver
import sys
import threading

from PIL import Image
from playwright.sync_api import sync_playwright

root = sys.argv[1]
out = sys.argv[2]
pages = sys.argv[3].split(",")


class H(http.server.SimpleHTTPRequestHandler):
	def __init__(s, *a, **k):
		super().__init__(*a, directory=root, **k)

	def log_message(self, *a):
		pass


socketserver.TCPServer.allow_reuse_address = True
srv = socketserver.TCPServer(("127.0.0.1", 8766), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
os.makedirs(out, exist_ok=True)
with sync_playwright() as pw:
	b = pw.chromium.launch()
	for pg in pages:
		path, name, w = pg.split(":")
		p = b.new_page(viewport={"width": int(w), "height": 800})
		p.goto("http://127.0.0.1:8766" + path)
		p.wait_for_timeout(800)
		p.add_style_tag(
			content=".reveal,.arrive,.pop{opacity:1!important;transform:none!important;animation:none!important;transition:none!important}.site-header{position:relative!important}"
		)
		p.evaluate(
			"async()=>{for(let y=0;y<document.body.scrollHeight;y+=600){window.scrollTo(0,y);await new Promise(r=>setTimeout(r,60))}window.scrollTo(0,0)}"
		)
		p.evaluate('document.querySelectorAll("img[loading=lazy]").forEach(i=>i.loading="eager")')
		p.wait_for_timeout(1200)
		p.screenshot(path=f"{out}/{name}.png", full_page=True)
		im = Image.open(f"{out}/{name}.png")
		W = 683 if int(w) > 700 else int(w)
		k = 0
		step = 2600
		for y in range(0, im.height, step):
			c = im.crop((0, y, im.width, min(im.height, y + step)))
			c = c.resize((W, int(c.height * W / im.width)))
			c.save(f"{out}/{name}-{k}.png")
			k += 1
		print(name, im.height, k)
	b.close()
srv.shutdown()
