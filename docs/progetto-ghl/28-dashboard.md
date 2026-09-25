# La dashboard: un cruscotto per ogni parte del gestionale

**Stato:** ✅ fatto (24/09/2026)

## Il problema

La dashboard era quella di Frappe CRM: una pagina sola, per tutti, con i numeri
di lead e trattative. Intanto il gestionale e' diventato dieci cose — inbox con
WhatsApp, SMS ed email, telefono e dialer, agenda e prenotazioni online,
piattaforme esterne, tracciamento e inserzioni Meta, automazioni, social,
attivita' — e **nessuna di queste aveva un numero in dashboard**. Chi voleva
sapere quanti clienti aspettano una risposta, quante chiamate sono andate perse
o quanto costa un cliente acquisito doveva aprire tre schermate diverse.

Serviva anche il contrario: un sito senza telefonia non deve vedere un riquadro
"Chiamate perse: 0". Uno zero che non significa niente nasconde gli zeri che
significano qualcosa.

## Come funziona

**Un catalogo di widget per ogni modulo.** 166 widget in 16 categorie, ognuno
una funzione Python che risponde a una domanda precisa per il periodo scelto:

| Categoria | Widget | Qualche esempio |
|---|---|---|
| Vendite | 23 | Ricavo vinto, tasso di vittoria (in punti), pipeline ponderata, previsione per mese, imbuto, motivi di perdita |
| Fatturazione | 19 | Fatturato, fatture emesse, note di credito, cose da fare (da inviare, scartate dallo SdI o dal Sistema TS), appuntamenti da fatturare, fatturato per servizio, professionista e cliente, fatture dei fornitori |
| Persone | 8 | Nuove persone, da dove arrivano, clienti di ritorno |
| Conversazioni | 14 | In attesa di risposta, tempo di risposta, a che ora scrivono, conversazioni aperte per persona |
| WhatsApp | 10 | Ricevuti/inviati, tasso di lettura, non consegnati da rimandare, template inviati |
| SMS / Email | 4 + 3 | Volumi e risposte per canale |
| Telefono | 16 | Chiamate perse, tasso di risposta, tempo al telefono, richiamate dovute, esiti del dialer |
| Agenda | 18 | Appuntamenti di oggi, da confermare, no show e annullamenti, occupazione del team, ore di punta |
| Prenotazioni online | 5 | Prenotazioni dal sito e dalle piattaforme (MioDottore, Treatwell…) |
| Marketing | 9 | Visite, conversioni, fonti, link tracciati, form |
| Meta Ads | 11 | Spesa, costo per lead, **costo per cliente**, ROAS per inserzione, qualita' dei lead |
| Automazioni | 8 | Iscritti, passi eseguiti, errori |
| Social | 7 | Post pubblicati e programmati per piattaforma |
| Attivita' | 9 | Da fare oggi, scadute, completate |
| Squadra | 2 | Classifica e carico per persona |

Sette forme: numero (90), grafico a linee o barre (32), lista (20), ciambella
(11), tabella (9), mappa di calore giorno per ora (3), imbuto (1).

**Ogni widget dice di cosa ha bisogno** (`requires=("whatsapp",)`). Il sito sa
quali parti usa davvero (`crm/dashboard/features.py`: un flag o un `exists` a
testa, calcolati una volta per richiesta), e **la libreria offre prima quello a
cui il sito sa rispondere**. Il resto compare sotto, col lucchetto e il pulsante
"Configura WhatsApp" che apre la pagina giusta delle impostazioni.

**Dieci dashboard pronte**, una per modulo: Panoramica, La mia giornata, Vendite,
Fatturazione, Conversazioni, Agenda, Telefono, Marketing, Attivita', Squadra. Un modello e'
fatto di righe di widget, non di posizioni: viene impaginato per chi guarda,
con i soli widget a cui il suo sito e il suo ruolo sanno rispondere. Una
sezione vuota sparisce col suo titolo, una riga con dei buchi divide la
larghezza fra chi resta.

**Una dashboard fatta da un modello lo segue finche' nessuno la risistema.** Chi
collega WhatsApp trova la sezione WhatsApp sulle Conversazioni alla prossima
apertura, senza toccare niente. Salvata a mano diventa sua; "Torna al modello"
la riporta indietro. Salvare senza aver cambiato niente non la stacca.

## Il builder

"Modifica" apre la libreria accanto alla griglia (sopra, sugli schermi sotto i
~1400px, per non schiacciare i widget). Si cerca (gli accenti non contano), si
filtra per categoria, si aggiunge con un clic; poi si trascina, si ridimensiona,
si duplica, si rinomina, si imposta (pipeline, righe, misura) e si aggiungono
titoli di sezione e spazi vuoti. La griglia e' di 20 colonne; sul telefono i
widget si impilano in ordine di lettura, i numeri due per riga.

Dal menu: nuova dashboard (vuota o da un modello, solo per me o per il team),
impostazioni (nome, icona, periodo di apertura, **"solo il mio lavoro"** — la
dashboard personale in cui ogni widget conta solo chi la guarda), duplica,
elimina.

## Chi vede cosa

- Le dashboard **del team** le vedono tutti e le cambiano i manager; le
  **private** sono di chi le ha fatte, venditori compresi, e nessun altro le vede
  (permission query e `has_permission`, come per le notifiche).
- I 54 widget **da manager** (spesa pubblicitaria, carico della squadra, classifiche)
  non arrivano a un venditore, nemmeno nel catalogo.
- Il filtro "persona" segue la gerarchia (`crm/permissions/org_hierarchy.py`):
  un responsabile vede i suoi, un venditore solo se stesso.
- Un widget dice anche cosa conta: il team (default), solo chi guarda (`me`) o
  tutta l'azienda (`site`). Quando non e' quello che dicono i filtri della
  pagina, la scheda lo scrive: "Tutti", "Miei".

## I numeri

- **Ogni numero ha il suo confronto**: il periodo della stessa lunghezza che
  finisce il giorno prima. Il delta e' verde o rosso secondo se salire e' una
  buona notizia (le chiamate perse che salgono sono rosse), ed e' **in punti**
  per i tassi: da 50% a 60,5% e' "+10,5 pts", non "+21%".
- I 47 widget **"Adesso"** (in attesa di risposta, pipeline aperta, appuntamenti
  di oggi) non dipendono dal periodo e lo dicono con un badge.
- Importi convertiti nella valuta del CRM col cambio della trattativa, come
  faceva la dashboard di prima. Formati nella lingua di chi legge.
- Un widget che fallisce finisce nell'error log e torna come errore nella sua
  scheda; gli altri si caricano. Una risposta lenta per un periodo vecchio non
  sovrascrive quella nuova. La pagina si aggiorna da sola ogni cinque minuti
  se e' in vista.

## Colori e grafici

Le regole sono quelle della data visualization, non del gusto:

- **Una palette categoriale validata** (separazione per daltonismo e contrasto,
  tema chiaro e scuro, con lo script di validazione), assegnata in ordine fisso
  e mai ciclata.
- **Un colore segue la cosa, non il suo posto.** Uno stato noto tiene il suo slot
  per nome: gli appuntamenti completati sono verdi, i no show rosa, le chiamate
  perse rosse e tratteggiate — mai verdi perche' capitavano terze. Le
  combinazioni usate sono state validate una per una.
- Un asse solo per grafico: due misure di scala diversa vanno in due widget.
- Ciambelle con al massimo sei fette; la sesta e' "Altro", in grigio neutro.
- La mappa di calore usa una rampa sola, dal chiaro allo scuro; sul tema scuro
  si inverte, cosi' "poco" si confonde sempre con lo sfondo e "niente" resta
  neutro.
- Il testo non prende mai il colore di una serie; i tooltip escapano quello che
  arriva dai dati (il nome di una campagna lo scrive chiunque in un URL).

## La fatturazione

Quando il sito fattura (un'azienda emittente configurata, o documenti gia'
emessi) compaiono la dashboard **Fatturazione** e, nella Panoramica, una riga con
fatturato, cose da fare e appuntamenti da fatturare. E' tutto per i manager, come
la pagina Fatture, e conta lo studio intero: una fattura e' dello studio, non del
venditore che guarda.

- **Il fatturato e' l'imponibile** (`net_total`: niente IVA, bollo o cassa), o il
  totale del documento se il widget e' impostato cosi'. Le note di credito
  (TD04, TD08) tolgono il loro importo; autofatture e integrazioni (TD16-TD23,
  TD26-TD28) sono acquisti e restano fuori. Una fattura **scartata dallo SdI conta
  come non emessa** (Circolare 13/E del 2018) finche' non riparte.
- **Non c'e' "incassato" ne' "scaduto", ed e' voluto.** Il modulo registra quando
  una spesa sanitaria e' stata pagata, per il Sistema TS, e `payment_date` vale la
  data della fattura se nessuno la cambia: non registra se il cliente ha saldato.
  Un "da incassare" sarebbe un numero inventato.
- **Da fare** e' quello che elenca `crm.invoicing.api.pending_actions`: fatture
  emesse da inviare allo SdI o al Sistema TS, o rimandate indietro. Nella lista
  vengono prima gli scarti dello SdI, che hanno cinque giorni per ripartire.
- **Appuntamenti da fatturare**: quelli avvenuti negli ultimi giorni (30 di
  default, si cambia nelle impostazioni del widget) senza una fattura collegata,
  come la coda di `api.appointments_to_invoice`.
- **Fatturato per professionista** compare solo in un centro (piu' di un
  professionista attivo), **Sistema TS** solo in uno studio sanitario, **fatture dei
  fornitori** solo se il sito le riceve.
- Importi in euro, come ogni documento FatturaPA che il modulo scrive.

Le dashboard dei modelli nascono una volta, quando un sito non ne ha: la patch
`an_invoicing_dashboard` aggiunge la Fatturazione ai siti che hanno gia' le altre,
e soltanto quella, cosi' una dashboard cancellata apposta resta cancellata.

## Come si aggiunge un widget

```python
# crm/dashboard/widgets/whatsapp.py
@widget(
	"whatsapp_failed",
	category="whatsapp",
	kind="number",
	title=_lt("WhatsApp not delivered"),
	description=_lt("Messages Meta refused or could not deliver"),
	requires=WHATSAPP,
)
def whatsapp_failed(ctx: Context):
	now = outgoing_by_status(ctx).get(FAILED, 0)
	before = outgoing_by_status(ctx, True).get(FAILED, 0)
	return charts.number(now, before, negative_is_better=True, route=INBOX)
```

Il widget riceve un `Context` (periodo, periodo prima, persone da contare,
opzioni) e restituisce dati, mai istruzioni di disegno: `charts.number`,
`trend`, `bars`, `donut`, `funnel`, liste e tabelle (`crm/dashboard/charts.py`).
Il test `test_every_widget_answers_with_its_kind` lo esegue su MariaDB per il
team e per un venditore, e su un periodo vuoto: una colonna rinominata sotto un
widget fallisce li', per nome, invece che come riquadro bianco sulla dashboard
di qualcuno.

Gli id salvati dalla prima dashboard (`won_deals`, `sales_trend`,
`funnel_conversion`…) sono rimasti: un layout salvato un anno fa si apre coi
numeri nuovi.

## File

| File | Ruolo |
|---|---|
| `crm/dashboard/registry.py` | Il decoratore `@widget`, le opzioni, il catalogo |
| `crm/dashboard/context.py` | Periodo, periodo prima, chi si conta (gerarchia), opzioni pulite |
| `crm/dashboard/charts.py` | Le forme delle risposte — pure, testate con `unittest` |
| `crm/dashboard/features.py` | Quali parti del gestionale il sito usa |
| `crm/dashboard/templates.py` | Le dieci dashboard pronte, a righe |
| `crm/dashboard/layout.py` | Da righe a posizioni sulla griglia; pulizia dei layout salvati |
| `crm/dashboard/store.py` | Dashboard su disco: modelli che seguono il sito, permessi |
| `crm/dashboard/widgets/*.py` | I widget, un file per modulo |
| `crm/api/dashboard.py` | Elenco, layout, catalogo, dati di piu' widget in una richiesta, salvataggi |
| `crm/patches/v1_0/a_dashboard_for_every_module.py` | La "Manager Dashboard" diventa la Panoramica; nascono le altre |
| `crm/patches/v1_0/an_invoicing_dashboard.py` | La dashboard Fatturazione sui siti che hanno gia' le altre |
| `frontend/src/pages/Dashboard.vue` | La pagina: scelta, periodo, persona, modifica |
| `frontend/src/components/Dashboard/` | Griglia, libreria, dialoghi, cornice e le sette forme di widget |
| `frontend/src/utils/dashboard.js` | Periodi, formati, griglia, ricerca — puri, testati |
| `frontend/src/utils/dashboardCharts.js` | Palette e opzioni ECharts — pure, testate |

Test: `crm/tests/test_dashboard_widgets.py` (ogni widget su MariaDB, i KPI di
vendita su trattative note e quelli della fatturazione su documenti noti), `test_dashboard_layout.py` (pure),
`test_dashboard_store.py` (modelli e permessi), `frontend/tests/unit/dashboard.test.js`.

## Non incluso

- Le traduzioni italiane delle stringhe nuove (titoli e descrizioni dei widget,
  etichette del builder) non sono in `crm/locale/it.po`, come quelle degli altri
  moduli aggiunti da questo fork (agenda, dialer, automazioni, social…): il
  file arriva da Crowdin e copre solo Frappe CRM. Finche' non si traduce il fork
  intero, la dashboard parla inglese anche a chi ha l'italiano.
- Nessun widget definito dall'utente con query libere: il catalogo e' codice,
  rivisto e testato. Un report a scelta resta il lavoro delle viste salvate.
- Niente esportazione o invio programmato della dashboard via email.
- I colori per nome valgono per gli stati noti; le categorie libere (fonti,
  piattaforme, servizi) prendono ancora i colori in ordine di grandezza.
