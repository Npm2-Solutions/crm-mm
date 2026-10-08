# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A form template: the draft the centre works on (`crm.moduli.modelli`).

People never fill the draft: they fill a published version, which does not
change. So the draft can be half-written; publishing is what asks it to be right.
"""

import re
import unicodedata

import frappe
from frappe import _
from frappe.model.document import Document

from crm.moduli import modelli

#: The address of a form on the website: /crm-form/<route>.
INDIRIZZO = re.compile(r"^[a-z0-9][a-z0-9-]{1,79}$")
#: Where the person goes once the form is sent: a page, on this site or another.
DOPO = re.compile(r"^(https?://[^\s\"'<>]+|/(?!/)[^\s\"'<>]*)$")


def indirizzo_da(titolo: str | None) -> str:
	"""An address from a title: "Richiedi informazioni" is richiedi-informazioni."""
	testo = unicodedata.normalize("NFKD", titolo or "").encode("ascii", "ignore").decode().lower()
	indirizzo = re.sub(r"[^a-z0-9]+", "-", testo).strip("-")[:70].strip("-")
	return indirizzo if len(indirizzo) >= 2 else "modulo"


class CRMFormTemplate(Document):
	def validate(self):
		self.title = (self.title or "").strip()
		if not self.title:
			frappe.throw(_("A form needs a title"))
		self.use = self.use or modelli.FORMA
		uso = next((uso for uso in modelli.usi() if uso.chiave == self.use), None)
		if not uso:
			frappe.throw(_("{0} is not a use of forms on this site").format(frappe.bold(self.use)))
		if uso.clinico:
			# a use that records health data, always
			self.clinical = 1
		if not uso.si_manda:
			# a sheet, or a form on the website: nobody owes it, nothing sends it
			self.ask_on = "By hand"
			self.send_before = 0
		if uso.sul_sito:
			self._sul_sito()
		else:
			self.route = None
		if self.clinical and not modelli.dato_clinico_disponibile():
			# the mark means something only where the clinic is on: elsewhere it
			# would promise a protection nobody gives
			frappe.throw(_("Health data is for the medical centre, which is off on this site"))
		schema = modelli.carica_schema(self.schema)
		if not isinstance(schema.get("sections"), list):
			frappe.throw(_("This is not a form"))
		if self.ask_on != "Services":
			self.set("services", [])
		if self.validity == "Every few weeks":
			from crm.moduli.dovuti import SETTIMANE

			minimo, massimo = SETTIMANE
			if not minimo <= (self.validity_weeks or 0) <= massimo:
				frappe.throw(_("A form is asked again every {0} to {1} weeks").format(minimo, massimo))

	def _sul_sito(self):
		"""A form anybody fills on the website: an address of its own, and no health
		data - whoever sends it is nobody's patient yet."""
		if self.clinical:
			frappe.throw(_("A form on the website does not record health data"))
		self.route = (self.route or "").strip().strip("/").lower()
		if not self.route:
			# a new form gets one from its title, which the author may then change
			self.route = modelli.indirizzo_libero(indirizzo_da(self.title))
		if not INDIRIZZO.match(self.route):
			frappe.throw(_("The address takes lowercase letters, numbers and dashes"))
		altro = frappe.db.get_value(
			modelli.MODELLO, {"route": self.route, "use": modelli.SITO, "name": ("!=", self.name)}, "title"
		)
		if altro:
			frappe.throw(_("{0} is already at this address").format(frappe.bold(altro)))
		self.allowed_embedding_domains = "\n".join(
			riga.strip() for riga in (self.allowed_embedding_domains or "").splitlines() if riga.strip()
		)
		self.success_url = (self.success_url or "").strip()
		if self.success_url and not DOPO.match(self.success_url):
			# a page to go to, never a script to run
			frappe.throw(_("The page after sending is an address that starts with https:// or /"))

	def on_trash(self):
		if frappe.db.exists(modelli.VERSIONE, {"template": self.name}):
			frappe.throw(
				_(
					"{0} has published versions, and what was filled on them points at them: "
					"switch it off instead"
				).format(frappe.bold(self.title)),
				frappe.LinkExistsError,
			)
