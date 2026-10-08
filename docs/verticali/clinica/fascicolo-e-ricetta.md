# Fascicolo sanitario e ricetta dematerializzata: per uno sviluppo futuro

**Stato:** 📌 da decidere, nessun codice scritto (08/10/2026). Si parte solo dopo
un parere legale aggiornato e l'accreditamento di NPM2 presso il Ministero.

Il Fascicolo sanitario elettronico (FSE 2.0) e la ricetta dematerializzata non si
costruiscono «al buio»: passano da enti esterni che accreditano il software e il
centro. Questo documento raccoglie quello che sappiamo, quello che DottorCloud ha
già, cosa va deciso e come si farà il lavoro quando arriverà il via. Le fonti sono
in [ricerca §2.5 e §2.7](./ricerca.md#27-fascicolo-sanitario-elettronico-fse-20);
la regola generale è la [decisione 4](./README.md#decisione-4--i-tubi-regolati-si-comprano):
il gestionale produce il documento giusto, un intermediario (o il gateway) lo
consegna e restituisce l'esito.

Legenda come in [ricerca.md](./ricerca.md): [V] verificato sulla fonte, [I]
inferito o da verificare.

## Quello che sappiamo

- **Il Fascicolo comprende anche le prestazioni private** dal D.L. 34/2020 [V].
- **Fase III dal 31/03/2026** (DM 30/12/2024): documenti caricati entro 5 giorni
  dalla prestazione, anche privata [V].
- **Per le strutture private non accreditate l'obbligo è contestato:** l'Ordine dei
  medici di Udine scrive che non è ancora sanzionabile; FNOMCeO, ANDI e AIO lo
  considerano non esigibile in pratica [V]. Le scadenze sono state spostate più
  volte: vanno ricontrollate quando si decide [I].
- **La strada tecnica:** documenti HL7 Italia CDA2 con il PDF incorporato, firma
  qualificata PAdES, invio al gateway del Ministero (Gateway FSE 2.0), software
  accreditato con i test di conformità per ogni tipo di documento [V]
  ([ministero-salute/it-fse-accreditamento](https://github.com/ministero-salute/it-fse-accreditamento)).
- **Il consenso all'alimentazione** del Fascicolo non serve più dal D.L. 34/2020;
  resta quello alla consultazione e il diritto del paziente di oscurare un
  documento [I, da verificare col legale].
- **Ricetta dematerializzata:** per il Servizio sanitario passa dal Sistema TS
  (SAC). Per le prescrizioni private («ricetta bianca» elettronica) le norme
  annunciate hanno avuto date spostate [I, da verificare]. È un'integrazione
  diversa dal Fascicolo, con il Sistema TS, e oggi fuori dal perimetro (solo
  privati: [domanda 2](./README.md#le-domande-da-chiudere-prima)).
- **Più avanti, EHDS** (regolamento UE 2025/327): formati comuni e marcatura CE
  delle cartelle elettroniche, dal 2027 al 2031 ([ricerca §2.6](./ricerca.md#26-dispositivo-medico-e-spazio-europeo-dei-dati-sanitari)).
  Il lavoro sul CDA2 ci torna utile.

## Quello che DottorCloud ha già

| Pezzo | Dove | Cosa serve ancora per il Fascicolo |
|---|---|---|
| Il referto di una visita firmata, PDF/A, fatto una volta, con SHA-256 | `crm/clinica/referto.py` | Incorporarlo in un CDA2 e firmarlo con la firma qualificata del professionista: oggi è sigillato con il sigillo PAdES del centro (`crm/moduli/sigillo.py`) |
| I documenti clinici archiviati (referti esterni, esami, immagini, ricette) | `crm/clinica/documenti.py` | Decidere quali tipi vanno al Fascicolo (solo i nostri referti, all'inizio) |
| I codici della struttura e le credenziali del Sistema TS | `crm/tessera_sanitaria` | Capire se bastano per l'autenticazione verso il gateway o servono certificati propri |
| Oscuramento di un episodio, dossier, registro degli accessi | `crm/clinica/dossier.py`, `cartella.py` | Portare l'oscuramento fino al documento inviato (metadato al momento dell'invio) |
| Consensi registrati, per tipo | `crm/moduli/consensi.py` | Un tipo di consenso del Fascicolo, se il legale lo chiede |
| Codice fiscale del paziente | `CRM Billing Profile` | Obbligatorio per l'invio: un referto senza codice fiscale resta fuori, detto |

## Cosa va deciso, e da chi

1. **Parere legale aggiornato** (NPM2): obbligo per i privati non accreditati, data,
   sanzioni; consenso e oscuramento; ricetta bianca elettronica sì o no.
2. **Accreditamento di DottorCloud** (NPM2): registrazione sul portale di
   accreditamento del Ministero, test di conformità per il «referto di specialistica
   ambulatoriale» come primo tipo, certificati.
3. **Diretti o con un intermediario** (NPM2): passare dal gateway con il nostro
   accreditamento, oppure un intermediario accreditato come per l'SdI con Itala.
   La decisione 4 dice intermediario, se ce n'è uno con costi sensati.
4. **Firma qualificata dei professionisti:** con quale fornitore (remota, a
   consumo), chi la paga, come si lega a `crm/moduli/firme.py`.
5. **Ogni centro:** registrazione presso Regione o ASL, codici della struttura,
   come si autenticano i suoi professionisti.
6. **Privacy:** DPIA, informativa e nomina a responsabile aggiornate
   (`docs/marchi/dottorcloud/`).

## Come si farà il lavoro (quando arriva il via)

1. **Regole pure** (`crm/clinica/fse_regole.py`, testate con `unittest`): il CDA2
   del referto di specialistica dai dati della visita firmata, i metadati
   (tipo, struttura, professionista, paziente, oscuramento), cosa manca per
   inviare, in parole. Casi presi dagli esempi ufficiali del Ministero.
2. **La firma qualificata** del professionista al momento della firma della visita,
   con un fornitore registrato come gli altri (`firme.registra_fornitore`).
3. **L'invio** (`crm/clinica/fse.py`): un adattatore con un finto gateway nei test
   (come `stripe_finto.py`, `twilio_finto.py`), l'invio in un job dopo la firma,
   ogni esito tenuto in un registro prima di essere applicato, ritentato, mai per
   la demo (`crm/demo/guardie.py`), mai una visita di prova; l'oscuramento e la
   cancellazione mandati anch'essi.
4. **Le schermate:** sulla visita «Inviato al Fascicolo il…» o perché no; nelle
   Impostazioni > Clinica una pagina «Fascicolo sanitario», spenta per partire,
   accesa solo con tutto in ordine (come i pagamenti online).
5. **La ricetta dematerializzata**, se il legale la chiede, come progetto a parte sul
   Sistema TS.

## Fuori, per ora

Flussi regionali, CUP, accreditamento con il Servizio sanitario, PACS e laboratori
(vedi la lista del gestionale «completo» in [ricerca.md](./ricerca.md#la-lista-di-un-gestionale-completo-e-la-fase-che-la-copre)).
