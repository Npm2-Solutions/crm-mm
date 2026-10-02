# 50 · Trattative e preventivi, due livelli collegati

**Stato:** fatto (02/10/2026). Nasce da una domanda: perché ci sono sia le
«offerte» sia i preventivi, e se conviene unirli.

## Il bisogno

- In DottorCloud c'erano le **Offerte** e i **Preventivi**, e non si capiva perché
  tutti e due.
- La domanda era se unirli, facendo diventare un'offerta un preventivo vero e
  proprio, o tenere due livelli.
- E dove stanno: nel CRM per tutti, o solo nel verticale medico.

## Com'era

- **«Offerte» non era un secondo documento**: era la traduzione ereditata di
  *Deals*, la pagina delle trattative della pipeline (una sola si chiamava già
  «Trattativa»). In italiano «offerta» vuol dire quasi «preventivo», da qui il
  doppione apparente.
- **I documenti veri sono i preventivi** (`crm/preventivi`,
  [«Il preventivo»](../gestionale-medico/design.md)):
  - righe di servizi dal listino, fasi, il PDF, accettato o rifiutato, le versioni;
  - accettato, le righe diventano appuntamenti e poi fatture;
  - con la clinica accesa, i piani di cura del dentista.
- **Erano già collegati**: un preventivo proposto apriva o spostava la trattativa
  nella pipeline «Preventivi», accettato la vinceva, rifiutato la perdeva con il
  motivo.
- **Il vero doppione era la griglia «Prodotti» della trattativa**: un catalogo suo
  (`CRM Product`), mentre i preventivi usano servizi e listini. Due cataloghi e due
  valori per una vendita sola, e il totale dei prodotti poteva sovrascrivere quello
  del preventivo.
- **Tre difetti trovati strada facendo**:
  - una trattativa vinta con un preventivo accettato valeva zero sulle dashboard: il
    valore andava nel valore atteso, e le dashboard sommano il valore della
    trattativa;
  - dalla pagina di una trattativa non si vedevano i suoi preventivi;
  - gli stati del preventivo avevano il genere sbagliato («Accettate»,
    «Rifiutata»), presi dalle traduzioni di altre cose.

## Come fanno gli altri

- **I CRM**: HubSpot, Salesforce, Pipedrive, Zoho, Odoo, Dynamics, Bitrix24 e
  GoHighLevel hanno tutti **due livelli**:
  - la trattativa (chi, a che punto, quanto vale, da dove arriva);
  - il preventivo, un documento per una persona, collegato alla trattativa.
  Nessuno ha un'«offerta» sopra il preventivo. Le «Offers» di GoHighLevel sono
  pacchetti di corsi venduti con le sue membership.
- **I gestionali dentistici e medici** (XDent, AlfaDocs, Dentaltrey, Dentrix,
  Pabau, Zenoti):
  - promozioni e pacchetti sono marketing, una cosa per tante persone;
  - il preventivo o piano di cura è per un paziente, dopo la visita;
  - si misurano la quota di preventivi accettati e quelli in attesa da richiamare,
    entro 48-72 ore e poi ogni settimana.
- **Le regole italiane**:
  - il preventivo scritto è dovuto dal professionista (L. 124/2017);
  - il comma 525 della L. 145/2018, riscritto nel 2023, vieta «offerte, sconti e
    promozioni» nelle comunicazioni sanitarie quando possono indurre a
    trattamenti inappropriati.

## Cosa cambia

- **Due livelli, chiari e collegati, nel CRM per tutti**: trattative e preventivi
  funzionano allo stesso modo per un centro estetico, una palestra e un dentista. La
  clinica aggiunge solo i denti sulle righe (già fatto).
- **«Offerte» diventa «Trattative»**:
  - il menu, le pagine, le impostazioni;
  - le due frasi che dicevano ancora «offerta» per una trattativa.
- **Il preventivo è figlio della trattativa**:
  - la trattativa ha la scheda **Preventivi**: i suoi preventivi, e un preventivo
    nuovo fatto lì è suo;
  - proposto, sposta la sua trattativa a «Preventivo consegnato»: niente seconda
    trattativa per una vendita sola;
  - il preventivo dice la sua trattativa («Trattativa: Preventivo consegnato») e ci
    porta con un clic;
  - una nuova versione resta sulla stessa trattativa finché è aperta.
- **Un preventivo sposta solo le trattative della pipeline «Preventivi»**:
  - la trattativa dei nuovi clienti segue la persona fino alla prima visita, e una
    pipeline fatta dal centro è il suo modo di lavorare: lì la scheda mostra i
    preventivi della persona, e il preventivo trova la sua trattativa quando si
    propone;
  - una trattativa chiusa non si riapre: dopo un «no», una nuova versione è una
    vendita nuova.
- **Accettato, la trattativa vinta vale il preventivo**: il valore che le dashboard
  sommano.
- **Via la griglia «Prodotti» dalla trattativa**:
  - il valore viene dai preventivi, con un catalogo solo, servizi e listini;
  - una patch la toglie dove nessuna trattativa ha prodotti; dove qualcuna ne ha,
    resta: niente di scritto dal centro sparisce;
  - i campi restano nel DocType: chi la vuole la rimette dalla disposizione dei
    campi;
  - `CRM Product` resta per la vetrina del sito e per ERPNext.
- **Le dashboard**, nella dashboard Vendite, sezione «Preventivi»:
  - **Preventivi proposti** nel periodo;
  - **Preventivi accettati**: dei preventivi che hanno avuto una risposta nel
    periodo, la quota accettata; un rifiutato seguito da una nuova versione non
    conta come «no», è la stessa conversazione;
  - **Preventivi in attesa**: quanto valgono adesso, nella valuta dei preventivi;
  - **Preventivi da richiamare**: quelli senza risposta, prima chi aspetta da più
    tempo; dopo tre giorni «Da richiamare», scaduto «Scaduto».
  Ognuno conta solo i preventivi che chi guarda può leggere: un piano di cura è un
  dato sanitario anche dentro un numero.
- **Gli stati del preventivo** al maschile, con un contesto loro («Accettato»,
  «Rifiutato»), anche sui pulsanti che registrano la risposta.

## Le «offerte» del marketing, se servono

Non fatte qui: se il marketing vuole delle offerte, sono **pacchetti del catalogo**,
servizi con un prezzo e una scadenza:

- si vendono direttamente (ci sono già i cicli di sedute e gli abbonamenti) o
  riempiono un preventivo;
- con la clinica accesa, solo pacchetti neutri e niente sconti, per il comma 525
  (da far vedere a un legale).

## Come è fatta

- `crm/preventivi/pipeline.py`:
  - `prende_preventivi()`: una trattativa della pipeline «Preventivi»;
  - `si_puo_spostare()`: e aperta;
  - `preventivo_chiuso()` scrive il valore della trattativa vinta.
- `crm/preventivi/api.py`:
  - `get_quotes(lead, deal)` e `save_quote(..., deal)` per la pagina della
    trattativa; il server dice se la trattativa prende i preventivi (`deal` nella
    risposta);
  - `copy_quote` tiene la trattativa aperta;
  - `deal_label` nel dettaglio: lo stadio della trattativa.
- `crm/dashboard/widgets/quotes.py`: i quattro widget, sulla regola di lettura dei
  preventivi (`crm.preventivi.api.condizione`); la caratteristica «quotes» in
  `crm/dashboard/features.py`; la sezione nella dashboard Vendite.
- Il frontend:
  - la scheda Preventivi in `pages/Deal.vue` e `MobileDeal.vue`;
  - `Activities.vue` passa la trattativa a `QuotesCard`;
  - `QuoteDialog.vue`: il pulsante della trattativa, gli stati con il contesto
    «Quote».
- `crm/install.py`: la disposizione dei campi della trattativa senza prodotti; patch
  `deals_take_their_value_from_quotes`.
- `crm/locale/it.po`: «Trattative», gli stati con `msgctxt "Quote"`, le frasi nuove.

## Verifiche

- `crm/preventivi/tests/test_preventivi.py`:
  - accettato, la trattativa vinta vale il preventivo;
  - dalla trattativa i suoi preventivi, uno nuovo è suo, e proposto sposta lei;
  - una trattativa dei nuovi clienti resta dov'è, e il preventivo va nella pipeline
    «Preventivi»;
  - la trattativa di un'altra persona no;
  - una trattativa chiusa non si riapre, una aperta tiene la nuova versione;
  - i numeri: proposti, accettati (il «no» ripensato non conta), in attesa, da
    richiamare dopo tre giorni;
  - chi non legge i preventivi non li conta;
  - la patch: via la griglia e i totali, il resto com'era.
- Nel browser, in italiano:
  - il menu «Trattative»;
  - la scheda Preventivi della trattativa, anche sul telefono;
  - il preventivo con la sua trattativa e i pulsanti «Rifiutato» / «Accettato»;
  - la scheda Dati senza prodotti;
  - la dashboard Vendite con la sezione Preventivi, in euro.
