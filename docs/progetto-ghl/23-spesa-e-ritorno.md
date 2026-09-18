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

Questa e' la schermata che chiude quel buco: Settings → **Ad performance**.

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
