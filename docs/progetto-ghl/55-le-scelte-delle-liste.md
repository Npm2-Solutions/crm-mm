# 55 · Le scelte delle liste: filtra, ordina, raggruppa, colonne

**Stato:** fatto (06/10/2026).

## Il bisogno

Ogni lista del computer (Persone, Trattative, Aziende, Rubrica, Cose da fare,
Note, Chiamate) offre quattro menu per sceglierne i campi: **Filtro**, **Ordina**,
**Raggruppa per**, **Colonne** (e la bacheca le **Impostazioni Kanban**, i
responsabili i **filtri rapidi**). Aperti uno per uno, offrivano tutto quello che
il documento tiene, così come il programma di partenza lo elencava:

- **in inglese** in «Aggiungi colonna» e nei filtri rapidi («Source», «Medium»,
  «First Name»), con la descrizione tecnica del campo sotto ogni voce;
- **doppioni senza modo di distinguerli**: tre «Sorgente» (quella della persona e
  quelle del primo e dell'ultimo contatto), due «Data», due «Campagna», «Creato
  il» due volte, «Assegnato a» due volte nelle cose da fare;
- **codici e cose della macchina**: «Nome» che è il codice della persona
  (CRM-LEAD-…), «Serie», «Simile» (chi ha messo il cuore), «Commenti», «Tag», gli
  ID di Meta, il browser e le visite del tracciamento, dove il pannello delle
  conversazioni tiene il segno, il codice di una chiamata da Twilio; nella
  bacheca, sotto ogni campo, il suo nome tecnico e il suo tipo
  («deal_value - Currency»);
- **parole sbagliate**: «Responsabile» per chi ha creato il record (il
  responsabile è un'altra cosa), «Simile» per il cuore, «Referente» per la pagina
  da cui si arrivava, «Modified By» rimasto in inglese;
- **scelte che non servono**: ordinare per un testo lungo o un'immagine,
  raggruppare per un importo o per un istante al secondo (un gruppo per riga);
- **intestazioni dei gruppi** come le scrive il database: lo stato di una
  trattativa in inglese, «0» e «1» per un sì e un no, un collega per indirizzo
  email.

## Come funziona

- **Una regola sola**, senza sito, in `crm/liste/regole.py`: per ogni uso
  (`filtro`, `ordine`, `gruppo`, `colonna`) i tipi di valore che prende, i campi
  del framework che offre e con quali parole («Creato da», «Ultima modifica di»,
  «Preferito»), quello che nessuna lista offre (codice, serie, commenti, tag).
  Ogni campo una volta; due campi con lo stesso nome si distinguono per la
  sezione in cui stanno («Sorgente (Primo contatto)», «Sorgente (Ultimo
  contatto)»), quello che sta direttamente nella scheda tiene il suo nome. Il
  campo del documento vince su quello del framework che si chiama come lui (le
  cose da fare hanno il loro «Assegnato a»).
- **Dal modello del documento** (`crm/liste/campi.py`): i campi che la sessione
  può leggere, ognuno con la sua sezione e la sua scheda, meno quelli che un
  documento tiene solo per la macchina (`SOLO_PER_LA_MACCHINA`).
- **Le chiamate** (`crm/api/doc.py`): `sort_options`, `get_filterable_fields`,
  `get_group_by_fields` usano la regola; `get_list_fields` dà colonne, campi della
  bacheca e filtri rapidi, chiesti la prima volta che il menu si apre
  (`composables/campiDellaLista.js`), mai mentre la lista carica. Una colonna
  salvata con il nome che il framework le dava («Owner», «Like») si legge con il
  suo (`nome_della_colonna`).
- **I gruppi** (`utils/gruppi.js`): l'intestazione dice il valore come lo dice
  una riga: lo stato nelle parole di chi legge, lo stadio della persona nel suo
  contesto («Lead»), «Sì» e «No», un collega per nome, un giorno come data,
  «Non impostato» per chi non ha niente.
- **La bacheca**: la colonna, il titolo e i campi della scheda vengono dallo
  stesso elenco; i due elenchi che prima dipendevano l'uno dall'altro (la scheda
  restava vuota quando i campi arrivavano dopo) sono uno solo.
- **Le parole**: «Persona» per il documento della persona («Lead» resta lo
  stadio, con il suo contesto), «Pagina di provenienza» per il referrer.
- **Gli editor della scheda** (il pannello laterale, i campi dei Dati, la
  creazione veloce): la stessa regola con l'uso `scheda`, che prende ogni tipo di
  campo (anche le tabelle) e mai la struttura né i campi della macchina; le righe
  e le scelte nelle parole di chi legge, distinte, senza più il nome tecnico e il
  tipo sotto ogni voce («first_name - Data»); il pannello non ripropone un campo
  che ha già. Le colonne di una tabella (le proprie di ognuno) si leggono
  tradotte.

## Da sapere

- Un nuovo campo che un documento tiene solo per la macchina va in
  `campi.SOLO_PER_LA_MACCHINA`; un nuovo uso, in `regole.TIPI` e
  `regole.STANDARD_PER_USO`.
- Un filtro, un ordine o un gruppo già salvato in una vista su un campo che la
  lista non offre più continua a funzionare: semplicemente non si sceglie più.
