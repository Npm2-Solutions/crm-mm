# Copyright (c) 2026, NPM2 Solutions Srl and contributors
"""Rapporto di contrasto WCAG fra due colori.
Uso: echo "#0b6f64 #ffffff" | python3 contrasto.py"""

import sys


def lum(h):
	h = h.lstrip("#")
	r, g, b = [int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)]

	def f(c):
		return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

	return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def cr(a, b):
	la, lb = lum(a), lum(b)
	return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


if __name__ == "__main__":
	pairs = [l.split() for l in sys.stdin if l.strip()]
	for p in pairs:
		print(f"{p[0]} on {p[1]}: {cr(p[0],p[1]):.2f}")
