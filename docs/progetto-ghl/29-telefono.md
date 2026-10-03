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

## Seconda parte: schermate fatte per il telefono (03/10/2026)

La prima parte aveva messo a posto le pagine del computer viste su un
telefono. Ma le pagine che si aprono ogni giorno restavano quelle del computer,
rimpicciolite: le persone come righe di una tabella pensata per quindici
colonne, le cose da fare e le trattative come colonne di una lavagna da far
scorrere di lato, l'agenda come una griglia di ore che ne mostra quattro alla
volta e riduce un appuntamento di mezz'ora a una striscia, la scheda di una
persona con quindici schede in una riga da scorrere.

Le app di CRM e di agenda fatte per il telefono (HubSpot, Pipedrive, Google
Calendar, i gestionali delle cliniche) fanno tutte le stesse scelte, e le
abbiamo prese:

- **una riga per cosa**, cercata scrivendo, con l'azione che viene dopo a un
  tocco: si chiama una persona dalla sua riga;
- **l'azione principale in basso a destra**, sopra la barra: «+»;
- **la giornata come elenco**, in ordine di ora, con il segno di «adesso»;
- **poche schede, le altre sotto «Altro»**.

| Pagina | Sul telefono |
|---|---|
| Persone | `ElencoPersone`: si cerca per nome, per email o per numero scritto in qualsiasi modo («+39 340 111 2233», «3401112233», «340-111-2233»: si confrontano le ultime nove cifre). Ogni riga dice chi è, come raggiungerla e quando torna («Oggi 15:30», per chi vede l'agenda). Il telefono è a un tocco. La lista cresce scorrendo, una pagina alla volta. |
| Da fare | `ElencoCose`: Mie o Di tutti, divise per quando scadono (In ritardo, Oggi, Domani, Più avanti, Senza un giorno). Il cerchio la segna fatta, con «Annulla» nell'avviso. |
| Trattative | `TrattativePerFase`: le fasi sono una riga di chip, ciascuna con quante trattative contiene. Le trattative della fase scelta sono schede una sotto l'altra: chi, quanto vale, chi la segue, quando si è mossa. La pagina si apre sulla prima fase aperta che ha trattative. Il «+» mette la nuova trattativa nella pipeline e nella fase che si vedono, mai in una chiusa. |
| Agenda | `AgendaDelGiorno`: il telefono apre sul giorno come elenco. Prima quello che dura tutto il giorno, poi tutto in ordine di ora, con una linea dove cade adesso. Sopra c'è la settimana per saltare a un giorno. La griglia delle ore resta a una scelta (Lista, Giorno, Settimana, Mese) e si apre sullo stesso giorno. «Tutto il giorno» accanto alle ore va su due righe corte. |
| Oggi | I quattro numeri stanno in una riga di riquadri piccoli (`dc-stat-row`): gli appuntamenti cominciano nella prima schermata. |
| Una persona, una trattativa | `SchedeDelTelefono`: le schede di ogni giorno in una barra corta (Attività, Dettagli, Eventi, poi Clinica o Da fare), le altre sotto «Altro», che mostra il nome della scheda aperta quando è una di quelle. Le sei azioni rapide stanno in una riga. |

Il server dà ogni lista in una sola chiamata (`crm/api/sul_telefono.py`), con
gli stessi permessi di tutto il resto: `frappe.get_list` decide chi vede quale
persona, trattativa e cosa da fare, e email e telefono arrivano mascherati a
chi non può leggerli.

Nel giro abbiamo trovato due errori, ora corretti:

- `defaultPipeline`, letto da uno store Pinia senza `storeToRefs`, perdeva la
  reattività: una nuova trattativa non prendeva la pipeline predefinita.
- Una trattativa senza responsabile mostrava il nome di chi la guardava:
  `getUser()` senza un nome restituisce l'utente della sessione.

Le regole per le prossime schermate si allungano:

- **Una lista che si apre ogni giorno ha la sua forma da telefono** in
  `components/Mobile/`, con i dati da `crm/api/sul_telefono.py`. Non è la
  tabella del computer a righe.
- **L'azione principale di una pagina è `PulsanteAggiungi`**, non un pulsante
  nell'intestazione.
- **Più di cinque schede passano per `SchedeDelTelefono`.**

## Terza parte: un'app, non il computer in piccolo (03/10/2026)

Un giro di prova ha toccato ogni pulsante, menu e dialogo di ogni pagina su un
telefono di 390 punti (Playwright, solo letture: ogni scrittura fermata prima
del server), misurando su ogni schermata i bersagli piccoli, i campi che fanno
ingrandire iOS, il testo tagliato o minuscolo, i dialoghi che escono dallo
schermo. Quello che restava del computer si vedeva in ogni pagina: dialoghi
centrati come finestre, menu a tendina da mouse, campi a 14px, pulsanti di 28,
il «Altro» che apriva la barra laterale del computer in un cassetto, le
impostazioni con un elenco di righe da 31px e lo stesso titolo tre volte.

Le scelte sono quelle di un'app (iOS e Android le fanno uguali):

- **Un dialogo è un foglio che sale dal basso**: largo quanto lo schermo, gli
  angoli in alto tondi, la maniglia, il titolo e i pulsanti fermi mentre il
  modulo scorre, i pulsanti larghi quanto il foglio e alti 44px.
- **Un menu, le scelte di una select, l'elenco di un campo sono un foglio di
  azioni**: in basso, righe di 48px a 16px, lo schermo dietro velato.
- **Un campo è a 16px e alto 40**: sotto i 16px iOS ingrandisce la pagina al
  tocco e la lascia ingrandita. Lo stesso per le select di frappe-ui.
- **Un controllo piccolo ha un anello invisibile** che prende il tocco (solo
  sugli schermi al tocco): i pulsanti da 28 e 32px arrivano a 40.
- **Un pulsante largo quanto il suo modulo** (prenota, salva, invia) è alto 44.
- **Un avviso compare sopra la barra in basso**, mai sopra di essa.

Tutto questo è in `frontend/src/telefono.css`, sul markup che frappe-ui dà ai
suoi componenti: ogni schermata lo prende insieme, anche quelle che verranno.

| Dove | Sul telefono |
|---|---|
| Altro | Una pagina (`pages/Altro.vue`, `/altro`), non più il cassetto con la barra del computer: chi sei (il profilo, che apre le impostazioni), le notifiche con quante sono da leggere, le voci del menu che la barra non ha, le viste salvate, i primi passi, le voci dell'account come le ha ordinate il centro (`composables/vociAccount.js`: le stesse del menu dell'account sul computer), Esci in rosso. Righe da 52px in schede, l'icona in un riquadro. La voce resta accesa sulle pagine che si aprono da lì. |
| Impostazioni | La radice è un elenco da app: il titolo grande, la X per uscire, le categorie in righe da 52px con l'icona in un riquadro. Dentro, la barra ha «‹» col nome di dove torna (Impostazioni, poi la categoria) e la X: il titolo della pagina lo dice la pagina, una volta sola. |
| Aziende, Contatti, Chiamate | `ElencoAziende`, `ElencoContatti`, `ElencoChiamate` come le persone: si cerca scrivendo (il numero in qualsiasi modo), una riga per cosa, il «+». Un'azienda dice cosa fa, il suo sito e quante trattative ha; una chiamata con chi, da che parte, com'è andata, quando e quanto è durata, le perse in rosso, richiamare a un tocco. |
| Oggi | «Oggi» una volta sola (il titolo; il pulsante del giorno solo su un altro giorno), Accogli e Non venuti larghi quanto la riga e alti 40, i giorni passati senza esito ai primi quattro con «Mostra tutti e 25». |
| Agenda | Con il pannello aperto la vista dietro si toglie: la select «Lista» e le frecce del giorno, posizionate, finivano sopra il titolo del pannello. Niente settimana (sette colonne da 45px non si leggono); i filtri sfumano sul bordo, a dire che scorrono. |
| Le liste rimaste | Le trattative e i contatti di un'azienda: le caselle compaiono solo tenendo premuta una riga, come nelle liste di un telefono, e un tocco poi sceglie invece di aprire; un dettaglio senza valore non ha la sua etichetta (né «€ 0,00» per un fatturato mai scritto). |

Le parole trovate in inglese sono ora in italiano: le schede vuote
dell'attività di una persona, «Outgoing Call» (incollato a una parola
inglese) e «Lead» nel dettaglio di una chiamata, le colonne del registro,
«Mobile No». Le icone che frappe-ui non sa disegnare (un nome che Feather non
ha diventava un cerchio vuoto: il giro di chiamate, «Fuori dalla tua cura»)
sono di Lucide; automazioni e post social hanno le loro (prima il fulmine delle
trattative e la freccia di un link esterno). Un centro che non ha scelto una
valuta conta in euro, non in dollari.

## Quarta parte: ogni pagina, ogni foglio (03/10/2026)

Un secondo giro ha aperto una per una le pagine delle impostazioni, i fogli e
le pagine rimaste, sul telefono di 390 punti; quello che si è visto è stato
corretto per tutte le schermate insieme quando la causa era comune.

| Dove | Sul telefono |
|---|---|
| Impostazioni | Una pagina scorre tutta insieme, senza riquadri che scorrono dentro altri. Le parole di un'impostazione stanno sopra e il suo campo sotto, largo quanto lo schermo; un interruttore resta accanto alle sue parole. Le tendine sono alte 40 e a 16px come i campi. La barra «Aggiorna» della fatturazione è quella dello schermo, col pulsante largo. Il tema mostra il segno senza il nome tagliato; chi fa cosa tiene stretta la colonna dei servizi, i nomi interi e i segni sotto; i formati, il livello di un utente sotto il suo indirizzo, i listini uno sotto l'altro, i segni sotto i nomi negli elenchi della fatturazione; gli elenchi vuoti hanno lo stato vuoto del design system. Nome e logo, Conversazioni e Calendario, aperte da un link, non vanno più in errore. |
| La scheda di una persona | Il titolo della scheda non si ripete (lo dice già la barra), i pulsanti di eventi e cose da fare sono larghi quanto lo schermo, la riga che spiega una scheda si ferma a due righe con «Mostra altro» (`DescrizioneRipiegata`), l'avviso delle 24 ore di WhatsApp dice l'essenziale. |
| I fogli | I pulsanti in fondo prendono la larghezza qualunque riga li contenga, larghi uguali, e vanno a capo invece di uscire dallo schermo (quattro, nel post social); un segnaposto vuoto che spingeva un pulsante a destra sparisce; un avviso sopra un foglio aperto arriva dall'alto. La barra di un editor va su due righe invece di tagliare gli ultimi pulsanti. Un evento ha i campi tutti alti uguali (i partecipanti, gli avvisi, il colore). Le righe di un preventivo sono schede: il servizio e la descrizione larghi quanto lo schermo, poi fase, prezzo e sconto affiancati e l'importo; erano sette colonne che uscivano dal bordo. Chi ha aperto una cartella mette chi e quando sulla prima riga, cosa sotto. Allegare non chiede di trascinare file, che su un telefono non si trascinano. |
| Le scelte | Il valore di un campo a scelta (tipo di chiamata, stato, priorità) si legge nella lingua di chi legge, salvato com'è; un elenco a tendina non ripete il nome come descrizione («Consulenza» sotto «Consulenza»). |
| Note | Un elenco suo (`ElencoNote`, `get_notes`): si trova scrivendo il titolo o le parole, una riga per nota con le prime parole, chi l'ha scritta, di chi parla e quando, «+» ne scrive una. |
| Automazioni | Il titolo non si riduce più a una lettera: le ricette sono un'icona e «+» ne crea una. Nell'editor il titolo resta intero: la prova a vuoto e le statistiche stanno nel menu «⋯». |
| Lista d'attesa | I tre numeri su una riga, come i riquadri del design system. |
| /prenota | I passi su una riga: quello dove si è dice il suo nome, gli altri il numero. |

Le scritte troppo chiare per essere lette (il rosso e il blu `ink-*-4`) sono
del settimo passo; i comandi che comparivano solo al passaggio del mouse si
vedono su uno schermo al tocco. Sul tema scuro gli stati (in attesa, non
venuti, confermato) restavano coi colori del chiaro, scuri su scuro: ora hanno
quelli che il design system disegna sullo scuro. A 360 punti il nome di un
numero di Oggi va su due righe invece di tagliarsi.

Le parole: Sig., Dott. e gli altri titoli, i generi, le fonti che mancavano,
le parti del giorno, le ricette delle automazioni e quello che scrivono, la
data di un evento («3 ott 2026», non «ott 3, 2026»), il selettore data e ora
di frappe-ui, «Pianifica» un post (era un sostantivo), il motivo per cui una
proposta della lista d'attesa non è partita, la provenienza di una persona
(«Prenotazione online», non `service_booking`), «Da fare» per quanto resta di
un preventivo (era «Sinistra»), il nome di un campo a metà frase in minuscolo
(«Aggiungi sito web…», non «Aggiungi Sito web…»). Le parole brevi che il
framework traduce in un senso solo hanno il loro dove le usiamo in un altro:
«Genitore» (non «Principale»), l'«Inizio» di un orario (non «Avvia»), le
«Sedute» di un ciclo, la «Sintesi» del paziente, un modulo «Iniziato», «Ferma»
la registrazione, la «Pagina di provenienza» di una visita, «Presa visione»
per un'informativa e «Letto» per un messaggio (erano «Leggere»), un periodo
«1 ott 2026 – 31 ott 2026». Nelle frasi di una scheda le date sono per esteso
(«Paziente dal 29 set 2026»), non nel formato del sistema. Le opzioni della fatturazione
non parlano più del «progetto originale». La scritta che accompagna una bozza
dell'assistente è nella lingua del centro: la legge il paziente, non chi l'ha
controllata.

Una prenotazione dalle pagine del centro senza una visita tracciata era tra le
«Terze parti», come quelle di una piattaforma: ora è traffico diretto, e una
patch corregge quelle già salvate.

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
| `crm/api/sul_telefono.py` | Le liste del telefono: persone (cifre, nome, email, il prossimo appuntamento), cose da fare aperte, fasi e trattative. Testato in `crm/tests/test_sul_telefono.py` |
| `frontend/src/components/Mobile/ElencoPersone.vue`, `ElencoCose.vue`, `TrattativePerFase.vue`, `AgendaDelGiorno.vue`, `SchedeDelTelefono.vue`, `PulsanteAggiungi.vue` | Le schermate fatte per il telefono |
| `frontend/src/utils/sulTelefono.js` | Le parti pure: la riga di una persona, i gruppi delle cose da fare, la fase di partenza, il valore di una trattativa, la settimana, la giornata in ordine, dove cade adesso. Testato |
| `frontend/src/pages/Leads.vue`, `Tasks.vue`, `Deals.vue`, `Calendar.vue`, `Today.vue`, `MobileLead.vue`, `MobileDeal.vue`, `components/PersonHeader.vue` | Le schermate del telefono al posto di tabelle e lavagne |
| `frontend/src/telefono.css` | Fogli dal basso, fogli di azioni, campi a 16px, anelli al tocco, pulsanti delle azioni, avvisi sopra la barra |
| `frontend/src/pages/Altro.vue`, `composables/vociAccount.js`, `composables/visteSalvate.js` | La pagina «Altro»; le voci dell'account e le viste salvate, le stesse del computer |
| `frontend/src/components/Settings/Settings.vue` | La radice da app, la barra col nome di dove torna |
| `frontend/src/components/Mobile/ElencoAziende.vue`, `ElencoContatti.vue`, `ElencoChiamate.vue` + `crm/api/sul_telefono.py` (`get_organizations`, `get_contacts`, `get_calls`) | Le liste di aziende, contatti e chiamate |
| `frontend/src/components/ListViews/MobileListRows.vue`, `utils/mobileList.js` | La scelta tenendo premuto, i dettagli vuoti tolti |
| `frontend/src/pages/Today.vue`, `components/Today/ParticipantRow.vue`, `utils/oggi.js` (`firstOfPast`) | Oggi sul telefono |
| `frontend/src/components/Mobile/ElencoNote.vue`, `pages/Notes.vue` + `crm/api/sul_telefono.py` (`get_notes`) | Le note sul telefono |
| `frontend/src/components/Mobile/DescrizioneRipiegata.vue` | La riga che spiega una scheda, piegata a due righe |
| `frontend/src/telefono.css` (impostazioni, fogli, tendine, avvisi) | Una pagina che scorre sola, le righe delle impostazioni, i pulsanti dei fogli che vanno a capo, le tendine a 40px, l'avviso dall'alto sopra un foglio |
| `frontend/src/components/Settings/**` | Le pagine delle impostazioni sul telefono, gli stati vuoti, i campi che aspettano le impostazioni |
| `frontend/src/components/FieldLayout/Field.vue`, `Controls/Link.vue` | Le scelte tradotte, le descrizioni che non ripetono il nome |
| `crm/api/booking.py` (`categoria_senza_visita`) + `crm/patches/v1_0/the_centres_own_pages_are_direct_traffic.py` | Le pagine del centro sono traffico diretto |
| `crm/assistente/modello.py` (`segno`) | La scritta di una bozza nella lingua del centro |
| `frontend/src/espresso.css` (tema scuro) | Gli stati leggibili sullo scuro |
| `frontend/src/components/Quotes/QuoteDialog.vue`, `Modals/EventModal.vue`, `Calendar/EventNotifications.vue`, `Clinic/ClinicArea.vue`, `FilesUploader/FilesUploaderArea.vue` | Le righe di un preventivo, un evento, chi ha aperto una cartella, allegare |
| `crm/fcrm/doctype/crm_fields_layout/crm_fields_layout.py` (`in_frase`) | Il nome di un campo dentro il suo segnaposto |

## Non incluso

- **Il builder della dashboard** resta da desktop: una griglia da trascinare
  su un telefono non si usa. Sul telefono le dashboard si guardano.
- **Il 404 della pagina Telephony** per chi non ha ancora un agente: è come la
  pagina sa che l'agente va creato. frappe-ui rilancia l'errore di ogni
  richiesta partita da sola, e la console lo mostra, ma chi usa la pagina non
  vede niente.
