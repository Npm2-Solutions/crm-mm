# 60 · I pagamenti online: fatture, acconti e abbonamenti con carta, sull'account Stripe del centro

**Stato:** fatto (08/10/2026; la fattura d'acconto, gli abbonamenti dall'area e
l'addebito mensile il 09/10/2026). Spenti finché il centro non collega il suo
account Stripe; un servizio chiede un acconto solo se il centro lo sceglie su quel
servizio; l'area vende abbonamenti e addebita la carta salvata solo con i due
interruttori accesi.

**Il principio.** Stripe incassa e basta: la fattura è sempre di DottorCloud (SdI,
Sistema TS), fatta dal suo motore, e nasce quando arrivano i soldi. Un pagamento
fatto prima della prestazione la rende effettuata per quell'importo (art. 6, c. 4,
DPR 633/72): si fattura il giorno in cui è pagato. Mai Stripe Billing, i suoi
abbonamenti o le sue fatture, che non sono fatture italiane.

## Il bisogno

- La persona paga **una fattura da casa**, con carta, dalla sua area o da un link
  che la reception le manda: la fattura risulta incassata da sola, senza che
  nessuno controlli il conto.
- Chi prenota online un servizio che il centro vuole garantito paga **un
  acconto** (o il prezzo intero) subito: il posto è tenuto mezz'ora, la
  prenotazione è confermata quando il pagamento arriva, e si libera se non arriva.

## Perché sull'account del centro

DottorCloud non rivende traffico e non tiene soldi (come con Twilio, doc 52): il
centro collega **il suo** account Stripe, i soldi vanno lì, Stripe è il fornitore
del centro per i dati di pagamento e DottorCloud non vede mai la carta. Niente
Stripe Connect: un'app Connect farebbe di NPM2 una piattaforma che incassa per
conto d'altri, con i suoi obblighi; qui DottorCloud crea solo i link e legge
l'esito.

## Come si collega

Impostazioni > Fatturazione > Pagamenti online (`pagamenti.gestisci`, il
responsabile del centro):

1. un account Stripe attivato con i dati e il conto del centro;
2. dalla dashboard di Stripe, Sviluppatori > Chiavi API, la **chiave segreta**
   (`sk_test_…` per provare, `sk_live_…` per i pagamenti reali) o una chiave con
   restrizioni (`rk_…`) che possa scrivere Checkout Sessions, Webhook Endpoints e
   Refunds e leggere Charges;
3. incollata e «Collega Stripe»: DottorCloud chiede a Stripe di chi è l'account
   (nome, paese, valuta; la modalità dal prefisso della chiave, «Modalità di
   prova»), crea sull'account **il suo endpoint del webhook** per i quattro eventi
   che legge (`checkout.session.completed`, `checkout.session.expired`,
   `charge.refunded`, `payment_intent.payment_failed`) e ne tiene il segreto di
   firma. Chiave e segreto sono campi Password, non tornano mai alla pagina e non
   finiscono in un log.

Dal 09/10/2026 l'endpoint chiede anche `payment_intent.succeeded`, l'esito di un
addebito sulla carta salvata: «Controlla» aggiunge a un endpoint fatto prima gli
eventi che gli mancano (e lo fa da sé quando si accende l'addebito mensile), come
rifà l'endpoint se qualcuno l'ha cancellato o spento su Stripe; «Scollega» lo
cancella su Stripe e dimentica chiave e segreto.

## Una fattura pagata online

- Si paga solo una fattura **emessa a una persona**, ancora da incassare: mai una
  nota di credito, una fattura di prova, una scartata dallo SdI, quelle dei dati
  di prova.
- Il link è una **Checkout Session** di Stripe per quanto resta da pagare
  (`incassi.da_pagare`), con il numero della fattura e il nome del centro, fatto
  quando qualcuno lo chiede e tenuto finché vale (un giorno).
- Dall'**area**: «Paga online» sulla riga della fattura (mai nell'anteprima del
  centro); al ritorno «Grazie: il pagamento è andato a buon fine», poi «Pagata
  online il …». Il sollecito (doc 45) porta già all'area.
- Dalla **reception**: nel dialogo della fattura «Link di pagamento», da copiare e
  mandare (`fatture.incassi`).
- Pagata: la fattura è incassata dalla stessa porta del «Incassata oggi»
  (`incassi.segna`), il suo registro dice «Pagata online con carta su Stripe
  (pi_…)», con MP08 e il payment intent; chi gestisce la fatturazione è avvisato.
  Il metodo di pagamento scritto nella fattura emessa non cambia: era già nel suo
  XML.
- Un **rimborso** fatto su Stripe è scritto nel pagamento e nel registro della
  fattura e detto a chi gestisce la fatturazione: la fattura **resta incassata**,
  decide una persona (una nota di credito, «Non incassata»).

## L'acconto alla prenotazione

- Su ogni servizio (Agenda > Servizi > Online): «Pagamento online alla
  prenotazione»: nulla, un acconto (un importo, mai più del prezzo) o il prezzo
  intero. Offerto solo con Stripe collegato.
- Il **prezzo intero** è quanto farebbe la fattura del servizio (cassa, IVA e bollo
  compresi, dalla sua scheda fiscale): la fattura d'acconto è allora la fattura
  intera, e alla reception non resta niente.
- /prenota lo dice nel riepilogo e prima del pulsante; dopo «Conferma
  prenotazione» il posto è tenuto come richiesta online (`Scheduled`) e la persona
  va alla pagina di Stripe. Torna sulla sua prenotazione: «Manca il pagamento» con
  «Vai al pagamento», o l'attesa della conferma, poi «Prenotazione confermata»
  con «Acconto pagato online: 30,00 €». Email e avviso al professionista partono
  solo a pagamento arrivato.
- Il link scade dopo mezz'ora (il minimo di Stripe): l'evento
  `checkout.session.expired`, o il giro ogni dieci minuti che chiede a Stripe e
  chiude il link, **liberano il posto**. Un pagamento arrivato tardi su un posto già
  liberato è restituito subito.
- Una disdetta mentre il pagamento aspetta chiude il link. Una disdetta di chi ha
  pagato, almeno N ore prima (24 per partire; Impostazioni > Pagamenti online),
  restituisce l'acconto su Stripe da sola; più tardi resta al centro.

## La fattura d'acconto

- Quando Stripe conferma l'acconto (o il prezzo intero) pagato a /prenota,
  DottorCloud emette da solo una **fattura d'acconto** alla persona per quell'importo
  (`crm/pagamenti/fatture.py`): dal motore di sempre (mai fatture accanto al motore),
  la scheda fiscale del servizio (sanitaria: va al Sistema TS come sempre), il
  professionista dell'appuntamento, chi paga per la persona; una riga «Acconto per
  Fisioterapia del 12 ottobre 2026». La riga si trova in modo che la fattura, con
  cassa, IVA e bollo, faccia esattamente i soldi arrivati. Pagata con carta (MP08),
  incassata dalla stessa porta del «Incassata oggi» (`incassi.segna`); allo SdI
  parte come le altre, se il centro ha acceso l'invio automatico.
- È legata all'appuntamento con `advance_for`, **mai con `appointment`**: quello la
  farebbe chiudere come «venuto» e la toglierebbe dalle cose da fatturare.
- Se non si può emettere (manca il codice fiscale, la scheda fiscale o il
  professionista: `documento.da_correggere`) resta una bozza, e chi gestisce la
  fatturazione è avvisato con il perché. La prenotazione si conferma comunque.
- Una volta sola, comunque Stripe ripeta l'evento.
- Quando la reception fattura poi l'appuntamento, la proposta è **il saldo**: il
  prezzo meno gli imponibili degli acconti già fatturati alla stessa persona (meno
  le loro note di credito), con la causale «Saldo; acconto fattura N. 2026/S/12 del
  9 ottobre 2026». Se l'acconto copriva tutto non si propone niente: «Questo
  appuntamento è già fatturato: fattura d'acconto …», e l'appuntamento esce dalle
  cose da fatturare. Il dialogo della fattura elenca le fatture d'acconto.
- Un acconto **restituito** (la disdetta in tempo, o un rimborso fatto su Stripe,
  anche in parte) diventa una **nota di credito** sulla fattura d'acconto per la
  quota restituita, emessa da sola (al Sistema TS come rimborso dell'originale, come
  sempre); bozza e avviso se non si può. Una fattura d'acconto ancora in bozza non
  ha numero: si toglie.
- **I dati di prima.** Gli acconti pagati prima del 09/10/2026 senza fattura non si
  fatturano a ritroso: per quelli il dialogo dice ancora «Acconto pagato online senza
  fattura: 30,00 €», e la fattura dell'appuntamento si fa intera e si segna pagata
  con carta per quella parte, come prima.

## Comprare un abbonamento dall'area

- Impostazioni > Fatturazione > Pagamenti online: «Vendi abbonamenti dall'area
  clienti» (spento). Su ogni tipo di abbonamento (Agenda > Servizi > Abbonamenti)
  «Vendibile online dall'area», offerto solo con quell'interruttore acceso; vuole
  una scheda fiscale e un prezzo (la fattura si fa al pagamento).
- Nell'area, in Appuntamenti, «Acquista online»: ogni abbonamento in vendita con
  quanto dura, cosa comprende, quanto si paga - in una volta, o al mese per quante
  rate -, il prezzo come lo fa la fattura (cassa e IVA comprese). Mai
  nell'anteprima del centro; mai per i dati di prova.
- «Acquista» apre un foglio con il riepilogo e «Vai al pagamento»: la Checkout di
  Stripe. Pagato **subito**: l'abbonamento è venduto da oggi con il codice di
  sempre (`abbonamenti.nuovo`), alla persona o al figlio per cui agisce (le regole
  di chi entra nell'area), e la sua fattura emessa e incassata con carta. Il
  pagamento che non arriva non vende niente.
- Pagato **al mese** (solo con anche l'addebito mensile acceso): la Checkout è per
  la prima rata, con la persona come cliente sull'account del centro (`CRM Stripe
  Customer`, segue la persona e se ne va con lei) e la carta tenuta per le
  successive (`setup_future_usage=off_session`); sopra il pulsante di Stripe e nel
  nostro foglio le parole del mandato: «Autorizzi il centro ad addebitare 49,78 €
  ogni mese sulla carta fino al 8 gennaio 2027; puoi disdire dall'area». Pagata, la
  prima rata è fatturata e incassata; della carta si tiene l'id di Stripe (`pm_…`),
  il circuito, le ultime quattro cifre e la scadenza, mai altro.
- I **cicli di sedute** non hanno un catalogo (ognuno nasce alla reception con il
  servizio, le sedute e il prezzo): l'area vende solo i tipi di abbonamento. Un
  ciclo pagato al mese non esiste (un ciclo non ha rate).

## L'addebito mensile con la carta salvata

- Impostazioni > Pagamenti online: «Addebito mensile con carta salvata» (spento,
  solo con la vendita dall'area accesa).
- Il giro del giorno degli abbonamenti, prima di fatturare le rate, **addebita la
  carta** per ogni rata dovuta di un abbonamento con la carta attiva: un
  PaymentIntent off session confermato, con una chiave di idempotenza per tentativo
  (abbonamento, rata, numero del tentativo) e il tentativo scritto prima di chiedere
  a Stripe. **Solo se riesce** la rata si fattura, già incassata con carta (MP08);
  la risposta di Stripe o il webhook, quale arriva prima, applicata una volta. Il
  giro fatto due volte lo stesso giorno addebita una volta.
- **Non riuscito** (rifiutata, scaduta, la banca chiede di confermare): nessuna
  fattura; la persona riceve «Il tuo pagamento non è riuscito» per email, con
  l'entrata nella sua area, e per SMS se i solleciti del centro vanno anche per SMS
  (mai a chi ha scritto STOP); chi gestisce la fatturazione è avvisato. La carta si
  riprova 3 e 7 giorni dopo la scadenza, tre tentativi in tutto, mai due nello stesso
  giorno; poi la rata si fattura come tutte le altre (`issue_invoices`) e la segue
  la reception, con i solleciti di sempre. Dall'area la persona può pagarla subito
  («Paga ora»: una Checkout per quella rata, che pagata la fattura allo stesso modo).
- Nell'area, sulla scheda dell'abbonamento: «Addebito mensile sulla carta Visa ••••
  4242 · prossimo 1 novembre 2026, 49,78 €», o l'addebito non riuscito e quando si
  riprova; «Interrompi gli addebiti»: la carta non è più addebitata (e Stripe la
  stacca dal cliente), «Le rate restano da pagare come previsto dal tuo
  abbonamento». Il rinnovo automatico fa un abbonamento nuovo senza carta.
- Alla reception, sulla scheda dell'abbonamento della persona: «Addebito automatico
  attivo · carta Visa •••• 4242», «Non riuscito il … : la persona ha il link per
  pagare», e «Interrompi gli addebiti» anche da lì. La chiusura di cassa conta questi
  incassi come pagamenti con carta del giorno (incassati quel giorno da
  `incassi.segna`).
- Gli abbonamenti senza carta fanno esattamente come prima.
- Le condizioni dell'addebito ripetuto (il mandato, il recesso, le informazioni al
  consumatore) vanno riviste dal consulente del centro: non lo dice lo schermo.

## Il registro

- `CRM Online Payment`: chi, per cosa (fattura, acconto, abbonamento acquistato,
  rata addebitata), quanto, gli id di Stripe, la fattura fatta al pagamento e la
  nota di credito di un acconto restituito, il tentativo, lo stato (In attesa,
  Pagato, Scaduto, Rimborsato…); segue la persona, si cancella con lei, va
  nell'esportazione dei dati da solo. Così `CRM Stripe Customer`.
- `CRM Stripe Event`: ogni evento di Stripe, tenuto prima di applicarlo e applicato
  una volta (Stripe li rimanda finché non sente 2xx). La firma
  (`Stripe-Signature`, HMAC-SHA256 del corpo grezzo, cinque minuti di tolleranza) è
  controllata prima di leggere: una sbagliata o vecchia è un 400. Un evento di un
  altro sito sullo stesso account (il suo `metadata.site`) è ignorato.

## Mai

- Per i dati di prova (`guardie.mai_a_stripe`), per una fattura di prova, nell'anteprima dell'area.

## Lasciato fuori

- **La penale di mancata presentazione** con carta salvata: ora si potrebbe (la carta
  salvata e l'addebito off session ci sono), ma chiede regole chiare per il
  consumatore e il consenso a quella penale. Un passo a parte.
- **L'addebito diretto SEPA** al posto della carta.
- **I cicli venduti dall'area**: manca un catalogo dei cicli.
- **I POS e i terminali** (SumUp, Stripe Terminal) alla cassa.

## Sul banco di prova

`stripe_api` nel `site_config.json` di un sito di prova punta DottorCloud a uno
Stripe finto (`crm/pagamenti/tests/stripe_finto.py`); su un centro non c'è mai.
