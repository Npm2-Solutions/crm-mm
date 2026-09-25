# Il design: una persona, un filo, quattro sguardi

**Stato:** 🎨 design (25/09/2026). Le schermate sono sulla tela
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
| Piano alimentare | — | — | ● | ● |
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
   modello si vede nel CRM, nell'area cliente e nel PDF.
4. **La firma.** È un componente del modulo, non un modulo a parte. Si firma al
   banco sul tablet, a casa dal telefono o su carta, e restano le prove di chi,
   quando e che cosa.
5. **L'area cliente.** È l'app del centro, con il suo nome e il suo colore: si
   entra con un codice, si installa sul telefono, dentro ci sono appuntamenti,
   piani, documenti e messaggi.
6. **I livelli.** Segreteria, Manager amministrativo, Operatore. Il site, e
   System Manager, restano all'agenzia.
7. **L'assistente.** Scrive la bozza, non decide. La visita dettata diventa la
   scheda, il piano parte da una proposta, l'operatore firma.
8. **Il confine.** Nessun dato clinico fuori dal suo posto: non nelle note, non in
   chat, non nelle campagne. Ogni accesso resta scritto.

## Le schermate

Sulla tela ci sono quattro pagine.

| Pagina | Tavola | Che cosa mostra |
|---|---|---|
| L'idea | Una persona, un filo, quattro sguardi | La matrice qui sopra e gli otto principi |
| | Le regole e i livelli | Le sei regole per diventare paziente e la tabella di chi vede cosa |
| Nel CRM | La persona vista dall'operatore | La sezione "Clinica": sintesi (allergie, parametri, aderenza), la visita sul modello della specialità con l'assistente in ascolto, la storia clinica; a destra "paziente dal… per la regola 1" e i consensi |
| | La stessa persona vista dal marketing | La chat del filo fino al momento in cui diventa paziente, poi un lucchetto; da dove arriva, la richiesta vinta in automatico, cosa le si può mandare, e un'automazione saltata per mancanza di consenso |
| | La giornata della segreteria | Arrivi, sala d'attesa, moduli da firmare oggi, la coda "Dall'agenda, non ancora fatturati" che c'è già, e "ieri senza esito" |
| | Il builder dei modelli | Palette dei componenti, il modulo al centro, le proprietà della firma a destra: chi firma, che firma, dove, e cosa succede dopo |
| | Il tablet al banco | Il paziente sceglie i consensi facoltativi e firma col dito; la schermata è bloccata sui suoi moduli |
| | Impostazioni: utenti e livelli | Livelli per persona, qualifica dall'erogatore, l'agenzia in sola lettura con l'accesso di supporto |
| Area cliente | Accesso, Oggi, Piano alimentare, Allenamento, Documenti e messaggi, Firmare dal telefono | Un prototipo cliccabile: si naviga dalla barra in basso |
| Com'è fatto | Com'è fatto · Le fasi | I moduli, i tre motori, gli adattatori; le cinque fasi con le stime |

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
  testo da leggere, calcolo (per esempio il BMI da peso e altezza), mappa del
  corpo, foto clinica, allegato, firma (paziente, operatore, genitore o tutore),
  pasto e alimento, esercizio con serie e ripetizioni.
- **La logica**: "mostra se", "obbligatorio se", "ferma e avvisa l'operatore se"
  (il pacemaker prima delle onde d'urto).
- **Le versioni**: una versione pubblicata non si modifica. Ogni compilazione
  punta alla versione che ha usato, e il PDF porta il testo esatto firmato.
- **Tre rese dello stesso schema**: nel CRM con `FieldLayout` in modalità
  standalone (quella di `formDialog()`), più i componenti nuovi (firma, mappa del
  corpo, scala, pasto, esercizio); nell'area cliente con una resa leggera; nel PDF
  con un print format Jinja e il motore PDF/A che la fatturazione ha già.
- **Dove stanno i valori**: in un campo JSON della compilazione, più le poche
  colonne vere che servono alle statistiche (diagnosi, peso, parametri vitali).
- **Il builder** parte da quello che c'è (Impostazioni → Forms, oggi solo per i
  lead) e diventa uno solo, con due destinazioni: il lead dal sito, come oggi, e il
  modello del centro.
- **Il marchio "dato clinico"** sul modello decide la regola 1: una compilazione
  di un modello clinico fa diventare paziente.

## I livelli e i permessi

- **Tre livelli, più l'agenzia.** Un livello è un Role Profile di Frappe; la v16
  ne permette più d'uno per utente (`User.role_profiles`), che è il titolare che
  visita: Manager più Operatore. Il CRM assegna livelli, mai ruoli.
- **Un posto solo decide**: un modulo (per esempio `crm/permissions/livelli.py`) al
  posto delle 16 copie di `MANAGER_ROLES`, e un livello calcolato dal server che il
  frontend legge.
- **Per record**: l'operatore vede i suoi pazienti; con il consenso al dossier li
  vedono tutti gli operatori del centro, tranne gli episodi oscurati.
- **L'agenzia e i dati clinici**: i DocType clinici non danno permessi a System
  Manager. Il supporto sulla cartella è un accesso a tempo, chiesto dal centro,
  con un motivo, registrato.
- **Il registro degli accessi**: ogni lettura clinica dalla SPA passa da un'API che
  chiama `doc.add_viewed()` (la SPA non passa dal form del Desk, che è l'unico a
  scriverlo da solo), e il View Log si tiene 24 mesi.

## Il modello dati

Nel modulo `crm/clinica`, DocType con prefisso `Clinic`:

| DocType | Che cos'è | Campi che contano |
|---|---|---|
| `Clinic Patient` | la scheda paziente, uno a uno con `CRM Lead` | paziente dal, regola, origine, tutore o pagante, consenso al dossier |
| `Clinic Template` | il modello | uso (modulo, scheda, piano), specialità, versione, stato, schema JSON, testo legale, dato clinico sì/no, firme richieste |
| `Clinic Form Request` | un modulo da compilare | modello e versione, persona, canale (tablet, link, carta), token, scadenza, stato |
| `Clinic Form` | un modulo compilato e firmato (submittable) | valori, firme, prove (ora, dispositivo, impronta), PDF |
| `Clinic Consent` | il registro dei consensi | tipo, stato, versione del testo, da quale modulo, revocato il |
| `Clinic Record` | una voce di cartella: visita, nota, misura (submittable) | modello e versione, operatore (l'erogatore), appuntamento, valori, colonne per le statistiche |
| `Clinic Document` | l'archivio | tipo, file privato, data, provenienza, visibile al paziente |
| `Clinic Plan` | un piano | tipo, modello, operatore, periodo, contenuto, versione, pubblicato |
| `Clinic Plan Log` | un check-in del paziente | pasto fatto, peso, fatica, foto, nota |
| `Clinic Message` | un messaggio nell'area | autore, testo, letto il |
| `Clinic Access Grant` | l'accesso di supporto dell'agenzia | chi, perché, da, a, chiesto da |

Da `crm/invoicing` si riusano l'erogatore (`CRM Service Provider`: il medico con la
sua qualifica) e, da aggiungere lì, l'anagrafica fiscale della persona.

## Le fasi

| Fase | Che cosa | sp | Da qui il centro può… |
|---|---|---|---|
| 0 — Le fondamenta | Livelli e gestione ruoli nel CRM; Sito nascosto senza Builder; fatture lette solo da chi deve; anagrafica fiscale sola; sezione Clinica con una visita semplice; regole per diventare paziente con il recupero; consensi registrati | 4,5–6 | …lavorare dalla pagina della persona, e i pazienti si contano da soli |
| 1 — Le cuciture | Diventare paziente chiude il deal; due pipeline; evento per le automazioni; accettazione e sala d'attesa; "sono venuti?"; richiami col consenso giusto; dashboard del centro | 2–3 | …sapere quanto costa un nuovo paziente per inserzione |
| 2 — Modelli, firma, cartella | Motore dei modelli e builder; firma come componente; PDF con impronta; registro dei consensi; schede e referti; archivio; accessi, dossier, oscuramento | 7–9 | …spegnere il vecchio gestionale |
| 3 — Area cliente e piani | Accesso con codice, app installabile col marchio, appuntamenti, documenti, messaggi, fatture, moduli da firmare; piani e check-in | 5–7 | …dare a ogni paziente l'app del suo centro |
| 4 — L'assistente | Visita dettata in bozza, riassunto prima della visita, bozze di piani e messaggi | 3–4 | …scrivere meno |

Fasi 0–3: 19–25 settimane-persona; con l'assistente 22–29. Stime indicative, da
rifare dopo le decisioni aperte.

## Da decidere

1. Chi fa il marketing per il centro: voi, il centro, o entrambi?
2. L'operatore vede tutti i pazienti o solo i suoi, finché non c'è il consenso al
   dossier?
3. La direzione sanitaria è un livello o un permesso in più dell'operatore?
4. Basta la firma semplice per partire, o serve subito quella avanzata per i
   consensi informati?
5. Il codice dell'area cliente arriva per email, SMS o WhatsApp?
6. Quali piani per primi: alimentazione, allenamento, esercizi di fisioterapia?
7. Il paziente può rispondere ai messaggi? Se sì, è una chat, e ai medici arriva
   un'altra casella.
