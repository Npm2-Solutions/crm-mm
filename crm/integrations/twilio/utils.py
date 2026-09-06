from frappe.utils import get_url


def get_public_url(path: str | None = None):
	return get_url().split(":8", 1)[0] + path
