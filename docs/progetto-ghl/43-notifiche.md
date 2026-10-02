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
- **Quando ne arriva una** compare un avviso nel blocco verde profondo del marchio,
  come nel video, con il segno del tipo, la frase, le prime parole e «Apri». Non
  compare se il pannello o la pagina delle notifiche sono già aperti. Sul telefono
  il pallino sta su «Altro».
- **La lingua è quella di chi legge**: la frase resta in inglese con i suoi nomi a
  parte e viene tradotta quando la si legge. Quelle scritte prima si leggono allo
  stesso modo.
- **Dopo sei mesi se ne vanno**, lette o no (Impostazioni dei log).

## Come è fatta

- `crm/notifiche/avvisi.py`: `avvisa()`, la porta da cui entra ogni notifica. Ci
  passano le menzioni, le assegnazioni, le attività, WhatsApp, gli SMS, l'agenda,
  l'area paziente, la fatturazione e le automazioni. Una notifica uguale non ancora
  letta non viene scritta due volte; un messaggio della stessa persona prende il
  posto della notifica precedente col conto.
- `crm/notifiche/regole.py`: le frasi, la frase con i nomi, le parole di quelle
  scritte prima e il tipo, senza sito; provato in `tests/test_regole.py`, che
  controlla anche che ogni frase sia nel catalogo italiano con gli stessi posti.
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

## Verifiche

- Nel browser, sul computer e a 390 px, in chiaro e in scuro: il pannello con tutti
  i tipi, «Da leggere», «Segna tutto come letto», Esc. Una notifica WhatsApp apre
  la persona sul messaggio anche se la scheda era rimasta sulle email. L'avviso
  arriva in tempo reale e «Apri» porta al messaggio.
- `crm.notifiche.tests` (33 test) e i moduli che scrivono notifiche: area, agenda,
  automazioni, WhatsApp, permessi, sola lettura.
