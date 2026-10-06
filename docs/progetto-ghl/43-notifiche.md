# 43 · Le notifiche

**Stato:** fatto (02/10/2026).

## Il bisogno

Il pannello delle notifiche era quello del progetto da cui DottorCloud è nato: una
lista unica, tutta, senza giorni, ogni riga col viso di chi la manda o il logo di
WhatsApp, le frasi scritte con le classi dello schermo dentro i dati. Sotto c'erano
anche dei difetti veri:

- **una fattura scartata non si apriva**: la notifica portava alla scheda di una
  persona che non c'era;
- **sul telefono ogni link era sbagliato** (`#undefined` in coda all'indirizzo),
  «sono venute?» non portava a Oggi, e il conteggio restava fermo finché non si
  apriva la pagina;
- **dieci messaggi WhatsApp erano dieci notifiche**;
- **«Segna tutto come letto»** salvava le notifiche una per una, e ognuna
  ricaricava la lista: duecento notifiche, duecento ricariche;
- **chi ha il livello «Sola lettura» non poteva segnarle lette** (il campo
  dell'utente aveva il nome sbagliato);
- **la lista arrivava tutta, sempre**, con una lettura del nome di chi la manda per
  ogni riga;
- le frasi erano scritte nella lingua di chi faceva l'azione, non di chi legge;
  quella di un'attività assegnata era fatta di due pezzi incollati;
- una domanda dall'area paziente apriva la scheda Clinica invece dell'area;
- il messaggio di un'automazione sembrava un'assegnazione;
- gli eventi «Iniziano adesso», «In corso» e «In arrivo» erano in inglese, e un
  evento dalle 10:00 alle 11:00 si leggeva «10 - 11».

## Cosa cambia

- **Il pannello** è nuovo, nel sistema Espresso. In alto il titolo e quante sono
  da leggere nel verde tenue del marchio, «Segna tutto come letto» e la croce per
  chiuderlo. Sotto si sceglie fra «Tutte», «Da leggere» ed «Eventi». Le notifiche
  stanno sotto i loro giorni: Oggi, Ieri, Questa settimana, Prima.
- **Ogni notifica dice di che tipo è** con il suo segno: una nuvola del colore della
  sua categoria con l'icona. Una menzione è ambra con la chiocciola; un'assegnazione
  o un'attività sono nel colore del marchio, e quando vengono tolte sono grigie;
  WhatsApp è verde; SMS, area paziente e fatturazione sono blu; un'automazione è
  viola; l'agenda è ambra. Quando la manda una persona c'è il suo viso, col segno
  piccolo nell'angolo.
- **Il testo** è la frase con i nomi in grassetto. Sotto ci sono le prime parole
  del messaggio di cui parla (il commento, il WhatsApp o l'SMS, il dettaglio della
  fattura) e poi l'ora e il tipo. Una riga da leggere ha il pallino del marchio.
  Leggerla, o rimetterla da leggere, ha un pulsante suo, visibile anche sul
  telefono.
- **Si apre dove serve**: la persona o la trattativa, sul commento o sul messaggio
  di cui parla, segnato per un momento da un anello del marchio, anche se la scheda
  era rimasta sulle email; le attività finché sono tue; l'area paziente; Oggi per
  «sono venute?»; le Fatture. Se la persona non c'è più, la notifica non apre
  niente.
- **I messaggi della stessa persona si sommano** finché non li leggi: «Hai ricevuto
  3 messaggi WhatsApp da Laura».
- **Quello che non dà nessuno del centro non ha un nome davanti**: un'automazione,
  una regola di assegnazione, un lavoro in coda assegnano come Administrator, una
  persona che scrive dal sito come Guest. La notifica dice «Hai una nuova cosa da
  fare: …», «Ora segui tu Laura Bianchi», mai «Administrator ti ha assegnato…»
  (`regole.SENZA_CHI`, 05/10/2026).
- **Quando ne arriva una** compare un avviso nel blocco verde profondo del marchio,
  come nel video, con il segno del tipo, la frase, le prime parole e «Apri». Non
  compare se il pannello o la pagina delle notifiche sono già aperti. Sul telefono
  il pallino sta su «Altro».
- **La lingua è quella di chi legge**: la frase resta in inglese con i suoi nomi a
  parte e viene tradotta quando la si legge. Quelle scritte prima prendono la
  frase di oggi (03/10/2026): un messaggio, una menzione, un'assegnazione o una
  domanda dall'area dicono la persona per nome, non più «in lead
  CRM-LEAD-2026-00397»; le parole di un'automazione restano sue.
- **Dopo sei mesi se ne vanno**, lette o no (Impostazioni dei log).

## Sul telefono e sul computer (05/10/2026)

Le notifiche arrivano anche fuori da DottorCloud, nella barra del telefono o
del computer, appena vengono scritte: le notifiche push dei browser (Web Push),
senza nessuno in mezzo che le legga.

- **Si attivano da sé, per dispositivo**: Impostazioni > Il tuo account >
  Notifiche, «Su questo dispositivo», «Attiva le notifiche qui». Il browser chiede
  il permesso, e da lì ogni notifica del pannello arriva anche lì. Sull'app del
  telefono la pagina «Altro» lo offre con un tocco. Su iPhone e iPad le riceve solo
  l'app sulla schermata Home (regola di Safari): la pagina lo spiega, con i due
  tocchi per metterla lì. «Mandami una prova» ne manda una ai propri dispositivi;
  l'elenco dice quali li ricevono e si tolgono uno a uno.
- **Quali**: per ogni gruppo (menzioni, assegnazioni, messaggi, agenda…) un
  interruttore «Email» e, appena un dispositivo le riceve, uno «Dispositivi»,
  tutti accesi finché non si spengono. Mai sui dati di prova.
- **Cosa dicono**: la frase del pannello nella lingua di chi le riceve, le prime
  parole del messaggio dove le può leggere; toccata, apre DottorCloud sulla pagina
  della notifica e la segna letta. I messaggi della stessa conversazione prendono
  il posto l'uno dell'altro. Una notifica arrivata su un dispositivo non parte più
  anche per email.
- **Come**: il messaggio è cifrato per quel solo browser (RFC 8291) e firmato con
  la chiave del sito (VAPID, RFC 8292); lo porta il servizio di chi fa il browser
  (Google, Apple, Mozilla, Microsoft) e solo a quei servizi si scrive. Un
  dispositivo che il servizio non conosce più si dimentica da solo. Il service
  worker sta sulle pagine di DottorCloud (`/crm`), mostra la notifica e apre la
  pagina: non tiene niente in cache.

## Chi la riceve, quando, e dove porta un tocco (06/10/2026)

- **Un messaggio arriva sempre a qualcuno.** Un WhatsApp, un SMS o un'email di una
  persona lo legge chi la segue (a chi è assegnata), altrimenti chi ce l'ha (il
  proprietario della persona o della trattativa), altrimenti la segreteria: chi nel
  centro legge le conversazioni e può aprire quella persona, mai l'agenzia
  (`avvisi.chi_segue()`). Prima lo leggeva solo chi era assegnato: un numero nuovo
  che scriveva su WhatsApp, o una persona di nessuno, non lo diceva a nessuno.
  Un'email arrivata nella casella personale di qualcuno lo dice solo a lui.
- **Quando**: subito nel pannello e, se DottorCloud è aperto, nell'avviso a
  comparsa; sul telefono e sul computer solo dove le notifiche sono attivate e il
  tipo è acceso; per email dopo cinque minuti se è ancora da leggere e la si vuole
  (i messaggi, di solito, no). Mai fuori dal pannello per i dati di prova. Chi
  scrive non avvisa se stesso; un utente disattivato non le riceve.
- **Un tocco apre ciò di cui parla**, uguale dal pannello, dall'avviso, dalla
  notifica del telefono e dall'email: la persona sul messaggio; le cose da fare
  finché sono tue, e una cosa da fare senza persona apre l'elenco su di lei; un
  messaggio in segreteria di un numero che nessuno conosce apre il registro delle
  chiamate su quella chiamata; un avviso di Twilio apre Impostazioni > Telefono; una
  fattura ricevuta apre le Fatture su di lei; l'agenda apre l'Accoglienza. Solo una
  notifica che non ha un posto apre le notifiche.
- **L'avviso a comparsa si apre da tutto l'avviso**, non solo da «Apri»; una
  passata col dito lo chiude e non apre niente.
- **Sul telefono**: la notifica toccata porta DottorCloud in primo piano e gli dice
  dove andare, senza ricaricare; se la pagina non risponde entro due secondi e
  mezzo (addormentata, o di una versione di prima) viene caricata lì.

## Come è fatta

- `crm/notifiche/avvisi.py`: `avvisa()`, la porta da cui entra ogni notifica. Ci
  passano le menzioni, le assegnazioni, le attività, WhatsApp, gli SMS, l'agenda,
  l'area paziente, la fatturazione e le automazioni. Una notifica uguale non ancora
  letta non viene scritta due volte; un messaggio della stessa persona prende il
  posto della notifica precedente col conto.
- `crm/notifiche/regole.py`: le frasi, la frase con i nomi, le parole di quelle
  scritte prima e la frase che dicevano (`frase_di_prima()`: dal tipo e da che
  cosa riguardano, in inglese o in italiano, il nome di un'attività non conta), il
  tipo, senza sito; provato in `tests/test_regole.py`, che controlla anche che ogni
  frase sia nel catalogo italiano con gli stessi posti.
- La patch `the_old_notifications_name_the_person` dà a quelle scritte prima la
  frase e i nomi di oggi; una su qualcosa che non c'è più resta com'era.
- `crm/notifiche/api.py`: una pagina alla volta col conto da leggere; per ogni riga
  il percorso, deciso sul server; letta, tutte lette o di nuovo da leggere con una
  query sola e un segnale solo alle altre schede.
- `CRM Notification`: `sentence`, `sentence_args`, `count`, il tipo «Automation»,
  l'indice per utente e data, `clear_old_logs`.
- `frontend/src/components/Notifications/` (il segno, la riga, la lista),
  `Notifications.vue` (il pannello), `pages/MobileNotification.vue`,
  `stores/notifications.js`, `composables/notifiche.js` (l'ascolto, una volta per
  layout, e l'avviso); `utils/notifiche.js`, provato in `tests/unit/notifiche.test.js`.
- `composables/conversationScroll.js` (`target`): la conversazione si apre sul
  messaggio indicato dall'indirizzo.
- Le push: `crm/notifiche/spinta_regole.py` (cifrare, firmare, il nome del
  dispositivo, senza sito, provato sull'esempio della RFC 8291 byte per byte),
  `crm/notifiche/spinta.py` (le chiavi del sito in `FCRM Settings`, i dispositivi
  in `CRM Push Subscription`, l'invio in coda dopo `avvisa()`, il service worker
  servito su `/api/method/…` con `Service-Worker-Allowed: /crm`),
  `crm/notifiche/spinta_sw.js`; nel browser `utils/spinta.js` (provato),
  `composables/spinta.js`, `Settings/NotificationsSettings.vue`,
  `Mobile/NotificheSulTelefono.vue`; il router segna letta la notifica toccata
  (`?notifica=`).

## Verifiche

- Nel browser, sul computer e a 390 px, in chiaro e in scuro: il pannello con tutti
  i tipi, «Da leggere», «Segna tutto come letto», Esc. Una notifica WhatsApp apre
  la persona sul messaggio anche se la scheda era rimasta sulle email. L'avviso
  arriva in tempo reale e «Apri» porta al messaggio.
- `crm.notifiche.tests` (33 test) e i moduli che scrivono notifiche: area, agenda,
  automazioni, WhatsApp, permessi, sola lettura.
