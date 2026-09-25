# Il gestionale per i centri medici: come farlo stare in Frappe

**Stato:** 📐 proposta (25/09/2026), rivista dopo l'arrivo della fatturazione in
`develop`. Fattura elettronica e Sistema TS ci sono già (`crm/invoicing` e
`crm/tessera_sanitaria`, [guida](../../.pi/feats/fatturazione/guida.md)): questa
proposta ci si appoggia e non li tocca, se non nei punti detti sotto. Prima di
scrivere codice vanno chiuse le [domande](#le-domande-da-chiudere-prima) in fondo.
Obblighi, concorrenti ed ecosistema Frappe, con le fonti, sono in
[ricerca.md](./ricerca.md).

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
  CONTATTO  ───────────── prima visita ─────────────►  PAZIENTE
  da conquistare         il primo segno che             da curare
  lo segue il marketing  è venuto davvero               lo segue il centro,
  con i deal                                            con agenda e visite
```

- Il passaggio è **la prima visita**, non la prenotazione: chi prenota e non si
  presenta resta un contatto.
- È automatico: nessuno deve ricordarsi di "convertire" qualcuno.
- La persona non cambia scheda. Le si aggiunge la **scheda paziente** (consensi,
  tutore, dossier) e da quel momento compare fra i **Pazienti**.

Saperlo serve davvero: cartella e documenti clinici vanno conservati anche se la
persona chiede di essere cancellata, il medico vede i pazienti e il marketing no, e
"nuovi pazienti al mese" è il numero che il centro guarda.

### Come si diventa paziente: da soli, qualunque sia il modo di lavorare

Ogni centro lavora a modo suo: c'è quello con la segreteria che accoglie, quello
dove c'è solo il medico che apre la scheda della persona e comincia a scrivere,
quello che segna tutto in agenda e quello che fa solo le fatture. Quindi **ci sono
tutte le strade**, nessuna esclude le altre e nessuna è obbligatoria. La persona
diventa paziente al **primo segno che è venuta**, qualunque arrivi prima:

| Come lavora il centro | Il segno | Gesto in più richiesto |
|---|---|---|
| Solo il medico, che apre la scheda e scrive | Il medico salva la prima visita o nota clinica | nessuno: scrivere è già il gesto |
| Segreteria che accoglie | L'accettazione: l'arrivo registrato al banco | nessuno: è il suo lavoro |
| Agenda usata con gli stati | L'appuntamento segnato come svolto (`Completed`, o il partecipante `Attended`) | nessuno |
| Chi fa le fatture | La prima `CRM Invoice` confermata alla persona con una riga sanitaria (`is_healthcare` sulla riga, copiato dalla scheda del servizio: la copia funziona dalla PR #102, prima il flag restava sempre a 0) | nessuno: la fattura è obbligatoria comunque |
| Passaggio dal vecchio gestionale | L'importazione dei pazienti | nessuno |
| Un caso che nessuna regola vede | A mano: "Segna come paziente" sulla pagina della persona | un clic, solo quando serve |

La fattura è il segno più affidabile di tutti: è obbligatoria, la fa una persona,
e la fatturazione la fa già nascere dall'appuntamento. Una fattura non sanitaria
(un corso, un abbonamento) non rende nessuno paziente.

**Sei strade, una porta.** Tutte chiamano la stessa funzione, che non fa danni se
chiamata due volte: la prima strada che arriva crea la scheda paziente, le altre
trovano la porta già aperta e non fanno niente. La funzione scrive "paziente dal
12/10/2026, prima fattura", chiude come vinto il deal aperto della pipeline "Nuovi
pazienti" e lancia un evento "Diventato paziente" per le automazioni (benvenuto,
richiesta di recensione dopo una settimana…).

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

1. **Dal marketing al centro: la prima visita chiude il deal.** La pipeline "Nuovi
   pazienti" va da richiesta a contattato, ad appuntamento fissato, a venuto
   (vinto) o perso. La prenotazione sposta il deal su "appuntamento fissato", il
   primo segno di presenza su "venuto". Così il report delle inserzioni Meta, che
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
| Persona | `CRM Lead` è la persona, con un solo `Contact` ([18](../progetto-ghl/18-persona-unica.md), [21](../progetto-ghl/21-lead-contatto-trattativa.md)): nome, sesso, email, cellulare | La scheda paziente (consensi, tutore o genitore per i minori, dossier). Sulla persona **non c'è nessun indirizzo** e nessun codice fiscale |
| Agenda | Un motore solo: servizi, professionisti, stanze, attrezzature, listini condizionati, `/prenota`, piattaforme esterne, automazioni sugli stati. `Completed` e `Attended` si segnano a mano dal dialogo dell'appuntamento | L'accettazione per chi ha la segreteria; la visita, l'accettazione e la fattura che chiudono da sole l'appuntamento |
| Fatturazione | `CRM Invoice` nasce dall'appuntamento (la coda "Dall'agenda, non ancora fatturati", `issue_from_appointment`); i medici sono gli erogatori (`CRM Service Provider`, con utente e qualifica); il canale lo decide la classificazione; Sistema TS con le credenziali del centro | **Il codice fiscale e l'indirizzo non si ricordano.** `compila_da_controparte` prende dalla persona solo nome e cognome, quindi al paziente che torna si riscrivono ogni volta. Vedi [l'anagrafica fiscale](#unanagrafica-fiscale-sola) |
| Privacy | La spunta privacy di `/prenota` viene controllata (`crm/api/service_booking.py:565`) **ma non registrata**. L'hook `user_data_fields` è commentato. Sulla fattura c'è già l'opposizione all'invio TS, documento per documento | Consensi registrati (quale testo, quale versione, quando, come): marketing, dossier, referti online |
| Clinica | Niente | Cartella per specialità, referti, consensi informati, allegati, registro degli accessi |
| Ruoli | System Manager, Sales Manager, Sales User; Invoicing Manager e Invoicing User. Ogni utente vede tutti gli appuntamenti. **Sales User legge tutte le fatture** (permesso di lettura ed export su `CRM Invoice`) | Medico, Direzione sanitaria, Marketing. Il marketing non deve leggere le fatture: una riga "seduta di psicoterapia" è un dato sanitario |
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

1. **Un modulo nuovo, `crm/clinica/`:** scheda paziente, consensi, visite, referti
   e modelli di cartella. Si registra da `hooks.py` come la tessera sanitaria.
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
- **Medico:** la mia giornata, poi la pagina della persona (storia, allegati,
  consensi), poi la visita sul modello della sua specialità, poi il referto. Nei
  centri con un erogatore solo fa tutto da lì, fattura compresa.
- **Direzione:** appuntamenti, nuovi pazienti, prodotto per medico, consensi
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
  ├─1:1─ anagrafica fiscale (fatturazione) ── codice fiscale, indirizzo;
  │                                           la leggono fattura e clinica
  └─1:1─ Paziente (clinica) ─── nasce da solo al primo segno di presenza:
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

CRM Deal (com'è oggi): il primo segno di presenza chiude come vinto quello aperto
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
  profiles". È il punto più delicato del modello, perché oggi `find_person`
  riconosce una persona da email e telefono, e in una famiglia li condividono. Si
  decide in fase 0.
- **Una porta sola per diventare paziente.** Una funzione che non fa danni se
  chiamata due volte (`ensure_patient(persona, motivo)`), chiamata dai
  `doc_events` di visita, accettazione, appuntamento (`Completed` o `Attended`) e
  fattura (`on_submit` con una riga `is_healthcare`), dall'importazione e dal
  bottone "Segna come paziente". Un vincolo di unicità sulla persona impedisce due
  schede paziente anche se due eventi arrivano insieme. L'evento "Diventato paziente" si aggiunge a `EVENT_TO_TRIGGER` in
  `crm/automation/engine.py`.

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
| **0 — Le due facce e il paziente automatico** | Interruttore "centro medico"; ruoli Medico, Direzione sanitaria, Marketing, con menu e schede per ruolo e la forma dedotta dagli erogatori; lettura delle fatture tolta a Sales User; l'anagrafica fiscale sola, letta dalla fattura; la sezione "Clinica" sulla pagina della persona, con una visita semplice (testo e allegati); la porta unica, con tutte le strade (visita, appuntamento, fattura, importazione, a mano); consensi registrati, compreso quello di `/prenota`; persone collegate (genitore e figlio) | 3–4 | …lavorare dalla pagina della persona, medico compreso, senza riscrivere il codice fiscale |
| **1 — Le cuciture** | Il primo segno di presenza che chiude il deal; pipeline "Nuovi pazienti" e "Preventivi"; l'evento "Diventato paziente" nelle automazioni; l'accettazione con la sala d'attesa, per chi ha la segreteria; visita, accettazione e fattura che chiudono l'appuntamento; il promemoria di fine giornata "sono venuti?"; richiami ai pazienti con consenso; dashboard del centro | 2–3 | …sapere quanto costa un nuovo paziente, per inserzione |
| **2 — Cartella e referti** | Modelli per specialità; referto in PDF con firma (prima semplice su tablet, poi avanzata); consensi informati per prestazione; registro degli accessi; dossier e oscuramento; consegna del referto | 4–5 | …spegnere il vecchio gestionale |
| **3 — Paziente ed extra** | Area paziente (referti, fatture, questionario prima della visita); televisita; magazzino dei consumabili; cicli di sedute (fisioterapia); piani di cura (odontoiatria) | a scelta | …vendere il pacchetto completo |
| **Da tenere d'occhio** | Fascicolo sanitario 2.0: dal 31/03/2026 riguarda sulla carta anche le prestazioni private, ma per le strutture non accreditate l'obbligo è contestato e non sanzionato. Quando lo diventerà servono referti in CDA2, firma qualificata e un software accreditato dal Ministero ([ricerca §2.7](./ricerca.md#27-fascicolo-sanitario-elettronico-fse-20)) | — | — |

**Fasi 0–2: 9–12 sp, circa due mesi e mezzo per una persona.** Le prime due
risolvono la dualità; la terza è il gestionale clinico vero e proprio.

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
