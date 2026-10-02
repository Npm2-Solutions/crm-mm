# 34 — Il menu principale: la giornata del centro, poi il resto

> ✅ **FATTO (01/10/2026)**. Il menu della barra laterale era una colonna di
> diciassette voci senza gruppi, in un ordine nato una pagina alla volta (Persone,
> Trattative, Aziende, Conversazioni, Automazioni, Note, Da fare, Oggi,
> Agenda…), metà in inglese. Ora è la giornata del centro in cima, poi l'archivio,
> il marketing e il telefono, con le etichette piccole del design system; tutto in
> italiano, con la clinica i pazienti. La barra del telefono viene dallo stesso
> menu, e le impostazioni hanno una voce loro.

## Il menu

```
Notifiche
Dashboard · Oggi · Agenda · Lista d'attesa · Persone · Conversazioni · Da fare · Fatture
ARCHIVIO      Aziende · Note
MARKETING     Trattative · Automazioni · Social Planner · Sito web
TELEFONO      Chiamate · Tastierino
…
Impostazioni · Comprimi
```

- **In cima la giornata**: quello che la segreteria, i professionisti e il manager
  aprono ogni giorno, nell'ordine del lavoro (chi arriva, l'agenda, chi aspetta un
  posto, le persone, i messaggi, le cose da fare, le fatture). Senza etichetta: è il
  menu.
- **Archivio**: le aziende e le note, che si cercano quando servono.
- **Marketing**: come arrivano le persone nuove: le trattative, le automazioni, i post,
  il sito.
- **Telefono**: le chiamate, e il tastierino dove la telefonia è accesa.
- **Ognuno vede solo quello che gli serve**: ogni voce chiede la sua capacità, come
  prima; un gruppo senza voci non c'è. Il marketing vede la dashboard, le persone
  (con email e telefono mascherati), le aziende e il suo gruppo; l'amministrazione
  la dashboard, l'agenda, le persone e le fatture; la direzione sanitaria l'agenda
  e i pazienti.
- **Le parole**: "Persone", anche con la clinica: nell'elenco c'è chiunque il centro
  abbia sentito, chi ha chiesto, un genitore, il contatto di un'azienda, non solo i
  pazienti (02/10/2026); "Da fare" per le attività (non "Attività", che è la
  cronologia della persona), "Aziende", "Chiamate", "Tastierino".
- **Le impostazioni** hanno una voce in fondo alla barra (sul telefono in fondo al
  cassetto): prima si trovavano solo nel menu sotto il nome.
- **Dove si arriva**: senza una vista predefinita propria, chi ha la giornata
  (segreteria, professionisti, manager) arriva su *Oggi*; chi guarda il centro
  dall'alto (amministrazione, marketing, direzione) sulla dashboard.

## Sul telefono

La barra in basso prende i primi quattro posti dello stesso menu: la giornata, le
persone, le conversazioni, le fatture prima del resto. Segreteria, professionisti
e manager hanno *Oggi · Agenda · Persone · Chat*; l'amministrazione *Agenda ·
Persone · Fatture · Dashboard*. "Altro" apre il cassetto con tutto il menu.

## Come è fatto

- `frontend/src/utils/menu.js`: il menu come dati, puro (gruppi, voci, icona, chi le
  vede); `menuDi()`, `barraDelTelefono()`.
- `AppSidebar.vue` lo disegna, `MobileBottomNav.vue` ne prende la barra, con le
  stesse icone (`components/Icons/menu.js`); `utils/navigation.js` tiene accesa la
  scheda della barra dentro la sua sezione (una persona tiene accese le Persone).
- Le etichette di gruppo come le vuole il design system (piccole, maiuscole).

## Test

- `tests/unit/menu.test.js`: il menu di ogni livello parola per parola (manager,
  segreteria, professionista, marketing, amministrazione, direzione sanitaria), il
  tastierino solo con la telefonia, nessun gruppo vuoto, ogni pagina una volta e
  con un'icona, ogni pagina nel router; la barra del telefono di ogni livello, mai
  più di quattro posti.
- `tests/unit/navigation.test.js`: la scheda accesa con la barra che segue il menu.
- Nel browser, in italiano: il menu dei sei livelli e la pagina d'arrivo di
  ciascuno; la barra e il cassetto del telefono.
