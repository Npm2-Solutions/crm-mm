# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""The attribution ruleset — pure logic, no site required.

Every case here is a real-world URL shape: what an ad platform actually appends,
what a referrer actually looks like. The point of testing them one by one is that
the *order* of the rules is the whole design — a rule that fires too early
silently mislabels a channel, and nobody notices until the report is wrong.
"""

import unittest

from crm.utils import attribution as A


class TestExtraction(unittest.TestCase):
	def test_pulls_every_utm_parameter(self):
		url = (
			"https://example.com/prezzi?utm_source=newsletter&utm_medium=email"
			"&utm_campaign=black_friday&utm_term=crm&utm_content=header_link&utm_id=123"
		)
		data = A.extract(url)
		self.assertEqual(data["utm_source"], "newsletter")
		self.assertEqual(data["utm_medium"], "email")
		self.assertEqual(data["utm_campaign"], "black_friday")
		self.assertEqual(data["utm_term"], "crm")
		self.assertEqual(data["utm_content"], "header_link")
		self.assertEqual(data["utm_id"], "123")

	def test_pulls_click_ids_and_ad_hierarchy(self):
		url = "https://example.com/?gclid=abc123&campaignid=777&adgroupid=888&adid=999&keyword=crm+italia"
		data = A.extract(url)
		self.assertEqual(data["gclid"], "abc123")
		self.assertEqual(data["campaign_id"], "777")
		self.assertEqual(data["ad_group_id"], "888")
		self.assertEqual(data["ad_id"], "999")
		self.assertEqual(data["utm_keyword"], "crm italia")

	def test_missing_values_are_empty_not_none(self):
		"""Everything is written straight onto a Frappe document, and a None on a
		Data field is not the same as a blank."""
		data = A.extract("https://example.com/")
		self.assertEqual(data["utm_source"], "")
		self.assertEqual(data["gclid"], "")
		self.assertEqual(data["referrer_domain"], "")

	def test_referrer_domain_drops_www_and_port(self):
		self.assertEqual(A.get_domain("https://www.google.com:443/search?q=x"), "google.com")

	def test_survives_a_url_that_is_not_one(self):
		self.assertEqual(A.get_domain("not a url"), "")
		self.assertEqual(A.get_query_params(""), {})
		self.assertEqual(A.extract(None)["landing_page"], "")

	def test_path_keeps_the_query_string(self):
		self.assertEqual(A.get_path("https://example.com/a/b?x=1"), "/a/b?x=1")
		self.assertEqual(A.get_path("https://example.com"), "/")


class TestDomainMatching(unittest.TestCase):
	def test_matches_subdomains(self):
		self.assertTrue(A.is_search_engine("news.google.co.uk"))
		self.assertTrue(A.is_social_network("m.facebook.com"))

	def test_does_not_match_a_domain_that_merely_contains_the_name(self):
		"""`notgoogle.com` and `google-competitor.io` are not Google."""
		self.assertFalse(A.is_search_engine("notgoogle.com"))
		self.assertFalse(A.is_search_engine("google-competitor.io"))
		self.assertFalse(A.is_social_network("facebookclone.net"))


class TestClassification(unittest.TestCase):
	def classify(self, url, referrer=None, own_domains=()):
		return A.classify(A.extract(url, referrer), own_domains=own_domains)

	# -- paid search --

	def test_gclid_is_paid_search(self):
		self.assertEqual(self.classify("https://x.com/?gclid=abc"), "Paid Search")

	def test_msclkid_is_paid_search(self):
		self.assertEqual(self.classify("https://x.com/?msclkid=abc"), "Paid Search")

	def test_gbraid_and_wbraid_are_paid_search(self):
		"""The iOS-era replacements for gclid. Missing them would push a whole
		platform's traffic into Direct."""
		self.assertEqual(self.classify("https://x.com/?gbraid=abc"), "Paid Search")
		self.assertEqual(self.classify("https://x.com/?wbraid=abc"), "Paid Search")

	def test_utm_medium_cpc_is_paid_search(self):
		self.assertEqual(self.classify("https://x.com/?utm_medium=cpc"), "Paid Search")

	def test_utm_source_adwords_is_paid_search(self):
		self.assertEqual(self.classify("https://x.com/?utm_source=adwords"), "Paid Search")

	# -- paid social --

	def test_utm_source_fb_ad_is_paid_social(self):
		self.assertEqual(self.classify("https://x.com/?utm_source=fb_ad"), "Paid Social")

	def test_paid_social_medium_wins_over_a_search_referrer(self):
		"""An explicitly tagged campaign outranks whatever the browser happened to
		send as a referrer."""
		self.assertEqual(
			self.classify("https://x.com/?utm_medium=paid_social", "https://www.google.com/"),
			"Paid Social",
		)

	def test_tiktok_click_id_is_paid_social(self):
		self.assertEqual(self.classify("https://x.com/?ttclid=abc"), "Paid Social")

	# -- the fbclid judgement call --

	def test_fbclid_with_a_facebook_referrer_is_organic_social(self):
		"""Facebook appends fbclid to every outbound link, organic posts included.
		With a facebook referrer this is someone clicking a post."""
		self.assertEqual(
			self.classify("https://x.com/?fbclid=abc", "https://www.facebook.com/"),
			"Organic Social",
		)

	def test_fbclid_without_a_referrer_is_paid_social(self):
		"""No referrer plus an fbclid is the in-app browser signature of an ad
		click."""
		self.assertEqual(self.classify("https://x.com/?fbclid=abc"), "Paid Social")

	# -- organic and earned --

	def test_search_engine_referrer_is_organic_search(self):
		self.assertEqual(self.classify("https://x.com/", "https://www.google.com/"), "Organic Search")

	def test_social_referrer_is_organic_social(self):
		self.assertEqual(self.classify("https://x.com/", "https://www.linkedin.com/feed"), "Organic Social")

	def test_webmail_referrer_is_email(self):
		self.assertEqual(self.classify("https://x.com/", "https://mail.google.com/"), "Email")

	def test_any_other_referrer_is_a_referral(self):
		self.assertEqual(self.classify("https://x.com/", "https://someblog.it/post"), "Referral")

	def test_utm_medium_email_is_email(self):
		self.assertEqual(self.classify("https://x.com/?utm_medium=email"), "Email")

	def test_utm_medium_sms_is_sms(self):
		self.assertEqual(self.classify("https://x.com/?utm_medium=sms"), "SMS")

	def test_affiliate_click_id_is_affiliate(self):
		self.assertEqual(self.classify("https://x.com/?irclickid=abc"), "Affiliate")

	# -- direct, and what is not direct --

	def test_nothing_at_all_is_direct(self):
		self.assertEqual(self.classify("https://x.com/"), "Direct Traffic")

	def test_our_own_referrer_is_not_a_source(self):
		"""Navigating between our own pages must not register as a referral, or
		every multi-page visit invents a source for itself."""
		self.assertEqual(
			self.classify("https://x.com/b", "https://x.com/a", own_domains=("x.com",)),
			"Direct Traffic",
		)

	def test_an_unrecognised_tag_still_beats_direct(self):
		"""A link someone tagged by hand is not direct traffic, even when the
		vocabulary doesn't place it."""
		self.assertEqual(self.classify("https://x.com/?utm_source=printed_flyer"), "Referral")

	def test_medium_normalisation_handles_hyphens_and_case(self):
		self.assertEqual(self.classify("https://x.com/?utm_medium=Paid-Social"), "Paid Social")


class TestSourceMedium(unittest.TestCase):
	def test_declared_values_are_kept_verbatim(self):
		data = A.attribute("https://x.com/?utm_source=Newsletter&utm_medium=email")
		self.assertEqual(data["source"], "Newsletter")
		self.assertEqual(data["medium"], "email")

	def test_referring_domain_becomes_the_source(self):
		data = A.attribute("https://x.com/", "https://www.google.com/")
		self.assertEqual(data["source"], "google.com")
		self.assertEqual(data["medium"], "organic")

	def test_direct_reads_as_direct(self):
		data = A.attribute("https://x.com/")
		self.assertEqual(data["source"], "(direct)")
		self.assertEqual(data["medium"], "(none)")

	def test_paid_search_without_a_medium_implies_cpc(self):
		data = A.attribute("https://x.com/?gclid=abc")
		self.assertEqual(data["medium"], "cpc")


class TestUserAgent(unittest.TestCase):
	IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1"
	DESKTOP = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
	IPAD = "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Safari/604.1"

	def test_iphone(self):
		parsed = A.parse_user_agent(self.IPHONE)
		self.assertEqual(parsed["device_type"], "Mobile")
		self.assertEqual(parsed["os"], "iOS")
		self.assertEqual(parsed["browser"], "Safari")

	def test_desktop_chrome(self):
		parsed = A.parse_user_agent(self.DESKTOP)
		self.assertEqual(parsed["device_type"], "Desktop")
		self.assertEqual(parsed["os"], "Windows")
		self.assertEqual(parsed["browser"], "Chrome")

	def test_tablet(self):
		self.assertEqual(A.parse_user_agent(self.IPAD)["device_type"], "Tablet")

	def test_empty_user_agent(self):
		self.assertEqual(A.parse_user_agent("")["device_type"], "")

	def test_bots_are_recognised(self):
		self.assertTrue(A.is_bot("Googlebot/2.1 (+http://www.google.com/bot.html)"))
		self.assertTrue(A.is_bot("HeadlessChrome/120"))
		self.assertFalse(A.is_bot(self.DESKTOP))


class TestIPAnonymisation(unittest.TestCase):
	def test_ipv4_loses_the_last_octet(self):
		self.assertEqual(A.anonymize_ip("192.168.1.42"), "192.168.1.0")

	def test_ipv6_keeps_only_the_network(self):
		self.assertEqual(A.anonymize_ip("2001:db8:85a3:1234:5678:8a2e:370:7334"), "2001:db8:85a3::")

	def test_empty_stays_empty(self):
		self.assertEqual(A.anonymize_ip(""), "")
		self.assertEqual(A.anonymize_ip(None), "")


if __name__ == "__main__":
	unittest.main()
