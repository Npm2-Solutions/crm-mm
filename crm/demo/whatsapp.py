# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A WhatsApp message to a person of the demo data stays in the conversation and is
never handed to Meta (`crm.demo.guardie`). Loaded only where the WhatsApp app is."""

from frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_message.whatsapp_message import WhatsAppMessage

from crm.demo import guardie


class MessaggioWhatsApp(WhatsAppMessage):
	def send_outgoing(self):
		if self.type == "Outgoing" and guardie.trattenuto(self.to):
			# kept as sent in the conversation, as the demo shows it; nobody receives it
			self.status = "Success"
			return
		return super().send_outgoing()
