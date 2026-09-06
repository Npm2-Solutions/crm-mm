# 15 — Tracciamento del lead e attribuzione

> ✅ **Implementato.** Parte del [Progetto GHL-Parity](./README.md).
>
> Risponde alla domanda che nessuna schermata del CRM sapeva ancora rispondere:
> **da dove arriva questo lead, e cosa ha fatto prima di diventarlo.**

## Cosa fa GoHighLevel, e cosa abbiamo replicato

GHL tiene su ogni contatto due scatti di attribuzione — **First Attribution** e
**Latest Attribution** — con sorgente, mezzo, campagna, termine, contenuto,
pagina di atterraggio, referrer e gli identificativi di click delle piattaforme
pubblicitarie. Li popola da uno script di *External Tracking* che si incolla sui
siti del cliente, e li aggancia al contatto quando questo compie un'azione che
lo nomina: form, sondaggio, prenotazione, chat widget, order form.

| GHL | Qui | Note |
|---|---|---|
| External Tracking script | `crm/public/js/tracker.js` | Un tag, nessuna dipendenza |
| Session source (Paid Search, Organic Social, …) | `CRM Visitor Session.source_category` | 12 regole ordinate, [vedi sotto](#le-regole-di-classificazione) |
| First / Latest Attribution sul contatto | `first_touch_*` / `last_touch_*` su CRM Lead e CRM Deal | Stessi nomi sui due doctype |
| UTM + click id + gerarchia annuncio | `CRM Visitor Session` | 6 utm, 15 click id, campaign/adset/ad id |
| Page visits | `CRM Tracking Event` (`Page View`) | Con tempo sulla pagina |
| Trigger link click | `CRM Tracking Event` (`Link Clicked`) | Gia' esistevano i link tracciati, ora finiscono nel percorso |
| Source report | `crm.api.tracking.source_report` | Lead/trattative per categoria, sorgente, mezzo o campagna |
| — | Scheda **Tracking** su Lead e Trattativa | I due scatti + il percorso + le visite |

Fuori scope per ora: modelli multi-touch pesati (lineare, time-decay), stitching
cross-device oltre il click identificato, e l'invio di conversioni offline verso
le piattaforme (Meta CAPI, Google Enhanced Conversions).

## Il modello

```
  tracker.js sul sito del cliente
      │   localStorage: crm_vid (il browser), crm_sid (la visita)
      ▼
  POST /api/method/crm.api.tracking.collect          ← guest, text/plain
      │
      ├─ CRM Visitor           un browser. Anonimo finche' non si nomina.
      ├─ CRM Visitor Session   una visita + la campagna che l'ha prodotta
      └─ CRM Tracking Event    ogni pagina letta, form inviato, link cliccato
              │
              │  un invio form / una prenotazione / un click da email
              ▼
  attribute()  →  lega il visitatore al Lead, riscrive tutta la sua storia
                  passata con quel record, e salva i due scatti
```

Perche' la sessione e non la singola pagina: la campagna e' una proprieta' della
**visita**. Se fosse attaccata alle pagine, la seconda pagina di una visita
sarebbe "diretta" e la prima "paid" — e il primo/ultimo contatto diventerebbero
indecidibili. Per questo `first_touch_session` e `last_touch_session` sono due
Link a sessioni, e i campi denormalizzati sul lead servono solo per filtrare,
raggruppare e usarli nelle condizioni delle automazioni.

## Le regole di classificazione

Valutate in ordine, vince la prima (`crm/utils/attribution.py`, un test ciascuna
in `crm/tests/test_attribution.py`):

| # | Condizione | Categoria |
|---|---|---|
| 1 | `utm_source` e' un token noto di piattaforma (`adwords`, `fb_ad`, …) | Paid Search / Paid Social |
| 2 | `utm_medium` nomina il canale (`cpc`, `paid_social`, `email`, `sms`, `affiliate`, `organic`, `social`, `referral`) | quello |
| 3 | click id di ricerca a pagamento (`gclid`, `gbraid`, `wbraid`, `msclkid`, `dclid`, `yclid`) | Paid Search |
| 4 | click id di affiliazione (`irclickid`) | Affiliate |
| 5 | click id social a pagamento (`ttclid`, `li_fat_id`, `twclid`, `epik`, `sccid`, `rdt_cid`, `ctwa_clid`) | Paid Social |
| 6 | `fbclid` **senza** referrer social | Paid Social |
| 7 | referrer e' una webmail | Email |
| 8 | referrer e' un motore di ricerca | Organic Search |
| 9 | referrer e' un social | Organic Social |
| 10 | qualsiasi altro referrer di terzi | Referral |
| 11 | c'e' un tag che non sappiamo collocare | Referral |
| 12 | niente del tutto | Direct Traffic |

Due punti che sembrano dettagli e non lo sono:

- **`fbclid` da solo non vuol dire "a pagamento".** Facebook lo appende a ogni
  link in uscita, post organici compresi. Con un referrer di facebook/instagram
  e' un post (regola 9); senza referrer e' la firma del browser in-app, cioe' un
  annuncio. Prenderlo sempre per "paid" gonfia il rendimento delle campagne.
- **La webmail va prima dei motori di ricerca.** `mail.google.com` contiene
  `google`: senza la regola 7 ogni click da Gmail finirebbe in Organic Search.

Il referrer da un nostro stesso dominio non e' una sorgente: una navigazione
interna non deve inventarsi un referral.

## Le porte d'ingresso

Nessuna strada lascia il campo sorgente vuoto:

| Ingresso | Cosa succede |
|---|---|
| Form pubblico `/crm-form/<route>` | Gli id viaggiano accanto al record; in iframe arrivano sulla URL |
| Prenotazione `/book/<route>` | `book()` accetta gli id; un invitato che torna aggiorna solo l'ultimo contatto |
| Link tracciati (email/SMS) | Click registrato sul percorso, e l'id del visitatore portato a destinazione sulla query string |
| Meta Lead Ads | Server-to-server: `is_organic` separa paid da organico, `ad_id` nel contenuto |
| Creazione a mano nel CRM | `CRM UI` |
| API / import di terzi | `Third Party` |

Il primo contatto si scrive una volta e non si sovrascrive mai: e' la campagna
che ha introdotto quella persona, e una visita successiva non deve poterla
rivendicare. L'ultimo contatto si riscrive a ogni tocco.

## Installazione su un sito

1. Impostazioni → **Lead Tracking** → copia lo snippet.
2. Incollalo nell'`head` di ogni pagina da tracciare.
3. Quando i dati arrivano, elenca i domini in **Allowed Origins** (vuoto accetta
   qualsiasi origine: comodo in prova, da chiudere in produzione).
4. Metti gli IP dell'ufficio in **Excluded IPs**.

Con un banner dei cookie: attiva **Require consent** e chiama
`CRMTracker.consent(true)` quando l'utente accetta.

API per la pagina: `CRMTracker.track(nome, props)`, `CRMTracker.identify(traits)`,
`CRMTracker.getIds()`, `CRMTracker.refresh()` dopo aver iniettato un form.

## Privacy

- Nessun cookie di terze parti: la continuita' sul sito del cliente passa dal
  `localStorage` di quel sito.
- IP anonimizzato di default (ultimo ottetto per IPv4, ultimi 80 bit per IPv6);
  si puo' spegnere del tutto la memorizzazione.
- Do Not Track rispettato, bot esclusi, consenso opzionale come precondizione.
- Conservazione: la cronologia anonima piu' vecchia della soglia viene
  cancellata ogni notte. Quella attaccata a un lead o a una trattativa resta —
  a quel punto e' un dato del CRM, non traffico da tenere in casa.

## File

| File | Ruolo |
|---|---|
| `crm/utils/attribution.py` | Le regole. Funzioni pure, nessun frappe |
| `crm/api/tracking.py` | Endpoint di raccolta, attribuzione, percorso, report, pulizia |
| `crm/public/js/tracker.js` | Lo script da incollare sui siti |
| `crm/fcrm/doctype/crm_visitor/` | Il browser |
| `crm/fcrm/doctype/crm_visitor_session/` | La visita e la sua lettura di marketing |
| `crm/fcrm/doctype/crm_tracking_event/` | Cosa ha fatto |
| `crm/fcrm/doctype/crm_tracking_settings/` | La policy del sito |
| `frontend/src/components/Settings/TrackingSettings.vue` | Snippet + impostazioni |
| `frontend/src/components/Activities/AttributionArea.vue` | La scheda Tracking |
| `crm/tests/test_attribution.py` | Le regole, una per test |
| `crm/tests/test_tracking.py` | Il percorso completo, dal beacon al lead attribuito |

## Fonti

Ricerca condotta a settembre 2026 sulla documentazione pubblica di HighLevel e
sulle guide di terze parti:

- [Understanding Attribution Source (Ad Reporting) — HighLevel](https://help.gohighlevel.com/support/solutions/articles/48001219997-understanding-attribution-source-ad-reporting-)
- [Attribution and UTM parameters as filters on custom widgets — HighLevel](https://help.gohighlevel.com/support/solutions/articles/155000002549-how-to-add-attribution-and-utm-parameters-as-filters-on-custom-widgets)
- [GoHighLevel Attribution: UTMs, Sources and Fixes — GHLFocus](https://ghlfocus.com/gohighlevel-attribution-explained/)
- [GoHighLevel CRM Lead Tracking & Attribution: Complete Setup Guide](https://blog.closelyhq.com/gohighlevel-crm-lead-tracking-attribution-setup-guide/)
- [Workflow Contact Attribution Variables — Growthable](https://growthable.io/gohighlevel-tutorials/workflows/workflow-contact-attribution-variables-for-gohighlevel/)
