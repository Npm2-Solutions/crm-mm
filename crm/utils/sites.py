# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Is this URL us?

A Frappe site answers to more than one name. On Frappe Cloud it is created as
`<name>.frappe.cloud` and then given a custom domain, and both keep working —
`get_url()` returns the custom one, `frappe.local.site` is still the original.

Comparing a stored site URL against `get_url()` alone therefore misses the case
that matters most: the hub addressed by its other name. It then tries to reach
itself over HTTP, and fails in the least obvious way possible, because the
container cannot resolve its own public hostname from the inside:

    Failed to resolve 'hub.npm2solutions.com' ([Errno -2] Name or service not known)

That is not a networking problem to route around. It is the signal that the
call should never have left the process.
"""

from urllib.parse import urlparse

import frappe
from frappe.utils import get_url


def site_hostnames() -> set[str]:
	"""Every name this site answers to, lowercased."""
	names = {(urlparse(get_url()).hostname or "").lower()}
	# the bench's own name for the site, which is also a working hostname
	names.add((frappe.local.site or "").lower())
	return {name for name in names if name}


def is_this_site(url: str | None) -> bool:
	if not url:
		return False
	host = (urlparse(url if "//" in url else f"https://{url}").hostname or "").lower()
	return bool(host) and host in site_hostnames()
