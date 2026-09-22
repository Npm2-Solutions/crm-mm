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

## Dove si configura

Tutto sta in **Impostazioni → Fatturazione**, nella modale del CRM: azienda
emittente, registro delle qualifiche, servizi, erogatori, la connessione al provider
e le impostazioni comuni.

La scheda dell'azienda e' divisa per argomento, cosi' il sanitario e il Sistema TS
hanno il loro spazio invece di stare in fondo a un modulo unico: *Company*,
*Invoicing*, *Documents* (forma e conservazione), *Transmission* (lo SdI) e
*Healthcare* (categoria TS, Codice Proprietario, certificato e modalita' di
trasmissione).
Le schermate rendono il layout dei DocType, quindi le spiegazioni che leggi sotto
ogni campo sono le stesse scritte nella definizione — una regola spiegata una
volta sola non puo' divergere dall'interfaccia che la mostra.

Il pannello `/crm/fatture` resta la console dell'operatore: cosa e' stato emesso e
cosa aspetta ancora un bottone. Non si configura niente da li'.

---

## Prima di emettere: quattro cose

### 1. L'azienda emittente — `CRM Invoicing Company`

Chi firma le fatture. Partita IVA, sede, regime fiscale, cassa e ritenuta,
modalita' del bollo, formato di numerazione. Se lo studio e' sanitario, anche la
categoria presso il Sistema TS e — solo per strutture, farmacie, parafarmacie e
ottici — il Codice Proprietario `codiceRegione-codiceAsl-codiceSSA`.

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
non viene mai sovrascritta da una migrazione.

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
natura IVA, il `tipoSpesa` per il Sistema TS, se e' soggetta a bollo.

Il campo *Verificato dal commercialista* non blocca nulla: finche' non e' spuntato,
l'esenzione su quel servizio e' un'assunzione che nessuno ha confermato.

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

### La validazione dice tutto insieme

Se il documento non e' emettibile, l'errore elenca **tutti** i problemi, non il
primo: chi sta correggendo ha il cliente davanti, e correggere in una passata sola
costa niente mentre correggere in cinque costa l'appuntamento.

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

`/crm/fatture`, voce **Invoices** nella barra laterale. Tre schede.

**Da fare.** Ogni documento emesso che ha ancora un bottone da premere: da
trasmettere allo SdI, scartato, da comunicare al Sistema TS. Un bottone non premuto
non produce un errore — produce **assenza**, e l'assenza si scopre a gennaio.
Questa e' la lista che rende visibili oggi le assenze di ieri.

**Fatture.** L'elenco, con canale, stato SdI e stato TS. Il bottone *Trasmetti*
compare solo sui documenti che quel canale possono prenderlo.

**Sistema TS.** Contatori dell'anno, scadenza e giorni che mancano, ultimo invio
accolto, e il bottone che prepara lo zip.

La creazione e la modifica di un documento avvengono sulla sua form: il pannello e'
la console dell'operatore, non un secondo editor.

---

## Trasmettere allo SdI

L'XML si genera qui. Il canale aggiunge solo la strada accreditata per entrare, e
si sceglie sull'azienda emittente.

| Canale | Cosa serve | Chi tiene i documenti |
|---|---|---|
| `export` | niente | nessuno — il file lo consegni tu |
| `pec` | la casella PEC dello studio | nessuno |
| `provider` | l'API di un intermediario accreditato | il provider |

**Il predefinito e' `provider`**, e il motivo non e' tecnico. Le tre strade emettono
una fattura ugualmente valida: cambia chi risponde quando il canale tace. La PEC non
costa niente e non chiede l'accreditamento di nessuno, ma funziona solo se qualcuno
quella casella la legge — e uno studio a cui hai appena detto che la fatturazione e'
automatica non la legge. La notifica arriva, non la apre nessuno, i cinque giorni
scadono, e la lamentela arriva a chi ha venduto il sistema. L'intermediario e' la
risposta a pagamento a questo: guarda il canale, e ne risponde.

`export` resta il pavimento su cui stanno gli altri due: un codice canale che non
esiste ricade li' invece di dare errore, cosi' una configurazione sbagliata lascia la
fattura consegnabile a mano e non bloccata.

Quello che il predefinito **non** fa e' ricadere in silenzio. Un'azienda su
`provider` senza endpoint l'XML lo genera e lo conserva lo stesso, ma l'invio si
rifiuta e dice cosa manca, e il pezzo resta in «Cosa manca» finche' non lo chiudi. Un
canale che finge di aver mandato e' peggio di uno che si ferma.

### La PEC

E' la strada che non ha bisogno di nessuno: una casella certificata, un indirizzo,
e la fattura parte. Serve un Email Account in Frappe con quella PEC, **in invio e
in ricezione** — le ricevute tornano li'.

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

### Il provider: la connessione, e cosa resta da verificare

Nessun fornitore e' cablato nel codice: endpoint, URL di login e campo
dell'identificativo sono configurazione, con i valori predefiniti gia' impostati sul
fornitore con cui il sistema viene venduto. Svuotare l'URL di login e' una scelta
vera e chiede l'HTTP Basic.

Autenticarsi e restarlo e' `acube.py`, condiviso con il canale Sistema TS: il token
dura un giorno e sta in cache per azienda **e ambiente**, cosi' il passaggio in
produzione non riusa quello di sandbox facendolo sembrare un problema di credenziali.
Un 401 rinnova e riprova una volta; il secondo e' un problema vero.

**L'ambiente non e' un dettaglio.** Un documento in sandbox non e' arrivato a nessuno,
e l'unica cosa che lo distingue da una fattura vera e' quale interruttore era messo
mesi fa. Quindi: parte da sandbox, viene **timbrato sul documento** invece di essere
riletto dall'azienda, finisce in coda a ogni messaggio di un invio di prova, e sta in
cima al suo pannello invece che dentro una sezione — e' l'unica impostazione il cui
valore sbagliato non produce nessun errore.

Resta non verificata **la forma del payload del webhook**: il fornitore documenta i
nomi degli eventi, non la busta che ci mette intorno, e questo e' stato scritto senza
una consegna vera da leggere. Percio' niente pretende una forma: si cerca in piu'
posti plausibili, si rifiuta di indovinare, e cio' che non si e' potuto applicare
viene registrato con i **nomi** delle chiavi e mai con i valori — dalla stessa porta
entra `supplier-invoice`, e quello porta il documento sanitario di qualcuno. La prima
consegna vera chiude il punto, e il log serve a raccontartela.

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

Il codice di stato e' il contratto con la coda del fornitore, che riprova quindici
volte in circa dieci ore su tutto cio' che non e' 200. Quindi una consegna capita
risponde 200 anche quando non c'era niente da applicare — gli stessi byte
arriverebbero alla stessa risposta — e solo un guasto inatteso risponde 500.

Il pannello **Impostazioni → Fatturazione → Connessione al provider** costruisce l'URL
da incollare e genera il segreto. Il segreto si vede **una volta sola**: e' conservato
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
casella, sul provider arrivano via webhook, e una scaricata dal portale si applica
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

## Sistema TS: quattro strade, una pipeline

Cambiano solo gli ultimi dieci centimetri.

| Modalita' | Cosa serve | Chi trasmette |
|---|---|---|
| `credenziali_studio` | utente, password, PINCODE del centro, **nessuna delega attiva** | il CRM, in diretta |
| `intermediario` | commercialista Entratel **con** delega attiva | il CRM, canale `/entrate/` |
| `provider` | un endpoint sull'intermediario accreditato | il provider, sotto il proprio accreditamento |
| `export` | niente | il centro, dal portale |

**Il predefinito e' `credenziali_studio`**, e il motivo e' commerciale prima che
tecnico: non costa niente a documento, ed e' questo che rende le *fatture sanitarie
illimitate* un prodotto invece di una perdita. Un centro con sei professionisti fa
circa sedicimila righe l'anno: contarle finirebbe nel prezzo o nel margine.

Le credenziali sono **del centro e le inserisce il centro**, dalle sue impostazioni.
Una credenziale che non hai e' un incidente che non puoi avere.

`provider` e' la risposta per il centro che la strada diretta **non puo'** prenderla:
dove la delega ce l'ha il commercialista, trasmettere in nome proprio torna `105`. E'
un segmento vero, e poterlo servire e' una differenza che vale.

Il predefinito non blocca il salvataggio: un centro si configura prima che arrivino
le credenziali, e fermare l'onboarding su un campo che si riempie la settimana dopo
sarebbe assurdo. Il buco compare in «Cosa manca», l'invio si rifiuta da solo finche'
non lo chiudi, e **la fatturazione non aspetta niente di tutto questo**.

**Attenzione: il sì del provider non e' il sì del Sistema TS.** La chiamata diretta e'
sincrona e la risposta porta il protocollo. Il provider invece prende il file e lo
inoltra, quindi il documento resta `inviato` e non diventa `accolto`. Scrivere
`accolto` su un 202 sarebbe inventarsi un'accettazione che nessuno ha dato, e lo
studio se ne accorgerebbe a gennaio. Per questo il controllo della silenzio conta
`inviato` fra i documenti in attesa.

Il codice fiscale del paziente e' **cifrato prima di arrivare all'API di chiunque**,
provider compreso.

Chi ha bisogno delle credenziali dello studio e chi no e' una definizione sola
(`sistema_ts.richiede_credenziali`): un'azienda su `provider` di credenziali TS non ne
ha, e chiedergliele bloccherebbe il salvataggio su un campo che non potra' mai
riempire.

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

Scadenza: 31 gennaio dell'anno dopo. **I veterinari hanno la loro, a meta' marzo**,
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
