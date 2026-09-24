# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The look of the public booking page: pure helpers, tested without a database.

The practice picks one colour; the page needs three from it — the colour itself
for buttons and selections, a text colour that stays readable on top of it, and
a pale tint for soft backgrounds.
"""

from __future__ import annotations

import re

_HEX = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def hex_colour(value) -> str | None:
	"""``#RRGGBB`` in lower case, or ``None`` for anything that is not a colour."""
	match = _HEX.match(str(value or "").strip())
	if not match:
		return None
	digits = match.group(1)
	if len(digits) == 3:
		digits = "".join(c * 2 for c in digits)
	return f"#{digits.lower()}"


def _luminance(colour: str) -> float:
	"""WCAG relative luminance of a ``#rrggbb`` colour."""

	def channel(pair: str) -> float:
		c = int(pair, 16) / 255
		return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

	r, g, b = (channel(colour[i : i + 2]) for i in (1, 3, 5))
	return 0.2126 * r + 0.7152 * g + 0.0722 * b


def readable_ink(colour: str) -> str:
	"""White or near-black: whichever reads better on ``colour``."""
	lum = _luminance(colour)
	on_white = 1.05 / (lum + 0.05)
	on_black = (lum + 0.05) / (_luminance("#111111") + 0.05)
	return "#ffffff" if on_white >= on_black else "#111111"


def accent_vars(value) -> dict[str, str]:
	"""The CSS variables of the page for a chosen colour; empty when there is none."""
	colour = hex_colour(value)
	if not colour:
		return {}
	return {
		"--accent": colour,
		"--accent-ink": readable_ink(colour),
		"--accent-soft": f"color-mix(in srgb, {colour} 14%, transparent)",
	}
