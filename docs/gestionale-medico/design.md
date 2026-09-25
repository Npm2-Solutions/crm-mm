# Il design: una persona, un filo, quattro sguardi

**Stato:** 🎨 design (25/09/2026), rivisto dopo cinque ricerche online. Le
schermate sono sulla tela
[Gestionale medico — il design](https://claude.ai/artifact/VoCGjBss5bvAZTyegHpSnr)
(privata: si condivide dal suo menu). Questo documento dice il perché di ogni
scelta; la [proposta](./README.md) resta il piano, i [requisiti](./requisiti.md)
le richieste verificate sul codice, la [ricerca](./ricerca.md) e la
[ricerca per il design](./ricerca-design.md) le fonti.

## L'idea

Il CRM e il centro medico non sono due programmi: sono **due modi di guardare la
stessa persona**. Ogni cosa che le succede è un nodo dello stesso filo: la
pubblicità cliccata, il messaggio, la prenotazione, i moduli firmati, l'arrivo, la
visita, la fattura, il piano, il check-in dal telefono, il richiamo. Il ruolo di
chi guarda decide cosa vede, e il paziente, dalla sua area, è il quarto sguardo.

| Nodo del filo | Marketing | Segreteria | Operatore | Paziente |
|---|---|---|---|---|
| Clic su un'inserzione | ● | — | — | — |
| Scrive su WhatsApp | ● | ● | — | ● |
| Prenota | ● | ● | ● | ● |
| Firma i moduli a casa | ○ solo il consenso al marketing | ○ firmato o no | ● l'anamnesi compilata | ● |
| **Arriva: diventa paziente** | ● il deal diventa vinto | ● | ● | — |
| Visita | — | ○ che c'è stata | ● | ○ il referto, se pubblicato |
| Fattura | — | ● | ○ che è fatturata | ● |
| Piano | — | — | ● | ● |
| Check-in: peso, pasti, foto | — | — | ● | ● |
| Richiamo a sei mesi | ● | ● | ○ | ● |

● vede tutto · ○ vede che c'è, non cosa c'è · — non lo vede

Il filo esiste già: dalla PR #101 la cronologia della persona è "una chat sola",
con una grammatica visiva precisa (il lato dice chi scrive, il colore il canale, la
nota interna sta in mezzo in ambra). Il design la estende con un terzo asse, **chi
può vederlo**: un nodo clinico porta il lucchetto e compare solo nello sguardo
degli operatori; un nodo "visibile al paziente" compare anche nella sua area.

## Gli otto principi

1. **Il filo.** Tutto sta sulla linea del tempo della persona. Un'anagrafica sola:
   il paziente è una scheda in più, non una persona in più.
2. **Le regole.** Si deduce, non si configura. La prima regola che scatta fa
   diventare paziente; la forma del centro (un operatore o più) si conta dagli
   erogatori, come fa già la fatturazione con `practice_shape`.
3. **Il modello.** Un solo motore per moduli, schede cliniche e piani. Lo stesso
   modello si vede nel CRM, nell'area cliente e nel PDF. Si può partire dal
   modulo di carta che il centro usa già.
4. **La firma.** È un componente del modulo, al livello che la legge chiede:
   semplice per privacy e anamnesi, avanzata per il consenso informato,
   qualificata per quello che firma il professionista. Si firma al banco, a casa o
   su carta, e restano le prove di chi, quando e che cosa.
5. **L'area cliente.** È l'app del centro, con il suo nome e il suo colore. Si
   entra con un codice, poi col viso o l'impronta. Prima di ogni visita dice cosa
   preparare; dentro ci sono appuntamenti, piani, documenti e messaggi.
6. **I livelli.** Segreteria, Manager amministrativo, Operatore. Il site, e
   System Manager, restano all'agenzia.
7. **L'assistente.** Scrive la bozza, non decide, e dice di essere un'IA. La
   visita dettata diventa la scheda; farmaci e allergie li conferma l'operatore,
   che firma. Niente diagnosi, niente punteggi.
8. **Il confine.** Nessun dato clinico fuori dal suo posto: non nelle note, non in
   chat, non nelle campagne, non nelle notifiche. Ogni accesso resta scritto.

## Cosa prendiamo dai migliori

Dodici gestionali studiati (Jane, Cliniko, SimplePractice, Practice Better,
Healthie, Carepatron, Semble, Halaxy, Zanda, Nookal, Doctolib, Heidi:
[ricerca per il design §1](./ricerca-design.md#1-i-prodotti-di-riferimento)).
Le idee che entrano nel design:

| Idea | Da chi | Dove sta |
|---|---|---|
| "Prepara la visita": moduli, consensi e documenti da portare, con l'avanzamento | Doctolib, SimplePractice, Jane | Area cliente, "Oggi" |
| Moduli chiesti per regola (prestazione, operatore) e con una validità | Jane | Builder, "Quando si chiede" |
| Risposte del paziente che aggiornano la scheda, dopo una conferma | Semble, Cliniko, Halaxy | Motore dei modelli |
| Tablet che esce dall'utente dello staff e segna "compilato dal paziente" | Jane | Tablet al banco |
| Visita firmata e poi solo aggiunte; si riapre con un motivo scritto | Cliniko, Healthie, SimplePractice | Operatore |
| Chi vede la voce: tutti gli operatori, la mia disciplina, solo io | Jane | Operatore, permessi |
| Fuori dall'équipe si apre la cartella solo scrivendo il motivo | Healthie | Permessi |
| Questionari a punteggio con fasce e andamento nel tempo | Halaxy, SimplePractice | Builder, "Punteggio" |
| Proposte dell'IA da accettare una per una; trascrizione cancellata | Doctolib | Operatore, assistente |
| Il modello creato da un PDF o da una descrizione | Heidi, Practice Better | Builder |
| Programmi a tappe e diari che l'operatore commenta | Practice Better, Healthie | Piani |
| Familiari e tutori nella stessa area | Jane, Doctolib | Area cliente |

E quello di cui si lamentano i loro clienti, da non ripetere: assistenza
irraggiungibile, prezzo che sale per ogni operatore in più, report poveri, SMS
che non arrivano senza che nessuno se ne accorga, dati persi nel trasloco, server
di cui non si sa il paese. Da noi: l'agenzia è vicina e parla italiano, il prezzo
è per centro, la dashboard e gli export ci sono, lo stato di consegna dei messaggi
si vede, l'importazione si riconcilia riga per riga, i dati stanno in UE con un
contratto chiaro.

## Le schermate

Sulla tela ci sono quattro pagine.

| Pagina | Tavola | Che cosa mostra |
|---|---|---|
| L'idea | Una persona, un filo, quattro sguardi | La matrice qui sopra e gli otto principi |
| | Le regole e i livelli | Le sei regole per diventare paziente e la tabella di chi vede cosa |
| Nel CRM | La persona vista dall'operatore | La sezione "Clinica": sintesi (allergie, farmaci, parametri, aderenza), la visita dettata con le proposte da confermare e "chi la vede", la storia clinica; a destra "paziente dal… per la regola 1" e i consensi |
| | La stessa persona vista dal marketing | La chat del filo fino al momento in cui diventa paziente, poi un lucchetto; da dove arriva, la richiesta vinta in automatico, cosa le si può mandare, e un'automazione saltata per mancanza di consenso |
| | La giornata della segreteria | Arrivi, sala d'attesa, moduli da firmare oggi, la coda "Dall'agenda, non ancora fatturati" che c'è già, e "ieri senza esito" |
| | Il builder dei modelli | Si parte anche dal PDF di carta; il consenso su misura, la firma avanzata con codice, la controfirma qualificata, quando si chiede e cosa succede dopo |
| | Il tablet al banco | Il paziente sceglie i consensi facoltativi e firma col dito; si registra il tratto come immagine, non la pressione |
| | Impostazioni: utenti e livelli | Livelli per persona, qualifica dall'erogatore, l'agenzia in sola lettura con l'accesso di supporto |
| Area cliente | Accesso, Oggi, Piano alimentare, Allenamento, Documenti e messaggi, Firmare dal telefono | Un prototipo cliccabile: "Prepara la seduta", il pasto segnato con un tocco, il referto online per 45 giorni, il consenso firmato con un codice |
| Com'è fatto | Com'è fatto · Le fasi · Le norme, già dentro | I moduli, i tre motori, gli adattatori, i mattoni Frappe; le cinque fasi con le stime; che firma per quale modulo, i referti, l'assistente e il calendario delle norme |

Le schermate del CRM seguono lo stile di frappe-ui (Inter, grigi, raggi di 8 px) per
sembrare il prodotto che c'è; quelle dell'area cliente seguono `/prenota`, con il
colore dello studio al posto del verde d'esempio.

## Il motore dei modelli

**Un modello è uno schema versionato**: sezioni, campi, testo legale, componenti.
Un modulo, una scheda clinica e un piano sono lo stesso oggetto con tre usi:

| Uso | Chi lo compila | Dove finisce | Esempio |
|---|---|---|---|
| Modulo | il paziente | registro dei consensi, cartella | informativa, consenso informato, anamnesi |
| Scheda clinica | l'operatore | cartella | visita nutrizionale, valutazione fisioterapica |
| Piano | l'operatore, il paziente lo segue | area cliente | dieta, allenamento, esercizi a casa |

- **I componenti**: testo, numero, scelta, sì/no, data, scala 0–10, tabella,
  testo da leggere, calcolo (per esempio il BMI da peso e altezza), questionario a
  punteggio con fasce, destra e sinistra affiancate, frasi pronte che scrivono il
  testo, mappa del corpo, foto clinica, allegato, firma (paziente, operatore,
  genitore o tutore), pasto e alimento, esercizio con serie e ripetizioni.
- **La logica**: "mostra se", "obbligatorio se", "ferma e avvisa l'operatore se"
  (il pacemaker prima delle onde d'urto). La stessa logica gira anche sul server,
  in Python con i suoi test, così un modulo non si salva incompleto da nessuna
  strada.
- **Le versioni**: una versione pubblicata non si modifica. Ogni compilazione
  punta alla versione che ha usato, con l'impronta dello schema, e il PDF porta il
  testo esatto firmato. Chi cambia un consenso sceglie da che data richiederlo.
- **Quando si chiede**: per prestazione, per operatore o per disciplina, con una
  validità (un anno, un ciclo, per sempre). Il modulo arriva con la conferma della
  prenotazione, dentro "Prepara la visita".
- **Le risposte che valgono per la scheda** (allergie, farmaci, peso) si
  propongono alla sintesi del paziente e l'operatore le conferma.
- **Il consenso su misura**: un consenso informato ha sempre un campo che
  l'operatore scrive per quella persona. La Cassazione, nel 2026, ha detto che un
  modulo generico firmato non prova che il paziente sia stato informato davvero.
- **Dal modulo di carta**: si carica il PDF che il centro usa già, l'assistente
  propone i campi e chi costruisce il modello li controlla. È lavoro
  amministrativo: nessun rischio da dispositivo medico.
- **Tre rese dello stesso schema**: nel CRM con `FieldLayout` in modalità
  standalone (quella di `formDialog()`), più i componenti nuovi; nell'area
  cliente con gli stessi componenti Vue; nel PDF con un print format Jinja che
  percorre lo schema congelato, poi il motore PDF/A che la fatturazione ha già.
- **Dove stanno i valori**: in un campo JSON della compilazione, più le poche
  colonne vere che servono alle statistiche (diagnosi, peso, parametri vitali).
  Non i Web Form di Frappe: ogni loro campo deve essere un campo del DocType, e
  vorrebbe dire un DocType per specialità.
- **Il builder** parte da quello che c'è (Impostazioni → Forms,
  `FormBuilderPanel.vue`, oggi solo per i lead) e diventa uno solo, con due
  destinazioni: il lead dal sito, come oggi, e il modello del centro.
- **Il marchio "dato clinico"** sul modello decide la regola 1: una compilazione
  di un modello clinico fa diventare paziente.

## La firma

**Il livello lo sceglie il modello**, non chi fa firmare
([ricerca per il design §3](./ricerca-design.md#3-firma-e-area-cliente)):

| Modulo | Firma | Come |
|---|---|---|
| Informativa, consensi privacy, anamnesi, questionari | semplice | il tratto col dito (o un clic), più chi, quando, dispositivo e impronta del documento |
| Consenso informato, preventivo | avanzata | codice SMS dal fornitore di firma, al banco o a casa, dopo l'attivazione con un documento; in alternativa video |
| Controfirma dell'operatore, referto | qualificata | firma digitale remota del professionista |

- **Perché così.** La firma semplice vale quanto un giudice decide che valga (CAD
  art. 20); per privacy e anamnesi basta, perché la legge chiede di poter dimostrare
  il consenso, non una firma. Il consenso informato va "in forma scritta o
  attraverso videoregistrazioni" (L. 219/2017): con la firma avanzata la forma
  scritta non si discute.
- **Niente biometria.** Il tratto si salva come immagine. La pressione e i tempi
  di ogni punto (che `signature_pad` sa leggere) non si salvano: sarebbero dati
  biometrici, con le regole del Garante del 2014. La firma avanzata usa il codice
  SMS, non la grafometria.
- **Le prove di ogni firma**: il PDF/A con il testo, il modello e la sua versione,
  i valori, l'immagine della firma e una pagina di prove; l'impronta SHA-256 del
  PDF e dello schema; come è stato riconosciuto chi firma (operatore al banco, o
  link e codice); un registro degli eventi che si aggiunge soltanto (inviato,
  aperto, codice mandato, codice verificato, firmato) con ora del server, IP e
  dispositivo; il sigillo del centro e la marca temporale; la copia nell'area del
  paziente; l'invio in conservazione. Il registro segue lo schema di `CRM Invoice
  Log`, che c'è già.
- **Un adattatore, più fornitori.** `SignatureProvider` con cinque operazioni
  (crea la richiesta, pagina di firma, webhook, scarica il firmato, scarica le
  prove). La firma semplice la facciamo noi; per l'avanzata e la qualificata un
  fornitore italiano: Namirial eSignAnyWhere ha prezzi pubblici (240–360 € l'anno
  più IVA), InfoCert è il più diffuso, Intesi ha l'API standard CSC per la firma
  remota dei professionisti. Sigillo e marca temporale sul PDF con `pyHanko`.
- **Il kit dell'erogatore.** Con la firma avanzata il centro diventa "erogatore"
  (DPCM 22/2/2013, art. 57): riconosce la persona con un documento, le fa firmare
  una dichiarazione di accettazione, conserva documento e dichiarazione per 20
  anni, pubblica sul sito come funziona il servizio, ha un'assicurazione da almeno
  500.000 €. Il prodotto porta già la pagina per il sito, il modulo di
  accettazione, la conservazione e il promemoria per l'assicurazione.
- **Due strade.** A casa: il link monouso arriva con la conferma della
  prenotazione (senza dati sanitari nel messaggio), il paziente entra con un codice,
  legge, spunta, firma; il consenso informato si firma col codice se la firma
  avanzata è attiva, altrimenti si legge prima e si firma al banco. Al banco: il
  tablet mostra solo i moduli di quel paziente ed esce dall'utente dello staff; la
  prima volta si attiva la firma avanzata col documento. Su carta: si firma, si
  scansiona in PDF/A e l'operatore attesta la copia, con le stesse prove.
- **Da Frappe**: `Web Form Request` (dalla v16.35) dà link monouso, con scadenza e
  valori precompilati, senza login. Si usa quella, o si copiano le sue regole nel
  token che `/prenota` ha già.

## L'area cliente

- **Un'app a parte.** Una seconda app Vite nello stesso modulo, su `/area`, con il
  suo service worker: come HRMS, che ha l'app dei dipendenti accanto a quella
  dell'ufficio. Non la SPA del CRM: la sua pagina d'ingresso respinge chi non è
  dello staff, e il paziente scaricherebbe il codice dello staff. Riusa
  `FieldLayout`, la firma, `BottomSheet` e `MobileShell` di frappe-ui. `/prenota`
  resta Jinja.
- **Chi entra.** Un utente del sito (senza accesso al Desk) con il ruolo "Clinic
  Patient", collegato alla sua persona, solo su invito. Ogni API sta in
  `crm/api/portal.py` e ricava "la mia persona" sul server: non accetta mai un id
  dal telefono. Come Helpdesk fa con i clienti.
- **Come si entra.** La prima volta un codice via email o SMS (un endpoint piccolo
  sul modello di `login_via_key`: codice in Redis, 10 minuti, tentativi limitati;
  Frappe ha già il link via email, acceso di serie). Dalla volta dopo, se il
  paziente vuole, una passkey: viso o impronta, che restano sul telefono. Per
  scaricare un referto si rientra. SPID e CIE si aggiungono dopo, da un
  aggregatore.
- **"Prepara la visita".** Per ogni appuntamento una lista con l'avanzamento:
  moduli, consensi, documenti da caricare. Promemoria finché non è finita.
- **Referti.** L'area è una scelta: su carta resta tutto. Un referto resta online
  45 giorni e si può scaricare; niente esiti genetici o HIV. Sono le linee guida
  del Garante sui referti online.
- **Notifiche.** WhatsApp, SMS ed email dicono solo "c'è una novità nella tua
  area"; le email vanno solo a indirizzi verificati (nel dicembre 2025 il Garante ha
  ammonito un centro di fisioterapia per un referto mandato a un indirizzo sbagliato
  di una lettera). Le notifiche push arrivano su iPhone solo dopo "Aggiungi a Home",
  e su un server nostro servono un service worker e `pywebpush`: il relay di Frappe
  è pensato per Frappe Cloud.
- **Familiari.** Il genitore vede e firma per il figlio minorenne; un figlio può
  seguire un genitore anziano, se lui lo autorizza.
- **Documenti.** I file restano privati: il paziente li scarica perché può leggere
  il documento a cui sono attaccati, e Frappe registra ogni download. I file non
  sono cifrati sul disco: la cifratura sta nei backup e nel disco del server.

## I piani

([ricerca per il design §2](./ricerca-design.md#2-i-piani-nutrizione-allenamento-esercizi-a-casa))

- **Cinque tipi**: piano alimentare a menù, dieta a scambi, allenamento, esercizi a
  casa, abitudini. Tutti con lo stesso modello a righe: Frappe non annida le
  tabelle figlie, quindi un piano ha una tabella di "momenti" (giorno e pasto, o
  seduta) e una di voci (alimento o esercizio, con la quantità) che punta al suo
  momento.
- **Le librerie**: alimenti ed esercizi del centro. Per gli alimenti la BDA-IEO
  (per un software commerciale si chiede la licenza, a pagamento) e le tabelle
  libere CIQUAL e USDA per i buchi; Open Food Facts solo per i prodotti di marca,
  perché la sua licenza vieta gli usi medici. Per gli esercizi, video girati dal
  centro o un link YouTube o Vimeo: le librerie commerciali di solito non
  permettono di rivenderli.
- **Chi scrive cosa**: la qualifica dell'erogatore decide. La dieta la firmano
  medico, biologo nutrizionista o dietista (su prescrizione del medico); il
  personal trainer no, perché dare diete è esercizio abusivo della professione;
  gli esercizi di riabilitazione il fisioterapista o il medico.
- **Il paziente sceglie dentro i limiti**: tre alternative equivalenti al
  merluzzo, e "pesce: ancora 2 volte questa settimana". Lista della spesa dal menù.
- **Farli seguire**: un tocco per pasto (fatto, in parte, saltato); calorie solo
  se l'operatore le vuole mostrare; niente rosso "fuori obiettivo", niente
  classifiche; la serie di giorni si può recuperare; la foto del pasto è
  facoltativa, con il promemoria all'ora del pasto. Un diario alimentare si
  abbandona in pochi giorni se costa fatica.
- **Programmi a tappe**: contenuti che si aprono col tempo o finita la tappa
  prima, per i percorsi di nutrizione e di allenamento.
- **Orologi e bilance**: dal server con Google Health API (Fitbit, Pixel Watch),
  Garmin e Withings. Apple Salute e Health Connect vogliono un'app nativa: dopo.
- **Dispositivo medico**: il piano è uno strumento con cui il professionista
  scrive e il paziente segue. Il prodotto non promette di curare, e i conti dei
  nutrienti li fa il motore dalle tabelle, non l'IA.

## L'assistente

([ricerca per il design §4](./ricerca-design.md#4-lassistente-e-le-regole-europee))

**In ordine, da quello che rende di più con meno rischio:**

1. Lavoro d'ufficio: moduli di carta che diventano modelli, dati per la fattura e
   il Sistema TS, riassunto delle telefonate al banco.
2. Bozze dalla nota firmata dell'operatore: lettera al medico curante,
   certificato, istruzioni dopo la visita, risposta a un messaggio del paziente.
3. La visita dettata dall'operatore, messa nei campi del modello della specialità.
4. Il riassunto prima della visita, con le fonti citate, senza classifiche né
   avvisi.
5. Il menù per il nutrizionista: obiettivi suoi, nutrienti calcolati dalle
   tabelle, l'IA propone solo le ricette.
6. Una chat per il paziente solo per l'amministrazione (orari, prenotazioni,
   domande frequenti scritte dal centro); se parla di sintomi passa a una persona o
   indica il 112.

**Registrare la visita mentre si svolge, no, per ora.** In Svezia l'autorità ha
trovato che uno scribe che compila informazioni cliniche è un dispositivo medico,
almeno di classe IIa; nel Regno Unito invece no, se il medico rilegge. Se un centro
lo vuole, si integra uno scribe che ha già il marchio CE (Tandem, classe IIa, è
entrato in Italia con Humanitas) invece di certificarne uno nostro.

**Quello che non farà mai**, a meno di diventare un dispositivo medico
certificato: diagnosi o terapie suggerite, punteggi di rischio, "insight", ordini
automatici, analisi delle emozioni dalla voce.

**Come resta fuori dai dispositivi medici e dentro le regole:**

- Una sola frase sullo scopo, ovunque (istruzioni, sito, presentazioni):
  "supporto alla documentazione amministrativa; le bozze le rivede il
  professionista". Mai promettere diagnosi migliori.
- Scrive solo quello che è stato detto o scritto: niente diagnosi dedotte, niente
  codici ricavati da cose non dette, niente avvisi.
- Niente si salva da solo: firma l'operatore. Farmaci, allergie e dosi, dove gli
  scribe sbagliano di più, si confermano uno per uno.
- Dice sempre che è un'IA: al paziente in chat (AI Act art. 50, dal 2 agosto
  2026), nell'informativa (L. 132/2025, art. 7), e il professionista dice ai suoi
  clienti quali sistemi usa (art. 13). Ogni nota porta il segno "bozza dell'IA,
  verificata da… alle…".
- La L. 132/2025 vieta anche di scegliere chi curare con criteri discriminatori:
  vale per ogni punteggio o priorità sui lead, non solo per l'assistente.
- Ogni funzione nuova passa la verifica delle linee guida MDCG 2019-11, messa per
  iscritto.

**I dati:**

- La dettatura si trascrive e l'audio si cancella; la trascrizione resta finché la
  nota non è firmata (al massimo 14 giorni). La trascrizione delle chiamate ha già
  un adattatore compatibile con OpenAI, anche per un Whisper sul server del centro.
- Il modello linguistico gira in UE: l'API di Anthropic non fissa la regione, ma
  Claude su AWS Bedrock (profili "eu", anche Milano) o su Vertex AI (endpoint UE)
  sì; OpenAI ha la residenza in UE. Nessuna conservazione e nessun addestramento
  nel contratto.
- Il centro è titolare, l'agenzia responsabile (art. 28 GDPR), i fornitori
  sub-responsabili, con l'elenco pubblicato. Prima di partire, una valutazione
  d'impatto.
- Un registro dell'assistente: modello, fornitore, regione, versione del modello
  della scheda, impronte di ingresso e uscita, differenza fra bozza e nota firmata.
  Ogni mese un campione si rilegge.

## I livelli e i permessi

- **Tre livelli, più l'agenzia.** Un livello è un Role Profile di Frappe; la v16
  ne permette più d'uno per utente (`User.role_profiles`), che è il titolare che
  visita: Manager più Operatore. Il CRM assegna livelli, mai ruoli.
- **Il vincolo di Frappe**: a ogni salvataggio dell'utente i ruoli vengono rifatti
  dai profili, e un ruolo messo a mano sparisce. Quindi gli utenti dell'agenzia non
  hanno profili del centro, e il CRM rifiuta un profilo che contenga System
  Manager. L'invito del CRM assegna il livello, non i ruoli.
- **Un posto solo decide**: un modulo (per esempio `crm/permissions/livelli.py`) al
  posto delle 16 copie di `MANAGER_ROLES`, e dal server un elenco di capacità che
  il frontend legge, come fa LMS.
- **Per record**: l'operatore vede i suoi pazienti; con il consenso al dossier li
  vedono tutti gli operatori del centro, tranne gli episodi oscurati. Una voce può
  essere visibile a tutti gli operatori, alla disciplina o solo a chi l'ha scritta.
  Chi è fuori dall'équipe apre la cartella solo scrivendo il motivo, e il manager
  lo vede.
- **Due passaggi all'accesso** per i ruoli clinici (Frappe li chiede per ruolo), e
  il codice fiscale mascherato al marketing (i campi mascherati sono nuovi nella
  v16).
- **L'agenzia e i dati clinici**: i DocType clinici non danno permessi a System
  Manager. Il supporto sulla cartella è un accesso a tempo, chiesto dal centro,
  con un motivo, registrato.
- **Il registro degli accessi**: ogni lettura clinica dalla SPA passa da un'API che
  chiama `doc.add_viewed()` (la SPA non passa dal form del Desk, che è l'unico a
  scriverlo da solo), e il View Log si tiene 24 mesi. È anche il "componente di
  registrazione" che lo spazio europeo dei dati sanitari chiederà.

## Il modello dati

Nel modulo `crm/clinica`, DocType con prefisso `Clinic`:

| DocType | Che cos'è | Campi che contano |
|---|---|---|
| `Clinic Patient` | la scheda paziente, uno a uno con `CRM Lead` | paziente dal, regola, origine, tutore o pagante, consenso al dossier |
| `Clinic Template` | il modello, in lavorazione | uso (modulo, scheda, piano), specialità, dato clinico sì/no, quando si chiede, validità |
| `Clinic Template Version` | una versione pubblicata, immutabile | schema JSON, testo legale, firme richieste e livello, impronta SHA-256, pubblicata il |
| `Clinic Form Request` | un modulo da compilare | versione, persona, appuntamento, canale (tablet, link, carta), token, scadenza, stato |
| `Clinic Form` | un modulo compilato e firmato (submittable) | versione, valori, PDF/A e impronta, compilato da (paziente o staff) |
| `Clinic Signature` | tabella figlia di `Clinic Form` e `Clinic Record` | chi, in che veste, livello, metodo, ora, IP, dispositivo, id del fornitore |
| `Clinic Event Log` | il registro che si aggiunge soltanto | documento, evento, ora, IP, dispositivo, impronta dell'evento precedente |
| `Clinic Consent` | il registro dei consensi | tipo, stato, versione del testo, da quale modulo, revocato il |
| `Clinic Record` | una voce di cartella: visita, nota, misura (submittable, poi solo aggiunte) | versione, operatore (l'erogatore), appuntamento, valori, chi la vede, colonne per le statistiche |
| `Clinic Document` | l'archivio | tipo, file privato, data, provenienza, visibile al paziente, online fino al |
| `Clinic Plan` | un piano | tipo, versione del modello, operatore, periodo, pubblicato; tabelle dei momenti e delle voci |
| `Clinic Food`, `Clinic Exercise` | le librerie | nutrienti e fonte con licenza; video o link, istruzioni |
| `Clinic Plan Log` | un check-in del paziente | voce, esito (fatto, in parte, saltato), peso, fatica o dolore, foto, nota |
| `Clinic Message` | un messaggio nell'area | autore, testo, letto il |
| `Clinic AI Event` | il registro dell'assistente | funzione, modello, fornitore, regione, impronte, bozza e differenza con la nota firmata |
| `Clinic Access Grant` | l'accesso di supporto dell'agenzia | chi, perché, da, a, chiesto da |

Da `crm/invoicing` si riusano l'erogatore (`CRM Service Provider`: il medico con la
sua qualifica) e, da aggiungere lì, l'anagrafica fiscale della persona.

## Le norme e il calendario

La tavola "Le norme, già dentro" mette insieme quello che il prodotto fa per
conto di chi lo usa: il modello sceglie la firma, l'area conta i giorni del
referto, l'assistente non può fare diagnosi. Le date che contano:

| Quando | Che cosa | Per noi |
|---|---|---|
| 2 agosto 2026 | AI Act, trasparenza (art. 50): già in vigore | la chat dice che è un'IA; le bozze portano il segno |
| ottobre 2026 | i decreti italiani sull'IA attesi dalla L. 132/2025 | da rileggere quando escono |
| 26 marzo 2027 | spazio europeo dei dati sanitari (EHDS): i formati comuni | export della cartella nel formato europeo |
| 2 agosto 2028 | IA nei dispositivi medici: regole ad alto rischio | restiamo fuori, con lo scopo dichiarato |
| 26 marzo 2031 | EHDS per i gestionali della cartella, anche in cloud | marchio CE autodichiarato, componenti di log e interoperabilità, registrazione UE |

## Le fasi

| Fase | Che cosa | sp | Da qui il centro può… |
|---|---|---|---|
| 0 — Le fondamenta | Livelli e gestione ruoli nel CRM; Sito nascosto senza Builder; fatture lette solo da chi deve; anagrafica fiscale sola; sezione Clinica con una visita semplice; regole per diventare paziente con il recupero; consensi registrati | 4,5–6 | …lavorare dalla pagina della persona, e i pazienti si contano da soli |
| 1 — Le cuciture | Diventare paziente chiude il deal; due pipeline; evento per le automazioni; accettazione e sala d'attesa; "sono venuti?"; richiami col consenso giusto; dashboard del centro | 2–3 | …sapere quanto costa un nuovo paziente per inserzione |
| 2 — Modelli, firma, cartella | Motore dei modelli e builder, anche dal PDF; firma semplice nostra e avanzata con un fornitore; PDF/A con impronta e marca temporale; registro dei consensi; schede e referti, firmati e poi solo aggiunte; archivio; accessi, dossier, oscuramento | 8–10 | …spegnere il vecchio gestionale |
| 3 — Area cliente e piani | App a parte, codice e passkey; "Prepara la visita"; appuntamenti, documenti, messaggi, fatture; referti per 45 giorni; piani, librerie e check-in con un tocco | 6–8 | …dare a ogni paziente l'app del suo centro |
| 4 — L'assistente | Bozze dalla nota, visita dettata, riassunto con le fonti, menù con i conti dalle tabelle; registro dell'assistente | 3–4 | …scrivere meno |

Fasi 0–3: 21–27 settimane-persona; con l'assistente 24–31. Stime indicative, da
rifare dopo le decisioni aperte. `Web Form Request` chiede Frappe v16.35: il minimo
in `pyproject.toml` (oggi qualunque 16.x) va alzato.

## Da decidere

1. Chi fa il marketing per il centro: voi, il centro, o entrambi?
2. L'operatore vede tutti i pazienti o solo i suoi, finché non c'è il consenso al
   dossier?
3. La direzione sanitaria è un livello o un permesso in più dell'operatore?
4. Firma avanzata: con quale fornitore (Namirial, InfoCert, Intesi), e il centro
   accetta i doveri dell'erogatore? Finché non c'è, il consenso informato si firma
   su carta.
5. Il primo codice dell'area arriva per email o per SMS? WhatsApp resta solo per
   gli avvisi.
6. Quali piani per primi: alimentazione, allenamento, esercizi di fisioterapia?
   Per gli alimenti si compra la licenza BDA-IEO o si parte dalle tabelle libere?
7. Il paziente può rispondere ai messaggi? Se sì, è una chat, e ai medici arriva
   un'altra casella.
8. Registrare la visita mentre si svolge: mai, oppure con uno scribe che ha già il
   marchio CE?
9. Dove gira il modello linguistico: AWS Bedrock a Milano o Vertex AI in UE?
