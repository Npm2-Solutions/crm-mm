# 52 · Twilio: l'account del centro, tutto da DottorCloud

**Stato:** in corso (02/10/2026). Prima parte: il collegamento.

## Il bisogno

- Il centro usa **il suo account Twilio**: chiamate e SMS li paga lui a Twilio, al
  prezzo di Twilio.
- **Tutto il resto lo fa in DottorCloud**: scegliere e comprare i numeri, decidere
  chi risponde, chiamare, mandare SMS, vedere quanto spende. Su Twilio entra il
  meno possibile, idealmente solo per l'accesso.

## Com'era

- Il collegamento era **dell'agenzia**: incollava SID e token di un account nel
  Desk, e il centro non poteva collegare il suo.
- **I numeri si configuravano a mano** nella console di Twilio, uno per uno, e la
  pagina mostrava l'indirizzo sbagliato per le chiamate in arrivo (quello delle
  chiamate in uscita).
- **L'app di Twilio** (TwiML App) trovata per nome restava con l'indirizzo che
  aveva, anche se era quello di un altro sito.
- **Non si compravano numeri** da DottorCloud, né si mandavano a Twilio i documenti
  che i numeri italiani chiedono.

## Cosa permette Twilio (verificato il 02/10/2026)

### Il solo accesso: Twilio Connect

- Esiste: il centro preme «Collega», entra su Twilio, autorizza. HubSpot lo usa.
  Twilio crea per l'app un sottoaccount nell'account del centro e fattura il centro.
- **Twilio stesso lo limita** («Known Limitations for Connect Apps», aggiornato il
  29/07/2026). Un'app collegata così:
  - non gestisce i numeri, nemmeno per rilasciarli;
  - non usa le API dei documenti (Regulatory Compliance v2), quindi non compra
    numeri italiani, che i documenti li vogliono tutti;
  - non crea chiavi API, quindi il browser non telefona: niente centralino in
    DottorCloud;
  - non verifica numeri da mostrare, lavora solo nella regione US1 e non crea
    sottoaccount.
- **Per un centro italiano non basta**: senza numeri e senza browser non resta
  quasi niente.

### Le app OAuth di Twilio

- Valgono solo per l'account in cui nascono: non servono a un prodotto che lavora
  sugli account dei suoi clienti.

### Quindi: due codici, una volta

- Nella prima pagina della console Twilio ci sono **Account SID e Auth Token**. Il
  centro li incolla una volta in DottorCloud.
- DottorCloud li usa in quel momento per creare **il suo spazio** nell'account del
  centro, un sottoaccount «DottorCloud · indirizzo del sito», con la sua chiave e la
  sua app. Conserva solo le chiavi dello spazio: **il token dell'account non lo
  tiene**, e il resto dell'account non lo legge e non lo tocca.
- Twilio fattura lo spazio all'account del centro. Il centro vede nella sua console
  tutto quello che DottorCloud fa (numeri, chiamate, costi), nello spazio.
- **Su Twilio restano solo**: creare l'account, il metodo di pagamento e le
  ricariche; la portabilità di un numero che il centro ha già (un modulo di Twilio).

## Le regole italiane che contano

- **I numeri.** Twilio vende in Italia, anche via API (listino del 02/10/2026):
  - numeri mobili (+39 3…): chiamate e SMS, 45 $ al mese;
  - numeri verdi (800): solo chiamate in arrivo, 27 $ al mese più 0,46 $ al minuto.
  - I geografici (02, 06…) non sono nel listino: si portano da un altro operatore
    (solo dai grandi, fino a 6 settimane, modulo di Twilio) o si chiedono a Twilio.
- **Ogni numero italiano vuole i documenti**: ragione sociale, partita IVA, sede,
  il rappresentante con codice fiscale e documento, una prova dell'indirizzo; per un
  geografico la sede nel distretto del prefisso. Twilio li verifica in qualche
  giorno.
- **Le chiamate in uscita.** Dal 19/11/2025 l'AGCOM (delibera 106/25/CONS) fa
  bloccare le chiamate arrivate dall'estero che mostrano un numero mobile italiano
  (i fissi dal 19/08/2025). Twilio chiede di chiamare l'Italia con un numero
  geografico. Quindi: **il mobile per ricevere e per gli SMS, il geografico per
  chiamare**.
- **Gli SMS** possono avere come mittente il nome del centro (fino a 11 caratteri):
  Twilio non chiede di registrarlo, applica il suo codice di condotta (delibera
  AGCOM 42/13/CIR). A un nome però non si risponde: le risposte arrivano solo a un
  numero mobile. Gli SMS promozionali non partono dalle 22 alle 8 né la domenica.
- **I costi**, indicativi (listino Twilio, 02/10/2026):
  - chiamare un fisso costa 0,017 $ al minuto;
  - chiamare un cellulare costa 0,045 $ al minuto con un numero europeo, 0,35 $
    altrimenti;
  - il tratto nel browser costa 0,004 $ al minuto;
  - la registrazione costa 0,0025 $ al minuto;
  - un SMS verso l'Italia costa 0,093 $.

## Come funziona

### 1. Il collegamento (prima parte, fatta)

- **Impostazioni › Telefono › Telefonia › Twilio**, per chi configura il telefono
  (`telefono.configura`). Tre passi:
  1. creare l'account su Twilio e attivarlo con un metodo di pagamento;
  2. copiare Account SID e Auth Token dalla prima pagina della console;
  3. incollarli in DottorCloud e premere «Collega».
- **DottorCloud allora**:
  - crea lo spazio, o ritrova quello di un collegamento di prima;
  - crea la sua chiave e cancella quelle vecchie dello spazio;
  - prepara la sua app con l'indirizzo giusto per le chiamate dal browser;
  - punta ogni numero dello spazio a DottorCloud, per le chiamate e per gli SMS;
  - aggiorna l'elenco dei numeri.
- **Se i codici sono di un sottoaccount**, quello diventa lo spazio: serve a chi
  ricollega, o all'agenzia che ne ha già fatto uno.
- **Ogni ora DottorCloud ricontrolla** l'app e i numeri, e rimette a posto quello
  che qualcuno ha cambiato nella console. «Controlla» fa lo stesso subito e dice
  com'è l'account: attivo, di prova, sospeso. Un numero passato a un trunk SIP
  resta com'è, e la pagina lo dice.
- **«Scollega»** dimentica le chiavi e cancella quella di DottorCloud. Lo spazio e
  i suoi numeri restano nell'account del centro, e i numeri continuano a costare
  finché non si rilasciano. Ricollegando, DottorCloud ritrova lo stesso spazio.
- **Con un account di prova** Twilio fa chiamare solo i numeri verificati e non
  vende numeri italiani: la pagina lo dice e rimanda all'attivazione.

### 2. I numeri (seconda parte, fatta)

In Impostazioni > Telefono > Telefonia > Twilio, sotto il collegamento, «Nuovo
numero» apre una finestra in tre passi:

1. **Quale numero e di chi.** Mobile, geografico (con il prefisso della zona) o
   verde, ciascuno con a che cosa serve e il prezzo al mese che Twilio dà oggi
   (API dei prezzi, nella valuta dell'account). Di chi è: una società o un
   professionista a suo nome, come dice la fatturazione (il titolare con nome e
   cognome e senza ragione sociale è un professionista): Twilio chiede documenti
   diversi. Già qui la finestra dice se Twilio ha numeri pronti di quel tipo, e
   quali.
2. **A chi è intestato.** I campi del regolamento di Twilio per l'Italia, con dentro
   quello che DottorCloud sa del centro (ragione sociale, partita IVA, sede, email:
   mai la PEC, che può rifiutare le email normali). Un campo che DottorCloud conosce
   ha le sue parole; gli altri quelle di Twilio.
3. **I documenti.** Per ogni requisito il documento che lo soddisfa (la visura, una
   bolletta della sede, il documento del legale rappresentante…), caricato qui: un
   PDF, un JPEG o un PNG fino a 5 MB, come li prende Twilio. L'indirizzo della sede,
   quando serve, una volta sola.

**Mandati a Twilio**, DottorCloud crea l'intestatario, l'indirizzo, i documenti con i
loro file e il pacchetto che li tiene insieme, e chiede subito a Twilio di valutarlo:
se manca qualcosa la finestra lo dice e la richiesta resta una bozza da correggere
(rimandandola, la bozza di prima sparisce anche da Twilio); se è tutto in regola va in
verifica. **Ogni ora DottorCloud chiede a Twilio com'è andata** e lo dice a chi l'ha
chiesta, tra le notifiche (e per email, se non la legge): aprendola si apre la pagina
di Twilio. Approvati, i file e quello che era stato scritto spariscono da DottorCloud:
Twilio ha la sua copia. Rifiutati, la richiesta dice perché e si rimanda con quello
che era già scritto e i file già caricati.

**Il numero si sceglie** tra quelli che Twilio ha (con le cifre che si vogliono, della
zona per un geografico) e **si compra con un clic**: nasce puntato a DottorCloud per le
chiamate e, se è un mobile, per gli SMS, e compare tra i numeri. **I documenti
approvati valgono anche per il numero dopo** dello stesso tipo e dello stesso
titolare (della stessa zona, per un geografico): il secondo si compra subito.

**Un numero si rilascia** dalla pagina dei numeri, con una conferma: smette di
costare e non torna indietro. Solo nello spazio di DottorCloud: un account collegato a
mano può tenere numeri di altri siti.

**Solo i file del centro vanno a Twilio.** Un documento è un file caricato da chi
manda la richiesta, privato e non attaccato a nient'altro, o un file di una richiesta
di prima: nessun altro file del sito (il referto di un paziente) può partire da qui.

### 3. Le chiamate (terza parte)

- **Chi risponde (fatto).** Una chiamata al numero del centro fa squillare insieme
  tutti quelli che rispondono a quel numero: alla scrivania nel browser, se sono
  collegati, o sul cellulare. Il primo che risponde la prende. Se nessuno risponde
  entro i secondi scelti (Impostazioni > Telefonia > Segreteria, «Squilla per»,
  20 di partenza), risponde la segreteria con l'annuncio e mette la richiamata in
  coda; senza la segreteria, chi chiama sente le scuse invece del silenzio.
  Prima ne squillava uno solo, e «nessuno risponde» voleva dire solo «nessuno
  collegato».
- **Il messaggio (fatto).** Se il centro lo vuole, dopo l'annuncio chi chiama può
  lasciare un messaggio dopo il segnale (fino alla durata scelta): resta sulla
  chiamata come registrazione (`CRM Call Log.left_message`), viene trascritto se la
  trascrizione è attiva, e chi segue la persona riceve l'avviso «ha lasciato un
  messaggio in segreteria», che apre la persona. Senza chi la segue, l'avviso va a
  chi risponde a quel numero, e se non c'è nessuno a chi legge tutte le chiamate.
- **Il numero da cui si chiama (fatto).** Prima che una chiamata parta dal browser,
  DottorCloud chiede al server se può partire e quali numeri può mostrare. Con più
  numeri del centro la finestra della chiamata chiede da quale chiamare, con già
  scelto l'ultimo usato (lo ricorda il browser), altrimenti la propria linea. Il
  server mostra il numero scelto solo se è uno dei numeri del centro
  (`CRM Caller ID`), altrimenti la linea di chi chiama. Un cellulare italiano
  mostrato su una chiamata verso l'Italia ha l'avviso: «dal novembre 2025 queste
  chiamate vengono bloccate: scegli un numero fisso».
- **Il tastierino (fatto).** Durante la chiamata manda i toni ai menu automatici
  degli altri («premi 1 per…»); i tasti premuti restano scritti sopra.
- **I paesi che si possono chiamare (fatto).** In Impostazioni → Telefono →
  Telefonia → Twilio, «Paesi che si possono chiamare»: l'Italia di partenza, il
  responsabile aggiunge gli altri. Il server non fa partire una chiamata verso un
  paese che il centro non ha scelto, né mai verso un numero a pagamento (899,
  892, 166… in ogni paese): è lì che chi ruba una linea la fa chiamare. Gli stessi
  paesi diventano i permessi di Twilio dello spazio (le «Geo permissions», non
  più ereditate dall'account), così nemmeno una chiave rubata chiama altrove; ogni
  ora `assicura()` li rimette come li ha scelti il centro. Un account collegato a
  mano dall'agenzia resta com'è.

### 4. Gli SMS (quarta parte, fatta)

- **Un mittente del centro (fatto).** Tutti gli SMS del centro partono da un solo
  mittente, scelto in Impostazioni → Telefono → Telefonia → Twilio, «Mittente degli
  SMS»: il nome del centro (fino a 11 lettere senza accenti, cifre e spazi, non solo
  cifre: Twilio lo prende senza registrarlo), a cui nessuno può rispondere, o uno dei
  numeri dello spazio che mandano SMS, quando il centro vuole le risposte. Senza una
  scelta parte dal primo di quei numeri, altrimenti da un nome fatto con quello del
  centro. Prima ogni posto aveva il suo: l'SMS scritto a mano partiva dalla linea di
  chi scriveva (e un fisso italiano non manda SMS), le automazioni dalla linea di un
  operatore qualsiasi, la lista d'attesa e l'area clienti dal numero scritto nelle
  loro pagine. La patch `the_centre_sends_sms_from_one_sender` fa di quel numero il
  mittente; le due pagine ora dicono da dove partono gli SMS e portano a quella di
  Twilio.
- **STOP e START (fatto).** Un SMS che è solo una parola per fermare (STOP, BASTA,
  CANCELLAMI, DISISCRIVIMI, UNSUBSCRIBE…, in italiano o in inglese, scritta in
  qualsiasi modo) ferma gli SMS automatici del centro per quella persona
  (`CRM Lead.sms_opt_out`, con il momento): le automazioni lo saltano («Ha scritto
  STOP agli SMS del centro: non inviato»), la lista d'attesa manda la proposta per
  email, l'area non manda più le novità per SMS. Nel registro dei consensi il
  consenso al marketing è ritirato «Per SMS», o rifiutato se non era mai stato
  chiesto. La persona riceve la risposta («Non riceverà più gli SMS automatici di
  Centro Aurora. Scriva START per riceverli di nuovo.»), che resta nella
  conversazione. START li fa ripartire, il consenso no: si chiede di nuovo come
  sempre. Chi scrive a mano a quella persona lo vede sopra il box, e il suo SMS parte
  lo stesso. Una parola sola non fa partire le automazioni sugli SMS ricevuti. A un
  nome come mittente nessuno può rispondere, nemmeno STOP: chi manda SMS
  promozionali sceglie un numero.
- **Gli orari delle promozioni (fatto).** Un SMS di un'automazione che chiede il
  consenso al marketing parte dal lunedì al sabato, dalle 8 alle 22; scritto fuori da
  quegli orari aspetta il primo momento buono (le regole di Twilio per l'Italia). Un
  promemoria del centro, che il consenso non lo chiede, parte quando deve.

### 5. Costi e controlli (quinta parte, fatta)

- **Questo mese (fatto).** Sulla pagina di Twilio, sotto Controlla: quanto ha speso lo
  spazio dal primo del mese, come lo conta Twilio (i suoi «usage records»), per voce
  (chiamate con i minuti, SMS, numeri, registrazioni e trascrizioni, il resto), nella
  valuta dell'account. Lo vede chi paga lo spazio: il responsabile del centro
  sull'account del centro, l'agenzia sul suo. Quello che Twilio dice resta dieci
  minuti, poi si chiede di nuovo.
- **Il credito** è dell'account, e uno spazio non ne ha uno suo: Twilio non lo dice
  a chi ha solo le chiavi dello spazio. La pagina lo spiega: si vede e si ricarica su
  Twilio.
- **L'avviso di spesa (fatto).** «Avvisami quando il mese arriva a»: l'importo diventa
  un «usage trigger» dello spazio (sulla spesa totale, ogni mese), che Twilio non sa
  cambiare: un importo nuovo ne mette uno nuovo al posto del vecchio, vuoto lo toglie.
  Quando la spesa ci arriva Twilio chiama `spend_reached` e chi paga riceve la
  notifica «La spesa Twilio del mese è arrivata a …, oltre l'avviso a …», che apre la
  pagina di Twilio. Ogni ora `assicura()` lo rimette se qualcuno l'ha tolto nella
  console; sull'account dell'agenzia lo mette solo l'agenzia.
- **I problemi degli ultimi 7 giorni (fatto)**, dal registro di Twilio (Monitor),
  uno per codice con quante volte e l'ultima: quelli che un centro incontra detti da
  DottorCloud (il telefono spento, il numero che non esiste più, l'SMS fermato
  dall'operatore, il credito finito, i paesi non permessi, Twilio che non raggiunge
  DottorCloud), gli altri con le parole di Twilio e il codice; un pulsante apre il
  registro di Twilio.
- **Un SMS che non parte o non arriva (fatto)** dice perché con le stesse frasi e
  tiene il codice di Twilio (`CRM SMS Message.error_code`): quando Twilio lo rifiuta
  e quando Twilio poi dice che non è arrivato. Nel log restano solo il codice e lo
  stato, mai il numero né le parole.

### 6. I numeri che il centro ha già (sesta parte, fatta)

- **Un numero già nell'account del centro (fatto).** Sulla pagina di Twilio, accanto a
  «Nuovo numero», «Ho già un numero» → «Nell'account Twilio del centro»: il
  responsabile incolla di nuovo Account SID e Auth Token dell'account. Servono solo a
  quella richiesta e non restano: DottorCloud mostra i numeri dell'account fuori dallo
  spazio (uno su un trunk SIP resta dov'è, e lo dice), e quello scelto si sposta. Un
  numero italiano porta con sé i documenti già approvati, copiati nello spazio prima
  dello spostamento (il «bundle clone» di Twilio, approvato anche lì: l'SDK 8.5 non lo
  ha, DottorCloud lo chiede all'indirizzo di Twilio), e il suo indirizzo, scritto di
  nuovo nello spazio; poi il numero punta a DottorCloud ed entra nell'elenco dei numeri
  del centro. Solo nello spazio dell'account del centro: quello dell'agenzia è un altro
  account, e i codici di un account diverso da quello dello spazio non spostano niente.
- **Il numero storico di un altro operatore (fatto)**, «Con un altro operatore»: la
  pagina spiega le tre strade. Mostrarlo nelle chiamate (sotto), o l'operatore inoltra
  le chiamate a un numero del centro in DottorCloud (gli SMS non seguono), o il numero
  si porta su Twilio con il modulo di Twilio (dai grandi operatori, fino a sei
  settimane), con la guida di Twilio per l'Italia; arrivato nell'account, si sposta
  nello spazio come sopra.

### 7. Un numero verificato, da mostrare nelle chiamate (fatto)

Il centro tiene il suo fisso con il suo operatore e lo vuole nelle chiamate che fa da
DottorCloud. Non serve comprare un numero né mandare documenti: Twilio lo **verifica**
(«Verified Caller ID», verificato il 02/10/2026 sulla documentazione di Twilio).

- **Come si fa.** Su Impostazioni → Telefono → Telefonia → Twilio, Numeri →
  «Gestisci» → «Verifica un numero», o da «Ho già un numero» → «Con un altro
  operatore» → «Verificalo»: il numero, il suo nome, e se la linea ha un centralino
  le cifre da comporre dopo la risposta (un interno, `w` per mezzo secondo
  d'attesa) e i secondi prima della chiamata (da 0 a 60). Twilio chiama il numero
  **da +1 415 723 4000, in inglese** (altre lingue non ci sono), e chiede un codice di
  sei cifre che DottorCloud mostra sullo schermo: chi risponde lo digita sulla
  tastiera del telefono. **Nessun documento**: rispondere dimostra che la linea è
  del centro. Le chiamate verso quel numero continuano a squillare dove squillano.
- **Nello spazio.** La verifica si fa nello spazio di DottorCloud (il sottoaccount),
  perché è lo spazio che chiama: un numero verificato nell'account principale non
  vale per le chiamate dello spazio. Un numero che è già dello spazio non si
  verifica (Twilio risponde 21449), uno già verificato si ritrova (21450).
- **Come va a finire.** La riga del numero (`CRM Caller ID`) nasce «In attesa»,
  spenta; si accende quando Twilio dice che è verificato. Twilio lo dice alla fine
  della sua chiamata (`crm.integrations.twilio.api.caller_id_verified`, la sua
  StatusCallback, firmata come ogni sua richiesta); la finestra lo chiede ogni tre
  secondi finché aspetta, così lo sa anche un sito che Twilio non raggiunge; ogni ora
  `assicura()` rilegge i numeri dello spazio. Chi l'ha chiesto riceve l'avviso
  («Telefono») se la finestra era chiusa; dopo un quarto d'ora senza risposta la
  verifica è «Non riuscita» e si rifà con «Verifica di nuovo».
- **Toglierlo.** «Rimuovi» lo toglie da Twilio: non si mostra più; la riga resta,
  spenta. Se qualcuno lo aveva come propria linea, la pagina lo dice.
- **In Italia (AGCOM 106/25/CONS).** Dal 19 agosto 2025 un operatore italiano può
  bloccare una chiamata dall'estero che mostra un fisso italiano di un'altra rete, e
  Twilio mostra un numero italiano verificato in Italia solo per quanto lo lasciano
  gli operatori; dal 19 novembre 2025 un cellulare italiano è bloccato del tutto. La
  finestra della verifica, l'elenco dei numeri e la finestra della chiamata lo
  dicono: per essere sicuri che il numero si veda, si porta su Twilio. Verificare
  serve senza dubbi per le chiamate all'estero.
- **Solo numeri veri.** Si mostrano solo i numeri dello spazio e quelli verificati:
  una riga scritta a mano nel Desk non si offre più, Twilio rifiuterebbe la chiamata
  (13214). Un numero non verificato non si accende a mano.

## La stessa strada per l'agenzia

- Per un centro con la segreteria dell'agenzia lo spazio nasce **nell'account
  dell'agenzia**, `dottorcloud_twilio` in `common_site_config.json` (`account_sid`,
  `auth_token`), e i consumi li paga l'agenzia: «Usa l'account dell'agenzia», solo
  per l'agenzia.
- È il caso del listino: il telefono a 50 € al mese con 714 minuti inclusi.

## Cosa fa NPM2, una volta

- **Niente su Twilio Connect**: non si usa.
- **Per la segreteria**: l'account Twilio dell'agenzia, attivo, con le sue chiavi in
  `common_site_config.json`:

  ```json
  "dottorcloud_twilio": {"account_sid": "AC…", "auth_token": "…"}
  ```

## Come è fatta

| File | Cosa |
|---|---|
| `crm/telephony/collegamento_regole.py` | Senza sito: i due codici prima di chiedere a Twilio, il SID mascherato, il nome dello spazio, che cosa cambiare su un numero e sull'app, gli errori di Twilio a parole — provato con `unittest` |
| `crm/telephony/collegamento.py` | Il collegamento: lo spazio (nuovo, ritrovato, o il sottoaccount incollato), la chiave, l'app, i numeri puntati a DottorCloud; `assicura()` ogni ora; le chiamate della pagina (`get_twilio_connection`, `connect_twilio`, `connect_agency_twilio`, `check_twilio_connection`, `disconnect_twilio`) |
| `CRM Twilio Settings` | Di chi è l'account (`account_owner`), l'account (`main_account_sid`, `main_account_name`), lo spazio (`space_sid`, `space_name`), chi l'ha collegato e quando; tutto a permlevel 1, la pagina lo legge dal server |
| `frontend/src/components/Settings/Telephony/TwilioSettings.vue` + `utils/twilio.js` | La pagina: i tre passi, i due codici, lo stato, Controlla, Scollega; le stesse regole dei codici del server — provate |
| `crm/telephony/numeri_regole.py` | Senza sito: i tipi di numero e a che cosa servono, di chi è il numero, il prefisso di una zona, i campi e i documenti del regolamento con le parole di DottorCloud, i file che Twilio prende, la valutazione di Twilio riga per riga, il prezzo al mese, i documenti approvati che valgono per il numero dopo — provato con `unittest` |
| `crm/telephony/numeri.py` + `CRM Phone Number Request` | Le richieste: l'offerta (`get_number_offer`), i requisiti (`get_number_requirements`, con quello che era scritto per rimandarla), i numeri pronti (`search_numbers`), l'invio (`send_number_request`: solo i file del centro), ogni ora `aggiorna_le_richieste` con l'avviso, l'acquisto (`buy_number`), il rilascio (`release_number`), il togliere una bozza (`delete_number_request`) |
| `crm/telephony/inbound.py`, `routing.py`, `providers/base.py` (`Ring`, `Message`) | Chi squilla: tutti quelli raggiungibili insieme (`find_ringing`), per i secondi della segreteria; `nobody_answered`: l'annuncio con la richiamata o le scuse; il messaggio dopo l'annuncio quando il centro lo vuole |
| `crm/integrations/twilio/api.py` (`ring_ended`, `message_taken`, `message_recorded`) + `crm/telephony/messaggi.py` | Dove Twilio torna: lo squillo finito, il messaggio finito, la registrazione pronta; l'avviso a chi segue la persona (tipo «Call») |
| `frontend/src/components/Settings/Telephony/NewNumberDialog.vue` + `utils/numeri.js` | La finestra del nuovo numero e la scelta del numero; le richieste sulla pagina di Twilio, il rilascio sulla pagina dei numeri; il prezzo, il prefisso, i file e cosa manca prima di mandare — provati |
| `crm/telephony/uscita_regole.py` | Senza sito: dove può andare una chiamata (i paesi scelti, mai un numero a pagamento, un numero italiano anche senza +39), il cellulare italiano che l'AGCOM blocca, i permessi di Twilio da mettere — provato con `unittest` |
| `crm/telephony/uscita.py` + `CRM Twilio Settings.allowed_countries` | Le chiamate in uscita: `check_number` e `get_outbound_numbers` per la finestra, `perche_no` e `numero_da_mostrare` per `voice`, `allinea_i_paesi` (al salvataggio, al collegamento, ogni ora, solo nello spazio) |
| `frontend/src/components/Telephony/TwilioCallUI.vue` + `utils/chiamate.js` | La finestra della chiamata: il numero da mostrare, l'avviso AGCOM, il tastierino; i paesi sulla pagina di Twilio — le stesse regole del server, provate |
| `crm/telephony/sms_regole.py` | Senza sito: il nome del mittente che Twilio prende, quello fatto con il nome del centro, un messaggio che è solo STOP o START, gli orari delle promozioni — provato con `unittest` |
| `crm/telephony/sms.py` + `CRM Twilio Settings` (`sms_from`, `sms_sender_name`, `sms_sender_number`) | Il mittente di tutti gli SMS (`mittente()`) e le opzioni della pagina (`get_sms_sender_options`); STOP e START (`ascolta`, `ferma`, `riprendi`, `ha_fermato`) da `incoming_sms_handler`, la risposta tenuta nella conversazione |
| `frontend/src/components/Settings/SmsSenderLine.vue`, `Activities/SMSBox.vue` | Da dove partono gli SMS, sulle pagine dell'area e della lista d'attesa; sopra il box, la persona che ha scritto STOP |
| `crm/telephony/consumi_regole.py`, `errori_regole.py` | Senza sito: la spesa del mese per voce, l'importo dell'avviso e che cosa fare del trigger; i codici di Twilio a parole, i problemi raggruppati per codice — provati con `unittest` |
| `crm/telephony/consumi.py` + `errori.py`, `CRM Twilio Settings.spend_alert` | La spesa e i problemi per la pagina (`get_twilio_usage`), l'avviso come trigger dello spazio (`allinea_l_avviso`, al salvataggio e ogni ora), `spend_reached` che lo dice a chi paga; un codice di Twilio a parole (`errori.in_parole`), anche sugli SMS |
| `crm/telephony/trasloco_regole.py` | Senza sito: quale numero dell'account si sposta e quale resta (un trunk SIP), che cosa serve allo spazio prima (i documenti, l'indirizzo) — provato con `unittest` |
| `crm/telephony/trasloco.py` + `Settings/Telephony/MoveNumberDialog.vue` | «Ho già un numero»: i numeri dell'account del centro con i suoi codici incollati per quella richiesta (`get_account_numbers`), lo spostamento con il clone dei documenti e la copia dell'indirizzo (`move_number`); la guida per un numero di un altro operatore |
| `crm/telephony/verificati_regole.py` | Senza sito: il nome che Twilio tiene, l'interno e l'attesa come li prende, come è andata, quando una verifica è scaduta, i rifiuti di Twilio a parole — provato con `unittest` |
| `crm/telephony/verificati.py` + `Settings/Telephony/VerifyNumberDialog.vue`, `utils/verificati.js` | La verifica (`verify_number`, `verification_state`, `remove_verified`), la risposta di Twilio (`alla_fine_della_chiamata`), le verifiche dimenticate (`scadute`, ogni ora con la lista); la finestra con il codice e l'elenco con gli stati — provati con Twilio finto |

## Da decidere

1. **Il prezzo del telefono con l'account del centro.** Il listino dice 50 € al mese
   con 714 minuti inclusi, ma con l'account del centro i minuti li paga il centro a
   Twilio: i minuti inclusi lì non hanno senso.
2. **Exotel** (India) resta tra i fornitori: per i centri italiani non serve.

## Fonti

- Twilio, [Known Limitations for Connect Apps](https://support.twilio.com/hc/en-us/articles/36665782139931-Known-Limitations-for-Connect-Apps) e [Twilio Connect](https://www.twilio.com/docs/iam/connect)
- Twilio, [Subaccounts](https://www.twilio.com/docs/iam/api/subaccounts) e [Bundle Clones](https://www.twilio.com/docs/phone-numbers/regulatory/api/clones-resource)
- Twilio, [OutgoingCallerIds](https://www.twilio.com/docs/voice/api/outgoing-caller-ids) e [Verifying Caller IDs at Scale](https://www.twilio.com/docs/voice/api/verifying-caller-ids-scale)
- Twilio, Italia: [documenti dei numeri](https://www.twilio.com/en-us/guidelines/it/regulatory), [portabilità](https://www.twilio.com/en-us/guidelines/it/porting), [SMS](https://www.twilio.com/en-us/guidelines/it/sms), [prezzi della voce](https://www.twilio.com/en-us/voice/pricing/it), [prezzi dei numeri](https://assets.cdn.prod.twilio.com/pricing-csv/SiteNumbersPricing.csv)
- Twilio, [Regulatory and Compliance, ottobre 2025](https://www.twilio.com/en-us/blog/insights/2025-october-regulatory-updates) (AGCOM)
- AGCOM, [delibera 106/25/CONS](https://www.agcom.it/provvedimenti/delibera-106-25-cons)
