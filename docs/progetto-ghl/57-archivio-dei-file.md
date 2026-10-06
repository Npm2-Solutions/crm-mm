# 57 — L'archivio dei file: 1–2 TB per centro, su Hetzner

> 06/10/2026. Il codice è in `crm/archivio`; i conti in
> [25 — Quanto costa tenerci i clienti sopra](./25-costo-hosting.md).

## La risposta in due righe

I file privati di un centro (moduli firmati, referti, documenti, allegati delle
conversazioni) dopo un'ora vanno in un **bucket S3 dell'agenzia** su Hetzner
Object Storage, una cartella per sito. Sul server resta un file vuoto con lo
stesso nome. Ogni centro ha **1 TB incluso**, **2 TB** da Poliambulatorio in su;
oltre non si blocca niente, la pagina avvisa all'80% e l'agenzia fattura lo
spazio in più.

## Perché fuori dal server

Sul disco di Frappe Cloud lo spazio in più costa **$0,2 al GB al mese** e non si
può più togliere: 1 TB fanno circa $200 al mese, per centro. Su Hetzner Object
Storage la base costa **€6,49 al mese** (da aprile 2026) e comprende 1 TB di
spazio e 1 TB di traffico in uscita; il resto si paga a consumo, nello stesso
ordine di grandezza. Le chiamate all'API sono gratis.

| Dove | 1 TB pieno al mese | 2 TB pieni al mese |
|---|---|---|
| Hetzner Object Storage (Germania, Finlandia) | ~€6,5 | ~€13 |
| Backblaze B2, regione UE | ~$7 | ~$14 |
| Cloudflare R2 | ~$15 | ~$30 |
| Disco di Frappe Cloud | ~$200 | ~$400 |

Un centro reale occupa **1,5–3 GB dopo un anno** (doc 25): dieci centri stanno
nella base da €6,49. Promettere 1–2 TB costa poco perché si paga quello che si
usa; quello che si paga davvero sono i centri che caricano video o immagini
diagnostiche, e per quelli c'è la soglia.

## Come funziona

- **Spostare.** Ogni ora (`hourly_long`) i file privati scritti da più di
  un'ora vanno nel bucket, al massimo 500 file o 20 GB per giro. La chiave è
  `<sito>/<sha256[:2]>/<sha256>/<nome>`: il contenuto riscritto allo stesso
  indirizzo è un altro oggetto. Il corpo è firmato con il suo SHA-256 (il bucket
  rifiuta un corpo arrivato diverso), poi si controlla la dimensione lì, si
  scrive `CRM Archived File` e solo allora il file sul server si svuota.
- **Il file vuoto resta**, perché il framework sceglie i nomi guardando il disco
  (`generate_file_name`) e riconosce i doppioni con `exists_on_disk()`: senza,
  un nuovo file prenderebbe il nome di uno archiviato.
- **Aprire.** `/private/files/…` di un file archiviato: lo stesso controllo del
  framework (`find_file_by_url`, il registro degli accessi), poi un link al
  bucket che dura **5 minuti**, `Cache-Control: private, no-store` e nessun
  referer. Un ospite o chi non può leggerlo lo respinge il framework, come
  sempre.
- **Leggere nel codice.** `File.get_content()`, le miniature, gli zip, un file
  reso pubblico: `crm.overrides.file` lo riporta sul server intero prima
  (impronta controllata), e un'ora dopo riparte senza essere rispedito.
- **Cancellare.** Tolto l'ultimo File con quell'indirizzo, l'oggetto se ne va
  dopo il commit; quello che una cancellazione dal database ha lasciato (i dati
  di prova) lo porta via `orfani()` la notte.
- **I file pubblici restano sul server**: logo, immagini del sito, esercizi.
  Li serve nginx dal disco.

Senza `dottorcloud_archivio` non si sposta niente e tutto funziona come prima.

## Lo spazio, nella pagina del piano

Impostazioni > Il centro > Funzionalità, «Spazio per i file»: quanto occupano i
file del centro (ogni indirizzo una volta) su quanto il piano include, con
l'avviso all'80% come i crediti SdI. L'agenzia legge anche quanto è già
nell'archivio, o che l'archivio è spento. Il piano (`CRM Plan.storage_gb`,
solo l'agenzia) può dire un'altra cifra.

## Impostare Hetzner (l'agenzia, una volta)

Hetzner non ha un'API per le credenziali S3 né per i bucket: il token della
Cloud API non serve. Si fa dalla Console:

1. **Progetto** «DottorCloud Archivio» in [Hetzner Console](https://console.hetzner.com).
2. **Object Storage > Create Bucket**: location **Falkenstein (fsn1)** o
   Nuremberg, nome `dottorcloud-archivio`, visibilità **Private**. Un bucket
   regge 100 TB e 50 milioni di oggetti, un progetto 100 bucket: cinquanta
   centri pieni a 2 TB stanno in un bucket; oltre, un secondo bucket per i siti
   nuovi (vedi sotto).
3. **Security > S3 Credentials > Generate credentials**: si copiano subito
   Access key e Secret key, Hetzner non le mostra più.
4. Nel `common_site_config.json` del bench (o nella Site Config di un sito):

   ```json
   "dottorcloud_archivio": {
     "endpoint": "https://fsn1.your-objectstorage.com",
     "region": "fsn1",
     "bucket": "dottorcloud-archivio",
     "access_key": "…",
     "secret_key": "…"
   }
   ```

   `prefix` (facoltativo) è la cartella del sito, il nome del sito se manca;
   `virtual_host: true` mette il bucket nel nome dell'host; `enabled: 0` lo
   spegne senza togliere le chiavi.
5. Una volta: `bench --site <un sito> execute crm.archivio.archivio.imposta_il_bucket`
   accende le **versioni** (un file cancellato per errore si ritrova) e il
   **CORS** in sola lettura (l'anteprima di un file di testo lo legge dal
   browser).
6. Hetzner > Object Storage > il bucket > **Lifecycle**: le versioni non
   correnti scadono dopo 30 giorni, o le versioni tengono tutto per sempre.

**Scalare.** Lo spazio cresce da solo, si paga a consumo. Un centro che va in
un bucket nuovo ha `dottorcloud_archivio` nella sua Site Config, che vince su
quella comune; i file già archiviati restano dove sono finché `riporta_tutto`
non li riporta (le chiavi non cambiano bucket da sole).

## I backup

I backup di Frappe Cloud con i file contengono i file **vuoti** degli archiviati:
il contenuto è nel bucket, protetto dalle versioni. Per uscire dall'archivio (un
sito che lascia l'agenzia, un altro fornitore):
`bench --site <sito> execute crm.archivio.archivio.riporta_tutto` riporta tutto
sul server, poi si toglie la configurazione.

## Dati sanitari

Il bucket è in Germania o Finlandia, privato; Hetzner firma il DPA (Art. 28 GDPR)
nella Console. Le chiavi stanno nella configurazione del bench, mai nel database
né nei log (un errore porta solo stato e codice S3). Il link al file dura cinque
minuti ed è per chi l'ha aperto dopo il controllo dei permessi; il registro
degli accessi lo scrive comunque. La cifratura lato client non c'è: renderebbe
impossibile il link diretto, e il browser dovrebbe passare dal server per ogni
file.

## Da decidere

- Il prezzo dello spazio oltre l'incluso: costa ~€6,5 al TB al mese, il listino
  propone **10 € al TB al mese**.
- Un tetto oltre il quale i caricamenti a mano si fermano (oggi niente si
  blocca, come per i crediti SdI).

## Fonti

- [Hetzner Object Storage, prezzi dal 1° aprile 2026](https://bex.co/blog/2026/09/11/hetzner-object-storage-tenant-backup-backend)
- [Hetzner Docs, Object Storage](https://docs.hetzner.com/storage/object-storage/overview/) e
  [strumenti S3](https://docs.hetzner.com/storage/object-storage/getting-started/using-s3-api-tools/)
- [Frappe Cloud, Storage Addons](https://docs.frappe.io/cloud/storage-addons)
- AWS, Signature Version 4 per S3: gli esempi su cui sono provate le firme
  (`crm/archivio/tests/test_regole.py`)
