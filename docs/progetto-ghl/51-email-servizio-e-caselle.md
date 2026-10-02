# 51 · Le email: il servizio di invio e le caselle

**Stato:** prima parte fatta (02/10/2026): il servizio di invio dell'agenzia, le
email che arrivano alla loro persona, la pagina delle caselle del centro. Seconda
parte in corso: la casella di ognuno, anche con l'accesso di Google e Microsoft.

## Il bisogno

- **Le notifiche**: promemoria, codici, conferme, offerte della lista d'attesa,
  avvisi. Le scrive DottorCloud da solo, per ogni centro, e devono arrivare: serve
  un servizio di invio centrale dell'agenzia.
- **La posta di ognuno**: chi lavora nel centro ha il suo indirizzo e vuole
  scrivere alle persone da DottorCloud, con le risposte che tornano lì.
- Non era chiaro come funzionassero le connessioni email.

## Com'era

- **Ogni email partiva dalla casella «predefinita in uscita» del sito.** Senza una
  casella del centro i promemoria non partivano, o partivano dalla configurazione
  del server con il nome del framework come mittente; con la casella del centro,
  partivano dalla sua casella (Gmail, Aruba…), che non è fatta per mandare
  centinaia di promemoria e finisce nello spam o bloccata.
- **La pagina «Account email»** offriva Gmail, Outlook, Sendgrid, SparkPost, Yahoo
  e Yandex:
  - Sendgrid e SparkPost sono servizi di invio, non caselle;
  - Outlook non accetta più la password dal 2024;
  - mancavano Aruba, Libero, Virgilio, Tiscali, iCloud.
- **Una casella aggiunta faceva una persona di ogni email** che non era una
  risposta («Append To: CRM Lead»), anche di chi il centro conosceva già: doppioni.
- **La risposta a un promemoria finiva sull'appuntamento**, dove nessuno la
  leggeva; lo stesso per un'offerta della lista d'attesa o un abbonamento.
- **Il manager non poteva salvare una casella che riceve**: il framework controlla
  una lista che legge solo l'amministratore.
- **Chi segue una persona riceveva nella sua casella personale una copia** di ogni
  email di quella persona, e il pannello delle notifiche non diceva niente.

## Come fanno gli altri

- **HubSpot, Pipedrive, GoHighLevel**: due strade separate.
  - Le email automatiche e di massa partono dal servizio della piattaforma, su un
    dominio verificato, a nome dell'azienda.
  - Le caselle personali si collegano per le conversazioni una a una, quasi sempre
    con l'accesso di Google o Microsoft (OAuth), a volte con IMAP e password.
- **Google e Microsoft stanno togliendo la password semplice**:
  - Outlook.com, Hotmail e Live non la accettano più dal 16 settembre 2024;
  - Microsoft 365 la spegne per l'invio (SMTP AUTH) alla fine del 2026, e
    annuncerà la data finale nel 2027;
  - Google Workspace, dal 14 marzo 2025, accetta solo l'accesso Google (OAuth) o
    le password per le app.
- **L'accesso Google a Gmail costa**: gli ambiti che leggono e mandano la posta
  sono «riservati», e chi li usa da un server deve passare una verifica e una
  valutazione di sicurezza (CASA) ogni anno.

## Come funziona adesso

### 1. Il servizio di invio di DottorCloud

- È **dell'agenzia, uno per tutti i centri**: un servizio come Amazon SES o Brevo,
  con il suo dominio (per esempio `posta.dottorcloud.it`) dimostrato una volta
  con SPF, DKIM e DMARC.
- **Da qui partono** promemoria, codici, conferme, offerte, notifiche: tutto quello
  che DottorCloud scrive da solo.
- **La persona legge il centro**: `Centro Aurora <notifiche@posta.dottorcloud.it>`.
  Il nome è del centro, l'indirizzo è del servizio: è l'unico che il servizio può
  firmare.
- **Le risposte vanno al centro** (Reply-To): alla casella principale del centro,
  o all'indirizzo che il centro sceglie nella pagina.
- **Chi scrive dalla pagina di una persona senza una casella sua** scrive da qui:
  `Anna Bianchi · Centro Aurora`, e le risposte tornano ad Anna.
- **Il centro non configura niente.** Mentre il servizio è acceso, nessuna casella
  del centro manda i promemoria; se l'agenzia lo spegne, torna a mandarli la
  casella del centro che li mandava prima.

### 2. Le caselle del centro

In Impostazioni > E-mail > Account email:

- **La casella della segreteria**: si sceglie dov'è (Gmail, Aruba, Libero,
  Virgilio, Tiscali, iCloud, Yahoo), si scrivono indirizzo e password. I server li
  conosce DottorCloud; la pagina dice cosa chiede ogni fornitore (Gmail, iCloud e
  Yahoo vogliono una password per le app).
- **Un'email che arriva va sulla pagina di chi la scrive**, trovato dal suo
  indirizzo: mai un'altra persona con lo stesso indirizzo.
- **Una persona nuova** solo per chi scrive la prima volta e solo se la casella lo
  dice; mai per un mittente automatico («noreply», un rimbalzo), per qualcuno del
  centro, per un'altra casella del centro o per la casella dove scrive una
  piattaforma di prenotazione (la sua sincronizzazione trova la persona).
- **La risposta a un promemoria passa sulla pagina della persona**, e
  l'appuntamento tiene il collegamento. Solo i documenti di DottorCloud: il filo
  di un'altra app (un ticket) resta dov'è.
- **Chi segue la persona lo sa dal pannello**: «Hai ricevuto un'email da Anna
  Rossi», e le email dopo si sommano («Hai ricevuto 3 email da…»); per email solo
  se lo vuole (doc 43). La copia del framework nella casella personale non arriva
  più.
- **Le risposte alle email di DottorCloud** vanno alla casella principale, o a un
  altro indirizzo scelto in cima alla pagina; un indirizzo che non si legge in
  DottorCloud è detto: le risposte restano lì.
- **Outlook, Hotmail e Microsoft 365** li collega l'agenzia, finché non c'è
  l'accesso Microsoft (seconda parte).

### 3. La casella di ognuno (seconda parte, in corso)

- In Impostazioni > Il tuo account: la propria casella, con gli stessi fornitori e
  la password per le app.
- Con l'accesso Google o Microsoft quando l'agenzia lo attiva: un clic, niente
  password.
- Si scrive dalla pagina di una persona con il proprio indirizzo; arrivano in
  DottorCloud solo le email delle persone che il centro conosce, non tutta la
  posta personale.

## Cosa fa NPM2, una volta

- **Il servizio di invio**: in Europa, con il contratto per il trattamento dei dati
  (art. 28 GDPR), per esempio Amazon SES nella regione di Milano o Brevo.
- **Il dominio di invio**: SPF, DKIM e DMARC. Gmail e Yahoo li chiedono dal 2024 a
  chi manda molte email.
- **La configurazione** in `common_site_config.json`, per tutti i siti del server:

  ```json
  "dottorcloud_posta": {
      "server": "email-smtp.eu-south-1.amazonaws.com",
      "porta": 587,
      "utente": "…",
      "password": "…",
      "mittente": "notifiche@posta.dottorcloud.it"
  }
  ```

  Ogni sito la segue al prossimo migrate, entro un'ora, o subito con «Sincronizza
  ora» nella pagina (che vede solo l'agenzia). Un servizio che non risponde non
  viene installato: resta un errore nel registro.
- **Per la seconda parte**, registrare l'app di DottorCloud:
  - su Google Cloud: verifica dell'app e valutazione di sicurezza annuale (CASA)
    per leggere e mandare la posta, o solo le password per le app;
  - su Microsoft Entra: l'editore verificato, perché le persone possano dare il
    consenso da sole.

## Come è fatta

- `crm/posta/servizio.py`:
  - `configurazione()` legge `dottorcloud_posta`;
  - `assicura()` fa e tiene allineato l'account «DottorCloud» (dopo il migrate e
    ogni ora), salvandolo solo se cambia; un errore annulla solo il suo
    salvataggio;
  - `intestazioni()` (hook `make_email_body_message`): il mittente con il nome del
    centro, la busta del servizio, il Reply-To;
  - le chiamate della pagina: `get_sending_service`, `set_reply_address`,
    `sync_sending_service` (solo l'agenzia).
- `crm/posta/ingresso.py`: `alla_ricezione()` (dopo l'inserimento di una
  Communication ricevuta) trova la persona, ne fa una nuova dove si deve, sposta
  le risposte dai documenti di DottorCloud, e avvisa chi la segue.
- `crm/api/settings.py`: i fornitori con i loro server (`FORNITORI`), le caselle
  senza il servizio, gli errori in parole, il salvataggio con l'elenco dei
  documenti letto per intero (`_dove_archivia`).
- `FCRM Settings.reply_to_email`: dove vanno le risposte, se il centro lo sceglie.
- Le notifiche: il genere «email» in `crm/notifiche/regole.py`, nel pannello e
  nelle email di avviso; il tipo «Email» di `CRM Notification`.
- `crm/permissions/utenti.py`: chi ha un livello non riceve la copia del framework
  (`thread_notify`).
- Il frontend:
  - `utils/caselle.js`: i fornitori, i segni di una casella, gli interruttori, cosa
    manca per salvarla, dove vanno le risposte;
  - `Settings/EmailAccountList.vue`, `SendingService.vue`, `EmailAccountCard.vue`,
    `EmailEdit.vue` (aggiungere e cambiare sono lo stesso modulo).
- La patch `emails_reach_their_person`: le caselle smettono di fare una persona a
  ogni email (lo fa DottorCloud per chi scrive la prima volta), chi ha un livello
  smette di ricevere la copia.

## Verifiche

- `crm/posta/tests/test_servizio.py`:
  - l'account segue la configurazione, la porta 465, senza password, una
    configurazione a metà non è un servizio;
  - un promemoria viene dal centro sull'indirizzo del servizio, la busta compresa,
    e le risposte vanno alla casella del centro o all'indirizzo scelto;
  - chi scrive senza casella sua scrive a nome del centro;
  - senza configurazione il servizio si ferma e torna la casella del centro;
  - un servizio che non risponde non disfa il resto del migrate;
  - la pagina: il manager sceglie dove vanno le risposte, la sincronizzazione è
    dell'agenzia, il servizio non è tra le caselle, il manager aggiunge una casella
    che riceve.
- `crm/posta/tests/test_ingresso.py`:
  - chi è conosciuto va sulla sua pagina, senza doppioni;
  - la risposta a un documento di DottorCloud passa alla persona, il filo di
    un'altra app no;
  - una persona nuova solo dove la casella lo dice, mai macchine, centro o
    piattaforme; un'email mandata non fa una persona;
  - l'avviso a chi segue la persona, e la seconda email si somma;
  - la patch.
- `frontend/tests/unit/caselle.test.js`.
- Nel browser, in italiano: la pagina del manager e dell'agenzia, un altro
  indirizzo per le risposte, una casella nuova di Aruba, il telefono.

## Fonti

- Microsoft, [Outlook.com senza l'autenticazione di base](https://support.microsoft.com/en-us/office/outlook-and-other-apps-are-unable-to-connect-to-outlook-com-when-using-basic-authentication-f4202ebf-89c6-4a8a-bec3-3d60cf7deaef).
- Office 365 for IT Pros, [il ritiro di SMTP AUTH rimandato](https://office365itpros.com/2026/01/29/smtp-auth-basic-retirement/) (gennaio 2026).
- Google Workspace, [dalle app meno sicure a OAuth](https://support.google.com/a/answer/14114704?hl=en).
- Google, [verifica degli ambiti riservati](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification).
