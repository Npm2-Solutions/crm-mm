# 12 — WhatsApp Business, connesso dal cliente in un click

> ✅ **FASE 1 IMPLEMENTATA (03/09/2026)** — onboarding completo. Verificato
> sulle guide Meta di settembre 2026. Resta un **prerequisito bloccante lato
> Meta** (programma Tech Provider) prima di poterlo provare davvero: vedi sotto.

## L'obiettivo

Come per Facebook: il cliente apre Settings → WhatsApp, preme **Connetti**,
**scansiona un QR code col telefono**, e da quel momento le chat WhatsApp
stanno **sia nel CRM sia nell'app WhatsApp Business sul telefono**, sincronizzate.
Una sola app Meta dell'agenzia per tutti i clienti.

## Le pagine legali

`/privacy` e `/terms` sono **record `Web Page`**, spediti come fixture dell'app
(`crm/fixtures/web_page.json`, registrati in `hooks.py`). Arrivano con
`bench migrate` e valgono per entrambe le app Meta: la revisione le pretende su
ognuna, ma nulla impedisce che puntino allo stesso posto.

Essendo record e non template, si correggono dall'interfaccia Website senza
toccare il codice — ma **`bench migrate` li reimporta**, quindi una correzione
che deve durare va riportata anche nel file della fixture, altrimenti al
deploy successivo torna indietro.

Il testo descrive cio' che il sistema tratta davvero — token dei collegamenti,
risposte ai moduli, messaggi WhatsApp, eventi di calendario, e con chi sono
condivisi — ma non e' stato rivisto da un legale.


## Due modi di collegare un numero, per due situazioni diverse

**Il QR (Embedded Signup)** e' la via dei clienti, e resta l'unica che viene
loro offerta: premono un bottone, scansionano dall'app WhatsApp Business, non
vedono un token.

**Le credenziali a mano** (Settings → WhatsApp → *Aggiungi un numero con le sue
credenziali*) servono a un numero che Embedded Signup non puo' raggiungere: il
**numero di test** che Meta presta a ogni app. Non e' un ripiego, e' l'unica
strada possibile in quel momento — l'agenzia ne ha bisogno per registrare i
video dell'App Review **prima** di essere Tech Provider, e senza di esso il CRM
non puo' inviare un solo messaggio.

Il token da usare e' quello **permanente da system user**, non il temporaneo
della dashboard, che scade a meta' registrazione.

## Un'app separata da quella di Facebook

WhatsApp ha la **sua** app Meta, non quella dei lead e del Social Planner.
`whatsapp_app_id` e `whatsapp_app_secret` nel config del bench; se mancano si
ricade su `meta_app_id`/`meta_app_secret`, cosi' chi tiene tutto in un'app sola
continua a funzionare senza toccare niente.

Perche' separate:

- **L'App Review e' serializzata per app.** Meta rifiuta una nuova submission
  finche' un'altra e' in revisione: con un'app sola la review di WhatsApp si
  mette in coda dietro quella delle Pagine, e viceversa.
- **Il rigetto e' contagioso.** Meta avverte che chiedere permessi non
  necessari e' causa comune di rigetto: un'app che chiede insieme lead,
  gestione Pagine, pubblicazione Instagram e messaggistica offre una superficie
  enorme a un solo revisore.
- **La restrizione lo e' altrettanto.** Un problema di policy sul lato
  messaggistica, che e' la parte piu' regolata, fermerebbe anche i lead ads di
  tutti i clienti.
- **Cicli di vita diversi**: status Tech Provider, limiti di onboarding e di
  messaggistica riguardano solo WhatsApp.

Non si duplica nulla di importante: la **Business Verification sta sul
portfolio**, non sull'app, quindi due app sotto lo stesso Business Manager la
condividono. L'hub resta uno solo, con lo stesso dominio in allowlist.

L'hub rifirma le consegne WhatsApp con il secret **dell'app WhatsApp**: se si
separano le app senza impostare `whatsapp_app_secret`, le firme non tornano e
i messaggi vengono rifiutati a valle.

## Cosa mettere dove, sull'app WhatsApp

Tutti gli indirizzi puntano all'**hub**, mai al site del cliente: e' l'hub a
ospitare la pagina di Embedded Signup e a ricevere i webhook, poi smista.
Cento clienti, un dominio solo.

| Dove, sull'app | Cosa mettere |
|---|---|
| Manage domains → allowlist | `<hub>` (solo il dominio, serve al JavaScript SDK) |
| Webhooks → WhatsApp Business Account | `https://<hub>/api/method/crm.integrations.whatsapp.webhook.handle` |
| … verify token | quello del site hub (Settings → Meta connection) |
| … campi | `messages`, `smb_message_echoes`, `history`, `smb_app_state_sync`, `message_template_status_update` |
| Facebook Login for Business → Configurations | configurazione Embedded Signup con Coexistence; il suo id va in `whatsapp_signup_config_id` |
| App settings → Basic → + Add Platform → **Website** | Site URL: `https://<hub>/` — senza la piattaforma Website il JavaScript SDK non e' autorizzato |
| App settings → Basic | Privacy Policy `https://<hub>/privacy` e Terms of Service `https://<hub>/terms` |
| App settings → Advanced → Data Deletion Request URL | `https://<hub>/api/method/crm.integrations.meta.webhook.data_deletion` |

Il callback di cancellazione dati e' **lo stesso** per le due app: valida la
firma con entrambi i secret, quindi accetta sia quella di Facebook sia quella
di WhatsApp. Non serve un secondo endpoint.

Il webhook non va incollato a mano: sull'hub, Settings → WhatsApp mostra il
bottone **"Configuralo"** quando manca, e lo registra da solo sull'app
(`{app_id}/subscriptions`). Meta verifica il callback sul momento, quindi
l'hub deve gia' rispondere in HTTPS.

**Nessun redirect URI da whitelistare.** Embedded Signup usa il JavaScript SDK
e restituisce il codice alla finestra che l'ha aperta: la lista dei "Valid
OAuth Redirect URIs" riguarda solo l'app Facebook.

## Cosa serve sull'app

Il collegamento col QR passa da **Embedded Signup**, che Meta sblocca solo alle
app registrate come **Tech Provider**. Sull'app servono, nell'ordine:

1. **Use case "Connect with customers through WhatsApp"**, aggiunto all'app.
   Porta con se' tre permessi obbligatori che non si possono togliere:
   `public_profile`, `whatsapp_business_management`, `whatsapp_business_messaging`.
   `business_management` e `email` sono opzionali: il primo serve solo per
   leggere il portfolio via API — con Meta Business Suite non serve.
2. **Business Verification** del portfolio dell'agenzia.
3. **App Review con Advanced access** su `whatsapp_business_management` e
   `whatsapp_business_messaging`. Senza Advanced access l'app non puo' toccare
   i WABA di clienti che non sono nostri: le chiamate tornano errore 200. Meta
   pretende **un video separato per ogni permesso** (uno che mostra la
   creazione di un modello, uno che mostra l'invio di un messaggio ricevuto
   dal client WhatsApp) piu' una descrizione scritta per ciascuno: un video
   solo per due permessi fa respingere la richiesta.
4. **Configurazione Facebook Login for Business** di tipo Embedded Signup: e'
   lei che genera il `config_id` da mettere in `whatsapp_signup_config_id`.
5. **Manage domains**: il dominio dell'hub va in allowlist, altrimenti il
   JavaScript SDK non parte.

In development mode i permessi compaiono nel dialog solo a chi ha un ruolo
sull'app; in live mode compaiono **solo** quelli approvati in App Review.

**Limiti di onboarding**: 10 nuovi clienti in 7 giorni finche' non si
completano Business Verification, App Review e Access Verification; poi 200.


## Il QR code: quale dei due

Esistono due strade che passano per un QR, e vanno distinte bene.

| | **Coexistence (ufficiale)** | **Ponte WhatsApp Web (non ufficiale)** |
|---|---|---|
| Cos'è | Funzione Meta: l'app WhatsApp Business del cliente viene collegata alla Cloud API | Librerie tipo Baileys / whatsapp-web.js / Evolution API che pilotano WhatsApp Web |
| QR | Sì, si scansiona **dall'app WhatsApp Business** | Sì, si scansiona come "dispositivo collegato" |
| Il cliente continua a usare il telefono | **Sì**, è il punto della funzione | Sì, ma la sessione è fragile |
| Storico chat | **Sincronizza 6 mesi di conversazioni 1:1** e 2 settimane di media | Solo da quel momento |
| Termini di servizio | Conforme | **Violazione**: numeri bannati, rottura a ogni aggiornamento di WhatsApp |
| Costo | Tariffe Meta per conversazione | "Gratis" finché non ti bannano il numero del cliente |

**Andiamo di Coexistence.** Dà esattamente l'esperienza che hai in mente — QR,
telefono che continua a funzionare, chat in entrambi i posti — restando una cosa
vendibile. La strada non ufficiale, su numeri di clienti paganti, è un rischio
che non vale la pena correre.

## Finire la configurazione dell'app (17/09/2026)

Le permission sono approvate — `whatsapp_business_messaging` e
`whatsapp_business_management` con accesso **advanced**, che è ciò che rende
l'app un Tech Provider. Restano tre cose, e due sono sul lato Meta:

1. **La configurazione di Embedded Signup.** Sull'app WhatsApp: *Facebook Login
   for Business → Configurations → Create from template →* "WhatsApp Embedded
   Signup". Il template con scadenza token a 60 giorni è quello indicato dalla
   doc. Si copia l'**id della configurazione**.
2. **Le impostazioni OAuth del client**, sotto *Facebook Login for Business →
   Settings*: Client OAuth login, Web OAuth login, Enforce HTTPS, Embedded
   Browser OAuth Login, Strict Mode, e **Login with the JavaScript SDK** —
   Embedded Signup gira nel browser col JS SDK. Il domino dell'hub va in
   *Allowed domains*; il redirect URI
   (`https://hub.../whatsapp-connect`) c'è già.
3. **L'id nel CRM.** Prima si poteva solo dal bench
   (`whatsapp_signup_config_id`); adesso si incolla nella schermata, perché su
   un host gestito il bench non è di chi configura, e quell'id è l'ultima cosa
   fra un cliente e il QR. Il bench continua a vincere dove c'è.

Due cose trovate mentre si verificava:

**`account_update` non era sottoscritto.** L'Embedded Signup lo richiede — è
come Meta racconta l'esito di un onboarding e lo stato dell'account dopo — e noi
avevamo `handle_account_update` senza iscriverci al campo: quindi era codice
morto, e un onboarding fallito non lo sapeva nessuno. Ora è in `WEBHOOK_FIELDS`
e viene smistato al nostro handler come gli altri campi della Coexistence.

**L'app WhatsApp può essere quella di Facebook per sbaglio.**
`get_whatsapp_app_id()` ripiega sull'app Meta quando non c'è un id proprio: è
legittimo (un'app sola per tutto) ed è anche identico a un'impostazione
dimenticata, che è come le chiamate WhatsApp finiscono firmate dall'app
Facebook. La schermata adesso dice quale app sta firmando, e se l'ha presa in
prestito.

### Quando "Start" non fa niente

La pagina dell'hub chiamava `FB.login` senza sapere se lo script di Facebook era
arrivato. Se non era arrivato — e la causa piu' comune e' un blocco pubblicita'
o privacy su `connect.facebook.net` — il pulsante si disabilitava, lo stato
diceva "Opening WhatsApp setup…" e non succedeva piu' nulla: un fallimento muto
su un pezzo che non si puo' nemmeno riprovare a caso.

Adesso la pagina sa tre cose e le dice:

- **lo script non c'e'**: aspetta fino a otto secondi (puo' solo essere lento) e
  poi dice che e' bloccato e cosa fare. Il nuovo tentativo lo fa la persona, di
  proposito: la finestra di Facebook si apre solo da un click vero, e premere
  Start al posto suo la farebbe bloccare come popup;
- **`FB.login` solleva un'eccezione**: popup bloccato, SDK vecchio,
  configurazione sbagliata — lo dice invece di fermarsi;
- **`FB.login` torna senza `authResponse`**: puo' essere una finestra chiusa
  dalla persona, ma e' anche cosa succede quando *Login with the JavaScript SDK*
  e' spento sull'app o il dominio non e' fra gli Allowed domains. Il messaggio
  nomina entrambe, e `status` finisce nel log della sessione.

Dove si guarda: **WhatsApp Signup Session** sull'hub. C'era gia' e registra ogni
passo; un `STARTED` senza niente dopo vuol dire che il click e' arrivato al
server e la finestra di Facebook non si e' mai aperta.

## Architettura (stesso schema del Facebook già fatto)

L'onboarding di Coexistence si fa con **Embedded Signup**, che gira nel browser
col **JS SDK di Facebook**: la pagina che lo ospita deve stare nella whitelist
dell'app. Con N siti cliente varrebbe lo stesso problema dei redirect URI —
e la soluzione è la stessa: **la pagina di connessione la ospita l'hub**.

```
cliente.it → Settings → WhatsApp → "Connetti"
           → si apre l'hub:  https://hub/whatsapp-connect?site=<firmato>
HUB        → FB.login() con il config_id dell'Embedded Signup v4
             il cliente sceglie/crea la WABA, il numero, e SCANSIONA IL QR
             dall'app WhatsApp Business (schermata gestita da Meta)
           → l'evento WA_EMBEDDED_SIGNUP restituisce waba_id + phone_number_id
           → callback FB.login restituisce un code con TTL di SOLI 30 SECONDI
HUB        → scambia SUBITO il code per il business token (server-side)
           → POST firmato (relay secret) al site del cliente: token + id
cliente.it → salva l'account WhatsApp, si iscrive ai webhook, pronto
```

Il code dura 30 secondi: per questo l'hub **scambia lui** e passa il token al
site via server-to-server, invece di rimbalzare il code nel browser come
facciamo per Facebook.

### Webhook: i flussi sono simmetrici

Come per i lead, la sottoscrizione è **a livello di app**: tutti i messaggi di
tutti i clienti arrivano all'hub, che li smista per WABA (o `phone_number_id`).

Ma la Coexistence aggiunge tre campi che una normale integrazione Cloud API non
vede mai — ed è qui che sta la sincronizzazione bidirezionale:

| Campo | Cosa porta | Chi lo capisce |
|---|---|---|
| `messages` | messaggi in arrivo dai clienti + stati di consegna | **frappe_whatsapp** |
| `smb_message_echoes` | i messaggi che l'azienda scrive **dal telefono** | **nostro** |
| `history` | fino a 6 mesi di conversazioni passate, a chunk | **nostro** |
| `smb_app_state_sync` | la rubrica dell'azienda | **nostro** |
| `account_update` | esito dell'Embedded Signup, stato dell'account | **nostro** |

`frappe_whatsapp` conosce solo `messages`: senza gestire gli altri, **quello che
il cliente scrive dal telefono non comparirebbe nel CRM** — cioè verrebbe a
mancare metà della promessa. Perciò l'hub **spacchetta ogni entry per campo**:
`messages` va all'endpoint di frappe_whatsapp (rifirmato con l'app secret, così
lo valida come una consegna Meta normale), il resto al nostro
(`receive_events`, firmato col relay secret) che li trasforma in
`WhatsApp Message`.

⚠️ Gli echo vengono scritti con `db_insert()`, **non** con `insert()`: un
messaggio Outgoing inserito normalmente farebbe partire l'invio via API a
frappe_whatsapp, e il messaggio — già partito dal telefono — verrebbe recapitato
due volte.

### L'app deve essere pubblicata, altrimenti non riceve niente

> *«Apps in development mode can only receive test notifications initiated
> through the app dashboard or notifications initiated by people who have a role
> on the app»* — e il pannello WhatsApp è ancora più netto: in dev mode **non
> vengono inviati dati di produzione**, nemmeno quelli di amministratori,
> sviluppatori o tester.

Quindi il webhook può essere configurato alla perfezione e non arrivare nulla lo
stesso. Per passare a Live servono, nelle impostazioni di base: privacy policy,
icona 1024×1024, categoria, uso aziendale, e l'email di contatto verificata.

Il passaggio a Live è indipendente dall'App Review: la review serve per
l'**Advanced Access**, cioè per agire sugli asset di *altre* aziende. Con lo
Standard Access un'app Live lavora sui propri, e il numero di test lo è.

### Perché un numero invia ma non riceve

Sono **tre** condizioni, e solo la prima serve per inviare:

| Cosa | Chi la crea | Se manca |
|---|---|---|
| token sull'account | Embedded Signup, o l'aggiunta manuale | non parte niente |
| `POST /{waba_id}/subscribed_apps` | Embedded Signup (`subscribe_waba`) | Meta non notifica l'app per quel WABA |
| `Meta WhatsApp Route` sull'hub | Embedded Signup (`claim_route`) | l'hub riceve l'entry e **la scarta**, perché non sa a chi darla |

L'aggiunta manuale di un numero non passa dall'hub, quindi non aveva nessuna
delle ultime due: un numero di test collegato a mano poteva inviare e non
riceveva mai nulla, senza un errore da nessuna parte. Ora `add_account` le
esegue entrambe, e il bottone **Check incoming** nelle impostazioni le rifà (sono
idempotenti) dicendo quale delle due non riesce.

Resta comunque necessaria la sottoscrizione **a livello di app** (callback URL +
verify token), che è quella del bottone *Configure it*: senza, Meta non chiama
l'hub per nessun cliente.

### La finestra di 24 ore

WhatsApp lascia scrivere liberamente solo per **24 ore dall'ultimo messaggio del
cliente**. Fuori da quella finestra Meta consegna soltanto un **template
approvato**, e un testo libero torna indietro con l'errore 131047.

Nella chat del CRM la finestra è calcolata dall'ultimo messaggio `Incoming`, e
quando è chiusa compare l'avviso con il bottone che apre i template. L'avviso
**non blocca** l'invio: quello che sappiamo della finestra vale quanto i messaggi
in entrata che ci sono arrivati, e finché la ricezione non è a posto sarebbe un
blocco basato su dati incompleti.

### Session logging

Meta richiede che l'Embedded Signup sia implementato **con session logging**.
La pagina dell'hub riporta ogni passo (`WA_EMBEDDED_SIGNUP`, avvii, annulli con
`current_step`, errori) a `log_session_event`, che li registra nel doctype
**`WhatsApp Signup Session`**: un onboarding che si pianta diventa assistibile
invece che un mistero.

## Cosa serve lato Meta (da fare in quest'ordine)

1. **Programma Tech Provider** — *il prerequisito bloccante*: la documentazione
   dell'Embedded Signup dice "You must already be a Solution Partner or Tech
   Provider". Va richiesto a Meta ed è un processo di verifica. **È la cosa più
   lunga: va avviata subito**, in parallelo con l'App Review dei lead.
2. Prodotto **WhatsApp** aggiunto all'app, con `whatsapp_business_management` e
   `whatsapp_business_messaging`.
3. **Configurazione Facebook Login for Business** per **Embedded Signup v4**
   (variante di login "WhatsApp Embedded Signup"; prodotti: WhatsApp Cloud API
   e Marketing Messages API). ⚠️ Le configurazioni fatte per la v2 **non
   valgono**: la v2 va in pensione il **15 ottobre 2026**.
4. Dominio dell'**hub** in *Allowed domains* e *Valid OAuth redirect URIs*;
   attivi: Client OAuth login, Web OAuth login, Enforce HTTPS, Embedded Browser
   OAuth Login, Strict Mode, **JavaScript SDK login**.
5. Webhook `messages` + `account_update` sull'URL dell'hub.

## Cosa c'è già nel CRM

Il fork parla già con l'app **`frappe_whatsapp`** (di Frappe): doctype
`WhatsApp Message`, `WhatsApp Templates`, `WhatsApp Account`, `WhatsApp Settings`.
`crm/api/whatsapp.py` legge e scrive quei documenti, l'interfaccia chat su
Lead/Deal esiste già (`WhatsAppArea.vue`, `WhatsAppBox.vue`, selettore di
template), e le automazioni hanno già il trigger `on_whatsapp_received`.

Manca **solo l'onboarding**: oggi un `WhatsApp Account` va configurato a mano,
incollando token e phone number id — esattamente la cosa da cui vogliamo
scappare.

## Piano di lavoro

**Fase 1 — onboarding ✅ fatta**
- `crm/www/whatsapp_connect.*` — pagina `/whatsapp-connect` sull'hub con
  l'Embedded Signup v4 (JS SDK, `featureType: whatsapp_business_app_onboarding`
  per la Coexistence), raggiunta con uno state firmato;
- `crm/integrations/whatsapp/signup.py` — scambio del code entro i 30 secondi,
  lettura del numero, sottoscrizione della WABA, consegna firmata al site;
- `crm/integrations/whatsapp/api.py` — il site riceve le credenziali e crea da
  sé il `WhatsApp Account` di frappe_whatsapp (scrivendo **solo i campi che
  quella versione ha davvero**, per non rompersi con release diverse) e lo
  imposta come account di invio;
- `crm/integrations/whatsapp/webhook.py` — l'hub spacchetta il payload per
  account e lo **rifirma con l'app secret**: il site di destinazione lo valida
  come una consegna Meta normale, quindi frappe_whatsapp lo elabora senza
  sapere che esiste un hub;
- doctype `Meta WhatsApp Route` (WABA → site), con le stesse difese delle
  pagine: elenco chiuso dei site e nessuna riassegnazione silenziosa;
- Settings → WhatsApp: stato, numeri, scelta del numero di invio, disconnessione;
- test: `crm/tests/test_whatsapp_connect.py`.

**Config aggiuntiva** (oltre a quelle di `11-app-meta-agenzia.md`):
`whatsapp_signup_config_id` = l'id della configurazione Embedded Signup v4.

## Cosa si può fare in chat (verificato sul codice)

| | Ricezione | Invio |
|---|---|---|
| Testo, emoji | ✅ | ✅ |
| Immagini | ✅ | ✅ |
| Video | ✅ | ✅ |
| Documenti | ✅ | ✅ |
| Audio | ✅ ascolto in chat | ✅ upload **e registrazione vocale dal browser** |
| Reazioni | ✅ | ✅ |
| Risposte a un messaggio | ✅ | ✅ |
| Messaggi da template | ✅ (resi con le variabili sostituite) | ✅ selettore template |

La **registrazione vocale** usa `MediaRecorder`: si preme il microfono nel
composer, il contatore mostra la durata, si preme stop e la nota vocale viene
caricata e inviata come messaggio audio. Se il browser non lo supporta o il
microfono è negato, lo dice invece di fallire in silenzio.

## File, audio e video: perché non partivano

Tre difetti in fila, tutti nostri.

**Il file era privato.** `frappe_whatsapp` non carica il file su Meta: gli passa
un **link** e Meta lo scarica da solo, senza sessione. `FileUploader` di
frappe-ui però carica in privato se non gli si dice il contrario, e un file
privato di Frappe a quella richiesta risponde con la pagina di login. Quindi
ogni messaggio con un allegato falliva, sempre, qualunque fosse il file.

**La nota vocale era in webm.** `MediaRecorder` su Chrome registra
`audio/webm`, che WhatsApp **non accetta**: la lista di Meta è AAC, AMR, MP3,
M4A e OGG (solo Opus, mono). Ora si registra in OGG/Opus o MP4, e se il browser
non sa fare né l'uno né l'altro lo si dice invece di registrare qualcosa che non
può essere consegnato.

**Niente diceva cosa fosse andato storto.** I formati accettati si controllano
adesso *prima* di caricare, per nome ed estensione — immagini JPEG e PNG fino a
5 MB, video MP4 e 3GP fino a 16 MB, audio fino a 16 MB, documenti fino a 100 MB.

E un messaggio fallito non è più un vicolo cieco: ha un **Riprova** accanto.
`send_outgoing` di frappe_whatsapp è scritto per poter essere richiamato, non
aveva solo nessuno che lo chiamasse. Se fallisce di nuovo, torna l'errore di
Meta, che è il motivo per cui si riprova a mano invece che in coda.

Il badge rosso, poi, cercava `failed` minuscolo — che è quello che dice il
webhook di Meta — mentre un invio mai partito scrive `Failed`. Un messaggio
fallito qui non mostrava proprio nessun badge.

## A quale numero stiamo scrivendo

Una persona ha un contatto solo — il CRM ne garantisce esattamente uno — ma quel
contatto può avere **più numeri**: il cellulare, la linea dell'ufficio, quello
vecchio che qualcuno aveva segnato. Non è un lusso: è quello che impedisce i
doppioni. Se scrive dal secondo numero e il CRM non lo conosce, il messaggio non
si aggancia a nessuno e finisce per **creare un secondo lead** per una persona
che avevamo già.

Quindi i numeri restano più d'uno, e la chat dice sempre a quale sta scrivendo.
Sopra il campo del messaggio c'è **«A: +39 …»**: se il numero è uno solo lo
scrive e basta, se ce n'è più d'uno diventa una tendina e si sceglie.

Il **principale** — quello che si usa quando nessuno sceglie, e quello che
chiamano il pulsante di chiamata e le automazioni — si imposta dal blocco dei
recapiti sulla scheda della persona: si clicca il numero e diventa principale.

La scelta la fa il browser ma non la decide: `whatsapp_recipient` accetta solo un
numero **che appartiene a quella persona** e rifiuta gli altri, perché un numero
arbitrario manderebbe la conversazione a uno sconosciuto.

## Una sola strada

Settings → WhatsApp ha **solo** il flusso di connessione: nessun form dove
incollare token e phone number id, nessuna configurazione alternativa. Un
numero entra nel CRM in un modo solo — Connetti, QR, fatto.

Questo significa che finché l'Embedded Signup non è disponibile (app non
ancora approvata, o `whatsapp_signup_config_id` mancante) il bottone resta
disabilitato e non c'è ripiego dentro il CRM. Per l'agenzia non è un blocco:
i doctype restano raggiungibili dal Desk (`/app/whatsapp-account`) come per
qualsiasi cosa in Frappe. Ma non è una strada offerta al cliente.

## Template: si creano nel CRM

### I template che esistono su Meta e non qui

La lista del CRM legge i record locali. Un template creato da **WhatsApp
Manager** — o `hello_world`, che Meta crea da sé con ogni nuovo WABA — su Meta
c'è e qui no: non si vede e non si può mandare.

Il bottone **«Sincronizza da Meta»** li porta dentro. Riallinea anche lo stato di
quelli creati da noi: normalmente arriva sul webhook
`message_template_status_update`, e questa è la via di ritorno se uno andasse
perso.

La `fetch` di frappe_whatsapp scrive con `db_insert`/`db_update` e non con
`insert`, quindi **non ri-sottopone niente a Meta**: legge soltanto. Se usasse
`insert` farebbe scattare l'`after_insert`, che rimanderebbe ogni template a
Meta come se fosse nuovo.

### Cosa Meta pretende, e cosa sbagliavamo

Un template con dei segnaposto viene **rifiutato all'istante** se non gli si dà
un esempio per ciascuno: *«you must include an example value for each
parameter»*. E i segnaposto devono essere numerati **da {{1}} senza buchi**.

Il modulo del CRM non aveva il campo degli esempi, quindi ogni template con un
`{{1}}` partiva senza e tornava REJECTED un secondo dopo il salvataggio, con il
motivo visibile solo in WhatsApp Manager. Ora il campo c'è — compare solo se il
corpo ha dei segnaposto — e il controllo si fa **prima** di salvare, mentre chi
scrive ha ancora il testo davanti.

Altri due difetti dello stesso modulo:

- **L'intestazione spariva.** `frappe_whatsapp` mette l'header nel payload solo
  se `header_type` dice di che tipo è; noi scrivevamo il testo e non il tipo,
  quindi Meta non lo vedeva mai. Ora il tipo lo deriviamo dal testo.
- **La lingua.** Il doctype ha `language` (Link a Language, obbligatorio) e ne
  ricava lui `language_code`. Noi compilavamo il codice e lasciavamo vuoto il
  campo obbligatorio, offrendo una lista scritta a mano di tre voci — `en`,
  `en_US`, `it` — che è quella che sembrava avere due volte l'inglese. Ora si
  sceglie una lingua vera e il codice se lo calcola l'app.


Prima il bottone "Create New Template" apriva il **form grezzo del Desk**
(`/app/whatsapp-templates/new`): fuori dal gestionale e incomprensibile per un
cliente. Ora c'è **Settings → WhatsApp Templates**: elenco con lo stato di
approvazione (Approvato / In attesa / Rifiutato), creazione e modifica con
categoria, lingua, header, corpo con le variabili `{{1}}` e footer. Il
salvataggio inoltra il template a Meta per la revisione — è frappe_whatsapp a
parlare con Meta, noi mettiamo l'interfaccia sopra.

I nomi dei campi vengono letti dal doctype installato invece che dati per
scontati: con una release diversa di frappe_whatsapp l'interfaccia si adatta
invece di rompersi.

### Variabili dei template

Un template con `{{1}}`, `{{2}}`… non si può inviare alla cieca. Quando lo si
sceglie in chat, il CRM legge quante variabili ha
(`get_template_placeholders`) e chiede i valori mostrando l'anteprima del
messaggio; i valori vengono salvati sul messaggio, così la timeline mostra il
testo **davvero** partito. Nelle automazioni lo stesso blocco accetta un valore
per variabile, e ognuno passa da `render()`: si può scrivere
`{{ first_name }}` e prenderlo dal record.

**Fase 2 — quel che resta**
- finestra 24h: avviso in chat quando serve un template per riaprire;
- header con media (immagine/video/documento) e bottoni nei template: l'editor
  fa header di testo, corpo e footer;
- valori di esempio per le variabili in fase di invio a Meta (li chiede in
  revisione per i template con placeholder);
- sincronizzazione dello stato di approvazione via webhook
  `message_template_status_update` (oggi lo stato si aggiorna quando
  frappe_whatsapp lo rilegge).

> L'azione **"Invia template WhatsApp" nelle automazioni c'è già** dal lavoro
> sul motore (`step_send_whatsapp_template`): non era da fare.

## Costi e chi li paga

Dal **1 luglio 2025** Meta non fattura più a conversazione ma **a messaggio**, e
solo quando viene consegnato un **template**:

- ogni messaggio **non-template** (testo, immagine, audio…) è **gratis**, ma si
  può inviare solo dentro la finestra di 24 ore;
- i template **utility** consegnati dentro una finestra aperta sono gratis;
- i template **marketing** si pagano sempre, con tariffa per categoria e prefisso
  del destinatario;
- entrando da un *free entry point* tutto è gratis per 72 ore.

### Chi mette la carta

Da **Tech Provider non hai una linea di credito**. La documentazione Meta è
esplicita: i clienti onboardati da un Tech Provider *«must provide their own
payment method after onboarding is complete»*, Meta fattura loro l'uso dell'API e
il partner fattura i propri servizi. E soprattutto: senza metodo di pagamento
sulla propria WABA il cliente **non può né inviare né ricevere** con la nostra
app.

Va quindi messo nell'onboarding: dopo il QR, il cliente deve aggiungere una carta
alla sua WhatsApp Business Account. Non è un dettaglio amministrativo, è un
prerequisito tecnico.

L'alternativa — linea di credito condivisa, fattura aggregata a noi, noi che
fatturiamo ai clienti — è riservata ai **Solution Partner**, processo lungo e che
ci rende *«Bill To Party»*: responsabili verso Meta di tutta la spesa dei clienti
che usano la nostra linea.

Il **numero di test** che Meta presta all'app è l'eccezione: WABA e numero di
test *«don't require a payment method on file in order to send template
messages»* e hanno limiti rilassati. Per registrare i video di App Review basta
quello.

## "URL bloccato" e il link che scadeva troppo presto (21/09/2026)

Due cose diverse, incontrate nello stesso tentativo di collegare un numero in
Coexistence.

### L'URL bloccato non era nostro

> Questo reindirizzamento non e' riuscito perche' l'URI di reindirizzamento non
> e' stato aggiunto alla whitelist nelle impostazioni OAuth client dell'app.

Letto dalle impostazioni dell'app WhatsApp (`1025903810451453`):

```
oauth_redirect_uris:  https://hub.npm2solutions.com/whatsapp-connect
js_sdk_host_domains:  https://hub.npm2solutions.com/
```

> **Correzione (21/09, sera).** Qui era scritto che la causa fosse *"Accedi con
> l'SDK JavaScript" spento*. Era sbagliato: l'interruttore era gia' acceso, e
> me l'ha fatto notare chi l'aveva acceso. La causa vera e' documentata ed e'
> un'altra.

L'URI in whitelist e' giusto — la pagina risponde sia con il trattino sia con
l'underscore, e il CRM manda al trattino. Il blocco non viene dal percorso e
non viene da un interruttore: viene da **cosa fa l'SDK quando il popup non si
apre**.

Dalla documentazione di Meta, *Login Security → In-App Browsers and the
JavaScript SDK*:

> The JavaScript SDK normally relies on popups and callbacks to complete a
> Login. For some in-app browsers that suppress popups, this can fail. When
> this happens, **the SDK will automatically attempt to redirect** […] to the
> page that invoked it. It can only do this redirect safely if the full URI of
> the page is listed in the Valid OAuth Redirect URIs.

La pagina che invoca il login e' `/whatsapp-connect?state=…`. Quella con lo
`state` attaccato **non** e' l'URI registrato, e Strict Mode confronta
carattere per carattere. Da qui "URL bloccato": non un permesso mancante, ma
un ripiego dell'SDK verso un indirizzo che l'app non conosce.

La stessa pagina di Meta dice come si chiude:

> If you have a lot of variation in the URIs where Login happens for your app,
> you can manually specify a **`fallback_redirect_uri`** as an option in the
> `FB.login()` call so you only need to add that one entry to your Valid OAuth
> Redirect URIs list.

Ed e' quello che la pagina fa adesso: fissa il ripiego sulla pagina nuda,
scritta esattamente come e' registrata. Il resto del giro di ritorno e'
descritto sotto, in *Quando il popup non si apre*.

Gli interruttori di *Accesso Facebook per le aziende → Impostazioni* vanno
comunque tutti su Si' — Client OAuth login, Web OAuth login, Enforce HTTPS,
Embedded Browser OAuth Login, Strict Mode, Login with the JavaScript SDK — ma
su questa app lo erano gia'.

### Il link scadeva in quindici minuti

`STATE_TTL` era 900 secondi. Un onboarding Coexistence vero significa aprire
WhatsApp sul telefono, confermare, copiare un codice di verifica e tornare
indietro — e chi prima deve anche fare login su Facebook supera il quarto d'ora
senza accorgersene.

Quando lo `state` scadeva a meta' flusso succedevano due cose, entrambe mute:
il **log di sessione smetteva di scrivere** (quindi dai log sembrava che nessuno
avesse mai premuto Start) e lo **scambio del codice falliva**.

Adesso dura **un'ora** — lo state dice soltanto "quale sito ha iniziato" ed e'
firmato, quindi una vita lunga non costa niente mentre una corta costava tutto —
e il log di sessione accetta anche uno state scaduto, marcandolo `expired:`.
Un onboarding che si e' trascinato e' esattamente quello che vale la pena vedere
scritto: rifiutarsi di registrarlo e' il modo in cui un flusso incagliato
diventa invisibile.

## Quando il popup non si apre (21/09/2026)

Il popup soppresso non e' un caso di bordo: e' il browser in-app di Instagram,
di Facebook, di un client di posta — cioe' i posti da cui un cliente clicca un
link che gli abbiamo mandato. Quando succede, l'SDK naviga invece di aprire una
finestra, e navigare distrugge la pagina che stava ascoltando.

Tre cose si rompevano in fila, e ognuna da sola bastava:

1. **Il ritorno era bloccato.** L'SDK rimandava all'URL che aveva aperto il
   login (`/whatsapp-connect?state=…`), che non e' l'URI registrato. Strict
   Mode: "URL bloccato".
2. **Il ritorno veniva scambiato per un link rotto.** La pagina leggeva lo
   `state` dalla query. Strict Mode non lo lascia passare (la sua eccezione per
   `state` ne ignora il valore), quindi la pagina diceva *"link non valido o
   scaduto"* a una registrazione appena conclusa.
3. **Mancavano i due id.** `waba_id` e `phone_number_id` arrivano in un
   `postMessage` alla finestra che ha aperto il flusso. Quella finestra non
   c'e' piu'.

### Come si chiudono

**`fallback_redirect_uri`** fissa dove Facebook puo' rimandare: la pagina nuda,
uguale all'URI registrato. Un solo indirizzo in whitelist, qualunque sia la
pagina di partenza.

**`sessionStorage`** porta quello che l'URL non puo' portare. Prima di lanciare
il login la pagina scrive nel tab lo `state` e l'indirizzo di ritorno; al
ritorno li rilegge. Stesso tab, stessa origine, sopravvive all'andata su
facebook.com. Se il browser l'ha svuotato, la pagina lo dice invece di girare
a vuoto.

**`debug_token`** recupera gli id quando nemmeno il tab li ha. E' la via
documentata in *Manage WhatsApp Business accounts*:

> After a business finishes the Embedded Signup flow, you can get the shared
> WABA ID using the returned accessToken with the Debug Token endpoint. […]
> IDs for the most recently onboarded WABAs appear first, so capture the first
> ID in the `target_ids` array for the `whatsapp_business_management` scope.

Dal conto, `GET /{waba_id}/phone_numbers` da' il numero.

**Un dettaglio che costa un giro intero**: un codice emesso su un redirect e'
legato a quell'indirizzo, e lo scambio deve ricitarlo in `redirect_uri`. Il
flusso col popup non ha nessun indirizzo e non deve mandarne — mandarlo lo fa
rifiutare.

## La pagina di accesso ospitata da Meta: perche' non sostituisce la nostra

Nel pannello WhatsApp Meta offre un URL gia' pronto:

```
https://business.facebook.com/messaging/whatsapp/onboard/
    ?app_id=…&config_id=…&extras={"sessionInfoVersion":"3","version":"v4"}
```

Si chiama **Hosted Embedded Signup**, e la tentazione e' ovvia: funziona
sempre, perche' gira su facebook.com e quindi non ha ne' domini in whitelist
ne' popup da far sopravvivere. Togliere la nostra pagina e mandare li' sarebbe
un problema in meno.

Non si puo', e le ragioni sono tre, tutte documentate.

**1. Non fa Coexistence.** Dalla pagina *Hosted Embedded Signup*:

> Hosted Embedded Signup ("Hosted ES") can only be used to onboard business
> customers to **Cloud API**, and **the flow cannot be customized**.

Coexistence e' esattamente una personalizzazione del flusso
(`featureType: whatsapp_business_app_onboarding`). Il flusso ospitato porta il
cliente a un numero Cloud API nuovo — non al numero che ha gia' in mano, non
con lo storico delle chat. E' un altro prodotto, non un'altra porta per lo
stesso.

**2. Non torna indietro niente al browser.** Con Hosted ES gli id del cliente
arrivano dal webhook `account_update` con `event: PARTNER_ADDED`, e il token si
prende con la **System User Access Tokens API** puntando al portfolio del
cliente, con il nostro system token e l'`appsecret_proof`. Non c'e' codice da
scambiare, non c'e' callback: e' una catena di onboarding diversa da scrivere
per intero, che pretende anche un system token conservato sull'hub.

**3. Non sa da quale sito arriva il cliente.** L'URL non porta `state`, e non
c'e' un posto documentato dove infilarcelo. Con un site per cliente, l'hub
riceverebbe un `PARTNER_ADDED` con un WABA e nessun modo di dire di chi e'.

E c'e' un equivoco da sciogliere: la pagina ospitata **non** toglie una
schermata intermedia. E' anche lei una schermata con un bottone *Get started*,
solo che sta su facebook.com invece che sull'hub. Quello che toglie e' la
*nostra* pagina, non *una* pagina — e il motivo per cui quella funziona sempre
non e' che sia piu' semplice, e' che parte gia' dal dominio giusto.

Resta buona per una cosa: se un giorno serve collegare un cliente **senza**
WhatsApp Business gia' in uso — numero nuovo, Cloud API puro — quello e' il
flusso adatto, e quel giorno serviranno le tre cose sopra.

## Due configurazioni di accesso, e la differenza dura 60 giorni

Sull'app WhatsApp ci sono due configurazioni di Facebook Login for Business
valide per Embedded Signup:

| Id | Nome | Scadenza del token |
|---|---|---|
| `2922986928038126` | Tech Provider Embedded Signup config | **Mai** |
| `2026289871367450` | WhatsApp Embedded Signup con token a 60 giorni | 60 giorni |

Quella dei 60 giorni e' il template che la documentazione di Meta suggerisce
per cominciare (*Create from template → WhatsApp Embedded Signup Configuration
With 60 Expiration Token*). Per noi e' la scelta peggiore, e in modo
silenzioso: il token che conserviamo per il cliente muore al sessantesimo
giorno, il cliente scopre che WhatsApp non funziona piu' senza che niente
glielo abbia detto prima, e per rimetterlo a posto deve rifare tutto il giro,
QR compreso.

**Quella in uso e' la prima** (verificato 22/09): la Tech Provider, senza
scadenza. E' anche quella giusta per come lavoriamo, e la documentazione dice
perche': per un Tech Provider il token corretto e' il *Business Integration
System User access token*, che «defaults to never expire» e si ottiene
**scambiando il codice** — che e' esattamente cio' che fa `exchange_code`.

C'e' una conseguenza di quella scelta che vale la pena sapere, perche' cambia
cosa vede il cliente. Da *Facebook Login for Business*:

> If you select **System-user access token** then your app users will be
> **required to log in using a business portfolio**.

Quindi il flusso passa per un portfolio business, e un errore del tipo «X non
e' un ID business valido» va cercato li' — nel portfolio con cui si entra nel
flusso — non nel codice.

### Quale configurazione stiamo mandando davvero

Il pannello di Meta mostra quale configurazione e' selezionata **nel suo
builder**. Non e' la stessa cosa di quale id manda questo CRM: quello sta in
`whatsapp_signup_config_id`, fra bench config e Settings. Distinguere le due a
naso e' costato un pomeriggio, quindi ora Settings → WhatsApp scrive l'id in
uso accanto a quello dell'app, e dice da dove viene.

E si e' visto subito a cosa serviva: il builder di Meta mostrava la Tech
Provider, ma l'id che il CRM mandava era quello **a 60 giorni**. Le due cose
erano diverse e nessuno poteva accorgersene.

### E si puo' cambiare

La casella dell'id compariva **solo finche' l'id mancava**, dentro il riquadro
"Still missing". Appena salvato, il riquadro spariva e con lui l'unico posto da
cui modificarlo: il primo valore salvato era anche l'ultimo possibile. Un'app
puo' tenere piu' configurazioni, e quale mandare cambia — un token che scade
contro uno che non scade — quindi la casella non poteva essere un fatto
irreversibile.

Adesso la riga dell'id ha **Cambia** accanto, precompilata con quello in uso.
Non compare quando l'id viene dal bench config: li' la modifica da questa
schermata non avrebbe effetto, perche' il bench vince, e un campo che non fa
niente e' peggio di nessun campo.

## Il campo del webhook che non c'era

L'iscrizione registrata sull'app ha cinque campi:

```
messages, smb_message_echoes, history, smb_app_state_sync,
message_template_status_update
```

Nel codice ce ne sono sei: c'e' anche **`account_update`**, che la guida di
Embedded Signup mette fra i prerequisiti —

> You must be subscribed to the `account_update` webhook, as this webhook is
> triggered whenever a customer successfully completes the Embedded Signup
> flow, and contains their business information that you will need.

E' stato aggiunto al codice dopo che l'iscrizione esisteva gia', e **Meta non
aggiorna da sola un'iscrizione esistente**. Risultato: il gestore c'era, il
campo no, e una registrazione fallita non diceva niente a questo CRM.

La schermata guardava solo se l'URL fosse registrato — trovava di si', e
taceva. Adesso legge anche i campi e, quando ne manca qualcuno, lo scrive per
nome con un bottone *Completalo* accanto. Da premere una volta.

## Un click, e si apre Facebook (22/09/2026)

La pagina `/whatsapp-connect` con il bottone **Start** era una schermata di
troppo: il cliente preme Connetti nel CRM, e la cosa dopo che deve vedere e'
Facebook, non una pagina che gli spiega che sta per vedere Facebook.

Non si poteva togliere finche' il lancio passava da `FB.login`, per un motivo
strutturale: `FB.login` apre un popup, e un popup si apre solo dentro un click.
Il click deve avvenire su un dominio in *Allowed domains* — cioe' sull'hub —
quindi serviva una pagina dell'hub con un bottone. Il click nel CRM non si puo'
prestare a una finestra diversa.

La strada che lo toglie e' **non usare un popup per Facebook**: una navigazione
di primo livello non ha bisogno di nessun permesso.

```
CRM: click su Connetti
  → la tab va su hub/whatsapp-connect?state=…&go=1
      → la pagina hub NON si disegna: redirect immediato a
        facebook.com/v23.0/dialog/oauth?config_id=…&redirect_uri=…&extras=…
          → tutto il flusso, nella stessa tab
            → Facebook torna su hub/whatsapp-connect?code=…&state=…
              → la pagina chiude il collegamento e riporta al CRM
```

Una finestra dalla prima schermata all'ultima.

Per chi guarda: preme Connetti, si apre una finestra di Facebook. Nessuna
schermata intermedia, e nessun popup di Facebook da far sopravvivere ai
blocchi — la finestra e' la nostra, aperta dal click, e dentro ci va un
redirect.

`go=1` e' quello che dice alla pagina di essere un passaggio e non una
schermata. Senza, la pagina col bottone c'e' ancora: serve a chi arriva da un
link vecchio, e come ripiego se la configurazione manca.

### Cosa e' documentato e cosa no

**Documentato.** Il `config_id` su un dialog costruito a mano lo dice *Facebook
Login for Business*: «Build a manual login flow […] include your configuration
ID as an optional parameter». E lo `state` torna indietro intatto, dice
*Manually Build a Login Flow*: «This parameter […] will be passed back to you,
unchanged, in your redirect URI». Lo usiamo, con sessionStorage come secondo
appoggio.

**Non documentato: `extras`.** Con l'SDK JavaScript Coexistence si chiede con
`extras.featureType = whatsapp_business_app_onboarding`. Su un dialog costruito
a mano `extras` non e' documentato da nessuna parte. Lo mandiamo come parametro
di query, nella stessa forma che usa la pagina di onboarding ospitata da Meta —
ma **se Meta lo ignora, il flusso ricade sull'onboarding Cloud API normale**, e
il cliente finisce su un numero nuovo invece che sul suo.

### Quindi la verifica e' a valle, non a monte

Coexistence si decide dentro il flusso di Meta, dove non possiamo guardare. Ma
Meta la dice dopo, e la *Onboard WhatsApp Business app users* spiega come:

> If `is_on_biz_app` is true and `platform_type` is `CLOUD_API`, the business
> phone number is able to use Cloud API and the WhatsApp Business app.

`check_coexistence` legge quei due campi appena il numero e' collegato. Se
`is_on_biz_app` non e' vero, il collegamento resta valido — e' un numero Cloud
API funzionante — ma finisce scritto nell'error log e nel log di sessione con
il motivo per cui e' un problema: *l'app WhatsApp Business del cliente NON e'
collegata, e lo storico delle chat non arrivera'*.

Un esito diverso non e' un guasto da annullare. La cosa che non deve essere e'
silenziosa.

## Raccogliere l'errore, e il conflitto con l'unico click

Meta dice cosa non ha funzionato esattamente una volta, e in due forme diverse:

| Dove | Come |
|---|---|
| Mentre il flusso gira | messaggio `WA_EMBEDDED_SIGNUP` con `error_message`, `error_id`, `session_id`, `current_step` |
| Quando restituisce il browser | query string OAuth con `error`, `error_code`, `error_reason`, `error_description` |

I nomi cambiano, il significato no. Adesso finiscono negli stessi campi di
`WhatsApp Signup Session` — `error_message`, `error_code`, `error_id`,
`session_id` — invece che dentro `details`, che era un blob JSON da aprire a
mano nel Desk. `error_id` e `session_id` sono i due valori che Meta chiede
quando si apre un ticket di assistenza: sono il motivo per cui meritano un
campo e non una riga in un JSON.

E Settings → WhatsApp mostra gli ultimi tentativi, con il messaggio in chiaro.
Solo sull'hub: l'onboarding di un cliente viene registrato dove sta la pagina,
non dove sta il suo CRM, e un site cliente lo dice invece di mostrare una lista
vuota come se non fosse successo niente.

### Il conflitto, e come l'ho risolto male prima di risolverlo bene

Il primo dei due canali — quello che dice davvero qualcosa — esiste **solo
finche' la nostra pagina e' aperta ad ascoltare**. Un redirect secco la butta
via: da quel momento facebook.com parla e non c'e' nessuno.

Il primo tentativo e' stato tenere tutt'e due: il CRM apriva un popup con la
nostra pagina dentro, e quella pagina chiamava `FB.login` per restare viva ad
ascoltare. Sulla carta: un click, e il log quando il browser lo concede.

Nella pratica era un pasticcio, e si vedeva. `FB.login` apre **un secondo
popup**, e un popup si apre solo dentro un click — nessuno aveva cliccato *li'*,
quindi il browser lo bloccava quasi sempre e si finiva col redirect un attimo
dopo. Quello che la persona vedeva era una finestra che apre una finestra e poi
se ne va da un'altra parte: costo visibile e ricorrente, beneficio quasi mai.

**Adesso: una tab sola, una navigazione sola.** Il CRM porta la tab sulla
pagina hub, la pagina hub va su Facebook, Facebook torna indietro, e la pagina
riporta al CRM. Nessun popup in nessun punto, quindi nessun blocco da
sopravvivere.

Cosa si perde: i messaggi in corso di flusso. Cosa resta: i rifiuti che Meta
mette nella query string al ritorno, che vengono registrati come prima. E la
pagina col bottone **Start** e' ancora li' — si raggiunge togliendo `go`
dall'URL — e quella, essendo un click vero, apre il popup e ascolta tutto.
Quando serve capire un errore a meta' flusso, e' quella la strada, usata
apposta invece che subita ogni volta.

## L'errore 1690130: «non e' un ID business valido»

Il payload, preso dal canale di sopra:

```json
{ "type": "WA_EMBEDDED_SIGNUP", "event": "ERROR",
  "data": { "error_code": 1690130,
            "error_message": "1270213918015409 non e' un ID business valido",
            "session_id": "01a0c8a7-…", "timestamp": "1790072801680" } }
```

`1690130` non e' nelle tabelle di errore di Embedded Signup, ne' in quelle di
WhatsApp. Sta nella famiglia `1690xxx`, che e' documentata in un posto solo:
**Business Owned Businesses**, cioe' `POST /{business_id}/owned_businesses` e
`client_businesses` — le chiamate con cui un *aggregator business* crea o
collega un **client business**. Le vicine dicono di che materia si tratta:

| Codice | Messaggio |
|---|---|
| 1690165 | This aggregator business already has an existing **client business associated with this user** |
| 1690192 | App is not owned or shared by a business: App must exist and be owned or shared to aggregator business **to create client businesses** |
| 1690138 | To create a business using a primary page, you must be an admin of that page |
| 1690232 | Businesses Do Not Have Primary Pages |

Ed e' esattamente quello che Embedded Signup fa quando il cliente scegli il suo
portfolio: il **nostro** business (l'aggregator) crea o collega il **suo**
business come client.

### Perche' essere admin non aiuta

Il permesso non e' il problema. Il problema e' *di chi e'* il portfolio.
Embedded Signup e' fatto per attaccare il portfolio di **un cliente** al nostro;
se il portfolio scelto e' il nostro — quello che possiede l'app — il
collegamento non ha senso e Meta rifiuta l'id. Essere admin di se stessi non
cambia niente: non si puo' essere clienti di se stessi.

Da qui il consiglio della documentazione, che a rileggerlo dice proprio questo:

> You can test the Embedded Signup flow using your own Facebook account, but
> this can result in additional business portfolios, WABAs, and business phone
> numbers. If you don't want to clutter your Facebook account with test data,
> you can **claim a sandbox test account** instead, and use it to simulate a
> business customer completing the flow.

### E una seconda causa, documentata come limite assoluto

Dalla pagina *Embedded Signup → Limitations*:

> **Existing WhatsApp Business Accounts (WABAs) that were originally created via
> the developer app cannot be selected or onboarded directly through the
> Embedded Signup flow.**

Se il WABA che compare nella schermata di conferma e' quello nato dall'app di
sviluppo — cioe' quello del numero di test che Meta presta — non e'
selezionabile da Embedded Signup, per progetto. Non e' una configurazione da
sistemare.

### Cosa dice internet: niente

Cercato (22/09): `1690130` **non e' documentato da nessuna parte**. Non e' nelle
tabelle di errore di Embedded Signup, non e' in quelle di WhatsApp, e nessuna
delle guide dei vendor che elencano gli errori del flusso — MSG91, Wati, Qiscus,
360dialog — lo cita. Le loro liste coprono il portfolio ristretto, la
verifica business mancante, il numero gia' registrato: non questo.

Una cosa utile c'e', dalla documentazione di 360dialog:

> The Embedded Signup uses Facebook Login, so **only the owner or administrator
> of the Business Portfolio can start and complete the flow**. Third-party
> providers are not allowed to navigate the Embedded Signup on behalf of the
> business.

Dice che il flusso lo deve fare il proprietario del portfolio, non il fornitore
al suo posto. Non dice che il fornitore non possa collegare il **proprio**
portfolio — quindi l'ipotesi «non si puo' essere clienti di se stessi» resta
un'ipotesi, dedotta dalla famiglia del codice, non una cosa scritta.

### Quindi: cosa e' certo e cosa no

| | |
|---|---|
| **Certo** | `1690xxx` e' documentato solo sotto *Business Owned Businesses*: riguarda il passo del portfolio, non WhatsApp |
| **Certo** | «WABAs originally created via the developer app **cannot be selected or onboarded** directly through the Embedded Signup flow» — limite assoluto, e combacia con un WABA nato dal numero di test |
| **Ipotesi** | che `1690130` significhi proprio «questo portfolio e' il tuo» |
| **Ignoto** | il significato esatto del codice: nessuno lo pubblica |

### Come si distingue

Un **sandbox test account** risponde a tutto in un colpo: e' un portfolio che
non e' il nostro e un WABA che non nasce dall'app di sviluppo. Se con quello il
flusso arriva in fondo, la causa era una di quelle e non c'e' niente da
correggere nel codice. Se fallisce anche li', allora e' altro — e il log adesso
ha `error_code`, `error_id`, `session_id` e `timestamp`, cioe' esattamente quello
che Meta chiede per aprire un ticket, che a quel punto e' la strada giusta.

### E il codice lo dice sullo schermo

`hint_for()` tiene quello che abbiamo ricostruito, indicizzato per famiglia di
codice, e la schermata lo scrive sotto il messaggio di Meta. **Etichettato come
pista, non come verdetto**: e' ricostruito da noi, non pubblicato da Meta, e
scriverlo come se fosse documentato sarebbe peggio che non scriverlo. Ma
l'alternativa era un numero sullo schermo e un pomeriggio di ricerche che
finisce dove e' finito il nostro.

## Il sandbox account: come si prende, e cosa prova davvero

Un sandbox account e' un finto cliente: un portfolio business che **non e' il
nostro** e un WABA che **non nasce dall'app di sviluppo**. E' la prova decisiva
per `1690130`, perche' toglie di mezzo entrambe le cause documentate in un colpo.

### Come si prende

La documentazione lo dice in due posti, con parole diverse — la dashboard e'
cambiata, quindi vale quello dei due che si trova:

**Percorso breve** (*Embedded Signup → Claiming sandbox accounts*):

1. App Dashboard → **WhatsApp** → pannello **Quickstart**
2. sezione **Testing Integrations**
3. bottone **Claim sandbox account**

**Percorso lungo** (*Using a Sandbox Account*, piu' recente):

1. App Dashboard → l'app → **Use cases** (icona matita)
2. sotto *Connect with customers through WhatsApp* → **Customize**
3. menu di sinistra → **Partner tools**
4. sezione *Claim a sandbox account* → scegli le **Features** → **Claim
   sandbox account**

Poi, dentro il flusso di Embedded Signup:

- alla schermata **Business portfolio** scegli **Sandbox Business**
- alla schermata del profilo WhatsApp scegli **Test Number**

### I vincoli, che sono parecchi

| | |
|---|---|
| Dura **30 giorni**, poi si disattiva e va richiesto di nuovo |
| Non si possono creare altri portfolio/WABA/numeri sandbox: gli asset sono generati da Meta e compaiono nel flusso |
| **E' legato all'admin dell'app**: perche' gli asset sandbox compaiano nel flusso, l'admin dell'app deve essere loggato nel suo account sviluppatore Meta |
| Il portfolio sandbox **non compare** in Meta Business Suite ne' in WhatsApp Manager |
| Il token si scambia e il WABA ID si legge, ma **il numero non puo' inviare ne' ricevere messaggi** |
| La pagina del Calling scrive «Sandbox accounts are only available to **Tech Partners**» — se il bottone non c'e', e' li' che guardare |

### Cosa prova, e cosa no

**Prova**: che il passo del portfolio passa con un portfolio che non e' il
nostro, e che la nostra catena di onboarding gira fino in fondo — scambio del
codice, claim della rotta, iscrizione al WABA, consegna al site.

**Non prova**: Coexistence. Il sandbox da' un *Test Number*, non un numero che
sta davvero su un telefono con WhatsApp Business installato, quindi la
schermata «collega il tuo account esistente» non ha niente da collegare. E non
prova la messaggistica, perche' quel numero non invia.

Quindi: se il flusso col sandbox arriva in fondo, `1690130` era una delle due
cause documentate e **nel codice non c'e' niente da correggere**. Se fallisce
anche col sandbox, allora e' altro — e a quel punto il log ha `error_code`,
`error_id`, `session_id` e `timestamp`, cioe' esattamente i quattro valori che
Meta chiede per aprire un ticket.

## `3441038`: «Non disponi delle autorizzazioni per questa risorsa»

Compare alla schermata **Aggiungi il tuo numero di telefono WhatsApp**, dopo
che il passo del portfolio e' andato a buon fine.

Cercato (22/09): **non e' documentato**, come `1690130`. Ne' nelle tabelle di
Embedded Signup, ne' in quelle di WhatsApp, ne' nelle guide dei vendor.

Ma il testo dice una cosa che vale la pena leggere con attenzione: parla di
**una risorsa**, e non dice quale. La risorsa che si sta compilando in quel
momento e' il numero — ed e' il posto sbagliato dove guardare. Un numero non e'
ancora una risorsa di nessuno: lo diventa quando viene creato **dentro** un
WhatsApp Business Account, che sta **dentro** un portfolio. E' li' che un
diritto puo' mancare.

Meta la stessa cosa la dice in chiaro altrove, nella tabella degli errori di
Embedded Signup:

> **User does not have permission to create WhatsApp Business Accounts.** You do
> not have the Admin level permission needed to create WhatsApp Business
> Accounts under the Business Account you selected. *Suggested Solution: Get
> Admin access to the Business Account to proceed or select an account you have
> Admin permissions for.*

E c'e' un motivo strutturale per cui questa configurazione lo pretende: e' una
configurazione **System-user access token**, e la documentazione di Facebook
Login for Business dice che con quel tipo «your app users will be required to
log in using a business portfolio», e che «**any admin** in your business
client's admin group can grant your app a system user access token». Admin,
non membro.

Quindi la cosa da controllare non e' il numero: e' **di quale portfolio si e'
Admin**, e se quello scelto allo schermo prima e' proprio quello.

Nota: questo errore arriva **dopo** `1690130`, non al suo posto. Il passo del
portfolio ora passa; e' il passo dopo che si ferma. E' un avanzamento, non uno
scambio.

## Staccare il collegamento dal telefono, e perche' il QR non ritorna

### Come si stacca

Dalla documentazione di *Onboard WhatsApp Business app users*:

> You cannot use the Deregister API to deregister a business phone number from
> Cloud API if it is already in use with both Cloud API and the WhatsApp
> Business app. Instead, your clients can use the WhatsApp Business app to
> disconnect from Cloud API by navigating to **Settings > Account > Business
> Platform** and clicking the **Disconnect Account** button.

Quindi: **non da API, dal telefono.** WhatsApp Business → Impostazioni →
Account → Business Platform → *Disconnetti account*. L'API non serve e non
funzionerebbe: un numero in Coexistence non si deregistra da fuori.

### Perche' il QR non ricompare

Perche' dal punto di vista di Meta quel numero **e' gia' collegato**. La
schermata «collega il tuo account esistente» offre di collegare qualcosa che
risulta gia' collegato, quindi non ha niente da offrire.

E c'e' una finestra che spiega come ci si arriva a meta':

> when a business completes the flow and you onboard the customer, you have
> **24 hours to synchronize their messaging history, otherwise they must be
> offboarded and they must complete the flow again**.

Il primo tentativo era arrivato fino al QR: il numero ha preso il suo companion
Cloud API. Il resto del flusso e' fallito subito dopo, quindi la
sincronizzazione non e' mai partita. Risultato: mezzo collegato — abbastanza
perche' Coexistence non si rioffra, non abbastanza perche' funzioni.

Staccare dal telefono riporta il numero allo stato di partenza, e il QR torna.

### Adesso il CRM se ne accorge

Quando il collegamento viene staccato, Meta manda un `account_update` con
`PARTNER_REMOVED` — e, se e' stato il sistema a staccarlo, anche un
`disconnection_info` con il motivo e chi l'ha fatto. Il gestore c'era e scriveva
una riga di log che non legge nessuno.

Ora ogni notifica di questo tipo diventa una riga in `WhatsApp Signup Session`,
accanto ai tentativi di collegamento, intestata al site del cliente giusto:

| Evento | Come viene letto |
|---|---|
| `PARTNER_ADDED`, `PARTNER_APP_INSTALLED` | collegato |
| `PARTNER_REMOVED`, `PARTNER_APP_UNINSTALLED` | **scollegato**, col motivo e chi l'ha fatto |
| `ACCOUNT_OFFBOARDED` | telefono cambiato o rinregistrato: Meta lo ricollega da solo in pochi minuti, invio sospeso nel frattempo |
| `ACCOUNT_RECONNECTED` | ricollegato |
| qualunque altro | scritto comunque — un evento che non abbiamo mai visto e' esattamente quello per cui serve una riga |

`ACCOUNT_OFFBOARDED` non e' un guasto e non viene segnato come tale: e' quello
che succede ogni volta che un cliente cambia telefono. Ma qualche messaggio
fallisce mentre dura, e senza la riga si va a caccia della ragione sbagliata.

## Il click torna, perche' senza non c'e' Coexistence (22/09, sera)

Il sintomo: la schermata che compare non e' piu' «collega il tuo account
WhatsApp Business esistente», ma **«Aggiungi il tuo numero di telefono
WhatsApp — inserisci un nuovo numero»**. Cioe' il flusso Cloud API normale.

E' la verifica che la documentazione stessa indica:

> To verify that you have enabled the feature correctly, access your
> implementation of Embedded Signup. **If the WABA selection screen has been
> replaced with a screen that gives you the option to connect your existing
> WhatsApp Business Account, the feature is enabled.**

Non e' stata sostituita. Quindi Coexistence **non e' attiva**, e il motivo era
scritto qui sopra da due giorni, nella riga che diceva cosa non era verificato:
`extras` e' documentato per `FB.login`, **non** per un dialog costruito a mano.
Meta lo ignora li'. Togliendo il click per aprire Facebook direttamente ho
tolto `FB.login`, e con lui l'unico posto dove `featureType` viene letto.

Da qui tutto il resto, in fila:

1. niente Coexistence → il flusso offre di aggiungere un numero **nuovo**;
2. il numero che si prova a mettere e' quello che sta gia' su un telefono con
   WhatsApp Business — e questo e' il caso che la documentazione chiama
   esplicitamente fuori: «Business phone numbers already in use with the
   WhatsApp Business app are supported, **but require you customize the flow to
   enable WhatsApp Business app user onboarding**»;
3. il QR non compare piu', perche' il QR e' un passo di Coexistence;
4. e il primo tentativo, quello che il QR l'aveva mostrato, girava ancora con
   `FB.login`.

**Quindi il click resta.** Non e' una schermata che abbiamo scelto di mettere:
e' il browser che pretende un gesto prima di aprire una finestra, e la finestra
di Facebook e' l'unico posto dove Coexistence esiste. Con `go` la pagina si
riduce al minimo — una riga e un bottone, gia' a fuoco — ma il bottone c'e'.

Il link diretto al dialog resta, sotto *«Il bottone non fa niente?»*, con
scritto cosa fa davvero: apre Facebook senza l'SDK, quindi **offre un numero
nuovo invece di quello sul telefono**. E' un ripiego per un browser che non
carica l'SDK, non una seconda strada equivalente.

### La lezione, che vale piu' del bug

L'unica parte non verificata di quel cambiamento era scritta nella sua PR, e la
verifica da fare era descritta in una riga. Nessuno l'ha eseguita, e il costo
non e' stato un errore: e' stato **un errore che sembrava un altro errore**.
`3441038` ha mandato a cercare permessi e portfolio per un giorno, quando la
causa era due passi prima.

## La schermata del numero: cosa scegliere, e cosa non scegliere

La schermata di Meta offre tre cose, e solo una porta a Coexistence:

```
Inserisci un nuovo numero di telefono          ← QUESTA
Usa un nome visualizzato con un numero virtuale
[elenco dei numeri gia' nei portfolio a cui hai accesso]
```

Dalla documentazione di *Version 4 Public Preview*, flusso Coexistence:

> Phone number entry screen: This screen lets the business customer enter the
> phone number they want to onboard. **To trigger the Coexistence flow, the
> customer must enter a WhatsApp Business app phone number.**

> The Coexistence flow is **automatically triggered when the business customer
> enters a phone number that is already in use with the WhatsApp Business app.**

Quindi il numero **si scrive**, non si sceglie dall'elenco. L'elenco contiene i
numeri gia' registrati nei portfolio: sono numeri Cloud API, non numeri che
stanno su un telefono. Sceglierne uno di li' e' l'altro flusso.

### Perche' alcuni sono «Non idoneo»

Il **numero di test** (`+1 555-…`) e' permanentemente non idoneo, ed e'
documentato due volte: «Existing WABAs that were originally created via the
developer app cannot be selected or onboarded directly through the Embedded
Signup flow», e i numeri 555 «cannot be migrated to another WhatsApp Business
Account, or used outside of the WhatsApp Business platform». Non c'e' niente da
sistemare: non sara' mai selezionabile li'.

### WhatsApp Business, non WhatsApp

Coexistence riguarda **l'app WhatsApp Business**, versione 2.24.17 o superiore.
Un numero con il WhatsApp normale non e' un caso di Coexistence, ed e' anche il
caso peggiore:

> Registered numbers can still be used for everyday purposes… but **cannot be
> used with WhatsApp Messenger**. **Numbers already in use with WhatsApp cannot
> be registered unless they are deleted first.**

Cioe': col WhatsApp normale non si puo' ne' fare Coexistence ne' registrare il
numero — a meno di cancellare prima l'account WhatsApp, che e' una cosa che a un
cliente non si chiede.

Percio' la prima domanda davanti a un collegamento che non parte non e' quale
portfolio o quale permesso: e' **quale app c'e' su quel telefono**.