# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""What Meta's errors mean, and what to do about them.

Meta answers a refusal with a number and a sentence written for whoever wrote
the integration — «(#131047) Re-engagement message», «Unsupported get request»,
«Invalid parameter». Both halves are useless to the person who pressed the
button: the number is not in the message, the message does not say what to do,
and neither says whether it is their problem or ours.

So every error gets a second sentence. It is not a translation of the first: it
says who has to do what. Where we are not sure, it says that too — a guess
labelled as a guess beats a number nobody can look up.

One table, used everywhere: every Graph call goes through `graph_request`, and
WhatsApp sends — which leave through `frappe_whatsapp` and never touch our
client — are read back out of their own text by `explain_text`.

The codes are Meta's own, from *Cloud API error codes* and *Graph API error
codes*. Where a subcode changes the meaning it has its own row, because 190 on
its own is «log in again» and 190/463 is «the token simply aged».
"""

import re

from frappe import _

# --- Graph API, all products -------------------------------------------------

# nosemgrep: frappe-breaks-multitenancy — the lambda is the point: _() runs per call, not once at import
GRAPH = {
	1: lambda: _(
		"Meta answered with its own generic failure, which usually means their end had a "
		"moment rather than anything being wrong here. Worth trying again; if it keeps "
		"happening it is theirs, not ours."
	),
	2: lambda: _(
		"Meta's service was temporarily unavailable. Nothing to change — the same call "
		"normally works minutes later."
	),
	4: lambda: _(
		"Too many calls to Meta in too short a time: the app's own rate limit, not this "
		"account's. It clears by itself within the hour."
	),
	10: lambda: _(
		"The app does not hold the permission this call needs. It has to be added to the "
		"Meta app and approved — a reconnection alone will not grant it."
	),
	33: lambda: _(
		"Meta cannot see the object this call names. Nearly always the wrong app or a "
		"missing permission rather than a wrong id: an object the app has no right to read "
		"is reported as one that does not exist."
	),
	100: lambda: _(
		"Meta refused a parameter. When it names a field, that field is the problem; when "
		"it names an object, the app most likely cannot see it."
	),
	102: lambda: _("The session with Meta is no longer valid. Reconnect the Meta account from Settings."),
	190: lambda: _(
		"The access token is no longer valid, so nothing can be read or sent until the Meta "
		"account is reconnected from Settings. No amount of retrying will fix it."
	),
	200: lambda: _(
		"Permission refused. On a live app this means the permission was never approved for "
		"it, or the person who connected does not hold the role on the asset that the call "
		"needs — usually Admin on the business portfolio."
	),
	294: lambda: _(
		"This call needs a page access token with management rights, and the one in use is "
		"not one. Reconnect and make sure the page is selected."
	),
	368: lambda: _(
		"The account is temporarily blocked for a policy violation. Meta lifts it by itself, "
		"and nothing in the CRM can shorten it — check the app's Alerts in the Meta dashboard "
		"for what triggered it."
	),
	463: lambda: _("The token has simply expired. Reconnect the Meta account."),
	2635: lambda: _(
		"This endpoint has been retired: the call belongs to an API version Meta no longer "
		"serves. That is ours to fix, not a setting."
	),
	80004: lambda: _(
		"Too many calls for this WhatsApp Business account. It clears by itself; sending the "
		"same volume again will only put it back."
	),
}

# 190 says "log in again" and means different things underneath
# nosemgrep: frappe-breaks-multitenancy — the lambda is the point: _() runs per call, not once at import
GRAPH_SUBCODES = {
	(190, 458): lambda: _(
		"Whoever connected has removed this app from their Facebook account. They have to "
		"connect again and leave it in place."
	),
	(190, 459): lambda: _(
		"Facebook is asking that person to verify their identity before the token works again."
	),
	(190, 460): lambda: _(
		"The password was changed, which invalidates the session. Reconnect the Meta account."
	),
	(190, 463): lambda: _("The token has simply expired. Reconnect the Meta account."),
	(190, 467): lambda: _(
		"The token was invalidated — usually a password change or a security check on that "
		"Facebook account. Reconnect."
	),
	(100, 33): lambda: _(
		"The object exists as far as the id goes, but this app cannot see it. Either it was "
		"created in another app, or the permission that would let this one read it is missing."
	),
	(200, 299): lambda: _(
		"The permission is missing for this specific asset. Being an admin of the business is "
		"not always enough: the page or the account has to be shared with the app too."
	),
}

# --- WhatsApp Cloud API ------------------------------------------------------
#
# The 13xxxx family. These are the ones that actually come up; the rest of the
# list is generic enough that the code itself says as much as a paraphrase would.

# nosemgrep: frappe-breaks-multitenancy — the lambda is the point: _() runs per call, not once at import
WHATSAPP = {
	130429: lambda: _(
		"Too many messages at once for this number's throughput. They are not lost, but the "
		"pace has to come down."
	),
	131000: lambda: _(
		"Meta's generic send failure. Usually momentary; the same message often goes through "
		"on a second attempt."
	),
	131005: lambda: _(
		"Access denied to this WhatsApp Business account. The token belongs to another "
		"account, or this one was never shared with the app."
	),
	131008: lambda: _("A required field was missing from the message. That is ours to fix."),
	131016: lambda: _("WhatsApp's own service was unavailable. Nothing to change; try again."),
	131021: lambda: _("The sender and the recipient are the same number — a number cannot message itself."),
	131026: lambda: _(
		"The message cannot be delivered. The number may not be on WhatsApp at all, or it is "
		"on a version too old, or the recipient has never accepted messages from this "
		"business. Check the number first: this is the code a wrong one produces."
	),
	131031: lambda: _(
		"This WhatsApp Business account is locked — a policy violation or an unpaid balance. "
		"It is settled in the Meta Business dashboard, not here."
	),
	131042: lambda: _(
		"Meta will not send until the business is eligible to pay: a valid payment method on "
		"the WhatsApp Business account, in Business Settings → Payments."
	),
	131045: lambda: _(
		"The number is not registered for sending. It has to complete registration on the "
		"WhatsApp Business account before anything can leave it."
	),
	131047: lambda: _(
		"More than 24 hours have passed since that person's last message, and outside that "
		"window only an approved template may be sent. Send a template, or wait for them to "
		"write first."
	),
	131048: lambda: _(
		"Meta has capped this number for spam: too many messages people did not welcome. It "
		"lifts as the quality rating recovers."
	),
	131049: lambda: _(
		"Meta chose not to deliver this one to protect the recipient's experience — their "
		"limit on marketing messages per person, not a fault of ours."
	),
	131051: lambda: _("That kind of message is not supported. Ours to fix."),
	131052: lambda: _(
		"Meta could not download the media. The file has to be reachable at a public address "
		"and served with the Content-Type of the kind of message it is sent as."
	),
	131053: lambda: _(
		"Meta refused the media itself. Either the format is not one it accepts, or what is "
		"inside does not match what the file claims to be — a `.mp4` holding Opus audio is "
		"the usual case."
	),
	131056: lambda: _(
		"Too many messages between these two numbers in too short a time. It is per pair, so "
		"other conversations are unaffected."
	),
	132000: lambda: _(
		"The template was sent with the wrong number of values: it has a different count of "
		"{{1}} placeholders than were filled in."
	),
	132001: lambda: _(
		"This template does not exist on the account that is sending — a template belongs to "
		"the WhatsApp Business account it was approved on, and to the language it was "
		"approved in. It has to be created again on the number in use."
	),
	132005: lambda: _("The filled-in template came out longer than WhatsApp allows."),
	132007: lambda: _(
		"The template's content breaks Meta's formatting rules — usually a placeholder next "
		"to another placeholder, or one at the very start or end."
	),
	132012: lambda: _("A value does not match the format the template expects for that placeholder."),
	132015: lambda: _(
		"The template is paused: too many people marked messages using it as unwanted. It "
		"resumes by itself, and editing it resets the pause."
	),
	132016: lambda: _(
		"The template has been disabled for good. It cannot be used again — a new one has to be created."
	),
	132068: lambda: _("The flow this template opens is blocked."),
	132069: lambda: _("The flow this template opens is limited at the moment."),
	133000: lambda: _(
		"A previous deregistration of this number never finished. Deregister it fully, then "
		"register it again."
	),
	133004: lambda: _("Meta's server was unavailable. Try again."),
	133005: lambda: _("The two-step verification PIN is wrong."),
	133006: lambda: _(
		"The number has to be verified again before it can be used. That happens in the WhatsApp Manager."
	),
	133008: lambda: _("Too many wrong PIN attempts. Meta blocks further tries for a while."),
	133009: lambda: _("The PIN was tried again too quickly. Wait before the next attempt."),
	133010: lambda: _("The number is not registered on the WhatsApp Business account."),
	133015: lambda: _("The number is in the middle of being deregistered. Wait for it to finish."),
	135000: lambda: _(
		"Meta refused the message without saying why. When it repeats on one recipient it is "
		"usually something about that number rather than the message."
	),
}


def advice(code: int | str | None, subcode: int | str | None = None) -> str:
	"""The second sentence: who has to do what. Empty when we have nothing to add."""

	def number(value):
		try:
			return int(value)
		except (TypeError, ValueError):
			return None

	code, subcode = number(code), number(subcode)
	if code is None:
		return ""
	if subcode is not None and (code, subcode) in GRAPH_SUBCODES:
		return GRAPH_SUBCODES[(code, subcode)]()
	for table in (WHATSAPP, GRAPH):
		if code in table:
			return table[code]()
	return ""


# `(#131047)` as Meta writes it inside a message, and `"code": 131047` as it
# writes it in a payload somebody has stringified.
IN_TEXT = re.compile(r"\(#(\d+)\)|[\"']code[\"']\s*:\s*(\d+)")


def explain_text(text: str) -> str:
	"""Read a code out of an error string and add what to do about it.

	For the errors that never pass through our own Graph client: a WhatsApp send
	leaves through `frappe_whatsapp`, and what comes back is Meta's sentence with
	the code in brackets.
	"""
	text = str(text or "")
	if not text:
		return text
	found = IN_TEXT.search(text)
	if not found:
		return text
	said = advice(found.group(1) or found.group(2))
	return f"{text}\n\n{said}" if said else text
