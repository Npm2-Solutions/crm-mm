# 58 · Fatture in Cloud: per il centro che fattura già lì

**Stato:** fatto (06/10/2026). Da provare con un account vero di Fatture in Cloud
prima del primo centro (vedi «Da verificare»).

## Il bisogno

- Un centro che **fattura già con Fatture in Cloud** (il programma di TeamSystem)
  vuole continuare a farlo: lì ha la numerazione, l'invio allo SdI, la
  conservazione, il commercialista che guarda i conti.
- In DottorCloud fa tutto il resto: l'appuntamento, la seduta, l'abbonamento, il
  pagamento alla reception, il PDF al paziente. **La fattura deve nascere lì** senza
  riscriverla.

## Cosa permette Fatture in Cloud (verificato il 06/10/2026)

- **L'API v2 è compresa in ogni abbonamento** di Fatture in Cloud, senza costi in
  più: il centro paga solo il suo abbonamento. Creare l'app per DottorCloud su
  developers.fattureincloud.it è gratuito.
- **OAuth 2**, codice di autorizzazione: il centro accede a Fatture in Cloud e
  consente; l'accesso dura un giorno e si rinnova con il refresh token, che dura un
  anno dall'ultimo rinnovo. L'indirizzo di ritorno è confrontato lettera per
  lettera, uno per app.
- **App privata o pubblica**: un'app nasce privata e la usano solo gli utenti che
  l'agenzia scrive nella sua lista (le email degli utenti di Fatture in Cloud).
  Pubblica dopo l'approvazione di Fatture in Cloud.
- **Limiti**: 1000 richieste l'ora per azienda e app, 40.000 al mese; con 429 si
  aspetta quanto dice Retry-After.
- **Le fatture**: crea, modifica, elimina documenti (fattura, nota di credito);
  calcola i totali di una fattura **senza crearla** (`/issued_documents/totals`);
  verifica l'XML, lo manda allo SdI, ne dà lo stato (`ei_status`), la ragione di
  uno scarto, l'XML.
- **Il Sistema TS**: i campi ci sono (`extra_data.ts_*`: invio sì o no, un tipo di
  spesa per documento, pagamento tracciato, opposizione), e Fatture in Cloud invia
  se nel suo account il Sistema TS è acceso.
- **Il bollo**: su una fattura elettronica `stamp_duty` è il bollo a carico di chi
  emette (DatiBollo, lo versa con l'F24); riaddebitato al cliente è una riga. Su una
  fattura cartacea `stamp_duty` è l'importo addebitato al cliente.
- **Account di prova**: l'agenzia può aprire un account Trial con un'azienda finta;
  l'invio allo SdI però c'è solo nei piani a pagamento.

## Com'è fatto

### Il collegamento (`crm/invoicing/fic/collegamento.py`)

- L'app è **dell'agenzia**, una per tutti i centri: `fic_client_id` e
  `fic_client_secret` in `common_site_config.json`. Ogni accesso passa dall'hub che
  già usano Meta e Google (`meta_hub_url`), che ripassa il codice al sito scritto
  nello stato firmato. Nello stato viaggia solo un numero a caso: il sito che ha
  chiesto lo ritrasforma nella sua azienda, e solo per la stessa sessione.
- **Impostazioni > Fatturazione > Fatture in Cloud**: il responsabile del centro
  preme «Collega Fatture in Cloud», accede lì e consente. Se chi accede vede più
  aziende (un commercialista), sceglie quella con la partita IVA dell'azienda che
  emette; partite IVA diverse non si accendono.
- Si leggono **aliquote IVA, conti e numerazioni** dell'azienda in Fatture in
  Cloud. Ogni trattamento IVA di qui (22%, esente art. 10, forfettario…) ha la sua
  aliquota là: scelta da sola dove ce n'è una sola, altrimenti la sceglie il centro.
  Ogni metodo di pagamento ha il suo conto (la cassa per i contanti, il POS per la
  carta, la banca per il bonifico), indovinato dal nome dove si può.
- L'interruttore **«Le fatture si emettono in Fatture in Cloud»** si accende solo
  quando non manca niente. Gli accessi si rinnovano da soli ogni ora vicino alla
  scadenza; un accesso perso dice «collegalo di nuovo» nella pagina e nelle cose
  che mancano per passare al reale.
- I token non escono dal server: sono campi password del documento
  `CRM Fatture in Cloud`, che solo il System Manager apre nel Desk.

### L'emissione (`crm/invoicing/fic/emissione.py`, `regole.py`)

- Al momento dell'emissione (`before_submit`, dopo i controlli del documento e
  prima del numero) la fattura calcolata qui si passa riga per riga
  (`regole.documento`: cliente, righe con la loro aliquota, cassa, rivalsa INPS,
  ritenuta, bollo, pagamento, riferimento della nota di credito, Sistema TS).
- **Prima Fatture in Cloud la somma** (`/issued_documents/totals`): IVA, ritenuta e
  totale da pagare devono essere i nostri al centesimo, o non si crea niente e la
  pagina dice quali importi non tornano.
- Poi la crea: **il numero è quello di Fatture in Cloud** (12, o 12/S con una
  numerazione), e la fattura qui lo prende (`document_number`, `fic_document_id`).
- Una transazione annullata dopo la creazione la **cancella anche là**
  (`after_rollback`, con l'accesso letto prima), prima di salvare un accesso
  rinnovato nel frattempo: il commit di quel salvataggio dimenticherebbe il resto. Una risposta persa per strada, o una
  cancellazione non riuscita, si ritrova al tentativo dopo con il segno che la
  fattura porta nell'oggetto interno (che il PDF non mostra): si aggiorna quella,
  non se ne crea un'altra.
- **Le fatture di prova restano qui**, e niente dei dati di prova arriva a Fatture
  in Cloud (`guardie.mai_fuori`).
- **L'elettronica parte da Fatture in Cloud**: il pulsante «Invia allo SdI» o
  l'invio automatico chiedono prima la verifica dell'XML a Fatture in Cloud, poi
  l'invio; l'XML trasmesso si conserva sulla fattura. Ogni dieci minuti si chiede lo
  stato di quelle in viaggio (consegnata, non consegnata, scartata con la ragione,
  esito dell'ente pubblico); scartata o non consegnata lo si dice a chi fattura.
- **Il pagamento**: una fattura alla persona emessa alla reception nasce pagata, sul
  conto del suo metodo; un incasso segnato dopo si segna anche là.
- **Annullare** una fattura non ancora partita la elimina anche da Fatture in Cloud;
  con l'accesso perso si annulla qui lo stesso, e la fattura dice di eliminarla anche
  là.
- **I crediti SdI del piano** non contano le fatture partite da Fatture in Cloud.

### Il Sistema TS

- **Due strade, una sola**: lo invia DottorCloud (come sempre, spesa per spesa, con
  le credenziali del centro: in Fatture in Cloud il Sistema TS resta spento), oppure
  lo invia Fatture in Cloud (la fattura gli arriva con i campi del Sistema TS, e qui
  lo stato dice «Lo invia Fatture in Cloud»). La stessa spesa due volte viene
  rifiutata.
- Fatture in Cloud manda **un solo tipo di spesa per fattura** e la fattura intera:
  una fattura con due tipi, o con una riga che al Sistema TS non va, si ferma prima
  con la proposta di farne due o di inviare da qui.

## Da sapere

- La scelta «di nessuno» (doc 49: lo SdI con Itala sull'account dell'agenzia) resta
  per chi non usa Fatture in Cloud. **Chi fattura con Fatture in Cloud non usa
  Itala**: numero, invio e conservazione sono di Fatture in Cloud, pagati nel suo
  abbonamento.
- **Le fatture ricevute** dai fornitori arrivano a Fatture in Cloud (il codice
  destinatario del centro è il suo): DottorCloud non le legge ancora da lì.
- Tipi diversi da fattura e nota di credito (una parcella, un'integrazione) si
  fanno in Fatture in Cloud.

## Da verificare con un account vero

- Come Fatture in Cloud arrotonda l'IVA di più righe con la stessa aliquota:
  DottorCloud la calcola riga per riga; se Fatture in Cloud la calcola sul
  riepilogo, una fattura con più righe al 22% e centesimi dispari può non tornare di
  un centesimo, e il controllo dei totali la ferma con le cifre.
- Che `stamp_duty` su una fattura cartacea entri nel totale da pagare come dice la
  guida.
- Che un incasso segnato dopo l'invio allo SdI passi anche là: si segna modificando
  i pagamenti del documento, e una fattura elettronica partita è in parte bloccata.
  Se Fatture in Cloud lo rifiuta, qui l'incasso resta e l'errore va nel registro.
- La cassa previdenziale insieme alla ritenuta e al bollo riaddebitato: Fatture in
  Cloud applica cassa e ritenuta alle stesse righe, DottorCloud la ritenuta anche sul
  bollo e la cassa no. Se i totali non tornano, la fattura si ferma prima.
