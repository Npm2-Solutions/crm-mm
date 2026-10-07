# 34 — Il menu principale: la giornata del centro, poi il resto

> ✅ **FATTO (01/10/2026), RIFATTO (02/10/2026)**. Il primo riordino aveva
> diciassette voci in quattro gruppi: la giornata, un archivio (Aziende, Note), il
> marketing con le trattative e un gruppo Telefono con "Chiamate" e "Tastierino".
> Il "Tastierino" non era un tastierino: era il giro di chiamate (una coda di
> persone da chiamare una dopo l'altra), e un numero qualsiasi non si poteva
> comporre da nessuna parte. Ora il menu è la giornata in un gruppo solo, poi il
> marketing; quello che non è una voce sta dentro la voce a cui appartiene, e il
> telefono è in alto a destra su ogni pagina. Il 03/10/2026 anche *Oggi* è
> uscita dal menu: è l'**Accoglienza**, una vista dell'agenda (sotto).

## Il menu

```
Notifiche
Agenda · Persone · Conversazioni · Da fare · Trattative · Fatture · Dashboard
MARKETING     Automazioni · Social Planner · Sito web
…
Impostazioni · Comprimi                                   ☎ in alto a destra
```

- **La giornata, nell'ordine in cui si lavora**: l'agenda (con l'accoglienza di
  chi arriva oggi), le persone, rispondere loro, le cose da fare, le trattative,
  le fatture, i numeri.
  Senza etichetta: è il menu. Le trattative stanno qui: sono la vendita di ogni
  giorno, con i suoi preventivi, non il marketing.
- **La dashboard** è l'ultima dove la giornata si apre sull'*Accoglienza*
  (segreteria, professionisti, manager: chi segna gli arrivi) e la prima dove si
  apre sui numeri (amministrazione, marketing, direzione sanitaria).
- **Marketing**: come arrivano le persone nuove: le automazioni, i post, il sito.
- **Ognuno vede solo quello che gli serve**: ogni voce chiede la sua capacità; un
  gruppo senza voci non c'è. La segreteria ha sette voci, un professionista sei,
  il manager dieci (erano tredici, dodici e sedici).

## Quello che non è una voce

Come in Pipedrive (Persone e Organizzazioni) e in Doctolib (la lista d'attesa
dentro l'agenda), le pagine che vivono insieme hanno un selettore nella loro
testata al posto del titolo (`SORELLE` in `utils/menu.js`, disegnato da
`ViewBreadcrumbs`):

| Voce | Selettore |
|---|---|
| Agenda | **Accoglienza · Agenda · Lista d'attesa** |
| Persone | **Persone · Aziende** |
| Da fare | **Da fare · Note** |

Il selettore mostra solo le pagine che il livello apre: una sola, nessun
selettore. Sul telefono tre pagine non stanno accanto ai pulsanti della testata:
lì il nome della pagina aperta è il titolo, e le altre sono nel suo menu
(«Accoglienza ▾»). Una pagina senza voce tiene accesa la voce in cui vive (anche una
persona tiene accese le Persone), nella barra laterale come in quella del
telefono (`utils/navigation.js`).

L'agenda chiama "Programma" (come Google Calendar) la sua vista a elenco, perché
"Agenda" è il nome della pagina.

### L'accoglienza è una vista dell'agenda

*Oggi* era nata come una voce a sé (29/09/2026): la giornata della segreteria,
con la sala d'attesa, gli esiti e le fatture, che la griglia delle ore non ha. Ma
sono gli stessi appuntamenti dello stesso giorno, guardati da chi accoglie invece
che da chi prenota: due voci per la stessa giornata facevano cercare l'agenda in
due posti (osservazione del 03/10/2026). Ora è l'**Accoglienza**, la prima delle
tre viste dell'agenda: chi è atteso, chi è in sala d'attesa, chi è venuto e chi
no, quello che i giorni scorsi hanno lasciato senza esito, quello che resta da
fatturare. Chi segna gli arrivi (`agenda.presenze`) entra lì al mattino
(`LANDINGS` in `router.js`) e passa alla griglia o alla lista d'attesa dal
selettore; l'agenda resta accesa nel menu su tutte e tre. La pagina tiene il nome
della rotta (`Today`) e il vecchio indirizzo (`/oggi`, alias di `/accoglienza`):
i link già mandati, le notifiche e le email continuano ad aprirla.

## Il telefono a portata di mano

Chiamare è una cosa che si fa, non un posto (le linee guida di Apple sulle barre,
GoHighLevel, HubSpot e Close hanno il telefono in alto, non nel menu). Dove una
telefonia è accesa, chi chiama o legge le chiamate ha un ☎ in alto a destra su
ogni pagina, con il numero dei richiami dovuti adesso. Si apre sotto il pulsante
sul computer, dal basso sul telefono (`components/Telephony/PhoneButton.vue`,
`PhonePanel.vue`):

- **Un numero o un nome**: il nome cerca le persone che si leggono, con un numero
  (`crm.telephony.pannello.find_people`, anche per le ultime cifre scritte con
  spazi o prefisso); un tocco mette il numero nel tastierino.
- **Il tastierino** e **Chiama**: la chiamata parte con la telefonia del centro,
  dopo il sì del server.
- **Da richiamare adesso**: i richiami promessi dalla segreteria telefonica.
- **Le ultime chiamate** che si leggono (`telefono.registro`), le perse in rosso,
  ciascuna con la sua persona e un pulsante per richiamare.
- **Tutte le chiamate** (il registro) e **Giro di chiamate** (la coda, che prima
  si chiamava "Tastierino"); il giro parte anche dal registro.

## Sul telefono

La barra in basso prende i primi quattro posti dello stesso menu: l'agenda (con
l'accoglienza dentro), le persone, le conversazioni, le fatture prima del resto.
Segreteria e manager hanno *Agenda · Persone · Chat · Fatture*, un professionista
*Agenda · Persone · Chat · Da fare*; l'amministrazione *Agenda · Persone · Fatture ·
Dashboard*; il marketing *Persone · Dashboard · Da fare · Trattative*. «Altro»
apre la pagina con il resto del menu (`pages/Altro.vue`). Il ☎ sta nella testata,
accanto alle azioni della pagina.

## Come è fatto

- `frontend/src/utils/menu.js`: il menu come dati, puro (gruppi, voci, icona, chi le
  vede), le pagine sorelle; `menuDi()`, `paginaSorelle()`, `barraDelTelefono()`.
- `AppSidebar.vue` lo disegna, `MobileBottomNav.vue` ne prende la barra, con le
  stesse icone (`components/Icons/menu.js`); `ViewBreadcrumbs.vue` disegna il
  selettore delle sorelle (sul telefono, con tre sorelle, un titolo con il menu).
- `crm/telephony/pannello.py`: le ultime chiamate e i richiami (`get_phone_panel`),
  le persone da chiamare (`find_people`); `composables/pannelloTelefono.js` le
  chiede una volta per tutta l'app, di nuovo ogni tre minuti e quando la finestra
  torna in primo piano; `utils/telefono.js` le regole pure del tastierino.

## Test

- `tests/unit/menu.test.js`: il menu di ogni livello parola per parola, la
  dashboard prima o ultima, il telefono e le pagine sorelle mai voci, le sorelle
  di ogni livello, ogni pagina nel router; la barra del telefono di ogni livello,
  mai più di quattro posti.
- `tests/unit/navigation.test.js`: la voce accesa dentro la sua sezione
  (l'agenda sull'accoglienza e sulla lista d'attesa).
- `tests/unit/telefono.test.js`: il tastierino, numero o nome, quando una chiamata.
- `crm/telephony/tests/test_pannello.py`: le ultime chiamate con la loro persona e
  le perse, le persone trovate per nome e per numero comunque scritto, nessuna per
  chi non chiama.
- Nel browser, in italiano, sul computer e sul telefono: il menu, i selettori, il
  pannello del telefono con la ricerca e le chiamate.
