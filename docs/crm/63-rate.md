# 63 — Preventivi pagati a rate

Un piano di cure del dentista da 4.000 € non si paga in una volta: i centri italiani
offrono il **pagamento rateale** direttamente, senza una finanziaria in mezzo — un
acconto e N rate mensili, senza interessi né spese. DottorCloud lo scrive sul
preventivo, lo stampa nel PDF, lo fa firmare con il resto e poi lo segue: le fatture
delle rate, quelle pagate, la prossima, quelle in ritardo.

Il codice: `crm/preventivi/rate_regole.py` (le regole senza sito, gli stessi casi del
browser in `crm/preventivi/tests/casi_rate.json`), `crm/preventivi/rate.py` (il sito),
`frontend/src/utils/preventivi.js` (le stesse somme), `Quotes/QuoteDialog.vue`,
`Quotes/InstalmentsLine.vue`, `area/components/QuoteCard.vue`.

## Cosa fa

- **Nel preventivo in bozza**, sotto i totali, «Pagamento»: *In un'unica soluzione*
  (com'era) o *A rate*: acconto (un importo o una percentuale del totale, anche 0),
  da 2 a 36 rate, ogni mese o ogni due mesi, il giorno della prima. Sotto, il piano in
  una frase («Acconto di 800,00 € all'accettazione · 10 rate da 320,00 € · dal 1
  novembre 2026 al 1 agosto 2027») o cosa non va. Le rate sono uguali al centesimo;
  i centesimi che avanzano vanno sull'ultima (100 € in tre: 33,33 · 33,33 · 33,34).
  Un giorno 31 in un mese più corto diventa l'ultimo del mese. Una bozza può lasciare
  il giorno della prima per dopo; proposta, lo vuole e non nel passato.
- **Il piano è del preventivo** (`CRM Quote Instalment`): rifatto a ogni salvataggio
  della bozza, poi congelato con le righe quando è proposto. È nel PDF («Piano dei
  pagamenti»: l'acconto all'accettazione, ogni rata con il suo giorno e l'importo,
  «Pagamento rateale direttamente al centro, senza interessi né spese») e quindi
  nell'impronta firmata; nell'area la persona lo legge prima di firmare.
- **Accettato**, l'acconto scade quel giorno. Come si fatturano le rate è copiato
  dalle impostazioni quando il preventivo è proposto (`instalments_invoiced`): una
  scelta cambiata dopo non tocca i preventivi già dati.
- **Seguirlo**: la scheda del preventivo mostra il piano, ogni riga con il suo stato
  (*Da pagare*, *Fatturata*, *Pagata*, *Annullata*), il numero della fattura che si
  apre nel dialogo della fattura, «scadeva il … · in ritardo» nel colore degli avvisi
  con il suo segno. Una riga sola dice come va: «Rate: 3 di 10 pagate · prossima 1
  novembre 2026, 250,00 € · 1 in ritardo, 250,00 €» — sulla scheda, nella scheda
  Preventivi della persona e nel suo Riepilogo (la riga dei preventivi).
- **Nell'area** la card del preventivo ha il suo piano (le prime righe da pagare,
  «Mostra tutte e 11»), la riga di come va e «Paga online» sulla rata fatturata e non
  pagata quando Stripe è collegato (doc 60: la stessa strada delle fatture).
- **Il sollecito** di una fattura di rata la nomina: «La fattura 2026/E/12 del 1
  novembre 2026, la rata 4 di 10 del tuo preventivo, di 320,00 €, risulta ancora da
  pagare.» (doc 47, `solleciti._la_rata`).
- **Il cruscotto**: «Rate da incassare» (categoria Fatturazione) — quanto valgono le
  rate non pagate che scadono nei prossimi 30 giorni o sono in ritardo, e quante in
  ritardo.

## Le due fatturazioni (Impostazioni > Trattative > Pipeline > Preventivi)

1. **Ogni rata alla scadenza** (predefinita). Ogni mattina (`rate.ogni_giorno`) la
   riga scaduta e non fatturata ha la sua fattura: una riga, l'importo della rata,
   «Rata 4 di 10 del preventivo «Piano di cura»», la scheda fiscale del servizio del
   preventivo che vale di più, il professionista di chi l'ha scritto. In bozza da
   controllare, o emessa subito se il centro lo vuole («Emettile subito»): una che il
   motore ferma resta in bozza e la riga dice perché. Una volta sola: la riga tiene la
   sua fattura; annullata o cancellata, torna da pagare e il giro dopo la rifà.
   Incassata (`incassi.segna`, la cassa, Stripe), la riga è pagata (`rate.allinea`,
   anche dagli eventi della fattura). **Gli appuntamenti** del preventivo sono pagati
   dalle rate: non compaiono più tra quelli da fatturare e «Fattura» da un
   appuntamento lo dice (`rate.pagati_a_rate`). È la scelta che segue la regola
   fiscale: il corrispettivo incassato prima della prestazione si fattura quando lo si
   incassa (art. 6 DPR 633/72), quindi ogni rata ha la sua fattura e la prestazione
   non ne ha un'altra. Al Sistema TS ogni fattura sanitaria va come sempre (il motore).
2. **Solo seguite**: il centro fattura da sé il lavoro man mano che lo fa (gli
   appuntamenti prendono le righe al prezzo concordato, come prima) e le rate sono
   solo un calendario: chi registra gli incassi (`fatture.incassi`) le segna pagate
   («Segna come pagata», «Di nuovo da pagare»). È la scelta di chi fa già le fatture
   di acconto con un altro programma.

Perché non una fattura di acconto a ogni incasso e poi la fattura della prestazione
che li scala: in sanità ogni fattura va al Sistema TS con il suo tipo di spesa, e due
documenti per la stessa spesa sono un doppio invio da evitare; la rata fatturata
quando si paga è la strada più semplice e corretta.

## La fine

- **Rifiutato**, tutte le rate sono annullate. **Chiuso** a metà, quelle non ancora
  fatturate («Preventivo chiuso: le 6 rate non ancora fatturate sono annullate»);
  quelle fatturate restano, con le loro fatture.
- **Una nuova versione accettata** chiude quella che sostituisce, se era in corso, e
  ne annulla le rate non fatturate: la nuova versione porta tutte le righe, le due
  insieme sarebbero il doppio.
- **Saldato in anticipo**: «Salda il resto, 2.560,00 €» fa una fattura sola di tutte
  le righe ancora da fatturare (si apre in bozza), o, se le rate sono solo seguite, le
  segna pagate oggi.

## La demo

Il dentista (`crm/clinica/demo/dentista.py`): il primo che ha detto sì al piano di cure
almeno 10 giorni fa paga a rate — il dentista scrive il piano di cura con il piano dei pagamenti
(un quinto all'accettazione, dieci rate al mese dal giorno dopo), la segreteria
lo registra accettato; le date tornano ai loro giorni come il resto della demo. La
parte della fatturazione (`crm/invoicing/demo.py` `_rate`) fattura acconto e rate
scadute nel loro giorno, pagate con carta: l'acconto e la prima, tre se è stato accettato da più di un mese. Il giro di ogni
giorno non tocca mai i preventivi della demo; dove il centro fattura già con la sua
azienda la demo non fa fatture, e le rate restano da pagare.

## Credito ai consumatori: perché non è un finanziamento

Il piano è del centro, **senza interessi, senza spese e senza un terzo**: non è un
finanziamento di una società come Compass o Agos, che resta fuori da DottorCloud
(un contratto di credito con il suo TAEG, i suoi obblighi informativi, una
finanziaria convenzionata).

Fino al 2025 il TUB escludeva dalla disciplina del credito ai consumatori i contratti
senza interessi né altri oneri (art. 122, c. 1, che recepiva la direttiva 2008/48/CE,
art. 2, par. 2, lett. f). Il **D.Lgs. 212/2025**, che recepisce la direttiva (UE)
2023/2225 (CCD2), in vigore per questa parte dal gennaio 2026, ha aggiunto la lett.
**i-bis**: è esclusa la dilazione offerta direttamente dal fornitore, senza terzi,
gratuita e senza interessi (salvo spese limitate per i ritardi), **entro 50 giorni**
dalla prestazione; il comma 1-ter dice che il fornitore, come attività accessoria,
può concludere solo dilazioni gratuite dei propri servizi. Un piano di 10 rate mensili
va oltre i 50 giorni: se ricada ancora nell'esclusione generale dei contratti senza
interessi né oneri o vada trattato come credito ai consumatori è una questione che le
fonti consultate non chiudono. Per questo DottorCloud non mette interessi, spese o
penali, non coinvolge terzi e non decide per il centro: chi offre piani lunghi lo
verifichi con il proprio consulente (testo vigente dell'art. 122 TUB e disposizioni
della Banca d'Italia).

Fonti: commenti al D.Lgs. 212/2025 su [Altalex](https://www.altalex.com/documents/2026/01/22/g-u-d-lgs-n-212-2025-cambia-tub-consumatori),
[eDotto](https://edotto.com/articolo/credito-ai-consumatori-la-riforma-introdotta-dal-decreto-di-recepimento),
[Diritto Bancario](https://www.dirittobancario.it/art/attuazione-ccd2-estensione-applicativa-della-disciplina-del-credito-al-consumo/);
il testo dell'art. 122 TUB su [Brocardi](https://www.brocardi.it/testo-unico-bancario/titolo-vi/capo-ii/art122.html);
la direttiva (UE) 2023/2225, art. 2, par. 2, lett. h (dilazione del fornitore entro 50
giorni), applicabile dal 20 novembre 2026. Ricerca del 8 ottobre 2026: le pagine sono
state lette nei risultati di ricerca, non nel testo ufficiale in Gazzetta.

## Lasciato fuori

- Il finanziamento di terzi (Compass, Agos e simili) e qualsiasi interesse o spesa.
- Le rate di importo diverso scelte a mano, frequenze diverse da uno o due mesi.
- Un piano cambiato dopo l'accettazione: si fa una nuova versione.
- Le fatture di acconto con lo storno nella fattura finale (vedi sopra).
- Un avviso alla persona prima di ogni scadenza: c'è il sollecito dopo, se il centro
  lo accende (doc 47).
