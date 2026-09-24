# Spesa e ritorno: il costo per cliente, non per lead

**Stato:** ✅ fatto (18/09/2026)

## Il numero che nessuno dei due sa da solo

Meta sa **quanto hai speso**. Il CRM sa **cosa si e' chiuso**. Nessuno dei due,
da solo, sa il numero che decide dove mettere il budget:

| | ce l'ha Meta | ce l'ha il CRM |
|---|---|---|
| Speso per inserzione | ✅ | ❌ |
| Lead arrivati | ✅ | ✅ |
| Costo per lead | ✅ | ❌ |
| Quali lead hanno comprato | ❌ | ✅ |
| **Costo per cliente acquisito** | ❌ | ❌ |

L'ultima riga e' vuota da entrambe le parti, ed e' l'unica che conta davvero,
perche' **l'inserzione con i lead piu' economici e' molto spesso quella con i
lead peggiori**. Chi guarda solo Gestione inserzioni sposta budget verso il costo
per lead piu' basso e a fine mese ha speso uguale e venduto meno.

Questa e' la schermata che chiude quel buco: Settings → Integrations → Meta → **Ad performance**.

## Come funziona

**Gli account pubblicitari si scelgono, non si indovinano.** "Trova i miei
account" chiede a Facebook (`/me/adaccounts`) quali account l'utente collegato
puo' leggere e li ricorda in `Facebook Ad Account`, **tutti spenti**. Un utente
di agenzia vede decine di account che non hanno niente a che fare con questo
CRM: la lista e' un'offerta, non una decisione. Riaggiornare la lista non
riaccende niente e non spegne niente — cambia solo i nomi.

**La spesa entra una volta al giorno**, per ogni account accesso:
`/act_.../insights` con `level=ad` e `time_increment=1`, cioe' una riga per
inserzione per giorno, in `Facebook Ad Insight`. Ogni riga si chiama
`{ad_id}-{data}`: rileggere un giorno lo **sovrascrive** invece di sommarlo due
volte. Si rileggono sempre gli ultimi 7 giorni, perche' Meta li ritocca (spesa
addebitata in ritardo, attribuzione che si assesta).

**I lead li contiamo noi.** Ogni lead porta `facebook_ad_id` (il codice
dell'inserzione, non il nome: i nomi cambiano). Contarli dal CRM invece di
leggere gli `actions` di Meta evita di indovinare quale dei suoi tipi di azione
significhi "ha compilato il modulo", e ci fa contare esattamente quello che
mostriamo.

**Il credito resta alla prima inserzione.** Se la stessa persona compila un
secondo modulo, il lead e' sempre suo e l'inserzione che lo ha portato resta la
prima — come il first touch. Altrimenti una seconda compilazione sposterebbe il
costo di un lead vecchio su un'inserzione nuova, e il report sarebbe sbagliato da
due parti contemporaneamente.

## Cose volute, non dimenticate

**Un'inserzione che spende e non porta lead deve comparire.** E' la riga piu'
importante del report, quindi le righe sono l'unione delle due parti, non un
join sui lead.

**Un costo senza niente da dividere resta vuoto, non zero.** "Costo per cliente:
0" si legge come *gratis*; la verita' e' *non ancora*.

**Due account in due valute non si sommano.** Il totale viene mostrato comunque
(la UI deve mostrare qualcosa) ma lo dice, e la valuta resta vuota: un numero
sicuro che non significa niente e' peggio di un numero mancante.

**Un account che fallisce non costa agli altri i loro numeri.** Ogni account
viene letto e salvato per conto suo, e l'errore finisce sulla scheda
dell'account, dove lo vede chi l'ha acceso.

## Il patch per i lead vecchi

`remember_which_ad_each_lead_came_from` riempie `facebook_ad_id` sui lead
importati prima che il campo esistesse, prendendolo da `first_touch_content` dove
c'era il codice nudo. Un lead il cui contenuto e' gia' un **nome** non si puo'
risolvere all'indietro: resta vuoto, perche' inventarlo sarebbe peggio.

## Quanto costa in chiamate

Una chiamata al giorno per account (piu' le pagine di risultati, se le
inserzioni sono molte). Con tre clienti sono tre chiamate al giorno: non e' un
modo per far salire un contatore, e' quello che serve. Il pulsante **"Leggi la
spesa adesso"** fa la stessa cosa fuori orario, in background.

**"Leggi 90 giorni"** serve la prima volta che si accende un account: il giro
giornaliero rilegge solo l'ultima settimana, quindi senza questo il report
partirebbe senza storia. Sono chiamate vere e utili — la storia serve per
confrontare i mesi — e sono anche quelle che fanno salire per davvero il
contatore delle chiamate Marketing API, senza inventarsi traffico finto.

## L'inserzione vera nella scheda del lead

Chi chiama un lead cinque minuti dopo che e' arrivato e' la persona per cui
questo conta piu' di tutti: sapere **cosa gli e' stato promesso** e' la
differenza tra *"salve, ha compilato un modulo"* e continuare la conversazione
che l'inserzione ha iniziato. Prima bisognava andare a cercarla in Gestione
inserzioni.

Nella tab Tracciamento del lead (e della trattativa) compare la scheda **"L'inserzione
che ha cliccato"**: titolo, testo, anteprima e il link per aprirla su Meta. Si
legge **quando qualcuno apre il lead**, non all'importazione, e si ricorda per
30 giorni: un'inserzione che nessuno guarda non costa niente, e la stessa
inserzione aperta cento volte costa una chiamata al mese.

Se Meta non risponde (nessun accesso all'account pubblicitario, inserzione
troppo vecchia) **la scheda semplicemente non c'e'**. Un lead vale piu' della
foto della sua inserzione. Anche l'immagine: i link della CDN di Meta scadono,
quindi se l'immagine non carica spariscere e' meglio di una cornice rotta — e
non ne teniamo una copia, perche' il creativo e' del cliente, non nostro.

## Quando un'inserzione smette di girare

Un'inserzione rifiutata da Meta smette di portare lead **senza dirlo a nessuno**:
il cliente lo scopre dal silenzio. Nello stesso giro giornaliero della spesa si
legge anche `effective_status` di tutte le inserzioni dell'account (una chiamata
per account: piu' economica e piu' utile che chiederlo inserzione per
inserzione).

Il risultato non finisce in un log ma in cima alla schermata, e solo se ha senso:
**si segnalano le inserzioni che hanno portato lead negli ultimi 30 giorni e che
adesso non stanno girando**. Un'inserzione vecchia in pausa e' archivio; una che
funzionava ieri ed e' stata rifiutata oggi e' soldi e lead che si fermano. Sulla
riga della tabella resta un'etichetta ("Rifiutata da Meta", "In pausa"), con le
parole di Meta tradotte in qualcosa su cui si puo' agire.

## Una nota sullo schema (18/09/2026)

La prima migrazione si e' fermata su `Length of thumbnail_url should be between
1 and 1000`: in Frappe un campo **Data** e' un varchar e lo schema rifiuta una
lunghezza oltre i 1000 caratteri. I link firmati della CDN di Meta possono
superarli, quindi `thumbnail_url` e `permalink` sono **Small Text** (colonna
TEXT): nessun limite, e su quei campi non si filtra e non si ordina mai.

Per non ripetere l'errore c'e' `crm/tests/test_doctype_schema.py`, che legge i
JSON di tutti i doctype dell'app e fallisce se un Data supera il varchar o se un
nome in `field_order` non ha un campo dietro. Sono controlli che costano tre
righe e che altrimenti si scoprono **a meta' di una migrazione, sul sito**.
