# 53 · Dati di prova: un centro pieno, tolto senza lasciare traccia

**Stato:** in corso (05/10/2026). Prima parte: il motore, la rimozione, le
protezioni e la parte base. Seconda parte: cicli, preventivi, abbonamenti, lista
d'attesa, conversazioni.

## Il bisogno

- Chi apre DottorCloud vuoto e carica i dati di prova deve trovare **tutto pieno**:
  l'agenda di oggi e delle settimane passate, le persone con la loro storia, le
  trattative in ogni fase, le cose da fare, le dashboard con i loro numeri.
- **Il CRM di base** fa la sua parte, sempre uguale; **ogni modulo** aggiunge la
  sua (la fatturazione le fatture, la clinica le cartelle). Un modulo acceso dopo
  porta la sua parte al caricamento successivo.
- **Toglierli deve essere facile, veloce e completo**: dopo, niente resta
  leggibile in giro.

## Com'era

- Una demo inglese di Frappe CRM: dodici persone americane, sette trattative nelle
  fasi inglesi, tre utenti con i vecchi ruoli, gli avatar di «Sarah Connor».
- Niente agenda, niente servizi, niente accoglienza, niente moduli.
- **La rimozione lasciava tracce**: le aziende e i contatti, i commenti «Deleted»,
  le righe di «Deleted Document» con tutto il record dentro, la ricerca globale, le
  email in coda (le notifiche partivano davvero verso gli indirizzi della demo).
  Una persona diventata paziente bloccava tutta la rimozione.

## Come funziona

### Le parti

- `crm/demo/registro.py`: una **parte** (`Parte`) è la quota di un modulo, con la
  sua chiave, il modulo del piano che la accende e le parti che le servono prima
  (`dopo`). Il modulo la registra dal suo `registra()`, come le capacità.
- Al caricamento si fanno le parti dei moduli **accesi o in prova**, in ordine, non
  ancora fatte. Quelle fatte sono in un valore del sito (`crm_demo_data_parts`):
  una parte fallita a metà non conta come fatta.
- Le parti di base (`crm/demo/base.py`, `crm/demo/simulazione.py`):
  - **La squadra**: sei colleghi con il loro livello (responsabile, segreteria,
    fisioterapista, osteopata, dietista, chinesiologo), la qualifica, i turni, le
    festività e un'assenza. Nessuna password: non entrano.
  - **Stanze e servizi**: quattro stanze, dieci servizi con prezzi e durate, le
    lezioni di gruppo, un listino in convenzione.
  - **Persone e appuntamenti**: tre mesi di vita del centro, giorno per giorno.
    Ogni turno si riempie con la seduta che tocca a chi è in cura o con una
    persona nuova; le lezioni hanno i loro abituali. Una persona arriva pochi
    giorni prima della prima visita, dal sito, da un amico, da Instagram; una
    richiesta apre la trattativa nella pipeline dei nuovi clienti. **Le regole del
    CRM fanno il resto, come per un centro vero**: la prenotazione sposta la
    trattativa, la prima visita la vince e fa la persona cliente (o paziente, con
    la clinica). Il passato è venuto, mancato o disdetto; oggi c'è chi è già
    passato, chi è in sala d'attesa e chi deve arrivare; qualche giorno recente è
    rimasto da segnare; le prossime tre settimane sono prenotate sempre meno.
    Una mamma prenota e paga per il figlio. Il consenso al marketing c'è o no.
  - **Cicli e preventivi, alla prima visita**: dopo la prima visita il percorso si
    concorda come in un centro vero. La segreteria vende un **ciclo di sedute**
    (cinque o dieci di fisioterapia, cinque di tecar, pagato tutto insieme o seduta
    per seduta, a volte con una scadenza), oppure il professionista consegna un
    **preventivo** del percorso, una riga per seduta, con il suo PDF: accettato
    (subito o il giorno dopo), rifiutato con il motivo, o ancora da decidere se la
    visita è recente. Il resto lo fa il prodotto: le sedute dopo entrano nel ciclo
    («seduta 4 di 10», al prezzo del ciclo) o prendono la loro riga del preventivo,
    fatta quando la persona viene; il preventivo si completa da solo; la pipeline
    dei preventivi segue (consegnato, accettato, rifiutato). Chi rifiuta non torna
    per il percorso.
  - **Aziende e convenzioni**: cinque aziende e le loro trattative in fasi
    diverse, una vinta e una persa.
  - **Cose da fare, note, telefonate**: anche per chi carica la demo, con due
    colleghi che lo menzionano.
  - **Abbonamenti** (`crm/demo/abbonati.py`): tre tipi in vendita (Pilates otto
    ingressi al mese che si rinnova da solo, posturale di tre mesi sospendibile,
    tutte le lezioni per sei mesi a rate) e gli abituali delle lezioni che li hanno
    comprati alla prima lezione. Nelle lezioni già prenotate ognuno usa gli ingressi
    del suo e gli altri pagano il loro posto, il mese finito si rinnova, il
    promemoria della scadenza parte (verso nessuno), una settimana saltata o le
    vacanze sono una sospensione che sposta la fine.
  - **Lista d'attesa** (`crm/demo/in_attesa.py`): chi aspetta un posto con
    l'osteopata (una con urgenza), con la dietista, un sabato mattina, con i giorni
    e le ore che vanno bene; il motore della lista trova un posto libero e lo
    offre: un'offerta aspetta la risposta, due sono state confermate e prenotate;
    una persona ha trovato posto altrove, a un'altra sono finiti i giorni. La
    lezione più piena della settimana si riempie e due persone aspettano un posto.
  - **Conversazioni** (`crm/demo/conversazioni.py`): email tra il centro e le sue
    persone (la prima visita, la fattura per la detrazione, la convenzione, il
    referto, la lezione di prova, una disdetta...), e SMS e WhatsApp dove il centro
    li ha attivi: un canale spento non mostra nulla, quindi non si scrive. Ogni
    messaggio al suo momento; le conversazioni sono quasi tutte gestite, alcune
    aspettano il centro (quelle della segreteria assegnate a chi carica la demo),
    una è rimandata di due giorni.
- Le parti dei moduli del CRM, registrate dal loro `registra()`:
  - **Moduli e consensi** (`crm/moduli/demo.py`): il responsabile ha pubblicato
    l'informativa con i due consensi (presa visione e novità) e un questionario di
    benvenuto, chiesti a chi non li ha ancora firmati; la scheda della seduta del
    fisioterapista; il modulo «Richiedi informazioni» del sito. **Quello che si firma
    si firma oggi, con il suo PDF e le sue prove**: una firma non si data mai
    indietro. Il centro ha cominciato stamattina: la segreteria ha mandato il link a
    chi viene nei prossimi sette giorni, e molti hanno già firmato da casa, come lo
    farebbe una persona (apre il link, chiede il codice, lo legge nella sua email,
    compila, firma); qualcuno si è fermato a metà, altri non l'hanno ancora aperto.
    Chi è arrivato oggi ha firmato sul tablet dell'accoglienza; il fisioterapista ha
    scritto le schede delle sue ultime sedute; tre persone hanno scritto dal sito
    (la persona trovata o creata, il modulo con il suo PDF, i consensi, la
    trattativa). Così la demo è piena a qualunque ora si carichi.
  - **Documenti** (`crm/documenti/demo.py`): il contratto di ogni abbonamento (un
    PDF con le sue condizioni), firmato e consegnato a mano; il certificato per
    l'attività non agonistica portato dagli abituali delle lezioni, scansionato; il
    contratto di alcuni anche online (il link per email, il codice detto allo
    sportello), e una persona l'ha già scaricato dalla pagina. Archiviati oggi,
    come i moduli.
  - **Fatturazione** (`crm/invoicing/demo.py`, con il modulo «fatturazione»), solo
    dove il centro non ha ancora un'azienda che emette: un centro che fattura già
    non riceve fatture dalla demo, mai un numero della sua serie.
    - L'azienda della demo è **in prova**, con un nome che lo dice («… (dati di
      prova)») e una partita IVA di un ufficio che non ne dà: nessuno ce l'ha. Le sue
      fatture sono fatture di prova, sulla loro serie (`2026/PROVA-S/1`), con la
      fascia sul PDF, il resoconto al Sistema TS controllato e mai mandato, niente
      allo SdI.
    - L'azienda della demo è quella che emette finché c'è: un'azienda del centro
      spenta tiene il suo segno di predefinita, e lo ritrova quando la demo se ne va.
    - Il responsabile risponde alle tre domande della preimpostazione sanitaria
      (una struttura, il regime ordinario, i codici della Regione): è la parte del
      Sistema TS (`crm/tessera_sanitaria/demo.py`), che la registra nella demo della
      fatturazione (`registra_preparazione`) come registra tutto il resto, perché la
      fatturazione non lo conosce. Ogni servizio
      della demo ha la sua scheda, come la fa la pagina dei servizi: esente per chi è
      professione sanitaria, tassata al 22% e allo SdI per chi non lo è (l'osteopata,
      il chinesiologo delle lezioni). Mai una scheda del centro legata a un servizio
      della demo.
    - La segreteria fattura le visite dei tre mesi, ognuna nel suo giorno e
      nell'ordine dei giorni, come sono state pagate: carta, contanti, bonifico;
      qualcuno si è opposto al Sistema TS. I cicli pagati per intero si fatturano il
      giorno in cui sono stati venduti. Gli ultimi tre giorni restano da fatturare;
      una fattura è corretta da una nota di credito.
    - Il codice fiscale di chi paga è coerente con il suo nome, ma nato in un luogo
      che nessun codice ha (una «Y»): non è di nessuno.
    - Le rate degli abbonamenti non si fatturano: sono stati venduti prima che ci
      fossero le schede.
- È **sempre la stessa demo**: le scelte vengono da un seme fisso, uno per
  parte (una parte è la stessa qualunque altra sia venuta prima), le date dal
  giorno in cui si carica.

### Come si crea (`crm/demo/modo.py`)

- Ogni record passa dai suoi controller e dai doc events dei moduli: la demo è il
  prodotto che lavora, non righe scritte di lato.
- Mentre una parte gira **niente esce**: le email non partono, i lavori in coda
  non si accodano, il browser non riceve messaggi, le automazioni tacciono,
  l'appuntamento non si copia nel calendario del framework (né nella sua email
  quotidiana), nessuna piattaforma di prenotazione viene avvisata, la ricerca
  globale (che le schermate di DottorCloud non leggono) non registra nulla, e il
  sigillo dei PDF non chiede la marca temporale (`sigillo.marcatore`): un modulo
  della demo non consuma le marche che il centro compra.
- **Un'email resta nella parte** invece di partire (`registro.posta_per`): la
  persona della demo la legge come farebbe nella sua casella, per il link di un
  modulo o il codice che lo apre. Così la demo passa dalle stesse pagine di una
  persona vera, con le prove vere di quello che è successo.
- **Ogni record creato finisce nel registro** (`CRM Demo Record`), anche quelli
  che i controller creano da soli: il contatto della persona, l'assegnazione, la
  versione, il commento, la notifica. Lo scrive un `after_insert` su tutti i
  doctype, attivo solo durante la creazione. Il registro si scrive man mano,
  prima di ogni commit: un caricamento interrotto resta tutto rimovibile.
- Quello che è del prodotto e non della demo resta fuori dal registro
  (`fuori_dal_registro`): le pipeline dei nuovi clienti e dei preventivi, fatte
  come le fa il prodotto quando il centro non le ha.
- Il caricamento è un lavoro in coda (un paio di minuti a grandezza piena); la
  pagina segue l'avanzamento dal socket.

### Come si toglie (`crm/demo/togli.py`)

Dal registro e dal database, non dai controller: un modulo firmato, una fattura di
prova emessa, la scheda di un paziente, una pipeline con trattative si tolgono come
il resto, in pochi secondi (circa 6.500 record in meno di 4 secondi).

1. **Quello che il centro ha adottato resta**: un servizio, una stanza, un listino
   che un record del centro usa è del centro ora, ed esce dal registro.
2. **Quello che riguarda la demo se ne va con lei, chiunque l'abbia scritto**:
   una nota del centro su una persona della demo, un appuntamento prenotato per
   lei, un'email. Quello che la nomina soltanto resta, senza il riferimento (una
   persona del centro la cui azienda era della demo).
3. Se ne vanno le righe con le loro tabelle figlie, poi tutto quello che il
   framework tiene accanto: versioni, commenti, comunicazioni, assegnazioni,
   condivisioni, notifiche, log, la ricerca globale, i documenti eliminati, le
   email in coda verso gli indirizzi della demo; i colleghi della demo con ruoli,
   impostazioni, sessioni e permessi; i file sul disco (i PDF dei preventivi e dei
   moduli firmati, i tratti delle firme, i contratti, le scansioni); le prove di un
   modulo o di una consegna se ne vanno con la loro catena intera; i
   contatori dei nomi tornano all'ultimo numero ancora usato, mai sotto un record
   esistente né sotto dov'erano prima della demo (`crm_demo_data_series`), e quelli
   che la demo ha cominciato, vuoti, se ne vanno.

I test contano ogni tabella prima e dopo: devono tornare uguali.

### Nessuno riceve nulla (`crm/demo/guardie.py`)

Finché i dati di prova ci sono:

- un'**email** a un indirizzo della demo esce dalla coda prima di partire (gli
  indirizzi sono su example.com, che non riceve posta);
- un **WhatsApp** o un **SMS** al numero di una persona della demo resta nella
  conversazione e non arriva a Meta né a Twilio;
- una **chiamata** a una persona della demo non parte, e lo dice;
- una **notifica** su un record della demo resta nel pannello, mai per email;
- la **pagina di prenotazione** non mostra i servizi della demo ai visitatori;
  chi è entrato in DottorCloud li vede, per provarla;
- i **moduli della demo** (l'informativa, il questionario) si chiedono solo alle
  persone della demo: una persona vera prenotata mentre la demo c'è non riceve il
  link e non li deve allo sportello (`solo_per_la_demo`). Il centro li usa
  scegliendoli, e allora restano suoi;
- i **primi passi** contano solo quello che è del centro (`primi_passi.c_e`): i
  servizi, i colleghi, le persone e gli appuntamenti della demo non fanno un passo
  al posto suo, e la scheda continua a dire cosa resta da preparare;
- un **messaggio o una chiamata in arrivo** da un numero che è anche di una
  persona della demo non viene mai attaccato a lei (`persona_vera`): i numeri della
  demo sembrano quelli di chiunque, e quello che è attaccato a una persona della
  demo se ne va con la demo. Va alla persona vera con quel numero, o a una nuova.

## Dove si usa

- **Impostazioni > Il centro > Dati di prova**: cosa contengono, il caricamento
  con l'avanzamento, i numeri, le parti nuove da aggiungere, la rimozione.
- La voce «Togli i dati di prova» nella barra laterale e nella pagina «Altro» del
  telefono, finché ci sono.
- Alla fine della configurazione iniziale il caricamento parte da solo, in coda.
- Serve la capacità `dati_prova.gestisci` (il responsabile del centro).

## Prossime parti

- **Area clienti e piani** (con il modulo «area»): gli inviti, la bacheca, i piani
  e i programmi pubblicati.
- **La clinica**: pazienti, cartelle e visite firmate, la sintesi, il dossier,
  l'odontogramma e i piani di cura, le diete.
