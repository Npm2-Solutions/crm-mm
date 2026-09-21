# 10 — Meta Lead Ads (Facebook + Instagram) production-grade

> ✅ **IMPLEMENTATO (31/08/2026)**. Ricostruita l'integrazione lead sync sulla base
> delle guide ufficiali Meta (developers.facebook.com, verificate ad agosto 2026).
> Sostituisce il flusso "incolla access token" (che si rompeva in ore: i token
> utente scadono) con OAuth completo + webhook real-time + riconciliazione.

## Architettura implementata

```
Settings modal → "Meta Lead Ads"
  1. App ID/Secret (+ webhook URL e verify token da copiare nell'app Meta)
  2. "Connect with Facebook" → OAuth code flow (state firmato HMAC)
       code → user token → LONG-LIVED user token (~60gg)
       → /me/accounts → PAGE TOKEN per pagina (non scade) cifrati (Password)
       → pagine + form (paginati) upsert, con mapping domande preservato
  3. Selezione pagine: toggle per pagina → POST /{page}/subscribed_apps
       (subscribed_fields=leadgen, col page token) → webhook real-time
  4. Mapping campi: per form, domande (per KEY, non label) → campi CRM Lead,
       con default automatici (FULL_NAME→nome, EMAIL, PHONE, ...)
```

**Ingestione** (`crm/integrations/meta/leads.py`), condivisa da webhook e polling:
- webhook `crm.integrations.meta.webhook.handle`: GET = handshake hub.challenge;
  POST = verifica **X-Hub-Signature-256** (HMAC-SHA256 del body col app secret),
  risposta 200 immediata + coda (Meta ritenta per sole 36h) — il payload NON
  contiene i dati: fetch di /{leadgen_id} col page token;
- **dedup per `facebook_lead_id`** (id globale univoco ⇒ webhook+polling idempotenti);
- FULL_NAME splittato in nome/cognome, telefoni normalizzati (`p:+39...`),
  source Facebook/Instagram (campo `platform` con fallback se non disponibile);
- **riconciliazione oraria** sugli ultimi 2 giorni dei form delle pagine attive
  (retry webhook = 36h; la dedup la rende economica);
- **backfill 90 giorni** on-demand (Meta CANCELLA i lead dopo 90 giorni: mai
  trattare Meta come system of record);
- failure log (`Failed Lead Sync Log`) su ogni lead non importabile;
- **token health giornaliero** via /debug_token, flag sulla pagina + error log;
- ogni chiamata Graph porta **appsecret_proof** (si può attivare "Require App
  Secret" sull'app);
- trigger automazioni: i lead creati emettono `Lead Created` con payload
  `{facebook_form_id, source}` ⇒ le automazioni possono filtrare per form
  (equivalente del trigger GHL "Facebook Lead Form Submitted").
- **Data Deletion Callback** (`.../webhook.data_deletion`, signed_request
  verificato) — richiesto dall'App Review.
- Instagram: i lead IG appartengono alla stessa pagina Facebook (conferma docs) —
  un'unica integrazione copre entrambi.

## La sincronizzazione delle Pagine gira in background

Scoprire le Pagine costa una chiamata Graph per ogni Pagina raggiunta tramite
un portfolio Business, piu' una per i form di ognuna. Un account con accesso a
tutte le Pagine di un'agenzia sono decine o centinaia di chiamate in fila:
dentro una richiesta web si va oltre il timeout del gateway, e una richiesta
che muore si porta dietro l'intera transazione — **compreso il token appena
ottenuto**. Era questo il motivo per cui dare accesso a una sola Pagina
funzionava e darlo a tutte tornava indietro "non collegato".

Ora il callback salva il token e fa `commit` subito, poi mette in coda il
lavoro (`start_page_sync`). La schermata mostra "sto leggendo le tue Pagine" e
si ricontrolla da sola finche' il job non ha finito. Anche "Aggiorna pagine"
passa dalla stessa coda.

## Chi decide cosa: Facebook concede, il CRM sceglie

Una sola decisione, in un solo posto. *Meta connection* elenca le Pagine
concesse e i loro interruttori: quello e' il punto in cui si sceglie. *Lead
forms* mostra i moduli **solo delle Pagine accese** — accenderne una la fa
comparire li', spegnerla la fa sparire. Non e' cosmetica: e' cio' che
l'interruttore promette.

Una Pagina che non e' mai stata concessa non compare da nessuna parte, e si
aggiunge con "Aggiungi Pagine da Facebook".

L'elenco mostra **solo le Pagine su cui l'interruttore puo' fare qualcosa**:
Meta pretende il task ADVERTISE per tutto cio' che e' leadgen, quindi una
Pagina senza offrirebbe un interruttore capace solo di fallire. Quelle vengono
**contate, non elencate** — sparire senza una parola sarebbe un mistero a sua
volta. Le Pagine salvate prima che il CRM registrasse i task non ne hanno e
restano visibili: giudica Meta.

L'elenco e' **paginato** (venti per volta, con ricerca quando sono di piu'):
l'account di un'agenzia puo' contenerne centinaia, e non hanno niente da fare
dentro il payload dello stato della connessione.

### Quando una Pagina viene dimenticata

Alla sincronizzazione, una Pagina che Facebook non concede piu' viene rimossa,
insieme ai suoi profili social e ai suoi moduli. Resta solo se c'e' **dato
vero** da proteggere: la sincronizzazione lead accesa, oppure lead gia'
arrivati da uno dei suoi moduli.

Tenerla per la sola esistenza dei moduli era sbagliato: quei moduli erano stati
sincronizzati dalla stessa Pagina non concessa, quindi altrettanto obsoleti, e
bastavano a mantenere in vita per sempre un elenco di Pagine inutilizzabili.



Una sola strada, non un misto. Il dialog di Facebook serve a dire *"questa app
puo' vedere queste Pagine"*: conviene concederle tutte, una volta. Cosa il CRM
usa davvero si decide **qui**, con gli interruttori della schermata di
connessione.

Non e' una preferenza. La strada opposta — decidere tutto nel dialog — non
regge: Facebook **non riapre il selettore** alle autorizzazioni successive
(serve `auth_type=rerequest`, ed e' comunque un giro fuori dal CRM), e con
un'app sola dell'agenzia su tanti clienti ogni modifica rimanderebbe il cliente
su facebook.com. E' anche cio' che fa GHL.

L'elenco e' `/me/accounts`, cioe' esattamente cio' che si e' concesso. Il CRM
non va a cercare altrove: percorrere `owned_pages` e `client_pages` del
portfolio portava dentro Pagine **non** concesse, che arrivano senza i permessi
per usarle e falliscono a ogni chiamata. Una Pagina tolta dal dialog viene
dimenticata, purche' non abbia moduli ne' la sincronizzazione accesa.


### Disconnettere significa smettere davvero (08/09/2026)

"Disconnetti" cancellava il solo token utente. Ma i lead non arrivano con
quello: arrivano con il **token della Pagina**, che non scade insieme, e la
Pagina resta iscritta al webhook `leadgen` dell'app. Risultato: la schermata
diceva "non connesso" e i lead continuavano a entrare — sia dal webhook, sia
dalla riconciliazione oraria che ripesca gli ultimi due giorni.

Adesso la disconnessione, per ogni Pagina: disiscrive l'app dal webhook
(`DELETE /{page}/subscribed_apps`), spegne la sincronizzazione, dimentica il
token e rilascia la Pagina sull'hub. Meta lato suo non ha piu' nulla a cui
notificare, e il CRM non ha piu' nulla con cui chiedere.

Due conseguenze da dire prima, ed e' quello che spiega il dialog di conferma:
anche il Social Planner pubblica con quei token, quindi si ferma; e per
tornare indietro si ripassa dal login di Facebook.

Il rilascio sull'hub non e' un dettaglio: l'hub **rifiuta** di riassegnare una
Pagina gia' rivendicata, quindi una Pagina disconnessa su un sito cliente non
avrebbe mai piu' potuto essere collegata altrove. Ora `set_page_sync(off)` e la
disconnessione la liberano, con una firma diversa da quella della
rivendicazione perche' una richiesta catturata non possa essere rigiocata al
contrario.

Per i siti disconnessi *prima* di questa correzione c'e' la patch
`stop_lead_import_after_disconnect`: senza token utente non c'e' connessione,
quindi nessuna Pagina puo' importare. I token delle Pagine li lascia stare — ci
pubblica il Social Planner, e disiscrivere su Meta vorrebbe dire chiamate di
rete dentro una migrazione.

### L'inserzione ha un nome, non un numero (17/09/2026)

Un lead arriva portando un `ad_id` e nient'altro, quindi la scheda poteva solo
dire *"ad 120210…"*: vero e inutile. Adesso il CRM chiede a Meta come si chiama
quell'inserzione (`/{ad_id}?fields=name,adset{name},campaign{id,name}`) e la
persona legge **"arrivato dall'inserzione Promo Autunno, campagna Lead
Settembre, gruppo Milano 25-45"**.

Quattro cose non ovvie:

**Si chiede una volta per inserzione.** Cento lead dalla stessa inserzione non
sono cento domande: la risposta sta in `Facebook Ad` e vale una settimana — che
e' abbastanza per risparmiare le chiamate e poco abbastanza perche' una campagna
rinominata si aggiorni al lead successivo.

**I nomi arrivano col lead, senza una seconda chiamata (correzione del
17/09/2026).** Nella prima versione il nome lo chiedevamo leggendo il nodo `ad`
col token della Pagina: sbagliato due volte. L'inserzione non appartiene alla
Pagina ma all'account pubblicitario, quindi quel token veniva rifiutato — i nomi
non comparivano mai e ogni lead spendeva una chiamata per farsi dire no. E la
chiamata non serviva: Meta mette `ad_name`, `adset_name`, `campaign_id` e
`campaign_name` **sul lead stesso**, accanto ad `ad_id`, nella stessa risposta.
Adesso li chiediamo li'. Costo: zero chiamate in piu', nessun token utente da
tenere valido, niente che possa disallinearsi.

Il privilegio richiesto e' lo stesso che serve gia' per `ad_id` — un token di chi
puo' inserzionare su quell'account pubblicitario, con `ads_management` — e quando
manca Meta **omette i campi** invece di dare errore, esattamente come fa con
`ad_id`.

La lettura del nodo `ad` resta come ripiego (`describe_ad`, col token utente e
la cache in `Facebook Ad`) per i lead che arrivano senza quei campi: una versione
vecchia delle API, o un backfill che ha dovuto chiedere meno. Ogni tentativo
chiede meno del precedente, perche' **un campo rifiutato non deve costare il
lead**.

**Un rifiuto non costa il lead.** L'inserzione appartiene all'account
pubblicitario del cliente, e chi ha collegato la pagina non sempre puo'
inserzionare su quell'account: la chiamata puo' essere negata. Allora si tiene
l'id come ripiego, il rifiuto viene ricordato per non richiedere ogni volta, e —
questo era il difetto da evitare — **un nome che sapevamo non si perde per un
rifiuto temporaneo**. Passata la settimana si riprova, perche' un accesso
concesso dopo deve poter avere effetto.

**Un lead organico non chiede niente**, perche' non c'e' nessuna inserzione
dietro.

Nella scheda, sotto Tracciamento, le tre caselle cambiano nome quando il lead
viene da un modulo: "Campagna", "Gruppo di inserzioni", "Inserzione" invece di
Campaign/Term/Content, che erano i valori giusti sotto le parole sbagliate.

### Il registro delle importazioni (08/09/2026)

`Facebook Lead Import`: una riga per submission presa in carico, con il modulo,
la persona che ne e' nata e l'esito (Created/Merged). Serve a una cosa sola, ma
importante: **sapere che una compilazione e' gia' stata gestita anche quando la
persona non c'e' piu'**. Prima la domanda era "esiste un lead con questo leadgen
id?", quindi cancellare un lead lo faceva tornare alla riconciliazione oraria
successiva. Il `on_trash` del lead timbra `deleted_on` sulle sue righe e le
lascia dov'erano.

## Perche' Facebook chiede il portfolio Business

Il dialog chiede di scegliere un portfolio perche' l'app domanda
`business_management`: serve alle Pagine possedute o gestite da un Business,
che senza quel permesso non compaiono nemmeno dopo essere state spuntate.


## Checklist di produzione (dalle guide ufficiali)

> **Un'app sola per tutti i clienti**: vedi
> [11-app-meta-agenzia.md](11-app-meta-agenzia.md). Quello che segue vale per
> l'app dell'agenzia (configurata una volta) o per un site singolo con app propria.

### App Meta (developers.facebook.com)
1. Prodotto **Facebook Login**: Valid OAuth redirect URI =
   `https://<site>/api/method/crm.integrations.meta.oauth.callback` (HTTPS).
   (Non esiste API pubblica per questa whitelist: è l'unico passo davvero
   manuale, insieme alla creazione dell'app.)
2. **Webhook (Page → leadgen): CONFIGURATO AUTOMATICAMENTE** al salvataggio di
   App ID/Secret (o col bottone "Configure automatically") via
   `POST /{app_id}/subscriptions` con l'app token — Meta verifica il callback
   in modo sincrono, quindi il sito deve essere raggiungibile in HTTPS. La
   configurazione manuale resta documentata in Settings come fallback.
3. **Data Deletion Request URL** =
   `https://<site>/api/method/crm.integrations.meta.webhook.data_deletion`.

### App Review (per usare l'app con utenti esterni al team)
- **Advanced Access** per: `pages_show_list`, `pages_read_engagement`,
  `pages_manage_metadata`, `pages_manage_ads`, `leads_retrieval`,
  `ads_management` (+ `business_management`; per il Social Planner anche
  `pages_manage_posts`, `instagram_basic`, `instagram_content_publish`) —
  con **Business Verification**
  dell'azienda e screencast del flusso completo (login → scelta pagina → sync).
- **Data Use Checkup** annuale.
- In development mode i webhook reali non arrivano: usare il
  [Lead Ads Testing tool](https://developers.facebook.com/tools/lead-ads-testing)
  o il bottone **"Test lead"** in Settings (`POST /{form}/test_leads`, 1 per form).

### Il tranello n°1: Leads Access Manager
Se il Business ha attivato la personalizzazione dell'accesso ai lead, le API
rispondono vuoto/permission error **anche con token validi**: in
**Business Settings → Integrations → Leads Access** va assegnato questo CRM.
L'hint è mostrato anche nella pagina Settings.

### Rate limit
Leadgen: ~4800 × lead generati (90gg) chiamate/24h per pagina; usare i page token
(bucket separati); backoff sui codici 4/17/32/613/80001.

## Un solo sistema (03/09/2026)

Il vecchio `Lead Sync Source` — token incollato a mano + polling ogni 5/10/15
minuti — **è stato rimosso**: doctype, scheduler, pagina Settings "Lead Syncing"
e il modulo `background_sync`. I lead dai form arrivano **solo** dal motore Meta
(OAuth → webhook real-time → riconciliazione oraria → backfill 90 giorni).
Una patch elimina il doctype dai site esistenti; i log di errore ora puntano al
**form** invece che alla vecchia sorgente, e il "riprova" reimporta col motore
nuovo.

### Le voci nel menu Settings

Un gruppo solo, **"Meta & Messaging"**, in ordine di dipendenza:

| Voce | A cosa serve |
|---|---|
| **Meta connection** | l'unica connessione: app, webhook, "Connetti con Facebook". Alimenta tutto il resto |
| **Lead forms** | quali pagine sincronizzano i lead e come le domande mappano sui campi |
| **Social profiles** | i profili su cui pubblica il Social Planner |
| **WhatsApp** | il numero collegato col QR |
| **WhatsApp Templates** | i modelli e il loro stato di approvazione |

## Test

`crm/tests/test_meta_leads.py`: mapping/split nome, idempotenza, source IG,
failure log, normalizzazione telefono, merge domande senza perdere mapping,
verifica firma webhook, un lead cancellato che non torna, disconnessione che
ferma davvero le Pagine, notifica
ignorata per una Pagina spenta (anche quando arriva senza page id), rilascio
della rotta sull'hub e rifiuto del replay di una rivendicazione.

## Quando Meta dice "impersonating a user's page" (21/09/2026)

Errore vero, incontrato collegando le pagine di un cliente:

> Any of the pages_read_engagement, pages_manage_metadata, pages_read_user_content,
> pages_manage_ads, pages_show_list or pages_messaging permission(s) must be granted
> before impersonating a user's page.

Nomina sei permission e non dice quale manca. Significa una cosa sola: **il token
non porta i permessi di Pagina**, e i motivi sono tre, tutti invisibili dal CRM:

1. nel dialogo di login qualcuno ha tolto una spunta (a una permission o a una
   Pagina) — e **Facebook non lo richiede piu'** ai login successivi, a meno di
   `auth_type=rerequest`;
2. il token e' stato ottenuto **prima** che la permission venisse aggiunta all'app:
   i token sono congelati al momento del rilascio e non si aggiornano da soli;
3. chi ha collegato non ha il ruolo necessario **su quella Pagina** (serve almeno
   Inserzionista/ADVERTISE), quindi la vede in `/me/accounts` ma non puo' gestirla.

Adesso il CRM lo dice prima. Al login leggiamo `debug_token` e salviamo in
`CRM Meta Settings.granted_scopes` **cosa Facebook ha concesso davvero**; la
schermata Connessione confronta quella lista con quella che serve e, se manca
qualcosa, mostra in rosso **i nomi esatti** e il pulsante "Chiedi di nuovo a
Facebook", che riapre il dialogo con `rerequest`.

Una connessione fatta prima che questo esistesse non ha niente di registrato: la
prima schermata che lo chiede paga una chiamata a `debug_token` e la salva, cosi'
il caso peggiore (quello in cui stai guardando lo schermo senza capire) e' anche
quello che si risolve da solo. Se non c'e' nemmeno un token, il CRM **tace**:
accusare una connessione funzionante di non avere niente sarebbe peggio del
silenzio.

## "No page token stored. Reconnect Facebook." — e riconnettere non basta

Il seguito naturale del problema qui sopra, e il caso piu' frustrante: il CRM
chiede di riconnettere, tu riconnetti, e non cambia niente.

Il motivo e' che `discover_pages` tiene **solo le Pagine che tornano da
`/me/accounts` con un `access_token`**: quelle sono le Pagine che la persona ha
davvero spuntato nel dialogo. Una Pagina che resta nel CRM senza token e' una
Pagina che **l'ultimo login non ha incluso** — e non viene cancellata perche'
qualcuno l'aveva accesa o perche' ha gia' prodotto lead (buttarla via
porterebbe con se' la sua storia).

Quindi il CRM adesso lo scrive. Dopo ogni sincronizzazione, ogni Pagina rimasta
fuori viene marcata `granted = 0` (e `token_valid = 0`, perche' senza token non
funziona niente), e nella lista compare l'etichetta rossa **"Non concessa"** con
la spiegazione. Il messaggio d'errore delle tre azioni che richiedono il token
non dice piu' "Reconnect Facebook" e basta, ma:

> Facebook non ha incluso questa Pagina nell'ultimo collegamento, quindi il CRM
> non ha un token per lei. Premi "Riconnetti" e spunta questa Pagina nel
> dialogo. Se li' non compare, appartiene al portfolio Business di qualcun
> altro: deve essere il proprietario a darti un ruolo sulla Pagina.

Quest'ultima frase e' il punto. **Riconnettere non puo' funzionare se il dialogo
non offre quella Pagina**, e non la offre finche' il Business Manager che la
possiede non ti assegna un ruolo (serve almeno Inserzionista). E' un passaggio
che avviene su Facebook, tra due persone, e nessun codice puo' farlo al posto
loro: l'unica cosa utile che il software puo' fare e' dirlo chiaramente invece
di mandarti in cerchio.
