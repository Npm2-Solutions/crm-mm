# 16 — Sito web vetrina, integrato nel CRM

> **Stato: implementato (fase 1+2) il 06/09/2026.** Cosa c'è nel repo e dove: §13.
> La proposta che segue resta come racconto delle decisioni.
>
> Stato precedente: proposta rivista il 06/09/2026 dopo lettura del codice di
> [frappe/builder](https://github.com/frappe/builder).** La prima stesura proponeva di
> costruire un motore di pagine dentro il CRM; due scoperte nel codice di Builder l'hanno
> ribaltata (§4.7, §4.8). Ora la proposta è: **Builder è la tela, il CRM è il guscio e i dati.**
> Riapre in forma ridotta il modulo [01](./01-funnel-landing-builder.md): niente funnel,
> A/B test o checkout.

## 1. Cosa serve davvero

| # | Requisito | Nota |
|---|---|---|
| R1 | Creare un **sito web semplice** (home, servizi, chi siamo, contatti) | non serve un designer libero, ma se arriva gratis non è un male |
| R2 | Le pagine contengono **form del CRM** che generano Lead/Deal | §8.1 |
| R3 | Le pagine contengono **liste dinamiche di servizi/prodotti** collegate alle liste di sistema | la fonte resta `CRM Service` / `CRM Product` |
| R4 | Sul servizio: **immagine, descrizione e un pulsante "pubblica"** | il servizio diventa contenuto pubblicabile |
| R5 | È **un'aggiunta al CRM**, integrata bene | nessuna seconda applicazione *da imparare* |
| R6 | Tutto in **frappe-ui / tema espresso**, impostazioni **dentro il modale Impostazioni** | **si piega su un punto solo**: la tela di disegno non può stare nel modale (§5.3) |

Il valore non è nella libertà grafica: è nel **collegamento con il CRM**. Un sito fatto
altrove e un CRM separato è ciò che i clienti hanno già; qui lista servizi, prezzi,
calendario, form, attribuzione dei lead e automazioni sono **lo stesso dato**.

## 2. Cosa c'è già nel repo (da riusare, non rifare)

| Pezzo | Dove | Cosa dà |
|---|---|---|
| **Form builder + form pubblici** | `crm/api/form.py`, `crm/www/crm_form.{py,html}`, `Settings → Forms` | costruzione visuale del form, target `CRM Lead`/`CRM Deal`, layout a sezioni/colonne, logica condizionale, publish/draft, **snippet iframe + allow-list di domini con CSP `frame-ancestors`** |
| **Prenotazione pubblica** | `crm/www/book.{py,html}`, `crm/api/booking.py` | pagina per calendario, indice `/book`, API guest con `rate_limit`, reschedule/cancel via token |
| **Token grafici espresso** | blocco `:root` in `crm_form.html` e `book.html` | il tema delle pagine pubbliche esiste già, in due copie |
| **Catalogo** | `CRM Service`, `CRM Product`, `CRM Booking Calendar`, `CRM Price List` | `CRM Product` ha già immagine e descrizione rich-text |
| **Branding** | `FCRM Settings` + `Settings → Brand` | logo, nome, favicon centralizzati |
| **Pagine legali** | fixture `Web Page` `privacy` / `terms` | footer legale pronto |
| **Meta, social, WhatsApp, tracked links** | `crm/integrations/meta`, `crm/social` | pixel, Conversions API, planner, CTA |
| **Automazioni** | `crm/automation/engine.py` | `on_lead_created`, `on_booking_created` già agganciabili |
| **Tracciamento e attribuzione** | `crm/public/js/tracker.js`, `CRM Visitor Session`, `first_touch_*` / `last_touch_*` ([modulo 15](./15-tracciamento-lead.md)) | provenienza dei lead già risolta: al sito basta montare il tracker |

## 3. Fatti verificati (settembre 2026)

**Frappe Builder** — MIT dalla **v1.31** (16/07/2026), ultima **v1.33.0** (28/08/2026):
agente AI "Bob", design token, versionamento pagine, component script con props,
analytics CTR, 35 lingue. Rilasci **quindicinali**.

**Page builder nativo del framework** — `Web Page` con Content Type "Page Builder" e
blocchi che puntano a `Web Template` tipizzati
([doc](https://docs.frappe.io/erpnext/web-page-builder)). Esiste, ma §4.1 mostra che
Frappe stessa non lo usa.

**Web Form nativi** — restano il motore di submission; è già la scelta di questo repo
(i form CRM usano `Web Form` come storage con `crm_published`).

## 4. Come lo fa Frappe — letto nel codice di Builder

### 4.1 Builder non usa il `Web Page` nativo

```python
class BuilderPage(WebsiteGenerator): ...

website_generators         = ["Builder Page"]
website_path_resolver      = "…builder_page.resolve_path"
page_renderer              = "…BuilderPageRenderer"      # rotte dinamiche :parametro
get_website_user_home_page = "…get_website_user_home_page"
```

### 4.2 Rifiuta la chrome del framework

`templates/generators/webpage.html` comincia da `<!DOCTYPE html>` e si scrive da sé head,
favicon, font, reset. Nessun `web.html`, nessun Website Theme — come già fanno
`crm_form.html` e `book.html`.

### 4.3 Il contenuto è JSON, non una child table

`blocks` (pubblicato) + `draft_blocks` (bozza). Il publish è tre righe: snapshot, promuovi
la bozza, azzera. Il restore di uno snapshot rientra **nella bozza**, non in produzione.

### 4.4 Rendering server-side, poi Jinja

`get_block_html()` costruisce l'HTML con BeautifulSoup; `render_template()` lo fa passare
in Jinja. I binding sono placeholder Jinja compilati nell'HTML; una lista è un blocco con
`isRepeaterBlock` + `dataKey`.

### 4.5 Quanto pesa

**44.149** righe Vue/TS (294 file) + **23.456** righe Python. Copiarlo dentro il CRM non è
un'opzione; *forkarlo* con un diff sottile è un'altra cosa (§5.4).

### 4.6 L'editor assume di possedere la scheda del browser

- SPA a `/builder/page/:pageId` — il path è configurabile (`frappe.conf.builder_path`).
- **Nessun sistema di plugin, nessuna modalità embed, nessun `postMessage`.**
- Su permesso mancante fa `window.location.href = "/app"` — dentro un iframe è un problema.
- `PageBuilder.vue` è `h-screen w-screen` e **rifiuta gli schermi piccoli**:
  *"Screen too small — please switch to a larger screen to edit"*.

### 4.7 ⭐ Un'app può spedire a Builder i propri componenti — con il loro data script

```python
# builder/export_import_standard_page.py
pages_path      = os.path.join(app_path, "builder_files", "pages")
components_path = os.path.join(app_path, "builder_files", "components")
scripts_path    = os.path.join(app_path, "builder_files", "client_scripts")
fonts_path      = os.path.join(app_path, "builder_files", "fonts")
variables_path  = os.path.join(app_path, "builder_files", "variables")
```

`after_app_install(app_name)` li sincronizza. E `Builder Component` ha il campo
**`component_data_script`**, che *riceve le props dell'istanza e riempie i binding
`component.*`*.

**Questo ribalta l'obiezione principale contro Builder.** Non è vero che il cliente deve
scrivere Python per avere una lista di servizi: il data script lo scriviamo **noi**, una
volta, e lo spediamo dentro `crm/builder_files/components/`. Il cliente trascina il
componente "Servizi CRM", imposta le props (categoria, limite, layout, mostra prezzo) e ha
la sua lista dinamica. Esattamente la UX che volevo ottenere con i blocchi tipizzati — ma
senza scrivere il motore di pagine.

### 4.8 ⭐ Builder **è** frappe-ui

```js
// builder/frontend/tailwind.config.js
import frappeUIPreset from "frappe-ui/tailwind";
export default { presets: [frappeUIPreset], … }
```

`frappe-ui` **1.0.0-beta.21** (il CRM è alla beta.29), stesso preset Tailwind, stessi token
(`bg-surface-gray-1`, `text-ink-gray-9`, `Button variant="solid"`).

**Qui mi ero sbagliato**: nella prima stesura avevo scritto "altra UI, doppio branding".
Sul linguaggio visivo è falso — Builder e il CRM sono fratelli. Il salto che resta è di
**chrome e navigazione** (la sua dashboard, la sua barra, il suo concetto di progetto),
non di aspetto.

### 4.9 Cosa ne ricaviamo

| Prendiamo da Builder | Restiamo noi |
|---|---|
| la tela, i blocchi, gli stili, i breakpoint, i design token | il catalogo (servizi, prodotti), la sua pubblicazione, i form |
| publish/bozza, snapshot, versionamento, analytics di pagina | la lista pagine e il "pubblica" nel modale del CRM |
| rotte dinamiche `:slug`, SEO, sitemap | le API guest e i data script dei nostri componenti |
| l'agente AI e i template della community | brand, menu, footer, consenso, attribuzione dei lead |

## 5. La decisione, rivista

### 5.1 Le strade, rilette

| | **A · Builder come tela** | **B · Motore di pagine nel CRM** | **C · Copiare Builder dentro** |
|---|---|---|---|
| Sforzo | **basso-medio**: libreria componenti + guscio | medio-alto: 3–4 settimane | altissimo (68k righe) |
| Libertà grafica | massima, gratis | media | massima |
| Blocchi CRM tipizzati | **sì** — componenti spediti da noi con data script (§4.7) | sì | sì |
| Aspetto coerente col CRM | **sì** — stesso frappe-ui (§4.8) | sì | sì |
| Impostazioni nel modale | sì | sì | sì |
| Tela nel modale | **no** — serve una rotta a piena pagina (§4.6) | sì | no |
| Manutenzione motore | upstream | **nostra** | nostra, enorme |
| Costo per tenant | **+1 app** da installare, migrare, aggiornare | zero | zero |
| Rilasci upstream | ogni due settimane: opportunità **e** rischio di rebase | — | — |

### 5.2 Decisione — **A: Builder è la tela, il CRM è il guscio e i dati**

Ribalta la decisione D1 della prima stesura. Le ragioni sono due, entrambe nuove:
§4.7 (i componenti li spediamo noi, quindi niente Python per il cliente) e §4.8 (stesso
design system, quindi niente salto visivo). Con quelle due, costruirsi un motore di pagine
diventa lavoro che si può non fare.

Non si copia Builder dentro il CRM: si **installa accanto** nello stesso site, come app
del bench, e il CRM gli parla come parla già a `frappe_whatsapp`.

### 5.3 L'unico requisito che si piega: R6

Le **impostazioni** stanno nel modale, come chiesto: sito, pagine, vetrina, form.
La **tela di disegno** no: `PageBuilder.vue` è `h-screen w-screen` e rifiuta gli schermi
piccoli (§4.6). Un modale non è il posto per un editor visuale — e non lo sarebbe nemmeno
se lo scrivessimo noi.

Quindi: dal modale si gestisce e si pubblica; per disegnare si va su una **rotta a piena
pagina del CRM** (`/crm/sito/pagine/:name`) che ospita Builder in un iframe *stesso
dominio*. La sessione è condivisa (cookie), la barra del CRM resta intorno, il pulsante
"Torna al sito" riporta indietro.

### 5.4 Fork: non ora, e comunque sottile

Senza fork, l'iframe funziona ma la cucitura si vede: Builder mostra la sua barra e i suoi
link "torna alla dashboard", e il redirect `window.location.href = "/app"` sui permessi può
portare l'iframe fuori strada.

Il fork che serve è **piccolo e additivo**: un `?embed=1` che nasconde la chrome della
dashboard, sostituisce i redirect con un evento, ed emette `postMessage` su save e publish.
Poche decine di righe in `PageBuilder.vue`, `BuilderToolbar.vue` e `router.ts`.

Ordine consigliato:
1. **Fase 1 senza fork**: iframe così com'è, più un pulsante "apri in una scheda". Si misura
   quanto dà fastidio davvero.
2. Se dà fastidio: **proporre l'embed mode upstream** come PR. È una feature che serve a
   chiunque incapsuli Builder, ed è MIT: se la prendono, fork zero.
3. Solo se la PR non passa: fork sottile su `develop`, rebase a ogni release (quindicinale).

**Non** forkare per personalizzare l'editor: quella strada porta a divergere e non tornare più.

## 6. Architettura

### 6.1 I tre pezzi

```
┌─ site Frappe ──────────────────────────────────────────────────────┐
│                                                                    │
│  app crm  ──── crm/builder_files/components/*.json ────▶ app builder│
│  (fork)         componenti "CRM" + data script                     │
│    │            crm/builder_files/pages/*.json                     │
│    │            starter: home, servizi, contatti                   │
│    │            crm/builder_files/variables/*.json                 │
│    │            token di brand                                     │
│    │                                                               │
│    ├─ Settings → Sito web (frappe-ui, nel modale)                  │
│    │    Sito · Pagine · Vetrina                                    │
│    │                                                               │
│    ├─ /crm/sito/pagine/:name → iframe /builder/page/:name          │
│    │                                                               │
│    └─ crm.api.site.* (whitelisted, guest, rate-limited)            │
│         list_services · list_products · form_html · booking_slots  │
└────────────────────────────────────────────────────────────────────┘
```

### 6.2 La libreria di componenti CRM (il cuore del lavoro)

Uno `Builder Component` per blocco, spedito in `crm/builder_files/components/`, ciascuno
con le sue props e il suo `component_data_script`:

| Componente | Props | Data script legge |
|---|---|---|
| **Servizi CRM** | categoria, solo prenotabili, limite, layout, mostra prezzo, testo CTA | `CRM Service` con `publish_on_website=1` |
| **Prodotti CRM** | categoria, limite, mostra prezzo | `CRM Product` non disabilitati |
| **Form CRM** | quale form, titolo, redirect | `Web Form` CRM pubblicato → HTML del form (§8.1) |
| **Prenota** | quale calendario, inline o CTA | `CRM Booking Calendar` |
| **Contatti** | mostra mappa, orari | `CRM Website Settings` |
| **WhatsApp** | testo precompilato, floating/inline | numero dalle impostazioni |
| **Ultimi post** | rete, limite | `CRM Social Post` pubblicati |
| **Scheda servizio** | (per la pagina dinamica `/servizi/:slug`) | `frappe.form_dict.slug` → `CRM Service` |

Esempio di data script spedito da noi:

```python
# crm/builder_files/components/servizi_crm.json → component_data_script
rows = frappe.get_all("CRM Service",
    filters={"publish_on_website": 1, "enabled": 1,
             **({"category": props.categoria} if props.categoria else {})},
    fields=["service_name", "website_slug", "short_description",
            "website_image", "default_price", "currency"],
    order_by="website_order asc, service_name asc",
    limit=props.limite or 6)
component["servizi"] = rows
```

Il cliente non vede nulla di tutto questo: trascina "Servizi CRM" e compila tre campi.

### 6.3 Campi sito su `CRM Service` (R4, il "pulsante pubblica")

```
website_section     (Section Break "Sito web")
publish_on_website  (Check)        ← l'interruttore
website_slug        (Data, unico)  ← auto da service_name
website_image       (Attach Image)
short_description   (Small Text)   ← card in lista
website_description (Text Editor)  ← pagina di dettaglio
gallery             (Table: CRM Web Image)
price_display       (Select: Nascondi | Prezzo | "a partire da")
booking_calendar    (Link → CRM Booking Calendar)   ← D4
cta_type / cta_target
website_order       (Int)
seo_title, seo_description
```

Stessi campi su `CRM Product`. **Nessuna duplicazione del catalogo**: la fonte resta il
doctype di sistema, il sito è una vista pubblicata. Cambi il prezzo in agenda, cambia sul sito.

### 6.4 Dove vive nel CRM: una scheda "Sito", più il modale

Il taglio giusto non è "tutto nel modale". Il modale Impostazioni è per la
**configurazione** — le cose che tocchi una volta e poi dimentichi. Pubblicare un servizio,
aggiornare la home, buttare giù una landing è **lavoro ricorrente**, e il lavoro ricorrente
non si fa dentro un modale di impostazioni.

È esattamente il taglio che questo repo ha già fatto per il social: `/social` è una voce di
sidebar (il **Social Planner**, dove si lavora), mentre `Impostazioni → Social profiles`
tiene le connessioni. Il sito si comporta allo stesso modo.

**Sidebar → `Sito`** (una voce in `links` dentro `AppSidebar.vue`, con
`condition: () => siteEnabled`), che apre `/sito` con tre schede:

| Scheda | Cosa contiene |
|---|---|
| **Pagine** | le `Builder Page`: nome, rotta, stato (bozza/pubblicata), ultima modifica, visite. Azioni per riga: **Disegna**, Anteprima, **Pubblica/Ritira**, Duplica, Elimina. "Nuova pagina" parte dalle nostre starter page |
| **Vetrina** | servizi e prodotti in una tabella sola: toggle **Pubblica**, immagine, descrizione breve, ordine trascinabile, link "modifica scheda". È il posto dove si decide *cosa* il sito mostra |
| **Moduli** | i form CRM già esistenti, con il loro stato e il link "incorpora". Oggi vivono in `Impostazioni → Forms`: restano lì, qui compaiono in sola lettura con un link — non si spostano le abitudini di chi già li usa |

**Disegna** apre `/sito/pagine/:name`: pagina intera del CRM, header sottile (nome pagina,
stato, "Torna al sito", "Apri nel browser") e sotto l'iframe di Builder a tutta altezza.
È l'unico punto in cui si vede Builder, ed è a un clic di distanza dal rientro.

**Impostazioni → Sito web** resta, ma solo per ciò che è configurazione:

| Voce | Cosa |
|---|---|
| **Sito** | interruttore generale, dominio e home, brand (logo, colori, font → scritti nei Builder Token), menu di navigazione, footer e dati legali, SEO di default, GA4 / Meta Pixel, banner di consenso |

E una scheda **"Sito web"** dentro l'editor di servizio già esistente
(`Settings/Scheduling/ServicesSettings.vue`): immagine, descrizioni, slug, CTA, interruttore
di pubblicazione. È lì che l'utente la cerca quando sta guardando un servizio.

### 6.4bis E i funnel?

**Non c'è una scheda Funnel, e non la farei adesso.** Un funnel non è un tipo di pagina: è
una *sequenza* di pagine con split test, tracking per step e checkout — cioè il modulo
[01](./01-funnel-landing-builder.md), fuori scope. Nel frattempo una landing page è
semplicemente una `Builder Page` con la sua rotta, e si costruisce nella scheda Pagine come
tutte le altre.

Se un giorno lo scope riapre, il funnel entra come **quarta scheda dentro `Sito`** — non
come sezione nuova dell'app — perché riusa le stesse pagine: un funnel è un raggruppamento
ordinato di `Builder Page` più un contatore e una variante. È il motivo per cui la sidebar
prende una voce sola e generica ("Sito") invece di due specifiche.

### 6.5 Rotte, permessi, conflitti

- **Ruoli**: `Builder Page` è aperto a `System Manager` e `Website Manager`. Il Sales
  Manager del CRM non basta → si assegna `Website Manager` ai manager CRM, oppure si
  spedisce un ruolo `CRM Website Manager` con i permessi giusti via fixture.
- **Rotte**: Builder installa `website_path_resolver` e `get_website_user_home_page`. La
  home resta vuota finché non la si imposta, quindi non ruba `/` da sola. Restano da
  presidiare: `/crm` (già una route rule), `/book`, `/crm-form`, `/whatsapp-connect`.
- **`/servizi/:slug`**: pagina Builder con rotta dinamica + il componente "Scheda servizio";
  non serve una route rule nostra.
- **Data script**: girano in `safe_exec` o `safer_exec` — da verificare quali moduli servono
  ai nostri componenti e se il site richiede `server_script_enabled` (spike di mezza giornata).

## 7. Cosa si guadagna e cosa si perde rispetto alla prima stesura

**Non si scrive più**: il doctype pagina, il renderer delle sezioni, il base template,
l'editor delle pagine, l'anteprima, gli snapshot, il publish. Circa **8–10 giorni** che
spariscono, e un motore in meno da mantenere per sempre.

**Si scrive invece**: la libreria di componenti con i data script (il pezzo di valore), il
guscio nel modale, i campi sito sui servizi, la rotta con l'iframe.

**Si accetta**: una seconda app su ogni site (install, migrate, build, aggiornamenti
quindicinali); i ruoli di Builder; una cucitura visibile finché non c'è l'embed mode; e
pagine pubbliche che non ereditano automaticamente i token espresso delle nostre pagine
form/booking — vanno replicati come **Builder Token** spediti da noi (`builder_files/variables/`).

## 8. Le integrazioni

### 8.1 Form: le tre vie dell'embed (R2)

| Via | Quando | Stato |
|---|---|---|
| **Componente "Form CRM"** — il data script rende l'HTML del form e il blocco lo inietta, stesso dominio, stessi stili | **sulle pagine del sito** | da fare: estrarre da `crm_form.html` una macro Jinja riusabile, e verificare che l'HTML passi non-escaped nel binding (spike) |
| **iframe** — `/crm-form/<route>?embed=1` con allow-list di domini e CSP `frame-ancestors` | siti esterni del cliente | **già fatto** |
| **Script JS** — monta il form nell'host e fa POST cross-origin | sito esterno che vuole zero cornice | solo su richiesta (CORS, CSRF, versionamento) |

Perché non l'iframe sulle nostre pagine: secondo documento, font non ereditati, nessun
autodimensionamento senza `postMessage`, autofill rotto, invisibile ai motori di ricerca,
pixel nel frame sbagliato. Su un dominio altrui l'isolamento è un pregio; sul proprio è un difetto.

### 8.2 Servizi e prodotti dinamici (R3, R4)

Lista risolta a ogni render dal doctype; `publish_on_website` è l'interruttore, e finché è
spento il servizio non esce da nessuna API pubblica. Pagina di dettaglio `/servizi/:slug`
con rotta dinamica Builder. CTA "Prenota" → `/book/<route>` del calendario collegato:
l'appuntamento nasce già in agenda, col servizio giusto, la durata giusta, lo staff giusto.
JSON-LD `Service` / `Product` + `Offer` dal data script.

### 8.3 Attribuzione: non c'è da costruirla, c'è da collegarla

Quando ho scritto la prima versione di questa sezione proponevo di aggiungere i campi UTM
a `CRM Lead`. **Non serve più**: il modulo [15](./15-tracciamento-lead.md) è stato
implementato nel frattempo e porta già `tracker.js`, `CRM Visitor`, `CRM Visitor Session`,
`CRM Tracking Event`, i due scatti `first_touch_*` / `last_touch_*` su Lead e Trattativa,
la classificazione della sorgente e il report per categoria/campagna.

Quello che il sito deve fare è **entrare in quella pipeline**, non costruirne una seconda:

| Cosa | Come |
|---|---|
| Le pagine del sito tracciano le visite | `tracker.js` spedito come **Builder Client Script** in `crm/builder_files/client_scripts/`, così ogni pagina pubblicata lo monta senza che nessuno debba incollarlo |
| I form del sito nominano il visitatore | il componente **Form CRM** invia l'evento di submit che fa scattare `attribute()`: la storia anonima passata viene riscritta sul Lead appena creato |
| Le prenotazioni fanno lo stesso | la CTA "Prenota" porta su `/book/<rotta>`, già dentro lo stesso dominio e quindi la stessa sessione tracciata |
| Il report esiste già | `crm.api.tracking.source_report` risponde "da dove arrivano i lead del sito" senza una riga in più |

È un pezzo di lavoro che sparisce dal piano, e vale più di quanto costa: significa che dal
primo giorno **ogni lead che nasce dal sito arriva con la sua provenienza attaccata**.

La **Meta Conversions API** resta fuori scope anche qui: il modulo 15 la elenca fra le cose
non fatte (invio di conversioni offline verso le piattaforme), e non è questo il modulo che
la porta.

### 8.4 Il resto

- **Automazioni**: submit o prenotazione → `on_lead_created` / `on_booking_created` già esistenti.
- **WhatsApp**: CTA `wa.me` con testo precompilato; il messaggio atterra nell'inbox CRM.
- **Social**: alla pubblicazione, "condividi" che precompila un `CRM Social Post` con URL,
  titolo e immagine.
- **Tracked Links** per le CTA in uscita — i click finiscono già nel percorso del visitatore.
- **GDPR**: banner che gate-a GA4/Pixel prima del consenso, checkbox nel form salvata sul
  lead, footer verso le `Web Page` `privacy`/`terms` già spedite.
- **Dominio**: custom domain a livello di site (`bench setup add-domain`) — procedura di
  provisioning, modulo 06.

## 9. Come **non** lo farei

1. **Non** scrivere un motore di pagine adesso: §4.7 e §4.8 l'hanno reso lavoro evitabile.
2. **Non** copiare Builder dentro il CRM (68.000 righe, fine dell'upstream). Fork ≠ copia:
   il fork ammesso è un `?embed=1` di poche decine di righe, e solo dopo aver provato la PR upstream.
3. **Non** forkare per personalizzare l'editor: si diverge e non si torna.
4. **Non** mettere la tela dentro il modale: Builder rifiuta gli schermi piccoli, e avrebbe ragione.
5. **Non** far scrivere data script al cliente: li spediamo noi come componenti.
6. **Non** mandare il cliente sulla dashboard di Builder: la lista pagine, il publish e il
   catalogo restano nel CRM. Di Builder deve vedere solo la tela.
7. **Non** iframe del nostro form sulle nostre pagine (§8.1).
8. **Non** duplicare il catalogo in doctype "solo sito": una sola fonte di verità.
9. **Non** rendere pubblici campi interni (costi, staff, note): whitelist di campi e
   `rate_limit`, come già fa `booking.py`.
10. **Non** funnel, A/B, checkout, membership adesso: fuori scope, e nulla lo preclude.

## 10. Sicurezza, permessi, performance

- API pubbliche `allow_guest=True` **in sola lettura**, whitelist di campi, `rate_limit`.
- Data script dei componenti: sono codice nostro, versionato nel repo, non input utente.
- Ruoli: la gestione sito richiede `Website Manager` (o il nostro ruolo dedicato).
- Immagini: `File` privati mai referenziati da pagine pubbliche.
- Cache: Builder invalida già la rotta su publish (`clear_route_cache`); i nostri data
  script devono essere veloci — niente `no_cache` inutile, e `page_data` va tenuto snello.
- Test: unit test sulle funzioni pure (slug, whitelist campi, JSON-LD) in `crm/tests`;
  i data script si testano come funzioni Python normali prima di finire nel JSON.

## 11. Lo spike

**Stato: kit pronto, da eseguire su un bench.** In questo ambiente non c'è né un bench né
Frappe installato, quindi lo spike non è stato *eseguito*: è stato **verificato leggendo il
codice di Builder**, e il materiale per lanciarlo è nel repo.

### 11.1 Cosa è già verificato (lettura del codice, non esecuzione)

Il contratto dei componenti è stato ricostruito riga per riga:

| Cosa | Dove nel codice di Builder | Esito |
|---|---|---|
| I file dell'app vengono importati | `export_import_standard_page.sync_standard_builder_pages` | `<app>/builder_files/{components,pages,client_scripts,variables,fonts}`, importati da `make_records` che cerca `<cartella>/<cartella>.json` |
| Il data script riceve le props | `builder_component.get_component_data` | `_locals = {component: _dict(), props: _dict(props)}`; il valore di ritorno è `component` |
| Naming del componente | `builder_component.json` | `autoname: field:component_id` → `name == component_id` |
| Binding da prop | `get_dynamic_value_key`, `comesFrom="props"` | `{{ props.<chiave> }}` |
| Binding da data script | idem, `comesFrom="componentData"` | `{{ component.<chiave> }}` |
| Liste | `get_loop_info` + `render_repeater_children` | `{% for component in component.<chiave> %}` — ⚠️ **la variabile di ciclo si chiama `component` e oscura quella esterna**, e il repeater rende **solo `children[0]`** |
| Fallback statico | `set_dynamic_content_placeholders` | `{{ chiave if chiave else '<valore statico>' }}` |
| Sandbox | `utils.execute_script` | `safe_exec` se abilitata, altrimenti `safer_exec`: niente import, niente dunder |
| Ruoli | permessi di `Builder Page` | `System Manager`, `Website Manager` — il Sales Manager del CRM **non basta** |
| Chrome dell'editor | `PageBuilder.vue` | `h-screen w-screen` + rifiuto degli schermi piccoli → serve una rotta a piena pagina |

### 11.2 Cosa c'è nel repo

| File | Cosa |
|---|---|
| `crm/builder_files/components/servizi_crm/servizi_crm.json` | il componente **Servizi CRM**: props `titolo`/`categoria`/`limite`, repeater su `component.servizi`, card con nome, descrizione, durata e prezzo. Il data script legge **solo campi che `CRM Service` ha già**, così lo spike non richiede alcuna modifica di schema |
| `crm/builder_files/README.md` | il contratto qui sopra, scritto per chi costruirà gli altri componenti |
| `crm/tests/test_builder_files.py` | valida ogni componente spedito: fixture importabile, chiavi di blocco note, `blockId` unici, repeater con un solo figlio, props referenziate dichiarate, data script che compila e resta compatibile con `safe_exec`. Con Builder installato fa anche il giro completo su `get_component_data` |
| `scripts/builder/spike.sh` | `bench get-app` → `install-app` → `migrate` → controlla che il componente sia arrivato → esegue il data script. Poi elenca i sette controlli da fare a mano nel browser |

### 11.3 Le due incognite, chiuse

Verificate sul sorgente di Frappe, non per intuizione.

**1. I binding non vengono escapati — e va bene, ma ha un prezzo.**
`get_jenv()` costruisce un `FrappeSandboxedEnvironment` **senza passare `autoescape`**, e il
default di Jinja è `False`; Builder non emette `|safe` da nessuna parte. Quindi un valore
che finisce in un binding esce come HTML.

- ✅ **Il componente Form CRM si può fare come previsto**: il data script rende il markup del
  form e lo consegna come dato. Niente blocco HTML custom, niente client script.
- ⚠️ **Ma allora l'escaping è compito nostro.** Un `<` nel nome di un servizio finirebbe in
  pagina come markup: è XSS immagazzinato, da utente CRM a visitatore. Il data script di
  `Servizi CRM` ora passa ogni campo di testo per `frappe.utils.escape_html()`, e la regola è
  scritta in `crm/builder_files/README.md`: **testo → `escape_html`, rich text → `sanitize_html`,
  markup nostro → così com'è.**

**2. `fmt_money` è dentro la sandbox.** È in `VALID_UTILS` di `frappe/utils/safe_exec.py`,
insieme a `cint`, `cstr`, `flt`, `escape_html`, `sanitize_html`, `strip_html`,
`format_datetime`, `get_url`, `parse_json`. Il `try/except` difensivo è stato tolto: il
codice ora dice quello che fa.

**Una terza cosa emersa mentre verificavo.** `get_jenv()` sceglie fra globals ristretti e
non secondo `disable_render_safe_exec`, ma i metodi registrati via `hooks.jinja.methods`
vengono aggiunti **dopo** quella scelta. `get_component_data` è registrata proprio così da
Builder: funziona in entrambe le modalità. Era un modo silenzioso in cui i componenti
avrebbero potuto non renderizzare su un site configurato in modo restrittivo — non succede.

Nessuna delle tre tocca l'architettura. Il controllo `e` dello spike resta nello script come
conferma sul campo, non più come bivio.

## 12. Fasi


| Fase | Contenuto | Stima |
|---|---|---|
| **0 — Spike** | vedi §11: kit pronto in `scripts/builder/spike.sh`. **Se qui qualcosa non regge, si torna al piano B** | 1–2 gg |
| **1+2 — Consegna unica** | libreria componenti CRM (servizi, prodotti, form, prenota, contatti, WhatsApp, scheda servizio) + Builder Token di brand + starter pages; campi sito su `CRM Service`/`CRM Product` + scheda "Sito web" nell'editor servizio; gruppo "Sito web" nel modale (Sito, Pagine, Vetrina); rotta `/crm/sito/pagine/:name` con iframe | 10–14 gg |
| **3 — Crescita** | SEO (JSON-LD, sitemap, OG), `tracker.js` come client script sulle pagine, consenso cookie che gate-a i pixel, componenti FAQ/galleria/numeri/social | 5–7 gg |
| **4 — Opzionale** | embed mode (PR upstream, poi eventuale fork sottile), blog/news, multilingua, script embed JS per siti esterni | su richiesta |


## 13. Cosa è stato costruito

Fase 1+2, consegnate insieme come deciso. Tutto vive dentro il CRM: di Builder si vede
solo la tela, e solo quando si preme "Disegna".

### 13.1 Dove si lavora

| Superficie | Rotta / posto | Cosa fa |
|---|---|---|
| **Sito** (sidebar) | `/sito` | due schede: **Pagine** (stato, rotta, home, bozza non pubblicata, Disegna, Pubblica, Duplica, Elimina) e **Vetrina** (servizi e prodotti con l'interruttore Pubblica, immagine, descrizione, ordine) |
| **Editor** | `/sito/pagine/:name` | **schermo intero**, fuori dal layout del CRM: niente sidebar, niente header dell'app. Una striscia sottile (indietro, nome, stato) e sotto l'iframe di Builder, stesso dominio e stessa sessione |
| **Impostazioni → Sito web** | modale | interruttore generale, home e radice, brand, menu, footer e dati legali, SEO, GA4/Pixel, consenso |
| **Editor di servizio** | modale Agenda | l'interruttore "Pubblica sul sito" dove uno lo cerca, con il link alla scheda completa in Vetrina |

L'editor non è dentro il modale perché Builder rifiuta gli schermi piccoli (§4.6): sotto i
900px mostriamo un messaggio nostro invece del suo. E non è nemmeno dentro il layout del
CRM: sidebar e header dell'app sopra la toolbar di Builder farebbero tre barre impilate
sulla stessa tela. La rotta esce dal layout come già fa l'onboarding, e di nostro resta
una striscia sola.

**Non si esce mai dal CRM.** Un guardiano sull'iframe controlla dove è finito: se Builder
naviga verso la sua dashboard riporta a `/sito`, se finisce su `/app` (rimbalzo sui
permessi) avvisa e torna indietro.

### 13.2 Come non ci pestiamo i piedi

`crm/api/site_routes.py` è la guardia. Frappe controlla solo che due pagine non abbiano la
stessa rotta; non sa che `/crm` è l'app, `/book` le prenotazioni e `/crm-form` i moduli.

- L'insieme riservato è **derivato**, non scritto a mano: primo segmento di ogni
  `website_route_rules` di ogni app installata, più i percorsi del framework che non hanno
  una regola (`api`, `app`, `assets`, `files`, `builder`, …). Un'app installata domani è
  protetta senza toccare nulla.
- Un `doc_events` su `Builder Page.validate` **rifiuta il salvataggio** di una pagina che
  invaderebbe una di quelle: non si arriva nemmeno a pubblicarla.
- Stessa guardia sugli slug di servizi e prodotti, e sul campo rotta della nuova pagina,
  che valida mentre scrivi e propone un'alternativa libera.
- La home non si può ritirare né cancellare senza prima sceglierne un'altra — e la regola
  sta sul documento (`validate` e `on_trash`), non nella nostra API: si pubblica e si
  cancella anche dalla dashboard di Builder, e la rete deve esserci comunque.

### 13.3 Pubblicazione

Passa sempre da `Builder Page.publish()`, mai da un `db_set`: così restano gli snapshot e
la promozione della bozza che Builder fa di suo. Nell'editor il pulsante è quello di
Builder — un secondo Pubblica nostro sarebbe la stessa azione due volte — e le protezioni
reggono lo stesso perché stanno sul documento. La lista mostra "modifiche non pubblicate"
quando la bozza è avanti rispetto al vivo.

L'interruttore **Servi la home su `/`** scrive `Builder Settings.home_page` — l'unico
punto che decide cosa risponde alla radice — e la spegne quando lo spegni. Il CRM resta
su `/crm` in entrambi i casi.

### 13.4 Il tracciamento, in un punto solo

`Builder Settings.head_html` è l'unico posto dove un tag vale per tutte le pagine (il
template di Builder non include `web_include_js`). Le impostazioni del sito ci scrivono un
blocco delimitato da marcatori, senza toccare quello che c'è intorno:

- `tracker.js` sempre, così le visite alle pagine entrano nell'attribuzione del
  [modulo 15](./15-tracciamento-lead.md);
- token di brand e font;
- GA4 e Meta Pixel **tenuti come testo inerte** finché il banner non riceve un sì. È la
  differenza fra un banner che informa e uno che funziona.

### 13.5 I componenti

`crm/builder_files/components/` — cinque, generati da `scripts/builder/build_components.py`:
Servizi, Prodotti (data script), Form, Prenota, Contatti (metodo Jinja, §15.6).

Ogni testo che arriva dal CRM passa per `escape_html`: il rendering non fa autoescape
(§11.3), quindi un `<` in un nome servizio sarebbe markup in pagina.

### 13.6 Il form, inline

`crm/api/site_render.py` registra tre metodi Jinja (`crm_form_html`, `crm_booking_html`,
`crm_contact_html`). Builder passa ogni pagina per `render_template`, quindi un blocco il
cui markup è `{{ crm_form_html(props.modulo) }}` riceve il form vero: stesso documento,
stessi font, niente iframe, e gli id del visitatore viaggiano con l'invio esattamente come
sulla pagina form standalone. Un modulo non pubblicato rende un segnaposto, non una bozza.

### 13.7 File

| | |
|---|---|
| `crm/fcrm/doctype/crm_website_settings/` | il Single, più `CRM Web Nav Item` e `CRM Web Social Link` |
| `crm/fcrm/doctype/crm_service/`, `crm_product/` | campi sito (pubblica, slug, immagine, descrizioni, CTA, ordine, SEO) |
| `crm/api/site.py` | pagine, vetrina, impostazioni, API pubblica dei servizi |
| `crm/api/site_routes.py` | la guardia sulle rotte e gli slug |
| `crm/api/site_render.py` | frammenti Jinja e `head_html` del sito |
| `crm/templates/site/` | form inline, CTA prenotazione, contatti |
| `frontend/src/pages/Website.vue`, `WebsitePageEditor.vue` | la scheda Sito e la tela incapsulata |
| `frontend/src/components/Settings/Website/` | le impostazioni nel modale |
| `crm/tests/test_site.py`, `test_builder_files.py` | rotte riservate, slug, permessi, whitelist dei campi, contratto dei componenti |

### 13.8 Cosa resta fuori

Il selettore di slot **inline** (la CTA porta a `/book/<rotta>`, che è già una pagina
nostra), il blog, il multilingua, e i componenti decorativi (FAQ, galleria, numeri): quelli
si costruiscono con i blocchi nativi di Builder, senza bisogno che li spediamo noi.

## 14. Decisioni e domande

| | Domanda | Esito |
|---|---|---|
| **D1** | Motore di pagine nostro o Builder? | **Ribaltata: Builder**, installato accanto nel site. Ragioni in §4.7 e §4.8 |
| **D2** | Ampiezza della prima consegna | **Fasi 1+2 insieme**, precedute da uno spike di 1–2 giorni |
| **D3** | La home prende la radice `/` | **Configurabile** — è già così in Builder (`home_page` nelle sue impostazioni), lo pilotiamo dal nostro modale |
| **D4** | Servizi vs Calendari di prenotazione | **Confermata**: campo `booking_calendar` su `CRM Service`, il sito pubblica **i servizi**, `show_in_menu` su `CRM Booking Calendar` va deprecato |
| **D5** | Multi-tenant | **Confermata**: un sito per site Frappe. Niente astrazione multi-sito |
| **D6** | ~~Builder come opzione?~~ | **Superata**: Builder è la base, non l'opzione |
| **D7** | Fork subito o dopo? | **Confermata: dopo.** Fase 1 senza fork, poi PR upstream per l'embed mode, fork sottile solo come ultima spiaggia (§5.4) |

## 15. Compatibilità futura

Le API `crm.api.site.*` restano il contratto: le usano i data script dei nostri componenti
oggi, potrebbero usarle una landing esterna o un'app mobile domani. E se un giorno lo scope
riaprisse sul modulo [01](./01-funnel-landing-builder.md), uno step di funnel è una
`Builder Page` con una variante e un contatore: il layer funnel resta un'aggiunta sopra,
non una riscrittura.
