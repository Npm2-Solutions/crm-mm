# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# Modifications copyright (c) 2026, NPM2 Solutions Srl
# For license information, please see license.txt

"""A Home Action: one entry of the avatar menu every user opens.

A Sales Manager can edit these, and the menu is also opened by System Managers,
so nothing stored here may be something a browser runs. The icon is the name of
a Feather icon, never markup; the route is a path on this site or an http(s)
link, never `javascript:`, `data:` or any other scheme. The menu applies the same
rules when it draws the entries (frontend/src/utils/dropdownItems.js).
"""

import json
import re
from functools import cache
from pathlib import Path
from urllib.parse import urlsplit

import frappe
from frappe import _
from frappe.model.document import Document

# How a browser finds a scheme (WHATWG URL): an ASCII letter, then letters,
# digits, "+", "-" or ".", then a colon. Without one the route is relative.
URL_SCHEME = re.compile(r"^([A-Za-z][A-Za-z0-9+.-]*):")
# Browsers drop tabs and newlines anywhere in a URL: "java\tscript:" still runs.
CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f]")
SAFE_SCHEMES = frozenset(("http", "https"))


@cache
def allowed_icons() -> frozenset[str]:
	"""The names FeatherIcon can draw; the frontend imports the same file."""
	return frozenset(json.loads(Path(__file__).with_name("feather_icons.json").read_text()))


def is_allowed_icon(icon) -> bool:
	return isinstance(icon, str) and icon in allowed_icons()


def is_safe_route(route) -> bool:
	"""A path on this site ("/crm/leads", "#", "?tab=1") or an http(s) URL."""
	if not isinstance(route, str):
		return False
	route = route.strip()
	if not route or CONTROL_CHARACTERS.search(route):
		return False
	scheme = URL_SCHEME.match(route)
	if not scheme:
		return True
	if scheme.group(1).lower() not in SAFE_SCHEMES:
		return False
	try:
		return bool(urlsplit(route).netloc)
	except ValueError:  # an unclosed IPv6 bracket, say
		return False


class CRMDropdownItem(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		hidden: DF.Check
		icon: DF.Code | None
		is_standard: DF.Check
		label: DF.Data | None
		name1: DF.Data | None
		open_in_new_window: DF.Check
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		route: DF.Data | None
		type: DF.Literal["Route", "Separator"]
	# end: auto-generated types

	def validate(self):
		# Runs only when a row is saved on its own (frappe.client.save does that
		# for anyone who can write FCRM Settings); saving the settings skips child
		# controllers, so FCRM Settings calls validate_icon_and_route itself.
		self.validate_icon_and_route()

	def validate_icon_and_route(self):
		if isinstance(self.icon, str):
			self.icon = self.icon.strip()
		if isinstance(self.route, str):
			self.route = self.route.strip()

		# The rejected value stays out of the message: error dialogs render HTML.
		if self.icon and not is_allowed_icon(self.icon):
			frappe.throw(
				_("Row #{0}: the icon must be the name of a Feather icon, like settings").format(self.idx),
				title=_("Invalid icon"),
			)
		if self.route and not is_safe_route(self.route):
			frappe.throw(
				_("Row #{0}: the route must be a path on this site or an http(s) link").format(self.idx),
				title=_("Invalid route"),
			)
