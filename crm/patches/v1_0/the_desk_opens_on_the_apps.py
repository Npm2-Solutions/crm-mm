# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Frappe 16.50 kept the grid of icons for a site that had one, and invites its
manager to try the apps' screen: DottorCloud ships the apps' screen, its dock and
its sidebar (`crm.marchio.desktop_ad_app`), once. A later choice stays."""


def execute():
	from crm import marchio

	marchio.desktop_ad_app()
