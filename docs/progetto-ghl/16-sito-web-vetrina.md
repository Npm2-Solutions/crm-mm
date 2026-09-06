# 15 — Sito web vetrina, integrato nel CRM

> **Stato: proposta, in attesa di decisione.** Ricerca condotta a settembre 2026.
> Riapre in forma *ridotta* il modulo [01](./01-funnel-landing-builder.md) (funnel
> builder), che resta fuori scope: qui non si parla di funnel multi-step, A/B test o
> checkout, ma di **un sito web semplice che vive dei dati del CRM**.

## 1. Cosa serve davvero

La richiesta, tradotta in requisiti:

| # | Requisito | Nota |
|---|---|---|
| R1 | Creare un **sito web semplice** (poche pagine: home, servizi, chi siamo, contatti) | non un designer libero stile Figma |
| R2 | Le pagine contengono **form del CRM** che generano Lead/Deal | "via embed? va trovata la via corretta" → §7.1 |
| R3 | Le pagine contengono **liste dinamiche di servizi/prodotti** collegate alle liste di sistema | non copie statiche: la fonte resta `CRM Service` / `CRM Product` |
| R4 | Sul servizio: **immagine, descrizione e un pulsante "pubblica"** | il servizio diventa contenuto pubblicabile |
| R5 | È **un'aggiunta al CRM**, integrata bene | nessuna seconda applicazione da imparare |
| R6 | Tutto in **frappe-ui / tema espresso**, impostazioni **dentro il modale Impostazioni** | vincolo di UI, non negoziabile |

Il valore non è nella libertà grafica: è nel **collegamento con il CRM**. Un sito
fatto altrove (WordPress, Webflow) e un CRM separato è ciò che i clienti hanno già;
il vantaggio competitivo è che qui la lista servizi, i prezzi, il calendario di
prenotazione, i form, l'attribuzione dei lead e le automazioni sono **lo stesso dato**.

## 2. Cosa c'è già nel repo (da riusare, non rifare)

Il fork non parte da zero. Esiste già metà dell'infrastruttura di un sito pubblico:

| Pezzo | Dove | Cosa dà |
|---|---|---|
| **Form builder + form pubblici** | `crm/api/form.py`, `crm/www/crm_form.{py,html}`, `Settings → Forms` | costruzione visuale del form, target `CRM Lead`/`CRM Deal`, layout a sezioni/colonne, logica condizionale (`depends_on`), campi Link con opzioni risolte lato server, publish/draft, **snippet iframe + allow-list di domini con CSP `frame-ancestors`** |
| **Pagine di prenotazione pubbliche** | `crm/www/book.{py,html}`, `book_index.{py,html}`, `crm/api/booking.py` | pagina di booking per calendario, indice `/book` dei servizi prenotabili, API guest con `rate_limit`, reschedule/cancel via token |
| **Token grafici espresso su pagina pubblica** | blocco `:root` in `crm_form.html` e `book.html` | il "tema" del sito pubblico esiste già, in due copie da unificare |
| **Catalogo servizi** | `CRM Service` (+ `CRM Booking Calendar`, `CRM Price List`, `CRM Product`) | nome, categoria, descrizione, durata, prezzo, prenotabilità online; `CRM Product` ha già **immagine** e descrizione rich-text |
| **Branding** | `FCRM Settings` (`brand_name`, `brand_logo`, `favicon`) + `Settings → Brand` | logo/nome/favicon già centralizzati |
| **Pagine legali** | fixture `Web Page` `privacy` e `terms` (`hooks.py`) | footer legale già pronto |
| **Meta / social / WhatsApp / tracked links** | `crm/integrations/meta`, `crm/social`, `Settings → Tracked Links` | pixel, condivisione, CTA WhatsApp, attribuzione |
| **Motore automazioni** | `crm/automation/engine.py` (`on_lead_created`, `on_booking_created`, …) | un submit dal sito può far partire una sequenza |

Conclusione: **manca solo il contenitore** — la pagina componibile e il suo editor.

## 3. Fatti verificati (settembre 2026)

### 3.1 Frappe Builder

[frappe/builder](https://github.com/frappe/builder) — editor visuale drag-drop stile Figma.

- **Licenza MIT dalla v1.31** (16/07/2026; prima AGPL-3.0). Ultima release **v1.33.0**
  (28/08/2026): agente AI "Bob" che costruisce/modifica pagine e **fa il wiring dei form**,
  design token, 35 lingue. v1.28 aveva introdotto versionamento pagine, **component script
  con props** e analytics CTR.
- **Dati dinamici**: si scrive un **Data Script in Python**, eseguito **server-side** in
  ambiente ristretto (moduli whitelisted); si popola una variabile `data` (`data.servizi = …`)
  e si lega un blocco a una chiave dati (**una sola `data key` per blocco**, cfr.
  [issue #289](https://github.com/frappe/builder/issues/289)) per ottenere la ripetizione.
  I parametri di rotta arrivano da `frappe.form_dict`.
- **Cosa Builder non è**: un funnel builder (niente step, A/B, checkout) e **non è
  integrabile dentro la nostra SPA**: è un'altra applicazione, con un'altra UI, su
  un'altra rotta, con un altro modello di permessi.

### 3.2 Il page builder **nativo** di Frappe (spesso dimenticato)

`Web Page` con **Content Type = "Page Builder"** ha una child table di blocchi
(`Web Page Block`) in cui ogni riga punta a un **`Web Template`** (record con template
Jinja + campi tipizzati in `Web Template Field`); i valori del blocco si compilano da un
dialog "Edit Values" e finiscono nel contesto del template. Un'app può **spedire i propri
Web Template** come record standard.
Fonte: [Web Page Builder](https://docs.frappe.io/erpnext/web-page-builder).

Tradotto: **il modello dati "pagina = lista ordinata di sezioni tipizzate" esiste già nel
framework**, con routing, SEO, sitemap e cache inclusi. Quello che non dà è la *chrome*
(navbar/footer/tema Bootstrap del sito) né un editor decente.

### 3.3 Web Form nativi

Restano il motore di submission (validazione, guest, pagamenti via `frappe/payments`),
ma esteticamente basici — ed è **esattamente la scelta già fatta in questo repo**: i form
CRM usano `Web Form` come storage e `crm_published` per impedire che sia il framework a
renderizzarli, servendoli invece da una pagina nostra (`/crm-form/<route>`).

## 4. Le tre strade

| | **A — Adottare Builder** | **B — Sito nel CRM (sezioni tipizzate)** | **C — Copiare/forkare Builder dentro il CRM** |
|---|---|---|---|
| Sforzo iniziale | basso (install + integrazione dati) | **medio** (2–3 settimane per la fase 1) | altissimo |
| Libertà grafica | massima | media (layout curati, non arbitrari) | massima |
| Rispetta R5/R6 (dentro il CRM, espresso, modale) | **no** — seconda app, altra UI, altre rotte | **sì** | sì, ma… |
| Blocchi CRM-native (servizi, form, booking) | via Data Script Python scritto a mano per sito | **nativi e tipizzati** | nativi |
| Manutenzione | upstream (gratis) | nostra, ma piccola | **nostra, enorme**: si eredita un editor da 40k righe e si perde l'upstream |
| Onboarding cliente | deve imparare un editor Figma-like | compila 6 campi e pubblica | idem A |
| Multi-tenant | +1 app da installare/aggiornare su ogni site | zero (viaggia con il CRM) | zero |
| Rischio | disallineamento UI/permessi, doppio branding | libertà grafica insufficiente per clienti esigenti | progetto che non finisce |

### Decisione proposta — **B, progettata per convergere in C** (dove C = "Builder accanto, non dentro")

1. **Si costruisce B**: un *site builder a sezioni* dentro il CRM, in frappe-ui, con le
   impostazioni nel modale. È l'unica opzione che soddisfa R5 e R6, ed è quella che rende
   R2/R3/R4 *facili* invece che *possibili*.
2. **Non si copia Builder** (opzione C nel senso di fork): MIT lo permetterebbe, ma si
   erediterebbe un editor enorme senza poter più fare pull dall'upstream.
3. **Si lascia la porta aperta a Builder**: ogni blocco legge i suoi dati da una **API
   whitelisted guest-safe** (`crm.api.site.*`). Il giorno in cui un cliente vuole il
   designer libero, si installa Builder accanto e le stesse liste si consumano da un Data
   Script di tre righe. Nessun lavoro buttato.

> Il modello dati delle pagine è quello del §3.2 (pagina = blocchi tipizzati ordinati).
> Se lo prendiamo dal framework o lo rifacciamo su doctype nostri è la **domanda aperta
> D1** (§11): cambia il costo, non l'architettura.

## 5. Architettura proposta

### 5.1 DocType

Nuovi, tutti nel modulo `FCRM` con prefisso coerente:

| DocType | Tipo | Campi principali |
|---|---|---|
| **CRM Website Settings** | Single | `enabled`, `home_page` (Link a CRM Web Page), `site_title`, `tagline`, `logo`, `favicon` (default da `FCRM Settings`), `primary_color`, `font`, `nav_items` (child), `footer_text`, dati legali (ragione sociale, P.IVA, indirizzo, email, telefono), `social_links` (child), `privacy_page`/`terms_page`, `ga4_id`, `meta_pixel_id`, `consent_banner`, `default_og_image`, `robots_indexable` |
| **CRM Web Page** | Documento con web view | `title`, `route` (unico, validato contro la denylist), `published`, `published_on`, `page_type` (Pagina/Landing), `sections` (child), `seo_title`, `seo_description`, `og_image`, `noindex` |
| **CRM Web Section** | Child table | `section_type` (Select: Hero, Testo, Servizi, Prodotti, Form, Prenota, FAQ, Galleria, CTA, Contatti, Recensioni, Loghi, Numeri, Video, HTML), `enabled`, `title`, `subtitle`, `body` (Text Editor), `image`, `background` (Chiaro/Scuro/Accento), `props` (Long Text, JSON dei parametri specifici del tipo) |
| **CRM Nav Item / CRM Social Link** | Child | `label`, `link_type` (Pagina/Servizio/Esterno/Ancora), `target`, `open_in_new` |

Campi **aggiunti a `CRM Service`** (questo è R4, il "pulsante per pubblicarlo"):

```
website_section  (Section Break "Sito web")
publish_on_website (Check)      ← l'interruttore
website_slug     (Data, unico)  ← auto da service_name
website_image    (Attach Image)
short_description(Small Text)   ← per la card in lista
website_description (Text Editor) ← per la pagina di dettaglio
gallery          (Table: CRM Web Image)
price_display    (Select: Nascondi | Prezzo | "a partire da")
cta_type         (Select: Prenota | Form | Link | Nessuno)
cta_target       (Dynamic Link → CRM Booking Calendar / Web Form / URL)
website_order    (Int)
seo_title, seo_description (Data / Small Text)
```

Gli stessi campi su `CRM Product` (che ha già `image` e `description`).
**Nessuna duplicazione del catalogo**: la fonte resta il doctype di sistema, il sito è
una *vista pubblicata* di quel dato. Modifichi il prezzo in agenda → cambia sul sito.

### 5.2 Routing e rendering (server-side, non SPA)

- `CRM Web Page` è un **Website Generator** (`has_web_view`, `is_published_field: published`,
  campo `route`): la risoluzione della rotta, la 404 e la sitemap le fa il framework.
- Rotte di catalogo via `website_route_rules` in `hooks.py`, accanto a quelle esistenti:
  `/servizi` (indice), `/servizi/<slug>` (dettaglio servizio), `/prodotti[/<slug>]`.
- **Un solo base template** `crm/templates/site/base.html` con i token espresso estratti
  dalle due copie attuali in `crm_form.html` e `book.html` → `crm/public/site/site.css`,
  più le override di brand iniettate come CSS custom properties da `CRM Website Settings`.
  Header/footer del sito vivono lì: le pagine di form e booking **ereditano la stessa
  chrome**, e per la prima volta il sito, i form e il booking sembrano lo stesso sito.
- Ogni tipo di sezione è un include: `crm/templates/site/sections/<tipo>.html`, che riceve
  `section` (i campi + `props` già deserializzati) e i dati già risolti dal controller.
- Zero JavaScript di framework sulle pagine pubbliche: HTML+CSS, un filo di JS solo dove
  serve (menu mobile, form, slot di prenotazione). Pagine veloci = SEO e conversione.

### 5.3 L'editor, dentro il modale Impostazioni

Nuovo gruppo **"Sito web"** in `Settings.vue`, dopo "Agenda"/"Booking":

| Voce | Componente | Cosa fa |
|---|---|---|
| **Sito** | `Settings/Website/WebsiteSettings.vue` | interruttore generale, dominio, logo/colore/font, menu di navigazione (drag), footer e dati legali, SEO di default, analytics e consenso |
| **Pagine** | `Settings/Website/PagesList.vue` + `PageEditor.vue` | lista pagine (stato, rotta, "apri"), editor a due colonne: a sinistra le sezioni come card riordinabili (`vuedraggable`, come `FormBuilderPanel`), a destra i campi della sezione selezionata; in alto anteprima desktop/mobile e switch **Pubblica** |
| **Vetrina** | `Settings/Website/ShowcaseSettings.vue` | tabella di servizi e prodotti con **toggle "Pubblica"**, immagine, ordine trascinabile, link "modifica scheda" |

In più, una scheda **"Sito web"** dentro l'editor di servizio già esistente
(`Settings/Scheduling/ServicesSettings.vue`): immagine, descrizioni, slug, CTA, switch di
pubblicazione. È lì che l'utente si aspetta di trovarla — non in un secondo posto.

Riuso stretto di ciò che esiste: `FormBuilderPanel.vue` ha già il pattern
canvas+pannello+anteprima+publish; l'editor pagina ne è il fratello.

### 5.4 Anteprima

Anteprima = **iframe della rotta reale** con `?preview=<token>` (le pagine draft sono
visibili solo a chi ha il ruolo), non una ri-implementazione Vue dei blocchi. Una sola
verità di rendering: il Jinja. Costa poco ed evita il classico "in anteprima era diverso".

## 6. Catalogo dei blocchi

**Contenuto**: Hero (titolo, sottotitolo, immagine/video di sfondo, 2 CTA) · Testo
rich-text · Immagine+testo alternati · Galleria · Video/embed · FAQ (accordion, con
JSON-LD `FAQPage`) · Loghi/partner · Numeri/statistiche · Recensioni (statiche ora, dal
modulo reputation quando/se rientrerà) · CTA a tutta larghezza · HTML custom (solo Sales
Manager, sanitizzato).

**Collegati al CRM** (il motivo per cui esiste tutto questo):

| Blocco | Fonte dati | Parametri (`props`) |
|---|---|---|
| **Servizi** | `CRM Service` con `publish_on_website=1` | categoria, solo prenotabili, limite, ordine, layout griglia/lista/carosello, mostra prezzo, testo CTA |
| **Prodotti** | `CRM Product` non disabilitati | categoria, limite, mostra prezzo (listino o `standard_rate`) |
| **Form** | un `Web Form` CRM pubblicato | quale form, titolo/sottotitolo override, redirect post-invio |
| **Prenota** | `CRM Booking Calendar` | quale calendario, inline (widget slot) o CTA verso `/book/<route>` |
| **Contatti** | `CRM Website Settings` | mappa (Leaflet, già in dipendenza), telefono/email/WhatsApp cliccabili, orari |
| **WhatsApp** | numero da impostazioni | testo precompilato per `wa.me`, floating o inline |
| **Ultimi post** | `CRM Social Post` pubblicati | rete, limite — la vetrina social senza embed di terze parti |

Ogni blocco è **tipizzato**: l'utente compila campi, non scrive Python. È la differenza
sostanziale rispetto ai Data Script di Builder — e il motivo per cui il nostro sito è
*più facile* del loro pur essendo *meno libero*.

## 7. Le integrazioni, una per una

### 7.1 Form: le tre vie dell'embed (R2)

| Via | Quando | Stato |
|---|---|---|
| **Inline server-side** — il blocco Form renderizza i campi nella pagina, stesso dominio, stesso CSS | **sul nostro sito, sempre** | da fare: estrarre da `crm_form.html` una macro Jinja condivisa fra la pagina form standalone e il blocco |
| **iframe** — `<iframe src="/crm-form/<route>?embed=1">` con allow-list di domini e CSP `frame-ancestors` | sito esterno del cliente (WordPress, Wix) | **già fatto** |
| **Script JS** — `<script src="/assets/crm/embed.js" data-form="…">` che monta il form inline nell'host e fa POST cross-origin | sito esterno che vuole zero cornice | solo su richiesta: richiede CORS, gestione CSRF, versionamento dello script |

**Perché inline e non iframe sul nostro sito**: l'iframe costa un secondo documento, non
eredita i font, non si autodimensiona senza `postMessage`, rompe l'autofill del browser,
è invisibile ai motori di ricerca e complica il tracking delle conversioni (il pixel sta
nel frame sbagliato). Su un dominio diverso l'isolamento è un pregio; sul proprio è solo
un difetto.

Una macro sola, due host: nessuna seconda implementazione del form da mantenere.

### 7.2 Servizi e prodotti dinamici (R3, R4)

- La lista è **risolta a ogni render** dal doctype: nessuna copia, nessuna sincronizzazione.
- Il "pulsante pubblica" è `publish_on_website`; finché è spento il servizio non esce da
  nessuna API pubblica (niente contenuti draft indicizzati per sbaglio).
- Pagina di dettaglio `/servizi/<slug>` generata dallo stesso motore di sezioni, con un
  layout di default (hero + descrizione + galleria + prezzo + CTA prenota/form + servizi
  correlati) che si può sovrascrivere per singolo servizio.
- CTA "Prenota" → `/book/<route>` del calendario collegato: l'appuntamento nasce già in
  agenda, con il servizio giusto, la durata giusta e lo staff giusto. **Questo è il pezzo
  che nessun WordPress fa.**
- JSON-LD `Service` / `Product` + `Offer` su ogni scheda: rich snippet gratis.

### 7.3 Attribuzione dei lead — il vero moltiplicatore

Ogni submit dal sito porta con sé: pagina di atterraggio, blocco/form di origine, referrer,
`utm_*`, `gclid`, `fbclid`, `msclkid`. Oggi `CRM Lead` ha `source` ma **non ha campi UTM**:
vanno aggiunti (o una child table `CRM Lead Attribution`, se si vuole il multi-touch).
Con quelli in mano si ottengono, gratis: sorgente reale di ogni deal chiuso, ROI per
campagna, e — con l'integrazione Meta già presente — la **Conversions API server-side**
(evento `Lead` con `event_id` dedupato con il pixel) che è oggi l'unico modo serio di far
ottimizzare le campagne Meta.

### 7.4 Il resto

- **Automazioni**: form o prenotazione dal sito → `on_lead_created`/`on_booking_created`
  già esistenti → email/WhatsApp di benvenuto, task all'agente, iscrizione a una sequenza.
- **WhatsApp**: CTA `wa.me` con testo precompilato che cita la pagina; il messaggio in
  arrivo atterra nell'inbox CRM già collegato.
- **Social**: alla pubblicazione di una pagina o di un servizio, offrire "condividi" che
  precompila un `CRM Social Post` con URL, titolo e immagine → il planner fa il resto.
- **Tracked Links**: le CTA verso l'esterno possono passare dai link tracciati già presenti.
- **Legale/GDPR**: banner cookie che **gate-a** il caricamento di GA4/Pixel (niente script
  prima del consenso), checkbox di consenso nel form salvata sul lead, footer che punta
  alle `Web Page` `privacy`/`terms` già spedite come fixture.
- **Dominio**: il dominio custom è a livello di site Frappe (`bench setup add-domain`),
  non per pagina; con `home_page` in `CRM Website Settings` la home del sito diventa la
  radice `/`. Da documentare nella procedura di provisioning (modulo 06).

## 8. Come **non** lo farei

1. **Non** un canvas drag-drop libero fatto in casa. Sono mesi di lavoro per arrivare
   dietro a Builder, che è MIT e gratis.
2. **Non** copiare il codice di Builder dentro il CRM: si eredita un editor enorme e si
   perde per sempre l'allineamento con l'upstream.
3. **Non** far scrivere Python (Data Script) all'utente per avere una lista di servizi.
   Blocchi tipizzati: l'utente compila campi.
4. **Non** iframe del nostro form sul nostro sito (§7.1).
5. **Non** un campo HTML libero come modello di contenuto: XSS, zero riuso, zero SEO
   strutturata. HTML custom sì, ma come *blocco eccezionale*, sanitizzato e con permesso.
6. **Non** duplicare il catalogo in doctype "solo sito": una sola fonte di verità.
7. **Non** rotta catch-all `/<path>` che scavalca il router del framework; e denylist
   obbligatoria per gli slug (`crm`, `api`, `app`, `assets`, `files`, `book`, `crm-form`,
   `whatsapp-connect`, `login`, `privacy`, `terms`, …).
8. **Non** funnel, A/B, checkout, membership adesso: fuori scope, e l'architettura a
   sezioni non li preclude.
9. **Non** rendere pubblici campi interni (costi, staff, note): le API pubbliche
   espongono una whitelist esplicita di campi, con `rate_limit` come già fa `booking.py`.
10. **Non** una SPA Vue per le pagine pubbliche: SSR, HTML statico e cache.

## 9. Sicurezza, permessi, performance

- Permessi: gestione sito riservata a `Sales Manager`/`System Manager`; le API pubbliche
  sono `allow_guest=True` **in sola lettura**, con campi in whitelist e `rate_limit`.
- Cache: `Website Page Cache` invalidata su publish/unpublish del contenuto correlato
  (pagina, servizio, prodotto, impostazioni).
- Immagini: `File` privati mai referenziati da pagine pubbliche; upload dal modale con
  `is_private=0` e validazione tipo/peso.
- Anteprima draft: token firmato a scadenza, mai "chiunque con il link".
- Test: unit test sulle funzioni pure (risoluzione slug, denylist, serializzazione
  `props`, costruzione JSON-LD) in `frontend/tests/unit` e `crm/tests`, come da AGENTS.md.

## 10. Fasi

| Fase | Contenuto | Stima |
|---|---|---|
| **1 — Fondamenta** | base template unificato + `site.css` con i token espresso estratti; `CRM Website Settings` + pagina "Sito" nel modale; `CRM Web Page` + 5 sezioni (Hero, Testo, Immagine+testo, CTA, Contatti); editor pagine; publish | 8–10 gg |
| **2 — Il CRM dentro le pagine** | campi sito su `CRM Service`/`CRM Product` + scheda "Sito web" nell'editor servizio + pagina Vetrina; blocchi Servizi, Prodotti, Form (inline), Prenota; `/servizi[/<slug>]` | 8–10 gg |
| **3 — Crescita** | SEO (meta, OG, JSON-LD, sitemap, robots), attribuzione UTM sui lead + Conversions API, consenso cookie, blocchi FAQ/Galleria/Numeri/Recensioni/Social | 6–8 gg |
| **4 — Opzionale** | blog/news per SEO, multilingua, script embed JS per siti esterni, ponte Builder documentato | su richiesta |

Fase 1+2 = un sito vetrina vendibile. Ogni fase è indipendente e rilasciabile.

## 11. Domande aperte (da decidere prima di scrivere codice)

- **D1 — Modello pagina**: doctype nostri (`CRM Web Page` + `CRM Web Section`, controllo
  totale su chrome e campi, come già fatto per form e booking) **oppure** `Web Page`
  nativo + nostri `Web Template` (meno codice, ma si eredita la chrome del sito Frappe e
  i tipi di campo dei Web Template)? *Raccomandazione: doctype nostri* — è la scelta già
  fatta due volte in questo repo, e la coerenza grafica con espresso è un requisito.
- **D2 — Ampiezza fase 1**: solo pagine statiche + servizi, o subito anche form e booking
  inline? *Raccomandazione: fase 1+2 insieme*, perché è la combinazione che si vende.
- **D3 — Home del site**: la home del sito diventa la radice `/` del site Frappe (e il CRM
  resta su `/crm`), o il sito vive sotto un prefisso (`/sito/...`) finché non c'è un
  dominio dedicato?
- **D4 — Servizi vs Calendari di prenotazione**: oggi il catalogo pubblico di `/book` legge
  `CRM Booking Calendar` (`show_in_menu`), mentre il catalogo reale è `CRM Service`. Il
  sito deve pubblicare **i servizi** e collegarli al calendario; va decisa la mappatura
  (un campo `booking_calendar` su `CRM Service`?) e se `show_in_menu` va deprecato.
- **D5 — Multi-tenant**: ogni cliente ha già il proprio site, quindi un sito per site.
  Confermato? (se sì, niente astrazione multi-sito, e si risparmia molto).
- **D6 — Builder**: lo teniamo come opzione documentata per i clienti "design-first",
  o lo escludiamo del tutto?

## 12. Compatibilità futura

Le API `crm.api.site.*` (servizi, prodotti, form, slot) sono il contratto: le usano i
nostri template Jinja oggi, potrebbero usarle un Data Script di Builder o una landing
esterna domani. Il modello "pagina = sezioni tipizzate ordinate" è anche il modello su cui
si innesterebbe il layer funnel del [modulo 01](./01-funnel-landing-builder.md) se lo
scope riaprisse: uno step di funnel è una `CRM Web Page` con una variante e un contatore.
