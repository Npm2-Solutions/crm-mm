# 54 · Una persona, due porte: il Riepilogo, la chat, la lista Persone

**Stato:** fatto (06/10/2026).

## Il bisogno

Le parole dell'utente: «io ho la mia lista dei contatti che sono sia i lead, sia i
pazienti, è un po' tutto insieme [...] se io ho la mia lista contatti, io entro su
un contatto, mi aspetto di vedere i dati del mio contatto, non di avere la chat
forse, però è anche comodo [...] perché io entro e vedo subito i messaggi [...]
o troviamo una vista unica, sempre la stessa, oppure dividiamo veramente le due
cose». La via più semplice, diretta e veloce.

## Com'era

- La lista si chiamava già **Persone** (doc 21: una persona sola, «lead» è uno
  stadio), ma l'indirizzo era `/crm/leads`, il primo stadio si leggeva
  «Contatto» come la vecchia rubrica dei «Contatti», e il filtro sullo stadio era
  una tendina tra gli altri filtri.
- La scheda della persona si apriva sull'ultima scheda lasciata, di solito la
  conversazione: chi entrava per sapere «quando torna?», «quanto deve?» trovava
  la chat; chi entrava per rispondere da Conversazioni trovava nella colonna di
  destra solo nome, recapiti e assegnatario.

## Cosa fanno gli altri

- **Una sola lista di persone, con lo stadio**: GoHighLevel (un solo elenco di
  contatti, tipo Lead/Cliente e liste filtrate,
  [Contact Types](https://help.gohighlevel.com/support/solutions/articles/155000001302-contact-types)),
  HubSpot (fase del ciclo di vita sul contatto,
  [lifecycle stages](https://knowledge.hubspot.com/records/use-lifecycle-stages)),
  respond.io ([lifecycle](https://respond.io/help/workspace-settings/workspace-settings-lifecycle)).
  Dove esiste una lista «Leads» a parte (HubSpot
  [Leads](https://knowledge.hubspot.com/records/create-leads), Pipedrive
  [Leads Inbox](https://support.pipedrive.com/en/article/leads-inbox)) è
  un'occasione di vendita legata alla persona: da noi la trattativa.
- **La casella dei messaggi e la scheda, collegate**: la casella per lavorare i
  messaggi, con accanto un pannello della persona (GoHighLevel,
  [right panel](https://help.gohighlevel.com/support/solutions/articles/155000001321-right-panel-expandable-sidebar-in-conversations);
  Intercom, [profili](https://www.intercom.com/help/en/articles/6988783-get-context-fast-with-user-and-company-profiles));
  la scheda per il quadro completo. I CRM nati per i messaggi aprono la scheda
  sulla chat (GoHighLevel,
  [contact detail page](https://help.gohighlevel.com/support/solutions/articles/155000006651-the-all-new-contact-detail-page)),
  i gestionali su un riepilogo (Jane,
  [patient profile dashboard](https://jane.app/guide/patient-profile-dashboard):
  prenotazioni, assenze, ultima visita, saldo; SimplePractice, «Overview»).
- **Pacchetti e abbonamenti** stanno vicino alle prenotazioni quando sono sedute
  da consumare (Practice Better,
  [client records](https://help.practicebetter.io/hc/en-us/articles/41912588997275-Working-with-Client-Records-in-Practice-Better);
  Doctolib Kiné,
  [dossier patient](https://community.doctolib.fr/t/nouvelle-fonctionnalite-doctolib-kine-le-dossier-patient-fait-peau-neuve/54930)).

## La scelta

Tra «una vista unica», «una persona, due porte» e «una separazione netta»,
l'utente ha scelto **una persona, due porte**, e la lista **Persone**:

- **una sola scheda della persona**, la stessa da Persone, dall'agenda, da
  Conversazioni e dalle notifiche, con due facce: **Riepilogo** e **Chat**;
- **la porta decide la faccia**: da Persone, dall'agenda, da una ricerca o da un
  link qualsiasi si apre sul Riepilogo; da Conversazioni e dalla notifica di un
  messaggio sulla chat. Un tocco per passare dall'una all'altra;
- **Conversazioni resta la coda dei messaggi** (da leggere, in attesa, gestite),
  con il Riepilogo accanto alla chat;
- **la lista resta Persone**, il primo stadio si legge **Lead**, in cima le viste
  **Tutti · Lead · Clienti · Pazienti** (Pazienti con la clinica), l'indirizzo è
  `/crm/persone`.

## Come funziona

### Il Riepilogo

- `crm/persone/riepilogo.py`: **una chiamata** (`get_summary`) a cui ogni modulo
  aggiunge le sue righe (`registra_voce`), come aggiunge un posto all'area
  clienti. Ogni riga decide da sé cosa legge la sessione: una riga che non si
  può leggere **non c'è**, senza rifiuto (il suo messaggio se ne va con lei); una
  che si rompe si scrive nel registro degli errori e il resto si apre.
  - la base: **In corso** (i cicli di sedute attivi, gli abbonamenti attivi o
    sospesi, i posti in lista d'attesa, ognuno con la capacità che lo legge nella
    scheda Abbonamenti), **Da fare** (le cose da fare aperte, prima quelle con un
    giorno), **Trattative** (quelle aperte, con la fase e la pipeline);
  - la fatturazione: **Da incassare** (`incassi.della_persona`: le fatture
    emesse e non incassate, mai una nota di credito, una di prova o una scartata
    dallo SdI; il totale che il cliente paga; le bozze da emettere);
  - i moduli: **Moduli** da firmare per il prossimo appuntamento
    (`dovuti.nel_riepilogo`);
  - i preventivi: quelli **in attesa di risposta** e quelli accettati ancora in
    corso (`api.nel_riepilogo`, come li elenca la scheda Preventivi).
- Il browser aggiunge quello che ha già: l'**ultimo messaggio** dalla persona
  (`last_conversation_*`, scritto a ogni messaggio), con «Da leggere», per chi
  legge le conversazioni; gli **appuntamenti** che ha chiesto la testata della
  pagina (gli stessi, senza una seconda richiesta): i prossimi tre e l'ultimo.
- `SummaryArea.vue`: le carte in due colonne dove ci stanno, una sotto l'altra
  sul telefono e nella colonna di Conversazioni (`compatto`, senza l'ultimo
  messaggio, che è lì accanto). Ogni carta porta alla sua scheda, ogni riga a
  quello che nomina (l'appuntamento in agenda, la fattura nel suo dialogo, la
  trattativa). Di ogni elenco le prime tre righe, il resto nella sua scheda.
  Niente da dire: lo stato vuoto lo dice.

### Le due porte

- `router.js`: la persona senza scheda nell'indirizzo si apre su `#summary`,
  non più sull'ultima scheda lasciata: chi manda un collega su una persona la
  fa leggere dall'inizio. La trattativa resta com'era.
- La notifica di un messaggio apre il messaggio nella chat; un messaggio senza
  più il suo nome apre la chat (`notifiche/api.percorso`).
- In Conversazioni, «Apri la scheda» apre la persona sulla chat, dove si era; la
  colonna di destra (sul telefono, il foglio che si apre toccando il nome) ha il
  Riepilogo.
- La scheda «Attività» si chiama **Chat**, come la voce del menu sul telefono.

### La lista Persone

- Lo stadio resta scritto «Contact» (`CRM Lead.relationship`): si legge **Lead**
  dove si mostra, nel suo contesto («Relationship», anche in inglese, `en.po`).
- Le viste rapide sono il filtro rapido sullo stadio disegnato come bottoni
  (`ViewControls.vue`, `vistePerRapporto` in `utils/rapporto.js`), sul telefono
  sotto la ricerca (`ElencoPersone.vue`, `get_people(relationship=...)`).
- L'indirizzo è `/crm/persone` e `/crm/persone/<persona>`; quelli di prima
  (`/crm/leads/...`, nelle email già mandate e nei segnalibri) portano lì. Le
  email delle notifiche, le notifiche sul telefono e il Desk scrivono il nuovo.

## Da sapere

- Il nome del DocType (`CRM Lead`) e i nomi delle rotte (`Lead`, `Leads`) non
  cambiano: viste salvate, link interni e permessi restano quelli.
- Un modulo che vuole dire qualcosa nel Riepilogo registra la sua riga dal suo
  `registra()` con una chiave sua; la scheda la disegna quando la conosce.
