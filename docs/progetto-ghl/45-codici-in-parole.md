# 45 · La fatturazione in parole: ogni codice col suo nome, e solo quelli che servono

**Stato:** fatto (02/10/2026). È la prima di tre parti: dopo vengono la
fatturazione sanitaria già impostata quando DottorCloud è acceso (46) e la
fattura fatta dentro DottorCloud, senza il Desk (47).

## Il bisogno

Per impostare la fatturazione bisognava conoscere i codici dell'Agenzia delle
Entrate e del Sistema TS. Le scelte erano codici: `RF01`, `N4`, `TC21`, `RT01`,
`MP08`, `TD04`, `SP`, `credenziali_studio`, `analogico_con_copia`. A volte una
descrizione sotto il campo li elencava tutti in fila («TK Ticket · FC Farmaco… · SR
Spesa prestazione sanitaria: intramoenia…»), a volte nemmeno quella. I nomi dei
campi erano quelli del tracciato: «Natura», «tipoSpesa», «flagTipoSpesa»,
«codiceRegione», «Causale pagamento», «Rate», «Type».

E le scelte erano tutte, anche per un centro medico: diciotto regimi fiscali (il
sale e i tabacchi, i fiammiferi, l'editoria), ventuno nature IVA (il reverse charge
dei rottami, dell'oro, dei telefonini), ventidue casse (avvocati, notai,
giornalisti), ventitré modalità di pagamento. Chi sceglie fra codici che non
capisce ne sceglie uno sbagliato, e lo scopre quando una fattura torna scartata.

Due descrizioni dei tipi di spesa erano anche sbagliate: `SR` diceva
«intramoenia» e `CT` «certificazione medica». Con quelle parole un centro sceglie
il codice sbagliato per ogni visita.

## Cosa cambia

- **Ogni codice ha un nome e una riga che dice quando si usa.** «Regime
  ordinario», «Regime forfettario», «Esente (art. 10)», «ENPAP: psicologi» con «Contributo
  del 2% sul compenso, esposto in fattura», «Contanti» con «Non tracciabile: sulla
  prestazione sanitaria il paziente perde la detrazione del 19%». La riga sotto il
  campo è quella della scelta fatta.
- **Con la clinica accesa si vedono solo le scelte di un centro medico**: tre
  regimi (ordinario, forfettario, minimi), tre nature IVA (esente art. 10, non
  soggetta per forfettario o minimi, anticipazioni art. 15), le casse della sanità
  (ENPAM, ENPAP, ENPAPI, ENPAB, ENPAV, ENPAF, INPS gestione separata), le modalità
  di pagamento che si usano davvero, i documenti che si emettono (fattura, nota di
  credito e di debito, acconto, parcella). Il resto non sparisce: un valore già
  scelto resta nel suo campo, col suo nome; solo non viene più proposto.
- **I tipi di spesa seguono chi emette.** Un fisioterapista, uno psicologo o un
  dietista che fattura a proprio nome ha un tipo di spesa solo, «Prestazioni del
  professionista sanitario», e la scheda del servizio offre quello. Un medico o un
  dentista ha i suoi; una struttura autorizzata i suoi.
- **I tipi di spesa hanno le parole della specifica del Sistema TS** (730 Spese
  Sanitarie, WS sincrono v1.3, Tabella 4): `SR` sono le visite e le prestazioni
  specialistiche, `CT` le cure termali.
- **I campi hanno nomi chiari**: «Perché non c'è IVA», «Tipo di spesa (Sistema
  TS)», «Caso particolare (Sistema TS)», «Come arrivano le fatture allo SdI», «Come
  arrivano le spese al Sistema TS», «Chi emette, per il Sistema TS», «Come si paga
  il bollo», «Causale della ritenuta (Modello 770)», «Codice regione», «Codice
  ASL», «Codice struttura (SSA)». Le descrizioni non elencano più codici.
- **La causale della ritenuta si sceglie da un elenco** (prestazione
  professionale, lavoro autonomo occasionale…) invece di scriverne la lettera.
- **La qualifica di un professionista si sceglie fra le professioni sanitarie**,
  con la clinica accesa: non fra avvocati, ingegneri e sviluppatori. La qualifica
  si legge col suo nome («Fisioterapista»), mai col codice.
- **Le sezioni che sono il contenuto della loro scheda sono aperte**: «Sistema di
  Interscambio» in Trasmissione, «Anagrafica sanitaria» in Sanitario. Restano
  chiuse quelle di contorno (albo, registro imprese).
- **Un campo di sola lettura mostra il nome della scelta** («Ancora sconosciuta»),
  non il codice (`sconosciuta`).
- **Nel Desk, il modulo della fattura** offre le stesse scelte con gli stessi nomi,
  per il profilo acceso, e mostra il canale, la tracciabilità del pagamento e gli
  stati come parole («Da inviare», non `da_inviare`).
- **Nei collegamenti** (la qualifica, ma anche una persona o una trattativa) la
  ricerca mostra il nome del record e non ripete sotto il suo codice.

Quello che si salva non cambia: sono ancora i codici che leggono lo SdI e il
Sistema TS.

## Come è fatta

- `crm/invoicing/engine/voci.py`: il vocabolario, Python puro. Ogni famiglia di
  codici (regimi, nature, documenti, pagamenti, casse, ritenute, causali, bollo,
  conservazione, canali…) è un elenco di `Voce(valore, etichetta, spiegazione,
  sanita)`, nell'ordine in cui si propone; `voci(famiglia, profilo, attuale,
  ammessi)` dà le scelte di un profilo, tenendo sempre i valori già salvati (uno,
  o quelli di tutte le righe di una tabella).
- `crm/tessera_sanitaria/engine/voci.py`: le famiglie del Sistema TS (tipi di
  spesa, casi particolari, chi emette, come si invia, la delega, l'operazione),
  registrate nel vocabolario della fatturazione quando il modulo si carica: la
  fatturazione non sa cos'è un tipo di spesa.
- `crm/verticali.py`: un verticale dice il suo profilo di fatturazione
  (`Verticale.fatturazione`); la clinica dice `sanitario`.
- `crm/invoicing/scelte.py`: quale campo parla quale famiglia (`CAMPI`), le regole
  che restringono una famiglia secondo il documento (`registra_regola`: il Sistema
  TS registra i tipi di spesa per la categoria di chi emette), il filtro delle
  qualifiche nel profilo sanitario, `adatta_campi()` per le schermate disegnate dal
  DocType (`crm.api.doc.get_fields` ora passa per gli adattatori registrati con
  `registra_adattatore`), `get_options()` per il modulo del Desk, `get_vocabulary()`
  per le righe degli elenchi.
- I DocType della fatturazione: nomi e descrizioni nuovi, `show_title_field_in_link`
  sulla qualifica.
- Il frontend: `utils/scelte.js` (la spiegazione della scelta fatta, il valore già
  salvato, il nome di un codice, il nome in sola lettura), `Field.vue`,
  `settingsTabs.js` (una scheda non si apre su una sezione chiusa),
  `Controls/Link.vue` (il titolo dei record che lo mostrano nei collegamenti, anche
  per un valore che la ricerca non ha portato; `link_title_doctypes` nel boot),
  `composables/vocabolarioFatturazione.js`, le righe dei servizi e dei
  professionisti.
- `crm/invoicing/doctype/crm_invoice/crm_invoice.js`: le scelte in parole e gli
  stati nel modulo del Desk.
- `crm/locale/it.po`: ogni nome e ogni spiegazione in italiano.

Un nuovo campo con un codice va in `scelte.CAMPI` con la sua famiglia, e un nuovo
valore ammesso da un DocType va nel vocabolario con il suo nome: i test lo
chiedono.

## Verifiche

- `crm/invoicing/tests/test_voci.py` e `crm/tessera_sanitaria/tests/test_voci.py`
  (Python puro): ogni valore che i DocType ammettono ha un nome nella sua famiglia,
  e ogni nome e spiegazione è tradotto; i nomi non sono il codice; le scelte del
  profilo sanitario, valore per valore; le descrizioni dei tipi di spesa sono
  quelle della specifica; un fisioterapista ha un solo tipo di spesa.
- `crm/invoicing/tests/test_scelte.py` e
  `crm/tessera_sanitaria/tests/test_scelte_ts.py` (sul sito): le coppie campo →
  famiglia coincidono con quelle del test puro; le schermate ricevono nomi e
  spiegazioni, il profilo sanitario toglie il resto, la causale diventa un elenco,
  le qualifiche di un centro medico sono sanitarie, gli altri DocType non
  cambiano; il modulo della fattura tiene i valori già scelti, anche quelli delle
  righe.
- Tutte le suite della fatturazione e del Sistema TS, e quelle che toccano le
  fatture (clienti, pazienti, cicli, abbonamenti, accesso alle fatture).
- Nel browser, in italiano: l'azienda scheda per scheda, un servizio sanitario e
  uno no, un professionista con la sua qualifica e la ricerca delle qualifiche, una
  qualifica, la fattura nel Desk.
