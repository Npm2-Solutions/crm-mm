"""Electronic invoicing for the CRM: any service, healthcare included.

The fiscal rules live in `engine/`, which imports nothing from Frappe and can be
read, tested and audited on its own. Everything that touches the database sits
outside it, so a tax rule is never buried in a controller.
"""
