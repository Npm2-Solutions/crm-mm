# 56 · L'agenda che si legge: il giorno del centro, la settimana di uno, il mese

**Stato:** fatto (06/10/2026).

## Il bisogno

«Si legge malissimo il calendario». L'agenda aveva due pagine in una, con due
barre diverse:

- **Calendario** (il calendario di frappe-ui): giorno e settimana mettevano tutti i
  professionisti nella stessa colonna, gli appuntamenti uno sopra l'altro a
  cascata («Controllo nutrizionale — Ilaria…»); il mese due titoli e «altri 28».
  Il campo per vedere gli impegni di un collega diceva «John Doe».
- **Programma** (una colonna per professionista): un appuntamento di mezz'ora era
  alto 33 px, ci stavano l'ora e metà della seconda riga. Il titolo era «Servizio
  — Persona» tagliato a metà, così **il nome della persona non si leggeva mai**; la
  terza riga (la stanza) usciva dal blocco. Colonne senza larghezza minima (nove
  professionisti, 127 px l'una), nomi tagliati («David…»), sotto il nome l'email o
  «Administrator», colonne di chi quel giorno non lavora. I turni il motore li
  conosce, ma la griglia non li mostrava: libero e chiuso avevano lo stesso bianco.
- **I controlli**: cinque filtri su una riga intera sopra ogni giorno, lo zoom solo
  nel Programma, «Collega Google Calendar» tra i comandi di tutti i giorni; nelle
  impostazioni solo la «Vista predefinita», che valeva per il Calendario e non per
  il Programma.

Il design system diceva già come va un appuntamento (AgendaEvent, nella
`brand/design-system/espresso`): l'orario piccolo nel colore della categoria,
**il nome della persona** come titolo, sotto «Visita cardiologica · Studio 2».

## Come funziona

### Le viste

- **Giorno** (si apre lì): una colonna per professionista (o per ambulatorio, dal
  menu Vista). Si vedono chi lavora quel giorno e chi ha qualcosa in agenda; gli
  altri con «Mostra chi non lavora». Ogni colonna è larga almeno 11rem (9rem sul
  telefono): quando non ci stanno, scorrono di lato sotto le loro intestazioni,
  mentre le ore restano ferme a sinistra. In testa alla colonna il nome intero,
  l'orario di quel giorno («08:30–13:00 · 14:00–19:00», su due righe quando non
  ci sta, mai tagliato a metà di una fascia; una fascia più larga della colonna
  finisce con i puntini), il motivo di un'eccezione («Ferie») o «Non lavora», e
  quanti appuntamenti ha. Sul telefono, anche di traverso, il nome prende il
  posto della faccia.
- **Settimana**: i giorni di **un** professionista (o di un ambulatorio), scelto
  con lo stesso pulsante «di chi» (da un giorno con uno solo spuntato, la
  settimana è sua; altrimenti la propria, se si è un professionista). Da lunedì a
  venerdì, sabato e domenica quando lavora o ha qualcosa. Un tocco
  sull'intestazione di un giorno apre quel giorno. Sette giorni con tutti i
  professionisti insieme non si leggono: per quello c'è il Giorno.
- **Mese**: ogni giorno con quanti appuntamenti ha e i primi tre per orario e
  persona, poi «altri N»; un tocco sul giorno lo apre, su una riga apre
  l'appuntamento. Sul telefono il numero e quanti ne ha.
- **Telefono**: il giorno si apre come elenco (come prima); Giorno e Mese sono una
  scelta più in là, la Settimana no (sette colonne su un telefono non dicono niente).
  La vista si sceglie da un tasto alto come gli altri della riga («Lista»,
  «Giorno», «Mese», con la sua icona), le viste in un foglio dal basso; «di chi»
  dice «Tutti» accanto all'icona che dice di chi, Filtri e Vista sono le loro
  icone (con il loro nome per chi legge con lo schermo): una riga sola, che ci
  sta anche a 320 px.

Un indirizzo con una data (una notifica, «Prenota» dalla scheda di una persona)
apre quel giorno nella vista Giorno.

### L'appuntamento

`components/Calendar/BloccoAgenda.vue`, con le regole in `utils/agenda.js`.

- **Prima la persona**, poi cosa e dove: «09:00 Mario Rossi» e sotto «Visita ·
  Studio 2». In una colonna di professionista dice la stanza, in una di
  ambulatorio il professionista. Una lezione si chiama con il suo servizio e
  conta le persone («Pilates di gruppo», «6 persone»).
- **Righe intere**, mai mezza: ogni riga è alta 16 px e il blocco ne mostra quante
  la sua altezza ne contiene (`righeDelBlocco`). Meno di una riga: orario e nome in
  piccolo; una riga: «09:00 Mario Rossi · Visita · Studio 2»; due: orario e nome,
  poi cosa e dove; tre: l'orario «09:00 – 09:30», il nome, cosa e dove; da quattro
  cosa e dove su righe separate, e le note in quelle che restano.
- **I segni**, ognuno un'icona con le sue parole (il nome per chi legge con lo
  schermo e il suggerimento del puntatore): conflitto, confermato, in sala
  d'attesa (qualcuno dell'appuntamento ha fatto il check-in), completato, non
  venuto, prima visita, prenotato online o su una piattaforma. La prima visita è
  anche il blocco pieno del marchio, quello in corso l'anello con la croce
  («Adesso · 15:30–16:15»; sul telefono, dove la colonna è stretta, croce e
  anello bastano e l'orario resta intero; nel tema scuro, sul blocco menta,
  barretta, croce e anello interno prendono l'inchiostro scuro delle sue
  parole), un annullato grigio e barrato.
- **Gli annullati** non occupano il posto che hanno liberato: non si disegnano,
  tranne con «Mostra gli appuntamenti annullati» o quando il filtro di stato li
  chiede. L'elenco del telefono li mostra sempre, con il loro stato.
- **Colori**: per servizio (il colore del servizio) o per stato (prenotato,
  confermato, in sala d'attesa, completato, non venuto, annullato), con la
  legenda nel menu Vista: un colore non dice mai niente da solo.

### La griglia

`components/Calendar/GrigliaAgenda.vue`, le colonne e quello che disegnano da
`cosePerColonna` (`utils/agenda.js`).

- **Le ore che mostra**: dalla prima apertura all'ultima chiusura delle colonne
  che disegna, a ore intere, allargate da quello che è prenotato fuori;
  08:00–20:00 dove nessuno ha orari. Tre altezze per l'ora: Compatta (72 px),
  Normale (96 px), Ampia (144 px); da Normale in su le mezze ore tratteggiate.
- **Fuori turno** a righe diagonali chiare; il tempo occupato da quello che non si
  può leggere («Occupato») e gli impegni di un collega («Impegno»: quando, mai
  cosa) come fasce tratteggiate. I propri eventi stanno nella propria colonna
  (aggiunta in testa a chi non è un professionista, «I tuoi impegni»), quelli di
  tutto il giorno sopra le ore.
- **Adesso**: una linea sola attraverso il giorno e l'ora scritta nella colonna
  delle ore; passa sotto gli appuntamenti, perché sopra un nome lo barrava come
  un annullato (quello in corso ha già l'anello e la croce). All'apertura le ore
  scorrono a un'ora e mezza prima di adesso, o al primo appuntamento del giorno.
- **Un orario libero** apre un appuntamento nuovo (o un evento, come l'ultima
  volta) per quella colonna, all'orario toccato, arrotondato al **passo della
  griglia**. Solo dove chi legge può prenotare: un professionista prenota nella
  sua agenda (`agenda.prenota` sui suoi), e la colonna di un collega non apre
  niente né accoglie un appuntamento trascinato, come il server rifiuterebbe. **Trascinare** un appuntamento (non con un dito: sul telefono e sul
  tablet l'orario si cambia dal pannello) lo sposta all'orario e alla colonna
  dove cade, con lo stesso punto preso in mano; nella settimana in un altro
  giorno.

### La barra

Una sola per tutte le viste: ‹ Oggi › e la data (un tocco apre il calendario per
scegliere il giorno), quanti appuntamenti e impegni ci sono, poi Giorno ·
Settimana · Mese, **di chi** («Tutti i professionisti», alcuni spuntati, uno solo
nella settimana), **Filtri** (servizi, ambulatori o professionisti, stato,
sorgente, quanti sono attivi accanto) e **Vista**. «Nuovo» resta nell'intestazione.
Esc chiude il pannello di un appuntamento come quello di un evento (chiedendo
prima se c'è qualcosa di scritto da scartare; dentro un campo non fa niente).

### Le configurazioni

- **Di chi legge**, nel suo browser (menu Vista): colonne per professionista o per
  ambulatorio, altezza delle ore, colori per servizio o per stato, chi non lavora,
  gli annullati, l'ultima vista usata, di chi sono il giorno e il mese (chi è
  spuntato in «di chi»; «Azzera tutto» torna a tutti) e di chi è la settimana.
  Chi vede solo la propria agenda (un professionista) apre sulla propria colonna
  finché non sceglie altri; chi se n'è andato esce dalla scelta da solo. Dal menu anche
  «Impostazioni dell'agenda» e «Il tuo Google Calendar» (Il tuo account), che
  prima era un pulsante nell'intestazione.
- **Del centro**, in Impostazioni > Agenda > Agenda e promemoria:
  la **vista iniziale** (Giorno, Settimana, Mese: dove si apre finché qualcuno non
  ne sceglie un'altra; una pagina aperta prima che arrivino le impostazioni la
  prende quando arrivano) e il **passo della griglia** (5, 10, 15 o 30 minuti), più i
  promemoria degli eventi come prima. Gli orari mostrati non sono
  un'impostazione: vengono dagli orari del centro e dai turni (Impostazioni >
  Agenda > Orari e turni).

### Il server

`crm.api.appointments.get_calendar(..., with_hours=1)`, per un giorno o una
settimana, aggiunge:

- `hours`: per ogni professionista dei servizi e ogni ambulatorio, giorno per
  giorno, le finestre aperte in minuti dell'orologio del centro
  (`{"open": [[480, 780]], "note": "Ferie"}`), calcolate dal motore che prenota
  (`staff_working_hours`, `resource_working_hours`: turni, eccezioni, festivi;
  `orari_di`), prese anche dai giorni accanto quando il fuso dell'agenda non è
  quello del centro; `null` dove nessuno ha mai messo orari (aperto sempre).
- `engaged`: gli eventi dei professionisti come tempo occupato, con il loro nome
  (per non disegnare due volte un evento che chi legge vede intero) e chi
  riguardano, mai l'oggetto.

Un mese non li chiede.

## File

- `frontend/src/utils/agenda.js` (puro, provato in `tests/unit/agenda.test.js`):
  altezze e righe, testo e segni del blocco, colori per stato, orari e chiusure
  di una colonna, le ore della griglia, colonne del giorno e giorni della
  settimana, periodi ed etichette, cosa sta in ogni colonna e in ogni giorno del
  mese.
- `frontend/src/components/Calendar/`: `GrigliaAgenda.vue`, `BloccoAgenda.vue`,
  `MeseAgenda.vue`, `ChiNellAgenda.vue`, `FiltriAgenda.vue`, `VistaAgenda.vue`,
  `VistaDelTelefono.vue` (le viste sul telefono); la
  pagina `frontend/src/pages/Calendar.vue`. Via `ResourceScheduler.vue` e il
  calendario di frappe-ui da questa pagina.
- `frontend/src/espresso-componenti.css`, sezione 12: il blocco
  (`dc-evento__ora`, `__chi`, `__dettagli`, `--sottile`, `--impegno`), le fasce
  chiuse e occupate, la larghezza minima delle colonne.
- `crm/api/appointments.py` (`_giornate`, `orari_di`, `_impegni`), provato in
  `crm/tests/test_scheduling.py`; `FCRM Settings.calendar_grid_step`, la pagina
  `Settings/CalendarSettings.vue`.
