# 65 · Telnyx: l'altro gestore, fatto come Twilio

**Stato:** fatto (10/10/2026).

## Il bisogno

- Il centro deve poter scegliere **Telnyx al posto di Twilio**, con le stesse cose
  che il doc 52 dà a Twilio: collegare il suo account da DottorCloud, comprare i
  numeri italiani con i documenti, far squillare tutti insieme, la segreteria e la
  richiamata, telefonare dal browser, mandare SMS da un mittente del centro,
  vedere quanto spende, mostrare un numero che ha già con un altro operatore.
- **Un gestore alla volta.** Chiamate, numeri e SMS del centro passano da uno
  solo: una chiamata e la sua risposta non prendono mai due strade, e un SMS ha un
  mittente solo. Con Twilio collegato, la pagina di Telnyx aspetta che lo si
  scolleghi, e viceversa (`crm/telephony/operatore.py`, `libero_per`).

## Cosa permette Telnyx (verificato il 10/10/2026)

- **Un account solo, senza spazi dentro.** Telnyx non ha i sottoaccount di Twilio
  per un account qualunque (gli «account gestiti» sono un'opzione da chiedere a
  Telnyx), e **nessuna chiave è limitata a una parte dell'account**. Quindi
  DottorCloud **tiene la chiave API** del centro, cifrata, nel server, e la usa solo
  su quello che crea lui. Scollegando, la chiave viene dimenticata.
- **Le risorse che DottorCloud crea**, tutte con il nome «DottorCloud · indirizzo
  del sito», riconoscibili nel portale e ritrovate a un nuovo collegamento:
  - un'**applicazione TeXML** (il gemello di TwiML): dove Telnyx chiede cosa fare di
    una chiamata a un numero del centro;
  - una **connessione a credenziali**: dove si registrano i browser, una
    credenziale per persona;
  - un **profilo voce in uscita**: i paesi che si possono chiamare;
  - un **profilo di messaggistica**: da dove partono e dove arrivano gli SMS.
- **I webhook sono firmati** con Ed25519 su «timestamp|corpo», con una chiave
  pubblica dell'account che Telnyx **non dà dall'API**: per questo il centro copia
  dal portale due codici, la chiave API e la chiave pubblica. DottorCloud rifiuta
  ogni richiesta non firmata o più vecchia di cinque minuti.
- **I numeri si segnano** con un'etichetta del sito (`dottorcloud-<indirizzo>`):
  in un account con i numeri di altri siti (quello dell'agenzia) ognuno trova i
  suoi.
- **Telnyx si paga in anticipo**: l'account ha un credito, e quando finisce
  chiamate e SMS si fermano. Twilio non dice a uno spazio il credito dell'account;
  Telnyx all'account lo dice, e la pagina lo mostra.

## Le regole italiane con Telnyx

- **I numeri.** Telnyx vende in Italia i **geografici** (02, 06, 011…, chiamate in
  entrata e in uscita) e i **numeri verdi** (800, solo in entrata). **Non vende
  mobili italiani**: un fisso italiano non manda SMS, e gli SMS del centro partono
  con il suo nome come mittente (a cui non si risponde).
- **I documenti** sono i requisiti di Telnyx per l'Italia: dati dell'intestatario,
  un indirizzo in Italia (per un geografico nel distretto del prefisso), i documenti
  **solo in PDF, fino a 20 MB**. Telnyx li raccoglie in un gruppo che vale per il
  numero dopo dello stesso tipo e della stessa zona.
- **Prima il numero, poi i documenti.** In Italia Telnyx non approva i documenti
  prima dell'ordine: si sceglie il numero, lo si ordina con i documenti, e Telnyx
  controlla tutto a mano in qualche giorno lavorativo. L'ordine dice com'è andata.
- **Le chiamate in uscita.** Le stesse regole AGCOM del doc 52: un numero
  verificato di un altro operatore compare in Italia finché gli operatori lo
  lasciano passare, e un mobile italiano mostrato da una chiamata dall'estero si
  blocca. Il numero che compare è uno del centro o la propria linea, mai uno
  inventato dal browser.
- **Il nome come mittente** Telnyx lo accetta da un account verificato al livello
  2: il codice 20017 lo dice a parole.

## Com'è fatto in DottorCloud

### Il collegamento (Impostazioni > Telefono > Telefonia > Telnyx)

- Tre passi: creare e verificare l'account su Telnyx e ricaricarlo; creare una
  chiave API e copiare la chiave pubblica; incollarle e collegare. Le due chiavi si
  controllano prima di chiedere a Telnyx (`regole.cosa_manca`, lo stesso nella
  pagina: `utils/telnyx.js`).
- DottorCloud crea o ritrova le sue quattro risorse, punta a sé ogni numero libero
  o con la sua etichetta, lascia stare quelli sul centralino del centro (una
  connessione SIP) o su un'altra applicazione, e lo dice.
- **Ogni ora** (`collegamento.assicura`) rimette quello che qualcuno ha cambiato nel
  portale e allinea i paesi e il mittente; «Controlla» fa lo stesso subito e dice il
  credito.
- L'**agenzia** può collegare il suo account (`dottorcloud_telnyx` in
  `common_site_config.json`, con `api_key` e `public_key`): lì DottorCloud non prende
  i numeri liberi, che possono essere di altri siti, e accetta solo le chiamate delle
  sue connessioni.

### Le chiamate

- **In arrivo**: Telnyx chiede all'applicazione TeXML (`crm.integrations.telnyx.api`
  `incoming_call`); DottorCloud risponde come con Twilio (`crm/telephony/inbound.py`,
  la stessa segreteria e lo stesso squillo a tutti), in TeXML
  (`crm/telephony/providers/telnyx.py`). Il browser squilla con il suo indirizzo SIP
  (`<Sip>sip:utente@sip.telnyx.com</Sip>`: TeXML non ha il `<Client>` di Twilio), il
  cellulare con il suo numero, e chi risponde lo dice Telnyx (`call_status`).
- **Dal browser**: l'SDK WebRTC di Telnyx (`@telnyx/webrtc`, caricato al primo uso)
  con un gettone della propria credenziale. La connessione a credenziali
  **parcheggia** ogni chiamata e chiede a DottorCloud (`voice`) se può partire:
  `uscita.perche_no` decide sul server qualunque cosa abbia fatto la pagina, come con
  Twilio.
- **Le registrazioni**: Telnyx dà un link che scade in dieci minuti, quindi un
  lavoro le scarica subito in un file privato del registro della chiamata
  (`registrazioni.py`); il lettore le serve da lì, a pezzi.

### Gli SMS

- Tutti da `sms.mittente()`, come con Twilio: il nome del centro o un suo numero che
  manda SMS. `crm.api.sms.deliver_sms` sceglie il gestore collegato.
- In arrivo: STOP e START (lo stesso `sms_regole`), le risposte ai promemoria, la
  risposta automatica di Telnyx a uno STOP non scritta due volte; lo stato di un SMS
  mandato e il suo errore a parole (`errori_regole`).

### I numeri

- **Numero nuovo**: tipo e prezzo, la zona, i numeri pronti, l'intestatario con i
  dati della fatturazione già scritti, i documenti in PDF, poi l'ordine
  (`numeri.send_number_request`). Ogni ora DottorCloud chiede com'è andata e lo dice
  tra le notifiche («Telefono»), con il motivo di un rifiuto dai commenti di Telnyx.
  I documenti approvati valgono per il numero dopo.
- **Ho già un numero**: uno dell'account Telnyx del centro entra in DottorCloud
  senza codici (DottorCloud lavora già lì: `trasloco.move_number`); uno di un altro
  operatore si verifica, si inoltra o si porta su Telnyx.
- **Verificato per le chiamate**: Telnyx chiama il numero, o gli manda un SMS, con un
  codice che si scrive in DottorCloud (al contrario di Twilio, dove il codice lo si
  digita al telefono: `verificati.verify_number`, `confirm_code`).
- **Rilasciato** solo un numero di DottorCloud.

### Quanto spende

- Il mese per voce (chiamate, SMS, numeri, registrazioni) dai rapporti di Telnyx, il
  **credito** con un avviso quando sta per finire, i problemi degli ultimi giorni a
  parole, per chi paga l'account.
- Telnyx non ha un avviso che richiami quando la spesa arriva a una cifra: DottorCloud
  guarda **ogni ora** e avvisa una volta al mese per la spesa, una volta per il
  credito basso finché non viene ricaricato (`consumi.controlla_gli_avvisi`).

## Cosa resta su Telnyx

- Creare l'account, verificarlo, ricaricarlo; creare la chiave API e copiare la
  chiave pubblica; la portabilità di un numero di un altro operatore (la richiesta di
  Telnyx).

## Dove sta

- `crm/telephony/operatore.py`: il gestore collegato, uno alla volta.
- `crm/telephony/telnyx/`: le regole senza sito (`regole.py`, `numeri_regole.py`,
  `consumi_regole.py`, `errori_regole.py`), il client (`cliente.py`), il
  collegamento, i numeri, la spesa, i verificati, i numeri già nell'account, gli
  SMS, le registrazioni, il TeXML.
- `crm/integrations/telnyx/api.py`: i webhook (chiamate, stato, registrazioni, SMS),
  il gettone del browser, `prepare_call`.
- `crm/fcrm/doctype/crm_telnyx_settings/`: le impostazioni; i codici e gli
  identificativi delle risorse al permlevel 1.
- Pagina: `frontend/src/components/Settings/Telephony/TelnyxSettings.vue`,
  `TelnyxMoveDialog.vue`, `NewNumberDialog.vue` e `VerifyNumberDialog.vue` con il
  gestore; il telefono nel browser `components/Telephony/TelnyxCallUI.vue`.
- Prove: `crm/telephony/telnyx/tests/` con un Telnyx finto (`telnyx_finto.py`, firme
  Ed25519 vere), `frontend/tests/unit/telnyx.test.js`.
