# Il gestionale per i centri medici: come farlo stare in Frappe

**Stato:** 📐 proposta (25/09/2026, rivista lo stesso giorno). La fatturazione, e
con lei l'invio al Sistema TS, c'è già ed è fuori da questa proposta. Prima di
scrivere codice vanno chiuse le [cinque domande](#le-cinque-domande-da-chiudere-prima)
in fondo. Obblighi, concorrenti ed ecosistema Frappe, con le fonti, sono in
[ricerca.md](./ricerca.md).

## Il problema in una riga

Il CRM oggi fa molto bene il **prima** della visita: trova la persona, la fa
prenotare (dal sito, da MioDottore, al telefono), le ricorda l'appuntamento, dice
quanto è costato acquisirla. Un gestionale medico è soprattutto il **durante** e il
**dopo**: accettazione, visita, cartella, referto, richiami.

CRM e centro medico hanno in comune due cose sole, **la persona e l'agenda**. La
difficoltà non è Frappe: è decidere dove passa il confine, chi vede cosa e come i
due mondi si passano la persona. Questo documento lo decide.

## La dualità: una persona, due mestieri

Non sono due sistemi e non sono due anagrafiche. È **una persona sola** che
attraversa due fasi, e **due mestieri** che lavorano su di lei.

### Le due fasi della persona

```
  CONTATTO  ───────────── prima visita ─────────────►  PAZIENTE
  da conquistare         la segreteria segna            da curare
  lo segue il marketing  "arrivato"                     lo segue il centro,
  con i deal                                            con agenda e visite
```

- Il passaggio è **la prima visita**, non la prenotazione: chi prenota e non si
  presenta resta un contatto.
- È automatico: nessuno deve ricordarsi di "convertire" qualcuno.
- La persona non cambia scheda. Le si aggiunge la **scheda paziente** (codice
  fiscale, nascita, consensi) e da quel momento compare fra i **Pazienti**.

Saperlo serve davvero: cartella e documenti clinici vanno conservati anche se la
persona chiede di essere cancellata, il medico vede i pazienti e il marketing no, e
"nuovi pazienti al mese" è il numero che il centro guarda.

### Due mestieri, due facce dello stesso CRM

Stesso sito, stessa persona: menu, schede e numeri cambiano con il ruolo.

| | Marketing (voi, o chi fa commerciale nel centro) | Centro (segreteria, medici, direzione) |
|---|---|---|
| Menu | Persone, Richieste (i deal), Automazioni, Meta, Social, Sito | Agenda, Pazienti, Conversazioni |
| Scheda della persona | da dove arriva, deal, campagne, conversazioni | appuntamenti, visite, documenti, consensi, conversazioni |
| Dashboard | richieste, costo per nuovo paziente per inserzione | appuntamenti di oggi, no-show, occupazione, nuovi pazienti |
| Non vede | visite, referti, dati clinici | — |

Nel codice il meccanismo c'è già: le voci del menu (`AppSidebar.vue`) e le schede
della persona (`frontend/src/pages/Lead.vue`) hanno una `condition` ciascuna, oggi
usata solo per "è manager". Mancano i ruoli: oggi esistono solo Sales User e Sales
Manager.

**I nomi si cambiano per sito, senza codice.** Frappe aggiunge alle traduzioni
delle app quelle del DocType `Translation` del sito (`get_all_translations`), e la
SPA le riceve da `crm.api.get_translations`. Sul sito di un centro "Deals" può
leggersi "Richieste" senza toccare gli altri clienti.

### Le tre cuciture fra i due mondi

Separare non basta: la dualità si gestisce nei tre punti in cui un mondo passa la
persona all'altro.

1. **Dal marketing al centro: la prima visita chiude il deal.** La pipeline "Nuovi
   pazienti" va da richiesta a contattato, ad appuntamento fissato, a venuto
   (vinto) o perso. La prenotazione sposta il deal su "appuntamento fissato", la
   prima visita su "venuto". Così il report delle inserzioni Meta, che conta i deal
   vinti (`cost_per_won` in `crm/integrations/meta/insights.py`), dice quanto costa
   un nuovo paziente, senza lavoro in più per la segreteria. Con le automazioni di
   oggi non si fa: i trigger degli appuntamenti lavorano sulla persona, non sul
   deal (`resolve_reference` in `crm/automation/engine.py`). Serve un piccolo
   aggancio nel codice.
2. **Dal centro al marketing: il richiamo.** Pazienti che non vengono da un anno,
   controlli da ripetere, recensioni. Solo con il consenso al marketing, e
   scegliendo i destinatari su dati amministrativi (ultima visita, servizio
   prenotato), **mai su dati clinici** (diagnosi, referti). Il marketing vede "non
   viene da 14 mesi", non il perché.
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
| Persona | `CRM Lead` è la persona, con un solo `Contact` ([18](../progetto-ghl/18-persona-unica.md), [21](../progetto-ghl/21-lead-contatto-trattativa.md)): nome, sesso, email, cellulare | La scheda paziente: codice fiscale, nascita, residenza (sulla persona **non c'è nessun indirizzo**), tessera sanitaria, genitore o tutore per i minori |
| Privacy | La spunta privacy di `/prenota` viene controllata (`crm/api/service_booking.py:565`) **ma non registrata**. L'hook `user_data_fields` è commentato | Consensi registrati (quale testo, quale versione, quando, come): marketing, dossier, referti online |
| Agenda | Un motore solo: servizi, professionisti, stanze, attrezzature, listini condizionati, `/prenota`, piattaforme esterne, automazioni sugli stati | Lo stato "arrivato", l'accettazione, le prestazioni *eseguite* (spesso diverse dalle prenotate) |
| Fatturazione | C'è già, fuori da questo progetto | Riceve dall'accettazione le prestazioni eseguite |
| Clinica | Niente | Cartella per specialità, referti, consensi informati, allegati, registro degli accessi |
| Ruoli | System Manager, Sales Manager, Sales User. Ogni utente vede tutti gli appuntamenti | Segreteria, Medico, Direzione sanitaria, Marketing, con menu e schede per ruolo |
| Moduli | Nessun interruttore per modulo: `crm/dashboard/features.py` rileva cosa usa il sito, ma serve solo alla dashboard | Un interruttore "centro medico" che accende menu, pagine, impostazioni, widget e job |

Il resto (conversazioni su tutti i canali, automazioni, prenotazione online,
telefono, dashboard, sito) è più avanti di quello che offrono i gestionali medici
italiani, che su questa parte sono deboli. **È il vantaggio da difendere: non va
rifatto, va collegato.**

## Decisione 1 — Niente Marley Health e niente ERPNext, per ora

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
3. **Non sa niente dell'Italia** (Sistema TS, esenzione IVA sanitaria, bollo,
   divieto SDI per le fatture ai pazienti), e il medico dovrebbe lavorare nel Desk.

Da Marley si prende **il modello dati come riferimento** (come separa appuntamento,
incontro clinico, procedura e referto) e, dove serve, singoli pezzi di codice: la
GPL-3 si combina con la vostra AGPL-3. L'app intera no.

Se la vostra fatturazione passa da ERPNext, una trappola da conoscere: il core
genera da solo l'XML della fattura elettronica a ogni fattura di una società
italiana (`erpnext/regional/italy`), e per le fatture ai pazienti va spento, perché
non devono mai andare allo SDI ([ricerca §1.3](./ricerca.md#13-erpnext-e-la-fattura-elettronica-italiana)).

## Decisione 2 — Un verticale dentro `crm`, con le regole di un'app separata

| | Dove sta il codice | Pro | Contro |
|---|---|---|---|
| **A** | Un modulo Frappe nuovo dentro l'app `crm` | Un repo, una SPA, una PR per funzione. Sono fatti così anche agenda, automazioni, dashboard e piattaforme | Le tabelle sanitarie esistono (vuote) anche sui siti non medici. Serve disciplina sui confini |
| **B** | App separata con la sua SPA, come Helpdesk o LMS | Isolamento totale | Due SPA, cioè di nuovo la dualità: la segretaria salta fra `/crm` e `/clinica` per lo stesso paziente |
| **C** | App separata per il backend, pagine nella SPA del CRM | Tabelle solo sui siti medici | Ogni funzione vive in due repo: due PR e due CI da tenere allineate |

**Proposta: A, con le regole di B.**

Il motivo classico per stare in un'app separata è poter continuare a tirare da
`frappe/crm`. Non vale più: agenda, piattaforme, automazioni, dashboard, telefonia e
sito sono già dentro `crm/` (circa 80 mila righe Python e 78 mila Vue, 106 DocType).

Vale invece il motivo per cui ERPNext, nella v14, ha estratto Healthcare, Education,
Agriculture, Non Profit e HR in app proprie
([guida alla migrazione](https://github.com/frappe/erpnext/wiki/Migration-Guide-to-ERPNext-version-14)):
un verticale dentro il prodotto base finisce per sporcarlo. Le regole qui sotto
servono a evitarlo e a tenere aperta l'estrazione. **In Frappe la tabella prende il
nome dal DocType, non dall'app** (`tabClinic Visit`), quindi spostare un modulo in
un'app a sé è una patch sulle definizioni, non una migrazione di dati. È quello che
ha fatto ERPNext: chi usava Healthcare ha installato la nuova app e ha ritrovato i
suoi dati.

Le regole:

1. **Un modulo Frappe nuovo, `Clinica`:** paziente, consensi, accettazione,
   visite, referti e modelli di cartella. Cartella `crm/clinica/`, voce in
   `modules.txt`.
2. **Dipendenza a senso unico.** Il modulo importa da `crm`, il resto di `crm` non
   importa mai da lui. Si aggancia con `doc_events` in `hooks.py` e con i punti di
   estensione che esistono già: trigger delle automazioni, widget e feature della
   dashboard. Un test che scorre gli import fa rispettare la regola.
3. **Un interruttore per sito, "centro medico".** Accende le voci di menu, i gruppi
   delle impostazioni (`Settings.vue` ha la stessa `condition` del menu), i widget
   (`features.py`) e i job. **Ogni job schedulato del modulo esce subito se il sito
   non è medico**: lo scheduler di ogni sito è ciò che decide quanti siti stanno su
   un server.
4. **Nessun dato clinico fuori dai DocType clinici.** Niente su `CRM Lead`, nelle
   note, nella timeline, nei messaggi WhatsApp o nelle automazioni. La timeline
   della persona può dire "visita del 12/10, referto consegnato", mai cosa c'è
   scritto.
5. **Nomi.** DocType in inglese con un prefisso proprio (`Clinic Patient`,
   `Clinic Visit`…), come il resto del codice. Le etichette italiane arrivano dalla
   traduzione.

## Decisione 3 — La SPA per chi lavora, il Desk per chi configura

Le giornate tipo vanno nella SPA `/crm`, dove il centro lavora già:

- **Segreteria:** agenda, poi "arrivato", poi accettazione (e la fattura, con
  quello che usate già), poi il prossimo appuntamento.
- **Medico:** la mia giornata, poi la scheda del paziente (storia, allegati,
  consensi), poi la visita sul modello della sua specialità, poi il referto.
- **Direzione:** appuntamenti, nuovi pazienti, prodotto per medico, consensi
  mancanti.
- **Marketing:** richieste, pipeline, campagne e costo per nuovo paziente.

La configurazione all'inizio sta nel **Desk** (`/app`): modelli di cartella, testi
dei consensi, ruoli. Frappe genera quelle schermate dai DocType, gratis, e le usate
voi per configurare il cliente. Nella SPA si porta solo ciò che il centro tocca
davvero ogni settimana.

## Decisione 4 — I "tubi" regolati si comprano

Fattura e Sistema TS li avete già. Restano la **firma dei referti** e, quando
servirà, il **Fascicolo sanitario**: stesso principio, un adattatore con un
intermediario dietro, come i connettori di `crm/booking_platforms/`. Il gestionale
produce il documento giusto, l'intermediario lo firma o lo consegna e restituisce
l'esito ([ricerca §3](./ricerca.md#3-i-tubi-regolati-sdi-sistema-ts-firma)).

## Il modello dati, prima versione

```
CRM Lead (la persona, com'è oggi)
  └─1:1─ Paziente ─── nasce alla prima visita: codice fiscale, nascita, residenza,
            │          tessera sanitaria, tutore o pagante (un'altra persona),
            │          consenso al dossier
            ├── Consenso ×N ─── tipo, versione del testo, firmato il, come, PDF
            └── Documento ×N ── esami portati dal paziente (file privati)

CRM Appointment (l'agenda, com'è oggi)
  └─1:N─ Accettazione ─── chi è arrivato, prestazioni eseguite, medico, chi paga
            ├── Visita ──────── dati clinici sul modello della specialità
            │     └── Referto ── PDF, firma, consegna
            └──► la fatturazione che usate già: le prestazioni eseguite ne sono le righe

CRM Deal (com'è oggi): la prima accettazione chiude come vinto quello aperto
```

Perché così:

- **Il paziente è un DocType a parte, non campi su `CRM Lead`.** Non tutte le
  persone sono pazienti (il lead da Meta che non è mai venuto), i permessi sono
  diversi, e `CRM Lead` è il DocType più letto del core (il solo `mobile_no`
  compare in 201 punti, doc 18): il verticale non deve toccarlo.
- **L'accettazione separa l'agenda dalla fattura.** `CRM Appointment` resta agenda
  e basta. L'accettazione registra cosa è stato fatto davvero, vale anche senza
  appuntamento (chi entra senza prenotare), e in un appuntamento di gruppo ce n'è
  una per partecipante.
- **Visita e accettazione sono due DocType** perché la segreteria deve vedere
  l'una e non l'altra. Un permesso per DocType è più semplice e più sicuro di un
  permesso per campo, ed è quello che chiede il Garante per il dossier sanitario:
  i dati sulla salute separati dagli altri dati personali.
- **Paziente, pagante e chi prenota possono essere tre persone diverse:** il
  bambino, il genitore che paga, la nonna che telefona. Jane li chiama "related
  profiles". È il punto più delicato del modello, perché oggi `find_person`
  riconosce una persona da email e telefono, e in una famiglia li condividono. Si
  decide in fase 0.

Le scelte Frappe che contano:

- **Submittable** tutto ciò che, una volta chiuso, non si riscrive: visita
  firmata, referto, consenso. La correzione è *annulla e modifica*, e Frappe tiene
  le due versioni collegate. È esattamente quello che serve a una cartella
  clinica, che si integra ma non si riscrive.
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
  `FieldLayout` in modalità standalone, lo stesso che usa `formDialog()`. Nuova
  specialità vuol dire nuovo record, nessun deploy. I valori stanno in un campo
  JSON della visita; le poche cose che servono alle statistiche (diagnosi,
  parametri vitali) sono colonne vere.
- **Print format Jinja e carta intestata per studio** per referto e consenso.

## Le fasi

Stime in settimane-persona (sp) per un senior Frappe, come in
[08](../progetto-ghl/08-roadmap.md). Il collo di bottiglia non sarà il codice ma la
prova con il centro pilota.

| Fase | Cosa | sp | Da qui il centro pilota può… |
|---|---|---|---|
| **0 — Le due facce** | Interruttore "centro medico"; ruoli Segreteria, Medico, Direzione sanitaria, Marketing, con menu e schede per ruolo; scheda paziente creata alla prima visita, con codice fiscale validato; consensi registrati, compreso quello di `/prenota`; persone collegate (genitore e figlio) | 2–3 | …importare i pazienti e dare a ognuno la sua vista |
| **1 — Le cuciture** | Da "arrivato" all'accettazione, con le prestazioni eseguite passate alla fatturazione; pipeline "Nuovi pazienti" e "Preventivi"; la prima visita che chiude il deal; richiami ai pazienti con consenso; dashboard del centro | 2–3 | …sapere quanto costa un nuovo paziente, per inserzione |
| **2 — Cartella e referti** | Modelli per specialità; visita; referto in PDF con firma (prima semplice su tablet, poi avanzata); consensi informati per prestazione; allegati; registro degli accessi; dossier e oscuramento; consegna del referto | 5–6 | …spegnere il vecchio gestionale |
| **3 — Paziente ed extra** | Area paziente (referti, questionario prima della visita); televisita; magazzino dei consumabili; cicli di sedute (fisioterapia); piani di cura (odontoiatria) | a scelta | …vendere il pacchetto completo |
| **Da tenere d'occhio** | Fascicolo sanitario 2.0: dal 31/03/2026 riguarda sulla carta anche le prestazioni private, ma per le strutture non accreditate l'obbligo è contestato e non sanzionato. Quando lo diventerà servono referti in CDA2, firma qualificata e un software accreditato dal Ministero ([ricerca §2.7](./ricerca.md#27-fascicolo-sanitario-elettronico-fse-20)) | — | — |

**Fasi 0–2: 9–12 sp, due mesi e mezzo circa per una persona.** Le prime due
risolvono la dualità; la terza è il gestionale clinico vero e proprio.

## Le cinque domande da chiudere prima

1. **Chi fa il marketing per il centro?** Voi come agenzia, qualcuno del centro, o
   entrambi? Decide i ruoli e chi vede cosa: i vostri utenti sui siti dei clienti
   non devono vedere dati clinici.
2. **Dove fate la fatturazione oggi?** In un altro programma o dentro Frappe?
   Decide come l'accettazione le passa le prestazioni eseguite.
3. **Che centri sono i primi clienti?** Il poliambulatorio "visite e referti" è il
   caso semplice. Odontoiatria (odontogramma, preventivi, piani di cura),
   fisioterapia (cicli di sedute) e medicina del lavoro (aziende clienti,
   protocolli, giudizi di idoneità) sono mondi a sé. Proposta: solo privati;
   l'accreditamento con il Servizio sanitario (ricetta dematerializzata, flussi
   regionali, CUP) è un altro progetto.
4. **I medici condividono la cartella?** Se sì è un dossier sanitario (consenso
   specifico, oscuramento, registro degli accessi); se no ognuno vede solo i suoi
   pazienti. La regola la decide il direttore sanitario.
5. **Il pilota sostituisce il gestionale di oggi o lo affianca per un periodo?**
   Decide quanto pesa l'importazione: anagrafiche, appuntamenti futuri, cartelle.

## Cosa non fare

- **Due anagrafiche**, una per il CRM e una per il centro. La persona è una sola;
  il paziente è una scheda in più, non una persona in più.
- **Installare Marley Health o ERPNext "per avere tutto".** Sarebbe proprio la
  seconda anagrafica, con una seconda agenda e un'interfaccia che i medici non
  useranno.
- **Mettere campi clinici su `CRM Lead`.** Li vedrebbe chiunque veda le persone,
  compreso chi fa marketing, compresi i vostri utenti d'agenzia sui siti dei
  clienti.
- **Scegliere i destinatari di una campagna su dati clinici.**
- **Un DocType per specialità.** Diventano venti, tutti da migrare a ogni modifica.
- **Rincorrere GipoNext o AlfaDocs funzione per funzione.** Si parte da quello che
  la segreteria del pilota fa dieci volte al giorno.

## Voi come fornitore

Ospitando cartelle cliniche diventate **responsabili del trattamento** di dati
sanitari per ogni centro (art. 28 GDPR). Servono una nomina per cliente, una
valutazione d'impatto (DPIA) per il modulo clinico, backup cifrati e dati in UE
(Hetzner in Germania va bene). E un punto che si dimentica: **i vostri utenti
d'agenzia sui siti dei clienti non devono avere ruoli clinici.**

Un software per accettazione, agenda, fatture e cartella al posto della carta non è
un dispositivo medico. Lo diventa se suggerisce dosaggi o segnala interazioni fra
farmaci (linee guida MDCG 2019-11, rev. giugno 2025): quelle funzioni restano
fuori. Più avanti c'è lo Spazio europeo dei dati sanitari (regolamento UE
2025/327): i sistemi di cartella elettronica dovranno autocertificarsi e avere la
marcatura CE, con date fra il 2027 e il 2031. Prima di vendere il modulo clinico
come prodotto va sentito un legale ([ricerca §2.6](./ricerca.md#26-dispositivo-medico-e-spazio-europeo-dei-dati-sanitari)).

## Come si parte davvero

1. Un giorno seduti nella segreteria del centro pilota: cosa fanno con il
   gestionale di oggi, in che ordine, quante volte al giorno, e chi risponde a
   quale messaggio.
2. Le cinque domande qui sopra, chiuse con il committente.
3. Fase 0.
