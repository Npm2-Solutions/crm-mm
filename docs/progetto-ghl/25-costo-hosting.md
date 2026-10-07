# 25 — Quanto costa tenerci i clienti sopra

> **Aggiornato il 07/10/2026** con i prezzi veri di Frappe Cloud e di Hetzner e
> la decisione proposta: [vai all'aggiornamento](#aggiornamento-del-07102026-i-prezzi-veri-frappe-cloud-o-hetzner-diretto).

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

> ✅ **Chiusa (07/10/2026).** Sul proprio server di Frappe Cloud i siti non si
> pagano a parte: se ne mettono quanti ne regge il server, senza costi in più
> (NPM2, dal pannello di Frappe Cloud). Si paga solo il server: 70 $ al mese il
> cpx32 condiviso (4 vCPU, 8 GB), 140 $ il cpx42, 170 $ il ccx23 dedicato; il
> taglio si cambia al volo.

## Aggiornamento del 07/10/2026: i prezzi veri, Frappe Cloud o Hetzner diretto

### Cosa costa Frappe Cloud

Dal pannello di Frappe Cloud («Change Plan» di un server nostro). Prezzi in
dollari al mese, disco da 80 GB in tutti; il taglio si cambia al volo.

**Condivisi** (vCPU condivise, Hetzner CPX) — per carichi bassi e medi:

| Server | vCPU | RAM | Al mese | Al giorno |
|---|---|---|---|---|
| cpx22 | 2 | 4 GB | 40 $ | 1,29 $ |
| **cpx32** | **4** | **8 GB** | **70 $** | 2,26 $ |
| cpx42 | 8 | 16 GB | 140 $ | 4,52 $ |
| cpx52 | 12 | 24 GB | 200 $ | 6,45 $ |
| cpx62 | 16 | 32 GB | 260 $ | 8,39 $ |

**Dedicati** (vCPU dedicate, Hetzner CCX) — per la produzione pesante:

| Server | vCPU | RAM | Al mese | Al giorno |
|---|---|---|---|---|
| ccx13 | 2 | 8 GB | 85 $ | 2,74 $ |
| ccx23 | 4 | 16 GB | 170 $ | 5,48 $ |
| ccx33 | 8 | 32 GB | 280 $ | 9,03 $ |
| ccx43 | 16 | 64 GB | 550 $ | 17,74 $ |
| ccx53 | 32 | 128 GB | 1.070 $ | 34,52 $ |
| ccx63 | 48 | 192 GB | 1.700 $ | 54,84 $ |

**I siti non si pagano a parte:** sul proprio server se ne mettono quanti ne
regge, senza costi in più (verificato da NPM2 sul pannello, 07/10/2026). La voce
aperta più sotto è chiusa.

### Cosa costa Hetzner diretto

Hetzner ha alzato i prezzi due volte nel 2026, ad aprile e il 15 giugno
(CPX e CCX fino a +176%). Prezzi dopo giugno, IVA e IPv4 esclusi, dagli articoli
che li riportano: vanno confermati sul sito di Hetzner prima di decidere.

| Server | Hetzner diretto | Frappe Cloud | Differenza al mese |
|---|---|---|---|
| cpx32 (4 vCPU, 8 GB) | ~36 € | 70 $ (~60 €) | ~25 € |
| cpx42 (8 vCPU, 16 GB) | ~93 € | 140 $ (~120 €) | ~25 € |
| ccx23 (4 vCPU dedicate, 16 GB) | ~86 € | 170 $ (~145 €) | ~60 € |
| ccx33 (8 vCPU dedicate, 32 GB) | ~138 € | 280 $ (~240 €) | ~100 € |

Il cambio dollaro/euro è approssimato. Un dedicato fisico (AX42) è passato da
~68 € a ~187 € al mese.

### Quanti centri per server

Il conto qui sotto (22/09) dava 25–30 siti a un server da 4 vCPU e 8 GB. Da
allora lo scheduler è cresciuto: oggi `crm/hooks.py` chiede per sito un job ogni
minuto, uno ogni 2, quattro ogni 10, uno ogni 5 e due ogni 15, cioè **~2,3 job al
minuto per sito** (erano ~1,6), più 9 orari e 12 giornalieri. Stima prudente:
**15–20 centri su un cpx32**, da misurare con i primi centri veri. Il disco da
80 GB basta a lungo, perché i file privati vanno nel bucket (doc 57) e sul
server resta il database.

### Quanto pesa su un centro

| Server | Centri | Costo a centro al mese | Sul piano più piccolo (59 €) |
|---|---|---|---|
| cpx32, 70 $ | 15–20 | ~3–4 € | ~6% |
| cpx42, 140 $ | 30–40 | ~3–4 € | ~6% |
| ccx23, 170 $ | 30–40 | ~4–5 € | ~8% |

Con i centri fondatori (Professionista a ~34 € al mese) l'hosting resta sotto il
15%. **Il server non è la voce che decide il prezzo:** decidono l'assistenza e
l'avvio.

### Frappe Cloud o Hetzner diretto

| | Frappe Cloud | Hetzner diretto |
|---|---|---|
| Costo del server | 1,3–2 volte Hetzner | il prezzo di Hetzner |
| Siti | illimitati sul proprio server | illimitati |
| Backup, aggiornamenti, certificati, monitoraggio | compresi | da fare noi |
| Cambio taglio | al volo dal pannello | a mano, con un riavvio |
| Assistenza sul framework | sì | no |
| Chi tocca i dati | Frappe Technologies (India) sui server Hetzner in Germania | solo NPM2 e Hetzner (Germania) |
| Contratto per il trattamento | da chiedere, con le clausole tipo per l'India | Hetzner lo firma nella Console |
| Tempo di NPM2 | quasi niente | qualche ora al mese, più la reperibilità |

**Decisione proposta:** si parte su **Frappe Cloud con un cpx32 condiviso**
(70 $ al mese) per il lancio e i centri fondatori; si sale di taglio dal pannello
quando serve. Si passa a **Hetzner diretto** quando succede una di queste cose:

1. il legale dice che l'accesso dall'India è un trasferimento che le clausole
   tipo non coprono ([domanda 3](../gestionale-medico/legale/README.md#le-domande-per-il-legale));
2. i centri superano 30–40, e la differenza di costo diventa centinaia di euro;
3. NPM2 ha chi gestisce i server.

Il trasloco è semplice: i file sono già nel nostro bucket, e ogni centro si porta
via tutto con l'esportazione (Impostazioni > Il centro > I tuoi dati) o con un
backup del sito. **Press**, il software di Frappe Cloud, non si installa per
conto nostro: è fatto per chi rivende hosting e chiede una persona dedicata; per
decine di centri basta un bench con i siti e qualche script.

### Da chiedere a Frappe Cloud

1. Il contratto per il trattamento dei dati (art. 28) con le clausole tipo per
   l'India; chi del loro personale accede ai server, da dove, e se resta scritto.
2. I backup: ogni quanto, per quanto tempo, cifrati o no, dove stanno, e se si
   possono mandare anche nel nostro bucket.
3. Il ripristino: in quanto tempo, e se si può provare.

Le risposte chiudono i «da verificare» della
[nomina](../gestionale-medico/legale/nomina-responsabile.md) e della
[DPIA](../gestionale-medico/legale/dpia-cartella.md).

### Fonti dell'aggiornamento

- il pannello di Frappe Cloud di NPM2 (prezzi dei server, siti senza costi in
  più), 07/10/2026
- [privatedevops, l'aumento di giugno 2026](https://privatedevops.com/news/hetzner-june-2026-cloud-price-increase-what-to-do)
- [wz-it, CPX e CCX fino a +176%](https://wz-it.com/en/blog/hetzner-price-increase-june-2026-cpx-ccx-alternatives/)
- [deskmodder, gli aumenti di aprile e giugno](https://www.deskmodder.de/blog/?p=213645)
- [Frappe, self-hosted o Frappe Cloud](https://docs.frappe.io/customer-guide/getting-started/self-hosted-vs-frappe-cloud.md)

## Il conto (22/09/2026)

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
