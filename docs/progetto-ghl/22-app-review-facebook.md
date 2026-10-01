# 22 — App Review dell'app Facebook: cosa serve, cosa no, cosa rifare

*01/10/2026. Stato letto dall'API di Meta e dal PDF inviato il 21/09/2026 (con i dieci video
allegati guardati uno per uno), non dedotto. Sostituisce la versione del 17/09, che
parlava di dev mode e di 17 permission da sfoltire: la revisione è chiusa.*

## Dove siamo

| | |
|---|---|
| App | `NPM2 Solutions` (`1438298434873676`) |
| Modalità | **live** |
| Conformità | ✅ nessuna azione richiesta, Data Use Checkup e verifica business superati |
| Revisione | chiusa il 01/10/2026 (`ACTIONED`): 6 approvate, 7 respinte |

**Approvate, accesso advanced** (nessuna azione): `pages_show_list`, `pages_manage_metadata`,
`leads_retrieval`, `business_management`, `ads_management`, `public_profile`.

**Respinte:**

| Permission | Motivo di Meta | Che cos'era davvero |
|---|---|---|
| `pages_manage_posts`, `instagram_basic`, `instagram_content_publish` | screencast non in linea con il caso d'uso | il video non mostrava né il login né la pubblicazione riuscita (sotto) |
| `ads_read` | idem | il video mostra Ad performance ma non il login, e senza didascalie |
| `pages_manage_ads` | caso d'uso non valido o non necessario | per Meta questa permission serve a **creare e gestire** inserzioni; noi non lo facciamo mai |
| `pages_read_engagement` | idem | il testo parlava solo dei moduli lead; la permission è pensata per leggere i contenuti della Pagina |
| `Marketing API Access Tier` | non bastano le chiamate Marketing API riuscite negli ultimi 15 giorni | non c'è nulla da dimostrare con un video: servono 500 chiamate riuscite in 15 giorni |

## Cosa c'era che non andava nell'invio del 21/09

I testi erano quasi tutti giusti: descrivono quello che il codice fa. Il guaio erano i video e il
modulo.

**Video.** I dieci link sono otto video diversi, tutti a 640×290. In nessuno ho visto
didascalie o tooltip, e la finestra di Facebook è in italiano.

- `pages_manage_posts`, `instagram_basic` e `instagram_content_publish` usano **lo stesso
  video** (stessa durata, stessi fotogrammi), quello del Social Planner. Parte dal calendario, senza Meta Login. Mostra un solo
  profilo, `@osteopatatalia` (Instagram, nessuna Pagina Facebook), e il primo clic su
  "Publish now" dà l'errore *"Select at least one social account"*. Il post era un "T" con
  uno screenshot **PNG**, programmato per una data passata, e il video finisce su
  "Publishing…" con la voce **rossa (Failed)** nel calendario. Nessun post compare mai su
  Facebook o su Instagram.
- `ads_read` mostra Ad performance con la spesa per inserzione, ma non il Meta Login.
- `pages_manage_ads` e `pages_read_engagement` mostrano le schermate dei moduli lead (e un lead
  di prova che arriva), senza il Meta Login.
- `pages_show_list` e `business_management` mostrano il Meta Login completo, con l'elenco delle
  autorizzazioni: sono passate.

**Modulo per il revisore.**

- "Is Facebook Login integrated on this platform?" era su **No**: l'app usa Facebook Login.
- Le istruzioni erano in italiano e senza il percorso nel menu.
- La password di prova era in chiaro nel PDF: cambiala a revisione finita.

**Il probabile motivo del post fallito.** Instagram pubblica solo **JPEG** (lo dice la doc di
Meta sulla pubblicazione) e `crm/social/publisher.py` manda il file così com'è. Lo screenshot era
un PNG. È un'ipotesi: l'errore vero è salvato sul post (aprilo nel Planner e leggilo).

## Che cosa serve davvero

| Funzione | Chiamate | Permission | Se Meta dice no |
|---|---|---|---|
| Lead ads | `/me/accounts`, `/{page}/leadgen_forms`, `/{page}/subscribed_apps`, `/{lead}`, `/{form}/leads` | `pages_show_list`, `pages_manage_metadata`, `leads_retrieval`, `business_management` | ✅ già approvate |
| Nomi e creatività delle inserzioni, stato di consegna, Conversions API | `/{ad}`, `/{act}/ads`, `POST /{dataset}/events` | `ads_management` | ✅ già approvata |
| Spesa per inserzione | `/me/adaccounts`, `/{act}/insights` | `ads_read` (o `ads_management`) | si perde la spesa, il costo per lead e il costo per cliente; i lead non cambiano |
| Social Planner | `/{page}/feed`, `/photos`, `/videos`, `/{ig}/media`, `/{ig}/media_publish` | `pages_manage_posts`, `instagram_basic`, `instagram_content_publish`, più `pages_read_engagement` come prerequisito | il Planner non pubblica sulle Pagine dei clienti |
| nessuna | nessuna | `pages_manage_ads` | niente: il codice non crea né gestisce inserzioni |

Due cose che non si possono dire con certezza da qui:

- **`pages_manage_ads` serve per leggere i lead?** La doc di Meta la elenca fra le dipendenze di
  `leads_retrieval`, ma `leads_retrieval` è stata approvata senza. Un account con un ruolo
  sull'app non fa vedere la differenza: serve il test della sezione "Il test prima di
  reinviare".
- **`pages_read_engagement`.** Per il Planner Meta la elenca come prerequisito di
  `pages_manage_posts` e `instagram_content_publish`. Per i soli lead non è chiaro: la doc dice
  che per leggere i dati di una Pagina basta una fra `pages_read_engagement`,
  `pages_manage_ads` e `pages_manage_metadata`, e quest'ultima è approvata.

## Cosa reinviare

| Permission | Decisione |
|---|---|
| `pages_manage_posts`, `instagram_basic`, `instagram_content_publish` | **reinvia** con il video A |
| `pages_read_engagement` | **reinvia**, ma presentata come prerequisito del Planner (testo nuovo) e con il video A |
| `ads_read` | **reinvia** con il video B |
| `pages_manage_ads` | **non reinviare** finché il test non dice che serve; il testo di riserva è sotto |
| `Marketing API Access Tier` | **non reinviare** finché la dashboard non dice che le 500 chiamate ci sono |

Se non vuoi il Planner adesso, togli `pages_manage_posts`, `instagram_basic`,
`instagram_content_publish` e `pages_read_engagement` dall'invio e da `SCOPES`
(`crm/integrations/meta/oauth.py`), e togli "Post programmati" dal sito. Reinviare un Planner che
non si riesce a mostrare funzionante è l'unico modo di farsi respingere di nuovo.

## Il test prima di reinviare

Serve un account Facebook **senza alcun ruolo sull'app** (con un ruolo, Meta concede anche le
permission non approvate e il test non dice niente).

1. Su un sito di prova, metti nel `site_config.json` solo le permission approvate:
   `"meta_scopes": ["pages_show_list", "pages_manage_metadata", "leads_retrieval", "ads_management", "business_management"]`.
2. Collega Facebook con quell'account, accendi una Pagina e invia un lead di prova dal
   Lead Ads Testing Tool di Meta.
3. Se il lead arriva con i campi e con l'`ad_id`: `pages_manage_ads` e (senza Planner)
   `pages_read_engagement` si tolgono da `SCOPES` e dalla richiesta. Se fallisce con "(#200)" o
   "(#283)": reinvia `pages_manage_ads` con il testo di riserva.

Il banner rosso "Facebook did not grant everything…" comparirà su quel sito: è atteso, perché
`missing_scopes()` confronta con tutti gli `SCOPES`.

## Prima di girare

- **Un sito di prova**, con la sua connessione Facebook. Sull'hub di produzione non premere mai
  "Disconnect": spegne l'import dei lead dei clienti. Per rivedere la finestra di Facebook usa
  "Reconnect".
- **Solo risorse tue o di prova.** Nel video dei lead si vedevano nomi di Pagine e di account
  pubblicitari dei clienti. Scegli nella finestra di Facebook soltanto la Pagina, l'account
  Instagram e l'account pubblicitario di prova.
- **Tutto in inglese**: lingua del profilo CRM, lingua di Facebook, lingua di Instagram.
- **Una Pagina Facebook di cui sei amministratore**, con un account Instagram professionale
  collegato. Se Instagram rifiuta la pubblicazione, controlla la Page Publishing Authorization
  della Pagina.
- **Una foto JPEG vera**, non uno screenshot PNG. Dopo averla caricata, apri il suo indirizzo in
  una finestra privata: deve vedersi senza accesso (Instagram la scarica dal nostro server).
- **Una prova a vuoto prima di registrare**: programma un post, aspetta che diventi verde, guarda
  che compaia su Facebook e su Instagram. Se diventa rosso, leggi l'errore e risolvi prima di
  filmare.
- **Registrazione** a 1080p, almeno. Mouse lento. Le didascalie in inglese (iMovie, CapCut,
  DaVinci): una frase breve per ogni passaggio, e il nome della permission nel momento in cui la
  usi.
- Il codice **non è stato cambiato**: la conversione in JPEG per Instagram non c'è ancora (vedi
  "Cosa resta da correggere").

## Video A — Social Planner

Si allega a: `pages_manage_posts`, `pages_read_engagement`, `instagram_basic`,
`instagram_content_publish`. Durata: 3-4 minuti.

| # | Cosa si vede | Didascalia (inglese) |
|---|---|---|
| 1 | Scheda titolo, 3 secondi | *NPM2 Solutions (app ID 1438298434873676) — Social Planner: scheduling a post to a Facebook Page and an Instagram account* |
| 2 | Accesso al CRM con l'account di prova | *The business owner signs in to the CRM* |
| 3 | Menu in alto a sinistra → Settings → Integrations → Meta → scheda **Connection** | *Settings → Integrations → Meta* |
| 4 | Clic su **Connect with Facebook** (o **Reconnect**) | *The owner connects their Facebook account* |
| 5 | Finestra di Facebook: URL `facebook.com` visibile, "Continue as…" | *Facebook Login: the owner signs in on Facebook* |
| 6 | La scelta della Pagina e dell'account Instagram: spunta solo quelli di prova | *The owner chooses which Page and Instagram account the app can use* |
| 7 | L'elenco delle autorizzazioni, scorso lentamente | *The owner reviews and grants the permissions: show Pages, manage and post on Pages, Instagram account and content publishing* |
| 8 | Clic su Save/Continue, poi "Facebook connected" | *Permissions granted* |
| 9 | Settings → Marketing → **Social Planner**: la Pagina e `@account` Instagram nell'elenco dei profili | *pages_show_list, pages_read_engagement, instagram_basic: the Page and its linked Instagram account appear as publishing profiles* |
| 10 | Menu → **Social Planner** → **New post** | *The owner writes a post* |
| 11 | Seleziona **entrambi** i profili, scrivi un testo vero, aggiungi la foto JPEG | *One post for the Facebook Page and the Instagram account* |
| 12 | "Schedule at": fra 4-5 minuti da ora. Clic su **Schedule** | *The owner schedules the post for a date and time* |
| 13 | Il calendario con il post blu (Scheduled) | *The post is waiting for its time* |
| 14 | Taglio. Il post diventa verde (Published); apri il post per mostrare l'orario | *At the scheduled time the CRM publishes it: POST /{page-id}/photos and POST /{ig-user-id}/media_publish* |
| 15 | Nuova scheda: la Pagina Facebook con il post | *pages_manage_posts: the post is on the owner's Facebook Page* |
| 16 | Nuova scheda: Instagram con il post | *instagram_content_publish: the same post is on the owner's Instagram account* |

Da evitare: "Publish now" invece di "Schedule" (il testo parla di post programmato); date nel
passato; un profilo solo; finire su un errore; le Pagine dei clienti.

Il pezzo "dopo due minuti" si può tagliare: lo scheduler passa ogni 2 minuti (`process_due_posts`).
Tieni però l'orologio del sistema o del post in vista prima e dopo il taglio.

## Video B — Spesa pubblicitaria

Si allega a: `ads_read`. Durata: 2 minuti.

| # | Cosa si vede | Didascalia (inglese) |
|---|---|---|
| 1 | Scheda titolo | *NPM2 Solutions (app ID 1438298434873676) — Ad performance: reading the spend of the owner's ad account* |
| 2 | Accesso, poi Settings → Integrations → Meta → **Connection** → **Reconnect** | *The business owner connects Facebook* |
| 3 | Finestra di Facebook: scegli **solo l'account pubblicitario di prova** fra le risorse | *The owner chooses which ad account the app can read* |
| 4 | Le autorizzazioni, scorse lentamente, poi Save | *The owner grants access to their ad account* |
| 5 | Scheda **Ad performance** → **Find my ad accounts** | *GET /me/adaccounts: the app lists the ad accounts the owner can see* |
| 6 | Accendi **Read spend** sull'account di prova | *The owner chooses which account feeds the CRM* |
| 7 | Clic su **Read spend now**, il messaggio "Reading the spend in the background" | *GET /act_{id}/insights?level=ad&time_increment=1: spend, impressions and clicks per ad per day* |
| 8 | La tabella: spesa, lead, costo per lead, costo per cliente | *ads_read: the spend from Meta, the leads and the clients from the CRM, on one line per ad* |
| 9 | (facoltativo) la dashboard con "Cost per new client" | *The same numbers on the owner's dashboard* |

Da evitare: i conti pubblicitari di altri; la tabella senza spesa (scegli un account con
spesa negli ultimi 7 giorni, altrimenti la tabella è vuota e il revisore non vede nulla).

## I testi da incollare

In inglese, perché in inglese vengono letti. Uno per permission, nel campo "Tell us how you're
using this permission or feature".

### `pages_manage_posts`

> The CRM includes a social planner for the business that owns a Facebook Page. After the owner
> connects Facebook, the planner lists the Pages they chose to share with the app. The owner writes
> a post, selects one of their own connected Pages, picks a date and time, and presses Schedule.
> At that time the CRM publishes the post to that Page on the owner's behalf: POST
> /{page-id}/feed for text, POST /{page-id}/photos for an image, POST /{page-id}/videos for a
> video, with the Page access token the owner's login produced. The owner can also set a post to
> repeat daily, weekly or monthly.
>
> This improves the experience because the same small business that answers its leads in the CRM
> also has to keep its Page active, and doing both in one place — with the calendar next to the
> leads those posts produce — removes a separate tool and a separate login from its day. It is
> necessary because publishing to a Page through the API is impossible without it.
>
> We only publish posts the owner wrote and scheduled in the CRM, only to Pages the owner
> connected, and only at the time they chose. We never edit or delete existing posts and never
> post anything the owner did not write.

### `pages_read_engagement`

> We request pages_read_engagement because Meta lists it as a prerequisite of pages_manage_posts
> and instagram_content_publish, the permissions our social planner publishes with, and because it
> lets the app read basic metadata about the Pages the owner connected.
>
> We read only that metadata: GET /me/accounts?fields=id,name,category,tasks,instagram_business_account{id,username}
> returns each Page's id, name, category, the tasks the owner has on it and the Instagram business
> account linked to it, and GET /{page-id}/leadgen_forms returns the name, status and questions of
> the Page's lead forms. We use them to show the owner their Pages and linked Instagram accounts
> as publishing profiles and lead sources, and to tell which Pages the connection can actually use.
>
> We do not read posts, photos, videos, comments, followers or Page insights. We store the Page's
> id, name and category, its access token (encrypted) and the Instagram username, only for the
> business that connected the Page.

### `instagram_basic`

> When the owner connects Facebook, we read the Instagram business account linked to each Page
> they connected (the instagram_business_account field of the Page: its id and username) and show
> that username in the social planner's list of profiles, so the owner can choose to publish to
> Instagram as well as to the Page. A Page with no linked Instagram account simply offers Facebook
> only.
>
> It is necessary because it is the permission that exposes the Instagram business account id,
> and that id is the target of every Instagram publishing call: without it the app cannot know
> which Instagram account belongs to the owner, and instagram_content_publish has nothing to
> publish to. We use it only for the account's id and username; we do not read its media,
> followers, comments or messages.

### `instagram_content_publish`

> In the CRM's social planner the owner writes a post, selects the Instagram business account
> linked to their Page, attaches a photo and a caption, picks a date and time and presses Schedule.
> At that time the CRM publishes it on the owner's behalf: POST /{ig-user-id}/media creates the
> container with the image and the caption, we check GET /{container-id}?fields=status_code until
> it reports FINISHED, and then POST /{ig-user-id}/media_publish publishes it.
>
> This improves the experience because the business that works its leads in the CRM keeps its
> Instagram presence from the same calendar, next to the leads that come from it, instead of
> switching tools. It is necessary because it is the only way to publish to an Instagram business
> account through the API.
>
> We publish only content the owner wrote and scheduled, only to an Instagram account linked to a
> Page the owner connected. Nothing is published without the owner scheduling it.

### `ads_read`

> The CRM shows each business what its ads cost next to what they brought. The owner chooses which
> of their ad accounts feed the CRM: we call GET /me/adaccounts to list the accounts the connected
> user can read, and nothing is read until the owner switches an account on.
>
> For each account switched on we read the spend: once a day we call GET /act_{id}/insights with
> level=ad and time_increment=1, for the last seven days, and store the spend, impressions and
> clicks per ad per day. The CRM already knows which ad produced each lead and which of those
> leads became a paying client. Putting the two together gives the owner, for each ad, the cost per
> lead, the cost per client and the return on ad spend, on one line. Ads Manager can show the cost
> per lead, but only the CRM knows which of those leads actually bought, and the two figures very
> often disagree: the ad with the cheapest leads is frequently the one with the worst clients.
>
> It is necessary because the spend is half of that calculation and exists only on Meta's side.
> We store only aggregated metrics (spend, impressions, clicks per ad per day) and only for the
> business that owns the ad account. The data is used to report to that business and for nothing
> else.

### `pages_manage_ads` — solo se il test dice che serve

> We request pages_manage_ads only because the Lead Ads documentation lists it among the
> permissions needed to retrieve full lead data: "To retrieve all lead data and ad level data, you
> will need the ads_management permission, the leads_retrieval permission, the pages_show_list
> permission, the pages_read_engagement permission, the pages_manage_ads permission." In our app it
> is used in that capacity only: it is part of the permission set with which the Page access token
> reads each lead and the ad fields that come with it (ad_id, ad_name, adset and campaign names).
> The CRM does not create, edit, pause or delete any campaign, ad set, ad, creative or audience
> and has no feature that does. We would not request this permission if the lead retrieval worked
> without it.

### `Marketing API Access Tier` — non ancora

Prima che la dashboard dica che le 500 chiamate riuscite in 15 giorni ci sono. Il testo inviato il
21/09 è quasi tutto vero. Va corretta una frase: *"no call is made for an ad nobody has looked
at"*, falsa, perché una volta al giorno leggiamo in blocco lo stato di consegna di tutte le
inserzioni dell'account (`{act}/ads`). Al suo posto:

> Creatives are fetched only when someone opens a lead that came from that ad, and cached for 30
> days; ad names are cached for 7 days; the delivery status of an account's ads is read in one
> paginated call per account per day, together with the daily spend.

### Il modulo per il revisore

**"Is Facebook Login integrated on this platform?"** → **Yes**.

**Istruzioni di accesso** (il percorso è quello del codice attuale: controllalo sul sito prima
dell'invio, se l'hub gira ancora la versione del 21/09 il percorso è "Meta & Messaging → Meta
connection"):

> 1. Open https://hub.npm2solutions.com/ and sign in with the email and password below.
>    Email: fbverify@npm2solutions.com — Password: [la password di prova]
> 2. The account is a sales manager of a demo CRM. It is already connected to a test Facebook
>    Page, a linked Instagram business account and a test ad account, so every screen can be seen
>    without a Facebook login. The screen recordings show the complete Facebook Login flow.
> 3. Facebook Login: user menu (top left) → Settings → Integrations → Meta → "Connection" tab →
>    "Connect with Facebook".
> 4. Lead ads (pages_show_list, pages_manage_metadata, leads_retrieval, business_management,
>    ads_management): same page, "Connection" and "Lead Ads" tabs.
> 5. Ad spend (ads_read): same page, "Ad performance" tab → "Find my ad accounts" → "Read spend now".
> 6. Social planner (pages_manage_posts, pages_read_engagement, instagram_basic,
>    instagram_content_publish): Settings → Marketing → "Social Planner" lists the Page and the
>    Instagram account; then the "Social Planner" entry in the left menu → "New post".
> 7. The app is not server-to-server and does not use a system user token: users sign in with
>    Facebook Login for Business.

Se vuoi che il revisore provi il login da sé, aggiungi un Test User in App Dashboard → Roles e
metti le sue credenziali nel campo facoltativo dei codici di accesso.

## Dopo l'invio

1. Se la dashboard dice che la revisione è in corso e l'invio resta bloccato, è un caso per il
   supporto sviluppatori (era già successo a settembre).
2. La spesa degli ultimi 15 giorni si legge ogni giorno da `sync_ad_spend`: per le 500 chiamate
   guarda App Dashboard → App Review → Permissions and Features → Marketing API Access Tier. Non
   forzare chiamate a vuoto.
3. Dopo l'approvazione, controlla che un cliente vero riceva i lead con un account senza ruolo
   sull'app: è l'unico test che conta.

## Cosa resta da correggere nel codice (non fatto)

- **Instagram vuole JPEG.** `crm/social/publisher.py` dovrebbe convertire in JPEG un'immagine PNG
  prima di mandarla.
- **`SCOPES` obbligatori e opzionali.** Con le permission del Planner e di `pages_manage_ads`
  ancora non approvate, `missing_scopes()` accusa ogni cliente di non aver concesso tutto, anche
  con i lead che funzionano. I lead stanno nell'insieme obbligatorio, il Planner e la spesa in
  quello opzionale.
- **Il Planner non dovrebbe chiedere `instagram_business_account`** se `instagram_basic` non è
  concessa: non ho verificato come risponde Meta.
