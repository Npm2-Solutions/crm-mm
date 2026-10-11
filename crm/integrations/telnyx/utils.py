# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_url


def get_public_url(path: str | None = None) -> str:
	"""The absolute address Telnyx calls back on (doc 65).

	A site can sit behind a proxy or a development tunnel whose public name is not
	the one the app knows itself by, so the base is configurable, as Twilio's is.
	The site URL is the fallback for the ordinary case where the two agree.
	"""
	base = frappe.db.get_single_value("CRM Telnyx Settings", "webhook_base_url")
	return (base or get_url()).rstrip("/") + (path or "")
