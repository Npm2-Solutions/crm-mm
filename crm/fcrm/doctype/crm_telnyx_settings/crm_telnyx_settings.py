# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's Telnyx account (doc 64).

Connected from Settings > Phone > Telephony > Telnyx (`crm.telephony.telnyx.
collegamento`): the account's key and public key, and what DottorCloud made in it -
its TeXML application, its credential connection, its outbound voice profile, its
messaging profile - sit on permission level 1, the agency's, and are written only
by the connection. What the centre decides - recording, the countries it calls,
the SMS sender, the alerts - is the centre's, on level 0.
"""

import frappe
from frappe import _
from frappe.model.document import Document

from crm.permissions import livelli

TECNICO = "tecnico.integrazioni"


class CRMTelnyxSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		account_owner: DF.Literal["", "Centre", "Agency"]
		allowed_countries: DF.SmallText | None
		api_key: DF.Password | None
		balance_alert: DF.Float
		balance_alert_told: DF.Check
		connected_by: DF.Link | None
		connected_on: DF.Datetime | None
		credential_connection_id: DF.Data | None
		enabled: DF.Check
		managed_account_id: DF.Data | None
		messaging_profile_id: DF.Data | None
		outbound_voice_profile_id: DF.Data | None
		public_key: DF.Data | None
		record_calls: DF.Check
		recording_notice: DF.SmallText | None
		sms_from: DF.Literal["", "Name", "Number"]
		sms_sender_name: DF.Data | None
		sms_sender_number: DF.Data | None
		spend_alert: DF.Float
		spend_alert_told: DF.Data | None
		texml_application_id: DF.Data | None
		verify_webhook_signature: DF.Check
		webhook_base_url: DF.Data | None
	# end: auto-generated types

	def validate(self):
		if self.flags.dal_collegamento:
			return
		from crm.telephony import sms

		sms.valida_il_mittente(self)
		self.valida_gli_avvisi()
		if self.has_value_changed("enabled"):
			# switched on and off by connecting and disconnecting, not by a form
			livelli.verifica_nel_crm(TECNICO, messaggio=_("The agency connects and disconnects Telnyx."))
			if self.enabled:
				from crm.telephony import operatore

				operatore.libero_per(operatore.TELNYX)

	def valida_gli_avvisi(self):
		"""The alerts are amounts, set by whoever pays for the account: on the
		agency's account, the agency."""
		from crm.telephony import consumi_regole as R

		for campo, titolo in (("spend_alert", _("Spend Alert")), ("balance_alert", _("Low Balance Alert"))):
			if not self.has_value_changed(campo):
				continue
			if self.account_owner == "Agency":
				livelli.verifica_nel_crm(
					TECNICO, messaggio=_("The agency pays for this account: it sets the alerts.")
				)
			try:
				soglia = R.soglia(self.get(campo))
			except ValueError as errore:
				frappe.throw(_(str(errore)), title=titolo)
			self.set(campo, float(soglia or 0))
		if self.has_value_changed("spend_alert"):
			# a new amount is told again when the month reaches it
			self.spend_alert_told = ""
		if self.has_value_changed("balance_alert"):
			self.balance_alert_told = 0

	def on_update(self):
		if self.flags.dal_collegamento or not self.enabled:
			return
		# the countries the centre may call, set on Telnyx's outbound voice profile
		# too; what Telnyx does not take now is put back within the hour
		from crm.telephony.telnyx import collegamento

		if self.has_value_changed("allowed_countries"):
			collegamento.allinea_i_paesi(self, avvisa_se_no=True)
		# the centre's name as the messaging profile's sender, when the SMS leave with it
		if any(self.has_value_changed(campo) for campo in ("sms_from", "sms_sender_name")):
			collegamento.allinea_il_mittente(self)
