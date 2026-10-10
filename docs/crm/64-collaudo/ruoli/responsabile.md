# Collaudo · Responsabile del centro

## A cosa serve

Questa è la lista del responsabile del Poliambulatorio San Luca: il giorno 0 rilegge
e completa le impostazioni che `prepara.centro` ha fatto, come le farebbe il
responsabile di un centro vero; poi, nei giorni del collaudo, guarda i numeri, le
fatture al fondo, i dati del centro. Ogni riga dice cosa fare e cosa deve succedere.
Quando una riga non va come è scritto, una segnalazione con il suo codice (per
esempio RES-11): [segnalazioni.md](../segnalazioni.md).

## Prima di cominciare

- **Chi sei:** l'utente del ruolo `responsabile`, livello Responsabile: tutto il
  lavoro del centro e le sue impostazioni, non quelle dell'agenzia (chiavi, servizi
  esterni dell'agenzia).
- **Dove:** `https://collaudo.dottorcloud.com/crm`, sul computer; *(telefono)* sul
  tuo telefono.
- **Con chi:** il sistemista ([server-di-collaudo.md](../server-di-collaudo.md)) ha
  collegato Stripe, Twilio e WhatsApp, o lo fate insieme alle righe RES-10, RES-12.
- **La regola:** mai «Attiva la fatturazione» sul collaudo.

## Il giorno 0: il centro

- [ ] **RES-01 · Entra.** Dal computer; cambia la password (Impostazioni › Il tuo
  account › Profilo › «Cambia la password»).
  *Atteso:* DottorCloud in italiano; la scheda «Primi passi» dice cosa resta da
  preparare.
  Note: ______________________________________________

- [ ] **RES-02 · Il telefono *(telefono)*.** L'app sulla schermata Home e le notifiche
  accese (Impostazioni › Il tuo account › Notifiche).
  *Atteso:* la notifica di prova arriva.
  Note: ______________________________________________

- [ ] **RES-03 · Nome e logo.** Impostazioni › Il centro › Generale › «Nome e logo».
  Poi apri `/prenota` da una finestra privata.
  *Atteso:* in alto il logo e il nome del Poliambulatorio San Luca; in fondo «Con
  tecnologia DottorCloud»; mai due loghi affiancati.
  Note: ______________________________________________

- [ ] **RES-04 · Funzionalità.** Impostazioni › Il centro › Funzionalità.
  *Atteso:* quello che DottorCloud comprende, la clinica, gli extra accesi; lo
  «Spazio per i file» usato.
  Note: ______________________________________________

- [ ] **RES-05 · Utenti.** Impostazioni › Il centro › Utenti: la squadra con i suoi
  livelli. «Invita» un collega in più (un indirizzo della squadra) come Segreteria.
  *Atteso:* ognuno ha il livello del suo ruolo, il medico anche la Direzione
  sanitaria; l'invito arriva per email.
  Note: ______________________________________________

- [ ] **RES-06 · Sedi.** Impostazioni › Il centro › Sedi: Milano e Monza. Disattiva
  Monza, guarda l'agenda, riattivala.
  *Atteso:* con una sede sola nessuna schermata nomina le sedi (l'agenda non ha più
  il selettore); con due torna.
  Note: ______________________________________________

- [ ] **RES-07 · I servizi.** Impostazioni › Agenda › Servizi: la «Visita medica» con
  l'acconto di 30 € alla prenotazione online, la «Visita nutrizionale» pagata per
  intero, il «Controllo nutrizionale online» come visita online.
  *Atteso:* ogni servizio con chi lo fa, la durata, il prezzo, l'ambulatorio; la sua
  scheda fiscale.
  Note: ______________________________________________

- [ ] **RES-08 · Gli abbonamenti.** Impostazioni › Agenda › Servizi › Abbonamenti:
  «Pilates mensile» «Vendibile online dall'area».
  *Atteso:* si salva solo con la scheda fiscale e il prezzo; un abbonamento al mese si
  vende online solo con l'addebito mensile acceso.
  Note: ______________________________________________

- [ ] **RES-09 · Un'assenza.** Impostazioni › Agenda › Orari e turni: un giorno di
  assenza del dietista la settimana prossima.
  *Atteso:* quel giorno la sua colonna è chiusa in agenda e `/prenota` non offre i
  suoi orari.
  Note: ______________________________________________

- [ ] **RES-10 · Pagamenti online.** Impostazioni › Fatturazione › Pagamenti online
  (con la chiave `sk_test_` del sistemista): «Vendi abbonamenti dall'area clienti»,
  «Addebito mensile con carta salvata», la restituzione dell'acconto a 24 ore.
  *Atteso:* la pagina dice «Modalità di prova»; i due interruttori restano accesi.
  Note: ______________________________________________

- [ ] **RES-11 · I promemoria.** Impostazioni › Agenda › Agenda e promemoria ›
  Promemoria degli appuntamenti: accendi gli SMS; «Crea il modello dei promemoria»;
  quando Meta l'ha approvato, sceglilo.
  *Atteso:* la pagina offre solo un modello con i pulsanti per confermare e per
  disdire; «Un “non posso venire” disdice l'appuntamento» è acceso; gli ultimi
  promemoria si leggono lì sotto.
  Note: ______________________________________________

- [ ] **RES-12 · Il telefono del centro.** Impostazioni › Telefono › Telefonia ›
  Twilio: il «Mittente degli SMS» (il numero), i «Paesi che si possono chiamare»
  (solo l'Italia), «Avvisami quando il mese arriva a» con un importo basso.
  *Atteso:* «Controlla» dice che lo spazio è attivo; «Questo mese» dice quanto ha
  speso, per voce.
  Note: ______________________________________________

- [ ] **RES-13 · La segreteria telefonica.** Nella pagina Telefonia: i secondi di
  squillo, l'annuncio, il messaggio dopo il segnale acceso.
  *Atteso:* una chiamata a cui nessuno risponde passa all'annuncio e al messaggio
  ([segreteria.md](./segreteria.md), SEG-13).
  Note: ______________________________________________

- [ ] **RES-14 · La posta del centro.** Impostazioni › Email › Account: aggiungi la
  casella del collaudo (per esempio un Gmail con la password per le app); scegli dove
  vanno le risposte alle email di DottorCloud.
  *Atteso:* la casella si salva con i server che DottorCloud conosce; il servizio di
  invio non è nella lista; un'email che un paziente le scrive va sulla sua pagina.
  Note: ______________________________________________

- [ ] **RES-15 · L'area dei pazienti.** Impostazioni › Pazienti › Area pazienti:
  «Sono qui» dal telefono acceso, «Avvisa la persona via email quando c'è un
  documento nuovo» acceso.
  *Atteso:* i due interruttori restano accesi; la pagina dice da dove partono gli
  SMS dell'area.
  Note: ______________________________________________

- [ ] **RES-16 · L'informativa.** Impostazioni › Pazienti › Moduli: un modulo nuovo da
  «Parti da», l'informativa con i consensi; pubblicalo e chiedilo a ogni prima
  prenotazione.
  *Atteso:* le parole dei consensi si congelano alla pubblicazione; chi prenota la
  prima volta lo deve, e l'Accoglienza lo dice.
  Note: ______________________________________________

- [ ] **RES-17 · La prenotazione online.** Impostazioni › Agenda › Prenotazione
  online: i servizi e le persone, la pagina e le regole. Poi `/prenota` dal telefono.
  *Atteso:* prima la sede, poi i servizi che vi si tengono; l'acconto detto prima del
  pulsante; il fondo tra quelli proposti.
  Note: ______________________________________________

- [ ] **RES-18 · Le pipeline.** Impostazioni › Trattative › Pipeline: «Nuovi
  pazienti» e «Preventivi»; per i preventivi a rate «Ogni rata alla scadenza» e
  «Emettile subito».
  *Atteso:* le scelte restano; un preventivo proposto dopo le copia (quelli già dati
  no).
  Note: ______________________________________________

## Il giorno 0: la fatturazione

- [ ] **RES-19 · L'azienda.** Impostazioni › Fatturazione › Azienda emittente:
  struttura sanitaria autorizzata, regime ordinario, i codici di regione, ASL e
  struttura.
  *Atteso:* i campi parlano a parole, mai codici da scegliere; i servizi hanno le
  loro schede sanitarie esenti.
  Note: ______________________________________________

- [ ] **RES-20 · Prova e attivazione.** Impostazioni › Fatturazione › Prova e
  attivazione: leggi «Cosa manca». **Non premere «Attiva la fatturazione».**
  *Atteso:* l'azienda è in prova; quello che blocca ha la croce rossa e «Imposta»
  porta dove si riempie; il resto si dice e non ferma.
  Note: ______________________________________________

- [ ] **RES-21 · I solleciti.** Impostazioni › Fatturazione › Pagamenti e solleciti:
  accesi, con le parole di «Come pagare».
  *Atteso:* sul collaudo nessun sollecito parte: una fattura di prova non si sollecita
  mai. È giusto così.
  Note: ______________________________________________

## I giorni del collaudo

- [ ] **RES-22 · Il fondo del mese.** Fatture › Convenzioni: il «Fondo Salute Più»,
  il mese, le pratiche con il loro stato. «Fattura al fondo», controllala nella
  finestra, emettila, «Invia allo SdI».
  *Atteso:* una riga per pratica (prestazione, paziente, giorno, autorizzazione,
  tessera; niente codice fiscale né diagnosi); la fattura è di prova e va all'ambiente
  di prova di Itala; non va al Sistema TS.
  Note: ______________________________________________

- [ ] **RES-23 · L'estratto.** «Esporta il mese».
  *Atteso:* un CSV con il punto e virgola, la virgola per i decimali e le date
  all'italiana; si apre in Excel senza correzioni.
  Note: ______________________________________________

- [ ] **RES-24 · Le fatture dei fornitori.** Dopo che il sistemista ne ha inserita
  una nell'area di prova di Itala: Fatture › Ricevute.
  *Atteso:* la fattura arriva con i suoi importi letti dall'XML; si segna vista, al
  commercialista, pagata; chi gestisce la fatturazione ha avuto la notifica.
  Note: ______________________________________________

- [ ] **RES-25 · La dashboard.** Dashboard, con il selettore della sede.
  *Atteso:* i numeri si muovono con la settimana (appuntamenti, assenze, «Da
  incassare dai fondi», «Rate da incassare»); con una sede scelta, l'agenda e il
  fatturato contano solo quella.
  Note: ______________________________________________

- [ ] **RES-26 · Portare le persone dal vecchio programma.** Impostazioni › Il centro ›
  I tuoi dati: un foglio Excel di cinque persone della squadra (indirizzi con il «+»),
  scritto come lo scrive un programma italiano («ROSSI MARIO», «02/01/1980», «333 123
  4567»).
  *Atteso:* l'anteprima prima di scrivere niente, ogni colonna riconosciuta, quello
  che non va detto riga per riga; chi c'è già prende solo quello che mancava.
  Note: ______________________________________________

- [ ] **RES-27 · Portare gli appuntamenti.** Nella stessa pagina, un foglio di tre
  appuntamenti futuri delle stesse persone, con un servizio che il centro non ha.
  *Atteso:* l'anteprima chiede a cosa corrisponde ogni servizio, professionista e
  ambulatorio; il servizio che non c'è va su «Altro»; rifatto, non porta niente due
  volte; gli appuntamenti futuri avranno i loro promemoria.
  Note: ______________________________________________

- [ ] **RES-28 · Portare via i dati.** Nella stessa pagina, l'esportazione di tutto.
  *Atteso:* un archivio solo, fatto in coda; si scarica; dentro, le persone, gli
  appuntamenti e i file.
  Note: ______________________________________________

- [ ] **RES-29 · La spesa del telefono.** Quando lo spazio Twilio arriva all'importo
  di RES-12.
  *Atteso:* la notifica «La spesa Twilio del mese è arrivata a …», che apre la pagina
  di Twilio.
  Note: ______________________________________________

- [ ] **RES-30 · Le impostazioni sul telefono *(telefono)*.** Apri tre pagine delle
  impostazioni dal telefono e cambia una cosa.
  *Atteso:* la pagina scorre tutta insieme; ogni impostazione ha le sue parole sopra e
  il campo largo come lo schermo; «Aggiorna» sta nella barra in fondo.
  Note: ______________________________________________
