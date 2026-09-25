# Gestionale medico: ecosistema Frappe, obblighi, intermediari, concorrenti

Ricerca del 25/09/2026, a supporto della [proposta](./README.md).

Tag: **[V]** verificato sulla pagina citata; **[V-s]** solo dallo snippet del motore
di ricerca, la pagina non è stata letta; **[I]** inferenza o giudizio. Le regole
fiscali vanno comunque fatte validare dal commercialista del centro pilota prima di
essere scritte nel codice.

---

## 1. L'ecosistema Frappe

_Ricerca in corso (25/09/2026): stato di Marley Health e della localizzazione italiana di ERPNext._

<!-- ecosistema -->

### Comportamenti di Frappe verificati sul sorgente (branch `version-16`)

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

- Chi deve inviare i dati al Sistema TS, e chi documenta prestazioni sanitarie a
  persone fisiche, **non può emettere la fattura elettronica via SDI** per quelle
  prestazioni: fattura cartacea o PDF [V-s].
- Il divieto non è più una proroga di anno in anno: il **D.Lgs. 81/2025** (GU del
  12/06/2025) ha modificato in modo strutturale l'art. 10-bis del D.L. 119/2018 [V-s]
  ([Fiscomania](https://fiscomania.com/prestazioni-sanitarie/),
  [AteneoWeb](https://www.ateneoweb.com/approfondimenti/prestazioni-sanitarie-e-fattura-elettronica-divieto-permanente-dal-2026/)).
- Verso fondi, assicurazioni e aziende (B2B) la fattura elettronica resta la regola
  [I, da validare col commercialista].

### 2.2 Sistema Tessera Sanitaria: obbligo annuale

- **Dalle spese del 2025 l'invio è annuale, entro il 31 gennaio dell'anno dopo**
  (art. 5 D.Lgs. 81/2025 e decreto del 29/10/2025). Per il 2025 la scadenza è
  slittata al 2 febbraio 2026 perché il 31 gennaio era sabato [V-s].
- **Si può inviare progressivamente durante l'anno** (invii parziali facoltativi)
  invece di accumulare tutto a gennaio [V-s]. Nel gestionale: un invio al mese,
  così gli scarti si scoprono subito e non a fine gennaio [I].
- Prima era semestrale (spese 2024) [V-s]. Le sanzioni per invio omesso o tardivo
  si contano per documento [V-s]
  ([Sistema TS, normativa](https://sistemats1.sanita.finanze.it/portale/it/web/guest/spese-sanitarie-normativa),
  [Fiscomania](https://fiscomania.com/comunicazione-spese-sanitarie-sts/),
  [DBMedica](https://www.dbmedica.it/news/sistema-ts-2026-addio-alle-scadenze-semestrali/),
  [ANDI](https://andi.it/invio-dati-al-sistema-tessera-sanitaria-entro-il-31-gennaio/)).

<!-- fisco -->

### 2.4 Privacy e dati sanitari

- **Per curare non serve il consenso.** Il professionista sanitario tenuto al
  segreto, da solo o dentro una struttura pubblica o privata, tratta i dati per
  diagnosi e cura senza chiedere il consenso (Garante, provvedimento n. 55 del
  7/3/2019) [V-s]. Serve invece per i trattamenti che non sono cura: dossier
  sanitario, referti online, app, marketing e fidelizzazione [V-s, elenco da
  rileggere sul provvedimento]
  ([Garante, docweb 9091942](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/9091942)).
- **Dossier sanitario** (Linee guida del Garante, 4/6/2015) [V-s]
  ([docweb 4084632](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/4084632)):
  - ogni accesso, anche la sola consultazione, tracciato in log **conservati almeno
    24 mesi**;
  - accesso solo al personale coinvolto nella cura;
  - il paziente può sapere chi ha consultato il suo dossier e può **oscurare**
    singoli eventi;
  - dati sulla salute separati dagli altri dati personali, con criteri di cifratura.
- Le violazioni si notificano secondo il GDPR (art. 33, entro 72 ore) [I].

<!-- privacy -->

---

## 3. I tubi regolati: SDI, Sistema TS, firma

_Ricerca in corso (25/09/2026): intermediari per SDI, Sistema TS e firma, con le loro API._

<!-- tubi -->

---

## 4. I gestionali concorrenti

_Ricerca in corso (25/09/2026): cosa offrono GipoNext, AlfaDocs, DBMedica, MEG e gli altri._

<!-- concorrenti -->
