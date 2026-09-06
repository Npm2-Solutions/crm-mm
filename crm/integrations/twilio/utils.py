import frappe
from frappe.utils import get_url


def get_public_url(path: str | None = None) -> str:
	"""The absolute address Twilio calls back on.

	A site can sit behind a proxy or a development tunnel whose public name is not
	the one the app knows itself by, so the base is configurable. The site URL is
	the fallback for the ordinary case where the two agree.

	Twilio signs the exact URL it calls, so this has to be the address Twilio was
	given — get it wrong and every webhook fails signature validation.
	"""
	base = frappe.db.get_single_value("CRM Twilio Settings", "webhook_base_url")
	return (base or get_url()).rstrip("/") + (path or "")
