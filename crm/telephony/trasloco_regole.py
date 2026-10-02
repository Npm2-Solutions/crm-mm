# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A number the centre already has, into DottorCloud's space, without a site (doc 52,
sixth part).

- **In the centre's own Twilio account**: it moves into the space with the
  account's codes, given once for that and never kept. Its approved documents are
  copied to the space first (a bundle clone), its address too; then it moves and is
  pointed at DottorCloud.
- **On a SIP trunk** it stays where it is: the trunk takes its calls.
- **With another operator** its calls are forwarded to a number of the centre's in
  DottorCloud, or it is ported to Twilio with Twilio's form and then moved.

The words are English, translated where they are shown.
"""

from __future__ import annotations


def perche_resta(numero: dict) -> str:
	"""Why a number of the account cannot move into the space; '' when it can."""
	if numero.get("trunk_sid"):
		return "It goes to a SIP trunk, which takes its calls: it stays where it is."
	return ""


def cosa_serve(numero: dict) -> tuple[bool, bool]:
	"""What the space needs before the number moves there: its documents (a bundle
	of Twilio's), its address."""
	return bool(numero.get("bundle_sid")), bool(numero.get("address_sid"))


def da_spostare(numeri: list[dict]) -> list[dict]:
	"""The account's numbers as the page lists them, each with why it cannot move
	when it cannot (``reason``): the ones that can first, then by number."""
	righe = [{**numero, "reason": perche_resta(numero)} for numero in numeri]
	return sorted(righe, key=lambda riga: (bool(riga["reason"]), riga.get("phone_number") or ""))
