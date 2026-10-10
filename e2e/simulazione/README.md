# La simulazione di una settimana

A real centre's week, Monday to Saturday and a month after, played by its staff
and its patients through the real screens, each in their own browser and device: the desk at a
1440 computer, the manager on a computer and a phone, the medical director on a
tablet held upright, the physiotherapist on a 390 phone, the dentist on a computer
in the dark theme, the dietitian on a 320 phone, the patients on their phones
(390, 320, sideways, with Android's large text, dark, a mother booking for her
child). Each step is checked as it goes: no page error, no server error, nothing
leaving the bench but to the fakes, nothing wider than the device, no raw code or
English word on the screen or in an email, the main actions as big as a finger,
every email once, no field named with its «*» to a screen reader. Every day the permissions are swept: what each persona must not
open is refused in words, with nothing in the answer.

## What it stands on

- **`crm/collaudo/prepara.py`**: `centro()` makes an empty test site a plausible
  poliambulatorio (two locations, the team by levels, the services, the health
  fund, the company that issues, subscriptions, reminders, payment reminders, the
  area, the waiting list, online booking, quotes in instalments, the clinical
  sheets). It refuses any site whose `site_config.json` does not say
  `"dottorcloud_collaudo": 1`, and a site with people of its own.
- **`crm/collaudo/tempo.py`**: the bench's clock moved through the week with
  freezegun (the framework's development requirement), in every request and job of
  that site only; the scheduler stays off and the suite runs each scheduled job at
  the hour it wants (`esegui`). The browsers follow with Playwright's clock.
- **`crm/collaudo/api.py`**: the mail each person received (the bench's email is
  muted and stays in the queue), the SMS, the server's errors, the week's script.
- **`finti/server.py`**: Stripe, stdlib only - its API, its hosted page where the
  person's browser pays with Stripe's test cards (4242… pays, …9995 is declined,
  …3155 asks to confirm, …0341 pays now and is declined later), its signed
  webhooks at the bench's hour.

## Run it locally

```bash
# a site of its own, empty
bench new-site collaudo.localhost --admin-password admin --install-app crm
bench --site collaudo.localhost set-config dottorcloud_collaudo 1
bench --site collaudo.localhost set-config mute_emails 1
bench --site collaudo.localhost set-config host_name http://collaudo.localhost:8000
bench setup requirements --dev          # freezegun
# the fakes (the suite starts them too, if they are down)
python3 e2e/simulazione/finti/server.py --porta 8791 &
bench --site collaudo.localhost execute crm.collaudo.prepara.centro

yarn install --ignore-scripts && npx playwright install chromium
SIM_BASE=http://collaudo.localhost:8000 yarn simulazione
```

The bench's workers must run (`bench start`, or `bench worker`): the jobs the
screens start (an invoice's PDF, a refund, the waiting list's offer, the archive)
run there, at the bench's moved clock; the site's own scheduler stays off (a new
site's is) and the suite runs each scheduled job at its hour. Invoices' PDFs need
`wkhtmltopdf` on the machine.

A bench that serves one default site (`serve_default_site`) needs a web server of
its own for the test site: `bench --site collaudo.localhost serve --port 8001`
and `SIM_BASE=http://collaudo.localhost:8001` (and `host_name` to match); without
realtime for that site, `SIM_SENZA_SOCKET=1` leaves the socket's errors out.

Each run plays a new week: the Monday after the last appointment on the site,
with no holiday in it. A second run on the same site meets the people of the
first (their areas open, their codici fiscali known): for a clean week, a new
site. `SIM_FINO=mercoledi` stops after a day;
`SIM_DA=giovedi` resumes the week a run stopped, from its saved state
(`rapporto/stato.json`). `SIM_CHROMIUM` uses a Chromium of your own.

## In GitHub

Actions > «Simulazione di una settimana» > Run workflow, on develop or on a branch:
a fresh bench, `centro()`, the fakes, the week; the report is the run's artifact.

## What the week does

- **Monday**: the manager takes invoicing live; six people book from home on
  /prenota (a deposit paid, a card declined then another, a bank's
  confirmation, a visit paid in full and online, a fund's direct form, a mother
  for her child), giving the codice fiscale a healthcare invoice needs, nobody a
  client nor a patient by booking; the desk confirms the fund's visit with its
  authorisation; the advance invoices issued by themselves, and the deposit read
  on the appointment's panel; phone bookings fill the
  evening class, the next one joins the waiting list; the areas are opened (a
  mother to her son's); the reminders leave and are answered; a seat freed goes
  to the waiting list; the class: «I'm here» from the area, check-in at the desk,
  the physiotherapist closes it on her phone, an invoice for each place; the cash
  closing.
- **Tuesday**: forms filled and signed with a finger in the area; the
  physiotherapist's assessment on the clinical sheet with the body chart, its
  report online, opened with the code; the fund's visit invoiced for the
  person's share; at Monza «I'm here», the doctor's history on the tablet, the
  balance of the deposit from the manager's phone; each location's cash.
- **Wednesday**: a cycle of sessions sold; the dentist's first visit and the
  care plan in instalments, signed in the area; a visit's balance; monthly
  subscriptions bought in the area (one on a card that will be refused); a
  child's visit invoiced to his mother by bank transfer; exercises at home
  published and ticked with their effort; the class on subscriptions.
- **Thursday**: a cancellation in time refunds the deposit with its credit note;
  the online visit, both entering the room; a no-show; marketing's campaign to a
  list (only who agreed); the review request; a session of the cycle; a late
  cancellation keeps the deposit, and the desk gives it back as a courtesy.
- **Friday**: a visit invoiced to the company that pays for it; the fund's
  month; the dashboard's money against the invoices; the centre's data taken
  away.
- **Saturday and a month after**: the night's payment reminder; a session
  started from the last visit; the subscriptions charged on the saved cards, one
  refused, tried again, paid from the area; the care plan's instalments
  invoiced.

Every evening the permissions are swept, and every step is checked as above.

## The report

`rapporto/` (not versioned): a page per day (`lunedi.html`, `lunedi.md`) with each
step, who did it on which device, how it went, the defects and the screenshots,
and `RIEPILOGO.md` with every defect of the run. `DIFETTI.md` here lists what the
simulation found and which commit put it right.

## Writing a step

A step is what one persona does on their device, found by the words and roles
the screen gives its controls, then the database asked whether it is so
(`s.passo(titolo, chi, fai, { chiave, dopo })`; a step whose `dopo` failed is
skipped). The files are formatted with this folder's `.prettierrc.json`
(`node frontend/node_modules/.bin/prettier --write "e2e/simulazione/**/*.ts"`).
