# 44 · Le email

**Stato:** fatto (02/10/2026).

## Il bisogno

Le email che DottorCloud manda avevano ancora la veste del framework: un riquadro
grigio con un pallino colorato accanto al titolo, i link sottolineati nel blu del
browser, i codici in grassetto in mezzo alla frase. Ogni modulo poi le scriveva a
modo suo:

- **il codice per entrare nell'area** o per aprire un documento era una parola in
  grassetto dentro una frase, da cercare;
- **«Entra qui»**, «Apri», «Gestisci»: link nel testo, piccoli sul telefono;
- **il promemoria di un evento** era in inglese («Event Reminder», «Start Time:
  2026-10-02 10:00:00», «1 hour(s)»), con i suoi colori blu;
- **per un'assegnazione, una menzione o un documento condiviso** arrivava l'email
  del framework, che parlava di DocType e di codici e apriva il Desk;
- **una notifica non letta** restava nel pannello: chi non era davanti a
  DottorCloud non lo sapeva;
- le email del framework (la nuova password, il benvenuto, il codice di accesso)
  avevano le sue parole, in parte in inglese.

## Cosa cambia

- **Una veste sola**, quella del marchio (Espresso): lo sfondo chiaro, la carta
  bianca con la coda della nuvola, il titolo grande e stretto, il testo a 15 px.
  Le email di sistema la indossano tutte: i codici, le prenotazioni, le offerte
  della lista d'attesa, i documenti, i moduli da compilare, l'area pazienti, gli
  abbonamenti, gli inviti, la nuova password. Un'email scritta da una persona (la
  risposta a un paziente) resta un'email normale, senza carta e senza firma.
- **In alto il segno del centro**, come nelle sue pagine pubbliche: il suo logo
  dove il programma di posta lo può mostrare (PNG o JPEG, mai SVG), largo da solo,
  quadrato accanto al nome; altrimenti il suo nome. Il logo di DottorCloud sta in
  alto solo per un centro che non ha né logo né nome.
- **Sotto la carta firma il prodotto**: «Powered by DottorCloud», con la sua icona.
  Nel piede della carta la firma dell'account email del centro e il suo indirizzo,
  il link per non ricevere più email e il controllo di lettura dove servono.
- **Un'email chiede una cosa sola, con un pulsante**: nel colore d'azione del
  marchio, con la coda della nuvola, disegnato come tabella perché lo mostrino tutti
  i programmi di posta (anche Outlook): «Entra nella tua area», «Apri il documento»,
  «Conferma o rifiuta», «Gestisci la prenotazione», «Apri l'agenda in DottorCloud».
- **Il codice sta nella sua casella**: grande, spaziato, facile da leggere e da
  copiare.
- **Il promemoria di un evento** è in italiano: il titolo, il giorno e l'ora
  («giovedì 2 ottobre, 10:00»), la descrizione senza HTML, «Inizia fra un'ora» e il
  pulsante che apre l'agenda su quel giorno.
- **Le notifiche arrivano anche per email**, quando restano da leggere: cinque
  minuti dopo, se non l'hai letta in DottorCloud, ti arriva la frase del pannello
  con le prime parole del messaggio e il pulsante che la apre in DottorCloud (la
  persona, la trattativa, Oggi, le Fatture), mai il Desk. Se sono più di una arriva
  un'email sola che le elenca (fino a dieci). Una conversazione arriva una volta
  finché non la leggi, non a ogni messaggio. Quella letta prima non parte.
- **Ognuno sceglie le sue**, in Impostazioni › Il tuo account › Notifiche: menzioni,
  assegnazioni e attività, domande dall'area pazienti, WhatsApp e SMS, agenda,
  fatturazione, automazioni. Ognuno vede solo quelle che può ricevere: la
  fatturazione chi la gestisce, l'agenda chi segna le presenze di tutti, le domande
  dall'area chi legge le bacheche. Di solito sono accese quelle che riguardano solo
  te; i messaggi e la domanda del giorno sull'agenda si leggono in DottorCloud.
  Ogni email dice perché è arrivata e dove cambiare la scelta.
- **Le email del framework** per assegnazioni, menzioni e documenti condivisi non
  partono più: arrivano le notifiche di DottorCloud, con le sue parole.
- **Le parole del framework** nelle sue email (la nuova password, il benvenuto, il
  codice di verifica, l'invito, la richiesta dei propri dati) sono in italiano,
  con la voce di DottorCloud: il tu, le maiuscole dell'italiano, «Reimposta la
  password».
- **Solo il tema chiaro**: nessun programma di posta disegna bene quello scuro, e
  l'email lo dice (`color-scheme: light`).

## Come è fatta

- `crm/templates/emails/standard.html`, `email_header.html`, `email_footer.html`:
  la veste di ogni email, al posto di quella del framework (di cui tiene le classi,
  per i messaggi scritti per lei). La carta c'è quando l'email ha un titolo
  (`header`) o `with_container`; gli stili stanno sugli elementi, perché i
  programmi di posta tengono poco altro, con la specificità che vince quelli del
  framework.
- `crm/posta/aspetto.py`: `contesto_email()` (un metodo Jinja: il segno del centro,
  i colori del marchio che è acceso, la firma), `pulsante(url, testo)` e
  `codice(valore)`, i pezzi che un modulo mette nel suo messaggio; provato in
  `crm/posta/tests/test_aspetto.py`.
- `crm/marchio.py`: `logo_email` e `icona_email` del marchio, in PNG
  (`crm/public/images/email/`).
- `crm/notifiche/posta.py`: le scelte di ognuno (un suo default), chi riceve cosa
  (`riceve()`), `manda_le_email()` ogni cinque minuti, l'indirizzo in DottorCloud
  che una notifica apre, l'email di una e quella di più; `email_due` ed
  `emailed_on` su `CRM Notification`; provato in `crm/notifiche/tests/test_posta.py`.
- `frontend/src/components/Settings/NotificationsSettings.vue`: la pagina delle
  scelte, nel gruppo «Il tuo account».
- `hooks.py`: `notification_skip_email_types` (assegnazioni, menzioni, documenti
  condivisi) e il lavoro ogni cinque minuti.
- I moduli: l'area (`area/accesso.py`, `area/messaggi.py`), i documenti
  (`documenti/consegna.py`), i moduli da compilare (`moduli/richieste.py`), la lista
  d'attesa (`scheduling/attese.py`, `attese_pubblico.py`), gli abbonamenti, la
  prenotazione online (`api/service_booking.py`, `api/booking.py`), gli eventi
  (`api/event.py`), la prova di un extra (`api/plan.py`), l'invito di un collega
  (`crm_invitation`).

Un modulo che manda un'email le dà un titolo (`header`) e `with_container=True`,
scrive il messaggio in paragrafi con le parole sfuggite (`escape_html`), mette la
cosa da fare in un `pulsante()` e un codice in `codice()`. Nessun colore suo:
quelli del marchio vengono dalla veste.

## Verifiche

- Le email rese come le manda il sito e fotografate a 640 px e a 390 px: la
  conferma di una prenotazione, la nuova password, una notifica, il riepilogo di
  più notifiche, il codice dell'area, un'email scritta da una persona; il segno del
  centro col logo largo, con quello quadrato e il nome, col solo nome, con un logo
  SVG (resta il nome) e senza niente (in alto DottorCloud, e sotto nessuna firma).
  Al telefono nessuna esce dai 390 px.
- Nel browser la pagina Notifiche, sul computer e a 390 px, in chiaro e in scuro: la
  scelta resta dopo aver ricaricato.
- `crm.notifiche.tests` (47 test), `crm.posta.tests` e i moduli che mandano email:
  area, documenti, moduli, lista d'attesa, abbonamenti, prenotazioni, eventi,
  inviti, marchio.
