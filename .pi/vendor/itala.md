# Itala — the contract, as published

ITALA Tecnologia Informatica S.r.l. (P.IVA 12478341006), an intermediary accredited
at the Agenzia delle Entrate's Sistema di Interscambio. Two products, two APIs. This
is a summary in our words of what their public documentation says, read on
02/10/2026; anything the adapters do that is not here is an invention and should
be taken out.

## Electronic invoices — fattura-elettronica-api.it, REST API 2.0

Guide: https://www.fattura-elettronica-api.it/documentazione/ (the old
`/guida2.0/` redirects there); OpenAPI 3.0.3 at
https://www.fattura-elettronica-api.it/docs/fattura-elettronica-api.yaml (only on
`www.`). FAQ: https://www.fattura-elettronica-api.it/faq/. Official PHP client:
github.com/clixclix2/FatturaElettronicaAPIClient2. Read again on 02/10/2026.

- **Doors.** Test `https://fattura-elettronica-api.it/ws2.0/test`, production
  `https://fattura-elettronica-api.it/ws2.0/prod`.
- **Authentication.** HTTP Basic with the account's API credentials (client_id :
  client_secret, from the reserved area, "scheda personale"), or Bearer with the
  token of `POST /authentication` (`{"token", "expires"}`). Every Basic call also
  answers with `X-auth-token` and `X-auth-expires`: the first call can be Basic and
  the next ones Bearer, without ever calling `/authentication`.
- **Errors.** Always JSON; 400, 401, 404 carry `{"error": "..."}`.
- **Sending an XML.** `POST /fatture`, `Content-Type: application/xml`, the whole
  FatturaPA, **unsigned**: they add or rewrite `FatturaElettronicaHeader/
  DatiTrasmissione` with their own references and progressive, and **sign the
  invoices to a public body themselves** (FAQ; the credits of a PA invoice include
  the signature). A signed `.p7m` could not be rewritten. Answer: `id` (theirs),
  `sdi_identificativo` (**null while `PREN`**: the SdI's id comes later, with the
  updates - their `id` is not it), `sdi_nome_file` (the name of the file actually
  transmitted), `sdi_fattura` (the XML actually transmitted), `sdi_stato` (`INVI`
  sent, `PREN` taken in charge and not yet at the SdI, `ERRO` error, see
  `sdi_messaggio`), `sdi_messaggio`.
- **Sending from JSON.** `POST /fatture`, `Content-Type: application/json`, the
  data only; `piva_mittente` in multi-company accounts. Not used here: the XML is
  built and checked in DottorCloud.
- **Updates and incoming invoices.** `GET /fatture`, filters `unread=true`,
  `date_from`, `date_to`, `id_from`, `id_to`, `sdi_id`, `partita_iva` (in a
  multi-company account, one company's documents only), `solo_ricezioni`,
  `solo_trasmissioni`, `origine`, `partita_iva_controparte`, `numero_documento`,
  `anno_documento`, `tipo_documento`. Rows with `ricezione: 1` are invoices received
  (`sdi_fattura_base64`, `sdi_fattura_xml`, `dati_documento`), rows with
  `ricezione: 0` transmission updates: `sdi_stato` `INVI`, `PREN`, `ERRO`, `CONS`
  delivered, `NONC` not delivered (the obligation is met), and for the public
  administration `ACCE` accepted, `RIFI` refused, `DECO` term elapsed.
- **Reading uses an update up.** An update returned once is not returned again
  (the PHP client's `ricevi()`: "non viene più trasmesso", unless "Da leggere" is
  ticked again in their dashboard). So DottorCloud keeps every update before it
  applies it (`CRM SdI Update`) and tries a failed one again. Two sites polling the
  same VAT number steal each other's updates: a copy of a site reads nothing
  (`itala_site`).
- **One document.** `GET /fatture/{id}` (one object: `ricezione`, `id`,
  `sdi_identificativo`, `sdi_stato`, `sdi_messaggio`), asked for an invoice that has
  heard nothing for a day; its PDF `GET /fatture/{id}/pdf`; its attachments
  `GET /fatture/{id}/allegati`; **the SdI's original notice**
  `GET /fatture/{id}/notifica` (`Content-Type: application/xml`; its own file name
  in `Content-Disposition` when given - not documented, read when there - else one
  name per state).
- **Webhook.** URL and token set in their dashboard, one per account: `POST`, the
  same JSON as `GET /fatture` (a list), unread only, with `Authorization: Bearer
  <token>`; a 200 marks them delivered, anything else is retried every 3 hours for
  up to 3 days. Frappe reads any Bearer as its own OAuth token and would refuse the
  call: the webhook's address takes the header away before Frappe looks
  (`webhook.prima_della_richiesta`). Only for a company with an account of its own:
  on the agency's shared account the updates are polled with `partita_iva`.
- **Multi-company.** For accounts enabled to it: `POST /aziende` (required
  `ragione_sociale`, `piva`, `cfis`; with invoices sent as XML only `piva` and
  `cfis` matter), `PUT /aziende/{id}`, `GET /aziende`, `GET /aziende/{id}`,
  `DELETE /aziende/{id}` (a centre that leaves: `remove_from_itala`). The record:
  `id`, `ragione_sociale`, address, `piva`, `cfis`, `abilita_ricezione` (default 1,
  sent as 1: both directions), `tipo_regime_fiscale`, register and REA data,
  administration phone and email, `iban`.
- **Receiving.** The account gets a recipient code ("il codice te lo forniamo dopo
  la tua iscrizione"): each company registers it at ivaservizi.agenziaentrate.gov.it
  as the address of its invoices, and from then on its suppliers' invoices reach
  Itala (`itala_recipient_code` on the settings, `recipient_code_registered` on the
  company). Every invoice received costs a credit.
- **Reselling.** Allowed: the agency keeps each client's written authorisation to
  send invoices on its behalf (FAQ).
- **Timeouts.** A `POST /fatture` whose answer is lost may have arrived: before
  sending again, `GET /fatture?numero_documento&anno_documento&partita_iva` says
  whether Itala has it (an SdI duplicate is rejection 00404).
- **Pages.** `per_page` (default 100, at most 1000), `page`; a `Link: <...>
  rel="next"` header when there is another page.

## What the test door answered (05/10/2026)

Tried from a development site with the agency's test credentials. Where the API
says something its guide does not, the API is what the code follows:

- **Every value is text.** `"id": "550797"`, `"ricezione": "0"`,
  `"sdi_identificativo": "5507970"`, `"test": "1"`: the guide's integers come as
  strings. `"0"` is true in Python, so a flag is read with `busta.ricevuta()`, never
  by its truth.
- **A company's VAT number keeps its prefix.** `/aziende` answers
  `"piva": "IT13832480969"` for one registered as `13832480969`; the filter
  `partita_iva` of `GET /fatture` wants it **without** (`IT…` finds nothing), and a
  row of `/fatture` names it without. Compared with `busta.stessa_partita_iva()`.
- **A duplicate company is a 400**: «Azienda gia' esistente in anagrafica con stessa
  partita iva o codice fiscale». Then it is looked for by its VAT number.
- **A company may be refused in test**: «Cedente [13832480969] non abilitato in
  ambiente di test. Contattare l'assistenza.» A company registered by DottorCloud
  through `/aziende` was not.
- **The schema comes first**: a file the XSD refuses is a 400, «XML non conforme
  allo schema FPR12», with no line nor element. The XML is checked against the
  published XSD in the tests (`crm/invoicing/tests/xsd`).
- **A sent invoice** comes back at once `INVI` with a made-up SdI identifier (the
  account's sending mode is "PREDEFINITO"), its transmission block rewritten with
  Itala's (`IdCodice` 12478341006, a progressive like `83GA`). It is not an unread
  update: `unread=true` lists it only once a state is changed by hand in their
  dashboard with "Da leggere" ticked. With no SdI behind it,
  `/fatture/{id}/notifica` is a 404 and `sdi_file_notifica` is empty: the state is
  applied as Itala's word.

- **An invoice received** (inserted by hand in their dashboard, "Ricezione") is a
  row with `ricezione` "1", the row's own `numero_documento`, `data_documento`,
  `tipo_documento` (TD01) and `data`, an empty `sdi_stato` and a null
  `sdi_data_aggiornamento`; its `dati_documento` speaks FatturaPA's names
  (`mittente.PartitaIVA` "IT…", `Denominazione`, `documento.Numero`, `Data`,
  `Totale`, `Tipo` "FATT"). Read by `busta.fattura_ricevuta()`. Inserting one by
  hand with "Invio" asks for the issuer to be a registered company («il
  Cedente/Cessionario … non è una tua azienda registrata»).
- **`unread=true` uses the rows up**, as the guide says: listing them by hand
  takes them from the site. `GET /fatture/{id}` reads one without.

## Sistema TS — sistema-ts-api.it, REST API v1

Guide: https://www.sistema-ts-api.it/documentazione/ (OpenAPI at
`/docs/sistema-ts-api.yaml`). **Not used by DottorCloud yet** (doc 49).

- **Doors.** Test `https://sistema-ts-api.it/api/v1/test`, production
  `https://sistema-ts-api.it/api/v1/prod`; authentication as above, with the
  credentials of sistema-ts-api.it.
- **Providers (erogatori).** `POST /erogatori`: required `partitaIva`,
  `codiceFiscale`; to transmit also `usernameSts`, `passwordSts`, `pincodeSts` (the
  centre's own Sistema TS credentials; codice fiscale and pincode are encrypted on
  their server and never returned); `denominazione`, `descrizione`. `PUT` with only
  what changes (a new pincode). **No regional, ASL or facility (SSA) codes.**
- **Expense documents.** `POST /documenti-spesa`, JSON: `operazione` (`INS`
  default, `CAN` to cancel), `partitaIvaErogatore`, `tipoDocumento` (`F` invoice,
  `D` commercial document), `numeroDocumento`, `dataDocumento`,
  `codiceFiscaleCittadino`, `dispositivo`, `dataPagamento`, `pagamentoTracciato`,
  `flagOpposizione`, `vociSpesa` (`tipoSpesa` TK FC FV AD AS SR CT PI IC SP SV AA,
  `importo`, either `aliquotaIVA` or `naturaIVA`). A cancellation carries only what
  identifies the document. Answer: `id`, `statoSts` (`INVI`, `PREN`, `ERRO`),
  `protocolloSts`, `messaggioSts`. `PUT /documenti-spesa/{id}` corrects and retries
  one in `ERRO`. `GET /documenti-spesa` and `/{id}` read them back (filters by date,
  id, protocol, VAT number, number, year, type). **No refund (R) or variation (V)
  operation, no advance-payment flag.**
