# 64 · Il centro pilota

## A cosa serve

Il livello 3 del collaudo ([README](./README.md)): un centro vero lavora con
DottorCloud per 2–4 settimane, con il suo vecchio programma accanto. L'agenda, i
promemoria, l'area dei pazienti e i moduli vanno per davvero dal primo giorno; la
fatturazione resta in prova finché non si decide di passare, e le fatture vere le fa
ancora il vecchio programma. Questa pagina dice come si sceglie il centro, cosa si
firma prima, cosa si porta dal vecchio programma, cosa va per davvero e cosa no, cosa
si guarda ogni giorno e ogni settimana, cosa si misura, come si passa alla
produzione e come si torna indietro.

## Scegliere il centro

| Cosa | Perché |
|---|---|
| Un centro medico privato con 2–6 professionisti, una segreteria, una o due sedi | abbastanza lavoro per vedere tutto, abbastanza piccolo da seguirlo ogni giorno |
| Un responsabile e un direttore sanitario che hanno tempo: dieci minuti al giorno, un'ora alla settimana | senza di loro le decisioni aspettano |
| Il vecchio programma esporta persone e appuntamenti in Excel o CSV | è la strada per portarli (sotto) |
| Un periodo normale: non agosto, non dicembre, non un trasloco | le assenze e i tempi si confrontano con una settimana normale |
| Internet stabile allo sportello, un tablet per i moduli | la giornata della segreteria passa da lì |
| Se fattura con Fatture in Cloud, si sa dal primo giorno | il passaggio della fatturazione è un altro (doc 58) |
| Se riceve prenotazioni da piattaforme (MioDottore…), si decide se collegarle | nel pilota si può lasciarle al vecchio programma |

## Le carte e la privacy, prima di tutto

Nessun dato di una persona vera entra in DottorCloud prima di queste righe.

1. **Le condizioni** del pilota e del servizio, accettate dal centro
   ([bozza](../../marchi/dottorcloud/legale/condizioni.md)): quanto dura il pilota,
   cosa succede alla fine, come si esce.
2. **La nomina a responsabile del trattamento** (art. 28 GDPR), firmata dal centro e
   da NPM2 ([bozza](../../marchi/dottorcloud/legale/nomina-responsabile.md)), con i
   sotto-responsabili di NPM2 e i fornitori che il centro contratta da sé (Twilio,
   Meta, Stripe).
3. **La DPIA** della cartella: NPM2 la prepara, il centro completa la sua parte e la
   firma ([bozza](../../marchi/dottorcloud/legale/dpia-cartella.md)).
4. **L'informativa e i consensi** del centro, riletti dal suo DPO: sono i moduli che
   i pazienti firmeranno dal primo giorno.
5. **Gli utenti dell'agenzia** sul sito del centro non hanno livelli clinici.
6. **Una violazione dei dati** (un messaggio alla persona sbagliata, un accesso che
   non doveva esserci) si dice subito al centro, che ha 72 ore per il Garante (art. 33
   GDPR): la procedura è nella nomina.

Le bozze legali vanno riviste da un avvocato prima di usarle: le domande aperte sono
nel [README dei documenti legali](../../marchi/dottorcloud/legale/README.md).

## Il sito del centro

1. Un sito nuovo dove gira la produzione (doc 25), **non** il server di collaudo:
   senza `dottorcloud_collaudo`, `stripe_api`, `sistema_ts_ambiente`.
2. La prima apertura (doc 37): la lingua, il nome del centro, il fuso orario; niente
   dati di prova.
3. Il responsabile del centro, con NPM2 accanto, fa le impostazioni della sua lista
   ([responsabile.md](./ruoli/responsabile.md)) sul suo sito: sedi, ambulatori,
   servizi e prezzi, turni e festività, utenti con i loro livelli, promemoria, area,
   lista d'attesa, prenotazione online, moduli e consensi, l'azienda che emette
   (in prova).
4. I canali del centro, con i suoi account: Twilio (doc 52), WhatsApp con il suo
   numero e il QR (doc 12), il modello dei promemoria approvato da Meta (doc 59), la
   casella della segreteria (doc 51).
5. **Stripe resta scollegato** fino al passaggio, oppure solo con la chiave di prova:
   un acconto vero pagato mentre la fatturazione è in prova farebbe una fattura
   d'acconto di prova, che il passaggio toglie, e i soldi resterebbero senza fattura.
   Niente acconti online, niente abbonamenti venduti dall'area, finché non si passa.

## Portare i dati dal vecchio programma

Impostazioni › Il centro › **I tuoi dati** (`persone.importa`), una sera, con il
centro chiuso.

1. **Le persone.** Il foglio del vecchio programma (Excel o CSV, così com'è esce):
   l'anteprima riconosce le colonne dai nomi che usano i programmi italiani («Cognome
   e nome», «Cellulare», «Codice fiscale», «Data di nascita»…), legge le date e i
   numeri come li scrive un foglio italiano, e dice riga per riga cosa non va.
   Importando, chi c'è già prende solo quello che mancava; chi è nuovo ha i suoi dati
   di fatturazione e le sue note; con la clinica, chi era un paziente lo è anche qui.
2. **Gli appuntamenti futuri** (e, se si vuole, la storia). Prima ci devono essere i
   servizi, gli utenti dei professionisti e gli ambulatori: l'anteprima chiede a cosa
   corrisponde ognuno di quelli del foglio (i professionisti si riconoscono dal nome,
   senza «Dott.»); un servizio che il centro non ha va su «Altro». Rifatto, non porta
   niente due volte. Un conflitto resta scritto sull'appuntamento.
3. **Il conto.** Dopo l'importazione, si confronta con il vecchio programma: quante
   persone, quanti appuntamenti per giorno nelle prossime due settimane.
4. **I promemoria.** Gli appuntamenti futuri importati hanno i promemoria di
   DottorCloud alla loro ora, se sono accesi: lo stesso giorno si spengono quelli del
   vecchio programma. Una persona riceve un promemoria solo.
5. **Quello che non si porta:** le cartelle cliniche (restano nel vecchio programma e
   si consultano lì; un documento che serve si carica a mano tra i Documenti della
   persona) e le fatture (sono fatti fiscali del vecchio programma e della sua
   conservazione).

## Cosa va per davvero, e cosa no

| Cosa | Nel pilota | Perché |
|---|---|---|
| Agenda e Accoglienza | **per davvero**: l'agenda vera è DottorCloud | una sola agenda; il vecchio programma solo se serve per fatturare (sotto) |
| Promemoria | **per davvero**, solo da DottorCloud | quelli del vecchio programma spenti |
| Prenotazione online (`/prenota`) | **per davvero**, senza pagamento online | il link sul sito del centro dalla seconda settimana |
| Area dei pazienti | **per davvero**: appuntamenti, moduli, documenti, piani, messaggi | le fatture non ci sono: sono di prova |
| Moduli e consensi | **per davvero** | un modulo firmato è un documento del centro, con le sue prove |
| Lista d'attesa | **per davvero** | |
| Conversazioni (WhatsApp, SMS, email) | **per davvero** | |
| Telefono | per davvero se il centro porta il suo numero; se no dopo | doc 52 |
| Cartella clinica | da decidere con il direttore sanitario: dal primo giorno per chi se la sente, o dopo il passaggio | una visita firmata resta, non si cancella |
| Convenzioni | **per davvero** le pratiche e le autorizzazioni | la fattura al fondo la fa ancora il vecchio programma |
| Fatturazione | **in prova**: le fatture vere le fa il vecchio programma | si passa con la decisione (sotto) |
| Sistema TS e SdI | dal vecchio programma | una fattura di prova non va da nessuna parte |
| Pagamenti online | **spenti** | vedi «Il sito del centro» |
| Solleciti | spenti | una fattura di prova non si sollecita |
| Automazioni del marketing | spente; si accendono dopo il passaggio, una alla volta | |

**Il vecchio programma e le fatture.** Se il vecchio programma fattura senza un
appuntamento, la segreteria fa lì solo le fatture (strada A). Se vuole
l'appuntamento, la segreteria lo scrive in tutti e due i posti (strada B), e si misura
quanto tempo costa. Si decide il primo giorno. Chi vuole, fa in DottorCloud anche la
fattura di prova di un giorno alla settimana, per confrontare i totali.

## Il controllo di ogni giorno: dieci minuti

**Prima**, NPM2 guarda: il registro degli errori del sito, gli ultimi promemoria
(quelli «non inviati» e «non arrivati»), i problemi di Twilio degli ultimi giorni, le
segnalazioni nuove.

**Con il centro**, alla stessa ora ogni giorno (in videochiamata o al telefono), con
la segreteria e chi può:

1. cosa non è andato ieri;
2. cosa blocca oggi;
3. le risposte ai promemoria e le assenze di ieri;
4. le segnalazioni aperte e la loro gravità ([segnalazioni.md](./segnalazioni.md));
5. una cosa che è andata meglio di prima.

Una riga nel registro del pilota, per ogni giorno: chi c'era, cosa si è deciso.

## La revisione di ogni settimana

Un'ora, con il responsabile, il direttore sanitario e la segreteria:

1. i numeri della settimana contro quelli della settimana prima del pilota (sotto);
2. le segnalazioni: chiuse, aperte, accettate così;
3. cosa si accende la settimana dopo (per esempio: settimana 2 i promemoria su
   WhatsApp e il link di `/prenota` sul sito; settimana 3 la cartella per tutti);
4. quanto manca alla lista per andare in produzione ([README](./README.md#la-lista-per-andare-in-produzione)).

## Cosa si misura

La settimana prima del pilota si misura con il vecchio programma: è il punto di
partenza.

| Cosa | Come | Si vuole |
|---|---|---|
| Assenze | appuntamenti segnati «Assente» sul totale, per settimana (la dashboard, e il vecchio programma prima) | non più di prima; meglio di prima con i promemoria |
| Conferme ai promemoria | i promemoria con «Ha confermato», sul totale (gli ultimi promemoria nelle impostazioni) | sempre più alta |
| Posti ridati | gli appuntamenti nati da un'offerta della lista d'attesa | più di zero |
| Tempo allo sportello | il cronometro su tre cose, cinque volte ciascuna: una visita prenotata al telefono; un arrivo con la sua fattura; una persona nuova con i suoi moduli | non più di prima dalla seconda settimana |
| Moduli firmati a casa | i moduli firmati dal link sul totale | sempre più alto |
| Persone nell'area | chi è entrato sul totale degli invitati | sempre più alto |
| Errori | le segnalazioni per gravità, per settimana | zero «Bloccante», sempre meno «Grave» |
| Doppio lavoro | i minuti al giorno per scrivere nel vecchio programma (strada B) | zero dopo il passaggio |

## Il passaggio alla produzione

Si passa quando la [lista per andare in produzione](./README.md#la-lista-per-andare-in-produzione)
è tutta spuntata e la revisione della settimana dice sì. Meglio il primo giorno di un
mese: il commercialista lo preferisce.

1. **La numerazione**, con il commercialista: si continua quella del vecchio
   programma (l'agenzia porta il contatore della serie all'ultimo numero usato: un
   contatore sale, non scende mai) o si comincia una serie nuova.
2. **Il centro**: ha aderito alla conservazione dell'Agenzia delle Entrate e l'ha
   spuntato; ha registrato il codice destinatario di Itala e l'ha spuntato; ha scritto
   le credenziali del Sistema TS. L'agenzia ha caricato il certificato del kit e
   scelto come arrivano le spese (doc 49).
3. **Il vecchio programma** fa l'ultima fattura vera il giorno prima, e la sua
   comunicazione al Sistema TS copre le sue fatture; dal giorno dopo non fattura più.
4. **«Attiva la fatturazione»**: il responsabile, in Impostazioni › Fatturazione ›
   Prova e attivazione. Le fatture di prova se ne vanno (e quello che le indicava: la
   rata di un abbonamento torna da fatturare); da quel momento ogni fattura è vera.
5. **Le prime fatture vere, una per una:** la prima sanitaria si comunica a mano al
   Sistema TS («Comunica») e si guarda il protocollo; la prima elettronica (al fondo, a
   un'azienda) parte con «Invia allo SdI» e si aspetta «consegnata». Poi, se il centro
   vuole, l'invio automatico (Impostazioni › Fatturazione › Avanzate › Opzioni).
6. **Stripe:** in Pagamenti online, «Scollega» la chiave di prova se c'era, incolla
   la chiave dal vivo (`sk_live_…`, o una `rk_live_…` con i permessi del doc 60),
   «Collega Stripe»; poi gli acconti sui servizi, la vendita dall'area e l'addebito
   mensile, come si è deciso. Nessuna prova finta dal vivo: ogni pagamento fa una
   fattura vera. Le prime le guardiamo una per una.
7. **Fatture in Cloud**, solo per un centro che fattura lì: collegato, e
   l'interruttore acceso quando non manca più niente (doc 58).
8. **Solleciti e automazioni**: si accendono uno alla volta, riletti con il centro.

## Tornare indietro

**Quando:** una segnalazione «Bloccante» sull'agenda, sui promemoria o sui dati che
non si corregge entro un giorno di lavoro; una violazione dei dati; il centro lo
chiede.

**Prima del passaggio** (la fatturazione è ancora in prova, quindi non c'è niente di
fiscale da disfare):

1. Si decide con il responsabile e lo si dice a tutta la squadra del centro.
2. **L'agenda** torna al vecchio programma: gli appuntamenti futuri si prendono
   dall'esportazione di DottorCloud (Impostazioni › Il centro › I tuoi dati, un foglio
   per tipo) e si portano nel vecchio programma; da quel momento si prenota solo lì.
3. **I promemoria** di DottorCloud si spengono (Impostazioni › Agenda › Agenda e
   promemoria › Promemoria degli appuntamenti) e quelli del vecchio programma si
   riaccendono, lo stesso giorno.
4. **La prenotazione online** di DottorCloud si spegne, e il sito del centro torna a
   puntare alla sua pagina di prima.
5. **L'area**: un messaggio sulla bacheca di chi ce l'ha, poi, se si decide, «Chiudi
   l'accesso».
6. **I moduli firmati e i referti** restano documenti del centro: l'esportazione glieli
   dà, e il centro li tiene nel suo archivio.
7. **I numeri:** Twilio è un account del centro, e i suoi numeri restano suoi; il
   numero WhatsApp collegato con il QR continua a funzionare nell'app sul telefono.
8. **I dati:** come dice la nomina alla fine del servizio: l'esportazione completa al
   centro, poi la cancellazione del sito nel termine concordato.

**Dopo il passaggio**, in più:

- le fatture vere fatte in DottorCloud restano: la loro numerazione è un fatto
  fiscale, e tornare in prova si può solo senza fatture vere. Il vecchio programma
  riprende dal numero dopo, con il commercialista;
- quello che DottorCloud ha già comunicato al Sistema TS e allo SdI resta comunicato;
- Stripe si scollega; un posto tenuto in attesa di un pagamento si libera quando il
  link scade;
- l'azienda resta registrata presso Itala finché l'agenzia non la toglie («Togli da
  Itala», doc 49).
