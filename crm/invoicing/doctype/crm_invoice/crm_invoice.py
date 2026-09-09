# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The invoice.

Draft is editable and carries no fiscal number. Submitting assigns the number,
freezes the document and, when it belongs on the SdI, writes the XML. Cancelling
is only possible while nothing has left the building: once a document has been
transmitted it is not cancelled, it is corrected with a credit note, and the
controller says so instead of letting somebody find out later.

The order of `validate` is the order of the domain and not a convenience:
classify, then compute, then check. Computing before classifying would apply a
VAT rate to a line whose regime has not been decided.
"""

from __future__ import annotations

import hashlib

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from crm.invoicing import documento, ts, xml_sdi
from crm.invoicing.engine.classificazione import GuardiaSdI, guardia_sdi
from crm.invoicing.engine.codici import Canale, TipoDestinatario


class CRMInvoice(Document):
	# ------------------------------------------------------------------ lifecycle

	def before_insert(self):
		"""Copy the company's choices onto the document, once.

		It has to happen here and not in `validate`: a Check field is 0 on a new
		document, not empty, so there is no later moment at which "the user did not
		choose" can still be told apart from "the user chose no".
		"""
		self.risolvi_azienda()
		emittente = documento.azienda(self)
		self.fund_mandatory = emittente.get("fund_mandatory")
		self.fund_subject_to_withholding = emittente.get("fund_subject_to_withholding")
		self.recharge_stamp_duty = emittente.get("recharge_stamp_duty")
		# Never towards a natural person: they are not a withholding agent
		# (art. 23, c. 1, DPR 600/73).
		self.apply_withholding = int(
			bool(emittente.get("apply_withholding_by_default"))
			and self.recipient_type != TipoDestinatario.PERSONA_FISICA
		)

	def validate(self):
		self.applica_predefiniti()
		self.compila_da_controparte()
		preparato = documento.prepara(self)
		self._preparato = preparato
		self.controlla(preparato)

	def before_submit(self):
		preparato = getattr(self, "_preparato", None) or documento.prepara(self)
		problemi = documento.blocchi(self, preparato["classificazione"])
		if problemi:
			frappe.throw(
				"<br>".join(problemi),
				title=_("The document cannot be issued"),
			)
		documento.numera(self)
		if self.privacy_opposition and not self.opposition_recorded_on:
			self.opposition_recorded_on = getdate()

	def on_submit(self):
		preparato = getattr(self, "_preparato", None) or documento.prepara(self)
		documento.registra(
			self,
			"issued",
			_("Issued as {0} on the {1} channel").format(self.document_number, self.channel),
			stato=self.channel,
			payload={"total": self.grand_total, "channel": self.channel},
		)
		if self.channel == Canale.SDI:
			self.genera_xml(preparato)
		if self.channel == Canale.PDF_TS:
			self.verifica_tracciato(preparato)

	def before_cancel(self):
		"""An issued document that has already left is corrected, not cancelled."""
		if self.sdi_status in ("inviato", "consegnata", "esito_pa", "decorrenza_termini"):
			frappe.throw(
				_(
					"This invoice has already been transmitted to the Sistema di Interscambio. "
					"It cannot be cancelled: issue a credit note (TD04) that refers to it."
				)
			)
		if self.ts_status in ("inviato", "accolto"):
			frappe.throw(
				_(
					"This invoice has already been reported to the Sistema TS. It cannot be "
					"cancelled: report a variation or a cancellation for it first."
				)
			)

	def on_cancel(self):
		self.ignore_linked_doctypes = ("CRM Invoice Log",)
		documento.registra(self, "cancelled", _("Cancelled before any transmission"))

	# ------------------------------------------------------------------- defaults

	def risolvi_azienda(self):
		if not self.company:
			self.company = frappe.db.get_value(
				"CRM Invoicing Company", {"is_default": 1, "enabled": 1}, "name"
			) or frappe.db.get_single_value("CRM Invoicing Settings", "default_company")
		if not self.company:
			frappe.throw(_("No issuing company: create a CRM Invoicing Company first"))

	def applica_predefiniti(self):
		"""Fill what was left empty. An empty value here means 'not chosen yet'."""
		self.risolvi_azienda()
		emittente = documento.azienda(self)
		for campo, chiave in (
			("fund_type", "fund_type"),
			("fund_rate", "fund_rate"),
			("stamp_duty_mode", "stamp_duty_mode"),
			("withholding_rate", "withholding_rate"),
			("withholding_type", "withholding_type"),
			("payment_reason", "payment_reason"),
		):
			if not self.get(campo):
				self.set(campo, emittente.get(chiave))
		if not self.payment_date:
			self.payment_date = self.posting_date

	def compila_da_controparte(self):
		"""Pull the billing profile from the linked record, once.

		Only empty fields are filled: what is on the invoice is what was confirmed,
		and re-pulling would quietly undo a correction made at the desk.
		"""
		if not (self.party_type and self.party):
			return
		if not frappe.db.exists(self.party_type, self.party):
			return
		record = frappe.get_cached_doc(self.party_type, self.party).as_dict()
		if not self.billing_name:
			self.billing_name = (
				record.get("organization_name")
				or record.get("organization")
				or " ".join(filter(None, [record.get("first_name"), record.get("last_name")])).strip()
				or record.get("name")
			)
		if self.recipient_type == TipoDestinatario.PERSONA_FISICA:
			if not self.first_name:
				self.first_name = record.get("first_name")
			if not self.last_name:
				self.last_name = record.get("last_name")

	# ---------------------------------------------------------------- validation

	def controlla(self, preparato):
		"""Warn while editing, block on submit.

		A draft that refuses to save is a draft nobody keeps: the blocking list runs
		at submit, and here we only surface what is already wrong so it can be fixed
		while the client is still in the room.
		"""
		classificazione = preparato["classificazione"]
		if self.docstatus == 0 and classificazione.tutti_errori:
			frappe.msgprint(
				"<br>".join(classificazione.tutti_errori),
				title=_("This document cannot be issued yet"),
				indicator="orange",
			)

	# --------------------------------------------------------------------- files

	def genera_xml(self, preparato):
		"""Write the FatturaPA file and attach it.

		The findings are recorded rather than raised: an invoice that is fiscally
		valid but not yet transmissible is a real state, and it is better held with
		its reasons attached than refused at the counter.
		"""
		# The progressive is claimed before the file is built, never after: the SdI
		# refuses a file name it has already seen, and it does not forget.
		progressivo = xml_sdi.prossimo_progressivo(self.company)
		xml, nome, rilievi = xml_sdi.genera(self, preparato, progressivo)

		allegato = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": nome,
				"attached_to_doctype": self.doctype,
				"attached_to_name": self.name,
				"attached_to_field": "xml_file",
				"is_private": 1,
				"content": xml,
			}
		).insert(ignore_permissions=True)

		# `scartata` is what the SdI says, not what we suspect: the findings live in
		# the message and the transmission endpoint refuses on the blocking ones.
		self.db_set(
			{
				"xml_file": allegato.file_url,
				"xml_hash": hashlib.sha256(xml.encode()).hexdigest(),
				"sdi_filename": nome,
				"sdi_status": "da_inviare",
				"sdi_message": "\n".join(rilievi) if rilievi else None,
			},
			update_modified=False,
		)
		documento.registra(
			self,
			"sdi_generated",
			"\n".join(rilievi) if rilievi else _("XML generated and validated"),
			stato="rilievi" if rilievi else "ok",
			payload={"file": nome, "findings": len(rilievi)},
		)

	def verifica_tracciato(self, preparato):
		"""Check the Sistema TS rules now, not in January."""
		esito = ts.verifica(self, preparato["azienda"])
		if esito.errori or esito.avvisi:
			documento.registra(
				self,
				"ts_prepared",
				"\n".join(esito.errori + esito.avvisi),
				stato="errori" if esito.errori else "avvisi",
			)
		if esito.errori:
			self.db_set("warnings", "\n".join(esito.errori), update_modified=False)

	# ------------------------------------------------------------------- the guard

	def guardia(self):
		"""Server-side barrier before anything is sent to the SdI.

		Not a UI flag: it holds for every user and every override, and the button
		does not exist in the interface at all. A greyed-out button invites somebody
		to go looking for how to turn it on.
		"""
		preparato = getattr(self, "_preparato", None) or documento.prepara(self)
		try:
			guardia_sdi(preparato["classificazione"])
		except GuardiaSdI as blocco:
			documento.registra(
				self,
				"sdi_blocked",
				blocco.motivo,
				stato="403",
				payload={"lines": blocco.righe},
			)
			raise
