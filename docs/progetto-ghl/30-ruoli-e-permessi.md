# 30 — Ruoli e permessi: chi può fare cosa, modulo per modulo

**Stato:** 🟢 PR 1 fatta (29/09/2026): registro, livelli di base, piano, pagina
Utenti e inviti per livello, passaggio degli utenti di prima
([com'è fatta](#la-pr-1-comè-fatta)). Della PR 2 sono fatte le fatture: il Sales
User non le legge più, l'Operatore legge quelle delle sue prestazioni, la Segreteria
le emette e le trasmette solo se il Manager glielo permette. Il resto delle PR 2–4
resta da fare. Lo stato "di oggi" qui sotto è quello verificato prima della PR 1,
sul commit `151cba6`.

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
- **I tre punti rimasti aperti sono chiusi dalla [PR 2](#la-pr-2-comè-fatta)**
  (29/09): quello che ogni Sales User leggeva e scriveva (due punti sopra); il
  calendario, che dava nome, email e telefono di tutti i partecipanti di ogni
  appuntamento e ora dà a chi vede solo parte dell'agenda il resto come tempo
  occupato; `create_deal`, che salvava con `ignore_permissions`.

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
| Consensi: vedere lo stato, registrare una risposta o una revoca (dal 29/09/2026) | ✓ | suoi | ✓ | team | — | — | ✓ |
| Tipi di consenso e i loro testi | — | — | ✓ | — | — | — | — |

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
| Sapere chi è paziente, da quando e perché; segnarlo a mano (dal 29/09/2026) | ✓ | i suoi | ✓ | — | — | — | ✓ |
| Ritrovare i pazienti negli appuntamenti e nelle fatture di prima | — | — | ✓ | — | — | — | ✓ |
| Modelli clinici (builder) | — | — | — | — | — | — | ✓ |
| Moduli non clinici: privacy, contratti, preventivi | — | — | ✓ | — | — | — | ✓ |
| Piani: alimentazione, allenamento, esercizi | — | secondo la qualifica | — | — | — | — | vede |
| Pubblicare referti e documenti nell'area cliente | quelli amministrativi | i suoi | — | — | — | — | ✓ |
| Registro degli accessi alla cartella: chi e quando, non cosa | — | — | ✓ | — | — | — | ✓ |
| Concedere e revocare l'accesso di supporto all'agenzia | — | — | ✓ | — | — | — | ✓ |
| Usare l'assistente: dettatura, bozze | — | ✓ | lo attiva | — | — | — | ✓ |

Dal 29/09/2026 ci sono la scheda paziente e la cartella semplice: `pazienti.vedi`,
`pazienti.segna`, `pazienti.recupera`, `clinica.vedi`, `clinica.scrivi`,
`clinica.traccia` ("che c'è stata una visita") e `clinica.accessi`, nel modulo "clinica"
del piano; il livello Direzione sanitaria viene dalla clinica (`crm/clinica/__init__.py`).
Dal 30/09/2026 anche:

- `clinica.archivia`: aggiungere documenti all'archivio. La segreteria per un
  operatore, l'operatore per i suoi pazienti.
- `clinica.oscura`: oscurare un episodio su richiesta del paziente. Solo la
  direzione.
- `clinica.fuori_equipe`: aprire una cartella fuori équipe scrivendo il motivo.
  L'operatore.
- `clinica.consegna`: consegnare un referto al paziente, a mano o online per 45
  giorni. L'operatore i suoi, la direzione tutti.
- `area.invita`: aprire l'area del paziente alla persona, o a chi risponde per
  lei, e chiuderla. La segreteria, l'operatore per i suoi, il manager e la
  direzione.
- `area.messaggi`: scrivere alla persona nella sua area. La segreteria per
  l'amministrazione, l'operatore per i suoi e della cura, la direzione.
- `piani.scrivi`: scrivere e pubblicare i piani (dieta, allenamento, esercizi a
  casa, abitudini) dei tipi che la propria qualifica consente. L'operatore, per
  i suoi.

Il paziente non è un livello: entra nell'area come utente del sito con il ruolo
"Clinic Patient", mai nel CRM.

La visibilità "la propria disciplina" è una scelta dell'operatore sulla sua voce
(`crm/clinica/dossier.py`).

### Area cliente (quando c'è)

| Capacità | Seg | Op | Man | Com | Mkt | Amm | Dir |
|---|---|---|---|---|---|---|---|
| Invitare il paziente nell'area | ✓ | ✓ | ✓ | — | — | — | — |
| Scrivere al paziente nell'area | messaggi amministrativi | ai suoi pazienti | ✓ | — | — | — | — |
| Sezioni, marchio e testi dell'area | — | — | ✓ | — | — | — | — |

### Assistente (quando c'è)

Un modulo del piano a sé, `assistente`, spento finché l'agenzia non lo accende
(`crm/assistente/__init__.py`).

| Capacità | Seg | Op | Man | Com | Mkt | Amm | Dir |
|---|---|---|---|---|---|---|---|
| Dal modulo di carta: il PDF diventa una bozza di modello (`assistente.moduli`) | — | — | ✓ | — | — | — | — |
| Leggere il registro dell'assistente (`assistente.registro`) | — | — | ✓ | — | — | — | — |
| Bozze dalla propria nota, visita dettata, riassunto prima della visita (`assistente.bozze`) | — | ai suoi pazienti | — | — | — | — | — |
| Leggere gli eventi clinici del registro (`assistente.registro_clinico`) | — | — | — | — | — | — | ✓ |

- Dove gira il modello è dell'agenzia: fornitore, indirizzo, modello, chiave,
  regione e il contratto senza conservazione né addestramento stanno sul
  permlevel 1 di `CRM Assistant Settings`, visti con `tecnico.integrazioni`.
- Se usarlo, e per quali funzioni, lo decide il manager.
- Ogni funzione dice chi la usa e chi legge i suoi eventi: quelle cliniche li
  fanno leggere solo alla direzione sanitaria.
- Le funzioni cliniche chiedono anche il consenso del paziente all'assistente
  (`ai_assistant`).

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

- **Prima della PR 2** la regola c'era per persone e trattative: si vedevano le
  proprie, le assegnate, le condivise e quelle del proprio sottoalbero nella
  gerarchia; il Sales Manager fuori dall'albero e il System Manager vedevano tutto.
  Chiamate, note e task seguivano il lead o la trattativa (29/09). Un'assegnazione
  chiusa continuava a dare accesso: si escludeva solo l'annullata.
- **Dalla PR 2** (29/09) gli ambiti sono tre, e li dice il livello:
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
- Un'assegnazione chiusa non dà accesso per sempre: 90 giorni dopo la chiusura.

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
| 2 | Permessi dei documenti allineati; l'ambito che segue la persona, anche per SMS, WhatsApp e appuntamenti | ✅ fatto, 29/09 |
| 3 | Capacità nel frontend, rotte protette, impostazioni divise | ✅ fatto, 29/09 |
| 3b | Le pagine del Manager che scrivono documenti del core: account e modelli email, regole di assegnazione, importazione | ✅ fatto, 29/09 |
| 4 | I livelli facoltativi: Commerciale, Marketing, Amministrazione, Sola lettura | ✅ fatto, 29/09 |

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
si toglie il livello Manager da solo. A chi ha un ruolo di un'altra app un livello
non si dà: con i profili Frappe glielo toglierebbe, e il CRM lo dice invece di
farlo. `update_user_role` resta per chi lo chiama
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

## La PR 2, com'è fatta

**L'ambito lo dice il livello.** `crm/permissions/org_hierarchy.py` chiede la
capacità che mostra le persone (`persone.vedi`) o le trattative
(`trattative.vedi`) e ne legge l'ambito:

- **tutto il centro**: Segreteria, Manager, Direzione sanitaria. La segreteria prima
  vedeva solo le persone sue o assegnate, e non vedeva nemmeno quelle che creava;
- **team**: il Commerciale, con la gerarchia di vendita; senza, le sue;
- **suoi**: l'Operatore, cioè le persone assegnate a lui e quelle **che ha in cura**.
  Sono chi ha un appuntamento con lui e quello che un modulo aggiunge con l'hook
  `crm_people_in_care`: la clinica aggiunge i pazienti per cui ha scritto in
  cartella. Il CRM non sa niente della clinica.

**Un posto nella gerarchia restringe.** Chi sta nell'albero vede il suo team, qualunque
sia il livello: il responsabile, come il Sales Manager di prima. Chi lavora dal Desk
solo con i ruoli, fuori dai livelli, tiene la regola di prima. L'ambito si calcola
una volta per richiesta.

**Quello che è di una persona la segue** (`crm/permissions/seguono.py`, con i mattoni
di `org_hierarchy`: una condizione sola per la lista e per il record):

- **gli appuntamenti**, con l'ambito di `agenda.vedi`:
  - tutto il centro per Segreteria e Manager;
  - per l'Operatore quelli che lavora o che ha prenotato. Prenota solo nella sua
    agenda;
  - per il Commerciale quelli delle sue persone. Il resto dell'agenda il
    calendario lo mostra come **tempo occupato** (quando, chi lo lavora, quale sala,
    mai chi viene né perché), nelle due viste.
  Eliminare un appuntamento chiede `agenda.elimina`, del Manager;
- **i messaggi WhatsApp e gli SMS** a chi può conversare, sulle persone che vede; un
  messaggio che non è di nessuno è di tutti quelli che conversano, come una
  chiamata. La Direzione sanitaria non conversa e non li legge;
- **il tracciamento** (visitatori ed eventi) sulle persone che si vedono; il
  traffico che non è ancora di nessuno a chi gestisce il tracciamento;
- **le prenotazioni delle vecchie pagine** a chi le ha ricevute o vede la persona.

**Quello che lo schermo tiene al Manager, il server lo chiede alla capacità**
(`crm/permissions/documenti.py`). Si scrive solo con la capacità della pagina:

- servizi, prezzi, listini, impostazioni dell'agenda e festività: `agenda.configura`;
- turni e sale: `agenda.turni`, la Segreteria per tutti, l'Operatore i suoi turni;
- calendari di prenotazione: `prenotazione_online.configura`;
- stati e fasi della pipeline: `pipeline.configura`;
- viste pubbliche: `viste.configura`; le proprie restano di ognuno;
- modelli e impostazioni WhatsApp: `modelli_messaggio.gestisci` e `canali.configura`;
- il telefono degli altri: `telefono.configura`; il proprio è di ognuno.

Leggere non cambia, e chi è fuori dai livelli tiene i permessi dei suoi ruoli.

**Il resto:**
- un'assegnazione chiusa apre il record per 90 giorni, poi non più;
- `create_deal` inserisce la trattativa come l'utente, con i permessi per campo, e
  non la apre su una persona o un'organizzazione che l'utente non vede.

## La PR 3, com'è fatta

**Lo schermo chiede la capacità.** Menu, pagine e pulsanti chiedono `puo('…')`
allo store degli utenti; `isManager()`, `isAdmin()` e `isSalesUser()` non ci sono
più. Le rotte dichiarano `meta.richiede` e la guardia del router lo controlla: una
pagina che il menu non mostra non si apre nemmeno dall'indirizzo, e si torna alla
prima pagina che il livello apre (persone, agenda, conversazioni, fatture…). Anche
la vista predefinita di un utente non porta più su una pagina che il suo livello non
apre.

**Ogni pagina delle impostazioni ha la sua capacità**, quella della tabella qui sopra:
un gruppo compare se almeno una sua pagina compare. La Segreteria trova Profilo,
Preferenze, turni e sale, Google Calendar e il suo telefono; l'Operatore i suoi
turni ma non le sale, che sono di tutto il centro. La Gerarchia ora la costruisce il
Manager (`gerarchia.gestisci`), non più System Manager, e mostra i livelli al posto
di Sales Manager e Sales User.

**La parte dell'agenzia** di una pagina sta su un livello di permesso a parte
(permlevel 1, solo System Manager) e si vede con `tecnico.integrazioni`:

- **Cruscotto**: la chiave del servizio di cambio. Il provider lo sceglie il centro;
- **Telefono**: le credenziali di Twilio ed Exotel, l'app TwiML, i trunk SIP, il
  test della connessione, e collegare o scollegare il provider. Al centro restano la
  registrazione delle chiamate con il suo avviso e gli ID chiamante;
- **Trascrizione**: l'indirizzo del servizio, la chiave, il modello e i limiti. Il
  centro la accende, sceglie lingua, vocabolario e per quanto si tengono le
  trascrizioni; se il servizio manca, glielo dice ("l'agenzia deve prima
  configurarlo");
- **Tracciamento**: lo script da mettere sul sito, i siti che possono mandare dati,
  gli indirizzi esclusi e quanto si tiene la navigazione anonima. Al centro restano
  i numeri e gli interruttori;
- **Fatturazione, connessione al provider**: generare e ruotare il segreto del
  webhook;
- **ERPNext** e **Predefiniti** (valuta e formati del sito): tutta la pagina. ERPNext
  lo scrive solo `tecnico.erpnext`, anche dall'API.

Il livello di permesso fa due cose: la copia delle impostazioni che arriva al Manager
non ha quei valori, e un suo salvataggio li lascia com'erano. Non copre
`frappe.client.get_value` sui documenti singoli, che guarda il documento e non il
campo: per questo i segreti restano anche campi Password, mascherati per tutti.

**Diverso da come era scritto.** L'indirizzo del webhook delle piattaforme di
prenotazione resta al Manager: è quello che si incolla nella piattaforma, e senza
non si finisce di collegarla. Le condizioni delle regole di assegnazione scritte in
Python restano dal Desk come prima: lo schermo le costruisce guidate.

**Rimasto per la PR 3b** (fatta, sotto). Account email, modelli email, regole di
assegnazione, importazione: lo schermo le dava al Manager, ma sono documenti del
core che Frappe dà solo a System Manager, e il server li rifiutava. Gli SLA sono un
documento del CRM e il Manager li scriveva già: ora chiedono `assegnazione.regole`.

## La PR 3b, com'è fatta

Quattro pagine che lo schermo dà al Manager scrivevano documenti del core, che
Frappe dà solo a System Manager: il server rispondeva di no.

- **Modelli email, regole di assegnazione, importazione.** Un ruolo porta la regola
  sul documento (Sales User per i modelli, Sales Manager per le regole e le
  importazioni), messa una volta sola da `concedi_documenti_del_core` a ogni
  migrazione, e la capacità della pagina la restringe come per gli altri documenti
  del Manager (`modelli_messaggio.gestisci`, `assegnazione.regole`,
  `persone.importa`). I modelli li leggono tutti, come prima.
- **L'importazione** si fermava anche su un'altra porta: nessun ruolo aveva il
  permesso "import" su persone, trattative, organizzazioni, attività e chiamate.
  Ora ce l'hanno Sales Manager e System Manager, e un test porta un CSV fino alle
  persone create.
- **Gli account email** passano da API del CRM con `email.account_centro`: elenco
  senza password né chiavi, aggiunta e modifica solo con i provider che la pagina
  offre. Un account con server e porte suoi resta all'agenzia, dal Desk. Il profilo
  di ognuno e le piattaforme di prenotazione scelgono un account da un elenco di
  soli nomi e indirizzi, che ora funziona anche per chi non è System Manager.
- **Le condizioni scritte in Python restano all'agenzia** (`tecnico.codice`). Lo
  schermo delle regole di assegnazione e degli SLA costruisce condizioni guidate e
  mandava anche il Python che il browser ne ricavava: chiunque salvasse una regola
  poteva metterci qualsiasi Python. Ora per chi non è l'agenzia il server riscrive
  il Python dalle condizioni guidate prima che qualcosa lo valuti
  (`crm/permissions/condizioni.py`, puro, con i suoi test), e rifiuta quello che lo
  schermo non sa costruire: campi che il documento non ha, operatori che non offre,
  qualcosa di diverso da `and` e `or` fra due condizioni. Una condizione che
  l'agenzia ha scritto dal Desk resta com'è, e il Manager può ancora spegnere la
  regola. Le regole valgono per persone e trattative.
- **Il segreto del webhook della fatturazione** chiede `fatture.segreti`, la
  capacità tecnica che la fatturazione aveva già, al posto di `tecnico.integrazioni`:
  il CRM non la nomina, la fatturazione non nomina quelle del CRM.

## La PR 4, com'è fatta

**Tre livelli nuovi**, facoltativi come il Commerciale:

- **Marketing** (profilo `CRM Marketing`, si offre dove il piano ha il modulo
  Marketing): automazioni, social, Meta, tracciamento, moduli, campagne, modelli di
  messaggio, sito, numeri di marketing. Vede persone e trattative **con email e
  telefoni mascherati**, e non legge conversazioni, chiamate, note, agenda,
  consensi né fatture. Ha un ruolo suo, `Marketing`, che sui documenti del
  marketing ha gli stessi diritti del Sales Manager;
- **Amministrazione** (`CRM Accounting`): tutta la colonna della fatturazione,
  i dati fiscali delle persone, persone, trattative e agenda da leggere, i numeri
  economici e di marketing;
- **Sola lettura** (`CRM Read Only`): si aggiunge a un altro livello e non porta
  ruoli. Il registro gli toglie le capacità che scrivono, e un hook su ogni
  documento gli nega creare, modificare, eliminare e condividere, anche con l'API;
  restano le proprie notifiche e il proprio profilo. Da sola non si può dare.

**La maschera è quella di Frappe.** Email, cellulare e telefono di persone e
trattative hanno la proprietà `mask`, e li vede in chiaro solo chi ha il ruolo
`Contact Details`: ogni livello lo porta, tranne Marketing e Sola lettura (il
registro lo aggiunge da sé, `Livello.recapiti`). Frappe maschera la scheda, le
liste, le esportazioni e i valori nei cambi della cronologia; un salvataggio non
riscrive mai la maschera al posto del valore. Chi lavorava fuori dai livelli, con i
ruoli di prima, riceve il ruolo con la migrazione e a ogni salvataggio: vedeva i
recapiti e continua a vederli.

**Cosa non maschera, e perché va bene.** Le letture del server
(`frappe.db.get_value`, `frappe.get_all`) restano in chiaro: webhook, automazioni e
invii leggono i numeri veri. Il ruolo Guest non serve a distinguerle: ce l'hanno
tutti gli utenti collegati. Per prudenza il numero di un invio WhatsApp si legge
con `crm.utils.stored_value`, che non passa da nessuna maschera. La rubrica del
core (Contact) non si maschera, perché la regola varrebbe per tutto il sito: a chi
vede le persone mascherate è negata del tutto.

**Scrivere chiede la capacità, non basta vedere.** Tutti i livelli hanno Sales
User, e Sales User può scrivere ed eliminare persone e trattative: una persona si
crea e si modifica con `persone.scrivi`, si elimina con `persone.elimina` (il
Manager); una trattativa con `trattative.scrivi`. Prima la Direzione sanitaria
poteva modificare o eliminare una persona dall'API, e leggeva chiamate e note: non
più.

**Leggere ha la sua capacità, come per persone e trattative.** Email, WhatsApp e
SMS si leggono con `conversazioni.vedi` e si scrivono con `conversazioni.usa`; le
note, e i commenti interni della cronologia, si leggono con `note.vedi` e si
scrivono con `note.scrivi`; le chiamate si leggono con `telefono.registro`. Così la
Sola lettura, che perde le capacità che scrivono, legge quello che legge il suo
livello. Rispondere su una persona o una trattativa chiede di conversare e di
vederla, non di poterla modificare: l'Operatore risponde sulle sue trattative, che
non modifica. Mandare un'email dalla scheda chiede `conversazioni.usa` anche
all'API (il permesso "email" di Frappe).

**Lo schermo chiede al server.** La scheda di una persona o di una trattativa chiede
i permessi a `crm.api.doc.get_doc_permissions`, che per ogni scrittura interroga
anche i controller: `frappe.client.get_doc_permissions` rispondeva con i soli ruoli.
Chi non può modificare trova i campi in sola lettura e niente pulsanti che il
server rifiuterebbe: arricchire, allegare, cambiare l'immagine, aprire una
trattativa, cambiare fase o pipeline, aggiungere un contatto. Il menu "Nuovo" offre
solo quello che il livello può fare: scrivere a qualcuno, un evento o un
appuntamento (`agenda.prenota`), registrare una chiamata (`telefono.chiama`), una
nota, un task (non in Sola lettura). I pulsanti di chiamata si vedono con
`telefono.chiama`; i filtri dei canali della cronologia (email, chiamate, commenti)
e i passi del "Getting started" solo a chi li legge o li può fare.

**Leggere i numeri non è fare dashboard.** Vedere i numeri del centro e le dashboard
del Manager è `dashboard.centro`, che non scrive; condividere e modificare quelle del
team resta `dashboard.condivise`, farne di proprie `dashboard.personali`. Così la
Sola lettura apre la dashboard (e un Manager in sola lettura tiene i suoi numeri)
senza crearne. La pagina delle fatture è il registro del centro: la apre chi vede
le fatture di tutto il centro (`fatture.vedi` con ambito centro, la Sola lettura
compresa), e "Nuova fattura" e la coda da fatturare restano a chi emette. Una rotta
può chiedere l'ambito di una capacità (`meta.ambito`), come il menu.

**Assegnare chiede `persone.assegna`.** Frappe lascia assegnare a chiunque legga il
documento: le sue chiamate `frappe.desk.form.assign_to.*` passano dal CRM
(`override_whitelisted_methods`), che per persone e trattative chiede la capacità.
Le regole di assegnazione chiamano le funzioni di Frappe direttamente, e restano
come sono. Chi non assegna vede a chi è assegnata, senza poterlo cambiare.

**Condiviso non vuol dire modificabile.** Il CRM condivide ogni persona e trattativa
con il suo proprietario, in scrittura, e Frappe concede quello che è condiviso senza
chiedere agli hook dei controller. Un salvataggio fatto per conto dell'utente (non
quelli del server, con `ignore_permissions`) chiede quindi di nuovo: la capacità per
persone, trattative e note, la Sola lettura per ogni documento.

**Rimasto fuori.** Esportare solo chi ha il consenso (per ora il Marketing esporta
mascherato), i testi della pagina `/prenota` e le dashboard condivise "di
marketing": servono pezzi che non ci sono ancora, e il Manager li tiene. La casella
delle conversazioni resta a chi risponde (`conversazioni.usa`): la Sola lettura
legge le conversazioni dalla scheda della persona. Un ToDo scritto a mano con l'API
assegna senza passare da `persone.assegna`: le regole di assegnazione scrivono i
ToDo allo stesso modo, e un controllo lì le fermerebbe.

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
   Per ora sì (PR 4): si cambia togliendo o dando il ruolo `Contact Details`.
7. Nei centri medici serve il livello Commerciale?
8. Sola lettura nella prima PR o dopo? Arrivata con la PR 4.
9. L'agenzia vede il non clinico per l'assistenza come oggi, o anche quello solo con
   un accesso a tempo?
