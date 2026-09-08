# Lead, contatto, azienda, trattativa: cosa significano davvero

*08/09/2026 — verifica del nostro modello contro Salesforce, HubSpot, Pipedrive
e GoHighLevel, e le correzioni che ne sono venute fuori.*

## Cosa fanno gli altri

| | persona permanente | azienda | "lead" | trattativa |
|---|---|---|---|---|
| **Salesforce** | Contact | Account | record temporaneo a sé; alla conversione diventa **read-only** ed esce dal lavoro quotidiano | Opportunity, appesa all'Account |
| **HubSpot** | Contact | Company | oggetto **processo**: non può esistere da solo, deve essere associato a un contatto o a un'azienda; un contatto puo' avere **piu' lead** | Deal |
| **Pipedrive** | Person | Organization | vive nella Leads Inbox e **non puo' entrare in pipeline** finche' non diventa deal | Deal |
| **GoHighLevel** | Contact (unico) | — | **non esiste**: e' uno stato del contatto | Opportunity, contatto primario piu' contatti aggiuntivi |

L'invariante comune: **la persona e' unica e permanente, la vendita e'
ripetibile, e "lead" e' uno stadio o un processo — mai una seconda copia della
persona.** Salesforce e' l'unico dove il Lead e' un record vero, e infatti alla
conversione lo congela.

Il nostro modello (la persona resta, porta una o piu' trattative, la
conversazione sta su di lei) e' quello di HubSpot e GHL. Il problema non era il
modello: erano i pezzi di codice rimasti fedeli a quello di Salesforce.

## Le sei correzioni

### 1. Il nome — la lista si chiama Persone

Il record permanente si chiama `CRM Lead` per ragioni storiche e li' resta: il
doctype e' referenziato da centinaia di punti e da tutte le viste salvate.
Cambia l'etichetta, che e' cio' che si legge: nella barra laterale e in cima
alla lista adesso c'e' **Persone**. "Lead" torna a essere quello che e' — come
sta una persona all'inizio, non come si chiama per sempre.

### 2. La lista mostra tutti

`Leads.vue` filtrava `converted: 0`: appena nasceva una trattativa la persona
spariva dall'elenco. Era la semantica Salesforce (il lead convertito esce di
scena) sopra un modello in cui la persona resta. Il filtro non c'e' piu', e il
campo `converted` torna disponibile come filtro rapido con l'etichetta giusta,
**Has a deal**, per chi vuole vedere solo chi non ha ancora una trattativa.

### 3. Una persona sola, cercata sul serio

Tre punti cercavano la persona con `{email, converted: 0}` — webhook in
ingresso, prenotazioni, liste di chiamata — quindi un cliente che tornava dopo
aver aperto una trattativa **non veniva trovato e ne nasceva una seconda copia**.
Adesso c'e' un solo modo di cercare una persona, `crm.api.lead.find_person`, che
guarda email e telefono (in E.164) sia sui campi della persona sia sulle righe
della sua rubrica, e non esclude nessuno.

L'import Meta deduplicava solo su `facebook_lead_id`: stessa persona, due
moduli, due record. Ora una compilazione di chi il CRM conosce gia' viene
**unita** alla persona: cio' che ha scritto riempie solo i campi ancora vuoti (un
numero corretto a mano nel CRM batte quello ridigitato in un modulo), il primo
touch resta suo e questo diventa l'ultimo. Le compilazioni si accumulano in
`facebook_submissions`, che serve a due cose: la storia di quali moduli ha
compilato, e l'idempotenza — Meta riconsegna, e la riconciliazione oraria
rilegge due giorni di ogni modulo.

### 3-bis. Cancellare un lead deve volere dire cancellarlo

Sul sito vero e' successo questo: cancellati i lead arrivati da Facebook, si
sono ricreati da soli entro l'ora. Il motivo non era un'importazione impazzita
ma la domanda sbagliata: *"esiste un lead che porta questo leadgen id?"*. Con il
lead cancellato la risposta era no, e la riconciliazione oraria — che rilegge
gli ultimi due giorni di ogni modulo — lo riportava dentro.

Se una compilazione e' gia' stata gestita e' un fatto **dell'importazione**, non
di un record che qualcuno puo' aver cancellato nel frattempo. Adesso sta in
`Facebook Lead Import`, una riga per submission che sopravvive alla persona; il
`on_trash` del lead ci mette sopra la data di cancellazione invece di toglierla.
La patch `remember_the_leads_already_imported` ci scrive quello che il CRM ha
adesso, cosi' i lead di oggi si possono cancellare e restano cancellati. Una
compilazione il cui lead era gia' stato cancellato prima della patch il CRM non
la conosce e puo' rientrare **una volta**: da li' in poi la riga c'e'.

Con l'unione, pero', `Lead Created` non scatta piu' per chi torna: e' nato mesi
fa. Percio' esiste un trigger nuovo, **Lead Form Submitted**, che scatta a ogni
compilazione — persona nuova o no — con `facebook_form_id` e `source` nel
payload. E' la stessa distinzione di GHL fra "Contact Created" e "Facebook Lead
Form Submitted".

### 4. L'azienda dall'inizio *(fatto 08/09/2026)*

Su `CRM Lead` `organization` era testo libero mentre su `CRM Deal` era un Link a
`CRM Organization`: due persone della stessa azienda non erano collegate da
niente finche' non si convertivano. In Salesforce, HubSpot e Pipedrive l'azienda
e' un oggetto di prima classe fin da subito, e adesso lo e' anche qui.

Il punto delicato e' **quando** creare l'azienda. Frappe valida i Link **prima**
di qualunque hook in inserimento (`Document.insert` chiama `_validate_links()`
prima di `before_insert` e di `validate`), quindi un hook sarebbe arrivato tardi
e la persona sarebbe stata rifiutata invece che salvata. E i nomi di azienda
arrivano da ovunque: risposta a un'inserzione, modulo pubblico, arricchimento
dal sito, qualcuno che scrive.

Percio' `CRMLead._validate_links` e' sovrascritto e chiama `ensure_organization`
un istante prima del controllo. E' l'unico momento che copre **tutte** le strade
in ingresso e tutti e due i casi, inserimento e salvataggio, perche' ci passano
tutte. L'azienda nuova nasce con quello che la persona sa di lei — sito,
settore, fatturato, dipendenti, descrizione — che altrimenti andrebbe perso; se
l'azienda esiste gia', quello che dice di se' vale piu' di quello che digita una
persona nuova.

Un'eccezione dichiarata: sui **moduli pubblici** il campo resta una casella di
testo (`TYPED_BY_HAND` in `crm/api/form.py`). Uno sconosciuto non conosce
l'elenco delle aziende del CRM, non ha il permesso di cercarci dentro, e non
deve essere impedito di scrivere il nome della propria: il record nasce dal
nome, alla ricezione.

`create_organization` alla conversione non crea piu' niente: la persona e' gia'
collegata alla sua azienda. Gli resta solo la scelta di chi converte a mano e
punta la trattativa su un'azienda diversa da quella della persona.

La patch `give_the_person_a_real_company` crea le aziende per i nomi gia'
scritti sulle persone: un `CRM Organization` prende il nome da se' stesso,
quindi la stringa che una persona porta **e'** gia' il link, appena l'azienda
esiste.

### 5. La trattativa non e' piu' una copia della persona

`create_deal` copiava dal lead tutto tranne email/telefono/SLA — nome, ruolo,
azienda, settore, fatturato, social — e da quel momento le due copie erano
libere di divergere.

I campi restano sulla trattativa, perche' liste, board e template li leggono, ma
sono diventati **specchi** (`fetch_from`): la persona e l'organizzazione sono la
sorgente. Frappe riempie uno specchio quando si salva la trattativa, e non
basta — la persona si modifica sulla sua pagina — quindi `crm/api/mirror.py`
spinge la modifica sulle trattative che la mostrano.

Restano scrivibili di proposito: il modale "nuova trattativa" e' anche il posto
dove si digita una persona o un'azienda nuova, e un campo read-only li' non si
potrebbe compilare. Conseguenza da sapere: un dato dell'azienda modificato
*sulla trattativa* torna a quello che dice l'azienda al salvataggio successivo.
Il posto per cambiarlo e' l'azienda. Quando il link organizzazione del modale
avra' il suo "Create New", gli specchi diventeranno read-only.

Due bug preesistenti trovati per strada: `annual_revenue` e `website` sulla
trattativa avevano `fetch_from: ".annual_revenue"` — senza campo link davanti,
cioe' non funzionante.

### 6. Una persona, una voce di rubrica, un elenco

Ogni lead ha gia' il suo `Contact` (patch `give_every_lead_a_contact`), la
pagina del contatto rimanda gia' alla persona, e `create_person` crea sempre
tutti e due. Restava la voce **Contacts** nella barra laterale: un secondo
elenco delle stesse persone, le cui righe rimbalzavano sulla prima. Non c'e'
piu'. La rubrica resta raggiungibile dalla persona (`?rubrica=1`), che e' il
solo posto dove serve: modificare numeri e indirizzi.

`give_every_contact_a_person` chiude il caso opposto: le voci di rubrica nate
prima di `create_person` (un contatto digitato dentro una trattativa, un
import) ricevono la loro persona, cosi' togliere l'elenco non nasconde nessuno.

## Test

- `crm/fcrm/doctype/crm_lead/test_crm_lead.py`: scrivere il nome di un'azienda
  la crea e la collega, con quello che la persona sa di lei; due persone della
  stessa azienda ne condividono una sola; un'azienda che esiste gia' non viene
  riscritta da chi arriva dopo.
- `crm/tests/test_meta_leads.py`: una seconda compilazione e' una submission e
  non una seconda persona; una submission unita non viene reimportata; l'unione
  non sovrascrive cio' che e' stato scritto a mano; `find_person` trova chi ha
  gia' una trattativa; **un lead cancellato non torna**, e cancellare una
  persona timbra le sue submission.
- `crm/fcrm/doctype/crm_deal/test_crm_deal.py`: la trattativa mostra il nome che
  la persona ha adesso e i dati che l'azienda ha adesso; convertire lascia la
  persona dov'e' e la seconda conversione le mette accanto una seconda
  trattativa.

## Fonti

- [Salesforce Help — What happens when I convert leads?](https://help.salesforce.com/s/articleView?language=en_US&id=sales.faq_leads_what_happens_when.htm&type=5)
- [Salesforce Ben — Opportunities vs Leads](https://www.salesforceben.com/salesforce-opportunities-vs-leads/)
- [HubSpot — Create leads](https://knowledge.hubspot.com/records/create-leads)
- [Pipedrive — Leads vs deals](https://support.pipedrive.com/en/article/leads-vs-deals)
- [Pipedrive — Contacts: people and organizations](https://support.pipedrive.com/en/article/contacts-people-and-organizations)
- [HighLevel — Opportunities FAQ](https://help.gohighlevel.com/support/solutions/articles/155000002000-opportunities-faqs)
