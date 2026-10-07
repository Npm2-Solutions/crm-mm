# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Settings > The centre > Your data: the centre's manager takes everything away.

One archive a time, made in a job: every record of DottorCloud's document types
and of the framework's that go with them (`regole.da_esportare`), whole in JSON
lines and as tables for Excel, and - when asked - the files attached to them,
brought back from the archive first. The demo's records stay out. The ZIP is a
private file of whoever asked, the access log says who took what, and it goes
after `GIORNI` days. Health data are in it: only `dati.esporta`, the manager's,
never the agency's for being the agency.
"""

from __future__ import annotations

import json
import os
import zipfile

import frappe
from frappe import _
from frappe.utils import add_days, now, now_datetime, nowdate

from crm.esportazione import regole
from crm.permissions.livelli import richiede

#: The state of the one archive being made, in the cache.
CHIAVE = "crm:esportazione"
#: What the page listens to.
EVENTO = "crm_esportazione"
#: The archive's name starts so; the daily sweep and the page find it by it.
PREFISSO = "dati-del-centro-"
#: Days an archive is kept for whoever asked.
GIORNI = 7
#: Records read at a time.
LOTTO = 500


@frappe.whitelist()
@richiede("dati.esporta")
def get_exports() -> dict:
	"""The archive being made, if any, and the ones ready."""
	pronti = frappe.get_all(
		"File",
		filters={"file_name": ["like", f"{PREFISSO}%"], "is_private": 1, "is_folder": 0},
		fields=["name", "file_name", "file_url", "file_size", "creation", "owner"],
		order_by="creation desc",
	)
	return {
		"running": frappe.cache.get_value(CHIAVE),
		"ready": [
			{
				**pronto,
				"mine": pronto.owner == frappe.session.user,
				"until": add_days(pronto.creation, GIORNI),
			}
			for pronto in pronti
		],
		"days": GIORNI,
	}


@frappe.whitelist(methods=["POST"])
@richiede("dati.esporta")
def start_export(with_files: int | str = 1) -> dict:
	"""Start making the archive, in a job. One at a time for the whole centre."""
	if frappe.cache.get_value(CHIAVE):
		frappe.throw(_("An archive is already being made: it is ready in a few minutes"))
	con_file = frappe.utils.cint(with_files) == 1
	stato = {
		"by": frappe.session.user,
		"started": now(),
		"with_files": con_file,
		"done": 0,
		"total": 0,
	}
	frappe.cache.set_value(CHIAVE, stato, expires_in_sec=6 * 3600)
	# who took the centre's data, and when: the framework's own register of exports
	from frappe.core.doctype.access_log.access_log import make_access_log

	make_access_log(method="crm.esportazione.esporta.start_export", file_type="ZIP", page="Your data")
	frappe.enqueue(
		"crm.esportazione.esporta.prepara",
		queue="long",
		timeout=4 * 3600,
		job_id=f"crm-esportazione-{frappe.local.site}",
		deduplicate=True,
		utente=frappe.session.user,
		con_file=con_file,
		enqueue_after_commit=True,
	)
	return get_exports()


def prepara(utente: str, con_file: bool = True) -> str | None:
	"""Make the archive and keep it as `utente`'s private file."""
	nome = f"{PREFISSO}{now_datetime().strftime('%Y-%m-%d-%H%M')}.zip"
	percorso = frappe.get_site_path("private", "files", nome)
	try:
		_scrivi(percorso, utente, con_file)
		file = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": nome,
				"file_url": f"/private/files/{nome}",
				"is_private": 1,
			}
		)
		file.flags.ignore_permissions = True
		file.insert()
		frappe.db.set_value("File", file.name, "owner", utente, update_modified=False)
		frappe.db.commit()  # nosemgrep: frappe-manual-commit — the archive is ready, whatever follows
		_avvisa(utente, {"state": "ready", "file": file.name})
		return file.name
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="The centre's archive could not be made")
		if os.path.exists(percorso):
			os.remove(percorso)
		_avvisa(utente, {"state": "error"})
		return None
	finally:
		frappe.cache.delete_value(CHIAVE)


def _scrivi(percorso: str, utente: str, con_file: bool) -> None:
	tipi = regole.da_esportare(_metadati())
	demo = _della_demo()
	elenco = {"tipi": {}, "file": 0}
	with zipfile.ZipFile(percorso, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
		zf.writestr(
			"LEGGIMI.txt",
			regole.LEGGIMI.format(marchio=_marchio(), giorno=nowdate()),
		)
		for numero, doctype in enumerate(tipi, start=1):
			_avanza(utente, numero, len(tipi), doctype)
			righe = list(_righe(doctype, demo.get(doctype, set())))
			elenco["tipi"][doctype] = len(righe)
			if not righe:
				continue
			nome = regole.nome_del_tipo(doctype)
			zf.writestr(f"dati/{nome}.jsonl", regole.jsonl(righe))
			intestazione = list(dict.fromkeys(campo for riga in righe for campo in riga))
			zf.writestr(f"tabelle/{nome}.csv", regole.tabella(righe, intestazione))
		if con_file:
			elenco["file"] = _file(zf, set(tipi), demo)
		zf.writestr("elenco.json", json.dumps(elenco, ensure_ascii=False, indent=1))


def _metadati() -> list[dict]:
	app = dict(frappe.get_all("Module Def", fields=["name", "app_name"], as_list=True))
	tipi = frappe.get_all("DocType", fields=["name", "module", "istable", "issingle", "is_virtual"])
	return [{**tipo, "module_app": app.get(tipo.module)} for tipo in tipi]


def _della_demo() -> dict[str, set[str]]:
	"""What the demo made, by document type: it is not the centre's."""
	demo: dict[str, set[str]] = {}
	if not frappe.db.exists("DocType", "CRM Demo Record"):
		return demo
	for riga in frappe.get_all("CRM Demo Record", fields=["ref_doctype", "ref_name"]):
		demo.setdefault(riga.ref_doctype, set()).add(riga.ref_name)
	return demo


def _righe(doctype: str, saltare: set[str]):
	"""Every record of `doctype`, a batch at a time, with its child tables."""
	meta = frappe.get_meta(doctype)
	campi = [
		campo.fieldname
		for campo in meta.fields
		if campo.fieldtype not in regole.SENZA_VALORE or campo.fieldtype in ("Table", "Table MultiSelect")
	]
	figli = {
		campo.fieldname: campo.options
		for campo in meta.fields
		if campo.fieldtype in ("Table", "Table MultiSelect") and campo.options
	}
	inizio = 0
	while True:
		lotto = frappe.get_all(
			doctype,
			fields=["*"],
			order_by="creation asc, name asc",
			limit_start=inizio,
			limit_page_length=LOTTO,
		)
		if not lotto:
			return
		inizio += LOTTO
		lotto = [record for record in lotto if record.name not in saltare]
		nomi = [record.name for record in lotto]
		righe_figlie: dict[tuple[str, str], list] = {}
		for campo, tipo_figlio in figli.items():
			if not nomi:
				break
			for figlio in frappe.get_all(
				tipo_figlio,
				filters={"parent": ["in", nomi], "parenttype": doctype, "parentfield": campo},
				fields=["*"],
				order_by="idx asc",
			):
				righe_figlie.setdefault((figlio.parent, campo), []).append(figlio)
		for record in lotto:
			for campo in figli:
				record[campo] = righe_figlie.get((record.name, campo), [])
			yield regole.riga(record, campi, set(figli))


def _file(zf: zipfile.ZipFile, tipi: set[str], demo: dict[str, set[str]]) -> int:
	"""The files attached to the records in the archive, from the server or brought
	back from the bucket first; never another archive."""
	from crm.archivio import archivio

	quanti = 0
	for file in frappe.get_all(
		"File",
		filters={"is_folder": 0, "attached_to_doctype": ["in", list(tipi) or [""]]},
		fields=["name", "file_name", "file_url", "attached_to_doctype", "attached_to_name"],
		order_by="creation asc",
	):
		if file.attached_to_name in demo.get(file.attached_to_doctype, set()):
			continue
		if (file.file_name or "").startswith(PREFISSO) or not file.file_url:
			continue
		if file.file_url.startswith(("http://", "https://")):
			continue
		try:
			archivio.riporta(file.file_url)
			percorso = frappe.get_doc("File", file.name).get_full_path()
		except Exception:
			frappe.log_error(title="The centre's archive: a file could not be read")
			continue
		if not os.path.exists(percorso):
			continue
		zf.write(
			percorso,
			regole.percorso_del_file(
				file.attached_to_doctype, file.attached_to_name, file.file_name, file.name
			),
		)
		quanti += 1
	return quanti


def _marchio() -> str:
	from crm import marchio

	return marchio.nome()


def _avanza(utente: str, fatti: int, totale: int, doctype: str) -> None:
	stato = frappe.cache.get_value(CHIAVE) or {}
	stato.update({"done": fatti, "total": totale, "step": doctype})
	frappe.cache.set_value(CHIAVE, stato, expires_in_sec=6 * 3600)
	_avvisa(utente, {"state": "running", **stato})


def _avvisa(utente: str, dati: dict) -> None:
	frappe.publish_realtime(EVENTO, dati, user=utente, after_commit=False)


def togli_le_vecchie() -> None:
	"""Daily: an archive goes after `GIORNI` days. It holds the whole centre."""
	limite = add_days(now_datetime(), -GIORNI)
	for nome in frappe.get_all(
		"File",
		filters={"file_name": ["like", f"{PREFISSO}%"], "is_private": 1, "creation": ["<", limite]},
		pluck="name",
	):
		frappe.delete_doc("File", nome, ignore_permissions=True, force=True)
