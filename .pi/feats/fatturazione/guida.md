# Fatturazione elettronica

> Fatture per servizi di ogni tipo, sanitari compresi. Il CRM emette il documento,
> lo calcola, lo numera, scrive l'XML FatturaPA, comunica le spese sanitarie al
> Sistema TS — e si rifiuta, con un 403 lato server, di mandare allo SdI una
> fattura sanitaria intestata a una persona fisica.

Il modulo e' `crm/invoicing/`. La documentazione tecnica sta nel suo
[README](../../../crm/invoicing/README.md); qui c'e' come si usa.

---

## Due moduli, una direzione

Il codice e' diviso come fossero due app, perche' un domani possano esserlo:

- **`crm/invoicing`** emette, calcola, stampa, conserva e trasmette documenti per
  qualsiasi settore. Non sa che esiste il sanitario: niente professioni, niente tipi
  spesa, niente delega, niente pazienti;
- **`crm/tessera_sanitaria`** aggiunge la meta' sanitaria e si innesta da sola, su
  tre punti di estensione.

La dipendenza va in una direzione sola, e c'e' un test che lo verifica. In
`crm/hooks.py` c'e' la riga che decide che il modulo TS e' installato: **togliendola
resta un sistema di fatturazione funzionante**.

---

## Il modulo chiede solo quello che non puo' dedurre

Due assi, indipendenti. **Quale modulo** decide cosa esiste; **singolo o centro**
decide cosa ti viene chiesto.

| | Singolo | Centro |
|---|---|---|
| Senza Sistema TS | consulente, sviluppatore | studio associato, agenzia |
| Con Sistema TS | osteopata, psicologo | poliambulatorio |

Il campo che si ribalta e' l'erogatore. Chi eroga decide il regime IVA, la cassa e —
col modulo sanitario — se il documento puo' passare dallo SdI. In un centro e' il
campo piu' importante della riga. Per chi lavora da solo e' sempre la stessa persona,
su un campo con un solo valore possibile, e chiederlo sessanta volte al giorno e'
attrito e basta.

Percio' **si deduce, non si configura**: si contano gli erogatori attivi. Uno, e il
campo sparisce gia' compilato. Due, e ricompare. Chi assume il secondo fisioterapista
non deve ricordarsi di cambiare niente. Zero non e' uno: un registro vuoto non deve
leggersi come «singolo».

Nascosto e non in sola lettura, perche' un campo bloccato occupa comunque una colonna
e invita comunque un click.

## La fattura nasce dall'appuntamento

L'agenda sa gia' le tre cose da cui dipende il routing — chi e' il cliente, chi
eroga, che prestazione — piu' la data. Riscriverle a mano e' la differenza fra un
sistema che si usa fra un paziente e l'altro e uno che si abbandona il giovedi'. Un
centro da sei professionisti fa circa **sessanta documenti al giorno**: a quel ritmo
ogni interazione in piu' e' un minuto al giorno.

Nel pannello, sotto «Da fare», c'e' la coda **«Dall'agenda, non ancora fatturati»**:
appuntamenti passati che non hanno prodotto un documento. Solo passati — una lista che
mostra le prenotazioni di domani e' una lista di cui non ti fidi. Un bottone apre la
bozza, gia' compilata, nella finestra della fattura.

**E la bozza dice dove andra' prima di essere emessa**: in cima alla finestra,
*Fattura elettronica* oppure *PDF + Sistema TS*, con la riga che lo spiega. L'errore
si vede prima di farlo, non dopo — un documento che si scopre non emettibile al
momento dell'emissione ha gia' consumato il tempo di chi l'ha scritto, col cliente
ancora davanti.

---

## Dove si configura

Tutto sta nel gruppo **Fatturazione** delle Impostazioni: *Azienda emittente*;
*Servizi e professionisti*, con le schede dei servizi fatturabili, dei professionisti
che li erogano e dell'albo delle qualifiche; *Prova e attivazione*; le *Opzioni*
comuni a ogni documento.

La scheda dell'azienda e' divisa per argomento. Il centro vede tre schede:
*Azienda*, *Fatturazione* (cassa, ritenuta, bollo) e *Sanitario* (chi emette, i
codici della struttura, le **credenziali del Sistema TS**). Il resto e'
dell'agenzia e sta sul livello di permesso 1 (System Manager): la numerazione, i
*Documenti* (forma e conservazione), la *Trasmissione* (il canale, Itala, la prova)
e la modalita' e il certificato del Sistema TS. Una schermata non disegna mai un
campo che chi la guarda non puo' leggere (doc 49).
Le schermate rendono il layout dei DocType, quindi le spiegazioni che leggi sotto
ogni campo sono le stesse scritte nella definizione — una regola spiegata una
volta sola non puo' divergere dall'interfaccia che la mostra.

Il pannello `/crm/fatture` resta la console dell'operatore: cosa e' stato emesso e
cosa aspetta ancora un bottone. Non si configura niente da li'.

**I codici si scelgono per nome.** Ogni campo che salva un codice dell'Agenzia o
del Sistema TS (regime, natura IVA, cassa, ritenuta, causale, modalita' di
pagamento, tipo di spesa...) offre le scelte col loro nome e una riga che dice
quando si usano; si salva il codice. Con la clinica accesa si vedono solo quelle di
un centro medico, e i tipi di spesa sono quelli che la categoria di chi emette puo'
usare. Un valore scelto prima resta nel suo campo anche se il profilo non lo
propone piu' (doc 45).

---

## Prima in prova, poi attiva

Ogni azienda **parte in prova** (doc 49). Una fattura si fa, si emette e si manda
come sara' dal vivo, ma e' di prova:

- ha una serie sua, `2026/PROVA-S/1`: la numerazione vera parte da uno il giorno in
  cui si attiva, senza buchi;
- il PDF ha la fascia «Fattura di prova: non ha valore fiscale»;
- quella elettronica va all'ambiente di prova di Itala, e allo SdI non arriva niente;
- la comunicazione al Sistema TS si controlla all'emissione e non parte;
- non fa un cliente ne' un paziente, e non compare nell'area del paziente.

La pagina delle fatture lo dice («Fatturazione in prova»), la finestra della fattura
ha il segno «Prova». **Prova e attivazione** dice cosa manca e di chi e' da fare;
quello che impedisce di attivarla porta la croce rossa. Attivando, le fatture di
prova vengono tolte e da quel momento ogni fattura e' vera. Tornare in prova e'
dell'agenzia, e solo finche' non c'e' una fattura vera.

---

## Prima di emettere: quattro cose

Con la clinica accesa la fatturazione e' quella di un centro medico, e si imposta
con **tre domande** in cima alla pagina dell'azienda emittente: chi emette (una
struttura autorizzata, un medico o dentista a suo nome, un altro professionista
sanitario a suo nome, una struttura accreditata), i codici della struttura o la
professione, il regime. Da li' vengono categoria del Sistema TS, cassa e ritenuta;
i servizi dell'agenda diventano schede sanitarie esenti con un clic nella pagina
dei servizi fatturabili (doc 46).

### 1. L'azienda emittente — `CRM Invoicing Company`

Chi firma le fatture. Partita IVA, sede, regime fiscale, cassa e ritenuta,
modalita' del bollo, formato di numerazione. Se lo studio e' sanitario, anche la
categoria presso il Sistema TS e — solo per strutture, farmacie, parafarmacie e
ottici — il Codice Proprietario: codice regione, codice ASL e codice struttura
(SSA).

Il formato di numerazione si valida **quando salvi l'azienda**, non al primo invio
al Sistema TS: `numDocumento` accetta al massimo 20 caratteri dell'alfabeto
`[A-Za-z0-9_./-]`, quindi niente spazi, `#`, accenti o `:`. Un formato scelto a
posteriori si scopre a gennaio che non passa, e a quel punto sono migliaia di
righe.

Puoi avere piu' aziende emittenti: una e' predefinita.

### 2. Il registro delle qualifiche — `CRM Professional Qualification`

Cinquantasei voci, seminate all'installazione: professioni sanitarie, ordinistiche
(avvocato, commercialista, ingegnere, consulente del lavoro...), non ordinistiche
(consulente, formatore, sviluppatore) e societa'.

Ogni voce dice quattro cose: se la prestazione e' esente IVA, se va comunicata al
Sistema TS, se la fattura elettronica via SdI e' **vietata**, **obbligatoria** o
ammessa, e quale cassa si applica.

**Il registro e' tuo.** Il file `engine/professioni.py` e' il punto di partenza
documentato — e' dove sta la ricerca — ma i record vincono, e una tua correzione
non viene mai sovrascritta da una migrazione. Vincono anche sul registro sanitario
spedito: una qualifica che rendi ordinaria resta ordinaria, una che spegni viene
rifiutata, non torna com'era. Con la clinica accesa l'elenco mostra le professioni
sanitarie e quelle in uso; le altre sono dietro «Mostra le altre professioni».

Le voci con `needs_verification` sono i punti che il commercialista deve chiudere
prima del go-live: ostetrica (cassa), massoterapista (categoria TS), geometra
(aliquota del contributo), agente di commercio (base della ritenuta), formatore
(esenzione art. 10 n. 20). Li trovi tutti in *Cosa manca* nel pannello.

### 3. Gli erogatori — `CRM Service Provider`

Chi esegue la prestazione, con la sua qualifica. **La qualifica non e' un dato
anagrafico: e' cio' che decide il tipo di spesa e il regime IVA.** In un
poliambulatorio con calendario condiviso un'assegnazione sbagliata non da' errore
— da' righe scartate a gennaio.

### 4. Le schede dei servizi — `CRM Billable Service`

**Un servizio senza scheda non e' fatturabile.** La scheda dice se la prestazione
e' sanitaria, se e' esente e con quale riferimento normativo, l'aliquota o la
natura IVA (*Perche' non c'e' IVA*), il tipo di spesa per il Sistema TS, se e'
soggetta a bollo.

Il campo *Verificato dal commercialista* non blocca nulla: finche' non e' spuntato,
l'esenzione su quel servizio e' un'assunzione che nessuno ha confermato.

---

## Il cliente si scrive una volta

Codice fiscale, partita IVA, codice destinatario, PEC e indirizzo stanno
nell'**anagrafica fiscale** del cliente (`CRM Billing Profile`): una per persona,
una per organizzazione. Prima la fattura prendeva dalla persona solo nome e
cognome, e al paziente che torna si riscriveva tutto il resto ogni volta.

- **La bozza prende** dall'anagrafica quello che ha lasciato vuoto. L'indirizzo
  viaggia intero: se alla cassa si è scritta la città, la via dell'anagrafica non
  ci si mescola. La ragione sociale solo per un'azienda o un ente: la fattura a
  una persona porta nome e cognome.
- **La fattura confermata restituisce** quello che sapeva, solo dove l'anagrafica
  è vuota: il secondo documento non chiede niente, e quello che qualcuno ha scritto
  apposta non si sovrascrive mai.
- **Non restituisce niente se è intestata a un altro.** La visita del figlio
  fatturata al genitore porta il codice fiscale del genitore: scriverlo
  nell'anagrafica del figlio lo metterebbe su tutte le fatture dopo. Si confrontano
  le parole dei due nomi, non i campi, perché un modulo web scrive "Mario Rossi"
  tutto nel nome e la cassa lo divide.
- **Chi paga per un altro** (29/09/2026). Se sulla pagina della persona c'è chi paga
  per lei (il genitore, fra le [persone collegate](../../../docs/gestionale-medico/README.md#le-persone-collegate)),
  la fattura nuova è intestata a lui: i suoi dati fiscali, il suo nome, e nella
  causale "Prestazione resa a Giulia Rossi" con il codice fiscale della figlia. Se la
  cassa scrive il nome o il codice fiscale della figlia, la fattura resta sua e niente
  del genitore ci finisce dentro. Confermata, completa l'anagrafica di chi nomina. Se
  pagano in due, si sceglie fattura per fattura.
- **Di chi è l'anagrafica** lo dice il record della fattura: la persona o
  l'organizzazione sono loro stesse; un contatto è la sua persona; una trattativa è
  la sua organizzazione se la fattura va a un'azienda, la sua persona se va a una
  persona.

Si vede e si corregge dalla pagina della persona (o dell'organizzazione), nella
sezione **Billing details**, per chi ha la capacità `persone.dati_fiscali`
(Segreteria, Manager, Operatore; non il Commerciale né il marketing). Segue la
persona: la legge chi vede la persona.

Un codice fiscale che sbaglia il carattere di controllo non si salva, come una
partita IVA di un formato noto scritta male, un codice destinatario che non ha sei
o sette caratteri, un CAP italiano che non ha cinque cifre. Data di nascita e sesso
si leggono dal codice fiscale. Un codice che contraddice il nome, il cognome o il
sesso della persona, o che sta già su un'altra persona, **si segnala e non si
blocca**: con i cognomi doppi o stranieri il confronto sbaglia, e quello va
davanti a una persona, non in mezzo a un salvataggio.

---

## Emettere

Una `CRM Invoice` nasce in bozza: modificabile, **senza numero fiscale**. Il numero
si assegna alla conferma (`submit`), bloccando la riga del contatore, dentro la
stessa transazione che salva il documento — un numero assegnato e poi non usato
sarebbe un buco nella sequenza, e l'Agenzia ha bocciato la numerazione con salti
(Risposta 505/2020).

Alla conferma il documento **si congela** e prende la sua strada:

| Canale | Quando | Cosa succede |
|---|---|---|
| `sdi` | prestazione non sanitaria, oppure destinatario soggetto IVA, PA o estero, oppure osteopata/chiropratico/chinesiologo | si genera l'XML FatturaPA e si allega |
| `pdf_ts` | prestazione sanitaria esente verso persona fisica | PDF al paziente + comunicazione al Sistema TS |
| `pdf_solo` | il caso raro senza ne' SdI ne' TS | solo il PDF |

Il canale **non si sceglie**: lo decide la classificazione. In lista lo vedi
accanto al totale.

### La finestra della fattura

La fattura si fa in una finestra di DottorCloud, mai nel Desk
(`crm/invoicing/emissione.py`, `InvoiceDialog.vue`; doc 47). Quattro parti:

1. **Per chi e'**: il paziente (il cliente, senza la clinica), il tipo di
   destinatario, e i *Dati in fattura* presi dalla sua scheda fiscale. A una persona
   fisica la fattura va a suo nome, mai a quello dell'azienda per cui lavora.
2. **Cosa e' stato fatto**: il servizio e chi l'ha eseguito, quantita' e prezzo. Il
   prezzo, la descrizione e il professionista vengono dalla scheda del servizio;
   cambiando servizio arrivano quelli nuovi. Uno studio con un solo professionista
   non lo chiede.
3. **Come e' stata pagata**: la modalita' (con la riga che dice se e' tracciabile) e
   la data; per una fattura che va al Sistema TS, l'opposizione del paziente.
4. **Dove andra'**, in cima, prima di tutto.

Mentre si scrive, il server classifica e conta **in memoria**: dove andra', quanto fa
(imponibile, cassa, IVA, bollo, ritenuta, totale) e tutto quello che manca. Una riga
senza chi l'ha eseguita lo dice, e il totale non si mostra finche' non sarebbe quello
vero. Niente si salva a meta': *Salva la bozza* e *Emetti* sono gli unici due modi di
scrivere. La finestra scrive solo cliente, pagamento e righe; cassa, ritenuta, bollo
e canale li decidono l'azienda e il motore — anche la ritenuta di una bozza gia'
salvata, se cambia il destinatario: mai verso un privato.

Si apre da *Nuova fattura* e *Apri* nel pannello, da *Emetti la fattura* di un
appuntamento, di un ciclo o di una rata di abbonamento, e dalla fattura nella storia
della persona.

### La nota di credito

Su una fattura emessa, *Nota di credito* prepara una bozza TD04 con lo stesso
cliente e le stesse righe, che dice quale fattura corregge. Si controlla e si emette
come una fattura. Se l'originale e' andato al Sistema TS, la nota e' il suo
**rimborso** (operazione R) e la comunicazione porta il riferimento al documento
originale: partita IVA, data e numero.

### Una scartata si corregge

Una fattura scartata dallo SdI si considera non emessa. La finestra mostra il motivo
e offre *Correggila* invece di *Invia*: torna in bozza **con il suo numero e la sua
data**, si corregge e si emette di nuovo, entro cinque giorni dalla notifica. Una
bozza che ha gia' il numero non si elimina: lascerebbe un buco nella numerazione.

### La validazione dice tutto insieme

Se il documento non e' emettibile, l'errore elenca **tutti** i problemi, non il
primo: chi sta correggendo ha il cliente davanti, e correggere in una passata sola
costa niente mentre correggere in cinque costa l'appuntamento.

Nella lista c'e' anche quello che il **Sistema TS** rifiuterebbe a gennaio: il
tracciato si controlla sulla bozza (`controlla_bozza`, doc 48). Quello che riguarda
il documento ferma l'emissione; quello che riguarda l'azienda (il suo codice
fiscale, i codici della struttura) si dice e non ferma la fattura che il paziente
aspetta. Tutto in parole: i tipi di spesa con il loro nome, gli importi in euro.

I **rilievi dello SdI** sul file XML seguono l'elenco ufficiale dei controlli
(v1.8) e dicono in fondo il codice con cui lo SdI risponderebbe: «manca la partita
IVA di chi emette (SdI 00200)». L'invio si ferma solo su quelli con il codice; la
finestra li mostra prima dell'invio.

### Un documento misto non si emette

Una riga sanitaria verso persona fisica porta **tutto** il documento fuori dal
canale SdI, e al Sistema TS va solo la quota sanitaria. Ma se nello stesso
documento c'e' anche una riga di osteopata — per cui lo SdI e' **obbligatorio** per
espressa previsione — non c'e' regola piu' restrittiva che tenga: vanno emessi due
documenti. Il sistema lo dice, e si ferma.

---

## La guardia

Dal 2026 la fattura elettronica via SdI per prestazioni sanitarie verso persone
fisiche e' vietata in modo **strutturale** (D.Lgs. 12 giugno 2025 n. 81, che
modifica l'art. 10-bis del D.L. 119/2018).

`crm.invoicing.api.send_to_sdi` risponde **403** su quei documenti. Non e' un flag
di interfaccia: vale per ogni utente e ogni override, e nel pannello il bottone
*Trasmetti* su quei documenti **non esiste proprio** — un bottone grigio invita a
cercare come accenderlo. Ogni tentativo bloccato finisce nel registro
`CRM Invoice Log`.

Ma la guardia **non** si basa su «sembra sanitario». La Risoluzione AdE n. 9 del 24
febbraio 2026 ha chiuso quattro casi con esiti opposti:

| Professione | IVA | SdI | Sistema TS |
|---|---|---|---|
| Osteopata | imponibile, aliquota ordinaria | **obbligatorio** | no |
| Chiropratico | imponibile | **obbligatorio** | no |
| Chinesiologo | imponibile 22% | **obbligatorio** | no |
| Massoterapista | esente art. 10 n. 18 | **vietato** | si' |

Bloccare l'osteopata «perche' sembra sanitario» e' la violazione all'incontrario, e
non se ne accorge nessuno.

---

## Il pannello

`/crm/fatture`, voce **Fatture** nella barra laterale. Tre schede.

**Da fare.** Ogni documento emesso che ha ancora un bottone da premere: da
trasmettere allo SdI, scartato, da comunicare al Sistema TS. Un bottone non premuto
non produce un errore — produce **assenza**, e l'assenza si scopre a gennaio.
Questa e' la lista che rende visibili oggi le assenze di ieri.

**Fatture.** L'elenco, con canale, stato SdI e stato TS. Il bottone *Trasmetti*
compare solo sui documenti che quel canale possono prenderlo.

**Sistema TS.** Contatori dell'anno, scadenza e giorni che mancano, ultimo invio
accolto, e il bottone che prepara lo zip.

Ogni documento si apre nella sua finestra (*Apri*), la stessa con cui si crea: il
pannello e' la console dell'operatore, la finestra e' l'unico editor.

---

## Trasmettere allo SdI

L'XML si genera qui. Il canale aggiunge solo la strada accreditata per entrare, e
si sceglie sull'azienda emittente.

| Canale | Cosa serve | Chi tiene i documenti |
|---|---|---|
| `export` | niente | nessuno — il file lo consegni tu |
| `pec` | la casella PEC dello studio | nessuno |
| `provider` | Itala, l'intermediario accreditato, sull'account dell'agenzia | Itala |

**Il predefinito e' `provider`, cioe' Itala**, l'unico che si offre ai centri; il
file da caricare e la PEC restano, li sceglie l'agenzia. E il motivo non e' tecnico. Le tre strade emettono
una fattura ugualmente valida: cambia chi risponde quando il canale tace. La PEC non
costa niente e non chiede l'accreditamento di nessuno, ma funziona solo se qualcuno
quella casella la legge — e uno studio a cui hai appena detto che la fatturazione e'
automatica non la legge. La notifica arriva, non la apre nessuno, i cinque giorni
scadono, e la lamentela arriva a chi ha venduto il sistema. L'intermediario e' la
risposta a pagamento a questo: guarda il canale, e ne risponde.

`export` resta il pavimento su cui stanno gli altri due: un codice canale che non
esiste ricade li' invece di dare errore, cosi' una configurazione sbagliata lascia la
fattura consegnabile a mano e non bloccata.

Quello che il predefinito **non** fa e' ricadere in silenzio. Finche' l'agenzia non
ha collegato Itala, l'XML si genera e si conserva lo stesso, ma l'invio si rifiuta e
dice cosa manca, e il pezzo resta in «Cosa manca» finche' non lo chiudi. Un canale
che finge di aver mandato e' peggio di uno che si ferma.

### La PEC

E' la strada che non ha bisogno di nessuno: una casella certificata, un indirizzo,
e la fattura parte. Serve un account email con quella PEC (Impostazioni > Email),
**in invio e in ricezione** — le ricevute tornano li'.

Due dettagli che decidono se funziona:

- **solo la prima fattura va a `sdi01@pec.fatturapa.it`.** Con la ricevuta di
  consegna lo SdI dice a quale indirizzo scrivere da li' in avanti, e la posta
  mandata a quello vecchio non riceve risposta. Il modulo lo impara e lo salva.
- **la fattura alla PA va firmata.** La firma qualificata e' obbligatoria su FPA12
  e facoltativa su FPR12. Mandarne una non firmata torna indietro con `00102`, e a
  quel punto i cinque giorni corrono gia': il canale si rifiuta e dice cosa manca.
  Il `.p7m` firmato si allega sul documento.

### Solo uscita, o anche ingresso

Sul canale provider c'e' un interruttore per azienda:

- **`uscita`** manda le fatture e riporta indietro le loro ricevute. Basta.
- **`entrambi`** archivia anche le fatture che ti mandano i fornitori.

Il ciclo passivo e' volutamente **un registro, non una contabilita'**: cosa e'
arrivato, da chi, e il file originale. Niente riconciliazione con gli ordini, niente
approvazione, niente registrazione — fare meta' partita doppia sarebbe peggio che non
farla. L'XML e' il documento; tutto il resto e' comodita' che il provider aveva gia'
estratto.

Accendilo solo dove qualcuno lo legge davvero: una casella che non apre nessuno e'
peggio di non averla.

### Itala, sull'account dell'agenzia

Itala e' l'unico intermediario, e un solo account basta per tutti i centri: quello
dell'agenzia, nelle *Opzioni* (visibile solo all'agenzia) oppure una volta per tutto
il server, in `common_site_config.json` (`itala_client_id`, `itala_client_secret`).
Ogni azienda si registra da sola sotto l'account (la gestione multi-azienda di Itala,
`/aziende`) la prima volta che parte una sua fattura, una volta per ambiente; un
centro che ha gia' un account Itala suo lo tiene, scritto dall'agenzia sull'azienda.
Il contratto, riassunto: `.pi/vendor/itala.md`.

Gli indirizzi di prova e di produzione sono quelli pubblicati da Itala. **L'ambiente
e' del documento**: una fattura di prova va sempre alla porta di prova, una vera
sempre alla produzione, ed e' timbrato sulla fattura. Il token si raccoglie dalle
risposte (`X-auth-token`) e sta in cache per account **e ambiente**; un 401 rinnova e
riprova una volta, il secondo e' un problema vero.

Itala riscrive il blocco di trasmissione con i suoi riferimenti: il nome del file che
lo SdI ricevera' e' il suo, e si tiene sulla fattura con l'identificativo di Itala.
Le notifiche rispondono a quel nome, gli aggiornamenti a quell'identificativo.

**Gli esiti si chiedono.** Un account per tanti siti non ha un webhook per ognuno:
ogni sito chiede a Itala ogni dieci minuti, per la sua partita IVA, solo quando
qualcosa aspetta (una fattura partita senza esito, una alla PA consegnata e non
ancora accettata, i fornitori se si ricevono). Chi emette soltanto chiede solo le sue
trasmissioni. Una volta al giorno si registra quello che Itala non ha risposto.

### Fatture in Cloud, per chi fattura gia' li'

Un centro che fattura con Fatture in Cloud lo collega in *Impostazioni >
Fatturazione > Fatture in Cloud* (doc 58, `crm/invoicing/fic`). Con l'interruttore
acceso ogni fattura vera nasce li' al momento dell'emissione: Fatture in Cloud la
somma prima (IVA, ritenuta e totale da pagare devono essere i nostri al centesimo,
o non si crea niente), le da' il suo numero, la manda allo SdI e ne dice lo stato.
Per quell'azienda Itala non si usa e i crediti SdI del piano non contano; la prova
resta qui. Il Sistema TS lo invia DottorCloud, come sempre, oppure Fatture in Cloud:
uno dei due, mai entrambi. L'app e' dell'agenzia, una per tutti i centri
(`fic_client_id`, `fic_client_secret` in `common_site_config.json`), con il suo
indirizzo di ritorno sull'hub.

### La porta da cui tornano le ricevute

E' un endpoint pubblico, quindi il progetto riguarda soprattutto chi puo' bussare:

- **un segreto per azienda**, confrontato a tempo costante, in header o in query
  perche' la configurazione del fornitore sceglie fra i due. Tutti i candidati vengono
  controllati anche dopo che uno ha corrisposto, cosi' nessuno puo' misurare quanto in
  basso nella lista e' finito il suo tentativo;
- **a chi viene rifiutato non si dice niente**: azienda sconosciuta, segreto sbagliato
  e corpo spazzatura ricevono la stessa risposta;
- **un'azienda che non ha mai generato un segreto non si apre** con un chiamante che
  non presenta niente;
- **l'identita' non si legge mai dal corpo**: a quale fattura risponde una ricevuta si
  decide come su ogni altro canale, dal nome file che ci ha messo lo SdI.

Il codice di stato e' il contratto con la coda del fornitore: Itala riprova ogni
tre ore, per al massimo tre giorni, su tutto cio' che non e' 200. Quindi una
consegna capita risponde 200 anche quando non c'era niente da applicare — gli
stessi byte arriverebbero alla stessa risposta — e solo un guasto inatteso risponde
500. Quello che arriva e' tenuto prima di essere applicato (`CRM SdI Update`): un
200 non perde mai un aggiornamento.

Itala presenta il segreto come `Authorization: Bearer <segreto>`. Frappe legge ogni
Bearer come un suo token OAuth e rifiuterebbe la chiamata prima dell'endpoint:
per l'indirizzo del webhook, e solo per quello, l'intestazione e' tolta prima che
Frappe la guardi e tenuta per il confronto col segreto della societa'
(`crm.invoicing.sdi.webhook.prima_della_richiesta`, un `before_request`).

Serve solo a un'azienda con un account Itala suo: il riquadro dell'agenzia in
**Impostazioni → Fatturazione → Prova e attivazione** costruisce l'URL da incollare e
genera il segreto. Il segreto si vede **una volta sola**: e' conservato
cifrato, e un valore rileggibile da una schermata e' un valore leggibile da uno
screenshot. Rigenerarlo e' anche ruotarlo — il vecchio smette di funzionare subito.

### Mandare non basta

Il file parte, e quella e' la meta' facile. Tre cose non le fa la trasmissione:

**Leggere le ricevute.** Finche' non arriva `RC` o `MC` nessuno sa se la fattura
e' emessa. Sul canale PEC non spinge nessuno: legge il controllo giornaliero.

**Rispondere a uno scarto entro cinque giorni.** `NS` vuol dire che la fattura
**si considera non emessa**, e la strada che l'Agenzia definisce preferibile e'
rimandarla con **lo stesso numero e la stessa data** (Circolare 13/E del 2 luglio
2018). Il bottone e' `crm.invoicing.api.reopen_rejected`: riporta il documento in
bozza tenendo numero e data — non e' riscrivere la storia, quel documento non
esiste ancora — e butta via l'XML, perche' lo SdI rifiuta un nome di file che ha
gia' visto.

**La conservazione a norma, dieci anni.** Non te la da' la trasmissione, e **non e'
una cosa sola**: si divide dove si divide il routing. Vedi *La conservazione si
divide in due*, piu' sotto.

### Le ricevute

Ne tornano sei, e una sola e' una buona notizia.

| Tipo | Cosa vuol dire |
|---|---|
| `RC` | consegnata al destinatario |
| `NS` | **scartata**: la fattura si considera non emessa, cinque giorni per rimandarla |
| `MC` | mancata consegna: emessa, depositata nell'area riservata del destinatario |
| `AT` | attestazione di trasmissione con impossibilita' di recapito |
| `NE` | la PA ha accettato (`EC01`) o rifiutato (`EC02`) |
| `DT` | la PA non si e' espressa entro quindici giorni |

`MC` e' quella che si legge male. **Non e' un fallimento**: la fattura e' emessa e
sta nell'area riservata del cliente. Quello che si deve fare e' avvisarlo, perche'
lo SdI non lo fa — e il modulo alza esattamente quell'avviso.

Le ricevute si applicano da sole: sul canale PEC il controllo giornaliero legge la
casella, con Itala si chiedono ogni dieci minuti (o arrivano via webhook, per
un'azienda con un account suo), e una scaricata dal portale si applica
con `crm.invoicing.api.apply_sdi_notice`. Applicare due volte la stessa non fa
nulla: la casella PEC riconsegna e i webhook ritentano.

---

## Il PDF che il cliente conserva

PDF/A-3b, e la conformita' si **misura**. Il modulo costruisce la struttura sopra
al PDF reso — XMP non compresso con `pdfaid`, OutputIntent sRGB, metadati azzerati,
date e identificativo presi dal documento e non dall'orologio — e poi rilegge cio'
che ha prodotto. Il campo *PDF conformance* sulla fattura dice quello che e' venuto
fuori, non quello che si sperava.

Sul ramo SdI l'XML FatturaPA viaggia **dentro** il PDF come associated file: la
resa leggibile e l'originale leggibile da una macchina restano un file solo.

Il PDF si genera **una volta sola**. Il renderer non e' stabile fra versioni,
quindi rigenerare non e' un percorso di recupero: il file consegnato e' quello
conservato, e l'impronta presa alla creazione e' cio' che lo dimostra.

Il nome resta neutro — `documento_2026-S-128.pdf`, mai
`fattura_psicoterapia_rossi_marzo.pdf`: il nome di un file e' a sua volta un dato,
e racconta la diagnosi a chiunque guardi una cartella dei download.

---

## La conservazione si divide in due

Lo stesso studio che non puo' mandare allo SdI le sedute di fisioterapia ci manda
gli abbonamenti in palestra, i corsi e le perizie per l'assicurazione. Non e' un
caso limite: e' la giornata normale di un poliambulatorio. Quindi **la conservazione
non e' un'impostazione sola**, e si divide esattamente dove si divide il routing.

| Ramo | Chi conserva | Campo sull'azienda |
|---|---|---|
| Documenti che passano dallo SdI | l'Agenzia (gratis) o un provider | `conservation_service` |
| Documenti che non ci passano mai | qualcuno che paghi, o la carta | `document_mode` + `conservation_local` |

La ragione dell'asimmetria e' una sola: **l'Agenzia conserva solo cio' che e'
passato dallo SdI**. Il suo servizio e' gratuito, conserva quindici anni, vuole
un'**adesione esplicita** in Fatture e Corrispettivi e copre le fatture da
quel giorno in avanti. E' un modulo da firmare una volta, non un prodotto da
comprare — ma copre il ramo che copre. Le fatture sanitarie verso persona fisica,
che allo SdI e' **vietato** far transitare, ne restano fuori: e' li' che la
conservazione smette di essere gratis.

Percio' `document_mode` riguarda **solo quel secondo ramo**:

- **`elettronica_extra_sdi`** — quei documenti nascono elettronici, e qualcuno va
  pagato per tenerli dieci anni. Chi sia lo dici nel campo accanto.
- **`analogico_con_copia`** — l'originale e' la carta, in due esemplari, e non deve
  conservarlo nessun servizio.

La dicitura sulla conservazione e il secondo esemplare in stampa seguono quel ramo,
mai quello SdI: una fattura elettronica non ha una seconda copia, e scrivere che e'
conservata ai sensi del D.M. 17 giugno 2014 quando a conservarla e' l'Agenzia e'
dire il custode sbagliato.

«Cosa manca» le chiede tutte e due, separate, e solo quando sono dovute: il
conservatore locale compare come buco solo se hai scelto `elettronica_extra_sdi` e
non hai detto chi.

---

## Sistema TS: tre strade, una pipeline

Cambiano solo gli ultimi dieci centimetri, e la strada la sceglie l'agenzia: il
centro scrive soltanto le sue credenziali.

| Modalita' | Cosa serve | Chi trasmette |
|---|---|---|
| `credenziali_studio` | utente, password, PINCODE del centro, **nessuna delega attiva** | il CRM, in diretta |
| `intermediario` | commercialista Entratel **con** delega attiva | il CRM, canale `/entrate/` |
| `export` | niente | il centro, dal portale |

Una fattura di prova non si trasmette mai (doc 49); una vera va alla produzione del
Sistema TS. Il collaudo di Sogei si sceglie solo per un sito di sviluppo, con
`sistema_ts_ambiente: test` nella configurazione del sito. Il certificato del kit
ufficiale l'agenzia lo carica una volta per il sito, nelle *Opzioni*; quello di
un'azienda vale solo se c'e'.

**Provato sul collaudo il 05/10/2026** (kit `kit730P_ver_20240214`, invio sincrono):
una fattura accolta con protocollo, la sua nota di credito accolta come rimborso
(`R`), uno scarto letto con le parole del servizio (S035, pagamento di un anno
chiuso), una segnalazione letta allo stesso modo (W014, stesso paziente lo stesso
giorno). Quello che serve per rifarlo:

- **Il certificato del collaudo** lo firma la «Sogei Certification Authority
  Test», che nessun sistema riconosce e Sogei non pubblica: il sito di sviluppo
  nomina il file di cui fidarsi con `sistema_ts_ca` (il certificato che il server
  presenta, salvato con `openssl s_client`). In produzione il certificato e'
  pubblico (Sectigo) e quel valore non si legge mai.
- **Le utenze del kit**: quella del medico (`PROVAX00X00X000Y`, PINCODE
  `1234567890`, partita IVA `01201200121`) entra; quella della struttura
  autorizzata (`ASC7Y72S`) risponde «Errore generico di autenticazione» anche alla
  richiesta d'esempio del kit, mandata intatta. Il codice fiscale e la partita IVA
  del kit non passano le cifre di controllo: un'azienda di prova li riceve scritti
  nel database, e la verifica prima dell'invio va saltata solo per loro.
- **I tempi**: il collaudo ha messo 65 secondi a rifiutare un accesso. Il
  trasporto aspetta la risposta 90 secondi e, se non arriva, non rimanda: il
  documento potrebbe esserci gia'.

**Il predefinito e' `credenziali_studio`**, e il motivo e' commerciale prima che
tecnico: non costa niente a documento, ed e' questo che rende le *fatture sanitarie
illimitate* un prodotto invece di una perdita. Un centro con sei professionisti fa
circa sedicimila righe l'anno: contarle finirebbe nel prezzo o nel margine.

Le credenziali sono **del centro e le inserisce il centro**, dalle sue impostazioni.
Una credenziale che non hai e' un incidente che non puoi avere.

La vecchia modalita' `provider` spediva il tracciato a un indirizzo che nessun
intermediario documenta: e' tolta, e le aziende che l'avevano tornano alle
credenziali del centro. Il servizio di Itala per il Sistema TS (sistema-ts-api.it)
oggi non porta i codici di una struttura, ne' il rimborso o la variazione: regge un
professionista a suo nome, non un poliambulatorio (doc 49).

Il predefinito non blocca il salvataggio: un centro si configura prima che arrivino
le credenziali, e fermare l'onboarding su un campo che si riempie la settimana dopo
sarebbe assurdo. Il buco compare in «Cosa manca», l'invio si rifiuta da solo finche'
non lo chiudi, e **la fatturazione non aspetta niente di tutto questo**.

La chiamata diretta e' sincrona e la risposta porta il protocollo: `accolto` si
scrive solo su un'accettazione vera, e il controllo del silenzio conta `inviato` fra
i documenti in attesa.

Il codice fiscale del paziente e' **cifrato prima di lasciare DottorCloud**.

Chi ha bisogno delle credenziali dello studio e chi no e' una definizione sola
(`sistema_ts.richiede_credenziali`): un'azienda su `export` di credenziali TS non ne
ha bisogno, e chiedergliele bloccherebbe il salvataggio su un campo che non riempira'.

`export` resta il piano B universale e resta testato anche quando nessuno lo usa. Si
retrocede da soli, non in silenzio: PINCODE scaduto, delega cambiata, scarti
`105`/`106` riportano l'azienda a `export` con un avviso. **La fatturazione non si
ferma mai** per un problema dell'ultimo miglio.

La verita' sulla delega non si chiede: si sonda. Alla domanda «chi ha mandato i dati
l'anno scorso?» molti studi rispondono male, non per malafede — non lo sanno. Gli
errori del Sistema TS invece sono inequivocabili:

- `105` invio per conto in assenza di delega attiva → **la delega non c'e'**
- `106` invio in proprio in presenza di delega attiva → **la delega c'e'**

Il sondaggio si lancia con `crm.invoicing.api.probe_delegation`: manda il primo
documento reale in attesa e legge la risposta. Se torna `105` o `106` l'azienda
viene spostata da sola sulla modalita' giusta e retrocessa a `export` con un
avviso — la fatturazione non si ferma, e nessuno resta a indovinare.

### Comunicare un documento

Con `credenziali_studio` o `intermediario` il bottone **Comunica** (*Report*) nella scheda
«Da fare» manda il singolo documento, **subito**, e la risposta arriva in giornata
invece che il 20 gennaio con quattromila righe in coda. Uno scarto non e' un
guasto: dice quale codice e' tornato, e i codici `105` e `106` hanno gia' spostato
la modalita' dell'azienda.

Sulle aziende in `export` il bottone non compare: li' il file si prepara e si
carica dal portale, e non c'e' niente da premere.

### Preparare l'invio

*Sistema TS → Prepara il file*. Costruisce uno o piu' zip, ciascuno sotto i 5 MB
(oltre e' scarto `108`), e crea un `CRM TS Submission` per parte.

Le fatture che non passano la validazione del tracciato vengono **elencate e
lasciate fuori**, non bloccano le altre: una riga rotta non deve costare la
scadenza dell'intero anno.

L'anno di competenza e' quello della **data di pagamento**, non dell'emissione: un
pacchetto pagato a dicembre e fatturato a marzo appartiene a dicembre.

Scadenza: 31 gennaio dell'anno dopo, il primo giorno lavorativo dopo se cade di sabato o festivo (spese 2026: lunedì 1° febbraio 2027). **I veterinari hanno la loro, a meta' marzo**,
e per questo hanno un batch separato.

### L'opposizione

Il cittadino puo' chiedere che la spesa non finisca nella precompilata. Con
l'opposizione il documento **si trasmette comunque**, in forma anonima: il codice
fiscale non viene nemmeno scritto (mandarlo con il flag attivo fa scartare la
riga). L'annotazione sul documento fiscale non e' facoltativa (art. 3, c. 2, DM
31/7/2015) ed e' tenuta **neutra**: un riferimento all'esercizio dell'opposizione,
nient'altro.

---

## Il calcolo, nell'ordine giusto

`compenso → cassa → IVA → soglia bollo → riaddebito → ritenuta`

L'ordine e' fissato e testato, perche' e' sui casi di confine che si sbaglia: 76 €
con ENPAP 2% fanno 77,52 e il bollo e' dovuto; 75 € ne fanno 76,50 e non lo e'. A
77,47 esatti **non** e' dovuto: la soglia si supera, non si raggiunge.

Quattro cose che quasi tutti danno per scontate al contrario:

- **ENPAM non prevede alcun contributo integrativo** da addebitare al paziente.
- **Il riaddebito del bollo non e' «escluso art. 15»**: e' parte integrante del
  compenso (Risposta AdE 428/2022), quindi segue il regime IVA della prestazione.
- **Il contributo integrativo concorre alla base imponibile IVA**, quindi entra
  nella soglia del bollo e nell'importo comunicato al TS.
- **Il contributo integrativo non e' soggetto a ritenuta; la rivalsa INPS 4% si'.**

L'invariante: **il totale del documento e la somma comunicata al Sistema TS
coincidono**, salvo l'unica eccezione del bollo pagato in contanti.

---

## Monitoraggio

Un lavoro giornaliero cerca **l'assenza**, non gli errori, perche' i guasti di
questo dominio sono silenziosi e annuali:

- certificato `SanitelCF.cer` scaduto o rigenerato → **tutti** gli invii falliscono
  con `002`, senza dire niente. Avviso a 90 giorni;
- nessun invio TS accolto da N giorni con documenti in attesa;
- scadenza annuale vicina con documenti ancora fermi.

Gli avvisi arrivano a chi ha il ruolo *Invoicing Manager*, uno per condizione per
azienda al giorno: un alert ripetuto ogni ora e' rumore, e il rumore e' il modo in
cui si scorre oltre quello che contava.

---

## Cosa il modulo non decide

- **Cartaceo o elettronico, per il ramo fuori SdI** (`document_mode`): due
  configurazioni di prodotto con costi diversi, non un dettaglio. Il modulo dice
  quale scelta comporta cosa e non sceglie: e' una decisione commerciale.
- **L'esenzione, professione per professione.** Il registro e' un punto di partenza
  documentato; `needs_verification` segna dove serve il commercialista.
- **I nomi degli elementi e il formato delle date del tracciato TS**: vengono dal
  kit ufficiale e vanno riconfrontati con i suoi XSD prima del go-live.

*Non costituisce consulenza fiscale ne' legale. I riferimenti normativi sono
doppiati con i Testi Unici applicabili dal 1° gennaio 2027.*
