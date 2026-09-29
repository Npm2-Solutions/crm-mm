# Il CRM sul telefono

**Stato:** ✅ fatto (29/09/2026)

## Il problema

Il CRM aveva già una forma da telefono: la barra in basso (Persone, Trattative,
Chat, Attività, Altro), le schede mobili di lead, trattativa, contatto e
azienda, le liste a righe, le impostazioni come elenco che porta a una pagina.
Ma nessuno l'aveva mai passato schermata per schermata con un telefono in mano,
ed è lì che vengono fuori le cose che su un monitor non si vedono:

- **Cose che esistono solo al passaggio del mouse.** Su un telefono il mouse
  non c'è: le azioni su un messaggio (rispondere citandolo, reagire), il menu
  delle colonne del kanban e il «+» fra i passi di un'automazione non
  comparivano mai.
- **Titoli ad altezza fissa.** In quasi quaranta pagine delle impostazioni il
  titolo era alto 20px per costruzione: quando andava a capo («Issuing
  company», «Rooms & Equipment», «Online booking») la seconda riga finiva sopra
  la descrizione.
- **Pulsanti che schiacciano il testo.** Titolo e descrizione a sinistra,
  pulsanti a destra: a 390px la descrizione restava in una colonna di una
  parola per riga, e con due pulsanti («Online booking», «New service») il
  secondo usciva dallo schermo.
- **Righe che spingono fuori il controllo.** Un titolo che non va a capo
  spingeva l'interruttore accanto oltre il bordo: in General tre interruttori
  su sei non si vedevano o se ne vedeva metà, in Dashboard la valuta era
  tagliata, nella lista utenti il ruolo e il suo menu.
- **Una finestra da desktop.** Le impostazioni si aprivano in una finestra con
  i margini di un monitor — 16px ai lati, 48 sopra — alta 32px più dello
  schermo: l'ultima riga di ogni pagina restava sotto il bordo, e restavano
  294px di testo su 390.
- **Moduli lunghi.** Nuovo lead, nuova trattativa, nuovo contatto: il pulsante
  Crea compariva solo in fondo, dopo tutti i campi.
- **Controlli da mouse.** Interruttori alti 16px, il menu di una nota 20px, la
  casella di selezione di una riga 14px: un pollice li manca, o tocca la riga
  e apre la scheda.
- **Griglie da desktop.** Le intestazioni della tabella delle pipeline scritte
  una sopra l'altra, le tabelle figlie con colonne di due lettere, tre e
  quattro campi per riga nei dialoghi delle impostazioni, le schede delle
  piattaforme di prenotazione coi badge sopra i nomi.
- **Il calendario** aveva i filtri su tre righe sopra ogni giorno, e li teneva
  anche con un appuntamento aperto.
- **La dashboard** tagliava i titoli dei numeri («Waiting for an ans…») e i
  confronti («vs $14,1…»).
- **Il kanban** aveva colonne larghe 288px che scorrevano senza fermarsi su una.
- **Le schede delle attività** tagliavano la descrizione a metà parola.
- **La scheda Eventi** di lead e trattativa, con gli appuntamenti della
  persona, sul telefono non c'era.

Strada facendo sono venute fuori anche tre cose che non erano del telefono:
la pagina delle regole di prenotazione chiedeva il catalogo con un POST a un
metodo che accetta solo GET (e il costruttore di link restava vuoto); la
pagina Meta, senza un'app configurata, andava in errore a ogni apertura; il
selettore della persona nel pannello appuntamento, dopo la scelta, mostrava
l'id del record («CRM-LEAD-2026-00055») invece del nome.

## Come l'abbiamo guardato

Playwright, con un telefono simulato il più vicino possibile al vero: iPhone,
390×844 e 360×780, tocco, densità 2, tema chiaro e scuro. Quattro giri, ognuno
con delle misure, non solo con gli screenshot:

1. **Ogni pagina** (38): cosa esce di lato dallo schermo, i bersagli sotto i
   24px (e sotto i 32), il testo tagliato senza puntini.
2. **Ogni cosa che si apre** (48 fra dialoghi, menu, selettori e pannelli):
   se resta dentro lo schermo.
3. **Ogni sezione delle impostazioni** (42) e i dialoghi dentro di esse (37):
   cosa esce dalla finestra.
4. **Le cose che si fanno davvero, col dito**: una nota su un lead, un lead
   nuovo, un appuntamento, una risposta in chat, lo stato di un'attività, lo
   stadio di una trattativa, un interruttore nelle impostazioni, due righe
   selezionate in una lista. Tocchi veri (`tap`), non clic; e per il lead
   nuovo il controllo che Crea sia sullo schermo senza scorrere.

Una misura dice dove guardare, non se va bene: ogni segnalazione è stata
guardata sullo screenshot. I link nel testo sotto i 24px sono ammessi (le
linee guida li esentano), e così un campo dentro un riquadro che lo apre.

## Cosa cambia

| Cosa | Prima | Adesso |
|---|---|---|
| Azioni sui messaggi | Solo al passaggio del mouse | Un tocco sul messaggio le mostra (il messaggio prende il focus) |
| Menu delle colonne del kanban, «+» fra i passi di un'automazione | Invisibili al tocco | Sempre visibili su uno schermo senza mouse |
| Colonne del kanban | 288px, scorrimento libero | 85% dello schermo, si fermano una alla volta |
| Scheda Eventi di lead e trattativa | Mancava | C'è, dopo Dati |
| Impostazioni | Finestra con margini, 32px più alta dello schermo | Tutto lo schermo, con le aree sicure dei telefoni con la tacca |
| Titoli delle pagine delle impostazioni | Alti 20px, la seconda riga sopra la descrizione | Vanno a capo; i pulsanti sotto la descrizione |
| Margini delle pagine delle impostazioni | 32px per lato | 20px |
| Righe con un controllo | Il testo non va a capo e spinge fuori il controllo | Il testo cede, il controllo resta; se non ci stanno, il controllo va sotto |
| Utenti, pipeline, piattaforme di prenotazione | Colonne sovrapposte o tagliate | Il nome cede, il resto va sotto o prende la larghezza che gli serve |
| Tabelle figlie (Home Actions e ogni tabella nei moduli) | Colonne fino a due lettere | Ogni colonna ha una larghezza minima, la tabella scorre di lato |
| Campi a tre o quattro per riga nei dialoghi | 100px l'uno | Uno per riga (due, se erano quattro) |
| Nuovo lead, trattativa, contatto, evento, e ogni dialogo con dei pulsanti | Crea in fondo al modulo, sotto il bordo dello schermo | La riga dei pulsanti resta in fondo allo schermo mentre il modulo scorre |
| Interruttori, menu delle note, pulsanti piccoli | 16–20px | Un anello invisibile li porta a 36px al tocco, senza cambiare aspetto |
| Casella di selezione delle righe | 22px, a metà della riga | Tutta l'altezza della riga, dal bordo dello schermo |
| Calendario | Filtri su tre righe, anche col pannello aperto | Una riga che scorre di lato; col pannello aperto si fanno da parte |
| Dashboard | Titoli e confronti tagliati | Titolo su due righe, il confronto sotto la variazione |
| Descrizione nelle schede delle attività | Tagliata a metà parola | Due righe e i puntini |
| Data e ora nei moduli | «2026-09-26 00:00:00» | «2026-09-26 00:00»: al minuto |
| Persona nel pannello appuntamento | L'id del record | Il nome, con la × per sceglierne un'altra |
| Nota inviata | «Comment sent» sotto «Write a note for the team» | «Note added» |
| Menu «New» della persona | «Comment», due righe sopra «Note» (un'altra cosa) | «Internal note» |

## I numeri

Stesso telefono, stesse pagine, prima e dopo (390px, tema chiaro). Sono i
controlli che le misure sanno contare; i titoli sulla descrizione e i
pulsanti che schiacciavano il testo si sono visti sugli screenshot, pagina per
pagina.

| | Prima | Dopo |
|---|---|---|
| Pagine con controlli sotto i 24px (fuori dalle impostazioni) | 12 su 38 | 0 |
| Sezioni delle impostazioni con controlli sotto i 24px | 12 su 42 (37 controlli) | 0 |
| Dialoghi delle impostazioni con qualcosa fuori dalla finestra | 1 (le piattaforme) | 0 |
| Sezioni delle impostazioni con errori in console | 3 | 1 (Telephony, vedi sotto) |
| Percorsi col dito completati | — | 8 su 8 |

A 360px e in tema scuro, le 38 pagine, le 42 sezioni delle impostazioni, i
37 dialoghi delle impostazioni e le 48 cose che si aprono non danno nessuna
segnalazione oltre al nuovo lead e al nuovo evento, più alti dello schermo per
forza di cose: scorrono, e i pulsanti restano in fondo.
Non contano come segnalazioni le parti di una select di frappe-ui (si apre
toccando il riquadro intero) e le caselle con la loro etichetta accanto
(si tocca l'etichetta).

## Le regole per le prossime schermate

- **Niente solo al passaggio del mouse.** Quello che compare al passaggio deve
  comparire anche al tocco: `[@media(hover:none)]:opacity-100`, oppure il
  focus (`group-focus-within`) con l'elemento focalizzabile (`tabindex="-1"`).
- **`max-md:` per quello che cambia sul telefono.** È la stessa soglia (768px)
  di `isMobileView`, che decide quali componenti si montano: `sm:` (640px)
  lascerebbe fra 640 e 768 il layout sbagliato.
- **Un titolo non ha altezza fissa**: `leading-tight md:h-5 md:leading-none`.
- **Intestazione di pagina**: titolo e descrizione, poi le azioni sotto, sul
  telefono (`max-md:flex-col max-md:items-start max-md:gap-3`).
- **In una riga il testo cede, il controllo no**: `min-w-0` sulle parole,
  `shrink-0` sul controllo, e una descrizione va a capo, non si tronca.
  `SettingsRow` manda il controllo sotto quando i due non ci stanno.
- **Controlli piccoli**: `.touch-target` (un anello invisibile, solo sugli
  schermi al tocco); gli interruttori di frappe-ui l'hanno già.
- **Dialoghi lunghi**: `.dialog-footer` sulla riga dei pulsanti; quella delle
  azioni di frappe-ui (`#actions`) lo è già.
- **Griglie di campi**: tre o quattro per riga diventano una (due) sul
  telefono.
- **Tabelle**: una larghezza minima per colonna e lo scorrimento di lato, non
  colonne schiacciate a niente.

## File

| File | Cosa cambia |
|---|---|
| `frontend/src/index.css` | `.touch-target`, gli anelli degli interruttori, le impostazioni a tutto schermo, `.dialog-footer` e la riga delle azioni di frappe-ui |
| `frontend/src/components/Settings/**` | Intestazioni, margini, righe, griglie, schede di connessione: il telefono in ogni pagina |
| `frontend/src/components/Settings/Settings.vue` | Tutto lo schermo |
| `frontend/src/components/Settings/SettingsRow.vue`, `Telephony/SettingRow.vue` | Il controllo va sotto quando non ci sta |
| `frontend/src/components/Controls/Grid.vue` | Colonne con una larghezza minima e scorrimento di lato |
| `frontend/src/components/Modals/*Modal.vue`, `FieldLayoutDialog.vue` | `.dialog-footer` |
| `frontend/src/components/Activities/WhatsAppArea.vue`, `ChatBubble.vue` | Azioni al tocco |
| `frontend/src/components/Kanban/KanbanView.vue` | Colonne e menu al tocco |
| `frontend/src/pages/MobileLead.vue`, `MobileDeal.vue` | La scheda Eventi |
| `frontend/src/pages/Calendar.vue`, `components/Calendar/AppointmentPanel.vue`, `Attendee.vue` | Filtri in una riga, la persona per nome, campi che si toccano in tutta la loro altezza |
| `frontend/src/components/Dashboard/*` | Titoli e confronti dei numeri |
| `frontend/src/components/ListViews/MobileListRows.vue` | La casella di selezione dal bordo dello schermo |
| `frontend/src/utils/index.js` | `datetimeFormat()`: data e ora al minuto |
| `crm/integrations/meta/api.py` | Il controllo del webhook senza un'app, testato in `crm/tests/test_meta_webhook_check.py` |

## Non incluso

- **Il builder della dashboard** resta da desktop: una griglia da trascinare
  su un telefono non si usa. Sul telefono le dashboard si guardano.
- **Il 404 della pagina Telephony** per chi non ha ancora un agente: è come la
  pagina sa che l'agente va creato. frappe-ui rilancia l'errore di ogni
  richiesta partita da sola, e la console lo mostra, ma chi usa la pagina non
  vede niente.
