# 60 · I pagamenti online: fatture e acconti con carta, sull'account Stripe del centro

**Stato:** fatto (08/10/2026). Spenti finché il centro non collega il suo account
Stripe; un servizio chiede un acconto solo se il centro lo sceglie su quel servizio.

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

«Controlla» rifà l'endpoint se qualcuno l'ha cancellato o spento su Stripe;
«Scollega» lo cancella su Stripe e dimentica chiave e segreto.

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
- Quando la reception fattura quell'appuntamento, il dialogo dice «Acconto già
  pagato online: 30,00 €»: la fattura si fa intera e si segna pagata con carta per
  quella parte. È la strada più semplice e corretta: il motore delle fatture
  elettroniche non conosce gli anticipi, e toglierlo dal totale farebbe una fattura
  sbagliata.

## Il registro

- `CRM Online Payment`: chi, per cosa (fattura o acconto), quanto, gli id di
  Stripe, lo stato (In attesa, Pagato, Scaduto, Rimborsato…); segue la persona,
  si cancella con lei, va nell'esportazione dei dati da solo.
- `CRM Stripe Event`: ogni evento di Stripe, tenuto prima di applicarlo e applicato
  una volta (Stripe li rimanda finché non sente 2xx). La firma
  (`Stripe-Signature`, HMAC-SHA256 del corpo grezzo, cinque minuti di tolleranza) è
  controllata prima di leggere: una sbagliata o vecchia è un 400. Un evento di un
  altro sito sullo stesso account (il suo `metadata.site`) è ignorato.

## Mai

- Per i dati di prova (`guardie.mai_a_stripe`), per una fattura di prova, nell'anteprima dell'area.

## Lasciato fuori

- **La penale di mancata presentazione** con carta salvata: chiede una
  SetupIntent e un addebito off-session con l'autenticazione forte (SCA) della
  persona, e regole chiare per il consumatore. Da progettare a parte.
- **I POS e i terminali** (SumUp, Stripe Terminal) alla cassa.

## Sul banco di prova

`stripe_api` nel `site_config.json` di un sito di prova punta DottorCloud a uno
Stripe finto (`crm/pagamenti/tests/stripe_finto.py`); su un centro non c'è mai.
