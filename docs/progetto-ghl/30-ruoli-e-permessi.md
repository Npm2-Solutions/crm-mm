# 30 — Ruoli e permessi: chi può fare cosa, modulo per modulo

**Stato:** 🟢 PR 1 fatta (29/09/2026): registro, livelli di base, piano, pagina
Utenti e inviti per livello, passaggio degli utenti di prima. Le PR 2–4 restano da
fare ([com'è fatta la PR 1](#la-pr-1-comè-fatta)). Lo stato "di oggi" qui sotto è
quello verificato prima della PR 1, sul commit `151cba6`.

## In una pagina

Oggi il CRM confonde in una cosa sola tre cose diverse. La proposta le separa:

1. **Il livello** è quello che il CRM mostra e assegna a una persona: Segreteria,
   Operatore, Manager amministrativo, più alcuni facoltativi. In Frappe è un
   Role Profile, e una persona può averne più d'uno.
2. **Il ruolo** è il mattone di Frappe che porta i permessi sui documenti. Ogni
   modulo porta i suoi, pochi. Nel CRM non si vede mai.
3. **La capacità** è una cosa che si può fare, con un nome: `fatture.emetti`,
   `agenda.turni`. Il codice controlla capacità, non ruoli, e il frontend le
   riceve dal server.

A queste si aggiunge **l'ambito**: su quali record vale una capacità (i suoi, il
suo team, tutto il centro).

**Ogni modulo contribuisce** con i suoi ruoli, le sue capacità, i livelli a cui
vanno di serie, le sue pagine di impostazioni divise fra lavoro e tecnica, e le
regole d'ambito dei suoi documenti. Un file solo li mette insieme,
`crm/permissions/livelli.py`, come `crm/invoicing/estensioni.py` fa già per la
fatturazione.

**L'agenzia sta fuori.** System Manager e Administrator restano vostri, il CRM non
li offre mai. Le impostazioni tecniche (chiavi, webhook, token, log grezzi,
codice) restano all'agenzia, come il [doc 27](./27-impostazioni-canali-integrazioni.md)
ha già fatto per Meta e WhatsApp.

## Come stanno le cose oggi

- **Un ruolo solo per persona.** Il server calcola il più alto fra System Manager
  ("Admin"), Sales Manager ("Manager") e Sales User (`crm/api/session.py`). Il
  frontend decide con `isManager()` (63 righe in 20 file) e `isAdmin()` (9 righe in
  6 file). I ruoli della fatturazione il frontend non li vede, e chi ha solo quelli
  non entra nel CRM (`check_app_permission`).
- **Il controllo "è un manager" è copiato in 19 file**, più sei controlli scritti a
  mano, e non dice sempre la stessa cosa: in `google/oauth.py` include Sales User;
  il dialer, le viste pubbliche e la gerarchia guardano solo Sales Manager. I fix
  del 29/09 ne hanno aggiunti tre (filtri rapidi, regole di assegnazione, ERPNext),
  in attesa del registro.
- **La visibilità per record c'è per persone e trattative** (la gerarchia di
  vendita, `crm/permissions/org_hierarchy.py`), e dal 29/09 **chiamate, note e
  task le seguono**: una chiamata, con registrazione e trascrizione, la vede chi
  l'ha fatta o presa e chi vede il lead o la trattativa collegati. Appuntamenti
  con le note, messaggi WhatsApp e SMS, fatture e dati di tracciamento li legge
  ancora ogni Sales User.
- **I permessi sui documenti sono più larghi delle schermate.** Con l'API un Sales
  User scrive servizi, listini, turni, orari dello studio, fasi della pipeline,
  modelli e impostazioni WhatsApp, viste pubbliche: tutte cose che lo schermo
  riserva ai manager.
- **Lo schermo mostra cose che il server rifiuta.** Il menu dei livelli nella
  pagina Utenti offre Admin e Manager a tutti, per un `|| true`
  (`Users.vue:272`). Le fatture si vedono ai Sales Manager, che non possono
  scriverle. Predefiniti, account email e regole di assegnazione sono documenti del
  core di Frappe, riservati a System Manager. Automazioni, fatture, sito e
  importazione sono nascosti solo dal menu: dall'indirizzo si aprono.
- **I quattro problemi di sicurezza sono chiusi** (29/09, in `develop`; il perché
  di ogni scelta è in `.pi/ARCHIVE.md`):
  - gli inviti: il ruolo è uno che chi invita può dare, della chiave si salva
    solo l'hash, gli inviti si creano solo da Invita utente, e chi ha già un
    account accede prima di accettare. Le chiavi leggibili sono scadute con una
    patch;
  - il menu utente: l'icona è solo un nome Feather, l'indirizzo solo un percorso
    del sito o un link http(s), controllati al salvataggio e nel menu;
  - le funzioni che rispondevano senza controllo (chiamate, registrazioni,
    trascrizioni, calendario, contatti di trattative e persone, di chi è un
    numero, record collegati, creazione di trattative, ripristini) ora chiedono il
    permesso sul record;
  - filtri rapidi, interruttore della gerarchia, accesso degli ospiti ai moduli e
    metodi di ERPNext controllano il ruolo; i segreti delle integrazioni sono
    campi Password.
- **Restano aperti tre punti**, tutti nella PR 2 qui sotto: quello che ogni Sales
  User legge ancora (due punti sopra); il calendario, che dà nome, email e
  telefono di tutti i partecipanti di ogni appuntamento, da rivedere prima
  dell'area cliente; `create_deal`, che salva ancora con `ignore_permissions`,
  quindi lì non valgono né i permessi per campo né i User Permission.

## Chi lavora nel sistema: i livelli

| Livello | Chi | In breve | |
|---|---|---|---|
| **Segreteria** | banco, telefono, accettazione | agenda di tutti, persone, conversazioni, arrivi, moduli da firmare, fatture e incassi | base |
| **Operatore** | medico, nutrizionista, fisioterapista, psicologo, trainer, estetista | la sua agenda, i suoi clienti o pazienti, la cartella e i piani, i suoi messaggi | base |
| **Manager amministrativo** | titolare o responsabile del centro | tutto il lavoro del centro: impostazioni di lavoro, utenti e livelli, i numeri | base |
| **Commerciale** | chi vende pacchetti, preventivi, abbonamenti | richieste e trattative, le sue o del suo team | facoltativo |
| **Marketing** | chi fa campagne, social, inserzioni, anche l'agenzia | automazioni, social, Meta, tracciamento, con i dati personali mascherati | facoltativo |
| **Amministrazione** | contabilità, interna o esterna | fatture, Sistema TS, incassi, esportazioni | facoltativo |
| **Direzione sanitaria** | direttore sanitario | vigilanza clinica: tutte le cartelle, registro degli accessi, modelli clinici | facoltativo, con la clinica |
| **Sola lettura** | revisore, consulente, tirocinante all'inizio | si aggiunge a un altro livello e toglie ogni scrittura | facoltativo |

Fuori dai livelli:

- **Responsabile** non è un livello, è un posto nella gerarchia: vede i record del
  suo team. Vale per commerciali e operatori, ma non per i dati clinici, che
  seguono le regole del dossier.
- **Agenzia**: System Manager e Administrator. Vede il non clinico per
  l'assistenza, il clinico solo con l'accesso a tempo che il centro concede.
- **Paziente o cliente**: entra nell'area cliente come utente del sito. Non è un
  livello del CRM.
- **Utenti tecnici** per le integrazioni: li gestisce l'agenzia.

**Combinazioni tipiche:**
- il titolare che visita: Manager amministrativo più Operatore;
- la segretaria che tiene anche la contabilità: Segreteria più Amministrazione;
- il commercialista esterno: Amministrazione più Sola lettura;
- il direttore sanitario che visita: Operatore più Direzione sanitaria;
- l'agenzia che fa il marketing del centro: Marketing, senza bisogno di System
  Manager.

## Le capacità, modulo per modulo

Colonne: **Seg** Segreteria · **Op** Operatore · **Man** Manager amministrativo ·
**Com** Commerciale · **Mkt** Marketing · **Amm** Amministrazione · **Dir**
Direzione sanitaria. Sola lettura toglie le scritture al livello a cui si
aggiunge; l'agenzia ha la parte tecnica, nella tabella delle impostazioni.

Valori:

| Valore | Significa |
|---|---|
| ✓ | su tutto il centro |
| suoi / sue | solo i record assegnati a sé, o i propri clienti e pazienti |
| team | i propri record più quelli del team nella gerarchia |
| vede | in sola lettura |
| masch. | con codice fiscale, telefono ed email mascherati |
| a scelta | spento di serie; il Manager lo accende per quella persona |
| — | no |

### Persone, richieste e trattative (CRM)

| Capacità | Seg | Op | Man | Com | Mkt | Amm | Dir |
|---|---|---|---|---|---|---|---|
| Vedere le persone | ✓ | suoi | ✓ | team | masch. | vede | ✓ |
| Creare e modificare le persone | ✓ | suoi | ✓ | team | — | dati fiscali | — |
| Eliminare una persona, anche per il diritto all'oblio | — | — | ✓ | — | — | — | — |
| Assegnare e cambiare il responsabile | ✓ | — | ✓ | team | — | — | — |
| Unire i doppioni | ✓ | — | ✓ | — | — | — | — |
| Importare | — | — | ✓ | — | — | — | — |
| Esportare | — | — | ✓ | — | solo chi ha il consenso, masch. | fatture | — |
| Richieste e trattative | ✓ | vede le sue | ✓ | team | vede | vede il valore | — |
| Configurare pipeline e fasi | — | — | ✓ | — | — | — | — |
| Viste pubbliche, filtri rapidi, campi delle schede | — | — | ✓ | — | — | — | — |

### Conversazioni

| Capacità | Seg | Op | Man | Com | Mkt | Amm | Dir |
|---|---|---|---|---|---|---|---|
| Leggere e rispondere: email, WhatsApp, SMS | ✓ | suoi | ✓ | team | — | — | — |
| Note interne | ✓ | suoi | ✓ | team | — | — | — |
| Segnare letta, gestita, rimandata | ✓ | suoi | ✓ | team | — | — | — |
| Usare i modelli di messaggio | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| Creare e modificare i modelli | — | — | ✓ | — | ✓ | — | — |

### Agenda e prenotazioni

| Capacità | Seg | Op | Man | Com | Mkt | Amm | Dir |
|---|---|---|---|---|---|---|---|
| Vedere l'agenda | ✓ | la sua | ✓ | libero e occupato | — | vede | vede |
| Prenotare, spostare, annullare | ✓ | la sua | ✓ | ✓ | — | — | — |
| Eliminare un appuntamento | — | — | ✓ | — | — | — | — |
| Prenotare sopra un conflitto | a scelta | — | ✓ | — | — | — | — |
| Segnare arrivato, svolto, non presentato | ✓ | la sua | ✓ | — | — | — | — |
| Turni, ferie, sale | ✓ | chiede le sue ferie | ✓ | — | — | — | — |
| Servizi, listini, orari e regole dello studio | — | — | ✓ | — | — | — | — |
| Prenotazione online e pagina `/prenota` | — | — | ✓ | — | i testi | — | — |
| Piattaforme esterne (MioDottore, Treatwell…) | — | — | ✓ | — | — | — | — |
| Il proprio Google Calendar | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

### Telefono

| Capacità | Seg | Op | Man | Com | Mkt | Amm | Dir |
|---|---|---|---|---|---|---|---|
| Chiamare e usare il dialer | ✓ | ✓ | ✓ | ✓ | — | — | — |
| Registro delle chiamate | ✓ | le sue | ✓ | team | — | — | — |
| Ascoltare registrazioni e leggere trascrizioni | le sue | le sue | ✓ | le sue | — | — | — |
| Copioni di chiamata | li usa | li usa | li scrive | li usa | — | — | — |
| Segreteria telefonica, numeri, ID chiamante | — | — | ✓ | — | — | — | — |

### Marketing e automazioni

| Capacità | Seg | Op | Man | Com | Mkt | Amm | Dir |
|---|---|---|---|---|---|---|---|
| Vedere le automazioni | — | — | ✓ | vede | ✓ | — | — |
| Creare, modificare, attivare le automazioni | — | — | ✓ | — | ✓ | — | — |
| Passi che chiamano un indirizzo esterno (webhook) | — | — | — | — | — | — | — |
| Social: scrivere bozze | a scelta | — | ✓ | ✓ | ✓ | — | — |
| Social: approvare e pubblicare | — | — | ✓ | — | ✓ | — | — |
| Meta: pagine, moduli, spesa, qualità dei lead | — | — | ✓ | — | ✓ | — | — |
| Link tracciati e tracciamento | — | — | ✓ | — | ✓ | — | — |
| Moduli web per i lead | — | — | ✓ | — | ✓ | — | — |
| Liste e campagne, solo per chi ha il consenso | — | — | ✓ | — | ✓ | — | — |

I passi webhook li aggiunge solo l'agenzia: fanno chiamare al server un indirizzo
qualsiasi con i dati del record.

### Dashboard e numeri

| Capacità | Seg | Op | Man | Com | Mkt | Amm | Dir |
|---|---|---|---|---|---|---|---|
| Dashboard personali | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Creare e modificare le dashboard condivise | — | — | ✓ | — | quelle di marketing | — | — |
| Numeri operativi: arrivi, non presentati, attese | ✓ | i suoi | ✓ | team | — | — | ✓ |
| Numeri economici: fatturato, incassi, per operatore | — | i suoi | ✓ | — | — | ✓ | — |
| Numeri di marketing: spesa, costo per nuovo paziente | — | — | ✓ | — | ✓ | ✓ | — |
| Filtro per persona | — | — | ✓ | team | — | — | — |

### Fatturazione e Sistema TS

| Capacità | Seg | Op | Man | Com | Mkt | Amm | Dir |
|---|---|---|---|---|---|---|---|
| Vedere le fatture, anche nella cronologia della persona | ✓ | quelle delle sue prestazioni | ✓ | — | — | ✓ | — |
| Emettere, dall'appuntamento o nuove | ✓ | — | ✓ | — | — | ✓ | — |
| Registrare gli incassi | ✓ | — | ✓ | — | — | ✓ | — |
| Annullare, note di credito | — | — | ✓ | — | — | ✓ | — |
| Inviare allo SdI e al Sistema TS | a scelta | — | ✓ | — | — | ✓ | — |
| Esportare per il commercialista | — | — | ✓ | — | — | ✓ | — |
| Impostazioni fiscali: azienda, registro, servizi, erogatori, provider | — | — | ✓ | — | — | ✓ | — |

### Sito (solo dove c'è Frappe Builder)

| Capacità | Seg | Op | Man | Com | Mkt | Amm | Dir |
|---|---|---|---|---|---|---|---|
| Pagine e vetrina | — | — | ✓ | — | ✓ | — | — |
| Impostazioni del sito: nome, SEO, pixel, banner dei cookie | — | — | ✓ | — | ✓ | — | — |

### Utenti e impostazioni del centro

| Capacità | Seg | Op | Man | Com | Mkt | Amm | Dir |
|---|---|---|---|---|---|---|---|
| Profilo, preferenze, il proprio account email e la firma | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Utenti e livelli: invitare, cambiare livello, disattivare | — | — | ✓ | — | — | — | — |
| Gerarchia: l'albero e l'interruttore | — | — | ✓ | — | — | — | — |
| Marchio, impostazioni generali, calendario e promemoria | — | — | ✓ | — | — | — | — |
| Regole di assegnazione e SLA, senza codice | — | — | ✓ | — | — | — | — |
| Voci del menu utente, solo icone e indirizzi sicuri | — | — | ✓ | — | — | — | — |
| Account email del centro | — | — | ✓ | — | — | — | — |

Il Manager assegna tutti i livelli, ma mai System Manager, e non tocca gli utenti
dell'agenzia.

### Clinica (quando c'è il modulo)

| Capacità | Seg | Op | Man | Com | Mkt | Amm | Dir |
|---|---|---|---|---|---|---|---|
| Vedere la cartella | che c'è stata una visita | i suoi pazienti; tutti se c'è il consenso al dossier | — | — | — | — | ✓ |
| Scrivere e firmare visite e referti | — | i suoi pazienti | — | — | — | — | — |
| Rendere una voce visibile solo a sé o alla propria disciplina | — | ✓ | — | — | — | — | — |
| Aprire una cartella fuori équipe, scrivendo il motivo | — | ✓ | — | — | — | — | ✓ |
| Oscurare un episodio su richiesta del paziente | — | — | — | — | — | — | ✓ |
| Moduli da firmare e consensi: raccoglierli, vedere lo stato | ✓ | ✓ | vede lo stato | — | — | — | ✓ |
| Modelli clinici (builder) | — | — | — | — | — | — | ✓ |
| Moduli non clinici: privacy, contratti, preventivi | — | — | ✓ | — | — | — | ✓ |
| Piani: alimentazione, allenamento, esercizi | — | secondo la qualifica | — | — | — | — | vede |
| Pubblicare referti e documenti nell'area cliente | quelli amministrativi | i suoi | — | — | — | — | ✓ |
| Registro degli accessi alla cartella: chi e quando, non cosa | — | — | ✓ | — | — | — | ✓ |
| Concedere e revocare l'accesso di supporto all'agenzia | — | — | ✓ | — | — | — | ✓ |
| Usare l'assistente: dettatura, bozze | — | ✓ | lo attiva | — | — | — | ✓ |

### Area cliente (quando c'è)

| Capacità | Seg | Op | Man | Com | Mkt | Amm | Dir |
|---|---|---|---|---|---|---|---|
| Invitare il paziente nell'area | ✓ | ✓ | ✓ | — | — | — | — |
| Scrivere al paziente nell'area | messaggi amministrativi | ai suoi pazienti | ✓ | — | — | — | — |
| Sezioni, marchio e testi dell'area | — | — | ✓ | — | — | — | — |

## Le impostazioni, pagina per pagina

Oggi quasi tutto il modale si apre a chi è Manager. La proposta divide ogni pagina
fra quello che decide il centro e quello che resta all'agenzia.

| Gruppo › pagina | Oggi | Domani: il centro | Domani: resta all'agenzia |
|---|---|---|---|
| Profilo, Preferenze | tutti | tutti | — |
| Generali, Marchio, Calendario e promemoria | Manager | Man | — |
| Dashboard: previsioni, valuta, cambio | Manager | Man | la chiave del servizio di cambio |
| Predefiniti: valuta e formati del sito | Manager, ma è un documento del core per System Manager | — | tutta |
| Pipeline, Copioni di chiamata | Manager | Man | — |
| Utenti, Invita | Manager; Admin e Manager li dà solo System Manager | Man: tutti i livelli, mai System Manager | gli utenti dell'agenzia |
| Gerarchia | Manager guarda, System Manager modifica | Man | — |
| Email › Account | Manager, ma è un documento del core | Man, con un'API del CRM | server e porte, quando servono |
| Email › Modelli | tutti | Man, Mkt; tutti li usano | — |
| WhatsApp › Numeri, Modelli | Manager | Man; i modelli anche Mkt | app, webhook, ID (già così) |
| Regole di assegnazione, SLA | Manager | Man, con condizioni guidate | le condizioni scritte in Python |
| Moduli per i lead | Manager | Man, Mkt | l'accesso degli ospiti ai campi collegati (già così: System Manager, solo liste di valori) |
| Link tracciati, Tracciamento | Manager | Man, Mkt | lo script sul sito e quanto si tengono i dati |
| Fatturazione (sei pagine) | Manager, ma scrivono solo System Manager e Invoicing Manager | Man, Amm | i segreti del webhook del provider |
| Agenda: servizi, turni, orari, sale, listini | Manager | Man; turni, ferie e sale anche Seg | — |
| Prenotazione: online, pagina e regole | Manager | Man | — |
| Piattaforme di prenotazione | Manager; le beta solo System Manager | Man | token dei webhook, connettori in prova |
| Google Calendar | ognuno il suo | ognuno il suo | l'app OAuth |
| Social › Profili | Manager | Man, Mkt | — |
| Sito | Manager | Man, Mkt | domini e certificati |
| Voci del menu utente | Manager | Man, solo icone e indirizzi sicuri (già così) | — |
| Meta | Manager; la parte tecnica System Manager | Man, Mkt | app, webhook, log (già così) |
| Telefono | ognuno il suo; Manager il resto | ognuno il suo; Man segreteria, numeri, ID chiamante | chiavi di Twilio, Exotel e trascrizione, TwiML, SIP |
| ERPNext | Manager | — | tutta |
| Fuori dal modale: campi delle schede, viste pubbliche, filtri rapidi | Manager | Man | — |
| Script dei moduli (Form Script) | dal Desk | — | tutta |
| Importazione | la vedono tutti, funziona solo per Administrator | Man | — |
| Dati di prova | Manager | Man | — |
| Clinica: modelli, consensi, dossier, accessi (poi) | — | Dir; Man i moduli non clinici | — |
| Area cliente: sezioni e marchio (poi) | — | Man | il dominio |
| Assistente (poi) | — | Man lo accende | fornitore e regione |
| Firma avanzata (poi) | — | Man sceglie il fornitore | le credenziali |

## L'ambito: su quali record

- **Oggi** la regola c'è per persone e trattative: si vedono le proprie, le
  assegnate, le condivise e quelle del proprio sottoalbero nella gerarchia; il
  Sales Manager fuori dall'albero e il System Manager vedono tutto. Chiamate, note
  e task seguono il lead o la trattativa di cui parlano (29/09). Un'assegnazione
  chiusa continua a dare accesso: si esclude solo l'annullata.
- **Domani** gli ambiti sono tre:
  - **tutto il centro**: Segreteria, Manager, Amministrazione per quello che
    vedono, Direzione sanitaria per la clinica;
  - **team**: commerciali e responsabili, dalla gerarchia;
  - **suoi**: l'operatore vede le persone che hanno un appuntamento con lui, che
    gli sono assegnate o che ha in cura; il commerciale quelle assegnate.
- **Quello che è attaccato a una persona la segue.** Note, attività, chiamate con
  registrazioni e trascrizioni, appuntamenti, messaggi e fatture si vedono se si
  vede la persona e se il livello ha la capacità per quel tipo di dato. Chiamate,
  note e task lo fanno già, con i mattoni di `org_hierarchy.py` (una condizione
  sola per la lista e per il record); gli altri passano agli stessi mattoni.
- **La cartella clinica non segue la gerarchia.** Segue il rapporto di cura, il
  consenso al dossier, gli oscuramenti e l'apertura con motivo.
- Un'assegnazione chiusa non deve dare accesso per sempre.

## Il piano del centro: la seconda chiave

I centri comprano moduli, e un servizio dell'agenzia ne sblocca alcuni (la
segreteria sblocca il telefono, le campagne il marketing; i prezzi sono nel
[listino](../gestionale-medico/listino.md)). Quindi una capacità
vale se servono **due chiavi**: il modulo è attivo nel piano del centro, e il
livello della persona la prevede.

- **Il piano** sta in un documento solo per sito (per esempio `CRM Piano`). Dice:
  - la taglia, cioè quante agende. Un'agenda attiva è un professionista con almeno
    un appuntamento nel mese, anche se non entra mai nel CRM; sale, attrezzature e
    chi non riceve appuntamenti non contano;
  - i moduli attivi, e per ciascuno se lo paga il centro o se è incluso in un
    servizio dell'agenzia;
  - le date di prova e di scadenza.
  Lo scrive solo l'agenzia, o la sua console.
- **Ogni modulo, nel registro**, dice anche che cosa succede quando si spegne: i
  suoi dati restano e diventano di sola lettura, e automazioni e campagne si
  mettono in pausa. Non si cancella mai niente.
- **Un modulo spento** si vede con un lucchetto e "Attiva" nella pagina del piano e
  quando la pagina del modulo è vuota, non in ogni angolo del CRM.
- **Il centro può ampliare da solo.** "Attiva" apre subito una prova di 14 giorni e
  manda la richiesta all'agenzia, che la conferma e la fattura dal mese dopo. Il
  pagamento automatico (Stripe) si aggiunge solo se serve.
- **Un superamento della taglia non blocca mai niente.** Se le agende attive
  superano quelle della taglia, il CRM avvisa e propone la taglia sopra, ma
  appuntamenti e fatture funzionano.
- **Consumi**: il CRM conta agende attive, messaggi WhatsApp e SMS, minuti di
  telefono e firme avanzate, e li manda all'agenzia ogni mese per la fattura.
- **La console dell'agenzia** può essere il vostro CRM: i centri come
  organizzazioni, il piano come abbonamento, le fatture emesse con il modulo di
  fatturazione che c'è già.

## Come si costruisce

1. **Il registro**, `crm/permissions/livelli.py`. Ogni modulo lo chiama dal suo
   `registra()`, come la fatturazione fa oggi da `hooks.py`, e dichiara:
   - i suoi ruoli;
   - le capacità, ciascuna con i ruoli che la danno;
   - i livelli a cui vanno di serie;
   - le sue pagine di impostazioni, divise fra centro e agenzia;
   - le regole d'ambito dei suoi documenti;
   - il modulo del piano a cui appartiene, e cosa fa quando è spento.
2. **I livelli come Role Profile**, generati dal registro all'installazione e a
   ogni migrazione, senza doppioni. Frappe rifà i ruoli di un utente dai suoi
   profili a ogni salvataggio, quindi o si passa tutto dai livelli o non funziona.
   Sales User e Sales Manager restano come ruoli interni, perché il codice di
   Frappe CRM li usa, ma lo schermo non li mostra più.
3. **Sul server**, un decoratore `@richiede("fatture.emetti")` e una funzione
   `puo(utente, "…")` al posto delle 19 copie di `MANAGER_ROLES`, dei controlli
   scritti a mano e di `only_for`. `check_app_permission` accetta ogni livello del
   CRM, così chi fa solo amministrazione entra.
4. **I permessi dei documenti allineati alle capacità**:
   - nessuno scrive con l'API quello che lo schermo non gli fa fare (servizi,
     listini, turni, fasi, modelli…);
   - il Sales User non legge più le fatture;
   - SMS, messaggi WhatsApp, appuntamenti e tracciamento seguono la persona.
   I segreti sono già campi Password dal 29/09.
5. **Nel frontend**, l'avvio manda l'elenco delle capacità dell'utente.
   - `users.js` offre `puo('…')`, al posto delle 63 chiamate a `isManager()` e delle
     9 a `isAdmin()`.
   - Le rotte dichiarano cosa richiedono (`meta.richiede`), così una pagina nascosta
     non si apre più dall'indirizzo.
   - Le pagine delle impostazioni fanno lo stesso.
6. **La pagina Utenti** assegna uno o più livelli per persona e invita per livello.
   Gli utenti dell'agenzia sono in sola lettura. Sparisce il blocco dei moduli che
   oggi toglie la fatturazione a chi è Sales User.
7. **Il passaggio degli utenti di oggi**:
   - System Manager del centro → Manager amministrativo;
   - Sales Manager → Manager amministrativo;
   - Sales User → Segreteria, da verificare sito per sito;
   - Invoicing Manager → Amministrazione.
8. **I test**: il registro si prova senza sito, con `unittest`; per ogni livello un
   test sulle funzioni principali.

**Le PR, in ordine:**

| PR | Cosa | sp |
|---|---|---|
| 0 | I quattro problemi di sicurezza, ognuno a parte | ✅ fatto, 29/09 |
| 1 | Registro con le due chiavi (livello e piano), livelli, pagina Utenti e inviti, passaggio degli utenti | ✅ fatto, 29/09 |
| 2 | Permessi dei documenti allineati; l'ambito che segue la persona, anche per SMS, WhatsApp e appuntamenti | 1 |
| 3 | Capacità nel frontend, rotte protette, impostazioni divise | 0,5–1 |
| 4 | I livelli facoltativi: Commerciale, Marketing, Amministrazione, Sola lettura | 0,5 |

Direzione sanitaria arriva con la clinica.

## La PR 1, com'è fatta

**Il registro** sta in `crm/permissions/livelli.py`: moduli del piano, livelli,
ruoli, capacità con l'ambito che ogni livello riceve. Il calcolo (`calcola`) è puro
e la matrice di questo documento si prova senza sito (`test_livelli.py`, 37 test).
Ogni modulo registra la sua parte:

- il CRM in `crm/permissions/catalogo.py`: i moduli Base, Marketing e Telefono, i
  livelli di base e le capacità di persone, trattative, conversazioni, agenda,
  telefono, marketing, cruscotti e impostazioni;
- la fatturazione in `crm/invoicing/capacita.py`: i suoi due ruoli e le capacità
  `fatture.*`. Il CRM non nomina mai una capacità della fatturazione.

Il codice chiede `puo("fatture.emetti")`, o mette `@richiede(...)` sopra un metodo
whitelisted; il frontend riceve capacità e ambiti con la pagina
(`window.crm_permissions`) e chiede `puo()` allo store degli utenti.

**I livelli**, come Role Profile con il prefisso `CRM `, così il CRM riscrive solo i
profili suoi:

| Livello | Profilo | Ruoli |
|---|---|---|
| Segreteria | CRM Front Desk | Sales User, Front Desk, Invoicing User |
| Operatore | CRM Practitioner | Sales User, Practitioner |
| Manager amministrativo | CRM Manager | Sales User, Sales Manager, Invoicing Manager, Invoicing User |
| Commerciale (facoltativo) | CRM Sales | Sales User |

Front Desk e Practitioner sono ruoli nuovi e per ora non portano permessi sui
documenti: distinguono i livelli nelle capacità. I permessi dei documenti si
allineano nella PR 2. Marketing, Amministrazione e Sola lettura arrivano con la PR 4
(il registro sa già togliere le scritture a chi ha Sola lettura); Direzione
sanitaria con la clinica.

**Le capacità "a scelta"** (prenotare sopra un conflitto, inviare allo SdI e al
Sistema TS, scrivere bozze social per la segreteria) non sono ruoli: Frappe rifà i
ruoli dai profili a ogni salvataggio e un ruolo messo a mano sparirebbe. Stanno in
`CRM User Capability`, una riga per persona e capacità, e il Manager le accende
dalla finestra Accesso della persona.

**Il piano** è `CRM Plan`, un documento solo, scritto solo dall'agenzia. Un modulo
che il piano non elenca tiene il suo predefinito: quello che il CRM faceva già
(Base, Marketing, Telefono) resta acceso, un modulo nuovo (la Clinica) nasce spento.
Un modulo finito, prova scaduta o abbonamento chiuso, diventa di sola lettura: i
dati restano, le scritture no. In Impostazioni › Piano il Manager vede taglia,
agende attive del mese, moduli e consumi, e fa partire da solo 14 giorni di prova di
un modulo che non ha: la richiesta va all'agenzia per email.

**Gli utenti.** La pagina Utenti mostra i livelli di ognuno e li cambia dalla
finestra Accesso; l'invito e "Aggiungi utente esistente" scelgono i livelli. Il
Manager dà ogni livello, anche Manager, ma non tocca gli utenti dell'agenzia e non
si toglie il livello Manager da solo. `update_user_role` resta per chi lo chiama
ancora e dà il livello che corrisponde al ruolo; System Manager resta dell'agenzia.

**Il passaggio degli utenti di prima** (patch `give_users_their_levels`):

- Sales Manager diventa Manager amministrativo;
- Sales User diventa Segreteria, oppure Commerciale se il sito ha la gerarchia di
  vendita accesa: lì le persone devono vedere solo il loro team;
- System Manager non si tocca: è l'agenzia;
- non si tocca nemmeno chi ha un ruolo di un'altra app, o un ruolo che i livelli
  scelti non portano (un Sales User che era anche Invoicing Manager): con i profili
  Frappe glielo toglierebbe. Chi resta così conta per i livelli che i suoi ruoli
  implicano (Sales Manager → Manager, Sales User → Commerciale), e la pagina Utenti
  li mostra in corsivo finché qualcuno non sceglie i livelli.

Da verificare sito per sito, come diceva il passaggio qui sopra.

**Le 19 copie di `MANAGER_ROLES`** sono diventate capacità con un nome: servizi,
listini e regole dello studio (`agenda.configura`), turni e sale (`agenda.turni`,
che adesso ha anche la Segreteria), prenotazione online, piattaforme, automazioni,
pipeline, copioni, social, sito, moduli per i lead, tracciamento, viste, regole di
assegnazione, Meta, numeri e modelli WhatsApp, Google Calendar, cruscotti condivisi.
Per chi ha i ruoli di prima le risposte non cambiano. Resta ERPNext, che passa
all'agenzia con la PR 3 insieme alla sua pagina delle impostazioni.

**Un bug trovato strada facendo.** Fuori dal developer mode Frappe tiene gli hook
nella sua cache, e un processo che li trova lì non importa mai `crm/hooks.py`:
lì stava la sola registrazione dei moduli. In quei processi "fisioterapista" non
era nel registro delle qualifiche e i controlli del Sistema TS non giravano.
Adesso registra tutto `crm/registrazione.py`, anche da `before_request` e
`before_job`.

## Da decidere

1. I tre livelli di base e i nomi: Segreteria, Operatore, Manager amministrativo?
2. L'operatore vede solo i suoi pazienti, o tutti finché non c'è il consenso al
   dossier?
3. La segreteria può inviare allo SdI e al Sistema TS, annullare fatture, eliminare
   appuntamenti?
4. Le registrazioni delle chiamate: oggi le sente chi vede il lead o la
   trattativa. Basta così, o solo chi ha chiamato e il Manager?
5. I numeri economici: solo Manager e Amministrazione? L'operatore vede i suoi?
6. Il marketing lavora solo con i dati mascherati e senza leggere le conversazioni?
7. Nei centri medici serve il livello Commerciale?
8. Sola lettura nella prima PR o dopo?
9. L'agenzia vede il non clinico per l'assistenza come oggi, o anche quello solo con
   un accesso a tempo?
