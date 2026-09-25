# Il gestionale per i centri medici: come farlo stare in Frappe

**Stato:** 📐 proposta (25/09/2026). Prima di scrivere codice vanno chiuse le
[cinque domande](#le-cinque-domande-da-chiudere-prima) in fondo. Gli obblighi di
legge, i gestionali concorrenti e l'ecosistema Frappe, con le fonti, sono in
[ricerca.md](./ricerca.md).

## Il problema in una riga

Il CRM oggi fa molto bene il **prima** della visita: trova la persona, la fa
prenotare (dal sito, da MioDottore, al telefono), le ricorda l'appuntamento, dice
quanto è costato acquisirla. Un gestionale medico è soprattutto il **durante** e il
**dopo**: accettazione, cartella, referto, fattura, invio al Sistema TS, compensi
dei medici.

Sono due prodotti che hanno in comune due cose sole, **la persona e l'agenda**. La
difficoltà non è Frappe: è che il confine fra i due non è ancora tracciato. Questo
documento lo traccia.

## Cosa c'è già e cosa manca

| Area | Oggi nel repo | Cosa manca per un centro medico |
|---|---|---|
| Persona | `CRM Lead` è la persona, con un solo `Contact` ([18](../progetto-ghl/18-persona-unica.md), [21](../progetto-ghl/21-lead-contatto-trattativa.md)): nome, sesso, email, cellulare | Codice fiscale, nascita, residenza (sulla persona **non c'è nessun indirizzo**), tessera sanitaria, genitore o tutore per i minori |
| Privacy | La spunta privacy di `/prenota` viene controllata (`crm/api/service_booking.py:565`) **ma non registrata**. L'hook `user_data_fields` è commentato | Consensi registrati (quale testo, quale versione, quando, come), opposizione all'invio STS, consenso al dossier |
| Agenda | Un motore solo: servizi, professionisti, stanze, attrezzature, listini condizionati, `/prenota`, piattaforme esterne, automazioni sugli stati | Lo stato "arrivato", l'accettazione, le prestazioni *eseguite* (spesso diverse dalle prenotate), i listini per convenzione |
| Soldi | Niente. `total_amount` è il valore prenotato, non l'incassato. ERPNext crea clienti e preventivi, non fatture | Fattura sanitaria, incassi e acconti, note di credito, chiusura cassa, invio STS, fattura elettronica ai fondi e alle aziende, compensi dei medici |
| Clinica | Niente | Cartella per specialità, referti, consensi informati, allegati, registro degli accessi |
| Ruoli | System Manager, Sales Manager, Sales User. Ogni utente vede tutti gli appuntamenti | Segreteria, Medico, Direzione sanitaria, Amministrazione. Chi fa marketing non vede la clinica |
| Moduli | Nessun interruttore per modulo: `crm/dashboard/features.py` rileva cosa usa il sito, ma serve solo alla dashboard | Un interruttore "settore medico" che accende menu, pagine, impostazioni, widget e job |

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

1. **Porta una seconda agenda.** `Patient Appointment`, `Healthcare Practitioner`,
   `Practitioner Schedule`, `Healthcare Service Unit`: un'agenda e un'anagrafica
   parallele a quelle appena unificate ([sistema-unico](../prenotazioni/sistema-unico.md)).
   Due agende sono il problema che avete appena finito di risolvere.
2. **Vuole ERPNext su ogni sito.** Un server da $40 regge 8–12 siti perché il limite
   è la RAM e lo scheduler di ogni sito ([25](../progetto-ghl/25-costo-hosting.md)).
   ERPNext più Marley su ogni sito medico cambiano quel conto.
3. **Non sa niente dell'Italia.** Niente Sistema TS, esenzione IVA sanitaria, bollo,
   divieto di mandare allo SDI le fatture sanitarie ai privati. Andrebbe scritto
   comunque, dentro un'interfaccia Desk che il medico non userebbe.

Da Marley si prende **il modello dati come riferimento** (come separa appuntamento,
incontro clinico, procedura e referto) e, dove serve, singoli pezzi di codice: la
GPL-3 si combina con la vostra AGPL-3. L'app intera no.

**ERPNext** resta un'opzione *a valle* per il cliente grande che vuole la
contabilità vera: l'integrazione c'è già, sullo stesso sito o su uno remoto. Il
poliambulatorio privato tipico tiene la contabilità dal commercialista e al
gestionale chiede fatture, incassi, invio STS ed export. Se un cliente lo
installa, c'è una trappola: il core di ERPNext genera da solo l'XML della fattura
elettronica a ogni fattura di una società italiana (`erpnext/regional/italy`), e
per le fatture ai pazienti va spento, perché non devono mai andare allo SDI.

## Decisione 2 — Un verticale dentro `crm`, con le regole di un'app separata

| | Dove sta il codice | Pro | Contro |
|---|---|---|---|
| **A** | Moduli Frappe nuovi dentro l'app `crm` | Un repo, una SPA, una PR per funzione. Sono fatti così anche agenda, automazioni, dashboard e piattaforme | Le tabelle sanitarie esistono (vuote) anche sui siti non medici. Serve disciplina sui confini |
| **B** | App separata con la sua SPA, come Helpdesk o LMS | Isolamento totale | Due SPA: la segretaria salta fra `/crm` e `/clinica` per prenotare e poi fatturare lo stesso paziente |
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

1. **Due moduli Frappe nuovi.** `Clinica` contiene paziente, consensi, visite,
   referti e modelli di cartella. `Amministrazione` contiene accettazione, fatture,
   incassi, invio STS, compensi e convenzioni. Le cartelle sono `crm/clinica/` e
   `crm/amministrazione/`, con le voci in `modules.txt`.
2. **Dipendenza a senso unico.** I moduli nuovi importano da `crm`, il resto di
   `crm` non importa mai da loro. Si agganciano con `doc_events` in `hooks.py` e
   con i punti di estensione che esistono già: trigger delle automazioni, widget e
   feature della dashboard. Un test che scorre gli import fa rispettare la regola.
3. **Un interruttore per sito, "Settore: medico".** Accende le voci di menu
   (`AppSidebar.vue` ha già una `condition` per voce), i gruppi delle impostazioni
   (`Settings.vue` idem), i widget (`features.py`) e i job. **Ogni job schedulato
   del modulo esce subito se il sito non è medico**: lo scheduler di ogni sito è
   ciò che decide quanti siti stanno su un server.
4. **Nessun dato clinico fuori dai DocType clinici.** Niente su `CRM Lead`, nelle
   note, nella timeline, nei messaggi WhatsApp o nelle automazioni. La timeline
   della persona può dire "visita del 12/10, referto consegnato", mai cosa c'è
   scritto.
5. **Nomi.** DocType in inglese con un prefisso proprio (`Clinic Patient`,
   `Clinic Visit`…), come il resto del codice. Le etichette italiane arrivano dalla
   traduzione.

## Decisione 3 — La SPA per chi lavora, il Desk per chi configura

Le tre giornate tipo vanno nella SPA `/crm`, dove il centro lavora già:

- **Segreteria:** agenda, poi "arrivato", poi accettazione, incasso e fattura, poi
  il prossimo appuntamento.
- **Medico:** la mia giornata, poi la scheda del paziente (storia, allegati,
  consensi), poi la visita sul modello della sua specialità, poi il referto.
- **Direzione:** incassato, prodotto per medico, STS inviato e da inviare,
  consensi mancanti.

La configurazione all'inizio sta nel **Desk** (`/app`): modelli di cartella,
listini e convenzioni, sezionali, credenziali STS, regole dei compensi. Frappe
genera quelle schermate dai DocType, gratis, e le usate voi per configurare il
cliente. Nella SPA si porta solo ciò che il centro tocca davvero ogni settimana.

## Decisione 4 — I "tubi" regolati si comprano

Fattura elettronica verso lo SDI (per fondi, assicurazioni e aziende), invio al
Sistema TS, firma qualificata dei referti, conservazione a norma: **ognuno dietro
un adattatore**, come i connettori di `crm/booking_platforms/`, con un
intermediario dietro. Il gestionale produce i dati giusti (righe STS, XML
FatturaPA, PDF), l'intermediario li consegna, li conserva e restituisce gli esiti.
Per il Sistema TS ci sono API REST pronte (A-Cube, sistema-ts-api.it), per lo SDI
Aruba e OpenAPI.it; l'app `italian_invoice` di Solede (AGPL, v16) ha già un
provider OpenAPI.it da cui prendere. Il confronto è in
[ricerca.md](./ricerca.md#3-i-tubi-regolati-sdi-sistema-ts-firma).

Scriverli da zero si può, i tracciati sono pubblici. Ma vuol dire rispondere, per
tutti i clienti, di ogni scarto e di ogni cambio di specifiche. Si rivaluta dopo,
con i numeri: quando il costo per invio supera il costo di tenerli.

## Persona, deal, paziente: tre cose diverse

Oggi nel CRM:

- **la persona** (`CRM Lead`, *People* nel menu) è chiunque vi abbia contattato,
  una scheda per essere umano, per sempre. Il `Contact` è solo la sua rubrica: la
  pagina di un contatto porta alla persona (`frontend/src/router.js`);
- **il deal** è una vendita da seguire, con uno stato su una pipeline. Una persona
  ne ha zero, uno o tanti nel tempo; una richiesta nuova non ne apre un secondo se
  ce n'è già uno aperto (`open_deal_of`), ma a mano lo si può fare.

**Una persona può non avere nessun deal.** Chi prenota da `/prenota` o da una
piattaforma diventa persona e appuntamento, senza deal
(`find_or_create_person`). Chi compila un modulo del sito o di Meta diventa
persona e deal, perché qualcuno lo deve richiamare (`open_deal_for_inquiry`, da
`crm/api/form.py` e `crm/integrations/meta/leads.py`).

In un centro medico il deal serve per le richieste da richiamare e per le cure
con un preventivo (impianti, ortodonzia, medicina estetica, chirurgia, check-up,
convenzioni con aziende). Per chi prenota una visita non serve: molti pazienti
non avranno mai un deal.

**Il paziente è la terza cosa, e bisogna saperlo:** cartella e fatture vanno
conservate anche se la persona chiede di essere cancellata, il medico vede i
pazienti e chi fa marketing no, e "nuovi pazienti al mese" è il numero che il
centro guarda. La regola: **si diventa paziente alla prima accettazione**, cioè
la prima volta che si entra, non quando si prenota. Chi prenota e non si
presenta resta una persona. Deal e paziente sono indipendenti:

| | Con un deal | Senza deal |
|---|---|---|
| **Paziente** | paziente con un preventivo aperto | paziente che prenota le sue visite |
| **Non ancora paziente** | richiesta da una pubblicità, da richiamare | chi ha scritto o prenotato ma non è mai venuto |

**La prima visita chiude il deal come vinto, da sola.** Il report delle
inserzioni Meta conta come clienti i deal vinti (`cost_per_won` in
`crm/integrations/meta/insights.py`), ma in un centro medico nessuno li segnerà a
mano. Se la prima accettazione chiude come vinto il deal aperto della persona, il
report dice quanto costa un nuovo paziente per ogni inserzione, senza lavoro in
più per la segreteria.

## Il modello dati, prima versione

```
CRM Lead (la persona, com'è oggi)
  └─1:1─ Paziente ─── codice fiscale, nascita, residenza, tessera sanitaria,
            │          tutore o pagante (un'altra persona), opposizione STS,
            │          consenso al dossier
            ├── Consenso ×N ─── tipo, versione del testo, firmato il, come, PDF
            └── Documento ×N ── esami portati dal paziente (file privati)

CRM Appointment (l'agenda, com'è oggi)
  └─1:N─ Accettazione ─── chi è arrivato, prestazioni eseguite, medico,
            │              chi paga (paziente, fondo, azienda), prezzi da listino
            │              o da convenzione
            ├── Visita ──────── dati clinici sul modello della specialità
            │     └── Referto ── PDF, firma, consegna
            └── Fattura sanitaria ── Incasso ×N (metodo, tracciabile sì/no)
                  ├──► riga dell'invio STS (obbligo annuale; meglio un invio al mese)
                  └──► riga del prospetto compensi (mensile, per medico)
```

Perché così:

- **Il paziente è un DocType a parte, non campi su `CRM Lead`.** Non tutte le
  persone sono pazienti (il lead da Meta che non è mai venuto), i permessi sono
  diversi, e `CRM Lead` è il DocType più letto del core (il solo `mobile_no`
  compare in 201 punti, doc 18): il verticale non deve toccarlo.
- **L'accettazione separa l'agenda dai soldi.** `CRM Appointment` resta agenda e
  basta. L'accettazione registra cosa è stato fatto davvero, vale anche senza
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
  firmata, referto, fattura, nota di credito, invio STS, consenso. La correzione è
  *annulla e modifica*, e Frappe tiene le due versioni collegate. È esattamente
  quello che serve a una cartella clinica, che si integra ma non si riscrive.
- **Il numero di fattura si assegna al submit, non al primo salvataggio.** Frappe
  dà il nome al documento quando lo inserisce: una bozza cancellata può lasciare un
  buco nella numerazione, e le bozze salvate in ordine diverso da quello di
  emissione rompono l'ordine fra numeri e date. Il nome del documento resta
  interno; il numero fiscale è un campo, con un contatore per sezionale preso sotto
  lock al submit.
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
- **Print format Jinja e carta intestata per studio** per fattura, referto e
  consenso.
- **Le regole fiscali sono funzioni pure, testate** con `unittest` semplice come
  `crm/scheduling/booking_rules.py`: soglia del bollo, esenzione, numerazione,
  tracciato STS.

## Le fasi

Stime in settimane-persona (sp) per un senior Frappe, come in
[08](../progetto-ghl/08-roadmap.md). Il collo di bottiglia non sarà il codice ma la
validazione con il centro pilota e con il suo commercialista.

| Fase | Cosa | sp | Da qui il centro pilota può… |
|---|---|---|---|
| **0 — Fondamenta** | Interruttore "settore medico"; ruoli Segreteria, Medico, Direzione sanitaria, Amministrazione e permessi sull'agenda; paziente con codice fiscale validato; consensi registrati, compreso quello di `/prenota`; registro degli accessi; persone collegate (genitore e figlio) | 2–3 | …importare le anagrafiche dal gestionale di oggi |
| **1 — Accettazione e cassa** | Da "arrivato" all'accettazione; prestazioni eseguite; fattura sanitaria in PDF (righe esenti e righe al 22%, perché estetica e medico-legale non sono esenti; bollo; pagamento tracciabile) e note di credito; incassi e acconti; chiusura cassa; invio STS con opposizione e tracciabilità; widget e report degli incassi | 4–5 | …smettere di fatturare con il vecchio gestionale |
| **2 — Cartella e referti** | Modelli per specialità; visita; referto in PDF con firma (prima semplice su tablet, poi avanzata); consensi informati per prestazione; allegati; dossier e oscuramento; consegna del referto | 5–6 | …spegnere il vecchio gestionale |
| **3 — Amministrazione** | Compensi dei medici; convenzioni e fondi (listino dedicato, forma diretta con fattura elettronica al fondo); export per il commercialista; prima nota | 3–4 | …chiudere il mese dal gestionale |
| **4 — Paziente ed extra** | Area paziente (referti, fatture, questionario prima della visita); richiami clinici con le automazioni; televisita; magazzino dei consumabili; cicli di sedute (fisioterapia); preventivi e piani di cura (odontoiatria) | a scelta | …vendere il pacchetto completo |
| **Da tenere d'occhio** | Fascicolo sanitario 2.0: dal 31/03/2026 riguarda sulla carta anche le prestazioni private, ma per le strutture non accreditate l'obbligo è contestato e non sanzionato. Quando lo diventerà servono referti in CDA2, firma qualificata e un software accreditato dal Ministero ([ricerca §2.7](./ricerca.md#27-fascicolo-sanitario-elettronico-fse-20)) | — | — |

**Fasi 0–2: 11–14 sp, circa tre mesi per una persona.** È il minimo per sostituire
il gestionale di un poliambulatorio privato. La cassa viene prima della cartella
perché fattura e invio STS sono obbligatori e quotidiani, mentre molti medici
privati i referti oggi li scrivono in Word e possono continuare ancora qualche
settimana.

## Le cinque domande da chiudere prima

1. **Chi emette la fattura?** Il centro, che poi paga i medici a percentuale,
   oppure ogni medico con la sua partita IVA, con il centro che fattura per conto
   loro? Nel secondo caso gli emittenti sono tanti, ognuno con numerazione e invio
   STS suoi, e il modello della fase 1 cambia.
2. **Quali specialità hanno i primi clienti?** Il poliambulatorio "visite e
   referti" è il caso semplice. Odontoiatria (odontogramma, preventivi, piani di
   cura), fisioterapia (cicli di sedute) e medicina del lavoro (aziende clienti,
   protocolli, giudizi di idoneità) sono mondi a sé.
3. **Solo privati, o anche accreditati con il Servizio sanitario?** Proposta: solo
   privati, più fondi e assicurazioni. L'accreditamento porta ricetta
   dematerializzata, flussi regionali e CUP: è un altro progetto.
4. **I medici condividono la cartella?** Se sì è un dossier sanitario (consenso
   specifico, oscuramento, registro degli accessi); se no ognuno vede solo i suoi
   pazienti. La regola la decide il direttore sanitario.
5. **Il pilota sostituisce il gestionale di oggi o lo affianca per un periodo?**
   Decide quanto pesa l'importazione: anagrafiche, appuntamenti futuri, storico
   delle fatture, cartelle.

## Cosa non fare

- **Installare Marley Health o ERPNext "per avere tutto".** Due agende, due
  anagrafiche e un'interfaccia che i medici non useranno.
- **Mettere campi clinici su `CRM Lead`.** Li vedrebbe chiunque veda le persone,
  compreso chi fa marketing, compresi i vostri utenti d'agenzia sui siti dei
  clienti.
- **Un DocType per specialità.** Diventano venti, tutti da migrare a ogni modifica.
- **Scrivere da zero SDI, invio STS e firma qualificata come primo passo.**
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
   gestionale di oggi, in che ordine, quante volte al giorno.
2. Il commercialista del pilota valida le regole fiscali della fase 1 **prima**
   che vengano scritte.
3. Le cinque domande qui sopra, chiuse con il committente.
4. Fase 0.
