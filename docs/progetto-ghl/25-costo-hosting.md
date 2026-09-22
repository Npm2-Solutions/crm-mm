# 25 — Quanto costa tenerci i clienti sopra

> Stima del 22/09/2026, per un modello a **un server condiviso fra tutti i
> siti** — non un piano per sito. Sito tipo: un centro medico con ~10 utenze,
> di cui ~3 che ci lavorano davvero (due amministrativi e una segretaria tutto
> il giorno) e il resto che apre il calendario due volte al giorno.

## La risposta in due righe

Il piano piu' economico di Frappe Cloud che regge questo modello e' **Hetzner
unified, $40/mese (≈€37): 2 vCPU, 4 GB RAM, 80 GB disco**. Ci stanno
**8–12 siti**; pianifica su **10**, cioe' **~$4 per sito al mese**.

Se prevedi di superare gli otto clienti entro qualche mese, parti direttamente
dal taglio sopra (4 vCPU / 8 GB): regge **25–30 siti**, il costo per sito
scende a ~$2,7 e ti risparmi una migrazione.

## Cosa si paga davvero

Tre cose verificate leggendo il codice di Frappe Cloud (`press`), perche'
cambiano il conto e non sono ovvie dalla pagina dei prezzi.

**Un server unified si paga una volta sola.** App e database stanno sulla
stessa macchina. Nel codice, `create_unified_server` fa
`server.plan = database_server.plan = plan.name` e il controllo di spesa guarda
solo `app_plan.price_usd`: un piano, una fattura. Se invece prendi app e
database separati sono **due** piani, quindi il doppio.

**Il proxy non si paga a parte.** `new_unified` pesca un proxy gia' attivo e
condiviso nella region, non ne crea uno tuo.

**Ogni sito ha comunque bisogno di un piano sito**, ma di una classe a parte:
nel codice esiste il flag `dedicated_server_plan`, e un sito su server dedicato
viene **rifiutato** se gli assegni un piano normale
(`if on_dedicated_server and not plan.dedicated_server_plan: throw`). Questi
piani esistono e sono economici, ma **il loro prezzo non e' pubblicato** e non
sono riuscito a trovarlo.

> **L'unica voce aperta del preventivo.** Da chiedere a Frappe Cloud prima di
> firmare: *quanto costa un site plan per siti ospitati su un server dedicato?*
> Tutto il resto di questo documento e' verificato; questo no.

## Il conto

| Piano server | Siti realistici | $/sito/mese |
|---|---|---|
| **$40** — Hetzner, 2 vCPU / 4 GB / 80 GB | **8–12** | ~$4 |
| **~$70–80** — 4 vCPU / 8 GB | **25–30** | ~$2,7 |
| DigitalOcean, stesso taglio del primo | 8–12 | $60 → ~$6 |
| AWS, stesso taglio | 8–12 | $125 → ~$12 |

Hetzner sta in Germania (Norimberga, Falkenstein): per clienti italiani e' anche
la scelta giusta per latenza e per dove stanno i dati.

## Perche' 10 e non 30

**Il vincolo e' la RAM, non la CPU.** Su 4 GB: MariaDB prende ~1–1,5 GB, fra
sistema, agent, nginx e i tre Redis se ne vanno ~0,6 GB, e restano ~2 GB per i
processi Python, che stanno a 150–250 MB l'uno. Sono **8–10 processi in tutto**:
una bench con due worker web e tre di background, senza margine.

**La buona notizia: i worker sono per bench, non per sito.** Dieci siti
condividono gli stessi processi, quindi la RAM non cresce in proporzione ai
siti. Cresce quello che ogni sito porta con se': il working set del database, un
`init + connect` al minuto per lo scheduler, e i job di background.

**Gli utenti che pesano sono tre per sito, non dieci.** I professionisti che
aprono il calendario non spostano niente. Dieci siti fanno ~30 utenti davvero
attivi: per 2 vCPU e' al limite, non oltre — con la riserva che le viste a lista
e il calendario sono le pagine piu' pesanti che abbiamo.

**Il disco non e' il problema, all'inizio.** Un sito nuovo sta in ~0,5 GB; dopo
un anno con storico WhatsApp, registrazioni delle chiamate e allegati dei lead,
1,5–3 GB per sito e' realistico. Su 80 GB dieci siti stanno larghi; a trenta
diventa stretto e contano le impostazioni dei binlog di MariaDB.

## Il dettaglio che pesa piu' del server

Frappe **salta** i job dei siti dormienti. Ma `is_dormant` richiede che
*nessun utente* sia attivo da N giorni, e con una segretaria che lavora tutto il
giorno **nessuno dei nostri siti sara' mai dormiente**. Ogni sito paga il suo
scheduler intero, tutti i giorni.

E il nostro `hooks.py` chiede questo, **per sito**:

```
* * * * *      process_due_enrollments      ← ogni minuto
*/2 * * * *    process_due_posts            ← ogni 2 minuti
*/10 * * * *   catch_up_recent_leads        ← ogni 10 minuti
```

Fanno **~1,6 job al minuto per sito**, piu' gli orari e i giornalieri, piu' il
ciclo dello scheduler che itera i siti **in serie** ogni minuto.

| Siti | Job di background al minuto |
|---|---|
| 10 | ~16 |
| 20 | ~32 |
| 30 | ~48 |

Quel `* * * * *` e' il moltiplicatore piu' caro che abbiamo, e quasi sempre
risponde «niente da fare». `catch_up_recent_leads` invece si autospegne gia' da
solo quando il webhook funziona.

> **Rendere autoregolante anche quello delle automazioni taglierebbe circa il
> 60% del carico di background**, e il numero di siti per server salirebbe
> sensibilmente senza cambiare piano. Mezza giornata di lavoro, e vale piu' di
> un upgrade.

## Una cosa che non e' un costo

Un server solo vuol dire **tutti i clienti giu' insieme**. A $4 per sito, il
risparmio rispetto a due macchine da $40 e' ~€37 al mese: quando avrai quindici
centri medici che ci lavorano dentro tutto il giorno, due server piu' piccoli
invece di uno grande sono un'assicurazione che costa pochissimo.

## Fonti

- [Frappe Cloud — Servers](https://frappe.io/cloud/servers) — i tagli e i prezzi
  per provider, e la differenza fra unified e separati
- [Frappe Cloud — Pricing](https://docs.frappe.io/cloud/pricing)
- [Demystifying Frappe Cloud Pricing](https://frappecloud.com/blog/frappe-cloud/frappe-cloud-pricing)
- il codice di `press` (Frappe Cloud) per unified server, proxy condiviso e
  piani sito su server dedicato; il codice di `frappe` per la dormienza dello
  scheduler; il nostro `crm/hooks.py` per il carico per sito
