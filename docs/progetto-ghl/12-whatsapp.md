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
