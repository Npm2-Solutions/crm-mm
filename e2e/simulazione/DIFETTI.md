# Quello che la simulazione ha trovato

What the week found in DottorCloud, where, and the commit that put it right.
Each fix carries its test where there is logic to test.

| # | What | Where | Commit |
|---|---|---|---|
| 1 | /prenota and the old /book pages loaded their font from Google: a request leaving the centre's site at every booking | `crm/www/prenota.html`, `book.html`, `book_index.html` | bbdf14ee |
| 2 | /prenota's times, month arrows and seat steppers were under a finger's size on a phone, and the days had no name a screen reader could read | `crm/www/prenota.html` | afa5cd70 |
| 3 | A deposit paid online confirmed the booking twice: the person got the confirmation email twice | `crm/pagamenti/pagamenti.py` | 4467ceab |
| 4 | A booking's email said the hour with «(Europe/Rome)» after it | `crm/api/service_booking.py`, `crm/lingue.py` | 9b05e954 |
| 5 | After Frappe 16.50 the sign-in page's button was black again, not the brand's | `crm/templates/includes/marchio_framework.html` | ad64e223 |
| 6 | An invoice paid online that stayed a draft (no codice fiscale yet) was in nobody's things to do, and its notification did not open it | `crm/invoicing/api.py`, `crm/notifiche/api.py`, `Invoices.vue` | ad832a0d |
| 7 | A class was invoiced once, to its first participant: the others who came and paid were never invoiced | `crm/invoicing/api.py`, `Today.vue` | 2e62a544 |
| 8 | A deposit's invoice belonged to no location: missing from that location's cash closing and dashboard | `crm/scheduling/sedi.py` | e1ffa12f |
| 9 | Signed in, every member of staff landed on the framework's apps screen, one icon to tap («DottorC…» on a phone) | `crm/api/__init__.py`, `crm/hooks.py` | 8e21b32a |
| 10 | A patient signed in to the area who opened /crm got the framework's «Not permitted» with a black «Login»; the refusal did not wear the brand | `crm/www/crm.py`, `crm/marchio.py` | 6f92a04b |
| 11 | A visit written from the Clinic tab never said the person came: the agenda left them «Booked» after the visit was signed | `crm/clinica/cartella.py` | f2320184 |
| 12 | On a touch tablet the sidebar's rows (Notifications, Settings, Expand) were 28px | `frontend/src/telefono.css` | 66717a29 |
| 13 | Two «News in your area» emails four seconds apart (a visit's balance and the next deposit), the same words twice | `crm/area/collegamento.py` | 130b7387 |
| 14 | The area's dialogs had 31px buttons on a phone («Go to payment», «Sign and accept») | `frontend/src/area/area.css` | 34b9d5ae |
| 15 | After a session the server had ended, the right code led back to the area's door: the framework deleted the new session's cookie with the old one's | `crm/area/accesso.py`, `collegamento.py`, `passkey.py` | 4e6b92cb |
| 16 | An invoice paid by bank transfer, issued at the desk, was collected that day: never reminded, counted as money in hand | `crm/invoicing/incassi.py`, `emissione.py` | 3ae3f3e8 |
| 17 | With the deposit's invoice still a draft, the desk invoiced the whole price as the balance: 120 € after 30 € paid online | `crm/pagamenti/fatture.py` | 17fd378b |
| 18 | A child's payment reminder said «call them» though his mother had booked; a visit made out to a company was reminded to its employee | `crm/invoicing/solleciti.py` | a84c35da |
| 19 | On a tablet a record's fields drawn as buttons (a country, a select) were 28px to a finger | `frontend/src/telefono.css` | bc38f43d |

## Open questions (not changed)

- A deposit paid online makes its advance invoice, and that invoice makes the
  person a client - a patient, for a health service - before they ever came
  («Paziente dal…» the day they booked); Marco, who cancelled in time and got
  his deposit back with a credit note, stays «Paziente».
- A child booked online by a parent is the invoice's client (his codice fiscale
  for the Sistema TS): the booking records that she books, not that she pays,
  so the invoice is not made out to her unless the desk ticks it.
- A late cancellation by phone keeps the deposit; the desk's panel offers no way
  to give it back as a courtesy, nor says that it is kept.
- /prenota and the area's purchases ask no codice fiscale: a healthcare
  invoice for what is paid online waits as a draft until the desk asks it (the
  simulation completes them as the manager would). Asking it there would close
  the loop.
- The appointment's panel does not say that a deposit was paid.
- A company in test mode keeps the cash closing, the payment reminders and the
  area's invoices out: the simulation takes invoicing live on Monday morning.
- Opening the area for a child without an email, the dialog starts on «The
  person», not on «A parent or guardian».
- The centre's own website (`site_render`) loads Google Fonts when the centre
  chooses one.
- The old /book pages still write the hour with the zone's raw name and
  English month names (`_format_when`).
- A form's required mark («*», hidden from screen readers) is read in the
  question's name by Playwright's accessible name: worth checking with
  VoiceOver and TalkBack.

## What the week cannot play

- SMS, WhatsApp and calls: there is no fake Twilio nor Meta, so the reminders,
  the waiting list and the review requests go by email, and the missed call is
  not played. The SMS checks of the automations stay in the server's tests.
- The SdI and the Sistema TS: no intermediary nor credentials are connected and
  their automatic sending stays off, so the invoices are issued and kept, never
  sent.
- The realtime socket, where the bench serves the test site on a port of its own
  (`SIM_SENZA_SOCKET`): a page is not told what changed while it is open.
