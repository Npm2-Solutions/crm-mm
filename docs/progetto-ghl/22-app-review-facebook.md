# 22 — App Review dell'app Facebook: cosa serve e cosa no

*17/09/2026. Stato letto dall'API di Meta, non dedotto.*

## Dove siamo

L'app WhatsApp (`NPM2 Solutions WA Business`) e' approvata: `whatsapp_business_messaging` e
`whatsapp_business_management` con accesso **advanced**, app in live mode, e la
Coexistence funziona. Questa pagina riguarda **l'altra** app, quella dei lead ads
e del Social Planner.

| | |
|---|---|
| App | `NPM2 Solutions` (`1438298434873676`) |
| Modalita' | **dev mode**, non live |
| Permission che servono | tutte a `access_level: none` |
| Privacy policy | ✅ |
| Verifica business | ✅ **superata** |
| Data Use Checkup | ❌ su **tutti** i 17 privilegi richiesti |
| Data Deletion URL | ❌ vuoto |
| Si puo' inviare? | **No**: `can_submit: false`, "Cannot submit to App Review while a previous submission is in review" — mentre lo stato della submission dice `UNSUBMITTED` |

## Cosa vuol dire "dev mode" per i lead

Dalla doc dei Lead Ads, alla lettera:

> You can't retrieve leads if your app is in Development mode. For testing
> purposes, Development mode app users can access leads submitted by someone
> with a role in that same app.

Cioe': i lead arrivano nel CRM oggi **solo perche' l'app e' tua e le pagine sono
tue**. Su una pagina di un cliente non arriveranno mai finche' l'app non e'
approvata e in live mode. Non e' una questione di configurazione: e' la
modalita' dell'app.

## Le permission che servono davvero

La doc "Retrieving Leads" e' esplicita su cosa serve per leggere i lead:

> To retrieve all lead data and ad level data, you will need: [...] the
> `ads_management` permission, the `leads_retrieval` permission, the
> `pages_show_list` permission, the `pages_read_engagement` permission, the
> `pages_manage_ads` permission.

E la pagina Lead Ads aggiunge: *"You must include the `leads_retrieval` and
`pages_manage_ads` permissions in your submission."* `pages_manage_metadata`
serve *"if using webhooks"*, che e' come li prendiamo noi.

**Correzione di una cosa detta prima.** Avevo scritto che, secondo i requisiti
dell'API, `leads_retrieval` non ha prerequisiti e che valeva la pena verificare
se `ads_management` e `pages_manage_ads` si potevano togliere. La doc dice il
contrario: servono. Il campo `prerequisite_privileges` dell'API descrive le
dipendenze di *review*, non cio' che l'endpoint pretende a runtime. Il commento
nel nostro `SCOPES` era giusto e resta.

### Da chiedere — lead ads (7)

| Permission | Perche' | Passi che chiede |
|---|---|---|
| `pages_show_list` | elencare le pagine del cliente (`/me/accounts`) | use case, screencast, DUC |
| `pages_read_engagement` | leggere i dati della pagina e i suoi moduli | use case, screencast, api precheck, DUC |
| `pages_manage_metadata` | iscrivere la pagina al webhook `leadgen` | use case, screencast, api precheck, DUC |
| `leads_retrieval` | leggere `/{form}/leads` e `/{leadgen_id}` | **use case + DUC** |
| `ads_management` | richiesta dalla doc per leggere i dati del lead | use case, screencast, api precheck, DUC |
| `pages_manage_ads` | idem, e obbligatoria nella submission | use case, screencast, api precheck, DUC |
| `business_management` | le pagine possedute da un portfolio Business, che senza questa non compaiono nemmeno dopo essere state spuntate | use case, screencast, api precheck, DUC |

### Da togliere dalla richiesta (6)

Il nostro codice non le chiede mai, e ognuna e' un use case e uno screencast in
piu' su cui farsi rifiutare:

`instagram_business_basic` · `instagram_business_manage_messages` ·
`instagram_manage_comments` · `ads_read` · `Marketing API Access Tier` ·
`Business Asset User Profile Access`

### Da rimandare al secondo giro (3)

`pages_manage_posts` · `instagram_basic` · `instagram_content_publish` — sono il
Social Planner. Funziona anche dopo, e tenerle nella prima submission raddoppia
la superficie su cui un revisore puo' dire no.

## L'ordine delle operazioni

1. **Data Use Checkup.** Blocca tutti e 17 i privilegi, `public_profile`
   compreso — e quello non aspetta altro. E' un modulo, non un video.
2. **Data Deletion Request URL.** L'endpoint esiste gia' nel nostro codice:
   `https://hub.npm2solutions.com/api/method/crm.integrations.meta.webhook.data_deletion`
3. **Sbloccare la submission.** `can_submit: false` dice che una submission e'
   in review, lo stato dice `UNSUBMITTED`: una delle due informazioni e'
   sbagliata. La dashboard di App Review dira' quale; se non c'e' niente in
   corso, e' un caso per il supporto sviluppatori.
4. **Sfoltire** come sopra: 7 invece di 17.
5. **Categoria dell'app**: oggi e' "Social networks and dating". Per un CRM e'
   fuorviante per chi la esamina; "Business" descrive cosa fa.
6. **Use case** (i testi sotto) e, dove chiesto, screencast e api precheck.
7. Dopo l'approvazione: **switch a Live mode**. Prima di quello, i lead dei
   clienti non arrivano.

## Sugli screencast: quello che e' successo davvero

Sull'app WhatsApp `screencast` e `api_precheck` risultano **ancora non
completati**, e Meta ha approvato comunque: sono bastati use case, Data Use
Checkup e verifica business. Non e' una garanzia che valga anche qui — sono
permission diverse e revisori diversi — ma e' una ragione per **inviare** invece
di restare fermi mesi ad aspettare di aver girato quattro video.

## I testi da incollare

In inglese, perche' in inglese vengono lette. Uno per permission, nel campo che
chiede come la si usa.

### `pages_show_list`

> Our CRM is used by small businesses to manage the leads they generate on
> Facebook. After the business owner connects their Facebook account, we call
> `/me/accounts` to show them the list of their own Pages, so they can choose
> which Page's leads should flow into their CRM. We do not read Page content and
> we do not use this permission for anything else. The list is shown once, in the
> connection screen, and only to the person who granted it.

### `pages_read_engagement`

> After the business owner picks a Page, we read that Page's lead generation
> forms (`/{page-id}/leadgen_forms`) so the CRM can show which forms exist and
> map each form question to a CRM field. This is the only data we read with this
> permission: we do not read posts, comments or insights.

### `pages_manage_metadata`

> We subscribe our app to the Page's `leadgen` webhook
> (`POST /{page-id}/subscribed_apps` with `subscribed_fields=leadgen`) so that a
> lead reaches the business owner's CRM within seconds of being submitted,
> instead of being found hours later. The same permission lets us unsubscribe
> when the business owner disconnects the Page, which our product does
> automatically.

### `leads_retrieval`

> This is the core of the integration. When the `leadgen` webhook notifies us of
> a new lead, we read it (`GET /{leadgen-id}`) and create a contact in the
> business owner's own CRM, mapping each answer to a field they configured. We
> also read `/{form-id}/leads` to recover leads Meta delivered while the CRM was
> unreachable, and to import the existing leads of a form the owner has just
> connected. The data is used only to populate that business's CRM: it is never
> sold, shared with third parties, or used for advertising.

### `ads_management`

> Required by the Lead Ads documentation to retrieve full lead data, including
> the ad-level fields. We use it exclusively to read the leads and their
> attribution (which ad and form produced the lead), so the business owner can
> see which campaign a customer came from. We do not create, edit, pause or
> spend on any ad.

### `pages_manage_ads`

> Required in the submission by the Lead Ads documentation, alongside
> `leads_retrieval`, to read the leads of a Page's lead forms. We use it only for
> that read: the CRM has no advertising features.

### `business_management`

> The Pages of our customers are usually owned by a Business portfolio rather
> than by a personal profile. Without this permission those Pages do not appear
> in the connection screen even after the owner has ticked them, so the business
> owner cannot connect the Page they actually use. We read the list of Pages a
> Business owns; we do not manage the Business, its users or its assets.

### `ads_read`

> Granted as part of the Marketing API use case that `ads_management` belongs to;
> `ads_management` is required by the Lead Ads documentation to retrieve full
> lead data. Our application does not read ad insights, spend or campaign
> performance. The only ad data we read is the name of the ad, ad set and
> campaign that produced a lead, so the business owner can see which of their
> ads brought each customer.

### `Marketing API Access Tier`

> This feature is part of the lead ads use case our application requires; we are
> not requesting it in order to obtain higher rate limits or unlimited ad account
> management.
>
> Our application is a CRM for small businesses. Our use of these APIs is
> read-only and limited to lead retrieval on behalf of the Page owner who granted
> access: we read the Page's lead generation forms, we subscribe to the Page's
> `leadgen` webhook, and when a person submits a lead form we read that lead and
> create a contact in that business's own CRM. We also read the name of the ad,
> ad set and campaign behind each lead, so the owner sees "from the ad Autumn
> Promo, campaign September Leads" instead of a numeric id.
>
> We create no campaigns, ad sets, ads or audiences; we read no insights, spend
> or performance metrics; we manage no ad accounts and we create no system users.
> The Limited access tier is sufficient for our operations.
>
> The data we receive is used only to populate the CRM of the business that
> granted access. It is never sold, shared with third parties, or used for
> advertising or profiling.

## Il "0 di 500" dell'Access Tier

La doc della Marketing API: *"Limited access (default): automatically granted
when you add the Marketing API product to your app"*, e Full access chiede
*"at least 500 Marketing API calls in the last 15 days"* con meno del 15% di
errori.

Quindi **Limited ci basta** — le letture dei lead non sono governate da quei
limiti ma da quelli della pagina, che hanno la loro formula (200 × 24 × lead
degli ultimi 90 giorni). Quella riga non e' un permesso mancante: e' un upgrade
dei limiti di traffico che non ci serve.

Da quando il CRM legge il nome dell'inserzione, **le chiamate alla Marketing API
esistono davvero** — una per inserzione nuova, piu' i rinnovi settimanali, piu'
quelle di un backfill su 90 giorni. Se arrivano a 500 in 15 giorni dipende da
quante inserzioni diverse porta il traffico: non e' garantito, e non va forzato.
Il punto non era far diventare verde un pallino: era non dover scrivere a Meta
una giustificazione falsa.

## Cosa mostrare negli screencast

Uno solo basta, girato sul CRM vero, con questi passaggi in fila: Settings →
Meta → "Connect with Facebook" → il dialog di Facebook con la scelta delle
pagine → l'elenco delle pagine nel CRM → l'interruttore di sincronizzazione su
una pagina → i moduli della pagina con la mappatura delle domande → l'invio di
un lead di prova dal modulo → il lead che compare nella lista Persone con i
campi compilati. E' la stessa storia che raccontano tutti gli use case, quindi lo
stesso video si allega a tutte le permission che lo chiedono.
