# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMWebsiteSettings(Document):
	"""What is true of the website as a whole.

	Everything that describes *a* site — brand, menu, footer, SEO, tracking — lives on
	`CRM Web Site`, because there can be several. What is left here is the master switch
	and which one the CRM opens on.
	"""

	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		default_site: DF.Link | None
		enabled: DF.Check
	# end: auto-generated types

	pass
