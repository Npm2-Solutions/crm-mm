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

## Solo le Pagine concesse

L'elenco mostra `/me/accounts`, che e' esattamente cio' che si e' spuntato nel
dialog di Facebook — una Pagina amministrata tramite un portfolio Business
compare qui, una volta concessa.

Il CRM ha provato anche a percorrere `owned_pages` e `client_pages` del
portfolio: era un errore. Quegli edge restituiscono anche Pagine **non**
concesse, che arrivano senza i permessi per usarle. Ogni chiamata su di esse
fallisce con *"permission(s) must be granted before impersonating a user's
page"* e riempiono l'elenco di righe che nessuno puo' accendere. Chi vuole una
Pagina in piu' la aggiunge dal dialog, con "Scegli le pagine".

Una Pagina tolta dal dialog sparisce anche da qui, purche' non ci sia appeso
nulla: con dei moduli, o con la sincronizzazione lead ancora accesa, resta.

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
verifica firma webhook.
