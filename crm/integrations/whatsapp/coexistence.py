# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Coexistence webhooks — the half frappe_whatsapp does not know about.

A number in Coexistence keeps being used from the phone, so Meta sends three
extra webhook fields that plain Cloud API integrations never see:

- `smb_message_echoes` — messages the business SENDS from the WhatsApp Business
  app. Without these the CRM would only ever show the customer's side.
- `history` — up to six months of past conversations, delivered in chunks after
  the business approves sharing during onboarding.
- `smb_app_state_sync` — the business's contacts.

frappe_whatsapp only understands the `messages` field, so these are turned into
`WhatsApp Message` documents here.

**Why the rows are written with `db_insert()`**: inserting an Outgoing
`WhatsApp Message` normally makes frappe_whatsapp send it through the API. These
messages have already been sent — from the phone — so running that would deliver
every message twice. `db_insert()` writes the row without the controller.
"""

import json

import frappe

from crm.integrations.api import adopt_unknown_number, get_contact_lead_or_deal_from_number

COEXISTENCE_FIELDS = ("smb_message_echoes", "history", "smb_app_state_sync", "account_update")


def ingest_entry(entry: dict) -> dict:
	"""Handle one webhook entry; returns a small tally for the logs."""
	tally = {"echoes": 0, "history": 0, "contacts": 0}
	for change in entry.get("changes") or []:
		field = change.get("field")
		value = change.get("value") or {}
		if field == "smb_message_echoes":
			tally["echoes"] += ingest_echoes(value)
		elif field == "history":
			tally["history"] += ingest_history(value)
		elif field == "smb_app_state_sync":
			tally["contacts"] += ingest_state_sync(value)
		elif field == "account_update":
			handle_account_update(value)
	return tally


def business_number(value: dict) -> str:
	return ((value.get("metadata") or {}).get("display_phone_number") or "").lstrip("+")


def ingest_echoes(value: dict) -> int:
	"""Messages the business sent from the phone after onboarding."""
	stored = 0
	account = account_of(value)
	for message in value.get("message_echoes") or []:
		if store_message(message, business_number(value), account=account):
			stored += 1
	return stored


def ingest_history(value: dict) -> int:
	"""Past conversations, delivered in chunks after the business opts in."""
	stored = 0
	ours = business_number(value)
	account = account_of(value)
	for chunk in value.get("history") or []:
		for thread in chunk.get("threads") or []:
			for message in thread.get("messages") or []:
				if store_message(message, ours, historical=True, account=account):
					stored += 1
	return stored


def ingest_state_sync(value: dict) -> int:
	"""The business's contacts. Only logged for now — creating CRM leads from a
	whole address book is a decision for the user, not a side effect of connecting."""
	contacts = [row for row in value.get("state_sync") or [] if row.get("type") == "contact"]
	if contacts:
		frappe.logger("whatsapp").info(f"Coexistence: {len(contacts)} contacts announced")
	return len(contacts)


MEDIA_KINDS = ("image", "video", "audio", "document", "sticker")


def account_of(value: dict) -> str:
	"""The `WhatsApp Account` this webhook is about.

	Coexistence rows had no account on them at all. Which is not cosmetic: the
	account is where the token lives, so a message with no account cannot have
	its media fetched, cannot be retried, and belongs to no number when somebody
	asks later which one it was sent from.

	Meta names the number by its `phone_number_id`, and that is the one field a
	`WhatsApp Account` stores about it — there is no number on the doctype.
	"""
	phone_id = (value.get("metadata") or {}).get("phone_number_id") or ""
	if phone_id:
		found = frappe.db.get_value("WhatsApp Account", {"phone_id": phone_id}, "name")
		if found:
			return found
	# a site with one number: it is that one, whatever id the webhook names
	return frappe.db.get_value("WhatsApp Account", {"is_default_incoming": 1}, "name") or (
		frappe.db.get_value("WhatsApp Account", {"is_default_outgoing": 1}, "name") or ""
	)


def media_of(message: dict) -> tuple[str, str]:
	"""(media id, kind) when the message is a file, else `("", "")`.

	A photo, a voice note or a document arrives as an **id**, not as a file: the
	bytes have to be fetched from Meta with the account's token, and they are
	kept for a few days only. Until this existed the id was thrown away and the
	row said `[image]` with nothing attached — a photo sent from the phone was in
	the CRM as the word «image».
	"""
	kind = message.get("type") or ""
	if kind not in MEDIA_KINDS:
		return ("", "")
	return ((message.get(kind) or {}).get("id") or "", kind)


def fetch_media(message: str, media_id: str, kind: str, account: str) -> bool:
	"""Download one message's file and attach it. Runs in the background.

	In the background because this is a webhook: Meta waits for the response and
	retries what it does not get, and two round trips to the Graph API for every
	photo in a six-month history import is not something to make it wait for.
	"""
	if not (message and media_id and account):
		return False
	if frappe.db.get_value("WhatsApp Message", message, "attach"):
		return False

	import requests

	doc = frappe.get_cached_doc("WhatsApp Account", account)
	token = doc.get_password("token")
	headers = {"Authorization": f"Bearer {token}"}
	base = f"{doc.url}/{doc.version}"

	try:
		# what the file is, and the one-time link to it
		about = requests.get(f"{base}/{media_id}/", headers=headers, timeout=30)
		if about.status_code != 200:
			frappe.log_error(
				f"{media_id}: {about.status_code} {about.text[:500]}",
				"WhatsApp: media could not be described",
			)
			return False
		described = about.json()
		link = described.get("url")
		mime = described.get("mime_type") or ""
		if not link:
			return False

		# the link itself is on Meta's lookaside host and needs the same token
		got = requests.get(link, headers=headers, timeout=120)
		if got.status_code != 200:
			frappe.log_error(
				f"{media_id}: {got.status_code}",
				"WhatsApp: media could not be downloaded",
			)
			return False
	except Exception:
		frappe.log_error(frappe.get_traceback(), "WhatsApp: media fetch failed")
		return False

	# private: this is somebody's photo, their voice, their invoice. A public
	# file is a guessable URL that needs no login, and a customer's media has no
	# business being readable by anyone who guesses one.
	stored = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": media_file_name(message, kind, mime, described),
			"attached_to_doctype": "WhatsApp Message",
			"attached_to_name": message,
			"attached_to_field": "attach",
			"content": got.content,
			"is_private": 1,
		}
	).save(ignore_permissions=True)

	frappe.db.set_value("WhatsApp Message", message, "attach", stored.file_url, update_modified=False)
	frappe.db.commit()

	# the bubble was drawn when the row arrived, before the file existed: without
	# this it stays an empty frame until somebody reloads the page
	reference = frappe.db.get_value(
		"WhatsApp Message", message, ["reference_doctype", "reference_name"], as_dict=True
	)
	if reference and reference.reference_doctype:
		frappe.publish_realtime(
			"whatsapp_message",
			{
				"reference_doctype": reference.reference_doctype,
				"reference_name": reference.reference_name,
			},
		)
	return True


def media_file_name(message: str, kind: str, mime: str, described: dict) -> str:
	"""A name a person can read, and an extension the browser can act on.

	A document keeps the name it was sent with — that name is most of what a
	document *is* to whoever receives it. Everything else is named after what it
	is, because `IMG-20260924-WA0007.jpg` tells nobody anything.
	"""
	sent_as = (described.get("file_name") or "").strip()
	if kind == "document" and sent_as:
		return sent_as.replace("/", "-")
	extension = (mime.split(";")[0].split("/")[-1] or "bin").strip() or "bin"
	# mp4 audio is AAC and ogg audio is Opus; both are what the extension says
	return f"{kind}-{message}.{extension}"


def message_body(message: dict) -> tuple[str, str]:
	"""(text, content_type) for the message types worth storing as text."""
	kind = message.get("type") or "text"
	if kind == "text":
		return (message.get("text") or {}).get("body") or "", "text"
	if kind == "reaction":
		return (message.get("reaction") or {}).get("emoji") or "", "reaction"
	if kind in MEDIA_KINDS:
		node = message.get(kind) or {}
		# the caption, and nothing when there is none: the file is the message,
		# and a bubble that says «[image]» under an image is saying it twice.
		#
		# A sticker is filed as an image because `content_type` has no option for
		# one — and it is an image, a small webp. Writing a value the field does
		# not offer would leave a row the Desk cannot open.
		return node.get("caption") or "", ("image" if kind == "sticker" else kind)
	if kind == "location":
		node = message.get("location") or {}
		return node.get("name") or "[location]", "location"
	return f"[{kind}]", kind


def adopt_orphans(number: str, doctype: str, reference: str) -> int:
	"""File the messages to this number that had no record to be filed under.

	A message **sent from the phone** to somebody the CRM has never heard of is
	stored and attached to nothing, because starting a conversation is not the
	same as having a lead: every number an owner writes to from their own phone
	would otherwise become one — the accountant, the supplier, their mother.

	But when that person answers, a lead *is* created, and the conversation ends
	up split: the reply is on the record and the two lines that opened it are
	nowhere. Which reads worse than either half alone — somebody replying to
	nothing.

	So nothing is invented from a one-way message, and nothing is lost either:
	the moment the number has a record, whatever was already said to it goes
	there too.
	"""
	if not number or not doctype or not reference:
		return 0
	orphans = frappe.get_all(
		"WhatsApp Message",
		# filters AND or_filters: unfiled, and to or from this number. The
		# counterparty is `to` on something we sent and `from` on something that
		# arrived, so both have to be asked.
		filters=[["reference_name", "is", "not set"]],
		or_filters=[["to", "=", number], ["from", "=", number]],
		pluck="name",
		limit=200,
	)
	for name in orphans:
		frappe.db.set_value(
			"WhatsApp Message",
			name,
			{"reference_doctype": doctype, "reference_name": reference},
			update_modified=False,
		)
	return len(orphans)


def store_message(message: dict, our_number: str, historical: bool = False, account: str = "") -> bool:
	"""Idempotent by WhatsApp message id. Returns True when a row was written."""
	message_id = message.get("id")
	if not message_id or frappe.db.exists("WhatsApp Message", {"message_id": message_id}):
		return False

	sender = (message.get("from") or "").lstrip("+")
	recipient = (message.get("to") or "").lstrip("+")
	outgoing = bool(our_number) and sender == our_number
	counterparty = recipient if outgoing else sender
	text, content_type = message_body(message)

	values = {
		"doctype": "WhatsApp Message",
		"type": "Outgoing" if outgoing else "Incoming",
		"message_type": "Manual",
		"content_type": content_type,
		"message": text,
		"message_id": message_id,
		"to": counterparty if outgoing else our_number,
		"from": our_number if outgoing else sender,
		"status": "delivered" if historical else "sent",
		"whatsapp_account": account,
	}
	if message.get("context", {}).get("id"):
		values["is_reply"] = 1
		values["reply_to_message_id"] = message["context"]["id"]

	try:
		reference, doctype = get_contact_lead_or_deal_from_number(counterparty)
		if not doctype and not outgoing and not historical:
			# a live message from someone the CRM does not know yet gets a lead;
			# imported history does not, or six months of chats would become
			# hundreds of leads in one import
			reference, doctype = adopt_unknown_number(counterparty, message.get("profile_name")) or (
				None,
				None,
			)
		if doctype and reference:
			values["reference_doctype"] = doctype
			values["reference_name"] = reference
			# and everything already said to this number that had nowhere to go
			adopt_orphans(counterparty, doctype, reference)
	except Exception:
		pass

	known = {df.fieldname for df in frappe.get_meta("WhatsApp Message").fields}
	doc = frappe.new_doc("WhatsApp Message")
	for key, value in values.items():
		if key == "doctype" or key in known:
			doc.set(key, value)
	doc.set_new_name()
	# db_insert: the message already went out from the phone, so the controller
	# must not run and send it again
	doc.db_insert()
	# and because the controller did not run, neither did the hook that tells an
	# open chat to reload: without this the message sits there until a refresh
	# the file itself, which arrives as an id and has to be fetched. Queued
	# rather than fetched here: this runs inside the webhook Meta is waiting on,
	# and a history import would hold it open for two requests per photo.
	media_id, kind = media_of(message)
	if media_id and account:
		frappe.enqueue(
			"crm.integrations.whatsapp.coexistence.fetch_media",
			queue="short",
			message=doc.name,
			media_id=media_id,
			kind=kind,
			account=account,
			enqueue_after_commit=True,
		)

	# the controller did not run, so neither did the hook that keeps the person's
	# last message up to date — and the Inbox is sorted by it
	if doc.get("reference_doctype"):
		from crm.api.conversations import remember

		remember(doc.reference_doctype, doc.reference_name)

	if not historical and doc.get("reference_doctype"):
		frappe.publish_realtime(
			"whatsapp_message",
			{
				"reference_doctype": doc.reference_doctype,
				"reference_name": doc.reference_name,
			},
		)
	return True


# What Meta reports on `account_update`. The second column is the only thing
# that matters when somebody asks, weeks later, why WhatsApp stopped working.
#
# `PARTNER_REMOVED` is the one a person can cause from their own phone, in
# WhatsApp Business → Settings → Account → Business Platform → Disconnect
# Account. Until now it arrived and went into a log line nobody reads, so a
# number could go quiet with the answer sitting in the journal.
ACCOUNT_EVENTS = {
	"PARTNER_ADDED": ("Completed", "The app was connected to this WhatsApp account"),
	"PARTNER_APP_INSTALLED": ("Completed", "The app was installed on this WhatsApp account"),
	"PARTNER_REMOVED": (
		"Cancelled",
		"This WhatsApp account was disconnected from the app. Messages will not "
		"arrive until it is connected again.",
	),
	"PARTNER_APP_UNINSTALLED": ("Cancelled", "The app was removed from this WhatsApp account"),
	# A device change or a re-registration: Meta reconnects it by itself, usually
	# within minutes. Not a fault, but sends fail in between, so it is worth
	# seeing rather than guessing at a few failed messages.
	"ACCOUNT_OFFBOARDED": (
		"In Progress",
		"The phone was re-registered or changed. Meta is reconnecting the account; "
		"sending is suspended until it finishes.",
	),
	"ACCOUNT_RECONNECTED": ("Completed", "The account was reconnected after a device change"),
}


def handle_account_update(value: dict) -> None:
	"""Onboarding milestones and account status changes.

	These arrive long after onboarding, on their own, and they are the only
	warning a CRM gets that a live number has gone away — most of all when the
	business disconnects it from the phone itself.
	"""
	event = value.get("event") or ""
	frappe.logger("whatsapp").info(f"Coexistence account update: {json.dumps(value)[:500]}")

	outcome, what = ACCOUNT_EVENTS.get(event, ("In Progress", ""))
	waba_id = str((value.get("waba_info") or {}).get("waba_id") or "")
	# who pulled the plug, when Meta says: a person on the phone, or the system
	# after a spell of inactivity
	disconnection = value.get("disconnection_info") or {}
	if disconnection:
		what = (
			f"{what} ({disconnection.get('reason') or 'unknown reason'}, "
			f"initiated by {disconnection.get('initiated_by') or 'unknown'})"
		)

	try:
		frappe.get_doc(
			{
				"doctype": "WhatsApp Signup Session",
				"site_url": site_of_waba(waba_id),
				"event": event[:140],
				"waba_id": waba_id,
				"outcome": outcome,
				"error_message": what if outcome == "Cancelled" else "",
				"current_step": "account_update",
				"details": json.dumps(value)[:5000],
			}
		).insert(ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		# an account notice must never cost us the rest of the delivery
		frappe.log_error(frappe.get_traceback(), "WhatsApp: could not record an account update")


def site_of_waba(waba_id: str) -> str:
	"""Whose number this is, so the notice is filed against the right client."""
	if not waba_id:
		return ""
	return frappe.db.get_value("Meta WhatsApp Route", waba_id, "site_url") or ""
