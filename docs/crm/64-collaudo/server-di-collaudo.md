# 64 · Il server di collaudo

## A cosa serve

Questa pagina è per il sistemista di NPM2: dice passo per passo come si prepara il
server del livello 2 ([README](./README.md)), `collaudo.dottorcloud.com`. Un server
con un sito solo, il centro preparato da `crm.collaudo.prepara.centro` con la
squadra vera di NPM2, e i servizi esterni collegati dalle schermate di DottorCloud,
ognuno nel suo ambiente di prova: Stripe in modalità di prova, Itala di prova,
Twilio, il numero di test di WhatsApp, la posta, il video, l'archivio. Alla fine la
squadra apre le sue liste ([ruoli/](./ruoli/)) e comincia.

## Le regole che non si discutono

1. **Nessun dato di un paziente vero**, mai: le persone del collaudo sono i colleghi
   di NPM2 (con il loro consenso) e quelle a example.com.
2. **Le guardie dei dati di prova qui non valgono.** Le persone che la squadra crea
   non sono dati di prova (doc 53): un'email, un SMS, un WhatsApp, una chiamata
   partono davvero. Un indirizzo o un numero scritto a caso può essere di qualcuno:
   si scrivono solo quelli della squadra.
3. **Mai «Attiva la fatturazione»** sul sito di collaudo: l'azienda resta in prova,
   e le fatture vanno all'ambiente di prova di Itala. Attivata, una fattura
   elettronica partirebbe per lo SdI vero.
4. **Mai una chiave dal vivo** di Stripe (`sk_live_`, `rk_live_`), e mai `stripe_api`
   nella configurazione (manda DottorCloud allo Stripe finto della simulazione).
5. **`dottorcloud_collaudo` solo qui**, mai sul sito di un centro.
6. **La password della squadra non è quella del repository**: si sceglie con
   `dottorcloud_collaudo_password` (sotto), e ognuno la cambia al primo accesso.

## Quello che serve prima

| Cosa | Di chi | Dove si prende |
|---|---|---|
| Un server (VPS) in Europa | NPM2 | il fornitore che NPM2 usa (per esempio Hetzner) |
| Il nome `collaudo.dottorcloud.com` | NPM2 | il DNS di `dottorcloud.com` |
| L'accesso in lettura al repository | NPM2 | una chiave di deploy su GitHub |
| Il file della squadra (`team.json`) | il coordinatore del collaudo | le email dei colleghi, un ruolo ciascuno |
| Un account Stripe | NPM2 | ogni account ha la modalità di prova, anche prima di essere attivato |
| L'account Itala dell'agenzia | NPM2 | l'area riservata di Itala: le credenziali API (doc 49) |
| Un account Twilio attivato (non di prova) | NPM2 | la console di Twilio |
| L'app WhatsApp dell'agenzia e il suo numero di test | NPM2 | l'App Dashboard di Meta (doc 12) |
| Il servizio di invio delle email | NPM2 | lo stesso di produzione, con un mittente del collaudo (doc 51) |
| Un server Jitsi | NPM2 | il proprio, o `meet.jit.si` |
| Il bucket per i file | NPM2 | Hetzner Object Storage (doc 57) |
| Cinque telefoni della squadra per WhatsApp | la squadra | i telefoni di chi fa i pazienti |

## 1. Il server

- **Sistema:** Ubuntu LTS, il più recente che la versione di Frappe scelta supporta.
- **Risorse consigliate:** 4 vCPU, 8 GB di RAM, 80 GB di disco. La build del
  frontend è la parte che ne chiede di più; i file privati vanno nel bucket dopo
  un'ora, quindi il disco serve per il database, il codice e i backup.
- **Dove:** in Europa (Germania o Finlandia, come l'archivio).
- **Accesso:** solo con chiave SSH; un utente `frappe` che non è root; il firewall
  apre 22, 80 e 443.
- **I costi:** vedi il listino del fornitore.

## 2. Il nome e HTTPS

I servizi esterni chiamano il sito (Stripe e Twilio con i loro webhook, Meta tramite
l'hub dell'agenzia), i telefoni della squadra aprono i link delle email, l'area si
installa sulla schermata Home, le passkey e le notifiche sul telefono vogliono una
pagina sicura: serve un nome pubblico con HTTPS.

1. Nel DNS di `dottorcloud.com`: un record A `collaudo` verso l'indirizzo IPv4 del
   server (e AAAA se c'è IPv6).
2. Il certificato si fa dopo il bench, con Let's Encrypt (passo 3.7).
3. Il link di `/prenota` del collaudo non va mai sul sito di DottorCloud né in un
   post: lo usano solo i colleghi.

## 3. Il bench

Si segue il README del repository («Sviluppo») e la guida di installazione di
Frappe per la produzione.

1. Le dipendenze di sistema che chiede la versione di Frappe scelta (MariaDB, Redis,
   Node, Yarn, wkhtmltopdf…). **La versione di Frappe** è quella dei siti in
   produzione: il workflow Migration usa `develop` per il ramo `develop` e Python 3.14
   con Node 24. *Da verificare con chi gestisce la produzione, e da scrivere qui.*
2. Come utente `frappe`:

   ```bash
   pip install frappe-bench
   bench init --frappe-branch <ramo-di-frappe> frappe-bench
   cd frappe-bench
   ```

3. L'app, sul ramo da provare (il repository è privato: la chiave di deploy):

   ```bash
   bench get-app crm git@github.com:Npm2-Solutions/crm-mm.git --branch <ramo>
   ```

4. WhatsApp chiede l'app `frappe_whatsapp` (doc 12), la stessa versione dei siti in
   produzione:

   ```bash
   bench get-app frappe_whatsapp https://github.com/shridarpatil/frappe_whatsapp
   ```

5. Il sito ha il nome del dominio:

   ```bash
   bench new-site collaudo.dottorcloud.com
   bench --site collaudo.dottorcloud.com install-app crm
   bench --site collaudo.dottorcloud.com install-app frappe_whatsapp
   bench --site collaudo.dottorcloud.com migrate
   bench build --app crm
   ```

6. Produzione (nginx e supervisor), con il nome del sito come indirizzo:

   ```bash
   bench config dns_multitenant on
   sudo bench setup production frappe
   ```

7. Il certificato: `sudo bench setup lets-encrypt collaudo.dottorcloud.com`.
8. Il pianificatore acceso: `bench --site collaudo.dottorcloud.com enable-scheduler`.
   Sul banco della simulazione resta spento (la simulazione fa girare i lavori
   all'ora che vuole); qui la squadra lavora in tempo reale e i promemoria, Itala,
   l'archivio e le notifiche girano da soli.
9. I backup: `bench --site collaudo.dottorcloud.com backup --with-files` ogni notte
   (cron), tenuti fuori dal server.

**Aggiornare al codice nuovo del ramo**, tra un giro e l'altro:

```bash
cd ~/frappe-bench/apps/crm && git pull
cd ~/frappe-bench
bench --site collaudo.dottorcloud.com migrate
bench build --app crm
bench restart
```

## 4. La configurazione del sito

Tutto va nel `site_config.json` **del sito**
(`sites/collaudo.dottorcloud.com/site_config.json`), **mai** in
`common_site_config.json`: un'altra prova sullo stesso bench non deve ereditare le
chiavi del collaudo, e `crm/collaudo` legge `dottorcloud_collaudo` dalla
configurazione del sito. Si scrive a mano, o con
`bench --site collaudo.dottorcloud.com set-config -p <chiave> '<valore JSON>'`.

| Chiave | Esempio | A cosa serve | Sul collaudo |
|---|---|---|---|
| `host_name` | `"https://collaudo.dottorcloud.com"` | l'indirizzo che il sito dà di sé dove non c'è una richiesta: i link nelle email, le notifiche sul telefono, l'indirizzo del webhook di Stripe, quelli che Twilio chiama | **sì** |
| `dottorcloud_collaudo` | `1` | apre `crm.collaudo` (preparare il centro); senza, ogni chiamata è rifiutata | **sì, solo qui** |
| `dottorcloud_collaudo_password` | `"…"` | la password che `prepara.centro` dà a ogni collega; senza, è quella scritta nel repository | **sì**, una che non sta nel repository |
| `dottorcloud_posta` | `{"server": …, "porta": 587, "utente": …, "password": …, "mittente": "collaudo@…"}` | il servizio di invio: promemoria, codici, conferme partono da qui (doc 51) | **sì**, con un mittente del collaudo |
| `itala_client_id`, `itala_client_secret` | `"…"` | l'account Itala dell'agenzia (doc 49); l'azienda in prova usa la porta di prova | **sì** |
| `itala_codice_destinatario` | `"…"` | il codice destinatario dell'account, per le fatture dei fornitori | facoltativo |
| `dottorcloud_video` | `"https://meet.jit.si"` | il server Jitsi delle visite online | **sì** |
| `dottorcloud_archivio` | `{"endpoint": …, "region": …, "bucket": …, "prefix": "dottorcloud-collaudo", "access_key": …, "secret_key": …}` | l'archivio dei file privati (doc 57) | **sì**, con la sua cartella |
| `meta_hub_url`, `meta_relay_secret` | `"https://<hub>"`, `"…"` | WhatsApp passa dall'hub dell'agenzia (doc 12): gli stessi valori dei siti dei centri | **sì**, per WhatsApp |
| `dottorcloud_twilio` | `{"account_sid": …, "auth_token": …}` | l'account Twilio dell'agenzia, per la segreteria dell'agenzia (doc 52) | **no**: si prova la strada del centro |
| `fic_client_id`, `fic_client_secret` | | l'app Fatture in Cloud dell'agenzia (doc 58) | **no** (sotto) |
| `google_client_id`, `google_client_secret` | | Google Calendar e l'accesso con Google | facoltativo |
| `sistema_ts_ambiente`, `sistema_ts_ca` | | il collaudo di Sogei per il Sistema TS | **no** su questo sito (sotto, «Un sito fiscale a parte») |
| `stripe_api` | | manda DottorCloud allo Stripe finto della simulazione | **mai** |
| `encryption_key` | (lo scrive il bench) | cifra le password salvate nel sito | da tenere nel backup |

Le chiavi segrete non si incollano in una segnalazione, in una chat o in un
documento: stanno nel file e nel gestore di password di NPM2.

## 5. Il centro preparato

**Prima che qualcuno crei una persona**: `prepara.centro` rifiuta un sito che ha già
persone con un indirizzo fuori da example.com.

1. Il file della squadra, per esempio `/home/frappe/collaudo/team.json`. Le chiavi
   sono i sette ruoli; un ruolo che manca resta quello della simulazione, a
   example.com, che non riceve email:

   ```json
   {
     "responsabile": {"email": "roberta.colombo@npm2.example", "first_name": "Roberta", "last_name": "Colombo"},
     "segreteria": {"email": "silvia.ricci@npm2.example", "first_name": "Silvia", "last_name": "Ricci"},
     "medico": {"email": "andrea.conti@npm2.example", "first_name": "Andrea", "last_name": "Conti"},
     "fisioterapista": {"email": "marta.greco@npm2.example", "first_name": "Marta", "last_name": "Greco"},
     "dentista": {"email": "stefano.bruno@npm2.example", "first_name": "Stefano", "last_name": "Bruno"},
     "dietista": {"email": "francesca.gallo@npm2.example", "first_name": "Francesca", "last_name": "Gallo"},
     "marketing": {"email": "elisa.costa@npm2.example", "first_name": "Elisa", "last_name": "Costa"}
   }
   ```

   Al posto di `npm2.example` le caselle di lavoro dei colleghi. Due ruoli non hanno
   mai la stessa email.
2. Il centro, senza servizi finti:

   ```bash
   bench --site collaudo.dottorcloud.com execute crm.collaudo.prepara.centro \
     --kwargs '{"persone": "/home/frappe/collaudo/team.json", "servizi_finti": 0}'
   ```

3. Il comando risponde con il nome del centro, l'azienda che emette (in prova), la
   squadra con la sua password e i **problemi**. Finché Stripe non è collegato
   (sotto) i problemi dicono `stripe: off`: è atteso. Ogni altro problema si risolve
   prima di andare avanti.
4. Cosa trova la squadra: il «Poliambulatorio San Luca» con la sede di Milano e
   quella di Monza, gli ambulatori, ognuno con il suo livello (il medico anche la
   direzione sanitaria), le qualifiche e i turni, i servizi, il «Fondo Salute Più»
   in forma diretta, gli abbonamenti «Pilates mensile» (al mese, in vendita
   nell'area) e «Pilates trimestre», l'azienda in prova impostata come struttura
   sanitaria, promemoria (solo email), solleciti, area con «Sono qui», lista
   d'attesa, prenotazione online, richieste di recensione e preventivi a rate
   accesi, le schede cliniche di DottorCloud pubblicate dal medico. Sono i valori di
   `crm/collaudo/regole.py`: se cambiano lì, valgono quelli.
5. Ognuno entra in `https://collaudo.dottorcloud.com/crm` con la sua email e la
   password del collaudo, e la cambia subito (Impostazioni › Il tuo account ›
   Profilo › «Cambia la password»).
6. Ogni utente nasce con un cellulare di prova, di una serie che nessun operatore
   assegna. Chi deve rispondere alle chiamate del centro imposta la sua linea in
   Impostazioni › Telefono › Telefonia: al computer, o sul cellulare con il proprio
   numero.

`prepara.centro` si può rilanciare sullo stesso centro (ritrova quello che ha fatto e
va avanti), ma solo finché non ci sono persone della squadra: dopo, si rifà il sito
(«Tra un giro e l'altro»).

**L'orologio del banco** (`crm.collaudo.tempo`) è della simulazione: sul server di
collaudo non si sposta mai. La squadra lavora con l'ora vera, e Stripe, Twilio e
Meta pure.

## 6. I servizi esterni, nei loro ambienti di prova

Ognuno si collega dalle schermate di DottorCloud, come lo farà un centro. Le voci di
Impostazioni sono quelle che si leggono con la clinica accesa (il gruppo «Clienti»
si legge «Pazienti»).

### Posta

- **Il servizio di invio** (`dottorcloud_posta`): lo stesso servizio dell'agenzia,
  con un mittente del collaudo su un sottodominio suo (per esempio
  `collaudo@collaudo.posta.dottorcloud.it`, con SPF, DKIM e DMARC): un errore del
  collaudo non tocca la reputazione dell'indirizzo di produzione. Il sito lo prende
  al migrate, entro un'ora, o subito con «Sincronizza ora» (Impostazioni › Email ›
  Account, la vede solo l'agenzia).
- **Per i primi passi** si può usare una casella che trattiene tutto (come Mailpit)
  al posto del servizio vero: nessuna email esce, ma nessun telefono riceve i codici
  dell'area. Dal giorno 1 serve il servizio vero.
- **Le caselle del centro**: una casella creata per il collaudo (per esempio un
  Gmail con la password per le app) in Impostazioni › Email › Account; le email che
  i «pazienti» le scrivono vanno sulla loro pagina.
- **Gli indirizzi dei pazienti**: chi fa un paziente usa un indirizzo **diverso** da
  quello del suo utente di lavoro, che è già un utente del sito. Va bene il
  «+» se la casella lo accetta (Gmail e Google Workspace sì; le altre da
  verificare): `silvia.ricci+paziente@…`. Il genitore e il figlio, due indirizzi
  ancora diversi.
- **Nessuno fuori dalla squadra**: le guardie della demo non fermano queste
  persone. Chi crea una persona scrive solo un indirizzo della squadra o uno a
  example.com.

### Stripe in modalità di prova

1. Nella dashboard di Stripe, in **modalità di prova** (o in una sandbox): Sviluppatori
   › Chiavi API, la **chiave segreta** `sk_test_…`. Una chiave dal vivo non si usa
   mai qui.
2. Il responsabile, in Impostazioni › Fatturazione › **Pagamenti online**: incolla la
   chiave, «Collega Stripe». La pagina dice «Modalità di prova».
3. Su Stripe, Sviluppatori › Webhook (la dashboard di Stripe cambia: altrove si
   chiama Workbench): c'è l'endpoint che DottorCloud ha fatto,
   `https://collaudo.dottorcloud.com/api/method/crm.pagamenti.webhook.stripe`, con
   gli eventi `checkout.session.completed`, `checkout.session.expired`,
   `charge.refunded`, `payment_intent.succeeded`, `payment_intent.payment_failed`.
   Lì si vede anche ogni consegna e la risposta del sito (2xx).
4. Sulla stessa pagina di DottorCloud: «Vendi abbonamenti dall'area clienti» e
   «Addebito mensile con carta salvata» accesi, la restituzione dell'acconto a una
   disdetta almeno 24 ore prima.
5. `prepara.centro` ha già messo l'acconto di 30 € sulla «Visita medica», il prezzo
   intero online sulla «Visita nutrizionale» e sul «Controllo nutrizionale online»,
   «Pilates mensile» in vendita nell'area.

**Le carte di prova.** Scadenza: una data qualsiasi nel futuro; CVC: tre cifre
qualsiasi. Numeri da ricontrollare sulla tabella di Stripe prima di ogni giro
([Testing](https://docs.stripe.com/testing)): sono stati riscontrati il 10/10/2026
nei risultati della documentazione di Stripe, la pagina non era leggibile da qui.

| Caso | Carta | Cosa deve succedere in DottorCloud |
|---|---|---|
| Pagamento riuscito | `4242 4242 4242 4242` | acconto pagato, prenotazione confermata, fattura d'acconto (di prova) incassata |
| Rifiutata | `4000 0000 0000 0002` | Stripe rifiuta sulla sua pagina; il posto resta tenuto fino alla scadenza del link |
| Fondi insufficienti | `4000 0000 0000 9995` | come sopra, con il motivo dei fondi |
| Chiede 3-D Secure, poi va senza | `4000 0025 0000 3155` | la banca chiede di confermare al primo pagamento; salvata per l'addebito mensile, quelli dopo passano senza |
| Chiede 3-D Secure sempre | `4000 0027 6000 3184` | il primo pagamento passa dopo la conferma; l'addebito mensile dopo **non riesce** («la banca chiede di confermare»): niente fattura, l'email «Il tuo pagamento non è riuscito», «Paga ora» nell'area |
| Si attacca, poi ogni addebito fallisce | `4000 0000 0000 0341` | nella nostra strada la prima rata si paga subito con la Checkout, quindi fallisce già lì: non si vende niente. Serve per vedere quel caso, non l'addebito mensile |

**Quello che sul collaudo non si prova.** Una fattura di prova non si paga mai
online (`pagamenti.perche_non_pagabile`): «Paga online» su una fattura nell'area, il
«Link di pagamento» della segreteria e la rata di un preventivo da pagare online
rispondono «Una fattura di prova non si paga mai.». È giusto così. Si provano sul
sito fiscale a parte (sotto) o al passaggio del pilota.

**L'addebito del mese dopo, senza aspettare un mese.** Il giro del giorno addebita le
rate scadute. Solo sul server di collaudo, dopo che un «paziente» ha comprato
«Pilates mensile», il sistemista fa girare il giro con il giorno della rata dopo:

```bash
bench --site collaudo.dottorcloud.com execute crm.pagamenti.addebiti.ogni_giorno \
  --kwargs '{"oggi": "AAAA-MM-GG"}'
```

La rata riuscita ha la sua fattura di prova, incassata con carta; quella con la
carta `…3184` non riesce, e la persona riceve l'email. Il giro tiene il giorno
scritto come giorno del tentativo: su un abbonamento così, i tentativi dopo si
provano con un giorno ancora più avanti.

### Itala di prova

1. L'account Itala dell'agenzia è in `itala_client_id` e `itala_client_secret`
   (sopra), o in Impostazioni › Fatturazione › Avanzate › Opzioni (lo vede solo
   l'agenzia).
2. L'azienda di `prepara.centro` è **in prova**: le sue fatture hanno la serie
   `PROVA` e vanno alla porta di prova di Itala
   (`https://fattura-elettronica-api.it/ws2.0/test`). La prima che parte registra
   l'azienda presso Itala, nell'ambiente di prova.
3. Allo SdI va solo una fattura elettronica: a un'azienda o a un ente. Le fatture
   sanitarie a una persona non ci vanno mai (vanno al Sistema TS). Per provare Itala:
   la «Fattura al fondo» del mese (Fatture › Convenzioni) o una fattura a
   un'azienda, con «Invia allo SdI».
4. Nell'area riservata di Itala si vede la fattura arrivata. Nell'ambiente di prova
   torna subito «inviata», con un identificativo SdI inventato (`.pi/vendor/itala.md`):
   - per vedere un esito (consegnata, non consegnata, scartata; per un ente accettata
     o rifiutata), si cambia lo stato a mano nell'area riservata di Itala con «Da
     leggere» spuntato: DottorCloud lo legge al giro dopo, entro dieci minuti;
   - per una fattura di un fornitore, si inserisce a mano in «Ricezione»: compare in
     Fatture › Ricevute.
5. Da sapere:
   - Itala può rifiutare un'azienda in prova («Cedente … non abilitato in ambiente
     di test. Contattare l'assistenza.»): si scrive all'assistenza di Itala;
   - la partita IVA dell'azienda del collaudo non deve essere usata da un altro sito
     di prova sullo stesso account: gli aggiornamenti di Itala si leggono una volta
     sola, e due siti se li rubano. *Da verificare che nessun sito di sviluppo usi
     quella di `crm/collaudo/regole.py`.*

### Sistema TS

- **Sul collaudo il Sistema TS non riceve niente.** Una fattura di prova si controlla
  all'emissione come lo farebbe il Sistema TS, e resta lì: la fattura dice «Prova:
  controllata, non inviata». È quello che si prova: un errore del tracciato ferma
  l'emissione, e la finestra dice cosa correggere.
- **Il collaudo di Sogei esiste**, e il codice lo usa solo con
  `sistema_ts_ambiente: "test"` (e `sistema_ts_ca`, il certificato di cui fidarsi),
  e solo per una fattura **vera**: una di prova non parte mai. Per questo non è su
  questo sito: è il sito fiscale a parte, sotto. Gli sviluppatori l'hanno provato il
  05/10/2026 con le utenze del kit (`.pi/feats/fatturazione/guida.md`).
- **Guardare il tracciato a mano.** Dalla console del sito, con il nome di una
  fattura sanitaria di prova:

  ```bash
  bench --site collaudo.dottorcloud.com console
  ```

  ```python
  from crm.invoicing import documento
  from crm.tessera_sanitaria import documento as ts
  from crm.tessera_sanitaria.engine.tracciato import CifratoreFittizio, costruisci_file_allegato

  fattura = frappe.get_doc("CRM Invoice", "<nome della fattura>")
  emittente = documento.azienda(fattura)
  print(ts.verifica(fattura, emittente).errori)  # vuoto: il Sistema TS la prenderebbe
  print(costruisci_file_allegato([ts.documento_spesa(fattura, emittente)], CifratoreFittizio()).decode())
  ```

  I codici fiscali escono con `NONCIFRATO:` davanti invece che cifrati: un file così
  non si scambia mai per uno da mandare. Si confronta con lo schema
  `730_precompilata.xsd` del kit del Sistema TS.
- **L'XML di una fattura elettronica** (quella al fondo) si scarica dal Desk
  (`CRM Invoice`, il campo dell'XML) e si controlla con lo schema che è nel
  repository:
  `xmllint --noout --schema crm/invoicing/tests/xsd/Schema_VFPR12_v1.2.3.xsd fattura.xml`.

### Twilio

1. **L'account.** Un account Twilio di NPM2 **attivato**: con un account di prova
   Twilio fa chiamare solo i numeri verificati e non vende numeri italiani (doc 52).
2. **Lo spazio del collaudo.** Nella console di Twilio, un sottoaccount «DottorCloud
   collaudo»; i suoi Account SID e Auth Token si incollano in Impostazioni ›
   Telefono › Telefonia › Twilio, «Collega». I codici di un sottoaccount fanno di
   quel sottoaccount lo spazio: i consumi del collaudo restano separati.
3. **Un numero per ricevere chiamate e SMS.** Un mobile italiano:
   - «Nuovo numero», con i dati e i documenti **di NPM2** (la finestra propone i dati
     della fatturazione del centro di collaudo, che non sono di nessuno: si
     sostituiscono). Twilio li verifica in qualche giorno: si chiede una settimana
     prima del giro;
   - oppure, se NPM2 ha già un mobile italiano con i documenti approvati, «Ho già un
     numero» › «Nell'account Twilio del centro»: si sposta nello spazio.
4. **Il mittente degli SMS** («Mittente degli SMS»): il numero, perché si provano le
   risposte (SI, NO, STOP). Con il nome del centro come mittente nessuno può
   rispondere.
5. **Le chiamate in uscita.** Dal novembre 2025 una chiamata verso l'Italia che mostra
   un cellulare italiano è bloccata (AGCOM, doc 52), e Twilio non vende numeri
   geografici. Si mostra il fisso di NPM2 verificato («Verifica un numero»): passa
   per quanto lo lasciano gli operatori. Una chiamata che non arriva per questo non è
   un errore di DottorCloud: si scrive nella segnalazione.
6. **Paesi che si possono chiamare**: solo l'Italia. **Avvisami quando il mese arriva
   a**: un importo basso, così la spesa del collaudo si vede.
7. **La segreteria telefonica** (Impostazioni › Telefono › Telefonia): i secondi di
   squillo, l'annuncio, il messaggio dopo il segnale acceso.
8. **I costi**: numeri, chiamate e SMS li fattura Twilio allo spazio. Vedi il listino
   di Twilio per l'Italia: [voce](https://www.twilio.com/en-us/voice/pricing/it),
   [SMS](https://www.twilio.com/en-us/sms/pricing/it),
   [numeri](https://assets.cdn.prod.twilio.com/pricing-csv/SiteNumbersPricing.csv).

### WhatsApp

Il collaudo usa il **numero di test** che Meta presta all'app WhatsApp dell'agenzia:
non serve un numero vero, né il collegamento con il QR.

1. Nell'App Dashboard di Meta, l'app WhatsApp dell'agenzia › WhatsApp › **API Setup**:
   il numero di test, il suo «Phone number ID» e l'ID del suo account WhatsApp
   Business (WABA).
2. Sotto «To», i **destinatari**: al massimo cinque numeri, ognuno conferma con il
   codice che riceve su WhatsApp
   ([Get started](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started/)).
   Sono i telefoni di chi fa i pazienti e il genitore: solo loro ricevono i WhatsApp
   del collaudo.
3. Un **token permanente** di un utente di sistema del portfolio dell'agenzia, con
   i permessi `whatsapp_business_messaging` e `whatsapp_business_management` sull'app
   e sul WABA di test. Non quello temporaneo della dashboard, che scade (doc 12).
4. In DottorCloud, come agenzia (System Manager): Impostazioni › WhatsApp › Numeri ›
   «Dettagli tecnici» › «Aggiungi un numero con le sue credenziali»: Phone number ID,
   WABA ID, token. Poi «Controlla la ricezione dei messaggi»: deve dire che va.
5. Se l'hub risponde che l'account è già collegato a un altro sito (un sito di
   sviluppo, l'hub stesso), sull'hub si toglie la «Meta WhatsApp Route» di quel WABA
   e si aggiunge di nuovo. Se l'hub ha `meta_relay_sites`, ci va anche
   `https://collaudo.dottorcloud.com`.
6. Il modello dei promemoria: il responsabile, in Impostazioni › Agenda › Agenda e
   promemoria › Promemoria degli appuntamenti, «Crea il modello dei promemoria». Meta
   lo esamina, di solito entro un giorno: si fa il giorno 0.
7. Da sapere: il numero di test non chiede un metodo di pagamento per i modelli
   (doc 12); scrive solo ai cinque destinatari; un WhatsApp a un altro numero non
   arriva, e il promemoria va per SMS o email.

### Video

- `dottorcloud_video`: il server Jitsi dell'agenzia, se c'è.
- Altrimenti `https://meet.jit.si`: dal 24/08/2023 chi apre una stanza deve entrare
  con un account Google, GitHub o Facebook; gli altri entrano senza
  ([Jitsi](https://jitsi.org/blog/authentication-on-meet-jit-si/)). Il professionista
  apre la visita dall'agenda per primo. Va bene per il collaudo, con persone della
  squadra; per un centro vero si usa il server dell'agenzia.

### Archivio dei file

- **Il suo posto**: meglio un bucket a parte in un progetto Hetzner a parte (per
  esempio «NPM2 Collaudo»), con le sue chiavi S3; se no il bucket di NPM2 con una
  cartella sua, `"prefix": "dottorcloud-collaudo"`: le chiavi diventano
  `dottorcloud-collaudo/collaudo.dottorcloud.com/…` e non toccano mai la cartella di
  produzione.
- **Un bucket nuovo**, una volta:
  `bench --site collaudo.dottorcloud.com execute crm.archivio.archivio.imposta_il_bucket`
  (versioni e CORS). Sul bucket di NPM2 è già fatto: non si rilancia.
- **Una regola di Lifecycle** sulla cartella del collaudo (Hetzner › Object Storage ›
  il bucket › Lifecycle) che toglie gli oggetti dopo qualche settimana.
- **Come si prova**: un documento caricato su una persona; dopo più di un'ora il
  giro orario lo porta nel bucket e sul server resta il file vuoto; riaperto, il link
  del bucket dura cinque minuti. La pagina Impostazioni › Il centro › Funzionalità
  dice lo spazio usato.

### Fatture in Cloud

Non si prova su questo sito. Con Fatture in Cloud una fattura vera nasce lì con il suo
numero, e una fattura di prova non ci arriva mai (`tocca_a_fic`, doc 58): sul collaudo
l'azienda resta in prova, quindi Fatture in Cloud non vedrebbe niente. Si prova solo
con un centro pilota che fattura già lì, al passaggio.

### L'assistente (facoltativo)

Per provare la dettatura, la lettera e il riassunto della clinica: Impostazioni ›
Integrazioni › Assistente, la parte dell'agenzia (il fornitore del modello e la sua
chiave, con nessuna conservazione richiesta), poi le funzioni accese dal responsabile.
Solo con persone della squadra e frasi inventate.

## 7. Prima che la squadra cominci

- [ ] `https://collaudo.dottorcloud.com/crm` si apre con il lucchetto, in italiano,
      con il nome «Poliambulatorio San Luca».
- [ ] `prepara.centro` non dice problemi, tranne `stripe: off` prima di Stripe; dopo
      Stripe, rilanciato, nessuno.
- [ ] Il pianificatore è acceso e i lavori girano (Impostazioni › Il centro ›
      Funzionalità si aggiorna; nel Desk, «Scheduled Job Log» ha righe recenti).
- [ ] Una email di prova arriva in una casella della squadra (per esempio il codice
      dell'area a un «paziente»).
- [ ] Stripe dice «Modalità di prova» e l'endpoint del webhook risponde 2xx.
- [ ] Twilio: «Controlla» dice che lo spazio è attivo; un SMS arriva a un telefono
      della squadra.
- [ ] WhatsApp: il numero di test è nell'elenco, «Controlla la ricezione dei
      messaggi» va, il modello dei promemoria è approvato.
- [ ] Il registro degli errori del sito (Desk › Error Log) è vuoto, o ogni riga ha
      una spiegazione.
- [ ] Ogni collega ha cambiato la password e ha la sua lista stampata.

## 8. Un sito fiscale a parte (facoltativo)

Sul collaudo l'azienda resta in prova, quindi alcune cose non si possono vedere: una
fattura pagata online, il link di pagamento, i solleciti, le fatture nell'area, la
chiusura di cassa con gli incassi, la comunicazione al Sistema TS. Per vederle, uno
sviluppatore prepara un secondo sito sullo stesso bench, per esempio
`fiscale.collaudo.dottorcloud.com`:

1. il suo `site_config.json` ha `dottorcloud_collaudo`, `host_name`,
   `sistema_ts_ambiente: "test"`, `sistema_ts_ca` (il certificato del collaudo di
   Sogei, che nessun sistema riconosce: si salva con `openssl s_client`), e **nessuna
   chiave di Itala**, né nel file né nelle Opzioni della fatturazione: una fattura
   elettronica non può partire;
2. `prepara.centro` con la squadra, Stripe in modalità di prova collegato;
3. le credenziali del Sistema TS sono le utenze del kit, come dice la guida della
   fatturazione (`.pi/feats/fatturazione/guida.md`, «Provato sul collaudo il
   05/10/2026»): lo fa uno sviluppatore, perché codice fiscale e partita IVA del kit
   non passano le cifre di controllo;
4. qui, e solo qui, il responsabile preme «Attiva la fatturazione»: le fatture sono
   vere per DottorCloud, ma non arrivano a nessuno. Quelle sanitarie vanno al
   collaudo di Sogei («Comunica»), le altre non possono partire senza Itala.

Mai persone vere, mai una chiave dal vivo, mai le chiavi di Itala su questo sito.

## 9. Tra un giro e l'altro, e alla fine

- **Ricominciare da capo**: un sito nuovo (`bench drop-site` e di nuovo il passo 3.5),
  poi `prepara.centro`. Prima, su Stripe e Twilio, si toglie quello che il sito
  vecchio aveva fatto: «Scollega» in Pagamenti online (toglie l'endpoint del
  webhook), «Scollega» in Twilio (i numeri restano nello spazio e costano finché non
  si rilasciano), la «Meta WhatsApp Route» del numero di test sull'hub se il sito
  cambia nome.
- **I numeri Twilio** che non servono più si rilasciano dalla pagina dei numeri:
  smettono di costare e non tornano indietro.
- **I file nel bucket** del collaudo se ne vanno con la regola di Lifecycle.
- **Alla fine del collaudo** il server si spegne o resta per il giro dopo; i backup
  del collaudo si cancellano: contengono i dati dei colleghi.

## Fonti

- Stripe, [Testing](https://docs.stripe.com/testing) (le carte di prova) e
  [Billing testing](https://stripe.com/docs/billing/testing) (la carta `…0341`).
- Meta, [WhatsApp Cloud API, Get started](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started/)
  (il numero di test e i cinque destinatari).
- Jitsi, [l'autenticazione su meet.jit.si](https://jitsi.org/blog/authentication-on-meet-jit-si/).
- Twilio, i listini per l'Italia citati sopra e nel doc 52.
- Itala: il contratto riassunto in `.pi/vendor/itala.md` (le prove sulla porta di
  prova del 05/10/2026).
