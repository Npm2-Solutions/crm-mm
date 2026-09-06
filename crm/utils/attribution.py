# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Attribution primitives — parsing a visit into marketing dimensions.

Pure functions only: no `frappe`, no database, no request. Everything here takes
strings (a URL, a referrer, a user agent) and returns dictionaries, which is what
makes the ruleset testable without a site.

The model mirrors GoHighLevel's: every visit produces a *session source category*
(Paid Search, Organic Social, …) plus the raw marketing dimensions (source,
medium, campaign, term, content) and whatever click identifiers the ad platforms
appended. Two snapshots of that are kept per contact — the first one ever seen
(first attribution) and the most recent (last attribution) — so a lead can be
credited both to what introduced it and to what closed it.
"""

import re
from urllib.parse import parse_qsl, unquote, urlsplit

# ---------------------------------------------------------------------------
# Vocabularies
# ---------------------------------------------------------------------------

#: Session source categories. Ordered roughly paid → owned → earned → unknown.
SOURCE_CATEGORIES = (
	"Paid Search",
	"Paid Social",
	"Organic Search",
	"Organic Social",
	"Email",
	"SMS",
	"Affiliate",
	"Referral",
	"Direct Traffic",
	"CRM UI",
	"Third Party",
	"Unknown",
)

#: UTM parameters captured verbatim.
UTM_PARAMS = (
	"utm_source",
	"utm_medium",
	"utm_campaign",
	"utm_term",
	"utm_content",
	"utm_id",
)

#: Ad-platform click identifiers, mapped to the category they imply.
#: `fbclid` is deliberately absent — Facebook appends it to *every* outbound link,
#: organic posts included, so on its own it says nothing about paid. It is handled
#: as a special case in `classify()`.
PAID_SEARCH_CLICK_IDS = ("gclid", "gbraid", "wbraid", "msclkid", "dclid", "yclid")
PAID_SOCIAL_CLICK_IDS = ("ttclid", "li_fat_id", "twclid", "epik", "sccid", "rdt_cid", "ctwa_clid")
AFFILIATE_CLICK_IDS = ("irclickid",)

#: Every click id we persist, in one tuple (column order on CRM Visitor Session).
CLICK_ID_PARAMS = (*PAID_SEARCH_CLICK_IDS, "fbclid", *PAID_SOCIAL_CLICK_IDS, *AFFILIATE_CLICK_IDS)

#: Ad-hierarchy parameters. Google/Meta auto-tagging and most agency URL templates
#: use one of these spellings; they land on the session so ad-level reporting can
#: join a lead back to the creative that produced it.
AD_PARAM_ALIASES = {
	"campaign_id": ("campaign_id", "campaignid", "utm_campaign_id", "hsa_cam"),
	"ad_group_id": ("ad_group_id", "adgroupid", "adset_id", "adsetid", "hsa_grp"),
	"ad_id": ("ad_id", "adid", "creative_id", "hsa_ad"),
	"utm_keyword": ("utm_keyword", "keyword", "kw", "hsa_kw"),
	"utm_match_type": ("utm_matchtype", "utm_match_type", "matchtype", "hsa_mt"),
}

#: Referring hosts that mean the visitor came from a search results page.
SEARCH_ENGINE_DOMAINS = (
	"google",
	"bing",
	"yahoo",
	"duckduckgo",
	"yandex",
	"baidu",
	"ecosia",
	"ask",
	"aol",
	"startpage",
	"brave",
	"qwant",
	"naver",
	"seznam",
	"virgilio",
	"libero",
)

#: Referring hosts that mean the visitor came from a social network.
SOCIAL_DOMAINS = (
	"facebook",
	"fb",
	"instagram",
	"linkedin",
	"lnkd",
	"twitter",
	"x.com",
	"t.co",
	"tiktok",
	"pinterest",
	"reddit",
	"youtube",
	"youtu",
	"snapchat",
	"whatsapp",
	"telegram",
	"messenger",
	"threads",
	"quora",
	"tumblr",
	"vk",
	"discord",
	"twitch",
	"nextdoor",
)

#: Referring hosts that mean the click came out of a mail client.
#:
#: Entries with a dot match the host exactly (or a subdomain of it); bare entries
#: match a whole label anywhere in the host. `mail.google.com` has to be spelled
#: in full — `mail.google` is a prefix, and prefixes never match.
WEBMAIL_DOMAINS = (
	"mail.google.com",
	"mail.yahoo.com",
	"mail.live.com",
	"mail.proton.me",
	"mail.zoho.com",
	"protonmail.com",
	"mail.ru",
	"outlook",
	"hotmail",
	"webmail",
	"roundcube",
)

#: `utm_source` values the ad platforms and most templates use for paid traffic.
PAID_SEARCH_SOURCES = (
	"adwords",
	"google_ads",
	"googleads",
	"google-ads",
	"gads",
	"bing_ads",
	"bingads",
	"microsoft_ads",
	"msads",
	"sem",
	"yandex_direct",
)
PAID_SOCIAL_SOURCES = (
	"fb_ad",
	"fb_ads",
	"facebook_ad",
	"facebook_ads",
	"ig_ad",
	"instagram_ad",
	"instagram_ads",
	"meta_ads",
	"linkedin_ad",
	"linkedin_ads",
	"twitter_ad",
	"tiktok_ad",
	"tiktok_ads",
	"pinterest_ad",
	"snapchat_ad",
	"reddit_ads",
)

#: `utm_medium` values, by the category they imply. Matched on a normalized token
#: (lowercased, `-`/space collapsed to `_`).
PAID_SEARCH_MEDIUMS = ("cpc", "ppc", "paidsearch", "paid_search", "sem", "adwords", "google_ads")
PAID_SOCIAL_MEDIUMS = (
	"paid_social",
	"paidsocial",
	"social_paid",
	"social_cpc",
	"cpm",
	"display",
	"banner",
	"retargeting",
	"remarketing",
	"paid",
)
EMAIL_MEDIUMS = ("email", "e_mail", "newsletter", "mail", "edm")
SMS_MEDIUMS = ("sms", "mms", "text", "whatsapp", "wa")
AFFILIATE_MEDIUMS = ("affiliate", "affiliates", "partner", "partnership")
REFERRAL_MEDIUMS = ("referral", "referrer", "link")
ORGANIC_SEARCH_MEDIUMS = ("organic", "organic_search", "seo")
ORGANIC_SOCIAL_MEDIUMS = ("social", "social_organic", "organic_social", "social_media")

#: Substrings that identify automated traffic in a user agent.
BOT_MARKERS = (
	"bot",
	"crawl",
	"spider",
	"slurp",
	"headless",
	"phantom",
	"puppeteer",
	"playwright",
	"lighthouse",
	"pingdom",
	"uptime",
	"monitor",
	"curl",
	"wget",
	"python-requests",
	"httpclient",
	"axios",
	"facebookexternalhit",
	"whatsapp",
	"telegrambot",
	"preview",
	"scanner",
	"archiver",
)


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------


def normalize_token(value: str | None) -> str:
	"""Lowercase, trimmed, with `-`/space folded to `_` — the shape the medium and
	source vocabularies above are written in."""
	if not value:
		return ""
	return re.sub(r"[\s\-]+", "_", str(value).strip().lower())


#: A hostname: dot-separated labels, or bare `localhost`. Anything else that
#: `urlsplit` is willing to call a host (a stray sentence, a file path) is not one.
HOSTNAME_RE = re.compile(r"^(localhost|[a-z0-9]([a-z0-9\-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9\-]*[a-z0-9])?)+)$")


def get_domain(url: str | None) -> str:
	"""Registrable-ish host of `url`, without `www.` and without the port. Empty for
	anything that isn't a URL."""
	if not url:
		return ""
	url = str(url).strip()
	if not url:
		return ""
	if "//" not in url:
		url = "//" + url
	try:
		host = (urlsplit(url).hostname or "").lower()
	except ValueError:
		return ""
	if not HOSTNAME_RE.match(host):
		return ""
	return host[4:] if host.startswith("www.") else host


def get_path(url: str | None) -> str:
	"""Path (with query string) of `url`, for display in a journey timeline."""
	if not url:
		return ""
	try:
		parts = urlsplit(str(url).strip())
	except ValueError:
		return ""
	path = parts.path or "/"
	return f"{path}?{parts.query}" if parts.query else path


def get_query_params(url: str | None) -> dict:
	"""Query string of `url` as a flat dict, lowercased keys, first value wins."""
	if not url:
		return {}
	try:
		query = urlsplit(str(url).strip()).query
	except ValueError:
		return {}
	params = {}
	for key, value in parse_qsl(query, keep_blank_values=False):
		key = key.strip().lower()
		if key and key not in params:
			params[key] = unquote(value).strip()
	return params


def _domain_matches(domain: str, needles) -> bool:
	"""Whether `domain` is (or is a subdomain of) one of `needles`.

	Matching is on whole labels, so `notgoogle.com` never matches `google` while
	`news.google.co.uk` does.
	"""
	if not domain:
		return False
	labels = domain.split(".")
	for needle in needles:
		if "." in needle:
			if domain == needle or domain.endswith("." + needle):
				return True
		elif needle in labels:
			return True
	return False


def is_search_engine(domain: str) -> bool:
	return _domain_matches(domain, SEARCH_ENGINE_DOMAINS)


def is_social_network(domain: str) -> bool:
	return _domain_matches(domain, SOCIAL_DOMAINS)


def is_webmail(domain: str) -> bool:
	return _domain_matches(domain, WEBMAIL_DOMAINS)


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------


def extract(url: str | None, referrer: str | None = None) -> dict:
	"""Marketing dimensions carried by a landing URL and its referrer.

	Returns every UTM parameter, every click id and every ad-hierarchy id present,
	plus the referrer and its domain. Missing values are empty strings, never None,
	so the result can be written straight onto a Frappe document.
	"""
	params = get_query_params(url)
	data = {
		"landing_page": (url or "").strip()[:500],
		"landing_page_path": get_path(url)[:500],
		"referrer": (referrer or "").strip()[:500],
		"referrer_domain": get_domain(referrer),
	}

	for param in UTM_PARAMS:
		data[param] = params.get(param, "")[:140]

	for param in CLICK_ID_PARAMS:
		data[param] = params.get(param, "")[:255]

	for fieldname, aliases in AD_PARAM_ALIASES.items():
		data[fieldname] = next((params[a] for a in aliases if params.get(a)), "")[:140]

	return data


def _click_id(data: dict, params) -> str:
	return next((data[p] for p in params if data.get(p)), "")


def classify(data: dict, own_domains=()) -> str:
	"""The session source category for an extracted visit.

	Rules are evaluated in order and the first match wins — explicit campaign
	tagging outranks inferred signals, and inferred signals outrank the fallback:

	 1. `utm_source` is a known paid-ad token                → Paid Search / Paid Social
	 2. `utm_medium` names a channel                         → that channel
	 3. a paid-search click id (gclid, msclkid, …)           → Paid Search
	 4. an affiliate click id                                → Affiliate
	 5. a paid-social click id (ttclid, li_fat_id, …)        → Paid Social
	 6. `fbclid` without a social referrer                   → Paid Social
	 7. referrer is a webmail host                           → Email
	 8. referrer is a search engine                          → Organic Search
	 9. referrer is a social network                         → Organic Social
	10. any other third-party referrer                       → Referral
	11. a `utm_source` we could not place                    → Referral
	12. nothing at all                                       → Direct Traffic

	Rule 6 is the one judgement call. Facebook appends `fbclid` to every outbound
	link, so it cannot mean "paid" by itself — but a click that arrives with an
	`fbclid` and *no* referrer came from an in-app browser, which is how Meta ads
	behave. With a facebook/instagram referrer present it is an organic post
	(rule 8), which is the accurate reading.

	`own_domains` lists the site's own hosts; a referrer from one of them is an
	internal navigation, not a new source, and is ignored.
	"""
	source = normalize_token(data.get("utm_source"))
	medium = normalize_token(data.get("utm_medium"))

	# 1 — the platform named itself in utm_source
	if source:
		if source in PAID_SEARCH_SOURCES:
			return "Paid Search"
		if source in PAID_SOCIAL_SOURCES:
			return "Paid Social"

	# 2 — the medium names the channel
	if medium:
		if medium in PAID_SEARCH_MEDIUMS:
			return "Paid Search"
		if medium in PAID_SOCIAL_MEDIUMS:
			return "Paid Social"
		if medium in EMAIL_MEDIUMS:
			return "Email"
		if medium in SMS_MEDIUMS:
			return "SMS"
		if medium in AFFILIATE_MEDIUMS:
			return "Affiliate"
		if medium in ORGANIC_SEARCH_MEDIUMS:
			return "Organic Search"
		if medium in ORGANIC_SOCIAL_MEDIUMS:
			return "Organic Social"
		if medium in REFERRAL_MEDIUMS:
			return "Referral"

	# 3-5 — the ad platform tagged the click
	if _click_id(data, PAID_SEARCH_CLICK_IDS):
		return "Paid Search"
	if _click_id(data, AFFILIATE_CLICK_IDS):
		return "Affiliate"
	if _click_id(data, PAID_SOCIAL_CLICK_IDS):
		return "Paid Social"

	referrer_domain = data.get("referrer_domain") or ""
	if referrer_domain and _domain_matches(referrer_domain, own_domains):
		referrer_domain = ""  # our own pages are not a source

	# 6 — see docstring
	if data.get("fbclid") and not is_social_network(referrer_domain):
		return "Paid Social"

	# 7-10 — infer from where the click came from. Webmail goes first: mail.google.com
	# and mail.yahoo.com would otherwise read as search engines and every click out of
	# an inbox would be filed as organic search.
	if referrer_domain:
		if is_webmail(referrer_domain):
			return "Email"
		if is_search_engine(referrer_domain):
			return "Organic Search"
		if is_social_network(referrer_domain):
			return "Organic Social"
		return "Referral"

	# 11 — tagged, but with nothing we recognise
	if source or medium or data.get("utm_campaign"):
		return "Referral"

	# 12
	return "Direct Traffic"


#: Medium written when the visit carried no `utm_medium`, per category — the
#: GA convention, so `source / medium` pairs read the way marketers expect.
IMPLIED_MEDIUM = {
	"Paid Search": "cpc",
	"Paid Social": "paid_social",
	"Organic Search": "organic",
	"Organic Social": "social",
	"Email": "email",
	"SMS": "sms",
	"Affiliate": "affiliate",
	"Referral": "referral",
	"Direct Traffic": "(none)",
	"CRM UI": "(none)",
	"Third Party": "(none)",
	"Unknown": "(none)",
}


def resolve_source_medium(data: dict, category: str) -> tuple[str, str]:
	"""The `source / medium` pair for a visit: whatever the campaign declared, and
	otherwise what the category implies (referring domain, or `(direct)`)."""
	source = (data.get("utm_source") or "").strip()
	if not source:
		source = data.get("referrer_domain") or ""
	if not source:
		source = "(direct)" if category == "Direct Traffic" else "(not set)"

	medium = (data.get("utm_medium") or "").strip() or IMPLIED_MEDIUM.get(category, "(none)")
	return source[:140], medium[:140]


def attribute(url: str | None, referrer: str | None = None, own_domains=()) -> dict:
	"""`extract` + `classify` + `resolve_source_medium` in one call — the whole
	marketing read of a visit, ready to write onto a session."""
	data = extract(url, referrer)
	category = classify(data, own_domains=own_domains)
	source, medium = resolve_source_medium(data, category)
	data.update({"source_category": category, "source": source, "medium": medium})
	return data


# ---------------------------------------------------------------------------
# Client hints
# ---------------------------------------------------------------------------

_BROWSERS = (
	("Edge", r"edg(?:e|a|ios)?/"),
	("Opera", r"opr/|opera"),
	("Samsung Internet", r"samsungbrowser"),
	("Chrome", r"chrome|crios|chromium"),
	("Firefox", r"firefox|fxios"),
	("Safari", r"safari"),
	("Internet Explorer", r"msie|trident"),
)

_OPERATING_SYSTEMS = (
	("iOS", r"iphone|ipad|ipod"),
	("Android", r"android"),
	("Windows", r"windows"),
	("macOS", r"mac os x|macintosh"),
	("Linux", r"linux|x11"),
)


def is_bot(user_agent: str | None) -> bool:
	ua = (user_agent or "").lower()
	return bool(ua) and any(marker in ua for marker in BOT_MARKERS)


def parse_user_agent(user_agent: str | None) -> dict:
	"""Device type, browser and OS from a user agent string.

	Deliberately coarse: enough to answer "mobile or desktop, which browser" in a
	journey timeline, with no dependency on a UA database that would need updating.
	"""
	ua = (user_agent or "").lower()
	if not ua:
		return {"device_type": "", "browser": "", "os": ""}

	if is_bot(ua):
		device_type = "Bot"
	elif "ipad" in ua or ("tablet" in ua and "mobile" not in ua) or ("android" in ua and "mobile" not in ua):
		device_type = "Tablet"
	elif "mobi" in ua or "iphone" in ua or "ipod" in ua:
		device_type = "Mobile"
	else:
		device_type = "Desktop"

	browser = next((name for name, pattern in _BROWSERS if re.search(pattern, ua)), "")
	os_name = next((name for name, pattern in _OPERATING_SYSTEMS if re.search(pattern, ua)), "")
	return {"device_type": device_type, "browser": browser, "os": os_name}


def anonymize_ip(ip: str | None) -> str:
	"""Drop the host part of an address — last octet for IPv4, last 80 bits for
	IPv6 — so a stored IP identifies a network but not a household."""
	ip = (ip or "").strip()
	if not ip:
		return ""
	if ":" in ip:
		groups = ip.split(":")
		return ":".join(groups[:3]) + "::" if len(groups) > 3 else ip
	octets = ip.split(".")
	return ".".join(octets[:3]) + ".0" if len(octets) == 4 else ip
