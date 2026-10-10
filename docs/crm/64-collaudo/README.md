# 64 · Collaudo prima della produzione

**Stato:** in corso (10/10/2026). Il livello 1 si sta costruendo (`crm/collaudo`,
`e2e/simulazione/`); i livelli 2 e 3 sono scritti qui e si fanno a mano.

## A cosa serve

Prima che un centro vero lavori con DottorCloud, lo proviamo in tre livelli, ognuno
più vicino alla vita vera del precedente: prima una macchina che recita la settimana
di un centro, poi la squadra di NPM2 che fa i ruoli del centro su un server di
collaudo con i servizi esterni nei loro ambienti di prova, infine un centro pilota
che lavora con DottorCloud accanto al suo vecchio programma. Ogni livello ha i suoi
criteri d'uscita: finché non sono veri, non si passa al successivo. Questa pagina
dice cosa sono i tre livelli, quando si fanno e quando si passa avanti; le altre
pagine della cartella dicono come.

| Pagina | Per chi | Cosa c'è |
|---|---|---|
| [server-di-collaudo.md](./server-di-collaudo.md) | il sistemista di NPM2 | il server, la configurazione, il centro preparato, i servizi esterni nei loro ambienti di prova |
| [ruoli/](./ruoli/) | la squadra | una lista da spuntare per ogni ruolo, nell'ordine di una giornata |
| [segnalazioni.md](./segnalazioni.md) | tutti | come si segnala un problema, la gravità, dove si raccolgono |
| [centro-pilota.md](./centro-pilota.md) | NPM2 e il centro | il pilota accanto al vecchio programma, il passaggio alla produzione, il ritorno indietro |

## I tre livelli

| | 1 · Simulazione | 2 · Server di collaudo | 3 · Centro pilota |
|---|---|---|---|
| **Dove** | un sito vuoto sul banco di prova (il proprio computer o GitHub Actions) | `collaudo.dottorcloud.com`, un server di NPM2 | il sito del centro, quello che userà in produzione |
| **Chi** | nessuno: la macchina fa la squadra e le persone | la squadra di NPM2, ognuno un ruolo, sul computer e sul proprio telefono | la squadra del centro e i suoi pazienti veri |
| **I servizi esterni** | finti (lo Stripe finto, la posta che resta in coda) | veri, nei loro ambienti di prova: Stripe in modalità di prova, Itala di prova, Twilio, il numero di test di WhatsApp, la posta | veri; la fatturazione resta in prova fino alla decisione |
| **Quanto dura** | una corsa: la settimana del centro passa in circa un'ora | una settimana di lavoro (il calendario è sotto) | da 2 a 4 settimane |
| **Cosa prova** | che schermate, regole e lavori in coda stanno insieme per una settimana intera, su telefoni diversi | che le persone fanno la loro giornata e che i servizi esterni rispondono davvero | che un centro vero lavora meglio di prima, senza perdere niente |
| **Quando** | prima di ogni rilascio, prima di ogni giro del livello 2, dopo una modifica grande | prima del primo pilota, e prima di un rilascio che tocca un servizio esterno | una volta, prima di andare in produzione con il primo centro (e con il primo di un verticale nuovo) |

### 1 · La simulazione automatica

**Cos'è.** Un sito vuoto diventa un centro con `crm.collaudo.prepara.centro`: il
«Poliambulatorio San Luca», con due sedi (Milano e Monza), i loro ambulatori, la
squadra con i livelli e i turni, i servizi (una visita con l'acconto online, una
visita pagata per intero online, una visita online, le sedute di fisioterapia che
si vendono a cicli, il dentista, il Pilates di gruppo), un fondo sanitario in forma
diretta, gli abbonamenti, l'azienda che emette **in prova**, promemoria, solleciti,
area, lista d'attesa e prenotazione online accesi. Poi la suite di
`e2e/simulazione/` (Playwright) recita una settimana, da lunedì a sabato: la
squadra e dodici persone (una mamma con il figlio) passano dalle schermate vere, su
telefoni diversi (piccolo, girato di lato, con il testo grande, al buio). L'orologio
del banco va avanti da solo (`crm.collaudo.tempo`): una settimana passa in circa
un'ora, e i lavori pianificati girano all'ora che la settimana vuole. Le email che le
persone ricevono restano in coda e la suite le legge da lì (`crm.collaudo.api`).

I nomi del centro, dei servizi e della squadra sono quelli che `prepara.centro`
scrive oggi (`crm/collaudo/regole.py`): se cambiano lì, valgono quelli.

**Le due protezioni.** Ogni chiamata di `crm/collaudo` rifiuta un sito il cui
`site_config.json` non dice `"dottorcloud_collaudo": 1`, e la fa solo l'agenzia
(System Manager). `prepara.centro` rifiuta un sito che ha già persone non della
simulazione (un indirizzo fuori da example.com) o i dati di prova. **Mai
`dottorcloud_collaudo` sul sito di un centro.**

**Non sono dati di prova.** I record della simulazione non sono quelli del doc 53:
passano dalle strade vere, guardie comprese. Per questo la simulazione usa solo
indirizzi a example.com, che non riceve posta, e numeri di una serie che nessun
operatore assegna.

**Come si fa girare sul proprio computer.**

> La suite si sta scrivendo (10/10/2026). Il comando che lancia la suite e i nomi
> dei file del rapporto si completano qui quando `e2e/simulazione/` entra nel ramo.

1. Un bench con un sito **vuoto** e l'app installata, come dice il README del
   repository («Sviluppo»).
2. Il sito diventa un banco di prova:
   `bench --site <sito> set-config -p dottorcloud_collaudo 1`
3. Il centro, con i servizi finti:
   `bench --site <sito> execute crm.collaudo.prepara.centro --kwargs '{"servizi_finti": 1}'`.
   Con `servizi_finti: 1` Stripe è quello finto (`stripe_api` nel `site_config.json`
   del sito, collegato come il centro collega il suo), la posta resta in coda, le
   stanze delle visite online sono su un indirizzo di example.com. Il comando
   risponde con la squadra, la sua password e i problemi: **una lista vuota vuol dire
   che il centro sta in piedi**.
4. `bench start`, poi la suite di `e2e/simulazione/` con Playwright (come i test UI:
   `npx playwright install chromium`, l'indirizzo del sito in `BASE_URL`). Il
   comando esatto: *da completare*.

**Come si fa girare da GitHub.** Actions › **Simulazione** › Run workflow, si
sceglie il ramo da provare, Run. Come gli altri controlli (05/10/2026), non parte da
solo: si lancia a mano quando serve.

**Cosa dice il rapporto.** Si scarica dagli artefatti della corsa:

- la settimana passo per passo, per giorno e per ruolo: riuscito o no;
- di un passo non riuscito, la schermata, il video e la traccia di Playwright (come
  fanno già i test UI);
- gli errori che il server ha scritto nel registro durante la corsa;
- le email e gli SMS che ogni persona ha ricevuto, con i loro link;
- la fotografia del centro preparato e i suoi problemi.

**Criteri d'uscita del livello 1.**

- [ ] La simulazione è verde sul ramo del rilascio, due corse di fila (una sola
      verde può essere fortuna).
- [ ] Nessun errore nuovo nel registro del server durante la corsa.
- [ ] Quello che il CI direbbe è verde sul ramo (AGENTS.md, «Tests»): `yarn test:run`,
      la build, i test del server dei moduli toccati.
- [ ] Nessuna segnalazione di gravità «Bloccante» o «Grave» aperta con l'etichetta
      `collaudo` ([segnalazioni.md](./segnalazioni.md)).

### 2 · Il server di collaudo

**Cos'è.** Un server di NPM2 con un sito solo, `collaudo.dottorcloud.com`,
preparato con lo stesso `prepara.centro` ma con **la squadra vera** (un file con le
email dei colleghi) e **senza servizi finti**: Stripe, Itala, Twilio, WhatsApp, la
posta, il video e l'archivio si collegano dalle schermate di DottorCloud, ognuno nel
suo ambiente di prova. I colleghi fanno i ruoli del centro sul computer e sul
proprio telefono, e alcuni fanno i pazienti. Come si prepara:
[server-di-collaudo.md](./server-di-collaudo.md). Cosa fa ognuno:
[ruoli/](./ruoli/).

**Il calendario di una settimana.** I promemoria partono prima dell'appuntamento e le
risposte arrivano dopo: la giornata del centro ha bisogno del giorno prima.

| Giorno | Chi | Cosa |
|---|---|---|
| 0 | sistemista, responsabile | il server, il centro preparato, i servizi esterni collegati; il responsabile rilegge le impostazioni ([responsabile.md](./ruoli/responsabile.md)) |
| 1 | pazienti, genitore, segreteria | le prenotazioni online con l'acconto, le persone nuove al telefono, gli inviti all'area, i moduli mandati a casa, il dentista propone un preventivo |
| 2 | tutti | la giornata del centro: promemoria e risposte, arrivi, visite firmate, fatture di prova, la cassa |
| 3 | tutti | il seguito: piani spuntati nell'area, preventivo firmato, abbonamento comprato, lista d'attesa, disdette, la convenzione del mese |
| 4 | tutti | le liste dei ruoli rifatte sul telefono; quello che non è riuscito, rifatto |
| 5 | tutti, 1 ora | il riepilogo: le segnalazioni una per una, la decisione |

Ogni giorno, dieci minuti alla stessa ora: cosa non è andato ieri, cosa blocca oggi.

**Criteri d'uscita del livello 2.**

- [ ] Ogni lista dei ruoli è stata fatta tutta almeno una volta: ogni casella
      spuntata, o una segnalazione per quella che non è andata.
- [ ] Ogni ruolo ha fatto almeno metà della sua lista **sul telefono**, con almeno un
      iPhone e un Android nella squadra.
- [ ] Zero segnalazioni «Bloccante» o «Grave» aperte; ognuna delle «Media» ha una
      decisione (si corregge prima del pilota, o si accetta e si dice al centro).
- [ ] Ogni servizio esterno ha fatto i suoi casi:
  - Stripe: un acconto pagato, una carta rifiutata, una che chiede 3-D Secure, un
    acconto restituito dalla disdetta, un abbonamento comprato dall'area, un
    addebito mensile riuscito e uno non riuscito;
  - Itala di prova: una fattura elettronica di prova partita, il suo stato cambiato,
    una fattura di un fornitore ricevuta;
  - Sistema TS: il controllo all'emissione («Prova: controllata, non inviata»);
  - Twilio: un SMS in uscita, una risposta, uno STOP, una chiamata in entrata e una in
    uscita dal browser, una chiamata persa con il messaggio in segreteria;
  - WhatsApp: un promemoria con i pulsanti e la risposta che arriva in agenda;
  - posta: un codice dell'area, un promemoria, una risposta che arriva sulla
    persona;
  - video: una visita online, il paziente dall'area e il professionista
    dall'agenda;
  - archivio: un file privato archiviato dopo un'ora e riaperto.
- [ ] Nessun messaggio (email, SMS, WhatsApp, chiamata) è arrivato a qualcuno fuori
      dalla squadra: lo dicono i registri del servizio di invio e di Twilio.
- [ ] L'esportazione dei dati del centro e l'importazione di un foglio di prova
      riescono (Impostazioni › Il centro › I tuoi dati).

### 3 · Il centro pilota

**Cos'è.** Un centro vero lavora con DottorCloud per 2–4 settimane, con il vecchio
programma accanto: l'agenda, i promemoria, l'area e i moduli per davvero dal primo
giorno, la fatturazione in prova finché non si decide di passare. Come si sceglie il
centro, cosa si firma, cosa si porta dal vecchio programma, cosa si guarda ogni
giorno, come si passa alla produzione e come si torna indietro:
[centro-pilota.md](./centro-pilota.md).

**Criteri d'uscita del livello 3.**

- [ ] Due settimane di fila senza una segnalazione «Bloccante», e nessuna «Grave»
      aperta.
- [ ] La segreteria fa la sua giornata in DottorCloud senza tornare al vecchio
      programma, tranne che per le fatture.
- [ ] I numeri della [misura](./centro-pilota.md#cosa-si-misura) non sono peggiorati
      rispetto alla settimana prima del pilota (assenze, tempo allo sportello).
- [ ] Il responsabile e il direttore sanitario del centro dicono sì alla riunione
      settimanale.
- [ ] La lista qui sotto è tutta spuntata.

## La lista per andare in produzione

Si rilegge alla riunione che decide, con il centro. Ogni riga ha chi la verifica.

**Carte e privacy**

- [ ] La nomina a responsabile del trattamento è firmata dal centro e da NPM2
      ([bozza](../../marchi/dottorcloud/legale/nomina-responsabile.md)) — NPM2.
- [ ] La DPIA è completata con la parte del centro e firmata
      ([bozza](../../marchi/dottorcloud/legale/dpia-cartella.md)) — il centro.
- [ ] Le condizioni di servizio sono accettate
      ([bozza](../../marchi/dottorcloud/legale/condizioni.md)) — il centro.
- [ ] I testi dei consensi e l'informativa sono quelli del centro, riletti dal suo
      DPO — il centro.
- [ ] Le bozze legali sono state riviste da un avvocato (le domande sono nel
      [README dei documenti legali](../../marchi/dottorcloud/legale/README.md)) — NPM2.

**Il sito del centro**

- [ ] Il `site_config.json` non ha `dottorcloud_collaudo`, `stripe_api`,
      `sistema_ts_ambiente` né `sistema_ts_ca` — il sistemista.
- [ ] `host_name` è l'indirizzo del centro, con HTTPS — il sistemista.
- [ ] I backup partono, e un ripristino è stato provato su un altro server — il
      sistemista.
- [ ] L'archivio dei file usa la cartella di produzione (doc 57), non quella del
      collaudo — il sistemista.
- [ ] Il servizio di invio usa il dominio di produzione, con SPF, DKIM e DMARC
      (doc 51) — il sistemista.
- [ ] Ogni utente ha il suo livello, e gli utenti dell'agenzia non hanno livelli
      clinici — il responsabile e NPM2.
- [ ] Deciso se chiedere l'autenticazione a due fattori per i livelli clinici (la
      DPIA la segna «da fare») — il centro e NPM2.

**La fatturazione**

- [ ] «Prova e attivazione» non ha righe che bloccano — il responsabile.
- [ ] La numerazione è decisa con il commercialista (continuare quella del vecchio
      programma o una serie nuova) — il centro.
- [ ] La conservazione dell'Agenzia delle Entrate è attiva e spuntata; il codice
      destinatario di Itala è registrato e spuntato — il centro.
- [ ] Le credenziali del Sistema TS sono inserite e il certificato del kit è caricato
      — il centro e l'agenzia.
- [ ] Deciso il giorno del passaggio, e cosa fa il vecchio programma da quel giorno
      — il centro.

**I servizi esterni**

- [ ] Stripe: la chiave dal vivo è pronta, da collegare il giorno del passaggio —
      il responsabile.
- [ ] Il modello WhatsApp dei promemoria è approvato da Meta — il responsabile.
- [ ] I numeri Twilio del centro sono suoi, con i documenti approvati; un numero
      fisso per chiamare l'Italia (AGCOM, doc 52) — il responsabile.
- [ ] I promemoria del vecchio programma sono spenti (una persona riceve un
      promemoria solo) — il centro.

**Le persone**

- [ ] Ogni ruolo del centro ha fatto la sua lista di [ruoli/](./ruoli/) almeno una
      volta, sul suo sito — il centro.
- [ ] Il piano per tornare indietro è letto e approvato
      ([centro-pilota.md](./centro-pilota.md#tornare-indietro)) — il centro e NPM2.

## Da verificare

- Il comando che lancia la suite e i nomi degli artefatti del workflow
  «Simulazione»: si scrivono qui quando `e2e/simulazione/` è nel ramo.
- I numeri delle carte di prova di Stripe si ricontrollano sulla loro tabella
  ufficiale prima di ogni giro (sono in
  [server-di-collaudo.md](./server-di-collaudo.md#stripe-in-modalità-di-prova)).
