# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Every page of the settings somebody links to is in the menu.

The menu is the frontend's (`frontend/src/utils/impostazioni.js`): groups, entries
and tabs, each page under the name it had, as a key or an alias. The server builds
links to those names - a dashboard's hint, the way back from Facebook and Google,
the WhatsApp signup, the Social Planner's sources - and so do the buttons around
the app. A name the menu lost would open the first page instead, and nobody would
be told: so here every one of them is looked up.
"""

import re
from pathlib import Path
from unittest import TestCase

RADICE = Path(__file__).resolve().parents[2]
MENU = RADICE / "frontend" / "src" / "utils" / "impostazioni.js"


def nomi_del_menu() -> set[str]:
	"""Every name the menu opens: the keys of groups, entries and tabs, the aliases."""
	testo = MENU.read_text(encoding="utf-8")
	nomi = set(re.findall(r"\bkey: '([^']+)'", testo))
	for alias in re.findall(r"aliases: \[([^\]]*)\]", testo):
		nomi |= set(re.findall(r"'([^']+)'", alias))
	return nomi


def nomi_del_server() -> dict[str, str]:
	"""The pages the server sends a person to, each with where it comes from."""
	from crm.dashboard.features import FEATURES
	from crm.social.sources import SOURCES
	from crm.www.oauth_connected import SETTINGS_PAGE

	nomi = {f"the dashboard's {chiave}": f.settings for chiave, f in FEATURES.items() if f.settings}
	nomi.update({f"the way back from {chiave}": pagina for chiave, pagina in SETTINGS_PAGE.items()})
	nomi.update({f"the source {s.key}": s.settings_page for s in SOURCES})
	for file in (RADICE / "crm").rglob("*.py"):
		if "tests" in file.parts:
			continue
		testo = file.read_text(encoding="utf-8")
		dove = file.relative_to(RADICE)
		for nome in re.findall(r"[?&]settings=([A-Za-z][A-Za-z ]*)", testo):
			nomi[f"{dove}, a link"] = nome
		for nome in re.findall(r'"settings": "([^"]+)"', testo):
			nomi[f"{dove}, a widget"] = nome
	return nomi


def nomi_dell_app() -> dict[str, str]:
	"""The pages the app's own buttons open."""
	nomi = {}
	for file in (RADICE / "frontend" / "src").rglob("*"):
		if file.suffix not in (".vue", ".js") or file.name == "impostazioni.js":
			continue
		testo = file.read_text(encoding="utf-8")
		dove = file.relative_to(RADICE)
		for nome in re.findall(r"activeSettingsPage(?:\.value)?\s*=\s*'([^']+)'", testo):
			nomi[f"{dove}: {nome}"] = nome
		for nome in re.findall(r"openSettings\('([^']+)'\)", testo):
			nomi[f"{dove}: {nome}"] = nome
	return nomi


class IlMenuDelleImpostazioni(TestCase):
	def test_le_pagine_che_il_server_nomina_ci_sono(self):
		menu = nomi_del_menu()
		nomi = nomi_del_server()
		# the hints of the dashboard, the OAuth callbacks, WhatsApp's and the planner's
		self.assertGreater(len(nomi), 10)
		mancano = {dove: nome for dove, nome in nomi.items() if nome not in menu}
		self.assertEqual(mancano, {}, "pages the server links to that the settings' menu lost")

	def test_le_pagine_che_l_app_apre_ci_sono(self):
		menu = nomi_del_menu()
		nomi = nomi_dell_app()
		self.assertIn("Invite User", nomi.values())
		mancano = {dove: nome for dove, nome in nomi.items() if nome not in menu}
		self.assertEqual(mancano, {}, "pages the app's buttons open that the settings' menu lost")

	def test_i_vecchi_nomi_restano(self):
		# a sample of the names the pages had before they were grouped: as
		# entries, tabs or aliases they still open
		menu = nomi_del_menu()
		for nome in (
			"Price Lists",
			"Team rota",
			"Studio hours & rules",
			"Page & rules",
			"Booking platforms",
			"Sales Hierarchy",
			"SLA Policies",
			"Lead forms",
			"Qualification register",
			"Brand",
			"Home Actions",
		):
			self.assertIn(nome, menu)
