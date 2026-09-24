# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Where the Social Planner's profiles come from.

The planner publishes to profiles, and every profile belongs to a source: the
integration that owns the account behind it. Meta is the first — Facebook Pages
and the Instagram business accounts linked to them, through the connection in
Settings → Integrations → Meta — and it is not meant to stay the only one.

A source answers three questions, and nothing else in the planner needs to know
which source it is talking to:

- `status()`   is it connected, and as whom;
- `sync()`     turn its accounts into `CRM Social Account` rows;
- `publish()`  put one post on one of those profiles, and return its id there.

Adding one means writing those three and an entry in `SOURCES`: the settings
page lists it, the composer offers its profiles, the scheduler publishes
through it.
"""

from collections.abc import Callable
from dataclasses import dataclass

import frappe
from frappe import _


@dataclass(frozen=True)
class Source:
	key: str
	label: str
	# the profiles it provides, as `CRM Social Account.platform` spells them
	platforms: tuple[str, ...]
	# the Settings page it is connected from, by the untranslated key the
	# settings modal opens pages with
	settings_page: str
	description: Callable[[], str]
	status: Callable[[], dict]
	sync: Callable[[], dict]
	publish: Callable  # (post, target, account) -> the post's id on the platform


# --- Meta --------------------------------------------------------------------


def meta_description() -> str:
	return _("Facebook Pages and the Instagram business accounts linked to them.")


def meta_status() -> dict:
	from crm.integrations.meta.client import get_app_id, get_app_secret, get_settings
	from crm.integrations.meta.oauth import sync_running

	settings = get_settings()
	return {
		# there is a Meta app to connect to: without one the Connect button has
		# nowhere to go, and only an administrator can add it
		"ready": bool(get_app_id() and get_app_secret()),
		"connected": bool(settings.get_password("user_access_token", raise_exception=False)),
		"account": settings.connected_user_name or "",
		# the Pages are being read from Facebook again, and the profiles follow
		"syncing": sync_running(),
	}


def meta_sync() -> dict:
	"""The profiles, from the Pages the connection already knows.

	Reading the Pages again from Facebook is the connection's job and a slow one
	— a call per Page and one per form, too long for a web request on an account
	that manages many — so it runs in the background, and its last step is this
	same sync. Here the profiles are brought in line at once, from what is stored.
	"""
	from crm.integrations.meta.oauth import start_page_sync, sync_running
	from crm.social.accounts import sync_from_facebook_pages

	result = sync_from_facebook_pages()
	if not sync_running():
		start_page_sync()
	result["refreshing"] = True
	return result


def meta_publish(post, target, account) -> str:
	from crm.social.publisher import publish_to_meta

	return publish_to_meta(post, target, account)


SOURCES = (
	Source(
		key="meta",
		label="Meta",
		platforms=("Facebook", "Instagram"),
		settings_page="Meta connection",
		description=meta_description,
		status=meta_status,
		sync=meta_sync,
		publish=meta_publish,
	),
)


def source_for(platform: str | None) -> Source:
	for source in SOURCES:
		if platform in source.platforms:
			return source
	frappe.throw(_("No source publishes to {0}").format(platform or _("this profile")))
