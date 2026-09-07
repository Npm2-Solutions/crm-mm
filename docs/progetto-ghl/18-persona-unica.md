# 18 — Una persona sola: lead e contatto smettono di essere due

> 📐 **Proposta.** Da decidere **prima** della [timeline unificata](./17-timeline-unificata.md),
> che poggia su "la conversazione appartiene alla persona": qui si stabilisce chi
> è la persona.

## Il modello

Tre parole, tre significati distinti:

- **il lead è la persona** — esiste da quando arriva e non smette mai di esserlo;
- **il deal è la relazione con noi** — una persona può averne una, tre, nessuna;
- **il contatto è la rubrica** — i recapiti di quella persona, non una seconda persona.

## Cosa fa il codice oggi, che è l'opposto

Alla conversione, `CRMLead.create_contact` **copia** la persona in un secondo
record:

```python
contact = frappe.new_doc("Contact")
contact.update({"first_name": self.first_name or self.lead_name, "last_name": self.last_name, ...})
if self.email:     contact.append("email_ids", {"email_id": self.email, "is_primary": 1})
if self.mobile_no: contact.append("phone_nos", {"phone": self.mobile_no, "is_primary_mobile_no": 1})
```

E la copia va in **entrambe le direzioni** a seconda di come ci si arriva:
`create_contact` copia lead→contatto, `update_lead_contact` copia contatto→lead
quando se ne aggancia uno esistente. Dopo, nessuno tiene allineato niente: si
cambia il numero da una parte e l'altra resta al vecchio.

Il lead viene poi marcato `converted = 1` e sparisce dalla lista (`Leads.vue`
filtra `{ converted: 0 }`): da centro diventa scarto. Da una persona nascono
**quattro record** — Lead, Contact, Organization, Deal — di cui due sono la
stessa persona scritta due volte.

## La scelta: invertire il proprietario, non spostare i campi

`mobile_no` compare in **201 punti** del codice: 119 nel backend, 82 nel
frontend — chat WhatsApp, SMS, dialer, appuntamenti, liste, automazioni.
Toglierlo dal lead significa toccarli tutti, e sbagliarne qualcuno.

Quindi il campo **resta dov'è e smette di essere la verità**:

| | Oggi | Dopo |
|---|---|---|
| Dove vivono i numeri | copiati su lead **e** contatto | solo su `Contact.phone_nos` |
| `CRM Lead.mobile_no` | campo scrivibile | specchio in sola lettura (`fetch_from`) |
| Chi crea il contatto | la conversione | la creazione del lead, sempre |
| Il contatto per l'utente | una scheda a sé | la rubrica del lead, non una scheda |
| Più numeri per persona | non previsti | gratis: `phone_nos` è già una tabella figlia |

I 201 punti continuano a leggere `doc.mobile_no` e non si accorgono di niente.
Cambia solo **dove si scrive**.

### Cosa si aggiusta come effetto collaterale

- **La risoluzione di un numero in entrata diventa una strada sola**: numero →
  `Contact Phone` → contatto → il suo lead o la sua trattativa. È già quello che
  fa `get_contact`, solo che oggi deve anche indovinare fra tre possibilità.
- **Sparisce il "contatto orfano invisibile"**: un messaggio poteva agganciarsi a
  un Contact senza lead né trattativa, e la scheda Contatto non ha nessuna tab di
  attività — il messaggio non era visibile da nessuna parte. Un contatto senza
  lead non esisterà più.
- **`adopt_unknown_number` si semplifica**: crea lead **e** contatto, una forma
  sola invece di un lead con un numero appiccicato.

## Le interfacce, una per una

### Modale "Nuovo lead" (`LeadModal.vue`)

Non cambia per chi la usa: nome, email, telefono, come adesso. Cambia dove
finiscono i dati — il salvataggio crea lead **e** contatto insieme, e i recapiti
vanno sul contatto. La validazione del numero che c'è già (`isNaN` sul numero
ripulito) resta dov'è.

Il campo telefono diventa **ripetibile**: un "+ aggiungi numero" sotto il primo.
Chi ne ha uno solo non se ne accorge.

### Scheda del lead — pannello laterale

I recapiti diventano un **blocco solo**, "Recapiti", con i numeri e le email in
elenco e il badge *principale* su quello che si usa per chiamare e scrivere.
Modificarli scrive sul contatto. Non c'è più un campo "Mobile" e un campo
"Telefono" che nessuno sa distinguere.

Il bottone di chiamata (`Lead.vue`, `makeCall(doc.mobile_no)`) continua a usare
il numero principale: legge lo specchio, non cambia.

### Modale "Nuovo contatto" (`ContactModal.vue`)

**Sparisce come creazione autonoma.** Oggi crea una persona che il CRM non
collega a niente — la stessa che poi riceve messaggi invisibili.

La modale resta con i suoi campi, ma smette di creare un Contact da solo: salva
attraverso `crm.api.contact.create_person`, che crea il lead e si porta dietro il
contatto, e poi apre **il lead**. Creare una persona in rubrica *è* creare un
lead; chi la usa scrive gli stessi campi di prima.

Resta come **modifica** dei recapiti, richiamata dal pannello del lead.

### Modale "Converti in trattativa" (`ConvertToDealModal.vue`)

Oggi chiede *«Contatto esistente?»* con l'interruttore e la ricerca, perché deve
decidere se creare la seconda copia della persona o riusarne una. **Quella
domanda sparisce**: il contatto esiste già dalla creazione del lead.

Restano l'organizzazione e i dati della trattativa. La modale si accorcia di una
sezione intera, e con essa se ne va la domanda più confusa dell'interfaccia.

### Modale "Nuova trattativa" (`DealModal.vue`)

Oggi ha due interruttori — *Scegli organizzazione esistente*, *Scegli contatto
esistente* — che mostrano e nascondono sezioni intere (`chooseExistingContact`,
`hasContactSections`). Il secondo diventa **"A chi?"**: si sceglie una persona
esistente o se ne crea una nuova, e in quel caso nasce un lead con il suo
contatto. Una domanda invece di un interruttore che riconfigura la modale.

### Elenco "Contatti"

Diventa una **vista sui lead** — quelli qualificati, o con almeno una trattativa
— non un elenco parallelo di un altro doctype. Stessa tabella, filtro diverso:
"Lead" è la lista di lavoro di chi c'è da qualificare, "Contatti" è la rubrica
di chi c'è già.

Aprire una riga della rubrica apre **la persona**, cioè il lead, non una scheda
Contatto povera che non ha né chat né attività.

### Scheda della trattativa — tab "Contatti"

Resta: una trattativa può coinvolgere più persone (`CRM Contacts`). Cambia cosa
si aggiunge — persone, cioè lead, non record Contact creati per l'occasione.

## La migrazione

Il pezzo scomodo, e non c'è modo di renderlo indolore.

1. **Lead senza contatto** (tutti quelli non convertiti): si crea il contatto dai
   loro dati. Nessun conflitto.
2. **Lead convertiti, con la copia divergente**: qualcuno deve vincere. Vince il
   **contatto**, perché è quello che le email e la telefonia hanno usato finora;
   il numero o l'email del lead che non corrisponde diventa **una riga in più**
   sul contatto — un altro modo per raggiungere quella persona — invece di
   sparire in silenzio.
3. **Contatti senza lead** (creati a mano dalla modale che qui togliamo): si crea
   il lead attorno a loro, così nessuna persona resta senza casa.

La patch va scritta perché sia **rieseguibile senza danno**: su un sito grande
verrà interrotta almeno una volta.

## Le tappe

1. **Il campo `contact` sul lead** e la creazione contestuale, senza toccare
   ancora niente della UI: da qui in poi ogni lead nuovo nasce già a posto.
2. **Lo specchio**: `mobile_no`, `phone`, `email` del lead in sola lettura da
   `fetch_from`, più l'`on_update` sul Contact che rinfresca i suoi lead — il
   `fetch_from` di Frappe riempie al salvataggio, non insegue le modifiche
   altrui.
3. **La patch** sui dati esistenti.
4. **Le modali**: contatto, conversione, trattativa.
5. **La rubrica come vista**, e la scheda Contatto ritirata.

Le prime due sono invisibili all'utente e si possono rilasciare da sole. Dalla
terza in poi cambia quello che si vede, e conviene rilasciarle vicine.

### Dove siamo

Tappe 1–4 fatte. Della quinta è fatta la parte che conta per chi usa il CRM:
**aprire un contatto apre la persona**. Il reindirizzamento sta sulla rotta
`/contacts/:id`, quindi vale da ovunque si clicchi — la rubrica, la tab Contatti
di una trattativa, un link vecchio — e non solo dalla lista.

Il blocco **Contact** nel pannello laterale del lead c'è: l'elenco dei numeri e
delle email della persona, con il badge *principale*, sopra le altre sezioni —
la stessa posizione che la sezione Contatti ha da sempre sulla trattativa. Il
lead mostrava solo `email` e `mobile_no`, cioè il recapito principale e basta;
adesso si vede tutta la rubrica di quella persona.

La scheda Contatto non è però sparita: resta il posto dove si **modificano** —
ci si arriva dalla matita sul blocco, o dal bottone in alto (`?rubrica=1` salta
il reindirizzamento). Sparirà quando il blocco saprà anche scrivere.

Quello che **non** è stato fatto: la lista Contatti legge ancora il doctype
`Contact`, non i lead. Puntarla su `CRM Lead` significa condividere con la pagina
Lead le stesse impostazioni di lista, colonne e viste salvate — cambiarle di là le
cambierebbe di qua — e non è una cosa da fare di straforo su una pagina che si usa
tutti i giorni. Ora che ogni contatto ha il suo lead, comunque, quella lista *è*
la rubrica: righe di persone, che si aprono come persone.

## Il lead non si converte

"Converti in trattativa" raccontava la cosa sbagliata: che il lead fosse uno
stadio da superare, e la trattativa quello che diventa. Ma il lead **è** la
persona, e la persona resta anche quando la trattativa si chiude, si perde o si
raddoppia.

Il collegamento c'era già: `CRM Deal` ha da sempre il campo `lead`, e la
trattativa elenca la persona fra i suoi contatti. Mancava solo di dirlo:

- il bottone sulla scheda del lead è **"Nuova trattativa"**, non "Converti";
- se la persona ne ha già, diventa **"Trattative · n"**: si aprono da lì, e
  l'ultima voce del menu ne apre un'altra. Niente e nessuno impedisce la seconda;
- `crm.api.lead.get_deals` le trova per entrambe le strade — il campo `lead` e i
  contatti della trattativa — perché una trattativa nata dalla rubrica ha la
  seconda e non la prima.

Resta il flag `converted`, ma come **impianto interno**: è il filtro della lista
Lead, che è la lista di lavoro di chi c'è ancora da qualificare. Chi ha già una
trattativa esce da quella lista, non dal CRM — la sua scheda è la stessa di
prima, con la conversazione e le attività intatte. La parola "conversione" non
compare più da nessuna parte nell'interfaccia.

## La conversazione sta sulla persona

Il deal non mostrava tab *simili* a quelle del lead: mostrava **le stesse**.

```python
# crm/api/whatsapp.py
if reference_doctype == "CRM Deal":
    lead = reference_doc.get("lead")
    if lead:
        messages = frappe.get_all("WhatsApp Message",
            filters={"reference_doctype": "CRM Lead", "reference_name": lead}, ...)
```

```python
# crm/api/activities.py
if lead:
    activities, calls, notes, tasks, attachments = get_lead_activities(lead)
```

La chat del deal era la chat del lead, più quella del deal; e il registro
attività del deal ripeteva tutta la storia del lead. Aprire una trattativa
sembrava aprire il lead perché per metà lo era.

Adesso: **si parla con la persona, si lavora sulla trattativa.**

| | Dove sta |
|---|---|
| Email, WhatsApp, SMS, chiamate | sul lead — e il lead raccoglie anche quelle delle sue trattative |
| Registro attività, Data, Eventi, Task, Note, Allegati, Tracking, Commenti | sulla trattativa, e solo i suoi |

L'ordine conta: **prima** il lead raccoglie la conversazione delle sue
trattative (`get_conversation_on_deals`, e `whatsapp_thread_of` per i
messaggi), **poi** il deal smette di mostrarla. Al contrario, un messaggio
mandato da una trattativa non avrebbe più avuto nessun posto dove essere letto.

Sulla trattativa, al posto dei bottoni "Chiama" e "Scrivi", ce n'è uno che
**apre la persona**. E `create_deal` adesso valorizza `deal.lead` anche per una
trattativa creata dalla sua modale: senza quel collegamento la persona non
esisterebbe per la trattativa, e la sua conversazione non tornerebbe a casa.

### Anche un numero risolve alla persona

Restava un giro storto nascosto. `get_contact_lead_or_deal_from_number` provava
prima la **trattativa** — perché `get_contact` risponde con quella quando la
persona ne ha una — e ignorava i lead **convertiti**. Due conseguenze:

- un messaggio in entrata da un cliente veniva archiviato sulla sua trattativa,
  che una chat non ce l'ha;
- un messaggio da chi era già diventato cliente non risolveva affatto, e veniva
  **adottato in un secondo lead** per una persona che avevamo già.

E per i messaggi in **uscita** l'hook `validate` riscriveva il riferimento anche
quando il record c'era: scrivevi sul lead e il messaggio finiva sulla trattativa,
sparendo dalla chat in cui l'avevi appena battuto.

Adesso: un messaggio in uscita resta dove è stato scritto — chi ha premuto invio
lo ha già deciso — e un numero risolve **alla persona**, lead convertiti
compresi. La trattativa è la risposta solo quando nessuno possiede quel contatto,
cioè quando è nata dalla rubrica. Un contatto nudo resta nessuno, perché
consegnare a una pagina senza attività è peggio che dire di no.

## Cosa non faremo

**Non togliamo il doctype `Contact`.** È del framework: ci si appoggiano le
email, la telefonia e il campo `contact` della trattativa. Non è il nemico —
è il posto giusto per i recapiti. Il difetto era usarlo come *seconda persona*.

**Non togliamo `mobile_no` dal lead.** Duecento punti di lettura si aggiustano
cambiando chi scrive, non cambiando chi legge.
