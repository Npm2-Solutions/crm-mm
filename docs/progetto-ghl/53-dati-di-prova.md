# 53 · Dati di prova: un centro pieno, tolto senza lasciare traccia

**Stato:** in corso (04/10/2026). Prima parte: il motore, la rimozione, le
protezioni e la parte base.

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
  - **Aziende e convenzioni**: cinque aziende e le loro trattative in fasi
    diverse, una vinta e una persa.
  - **Cose da fare, note, telefonate**: anche per chi carica la demo, con due
    colleghi che lo menzionano.
- È **sempre la stessa demo**: le scelte vengono da un seme fisso, le date dal
  giorno in cui si carica.

### Come si crea (`crm/demo/modo.py`)

- Ogni record passa dai suoi controller e dai doc events dei moduli: la demo è il
  prodotto che lavora, non righe scritte di lato.
- Mentre una parte gira **niente esce**: le email non partono, i lavori in coda
  non si accodano, il browser non riceve messaggi, le automazioni tacciono,
  l'appuntamento non si copia nel calendario del framework (né nella sua email
  quotidiana), nessuna piattaforma di prenotazione viene avvisata, la ricerca
  globale (che le schermate di DottorCloud non leggono) non registra nulla.
- **Ogni record creato finisce nel registro** (`CRM Demo Record`), anche quelli
  che i controller creano da soli: il contatto della persona, l'assegnazione, la
  versione, il commento, la notifica. Lo scrive un `after_insert` su tutti i
  doctype, attivo solo durante la creazione. Il registro si scrive man mano,
  prima di ogni commit: un caricamento interrotto resta tutto rimovibile.
- Quello che è del prodotto e non della demo resta fuori dal registro
  (`fuori_dal_registro`): la pipeline dei nuovi clienti, fatta come la fa il
  prodotto quando il centro non ce l'ha.
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
   impostazioni, sessioni e permessi; i file sul disco; i contatori dei nomi
   tornano all'ultimo numero ancora usato (mai sotto un record esistente).

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
  chi è entrato in DottorCloud li vede, per provarla.

## Dove si usa

- **Impostazioni > Il centro > Dati di prova**: cosa contengono, il caricamento
  con l'avanzamento, i numeri, le parti nuove da aggiungere, la rimozione.
- La voce «Togli i dati di prova» nella barra laterale e nella pagina «Altro» del
  telefono, finché ci sono.
- Alla fine della configurazione iniziale il caricamento parte da solo, in coda.
- Serve la capacità `dati_prova.gestisci` (il responsabile del centro).

## Prossime parti

- **Conversazioni, lista d'attesa, abbonamenti, cicli, preventivi**: messaggi
  email, WhatsApp e SMS con le persone, chi aspetta un posto, gli abbonamenti e i
  cicli in corso, i preventivi in ogni stato.
- **Fatturazione, moduli e consensi, documenti, area clienti, piani**: le fatture
  di prova, i moduli firmati, i documenti consegnati, l'area di una persona, i
  piani e i programmi.
- **La clinica**: pazienti, cartelle e visite firmate, la sintesi, il dossier,
  l'odontogramma e i piani di cura, le diete.
