# 49 · Itala, la prova prima del vero, e solo l'essenziale

**Stato:** fatto (02/10/2026). Segue i controlli prima di emettere
([48](./48-controlli-in-parole.md)): la fattura si fa dentro DottorCloud
([47](./47-fattura-dentro-dottorcloud.md)) e dice tutto quello che manca; qui la
fatturazione si prova prima di metterla dal vivo, parte da un solo intermediario, e
al centro restano solo le impostazioni che sono sue.

## Il bisogno

Tre richieste:

- **provare la fatturazione prima di metterla dal vivo**, con le fatture vere fatte
  come saranno, senza che niente arrivi a nessuno;
- **un solo provider al pubblico: Itala.** Le altre strade (il file da caricare a
  mano, la PEC del centro) restano nel codice, ma non si offrono;
- **togliere al centro le impostazioni**, una soluzione già pronta con il minimo da
  impostare.

Com'era:

- il canale verso lo SdI si sceglieva sull'azienda fra tre, e per il provider il
  centro doveva scrivere endpoint, URL di login, utente, password, chiave API,
  segreto del webhook; ogni centro con un suo account;
- la «sandbox» valeva solo per il provider: una fattura di prova prendeva un numero
  della serie vera, che poi aveva un buco o partiva da 5;
- il Sistema TS andava all'ambiente di collaudo di Sogei finché nessuno scriveva
  `sistema_ts_ambiente` nella configurazione: una fattura vera, dal vivo, sarebbe
  stata comunicata al collaudo;
- il centro vedeva e poteva cambiare numerazione, conservazione, canale, modalità e
  certificato del Sistema TS;
- e due difetti trovati strada facendo:
  - la riconciliazione col provider chiedeva la direzione sbagliata: chi riceveva
    anche le fatture dei fornitori non riceveva più gli esiti delle sue, chi
    emetteva soltanto archiviava le fatture dei fornitori;
  - Itala riscrive il blocco di trasmissione con i suoi riferimenti, quindi le
    notifiche dello SdI rispondono al nome del file di Itala, che non veniva tenuto.

## Cosa cambia

- **Ogni azienda parte in prova.** Una fattura si fa, si emette e si invia come sarà
  dal vivo, ma è una fattura di prova:
  - ha una serie sua (`2026/PROVA-S/1`): la numerazione vera, quando si attiva,
    parte da uno senza buchi;
  - il PDF ha una fascia «Fattura di prova: non ha valore fiscale»;
  - quella elettronica va all'ambiente di prova di Itala: niente arriva allo SdI;
  - la comunicazione al Sistema TS si controlla all'emissione e non parte («Prova:
    controllata, non inviata»);
  - non fa un cliente né un paziente, e non compare nell'area del paziente;
  - la pagina delle fatture dice «Fatturazione in prova», la finestra della fattura
    ha il segno «Prova».
- **Attivare è un gesto solo**, in Impostazioni > Fatturazione > **Prova e
  attivazione**:
  - la pagina dice dove sta l'azienda (in prova, o attiva dal…), cosa manca e chi lo
    deve fare, e come partono le fatture;
  - quello che manca e impedisce di attivarla porta la croce rossa del marchio: la
    partita IVA, la sede, un professionista e una scheda di servizio, l'autorizzazione
    del bollo virtuale se si usa; il resto si dice e non ferma;
  - attivando, le fatture di prova vengono tolte (con quello che le indicava: la
    rata di un abbonamento torna da fatturare), e da quel momento ogni fattura è
    vera;
  - tornare in prova è dell'agenzia, e solo finché non c'è una fattura vera: la loro
    numerazione è un fatto fiscale.
- **Itala è l'unico intermediario**, sull'**account dell'agenzia**:
  - l'account sta nelle Opzioni della fatturazione, visibile solo all'agenzia, oppure
    una volta per tutto il server (`itala_client_id`, `itala_client_secret` in
    `common_site_config.json`); un'azienda può ancora avere un account suo;
  - ogni azienda si registra da sola sotto l'account (la gestione multi-azienda di
    Itala) la prima volta che parte una sua fattura, una volta per ambiente;
  - gli indirizzi di prova e di produzione sono quelli pubblicati da Itala: niente da
    scrivere;
  - il nome del file e l'identificativo che Itala dà alla fattura si tengono: le
    notifiche e gli aggiornamenti trovano la loro fattura;
  - un account per tanti siti non può chiamare ognuno col suo webhook: ogni sito
    chiede a Itala gli esiti ogni dieci minuti, e solo quando c'è qualcosa che
    aspetta (una fattura partita senza esito, una alla PA consegnata e non ancora
    accettata, i fornitori se si ricevono). Senza rumore: una volta al giorno si
    registra quello che non ha risposto.
- **Al centro resta solo il suo**:
  - l'azienda: chi emette, i dati, il regime, i contatti, la cassa e il bollo (le tre
    domande del 46 li impostano), le **credenziali del Sistema TS**;
  - numerazione, conservazione, trasmissione, modalità e certificato del Sistema TS
    sono dell'agenzia (livello di permesso 1, System Manager);
  - una schermata non disegna mai un campo che chi la guarda non può leggere: vale per
    ogni impostazione (`crm.api.doc.get_fields`);
  - i pulsanti di manutenzione delle Opzioni (leggere la PEC, sondare la delega
    Entratel) sono dell'agenzia.
- **Il Sistema TS**:
  - una fattura vera va alla produzione; il collaudo di Sogei si sceglie solo per un
    sito di sviluppo (`sistema_ts_ambiente: test`);
  - il certificato del kit ufficiale l'agenzia lo carica una volta per il sito, nelle
    Opzioni; quello di un'azienda vale solo se c'è; la scadenza si sorveglia per
    entrambi;
  - la modalità «tramite provider» spediva un file a un indirizzo che nessun
    provider documenta: tolta (le aziende che l'avevano tornano alle credenziali del
    centro).

## Il Sistema TS e Itala: cosa resta da decidere

Itala ha anche un servizio per il Sistema TS (sistema-ts-api.it, REST v1). Letto il
contratto, oggi non basta a un poliambulatorio:

- l'erogatore si registra con partita IVA, codice fiscale e le credenziali del
  Sistema TS del centro, ma **senza i codici di regione, ASL e struttura** che una
  struttura autorizzata deve mandare;
- le operazioni sono solo **inserimento e cancellazione**: niente rimborso né
  variazione;
- niente indicatore del pagamento anticipato.

Per un professionista che fattura a suo nome funzionerebbe. Quindi, per ora,
DottorCloud comunica direttamente con il Sistema TS con le credenziali del centro,
gratis e con il tracciato completo.

Da tenere d'occhio: Sogei ha pubblicato l'**autenticazione a due fattori** dei web
service del Sistema TS (v1.1 del 12/01/2026), un ID-SESSIONE da mandare in
`Authorization2F`, che si attiva «secondo i cronoprogrammi» di ogni servizio. Se
diventa obbligatoria anche per le spese sanitarie, il centro dovrà chiedere la
sessione (via email certificata), o la comunicazione passerà da un intermediario.
Da chiedere a Itala: se il suo servizio porta i codici di una struttura e come
gestisce la sessione.

## Come è fatta

- `crm/invoicing/prova.py`:
  - `segna()` all'emissione, prima del numero;
  - `mancanze()`: la lista di cosa manca, per la pagina dell'azienda e per attivare;
  - `get_status`, `go_live`, `back_to_test`, `register_at_itala`;
  - `togli_le_fatture_di_prova()`.
- `crm/invoicing/engine/numerazione.py`: `serie_di_prova()`, che sta nei venti
  caratteri del Sistema TS.
- `crm/invoicing/connessione.py`:
  - `Accesso`: chi siamo per Itala, per un'azienda e un ambiente;
  - `accesso()`: l'account proprio o quello dell'agenzia;
  - il token raccolto dalle chiamate Basic.
- `crm/invoicing/sdi/itala.py`: `registra_azienda()` (`/aziende`, ritrovata per
  partita IVA), `invia()` per l'ambiente del documento, `aggiornamenti()` per la
  partita IVA dell'azienda.
- `crm/invoicing/sdi/riconciliazione.py`: la direzione giusta, `da_chiedere()`.
- I campi:
  - `CRM Invoice.test_document`, `sdi_provider_id`, lo stato TS `prova`;
  - `CRM Invoicing Company.live_since`, `itala_id_test`, `itala_id`, le sezioni
    dell'agenzia sul livello 1;
  - `CRM Invoicing Settings`: l'account Itala e il certificato del Sistema TS.
- Il frontend:
  - `Settings/Invoicing/ProviderConnection.vue`, la pagina «Prova e attivazione»
    (la chiave resta `Provider connection`);
  - la fascia in `pages/Invoices.vue`;
  - il segno «Prova» in `InvoiceDialog.vue`.
- Patch `invoicing_tries_before_it_goes_live`: un'azienda che ha già emesso è attiva
  dal giorno della prima fattura; una che non ha emesso niente parte in prova, su
  Itala (se non c'era la PEC).
- Il contratto di Itala, riassunto: `.pi/vendor/itala.md`.

## Verifiche

- `crm/tests/test_prova.py` (sul sito):
  - in prova: la serie `PROVA-S`, il Sistema TS non la riceve, la finestra lo dice,
    non fa un cliente e non va nell'area;
  - dal vivo una prova non parte e non si corregge;
  - attivare toglie le prove e la fattura dopo è vera, sulla serie vera;
  - senza partita IVA non si attiva;
  - quello che manca dice chi lo fa;
  - in prova si torna solo senza fatture vere;
  - Itala, su una rete finta:
    - l'account dell'agenzia per ambiente, e senza account lo dice;
    - si registra una volta per ambiente, o si ritrova dalla partita IVA;
    - la prova parte per l'ambiente di prova e si tiene il nome del file di Itala;
    - il token si raccoglie e si riusa;
    - chi emette soltanto chiede le sue trasmissioni;
    - si chiede solo quando qualcosa aspetta;
  - il centro non vede i campi dell'agenzia.
- `crm/tests/test_invoicing.py`: Itala senza account, la riga «Itala» in quello che
  manca. Le altre prove della fatturazione girano su un'azienda attiva.
- Nel browser, in italiano:
  - la fascia sulle fatture, il segno «Prova» nella fattura nuova;
  - la pagina del centro e quella dell'agenzia, il telefono;
  - la scheda dell'azienda con tre schede (Azienda, Fatturazione, Sanitario) e le
    credenziali del Sistema TS;
  - una fattura `2026/PROVA-S/1` emessa, attivata la fatturazione: tolta, e niente
    più fascia.
