# 46 · La fatturazione di un centro medico, già impostata

**Stato:** fatto (02/10/2026). È la seconda delle tre parti della fatturazione
semplice: la prima è [45](./45-codici-in-parole.md) (ogni codice col suo nome), la
terza sarà la fattura fatta dentro DottorCloud.

## Il bisogno

Con la clinica accesa DottorCloud è il programma di un centro medico, e la sua
fatturazione è quella di un centro medico: chi emette comunica al Sistema TS, le
prestazioni sono sanitarie ed esenti (art. 10), il tipo di spesa è quello di chi
emette. Eppure bisognava impostarla campo per campo: la categoria del Sistema TS,
il regime, la cassa, la ritenuta, e poi una scheda fiscale per ogni servizio
dell'agenda, a mano.

Tre cose, poi, erano sbagliate:

- **una qualifica che il centro aveva corretto, o spento, tornava come era stata
  spedita.** Il registro sanitario che arriva con il programma rispondeva prima di
  quello del centro, perché il suo modulo si carica dopo la fatturazione. Un
  centro che, col commercialista, decideva che il massoterapista non è una
  professione sanitaria continuava a fatturarlo come tale;
- **«Ramo sanitario attivo»** in Impostazioni › Fatturazione › Opzioni era una
  casella che nessuno leggeva: spegnerla non cambiava niente;
- **una nuova azienda partiva da valori diversi** a seconda di dove la si creava:
  la pagina delle impostazioni diceva «provider» per lo SdI, il DocType «scarica
  il file». E «Nuova azienda» non svuotava il modulo: mostrava l'azienda aperta, e
  salvando l'avrebbe sovrascritta.

## Cosa cambia

- **Tre domande** nella pagina dell'azienda emittente, con la clinica accesa:
  1. chi emette le fatture: una struttura autorizzata dalla Regione, un medico o
     un dentista a suo nome, un altro professionista sanitario a suo nome, una
     struttura accreditata con il SSN;
  2. per una struttura, i codici della sua abilitazione al Sistema TS (Regione,
     ASL, struttura); per un professionista, la sua professione;
  3. per un professionista, il regime fiscale: ordinario, forfettario o minimi.
     Una struttura è nel regime ordinario.

  Dalle risposte si impostano:
  - la categoria del Sistema TS e il regime;
  - per un professionista, la cassa e la ritenuta della sua professione, come le
    dice il registro, e nessuna ritenuta proposta: un paziente non è un sostituto
    d'imposta. In uno studio senza nessuno ancora che esegua le prestazioni, il
    professionista stesso diventa il primo;
  - per una struttura, niente cassa né ritenuta.

  Una scheda in cima alla pagina riassume le risposte («Professionista
  sanitario, a suo nome · Regime ordinario · Prestazioni del professionista
  sanitario») e si cambiano con un clic.
- **Le schede dei servizi dall'agenda.** Nella pagina dei servizi fatturabili, i
  servizi dell'agenda senza scheda diventano schede in un clic:
  - prestazione sanitaria, esente, con la dicitura che la fattura riporterà;
  - il tipo di spesa di chi emette e il prezzo dell'agenda;
  - il professionista, quando l'agenda ne indica uno solo.

  Ogni scheda aspetta il commercialista, come tutte. Una scheda con lo stesso nome
  che non puntava a nessun servizio viene collegata, non doppiata. Anche una
  scheda nuova parte già come prestazione sanitaria esente.
- **Il registro delle qualifiche mostra le professioni sanitarie**, e quelle che
  qualcuno usa. Le altre (avvocato, ingegnere, sviluppatore…) restano dietro
  «Mostra le altre professioni».
- **Il registro del centro vince sempre su quello spedito.** Prima rispondono i
  registri che il centro modifica, poi quelli che arrivano col programma, in
  qualunque ordine si carichino i moduli. Una qualifica spenta ferma la catena con
  il suo messaggio, invece di tornare come spedita.
- **«Ramo sanitario attivo» non c'è più.** Quello che faceva credere di fare lo
  decide già la categoria di chi emette: «Non sanitario» non comunica niente al
  Sistema TS, e lo SdI non porta mai una prestazione sanitaria a una persona
  fisica.
- **Una nuova azienda parte da dove dice il DocType**, e da nessun'altra parte. Lo
  SdI parte da «Scarichi il file e lo carichi tu», che funziona dal primo giorno;
  il provider si accende quando l'agenzia lo collega. «Nuova azienda» apre un
  modulo vuoto, e la lista di cosa manca dell'azienda aperta si nasconde intanto.
- **I messaggi del Sistema TS sui codici della struttura** dicono le cose a parole:
  «Regione, ASL e struttura», non «codiceRegione-codiceAsl-codiceSSA», e non la
  categoria col suo codice.

## Come è fatta

- `crm/tessera_sanitaria/preimpostazione.py`:
  - `get_setup()`: le domande con le scelte in parole, le risposte di oggi, la
    scheda nuova di un centro medico;
  - `apply_setup()`: le risposte sull'azienda, con `fatture.configura`;
  - `cards_from_services()`: le schede dai servizi dell'agenda.

  Sta nel modulo del Sistema TS: conosce le categorie e i tipi di spesa, e la
  fatturazione non lo importa.
- `crm/invoicing/estensioni.py`: due livelli di risolutori, registrati con
  `registra_risolutore(funzione, spedito=...)`; `QualificaRifiutata` ferma la
  catena. `crm/invoicing/registro.py` la usa per una qualifica spenta; il Sistema
  TS registra il suo registro spedito con `spedito=True`.
- `crm/invoicing/doctype/crm_invoicing_settings`: senza `healthcare_enabled`.
- Il frontend:
  - `Settings/Invoicing/HealthcareSetup.vue` e `SceltaRadio.vue`: le tre domande;
  - `InvoicingCompany.vue`: la scheda delle risposte, il modulo nuovo vuoto;
  - `DocFields.vue` e `utils/settingsTabs.js` (`valorePredefinito`): i valori del
    DocType per un record nuovo;
  - `BillableServicesSettings.vue`: le schede dall'agenda, la scheda nuova
    sanitaria;
  - `QualificationsSettings.vue` e `RecordList.vue` (`visibile`): il registro
    filtrato.

## Verifiche

- `crm/invoicing/tests/test_confine.py` (puro): quello che ha scritto il centro
  vince su quello spedito, una qualifica spenta ferma la catena, fra due registri
  del centro risponde l'ultimo, `senza_estensioni` rimette a posto anche i
  registri spediti.
- `crm/tessera_sanitaria/tests/test_registro_del_centro.py` (sul sito): un
  massoterapista reso ordinario resta ordinario, una correzione del centro arriva
  in fattura, un osteopata spento non torna come spedito.
- `crm/tessera_sanitaria/tests/test_preimpostazione.py` (sul sito):
  - le scelte di un centro medico;
  - un fisioterapista nel forfettario, con la cassa della sua professione;
  - una struttura nel regime ordinario con i suoi tre codici, poi di nuovo uno
    psicologo, senza i codici;
  - la professione è di chi emette;
  - le schede dai servizi una volta sola, col professionista dell'agenda e la
    scheda omonima collegata.
- Le suite della fatturazione e del Sistema TS, quelle che toccano le fatture, e i
  test del frontend (`valorePredefinito`).
- Nel browser, in italiano:
  - le tre domande come struttura (con i codici) e come psicologo (la professione
    già scelta dal suo unico professionista);
  - una nuova azienda vuota, con lo SdI su «Scarichi il file e lo carichi tu»;
  - dieci schede create dall'agenda, e la scheda nuova sanitaria;
  - il registro delle qualifiche filtrato e intero.
