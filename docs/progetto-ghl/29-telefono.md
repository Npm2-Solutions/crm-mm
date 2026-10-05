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
- **Mentre si scrive la cornice segue la tastiera** (`utils/tastieraAperta.js`):
  un elemento fisso in fondo allo schermo finisce sotto la tastiera; quello che
  deve restare in vista sta in fondo alla cornice o a un foglio, non in
  `position: fixed`.
- **Ogni campo chiede la sua tastiera**: `tastieraDi(field)` per un campo di
  un DocType, `tastiera('telefono' | 'email' | 'url' | 'intero' | 'codice' |
  'cifre')` per gli altri (`utils/tastiera.js`); un numero intero su
  `type="number"` ha `inputmode="numeric"`.

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
| Accoglienza | I quattro numeri stanno in una riga di riquadri piccoli (`dc-stat-row`): gli appuntamenti cominciano nella prima schermata. |
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
| Accoglienza | Il titolo è «Accoglienza ▾»: le tre viste dell'agenda (Accoglienza, Agenda, Lista d'attesa) stanno nel suo menu, perché tre non entrano accanto ai pulsanti della testata. Il pulsante del giorno dice sempre quale («Oggi», «ven 2 ott»). Accogli e Non venuti larghi quanto la riga e alti 40, i giorni passati senza esito ai primi quattro con «Mostra tutti e 25». |
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
| Cartella clinica | L'odontogramma va a capo dopo il primo quadrante e si legge di seguito (18-11, poi 21-28): sedici denti affiancati uscivano dallo schermo. Le voci della sintesi sono tutte in italiano. |
| /prenota | I passi su una riga: quello dove si è dice il suo nome, gli altri il numero. |

Le scritte troppo chiare per essere lette (il rosso e il blu `ink-*-4`) sono
del settimo passo; i comandi che comparivano solo al passaggio del mouse si
vedono su uno schermo al tocco. Sul tema scuro gli stati (in attesa, non
venuti, confermato) restavano coi colori del chiaro, scuri su scuro: ora hanno
quelli che il design system disegna sullo scuro. A 360 punti il nome di un
numero dell'Accoglienza va su due righe invece di tagliarsi.

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
(«Paziente dal 29 set 2026»), non nel formato del sistema. Un'ora che il
database manda senza lo zero («7:30:00») si scrive «07:30», non «7:30:»; un
errore dell'assistente è una frase («L'assistente ora non è raggiungibile»),
non il nome di un'eccezione. Le opzioni della fatturazione
non parlano più del «progetto originale». La scritta che accompagna una bozza
dell'assistente è nella lingua del centro: la legge il paziente, non chi l'ha
controllata.

Una prenotazione dalle pagine del centro senza una visita tracciata era tra le
«Terze parti», come quelle di una piattaforma: ora è traffico diretto, e una
patch corregge quelle già salvate.

## Quinta parte: a 360 punti e al buio (03/10/2026)

Il giro che preme ogni pulsante e apre ogni foglio (`tocca.mjs`) è passato di
nuovo su tutte le pagine, sul telefono più stretto (360 punti) e col tema scuro:
milleduecento stati, nessuna pagina più larga dello schermo, nessun campo sotto
i 16px.

| Dove | Sul telefono |
|---|---|
| I fogli più alti dello schermo | Si aprono dal titolo, con la X per chiudere. Un evento, a 360 punti, si apriva già scorso: il campo del titolo prendeva il fuoco mentre il foglio saliva da sotto lo schermo, e il browser lo scorreva per raggiungerlo; ora il fuoco non scorre (`preventScroll`). Un foglio più alto dello schermo cresce verso il basso, dove si scorre: spinto in fondo, prima traboccava in alto, fuori portata. |
| Un'azienda | Le trattative si vedono: la scheda «Trattative» mostrava i contatti, perché sul telefono i dettagli vengono prima e le schede si contavano come sul computer. Le tre schede stanno sullo schermo senza icone, come quelle di una persona; una scheda vuota lo dice in una frase intera («Ancora nessun contatto»), non «Ancora niente in Trattative». La fase di una trattativa si legge in italiano, qui e nel contatto. |
| Un contatto | Le sue trattative si vedono anche in italiano: la scheda si cercava per il nome tradotto. |
| Automazioni | I passi parlano italiano: «Invia un'email», «Attendi», «Se / Altrimenti», «Apri una trattativa», le loro descrizioni, le categorie e gli obiettivi. Le frasi col nome del prodotto si traducono (il nome si mette dopo, `__()`), e nessuna nomina un altro prodotto. Nella testata, al posto di «Non salvata» c'è un punto: a 360 punti la scritta lasciava del titolo tre lettere. |
| Moduli | Nell'editor lo stato del modulo («Versione 1») va sotto il titolo invece di uscire dallo schermo. |
| Lista d'attesa | Vuota, ha lo stato vuoto del design system. |
| Importazione | «Scegli cosa importare» chiede «Cerca», non «Search doctype»: è il segnaposto di ogni campo collegato di frappe-ui che non ne ha uno suo. |

## Sesta parte: la tastiera giusta (03/10/2026)

Il giro guarda gli schermi, non la tastiera che sale. Toccando un campo, il
telefono apriva la tastiera delle lettere quasi ovunque: per un numero di
telefono, un'email, i giorni di un'impostazione, l'importo di una trattativa.

| Campo | Sul telefono |
|---|---|
| Cellulare e telefono (scheda, persona nuova, «Per chi è?» dell'agenda, la chiamata, il numero dell'operatore, i recapiti del sito) | Il tastierino del telefono, con + * # |
| Email e PEC | La tastiera con la @, senza maiuscola all'inizio |
| Sito, link, indirizzi dei servizi | La tastiera degli indirizzi, con / e .com |
| Ricavi, valore, probabilità, ogni campo numerico di una scheda | Il tastierino con la virgola: la scheda legge il numero nel formato del sistema (`flt`) |
| Giorni, ore, minuti, posti, limiti, priorità (76 campi, quasi tutti nelle impostazioni) | Il tastierino delle cifre |
| Codice fiscale, partita IVA, codice destinatario, codice SSA | Le maiuscole, mai corrette dal telefono |
| Codice regione e ASL del Sistema TS, gli ID di Meta e WhatsApp | Le cifre |
| Il SID di Twilio | Né maiuscole né correzioni: è un codice che distingue maiuscole e minuscole |
| La ricerca delle liste (persone, contatti, aziende, chiamate, note, chat) | Il tasto «Cerca», che chiude la tastiera sui risultati; un cognome non viene mai corretto in una parola (`tastiera('cerca')`) |

Restano come sono, e perché:

- **Gli importi dei dialoghi** (prezzo di un appuntamento, di una fattura, di
  un preventivo, di un ciclo): sono `type="number"`, letti dal browser. Il
  tastierino decimale di iPhone mostra solo il separatore della lingua del
  telefono, la virgola, e Safari su un `type="number"` può non accettarla;
  la tastiera dei numeri di oggi ha punto e virgola.
- **Il CAP** e **lo scostamento in giorni di un'automazione**: un CAP straniero
  può avere lettere, uno scostamento può essere negativo, e il tastierino
  delle cifre non ha né lettere né meno.
- **Nessun suggerimento automatico** dei propri dati: i campi tengono
  `autocomplete="off"` di frappe-ui, perché sono di un altro. Le pagine
  pubbliche (`/prenota`, i moduli del sito, l'area) li suggeriscono già: lì la
  persona scrive i suoi.

## Settima parte: scrivere sul telefono (03/10/2026)

La tastiera copre il fondo dello schermo senza accorciare la pagina: iPhone, e
Chrome su Android, rimpiccioliscono solo la parte che si vede (il «visual
viewport») e la fanno scivolare verso il campo. La cornice dell'app restava
alta quanto lo schermo, e quello che sta in fondo finiva sotto la tastiera:
«Crea» di un foglio, la casella della chat, «Prenota l'appuntamento». Intanto
la testata scivolava via in alto.

`utils/tastieraAperta.js` guarda il visual viewport mentre qualcuno scrive, e
scrive sulla radice quanto se ne vede. `telefono.css` (e `area.css` per l'area):

| Dove | Con la tastiera aperta |
|---|---|
| La cornice dell'app (`data-cornice-telefono`) | Alta quanto la parte visibile e ferma in alto: la testata resta, la lista o la chat finiscono sulla tastiera |
| La barra in basso | Si toglie, come nelle app del telefono, e torna quando la tastiera si chiude |
| Un foglio | Si appoggia sulla tastiera, il titolo in alto e i pulsanti in vista; lo spazio sopra il foglio si riduce |
| La lista di un menu, di una scelta, di un campo collegato | Sopra la tastiera, con la ricerca in cima e «Pulisci» in fondo |
| Le impostazioni | Alte quanto la parte visibile, la barra del salvataggio sopra la tastiera |
| L'area del paziente | La stessa cosa: la chat col centro, i dialoghi, i posti in basso che si tolgono |

Con il tocco, come in un'app:

- **Niente lampo grigio a ogni tocco.** Quello che si tocca mostra da sé che è
  premuto: i pulsanti di frappe-ui, la barra, le righe delle liste. iPhone lo
  mostra solo dove si ascolta il tocco, e la cornice lo ascolta.
- **Tirando giù in cima a una lista si ricarica la lista, non l'app.** Il
  gesto del browser ricaricava tutto, anche un modulo scritto a metà: è spento,
  e la cornice non rimbalza. Le liste del telefono (persone, contatti, aziende,
  chiamate, note, cose da fare, trattative per fase, la giornata dell'agenda,
  le chat, le notifiche e gli eventi) e le pagine di ogni giorno (le fatture,
  l'accoglienza, la lista d'attesa, la panoramica) hanno il loro: una freccia
  che si gira quando basta lasciare, poi il segno che gira finché la lista non
  è tornata (`composables/tiraPerAggiornare.js`). Si tira la scatola che
  scorre, che c'è anche quando la lista è vuota: «Nessuna notifica» si tira
  come una lista piena, per vedere se ne è arrivata una.
- **Tornando indietro, una lista è com'era.** Aperta una persona (una
  trattativa, una chat) e tornati indietro, la lista ha ancora le parole
  cercate, le righe che aveva e il punto a cui era arrivata; poi si aggiorna da
  sé, in silenzio, pagina per pagina: un numero corretto sulla scheda si vede
  già nella riga. Solo l'indietro la rimette così: aperta dal menu riparte
  dall'inizio, come una pagina nel browser. Quello che si ricorda resta in
  memoria per la sessione: un nome cercato non si scrive sul telefono
  (`utils/ritorno.js`). «Persone» in cima alla scheda fa lo stesso: la briciola
  della pagina da cui si è arrivati torna indietro invece di riaprirla da capo,
  e ha l'altezza di un pollice. Un'app installata su iPhone non ha il gesto per
  tornare: la briciola è la via del ritorno (`tornaConLeBriciole`). Le schede
  della barra in basso fanno lo stesso: dalla scheda di una persona aperta dalla
  lista, «Persone» è la lista com'era.
- **La scheda su cui si è, toccata di nuovo, torna in cima.** frappe-ui faceva
  scorrere la cornice, ma le liste del telefono scorrono in una scatola loro: il
  tocco non faceva niente. Ora la pagina torna su; con una chat aperta, «Chat»
  torna all'elenco delle chat, come nelle app del telefono
  (`utils/schedaAttiva.js`: una pagina dice cosa fa prima con
  `alToccoDellaScheda`).
- **Tenuto di traverso, il telefono resta un telefono.** A 844×390 l'app
  passava al computer: la barra laterale, la tabella, l'agenda alta due ore e
  mezza. Ora un telefono di traverso (meno di 500px di altezza, toccato con un
  dito) tiene la sua interfaccia (`isPhoneSize`, e in CSS `(max-height: 499px)
  and (pointer: coarse)` accanto a `(max-width: 767px)`). Quello che sta fermo si
  fa piccolo: la scheda di una persona sta su una riga (il nome, cosa viene dopo,
  i tasti rotondi senza parole, che restano il loro nome per chi non vede) e la
  barra in basso mette le parole accanto alle icone. Un tablet di traverso,
  alto più di 500px, resta il computer.
- **Il giorno dell'agenda si sfoglia col dito**, come nel calendario del
  telefono: la lista del giorno spinta a sinistra è il giorno dopo, a destra
  quello prima, e segue un poco il dito; la striscia della settimana sposta di
  una settimana. Anche l'accoglienza, che mostra un giorno, si sfoglia così.
  Solo un gesto di lato conta: su e giù la lista scorre (o si tira per
  aggiornare), e dal bordo dello schermo è l'indietro del telefono.
  Un gesto di lato in una pagina non porta più il browser alla pagina prima
  (`touch-pan-y`, `overscroll-behavior-x: none`; `composables/scorriGiorni.js`).
- **Sulla schermata Home si apre come un'app**, a tutto schermo, senza le
  barre del browser e con la sua icona. In «Altro» una scheda lo propone: su
  Android con il pulsante «Installa», che chiede al browser (`beforeinstallprompt`,
  tenuto da `utils/installa.js`); su iPhone, che non lo offre, con i due tocchi
  in Safari (Condividi, poi «Aggiungi alla schermata Home»). Non c'è più una
  volta installata, né dopo «Non ora» su quel telefono. L'area del paziente ha
  la sua, nella pagina iniziale e nel suo stile (`area/components/InstallCard.vue`):
  chi ha l'area sulla schermata Home ha l'app del centro.
- **Senza rete l'app lo dice**: sotto la testata, «Sei senza rete: finché non
  torna, le modifiche non si salvano», finché la rete non torna.
- **Un foglio si tira giù per metterlo via.** La maniglia in cima a un
  dialogo era solo disegnata. Ora preso per la cima (la maniglia, il titolo) il
  foglio segue il dito e lo schermo dietro si schiarisce. Lasciato oltre un
  terzo, o con un colpo veloce, si chiude come con Esc; se no torna su. Mai dal
  modulo né da un foglio già scorso: lì il dito scorre, scrive, firma. Un
  dialogo che non si può ancora chiudere (impostazioni con modifiche non
  salvate) torna su; le impostazioni, schermo intero senza maniglia, non si
  tirano (`utils/trascinaFoglio.js`).
- **La barra di stato ha il colore dell'app**, chiara o scura, e lo cambia col
  tema (`theme-color`).
- **«Indietro» chiude prima quello che sta sopra.** Il tasto di Android (e
  quello del browser) con un foglio, un menu, una lista o il pannello
  dell'agenda aperto lasciava la pagina, e una nota scritta a metà con lei.
  Ora chiude quello che sta sopra e resta; il secondo «indietro» lascia la
  pagina. Nessuna voce finta nella cronologia: una guardia del router
  riconosce l'indietro (il browser ha già messo lo stato della voce di
  destinazione) e annulla la navigazione, e il router rimette l'indirizzo da
  solo (`utils/indietro.js`). Un pannello di pagina si iscrive con
  `chiudeConIndietro(chiudi)`; uno dentro un foglio (le impostazioni) dà anche
  il suo elemento, e torna indietro di un passo prima che il foglio si chiuda:
  dalla voce alla categoria, poi all'elenco, poi le impostazioni si chiudono.
  Da una chat «indietro» torna all'elenco delle conversazioni, come su
  WhatsApp. L'area del paziente fa lo stesso con i suoi dialoghi.
- **Tenendo premuto non compare il menu del browser.** Sulla barra, sulle
  schede, sui pulsanti e sulle righe non si apre il menu di un link e non si
  seleziona una parola: una riga tenuta premuta si sceglie (`MobileListRows`).
- **Prenotare dal telefono, provato davvero.** Agenda, «+», il servizio dal
  foglio, la persona cercata per nome, un orario libero, «Prenota
  l'appuntamento»: l'appuntamento c'è, col suo prezzo. Strada facendo:
  - **gli orari liberi, un giorno alla volta**: il giorno una volta («Lunedì 5
    ottobre») e sotto i suoi orari, come in un'app di prenotazione, non più
    «dom 4 ott 02:30» su ogni bottone; dodici per giorno con «altri N», cinque
    giorni (`orariPerGiorno` in `utils/scheduler.js`). Prima i primi 24 orari
    potevano essere tutti della prima mattina;
  - **cercando una persona, il cellulare e l'email sotto il nome**: due
    «Marco Romano» erano due righe uguali. La ricerca trova anche per numero o
    per email (`search_fields` della Persona), in ogni campo che sceglie una
    persona;
  - **i campi allineati**: il pallino del servizio occupa il posto delle icone;
    un campo di ricerca largo `w-full` finiva 4px prima degli altri (il padding
    per l'anello del fuoco contato nella larghezza: `box-content` in
    `Controls/Link.vue`); la persona scelta, una scatola disegnata come un
    campo, è alta 40px come gli altri (`data-campo`, `telefono.css` sezione 2).
- **La giornata della segreteria, provata davvero.** Dal telefono, con
  scritture vere:
  - **«Accogli»** fermava la segreteria in due casi: un appuntamento
    sovrapposto forzato da un manager tornava a essere un errore per chi non
    può forzare, e un professionista il cui account non c'è più dava
    «Impossibile trovare Riga #1». Ora le sovrapposizioni si ricontrollano solo
    quando cambia qualcosa che le decide (orario, chi lo fa, le stanze, chi
    viene: `slot_changed`), e un esito si salva senza ricontrollare i
    collegamenti. In sala d'attesa il servizio sta sopra la persona;
  - **una cosa da fare nuova** è di chi la scrive: senza nessuno in «Assegnato
    a» non era di nessuno, e «Mie» restava vuota come se non fosse salvata;
  - **la barra di scrittura** sopra una descrizione, una nota, un commento o
    un'email sta su una riga: grassetto, corsivo, elenchi, link, immagine
    (`phoneToolbar` in `components/editor/config.ts`), non le due righe del
    computer;
  - **«Emetti la fattura»** su un appuntamento di cui l'agenda non sa chi ha
    fatto la prestazione dava un errore e nessuna strada: ora si apre la
    fattura con quello che l'agenda sa e chiede solo «Chi l'ha eseguito»
    (`appointment_invoice_proposal`, `nuovaFattura(cliente, { bozza })`); sotto
    ogni professionista la qualifica in parole, non il suo codice.
- **La visita del medico, provata davvero.** Dal telefono la dottoressa apre
  la persona, la scheda Clinica, «Nuova visita» e «Visita libera», scrive e
  salva la bozza. Il riquadro per scrivere si apriva sotto la sintesi, fuori
  dallo schermo, e sembrava che il pulsante non facesse nulla: ora, aperto,
  viene in vista da sé (`ClinicArea.vue`, dopo il cambio di stato, così il
  `nextTick` aspetta che sia disegnato).
- **La scheda della persona si raccoglie.** Nome, prossimo appuntamento e i
  pulsanti per chiamare e scrivere stavano sopra le schede e non se ne
  andavano mai: le schede scorrono in un riquadro loro, e con la tastiera
  aperta per una visita restava poco più di una riga. Ora, quando la scheda
  sotto scorre, la testata si raccoglie (il nome resta in alto, nelle
  briciole) e torna quando si risale in cima o si cambia scheda. Si raccoglie
  solo se c'è abbastanza sotto da restare scorsi senza di lei, se no
  rimbalzerebbe; un salto più lungo di quanto il riquadro mostra è della
  pagina, non del dito (le attività che si aprono sull'ultima), e non la
  raccoglie; un campo, un editor o un riquadro piccolo che scorrono dentro
  la scheda non contano (`composables/testataRaccolta.js`).
- **L'odontogramma del dentista, provato davvero.** Dal telefono il dentista
  apre l'odontogramma, sceglie il 46, aggiunge una carie con le superfici e
  salva. «Salva l'odontogramma» stava in cima al riquadro, fuori schermo
  mentre si scriveva sul dente in fondo: sul telefono ora sta alla fine, dove
  si arriva scrivendo. Nella riga del dente la × finiva da sola su una riga:
  ora sta accanto alla condizione, superfici e nota sotto, larghe quanto il
  riquadro. Tra le condizioni c'era «Cellulare»: il «Mobile» di un dente che
  si muove prendeva la parola del framework per il numero di telefono; ora le
  condizioni passano il contesto «Tooth condition» e il catalogo dice
  «Mobile».
- **Il piano di cura, provato davvero.** Dal telefono il dentista apre
  Preventivi da «Altro», scrive un preventivo con Igiene sul 36 (superfici
  OM, che diventano MO), lo salva e lo propone: «Igiene · Dente 36 MO».
  - **Una riga lasciata vuota** fermava la bozza con «Row 2: choose the
    service». Ora una riga in cui nessuno ha scritto niente resta fuori
    (`preventivi.regole.vuota`): un dente scritto basta a farne una riga.
  - **In inglese.** Il messaggio arrivava in inglese, e con lui altre 68 frasi
    delle regole: piani, programmi, preventivi, denti, alimenti, il motore
    dei moduli. Passano per `Problema` ed `Errore` e non per `_()`, quindi
    l'estrazione del catalogo non le vedeva. Ora sono tutte in `it.po`, e
    `crm/tests/test_frasi_delle_regole.py` le cerca una per una.
  - **Il foglio.** La × di un foglio con il titolo su due righe (lo stato e
    la trattativa sotto) scendeva a metà: ora sta accanto alla prima riga, in
    tutti i fogli (`telefono.css`). Sopra i pulsanti c'era una riga doppia,
    perché un `dialog-footer` dentro la fila di frappe-ui ripeteva il bordo:
    ora la fila è una. «Trattativa: …» è allineata al titolo, e il totale è
    largo quanto le righe, non un riquadro rientrato a destra.
- **Un ciclo venduto e la lista d'attesa, provati davvero.** Dai Dettagli
  della persona la segreteria vende dieci sedute di fisioterapia e apre la
  lista d'attesa. Le date dei fogli («Da», «Fino a», «Valido fino al») si
  leggevano «2026-10-04»: 26 campi data in 17 finestre non dicevano il
  formato. Ora seguono quello del centro come i campi della scheda
  (`dateFormat()` in `utils/index.js`); l'area pazienti, che non ha le
  impostazioni di sistema, scrive il giorno per primo (`FORMATO_DEL_CAMPO`).
- **La dieta a scambi, provata davvero.** Dai Piani la dietista apre una
  dieta a scambi: cinque momenti, ciascuno col suo giorno, l'ora e le voci.
  Il nome del momento divideva la riga col giorno e si leggeva «Spuntino del
  mattir»: sul telefono ora ha la sua riga, giorno, ora e cestino sotto.
- **Un modulo compilato in segreteria, provato davvero.** Dai Moduli della
  persona, «Compila un modulo» apre la pagina da compilare e firmare. La barra
  in basso accendeva «Altro», come se il modulo non fosse di nessuno: ora
  accende Persone, e così la barra laterale (`utils/navigation.js`).
  Poi la firma col dito: la barra delle azioni in fondo (Scarta, Salva per
  dopo, Altri modi di firmare, Firma e concludi) occupa tre righe, e quello
  che veniva portato in vista (un campo toccato con la tastiera aperta, la
  firma) poteva finirci sotto: il dito sulla firma apriva «Vuoi scartare
  questo modulo?». Ora il riquadro che scorre tiene conto della barra
  (`scroll-padding-bottom`), e la firma si fa e si conclude.
  «In autonomia» apre il foglio dei moduli da mandare: i suoi pulsanti si
  leggevano «Invia il link | Annulla», al contrario di ogni altro foglio.
  La fila di frappe-ui mette per primo il pulsante principale e sul telefono
  si gira, perché finisca sotto il pollice; una fila scritta a mano lo mette
  già per ultimo, e girata finiva a sinistra. Ora si gira solo quando il
  principale viene per primo (`telefono.css`).
- **Un appuntamento spostato, provato davvero.** Col telefono su un fuso e il
  centro su un altro, «Salva» senza toccare nulla spostava l'appuntamento
  (00:00 diventava 03:30). Gli orari liberi, l'ora proposta per un nuovo
  appuntamento, la linea «adesso» del giorno e l'attesa in accoglienza
  seguivano l'orologio del telefono. Ora tutto segue l'orologio del centro
  (`oraDelCentro()`, `sulCentro()`, `adessoDelCentro()` in
  `utils/scheduler.js`): anche le cose da fare in ritardo, di oggi e di
  domani, e il prossimo appuntamento nella lista delle persone.
- **Un abbonamento venduto e una trattativa spostata, provati davvero.** Dai
  Dettagli della persona la segreteria vende un abbonamento e da lì prenota.
  Dalle Trattative ne apre una e la sposta di fase dal foglio delle fasi.
  Ogni campo salvato diceva «Documento aggiornato», che si confondeva con i
  documenti della persona: ora dice «Salvato».
- **Un appuntamento annullato, provato davvero.** In fondo alla scheda,
  fisso, c'era «Ripeti questo appuntamento» con i suoi campi: sul telefono
  occupava il posto del pollice. Ora è una riga che si apre quando serve.
  Un tocco su «Annullato» nel menu dello stato annullava subito, senza
  chiedere: l'orario si liberava e la lista d'attesa poteva già offrirlo.
  Ora la scheda chiede conferma e il motivo, se lo si sa. Il motivo va alle
  piattaforme da cui l'appuntamento è arrivato e resta scritto sulla scheda.
  Rimesso «Confermato», l'appuntamento restava senza nessuno: niente
  promemoria, e nell'agenda solo il servizio. Ora chi era stato annullato
  torna prenotato, nei posti del servizio (`CRM Appointment.brought_back`).
- **L'accoglienza, provata davvero.** «Accogli» porta la persona in sala
  d'attesa, e l'attesa si conta sull'orologio del centro. Accanto a
  «Presente» c'era «Annulla», che in accoglienza si leggeva come annullare
  l'appuntamento. Ora dice cosa toglie: «Annulla l'arrivo», o «Annulla
  l'esito» dopo «Presente» o «Assente». Dopo «Presente» la fattura era in
  Fatture, in mezzo agli appuntamenti delle ultime due settimane: ora
  «Emetti la fattura» sta sull'appuntamento stesso, finché non è fatturato,
  e apre la fattura già compilata (`useFattura().fatturaDellIncontro`, la
  stessa strada della pagina Fatture).
- **Un appuntamento per una persona nuova, provato davvero.** Dal «+»
  dell'agenda, «Non è in DottorCloud? Scrivi un nome» apre nome, telefono ed
  email. Sul telefono telefono ed email stavano affiancati, in 160 punti
  ciascuno, e un'email si leggeva tagliata: ora sono uno sotto l'altro.
  Prenotato, l'appuntamento teneva solo il nome, senza una scheda: niente
  moduli, fattura o cartella. Ora chi è scritto con un contatto viene trovato
  o creato come in una prenotazione (`appointments._persona_scritta`); un
  nome da solo resta un nome, perché due Maria Rossi non sono una.
- **Un documento fotografato, provato davvero.** Dai Documenti della persona,
  «Aggiungi un documento» apre il foglio, e «Scegli il file» lascia al
  telefono la scelta tra fotocamera, foto e file. Il tipo partiva da «Modulo
  firmato», il primo dell'elenco: una carta d'identità fotografata al banco
  finiva archiviata come modulo firmato, e il tipo decide chi legge il
  documento. Ora il tipo lo sceglie chi archivia, e finché manca il foglio
  non salva.
- **Una cosa da fare, provata davvero.** Dal «+» delle Cose da fare: titolo,
  descrizione, scadenza, «Crea», poi il tondo per segnarla fatta. Il
  calendario della scadenza scriveva «Oct 2026» e sopra le colonne
  «S M T W T F S», dalla domenica, mentre la griglia, in italiano, parte dal
  lunedì: domenica 4 stava sotto la «S» del sabato. Ora mesi e lettere
  vengono dalla lingua dell'utente e dal giorno da cui parte la griglia
  («L M M G V S D», «Ott 2026», `frontend/vite/frappeUi.js`), e le frecce si
  leggono «Mese precedente» e «Mese successivo». La settimana parte dal
  lunedì per tutti, come la striscia dell'agenda sul telefono: anche
  l'agenda del computer, che partiva dalla domenica nella settimana e nel
  mese, dove sotto un giorno pieno ora si legge «altri 4» e non «4 more». Una scadenza scelta senza
  ora arrivava come la sua mezzanotte: nella lista si leggeva «00:00», e una
  di oggi era già «In ritardo». Ora vale tutto il giorno e mostra solo il
  giorno, sul telefono, nella scheda della persona e nell'elenco.
- **Una nota, provata davvero.** Scritta dal «+», trovata cercando una sua
  parola, aperta, corretta e salvata. Una nota o una cosa da fare scritte per
  sbaglio non si potevano togliere dal telefono: le liste del telefono non
  hanno il menu delle righe del computer. Ora il loro foglio ha il cestino,
  per chi può eliminarle (lo dice il server), con la domanda prima
  (`DoctypeModal`, `callbacks.afterDelete` di chi apre il foglio), dalle Note,
  dalle Cose da fare e dalla scheda della persona.
- **Un'email e una chiamata, provate davvero.** Dalla scheda di una persona
  l'email parte e compare nella sua storia, con il nome del centro come
  oggetto. «Registra una chiamata» invece non salvava: in uscita chiedeva il
  «Numero chiamante», cioè la propria linea, che chi non ha un numero in
  DottorCloud non sa. Ora una chiamata scritta a mano tiene il numero della
  persona e lascia vuoto quello che non si sa; le chiamate di Twilio portano
  sempre entrambi (`CRM Call Log.a_providers_call_carries_both_numbers`).
  Salvata, la scheda apriva «Chiamate», una scheda rimasta solo sul telefono
  e sempre vuota: le chiamate sono una vista della storia (la pillola
  «Chiamate»), e ora si apre quella, con la pillola intera in vista. Il giorno
  di una chiamata si legge «dom 4 ott», non «ott 4, domenica».
- **Una lista d'attesa, provata davvero.** Dai Dettagli della persona, «Metti
  in lista d'attesa»: servizio, giorni, parte del giorno, «Metti in lista», e
  «Trova un posto» propone i posti liberi. Sul sito di prova i posti del
  pomeriggio comparivano la sera: l'agenda leggeva gli orari di lavoro in UTC
  e mostrava tutto sull'ora del sito. Un centro arriva lì solo scegliendo un
  fuso diverso in Impostazioni › Agenda; ora quella pagina lo dice, e chiede
  di tenere il fuso del sito.

La prova è stata fatta in Chromium con un visual viewport finto, alto 508 punti
come con la tastiera di un iPhone da 844, e un riquadro al posto della
tastiera. Così si sono provati la persona nuova, il nuovo appuntamento, la
ricerca, una nota, la lista di un campo collegato, una conversazione WhatsApp e
la chat dell'area: il campo attivo resta in vista e la tastiera, chiudendosi,
riporta tutto com'era. Su un iPhone vero va guardato appena possibile, perché
nessun browser di prova ha la sua tastiera.

## Ottava parte: il tablet (05/10/2026)

Un tablet ha l'interfaccia del computer, toccata con un dito. Un giro su un
iPad in piedi (768 e 820 punti) e di traverso (1180) ha aperto ogni pagina del
giorno e una scheda di ogni tipo, misurando cosa usciva dallo schermo, cosa
veniva tagliato e cosa si toccava su meno di 24 punti.

- **In piedi il menu si riduce alle icone**, come nelle app di un tablet:
  aperto, prendeva 223 punti dei 768 di un iPad, e alla scheda di una persona
  restava una colonna più stretta di un telefono. Di traverso, e con il mouse,
  resta aperto. Il pulsante «Comprimi» / «Espandi» decide da lì in poi, in
  piedi e di traverso (`AppSidebar.vue`, `menuPiegato`; la vecchia chiave
  scriveva «aperto» per chi non l'aveva mai toccato, e vale solo se era chiuso).
- **L'accoglienza non taglia più i nomi.** Accanto ai pulsanti, i chip
  («Presente», «1 modulo da firmare») riducevano il nome a «C…» o a niente, e i
  minuti d'attesa finivano sotto «Presente». Ora i chip vanno sotto il nome
  quando non c'è posto per tutti e due; con il dito il nome si tocca su 40 punti
  (`Today/ParticipantRow.vue`).
- **La dashboard si impila dove la griglia è stretta**: venti colonne su 545
  punti davano a un numero 93 punti, «66,…» per i ricavi e «R…» per il titolo, e
  a una lista una lettera di ogni nome. Sotto `GRIGLIA_MINIMA` (900 punti) i
  riquadri vanno uno sotto l'altro come sul telefono, tre o quattro numeri per
  riga e gli altri a due a due da 760 punti (`perRiga`); il titolo va su due
  righe e il confronto sotto la variazione (`data-impilata`). Mentre la si
  sistema resta la griglia. I «Apri l'agenda» in fondo alle liste prendono il
  tocco su 44 punti su ogni schermo che si tocca, non solo sul telefono.
- **I tasti della scheda di una persona hanno una colonna ciascuno.** Erano sei
  colonne anche per cinque tasti (senza SMS), e «Chiama» toccava «WhatsApp»,
  anche sul computer; ora le colonne sono quanti i tasti, e una parola troppo
  lunga si accorcia invece di finire sulla vicina (`PersonHeader.vue`).
- **L'agenda in piedi si apre sul giorno**, come sul telefono: la settimana
  accanto al menu dava a ogni giorno 92 punti, cento appuntamenti disegnati
  come «Tratt…» uno sopra l'altro; la settimana è a un tocco. Nell'intestazione
  «Collega Google Calendar» è la sua icona sotto i 1024 punti: con le sue parole
  spingeva fuori «Lista d'attesa» (`pages/Calendar.vue`).
- **La colonna di una scheda è larga come un telefono**, in piedi: 368 punti
  accanto al pannello della persona. Quello che guardava lo schermo e non la
  colonna si schiacciava: i campi dei Dati su tre colonne da 90 punti
  («rita.deang» per l'email), la riga di Moduli con una parola per riga accanto
  ai suoi pulsanti, i tre passi dei Piani da 70 punti, un preventivo su quattro
  righe accanto ai suoi segni, «Programma un evento» tagliato. Ora le colonne di
  campi stanno affiancate dove ognuna ha 11rem (`FieldLayout/Section.vue`,
  `Column.vue`), le parole di una scheda tengono 15rem e i pulsanti vanno sotto
  (`Moduli/FormsArea.vue`, `Plans/PlansCard.vue`), i passi dove ognuno ha 12rem,
  i segni di un preventivo sotto le sue parole (`Quotes/QuotesCard.vue`), e sotto
  i 1024 punti gli Eventi offrono «Appuntamento» ed «Evento»
  (`Activities/ActivityHeader.vue`). Nella Clinica, quando la scheda è più stretta
  di 560 punti, due pulsanti vanno sotto «⋯» come sul telefono, e nella sintesi un
  valore va sotto il suo nome quando il riquadro è più stretto di 28rem
  (`Clinic/ClinicArea.vue`, `ClinicSummary.vue`, con una container query). Sul
  computer non cambia niente.
- **Le note sono quattro per riga dove ci stanno**, meno dove una scheda
  sarebbe più stretta di 13rem: in piedi erano 155 punti, il titolo «Nota di
  pr…» e l'autore e il giorno su tre righe (`pages/Notes.vue`).
- **Una pagina delle Impostazioni segue il suo riquadro, non lo schermo.** In
  piedi, accanto al menu delle Impostazioni, il riquadro è largo 504 punti: un
  telefono, su uno schermo che per `max-md:` è un computer. Su 53 pagine dieci
  si schiacciavano: la descrizione di «Servizi» in una colonna di 108 punti
  accanto ai suoi due pulsanti, le regole di un listino tagliate a «Co…» accanto
  ai listini, l'anteprima di «Pagina e regole» fuori dal riquadro, «Massaggio
  decont…» accanto a «Nessun professionista prenotabile», il titolo «Modelli
  WhatsApp» su due righe sopra la sua descrizione, due campi
  dell'Assistente da 94 punti. Il riquadro ora è una container query
  (`Settings.vue`) e la variante `impostazioni-strette:` (`tailwind.config.js`,
  sotto 40rem) mette in colonna quello che il telefono mette in colonna:
  l'intestazione di ogni pagina con le sue azioni sotto (le 27 pagine che lo
  facevano sul telefono e `Layouts/SettingsLayoutBase.vue`), i listini sopra le
  loro regole con la pagina che scorre tutta insieme, l'anteprima sotto i campi,
  chi può prenotare un servizio sotto il suo nome, gli extra del piano e i campi
  dell'Assistente su una colonna. Il nome di un professionista e il suo titolo
  vanno a capo invece di tagliarsi a vicenda (`Booking/OnlineBookingSetup.vue`).
  Un livello più giù, toccando una voce, l'editor di un modulo mette le sue
  azioni sotto il titolo come sul telefono (`Forms/TemplateBuilder.vue`: il
  segno «Versione 1» era tagliato), le azioni di un'intestazione non restano
  rientrate in un quarto della riga, e nella pipeline il nome di una fase tiene
  10rem con tipo, probabilità e trattative sotto (`Pipelines/PipelineView.vue`:
  era «Qualif»; anche sul telefono). Sul telefono il riquadro è lo schermo, e
  non cambia altro; di traverso e sul computer (760 punti e più) le colonne
  restano affiancate.

- **Niente solo al passaggio del mouse, anche sul tablet.** Il tablet ha la
  pagina del computer ma nessun mouse: quello che compariva solo sotto il
  puntatore restava invisibile. Ora si vede dove niente passa sopra
  (`[@media(hover:none)]`): la fascia con la fotocamera per cambiare la foto di
  un'azienda o di un contatto (`pages/Organization.vue`, `Contact.vue`: non c'è
  un altro modo), il segno di copia accanto al codice della trattativa
  (`pages/Deal.vue`, anche con la tastiera), gli strumenti di un riquadro mentre
  si sistema la dashboard (`Dashboard/DashboardGrid.vue`) e la × che toglie un
  filtro rapido (`ViewControls.vue`). La foto di una persona si cambia anche da
  «Altro», e il «+» di un giorno nel planner dei social è solo un suggerimento:
  si tocca il giorno.

- **Il marketing in piedi.** Nel planner dei social un giorno è largo 97
  punti, e il titolo di un post accanto all'ora era «p…»: sotto i 1280 punti
  il titolo va sotto l'ora (`pages/SocialPlanner.vue`), e «+24 altri» al tocco
  è alto 30 punti. L'editor di un'automazione sotto i 1024 punti mette
  «Statistiche» e «Prova a vuoto» nel menu «⋯», come sul telefono: accanto a
  «Salva» il nome era «Recupero no…» e la via del ritorno «Aut…»
  (`pages/AutomationEditor.vue`).

- **La dashboard si sistema col dito.** In modifica un riquadro non si
  spostava: la griglia (grid-layout-plus) prende un trascinamento solo dove la
  pagina non scorre, e lo dice al browser solo su Android; su un iPad il dito
  faceva scorrere la pagina e il trascinamento si annullava. Ora, al tocco, ogni
  riquadro ha una maniglia «⤧» tra i suoi strumenti, da cui si sposta, e
  l'angolo che lo ridimensiona è di 28 punti invece di 10; il resto del
  riquadro fa scorrere la pagina, come ci si aspetta. Gli strumenti al tocco
  sono di 28 punti (`Dashboard/DashboardGrid.vue`). Col mouse non cambia
  niente: si trascina da tutto il riquadro.

- **Un elenco che si riordina non ruba lo scorrimento.** La kanban parte già
  dopo una breve pressione al tocco; i filtri rapidi, le colonne della kanban,
  i campi di una griglia e gli editor del layout (schede, colonne, sezioni del
  pannello) no, e un dito che scorreva la riga dei filtri o un elenco in un
  dialogo spostava una voce. Ora anche loro aspettano 200 millisecondi al tocco
  (`ViewControls.vue`, `Kanban/KanbanSettings.vue`,
  `Controls/GridFieldsEditorModal.vue`, `FieldLayoutEditor.vue`,
  `SidePanelLayoutEditor.vue`); gli elenchi con una maniglia (fasi della
  pipeline, domande di un modulo) già si prendevano solo da lì. L'attesa vale
  solo per il dito (`delay-on-touch-only`): su un PC con lo schermo tattile,
  come quelli di molte accoglienze, il mouse trascina subito, e prima aspettava
  anche lui, kanban e colonne comprese. Un appuntamento dell'agenda col dito non
  si sposta: lo scorrimento resta dell'agenda, e l'orario si cambia nel suo
  pannello.

Restano com'erano: le caselle per scegliere più righe di una lista (14 punti:
frappe-ui le disegna come `input`, che non tiene un anello, e scegliere più
righe da un tablet è raro) e i riquadri della dashboard di traverso: lì la
griglia è quella che il centro ha sistemato, e un titolo lungo resta tagliato
come su un computer stretto.

## Nona parte: la pagina ingrandita (05/10/2026)

Chi vede poco ingrandisce. Su Android il testo grande delle impostazioni di
sistema ingrandisce tutta la pagina in Chrome: un telefono largo 360 punti al
130% dà alla pagina 277 punti. Su un iPhone lo zoom di Safari («aA») dà 312
punti a un telefono da 390 al 125%. Tra queste persone ci sono molti pazienti
dell'area e qualche collega. Le pagine di ogni giorno, le schede di una
persona, di una trattativa, di un contatto e di un'azienda, la dashboard e
l'area sono state guardate a 320 e a 280 punti: niente esce dallo schermo,
nessuna parola è schiacciata e nessun nome è tagliato sotto i 72 punti.

- **Le schede di una persona o di una trattativa stanno nella barra quante ce
  ne stanno.** Erano sempre quattro più «Altro». A 280 punti erano «Detta…»,
  «Eve…», «Preventi…». Ora la barra misura le parole nel suo carattere e ne
  tiene quante entrano accanto ad «Altro», fino a quattro; le altre vanno in
  «Altro» (`SchedeDelTelefono.vue`, `quanteNellaBarra` in `utils/sulTelefono.js`).
- **Il nome nell'intestazione ha il posto di «Assegna a».** Sul telefono, se
  nessuno è assegnato, il tasto è un'icona tonda come l'avatar che diventa:
  «Assegna a» scritto lasciava a 320 punti «Giulia Bianc…». Il nome del tasto
  resta per chi legge con la voce, ed è il titolo del foglio che apre
  (`AssignTo.vue`).
- **Il nome si legge intero, i chip vanno sotto.** Nell'agenda del giorno
  «Completato» e «Prima visita» stavano in una colonna a destra e lasciavano
  «Frances…»; nella lista d'attesa «Urgente» e «Posto proposto» lasciavano
  «Giov…»; nei contatti di una trattativa «Primario» lasciava «Silvi…». Ora i
  chip stanno accanto al nome finché c'è posto, sotto quando non c'è
  (`AgendaDelGiorno.vue`, `WaitingList.vue`, `MobileDeal.vue`).
- **I tasti di una persona prendono la larghezza della loro parola.** A 320
  punti, o con sei tasti su un iPhone SE, «WhatsApp» era «WhatsA…». Le colonne
  restano uguali finché ogni parola ci sta; quella che non ci sta prende i
  pochi punti che le servono dalle altre (`PersonHeader.vue`,
  `minmax(min-content, 1fr)`).
- **L'avviso di WhatsApp va su due righe invece di tagliarsi.** Era «Non ha mai
  scritto: solo un m…»: dove la riga non basta, le parole vanno a capo
  (`WhatsAppBox.vue`).
- **La dashboard mette un numero per riga** dove due sarebbero sotto i 136 punti
  l'uno: i titoli erano «Trattati… vinte» (`perRiga` in `utils/dashboard.js`).
- **Le etichette dei campi vanno fino a tre righe**: in due,
  «Responsabile della…» (`SidePanelLayout.vue`).

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
| `frontend/src/pages/Today.vue`, `components/Today/ParticipantRow.vue`, `utils/oggi.js` (`firstOfPast`) | L'accoglienza sul telefono |
| `frontend/src/components/ViewBreadcrumbs.vue` | Tre pagine sorelle sul telefono: la pagina aperta è il titolo, le altre nel suo menu |
| `frontend/src/pages/MobileOrganization.vue`, `MobileContact.vue` | Le trattative e i contatti di un'azienda e di un contatto, per nome della scheda |
| `frontend/tests/unit/automationParole.test.js` | Ogni parola del catalogo delle automazioni ha il suo italiano, nessuna nomina un altro prodotto |
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
| `frontend/src/composables/breakpoints.js` (`isPhoneSize`) + `telefono.css` sezione 10 | Il telefono tenuto di traverso resta un telefono, la scheda e la barra compatte. Testato in `tests/unit/breakpoints.test.js` |
| `frontend/src/utils/scheduler.js` (`orariPerGiorno`) + `components/Calendar/AppointmentPanel.vue` | Gli orari liberi di un servizio un giorno alla volta, i primi dodici e «altri N». Testato in `tests/unit/scheduler.test.js` |
| `frontend/src/composables/testataRaccolta.js` + `pages/MobileLead.vue` | La scheda della persona si raccoglie mentre la scheda sotto scorre, e torna in cima (`raccogliereLaTestata`); la raccoglie solo chi scorre (un dito, la rotella, un tasto, o la tastiera aperta), non la storia che si apre da sola sul giorno più recente. Testato in `tests/unit/testataRaccolta.test.js` |
| `frontend/src/composables/scorriGiorni.js` + `components/Mobile/AgendaDelGiorno.vue`, `pages/Today.vue` | Il giorno (e la settimana) dell'agenda e il giorno dell'accoglienza si sfogliano di lato (`direzioneDelGesto`). Testato in `tests/unit/scorriGiorni.test.js` |
| `frontend/src/utils/installa.js` + `components/Mobile/InstallaApp.vue` | L'app sulla schermata Home: cosa propone «Altro» (`comeInstallare`), l'offerta del browser tenuta per il pulsante. Testato in `tests/unit/installa.test.js` |
| `frontend/src/utils/schedaAttiva.js` | La scheda della barra su cui si è, toccata di nuovo, porta la pagina in cima; una pagina può fare prima altro (`alToccoDellaScheda`: una chat aperta torna all'elenco). Testato in `tests/unit/schedaAttiva.test.js` |
| `frontend/src/utils/trascinaFoglio.js` | Un foglio preso per la maniglia segue il dito; lasciato abbastanza giù, o con un colpo, si chiude, se no torna su (`siChiude`). Testato in `tests/unit/trascinaFoglio.test.js` |
| `frontend/src/utils/ritorno.js` + `composables/ritorno.js`, `composables/elencoDelTelefono.js` | Una lista ritrovata com'era tornando indietro (`useRitorno`: le parole cercate, le righe, il punto, poi aggiornata); le cinque liste che si cercano (persone, contatti, aziende, chiamate, note) scritte una volta sola in `useElencoDelTelefono`. Testato in `tests/unit/ritorno.test.js` e `elencoDelTelefono.test.js` |
| `frontend/src/composables/tiraPerAggiornare.js` + `components/Mobile/TiraPerAggiornare.vue`, le liste di `components/Mobile/`, `Conversations/ConversationPicker.vue`, `Notifications/NotificationsList.vue`, `EventNotificationsArea.vue`, `pages/Invoices.vue`, `Today.vue`, `WaitingList.vue`, `Dashboard.vue` | Una lista tirata giù dalla cima si ricarica; il gesto segue la scatola che scorre anche quando compare dopo. Testato in `tests/unit/tiraPerAggiornare.test.js` |
| `frontend/src/components/SenzaRete.vue` | La riga che dice che manca la rete, sul telefono e sul computer |
| `frontend/src/utils/indietro.js` + `components/Layouts/MobileLayout.vue`, `pages/Calendar.vue`, `components/Settings/Settings.vue`, `pages/Conversations.vue`, `area/App.vue` | «Indietro» chiude foglio, menu o pannello prima di lasciare la pagina. Testato in `tests/unit/indietro.test.js` |
| `frontend/src/utils/tastieraAperta.js` + `components/Layouts/MobileLayout.vue`, `area/App.vue`, `telefono.css` (8, 9), `area/area.css` | La cornice che segue la tastiera, il tocco da app. Testato in `tests/unit/tastieraAperta.test.js` |
| `frontend/src/utils/tastiera.js` + `FieldLayout/Field.vue`, `SidePanelLayout.vue`, `BillingProfileSection.vue`, `Invoices/InvoiceDialog.vue`, `Calendar/AppointmentPanel.vue`, `Telephony/CallUI.vue`, le impostazioni | La tastiera di ogni campo. Testato in `tests/unit/tastiera.test.js` |
| `frontend/src/components/Invoices/InvoiceDialog.vue`, `pages/Invoices.vue` + `crm/invoicing/emissione.py` | La fattura sul telefono: il «+» della pagina, ogni riga una scheda con le sue etichette e il totale a destra, la riga aggiunta che viene in vista, la fattura che si apre toccandola; le note del motore nella lingua di chi legge |
| `frontend/src/pages/FormFill.vue` + `telefono.css` (un pulsante d'icona resta quadrato) | Le azioni di un modulo in una riga: «⋯» (gli altri modi di firmare, Scarta), Salva per dopo, Firma e concludi |
| `frontend/src/components/Activities/TaskArea.vue`, `Clinic/ClinicArea.vue`, `SidePanelLayout.vue`, `espresso.css` (7) | Una cosa da fare con il giorno e la priorità su una riga loro; l'intestazione della Clinica che va a capo; la crocetta dei campi obbligatori accanto alle parole |
| `frontend/src/components/Activities/emailContent.css` | Un'email nel tema scuro: il suo riquadro dice anche lui `color-scheme: dark`, o il browser gli mette dietro il bianco |
| `frontend/src/pages/SocialPlanner.vue` | Il nuovo post è il «+», i profili l'ingranaggio |
| `frontend/src/components/BillingProfileSection.vue` + `utils/locale.js` (`inFrase`), `utils/paesi.js`, `telefono.css` (2) | I dati di fatturazione: «Aggiungi codice fiscale…» come i campi sopra, il paese per nome («Italia», da cercare) salvato con le sue due lettere, un campo più lungo della sua casella che finisce in «…». Testato in `tests/unit/locale.test.js` e `paesi.test.js` |
| `frontend/src/components/AssignTo.vue`, `AssignToBody.vue`, `MultipleAvatar.vue` | «Assegna a» è un foglio dal basso (si salva chiudendolo, come la scheda sul computer); nella testata solo la faccia di chi segue la persona, così il suo nome resta intero |
| 72 componenti e pagine (`:aria-label`) | Ogni pulsante fatto solo di un'icona dice cosa fa: chiudere, rimuovere, le opzioni di una riga, il giorno o il mese prima e dopo, il microfono di una chiamata. VoiceOver e TalkBack leggevano «pulsante» |
| `frontend/src/pages/SocialPlanner.vue` (telefono) | I post del mese sono righe da 44px, non le etichette da 26px della griglia |
| `frontend/src/telefono.css` (2: `[data-slot='tab-button']`), `components/Mobile/ElencoCose.vue` | Gli interruttori a segmenti («Tutte · Da leggere», «Mie · Di tutti», «Appuntamento · Evento», le pagine sorelle) alti 36px e non 26; una cosa da fare si apre toccando tutta la sua riga, non solo la riga di parole |
| `frontend/src/telefono.css` (2: `[data-slot='fixed-menu'] button`) | I pulsanti della barra di un editor (grassetto, elenchi, collegamento) di 36px sul telefono, non 24 |
| `frontend/index.html`, `crm/www/book*.html` | La pagina dice la lingua di chi la usa (`boot.lang`), non «en»: VoiceOver e TalkBack leggevano le parole italiane con una voce inglese, e il browser non sapeva dove andare a capo |
| `frontend/src/components/Dashboard/WidgetFrame.vue` | Il titolo di un numero va a capo dove va a capo l'italiano; la ⓘ che si apre solo passandoci sopra non c'è su un telefono, e lascia il posto al titolo («Appuntamenti di oggi», non «Appuntam…») |
| `frontend/src/area/area.css` | Nell'area del cliente ogni campo è di 16px sul telefono, come nel resto di DottorCloud: la domanda della chat era di 14px e l'iPhone ingrandiva la pagina toccandola |
| `App.vue` + `utils/menu.js` (`titoloDellaPagina`), le schede | Ogni pagina ha il suo titolo per VoiceOver e TalkBack, che saltano da un titolo all'altro: sul telefono il nome della pagina è un link o un interruttore in alto, mai un titolo, e 9 pagine su 13 non ne avevano nessuno. Una scheda ha per titolo il suo nome (persona, trattativa, azienda, contatto) |
| `frontend/vite/frappeUi.js` (`Dialog/Dialog.vue`) | Una finestra si legge col suo nome («Aggiungi una persona», «Nuova cosa da fare»): una che disegna il proprio corpo non aveva titolo collegato, e VoiceOver diceva solo «finestra di dialogo». Il suo primo titolo la nomina, altrimenti il titolo che le è dato; la × dice «Chiudi», non «Close» |
| `pages/Calendar.vue`, `Calendar/AppointmentPanel.vue`, `CalendarEventPanel.vue` | Il pannello dell'agenda, che sul telefono copre la pagina, prende lo stato attivo sul suo titolo quando si apre («Nuovo appuntamento») e lo rende a «Nuovo» quando si chiude (o al titolo della pagina, se quel pulsante è stato ridisegnato). Il ritorno ai dettagli di un evento è un pulsante, non un riquadro cliccabile |
| `frontend/index.html` | Due dita ingrandiscono la pagina, come in ogni sito: chi vede poco ne ha bisogno, e iOS lo permetteva comunque. Lo impediva `user-scalable=no`, nato per evitare che l'iPhone ingrandisse da solo un campo toccato: ora i campi sono di 16px sul telefono e non succede più |
| `Layouts/MobileLayout.vue`, `DesktopLayout.vue`, `vite/frappeUi.js` (`Toast/ToastProvider.vue`) | La pagina ha la sua zona principale (`main`), dove VoiceOver e TalkBack saltano al contenuto; la zona degli avvisi si chiama «Notifiche», non «Notifications alt+T», e la × di un avviso dice «Chiudi», non «Close toast» |
| `FieldLayout/Field.vue`, `SidePanelLayout.vue`, `Controls/Grid.vue` | Il primo caricamento di ogni pagina scende da 866 a 575 KB compressi (da 3,6 a 2,6 MB): l'editor di testo (TipTap, ProseMirror, 39 linguaggi di highlight.js, markdown) entrava all'avvio perché un campo lo importava subito; ora arriva quando un campo lo disegna |
| `frontend/src/components/Conversations/ConversationPicker.vue` | In cima alla chat la vista («Aperte») e il filtro «Da leggere» alti 36px |
| `frontend/src/components/PersonHeader.vue` | Sotto il nome, «Paziente dal…» e «Ultima visita…» vanno a capo senza che la seconda riga cominci con «·» |
| `frontend/src/components/RelatedPeopleSection.vue` | Collegare una persona: «Già in DottorCloud» e «Una persona nuova» le due metà di un interruttore solo, non due pulsanti uno sotto l'altro |
| `frontend/vite/frappeUi.js` (`Switch/Switch.vue`) | Un interruttore legato a un campo sì/no del server (0 o 1) si accendeva solo per `true`: «Aggiorna la data di modifica», salvato acceso, si vedeva spento. Ora 1 è acceso. E il nome dato all'interruttore va al suo pulsante, dove VoiceOver e TalkBack lo leggono, non al contenitore |
| `Settings/SettingsRow.vue`, `Telephony/SettingRow.vue` + `composables/nomeAlControllo.js` | Le parole di una riga delle impostazioni sono l'etichetta del suo interruttore (o campo): lo nominano, e toccarle lo accende o lo spegne |
| 31 pagine e finestre (Generale, Dashboard, Sito, Regole di assegnazione, SLA, Modelli email, Meta, profili social, prenotazione online, agenda…) | Ogni interruttore ha un nome: le parole che ha accanto, o in un elenco il nome della riga («Pagina Studio», «Dottoressa Verdi»), mai solo «interruttore» |
| `FieldLayout/Field.vue`, `SidePanelLayout.vue` + `composables/nomeAlControllo.js` | Le parole di un campo gli danno il nome, nelle finestre («Nuova persona», «Nuova trattativa») e nel pannello della scheda: un menu a tendina («Stato», «Pipeline», «N. di dipendenti») si leggeva senza nome, una data «Scegli la data». Un pulsante o un menu si legge con quello che mostra («Responsabile della trattativa, Sarah Connor»), uno vuoto una volta sola, e l'avatar accanto al nome non si legge più |
| `CommentBox.vue`, `EmailEditor.vue` | Il riquadro dove si scrive una nota o un'email si chiama come il suo invito («Scrivi un'email…»): il segnaposto si disegna, non si legge |
| `Activities/ChatBubble.vue`, `HappenedCard.vue` | Quello che le spunte di un messaggio dicono passandoci sopra («Letto», «Consegnato al telefono»), e «Inviato dal telefono», ora si legge anche con VoiceOver e TalkBack: un telefono non ha il passaggio del mouse. Le icone accanto alle parole non si leggono come «immagine» |
| Impostazioni: Generale, Dashboard, Agenda e promemoria, Utenti, Modelli email, Pagina e regole, La tua email | Ogni campo ha un nome (lo controlla l'albero di accessibilità di Chrome su tutte le 53 pagine): i menu («Ordine delle attività», «Vista predefinita», i promemoria «Tipo», «Quanto prima», «Unità»), il filtro «Livelli», il menu «Opzioni» di un utente o di un modello, i numeri delle regole della prenotazione, la firma |
| 55 file (stati vuoti, suggerimenti, «Nessun titolo», le regole della prenotazione, le automazioni, la chiamata…) | Nessuna parola nel grigio più chiaro (`ink-gray-4`, 2,83:1 sul bianco: al sole non si legge): passano al quinto (4,99:1 sul bianco, 5,21:1 sul fondo scuro). Il quarto resta alle icone che accompagnano, ai separatori e a uno spinner |
| `Settings/Profile/ProfileSettings.vue` | La foto del profilo si cambia e si toglie con due pulsanti veri, con il loro nome («Cambia la foto», «Rimuovi la foto»); la × di 16px ha l'anello che la fa prendere al dito |
| `frontend/src/area/area.css` | Nell'area del cliente «Esci» e «Non ora» (28px) hanno l'anello invisibile che li fa prendere al dito, come i pulsanti piccoli del resto di DottorCloud: l'area non carica `telefono.css` |
| `Settings/Settings.vue`, `Modals/GlobalModals.vue`, `DoctypeModals.vue`, `FieldLayoutDialogContainer.vue` + `utils/aRichiesta.js` | Quello che si apre ogni tanto arriva quando si apre: ogni pagina delle impostazioni (con l'editor di testo, il QR e la telefonia), le finestre di un record, della fattura e dei moduli. Misurato a freddo su un telefono, compresso: l'accoglienza scende da 1437 a 767 KB, l'elenco delle persone da 1506 a 909, l'agenda da 1482 a 829, «Altro» da 1435 a 749. Una pagina delle impostazioni lenta mostra la croce del marchio |
| `Activities/Activities.vue`, `IconPicker.vue`, `AttachmentItem.vue` + `utils/tipoDelFile.js` | La scheda di una persona porta solo la conversazione: ogni altra scheda (Clinica, Piani, Documenti, Preventivi, Moduli, Area, Eventi, Tracciamento) arriva quando la si apre; la casella dell'email e delle note la prima volta che serve, come WhatsApp e SMS («Rispondi» su un'email la apre e risponde appena c'è); le 1870 emoji quando si apre il selettore; l'icona di un allegato dal nome del file, senza il database dei tipi (e un .xls, un .xlsm o un .csv ora hanno l'icona del foglio di calcolo). Una persona che scrive su WhatsApp: da 1385 a 990 KB |
| `RichTextField.vue` + `editor/RichTextEditor.vue`, `Modals/EditValueModal.vue` | Un campo di testo formattato (la descrizione di un evento, la firma, il compito di una chiamata) carica l'editor quando si disegna, e la modifica di più righe di un elenco quando si sceglie un campo di testo |
| `Telephony/TwilioCallUI.vue`, `utils/index.js` (`isEmoji`) | L'SDK voce di Twilio arriva solo dove c'è una linea per telefonare; l'icona di una vista si riconosce come emoji dalle proprietà Unicode, non cercandola ogni volta in un elenco di 1870 |
| `frontend/vite.config.js` | `vuedraggable` è pubblicato solo come CommonJS e chiede `vue`: portava nel primo download il compilatore dei template di Vue, che nessuno usa. Ora si prende dai suoi sorgenti ES; e un solo Sortable per lui e per l'ordinamento di un elenco |
| `frontend/vite.config.js` (`VitePWA`) | Il service worker registrato su `/assets/crm/frontend/` non serviva nessuna pagina (stanno sotto `/crm`), e alla prima visita e a ogni nuova versione scaricava in sottofondo tutta l'app: 392 file, 7,6 MB. Ora si toglie da solo, con quello che aveva tenuto, anche dai telefoni che lo hanno già |
| `utils/ricarica.js`, `main.js` | Uscita una versione nuova con la pagina aperta, un pezzo che non c'è più ricarica la pagina una volta, invece di lasciare un pulsante che non apre niente. Mai senza rete, mai in giro, e mai per un modulo di un altro sito che non arriva (la telemetria del framework bloccata dal browser) |
| `Activities/EmailArea.vue`, `MessageActions.vue` | Il pulsante che risponde a un'email o a un messaggio dice «Rispondi», non «Risposta» |
| `crm/www/crm.py` (`traduzioni`), `frontend/index.html` | Le parole dell'italiano (15.000, 1,2 MB, 380 KB compressi) non stanno più dentro la pagina, che nessun browser tiene e che si scarica a ogni apertura dell'app: sono uno script che il browser tiene finché non cambiano (il suo indirizzo porta un'impronta delle parole). La pagina scende da 1266 a 26 KB; dalla seconda apertura le parole costano 0 byte |
| `src/carattere.css` + `src/assets/fonts/` | Il carattere è Inter come prima (gli stessi assi di peso e di dimensione ottica, le stesse cifre), ridotto agli alfabeti latini e ai segni che le parole usano: 131 KB invece di 264, scaricati la prima volta da ogni telefono e da ogni paziente (l'area scende da 509 a 381 KB compressi). Le facce di frappe-ui lasciavano fuori la punteggiatura: l'apostrofo tipografico (dell’area), le virgolette, le lineette, i puntini e l'euro si disegnavano con il carattere del telefono, ora con Inter. Una lettera greca o cirillica arriva ancora dal file intero |
| `frontend/vite/frappeUi.js` (il blocco di codice, le emoji, il Markdown) | L'editor di testo, che arriva quando si scrive un'email, una nota o un campo di testo, scende da 296 a 204 KB compressi. Il blocco di codice (``` in una nota) non porta più highlight.js con i suoi 37 linguaggi: il testo resta com'è scritto, senza un selettore di linguaggi che non farebbe nulla; il suo pulsante dice «Copia il codice». Le emoji dopo «:» (16 KB) arrivano la prima volta che qualcuno le chiede. Il Markdown come formato dell'editor (e la sua copia di marked) non serve a nessuno qui; il testo in Markdown incollato diventa ancora grassetto ed elenchi. Dal blocco di codice si esce di nuovo con tre Invio o con la freccia giù: frappe-ui sostituiva i tasti di TipTap invece di aggiungersi, e chi scriveva ``` per sbaglio restava dentro, sul telefono senza via d'uscita |
| `frontend/vite/precarica.js` | Quando un pezzo dell'app ne apre un altro, Vite gli dava l'elenco di tutto quello che serve, compreso quello già caricato (Vue, frappe-ui, il router); il suo aiutante, per ogni voce mai vista, scorre tutti i `<link>` della pagina (le immagini d'avvio dell'iPhone, i precaricamenti) e ne aggiunge uno. Ora l'elenco tiene solo quello che manca: non quello che il pezzo che chiama importa, né quello che importa l'ingresso dell'app, che il browser ha già caricato prima che parta qualsiasi `import()`. Le tabelle delle dipendenze scendono da 30 a 17 KB, la lista più lunga da 180 a 123 voci |
| `crm/www/crm.py` (`crm_user`, `benvenuto`, che era `ask_persona`), `router.js`, `stores/users.js`, `pages/Today.vue` | Su un telefono lento (processore 4 volte più lento, 150 ms di latenza) la prima pagina aspettava tre chiamate in fila: la lista degli utenti, per sapere se chi entra usa DottorCloud (lo dice già la pagina, che si apre solo a loro); per chi gestisce il centro, le domande della prima configurazione, due chiamate a ogni apertura per scoprire che non servono (servono solo dove la telemetria del framework è accesa: lo calcola il server); e l'accoglienza chiedeva cosa resta da fatturare solo dopo la giornata. Ora la pagina porta le due risposte e l'accoglienza chiede le due cose insieme: i suoi dati partono circa mezzo secondo prima (321 ms dall'avvio invece di 818), l'elemento più grande si disegna a 1,5 s invece di 1,9. Un utente chiesto prima che la lista arrivi aspetta la lista, invece di una chiamata per ogni nome; e la lista completa, che il server dà solo all'agenzia, la chiede solo lei: per gli altri era una seconda chiamata con gli stessi utenti a ogni apertura |
| `Activities/CallArea.vue`, `data/script.js`, `utils/callLog.js` | La scheda di una persona faceva 36 chiamate per aprirsi, ora 28: ogni telefonata della conversazione chiedeva subito i suoi dettagli, e la finestra dei dettagli, montata chiusa, apriva la telefonata come documento (contenuto, permessi, assegnatari, script, campi): sei chiamate per telefonata, sessanta con dieci telefonate. Ora i dettagli si chiedono quando si aprono o quando si ascolta la registrazione, e la finestra si monta alla prima apertura. Gli script della scheda si chiedevano tre volte (il controllo guardava uno stato che una lista non ha) e di nuovo a ogni persona aperta, quando non ce ne sono; i campi delle telefonate si chiedevano appena si disegnava il colore di una telefonata |
| `pages/MobileLead.vue`, `MobileDeal.vue`, `App.vue`, `Activities/Activities.vue` | Una scheda di una persona o di una trattativa si cambia subito. Ogni tocco smontava la scheda lasciata e montava la nuova, la conversazione e il suo editor compresi, e quello che si leggeva tornava in cima: ora i Dettagli e la conversazione, che disegna tutte le altre schede, si montano la prima volta che si aprono e poi restano. Con il processore 4 volte più lento, dal tocco al disegno: i Dettagli la prima volta da 1168 a 528 ms, le volte dopo 88; tornare ad Attività da 592 a 120; Eventi da 424 a 112; Attività da Eventi da circa 600 a 208. E la pagina non si rimonta più a ogni scheda, sul telefono e sul computer: dopo il `#` l'indirizzo nomina la scheda, non un'altra pagina |
| `composables/useActiveTabManager.js`, `Activities/Activities.vue`, `ConversationView.vue` | Il link di una notifica a un messaggio (una menzione, un WhatsApp, un SMS, un'email) apre la conversazione e si ferma sul messaggio anche sul telefono: lì la prima scheda è Dettagli, e un indirizzo che nomina un messaggio, non una scheda, apriva quella, dove il messaggio non c'era. Un'email non portava il suo nome come `id`, e la notifica di un'email non ci arrivava su nessun dispositivo. Con la persona già aperta il link si segue senza riaprire la pagina |
| `src/telefono.css` (6), `tailwind.config.js` | Un menu si apre prima. La regola che porta in alto gli avvisi sopra un foglio aperto cercava il foglio in tutta la pagina (9.000 elementi su una persona) a ogni `data-state` che cambiava ovunque: una scheda, un menu, un suggerimento. Ora lo cerca lungo la strada che il foglio fa sempre, dal `body` in giù. E Tailwind costruiva due misure del testo formattato che nessuno disegna (`prose-xl`, `prose-2xl`), 84 regole che il browser prova su ogni elemento quando ne calcola lo stile. Con il processore 4 volte più lento, il menu «Nuovo» di una persona si apre in 240 ms invece di 304, una scheda in 152 invece di 176 (mediane, le regole vecchie e nuove a turno sulla stessa pagina) |
| `Controls/Link.vue`, `frappe-ui/Autocomplete.vue` | Un campo che si sceglie da un elenco (genere, fonte, azienda, territorio, settore…) chiede le sue scelte quando lo si apre, non quando si disegna. I dettagli di una persona chiedevano al server sette elenchi, ciascuno due volte, prima che qualcuno ne aprisse uno: il primo tocco su Dettagli faceva 23 richieste, ora 8. Mentre le scelte arrivano l'elenco dice «Caricamento…», non «Nessun risultato». Il nome di un valore che si mostra col suo titolo (una lingua, una qualifica) si chiede da solo, una volta per tutta l'app |
| `composables/useActiveTabManager.js` | L'indirizzo segue la scheda dopo che la scheda si è disegnata. Scriverlo legge lo scorrimento della pagina, per tenerlo nella cronologia, e letto nel mezzo del tocco costringeva il browser a impaginare la pagina una volta di più prima di disegnare la scheda. Cambiare scheda: da 104 a 88 ms (mediane di 32 tocchi, a turno sulla stessa pagina); l'indirizzo arriva un fotogramma dopo, e una scheda già lasciata non si scrive |
| `utils/icone.js`, `components/Icon.vue`, `ScegliIcona.vue`, `main.js` | Le icone disegnate per nome entrano nella pagina una per una. Il plugin di frappe-ui ci metteva all'avvio tutte le 1.737 icone di Lucide: 82 KB compressi nel primo download di ogni pagina (l'ingresso dell'app pesava 111 KB, ora 28), 130 ms per costruirle su un telefono lento, e 8.673 elementi nascosti, nove su dieci di quelli della pagina di una persona (ora sono 704 in tutto), che il browser attraversava ogni volta che qualcosa cercava nella pagina. Le schermate di ogni giorno ne disegnano cinque. Ora le icone arrivano quando l'app è ferma, o quando un'icona le chiede, e la pagina tiene solo quelle disegnate; il selettore delle icone (di una vista, di una dashboard) le mette tutte quando si apre, per sceglierne una |
| `vite/frappeUi.js` (`icons/IconPicker.vue`) | Il selettore delle icone parla italiano: «Scegli un'icona...», «Nessuna icona per «…»», «Nessuna icona disponibile.» |
| `App.vue`, `router.js` (`segueLaQuery`), `pages/Dashboard.vue`, `pages/Calendar.vue` | Una pagina che segue da sé la sua query non si rifà quando la query cambia. La dashboard scriveva `?d=` aprendosi, si rifaceva e chiedeva tutto due volte: l'elenco delle dashboard, la disposizione, i dati di ogni widget (6 chiamate, ora 4); e passando a un'altra la apriva due volte. Le conversazioni rifacevano la pagina a ogni conversazione scelta: l'elenco chiesto di nuovo, lo scorrimento perso; ora l'elenco resta, anche tornando indietro sul telefono. L'agenda chiedeva da sola tutti gli eventi aperti del centro, fino a 9.999, prima di quelli del giorno o della settimana che mostra: ora solo questi; e sul computer chiedeva due volte gli appuntamenti della settimana, all'apertura e quando la griglia diceva il suo intervallo |
| `utils/expressions.js`, `utils/paesi.js`, `SidePanelLayout.vue` | Il pannello dei dettagli non rifà a ogni modifica quello che non cambia. A ogni valore scritto ridisegna tutti i campi, e per ciascuno ricompilava le sue condizioni (quando si vede, quando è obbligatorio, quando si scrive), rifaceva la lista degli utenti che un campo utente può nominare, e un campo del paese chiedeva di nuovo al browser i nomi di 676 codici. Ora una condizione si compila una volta, la lista degli utenti si fa una volta per il pannello e i paesi una volta per lingua (ogni campo ne riceve una copia sua). Sulla prima apertura la differenza non si misura |
| `components/DopoIlDisegno.vue`, `pages/MobileLead.vue` | Le sezioni sotto i campi dei Dettagli di una persona (dati di fatturazione, persone collegate, paziente, cicli, abbonamenti, lista d'attesa, consensi) arrivano appena i campi sono disegnati, quando il telefono è fermo, non nel primo tocco su Dettagli: stanno una schermata e più sotto, e chiedevano sette chiamate prima di disegnare la scheda. Il primo tocco su Dettagli scende da 360 a 288 ms (mediane di 10 tocchi per lato, a turno sulla stessa pagina, processore 4 volte più lento); chi scorre le trova già lì |
| `utils/puntatore.js`, `vite/frappeUi.js` (`Tooltip.vue`, `Button.vue`) | Sul telefono un suggerimento (il riquadro che spiega un'etichetta o un pulsante) non si apre mai: si apre quando un puntatore si posa sopra, e un dito non si posa. Eppure ciascuno montava una dozzina di componenti che non mostravano niente: sulla pagina di una persona erano due terzi di tutti. Ora, dove nessun puntatore si posa, un suggerimento è solo quello che lo apre; con un mouse, un trackpad o una penna tornano. Le Attività di una persona scendono da 997 componenti a 344, i Dettagli da 768 a 502, la dashboard da 709 a 373. Con il processore 4 volte più lento, aprire una persona dall'elenco fino alle schede disegnate passa da 1755 a 1646 ms, il primo tocco su Dettagli da 344 a 304 (mediane, a turno sulla stessa pagina) |
| `vite/frappeUi.js` (`Dialog.vue`, `Dropdown.vue`) | Una finestra o un menu si monta quando si apre la prima volta, non con la pagina. Chiusi non disegnavano niente, ma ogni finestra portava sette componenti e ogni menu sei: quattro finestre in ogni pagina, undici nei Dettagli di una persona, cinque menu nelle sue Attività. Dalla prima apertura restano, e si chiudono con la loro animazione come prima. Con i suggerimenti, sul telefono: l'accoglienza scende da 193 componenti a 131, l'agenda da 261 a 185, le persone da 207 a 151, le Attività di una persona da 997 a 265, i Dettagli da 768 a 407, la dashboard da 709 a 313 |
| `composables/testataRaccolta.js` | La testata di una persona non si raccoglie più da sola tornando alle Attività. Toccata la scheda, la conversazione va all'ultimo messaggio in due passi, e il secondo, pochi pixel mentre quello che contiene si assesta, cadeva nel secondo e mezzo dopo un gesto: sembrava che qualcuno avesse scorso, e la testata spariva con Chiama, WhatsApp e Prenota. Ora contano solo i gesti che muovono la pagina: un dito che scorre, la rotella, i tasti che scorrono; non un tocco, né Esc che chiude un menu |
| `crm/api/doc.py`, `crm/automation/engine.py`, `DeleteLinkedDocModal.vue`, `ListViews/LinkedDocsListView.vue`, `utils/collegati.js` | Eliminare una persona: la finestra dei documenti collegati elencava, quasi per tutti, le iscrizioni alle automazioni col loro codice («AENR-00052»), da scollegare o eliminare a mano. Ora un'iscrizione se ne va con la persona o con la trattativa, come le sue attese, e la finestra non la propone. Nessuna riga porta un codice: il suo nome, o quello che è («Trattativa»). Le intestazioni dicono «Documento» e «Tipo», il tipo in italiano («Cosa da fare», non «Task»), e sul telefono sta sotto il nome. Il collegamento c'è solo dove c'è una pagina (una trattativa, un appuntamento nell'agenda): apriva `/crm//`, o una lista senza la cosa. La domanda nomina chi si elimina, «Vuoi eliminare Chiara Rossi?», non «CRM Lead - CRM-LEAD-…» |
| `CommunicationArea.vue` | Il compositore di una persona fa l'editor della nota quando la nota si apre, e quello dell'email quando si apre l'email; poi restano. Li faceva tutti e due con la pagina, anche quando nessuno scrive una nota: due editor di testo, il più pesante di quello che la pagina disegna. Con il processore 4 volte più lento, aprire una persona dall'elenco fino alle schede disegnate passa da 1258 a 1144 ms (mediane di 8, a turno sulla stessa pagina; la mattina erano 1755). «Rispondi» con la nota aperta porta l'email con la sua citazione, e la nota resta com'era |
| `vite/frappeUi.js` (`editor/EditorTableMenu.vue`) | La barra di una tabella (righe, colonne, unire, dividere) costruisce i suoi pulsanti la prima volta che il cursore entra in una tabella. Nascosta fuori da una tabella, li costruiva con ogni editor: 23 componenti della pagina di una persona, per un'email in cui nessuno mette una tabella. Con il processore 4 volte più lento, aprire una persona fino alle schede passa da 1239 a 1149 ms e il lavoro nei primi 3 secondi da 960 a 889 (mediane di 12, a turno sulla stessa pagina) |
| `Calendar/MultiSelectFilter.vue`, `src/telefono.css` (5) | I filtri dell'agenda (servizi, professionisti, ambulatori, stato, sorgente) si aprono come un foglio dal basso, con righe di 48 px e scritte a 16 px: erano un riquadro sotto il pulsante, con righe di 30 px. Un elenco di scelte dentro un riquadro lo dice con `data-foglio`, e sul telefono è un foglio come un menu |
| `crm/install.py` (`LEAD_QUICK_ENTRY`, `DEAL_QUICK_ENTRY`, `LEAD_DATA_FIELDS`), `patches/v1_0/the_person_reads_in_order_on_a_phone.py`, `Modals/DealModal.vue` | Una persona si legge in ordine anche sul telefono, che legge una sezione colonna per colonna. «Aggiungi una persona», e la persona di «Crea una trattativa»: Titolo, Nome, Cognome, poi Cellulare, Email, Genere; erano una sezione di tre colonne da due campi, letta «Titolo, E-mail, Nome, Cellulare, Cognome, Genere», ora ogni riga è una sezione sua, e «Scegli una persona esistente» nasconde le due righe. La scheda Dati: una colonna per tipo (il nome, come raggiungerla, il resto), letta come il pannello a lato; era «Nome, Cellulare, Titolo, Cognome…». La patch cambia solo la sezione rimasta com'era |
| `utils/conversation.js` (`hidesTheNew`), `Activities/Activities.vue` | Una conversazione aperta dalle Conversazioni mostra i messaggi nuovi anche quando il canale letto per ultimo, su un'altra persona, li nasconderebbe: lasciata sulle note, si apriva su «Ancora nessuna nota su questa persona» con un'email da leggere. Si apre su tutti i canali |
| `pages/Lead.vue`, `MobileLead.vue` | In «Altro» della persona, «Copia il link» al posto di «Copia il codice»: l'indirizzo della scheda, da mandare a un collega. Il codice non diceva niente a nessuno |
| `utils/invoicing.js`, `pages/Invoices.vue` | Gli stati del Sistema TS: «Nel file da caricare» al posto di «Pronto export», «Esito PA» al posto di «Esito pa». L'anno resta su una riga accanto alla sua scelta (era «Anno» sopra «2026») |
| `crm/tessera_sanitaria/trasporto.py` | «Comunica» senza tutte le credenziali del Sistema TS dice che mancano, invece di «Internal Server Error»: le credenziali si leggevano fuori da quello che trasforma gli errori dell'invio in un messaggio |
| `Waiting/WaitingDialog.vue`, `crm/locale/it.po` | Le parole del glossario (doc 40): una cosa da fare è «Cosa da fare» (era «Attività», come la scheda della conversazione), un'email «Email» (era «E-mail»). «Proposte via email», «su WhatsApp», «via SMS» sono tre frasi intere, non una parola incollata |
| `utils/index.js` (`taskStatusOptions`, `taskPriorityOptions`) | Il menu dello stato di una cosa da fare, nella scheda Da fare di una persona e nel pannello di una chiamata, parla italiano: «In sospeso, Da fare, In corso, Fatto, Annullata». Diceva «Backlog, Todo, In Progress, Done, Canceled» |
| `Waiting/WaitingDialog.vue`, `Settings/Users.vue`, `Settings/EmailTemplate/EmailTemplates.vue` | Frasi intere anche per una proposta inviata («inviata via email», «Proposta inviata su WhatsApp») e per due elenchi vuoti delle impostazioni («Ancora nessun altro utente», «Ancora nessun modello email»): erano «Ancora niente in Utenti» |
| `crm/api/conversations.py` (`counts`) | I numeri sopra le Conversazioni contano solo le persone che chi legge vede, con gli stessi permessi dell'elenco: un medico che segue tre persone leggeva «Aperte 1739» e «Da leggere 21» sopra un elenco che diceva «Niente da leggere qui» |
| `Calendar/AppointmentPanel.vue`, `Automations/ConditionBuilder.vue` | «Ripeti questo appuntamento» dice cosa conta il numero («4 volte»); nelle automazioni, «E un'altra condizione» al posto di un «E» da solo |
| `Activities/ActivityHeader.vue` | Nella scheda Eventi di una persona o di una trattativa il pulsante pieno è «Appuntamento», quello per cui la scheda c'è; «Evento» (una chiamata, una riunione) è l'altro. Il Tracciamento non ha più il «Nuovo» con tutti i messaggi e i documenti della conversazione: si legge, e il suo pulsante (le impostazioni del tracciamento) sta dentro |
| `Modals/EventModal.vue` | Un evento nuovo, dalla scheda di una persona, comincia al prossimo quarto d'ora sull'orologio del centro, come quelli dell'agenda: prendeva l'ora del telefono al minuto in cui si apriva (14:49 su un telefono in un altro fuso, dove il centro segnava le 20:19) |
| `src/index.css` | La scelta che svuota un campo facoltativo (Settore, N. di dipendenti…) è un trattino: era una riga bianca, sul telefono una fascia di 48 px sopra la prima scelta |
| `Settings/AzioneImpostazioni.vue`, `Settings/Settings.vue` e 25 pagine delle impostazioni | Sul telefono l'azione di una pagina delle impostazioni («Aggiorna», «Salva», «Manda gli inviti») sta in fondo allo schermo, larga quanto lui e alta 44 px, come la barra della fatturazione: stava accanto al titolo, in cima a una pagina che scorre, lontana dal campo appena cambiato, e una modifica restava non salvata. Sul computer resta accanto al titolo |
| `crm/locale/it.po`, `tests/unit/paroleDaTradurre.test.js` | Quaranta parole date a un traduttore ricevuto come parametro (`t('1 month')`) si leggevano in inglese: «1 month · any number of entries» sotto un tipo di abbonamento nuovo, i limiti della prenotazione online («2h notice»), le offerte della lista d'attesa, le tappe di un programma, i nutrienti di un piano. Un test le vuole tutte nel catalogo |
| `frontend/vite/frappeUi.js` | Quello che legge un lettore di schermo è in italiano: la freccia di ogni campo che si sceglie da un elenco («Show popup» di reka, ora «Mostra le scelte»), la croce di un messaggio, il cerchio che gira, il mese e l'anno sopra il calendario («cycle-calendar-view») |
| `Settings/Scheduling/TeamMatrix.vue`, `ServicesSettings.vue` | Nella griglia di chi fa cosa le caselle che scorrono passano sotto il nome del servizio, non sopra; nel servizio il nome ha la riga per sé («Massaggio decont…») |
| `crm/fcrm/doctype/crm_deal/crm_deal.py` (`value_from_quotes`) | Una trattativa rimasta da prima della griglia dei prodotti teneva il suo totale: con «Aggiorna in automatico il valore previsto» acceso, ogni salvataggio lo scriveva sopra il valore del preventivo (doc 50). Ora un preventivo oltre la bozza dice quanto vale la trattativa |
| `crm_invoicing_company.json`, `crm/locale/it.po` | L'azienda emittente: «Nome in fattura» e «Nome» del professionista, dove c'erano due «Nome»; «l'editor del modulo» al posto di «il builder» |
| `Activities/EventArea.vue`, `EventNotificationsArea.vue` | «In arrivo» e «comincia ora» sull'orologio del centro: con l'ora del telefono, in un altro fuso, l'appuntamento di stasera stava tra quelli in arrivo |
| `Settings/Pipelines/PipelineList.vue`, `QuotesPipeline.vue`, `NewClientsPipeline.vue`, `frontend/vite/frappeUi.js` | La pagina Pipeline: la pipeline predefinita non ha più il «…» che apriva un menu vuoto, e le pipeline dei nuovi clienti e dei preventivi tengono ciascuna la sua «Salva» in fondo alla sezione (erano due barre una sopra l'altra). «(obbligatorio)» dopo un campo richiesto e «Nessuna opzione» in un menu vuoto, che erano in inglese |
| `Settings/AssignmentRules/`, `Settings/Sla/`, `SLASection.vue` | Regole di assegnazione e tempi di risposta in italiano: le priorità («Medio-bassa»), a chi si applicano («Persone», «Trattative»), gli stati («Aperto», «Risposto»: arrivavano dai record così come sono), i giorni degli orari di lavoro (erano Monday, Tuesday…). Sulla scheda «Prima risposta», «Risposta successiva» e «Rispettato in 2h 5m», una frase intera dove c'era un «in» inglese incollato |
| `Settings/EmailTemplate/EditEmailTemplate.vue`, `NewEmailTemplate.vue` | Il tipo di contenuto di un modello email è «Testo formattato» o HTML: diceva «Rich Text» |
| `Settings/WhatsAppTemplates.vue`, `utils/modelliWhatsApp.js`, `crm/integrations/whatsapp/templates.py` | Un modello WhatsApp nuovo: la categoria col suo nome e la riga su quando è quella giusta («Utilità: su qualcosa che la persona ha chiesto o prenotato»), non «MARKETING» come lo scrive Meta; gli stati della revisione in parole («In revisione», «Rifiutato», «In pausa»); le lingue per nome, quella del centro in cima e già scelta (si apriva sull'afrikaans, la prima della lista); l'esempio del messaggio parla di un appuntamento |
| `crm/telephony/consumi.py` | La pagina Twilio, quando Twilio non risponde, dice ancora da quando conta la spesa e quanti giorni guarda: leggeva «speso dal ,» e «Problemi negli ultimi {0} giorni» |
| `Settings/CallScriptsSettings.vue` | Un nuovo script delle chiamate sul telefono: nome, servizio e «quando si usa» uno sotto l'altro (in due colonne i testi si tagliavano); «Elimina» solo su uno script salvato |
| `Settings/TrackedLinksSettings.vue`, `Automations/MergeFieldInput.vue`, `StepPanel.vue`, `crm_tracked_link` | I link tracciati senza sintassi: nei messaggi di un'automazione «Inserisci un campo» offre anche i link, e la pagina lo dice invece di mostrare `{{ tracked_link("slug") }}`; lo slug è il «nome breve». Nell'editor «I campi sono quelli della persona» (era «I campi vengono da CRM Lead») e «100% in totale» |
| `Modals/CreateDocumentModal.vue` | Il dialogo che crea un record da un campo collegato si intitola «Crea settore», col nome del DocType nella lingua di chi legge: era «Nuovo Industry» |
| `crm/invoicing/scelte.py` (`PAESI`, `paesi()`) | Il paese dell'azienda emittente si sceglie per nome («Italia»), nella lingua di chi legge: mostrava «IT», il codice che va in fattura e che resta salvato |
| `crm/invoicing/install.py` (`parole_di`, `nella_lingua`), `crm/tessera_sanitaria/install.py` | Le qualifiche che DottorCloud porta scrivono nome, note e punti da verificare nella lingua del centro, e li seguono dopo un migrate finché lo studio non li cambia: erano in inglese nel record («Cassa Forense contributo integrativo 4%: mandatory…», «Consulente (non-regulated profession)»). Il codice di una qualifica è «un nome breve che non cambia mai», non «un identificativo usato dal motore» |
| `Settings/Hierarchy/Hierarchy.vue` | «Abilita» e «Disattiva» della gerarchia li vede solo chi può davvero accenderla, l'amministratore di sistema (la regola del server: un responsabile messo nell'albero si toglierebbe il suo limite). Il responsabile premeva «Abilita» e riceveva un errore; ora legge «Solo un amministratore di sistema può attivarla», e l'albero lo gestisce come prima |
| `Settings/Scheduling/SchedulingDefaults.vue`, `utils/fusiOrari.js` | Il fuso orario dell'agenda: dopo quello del sito, il fuso del dispositivo e «Europe/Rome», ognuno col suo nome («Europe/Rome · Ora dell'Europa centrale»), poi gli altri. Sul telefono era un foglio di quattrocento righe che partiva da «Africa/Abidjan» |
| `pages/Invoices.vue` | «Comunica» al Sistema TS chiede conferma: sul telefono sta nella scheda che si tocca per aprire la fattura, e un tocco sbagliato mandava subito la spesa |
| `utils/numberFormat.js` (`flt`) | Un importo scritto con la tastiera decimale del telefono, che ha solo il separatore della sua lingua: su un sito che scrive i numeri all'inglese «12,5» diventava 125, e un prezzo di 12,50 € ne valeva 1250. Ora il separatore delle migliaia preso una volta sola, con una o due cifre dopo, è la virgola dei decimali che la tastiera aveva; «1,234» resta milleduecentotrentaquattro. Test: `tests/unit/numberFormat.test.js` |
| `crm/lingue.py` (`valuta()`), `crm/dashboard/context.py`, `crm/api/dashboard.py`, `crm_deal.py`, `crm_organization.py` | La dashboard del medico diceva «0 USD»: dove il centro non ha scelto una valuta, il codice ereditato ripiegava sul dollaro, e ogni trattativa in euro chiedeva il cambio a un servizio esterno e si sommava in dollari. Ora vale la valuta scelta nelle impostazioni, altrimenti quella del paese del centro, l'euro dove nessuno l'ha detto. I record di prova delle trattative sono in euro. Test: `crm/tests/test_valuta_del_centro.py` |
| `crm/install.py` (`add_genders_and_titles`), patch `a_person_has_genders_and_titles` | «Genere» sulla scheda di una persona era un elenco vuoto, e «Titolo» aveva solo «Sig.» e «Sig.ra»: li crea la procedura guidata del framework, e un sito installato senza non li aveva. Ora DottorCloud assicura i generi del framework («Donna», «Uomo», «Non conforme», «Preferisce non dirlo»…) e i titoli che si scrivono in Italia («Sig.», «Sig.ra», «Dott.», «Prof.»). Test: `crm/tests/test_generi_e_titoli.py` |
| `crm/utils/__init__.py` (`default_region`) | Un cellulare scritto senza prefisso («333 123 4567») su un sito che non ha detto il paese restava com'era: la libreria lo leggeva indiano, e senza il +39 non partivano WhatsApp, SMS e chiamate. Ora dove il sito non ha detto il paese il numero è italiano, la stessa regola della lingua e della valuta. Test in `crm/tests/test_valuta_del_centro.py` |
| `Modals/DoctypeModal.vue`, `utils/schedaChiusa.js` | Una nota o una cosa da fare aperta dal suo elenco si presentava, finché non arrivava, come «Nuova nota» vuota con «Crea»: sul telefono, con la rete lenta, un tocco su «Crea» ne avrebbe fatta un'altra. Ora la finestra di un record che ha un nome è «Modifica la nota» dal primo momento, con il segno del caricamento e il pulsante spento finché il record non c'è; se non si apre lo dice a parole («Non puoi aprire questa nota», «Questa cosa da fare non c'è più») |
| `Settings/AssistantSettings.vue`, `crm/locale/it.po` | Nel registro dell'assistente il fornitore si legge «Compatibile con OpenAI», non «OpenAI compatible»; il ruolo di un contatto è «Ruolo», non «Designazione» |
| `Mobile/AgendaDelGiorno.vue` | Nell'elenco del giorno «Prima visita» prendeva il posto dello stato: un paziente nuovo «Non venuto» o «Completato» non lo diceva. Ora i due segni stanno uno sopra l'altro |
| `utils/telefono.js` (`leggibile`), `utils/sulTelefono.js`, `Mobile/ElencoChiamate.vue`, `ElencoContatti.vue`, `Conversations/ConversationHeader.vue`, `ConversationAside.vue`, `Calendar/AppointmentPanel.vue` | Un numero salvato com'è, «+393331230000», si leggeva tutto attaccato negli elenchi, nella conversazione e nell'appuntamento. Ora si legge a gruppi, «+39 333 123 0000»; Milano e Roma dopo il prefisso; un altro paese, o un numero mascherato, come è scritto. Solo per leggere: quello che si salva e si compone resta il numero com'è. Test: `tests/unit/telefono.test.js` |
| `Clinic/ClinicSummary.vue` | Nella sintesi clinica peso, altezza e frequenza cardiaca aprivano la tastiera delle lettere: ora quella dei numeri; la pressione resta con quella che ha la «/» («120/80») |
| `Area/AreaAccessCard.vue` | Nella scheda «Area clienti» della persona il «Chiudi» rosso accanto a chi entra toglieva subito l'accesso all'area, senza chiedere: sul telefono sembrava il pulsante che chiude una finestra, e un tocco lasciava il paziente fuori. Ora si chiama «Chiudi l'accesso» e chiede prima, dicendo come si riapre: con «Apri l'area», e riceverà un nuovo invito |
| `src/index.css` | Il titolo di una finestra con una parola lunga, un indirizzo email, va a capo dentro la parola: frappe-ui lo lasciava largo quanto la parola, e sul telefono la X per chiudere usciva dallo schermo |
| `src/area/area.css` | Nell'area del paziente `.touch-target` era scritta su sette comandi (la spunta di un esercizio, una casella della lista della spesa, lasciare la lista d'attesa…) ma l'area non la disegnava. Ora c'è l'anello invisibile del resto dell'app, e lo hanno anche l'interruttore «Anche su SMS» (40 px, l'anello parte dentro il suo bordo) e «‹ I tuoi piani» in cima alla pagina. «In parte» e «Saltato», uno accanto all'altro, crescono solo in altezza, perché nessuno dei due prenda il bordo dell'altro |
| `crm/lingue.py` (`solo_italiano_e_inglese`), `crm/hooks.py` | Il framework spedisce l'italiano spento, e un visitatore legge solo una lingua accesa nel sito: /prenota, la porta dell'area, un link a un modulo o a un documento, l'accesso arrivavano in inglese a un telefono in italiano, e la procedura guidata non offriva l'italiano. DottorCloud lo accende all'installazione e a ogni migrate, con l'inglese, e spegne le altre lingue del framework, in cui non ha parole: un telefono in tedesco legge l'inglese se lo accetta, altrimenti la lingua del centro (05/10/2026, doc 40). Test: `crm/tests/test_lingua_dei_visitatori.py` |
| `crm/locale/it.po` | Le pagine di accesso e di nuova password del framework in italiano: «Accedi», «Ti diamo il benvenuto! Accedi per continuare.», «Password dimenticata?», «Manda il link», «Torna all'accesso», «Accedi con un link via email», la forza della password, i messaggi d'errore. Il catalogo del framework le aveva senza traduzione |
| `crm/marchio.py` (`contesto`, `PAGINE_DEL_FRAMEWORK`), `templates/includes/marchio_framework.html` | L'accesso, la nuova password e il messaggio dopo, che sono del framework: il pulsante principale nel colore d'azione del marchio (era il grigio più scuro, quasi nero), e sul telefono campi alti 44 px con il testo a 16 px (sotto i 16 px iPhone ingrandisce la pagina quando li tocchi), i link alti un pollice. Test in `crm/tests/test_marchio.py` |
| `utils/tastiera.js` (`'nome'`), `crm/www/prenota.html`, `crm/public/js/moduli_campi.js`, `crm/www/book.html` | Il nome di una persona si scrive con la maiuscola a ogni parola e senza correttore: nella scheda di una persona nuova, su /prenota, nei moduli del sito. iPhone metteva la maiuscola solo all'inizio del campo («Maria grazia») e il correttore poteva cambiare un cognome in una parola. Test: `tests/unit/tastiera.test.js` |
| `crm/www/book.html` | La vecchia /book, che si apre ancora dal link di una prenotazione fatta prima del passaggio ai servizi, era in inglese («Reschedule», «Cancel booking», «Pick a day»…): ora le sue frasi sono intere e in italiano, anche quelle dello script, scritte dal server nella lingua di chi la apre |
| `utils/temaDelTelefono.js`, `area/main.js`, `area.html`, `area/App.vue`, `area/pages/Login.vue` | L'area del paziente segue il tema del telefono, chiaro o scuro, e lo segue se cambia mentre è aperta; la barra del telefono prende lo stesso colore. Restava chiara su un telefono scuro, mentre /prenota passava al buio. Il logo largo del centro, disegnato per la carta bianca, sul fondo scuro ha la sua cartolina bianca. Test: `tests/unit/temaDelTelefono.test.js` |
| `Activities/MessageActions.vue`, `ChatBubble.vue`, `WhatsAppArea.vue`, `src/index.css` (`azioni-della-bolla`) | Le azioni di un messaggio («Rispondi», «Reagisci», «Aggiungi all'archivio clinico») erano tre tondi da 28 px a 4 px l'uno dall'altro, accanto alla bolla: accanto a un messaggio largo l'ultimo usciva dallo schermo (x 393 su 390), e nascosti prendevano lo stesso il tocco nello spazio vuoto accanto a un messaggio. Dove non c'è un puntatore sono una barra sopra il messaggio, dal suo lato, con pulsanti da 40 px; nascosta non prende tocchi. Nella vista WhatsApp il fuoco che la mostra è sulla riga, così un tocco su un pulsante non la chiude su Safari |
| `IconPicker.vue` | Le sei reazioni rapide erano quadratini da 20 px intorno a emoji da 24: ora pulsanti da 40 px, e il «+» si chiama «Altre reazioni». Il selettore completo era largo 440 px, fuori da uno schermo da 360 sui due lati con la ricerca sopra il bordo: sul telefono è un foglio dal basso, otto colonne da 40 px; i gruppi in italiano («Faccine ed emozioni», «Cibo e bevande»…) |
| `Activities/ActivityHeader.vue` | I filtri dei canali sopra la conversazione rispondevano su 32 px: lo scorrimento della striscia tagliava l'anello invisibile al bordo della striscia. Ora la striscia ha 6 px sopra e sotto, e il tocco prende 40 px |
| `Activities/ChannelSwitcher.vue`, `src/telefono.css` (`strumenti-compositore`), `EmailEditor.vue`, `CommentBox.vue`, `SMSBox.vue`, `WhatsAppBox.vue` | Gli strumenti di chi scrive (allega, modello, formattazione, microfono, invia) erano pulsanti da 28 px attaccati: un pollice su «Allega» prendeva «Formattazione». Sul telefono sono da 40 px, come i canali sopra (WhatsApp, Email, SMS, Nota); quelli dell'email, fino a cinque, vanno sotto il testo, con «Invia» in basso a destra |
| `Dashboard/widgets/ListWidget.vue` | Il link in fondo a un riquadro della dashboard («Apri le conversazioni», «Apri l'agenda», «Tutte le trattative»…) era una riga da 12 px che rispondeva su 16: sul telefono è alto quanto la riga, 44 px, a 14 px |
| `Today/ParticipantRow.vue` | All'accoglienza il nome della persona rispondeva su 29 px: l'anello dei pulsanti dell'esito, già da 40 px sul telefono, ci arrivava sopra. Ora i pulsanti non hanno anello sul telefono, e il nome è alto 44 px |
| `Mobile/TrattativePerFase.vue` | Le fasi sopra le trattative erano alte 30 px: ora 40 |
| `src/telefono.css` | Un pulsante di frappe-ui che apre una pagina (`:route`, `:link`) è disegnato come un link con le stesse classi, e restava senza l'anello invisibile: «Giro di chiamate» nella pagina delle chiamate rispondeva su 24 px. Ora ha l'anello come gli altri |
| `RelatedPeopleSection.vue` | Una persona collegata si apriva solo dal suo nome, una riga da 16 px: ora si apre da tutta la riga, con «Modifica» sopra |
| `Telephony/PhonePanel.vue` | Nel telefono in alto a destra «Da richiamare adesso» rispondeva su 32 px, una chiamata recente su 30, «Tutte le chiamate» e «Giro di chiamate» su 17: sul telefono sono righe da 44 px. Il campo «Numero o nome» prendeva il fuoco all'apertura: sul telefono apriva la tastiera del telefono sopra il tastierino del pannello e faceva scorrere il foglio mentre saliva. Ora prende il fuoco solo sul computer |
| `composables/chatAperta.js`, `src/telefono.css` («11»), `pages/MobileLead.vue`, `Conversations.vue`, `Activities/ComposerShell.vue`, `ActivityHeader.vue`, `ChannelSwitcher.vue` | Sulla conversazione di una persona la chat aveva un quarto dell'iPhone: sopra l'intestazione, la scheda della persona con le azioni rapide, le schede, i filtri dei canali; sotto la casella per scrivere e la barra in basso. Ora la conversazione è lo schermo, come nelle app di messaggi del telefono: la barra in basso si fa da parte e la casella è il fondo dello schermo, sopra la linea di iPhone; la scheda della persona aspetta raccolta, e il nome nell'intestazione la apre e la richiude. Con la tastiera aperta si fanno da parte anche le schede, i filtri dei canali e la riga dei canali della casella (`data-via-scrivendo`): il canale è già scelto, e la casella ne tiene il colore. Lo stesso in un filo della pagina Chat. Su un iPhone da 390 × 844 i messaggi passano da circa 230 a 555 px, con la tastiera aperta da quasi niente a 358; su un iPhone SE 378 px, 181 con la tastiera |
| `Activities/WhatsAppBox.vue` | Fuori dalle 24 ore l'avviso di WhatsApp sopra la casella era di due righe con il suo pulsante: un terzo della casella. Sul telefono è una riga sola, «Oltre le 24 ore: solo un modello · Scegli», e tutta la riga apre i modelli |
| `Activities/WhatsAppBox.vue`, `CommunicationArea.vue` | «Scrivi un messaggio WhatsApp…» andava su due righe accanto ai tre tasti della casella, e raddoppiava la casella; «Scrivi una nota per i colleghi…» era tagliato a metà. Sul telefono sono «Messaggio WhatsApp…» e «Nota per i colleghi…» |
| `Conversations/ConversationHeader.vue` (`inTestata`), `pages/Conversations.vue`, `src/telefono.css` (`icone-a-dito`) | Nella pagina Chat, aperto un filo, sopra la conversazione c'erano due intestazioni: la riga «Conversazioni» con l'aggiorna e quella della persona. Sul telefono quella della persona prende il posto della prima, accanto al telefono in alto a destra: 42 px in più alla chat. I suoi pulsanti (indietro, letta, più tardi, gestita) erano da 28 px attaccati: ora da 40; la persona si apre dal suo nome, come nelle app di messaggi |
| `Activities/EmailArea.vue` | «Rispondi» e «Rispondi a tutti» su un'email rispondevano su 28 px in altezza: la riga che li tiene tagliava l'anello invisibile. Ora prendono il tocco su 40 px |
| `Documents/DocumentsCard.vue` | Un documento si apriva solo dal suo nome, una riga da 16 px: ora da tutta la riga, con «Azioni» sopra |
| `Modals/WhatsappTemplateSelectorModal.vue`, `utils/segnaposti.js` | Nei modelli WhatsApp ogni scheda era alta 224 px anche sul telefono, una sotto l'altra: un modello di due righe era una scheda quasi vuota. Ora è alta quanto il testo, fino a quattro righe. I posti da riempire si leggevano come codice, «{{1}}», anche nella finestra per riempirli, con i campi «Valore per {{1}}»: ora sono un riquadro con il numero, il campo si chiama «Valore 1», e nel messaggio il riquadro mostra quello che si scrive. Test: `tests/unit/segnaposti.test.js` |
| `src/index.css` | Il testo guida della casella (l'email, la nota) andava a capo dove non ci stava, e la riga sotto lo tagliava a metà: ora resta su una riga, con «…» dove non entra |
| `Mobile/MobileAppHeader.vue`, `src/telefono.css` | L'anello invisibile del telefono in alto a destra arriva 8 px alla sua sinistra, e a 4 px di distanza prendeva gli ultimi 7 px dell'ultima icona della pagina: «Ricarica», «Altro», «Giorno dopo», «Giro di chiamate» rispondevano su 27 px. Ora fra i due c'è spazio, e rispondono su 34 × 40. Il nome della persona, che sulla conversazione apre la scheda, rispondeva su 26 px: ha l'anello delle briciole |
| `Controls/Link.vue` | «Assegnata a» nel pannello della persona mostrava l'indirizzo email del collega finché non se ne apriva l'elenco: ora il suo nome, dagli utenti che l'app ha già, in ogni campo che sceglie un collega |
| `Activities/WhatsAppBox.vue` | Di traverso il telefono è largo più di 768 px, e l'avviso delle 24 ore tornava di due righe con il suo pulsante: alla chat della persona restavano 90 px. Ora segue il telefono comunque lo si tenga: 111 px |
| `composables/conversationScroll.js` (`farFromTheEnd`), `Activities/Activities.vue` | Chi risaliva una conversazione lunga doveva scorrere a mano fino in fondo. Ora, più di uno schermo sopra l'ultimo messaggio, in basso a destra compare «Vai all'ultimo messaggio», un pulsante da 40 px sopra i messaggi che non prende spazio; in fondo sparisce. Test: `tests/unit/conversationScroll.test.js` |

## Non incluso

- **Il builder della dashboard** resta da desktop: una griglia da trascinare
  su un telefono non si usa. Sul telefono le dashboard si guardano.
- **Il 404 della pagina Telephony** per chi non ha ancora un agente: è come la
  pagina sa che l'agente va creato. frappe-ui rilancia l'errore di ogni
  richiesta partita da sola, e la console lo mostra, ma chi usa la pagina non
  vede niente.
- **Tre accelerazioni misurate e lasciate** (telefono con il processore 4 volte
  più lento). Il compositore della scheda montato dopo il disegno: un tocco
  sulle schede il 13% più veloce, ma chiede uno scheletro del compositore e un
  campo che prenda il fuoco al tocco su iPhone, dove la tastiera si apre solo
  dentro il tocco stesso. L'editor di testo fatto più tardi: le schede il 10%
  più veloci, ma quando arriva fa un fotogramma lungo 100 ms in più, e chi
  scrive se ne accorge. Gli stili che il menu di frappe-ui scrive sulla pagina
  aprendosi (niente tocchi né scorrimento sul resto, 46 elementi nascosti ai
  lettori di schermo): circa 100 ms di ricalcolo sul menu «Nuovo», ma toglierli
  vuol dire rifare il menu come non modale, con il fuoco e il tocco fuori da
  tenere a mano.
