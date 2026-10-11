# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's Telnyx account, from DottorCloud (doc 65).

The same phone as with Twilio (doc 52), through Telnyx: the account connected
once with its API key and its public key; DottorCloud's own TeXML application,
credential connection, outbound voice profile and messaging profile made in it;
the numbers bought with their documents and pointed at DottorCloud; the calls in
the browser; the SMS from the centre's one sender; what the account spends.

- ``regole``, ``errori_regole``: without a site, tested with plain ``unittest``;
- ``cliente``: Telnyx's REST API through ``requests``;
- ``collegamento``: connecting, checking every hour, disconnecting;
- ``numeri``, ``trasloco``, ``verificati``, ``consumi``, ``sms``: what Twilio's
  modules of the same names do, on Telnyx;
- the webhooks are ``crm.integrations.telnyx.api``, the call control
  ``crm.telephony.providers.telnyx``.
"""
