# 62 — Più sedi in un centro

Molti poliambulatori hanno due-cinque sedi sotto una società (o un marchio). Fino a
qui un sito era un centro in un posto solo. Ora un centro ha le sue **sedi**
(`CRM Location`), dentro lo stesso sito: un'agenda, un archivio di persone, una
fatturazione.

## Cosa fa

- **Impostazioni > Il centro > Sedi** (`impostazioni.generali`): nome, indirizzo
  (via, CAP, città, provincia), telefono, email, link alla mappa, orari di apertura
  con le parole del centro, l'azienda emittente se la sede fattura con un'altra
  società, attiva o no. Una sede con ambulatori o appuntamenti non si elimina: si
  disattiva.
- **Una sede non è una sede.** Tutto quello che nomina le sedi compare solo con
  due o più sedi attive (`sedi.piu_sedi()`, `utils/sedi.js` `piuSedi`; il boot porta
  `sedi` vuoto altrimenti). Con zero o una sede l'agenda, /prenota e l'accoglienza
  sono quelle di prima (test: `UnaSedeSola`, le schermate `*-una-sede-*`).
- **Ambulatori**: ognuno dice in che sede è (`CRM Resource.centre_location`); uno
  senza sede serve tutte (un'attrezzatura che si sposta).
- **Turni**: ogni riga della settimana e ogni giorno di eccezione può dire la sede
  (`CRM Service Day` / `CRM Availability Exception`, `centre_location`); vuota vale
  ovunque, decide l'ambulatorio.
- **L'appuntamento** tiene la sua sede (`CRM Appointment.centre_location`, scritta in
  `validate`): quella dei suoi ambulatori, altrimenti quella del turno in cui cade,
  altrimenti quella scelta, altrimenti l'unica attiva. Un professionista con il turno a
  Monza e l'ambulatorio a Milano è un conflitto («lavora presso… l'ambulatorio è
  presso…»), qualunque sia la regola sugli orari.
- **Il motore** (`availability.get_slots(location=)`): a una sede, i suoi ambulatori e
  le righe di turno di quella sede (o senza sede); senza sede chiesta e con più sedi,
  ogni sede per conto suo e ogni slot dice dove (`Slot.location`). Un servizio legato
  a un ambulatorio preciso, prenotato in un'altra sede, prende un ambulatorio dello
  stesso tipo lì («Studio 2» a Milano è «un ambulatorio» a Monza): senza, ogni
  servizio andrebbe duplicato per sede.
- **Agenda**: un selettore «Sede» nella barra (sul telefono nel foglio dei Filtri),
  tenuto in `crmAgenda`; le colonne sono gli ambulatori della sede e chi ci lavora quel
  giorno (`get_calendar(with_hours)` dà le sedi del giorno di ciascuno), più chi vi ha
  qualcosa; con «Tutte le sedi» il blocco dice la sede. Il pannello dell'appuntamento
  dice la sede.
- **/prenota**: prima la sede (o «Qualsiasi sede»), poi i servizi che vi si tengono
  (`sedi_regole.sedi_del_servizio`), gli orari di quella sede; con «Qualsiasi sede»
  ogni orario dice dove, e la prenotazione va lì. Spostata, resta nella sua sede.
- **L'indirizzo**: conferma, .ics e link del calendario, la pagina di gestione, l'area
  del cliente e il promemoria via email dicono «Sede di Monza, Via Italia 12, 20900
  Monza (MB)» (`sedi.indirizzo_di`); il promemoria nomina la sede anche in SMS e
  WhatsApp («… presso Sede di Monza»).
- **Accoglienza**: un selettore di sede, che apre sulla **sede abituale** di chi legge
  (Impostazioni > Il tuo account > Preferenze, un default dell'utente).
- **Chiusura di cassa**: una per sede al giorno, più quella di tutto il centro (sede
  vuota, come prima). Le fatture di una sede sono quelle con `CRM Invoice.centre_location`:
  la sede del loro appuntamento, altrimenti la sede abituale di chi le fa.
- **Fatturazione**: una sede che nomina un'azienda emittente la dà alle fatture di
  quella sede che non ne hanno una (`risolvi_azienda`); altrimenti come prima.
- **Dashboard**: un selettore di sede accanto al periodo; contano la sede i widget
  dell'agenda (`staffed_by`) e quelli di quanto fatturato e incassato (`issued(ctx)`).
  Margine, IVA e costi restano del centro intero: le fatture dei fornitori non hanno
  sede, e un margine di una sede sarebbe mezzo numero.
- **La storia**: dato un ambulatorio a una sede, i suoi appuntamenti senza sede ci
  vanno; dati i turni, gli appuntamenti da oggi in poi senza sede vanno nella sede del
  turno. Il resto resta senza sede, e senza sede compare in ogni sede (niente si
  nasconde).
- **Il piano**: si contano gli ambulatori (`AMBULATORI`) come prima; le sedi non
  hanno limite di piano.
- **Dati di prova**: la parte «Due sedi» (Milano con gli ambulatori di sempre, Monza
  con due suoi, l'osteopata a Monza martedì e giovedì), attraverso gli stessi
  documenti delle impostazioni; solo dove il centro non ha sedi sue.

## Lasciato fuori

- Permessi per sede (chi vede solo la propria sede): oggi tutti vedono tutte.
- Prezzi, servizi e orari di apertura del servizio per sede (`CRM Service.availability`
  resta del centro).
- La sede sul pannello di creazione dell'appuntamento come scelta: la decide
  l'ambulatorio o il turno.
- Una numerazione di fatture per sede (resta per azienda emittente).
- Margine/IVA per sede, la vista settimana filtrata per i turni della sede.
