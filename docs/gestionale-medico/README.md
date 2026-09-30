# Il gestionale per i centri medici: come farlo stare in Frappe

**Stato:** 🚧 in costruzione. Fase 0: livelli, capacità e piano (la PR 1 del
[doc 30](../progetto-ghl/30-ruoli-e-permessi.md#la-pr-1-comè-fatta)) fatti il
29/09/2026; il Sito nascosto senza Builder e le fatture lette solo da chi deve,
anche nella cronologia della persona, lo stesso giorno; poi
[l'anagrafica fiscale sola](#unanagrafica-fiscale-sola), letta dalla fattura e
completata da quella confermata; [il registro dei consensi](#il-registro-dei-consensi),
con quello di `/prenota`; [lo scheletro della clinica](#lo-scheletro-della-clinica), con
la scheda paziente che nasce dalle regole; e [la sezione Clinica](#la-sezione-clinica)
con la visita semplice e il registro degli accessi; infine [le persone
collegate](#le-persone-collegate), genitore e figlio, con la prenotazione per un altro.
Con queste la fase 0 è fatta. Proposta del 25/09/2026, rivista dopo l'arrivo della fatturazione in
`develop`. Fattura elettronica e Sistema TS ci sono già (`crm/invoicing` e
`crm/tessera_sanitaria`, [guida](../../.pi/feats/fatturazione/guida.md)): questa
proposta ci si appoggia e non li tocca, se non nei punti detti sotto. Prima di
scrivere codice vanno chiuse le [domande](#le-domande-da-chiudere-prima) in fondo.
Le richieste puntuali (livelli, Sito senza Builder, moduli con firma, archivio,
area cliente), verificate sul codice, sono in [requisiti.md](./requisiti.md).
Obblighi, concorrenti ed ecosistema Frappe, con le fonti, sono in
[ricerca.md](./ricerca.md). Il design, con i tre strati (CRM, fatturazione,
clinica), è in [design.md](./design.md); il listino proposto in
[listino.md](./listino.md); ruoli e permessi nel
[doc 30](../progetto-ghl/30-ruoli-e-permessi.md).

## Il problema in una riga

Il CRM oggi fa molto bene il **prima** della visita: trova la persona, la fa
prenotare (dal sito, da MioDottore, al telefono), le ricorda l'appuntamento, dice
quanto è costato acquisirla. Da poco fa anche il **dopo** amministrativo: la
fattura nasce dall'appuntamento e va al Sistema TS. Manca il **durante**: la
visita, la cartella, il referto, i consensi.

CRM e centro medico hanno in comune due cose sole, **la persona e l'agenda**. La
difficoltà non è Frappe: è decidere dove passa il confine, chi vede cosa e come i
due mondi si passano la persona. Questo documento lo decide.

## La dualità: una persona, due mestieri

Non sono due sistemi e non sono due anagrafiche. È **una persona sola** che
attraversa due fasi, e **due mestieri** che lavorano su di lei.

### Le due fasi della persona

```
  CONTATTO  ────────── la prima regola che scatta ──────────►  PAZIENTE
  da conquistare     un dato medico, l'arrivo, la visita,       da curare
  lo segue il        la fattura…                                lo segue il centro,
  marketing, con i deal                                         con agenda e visite
```

- Il passaggio è **il primo dato medico o il primo segno che la persona è
  venuta**, non la prenotazione: chi prenota e non si presenta resta un contatto.
- È automatico: nessuno deve ricordarsi di "convertire" qualcuno.
- La persona non cambia scheda. Le si aggiunge la **scheda paziente** (consensi,
  tutore, dossier) e da quel momento compare fra i **Pazienti**.

Saperlo serve davvero: cartella e documenti clinici vanno conservati anche se la
persona chiede di essere cancellata, il medico vede i pazienti e il marketing no, e
"nuovi pazienti al mese" è il numero che il centro guarda.

### Come si diventa paziente: da soli, qualunque sia il modo di lavorare

Ogni centro lavora a modo suo: c'è quello con la segreteria che accoglie, quello
dove c'è solo il medico che apre la scheda della persona e comincia a scrivere,
quello che segna tutto in agenda e quello che fa solo le fatture. Quindi non c'è
un passaggio obbligato ma **una lista di regole: la prima che scatta converte, e
stop**. Nessuna esclude le altre, nessuna è obbligatoria.

| # | Regola | Scatta quando | Tipica di |
|---|---|---|---|
| 1 | **Informazione medica** | Si salva il primo dato clinico sulla persona, di qualunque tipo: una nota, un'anamnesi, un'allergia, un parametro, un documento clinico, un consenso a un trattamento, un referto | il medico che apre la scheda e scrive |
| 2 | **Accettazione** | La segreteria registra l'arrivo al banco | i centri con la segreteria |
| 3 | **Appuntamento svolto** | L'appuntamento è segnato come svolto (`Completed`, o il partecipante `Attended`), anche con il "sì" del promemoria di fine giornata | chi usa l'agenda |
| 4 | **Fattura sanitaria** | Si conferma la prima `CRM Invoice` alla persona con una riga sanitaria (`is_healthcare` sulla riga, copiato dalla scheda del servizio: la copia funziona dalla PR #102, in `develop` dal 25/09/2026; prima il flag restava sempre a 0) | chi fa solo le fatture |
| 5 | **Importazione** | Si importano i pazienti dal vecchio gestionale | il primo giorno |
| 6 | **A mano** | Qualcuno preme "Segna come paziente" sulla pagina della persona | i casi che nessuna regola vede |

**La regola 1 non chiede che la persona sia venuta, e va bene così.** Dal momento
in cui il centro conserva un dato sanitario su qualcuno, quel dato va trattato da
dato di un paziente: lo vedono solo i ruoli clinici, si conserva, non si usa per il
marketing. Un file arrivato su WhatsApp resta nella conversazione e non conta
finché qualcuno non lo porta nella sezione "Clinica".

**La prima che scatta, e stop.** Tutte le regole chiamano la stessa funzione, e la
sua prima riga è "è già paziente? allora esci". La prima regola che arriva crea la
scheda paziente e scrive quale regola è scattata, quando e per mano di chi
("paziente dal 12/10/2026: primo dato clinico, allergia inserita dalla
dott.ssa Rossi"); le altre, dopo, non fanno più niente. Nello stesso momento la
funzione chiude come vinto il deal aperto della pipeline "Nuovi pazienti" e lancia
l'evento "Diventato paziente" per le automazioni (benvenuto, richiesta di
recensione dopo una settimana…).

**La stessa lista vale anche all'indietro.** Quando si accende il modulo su un
sito che ha già mesi di appuntamenti e fatture, un lavoro una tantum scorre le
persone e applica le regole nell'ordine della tabella, fermandosi alla prima che
trova. Nessuno deve segnare a mano i pazienti di prima.

Una fattura non sanitaria (un corso, un abbonamento) non rende nessuno paziente.

**Com'è fatto (29/09/2026), nello scheletro della clinica.** Il recupero non usa
l'ordine della tabella ma quello del tempo: per ogni persona vince il fatto che
sarebbe scattato per primo se la clinica fosse stata accesa da sempre, e "paziente
dal" è la sua data; a parità di momento decide la tabella. Una fattura di gennaio e
un appuntamento di marzo fanno un paziente da gennaio.

Quello che cambia per chi lavora:

- **Il medico vede una pagina sola.** Sulla pagina della persona compare la
  sezione "Clinica", solo per i ruoli clinici. Salvare la prima volta basta:
  sotto, il gestionale crea la scheda paziente e la collega. I dati restano in
  DocType separati per i permessi, ma la pagina è una.
- **Niente campi obbligatori per diventare paziente.** I dati anagrafici si
  completano quando capita. La scheda dice cosa manca senza bloccare chi scrive,
  e dal codice fiscale si ricavano da soli data di nascita e sesso (e il comune,
  con la tabella dei codici catastali; il controllo del codice c'è già in
  `crm/invoicing/engine/codice_fiscale.py`).
- **Visita, accettazione e fattura chiudono l'appuntamento.** Se la persona aveva
  un appuntamento oggi, salvare la visita, registrare l'arrivo al banco o emettere
  la fattura nata da quell'appuntamento lo segna come svolto. Presenze e no-show
  restano giusti anche dove nessuno aggiorna l'agenda.
- **Chi non segna niente riceve una domanda.** A fine giornata, per gli
  appuntamenti passati senza esito e senza fattura, un promemoria al medico:
  "sono venuti?", un clic sì o no. Senza risposta la persona resta contatto:
  meglio un paziente in meno che un no-show contato come paziente.
- **Paziente si resta.** Non si torna contatto, perché la cartella va conservata.

### Due mestieri, due facce dello stesso CRM

Stesso sito, stessa persona: menu, schede e numeri cambiano con il ruolo.

| | Marketing (voi, o chi fa commerciale nel centro) | Centro (segreteria, medici, direzione) |
|---|---|---|
| Menu | Persone, Richieste (i deal), Automazioni, Meta, Social, Sito | Agenda, Pazienti, Conversazioni, Fatture |
| Scheda della persona | da dove arriva, deal, campagne, conversazioni | appuntamenti, visite, documenti, consensi, fatture, conversazioni |
| Dashboard | richieste, costo per nuovo paziente per inserzione | appuntamenti di oggi, no-show, nuovi pazienti, da fatturare |
| Non vede | visite, referti, **fatture**, dati clinici | — |

Nel codice il meccanismo c'è già: le voci del menu (`AppSidebar.vue`, dove
"Invoices" usa proprio una `condition`) e le schede della persona
(`frontend/src/pages/Lead.vue`) hanno una `condition` ciascuna. Mancano i ruoli
clinici; quelli della fatturazione esistono già (Invoicing Manager, Invoicing
User).

**La forma del centro si deduce, non si configura**, come fa già la fatturazione:
`crm.invoicing.api.practice_shape` conta gli erogatori attivi. Con un erogatore
solo, il medico è anche segreteria e amministrazione e vede tutto; dal secondo i
mestieri si separano.

**I nomi si cambiano per sito, senza codice.** Frappe aggiunge alle traduzioni
delle app quelle del DocType `Translation` del sito (`get_all_translations`), e la
SPA le riceve da `crm.api.get_translations`. Sul sito di un centro "Deals" può
leggersi "Richieste" senza toccare gli altri clienti.

### Le tre cuciture fra i due mondi

Separare non basta: la dualità si gestisce nei tre punti in cui un mondo passa la
persona all'altro.

1. **Dal marketing al centro: diventare paziente chiude il deal.** La pipeline "Nuovi
   pazienti" va da richiesta a contattato, ad appuntamento fissato, a venuto
   (vinto) o perso. La prenotazione sposta il deal su "appuntamento fissato", la
   conversione a paziente su "venuto". Così il report delle inserzioni Meta, che
   conta i deal vinti (`cost_per_won` in `crm/integrations/meta/insights.py`), dice
   quanto costa un nuovo paziente, senza lavoro in più per nessuno. Con le
   automazioni di oggi non si fa: i trigger degli appuntamenti lavorano sulla
   persona, non sul deal (`resolve_reference` in `crm/automation/engine.py`). Lo fa
   la porta unica.
2. **Dal centro al marketing: il richiamo.** Pazienti che non vengono da un anno,
   controlli da ripetere, recensioni. Solo con il consenso al marketing, e
   scegliendo i destinatari su dati amministrativi (ultima visita, servizio
   prenotato), **mai su dati clinici** (diagnosi, referti, righe di fattura). Il
   marketing vede "non viene da 14 mesi", non il perché.
3. **Le conversazioni: un WhatsApp solo, due usi.** Lo stesso numero serve a chi
   chiede informazioni e a chi sposta un appuntamento. La segreteria risponde ai
   pazienti, il marketing alle richieste nuove, e in chat non passano contenuti
   clinici: i referti viaggiano su un canale protetto.

### Due pipeline, e molti pazienti senza deal

Oggi chi prenota da `/prenota` o da una piattaforma diventa persona e
appuntamento, **senza deal** (`find_or_create_person`). Chi compila un modulo del
sito o di Meta diventa persona e deal, perché qualcuno lo deve richiamare
(`open_deal_for_inquiry`). Una richiesta nuova non apre un secondo deal se ce n'è
già uno aperto (`open_deal_of`); a mano sì.

Per un centro medico bastano due pipeline, che il CRM supporta già
([guida](../../.pi/feats/pipelines/guide.md)):

- **Nuovi pazienti:** le richieste da pubblicità, moduli e telefonate, da
  richiamare fino alla prima visita.
- **Preventivi:** le cure costose (impianti, ortodonzia, medicina estetica,
  chirurgia, check-up), da preventivo consegnato ad accettato o rifiutato.

Il paziente che prenota le sue visite non ha deal, ed è giusto così:

| | Con un deal | Senza deal |
|---|---|---|
| **Paziente** | paziente con un preventivo aperto | paziente che prenota le sue visite |
| **Contatto** | richiesta da una pubblicità, da richiamare | chi ha scritto o prenotato ma non è mai venuto |

## Cosa c'è già e cosa manca

| Area | Oggi nel repo | Cosa manca per un centro medico |
|---|---|---|
| Persona | `CRM Lead` è la persona, con un solo `Contact` ([18](../progetto-ghl/18-persona-unica.md), [21](../progetto-ghl/21-lead-contatto-trattativa.md)): nome, sesso, email, cellulare. Codice fiscale e indirizzo stanno nella sua [anagrafica fiscale](#unanagrafica-fiscale-sola); genitore, figlio, chi paga e chi prenota sono [persone collegate](#le-persone-collegate) (29/09/2026) | ~~La scheda paziente, il tutore o il genitore per i minori~~: fatti il 29/09/2026 ([scheda](#lo-scheletro-della-clinica), [persone collegate](#le-persone-collegate)) |
| Agenda | Un motore solo: servizi, professionisti, stanze, attrezzature, listini condizionati, `/prenota`, piattaforme esterne, automazioni sugli stati. `Completed` e `Attended` si segnano a mano, con un clic dal pannello dell'appuntamento; la scheda della persona elenca i suoi appuntamenti e ne prenota uno ([14](../progetto-ghl/14-agenda-appuntamenti.md#un-calendario-due-cose-29092026)) | L'accettazione per chi ha la segreteria; la visita, l'accettazione e la fattura che chiudono da sole l'appuntamento |
| Fatturazione | `CRM Invoice` nasce dall'appuntamento (la coda "Dall'agenda, non ancora fatturati", `issue_from_appointment`); i medici sono gli erogatori (`CRM Service Provider`, con utente e qualifica); il canale lo decide la classificazione; Sistema TS con le credenziali del centro | ~~Il codice fiscale e l'indirizzo non si ricordano~~: fatto il 29/09/2026, con [l'anagrafica fiscale](#unanagrafica-fiscale-sola) |
| Privacy | Il [registro dei consensi](#il-registro-dei-consensi) (29/09/2026): quale testo, quale versione, quando, come; la spunta privacy di `/prenota` ci finisce, e la pagina chiede anche il marketing se il centro vuole. L'hook `user_data_fields` è commentato. Sulla fattura c'è già l'opposizione all'invio TS, documento per documento | I consensi della clinica: dossier, referti online, assistente |
| Clinica | La sezione Clinica della persona (29–30/09/2026): visite libere o sulla scheda della specialità, firmate e poi solo integrate, con gli allegati, il referto in PDF/A e la sintesi del paziente; i moduli e i consensi informati firmati; il registro degli accessi alla cartella | ~~Cartella per specialità, referti, consensi informati, allegati~~: fatti il 30/09/2026. L'archivio dei documenti e il registro degli accessi anche sull'archivio: fatti il 30/09/2026. Restano dossier e oscuramento, la consegna del referto |
| Ruoli | System Manager, Sales Manager, Sales User; Invoicing Manager e Invoicing User. Ogni utente vede tutti gli appuntamenti. **Sales User legge tutte le fatture** (permesso di lettura ed export su `CRM Invoice`), e dalla PR #101 le fatture compaiono anche nella cronologia della persona: `invoices_on` in `crm/api/activities.py` le legge con `frappe.get_all`, che salta i permessi (solo intestazione, importi e stati, niente righe) | Tre livelli (Segreteria, Manager amministrativo, Operatore) con la gestione dei ruoli nel CRM; System Manager e Administrator solo all'agenzia, mentre oggi l'"Admin" del CRM **è** System Manager ([requisiti §1](./requisiti.md#1-tre-livelli-e-il-site-resta-vostro)). Il marketing non deve leggere le fatture: una riga "seduta di psicoterapia" è un dato sanitario |
| Moduli | Nessun interruttore per modulo: `crm/dashboard/features.py` rileva cosa usa il sito, ma serve solo alla dashboard | Un interruttore "centro medico" che accende menu, pagine, impostazioni, widget e job |

Il resto (conversazioni su tutti i canali, automazioni, prenotazione online,
telefono, dashboard, sito, e ora le fatture) è più avanti di quello che offrono i
gestionali medici italiani sulla stessa parte. **È il vantaggio da difendere: non
va rifatto, va collegato.**

### Un'anagrafica fiscale sola

Il codice fiscale e l'indirizzo sono **della persona, non del paziente**: li chiede
la fattura di un consulente come quella di un fisioterapista. Quindi non stanno
nella scheda paziente, ma in un'anagrafica fiscale della fatturazione (per esempio
un `CRM Billing Profile` uno a uno con la persona):

- la fattura la legge in `compila_da_controparte`, come oggi legge nome e cognome;
- una fattura confermata la completa dove è vuota, così il secondo documento non
  chiede niente;
- la sezione "Clinica" mostra e modifica gli stessi campi: il medico che scrive il
  codice fiscale lo scrive una volta per tutti.

È un pezzo della fatturazione, non della clinica, perché serve a tutti i settori;
la clinica lo legge. Sta fuori da `CRM Lead` perché il marketing, che le persone
le vede, il codice fiscale non ha bisogno di vederlo.

**Com'è fatta (29/09/2026).** `CRM Billing Profile`, uno per persona e uno per
organizzazione (un indice unico lo tiene anche nel database): codice fiscale,
partita IVA, codice destinatario, PEC, indirizzo e, per un'azienda, la ragione
sociale. Data di nascita e sesso si leggono dal codice fiscale, non si scrivono.

- **La fattura lo legge** (`compila_da_controparte`): prende quello che ha lasciato
  vuoto, l'indirizzo tutto insieme. Una trattativa porta alla persona se la
  fattura è a una persona, alla sua organizzazione se è a un'azienda; un contatto
  alla sua persona.
- **La fattura confermata lo completa** dove è vuoto, e non sovrascrive mai. Non lo
  fa se la fattura è intestata a un altro, come il genitore che paga per il figlio:
  si confrontano le parole dei due nomi, così "Mario Rossi" scritto tutto nel nome
  da un modulo web resta la stessa persona. Le fatture già emesse hanno fatto lo
  stesso con una patch, dalla più recente.
- **Sulla pagina della persona** (e dell'organizzazione) c'è la sezione "Billing
  details" per chi ha `persone.dati_fiscali`: Segreteria, Manager, Operatore. Il
  profilo segue la persona: lo legge chi vede la persona. Un codice fiscale che non
  torna col suo carattere di controllo non si salva; uno che non torna con il nome,
  il cognome o il sesso della persona, o che sta anche su un'altra, si segnala e
  non si blocca.
- La sezione Clinica, quando arriva, mostra gli stessi campi (la PR 6).

### Il registro dei consensi

Fatto il 29/09/2026, nel CRM e non nella clinica, perché serve a tutti: in
`crm/moduli`, dove andranno anche i modelli e le firme della fase 2.

- **Un tipo di consenso** (`CRM Consent Type`) è una chiave che il codice chiede
  ("possiamo scrivergli?") e un testo che la persona legge. Il testo è del centro,
  lo controlla chi risponde della privacy, e ogni modifica è una versione nuova. I
  moduli registrano i loro tipi come registrano le capacità: il CRM porta
  l'informativa (presa visione, non si revoca) e il marketing; la clinica porterà
  dossier, referti online e assistente. Il centro può aggiungerne di suoi (le foto
  sui social).
- **Una risposta** (`CRM Consent`) dice sì o no, quando, come (online, al banco,
  su carta, al telefono, per email), su quali parole e con quale versione; da
  quale prenotazione, con IP e browser se viene dal sito. Non si modifica mai: la
  revoca si timbra sulla stessa riga, un nuovo sì è una riga nuova. Lo stato di
  una persona è la sua ultima risposta.
- **`/prenota`** registra la spunta dell'informativa con le parole che la pagina
  ha mostrato, nella lingua del visitatore, e l'indirizzo dell'informativa. Se il
  centro lo accende nelle impostazioni della prenotazione, chiede anche il
  marketing: una casella facoltativa e mai spuntata in anticipo, col testo del
  centro.
- **Sulla pagina della persona** la sezione "Consents": lo stato di ogni tipo, e
  un bottone per registrare una risposta o revocare. Revocare è facile quanto
  dare (art. 7(3) GDPR): chi sente "non scrivetemi più" lo registra, commerciale
  compreso. I testi si cambiano in Impostazioni › Consents, dal Manager.
- **Il marketing si specchia sulla persona** (`marketing_consent`), così liste e
  automazioni filtrano su "possiamo scrivergli" senza leggere il registro: è il
  mattone dei richiami col consenso della fase 1.
- Le risposte seguono la persona: le legge chi vede la persona, e se ne vanno
  con lei quando la si cancella.

Restano per dopo: le risposte che arrivano dalle piattaforme (MioDottore porta
`marketing_consent` e `data_privacy_consent` sulle prenotazioni che gli mandiamo),
i moduli web del CRM, e il collegamento "da quale modulo" quando arrivano i
modelli firmati della fase 2.

### Lo scheletro della clinica

Fatto il 29/09/2026, in `crm/clinica` (Frappe module "Clinica"):

- **L'interruttore è il piano.** Il modulo "clinica" del `CRM Plan` è spento di
  serie; lo accende l'agenzia. Spento, nessuna regola converte nessuno e le
  capacità della clinica non sono di nessuno. Acceso, parte una volta sola, in
  background, il recupero dei pazienti dagli appuntamenti e dalle fatture che ci
  sono già.
- **La porta unica** è `paziente.assicura_paziente`: "è già paziente? allora
  esci", poi la scheda (`Clinic Patient`, una per persona) con la regola, il
  momento, il documento che l'ha fatta scattare e chi.
- **Le regole di oggi**: appuntamento svolto (completato, o il partecipante
  presente; chi non si è presentato resta contatto), fattura sanitaria confermata,
  importazione (una scheda importata prende la regola da sola), a mano ("Mark as
  patient" sulla pagina della persona). Il primo dato clinico arriva con la
  sezione Clinica, l'accettazione con la fase 1. Un servizio che il centro fattura
  come non sanitario (un corso) non fa pazienti, come la sua fattura.
- **Chi lo sa**: segreteria, operatore (i suoi), manager e il nuovo livello
  **Direzione sanitaria** (ruolo Medical Director). Il commerciale e il marketing
  no: né la sezione "Patient", né i consensi della clinica (dossier, referti
  online), che dicono già da soli che qualcuno è paziente. L'agenzia solo con un
  accesso clinico; può però lanciare il recupero, che è un lavoro sui dati.
- **Paziente si resta**: la persona che è paziente non si cancella, perché la
  cartella va conservata; lo dice con parole sue invece di un collegamento rotto.
- **Il confine è un test** (`crm/clinica/tests/test_confine.py`): né il CRM né
  la fatturazione importano la clinica, che si aggancia con gli eventi dei
  documenti (appuntamento, fattura, piano, cancellazione) e con i registri. Solo
  `crm/registrazione.py` la nomina.

Restano per la fase 1 il deal che si chiude, l'evento per le automazioni e il
widget "nuovi pazienti": fatti con [la prima cucitura](#la-prima-cucitura-diventare-paziente-chiude-il-deal).

### La sezione Clinica

Fatta il 29/09/2026: la scheda "Clinic" sulla pagina della persona, con la visita
semplice (testo e allegati) e il registro degli accessi.

- **La visita** (`Clinic Record`, una visita o una nota) è dell'autore finché è
  una bozza; firmata non si riscrive più, si aggiunge ("Add to it"). Gli allegati
  sono privati, o non si attaccano. La prima voce salvata fa della persona un
  paziente (regola 1), dalla classe base di tutti i documenti clinici
  (`crm/clinica/base.py`): un test controlla che tutti ne ereditino.
- **Chi la legge**: l'autore sempre; la direzione sanitaria quando è firmata; gli
  altri operatori solo se il paziente ha dato il consenso al dossier. Una voce
  "Only me" resta dell'autore. La segreteria sa che c'è stata una visita (un
  lucchetto nella cronologia, con chi l'ha fatta), non cosa si è detto; manager,
  commerciale e marketing non la vedono. Nessun permesso a System Manager: il
  supporto sulla cartella sarà un accesso a tempo.
- **Il registro degli accessi**: ogni lettura della scheda scrive un View Log
  (la SPA non passa dal form del Desk, che lo scrive da solo); il manager e la
  direzione vedono chi l'ha aperta e quando, non cosa. Il View Log si tiene almeno
  24 mesi: se qualcuno lo mette in Log Settings sotto i 730 giorni, torna a 730.
- **La cronologia si apre ai moduli** con l'hook `crm_timeline_gatherers`: il CRM
  non sa niente della clinica, la clinica aggiunge i suoi nodi.
- **La direzione sanitaria** ha del CRM quello che dice la sua colonna nel doc 30:
  persone, consensi, agenda in lettura, calendario, dashboard e numeri operativi;
  non le conversazioni, e i canali che non può aprire non le compaiono.

Resta per la fase 2 la cartella vera: i modelli per specialità, la firma, i
referti, l'oscuramento, l'apertura fuori équipe con il motivo.

### Le persone collegate

Fatte il 29/09/2026. Il paziente, chi paga e chi prenota possono essere tre persone
- il bambino, il genitore che paga, la nonna che telefona - e il CRM lo sa. Era la
decisione lasciata alla fase 0: come riconoscere una persona quando in famiglia email
e telefono sono di tutti.

- **Un legame per coppia** (`CRM Related Person`, `crm/persone/`): Maria è il
  genitore di Luca, e per lui paga, prenota o decide. Si scrive dal lato di chi è
  seguito e si legge dai due lati: sulla pagina di Maria, Luca è suo figlio. Pagare,
  prenotare e decidere sono tre cose diverse: il padre separato che prenota il
  sabato non è per forza quello che paga.
- **Il contatto è di chi lo possiede.** Il figlio prenotato dalla madre ha un record
  suo, senza l'email e il telefono di lei. Restano suoi: una chiamata da quel numero
  è sua, e i messaggi sugli appuntamenti di Luca le arrivano dalla prenotazione, che
  lo dice ("Booked by" sulla riga dell'appuntamento). La pagina di Luca dice da chi
  passano i messaggi, e il pannello dell'appuntamento, scelto Luca, mette i recapiti
  di lei.
- **Chi è la persona di una prenotazione.** Il contatto trova il suo titolare; il
  nome dice se è lui o una delle persone collegate a lui, e a loro: il padre che
  prenota con l'email della madre trova il figlio. Un nome che non c'è è una persona
  nuova, collegata al titolare: mai il record di un altro. I nomi si confrontano per
  parole, come faceva già la fattura: "Mario Rossi", "Rossi Mario" e "Mario" sono
  la stessa persona; "Luca" e "Lucia" no, e nemmeno "M. Rossi". Un doppione si unisce
  in un minuto; una visita scritta sulla persona sbagliata si scopre quando è tardi.
  Un record che ha per nome un'email o un numero non dice chi è: la prenotazione
  con un nome vero sul suo contatto è sua.
- **`/prenota` chiede per chi è l'appuntamento**: per me, o per un'altra persona, con
  il suo nome e cosa si è per lei. L'informativa la legge chi prenota, per sé e per
  l'altro, e il registro dei consensi scrive chi ha risposto; il marketing è di chi
  prenota, che riceve i messaggi. I limiti per cliente contano chi viene: la madre che
  prenota per due figli prenota tre persone, non una tre volte.
- **La fattura va a chi paga**, quando paga uno solo: la visita della figlia è
  intestata al padre, con i suoi dati fiscali, e la causale dice "Prestazione resa a
  Giulia Rossi" con il suo codice fiscale. Se la cassa la intesta alla figlia (il suo
  nome o il suo codice fiscale), resta sua e niente del padre ci finisce dentro. La
  fattura confermata completa l'anagrafica di chi nomina.
- **Il paziente minorenne.** L'età viene dal codice fiscale: la sezione Paziente dice
  chi firma e decide per lui, e avvisa se è minorenne e non c'è nessuno. Al banco il
  consenso si registra anche come dato da uno dei collegati. Il campo "tutore" della
  scheda paziente è diventato un legame: una patch sposta quello che c'era.
- **Chi li vede**: un legame è delle due persone, lo vede chi vede una delle due; lo
  scrive chi scrive le persone, fra due persone che vede entrambe.

### La prima cucitura: diventare paziente chiude il deal

Fatta il 29/09/2026 (fase 1), in `crm/clinica/pipeline.py`:

- **Le due pipeline nascono con la clinica.** Quando l'agenzia la accende, il CRM
  crea "Nuovi pazienti" (richiesta, contattato, appuntamento fissato, venuto,
  non venuto) e "Preventivi" (da fare, consegnato, accettato, rifiutato), nella
  lingua del sito. Una pipeline con quel nome fatta a mano si usa così com'è. In
  Impostazioni → Pipeline, la sezione "Centro medico" dice quali sono e dove una
  prenotazione sposta la richiesta (`Clinic Settings`), e le crea se mancano.
- **La prenotazione sposta la richiesta** aperta di "Nuovi pazienti" su
  "appuntamento fissato"; una già più avanti resta dov'è, e le altre pipeline non
  si toccano.
- **Diventare paziente la vince**, con la data di chiusura di oggi. Il report delle
  inserzioni Meta conta i deal vinti di ogni inserzione, e così dice quanto costa
  un nuovo paziente; il widget "Cost per new patient" lo fa per tutto il periodo
  (la spesa divisa per chi è arrivato dagli annunci ed è diventato paziente), e
  "New patients" li conta. Un deal che non si salva non ferma il paziente: si
  scrive nel log.
- **Le automazioni lo sentono**: il trigger "Became Patient", sulla persona, con la
  regola che l'ha fatto. Il costruttore lo offre solo dove la clinica è accesa: il
  CRM non lo nomina, la clinica lo registra (`registra_evento`).
- **Solo chi diventa paziente adesso.** I pazienti trovati nei dati di prima,
  all'accensione, non chiudono deal e non fanno partire automazioni: non sono una
  notizia.

### La seconda cucitura: la giornata della segreteria

Fatta il 29/09/2026 (fase 1), in `crm/scheduling/esiti.py`, `crm/api/oggi.py` e nella
pagina **Oggi** (`/crm/oggi`, per chi ha `agenda.presenze`):

- **L'accettazione.** Al banco si dice che qualcuno è arrivato: il partecipante
  passa a "Arrived" e la sala d'attesa conta da quel momento. Con la clinica accesa
  è la regola 2 per diventare paziente, con l'ora dell'arrivo; il recupero dei dati
  di prima la legge anche lui.
- **L'appuntamento si chiude da solo** quando ognuno dei suoi partecipanti è venuto
  o no: Completed, o No Show se non è venuto nessuno. Lo dicono la segreteria o il
  medico, la visita scritta per quell'appuntamento e la fattura emessa da lui (solo
  a appuntamento iniziato: una fattura fatta prima non dice niente). Un esito si
  può disfare, e l'appuntamento si riapre.
- **Chi lo dice**: `agenda.presenze` del doc 30, la segreteria e il manager per
  tutti gli appuntamenti, l'operatore per quelli che lavora.
- **Fine giornata.** Finito l'ultimo appuntamento, chi era in sala d'attesa e
  nessuno ha segnato conta come venuto, e la segreteria riceve una notifica, una
  volta al giorno: "N appuntamenti di oggi non hanno un esito: sono venuti?". La
  notifica apre la pagina Oggi.
- **La pagina Oggi**: quanti attesi, in sala, venuti e non venuti; la sala
  d'attesa con i minuti; gli appuntamenti del giorno, con "accetta", "è venuto",
  "non è venuto" e "annulla"; gli ultimi sette giorni rimasti senza esito; e
  quanti appuntamenti sono ancora da fatturare, per chi fattura. Il giorno è
  quello del centro, non del browser. Sul telefono nome e pulsanti stanno su due
  righe.

Resta alla fase 2 "i moduli da firmare oggi", che aspetta la firma.

### La terza cucitura: il richiamo, e la dashboard del centro

Fatta il 29/09/2026 (fase 1). Con questa la fase 1 è completa.

- **Si sceglie su dati amministrativi.** La persona ha l'ultima visita e il suo
  servizio (`last_visit`, `last_service`), che l'agenda tiene da sé quando un
  appuntamento si chiude con la persona venuta; una patch li trova negli
  appuntamenti di prima. Mai la cartella: il marketing vede "non viene da 14 mesi",
  non il perché.
- **Solo con il sì.** Un'automazione può chiedere il consenso al marketing ("Only
  people who agreed to marketing"). Chi non l'ha dato non entra, e le esecuzioni lo
  dicono ("Skipped: no marketing consent"), una volta sola per persona; se lo dà più
  tardi entra. Se il consenso viene revocato mentre è dentro, i messaggi non partono.
- **Il richiamo è una ricetta**: "Recall after a year", un Date Reminder un anno
  dopo l'ultima visita, con il consenso chiesto; un'email, una settimana di attesa,
  l'obiettivo "ha prenotato" e un task per telefonare a chi non l'ha fatto.
- **La dashboard del centro** ("Medical centre"), registrata dalla clinica e creata
  quando la si accende (una patch la crea dove la clinica era già accesa):
  - nuovi pazienti e costo di un nuovo paziente;
  - l'agenda di oggi, il tasso di non presentati e chi è "da richiamare" (ultima
    visita oltre un anno fa, con il consenso);
  - l'incassato, gli appuntamenti da fatturare e da confermare;
  - l'andamento dell'agenda e i servizi più prenotati.

  Un modulo registra i suoi modelli (`templates.registra`), e un modello dice di
  che feature ha bisogno.
- **Accendere la clinica legge il piano appena salvato.** Frappe esegue gli hook
  prima di togliere il piano dalla cache: la clinica appena accesa risultava spenta,
  e non partivano né il recupero dei pazienti, né le pipeline, né la dashboard. Ora è
  il piano stesso a togliersi dalla cache, con i livelli e le feature della
  dashboard.

### Il motore dei modelli

Fatto il 30/09/2026 (fase 2, la prima parte). Sta nel CRM (`crm/moduli`), non
nella clinica: privacy, consensi e questionari servono anche a una palestra
([design](./design.md#il-motore-dei-modelli)).

- **Una bozza, poi versioni.** Un modello (`CRM Form Template`) si costruisce in
  Impostazioni → Forms, scheda "Forms to sign", accanto ai moduli web dei lead: un
  builder solo, due destinazioni. La gente compila una **versione pubblicata**
  (`CRM Form Template Version`), che non cambia più: ha l'impronta SHA-256 dello
  schema e, dentro lo schema, **le parole esatte dei consensi** prese dal registro
  il giorno della pubblicazione. Se il centro riscrive il testo del marketing, il
  modello dice "Changes not published": la versione nuova porta il testo nuovo, e
  chi pubblica sceglie da che giorno richiederla a chi aveva firmato la vecchia.
- **I componenti**: testo (con le frasi pronte), numero con unità e limiti, scelta
  singola o multipla con i punteggi, sì/no, data, scala, tabella (i farmaci),
  destra e sinistra, allegato, testo da leggere, calcolo (il BMI), punteggio con le
  fasce, consenso del registro, firma di paziente, operatore o tutore con il suo
  livello (semplice, avanzata, qualificata).
- **La logica**: "mostra se", "obbligatorio se", "ferma e avvisa l'operatore se",
  scritte con lo stesso costruttore di condizioni delle automazioni. Una domanda
  guarda solo quelle prima di lei (per mostrarsi, per calcolare, per contare), così
  un solo passaggio in ordine decide tutto; una risposta nascosta non conta e non
  si tiene. "Obbligatorio se" e "ferma se" possono guardare ovunque.
- **La stessa logica, due volte, provata sugli stessi casi.** `crm/moduli/schema.py`
  sul server e `frontend/src/utils/moduli.js` nel browser leggono
  `crm/moduli/tests/casi_schema.json` (condizioni, formule, valutazioni di moduli
  interi, validazioni). In più un confronto su 24.000 schemi casuali ha dato zero
  differenze fra i due lati: quello che la persona vede compilando è quello che il
  server decide.
- **Si prova prima di pubblicare**: "Try it" compila il modulo come farebbe la
  persona, con i calcoli, le condizioni e gli avvisi veri; "Check it" dice cosa
  manca. Quel che non va (un'opzione doppia, una formula che guarda avanti) è
  elencato mentre si scrive, e blocca solo la pubblicazione, non il salvataggio.
- **Quattro modelli di partenza**: informativa e consensi, anamnesi di prima visita
  (con BMI, allergie, farmaci, fumo), consenso informato a un trattamento (con il
  campo che l'operatore scrive per quella persona e l'avviso sul pacemaker),
  questionario prima della visita (dolore e un punteggio a fasce). I testi sono da
  far scrivere e controllare al centro.
- **Chi li scrive**: `moduli.configura`, al manager; con la clinica anche alla
  direzione sanitaria. Il marchio "dato clinico" c'è solo dove la clinica è accesa
  (lo registra la clinica, `modelli.registra_dato_clinico`) e resta nella versione.

### Compilare e firmare

Fatto il 30/09/2026 (fase 2, la seconda parte).

- **Dalla persona**: la scheda "Forms" della sua pagina elenca i moduli firmati e
  quelli da finire, e "Fill a form" ne comincia uno sulla versione pubblicata. Si
  compila con lei al banco, si salva a metà, si firma sullo schermo.
- **La firma semplice, col dito**: si tiene l'immagine del tratto, mai la
  pressione né i tempi dei punti (sarebbero dati biometrici). Con chi firma (il
  paziente, l'operatore, il genitore o tutore indicato in "Answered by"), l'ora
  del server, l'indirizzo e il dispositivo, e l'impronta delle risposte su cui è
  stata messa. Un campo che il modello vuole con firma avanzata o qualificata non
  si firma col dito: si firma con un fornitore o su carta, che arrivano con i canali
  di firma.
- **Firmando** il server rifà tutti i controlli con le sue regole (le stesse che il
  browser ha mostrato), e il modulo si chiude: da lì non si riscrive.
- **Il PDF/A**, fatto una volta sola alla firma: le risposte in parole, i testi
  letti, gli avvisi per l'operatore, le firme come immagini dentro il file, e una
  pagina delle prove (versione e impronta di cosa chiedeva, impronta delle
  risposte, chi ha firmato, come, quando, da dove, gli eventi). WeasyPrint lo
  disegna, il motore PDF/A della fatturazione lo converte e dice cosa ne è uscito
  ("PDF/A-3b (structure verified)"); il suo SHA-256 resta sul modulo.
- **I consensi** del modulo vanno nel registro con le parole congelate nella
  versione e la loro versione del testo, il modulo come fonte, il canale e chi ha
  risposto per la persona.
- **Il registro degli eventi** (`CRM Audit Log`) si aggiunge soltanto: iniziato,
  firmato, PDF fatto, consenso registrato, ciascuno con l'impronta di quello
  prima. Un evento cambiato rompe la catena da lì in poi, e
  `traccia.verifica_catena` dice dove.
- **Chi li vede**: seguono la persona, come i consensi (`moduli.vedi`,
  `moduli.compila`). Un modulo con dati sanitari è della sola squadra di cura: lo
  dice la clinica (`compilazioni.registra_lettore_clinico`), e firmato fa diventare
  paziente (regola 1).

### Dove si firma: il tablet del banco e il link a casa

Fatto il 30/09/2026 (fase 2, la terza parte).

- **"On their own"**, sulla scheda Forms della persona: si scelgono uno o più moduli
  e come darli. Un solo link apre tutti i moduli scelti.
- **Il link a casa**: arriva per email alla persona o, per chi firma un genitore o
  un tutore (le persone collegate con "decide per lui"), a loro; a un minore senza
  chi firma per lui non parte. Il messaggio dice che ci sono moduli da compilare
  prima della visita, mai quali: il titolo di un consenso può dire a cosa serve la
  visita. Aperto il link, un codice di sei cifre va allo stesso indirizzo (dieci
  minuti, cinque tentativi, tre codici l'ora) e solo dopo si vedono i moduli. Si
  compila, si salva e si riprende dallo stesso link, si firma col dito, si scarica
  la propria copia firmata. Il link vale 7 giorni e si ritira dalla scheda.
- **Il tablet del banco**: l'operatore sceglie i moduli e chi tiene il tablet (la
  persona o chi firma per lei). Il CRM esce dal suo utente su quel dispositivo e
  apre la pagina dei soli moduli di quella persona, senza codice: l'operatore ha
  visto chi lo tiene. La pagina si lega a quel browser la prima volta che si apre;
  firmato l'ultimo modulo dice di riconsegnare il tablet, e lo stesso indirizzo non
  riapre più niente.
- **Firmato fuori dal banco è firmato come al banco**: stessi controlli, stesse
  prove, stesso PDF/A. Il modulo non ha un autore del centro ("compilato dalla
  persona"); le prove dicono come è stato riconosciuto chi ha firmato (il tablet
  consegnato da chi, o il link e il codice a quale indirizzo) e il registro
  aggiunge invio, apertura, codice mandato e codice verificato.
- **Quello che non si firma da soli si firma al banco**: un modulo con la firma
  dell'operatore, o con una firma avanzata, si manda lo stesso. La persona lo
  compila e preme "Ho finito"; le risposte si controllano subito e il modulo aspetta
  nella scheda come "Da firmare al banco".
- **Una sola regola**: la pagina `/modulo` usa lo stesso motore del CRM (il file è
  lo stesso, copiato tra gli asset e tenuto uguale da un test), e il server rifà
  tutto quando si firma.

### Su carta e con un fornitore di firma

Fatto il 30/09/2026 (fase 2, la quarta parte).

- **Su carta** ("Other ways to sign" → "On paper" nella pagina del modulo): si
  stampa la copia da firmare con le risposte date fin lì (le risposte vuote sono
  caselle da barrare o righe su cui scrivere, e sotto ogni firma c'è il nome di chi
  firma), la persona firma, si carica la scansione (PDF, JPG o PNG, privata) e
  l'operatore attesta che è copia conforme dell'originale firmato davanti a lui.
  Le risposte scritte nel CRM si controllano come sempre. La firma è registrata
  come autografa ("handwritten", su carta); la scansione entra nel PDF/A come file
  allegato (la sua fonte) e, se è un PDF, con le sue pagine; il suo SHA-256, chi
  l'ha attestata e quando stanno sul modulo e nella pagina delle prove.
  L'originale di carta resta al centro. Un modulo con firma avanzata, senza
  fornitore, si firma su carta.
- **Con un fornitore** (`crm/moduli/firme.py`): la firma avanzata (il codice SMS
  del fornitore, dopo il riconoscimento con un documento) e quella qualificata
  vengono da un fornitore. Il CRM gli chiede cinque cose, chiunque sia: creare la
  busta, la pagina di firma, cosa dice il suo webhook, il PDF firmato (PAdES), le
  sue prove. Un fornitore è una classe registrata con `registra_fornitore`; il
  centro lo sceglie in `CRM Signature Settings` (le chiavi sono dell'agenzia).
  Il modulo mandato al fornitore non si cambia più; firmato, il webhook lo chiude
  con il PDF del fornitore così com'è (convertirlo romperebbe la firma) e le sue
  prove accanto. Rifiutato o scaduto torna una bozza; si può anche riprendere.
  Nessun fornitore reale è ancora collegato: Namirial, InfoCert o Intesi si
  aggiungono come una classe ciascuno, quando il centro sceglie.

### I moduli dovuti: quando si chiede

Fatto il 30/09/2026 (fase 2, la quinta parte).

- **Quando si chiede** lo dice il modello: a mano, al primo appuntamento, per alcuni
  servizi; e quanto vale uno firmato: per sempre, un anno, un appuntamento. Una
  versione nuova può richiederlo a chi aveva firmato la precedente, da una data.
  La regola è una sola e pura (`crm/moduli/dovuti.py`, `dovuto`).
- **Nella scheda Forms** della persona, "To sign for the appointment of…": i
  moduli che deve per il suo prossimo appuntamento (o in generale), con il perché
  (mai firmato, versione nuova, firmato più di un anno fa, uno per appuntamento) e
  cosa è già in corso (iniziato, link mandato, da firmare al banco). "Fill" lo
  comincia legato all'appuntamento; "On their own" li trova già scelti.
- **Nella pagina Oggi**, accanto a ogni persona, "N forms to sign": si firmano
  mentre aspetta. I moduli con dati sanitari solo per chi li legge.
- **Con la prenotazione**: un modello può dire "Send the link when an appointment
  is booked". Prenotato un appuntamento (dal CRM o da /prenota), chi deve quel
  modulo riceve il link, uno per persona con tutti i moduli, valido fino all'ora
  della visita; non se manca meno di un'ora, non se un link per quel modulo è già
  aperto, non se non c'è un indirizzo. Il messaggio non dice quali moduli.

Corretto insieme: la fine della giornata (le accettazioni che diventano "venuto" e
la domanda "sono venuti?") perdeva un giorno il cui ultimo appuntamento finiva dopo
le 23: ora guarda anche il giorno prima, e chiede una volta sola per giorno.

Resta alla fase 2: la cartella sul modello della specialità, i referti,
l'archivio. "Dal modulo di carta", con l'assistente che propone i campi, va alla
fase 4.

### La scheda clinica, il referto e la sintesi

Fatto il 30/09/2026 (fase 2, la sesta parte).

- **La scheda clinica** è un modello come gli altri, con l'uso "Clinical sheet"
  che registra la clinica (`modelli.registra_uso`, `clinico=True`): è sempre dato
  clinico, la scrive l'operatore e non il paziente. Non si manda, non si compila
  da un link o dal tablet, non è mai un modulo dovuto: solo l'uso "Form" lo è.
  Nella sezione Clinica, "New visit" offre la visita libera e le schede
  pubblicate; la visita si scrive sulla scheda, con gli stessi componenti dei
  moduli (i calcoli come il BMI compresi), più le note.
- **Firmata**, la visita si controlla con lo stesso motore dei moduli
  (obbligatori, "ferma e avvisa"), le risposte si fermano con la loro impronta
  (lo SHA-256 dello schema della versione e delle risposte) e nasce il
  **referto** (`crm/clinica/referto.py`): un PDF/A con la scheda in parole, le
  note, chi ha firmato e quando, la versione e le impronte. Si fa una volta
  sola, privato, e la visita ne tiene lo SHA-256; si apre dal link "Report"
  della visita, non sta fra gli allegati. Firmata, la visita non si riscrive: si
  integra, come prima.
- **La sintesi del paziente** (`crm/clinica/sintesi.py`): allergie, farmaci,
  patologie, peso, altezza, pressione, frequenza cardiaca. Nel builder, un campo
  di un modello clinico dice quale riga riempie ("Goes to the patient's summary
  as"). Quando si firma un modulo o una scheda con quella risposta, la risposta
  si propone; l'operatore la conferma, anche corretta, o la scarta, e può
  scrivere una riga a mano. La riga è l'ultimo valore confermato; ogni valore
  resta (`Clinic Summary Value`), con da dove viene e chi l'ha deciso. La legge
  chi legge la cartella, la decide chi la scrive.

Il referto porta le impronte ma non ancora il sigillo del centro, la marca
temporale o la firma qualificata del professionista: arrivano con il fornitore di
firma. Resta alla fase 2: l'archivio clinico dei documenti, il registro degli
accessi anche sull'archivio, dossier e oscuramento, la consegna del referto.

### L'archivio clinico e il registro degli accessi

Fatto il 30/09/2026 (fase 2, la settima parte).

- **L'archivio** (`crm/clinica/archivio.py`, `Clinic Document`), nella sezione
  Clinica sotto la sintesi, raccoglie i documenti del paziente: referti esterni,
  esami, immagini, prescrizioni, moduli firmati su carta, altro. Ognuno ha il tipo,
  la data, da dove viene e per quale operatore; il file è privato e se ne tiene lo
  SHA-256. Un documento clinico fa diventare paziente, come la visita (regola 1),
  ma non dice che la persona è venuta: un esame può arrivare prima della visita.
- **Il referto di ogni visita firmata** ci entra da solo: ora anche la visita
  libera ha il suo PDF/A. È il PDF della visita, si legge con le regole della
  visita e non si toglie. Un'integrazione ha il suo referto, che dice a quale
  visita si aggiunge; una nota non ne ha.
- **Chi lo legge** segue le regole della cartella: l'operatore per cui è e chi
  l'ha aggiunto; la direzione sanitaria; gli altri operatori solo con il consenso
  al dossier. "Only me" resta dell'operatore.
- **Chi aggiunge** un documento:
  - l'operatore, per i suoi pazienti (`clinica.archivia`);
  - la segreteria, che scansiona quello che porta il paziente e dice per quale
    operatore. Vede solo quello che ha aggiunto, e la scheda Clinica le si apre
    per questo.
- **Un errore** (la persona sbagliata, il file sbagliato) si toglie in giornata
  da chi l'ha aggiunto, poi solo dalla direzione sanitaria. Si scrive il motivo,
  e il registro degli eventi tiene chi, quando, perché e l'impronta del file.
- **Dalla conversazione**: su un file ricevuto su WhatsApp, "Add to the clinical
  archive" lo porta nell'archivio della persona che l'ha mandato. Il file della
  conversazione, che frappe_whatsapp salva pubblico, diventa privato: resta
  leggibile da chi legge la conversazione, non più da chiunque abbia l'indirizzo.
- **Il registro degli accessi** ("Who opened it") mette insieme tre cose, una riga
  per persona, minuto e tipo:
  - la cartella aperta;
  - l'archivio aperto;
  - ogni file scaricato, che Frappe registra da sé nell'Access Log.

  Anche l'Access Log si tiene almeno due anni.

Resta alla fase 2: il dossier con l'oscuramento degli episodi e l'apertura fuori
équipe con un motivo; la consegna del referto al paziente.

## Decisione 1 — Niente Marley Health e niente ERPNext

Marley Health è l'ex modulo Healthcare di ERPNext, oggi un'app a sé mantenuta da
Earthians: viva (v16.6.1 del 22/09/2026), GPL-3, circa 130 DocType, gratuita sul
marketplace di Frappe Cloud. Ma vuole ERPNext, ha l'interfaccia per lo più nel
Desk, non ha una traduzione italiana e non risulta usata in Italia (dettagli e
fonti in [ricerca.md](./ricerca.md#1-lecosistema-frappe)). Non conviene adottarla,
per tre motivi.

1. **Porta una seconda agenda e una seconda anagrafica.** `Patient`,
   `Patient Appointment`, `Healthcare Practitioner`, `Practitioner Schedule`,
   `Healthcare Service Unit`: proprio la dualità da evitare, accanto
   all'agenda appena unificata ([sistema-unico](../prenotazioni/sistema-unico.md)).
2. **Vuole ERPNext su ogni sito.** Un server da $40 regge 8–12 siti perché il limite
   è la RAM e lo scheduler di ogni sito ([25](../progetto-ghl/25-costo-hosting.md)).
   ERPNext più Marley su ogni sito medico cambiano quel conto.
3. **La parte italiana ce l'avete già, e meglio.** Marley non sa niente di Sistema
   TS, esenzioni, bollo e divieto SDI; `crm/invoicing` sì.

Da Marley si prende **il modello dati come riferimento** (come separa appuntamento,
incontro clinico, procedura e referto) e, dove serve, singoli pezzi di codice: la
GPL-3 si combina con la vostra AGPL-3. L'app intera no.

## Decisione 2 — Un verticale dentro `crm`, con le regole di un'app separata

**È la strada che la fatturazione ha già preso**, e ha funzionato: `crm/invoicing`
e `crm/tessera_sanitaria` sono due moduli dentro `crm`, la dipendenza va in una
direzione sola, il modulo sanitario si registra da `crm/hooks.py` (`registra()`) e
si aggancia ai punti di estensione di `crm/invoicing/estensioni.py`, e
`crm/invoicing/tests/test_confine.py` fa fallire la CI se la fatturazione importa
il modulo TS. Togliendo una riga da `hooks.py` resta una fatturazione che funziona.

La clinica si fa uguale. Le alternative erano peggiori:

| | Dove sta il codice | Contro |
|---|---|---|
| **A** ✅ | Un modulo dentro l'app `crm`, come la fatturazione | Le tabelle sanitarie esistono (vuote) anche sui siti non medici. Serve disciplina sui confini, che il test garantisce |
| **B** | App separata con la sua SPA, come Helpdesk o LMS | Due SPA, cioè di nuovo la dualità: la segretaria salta fra `/crm` e `/clinica` per lo stesso paziente |
| **C** | App separata per il backend, pagine nella SPA del CRM | Ogni funzione vive in due repo: due PR e due CI da tenere allineate |

L'estrazione resta aperta: **in Frappe la tabella prende il nome dal DocType, non
dall'app** (`tabClinic Visit`), quindi spostare un modulo in un'app a sé è una
patch sulle definizioni, non una migrazione di dati. È quello che ha fatto ERPNext
nella v14 con Healthcare, Education e Agriculture
([guida alla migrazione](https://github.com/frappe/erpnext/wiki/Migration-Guide-to-ERPNext-version-14)).

Le regole:

1. **Un modulo nuovo, `crm/clinica/`:** scheda paziente, cartella (visite,
   referti, archivio), piani, area cliente e assistente. Si registra da
   `hooks.py` come la tessera sanitaria. Il motore dei modelli con la firma e il
   registro dei consensi stanno invece nel CRM (`crm/moduli`), perché servono a
   ogni cliente ([i tre strati](./design.md#tre-strati-crm-fatturazione-clinica)).
2. **Dipendenza a senso unico.** La clinica importa da `crm` e dalla fatturazione;
   né `crm` né la fatturazione importano la clinica. Un `test_confine.py` come
   quello della fatturazione.
3. **Un interruttore per sito, "centro medico".** Accende le voci di menu, i gruppi
   delle impostazioni, i widget (`features.py`) e i job. **Ogni job schedulato del
   modulo esce subito se il sito non è medico**: lo scheduler di ogni sito è ciò
   che decide quanti siti stanno su un server.
4. **Nessun dato clinico fuori dai DocType clinici.** Niente su `CRM Lead`, nelle
   note, nella timeline, nei messaggi WhatsApp o nelle automazioni. La timeline
   della persona può dire "visita del 12/10, referto consegnato", mai cosa c'è
   scritto. La fatturazione fa già lo stesso con i nomi dei PDF, che restano
   neutri.
5. **Nomi.** DocType in inglese con un prefisso proprio (`Clinic Patient`,
   `Clinic Visit`…), come il resto del codice. Le etichette italiane arrivano dalla
   traduzione.

## Decisione 3 — Tutto nella SPA, le impostazioni generate dai DocType

Le giornate tipo vanno nella SPA `/crm`, dove il centro lavora già:

- **Segreteria, dove c'è:** agenda, poi l'accettazione quando il paziente arriva
  (dati controllati, consensi firmati al banco, sala d'attesa), poi la coda
  "Dall'agenda, non ancora fatturati" (che c'è già), poi il prossimo appuntamento.
- **Operatore** (medico, nutrizionista, fisioterapista…): la mia giornata, poi la pagina della persona (storia, allegati,
  consensi), poi la visita sul modello della sua specialità, poi il referto. Nei
  centri con un erogatore solo fa tutto da lì, fattura compresa.
- **Manager amministrativo:** appuntamenti, nuovi pazienti, prodotto per medico, consensi
  mancanti, cosa resta da fatturare.
- **Marketing:** richieste, pipeline, campagne e costo per nuovo paziente.

Le impostazioni della clinica (modelli di cartella, testi dei consensi) vanno nella
modale **Impostazioni**, come ha fatto la fatturazione: schermate generate dal
layout del DocType con `buildTabs` (`frontend/src/utils/settingsTabs.js`),
`DocFields.vue` e `RecordList.vue` (`components/Settings/Invoicing/`). Niente
schermate scritte a mano, e le spiegazioni sotto i campi sono quelle del DocType.

## Decisione 4 — I "tubi" regolati si comprano

Fattura e Sistema TS li avete già, con i canali export, PEC e provider accreditato
(`crm/invoicing/sdi/itala.py`) e le credenziali del centro. Restano la **firma dei referti** e,
quando servirà, il **Fascicolo sanitario**: stesso principio, un adattatore con un
intermediario dietro. Il gestionale produce il documento giusto, l'intermediario lo
firma o lo consegna e restituisce l'esito
([ricerca §3](./ricerca.md#3-i-tubi-regolati-sdi-sistema-ts-firma)).

## Il modello dati, prima versione

```
CRM Lead (la persona, com'è oggi)
  ├─1:1─ CRM Billing Profile (fatturazione) ── codice fiscale, indirizzo;
  │                                           la leggono fattura e clinica
  └─1:1─ Paziente (clinica) ─── nasce da solo alla prima regola che scatta:
            │                    paziente dal, motivo, tutore o genitore
            │                    (un'altra persona), consenso al dossier
            ├── Consenso ×N ─── tipo, versione del testo, firmato il, come, PDF
            ├── Documento ×N ── esami portati dal paziente (file privati)
            └── Visita ×N ───── medico (l'erogatore), dati clinici sul modello
                  │              della specialità, appuntamento se c'è
                  └── Referto ── PDF, firma, consegna

CRM Appointment (l'agenda, com'è oggi)
  ├── Accettazione (clinica, facoltativa) ── arrivo, dati controllati, consensi
  │                                          firmati al banco, sala d'attesa
  └── CRM Invoice (fatturazione, com'è oggi) ── la prima con una riga sanitaria
                                                fa diventare paziente

CRM Deal (com'è oggi): la conversione a paziente chiude come vinto quello aperto
```

Perché così:

- **Il paziente è un DocType a parte, non campi su `CRM Lead`.** Non tutte le
  persone sono pazienti (il lead da Meta che non è mai venuto), i permessi sono
  diversi, e `CRM Lead` è il DocType più letto del core (il solo `mobile_no`
  compare in 201 punti, doc 18): il verticale non deve toccarlo.
- **Il medico è l'erogatore.** `CRM Service Provider` lega già un utente alla sua
  qualifica: la visita punta lì, e non nasce un secondo elenco di medici.
- **La visita appende al paziente**, perché in molti centri l'accettazione non
  c'è. Il medico apre la persona e scrive; se c'era un appuntamento, la visita lo
  trova e lo chiude.
- **L'accettazione resta, facoltativa, e non duplica la fattura.** Registra
  l'arrivo: a che ora, dati controllati, consensi firmati al banco, chi è in sala
  d'attesa. Cosa è stato fatto davvero e chi paga restano sulla fattura, che nasce
  già dall'appuntamento: scriverli due volte sarebbe un doppione.
- **Visita e fattura sono DocType diversi** con permessi diversi: la segreteria
  fattura e non legge la cartella. È quello che chiede il Garante per il dossier
  sanitario: i dati sulla salute separati dagli altri dati personali.
- **Paziente, pagante e chi prenota possono essere tre persone diverse:** il
  bambino, il genitore che paga, la nonna che telefona. Jane li chiama "related
  profiles". È il punto più delicato del modello, perché `find_person` riconosce
  una persona da email e telefono, e in una famiglia li condividono. Deciso il
  29/09/2026: il contatto trova il titolare, il nome la persona
  ([le persone collegate](#le-persone-collegate)).
- **Una lista di regole, una porta sola.** Le sei regole stanno in un file solo
  (per esempio `crm/clinica/diventa_paziente.py`), nell'ordine della tabella, e
  chiamano tutte la stessa funzione (`ensure_patient(persona, regola, origine)`),
  la cui prima riga è "è già paziente? esci". Le chiamano: la classe base di tutti
  i DocType clinici al primo inserimento (così un DocType clinico nuovo è coperto
  senza ricordarsene, e un test controlla che tutti ereditino da lì), i
  `doc_events` di accettazione, appuntamento (`Completed` o `Attended`) e fattura
  (`on_submit` con una riga `is_healthcare`), l'importazione e il bottone "Segna
  come paziente". Un vincolo di unicità sulla persona impedisce due schede paziente
  anche se due regole scattano insieme. Il recupero all'indietro usa la stessa
  lista, e la scelta della regola che vince è una funzione pura, testata con
  `unittest` come `crm/scheduling/booking_rules.py`. L'evento "Diventato paziente"
  si aggiunge a `EVENT_TO_TRIGGER` in `crm/automation/engine.py`.

Le scelte Frappe che contano:

- **Submittable** tutto ciò che, una volta chiuso, non si riscrive: visita
  firmata, referto, consenso. La correzione è *annulla e modifica*, e Frappe tiene
  le due versioni collegate. È quello che serve a una cartella clinica, che si
  integra ma non si riscrive, ed è già il modo in cui funziona `CRM Invoice`.
- **Registro degli accessi.** Con `track_views` sul DocType Frappe scrive un View
  Log per ogni apertura, **ma solo dal form del Desk**
  (`frappe.desk.form.load.getdoc` chiama `doc.add_viewed()`). La SPA carica i
  documenti con `createDocumentResource`, cioè `frappe.client.get`, che non scrive
  niente. Quindi i documenti clinici nella SPA si leggono da un'API dedicata che
  chiama `add_viewed()` da sé. Il Garante vuole i log degli accessi al dossier
  conservati almeno 24 mesi: il View Log non è fra i log che Frappe pulisce da
  solo, ma si può aggiungere a Log Settings (e il suo default è 180 giorni), quindi
  va protetto.
- **Permessi per record** con `permission_query_conditions` e `has_permission`,
  come fa già `crm/permissions/org_hierarchy.py` per lead e trattative. La visita
  la vedono il medico che l'ha fatta e la direzione sanitaria; gli altri medici
  solo se il paziente ha dato il consenso al dossier e quell'evento non è oscurato.
- **File privati** per referti e allegati: Frappe li serve solo a chi può leggere
  il documento a cui sono attaccati.
- **Un modello di cartella per specialità, non un DocType per specialità.** Il
  modello è un layout (sezioni e campi) salvato su un record e disegnato da
  `FieldLayout` in modalità standalone, lo stesso che usano `formDialog()` e le
  impostazioni della fatturazione. Nuova specialità vuol dire nuovo record, nessun
  deploy. I valori stanno in un campo JSON della visita; le poche cose che servono
  alle statistiche (diagnosi, parametri vitali) sono colonne vere.
- **Print format Jinja e carta intestata per studio** per referto e consenso, come
  la fattura.

## Le fasi

Stime in settimane-persona (sp) per un senior Frappe, come in
[08](../progetto-ghl/08-roadmap.md). Il collo di bottiglia non sarà il codice ma la
prova con il centro pilota.

| Fase | Cosa | sp | Da qui il centro pilota può… |
|---|---|---|---|
| **0 — Le due facce e il paziente automatico** | Interruttore "centro medico"; i tre livelli come Role Profile, con la gestione dei ruoli nel CRM e System Manager solo all'agenzia; menu e schede per livello e la forma dedotta dagli erogatori; Sito nascosto senza Builder; lettura delle fatture tolta a Sales User, anche nella cronologia della persona; l'anagrafica fiscale sola, letta dalla fattura; la sezione "Clinica" sulla pagina della persona, con una visita semplice (testo e allegati); la lista delle regole e la porta unica (informazione medica, appuntamento, fattura, importazione, a mano), con il recupero una tantum sui dati che ci sono già; consensi registrati, compreso quello di `/prenota`; persone collegate (genitore e figlio) | 4,5–6 | …lavorare dalla pagina della persona, medico compreso, senza riscrivere il codice fiscale |
| **1 — Le cuciture** | La conversione a paziente che chiude il deal; pipeline "Nuovi pazienti" e "Preventivi"; l'evento "Diventato paziente" nelle automazioni; l'accettazione con la sala d'attesa, per chi ha la segreteria, che entra nella lista delle regole; visita, accettazione e fattura che chiudono l'appuntamento; il promemoria di fine giornata "sono venuti?"; richiami ai pazienti con consenso; dashboard del centro | 2–3 | …sapere quanto costa un nuovo paziente, per inserzione |
| **2 — Cartella, moduli e referti** | Cartella completa sul modello della specialità; il builder dei moduli del centro con la firma come componente (privacy, consensi, anamnesi) e il registro dei consensi; firma semplice nostra e avanzata con un fornitore, per i consensi informati ([design](./design.md#la-firma)); referto in PDF/A con firma; archivio clinico dei documenti; registro degli accessi; dossier e oscuramento; consegna del referto | 8–10 | …spegnere il vecchio gestionale |
| **3 — Area cliente ed extra** | Area cliente: appuntamenti, piani (nutrizionale, dieta, allenamento), documenti, comunicazioni dell'operatore, fatture, moduli da firmare (6–8 sp, [requisiti §6](./requisiti.md#6-area-cliente)); televisita; magazzino dei consumabili; cicli di sedute (fisioterapia); piani di cura (odontoiatria) | a scelta | …vendere il pacchetto completo |
| **Da tenere d'occhio** | Fascicolo sanitario 2.0: dal 31/03/2026 riguarda sulla carta anche le prestazioni private, ma per le strutture non accreditate l'obbligo è contestato e non sanzionato. Quando lo diventerà servono referti in CDA2, firma qualificata e un software accreditato dal Ministero ([ricerca §2.7](./ricerca.md#27-fascicolo-sanitario-elettronico-fse-20)) | — | — |
| **E poi** | AI Act: trasparenza dal 2 agosto 2026, dispositivi medici con IA dal 2 agosto 2028; spazio europeo dei dati sanitari (EHDS): formati comuni dal 2027, marchio CE autodichiarato per le cartelle in cloud dal 2031 ([design](./design.md#le-norme-e-il-calendario)) | — | — |

**Fasi 0–2: 15–19 sp, tre-quattro mesi per una persona.** Le prime due
risolvono la dualità; la terza è il gestionale clinico vero e proprio. Le stime
sono indicative e si rifanno dopo le decisioni in [requisiti.md](./requisiti.md).

## Le domande da chiudere prima

1. **Chi fa il marketing per il centro?** Voi come agenzia, qualcuno del centro, o
   entrambi? Decide i ruoli e chi vede cosa: i vostri utenti sui siti dei clienti
   non devono vedere dati clinici né fatture.
2. **Che centri sono i primi clienti?** Il poliambulatorio "visite e referti" è il
   caso semplice. Odontoiatria (odontogramma, preventivi, piani di cura),
   fisioterapia (cicli di sedute) e medicina del lavoro (aziende clienti,
   protocolli, giudizi di idoneità) sono mondi a sé. Proposta: solo privati;
   l'accreditamento con il Servizio sanitario (ricetta dematerializzata, flussi
   regionali, CUP) è un altro progetto.
3. **I medici condividono la cartella?** Se sì è un dossier sanitario (consenso
   specifico, oscuramento, registro degli accessi); se no ognuno vede solo i suoi
   pazienti. La regola la decide il direttore sanitario.
4. **Il pilota sostituisce il gestionale di oggi o lo affianca per un periodo?**
   Decide quanto pesa l'importazione: anagrafiche, appuntamenti futuri, cartelle.

## Cosa non fare

- **Due anagrafiche**, una per il CRM e una per il centro. La persona è una sola;
  il paziente è una scheda in più, non una persona in più.
- **Un secondo elenco di medici.** I medici sono gli erogatori della fatturazione.
- **Installare Marley Health o ERPNext "per avere tutto".** Sarebbe proprio la
  seconda anagrafica, con una seconda agenda e un'interfaccia che i medici non
  useranno.
- **Mettere campi clinici su `CRM Lead`.** Li vedrebbe chiunque veda le persone,
  compreso chi fa marketing, compresi i vostri utenti d'agenzia sui siti dei
  clienti.
- **Scegliere i destinatari di una campagna su dati clinici**, righe di fattura
  comprese.
- **Un DocType per specialità.** Diventano venti, tutti da migrare a ogni modifica.
- **Rincorrere GipoNext o AlfaDocs funzione per funzione.** Si parte da quello che
  il pilota fa dieci volte al giorno.

## Voi come fornitore

Ospitando cartelle cliniche diventate **responsabili del trattamento** di dati
sanitari per ogni centro (art. 28 GDPR). Servono una nomina per cliente, una
valutazione d'impatto (DPIA) per il modulo clinico, backup cifrati e dati in UE
(Hetzner in Germania va bene). E un punto che si dimentica: **i vostri utenti
d'agenzia sui siti dei clienti non devono avere ruoli clinici**, né leggere le
fatture.

Un software per agenda, fatture e cartella al posto della carta non è un
dispositivo medico. Lo diventa se suggerisce dosaggi o segnala interazioni fra
farmaci (linee guida MDCG 2019-11, rev. giugno 2025): quelle funzioni restano
fuori. Più avanti c'è lo Spazio europeo dei dati sanitari (regolamento UE
2025/327): i sistemi di cartella elettronica dovranno autocertificarsi e avere la
marcatura CE, con date fra il 2027 e il 2031. Prima di vendere il modulo clinico
come prodotto va sentito un legale ([ricerca §2.6](./ricerca.md#26-dispositivo-medico-e-spazio-europeo-dei-dati-sanitari)).

## Come si parte davvero

1. Un giorno nel centro pilota, accanto a chi apre la scheda del paziente
   (segreteria o medico): cosa fanno con il gestionale di oggi, in che ordine,
   quante volte al giorno, e chi risponde a quale messaggio.
2. Le domande qui sopra, chiuse con il committente.
3. Fase 0.
