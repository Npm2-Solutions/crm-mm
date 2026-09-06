# 15 — Sito web vetrina, integrato nel CRM

> **Stato: proposta, decisioni D1–D3 prese il 06/09/2026.** Ricerca condotta a settembre
> 2026, con lettura diretta del codice di [frappe/builder](https://github.com/frappe/builder).
> Riapre in forma *ridotta* il modulo [01](./01-funnel-landing-builder.md) (funnel
> builder), che resta fuori scope: qui non si parla di funnel multi-step, A/B test o
> checkout, ma di **un sito web semplice che vive dei dati del CRM**.

## 1. Cosa serve davvero

La richiesta, tradotta in requisiti:

| # | Requisito | Nota |
|---|---|---|
| R1 | Creare un **sito web semplice** (poche pagine: home, servizi, chi siamo, contatti) | non un designer libero stile Figma |
| R2 | Le pagine contengono **form del CRM** che generano Lead/Deal | "via embed? va trovata la via corretta" → §8.1 |
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
  ambiente ristretto; si popola una variabile `data` (`data.servizi = …`) e si lega un
  blocco a una chiave dati (**una sola `data key` per blocco**, cfr.
  [issue #289](https://github.com/frappe/builder/issues/289)) per ottenere la ripetizione.
- **Cosa Builder non è**: un funnel builder (niente step, A/B, checkout) e **non è
  integrabile dentro la nostra SPA**: è un'altra applicazione, con un'altra UI, su
  un'altra rotta, con un altro modello di permessi.

### 3.2 Il page builder **nativo** di Frappe

`Web Page` con **Content Type = "Page Builder"** ha una child table di blocchi
(`Web Page Block`) in cui ogni riga punta a un **`Web Template`** (record con template
Jinja + campi tipizzati in `Web Template Field`); i valori del blocco si compilano da un
dialog "Edit Values". Un'app può spedire i propri Web Template come record standard.
Fonte: [Web Page Builder](https://docs.frappe.io/erpnext/web-page-builder).

Il modello dati "pagina = lista ordinata di sezioni tipizzate" **esiste già nel framework**,
con routing, SEO, sitemap e cache inclusi. Quello che non dà è la *chrome* (navbar/footer/
tema Bootstrap del sito) né un editor decente. Vedi §4: **Frappe stessa non lo usa** per il
suo prodotto di page building.

### 3.3 Web Form nativi

Restano il motore di submission (validazione, guest, pagamenti via `frappe/payments`),
ma esteticamente basici — ed è **esattamente la scelta già fatta in questo repo**: i form
CRM usano `Web Form` come storage e `crm_published` per impedire che sia il framework a
renderizzarli, servendoli invece da una pagina nostra (`/crm-form/<route>`).

## 4. Come lo fa Frappe — letto nel codice di Builder

Prima di decidere D1 (doctype nostri o `Web Page` nativo?) vale la pena guardare cosa fa
Frappe quando costruisce sul serio un page builder. Clonata la repo, la risposta è netta.

### 4.1 Builder **non** usa il `Web Page` nativo

```python
# builder/builder/doctype/builder_page/builder_page.py
class BuilderPage(WebsiteGenerator): ...

# builder/hooks.py
website_generators   = ["Builder Page"]
website_path_resolver = "…builder_page.resolve_path"
page_renderer         = "…builder_page.BuilderPageRenderer"
get_website_user_home_page = "…builder_settings.get_website_user_home_page"
```

Doctype proprio, registrato come website generator. Quattro hook lavorano insieme:
il **generator** dà la rotta e la pubblicazione, il **path resolver** intercetta la
risoluzione dei percorsi, il **page renderer** (`BuilderPageRenderer(DocumentPage)`)
gestisce le rotte dinamiche `:parametro`, e **`get_website_user_home_page`** fa sì che
la home sia semplicemente *una rotta salvata nelle impostazioni*.

### 4.2 Il template è un documento HTML completo

`builder/templates/generators/webpage.html` comincia con `<!DOCTYPE html>` e si scrive
da sé `<head>`, favicon, font, reset.css, meta tag. **Nessun `web.html`, nessuna navbar
del sito Frappe, nessun Website Theme.** Builder rifiuta la chrome del framework
esattamente come la rifiutano — già oggi — le nostre pagine `crm_form.html` e `book.html`.

### 4.3 Il contenuto è JSON, non una child table

Due campi `Long Text`: `blocks` (ciò che è pubblicato) e `draft_blocks` (ciò che stai
modificando). Il publish è tre righe:

```python
def publish(self):
    self.published, self.published_at = 1, now()
    if self.draft_blocks:
        take_snapshot(…, snapshot_type="Publish")   # 25 conservati per pagina
        self.blocks = self.draft_blocks
        self.draft_blocks = None
    self.save()
```

E il restore di uno snapshot rientra **nel draft**, non in produzione. È il modello
publish/preview giusto, e con una child table sarebbe scomodo da ottenere.

### 4.4 Il rendering è server-side, e passa da Jinja

`get_block_html()` trasforma l'albero dei blocchi in HTML con BeautifulSoup
(`build_tag` → `create_html_tag`), accumulando le classi in un `<style>`; poi
`render_template(content, page_data)` fa passare quell'HTML **dentro Jinja**. I binding
dinamici sono compilati come placeholder Jinja dentro l'HTML generato; una lista è un
blocco con `isRepeaterBlock` e `dataKey.key` su cui `render_children` cicla.

I Data Script girano con `safe_exec` (o `safer_exec`), cioè il Python ristretto del
framework: **è codice, non configurazione**, e non è roba da utente finale.

### 4.5 Quanto pesa

| | righe | file |
|---|---|---|
| frontend (Vue + TS) | **44.149** | 294 |
| backend (Python) | **23.456** | — |

Sessantottomila righe. Questo chiude l'opzione "copiare Builder dentro il CRM".

### 4.6 Cosa ne ricaviamo

| Prendiamo | Lasciamo |
|---|---|
| doctype proprio + `WebsiteGenerator` + hook di routing | l'albero di blocchi arbitrario con CSS libero |
| documento HTML completo, chrome nostra | la generazione HTML con BeautifulSoup (i nostri blocchi sono `include` Jinja: è il 90% del codice risparmiato) |
| contenuto in JSON, `sections` + `draft_sections` | i Data Script in Python: i nostri blocchi sono tipizzati |
| `publish()` con snapshot, restore nel draft | il versionamento a 25 snapshot (2–3 bastano) |
| home page = una rotta nelle impostazioni (`get_website_user_home_page`) | le rotte dinamiche `:parametro` (ci basta `/servizi/<slug>` via route rule) |
| `is_standard` + `app`: pagine spedite con l'app | l'export/import in developer mode |
| `disable_indexing`, `canonical_url`, `authenticated_access` | — li prendiamo tali e quali |

> **Risposta a D1**: doctype nostri. Non è una preferenza estetica — è la stessa scelta
> che Frappe fa nel suo prodotto di page building, ed è la scelta già fatta due volte in
> questo repo (form e booking).

## 5. Le tre strade

| | **A — Adottare Builder** | **B — Sito nel CRM (sezioni tipizzate)** | **C — Copiare/forkare Builder dentro il CRM** |
|---|---|---|---|
| Sforzo iniziale | basso (install + integrazione dati) | **medio** (3–4 settimane) | altissimo (68k righe) |
| Libertà grafica | massima | media (layout curati, non arbitrari) | massima |
| Rispetta R5/R6 (dentro il CRM, espresso, modale) | **no** — seconda app, altra UI, altre rotte | **sì** | sì, ma… |
| Blocchi CRM-native (servizi, form, booking) | via Data Script Python scritto a mano per sito | **nativi e tipizzati** | nativi |
| Manutenzione | upstream (gratis) | nostra, ma piccola | **nostra, enorme**: si perde l'upstream |
| Onboarding cliente | deve imparare un editor Figma-like | compila sei campi e pubblica | idem A |
| Multi-tenant | +1 app da installare/aggiornare su ogni site | zero (viaggia con il CRM) | zero |
| Rischio | disallineamento UI/permessi, doppio branding | libertà grafica insufficiente per clienti esigenti | progetto che non finisce |

### Decisione — **B, con Builder come opzione accanto**

1. **Si costruisce B**: un *site builder a sezioni* dentro il CRM, in frappe-ui, con le
   impostazioni nel modale. È l'unica opzione che soddisfa R5 e R6, ed è quella che rende
   R2/R3/R4 *facili* invece che *possibili*.
2. **Non si copia Builder**: MIT lo permetterebbe, ma sono 68.000 righe e la fine
   dell'allineamento con l'upstream.
3. **Si lascia la porta aperta**: ogni blocco legge i suoi dati da una **API whitelisted
   guest-safe** (`crm.api.site.*`). Il giorno in cui un cliente vuole il designer libero,
   si installa Builder accanto e le stesse liste si consumano da un Data Script di tre
   righe. Nessun lavoro buttato.

## 6. Architettura proposta

### 6.1 DocType

| DocType | Tipo | Campi principali |
|---|---|---|
| **CRM Website Settings** | Single | `enabled`, `home_page` (rotta), `serve_at_root` (Check — vedi D3), `site_title`, `tagline`, `logo`, `favicon` (default da `FCRM Settings`), `primary_color`, `font`, `nav_items` (child), `footer_text`, dati legali (ragione sociale, P.IVA, indirizzo, email, telefono), `social_links` (child), `privacy_page`/`terms_page`, `ga4_id`, `meta_pixel_id`, `consent_banner`, `default_og_image`, `robots_indexable` |
| **CRM Web Page** | `WebsiteGenerator` | `title`, `route` (unico, validato contro la denylist), `published`, `published_at`, **`sections` (Long Text JSON — pubblicato)**, **`draft_sections` (Long Text JSON — in lavorazione)**, `seo_title`, `seo_description`, `og_image`, `canonical_url`, `disable_indexing`, `authenticated_access`, `is_standard` + `app` |
| **CRM Web Snapshot** | Documento | `reference_page`, `sections`, `label`, `snapshot_type` (Publish/Manual), `created_at` — 3 conservati per pagina |
| **CRM Nav Item / CRM Social Link** | Child | `label`, `link_type` (Pagina/Servizio/Esterno/Ancora), `target`, `open_in_new` |

Una **sezione** nel JSON è un oggetto piatto e tipizzato — non un albero:

```json
{ "type": "servizi", "enabled": true, "title": "Cosa facciamo",
  "props": { "categoria": "Estetica", "solo_prenotabili": true,
             "limite": 6, "layout": "griglia", "mostra_prezzo": "da" } }
```

Validazione sul salvataggio: tipo esistente, props conformi allo schema del tipo, niente
chiavi sconosciute. Il JSON è opaco al database ma è la scelta che rende banale il
draft/publish — la stessa fatta da Builder (§4.3).

Campi **aggiunti a `CRM Service`** (questo è R4, il "pulsante per pubblicarlo"):

```
website_section     (Section Break "Sito web")
publish_on_website  (Check)        ← l'interruttore
website_slug        (Data, unico)  ← auto da service_name
website_image       (Attach Image)
short_description   (Small Text)   ← per la card in lista
website_description (Text Editor)  ← per la pagina di dettaglio
gallery             (Table: CRM Web Image)
price_display       (Select: Nascondi | Prezzo | "a partire da")
booking_calendar    (Link → CRM Booking Calendar)   ← vedi D4
cta_type            (Select: Prenota | Form | Link | Nessuno)
cta_target          (Dynamic Link → Web Form / URL)
website_order       (Int)
seo_title, seo_description
```

Gli stessi campi su `CRM Product` (che ha già `image` e `description`).
**Nessuna duplicazione del catalogo**: la fonte resta il doctype di sistema, il sito è
una *vista pubblicata* di quel dato. Modifichi il prezzo in agenda → cambia sul sito.

### 6.2 Routing e rendering (server-side, non SPA)

- `CRM Web Page` è un **WebsiteGenerator** registrato con `website_generators` in
  `hooks.py`: risoluzione della rotta, 404 e sitemap le fa il framework.
- **Home configurabile (D3)**: `serve_at_root` acceso → si registra
  `get_website_user_home_page` che restituisce la rotta di `home_page`, e il sito prende
  `/`; spento → il sito vive sotto le sue rotte e la radice resta al framework. Un
  interruttore, nessuna scelta irreversibile, e il CRM resta comunque su `/crm`.
- **Denylist di slug** in `validate()`: `crm`, `api`, `app`, `assets`, `files`, `book`,
  `crm-form`, `whatsapp-connect`, `login`, `privacy`, `terms`, `_builder`.
- Rotte di catalogo via `website_route_rules`, accanto a quelle esistenti:
  `/servizi` (indice), `/servizi/<slug>` (dettaglio), `/prodotti[/<slug>]`.
- **Un solo base template** `crm/templates/site/base.html`, documento HTML completo, con i
  token espresso estratti dalle due copie attuali in `crm_form.html` e `book.html` →
  `crm/public/site/site.css`, più le override di brand iniettate come CSS custom properties.
  Header/footer del sito vivono lì: le pagine di form e booking **ereditano la stessa
  chrome**, e per la prima volta il sito, i form e il booking sembrano lo stesso sito.
- Ogni tipo di sezione è un include: `crm/templates/site/sections/<tipo>.html`, che riceve
  `section` (props deserializzate) e i dati già risolti dal controller. Nessun BeautifulSoup,
  nessun compilatore di stili: è la semplificazione che ci fa costare un decimo di Builder.
- Zero JavaScript di framework sulle pagine pubbliche: HTML+CSS, un filo di JS solo dove
  serve (menu mobile, form, slot di prenotazione).

### 6.3 L'editor, dentro il modale Impostazioni

Nuovo gruppo **"Sito web"** in `Settings.vue`, dopo "Agenda"/"Booking":

| Voce | Componente | Cosa fa |
|---|---|---|
| **Sito** | `Settings/Website/WebsiteSettings.vue` | interruttore generale, home e radice, logo/colore/font, menu di navigazione (drag), footer e dati legali, SEO di default, analytics e consenso |
| **Pagine** | `Settings/Website/PagesList.vue` + `PageEditor.vue` | lista pagine (stato, rotta, "apri"), editor a due colonne: a sinistra le sezioni come card riordinabili (`vuedraggable`, come `FormBuilderPanel`), a destra i campi della sezione selezionata; in alto anteprima desktop/mobile, **Salva bozza** e **Pubblica** |
| **Vetrina** | `Settings/Website/ShowcaseSettings.vue` | tabella di servizi e prodotti con **toggle "Pubblica"**, immagine, ordine trascinabile, link "modifica scheda" |

In più, una scheda **"Sito web"** dentro l'editor di servizio già esistente
(`Settings/Scheduling/ServicesSettings.vue`): immagine, descrizioni, slug, CTA, switch di
pubblicazione. È lì che l'utente si aspetta di trovarla — non in un secondo posto.

### 6.4 Anteprima

Anteprima = **iframe della rotta reale** con `?preview=1` (che rende `draft_sections`
invece di `sections`, visibile solo a chi ha il ruolo), non una ri-implementazione Vue dei
blocchi. Una sola verità di rendering: il Jinja. È lo stesso meccanismo di Builder
(`context.preview` → `draft_blocks`).

## 7. Catalogo dei blocchi

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

## 8. Le integrazioni, una per una

### 8.1 Form: le tre vie dell'embed (R2)

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

### 8.2 Servizi e prodotti dinamici (R3, R4)

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

### 8.3 Attribuzione dei lead — il vero moltiplicatore

Ogni submit dal sito porta con sé: pagina di atterraggio, blocco/form di origine, referrer,
`utm_*`, `gclid`, `fbclid`, `msclkid`. Oggi `CRM Lead` ha `source` ma **non ha campi UTM**:
vanno aggiunti (o una child table `CRM Lead Attribution`, se si vuole il multi-touch).
Con quelli in mano si ottengono, gratis: sorgente reale di ogni deal chiuso, ROI per
campagna, e — con l'integrazione Meta già presente — la **Conversions API server-side**
(evento `Lead` con `event_id` dedupato con il pixel) che è oggi l'unico modo serio di far
ottimizzare le campagne Meta.

### 8.4 Il resto

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
  non per pagina. Da documentare nella procedura di provisioning (modulo 06).

## 9. Come **non** lo farei

1. **Non** un canvas drag-drop libero fatto in casa. Sono mesi di lavoro per arrivare
   dietro a Builder, che è MIT e gratis.
2. **Non** copiare il codice di Builder dentro il CRM: 68.000 righe e la fine
   dell'allineamento con l'upstream (§4.5).
3. **Non** far scrivere Python (Data Script) all'utente per avere una lista di servizi.
   Blocchi tipizzati: l'utente compila campi.
4. **Non** iframe del nostro form sul nostro sito (§8.1).
5. **Non** un campo HTML libero come modello di contenuto: XSS, zero riuso, zero SEO
   strutturata. HTML custom sì, ma come *blocco eccezionale*, sanitizzato e con permesso.
6. **Non** duplicare il catalogo in doctype "solo sito": una sola fonte di verità.
7. **Non** rotta catch-all `/<path>` che scavalca il router del framework: si usa il
   WebsiteGenerator, come fa Builder, più la denylist degli slug.
8. **Non** funnel, A/B, checkout, membership adesso: fuori scope, e l'architettura a
   sezioni non li preclude.
9. **Non** rendere pubblici campi interni (costi, staff, note): le API pubbliche
   espongono una whitelist esplicita di campi, con `rate_limit` come già fa `booking.py`.
10. **Non** una SPA Vue per le pagine pubbliche: SSR, HTML statico e cache.

## 10. Sicurezza, permessi, performance

- Permessi: gestione sito riservata a `Sales Manager`/`System Manager`; le API pubbliche
  sono `allow_guest=True` **in sola lettura**, con campi in whitelist e `rate_limit`.
- Cache: invalidazione della rotta su publish/unpublish del contenuto correlato (pagina,
  servizio, prodotto, impostazioni) — Builder fa esattamente questo in `clear_route_cache`.
- Immagini: `File` privati mai referenziati da pagine pubbliche; upload dal modale con
  `is_private=0` e validazione tipo/peso.
- Anteprima draft: consentita solo ai ruoli di gestione, mai "chiunque con il link".
- Test: unit test sulle funzioni pure (risoluzione slug, denylist, validazione dello
  schema delle sezioni, costruzione JSON-LD) in `frontend/tests/unit` e `crm/tests`,
  come da AGENTS.md.

## 11. Fasi

Deciso (D2): **fase 1 e 2 si consegnano insieme** — un sito senza servizi, form e
prenotazione non è il prodotto di cui stiamo parlando.

| Fase | Contenuto | Stima |
|---|---|---|
| **1 — Fondamenta** | base template unificato + `site.css` con i token espresso estratti; `CRM Website Settings` + pagina "Sito" nel modale; `CRM Web Page` (generator, JSON sezioni, draft/publish, snapshot) + 5 sezioni di contenuto; editor pagine; anteprima | 8–10 gg |
| **2 — Il CRM dentro le pagine** | campi sito su `CRM Service`/`CRM Product` + scheda "Sito web" nell'editor servizio + pagina Vetrina; blocchi Servizi, Prodotti, Form (inline), Prenota; `/servizi[/<slug>]` | 8–10 gg |
| **3 — Crescita** | SEO (meta, OG, JSON-LD, sitemap, robots), attribuzione UTM sui lead + Conversions API, consenso cookie, blocchi FAQ/Galleria/Numeri/Recensioni/Social | 6–8 gg |
| **4 — Opzionale** | blog/news per SEO, multilingua, script embed JS per siti esterni, ponte Builder documentato | su richiesta |

## 12. Decisioni prese, e cosa resta aperto

| | Domanda | Esito (06/09/2026) |
|---|---|---|
| **D1** | Doctype nostri o `Web Page` nativo? | **Doctype nostri** — è ciò che fa Frappe stessa in Builder (§4) e ciò che questo repo fa già per form e booking. |
| **D2** | Ampiezza della prima consegna? | **Fasi 1+2 insieme**, ~3–4 settimane. |
| **D3** | La home del sito prende la radice `/`? | **Configurabile**: interruttore `serve_at_root` in `CRM Website Settings` + hook `get_website_user_home_page`, come Builder. Nessuna scelta irreversibile. |
| **D4** | Servizi vs Calendari di prenotazione | **Aperta.** Oggi il catalogo pubblico di `/book` legge `CRM Booking Calendar` (`show_in_menu`), mentre il catalogo reale è `CRM Service`. Proposta: un campo `booking_calendar` su `CRM Service`, il sito pubblica **i servizi**, e `show_in_menu` viene deprecato. Serve conferma. |
| **D5** | Multi-tenant | **Aperta.** Un sito per site Frappe: se confermato, niente astrazione multi-sito e si risparmia parecchio. |
| **D6** | Builder resta un'opzione documentata? | **Aperta.** Per clienti "design-first" si installa accanto e consuma le stesse API. |

## 13. Compatibilità futura

Le API `crm.api.site.*` (servizi, prodotti, form, slot) sono il contratto: le usano i
nostri template Jinja oggi, potrebbero usarle un Data Script di Builder o una landing
esterna domani. Il modello "pagina = sezioni tipizzate ordinate" è anche il modello su cui
si innesterebbe il layer funnel del [modulo 01](./01-funnel-landing-builder.md) se lo
scope riaprisse: uno step di funnel è una `CRM Web Page` con una variante e un contatore.
