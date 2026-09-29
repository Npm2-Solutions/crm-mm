# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Who one person is to another, and who acts for whom: the rules, without a site.

**One row per pair.** A link is stored once, from the side of the person who is
looked after: `person` is Luca, `related_person` is Maria, and `relation` says what
Maria is to Luca, "Parent". Read from Maria's page the same row says that Luca is
her "Child" (`inversa`). Two rows for one pair would disagree sooner or later.

**Who acts for whom.** The related person may do three things for the person: pay
their invoices, book for them and get the messages about it, act for them - sign
and decide, as a parent does for a minor child or a guardian for their ward. Always
in the stored direction, which is why the row is written from the side of whoever
is acted for. Between partners, where nobody acts for anybody, the side is the one
it was written from.

**The name decides, with the contact.** A family shares an email and a phone: the
contact finds its owner, and the name says whether the booking is theirs or for
somebody they book for. Names are compared by their words, the way the invoice
already did (`stesso_nome`): "Mario Rossi", "Rossi Mario" and "Mario" are one
person, "Luca Rossi" is another. Never by likeness: "Luca" and "Lucia" are a brother
and a sister, and a visit written under the wrong one is the worst mistake a
clinic's software can make. A second record for the same person is merged in a
minute; a record written into the wrong person is noticed when it is too late.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

GENITORE = "Parent"
FIGLIO = "Child"
TUTORE = "Legal guardian"
TUTELATO = "Ward"
PARTNER = "Partner"
FAMILIARE = "Family member"
ALTRO = "Other"

#: What the related person is to the person, and what the person is to them.
INVERSE = {
	GENITORE: FIGLIO,
	FIGLIO: GENITORE,
	TUTORE: TUTELATO,
	TUTELATO: TUTORE,
	PARTNER: PARTNER,
	FAMILIARE: FAMILIARE,
	ALTRO: ALTRO,
}
RELAZIONI = tuple(INVERSE)

#: What the related person may do for the person: the three flags of a row.
PAGA = "pays"
PRENOTA = "books"
RAPPRESENTA = "represents"
AZIONI = (PAGA, PRENOTA, RAPPRESENTA)

#: Who acts for whom, as a person's page reads a link.
LORO_PER_ME = "them_for_me"
IO_PER_LORO = "me_for_them"
NESSUNO = ""
VERSI = (LORO_PER_ME, IO_PER_LORO, NESSUNO)


def inversa(relazione: str | None) -> str:
	if relazione not in INVERSE:
		raise ValueError(f"unknown relation: {relazione!r}")
	return INVERSE[relazione]


@dataclass(frozen=True)
class Legame:
	"""A link as it is stored: `collegata` is `relazione` to `persona`, and acts for them."""

	persona: str
	collegata: str
	relazione: str


def orienta(io: str, altro: str, relazione: str, verso: str = NESSUNO) -> Legame:
	"""A link as a person's page writes it, turned the way it is stored.

	``relazione`` is what ``altro`` is to ``io`` - the page asks "who are they to
	Maria?" - and ``verso`` who acts for whom. When ``io`` is the one acting, the row
	is written from the other's side, and the relation turns with it.
	"""
	if not io or not altro:
		raise ValueError("a link needs two people")
	if io == altro:
		raise ValueError("a person is not linked to themselves")
	if verso not in VERSI:
		raise ValueError(f"unknown direction: {verso!r}")
	if verso == IO_PER_LORO:
		return Legame(persona=altro, collegata=io, relazione=inversa(relazione))
	inversa(relazione)
	return Legame(persona=io, collegata=altro, relazione=relazione)


def dal_lato_di(riga: dict, io: str) -> dict:
	"""A stored row as ``io``'s page reads it: the other one, what they are to
	``io``, and who acts for whom."""
	agisce = any(riga.get(azione) for azione in AZIONI)
	if riga.get("person") == io:
		return {
			"other": riga.get("related_person"),
			"relation": riga.get("relation"),
			"acts": LORO_PER_ME if agisce else NESSUNO,
		}
	if riga.get("related_person") == io:
		return {
			"other": riga.get("person"),
			"relation": inversa(riga.get("relation")),
			"acts": IO_PER_LORO if agisce else NESSUNO,
		}
	raise ValueError(f"{io!r} is not in this link")


def azioni(valori: dict, verso: str) -> dict:
	"""The three flags to store: none when nobody acts for anybody."""
	return {azione: 1 if verso and valori.get(azione) else 0 for azione in AZIONI}


# ------------------------------------------------------------------- the names


def parole(*testi: str | None) -> frozenset[str]:
	"""The words of a name: lower case, without accents or punctuation."""
	insieme = " ".join(t for t in testi if t)
	senza_accenti = unicodedata.normalize("NFKD", insieme)
	senza_accenti = "".join(c for c in senza_accenti if not unicodedata.combining(c))
	return frozenset(re.findall(r"[a-z]+", senza_accenti.lower()))


def stesso_nome(uno: str | None, altro: str | None) -> bool:
	"""One name holds all the words of the other: the same person, written more or
	less completely. A first name that is not there at all is somebody else."""
	a, b = parole(uno), parole(altro)
	if not (a and b):
		return False
	return a <= b or b <= a


_EMAIL = re.compile(r"\S+@\S+")
_NUMERO = re.compile(r"^[\s+()./-]*\d[\d\s+()./-]*$")


def nome_noto(nome: str | None) -> bool:
	"""Whether a record's name says who they are.

	A record made from a bare email or number carries it as its name. That says
	nothing, and a booking with a real name on the same contact is theirs.
	"""
	nome = (nome or "").strip()
	if not nome or _EMAIL.search(nome) or _NUMERO.match(nome):
		return False
	return bool(parole(nome))


def scegli(nome: str | None, candidati: Iterable[tuple[str, str | None]]) -> str | None:
	"""Which of ``candidati`` - ``(record, their name)`` - a typed name means.

	The one with exactly the same words, if one alone has them; otherwise the one
	whose name holds or is held by it, if one alone does. Two ("Rossi", with two
	children called Rossi) is nobody: a new record is safer than a guess.
	"""
	gia = set()
	uguali, simili = [], []
	cercate = parole(nome)
	for record, suo_nome in candidati:
		if record in gia:
			continue
		gia.add(record)
		if cercate and parole(suo_nome) == cercate:
			uguali.append(record)
		elif stesso_nome(nome, suo_nome):
			simili.append(record)
	if len(uguali) == 1:
		return uguali[0]
	if not uguali and len(simili) == 1:
		return simili[0]
	return None


def per_chi(
	nome: str | None,
	titolare: tuple[str, str | None] | None,
	collegate: Iterable[tuple[str, str | None]],
) -> str | None:
	"""The record a booking with this name goes to, given who owns its contact.

	The owner, when the name is theirs, or says nothing, or theirs says nothing; one
	of the people linked to them, when the name is one of theirs; ``None`` for
	somebody new - a new record, linked to the owner.
	"""
	if not titolare:
		return None
	record, suo_nome = titolare
	if not parole(nome) or not nome_noto(suo_nome) or stesso_nome(nome, suo_nome):
		return record
	return scegli(nome, collegate)


def dividi(nome: str | None) -> tuple[str, str]:
	"""First name and surname of a name typed in one box: the first word, and the rest."""
	parti = (nome or "").split(maxsplit=1) or [""]
	return parti[0], parti[1] if len(parti) > 1 else ""


#: Of age at eighteen: before, a parent or a guardian signs and decides.
MAGGIORE_ETA = 18


def eta(nascita: date | None, oggi: date) -> int | None:
	"""Full years at ``oggi``: a birthday not reached yet this year does not count."""
	if not nascita:
		return None
	anni = oggi.year - nascita.year
	if (oggi.month, oggi.day) < (nascita.month, nascita.day):
		anni -= 1
	return anni


def minorenne(nascita: date | None, oggi: date) -> bool | None:
	"""A minor, of age, or not known: the date of birth comes from the codice fiscale."""
	anni = eta(nascita, oggi)
	return None if anni is None else anni < MAGGIORE_ETA
