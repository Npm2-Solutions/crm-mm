# 40 — L'italiano dappertutto

> 🔄 **IN CORSO (01/10/2026)**. DottorCloud parla italiano, ma metà delle schermate
> dicevano ancora inglese: le frasi nuove senza traduzione, quelle ereditate rimaste
> vuote, le parole che frappe-ui scrive da sé ("Load More", "Sun 27", "All day"),
> gli stati delle liste mostrati come sono salvati ("Todo", "High"), l'ora con am/pm.
> Il lavoro va per PR: prima le pagine di ogni giorno, poi le impostazioni, poi il
> resto e le parole del server, infine le traduzioni ereditate rimesse nella voce
> del prodotto.

## Fatto: le pagine di ogni giorno (PR 1)

Oggi, la dashboard, l'agenda, la lista d'attesa, le persone e la loro scheda, le
conversazioni, le cose da fare, le fatture; l'area clienti.

- **Le frasi**: le pagine e i loro componenti, la dashboard del server (titoli,
  descrizioni, libreria), le frasi trovate a runtime (sotto).
- **I valori delle liste**: una colonna a scelta (stato, priorità) passa dal
  traduttore come i collegamenti ai tipi tradotti; anche le colonne del Kanban. "Da
  fare · In sospeso · In corso · Fatto", "Alta · Media · Bassa".
- **I dati di partenza**: le fasi della pipeline predefinita, gli stati di una
  persona, le sorgenti, i motivi di una trattativa persa, i settori. Sono nomi
  tradotti (`translated_doctype`): quelli di partenza si leggono in italiano, quelli
  che il centro rinomina restano come li ha scritti. La dashboard li traduce anche
  nell'imbuto e nelle liste.
- **L'ora a 24 ore**: Frappe la conosce solo così (le impostazioni offrono
  `HH:mm:ss` e `HH:mm`), il frontend scriveva "02:30 pm" nelle cose da fare, negli
  eventi e nelle notifiche. Ora "14:30", e il giorno prima del mese: "gio 1 ott
  2026, 14:30".
- **frappe-ui nella lingua dell'utente** (`frontend/vite/frappeUi.js`): alcuni suoi
  componenti scrivono parole inglesi senza un modo per cambiarle. La build le passa
  al traduttore (`__`, lo stesso catalogo): "Carica altri" e "20 di 870" sotto ogni
  lista, "Cerca", "Seleziona tutto" nei campi collegamento, "Oggi" e "Adesso" nei
  calendari delle date, i testi vuoti di select e combobox. Il calendario
  dell'agenda prende mesi e giorni da `Intl` nella lingua del boot ("Set - Ott
  2026", "Lun 28", "Tutto il giorno") e l'ora a 24 ore. Ogni sostituzione deve
  trovare quello che sostituisce: un frappe-ui che cambia quelle righe ferma la
  build e il test (`tests/unit/frappeUi.test.js`), invece di tornare all'inglese
  in silenzio.
- **L'area clienti** ha il suo dizionario (`frontend/src/area/it.js`): mancavano la
  chat con l'assistente, le passkey, gli avvisi. Un test
  (`tests/unit/areaParole.test.js`) legge ogni frase che l'area passa a `__()` e
  vuole trovarla nel dizionario.

## Fatto: le impostazioni (PR 2)

Tutte le 51 pagine delle impostazioni, dal proprio account all'agenzia: le 1654
frasi dei loro componenti e le 81 che arrivano dai dati e dal server (i livelli
degli utenti, i gruppi di alimenti, le parti del corpo degli esercizi, i modelli di
partenza dei moduli, i campi della fatturazione). Il giro nel browser apre ogni
pagina con il suo link diretto (`?settings=<chiave>`).

- La pagina delle stanze si chiama come il listino le conta: "Ambulatori e
  attrezzature" (era "Sale e attrezzature", con "ambulatorio" dentro).
- **Una parola, due posti**: "Hours" è la scheda degli orari di un servizio
  ("Orari") e l'unità di un'attesa nelle automazioni ("Ore"). Quando la stessa
  frase inglese vuole due italiani, il posto meno comune le dà un contesto,
  `__('Hours', null, 'Service editor tab')`, e il catalogo ha la sua voce con
  `msgctxt`: il traduttore cerca prima `frase:contesto`.

## Fatto: il resto dell'app e le parole del server (PR 3)

Le pagine che restavano (automazioni, social, sito, tastierino, offerte, aziende,
contatti, note, chiamate, notifiche) e tutto quello che arriva dal server.

- **Le frasi del server**: messaggi d'errore, email, notifiche, testi delle
  automazioni e della fatturazione elettronica, circa 2600 frasi; le etichette, le
  descrizioni e le opzioni dei DocType; i **nomi dei DocType**, che il framework
  mette nei suoi messaggi ("Non hai il permesso per Appuntamento"). Cinque nomi
  ereditati erano sbagliati: `CRM Lead` e `CRM Deal` erano entrambi "Offerta CRM",
  ora "Persona" e "Trattativa"; `CRM Task` è "Cosa da fare".
- **Le notifiche** incollavano una parola inglese nella frase: "ti ha menzionato
  in lead Mario Rossi". Ora una frase per caso: la persona per nome ("Anna ti ha
  menzionato in un commento su Mario Rossi"), la trattativa come tale ("…sulla
  trattativa Studio Verdi"); WhatsApp, SMS e assegnazioni allo stesso modo, con il
  nome invece del codice della scheda.
- **Quello che il codice rilegge** non è mai la frase tradotta: un annullamento
  arrivato da una piattaforma si riconosce in inglese e nella lingua del sito, il
  collegamento di una notifica alle cose da fare guarda se la cosa è ancora tua.
- **Una parola, due posti** (le voci con `msgctxt`): le viste delle conversazioni
  ("Aperte", "Gestite"), un consenso ("Registra", "Revoca"), la scheda di
  un'automazione, la comunicazione al Sistema TS, la parte del corpo di un
  esercizio ("Schiena"), le schede dell'editor delle automazioni ("Builder" è
  anche il nome di un prodotto).
- **Le parole che non passavano dal traduttore**: i titoli degli stati vuoti, il
  pulsante Salva dei dati, le descrizioni dei campi, il segnaposto del
  responsabile, priorità e stato nelle schede del Kanban, il segnaposto dell'ora di
  frappe-ui. I tipi di consenso e la licenza di una libreria, creati in inglese,
  si leggono nella lingua di chi li guarda; quello che il centro ha scritto resta
  com'è.
- **Le descrizioni dei DocType** non chiamano più il prodotto "the CRM" (22 testi,
  anche in inglese); le dimensioni del piano contano gli ambulatori del listino.
- **Il giro nel browser** guarda anche il testo visibile: le righe con parole solo
  inglesi, per trovare quello che non passa da `__()`.

Resta, per la prossima PR: le pagine di importazione dei dati, che frappe-ui
disegna senza traduttore; i dati delle librerie (gli esercizi di exercises-dataset
e gli alimenti CIQUAL hanno i nomi inglesi); le traduzioni ereditate da rimettere
nella voce del prodotto.

## Come si trovano le frasi in inglese

- **Nel codice**: le chiamate `__('…')` del frontend e `_()`/`_lt()` del server, e le
  etichette dei DocType, confrontate con i cataloghi di DottorCloud e del
  framework (che in produzione è compilato: va compilato anche in locale,
  `bench compile-po-to-mo --app frappe --locale it`).
- **A runtime**: molte parole sono dati (etichette definite in una lista, poi
  tradotte con `__(voce.label)`) e il codice non le mostra. Un giro nel browser in
  italiano registra ogni frase chiesta al traduttore e rimasta senza traduzione:
  `window.translated_messages`, avvolto in un Proxy prima che la pagina parta.
- **Sullo schermo**: quello che non passa dal traduttore (una prop disegnata
  com'è, un'etichetta scritta nel template) il Proxy non lo vede. Lo stesso giro
  legge il testo visibile e i segnaposto e segnala le righe con parole solo
  inglesi.

## La voce e le parole

Come parla DottorCloud, in italiano: valgono per ogni frase nuova.

- Italiano semplice e preciso, come parla una brava segreteria. Frasi brevi,
  nessun burocratese ("effettuare", "si prega di"), nessun punto esclamativo.
- Il **tu**: "Scegli", "Puoi", "Salva"; mai "Lei", mai l'infinito per un'istruzione
  ("Selezionare…" ✗).
- Le **maiuscole all'italiana**: solo la prima parola e i nomi propri
  ("Regole di assegnazione", non "Regole Di Assegnazione").
- I pulsanti sono verbi all'imperativo ("Crea", "Aggiungi un campo"); un errore
  dice cosa non è successo ("Non è stato possibile salvare…"); "Vuoi davvero…?";
  "Regola creata", senza "con successo".
- Segnaposto (`{0}`, `{brand}`), tag HTML e spazi ai bordi restano identici; i
  nomi di prodotti e servizi (WhatsApp, Sistema TS, SDI, PEC…) non si traducono.

| Inglese | Italiano |
|---|---|
| Lead, person | persona, la scheda della persona (con la clinica: paziente) |
| Deal | trattativa (la pagina del menu: "Offerte") |
| Contact, Organization | contatto, azienda |
| Task | cosa da fare (la lista: "Da fare") |
| Call log | chiamata |
| Appointment, event | appuntamento, evento |
| Service, professional | servizio, professionista |
| Room / equipment | ambulatorio, come nel listino ("Ambulatori e attrezzature") / attrezzatura |
| Slot, free time | orario libero; fascia oraria |
| Booking, booking page | prenotazione, pagina di prenotazione |
| Waiting list, cycle, session | lista d'attesa, ciclo di sedute, seduta |
| Subscription, quote, invoice | abbonamento, preventivo, fattura |
| Billing details | dati di fatturazione, anagrafica fiscale |
| Client area / patient area | area clienti / area pazienti |
| Form, template | modulo; modello |
| Owner | responsabile |
| Team | gruppo |
| Agent | operatore |
| Source | origine (le colonne esistenti: "Sorgente") |
| Sent, delivered, read, failed | inviato, consegnato, letto, non riuscito |
| No show, arrived | non venuto, arrivato |
| Won, lost | vinta, persa |
| Consent, signature | consenso, firma |
| Clinical record, report (medical) | cartella clinica, referto |
| Timezone | fuso orario |
| Branch | sede |
| Mobile | cellulare |
| Email | email (l'email) |

## Come è fatto

| File | Cosa fa |
|---|---|
| `crm/locale/it.po` | Il catalogo di DottorCloud: vince su quello del framework |
| `frontend/vite/frappeUi.js` | Le parole di frappe-ui nella lingua dell'utente, alla build |
| `frontend/src/components/ListViews/*ListView.vue`, `Kanban/KanbanView.vue` | I valori a scelta e le colonne del Kanban tradotti |
| `frontend/src/area/it.js` | Il dizionario dell'area clienti |
| `crm/dashboard/widgets/sales.py` | Le fasi tradotte nell'imbuto e nelle liste (`stage_name`) |
| `crm/fcrm/doctype/crm_notification/crm_notification.py` | `in_grassetto`, `nome_di`: le notifiche nominano chi e dove con frasi intere |
