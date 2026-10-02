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

- **Chi risponde**: più persone insieme (nel browser o sul cellulare) per qualche
  secondo, poi la segreteria con il messaggio e la richiamata, o un messaggio
  lasciato (registrato, trascritto, segnalato a chi segue la persona).
- **Il numero da cui si chiama**, scelto per chiamata tra quelli del centro, con
  l'avviso AGCOM su un mobile.
- **La tastiera** durante la chiamata, per i menu degli altri.
- **I paesi che si possono chiamare**: l'Italia, e quelli che il centro aggiunge,
  contro le frodi sui numeri a pagamento.

### 4. Gli SMS (quarta parte)

- **Un mittente del centro** per tutti i messaggi automatici (promemoria, lista
  d'attesa, area clienti, automazioni): il suo nome, o il numero mobile se vuole le
  risposte. Oggi ce ne sono quattro, uno per posto.
- **«STOP»** in risposta toglie il consenso agli SMS promozionali, dal registro dei
  consensi.

### 5. Costi e controlli (quinta parte)

- **Quanto ha speso lo spazio questo mese**, per voce (chiamate, SMS, numeri,
  registrazioni), il credito dell'account e un avviso quando scende.
- **Gli errori di Twilio a parole**: un numero senza documenti, il credito finito,
  un indirizzo che non risponde.

### 6. I numeri che il centro ha già (sesta parte)

- **Un numero già nell'account del centro** si sposta nello spazio: DottorCloud
  chiede il token una volta per quella sola operazione e copia i documenti già
  approvati (Bundle Clones).
- **Il numero storico di un altro operatore**: o lo si inoltra al numero di
  DottorCloud (lo fa l'operatore), o lo si porta su Twilio con il modulo di Twilio,
  con la guida in DottorCloud; arrivato nell'account, si sposta nello spazio.

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
| `frontend/src/components/Settings/Telephony/NewNumberDialog.vue` + `utils/numeri.js` | La finestra del nuovo numero e la scelta del numero; le richieste sulla pagina di Twilio, il rilascio sulla pagina dei numeri; il prezzo, il prefisso, i file e cosa manca prima di mandare — provati |

## Da decidere

1. **Il prezzo del telefono con l'account del centro.** Il listino dice 50 € al mese
   con 714 minuti inclusi, ma con l'account del centro i minuti li paga il centro a
   Twilio: i minuti inclusi lì non hanno senso.
2. **Exotel** (India) resta tra i fornitori: per i centri italiani non serve.

## Fonti

- Twilio, [Known Limitations for Connect Apps](https://support.twilio.com/hc/en-us/articles/36665782139931-Known-Limitations-for-Connect-Apps) e [Twilio Connect](https://www.twilio.com/docs/iam/connect)
- Twilio, [Subaccounts](https://www.twilio.com/docs/iam/api/subaccounts) e [Bundle Clones](https://www.twilio.com/docs/phone-numbers/regulatory/api/clones-resource)
- Twilio, Italia: [documenti dei numeri](https://www.twilio.com/en-us/guidelines/it/regulatory), [portabilità](https://www.twilio.com/en-us/guidelines/it/porting), [SMS](https://www.twilio.com/en-us/guidelines/it/sms), [prezzi della voce](https://www.twilio.com/en-us/voice/pricing/it), [prezzi dei numeri](https://assets.cdn.prod.twilio.com/pricing-csv/SiteNumbersPricing.csv)
- Twilio, [Regulatory and Compliance, ottobre 2025](https://www.twilio.com/en-us/blog/insights/2025-october-regulatory-updates) (AGCOM)
- AGCOM, [delibera 106/25/CONS](https://www.agcom.it/provvedimenti/delibera-106-25-cons)
