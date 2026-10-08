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
| — | Scheda **Tracking** su Lead e Trattativa | I due scatti + una timeline unica: ogni visita con dentro i suoi eventi |
| — | Sezioni **First Touch / Last Touch** nella scheda Dati | I campi grezzi, richiudibili, accanto agli altri dati del record |

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
| `frontend/src/utils/journey.js` | Raggruppa la cronologia per visita (funzioni pure, testate) |
| `crm/patches/v1_0/add_attribution_sections_to_data_layouts.py` | Porta le sezioni nella scheda Dati sui site gia' installati |
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

## Il pannello e' una timeline sola

Erano tre cose impilate: l'inserzione in un riquadro, i due snapshot di
attribuzione in altri due, e sotto la timeline delle visite. La domanda che si
fa a questo pannello e' una sola — **cosa e' successo, e in che ordine** — e
nessuna delle tre rispondeva.

Ora c'e' un flusso unico, e **niente e' messo in base a che cosa e'**: ogni riga
sta al momento in cui e' successa.

| Riga | Quando |
|---|---|
| l'inserzione cliccata | il first touch che ha prodotto, o — per un lead arrivato dal modulo inserzione — la creazione del record |
| first touch / last touch | la loro data |
| ogni visita | `started_on` |
| ogni evento | `occurred_on` |
| **arrivato nel CRM** | `creation` del lead o della trattativa |

### Perche' l'inserzione non sta in cima

All'inizio era fissata in testa, dando per scontato che l'inserzione venga
sempre prima. Non e' vero: una persona puo' leggere una pagina, andarsene, e
incontrare l'inserzione una settimana dopo. Adesso si ordina come tutto il
resto.

Meta non dice mai **quando** l'annuncio e' stato visto, e non e' comunque il
momento utile. Quello utile e' quando ha portato qui la persona: il touch che ha
prodotto. Per un lead che arriva dritto da un modulo inserzione, senza nessuna
navigazione dietro, quel momento e' la creazione del record — lo stesso fatto
raccontato dall'altro lato.

### La riga che mancava

`get_journey` restituisce anche `created_on`. Per un lead da modulo inserzione
**e' tutto il percorso che esiste**: non c'e' niente da navigare, quello che c'e'
da sapere e' quando e' arrivato e da cosa. E anche dove la navigazione c'e', e'
la riga che dice quando ha smesso di essere anonima.

### Piatta invece che annidata

`buildTimeline` sostituisce `groupJourney`. Gli eventi stavano sotto la loro
visita solo per dire da quale campagna venivano, ma in una lista ordinata nel
tempo la visita sta gia' accanto ai propri eventi. Sparisce anche la **visita
finta** che serviva a reggere un evento la cui sessione era caduta fuori dalla
risposta (ne tornano 50): ora compare dove e' successo.

A parita' di secondo l'ordine e' `inserzione → touch → visita → evento →
record`, che e' la sequenza in cui le cose accadono davvero quando un lead da
modulo le stampa tutte nello stesso istante.

## L'inserzione e il first touch sono una riga sola

Erano due righe, e si leggevano come due cose successe: una creativita', e sotto
— con un titolo suo e un orario suo — una sorgente, un mezzo e una campagna che
nominavano **quella stessa creativita'**.

Non e' successo niente due volte. L'attribuzione **e'** l'inserzione che arriva,
scritta nell'altro vocabolario, quindi sta sotto di essa: un'unica riga, la
creativita' in cima e i dati di attribuzione come dettaglio.

Quando c'e' un'inserzione ma nessun first touch a cui appenderla — non dovrebbe
capitare, ma il dato viene da due fonti diverse — l'inserzione tiene la sua
riga. Meglio una riga in piu' che un'informazione persa.

## «No visit recorded» su un lead che non ha mai visitato niente

Per un lead arrivato da un modulo Facebook il pannello diceva:

> Nothing has been recorded for this visitor yet. Check that the tracking script
> is installed on the site this lead came from.

con sotto un pulsante **Set up lead tracking**. Cioe': un avviso che sembra un
guasto, e un invito a sistemare qualcosa — sull'unico tipo di lead in cui non
c'e' niente di rotto. Quella persona ha compilato il modulo **dentro Facebook**
e sul sito non ci e' mai passata: non c'e' nessuna navigazione da mostrare, ed
e' normale.

Ora il caso e' riconosciuto (`first_touch.landing_page == "lead_ad_form"`,
insieme a *CRM UI* e *Third Party* che gia' c'erano) e il pannello dice:

> **No browsing to show** — This person filled in the form inside Facebook and
> never visited the site, so there is no browsing to show — nothing is missing.
> What there is to know is above: the ad, the campaign, and when the lead
> arrived.

senza nessun pulsante da premere.

Il pulsante, dove ha ancora senso, non si chiama piu' *Set up lead tracking* ma
**Open tracking settings**: dice quello che fa — apre le impostazioni — invece di
suggerire che ci sia qualcosa da riparare.

## «Lead created» non puo' venire prima dell'inserzione che l'ha creato

Un lead da modulo inserzione produce l'inserzione, l'attribuzione e la riga del
record **nello stesso secondo o due**, ognuno timbrato da chi lo ha scritto:
l'attribuzione quando il lead viene marcato, la riga quando viene inserito.
Quale dei due orologi vinca e' arbitrario — e quando vinceva quello del record,
la timeline diceva che il lead era stato creato **prima** dell'inserzione che
l'ha prodotto. Che non puo' essere successo.

Dentro una finestra di due minuti quelle tre righe sono trattate per quello che
sono — **un solo momento** — e l'ordine viene da cosa causa cosa: l'inserzione e'
stata vista, e' stata accreditata, il record e' comparso.

Oltre la finestra tornano eventi separati e decide l'orologio, perche' li'
significa qualcosa: chi ha letto una pagina e ha incontrato l'inserzione una
settimana dopo lo ha fatto davvero in quell'ordine.

La finestra vale solo fra inserzione, touch e record. Una visita o un evento non
vengono piegati: quelli hanno un orario loro che e' un fatto.

## «Guest created this lead»

Un lead da un modulo Meta, un messaggio WhatsApp da uno sconosciuto, una
prenotazione dalla pagina pubblica: sono tutti creati **senza nessuno
loggato**, quindi Frappe timbra `Guest` sul record.

E' tecnicamente vero e inutile. Guest non e' una persona, non si puo' chiedere
niente a Guest, e in mezzo a una lista di nomi si legge come un errore — o
peggio, come se qualcuno da fuori fosse entrato.

Un record creato senza nessuno loggato appartiene al **sistema**.
`Administrator` e' il nome che Frappe da' a quello, esiste su ogni sito e non
richiede di creare o configurare niente.

Un hook solo (`credit_the_system`) su CRM Lead, CRM Deal e Contact, e funziona
per tutte le strade che passano da li' — webhook, moduli, prenotazioni — invece
di una correzione in ogni punto che crea qualcosa. `set_user_and_timestamp()`
gira **prima** di `before_insert`, quindi riscrivere il campo li' e' quello che
finisce nel database; c'e' un test che se ne accorge se Frappe cambia l'ordine.

Una patch sistema i 16 lead e i 16 contatti gia' timbrati.
