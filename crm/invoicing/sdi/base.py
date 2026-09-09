# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The transmission channel, as a swappable last mile.

The XML is built in this system. What a channel adds is only the accredited way in
to the Sistema di Interscambio - and there are three honest ways to have one:

* **`export`** - the file is written and handed over. Always available, always
  tested, and the fallback for every failure of the other two;
* **`pec`** - the practice's own certified mailbox writes to the SdI. No provider,
  no contract, no third party holding the documents. The route the original design
  could not take, because it had nowhere to run a mailbox from;
* **`provider`** - an accredited intermediary's REST API.

An adapter answers one question - did it leave, and under what identifier - and
never decides anything fiscal. The guard has already run before any of this.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EsitoInvio:
	"""What a channel can say. Anything more belongs in a notice."""

	canale: str
	inviato: bool
	identificativo: str | None = None
	messaggio: str = ""
	file: str | None = None
	nome_file: str | None = None
	dettagli: dict = field(default_factory=dict)

	def come_dizionario(self) -> dict:
		return {
			"mode": self.canale,
			"sent": self.inviato,
			"identifier": self.identificativo,
			"message": self.messaggio,
			"file": self.file,
			"file_name": self.nome_file,
			**self.dettagli,
		}


class ErroreCanale(Exception):
	"""The channel could not take the document. It says why, in one sentence."""
