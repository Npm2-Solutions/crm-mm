# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The app's own shells - DottorCloud at /crm, the client area at /area - served
before the framework looks anywhere else for a page of that address.

The framework tries its web forms and its Web Pages with a dynamic route before a
www template, and both lists come from a Redis cache (`redis_cache`) that, while
it is filled again after a cache clear (a migrate, a build, an hour gone),
answers None to a request that asks at the same moment as another: «'NoneType'
object is not iterable», a 500 with nothing in the logs, now and then on any page
of the SPA. Neither list can hold these two addresses anyway: they are the app's.
"""

from frappe.website.page_renderers.template_page import TemplatePage

#: The endpoints of the app's single-page shells (`website_route_rules`).
GUSCI = frozenset({"crm", "area"})


class PaginaDellApp(TemplatePage):
	def can_render(self):
		return self.path in GUSCI and super().can_render()
