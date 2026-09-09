"""The fiscal engine: pure Python, no Frappe, no database, no network.

This is the part a `commercialista` has to be able to read. It answers four
questions and nothing else:

* what kind of operation is this — `classificazione`
* what does it add up to — `calcolo`
* what number does it carry — `numerazione`
* what does it look like on the wire — `fatturapa`, `sistema_ts`

`professioni` and `codici` are the tables those four consult. They are data, not
logic, and they are meant to be edited when the law moves.
"""

from .calcolo import Calcolo, calcola
from .classificazione import (
	EsitoClassificazione,
	GuardiaSdI,
	RigaDaClassificare,
	classifica,
	guardia_sdi,
)
from .codici import Canale, RegolaSdI, TipoDestinatario
from .professioni import PROFESSIONI, Professione, professione

__all__ = [
	"PROFESSIONI",
	"Calcolo",
	"Canale",
	"EsitoClassificazione",
	"GuardiaSdI",
	"Professione",
	"RegolaSdI",
	"RigaDaClassificare",
	"TipoDestinatario",
	"calcola",
	"classifica",
	"guardia_sdi",
	"professione",
]
