# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""Credentials never reach an error message — pure, runs with plain ``unittest`` too."""

import unittest

from crm.integrations.meta.redact import redact

# what `requests` says when graph.facebook.com cannot be reached
CONNECTION_ERROR = (
	"HTTPSConnectionPool(host='graph.facebook.com', port=443): Max retries exceeded with url: "
	"/v23.0/1234/feed?message=Ciao&access_token=EAABsecretToken&appsecret_proof=abc123def "
	"(Caused by NewConnectionError('Failed to establish a new connection'))"
)


class TestRedact(unittest.TestCase):
	def test_the_token_and_its_proof_are_hidden(self):
		text = redact(CONNECTION_ERROR)
		self.assertNotIn("EAABsecretToken", text)
		self.assertNotIn("abc123def", text)
		self.assertIn("access_token=***", text)
		self.assertIn("appsecret_proof=***", text)

	def test_the_rest_of_the_sentence_survives(self):
		text = redact(CONNECTION_ERROR)
		self.assertIn("Max retries exceeded", text)
		self.assertIn("/v23.0/1234/feed?message=Ciao&", text)
		self.assertIn("Caused by NewConnectionError", text)

	def test_the_token_exchange_keeps_its_secret(self):
		text = redact(
			"url: /v23.0/oauth/access_token?client_id=42&client_secret=s3cr3t&code=AQDcode&redirect_uri=x"
		)
		self.assertNotIn("s3cr3t", text)
		self.assertNotIn("AQDcode", text)
		self.assertIn("client_id=42", text)
		self.assertIn("redirect_uri=x", text)

	def test_an_app_token_is_hidden_whole(self):
		text = redact("url: /v23.0/debug_token?input_token=EAAuser&access_token=42|appsecret")
		self.assertNotIn("appsecret", text)
		self.assertNotIn("EAAuser", text)

	def test_encoded_and_escaped_urls_too(self):
		self.assertNotIn("SECRET", redact("next=%2Fme%3Faccess_token=SECRET"))
		self.assertNotIn("SECRET", redact("next=%2Fme%3Faccess_token%3DSECRET%26limit%3D5"))
		self.assertIn("%26limit%3D5", redact("next=%2Fme%3Faccess_token%3DSECRET%26limit%3D5"))
		self.assertNotIn("SECRET", redact("<a href='/me?a=1&amp;access_token=SECRET'>"))

	def test_a_word_that_only_looks_like_a_parameter_is_left_alone(self):
		self.assertEqual(redact("error code=190 from Meta"), "error code=190 from Meta")

	def test_nothing_in_nothing_out(self):
		self.assertEqual(redact(None), "")
		self.assertEqual(redact(""), "")
