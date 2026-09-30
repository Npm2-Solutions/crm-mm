# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""A line of the clinical record: a visit or a note, in words and attachments.

It is its author's while it is a draft. Signed, it is not rewritten any more: it
is added to, with an addendum that points at it - a clinical record is
integrated, never corrected in place. Who reads it is `crm.clinica.cartella`'s
business, and every read from the CRM leaves a trace in the access log.
"""

import json

import frappe
from frappe import _
from frappe.utils import now_datetime

from crm.clinica.base import DocumentoClinico

SOLO_IO = "Only me"


class ClinicRecord(DocumentoClinico):
	def validate(self):
		if self.is_new():
			self.practitioner = self.practitioner or frappe.session.user
		if self.addendum_to:
			firmato = frappe.db.get_value(
				"Clinic Record", self.addendum_to, ["lead", "docstatus"], as_dict=True
			)
			if not firmato or firmato.lead != self.lead:
				frappe.throw(_("An addendum belongs to the same patient's record"))
			if firmato.docstatus != 1:
				frappe.throw(_("A draft is edited, not added to"))

	def before_submit(self):
		if self.template_version:
			self._chiudi_la_scheda()
		allegati = frappe.db.exists(
			"File", {"attached_to_doctype": self.doctype, "attached_to_name": self.name}
		)
		if (
			not frappe.utils.strip_html(self.content or "").strip()
			and not allegati
			and not self.template_version
		):
			frappe.throw(_("A signed record says something: write what happened, or attach it"))
		self.signed_on = now_datetime()

	def on_submit(self):
		from crm.clinica import referto, sintesi

		# a visit's report, made once and filed in the archive; a note has none
		if self.kind == "Visit":
			referto.genera_e_allega(self)
			self._in_archivio()
		# the answers of a sheet that fill the patient's summary, proposed
		if self.template_version:
			schema, risposte, stato = self._scheda()
			sintesi.proponi(self, schema, risposte, stato)

	def _in_archivio(self):
		"""Filing the report does not undo the signature: the log says why it failed."""
		from crm.clinica import archivio

		frappe.db.savepoint("referto_in_archivio")
		try:
			archivio.dal_referto(self)
		except Exception:
			frappe.db.rollback(save_point="referto_in_archivio")
			frappe.log_error(
				title=f"Report of {self.name} not filed",
				reference_doctype=self.doctype,
				reference_name=self.name,
			)

	def _scheda(self):
		from crm.moduli import modelli
		from crm.moduli import schema as S

		versione = frappe.get_cached_doc(modelli.VERSIONE, self.template_version)
		schema = modelli.carica_schema(versione.schema)
		risposte = json.loads(self.answers or "{}") if isinstance(self.answers, str) else (self.answers or {})
		return schema, risposte, S.valuta(schema, risposte)

	def _chiudi_la_scheda(self):
		"""A sheet is checked as a form is when the visit is signed, and what it
		said is frozen with its hash."""
		from crm.moduli import compilazioni, modelli

		versione = frappe.get_cached_doc(modelli.VERSIONE, self.template_version)
		schema, risposte, _stato = self._scheda()
		puliti, stato = compilazioni.controlla(schema, risposte)
		self.answers = json.dumps(puliti, ensure_ascii=False)
		self.alerts = json.dumps(stato["stops"], ensure_ascii=False)
		self.answers_hash = compilazioni.impronta_risposte(versione.schema_hash, puliti)

	def before_cancel(self):
		frappe.throw(_("A signed record is not taken back: add an addendum to it"))
