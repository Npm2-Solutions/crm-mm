# Requisiti del gestionale: cosa vogliamo, e cosa c'è già

**Stato:** 📝 annotati il 25/09/2026, da verificare insieme. Per ogni richiesta:
cosa c'è oggi nel codice (verificato su `develop` dopo la PR #102), cosa manca,
come lo farei e cosa resta da decidere. Il quadro generale è nella
[proposta](./README.md).

| # | Richiesta | Oggi | Dove va |
|---|---|---|---|
| 1 | Tre livelli: Segreteria, Manager amministrativo, Operatore; System Manager e Administrator solo a chi gestisce il site | ⚠️ tre livelli ci sono, ma sono di vendita, e il più alto **è** System Manager | fase 0 |
| 2 | Senza Frappe Builder la parte Sito sparisce | ❌ la voce resta visibile ai manager | fase 0 |
| 3 | Cartella clinica completa per paziente | ❌ niente | fasi 0 e 2 |
| 4 | Modulistica da un builder del CRM, con la firma come componente, privacy compresa | ⚠️ un builder c'è, ma per i lead; la firma è esclusa | fase 2 |
| 5 | Archivio di referti e documenti del cliente | ⚠️ allegati privati sulla persona, senza tipi né registro accessi | fase 2 |
| 6 | Area cliente: piani (nutrizione, dieta, allenamento), appuntamenti, comunicazioni del medico | ❌ niente, solo il link per spostare o annullare in `/prenota` | fase 3 |

---

## 1. Tre livelli, e il site resta vostro

**Richiesta.** Nel CRM, in generale, tre livelli: **Segreteria**, **Manager
amministrativo**, **Operatore**. Il sistema è un gestionale, quindi System Manager
e Administrator sono riservati a chi gestisce il site di quel cliente, cioè
l'agenzia. Serve una gestione dei ruoli propria del CRM.

**Oggi (verificato).**

- I livelli sono tre, ma sono quelli della vendita: *Admin*, *Manager*, *Sales
  User* (`frontend/src/components/Settings/Users.vue`, `InviteUserPage.vue`).
- **L'Admin del CRM è System Manager.** `crm/api/user.py:update_user_role` accetta
  solo System Manager, Sales Manager e Sales User, e l'invito offre gli stessi tre
  (`CRM Invitation.role`). Per dare al titolare di un centro il livello più alto del
  CRM oggi gli si dà il ruolo che amministra il site.
- **Solo un System Manager può nominare un Manager** (`update_user_role`): il
  responsabile del centro non può promuovere nessuno senza di voi.
- Il frontend decide con `isAdmin()` (System Manager) e `isManager()` (Sales
  Manager o System Manager) in `frontend/src/stores/users.js`. Il backend ha
  l'insieme `MANAGER_ROLES` copiato in **16 file**.
- Per entrare nel CRM serve Sales User, Sales Manager o System Manager
  (`crm.api.check_app_permission`). La fatturazione ha i suoi ruoli, Invoicing
  Manager e Invoicing User, ma Sales User può leggere ed esportare tutte le
  fatture, e dalla PR #101 la cronologia della persona le mostra a chiunque apra
  la scheda (`invoices_on` in `crm/api/activities.py` usa `frappe.get_all`, che
  salta i permessi). Mostra intestazione, importi e stati, non le righe.

**Proposta.**

| Livello | Chi | Cosa fa | Cosa non fa |
|---|---|---|---|
| **Segreteria** | chi sta al banco e al telefono | agenda di tutti, persone, conversazioni, accettazione, fatture, moduli da far firmare | non legge la cartella clinica |
| **Manager amministrativo** | titolare o responsabile del centro | tutto il CRM del centro: impostazioni, utenti e livelli, listini, fatturazione, dashboard | non tocca il site (integrazioni tecniche, chiavi, domini, app installate) |
| **Operatore** | medico, nutrizionista, fisioterapista, trainer | la sua agenda, i suoi pazienti, la cartella, i piani, le comunicazioni ai suoi pazienti | non vede le impostazioni né i numeri del centro |
| *Agenzia* | voi: System Manager e Administrator | il site | — |

- **Un livello è un Role Profile di Frappe**, cioè un pacchetto di ruoli. La v16
  permette più profili per utente (`User.role_profiles`), che è esattamente il
  titolare che visita: *Manager amministrativo* più *Operatore*. Il CRM mostra e
  assegna **livelli**, mai ruoli.
- **O tutto dai livelli, o niente**: a ogni salvataggio dell'utente Frappe rifà i
  ruoli dai profili (`populate_role_profile_roles` in `user.py`), e un ruolo messo
  a mano sparisce. Gli utenti dell'agenzia quindi non hanno profili del centro, e
  il CRM rifiuta un profilo che contenga System Manager. Il CRM lo sa già in parte:
  `remove_crm_roles_from_user` non tocca chi ha un profilo
  ([ricerca per il design §5](./ricerca-design.md#5-i-mattoni-frappe)).
- **Sotto, i ruoli restano capacità**: quelli che ci sono (Sales User, Sales
  Manager, Invoicing Manager…) più quelli nuovi (per esempio *CRM Admin* al posto
  di System Manager nei controlli del CRM, e un ruolo clinico per l'operatore).
- **Un solo posto decide chi può cosa**: un modulo (per esempio
  `crm/permissions/livelli.py`) al posto delle 16 copie di `MANAGER_ROLES`, e un
  livello calcolato dal server che il frontend legge invece di confrontare nomi di
  ruolo in `isManager()`.
- **La gestione dei ruoli sta nel CRM**: Impostazioni → Utenti, con invito per
  livello. Il Manager amministrativo nomina Segreteria, Operatore e altri Manager.
  System Manager nel CRM non si offre mai: lo assegnate voi, dal Desk.
- **Le impostazioni tecniche restano vostre**: la separazione c'è già in parte (PR
  #95: "i dettagli tecnici solo agli admin") e va estesa con lo stesso criterio.

**Da decidere insieme.**

- L'operatore vede solo i suoi pazienti o tutti? Dipende dal dossier sanitario
  (domanda 3 della [proposta](./README.md#le-domande-da-chiudere-prima)).
- La direzione sanitaria è un quarto livello o un operatore con un permesso in più?
- Chi fa marketing (voi o il centro) che livello ha? Proposta: un ruolo a parte,
  senza dati clinici e senza fatture.

---

## 2. Senza Builder, niente Sito

**Richiesta.** Se Frappe Builder non è installato, tutta la parte Sito deve
sparire.

**Oggi (verificato).** La voce "Site" nel menu e il gruppo "Website" nelle
impostazioni si vedono a tutti i manager anche senza Builder. È voluto: il commento
in `AppSidebar.vue` dice che la pagina gestisce da sola "Builder mancante", perché
altrimenti non ci sarebbe un posto da cui accendere il sito. Il backend sa già se
Builder c'è (`crm/api/site.py: builder_installed()`).

**Proposta.** Quel motivo non vale per chi Builder non ce l'ha: installarlo è
un'operazione sul bench, cioè vostra, non un interruttore del cliente. Quindi,
senza Builder: via la voce di menu, via il gruppo nelle impostazioni, la rotta
`/sito` rimanda alla home, e spariscono i widget e i trigger che parlano del sito.
Il frontend deve saperlo all'avvio (un flag nel boot o nei dati di sessione).
Mezza giornata di lavoro.

---

## 3. Cartella clinica completa

**Richiesta.** Cartella clinica completa per ogni paziente.

**Oggi.** Niente. Il modello è nella [proposta](./README.md#il-modello-dati-prima-versione).

**Cosa vuol dire "completa".** Su un'unica linea del tempo del paziente:
anamnesi (remota, familiare, fisiologica), allergie e intolleranze, farmaci in
uso, parametri (peso, altezza, BMI, pressione…), visite sul modello della
specialità, diagnosi, terapie e prescrizioni, piani (sezione 6), documenti e
referti (sezione 5), moduli firmati (sezione 4). Ogni dato clinico salvato fa
diventare paziente (regola 1 della proposta) e segue i permessi della cartella.

---

## 4. Modulistica: un builder nel CRM, con la firma come componente

**Richiesta.** Modulistica varia (privacy, consensi, anamnesi, questionari) da un
builder di moduli configurabile nel CRM, con la firma digitalizzata come
componente del modulo.

**Oggi (verificato).**

- **Un builder di moduli c'è già**: Impostazioni → Forms
  (`frontend/src/components/Settings/Forms/FormBuilderPanel.vue`,
  `crm/api/form.py`). Ma serve a raccogliere lead dal sito: si appoggia al Web
  Form di Frappe, scrive solo su `CRM Lead` e `CRM Deal` (`ALLOWED_DOCTYPES`),
  pubblica su `/crm-form/<route>` e accetta solo campi semplici, senza allegati
  né tabelle (`SUPPORTED_FIELDTYPES`).
- **La firma non c'è**: il tipo di campo `Signature` di Frappe è escluso di
  proposito dagli editor di layout della SPA (`restrictedFieldTypes` in
  `FieldLayoutEditor.vue` e `SidePanelLayoutEditor.vue`).

**Proposta.**

- **Un builder solo, due usi**: il modulo che raccoglie lead, com'è oggi, e il
  **modulo del centro**. Un modulo del centro è un modello versionato: sezioni,
  campi, testo legale e componenti (testo, scelta, data, tabella, allegato,
  **firma**). Una compilazione è un record legato alla persona, e alla visita se
  c'è, che conserva i valori e **la versione esatta del testo firmato**.
- **La firma è un componente del modulo**: tracciata con il dito, la penna o il
  mouse, salvata come immagine nel record insieme alla traccia (chi, quando, da
  quale dispositivo) e all'impronta del PDF. È una firma elettronica semplice, e
  basta per informativa privacy, consensi al trattamento e questionari.
- **Per ciò che vuole di più**, come il consenso informato a una prestazione
  invasiva, lo stesso componente passa a un fornitore di firma avanzata
  (grafometrica o OTP): un adattatore, come per SdI e Sistema TS. I requisiti della
  firma avanzata sono in [ricerca §2.5](./ricerca.md#25-firma-dei-consensi-e-dei-referti).
- **Il PDF è il documento**: si genera alla firma, una volta sola, con la sua
  impronta. È lo stesso principio del PDF della fattura in `crm/invoicing` (il file
  consegnato è quello conservato), e può usarne lo stesso motore PDF/A.
- **Dove si firma**: al banco su un tablet (una schermata col solo modulo, bloccata,
  da passare al paziente), a casa con un link (area cliente, o un link con token
  come in `/prenota`), oppure su carta, scansionata e caricata.
- **Moduli pronti da consegnare**: informativa privacy (presa visione), consenso
  marketing, consenso al dossier, consenso ai referti online, consenso informato
  per prestazione, anamnesi di prima visita, questionario prima della visita. I
  testi li valida il DPO del centro.
- **Ogni modulo firmato alimenta il registro dei consensi.** "Consenso marketing
  sì o no", che le automazioni leggono per i richiami, viene da lì, e da lì si
  chiude il buco di `/prenota`, dove la spunta privacy si controlla ma non si
  registra.

**Da decidere insieme.** Basta la firma semplice per i primi clienti, o serve la
firma avanzata da subito? Quale fornitore?

---

## 5. Archivio di referti e documenti

**Richiesta.** Archiviazione di referti e della documentazione del cliente.

**Oggi (verificato).** La pagina della persona ha la scheda "Attachments", e gli
allegati sono privati per default (`FilesUploaderArea.vue`, salvo l'impostazione
`make_attachments_public`). Ma un referto e un preventivo sono lo stesso
"allegato": niente tipo, niente data clinica, niente distinzione di chi può
vederlo, niente registro degli accessi.

**Proposta.** Un archivio nella sezione "Clinica": documenti con tipo (referto
interno, referto esterno, esame, immagine, prescrizione, modulo firmato), data,
autore o provenienza, e visibilità (solo operatori, oppure anche nell'area
cliente). File privati e accessi registrati come la cartella. Un documento clinico
caricato è un dato medico, quindi fa diventare paziente. Da una conversazione
WhatsApp, "sposta nella cartella" porta il file dall'allegato della chat
all'archivio clinico.

---

## 6. Area cliente

**Richiesta.** Un'area riservata per il cliente, con una lista di cose: piano
nutrizionale, piano alimentare o dieta, piano di allenamento, lista degli
appuntamenti, comunicazioni del medico, e così via.

**Oggi (verificato).** Niente. C'è solo la gestione di un appuntamento con un link
e un token in `/prenota` (sposta o annulla). Frappe ha già gli utenti del sito
(Website User) e un portale, che il CRM non usa.

**Proposta.**

- **Chi entra**: il cliente come utente del sito, non del CRM, collegato alla sua
  persona. Si entra con email e codice monouso, senza password da ricordare, e
  dalla volta dopo, se vuole, col viso o l'impronta (passkey). Per scaricare un
  referto si rientra. È anche quello che chiedono le linee guida del Garante sui
  referti online (consenso, accesso protetto, possibilità di escludere singoli
  referti, 45 giorni online:
  [ricerca §2.4](./ricerca.md#24-privacy-e-dati-sanitari),
  [ricerca per il design §3](./ricerca-design.md#3-firma-e-area-cliente)).
- **Cosa vede**, in sezioni che il centro accende o spegne:

  | Sezione | Contenuto |
  |---|---|
  | Appuntamenti | prossimi e passati; sposta, annulla e prenota con le regole di `/prenota` |
  | Piani | nutrizionale, alimentare o dieta, allenamento, esercizi di fisioterapia |
  | Documenti | referti e documenti resi visibili dall'operatore; moduli da firmare |
  | Comunicazioni | i messaggi dell'operatore: una bacheca per paziente, non una chat |
  | Fatture | i PDF, che la fatturazione ha già |

- **Un piano è un oggetto solo, con modelli diversi**: tipo, operatore, periodo,
  contenuto strutturato e versioni. Una dieta è pasti per giorni, un allenamento è
  esercizi per sedute: stesso oggetto, modello diverso, costruito con **lo stesso
  builder dei moduli**. Un builder, tre usi: moduli, cartella, piani.
- **La notifica non porta il contenuto**: "hai un nuovo messaggio nella tua area"
  via WhatsApp o email, con il testo neutro. Dentro la chat non passano dati
  clinici (terza cucitura della [proposta](./README.md#le-tre-cuciture-fra-i-due-mondi)).
- **Com'è fatta**: con il nome, il logo e il colore dello studio, come
  `/prenota`, ma come **app a parte** (una seconda app Vite su `/area`, come l'app
  dei dipendenti di HRMS) e non in Jinja: moduli e firma devono essere gli stessi
  componenti del CRM, e la SPA del CRM respinge chi non è dello staff
  (`check_app_permission`). Le API (`crm/api/portal.py`) rispondono solo per "la
  mia persona", ricavata sul server. Gli accessi si registrano come quelli della
  cartella ([design](./design.md#larea-cliente)).

**Da decidere insieme.**

- Codice monouso via email o SMS? WhatsApp resta per gli avvisi senza contenuto.
- Quali piani per primi: nutrizione, allenamento, entrambi? Chi li scrive, e da
  quali modelli si parte?
- Le comunicazioni vanno solo dall'operatore al paziente, o il paziente può
  rispondere? Se risponde diventa una chat, e ai medici arriva un'altra casella da
  guardare.

---

## Stime indicative

| Pezzo | sp |
|---|---|
| Tre livelli, gestione ruoli nel CRM, le 16 copie di `MANAGER_ROLES` in un posto solo | 1,5–2 |
| Sito nascosto senza Builder | 0,1 |
| Builder dei moduli del centro, componente firma, PDF, registro dei consensi | 3–4 |
| Firma avanzata con un fornitore (adattatore, codice SMS, kit dell'erogatore) | 1 |
| Archivio clinico dei documenti | 1–1,5 |
| Area cliente con appuntamenti, documenti, comunicazioni, fatture, "Prepara la visita", passkey | 4–5 |
| Piani (modelli, editor per l'operatore, vista nell'area cliente) | 2–3 |
