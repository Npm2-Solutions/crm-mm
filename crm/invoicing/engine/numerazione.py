r"""Numbering of the series.

`Art. 21, c. 2, lett. b)`: "a sequential number identifying it uniquely". Separate
series are **not mandatory** - FAQ n. 33 del 27 novembre 2018 is explicit - but
they remain strongly advisable: two flows that end up in two different retention
systems are easier to govern apart.

**The real constraint comes from the Sistema TS**, not from the tax code:
`numDocumento` takes at most **20 characters** of the alphabet `[A-Za-z0-9_./\-]`.
No spaces, no `#`, no accents, no `:`. A format chosen after the fact turns out in
January not to pass - and by then it is thousands of rows.

So the format is validated **at the first document**, not at the first submission,
and the number is assigned **after the blocking validation and inside the same
transaction** that saves the document.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

#: The alphabet `numDocumento` admits.
NUM_DOCUMENTO_PATTERN = re.compile(r"^[A-Za-z0-9_./\-]{1,20}$")

#: Default format. The two series: `2026/S/128` healthcare, `2026/E/45` SdI.
FORMATO_DEFAULT = "{anno}/{serie}/{numero}"

_PLACEHOLDER = re.compile(r"\{(anno|serie|numero)(?::[^}]*)?\}")


class FormatoNonCompatibile(ValueError):
	"""The series format would not pass the Sistema TS tracciato."""


@dataclass(frozen=True)
class NumeroAssegnato:
	serie: str
	anno: int
	progressivo: int
	numero_documento: str


def valida_formato(formato: str, serie: str = "S", anno: int = 2026) -> None:
	"""Check that the format always produces an acceptable `numDocumento`.

	The check runs on the worst case - a six-digit counter - because document number
	100,000 arrives in November, not in January.
	"""
	if not formato:
		raise FormatoNonCompatibile("the format is empty")
	if not _PLACEHOLDER.search(formato):
		raise FormatoNonCompatibile("the format has no placeholder: use {anno}, {serie} and {numero}")
	if "{numero" not in formato:
		raise FormatoNonCompatibile("the format has no {numero}: the numbering would not be sequential")
	for progressivo in (1, 999_999):
		candidato = componi_senza_controllo(formato, serie, anno, progressivo)
		if not NUM_DOCUMENTO_PATTERN.match(candidato):
			raise FormatoNonCompatibile(
				f"the format would produce {candidato!r}, which the Sistema TS does not accept: "
				r"at most 20 characters of the alphabet [A-Za-z0-9_./\-]. "
				"No spaces, accents, '#' or ':'"
			)


def componi_senza_controllo(formato: str, serie: str, anno: int, progressivo: int) -> str:
	try:
		return formato.format(anno=anno, serie=serie, numero=progressivo)
	except (KeyError, IndexError, ValueError) as exc:
		raise FormatoNonCompatibile(
			f"the format {formato!r} is not usable: {exc}. Only {{anno}}, {{serie}} and "
			"{{numero}} are admitted"
		) from None


def componi(formato: str, serie: str, anno: int, progressivo: int) -> str:
	numero = componi_senza_controllo(formato, serie, anno, progressivo)
	if not NUM_DOCUMENTO_PATTERN.match(numero):
		raise FormatoNonCompatibile(f"number {numero!r} is not compatible with the Sistema TS tracciato")
	return numero


def prossimo(ultimo: int) -> int:
	"""The next counter. Trivial, and it lives here so nobody re-derives it.

	The Agenzia rejected numbering with gaps (Risposta n. 505 del 29 ottobre 2020),
	so a number assigned and then not used is a defect, not a detail: whoever calls
	this has to be inside the transaction that saves the document.
	"""
	return int(ultimo or 0) + 1
