# Il listino di DottorCloud

**Stato:** ✅ listino finale (01/10/2026), con il telefono cambiato il
03/10/2026: 50 € l'anno per attivarlo, e chiamate, numeri e SMS li paga il centro
a Twilio. Le soglie degli ambulatori si verificano con i primi centri. Prezzi al
mese, IVA esclusa, se non dicono altro. Sostituisce il listino a moduli del 29/09:
ora la parte clinica è inclusa, la taglia la danno gli ambulatori e la
fatturazione è un extra. Il CRM conta così dal 01/10/2026: vedi
[Nel CRM](#nel-crm).

## In una pagina

- **Un piano solo per le cliniche**, con dentro la parte clinica e l'area
  pazienti. La taglia la danno gli ambulatori; specialisti e utenti sono
  illimitati.
- **Gli extra si aggiungono**: fatturazione, marketing, telefono, assistente,
  firma avanzata.
- **I consumi si pagano a parte.** WhatsApp lo paga il centro direttamente a Meta,
  chiamate e SMS a Twilio, sul suo account.
- **I servizi dell'agenzia sbloccano gli extra con cui lavora.** Il piano lo paga
  sempre il centro.

## Il piano

| Livello | Ambulatori | Al mese |
|---|---|---|
| Solo | 1 | 49 € |
| Studio | fino a 2 | 99 € |
| Centro | fino a 5 | 189 € |
| Poliambulatorio | fino a 10 | 319 € |
| Oltre 10 | | +25 € ad ambulatorio |

Ogni livello comprende:

- persone e agenda con le sale, cicli di sedute, abbonamenti e liste d'attesa;
- prenotazione online e piattaforme come MioDottore, promemoria;
- conversazioni: email, WhatsApp, SMS;
- preventivi;
- moduli con firma semplice e registro dei consensi, documenti della persona;
- cartella clinica e referti, dossier, sintesi, odontogramma, piani alimentari e
  di riabilitazione;
- area pazienti: l'app della persona (appuntamenti, moduli, documenti, messaggi),
  con i piani di allenamento e di abitudini e i programmi a tappe;
- dashboard, utenti e livelli.

Le funzioni sono le stesse in tutti i livelli: cambia solo la taglia.

## Gli extra

| Extra | Solo | Studio | Centro | Poliambulatorio |
|---|---|---|---|---|
| Fatturazione | 15 € | 25 € | 39 € | 59 € |
| Crediti SdI inclusi, l'anno | 240 | 500 | 1.200 | 2.400 |
| Marketing | 29 € | 49 € | 79 € | 109 € |

- **Fatturazione**: fatture illimitate e invio al Sistema TS con le credenziali
  dello studio, sempre compreso. Le fatture sanitarie ai privati vanno al TS e non
  consumano crediti. Senza questo extra il centro fattura con il commercialista o
  con un altro programma.
- **Marketing**: automazioni, campagne, Meta (lead e spesa), social,
  tracciamento, costo per nuovo paziente, sito.
- **Telefono**: 50 € l'anno per attivarlo, per ogni taglia, e nient'altro.
  Centralino nel browser, dialer, registrazioni e trascrizioni sull'account Twilio
  del centro, collegato da DottorCloud ([doc 52](../../crm/52-twilio-del-centro.md)):
  chiamate, numeri e SMS il centro li paga a Twilio, al prezzo di Twilio, e la
  spesa la vede nella pagina di Twilio. Con la segreteria dell'agenzia è nel
  prezzo del servizio.
- **Assistente**: 19 € al mese per ogni professionista che lo usa. Scrive le bozze
  dalla nota, mette la visita dettata nei campi, riassume prima della visita.
- **Firma avanzata**: 39 € al mese per centro, fino a 2.000 firme l'anno.
  Consenso informato e preventivi si firmano con un codice SMS e valgono come su
  carta ([design](../../verticali/clinica/design.md#la-firma)). Il fornitore costa circa 30 € al mese
  (Namirial, 360 € l'anno per 2.000 documenti,
  [ricerca](../../verticali/clinica/ricerca-design.md#34-i-fornitori)).

**Il Sistema TS sta sempre nella fatturazione.** Chi fattura prestazioni sanitarie
a privati le deve comunicare al Sistema TS e non le può mandare allo SdI: lo sa il
registro delle professioni del modulo TS
(`crm/tessera_sanitaria/engine/professioni.py`). Per questo il TS non è un extra a
parte: chi fattura con DottorCloud ce l'ha.

## I consumi

| Voce | Prezzo | Come si paga |
|---|---|---|
| Messaggi WhatsApp | tariffe di Meta | a Meta, con la carta del centro in Business Suite |
| Chiamate, numeri e SMS | tariffe di Twilio | a Twilio, sull'account del centro |
| Crediti SdI oltre quelli inclusi | 0,10 € a credito, pacchetti da 500 (50 €) | nella fattura del mese |
| SMS sull'account dell'agenzia, con la segreteria | a consumo | nella fattura del mese |
| Firme avanzate oltre le 2.000 l'anno | a consumo | nella fattura del mese |
| Spazio per i file oltre l'incluso (1 TB; 2 TB da Poliambulatorio) | 10 € al TB al mese (proposta) | nella fattura del mese |

Un credito vale una fattura trasmessa allo SdI o ricevuta; una fattura alla PA ne
vale 3. Le fatture scartate per errori di formato non consumano crediti. Quando i
crediti finiscono le fatture partono lo stesso, perché hanno scadenze di legge: il
CRM avvisa all'80%.

## I servizi dell'agenzia

| Servizio | Prezzo indicativo | Sblocca |
|---|---|---|
| Segreteria: telefono e WhatsApp, prenotazioni, richiami | da 250 € fino a circa 100 appuntamenti al mese, circa 490 € fino a 250 | Telefono, chiamate comprese, e gli account della segreteria |
| Campagne e lead: inserzioni, moduli, automazioni di contatto e richiamo, report | 390–890 € più il budget pubblicitario | Marketing |
| Crescita: campagne più la segreteria che richiama i lead | i due servizi insieme, scontati | Telefono e Marketing |
| Avvio: importazione, configurazione, modelli, formazione | 290–1.490 € una volta sola, gratis con 12 mesi di servizio | — |

- **Il piano lo paga sempre il centro**: la cartella è sua e non dipende dal
  contratto con l'agenzia.
- **Quando un servizio finisce**, gli extra che sbloccava restano attivi 30 giorni.
  Poi si pagano a listino, oppure diventano di sola lettura: non si cancella
  niente, e campagne e automazioni vanno in pausa.
- **Con la segreteria il telefono è dell'agenzia**: lo spazio Twilio sta nel suo
  account, e il telefono e le chiamate sono nel prezzo del servizio; gli SMS vanno
  nella fattura del mese.

## Esempi

| Chi | Cosa prende | Al mese |
|---|---|---|
| Fisioterapista da solo, che fattura con DottorCloud | Solo + Fatturazione | 64 € |
| Studio di nutrizione, 2 stanze, 4 professioniste | Studio + Fatturazione | 124 € |
| Fisioterapia, 2 stanze, che chiama i pazienti dal browser | Studio + Fatturazione + Telefono, con il suo account Twilio | 124 € più 50 € l'anno; chiamate e SMS a Twilio |
| Poliambulatorio, 5 ambulatori, 14 specialisti, campagne dell'agenzia | Centro + Fatturazione; Marketing incluso nel servizio | 228 € più le campagne |
| Poliambulatorio, 8 ambulatori, 25 specialisti, segreteria dell'agenzia | Poliambulatorio + Fatturazione; Telefono incluso nel servizio | 378 € più la segreteria |

## Le regole

- **Ambulatorio**: una stanza in cui si visita o si tratta, come uno studio o un
  box. La palestra di fisioterapia conta come uno.
- **Superare la taglia non blocca niente**: il CRM avvisa e propone il livello
  sopra.
- **Il centro amplia il piano da solo**: "Attiva" apre 14 giorni di prova, e si
  paga dal mese dopo.
- **Pagando un anno in anticipo**, due mesi sono gratis.

## Perché è fatto così

- **Gli ambulatori, non le agende.** Contare le agende vuol dire contare i medici,
  come fanno i concorrenti: un poliambulatorio con venti specialisti a giornata
  pagherebbe per venti. Il prezzo che sale a ogni operatore in più è la lamentela
  più comune ([ricerca](../../verticali/clinica/ricerca-design.md#12-di-cosa-si-lamentano-i-clienti)).
  Le stanze sono un numero stabile, e il CRM le conosce dall'agenda.
- **La clinica dentro.** L'agenzia lavora soprattutto con le cliniche: un piano
  solo, senza un modulo clinico da aggiungere, si spiega in una riga.
- **La fatturazione fuori.** Molti centri fatturano con il commercialista: chi la
  prende paga 64, 124, 228 o 378 €, chi no 49, 99, 189 o 319 €.
- **I costi vivi sono bassi.** Un credito SdI costa 0,05 €, quindi i crediti
  inclusi costano 1–10 € al mese. WhatsApp non si rivende. Il server costa circa
  4 € al mese per sito ([doc 25](../../crm/25-costo-hosting.md)); con backup
  e dati clinici si contano 10 €. Il costo vero è l'assistenza e l'avvio.
- **Prezzi pubblici.** Doctolib, MioDottore, GipoNext e AlfaDocs lavorano su
  preventivo: un listino chiaro è già un vantaggio.

### Cosa costano le alternative

| Prodotto | Prezzo al mese | Nota |
|---|---|---|
| Doctolib | da 139 € | su preventivo, SMS a parte |
| MioDottore | circa 69 €, stimati | su preventivo; gestionale e telefonia a parte |
| AlfaDocs | da 109 € con 3 accessi | con i moduli si arriva a 1.500–2.000 € l'anno |
| Gestionali per una sola professione | 30–80 € | FisioDesk 0–44 €, OsteoEasy circa 31 €, Nutrium 28–50 €, MètaDieta 79 € |
| Poliambulatori | 100–300 € per 5–10 specialisti | oltre 500 € per le strutture grandi |
| GoHighLevel | 97–497 $ | solo CRM e marketing: niente cartella, niente Sistema TS |

Un centro che oggi usa MioDottore o Doctolib, più un gestionale, più uno
strumento per WhatsApp, spende facilmente 250–450 € al mese.

## Nel CRM

✅ **Allineato (01/10/2026).** Il piano nel CRM (`CRM Plan`, la pagina
Funzionalità:
[doc 30](../../crm/30-ruoli-e-permessi.md#il-piano-del-centro-la-seconda-chiave),
[doc 36](../../crm/36-funzionalita.md)) conta come questo listino:

1. **La taglia conta gli ambulatori**: le sale attive dell'agenda (Agenda › Sale e
   attrezzature, di tipo sala), non più le agende del mese. Superarla non blocca
   niente: la pagina lo dice e l'agenzia propone il livello sopra.
2. **La fatturazione è un extra del piano** (`fatturazione`), con il Sistema TS
   dentro. È accesa dove il piano non dice niente, perché ogni sito fatturava
   prima dei piani: un centro che non la prende ha la riga spenta. I crediti SdI
   inclusi (240, 500, 1.200, 2.400 l'anno) si contano sull'anno: uno a fattura
   inviata o ricevuta, tre a una fattura alla PA, niente per una scartata o mai
   partita; la pagina avvisa all'80%.
3. **La firma avanzata è un extra** (`firma`), spenta finché il piano non la
   comprende: senza, niente di nuovo parte verso il fornitore, e quello che era
   partito torna firmato o rifiutato.
4. **Nei consumi** crediti SdI e firme avanzate dell'anno (2.000 firme l'anno con
   la firma avanzata). WhatsApp no, perché lo fattura Meta al centro; chiamate e
   SMS nemmeno (dal 03/10/2026): li fattura Twilio a chi ha l'account, e la spesa
   del mese per tipo sta nella pagina di Twilio, per chi paga (il responsabile del
   centro sul suo account, l'agenzia sul suo).

I numeri stanno in `crm/fcrm/doctype/crm_plan/crm_plan.py` (`AMBULATORI`,
`CREDITI_SDI`, `FIRME_INCLUSE`): cambiano con il listino.

## Da decidere

1. Le soglie degli ambulatori (1, 2, 5, 10): quanti ambulatori e quanti
   specialisti hanno di solito i centri dell'agenzia.
2. Chi non è una clinica (centri estetici, palestre): il piano senza la parte
   clinica e l'Area clienti da sola, e i loro prezzi
   ([i tre strati](../../verticali/clinica/design.md#tre-strati-crm-fatturazione-clinica)).

## Fonti

- [Appuntoo, confronto prezzi 2026](https://appuntoo.com/blog/confronto-prezzi-gestionali/)
  (è un concorrente, dati del 14/07/2026)
- [MioDottore, prezzi per i centri](https://pro.miodottore.it/prezzi-centri-medici)
  (solo su richiesta)
- [Ambulatorio Facile](https://www.ambulatoriofacile.it/blog/gestionale-poliambulatorio)
- [GoHighLevel, piani 2026](https://www.ghlexperts.com/gohighlevel-plans-pricing)
- [Namirial eSignAnyWhere](https://www.namirial.it/dettagli/esignanywhere/)
- [SegretariaVirtualeMedico, offerta](https://www.segretariavirtualemedico.it/offerta/)
  (250 € fino a 100 appuntamenti, 490 € fino a 250)
- [Segreterie virtuali per medici](https://www.segreterievirtuali.it/assistente-virtuale/segretaria-virtuale-medici-di-base/)
  (da 39 €)
- [WebNovis](https://www.webnovis.com/blog/quanto-costa-campagna-facebook-ads.html)
  e [Giuseppe Basile](https://giuseppebasileweb.it/costi-pubblicita-facebook/) sul
  costo di gestione delle campagne Meta
