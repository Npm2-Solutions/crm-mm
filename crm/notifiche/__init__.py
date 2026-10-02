# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Notifications: what reaches somebody of the centre in DottorCloud's panel, and
how it reads (docs/progetto-ghl/43-notifiche.md).

- **One door** (`avvisi.avvisa`): every module tells somebody something the same
  way - a mention, an assignment, a task, a WhatsApp or an SMS of a person they
  follow, the day's appointments without an outcome, a question from the client
  area, the invoicing's alerts, an automation's message. A message of the same
  person adds to the notification not yet read ("3 WhatsApp messages from…")
  rather than piling up.
- **The words** (`regole`): a sentence is kept in English with its names and read
  in the language of whoever reads it, the names in bold; what was written before
  reads the same way. Nothing of how the panel draws it is kept in the data.
- **The panel** (`api`): a page at a time with how many are unread, where each one
  opens - computed here, never guessed by the screen - the first words of the
  message it is about where the reader may read it; read, all read, unread again
  with one query and one signal to the open tabs.
- Notifications older than six months go, read or not: the retention is in
  Log Settings (`default_log_clearing_doctypes`).
"""
