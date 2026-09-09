# Invoicing

Electronic invoicing for **every kind of service**, healthcare included. It issues
the document, computes it, numbers it, writes the FatturaPA XML, reports healthcare
expenses to the Sistema TS, and refuses — with a 403, server-side — to send a
healthcare invoice for a natural person through the SdI.

The guiding principle is the one the module inherits: **the choices that decide
fiscal correctness are data, the engine is code.** The exemption of a service, the
qualification of whoever performs it, the fund and its rate, the numbering format:
all of it lives in doctypes a practice owner edits, never in Python. The engine
never infers, and there is no silent default anywhere in it.

---

## Where this comes from, and what changed

The design is a port of a module built for GoHighLevel — a US-hosted CRM. Half of
that architecture existed to work around where the data had to live. This system
runs on its own infrastructure in Europe, so those workarounds are gone and what
they were protecting is simply true by construction.

| The GHL design | Here | Why |
|---|---|---|
| Patient registry in a **separate encrypted vault**, outside the CRM | Native doctypes | The CRM *is* the European system of record. There is no second system to keep the data out of. |
| **Four opaque fields** on the contact, and a client that raises if anything else is written | The full billing profile on the record | Nothing is being kept from a processor abroad. |
| **The PDF never enters the CRM**: signed opaque token, short expiry, second factor, 45-day cap | The document is attached to its record; delivery expiry is a setting, default off | The 45 days existed because the file lived outside the controller's systems. |
| **Double opt-in** on the address before the first send | Ordinary CRM email | The Garante's December 2025 finding was about sending health documents through a third-party channel. |
| Appointments **stay in the GHL calendar**; the arrangement is an art. 9 processing to be declared, covered by transfer clauses and a documented TIA | `CRM Appointment`, next to everything else | Nothing crosses a border, so there is nothing to declare. The agenda proposes the service and the provider directly. |
| Row-level security, per-tenant envelope encryption, blind indexes, an application guard that fails tests when a query forgets `tenant_id` | Frappe roles and permissions | Multi-tenancy was the threat model. One site is one practice. |
| SdI through a paid API that converts **JSON to XML** | The XML is generated here | Buying the conversion made sense when there was nowhere to run it. Owning the format means issuing, inspecting and keeping a document without a round trip. The accredited channel stays a swappable last mile. |
| **Healthcare only** | Every service | A CRM invoices a physiotherapist and a marketing agency from the same screen; the answer has to come from the same place. |

What did **not** change is everything the original had actually solved: the triple,
the 403, the order of the arithmetic, the two Sistema TS schemas, and the refusal
to guess.

---

## Architecture

```
DESK / SPA (data)                    ENGINE (code, no Frappe)          BRIDGE (Frappe)
 CRM Invoicing Company ──────┐        crm/invoicing/engine/
 CRM Professional Qualification ─┼──► professioni.py                    registro.py
 CRM Billable Service ───────┤        classificazione.py  ← the triple  documento.py
 CRM Service Provider ───────┘        calcolo.py                        xml_sdi.py
                                      numerazione.py                    ts.py
 CRM Invoice ──────────────────────►  diciture.py                       api.py
   + Item / Tax Summary / Payment     fatturapa.py     → XML            monitoraggio.py
                                      sistema_ts.py    → zip
 CRM Invoice Series (counter)         codici.py · codice_fiscale.py
 CRM TS Submission · CRM Invoice Log
```

`engine/` imports nothing from Frappe and has no database, no network and no
global state. It is the part an accountant has to be able to read, and its 164
tests run with a checkout and a Python interpreter:

```bash
python -m unittest discover -s crm/invoicing/tests -t .
```

The Frappe-side tests are in `crm/tests/test_invoicing.py` and need a bench.

---

## The triple, and the two symmetrical mistakes

Routing is not decided by "is this healthcare". It is decided by

```
(service, qualification of whoever performs it, kind of recipient)
   -> {exempt | taxable} x {SdI forbidden | SdI mandatory} x {Sistema TS yes | no}
```

because **Risoluzione AdE n. 9 del 24 febbraio 2026** closed four cases with
counter-intuitive answers:

| Qualification | VAT | Electronic invoice via SdI | Sistema TS |
|---|---|---|---|
| Osteopata | taxable, ordinary rate | **mandatory** | no |
| Chiropratico | taxable | **mandatory** | no |
| Chinesiologo | taxable 22% | **mandatory** | no |
| Massoterapista | exempt art. 10 n. 18 | **forbidden** | yes |

So a multi-specialty practice runs two opposite regimes on one legal person. The
mistake everybody guards against — sending a healthcare invoice to the SdI — is a
privacy breach. The mistake nobody guards against is **not** sending the
osteopath's, and it is born precisely from a guard written too wide.

`guardia_sdi` is a `PermissionError`, so `crm.invoicing.api.send_to_sdi` answers
**403**. It is not a UI flag: it holds for every user and every override, and in
the interface the action does not exist at all on those documents. A greyed-out
button invites somebody to go looking for how to turn it on.

---

## The arithmetic, in order

`fee → fund levy → VAT → stamp-duty threshold → re-charge → withholding`

The order is fixed and tested, because the boundary is where it goes wrong: 76 € of
fee with the 2% ENPAP levy makes 77.52 and the stamp duty is due; 75 € makes 76.50
and it is not; at exactly 77.47 it is **not** due — the threshold is passed, not
reached.

Four things almost everybody gets wrong, and which the engine gets right:

- **ENPAM provides no contributo integrativo to charge the patient.** Nothing goes
  on the invoice.
- **Re-charging the stamp duty is not an art. 15 exclusion.** Risposta AdE 428/2022:
  it is part of the compensation, so it follows the VAT regime of the service and
  counts towards revenue.
- **The contributo integrativo enters the VAT base**, and therefore the stamp-duty
  threshold and the amount reported to the Sistema TS.
- **The contributo integrativo is not subject to the withholding; the optional INPS
  4% rivalsa is.** Getting this backwards produces a certification that does not
  reconcile.

The invariant: **the total on the document and the sum reported to the Sistema TS
coincide**, with the single exception of a stamp duty paid in cash.

Beyond the original scope, the engine also carries withholding (`DatiRitenuta`),
split payment, reverse charge, non-taxable and out-of-scope treatments, art. 15
advances, per-line discounts, and multi-rate VAT summaries — the things a
non-healthcare invoice needs.

---

## Numbering

`numDocumento` accepts at most **20 characters** of `[A-Za-z0-9_./-]`. No spaces, no
`#`, no accents, no `:`. A format chosen after the fact turns out in January not to
pass, and by then it is thousands of rows — so it is validated when the company is
saved, on the worst case of a six-digit counter.

The number is assigned on submit, with the counter row locked, inside the
transaction that saves the document. A number assigned and not used is a gap, and
the Agenzia rejected numbering with gaps (Risposta n. 505 del 29 ottobre 2020).

---

## Sistema TS

One pipeline, three submission modes, and only the last ten centimetres change.

| Mode | What it needs | Who transmits |
|---|---|---|
| `export` | nothing | the practice, from the portal |
| `credenziali_studio` | user, password, PINCODE, **no active mandate** | this system |
| `intermediario` | an Entratel accountant **with** an active mandate | this system, on the `/entrate/` channel |

**Everybody is born in `export`**, so no onboarding waits on somebody else's
paperwork, and `export` stays tested even when every company is on automatic: it is
the universal plan B. The truth about the mandate is not asked for — practices
answer it wrong without meaning to, they simply do not know. It is probed: rejection
`105` means there is no mandate, `106` means there is one.

Two schemas, not one with a switch. The synchronous one is namespaced and puts
`voceSpesa` before the closing flags; the attached file has no namespace at all, one
`proprietario` per file, and a mandatory `flagOperazione`. `xs:sequence` makes the
order binding.

Encryption is RSA 1024 with PKCS#1 v1.5, and it happens **at send time, always**:
the ciphertext is randomised (never a key or an index) and it is not storable (the
certificate is reissued). Without a certificate the file is still built — `export`
has to work on day one — but with a stand-in that writes `NONCIFRATO` into the
field, so a file that is not ready to send can never be mistaken for one that is.

---

## Watching for silence

In invoicing, no news is not good news. The daily job looks for absence, not for
errors:

- the `SanitelCF.cer` certificate expired or reissued — **every** submission then
  fails with code `002`, quietly;
- no accepted submission for N days with documents waiting;
- the annual deadline approaching with something still outstanding — 31 January,
  and mid-March for vets, who therefore get their own batch.

---

## What this module does not decide

- **Paper or electronic** (`document_mode`): two product configurations with
  different retention duties, not a detail.
- **The exemption, profession by profession.** The register ships as a documented
  starting point with `needs_verification` marking every point an accountant has to
  close before go-live. `crm.invoicing.api.onboarding_checklist` returns them as a
  live list that says what each gap costs.
- **The element names and date format of the Sistema TS tracciato.** They come from
  the official kit and are worth re-checking against its XSDs before go-live.

*Not tax or legal advice. The A-Cube endpoints, the Sistema TS kit and the FatturaPA
technical specification should be taken from their current versions, and every legal
reference is doubled with the Testi Unici applicable from 1 January 2027.*
