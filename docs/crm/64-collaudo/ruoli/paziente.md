# Collaudo · Paziente

## A cosa serve

Questa lista è per i colleghi che fanno i pazienti del Poliambulatorio San Luca, sul
proprio telefono: prenotare online pagando l'acconto con le carte di prova di Stripe,
rispondere al promemoria, entrare nell'area, firmare i moduli e il preventivo,
comprare un abbonamento, pagare, disdire, scrivere al centro, entrare nella visita
online, dire «Sono qui». È quello che farà un paziente vero: se una cosa non si
capisce al primo colpo, è una segnalazione anche quella. Ogni riga ha il suo codice
(per esempio PAZ-04): [segnalazioni.md](../segnalazioni.md).

## Prima di cominciare

- **Il telefono:** il tuo, con il browser che usi di solito. Se il tuo numero è tra i
  cinque che il sistemista ha aggiunto al numero di test di WhatsApp, ricevi anche i
  WhatsApp; se no, SMS ed email.
- **L'email da paziente:** diversa da quella del tuo utente di lavoro, per esempio con
  il «+» (`nome.cognome+paziente@…`), se la tua casella lo accetta.
- **I dati:** il tuo nome, il tuo cellulare, la tua email da paziente. Disturbi e
  risposte inventati: mai un tuo dato sanitario vero.
- **I soldi sono finti:** Stripe è in modalità di prova. Le carte di prova (scadenza
  qualsiasi nel futuro, CVC tre cifre qualsiasi):

  | Carta | Cosa fa |
  |---|---|
  | `4242 4242 4242 4242` | paga |
  | `4000 0000 0000 9995` | rifiutata: fondi insufficienti |
  | `4000 0025 0000 3155` | chiede la conferma della banca la prima volta |
  | `4000 0027 6000 3184` | chiede la conferma della banca ogni volta |

- **L'indirizzo:** `https://collaudo.dottorcloud.com/prenota` per prenotare,
  `https://collaudo.dottorcloud.com/area` per l'area.
- **Le fatture:** sul collaudo sono di prova e non compaiono nell'area; «Paga online»
  su una fattura qui non si vede. È giusto così.

## Il giorno 1: prenotare

- [ ] **PAZ-01 · Una visita con l'acconto.** Da `/prenota`: la «Visita medica», la
  sede, un orario almeno 26 ore dopo adesso, «Per me», i tuoi dati, l'informativa,
  «Conferma prenotazione». Poi «Vai al pagamento».
  *Atteso:* prima del pulsante la pagina dice quanto paghi online; il posto è tenuto
  30 minuti; si apre la pagina di pagamento di Stripe.
  Note: ______________________________________________

- [ ] **PAZ-02 · La carta rifiutata, poi quella buona.** Su Stripe, prima la carta
  `…9995`, poi la `4242…`.
  *Atteso:* la prima è rifiutata da Stripe, e si riprova; con la seconda torni sulla
  tua prenotazione: «Prenotazione confermata», «Acconto pagato online» con l'importo;
  l'email di conferma arriva.
  Note: ______________________________________________

- [ ] **PAZ-03 · Il pagamento che non arriva.** Un'altra «Visita medica»: conferma, ma
  su Stripe non pagare. Dopo mezz'ora riapri la prenotazione dal suo link.
  *Atteso:* «Il pagamento non è arrivato in tempo: il posto è stato liberato.»; il
  posto torna libero in agenda.
  Note: ______________________________________________

- [ ] **PAZ-04 · La conferma della banca.** La «Visita nutrizionale» (si paga tutta
  online) con la carta `…3184`.
  *Atteso:* Stripe mostra la pagina della banca di prova; confermata, la visita è
  pagata e confermata.
  Note: ______________________________________________

- [ ] **PAZ-05 · Il controllo online.** Il «Controllo nutrizionale online», pagato con
  la `4242…`, per domani.
  *Atteso:* la pagina dice che è una visita online e che si entra dall'area, da 15
  minuti prima; nessuna email porta il link della stanza.
  Note: ______________________________________________

- [ ] **PAZ-06 · Con il fondo.** Una «Visita medica» scegliendo «Fondo Salute Più» e un
  numero di tessera inventato.
  *Atteso:* niente acconto; «Richiesta inviata»: aspetta il sì del centro; quando la
  segreteria conferma, arriva l'email.
  Note: ______________________________________________

- [ ] **PAZ-07 · La lista d'attesa.** Da `/prenota`, la «Visita fisioterapica»:
  «Nessun orario va bene?» › «Mettiti in lista d'attesa», i giorni e le parti del
  giorno, «Mettimi in lista».
  *Atteso:* «Sei in lista d'attesa»; l'email con il link per vedere la lista o
  uscirne. Quando si libera un posto, l'offerta arriva; confermata dal link, la
  visita è tua.
  Note: ______________________________________________

- [ ] **PAZ-08 · I moduli a casa.** Dall'email della segreteria: apri il link, chiedi
  il codice, leggilo nell'email, compila, firma con il dito.
  *Atteso:* il codice arriva in pochi secondi; i campi sono grandi e la pagina non si
  ingrandisce da sola; firmato, il modulo te lo dice.
  Note: ______________________________________________

- [ ] **PAZ-09 · L'area.** Dall'email d'invito, «Entra».
  *Atteso:* l'area del centro, con il suo logo in alto e «Con tecnologia DottorCloud» in
  fondo; in basso Oggi, Agenda, Piani, Documenti, Messaggi; il prossimo appuntamento
  in evidenza.
  Note: ______________________________________________

- [ ] **PAZ-10 · L'app e la passkey.** Nell'area: la carta per metterla sulla
  schermata Home, poi «Aggiungi una passkey». Esci e rientra con «Entra con una
  passkey».
  *Atteso:* l'area si apre come un'app, senza la barra del browser; si rientra con il
  viso o l'impronta, senza codice.
  Note: ______________________________________________

- [ ] **PAZ-11 · Con il codice.** Da un altro browser, `/area` › «Entra con la tua
  email» › «Mandami il codice».
  *Atteso:* il codice di sei cifre arriva per email e vale qualche minuto; con
  un'email che non ha l'area la pagina dice lo stesso, senza rivelare niente.
  Note: ______________________________________________

## Il giorno 2: la visita

- [ ] **PAZ-12 · Il promemoria.** Quando arriva (WhatsApp, SMS o email), conferma:
  su WhatsApp il pulsante «Confermo», per SMS rispondi «SI», per email «Confermo che
  ci sarò» dalla pagina.
  *Atteso:* ti arriva un grazie (dalla pagina: «Hai confermato: ti aspettiamo.»);
  alla segreteria il segno «Ha confermato» accanto al tuo nome.
  Note: ______________________________________________

- [ ] **PAZ-13 · Non posso venire.** Al promemoria di un altro appuntamento rispondi
  «Devo disdire» (o «NO» per SMS).
  *Atteso:* l'appuntamento è disdetto e te lo dice; il posto torna libero per chi
  aspetta.
  Note: ______________________________________________

- [ ] **PAZ-14 · Preparare la visita.** Nell'area, «Prepara l'appuntamento».
  *Atteso:* i moduli che devi ancora firmare per quella visita, un tocco per
  aprirli; firmati, spariscono dalla lista.
  Note: ______________________________________________

- [ ] **PAZ-15 · Sono qui.** Arrivato al centro (o mezz'ora prima della visita),
  «Sono qui».
  *Atteso:* «Sei in sala d'attesa: il centro sa che sei qui.»; prima della mezz'ora
  non si può ancora.
  Note: ______________________________________________

- [ ] **PAZ-16 · La visita online.** All'ora del controllo online, nell'area «Entra
  nella visita».
  *Atteso:* prima dei 15 minuti l'area dice quando si apre; poi entri nella stanza
  con la telecamera e il microfono, e il dietista è lì.
  Note: ______________________________________________

- [ ] **PAZ-17 · Scrivere al centro.** Messaggi: una domanda e una foto.
  *Atteso:* il messaggio parte; la risposta della segreteria arriva nell'area, e
  un'email ti dice che c'è una novità.
  Note: ______________________________________________

- [ ] **PAZ-18 · La chat degli orari.** Nella chat: «A che ora aprite il sabato?»;
  poi una domanda sulla salute; poi «ho un forte dolore al petto» (è una prova: non
  chiamare nessuno).
  *Atteso:* la prima risposta viene da quello che ha scritto il centro; la domanda
  sulla salute passa a una persona del centro; la terza dice subito di chiamare il
  112.
  Note: ______________________________________________

## Il giorno 3: il seguito

- [ ] **PAZ-19 · Il preventivo.** Nell'area, il preventivo del dentista: leggi il
  piano dei pagamenti, «Accetta e firma», firma con il dito.
  *Atteso:* se non sei appena entrato, ti chiede il codice; firmato, la copia firmata è
  in Documenti.
  Note: ______________________________________________

- [ ] **PAZ-20 · Non accetto.** Un secondo preventivo: «Non accetto», con un motivo.
  *Atteso:* il preventivo dice che non l'hai accettato; il centro lo sa.
  Note: ______________________________________________

- [ ] **PAZ-21 · L'abbonamento al mese.** Nell'area, Agenda › «Acquista online» ›
  «Pilates mensile», al mese. Leggi le parole del mandato, «Vai al pagamento», la
  carta `…3155`.
  *Atteso:* prima di pagare la frase «Autorizzi il centro ad addebitare … ogni mese
  sulla carta fino al …»; dopo, «Grazie: il pagamento è andato a buon fine…»; sulla
  scheda dell'abbonamento «Addebito mensile sulla carta … · prossimo …».
  Note: ______________________________________________

- [ ] **PAZ-22 · L'addebito che non riesce.** Un secondo «Pilates mensile» con la carta
  `…3184`. Il sistemista fa partire l'addebito del mese dopo
  ([server-di-collaudo.md](../server-di-collaudo.md#stripe-in-modalità-di-prova)).
  *Atteso:* l'email «Il tuo pagamento non è riuscito», con l'entrata nell'area;
  sull'abbonamento l'addebito non riuscito e quando si riprova; «Paga ora» con la
  `4242…` lo paga.
  Note: ______________________________________________

- [ ] **PAZ-23 · Fermare gli addebiti.** Sul primo abbonamento, «Interrompi gli
  addebiti».
  *Atteso:* la domanda «Interrompere gli addebiti sulla carta?»; poi la carta non è
  più addebitata, e l'area dice che le rate restano da pagare come prevede
  l'abbonamento.
  Note: ______________________________________________

- [ ] **PAZ-24 · Spostare.** Dal link della prenotazione di PAZ-01, «Cambia data o
  orario».
  *Atteso:* gli orari liberi; spostata, la prenotazione dice l'orario nuovo, nella
  stessa sede.
  Note: ______________________________________________

- [ ] **PAZ-25 · Disdire in tempo.** Una visita con l'acconto, più di 24 ore prima:
  «Annulla prenotazione» › «Sì, annulla».
  *Atteso:* «Prenotazione annullata» e «Acconto restituito»; su Stripe il rimborso.
  Note: ______________________________________________

- [ ] **PAZ-26 · Il questionario.** Dal link del questionario dopo la visita
  ([marketing.md](./marketing.md)), rispondi da 0 a 10.
  *Atteso:* si apre dal link, senza codice; si risponde con un tocco.
  Note: ______________________________________________

- [ ] **PAZ-27 · I piani.** Nell'area, Piani e Oggi: spunta gli esercizi di oggi con
  un tocco, di' quanto è stato faticoso da 1 a 10, recupera quelli di ieri; sulla
  lista della spesa spunta tre alimenti.
  *Atteso:* ogni spunta resta; si recupera al massimo due giorni indietro; le spunte
  della spesa restano sul telefono.
  Note: ______________________________________________

- [ ] **PAZ-28 · I documenti.** Documenti: il documento che il centro ti ha messo
  online.
  *Atteso:* prima di scaricarlo l'area chiede un codice; poi si apre.
  Note: ______________________________________________

- [ ] **PAZ-29 · STOP.** Rispondi «STOP» a un SMS del centro; poi «START».
  *Atteso:* «Non riceverà più gli SMS automatici di Poliambulatorio San Luca. Scriva
  START per riceverli di nuovo.»; con START tornano.
  Note: ______________________________________________

- [ ] **PAZ-30 · Prenotare di nuovo.** Nell'area, «Prenota di nuovo».
  *Atteso:* `/prenota` sul servizio dell'ultima visita, con i tuoi dati già scritti.
  Note: ______________________________________________
