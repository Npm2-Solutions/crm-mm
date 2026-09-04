# 14 — Agenda: appuntamenti multi-persona, stanze, attrezzature e listini

> ✅ **IMPLEMENTATO** (03/09/2026) direttamente in questo fork (modulo FCRM).
>
> Estende il calendario interno del CRM da "un evento, un proprietario" a
> un'agenda di studio/centro servizi: più professionisti sullo stesso
> appuntamento, più clienti sullo stesso professionista, stanze e attrezzature
> con capacità, listini variabili.

> Parte del [Progetto GHL-Parity](./README.md). Il booking pubblico stile
> Calendly resta nel [modulo 05](./05-calendari-prenotazioni.md): qui si parla
> dell'agenda **interna**, che quel modulo ora rispetta.

## Il problema

Il calendario del CRM poggiava sul DocType `Event` del framework: un titolo, un
intervallo, dei partecipanti come email. Basta per riunioni, non basta per
erogare prestazioni. Mancava tutto quello che rende un'agenda un'agenda:

- **due professionisti su un cliente** (visita in due, terapista + assistente);
- **un professionista su più clienti** (corso, sessione di gruppo con posti);
- **stanze e attrezzature**: due appuntamenti non possono usare la stessa sala,
  ma una palestra può ospitarne tre e di tapis roulant ce ne sono cinque;
- **listini variabili**: la stessa prestazione costa diversamente di sera, con
  un professionista senior, in gruppo o per un cliente convenzionato;
- **conflitti**: il sistema deve dire di no, e dire *perché*.

## Ricerca (settembre 2026)

Il vocabolario di [Cal.com](https://cal.com/help/event-types/round-robin) è lo
standard di fatto per lo staffing: `ROUND_ROBIN` (distribuzione al membro meno
carico, con peso e priorità), `COLLECTIVE` (intersezione delle disponibilità,
tutti prenotati insieme), `MANAGED`, più i
[round robin groups](https://cal.com/blog/round-robin-groups-scheduling) — un
host per gruppo quando servono ruoli diversi — e gli
[**offer seats**](https://cal.com/help/event-types/offer-seats) per far entrare
più invitati nello stesso slot (corsi, open day, orientamenti). Cal.com però
**non modella risorse fisiche**: niente stanze, niente attrezzature.

Chi le modella lo fa così:

- [Odoo Appointments](https://www.odoo.com/documentation/19.0/applications/productivity/appointments.html)
  dà a ogni risorsa una **capacità** (quante persone ospita) e permette di
  dichiarare **risorse collegate**, usabili in combinazione per assorbire una
  domanda più grande; il modulo OCA
  [resource_booking](https://apps.odoo-community.org/shop/resource-booking-6341)
  prenota **combinazioni** di risorse che devono essere tutte libere.
- I sistemi di meeting room ([Skedda](https://www.skedda.com/insights/meeting-room-scheduler),
  [Yarooms](https://www.yarooms.com/reports/best-meeting-room-booking-systems))
  trattano capienza e dotazioni come **attributi filtrabili** della risorsa, e
  mettono la prevenzione del doppio-booking al centro.
- Nel software per saloni/spa il motore di prenotazione è descritto come
  [il pezzo difficile](https://www.raftlabs.com/blog/how-to-build-app-like-fresha):
  deve trovare lo slot in cui **prestazione, professionista e risorsa fisica**
  sono liberi *contemporaneamente*.

Sul calcolo, la disponibilità comune si riduce a un problema classico di
intervalli — [sweep line](https://algo.monster/liteproblems/759) sui confini per
l'unione degli occupati, intersezione per il "tutti liberi insieme", conteggio
del carico simultaneo per la capacità.

Sui prezzi, il precedente più vicino è in casa: la
[Pricing Rule di ERPNext](https://docs.frappe.io/erpnext/pricing-rule), dove una
regola con **priorità** vince sul prezzo di listino e le condizioni decidono
quando si applica.

## Cosa è stato costruito

### Modello dati (`crm/fcrm/doctype/`)

| DocType | Ruolo |
|---|---|
| `CRM Resource` | Stanza / attrezzatura / veicolo. `capacity` = quante prenotazioni contemporanee regge (1 = uso esclusivo), `seats` = quante persone ospita, orari propri, tariffa oraria |
| `CRM Service` | La prestazione a listino: durata, buffer pre/post, orari, preavviso, orizzonte, **modello di staffing**, min/max partecipanti, risorse richieste, prezzo base |
| `CRM Service Staff` / `CRM Service Role` / `CRM Service Resource` | Chi può erogarla (con ruolo e priorità), quali ruoli servono, cosa serve come risorsa |
| `CRM Staff Schedule` | Orari settimanali del professionista, festività, **eccezioni per data** (ferie, straordinari), tetto giornaliero |
| `CRM Price List` + `CRM Service Price` | Listini e righe prezzo condizionate |
| `CRM Appointment` (+ `Staff`, `Participant`, `Resource`) | L'appuntamento, con prezzo congelato al momento della prenotazione |
| `CRM Scheduling Settings` | Timezone, default, regole di conflitto |

### Modelli di staffing

| `staff_selection` | Comportamento | Caso d'uso |
|---|---|---|
| `Any one` | Round robin: prende `staff_count` professionisti liberi, ordinati per priorità e poi per carico | Un professionista, tanti clienti nella giornata |
| `All required` | Collective: **tutti** i professionisti elencati devono essere liberi e vengono prenotati insieme | Due professionisti seguono un cliente solo |
| `One per role` | Un professionista libero per ogni ruolo dichiarato | Terapista + assistente |

Con `max_participants > 1` il servizio diventa una **sessione di gruppo**: il
motore, oltre agli slot nuovi, restituisce gli appuntamenti già esistenti che
hanno **posti liberi** (`join_appointment`, `seats_left`), così un secondo
cliente entra nella stessa lezione invece di crearne una parallela. Se la sala
ha meno posti del servizio, vince la sala.

### Motore (`crm/scheduling/`)

- **`intervals.py`** — algebra di intervalli pura, zero import di Frappe:
  `merge` / `intersect` / `intersect_all` / `subtract`, `covers`, `peak_usage`
  (sweep line con quantità, per la capacità delle risorse), `slots_in`.
  Convenzione: intervalli semiaperti, quindi due appuntamenti attaccati **non**
  sono in conflitto.
- **`availability.py`** — finestre di lavoro (settimanali + festività +
  eccezioni per data), occupato (appuntamenti, `Event`, booking pubblici,
  Google free/busy), assegnazione staff e risorse, generazione slot, e
  `find_conflicts()` — la stessa funzione che blocca il salvataggio e che il
  form chiama in anteprima, così i due non possono mai dire cose diverse.
- **`pricing.py`** — risoluzione del prezzo: fra le regole che matchano vince
  la **priorità**, a pari priorità la **specificità** (chi pone più condizioni),
  a pari specificità la più recente. Se non matcha nulla, prezzo base del
  servizio. La risposta esiste sempre, e `price_source` dice da dove viene.

Buffer: l'occupato viene allargato del **massimo** fra il buffer del servizio
che sta cercando e quello del servizio che occupa — un quarto d'ora di riassetto
protegge lo slot successivo da qualunque lato sia stato dichiarato.

Stati: solo `Cancelled` libera lo slot. Un **no-show ha consumato il tempo**
esattamente come una seduta fatta.

### Conflitti

`CRM Scheduling Settings` decide cosa bloccare: professionista doppio, risorsa
oltre capacità, cliente in due posti, fuori orario. Un manager può **forzare**:
l'appuntamento si salva e il conflitto viene scritto in `conflict_note`, dove
resta visibile — invece di sparire.

### API (`crm/api/appointments.py`)

`get_calendar` (una lettura per tutte le viste), `get_scheduler_meta`,
`get_available_slots`, `quote_price`, `check_conflicts`, `save_appointment`,
`move_appointment`, `set_status`, `set_participant_status`, `join_appointment`,
`create_series` / `cancel_series`, `get_workload`, più il CRUD amministrativo di
servizi, risorse, listini, orari e impostazioni.

### Interfaccia (frappe-ui / Espresso)

La pagina **Calendar** ha due viste sugli stessi dati:

- **Calendar** — mese/settimana/giorno di frappe-ui, con gli appuntamenti
  accanto agli `Event`. Trascinare un appuntamento passa dal motore, quindi
  buffer e conflitti valgono anche lì.
- **Agenda** — griglia giornaliera con **una colonna per professionista oppure
  per stanza/attrezzatura**. Un appuntamento con due professionisti compare in
  entrambe le colonne: è il punto della vista. Drag verticale sposta l'ora,
  drag orizzontale cambia professionista o stanza, click sul vuoto apre un
  nuovo appuntamento già su quella persona e a quell'ora.

Filtri per servizio, professionista, risorsa e stato sopra entrambe.

L'editor appuntamento parte dal servizio (che porta durata, staffing e risorse),
cerca gli slot liberi a 7 giorni mostrando anche i "unisciti" delle sessioni di
gruppo, auto-assegna, collega i partecipanti a lead/contatti/deal, calcola il
prezzo dal server dicendo **quale regola** ha vinto, e mostra i conflitti in
tempo reale con l'override per i manager.

Impostazioni dedicate nel gruppo **Agenda** del modale, nell'ordine in cui si
configura: Servizi → Stanze & Attrezzature → Listini → Orari di lavoro →
Scheduling.

### Integrazioni

- **Automazioni**: cinque trigger nuovi — `Appointment Created`, `Rescheduled`,
  `Cancelled`, `No Show`, `Completed` — risolti sul primo partecipante collegato
  a un lead o a un deal. Promemoria e sequenze di recupero funzionano quindi
  anche sull'agenda interna.
- **Google Calendar**: ogni appuntamento viene rispecchiato in un `Event`
  collegato (`sync_to_event`), che il sync nativo del framework porta nel
  calendario del professionista. Lo specchio è a senso unico: l'appuntamento è
  la fonte di verità.
- **Booking pubblico**: `CRM Booking Calendar.get_busy_intervals` ora passa dal
  motore condiviso, quindi un professionista pieno di appuntamenti interni non
  appare più libero ai visitatori della pagina pubblica.

## Test

- `crm/tests/test_scheduling.py` — algebra degli intervalli, i tre modelli di
  staffing, capacità di stanze e attrezzature, sessioni di gruppo e posti,
  conflitti (compresi buffer, back-to-back, no-show, override), listini
  variabili, superficie API.
- `crm/tests/test_booking.py` — un caso in più: un appuntamento interno blocca
  uno slot pubblico.
- `frontend/tests/unit/scheduler.test.js` — geometria della griglia (lane degli
  appuntamenti sovrapposti, box, assi, colonne).

## Prossimi passi

1. **Slot pubblici basati sui servizi**: collegare `CRM Booking Calendar` a un
   `CRM Service` per portare risorse e listini anche sulla pagina `/book`.
2. **Vista settimanale della griglia risorse** (oggi è giornaliera).
3. **Ricorrenze vere** (regola persistente e modifica "tutta la serie"): oggi
   `create_series` genera occorrenze indipendenti collegate da un `series` id.
4. **Pagamento e acconto** sull'appuntamento, riusando il checkout del booking.
5. **Saturazione** in dashboard: `get_workload` calcola già minuti prenotati e
   capacità per professionista.

## Fonti

- Cal.com — [Round Robin](https://cal.com/help/event-types/round-robin),
  [Round robin groups](https://cal.com/blog/round-robin-groups-scheduling),
  [Collective events](https://cal.com/blog/collective-events-scheduling-guide),
  [Offer seats](https://cal.com/help/event-types/offer-seats),
  [scheduling types e availability](https://deepwiki.com/calcom/cal.com/2.3-scheduling-and-availability-logic)
- Odoo — [Appointments](https://www.odoo.com/documentation/19.0/applications/productivity/appointments.html),
  [Appointment types (risorse, capacità, risorse collegate)](https://www.odoo.com/documentation/saas-19.3/applications/productivity/appointments/appointment_types.html),
  OCA [resource_booking](https://apps.odoo-community.org/shop/resource-booking-6341)
- Meeting room booking — [Skedda](https://www.skedda.com/insights/meeting-room-scheduler),
  [Yarooms](https://www.yarooms.com/reports/best-meeting-room-booking-systems)
- Salon/spa booking engine — [RaftLabs](https://www.raftlabs.com/blog/how-to-build-app-like-fresha)
- Algoritmi — [sweep line su intervalli](https://algo.monster/liteproblems/759),
  [line sweep](https://dilipkumar.medium.com/sweep-line-algorithm-e1db4796d638)
- Prezzi — [ERPNext Pricing Rule](https://docs.frappe.io/erpnext/pricing-rule)
