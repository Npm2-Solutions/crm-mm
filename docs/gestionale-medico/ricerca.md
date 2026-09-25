# Gestionale medico: ecosistema Frappe, obblighi, intermediari, concorrenti

Ricerca del 25/09/2026, a supporto della [proposta](./README.md).

Tag: **[V]** verificato sulla pagina citata (o nel codice del repo citato);
**[V-s]** solo dallo snippet del motore di ricerca, la pagina non è stata letta;
**[I]** inferenza o giudizio. Le regole fiscali vanno comunque fatte validare dal
commercialista del centro pilota prima di essere scritte nel codice.

---

## 1. L'ecosistema Frappe

### 1.1 Marley Health

- **Chi la mantiene.** È l'ex modulo Healthcare di ERPNext, uscito dal core nella
  v14. A luglio 2024 il repo "Frappe Health" è passato all'organizzazione
  **Earthians** con il nome Marley; sul forum un maintainer di Frappe ha scritto
  che Frappe non la mantiene, Earthians che il lavoro è finanziato dal programma
  di revenue sharing di Frappe [V]
  ([forum](https://discuss.frappe.io/t/introducing-new-health-app-marley/128757),
  [docs Frappe](https://docs.frappe.io/erpnext/frappe-healthcare)).
- **Viva e aggiornata.** Due linee di rilascio: v16.6.1 (22/09/2026) e v15.2.4
  (19/09/2026). La v16.6.0 ha aggiunto allergie, avvisi di interazione fra farmaci
  e una Fee Validity rifatta; la v16 (gennaio 2026) assicurazioni, portale del
  paziente, invii e disponibilità dei professionisti [V]
  ([rilasci](https://github.com/earthians/marley/releases),
  [annuncio v16](https://discuss.frappe.io/t/marley-healthcare-version-16-release/159139)).
  Sul marketplace di Frappe Cloud è gratuita, con più di 7.100 installazioni [V]
  ([marketplace](https://cloud.frappe.io/marketplace/apps/marley_health)).
- **Licenza GPL-3.0, ERPNext obbligatorio** (`required_apps = ["frappe/erpnext"]`)
  [V] ([repo](https://github.com/earthians/marley)). GPL-3 e AGPL-3 si possono
  combinare: singoli pezzi di codice si possono portare nel CRM [I].
- **Circa 130 DocType** nella `version-16`, figli compresi [V]:
  - paziente e agenda: Patient, Patient Appointment, Appointment Type, Healthcare
    Practitioner, Practitioner Schedule e Availability, Medical Department,
    Healthcare Service Unit, Fee Validity;
  - clinica: Patient Encounter, Vital Signs, Clinical Procedure, Lab Test,
    Observation, Diagnostic Report, Therapy Plan e Session, Service Request,
    Medication Request, Patient Allergy, Code System e Code Value;
  - ricoveri: Inpatient Record, Discharge Summary, Nursing Task;
  - assicurazioni: Insurance Payor, Contract, Claim, Patient Insurance Policy.
- **Interfaccia per lo più Desk** (la home è `/desk/healthcare`), più due app Vue
  separate: portale del paziente e `marley_frontend` (accettazione, chiosco,
  code, posti letto) [V] ([marley_frontend](https://github.com/earthians/marley_frontend)).
  Nessuna traduzione italiana: c'è solo il template `main.pot` [V].
- **Nessun uso trovato in Italia o in Europa.** Il thread del forum sulle strutture
  che usano ERPNext Healthcare elenca siti in India e Pakistan e una clinica a
  Manchester [V] ([forum](https://discuss.frappe.io/t/list-of-hospital-clinics-using-erpnext-healthcare/79721)).
  L'unico pacchetto regionale è l'integrazione indiana ABDM [V]. Una recensione
  lunga dice che i flussi reali vanno personalizzati e che la conformità resta a
  chi implementa [V]
  ([ClefinCode](https://clefincode.com/blog/global-digital-vibes/en/erpnext-healthcare-and-marley-comprehensive-analysis)).

### 1.2 Le altre app sanitarie per Frappe

- `Aakvatech-Limited/HMS_TZ`: MIT, sopra ERPNext e Marley, costruita attorno
  all'assicurazione sanitaria nazionale della Tanzania; attiva [V]
  ([repo](https://github.com/Aakvatech-Limited/HMS_TZ)).
- `medic_plus`: MIT, un solo sviluppatore, piattaforma multi-tenant su Marley per
  Frappe v16 [V] ([repo](https://github.com/dariakimberly4-netizen/medic_plus)).
- Abbandonate o superate: `ClinicAppointment` (2024), `ESS-LLP/erpnext-healthcare`
  (v11–v13), fork di frappe-health [V].
- **Nessuna app clinica mantenuta funziona senza ERPNext.** Marley è l'unico punto
  di partenza serio, e si porta dietro ERPNext [I].

### 1.3 ERPNext e la fattura elettronica italiana

- **Il core di ERPNext ha ancora `erpnext/regional/italy`** (in `version-15`,
  `version-16` e `develop`). Aggiunge campi italiani e **genera l'XML FatturaPA a
  ogni submit di una Sales Invoice di una società italiana**, ma non lo spedisce
  allo SDI. Ha solo i codici di natura generici N1–N7: N2, N3 e N6 generici sono
  scartati dallo SDI dal 2021, N4 "esenti" (quello delle prestazioni sanitarie) è
  ancora valido [V] ([erpnext](https://github.com/frappe/erpnext)).
  Se un cliente installa ERPNext, quell'XML automatico va spento per le fatture ai
  pazienti [I].
- **L'app `frappe/erpnext_italy` è ferma** al febbraio 2022 e a settembre 2026 non
  si installa pulita sulla v16 [V]
  ([repo](https://github.com/frappe/erpnext_italy), [issue](https://github.com/frappe/erpnext_italy/issues/4)).
- **`Solede-SA/italian_invoice`** è la più completa e attiva: AGPL-3.0, branch
  `version-15` e `version-16`, ultimo commit 7/09/2026. XML, validazione,
  transazioni SDI, fatture passive, registri IVA, split payment; invio tramite
  provider intercambiabili (manuale, OpenAPI.it o uno proprio) [V]
  ([repo](https://github.com/Solede-SA/italian_invoice),
  [connettore OpenAPI.it](https://github.com/Solede-SA/openapi)). È pensata per
  ERPNext [I]: da noi vale come codice da cui prendere, non come app da installare.
- Altre: `frappe-fab-italy-edi` (AGPL, 3 commit ad aprile 2026, dipende da
  `erpnext_italy`), `erpnext_fattura_elettronica` (ferma dal 2019), `eu_einvoice`
  di ALYF (solo formati tedeschi ed europei, niente FatturaPA) [V].
- **Specifiche in vigore:** versione 1.9.1, utilizzabile dal 15/05/2026, schema
  XML 1.2.3 [V]
  ([Agenzia delle Entrate](https://www.agenziaentrate.gov.it/portale/specifiche-tecniche-versione-1.9.1-%C2%A0-utilizzabili-dal-15-maggio-2026-)).

### 1.4 Comportamenti di Frappe verificati sul sorgente (branch `version-16`)

- **ERPNext v14 ha estratto i verticali in app proprie**: Healthcare, Hospitality,
  Non-Profit, Education, Agriculture, HR e Payroll, più alcune localizzazioni. Chi
  li usava ha installato l'app nuova sul bench e ha ritrovato i dati [V]
  ([guida alla migrazione v14](https://github.com/frappe/erpnext/wiki/Migration-Guide-to-ERPNext-version-14),
  [note di rilascio v14](https://erpnext.com/version-14/release-notes)).
- **Il View Log lo scrive solo il form del Desk.** `frappe.desk.form.load.getdoc`
  chiama `doc.add_viewed()` [V]; `frappe.client.get`, che è quello che usa
  `createDocumentResource` di frappe-ui e quindi la SPA del CRM, non lo chiama [V].
  `add_viewed()` scrive solo se il DocType ha `track_views` (o con `force=True`) [V]
  ([load.py](https://github.com/frappe/frappe/blob/version-16/frappe/desk/form/load.py),
  [client.py](https://github.com/frappe/frappe/blob/version-16/frappe/client.py),
  [document.py](https://github.com/frappe/frappe/blob/version-16/frappe/model/document.py)).
- **Il View Log non si cancella da solo.** Non è fra i `default_log_clearing_doctypes`
  di Frappe, ma ha un `clear_old_logs(days=180)` e quindi si può aggiungere a Log
  Settings [V]
  ([hooks.py](https://github.com/frappe/frappe/blob/version-16/frappe/hooks.py),
  [view_log.py](https://github.com/frappe/frappe/blob/version-16/frappe/core/doctype/view_log/view_log.py)).
  Per il dossier sanitario va tenuto almeno 24 mesi (§2.4) [I].

---

## 2. Gli obblighi di un centro medico privato

### 2.1 Fattura sanitaria al privato: niente SDI, per sempre

- Chi deve inviare i dati al Sistema TS **non può emettere la fattura elettronica
  via SDI** per le prestazioni sanitarie ai privati: fattura cartacea o PDF. Il
  divieto non è più una proroga di anno in anno: l'art. 2 del **D.Lgs. 81/2025**
  (GU del 12/06/2025) ha tolto il limite "2019…2025" dall'art. 10-bis del D.L.
  119/2018 [V] ([Gazzetta Ufficiale](https://www.gazzettaufficiale.it/eli/id/2025/06/12/25G00090/sg)).
  Vale anche per chi non è tenuto all'invio STS (art. 9-bis D.L. 135/2018) [V-s].
- Per l'Agenzia la fattura elettronica ai privati non si emette **nemmeno quando il
  paziente si oppone all'invio STS** [V]
  ([FAQ prestazioni sanitarie](https://www.agenziaentrate.gov.it/portale/Schede/Comunicazioni/Fatture+e+corrispettivi/FAQ+fe/Risposte+alle+domande+piu+frequenti+categoria/Prestazioni+sanitarie/)).
- Verso chi ha partita IVA (aziende, assicurazioni, fondi) la fattura elettronica
  via SDI è obbligatoria, **senza dati sanitari non necessari** [V] (stessa FAQ).

### 2.2 Sistema Tessera Sanitaria

- **Chi invia** [V]
  ([FAQ Sistema TS](https://sistemats1.sanita.finanze.it/portale/it/carattere-generale-faq1)):
  - dal 2015 strutture accreditate, medici e odontoiatri;
  - dal 2016 strutture autorizzate non accreditate, psicologi, infermieri,
    ostetriche, tecnici di radiologia, ottici e altri;
  - dal 2019 biologi e le nuove professioni sanitarie.

  In un poliambulatorio invia il centro, per le fatture che emette ai pazienti; i
  medici che fatturano al centro no [I].
- **Quando.** La cadenza mensile è stata rinviata più volte e non è mai partita. Le
  spese 2024 si sono inviate due volte l'anno; **dalle spese 2025 l'invio è
  annuale** (art. 5 D.Lgs. 81/2025 e decreto del 29/10/2025) [V]
  ([normativa Sistema TS](https://sistemats1.sanita.finanze.it/portale/it/web/guest/spese-sanitarie-normativa)).
  Si può inviare anche progressivamente durante l'anno [V-s].
- **Scadenze** [V]
  ([calendario](https://www.fiscoetasse.com/rassegna-stampa/31096-invio-dati-spese-sistema-TS-tessera-sanitaria-calendario-scadenze.html)):
  - spese 2025: entro il 2/02/2026;
  - spese 2026: entro l'1/02/2027, correzioni entro l'8/02/2027, opposizione
    online dei pazienti dal 9/02 all'8/03/2027.

  Ogni documento conta nell'anno in cui è stato **pagato** [V].
- **Sanzioni:** 100 € per documento, fino a 50.000 € l'anno, ridotte se si corregge
  entro 60 giorni [V] ([Fiscomania](https://fiscomania.com/comunicazione-spese-sanitarie-sts/)).
- **Come si invia** [V]
  ([specifiche](https://sistemats1.sanita.finanze.it/portale/it/spese-sanitarie/documenti-e-specifiche-tecniche-strumenti-per-lo-sviluppo)):
  - canali: portale web, web service SOAP sincrono (un documento per chiamata)
    oppure asincrono (uno zip fino a 5 MB);
  - credenziali o CNS; l'invio si può delegare a terzi;
  - il PIN di chi invia e il codice fiscale del paziente vanno cifrati con il
    certificato del Sistema TS;
  - campi che contano: tipo documento (F fattura, D documento), `flagOpposizione`,
    `pagamentoTracciato`, `tipoSpesa` (SR, SP, IC, AA…), aliquota o natura (N4),
    operazione (inserimento, variazione, rimborso, cancellazione).

### 2.3 IVA, bollo, pagamenti tracciabili

- **L'esenzione dell'art. 10 n. 18 DPR 633/72** copre solo diagnosi, cura e
  riabilitazione con finalità terapeutica. Le prestazioni medico-legali e quelle
  puramente estetiche sono **al 22%** [V-s]
  ([Fiscomania](https://fiscomania.com/prestazioni-sanitarie-dei-medici-iva/)).
  Una stessa fattura può quindi avere righe esenti e righe imponibili [I].
- **Bollo da 2 €** sulle fatture esenti sopra 77,47 € [V]
  ([Agenzia, risposta 129/2024](https://www.agenziaentrate.gov.it/portale/documents/20143/6193302/Risposta+n.+129_2024.pdf/8bcec98d-1b64-d4d8-1dd8-2d4ee1e9f786)).
  Il PDF mandato per email vale come fattura cartacea: marca fisica o bollo
  virtuale autorizzato (art. 15 DPR 642/72) [V-s].
- **Pagamento tracciabile per la detrazione del 19%** dal 2020, tranne farmaci,
  dispositivi medici e prestazioni di strutture pubbliche o accreditate. La prova
  è la ricevuta del POS o della banca, oppure il metodo di pagamento scritto in
  fattura; il flag `pagamentoTracciato` verso il Sistema TS è obbligatorio dal
  2020 [V]
  ([AteneoWeb](https://www.ateneoweb.com/approfondimenti/spese-sanitarie-e-tracciabilita-nella-dichiarazione-dei-redditi/)).

### 2.4 Privacy e dati sanitari

- **Per curare non serve il consenso** (art. 9(2)(h) GDPR). Serve invece per il
  dossier sanitario condiviso nella struttura, per i referti online, per le app e
  per il marketing. Il registro dei trattamenti serve sempre; il DPO serve a chi
  tratta dati sanitari su larga scala [V]
  ([Garante, provv. 55 del 7/3/2019](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/9091942)).
- **Dossier sanitario** (Linee guida del Garante, 4/6/2015) [V]
  ([docweb 4084632](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/4084632)):
  - ogni accesso, anche la sola consultazione, registrato in log **conservati almeno
    24 mesi**, con avvisi per gli accessi anomali;
  - accesso solo al personale coinvolto nella cura;
  - il paziente può sapere chi ha consultato il suo dossier;
  - il paziente può **oscurare** singoli episodi, senza che si veda che l'ha fatto;
  - dati sanitari separati dagli altri dati personali, con criteri di cifratura.

  Le linee guida chiedevano di notificare le violazioni entro 48 ore; oggi vale il
  GDPR, art. 33 [I].
- **Referti online** (Linee guida 2009): servizio su richiesta del paziente, che può
  escludere singoli esami, con consegna protetta [V-s]
  ([docweb 1679033](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/1679033)).
- **Consenso informato** (L. 219/2017, art. 1 c. 4): scritto o videoregistrato,
  inserito nella cartella clinica e nel Fascicolo sanitario [V-s]
  ([testo](https://www.medicoeleggi.com/argomenti000/italia2018/410019-1.htm)).
- **Conservazione.** Le cartelle dei ricoveri si tengono per sempre, le immagini
  diagnostiche almeno 10 anni; per le cartelle ambulatoriali private non c'è una
  regola nazionale e il periodo lo fissa il titolare [V]
  ([CGM](https://www.cgm.com/ita_it/magazine/articles/dati-sanitari-per-quanto-tempo-e-come-devono-essere-conservati.html)).
- **Copia della cartella** (legge Gelli, art. 4): entro 7 giorni dalla richiesta,
  le integrazioni entro 30 [V-s]
  ([testo](https://www.brocardi.it/resposabilita-professionale-personale-sanitario/art4.html)).

### 2.5 Firma dei consensi e dei referti

- **Firma elettronica avanzata (anche grafometrica)**, DPCM 22/02/2013 art. 57:
  identificare chi firma, raccogliere la sua accettazione scritta, conservare copia
  del documento d'identità e dell'accettazione per 20 anni, essere assicurati [V-s]
  ([Gazzetta Ufficiale](https://www.gazzettaufficiale.it/atto/serie_generale/caricaArticolo?art.versione=1&art.idGruppo=5&art.flagTipoArticolo=0&art.codiceRedazionale=13A04284&art.idArticolo=57&art.idSottoArticolo=1&art.idSottoArticolo1=10&art.dataPubblicazioneGazzetta=2013-05-21&art.progressivo=0)).
  Il Garante (biometria, 2014) vieta l'archivio centrale dei dati biometrici e
  chiede un'alternativa non biometrica [V-s]
  ([docweb 3556992](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/3556992)).
- Va bene per i consensi. **I referti per il Fascicolo sanitario vogliono la firma
  qualificata PAdES** [V]
  ([accreditamento FSE](https://github.com/ministero-salute/it-fse-accreditamento)).

### 2.6 Dispositivo medico e Spazio europeo dei dati sanitari

- **MDCG 2019-11 rev.1 (giugno 2025):** i sistemi informativi per accettazione,
  agenda e fatturazione e le cartelle elettroniche che sostituiscono la carta
  **non** sono dispositivi medici. Lo sono i moduli che suggeriscono dosaggi o
  segnalano interazioni fra farmaci [V]
  ([MDCG 2019-11](https://health.ec.europa.eu/document/download/b45335c5-1679-4c71-a91c-fc7a4d37f12b_en?filename=mdcg_2019_11_en.pdf)).
  Accendere gli avvisi di interazione di Marley probabilmente creerebbe un
  dispositivo medico [I].
- **EHDS, regolamento UE 2025/327.** I sistemi di cartella elettronica dovranno
  autocertificarsi, avere la marcatura CE e i componenti europei di
  interoperabilità e di log, con date scaglionate dal 26/03/2027 al 2029 e al 2031
  a seconda delle categorie di dati [V-s]
  ([Noerr](https://www.noerr.com/en/insights/the-european-health-data-space-is-on-its-way-an-overview)).
  Il modulo clinico ci ricadrà quando sarà venduto come prodotto: da verificare
  con un legale prima di allora [I].

### 2.7 Fascicolo sanitario elettronico (FSE 2.0)

- Dal D.L. 34/2020 il Fascicolo comprende anche le prestazioni fuori dal Servizio
  sanitario [V-s]
  ([Camera](https://temi.camera.it/leg19/post/il-nuovo-fascicolo-sanitario-elettronico.html)).
- Il DM del 30/12/2024 ha fissato la fase III al **31/03/2026**: documenti caricati
  entro 5 giorni dalla prestazione, anche per quelle private [V]
  ([Gazzetta Ufficiale](https://www.gazzettaufficiale.it/eli/id/2025/02/10/25A00808/sg)).
- **Per le strutture private non accreditate l'obbligo è contestato.** L'Ordine dei
  medici di Udine scrive che "non è ancora un obbligo sanzionabile"; FNOMCeO, ANDI e
  AIO lo considerano non ancora esigibile in pratica [V]
  ([OMCeO Udine](https://www.omceoudine.it/professione/altri-servizi/notizie-dall-ordine/1091-fascicolo-sanitario-elettronico-cosa-cambia-dal-31-marzo-2026.html),
  [DBMedica](https://www.dbmedica.it/news/fse-2-0-obblighi-e-scadenze-2026-per-le-strutture-private/)).
- La strada tecnica: documenti CDA2 di HL7 Italia, firma PAdES, il gateway del
  Ministero e l'accreditamento del software [V]
  ([ministero-salute/it-fse-accreditamento](https://github.com/ministero-salute/it-fse-accreditamento)).

---

## 3. I tubi regolati: SDI, Sistema TS, firma

| Tubo | Da soli | Con un intermediario |
|---|---|---|
| **Sistema TS** | Web service SOAP (sincrono o zip asincrono), credenziali del centro, cifratura di PIN e codice fiscale col certificato TS (§2.2) [V] | **A-Cube** (REST, autenticazione JWT, sandbox gratuita) e **sistema-ts-api.it** (ITALA S.r.l., abbonamento o a consumo) [V] ([A-Cube](https://www.acubeapi.com/en/solutions/sistema-tessera-sanitaria), [sistema-ts-api.it](https://www.sistema-ts-api.it/)) |
| **SDI** (solo fatture a fondi, assicurazioni, aziende) | Canale SDI diretto, da accreditare [I] | **Aruba** e **OpenAPI.it** hanno API REST [V-s] ([Aruba](https://fatturazioneelettronica.aruba.it/apidoc/docs.html), [OpenAPI.it](https://console.openapi.com/apis/sdi/documentation)). Il provider OpenAPI.it di Solede (§1.3) è un modello da seguire [I] |
| **Firma dei consensi** | Firma semplice (tratto su tablet con traccia e hash): nessun requisito formale, valore probatorio più debole [I] | Firma avanzata o grafometrica: i requisiti del DPCM 2013 (§2.5) li porta il fornitore [I] |
| **Firma dei referti** | Firma autografa sul PDF stampato [I] | Firma qualificata PAdES, necessaria per il Fascicolo (§2.5) [V] |

- Per Aruba, A-Cube e Fatture in Cloud non è stato trovato nessun connettore Frappe
  [I].
- **Non coperti da questa ricerca:** i fornitori di firma avanzata e qualificata e
  la conservazione a norma delle fatture. Vanno scelti prima della fase 2.

---

## 4. I gestionali concorrenti

| Gestionale | Cosa offre | Prezzo |
|---|---|---|
| **GipoNext** (Docplanner, cioè MioDottore) | Agenda e prenotazione online, referti anche online, Fascicolo, documenti e consensi, Sistema TS, archiviazione, convenzioni SSN, medicina del lavoro, integrazioni con radiologia e laboratorio [V] | Su preventivo [V] |
| **AlfaDocs** | Agenda multi-sede, Fascicolo 2.0, Sistema TS e SDI, pagamenti automatici, WhatsApp, note con l'IA [V] | Piani Light, Smart ed Elite, su preventivo [V] |
| **DBMedica** | Il catalogo più completo. Base: agenda, listini, cartella e referti con Fascicolo, fatture e Sistema TS, indicatori. Moduli: portale del paziente, promemoria, firma su tablet e consensi, portali di prenotazione, compensi dei medici, preventivi e acconti, pacchetti, convenzioni con assicurazioni e fondi, magazzino, code in accettazione, multi-sede e ruoli, PACS, API, flussi SSN [V] | Per numero di utenti, su preventivo [V] |
| **MEG** (Timeo) | Compensi dei medici (a ore, fissi o a percentuale), turni, convenzioni con i fondi (Previmedical, UniSalute, MetaSalute), contabilità, marketing, multi-sede, televisita [V] | — |
| **CGM XMEDICAL** | Agenda, cartella, firma elettronica, prenotazione CLICKDOC, assistente IA, contabilità, immagini, business intelligence, telemedicina, Fascicolo 2.0 [V] | — |
| **Klinika** (Onit Sanità) | CUP, accettazione e dimissione, cartella, magazzino, medicina del lavoro e dello sport [V] | — |
| **Doctolib** | Un'offerta per i centri medici italiani [V] | — |

Fonti: [GipoNext](https://gipo.it/a-chi-ci-rivolgiamo/giponext-per/poliambulatorio-medico),
[AlfaDocs](https://www.alfadocs.com/it/software-poliambulatori),
[DBMedica](https://www.dbmedica.it/),
[MEG](https://www.gestionalemedico.it/software-poliambulatorio-medico/),
[CGM](https://www.softwaregestionalemedico.it/),
[Klinika](http://klinikasoftware.it/),
[Doctolib](https://info.doctolib.it/centri-medici/).

**Prezzi.** Quasi tutti su preventivo. Numeri pubblicati o stimati, da prendere
come ordini di grandezza: ArzaMed da 25 € per utente al mese [V]
([Capterra](https://www.capterra.com/p/217860/ArzaMed/)); 100–300 € al mese per 5–10
specialisti e oltre 500 € per le strutture grandi, secondo un fornitore [V]
([Ambulatorio Facile](https://www.ambulatoriofacile.it/blog/gestionale-poliambulatorio));
Doctolib da 139 € e AlfaDocs da 109 € al mese, secondo un concorrente [V]
([Appuntoo](https://appuntoo.com/blog/confronto-prezzi-gestionali/)).

### La lista di un gestionale "completo", e la fase che la copre

| Area | Cosa serve | Fase |
|---|---|---|
| Front office | Agenda multi-sede e multi-specialista con stanze e attrezzature, prenotazione online sincronizzata con i portali, promemoria e richiami | **c'è già** |
| Front office | Code in accettazione | 1 |
| Paziente | Codice fiscale letto dal codice a barre della tessera sanitaria, registro dei consensi (cura, dossier, referti online, marketing) | 0 |
| Cassa | Listini per convenzione, preventivi e acconti, pacchetti; fattura PDF con natura N4 e bollo; SDI solo verso aziende e fondi; Sistema TS con opposizione e tracciabilità; POS e cassa | 1 e 3 (i preventivi sono i deal) |
| Clinica | Modelli per specialità e referti, firma avanzata per i consensi e qualificata per i referti, referti online, portale del paziente, log degli accessi per 24 mesi | 2 e 4 |
| Clinica | Fascicolo in CDA2, integrazione con PACS e laboratori | dopo, se e quando serve |
| Fondi e assicurazioni | Convenzioni, fatturazione diretta, pratiche | 3 |
| Medici | Compensi, anche con ritenuta d'acconto | 3 |
| Magazzino | Consumabili | 4 |
| Amministrazione | Indicatori, export per il commercialista, conservazione a norma, ruoli e permessi | 0, 1, 3 (gli indicatori nella dashboard che c'è già) |
