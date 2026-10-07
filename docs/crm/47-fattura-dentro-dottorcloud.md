# 47 · La fattura fatta dentro DottorCloud

**Stato:** fatto (02/10/2026). È la terza delle tre parti della fatturazione
semplice: la prima è [45](./45-codici-in-parole.md) (ogni codice col suo nome), la
seconda [46](./46-fatturazione-sanitaria.md) (un centro medico già impostato). I
controlli del Sistema TS e dello SdI prima di emettere, in parole, sono il
[48](./48-controlli-in-parole.md).

## Il bisogno

Una fattura si faceva nel modulo del Desk: una scheda del framework con i campi
della FatturaPA, aperta in un'altra finestra, da «Nuova fattura» come da «Emetti la
fattura» di un appuntamento, di un ciclo o di un abbonamento. Chi stava alla
reception doveva sapere che cos'è un tipo documento, un regime, una natura IVA, e
scoprire solo dopo il salvataggio dove sarebbe andata la fattura.

Tre cose, poi, erano sbagliate:

- **a una persona fisica la fattura andava a nome della sua azienda.** Se la
  persona aveva un'azienda scritta sulla sua scheda (quella per cui lavora), il nome
  in fattura era quello dell'azienda, anche per la visita di un paziente;
- **i messaggi del motore restavano in inglese.** Gli errori e gli avvisi della
  classificazione e del calcolo nascevano già composti, col nome della qualifica
  dentro, e nessuna traduzione li trovava;
- **una nota di credito al Sistema TS non diceva quale fattura rimborsava.**
  L'operazione di rimborso va comunicata con il documento originale (partita IVA,
  data, numero), e quel riferimento non partiva.

## Cosa cambia

- **La fattura si fa in una finestra di DottorCloud**, in quattro parti:
  1. **per chi è**: il paziente (il cliente, senza la clinica), il tipo di
     destinatario con la riga che dice quando si usa, e i dati in fattura (nome,
     codice fiscale, indirizzo), presi dalla sua scheda fiscale e correggibili;
  2. **cosa è stato fatto**: il servizio e chi l'ha eseguito, quantità e prezzo. Il
     prezzo, la descrizione e il professionista arrivano dalla scheda del servizio;
     uno studio con un solo professionista non lo chiede;
  3. **come è stata pagata**: la modalità con la sua riga (tracciabile o no) e la
     data; per una fattura che va al Sistema TS, l'opposizione del paziente;
  4. **dove andrà**, in cima, prima di tutto il resto: «PDF + Sistema TS» o
     «Fattura elettronica», con la riga che lo spiega.

  Mentre si scrive, il server dice dove andrà, quanto fa (imponibile, cassa, IVA,
  bollo, ritenuta, totale) e **tutto** quello che manca prima di emetterla, non la
  prima cosa. Finché una riga non ha chi l'ha eseguita, lo dice e non mostra un
  totale che non sarebbe quello della fattura. Una fattura nuova vive in memoria:
  niente resta salvato a metà, la bozza si salva solo quando qualcuno lo chiede.
- **Emessa**, la finestra mostra il numero, dove è andata e a che punto è (SdI,
  Sistema TS), e offre quello che si può fare: scaricare o creare il PDF, inviarla
  allo SdI se aspetta di partire, farne la **nota di credito**.
- **La nota di credito** nasce in bozza con lo stesso cliente e le stesse righe,
  dice quale fattura corregge e, se l'originale è andato al Sistema TS, è il suo
  rimborso: la comunicazione porta il riferimento al documento originale.
- **Una fattura scartata dallo SdI** mostra perché, e invece di «Invia» offre
  «Correggila»: torna in bozza con il suo numero e la sua data, si corregge e si
  emette di nuovo entro cinque giorni dalla notifica. Una bozza che ha già il numero
  non si elimina: lascerebbe un buco nella numerazione.
- **Chi riceve decide la ritenuta**, anche su una bozza già salvata: cambiando il
  destinatario in un privato la ritenuta va via (un privato non è sostituto
  d'imposta), cambiandolo in un'azienda torna se l'azienda emittente la applica.
- **Si apre da ovunque**: «Nuova fattura» e «Apri» nella pagina delle fatture,
  «Emetti la fattura» di un appuntamento (la bozza già compilata dall'agenda), di un
  ciclo e di una rata di un abbonamento, la fattura nella storia della persona. Il
  Desk non si apre più.
- **A una persona fisica la fattura va a suo nome**; a un'azienda, a nome
  dell'azienda.
- **I messaggi del motore si traducono**: nascono come modello e argomenti
  (`Messaggio`), e si compongono nella lingua di chi legge.
- **«Apri» dice «Apri»**: nei pulsanti che aprono qualcosa diceva «Aperto», la
  parola dello stato di una trattativa.
- La testata della pagina delle fatture non si sovrappone più sul telefono: il nome
  dell'azienda si accorcia, le impostazioni restano un'icona.

## Come è fatta

- `crm/invoicing/emissione.py`: la fattura come la disegna la finestra (`_vista`:
  tutto in parole, i permessi di cosa si può fare), e le chiamate:
  - `get_invoice`, `preview` (classifica e conta in memoria, non salva), `save`,
    `issue`, `credit_note`, `delete_draft`;
  - la finestra scrive solo cliente, pagamento e righe; cassa, ritenuta, bollo e
    canale li decidono l'azienda e il motore.
- `crm/invoicing/engine/messaggi.py`: `Messaggio`, una stringa che tiene il suo
  modello e i suoi argomenti; `documento.in_parole()` la traduce.
- `crm/tessera_sanitaria/documento.py`: il rimborso (operazione R) porta l'`IdSpesa`
  dell'originale.
- `crm/invoicing/doctype/crm_invoice/crm_invoice.py`: il nome in fattura di una
  persona fisica.
- Il frontend:
  - `components/Invoices/InvoiceDialog.vue`, montata una volta in
    `GlobalModals.vue`;
  - `composables/fattura.js` (`apriFattura`, `nuovaFattura`) per aprirla da ogni
    pagina;
  - `utils/fattura.js`: cosa si manda al server, le righe dei totali, il titolo.
- `crm/clinica/parole.py`: con la clinica accesa la fattura è per un paziente.

## Verifiche

- `crm/tests/test_emissione.py` (sul sito):
  - l'anteprima dice dove va e quanto fa, e non salva niente;
  - senza righe, e con una riga senza chi l'ha eseguita, dice cosa manca;
  - si salva, si emette, si fa la nota di credito, che al Sistema TS è il rimborso
    dell'originale;
  - una bozza si elimina, una fattura emessa no;
  - a una persona la fattura col suo nome, a un'azienda col nome dell'azienda;
  - chi riceve decide la ritenuta;
  - una scartata si corregge con lo stesso numero e non si elimina;
  - i messaggi del motore si traducono col loro modello.
- `frontend/tests/unit/fattura.test.js`: cosa si manda, i totali che contano, il
  titolo.
- Le suite della fatturazione e del Sistema TS.
- Nel browser, in italiano, con la clinica accesa:
  - una fattura nuova per un paziente, con il servizio e la professionista;
  - il codice fiscale che manca, poi scritto;
  - la bozza salvata, emessa (2026/S/1), la sua nota di credito;
  - una fattura elettronica consegnata, aperta dall'elenco;
  - la finestra e la testata su un telefono.
