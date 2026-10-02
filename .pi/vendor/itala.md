# Itala — the contract, as published

ITALA Tecnologia Informatica S.r.l. (P.IVA 12478341006), an intermediary accredited
at the Agenzia delle Entrate's Sistema di Interscambio. Two products, two APIs. This
is a summary in our words of what their public documentation says, read on
02/10/2026; anything the adapters do that is not here is an invention and should
be taken out.

## Electronic invoices — fattura-elettronica-api.it, REST API 2.0

Guide: https://fattura-elettronica-api.it/guida2.0/ (OpenAPI at
`/docs/fattura-elettronica-api.yaml`).

- **Doors.** Test `https://fattura-elettronica-api.it/ws2.0/test`, production
  `https://fattura-elettronica-api.it/ws2.0/prod`.
- **Authentication.** HTTP Basic with the account's API credentials (client_id :
  client_secret, from the reserved area, "scheda personale"), or Bearer with the
  token of `POST /authentication` (`{"token", "expires"}`). Every Basic call also
  answers with `X-auth-token` and `X-auth-expires`: the first call can be Basic and
  the next ones Bearer, without ever calling `/authentication`.
- **Errors.** Always JSON; 400, 401, 404 carry `{"error": "..."}`.
- **Sending an XML.** `POST /fatture`, `Content-Type: application/xml`, the whole
  FatturaPA. They add or rewrite `FatturaElettronicaHeader/DatiTrasmissione` with
  their own references and progressive. Answer: `id`, `sdi_identificativo` (or null),
  `sdi_nome_file` (the name of the file actually transmitted), `sdi_fattura`,
  `sdi_stato` (`INVI` sent, `PREN` taken in charge and not yet at the SdI, `ERRO`
  error, see `sdi_messaggio`), `sdi_messaggio`.
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
- **One document.** `GET /fatture/{id}`; its PDF `GET /fatture/{id}/pdf`; its
  attachments `GET /fatture/{id}/allegati`; **the SdI's original notice**
  `GET /fatture/{id}/notifica` (XML, with its file name).
- **Webhook.** URL and token set in their dashboard, one per account: the same JSON
  as `GET /fatture`, unread only, with `Authorization: Bearer <token>`; a 200 marks
  them delivered, anything else is retried every 3 hours for 3 days.
- **Multi-company.** For accounts enabled to it: `POST /aziende` (required
  `ragione_sociale`, `piva`, `cfis`; with invoices sent as XML only `piva` and
  `cfis` matter), `PUT /aziende/{id}`, `GET /aziende`, `GET /aziende/{id}`,
  `DELETE /aziende/{id}`. The record: `id`, `ragione_sociale`, address, `piva`,
  `cfis`, `abilita_ricezione` (default 1), `tipo_regime_fiscale`, register and REA
  data, administration phone and email, `iban`.
- **Pages.** `per_page` (default 100, at most 1000), `page`; a `Link: <...>
  rel="next"` header when there is another page.

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
