# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Keep credentials out of error messages.

Every Graph call authenticates in its query string — `access_token` and
`appsecret_proof`, and on the token exchanges `client_secret` itself. When the
connection fails before Meta answers (DNS, a refused connection, a timeout),
`requests` describes the failure with the URL it was trying to reach, query
string included. That sentence then travelled on: into the error a Social
Planner post shows to whoever wrote it, into the hub page a client reads while
connecting WhatsApp, into the error log.

Pure — no Frappe — so it runs with plain `unittest`.
"""

import re

SECRET_PARAMS = (
	"access_token",
	"appsecret_proof",
	"client_secret",
	"fb_exchange_token",
	"input_token",
	"code",
)

# `name=value` as it appears in a URL: after `?` or `&` — plain, percent-encoded
# or HTML-escaped — up to the next separator
_IN_URL = re.compile(
	r"(?P<key>(?:[?&]|%3F|%26|&amp;)(?:" + "|".join(SECRET_PARAMS) + r")(?:=|%3D))"
	r"(?:(?!%26)[^&\s'\")>])+",
	re.IGNORECASE,
)


def redact(text) -> str:
	"""`text` with the value of every credential in it replaced by `***`."""
	return _IN_URL.sub(r"\g<key>***", str(text or ""))
