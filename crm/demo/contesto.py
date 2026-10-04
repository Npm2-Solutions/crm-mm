# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What every part of the demo is handed: today in the centre's clock, the same
chances every time, who loads it, and the ways to date a record back and find what
an earlier part made."""

from __future__ import annotations

import datetime
import random
import unicodedata
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field

import frappe
from frappe.utils import get_datetime, getdate, now_datetime

from crm.demo import dati, registro

#: The same demo every time it is made: the chances are drawn from this seed.
SEME = 2026


@dataclass
class Contesto:
	"""Handed to `Parte.crea`. ``scala`` makes fewer records (the tests ask for a
	small demo); ``utente`` is whoever asked for the demo, who finds things to do
	and notifications of their own in it."""

	utente: str
	scala: float = 1.0
	adesso: datetime.datetime = field(default_factory=now_datetime)
	rng: random.Random = field(default_factory=lambda: random.Random(SEME))
	#: what one part leaves for the next while they run in the same job
	memoria: dict = field(default_factory=dict)
	#: called with a line of progress: the part being made says what it is doing
	avanzamento: object = None

	@property
	def oggi(self) -> datetime.date:
		return self.adesso.date()

	def quanti(self, numero: int) -> int:
		"""``numero`` at the demo's scale, at least one."""
		return max(1, round(numero * self.scala))

	def giorno(self, giorni: int) -> datetime.date:
		return self.oggi + datetime.timedelta(days=giorni)

	def alle(self, giorno: datetime.date, ora: str) -> datetime.datetime:
		ore, minuti = (int(parte) for parte in ora.split(":"))
		return datetime.datetime.combine(giorno, datetime.time(ore, minuti))

	def scegli_pesato(self, coppie) -> object:
		"""One of ``(value, weight)`` pairs."""
		valori = [valore for valore, _peso in coppie]
		pesi = [peso for _valore, peso in coppie]
		return self.rng.choices(valori, weights=pesi, k=1)[0]

	def avanza(self, testo: str) -> None:
		if callable(self.avanzamento):
			self.avanzamento(testo)

	def salva(self) -> None:
		"""What the part made so far, written down and committed: a long part never
		holds everything in one transaction, nor leaves anything out of the register."""
		corrente = registro.raccolta()
		if corrente is not None:
			registro.scrivi(corrente)
		frappe.db.commit()

	# -- who does what -----------------------------------------------------------

	def squadra(self, chiave: str) -> str | None:
		"""The demo user of the team's ``chiave`` ("desk", "giulia"), or whoever loads
		the demo for "io"."""
		if chiave == "io":
			return self.utente
		return registro.trova(f"team.{chiave}")

	@contextmanager
	def come(self, utente: str | None) -> Iterator[None]:
		"""Act as ``utente``: what is made carries their name, as when they make it."""
		from crm.permissions import livelli

		prima = frappe.session.user
		if not utente or utente == prima:
			yield
			return
		# nosemgrep: frappe-setuser — a demo colleague made by the part, never a request's user; given back below
		frappe.set_user(utente)
		livelli.dimentica_cache()
		try:
			yield
		finally:
			# nosemgrep: frappe-setuser — whoever was acting before
			frappe.set_user(prima)
			livelli.dimentica_cache()

	# -- dates back ----------------------------------------------------------------

	def retrodata(self, doctype: str, name: str, quando, chi: str | None = None) -> None:
		"""``name`` was made at ``quando`` by ``chi``, as the lists and the dashboards
		read it; its first version and assignment comments with it."""
		quando = get_datetime(quando)
		valori = {"creation": quando, "modified": quando}
		if chi:
			valori.update({"owner": chi, "modified_by": chi})
		frappe.db.set_value(doctype, name, valori, update_modified=False)
		for tabella, campo_tipo, campo_nome in (
			("Version", "ref_doctype", "docname"),
			("Comment", "reference_doctype", "reference_name"),
			("ToDo", "reference_type", "reference_name"),
			("DocShare", "share_doctype", "share_name"),
		):
			# nosemgrep: frappe-sql-format-injection — table and columns from the tuples above; the values bound
			frappe.db.sql(
				f"""update `tab{tabella}` set creation=%(quando)s, modified=%(quando)s
				where `{campo_tipo}`=%(doctype)s and `{campo_nome}`=%(name)s and creation > %(quando)s""",
				{"quando": quando, "doctype": doctype, "name": name},
			)

	# -- what earlier parts made -----------------------------------------------------

	def ricorda(self, doctype: str, name: str, chiave: str) -> None:
		registro.ricorda(doctype, name, chiave)

	def trova(self, chiave: str) -> str | None:
		return registro.trova(chiave)

	def con_chiave(self, prefisso: str) -> dict[str, str]:
		return registro.con_chiave(prefisso)


def nome_libero(doctype: str, nome: str) -> str:
	"""``nome``, or ``nome (2)``... when the centre already has a record by it: the
	demo never takes the name of something the centre made."""
	if not frappe.db.exists(doctype, nome):
		return nome
	numero = 2
	while frappe.db.exists(doctype, f"{nome} ({numero})"):
		numero += 1
	return f"{nome} ({numero})"


def indirizzo(nome: str, cognome: str, numero: int = 0) -> str:
	"""A demo address: letters only, at the domain that receives nothing."""
	parti = []
	for parola in (nome, cognome):
		piana = unicodedata.normalize("NFKD", parola).encode("ascii", "ignore").decode()
		parti.append("".join(c for c in piana.lower() if c.isalnum()))
	coda = str(numero) if numero else ""
	return f"{parti[0]}.{parti[1]}{coda}@{dati.DOMINIO}"


def giorni_della_settimana() -> tuple[str, ...]:
	return ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def nome_del_giorno(giorno: datetime.date) -> str:
	return giorni_della_settimana()[getdate(giorno).weekday()]
