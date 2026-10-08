# Il CRM — i documenti numerati

I documenti del CRM di base, quello su cui stanno i verticali e i marchi
([`../README.md`](../README.md)). Sono numerati e il numero non cambia: il codice li
cita come «doc 57». Sono nati come «Progetto GHL-Parity», l'obiettivo che segue.

> **Obiettivo**: portare DottorCloud (`crm-mm`, nato da un CRM open source) alla parità funzionale
> con GoHighLevel — funnel, marketing automation omnicanale, telefonia/SMS/inbox
> unificata, corsi & membership, calendari di prenotazione, white-label SaaS e
> reputation management — riusando al massimo l'ecosistema open-source Frappe.
>
> Ricerca condotta online ad **agosto 2026** (repo, docs ufficiali, changelog API);
> ogni modulo cita le fonti.

## ⚖️ Decisioni di scope (31/08/2026)

Scope ridotto rispetto alla parità completa, su decisione del committente:

- ✅ **IN SCOPE**: Workflow automation (02), SMS 2-way + inbox unificata + power
  dialer (03), Booking/calendari (05) — **si parte dal Booking**. Del modulo 06
  restano solo gli **script di provisioning + snapshot** (golden site) come
  strumento interno: ogni cliente ha già il proprio site, gestito manualmente.
- ❌ **FUORI SCOPE**: funnel builder (01), corsi/LMS (04), reputation (07),
  canali Meta Messenger/IG (parte di 03), signup pubblico/billing/rebilling e
  white-label aggiuntivo (parte di 06). I documenti restano come riferimento
  se lo scope dovesse riaprirsi.

### Aggiornamento (06/09/2026) — sito vetrina

Riapertura **parziale e ridotta** del modulo 01: non il funnel builder, ma un **sito
web semplice alimentato dai dati del CRM** (servizi, prodotti, form, prenotazioni).
Proposta e alternative in [16](./16-sito-web-vetrina.md); funnel, A/B test e checkout
restano fuori scope.

L'architettura scelta è quella già anticipata qui sopra: **Frappe Builder come app
accanto al CRM**, con i componenti collegati al CRM spediti da `crm/builder_files/`.

## Indice dei documenti

| Doc | Modulo | Stato | Verdetto sintetico |
|---|---|---|---|
| [00](./00-analisi-stato-attuale.md) | Analisi stato attuale del repo | — | Non si parte da zero: Twilio Voice browser, WhatsApp, scheduler, round-robin nativi |
| [01](./01-funnel-landing-builder.md) | Funnel & Landing Page | ❌ fuori scope | Adottare Frappe Builder (MIT da v1.31) + layer funnel custom |
| [02](./02-marketing-automation.md) | Marketing Automation | ✅ in scope | **Da costruire** (motore enrollment Python + canvas Vue Flow); i canali esistono già |
| [03](./03-telefonia-sms-inbox.md) | Telefonia, SMS, Inbox | ✅ in scope (no Meta) | SMS two-way + inbox unificata + power dialer su Twilio già integrato |
| [04](./04-corsi-membership.md) | Corsi & Membership | ❌ fuori scope | Adottare Frappe LMS; costruire solo drip/abbonamenti/ponte |
| [05](./05-calendari-prenotazioni.md) | Calendari & Booking | ✅ **in scope, primo** | Booking pubblico con disponibilità, buffer, round-robin, reschedule/cancel |
| [06](./06-white-label-saas.md) | White-Label / SaaS | ⚠️ solo provisioning+snapshot | Script interni per creare site clienti preconfigurati; niente billing |
| [07](./07-reputazione-recensioni.md) | Reputation | ❌ fuori scope | Solo Google via GBP API; Facebook API morta (v22) |
| [08](./08-roadmap.md) | Roadmap & effort | aggiornata | Fasi, dipendenze, stime — ricalibrata sullo scope ridotto |
| [13](./13-google-calendar.md) | Google Calendar collegato in un click | ✅ implementato | OAuth gestito dall'agenzia: nessuna credenziale da incollare sul sito cliente |
| [14](./14-agenda-appuntamenti.md) | Agenda interna: multi-persona, stanze, attrezzature, listini | ✅ implementato | Staffing collective/round-robin/per-ruolo, capacità delle risorse, sessioni di gruppo, prezzi condizionati |
| [15](./15-tracciamento-lead.md) | Tracciamento del lead e attribuzione | ✅ implementato | Script esterno, sessioni, primo/ultimo contatto, percorso pagina per pagina |
| [16](./16-sito-web-vetrina.md) | Sito web vetrina integrato nel CRM | ✅ implementato | Frappe Builder installato accanto come **tela**; il CRM resta guscio e dati: componenti spediti da noi con data script, impostazioni e publish nel modale |
| [17](./17-timeline-unificata.md) | Timeline unificata sulla scheda | 📐 proposta | Una schermata al posto di dodici tab: i chip non filtrano soltanto, cambiano vista — chat WhatsApp, thread email — con un solo composer che segue il canale |
| [18](./18-persona-unica.md) | Una persona sola: lead e contatto smettono di essere due | 📐 proposta | Il lead e' la persona, il deal la relazione, il contatto la rubrica: i recapiti vivono in un posto solo e il campo sul lead diventa uno specchio, cosi' i 201 punti che lo leggono non cambiano |
| [19](./19-trattativa-magra.md) | La trattativa magra, come l'opportunita' di GHL | ✅ fatto | L'opportunita' di GHL e' un pannello con i campi, le note, i task e un appuntamento: la nostra trattativa scende da otto tab a quattro, e i file finiscono accanto alle note |
| [20](./20-domini-dei-clienti.md) | Più siti, sul dominio del cliente | 🟡 proposta | Un cliente per site, tanti domini sopra: CNAME come GHL e certificati on-demand, senza configurare nginx a ogni dominio |
| [21](./21-lead-contatto-trattativa.md) | Lead, contatto, azienda, trattativa: cosa significano davvero | ✅ fatto | Verifica contro Salesforce, HubSpot, Pipedrive e GHL: la persona e' unica e permanente, "lead" e' uno stadio. Sei punti dove il codice seguiva ancora il modello opposto |
| [22](./22-app-review-facebook.md) | App Review dell'app Facebook: cosa serve e cosa no | 🟡 in corso | Stato letto dall'API di Meta: l'app e' in dev mode, quindi i lead dei clienti non possono arrivare. Le 7 permission che servono, le 6 da togliere, l'ordine delle operazioni e i testi degli use case |
| [23](./23-spesa-e-ritorno.md) | Spesa e ritorno: il costo per cliente, non per lead | ✅ fatto | La spesa di Meta letta ogni giorno per inserzione e incrociata con le trattative del CRM: costo per lead, costo per cliente acquisito e ROAS per inserzione — il numero che ne' Meta ne' il CRM sanno da soli |
| [24](./24-qualita-dei-lead.md) | Qualita' dei lead: far imparare le inserzioni dalle vendite | ✅ fatto | Conversions API per CRM: gli stadi del funnel tornano a Meta col lead id, cosi' le inserzioni ottimizzano per chi compra e non per chi compila. Coda, copertura, e i requisiti veri detti chiari |
| [27](./27-impostazioni-canali-integrazioni.md) | Impostazioni: WhatsApp, Social Planner e Integrazioni separati | ✅ fatto | Il gruppo "Meta & Messaging" diventa tre spazi; Meta è una pagina con schede sotto Integrazioni; il Social Planner parte dalle sorgenti. App, webhook, token e log grezzi solo agli amministratori — anche lato server — e i token non finiscono più nei messaggi d'errore |
| [26](./26-lo-stato-sta-sulla-trattativa.md) | Lo stato della vendita sta sulla trattativa | ✅ fatto | La crepa del doc 21: avendo fatto coincidere la persona con il lead, il ciclo di qualifica era uno solo per vita. Lo stato passa sulla trattativa — una scala sola — e chi torna dopo una trattativa chiusa ne apre una nuova |
| [25](./25-costo-hosting.md) | Quanto costa tenerci i clienti sopra | 📊 aggiornato 07/10 | Un server condiviso invece di un piano per sito. I prezzi veri di Frappe Cloud (siti illimitati sul proprio server, 70 $ il cpx32) e di Hetzner dopo gli aumenti del 2026, il confronto, la decisione: Frappe Cloud per il lancio, Hetzner diretto a 30–40 centri o se il legale dice no |
| [28](./28-dashboard.md) | La dashboard: un cruscotto per ogni parte del gestionale | ✅ fatto | 166 widget in 16 categorie, fatturazione compresa, e dieci dashboard pronte che seguono il sito: chi collega WhatsApp trova i suoi numeri senza toccare niente. Builder a griglia, colori che seguono la cosa e non il suo posto |
| [29](./29-telefono.md) | Il CRM sul telefono | ✅ fatto | Ogni pagina, dialogo e sezione delle impostazioni guardati con Playwright su un telefono simulato e percorsi col dito: niente più azioni solo al passaggio del mouse, titoli sulla descrizione, controlli spinti fuori dallo schermo o da 16px. Le regole per le prossime schermate |
| [30](./30-ruoli-e-permessi.md) | Ruoli e permessi: chi può fare cosa, modulo per modulo | 🟡 proposta | Livelli come Role Profile, ruoli come mattoni dei moduli, capacità controllate dal server; ogni modulo porta le sue. Le impostazioni divise fra centro e agenzia, l'ambito che segue la persona |
| [31](./31-impostazioni-in-ordine.md) | Le impostazioni in ordine | ✅ fatto | Da 48 voci in sedici gruppi a 33 in undici, un gruppo per ogni parte del lavoro del centro come nel menu dell'app; le pagine dello stesso argomento diventano le schede di una voce, come Meta, e i vecchi nomi aprono ancora la scheda giusta. Il menu tutto in italiano |
| [32](./32-un-segno-per-posto.md) | Un segno per posto: il centro in alto, DottorCloud in fondo | ✅ fatto | Niente più loghi affiancati: la barra laterale porta il logo di DottorCloud, come vuole il design system; dove una persona ha a che fare con il centro (prenotazione, moduli, la sua area) in alto c'è il centro, com'è disegnato il suo logo, e DottorCloud firma in fondo. Nome e logo spiegati, con l'anteprima |
| [33](./33-design-system-espresso.md) | Il design system nel gestionale: DottorCloud su Espresso | ✅ fatto | I grigi di Espresso tinti del verde del marchio, focus e ombre nel suo colore, la menta come azione al buio, la coda della nuvola e la croce dove si agisce e si sceglie: tutto dalle variabili di frappe-ui, senza riscrivere componenti. Verificato nel browser e sistemato dove serviva (le etichette a 4,5:1) |
| [34](./34-menu-principale.md) | Il menu principale: la giornata del centro, poi il resto | ✅ fatto | Da diciassette voci senza gruppi a la giornata in cima (Oggi, Agenda, Lista d'attesa, Pazienti, Conversazioni, Da fare, Fatture), poi archivio, marketing e telefono; in italiano, per livello, la barra del telefono dallo stesso menu, una voce per le impostazioni |
| [35](./35-impostazioni-a-due-livelli.md) | Le impostazioni a due livelli: prima la parte del lavoro, poi la cosa | ✅ fatto | A sinistra solo le undici parti del lavoro, ognuna con la sua icona; a destra quella aperta dice a cosa serve e mostra le sue voci, ognuna con una riga che spiega cosa si imposta lì; la voce aperta con la strada per tornare. Sul telefono gli stessi tre passi |
| [36](./36-funzionalita.md) | Funzionalità: cosa comprende DottorCloud, e gli extra | ✅ fatto | La pagina "Piano" diventa "Funzionalità": in alto quello che DottorCloud comprende (la base, la clinica, l'area pazienti), pronto da usare; sotto gli extra (marketing, telefono, assistente) con quello che aggiungono e la prova gratuita; per ognuno i link alle pagine dove si imposta. Tutto in italiano |
| [37](./37-primi-passi.md) | Primi passi: le cose da fare per cominciare, che si spuntano da sole | ✅ fatto | Al posto del "Getting started" di frappe-ui (in inglese, passi da CRM di vendita, un pannello che si apriva da solo): i passi di un centro (nome e logo, servizi, orari, colleghi, moduli, prenotazione online, email, primo paziente, primo appuntamento), ognuno spuntato dai dati del centro, per chi può farli, che portano dove si fanno |
| [38](./38-piani-spiegati.md) | I piani dei pazienti: una scheda loro, spiegati | ✅ fatto | I piani escono dalla scheda Area pazienti e ne hanno una loro; una frase dice cos'è un piano, tre passi come si fa, ogni tipo cosa contiene; un avviso se la persona non entra nell'area; editor, programmi e schede dell'area in italiano |
| [39](./39-design-system-completo.md) | Il design system, tutto: i componenti che mancavano e il kit del marchio | ✅ fatto | StatTile in Oggi e nella dashboard (il primo numero di ogni fila in blocco), stati vuoti con i blocchi della copertina, tag delle categorie, "in corso" con la croce, il l'evento dell'agenda (prima visita, adesso, annullato), avatar a nuvola, la coda su menu e carte, la croce sulla voce scelta, le date in italiano; in `brand/dottorcloud/` font, icone, forme, composizioni, il sito e i generatori |
| [40](./40-italiano.md) | L'italiano dappertutto: la voce, le parole del prodotto e le schermate tradotte | ✅ fatto | Le pagine di ogni giorno e l'area clienti, le impostazioni, il resto dell'app, le parole del server e i nomi dei DocType, l'importazione dei dati e l'editor di frappe-ui tradotti alla build; i valori delle liste, l'ora a 24 ore, le notifiche con frasi intere, le traduzioni ereditate nella voce del prodotto |
| [41](./41-anteprima-area.md) | L'anteprima dell'area pazienti: vederla come la vede il paziente, prima di aprirla | ✅ fatto | Dalla scheda della persona, «Anteprima» apre la sua area in sola lettura, anche prima dell'invito e senza mandarle niente: chi guarda vede solo quello che legge in DottorCloud, il resto resta al suo posto vuoto, i dati sanitari letti vanno nel registro degli accessi, e da lì non si cambia né si manda niente |
| [42](./42-area-nel-marchio.md) | L'area pazienti come la disegna il marchio | ✅ fatto | L'area segue le schermate del telefono del kit: titoli grandi, etichette in maiuscoletto, carte con la coda della nuvola, il prossimo appuntamento nel blocco scuro con le croci, ogni piano nella nuvola del colore del suo tipo, i giorni a tessera, la spunta in un tocco, il codice in sei caselle; in basso Oggi, Agenda, Piani, Documenti (con le fatture) e Messaggi |
| [43](./43-notifiche.md) | Le notifiche | ✅ fatto | Un pannello nuovo: le notifiche sotto i loro giorni, ognuna col segno del suo tipo, la frase nella lingua di chi legge, le prime parole del messaggio, l'ora; «Tutte», «Da leggere», «Eventi»; si apre sul messaggio di cui parla; i messaggi della stessa persona si sommano; l'avviso del marchio quando ne arriva una; sistemati i link sbagliati, «Segna tutto come letto», la sola lettura, la lista intera a ogni apertura |
| [44](./44-email.md) | Le email | ✅ fatto | Ogni email di sistema nella veste del marchio: la carta con la coda della nuvola, il segno del centro in alto, «Powered by DottorCloud» sotto; la cosa da fare in un pulsante, il codice nella sua casella; il promemoria degli eventi in italiano; le notifiche non lette arrivano anche per email dopo cinque minuti, una o più in un'email sola, e ognuno sceglie quali in Impostazioni › Il tuo account › Notifiche; le email del framework per assegnazioni, menzioni e condivisioni non partono più |
| [45](./45-codici-in-parole.md) | La fatturazione in parole | ✅ fatto | Ogni codice della fatturazione e del Sistema TS si sceglie col suo nome e una riga che dice quando si usa; con la clinica accesa solo le scelte di un centro medico (tre regimi, tre nature IVA, le casse della sanità), i tipi di spesa di chi emette, le qualifiche sanitarie; i campi con nomi chiari e le descrizioni senza elenchi di codici; le parole dei tipi di spesa sono quelle della specifica; lo stesso nel modulo della fattura del Desk |
| [46](./46-fatturazione-sanitaria.md) | La fatturazione di un centro medico, già impostata | ✅ fatto | Con la clinica accesa tre domande impostano l'azienda emittente (chi emette, i codici della struttura o la professione, il regime) e da lì categoria del Sistema TS, cassa e ritenuta; i servizi dell'agenda diventano schede sanitarie esenti in un clic; il registro mostra le professioni sanitarie; il registro del centro vince sempre su quello spedito; via la casella «Ramo sanitario» che non faceva nulla; una nuova azienda parte dai valori del DocType |
| [47](./47-fattura-dentro-dottorcloud.md) | La fattura fatta dentro DottorCloud | ✅ fatto | La fattura si fa in una finestra di DottorCloud: per chi è, cosa è stato fatto e da chi, come è stata pagata, e prima di tutto dove andrà; mentre si scrive il server dice quanto fa e tutto quello che manca; emessa, il PDF, l'invio allo SdI, la nota di credito (al Sistema TS il rimborso dell'originale); una scartata si corregge con lo stesso numero; si apre dalle fatture, dall'agenda, dai cicli, dagli abbonamenti e dalla storia della persona; a una persona fisica la fattura col suo nome; i messaggi del motore tradotti |
| [48](./48-controlli-in-parole.md) | Il Sistema TS e lo SdI prima di emettere, in parole | ✅ fatto | Il tracciato del Sistema TS si controlla sulla bozza: quello del documento ferma l'emissione, quello dell'azienda si dice e non ferma; i messaggi del Sistema TS e i rilievi dello SdI in parole, con i nomi dei tipi di spesa, gli importi in euro e il codice SdI in coda; i controlli sul file XML allineati all'elenco ufficiale (00422 per aliquota con la cassa, 00200 per lo schema, 00411/00415 sulla ritenuta, l'imposta arrotondata per eccesso); nella finestra i rilievi prima dell'invio, «Pagata prima della fattura», niente data di pagamento su una nota di credito |
| [49](./49-itala-prova-essenziale.md) | Itala, la prova prima del vero, e solo l'essenziale | ✅ fatto | Ogni azienda parte in prova: le fatture hanno la serie PROVA e una fascia sul PDF, quelle elettroniche vanno all'ambiente di prova di Itala, il Sistema TS non riceve niente, non fanno un cliente né vanno nell'area; «Prova e attivazione» dice cosa manca e attiva la fatturazione togliendo le prove; Itala è l'unico intermediario, sull'account dell'agenzia, ogni azienda registrata da sola; al centro restano solo i suoi dati e le credenziali del Sistema TS, il resto è dell'agenzia; corrette la direzione della riconciliazione e il nome del file di Itala; poi niente da scegliere dove non c'è scelta: lo SdI sempre Itala in uscita e in entrata, la conservazione quella gratuita dell'Agenzia (il centro spunta l'adesione), la numerazione mai vuota con il formato scelto tra esempi, la scheda «Sistema TS» che chiede prima come arrivano le spese |
| [50](./50-trattative-e-preventivi.md) | Trattative e preventivi, due livelli collegati | ✅ fatto | «Offerte» era la traduzione di *Deals*: ora «Trattative». La trattativa è la vendita, il preventivo il documento: la trattativa ha la scheda Preventivi e uno nuovo fatto lì è suo, proposto la sposta, accettato la vince con il suo valore (prima valeva zero sulle dashboard); un preventivo sposta solo le trattative della pipeline «Preventivi» e non riapre una chiusa; via la griglia «Prodotti» della trattativa, un catalogo solo; nella dashboard Vendite i preventivi proposti, la quota accettata, quanto vale chi aspetta e chi richiamare; gli stati al maschile. Le offerte del marketing, se servono, saranno pacchetti del catalogo, neutri con la clinica (comma 525) |
| [51](./51-email-servizio-e-caselle.md) | Le email: il servizio di invio e le caselle | ✅ fatto | Promemoria, codici, conferme e notifiche partono dal servizio di invio dell'agenzia, uno per tutti i centri, a nome del centro, con le risposte alla sua casella o all'indirizzo scelto; il centro non configura niente. Le caselle del centro si aggiungono scegliendo il fornitore (Gmail, Aruba, Libero, Virgilio, Tiscali, iCloud, Yahoo): un'email che arriva va sulla pagina di chi la scrive, senza doppioni, la risposta a un promemoria passa dall'appuntamento alla persona, e chi la segue lo sa dal pannello. Ognuno collega la sua casella (anche con l'accesso Google o Microsoft) e scrive da lì: arrivano solo le risposte e le email delle persone note, il resto della posta resta suo |
| [52](./52-twilio-del-centro.md) | Twilio: l'account del centro, tutto da DottorCloud | ✅ fatto | Il centro incolla una volta Account SID e Auth Token: DottorCloud crea il suo spazio nell'account del centro (un sottoaccount), con la sua chiave e la sua app, punta i numeri a sé e tiene solo le chiavi dello spazio; chiamate e SMS li paga il centro a Twilio. Il solo accesso (Twilio Connect) non basta: non compra numeri italiani né fa telefonare dal browser. I numeri italiani si chiedono da DottorCloud: tipo e prezzo, i dati della fatturazione già scritti, i documenti caricati e valutati da Twilio prima dell'invio, l'avviso quando Twilio risponde, la scelta e l'acquisto con un clic, il rilascio; i documenti approvati valgono per il numero dopo. Le chiamate in arrivo squillano a tutti insieme, poi la segreteria con la richiamata e, se il centro vuole, un messaggio registrato con l'avviso a chi segue la persona. Le chiamate in uscita partono solo verso i paesi scelti dal centro e mai verso i numeri a pagamento (gli stessi paesi nei permessi di Twilio), dal numero scelto tra quelli del centro con l'avviso AGCOM sul cellulare, con il tastierino. Gli SMS partono tutti da un mittente del centro (il nome o un suo numero); STOP ferma quelli automatici e ritira il consenso al marketing, START li fa ripartire; le promozioni solo dal lunedì al sabato, dalle 8 alle 22. La pagina di Twilio dice quanto ha speso lo spazio questo mese, per voce, con un avviso quando arriva all'importo scelto, e i problemi degli ultimi giorni a parole; un SMS che non arriva dice perché. Un numero che il centro ha già nel suo account Twilio si sposta nello spazio con i suoi documenti, con i codici incollati per quella volta; per uno di un altro operatore, l'inoltro o la portabilità spiegati |
| [53](./53-dati-di-prova.md) | Dati di prova: un centro pieno, tolto senza lasciare traccia | 🟡 in corso | La vecchia demo inglese (dodici persone americane) se ne va. I dati di prova sono parti registrate dai moduli: la base fa la squadra con i turni, le stanze e i servizi, tre mesi di vita del centro giorno per giorno (le persone arrivano, prenotano, vengono e tornano; le regole del CRM spostano le trattative e fanno i clienti), le aziende con le convenzioni, le cose da fare, le note e le telefonate. Ogni record creato finisce in un registro, anche quelli che i controller creano da soli; mentre si creano non parte nulla. La rimozione va dal registro al database in pochi secondi, porta via anche quello che riguarda le persone della demo e tutto quello che il framework tiene accanto, lascia al centro i servizi che ha adottato; i test contano ogni tabella prima e dopo. Finché ci sono, nessuna email, WhatsApp, SMS o chiamata raggiunge le persone della demo, e i visitatori della pagina di prenotazione non ne vedono i servizi. Impostazioni > Il centro > Dati di prova |
| [54](./54-una-persona-due-porte.md) | Una persona, due porte: il Riepilogo, la chat, la lista Persone | ✅ fatto | Una sola scheda della persona, la stessa da Persone, dall'agenda, da Conversazioni e dalle notifiche, con due facce: il Riepilogo e la chat. Da Persone e dall'agenda si apre sul Riepilogo (l'ultimo messaggio, gli appuntamenti, cicli e abbonamenti in corso, cosa resta da incassare e da fare, i moduli da firmare, i preventivi, le trattative), da Conversazioni e dalla notifica di un messaggio sulla chat; il Riepilogo sta anche accanto alla chat di Conversazioni. La lista resta Persone: il primo stadio si legge Lead, in cima le viste Tutti · Lead · Clienti · Pazienti, l'indirizzo è /crm/persone (i vecchi link portano lì) |
| [55](./55-le-scelte-delle-liste.md) | Le scelte delle liste: filtra, ordina, raggruppa, colonne | ✅ fatto | I menu Filtro, Ordina, Raggruppa per, Colonne, la bacheca e i filtri rapidi offrono i campi da una regola sola: ognuno una volta, in italiano, distinti per sezione («Sorgente (Primo contatto)»), mai un codice o un campo della macchina, solo i tipi che l'uso prende; i gruppi si intitolano come una riga legge il valore (stato tradotto, Sì/No, un collega per nome, una data) |
| [56](./56-agenda.md) | L'agenda che si legge: il giorno del centro, la settimana di uno, il mese | ✅ fatto | Un appuntamento dice prima la persona, poi cosa e dove, in righe intere quante la sua altezza ne contiene, con i segni in icone e parole; il giorno ha una colonna per chi lavora, larga da leggere, con il suo orario in testa e le ore fuori turno a righe; la settimana è di un professionista, il mese conta e nomina; una barra sola (‹ Oggi ›, Giorno · Settimana · Mese, di chi, Filtri, Vista); le scelte di chi legge nel suo browser, quelle del centro (vista iniziale, passo della griglia) nelle impostazioni |
| [57](./57-archivio-dei-file.md) | L'archivio dei file: 1–2 TB per centro, su Hetzner | ✅ fatto | I file privati del centro dopo un'ora vanno nel bucket S3 dell'agenzia su Hetzner, una cartella per sito; sul server resta un file vuoto col nome. Chi lo apre va al bucket con un link di cinque minuti dopo il controllo dei permessi, il codice che lo legge lo trova intero. 1 TB incluso, 2 TB da Poliambulatorio; oltre niente si blocca, la pagina del piano avvisa all'80% |
| [58](./58-fatture-in-cloud.md) | Fatture in Cloud: per il centro che fattura già lì | ✅ fatto | Il responsabile collega Fatture in Cloud una volta (OAuth dall'hub dell'agenzia); aliquote IVA, conti e numerazioni scelti da soli dove possono; con l'interruttore acceso ogni fattura vera nasce lì: Fatture in Cloud la somma prima (al centesimo, o niente), le dà il numero, la manda allo SdI e ne dice lo stato; il Sistema TS lo invia uno dei due |
| [59](./59-promemoria.md) | I promemoria degli appuntamenti: WhatsApp con i pulsanti, SMS, email | ✅ fatto | Il giorno prima (o quante ore il centro sceglie, mai di notte né nell'ultima ora) ognuno riceve il promemoria del suo posto: su WhatsApp con «Confermo», «Devo disdire», «Vorrei spostarlo», altrimenti per SMS (SI o NO) o per email con il link della pagina di prenotazione; la risposta è un segno sul blocco dell'agenda, un «non posso venire» libera l'orario per la lista d'attesa, la reception è avvisata; il modello WhatsApp di DottorCloud si crea dalle impostazioni sull'account del numero che invia |
| [60](./60-pagamenti-online.md) | I pagamenti online: fatture e acconti con carta, sull'account Stripe del centro | ✅ fatto | Il centro collega il suo Stripe con la chiave segreta (i soldi vanno a lui, DottorCloud non li tiene); una fattura si paga dall'area o da un link della reception e risulta incassata da sola; un servizio può chiedere un acconto alla prenotazione online, il posto è tenuto mezz'ora e si libera se il pagamento non arriva; la disdetta in tempo restituisce l'acconto |
| [61](./61-convenzioni-e-fondi.md) | Convenzioni, fondi sanitari e assicurazioni: forma diretta e indiretta, pratiche, estratto del mese | ✅ fatto | Il centro imposta fondi, assicurazioni e convenzioni aziendali con i loro prezzi (un listino dell'agenda o uno sconto) e la quota del paziente; la persona ha le sue coperture; l'appuntamento in forma diretta divide il prezzo tra paziente e fondo e dice «Autorizzazione mancante»; la persona riceve la fattura della sua quota (solo quella va al Sistema TS), il fondo una fattura al mese con una riga per pratica, e il mese si esporta in CSV per il portale del fondo |

## Architettura complessiva

```
                       ┌────────────────────────────────────────────────┐
                       │                UN SITO FRAPPE (per tenant)     │
                       │                                                │
  Frappe Builder ──────│──  pagine/funnel pubblici, form → CRM Lead     │
  (app ufficiale, MIT) │                                                │
                       │  ┌──────────────┐   ┌───────────────────────┐  │
  Frappe LMS ──────────│─▶│  crm (fork)  │◀──│  crm_suite (NUOVA app)│  │
  (app ufficiale)      │  │  lead/deal   │   │  ├─ automation  (02)  │  │
                       │  │  twilio voice│   │  ├─ funnels     (01)  │  │
  frappe_whatsapp ─────│─▶│  whatsapp api│   │  ├─ inbox/sms   (03)  │  │
  (community, MIT)     │  │  email       │   │  ├─ dialer      (03)  │  │
                       │  └──────────────┘   │  ├─ membership  (04)  │  │
  frappe/payments ─────│──  gateway          │  ├─ booking     (05)  │  │
  (app ufficiale, MIT) │                     │  ├─ reputation  (07)  │  │
                       │                     │  └─ saas        (06)* │  │
                       └─────────────────────┴───────────────────────┴──┘
                              * il modulo saas vive sul sito "agency" centrale

  Infrastruttura: frappe_docker + bench multi-sito + DNS wildcard + TLS wildcard
  Provisioning nuovi tenant: bench new-site + restore del golden site ("snapshot")
```

### Principi decisi

1. **Estendere, non forkare oltre**: tutto il codice nuovo va nella nuova app
   `crm_suite`, installata accanto a `crm`. Il fork del CRM resta minimo
   (branding + hook points) per poter continuare a fare pull da upstream.
2. **Adottare le app ufficiali dove esistono** (Builder, LMS, payments,
   frappe_whatsapp): il costo diventa integrazione, non sviluppo.
3. **Un solo channel-adapter layer** (`send(channel, recipient, payload)`)
   condiviso da workflow engine, inbox, booking e reputation.
4. **Il workflow engine (modulo 02) è la spina dorsale**: quasi ogni altro modulo
   vi si aggancia come trigger o come azione. Va costruito per primo.
5. Stack invariato: Python/Frappe backend, Vue 3 + frappe-ui frontend, MariaDB,
   Redis/scheduler per i job.

### Licenze (sintesi)

- Frappe Framework, Builder ≥1.31, payments, frappe_whatsapp, Vue Flow: **MIT/BSD**.
- CRM (questo fork), LMS, telephony, frappe-appointment: **AGPL-3.0** → l'app
  `crm_suite` va considerata AGPL; il modello di business (vendere il servizio
  hosted, non licenze) è pienamente compatibile, con obbligo di rendere
  disponibile il sorgente modificato agli utenti del servizio (dettagli nel
  [modulo 06](./06-white-label-saas.md), inclusa la questione trademark).

## Azioni con lead time lungo — da avviare SUBITO

Ricalibrate sullo scope ridotto:

1. **Twilio**: numeri SMS-capable per i clienti, e A2P 10DLC solo se si punta al
   mercato USA; registrazione mittente alfanumerico dove applicabile in EU.
2. **Google OAuth (Google Calendar)**: credenziali OAuth per il busy-block dei
   calendari di booking (già supportato dal framework).
3. ~~GBP API, Meta Business Verification~~ — non più necessarie (reputation e
   canali Meta fuori scope).
