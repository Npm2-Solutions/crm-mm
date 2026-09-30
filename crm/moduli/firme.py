# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The signatures the CRM does not give itself: a provider, or paper.

**A provider** (design.md, "Un adattatore, più fornitori"). The simple signature
is ours; the advanced one (an SMS code from the provider, after the person was
identified with a document) and the qualified one (the practitioner's remote
signature) come from a provider. Whoever it is, it does five things:

1. ``crea``: an envelope for this PDF and these signers;
2. ``pagina``: where one signer signs;
3. ``evento``: what its webhook says (signed, declined, expired), once it has
   checked the call is really from it;
4. ``firmato``: the signed PDF (PAdES): the document that proves the signature;
5. ``prove``: its own audit trail, kept next to the form.

A provider is a class registered with `registra_fornitore`; the centre picks one
in `CRM Signature Settings`, where its keys live (the agency's, permlevel 1). The
form sent to a provider waits, and is signed when the webhook says so: the PDF
it keeps is the provider's, since converting it would break the signature.

**Paper** needs nobody: the operator prints the form, the person signs it, the
scan is uploaded and the operator attests it is a true copy of the original
(`compilazioni.firma_su_carta`).
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit

IMPOSTAZIONI = "CRM Signature Settings"

_fornitori: dict[str, type[FornitoreFirma]] = {}


class FornitoreFirma:
	"""What a signature provider does for the CRM. Subclass it and register it."""

	#: The name the centre picks in the settings.
	nome = ""
	#: The levels it gives: ("advanced",) or ("advanced", "qualified").
	livelli: tuple[str, ...] = ("advanced",)

	def __init__(self, impostazioni=None):
		self.impostazioni = impostazioni

	def crea(self, doc, pdf: bytes, firmatari: list[dict]) -> dict:
		"""An envelope for ``pdf``: ``{"reference": ..., "signers": [{"field", "url"}]}``.
		Each signer is ``{"field", "name", "email", "phone", "level"}``."""
		raise NotImplementedError

	def pagina(self, riferimento: str, campo: str) -> str:
		"""Where the signer of ``campo`` signs, again: a link can be asked twice."""
		raise NotImplementedError

	def evento(self, richiesta) -> dict:
		"""What the webhook says, once checked: ``{"reference", "event", "signers":
		[{"field", "signed_at", "ip_address"}]}``, ``event`` one of signed,
		declined, expired. Raises if the call is not the provider's."""
		raise NotImplementedError

	def firmato(self, riferimento: str) -> bytes:
		"""The signed PDF."""
		raise NotImplementedError

	def prove(self, riferimento: str) -> bytes | None:
		"""The provider's audit trail (a PDF, usually), if it gives one."""
		return None


def registra_fornitore(classe: type[FornitoreFirma]) -> type[FornitoreFirma]:
	"""Make a provider available to the settings. Usable as a decorator."""
	if not classe.nome:
		raise ValueError("a signature provider needs a name")
	_fornitori[classe.nome] = classe
	return classe


def fornitori() -> list[str]:
	return sorted(_fornitori)


def attivo() -> FornitoreFirma | None:
	"""The centre's provider, if one is chosen, switched on and known."""
	if not frappe.db.exists("DocType", IMPOSTAZIONI):
		return None
	impostazioni = frappe.get_cached_doc(IMPOSTAZIONI)
	if not impostazioni.get("enabled") or not impostazioni.get("provider"):
		return None
	classe = _fornitori.get(impostazioni.provider)
	return classe(impostazioni) if classe else None


def dai_livello(livello: str) -> FornitoreFirma | None:
	"""The provider that gives ``livello``, if the centre has one."""
	fornitore = attivo()
	return fornitore if fornitore and livello in fornitore.livelli else None


def serve_il_fornitore(schema_campi: list[dict]) -> list[str]:
	"""The levels of the signature fields a finger cannot give."""
	return sorted(
		{
			campo.get("level")
			for campo in schema_campi
			if campo.get("type") == "signature" and (campo.get("level") or "simple") != "simple"
		}
	)


@frappe.whitelist()
def get_provider() -> dict:
	"""Whether the centre signs with a provider, and which levels it gives."""
	fornitore = attivo()
	return {
		"name": fornitore.nome if fornitore else None,
		"levels": list(fornitore.livelli) if fornitore else [],
		"available": fornitori(),
	}


def nessun_fornitore() -> None:
	frappe.throw(
		_("The centre has no signature provider yet: sign it on paper, or set one up"),
		title=_("No signature provider"),
	)


# nosemgrep: guest-whitelisted-method — the provider's own check of the call (evento) is the credential
@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=600, seconds=60 * 60)
def webhook(provider: str | None = None) -> dict:
	"""What the centre's provider says about an envelope: signed, declined,
	expired. The provider checks its own call (a signature, a secret); a form
	it does not know, or one already closed, is left as it is."""
	from crm.moduli import compilazioni

	fornitore = attivo()
	if not fornitore or (provider and provider != fornitore.nome):
		frappe.throw(_("No such signature provider here"), frappe.PermissionError)
	esito = fornitore.evento(frappe.request)
	nome = frappe.db.get_value(
		compilazioni.MODULO,
		{"provider": fornitore.nome, "provider_reference": esito.get("reference")},
		"name",
	)
	if not nome:
		return {"ok": True, "known": False}
	compilazioni.dal_fornitore(frappe.get_doc(compilazioni.MODULO, nome), fornitore, esito)
	return {"ok": True, "known": True}
