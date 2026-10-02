# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The emails: how every email DottorCloud sends looks, and the words of the ones
it sends to the centre's people (docs/progetto-ghl/44-email.md).

- **One layout** (`templates/emails/standard.html`, `email_header.html`,
  `email_footer.html`, over the framework's): every email - a patient's code, a
  booking, an offer from the waiting list, a document, the framework's own (a new
  password, a welcome) - on the brand's canvas, a white card with the cloud's tail,
  the centre's mark leading at the top, its words, the product signing at the foot.
- **Its pieces** (`aspetto`): what the layout needs of the brand and of the centre
  (`contesto`, a Jinja method), a button (`pulsante`) and a code in its box
  (`codice`) for the modules' messages.
"""
