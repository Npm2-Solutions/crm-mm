# 20 — Più siti, sul dominio del cliente

> **Stato: la modalità cartella è implementata (08/09/2026); i domini custom restano una
> proposta.** Decisione del committente: per ora niente proxy e niente certificati
> automatici — i siti si pubblicano nelle cartelle del dominio del site. Il resto di
> questo documento resta valido per quando si aprirà quel capitolo.
>
> Ricerca condotta il 07/09/2026.
> Estende il [modulo 16](./16-sito-web-vetrina.md), che oggi gestisce **un sito solo**
> sul dominio del site Frappe.

## 1. Il problema, detto com'è

Oggi: `CRM Website Settings` è un Single. Una home, un brand, un dominio — quello del site
Frappe. Il CRM sta su `crm.tuobrand.it` e il sito del cliente finisce lì sotto.

Serve invece:

- **più siti nello stesso CRM** (un cliente per site Frappe, ma quel cliente può avere più
  siti: marchi, campagne, lingue);
- ognuno pubblicabile **sul dominio del cliente** (`www.cliente.it`), che il cliente
  configura da sé puntando il DNS;
- oppure, per chi non ha un dominio, **su una cartella** del nostro
  (`tuobrand.it/cliente-a`);
- e il CRM resta su un dominio nostro, che il cliente non deve nemmeno vedere.

## 2. Come lo fa GoHighLevel

Verificato sulla loro documentazione e sulle guide di setup (settembre 2026):

1. Il cliente aggiunge il dominio dal pannello (Settings → Domains).
2. GHL gli dà **un CNAME** verso `sites.leadconnectorhq.com` — **mai un record A**. Il
   cliente lo mette dal suo registrar.
3. GHL **emette il certificato da solo**, con Let's Encrypt, quando il DNS ha propagato
   (15–60 minuti).
4. Il funnel va **pubblicato prima**: con DNS perfetto ma pagina non pubblicata, esce 404.
5. Avvertenze ricorrenti: cancellare A/AAAA/CNAME preesistenti sullo stesso host, e su
   Cloudflare mettere il proxy in **DNS only** (nuvoletta grigia), altrimenti i due
   certificati litigano.

Il punto interessante non è il CNAME: è che **nessuno emette certificati a mano**. È
quello che dobbiamo replicare, perché è l'unica parte che non scala.

## 3. La tecnica che serve: on-demand TLS

Il meccanismo si chiama **on-demand TLS**, ed è quello che rende self-service un prodotto
a domini custom. Invece di emettere un certificato per ogni cliente al momento della
configurazione, il proxy lo emette **al primo handshake TLS** su quel nome:

```
visitatore → https://www.cliente.it
                    │
                    ▼
             proxy (Caddy)
                    │  primo handshake per questo host:
                    │  GET /ask?domain=www.cliente.it  ──▶  CRM
                    │  ◀── 200 se il dominio è configurato e attivo
                    │      404 altrimenti
                    │
                    │  200 → chiede il certificato a Let's Encrypt, lo installa,
                    │        e da lì in poi non richiede più nulla
                    ▼
             Frappe (site del cliente)
             X-Frappe-Site-Name: cliente.tuobrand.it
```

**L'endpoint `ask` è il controllo antiabuso**, non un dettaglio: senza, chiunque punti un
dominio qualsiasi al nostro IP fa partire un ordine ACME, e i limiti di Let's Encrypt
(300 nuovi ordini per account ogni 3 ore) finiscono in un pomeriggio. Con l'`ask`, si
emette solo per i domini che il CRM conosce.

È cold path: dopo il primo handshake il certificato è in cache fino al rinnovo.

### Perché non basta `bench setup add-domain`

Funziona, ma è manuale a ogni dominio: aggiunge il dominio al `site_config`, **rigenera la
configurazione nginx** e vuole un `bench setup nginx` più un reload, e il certificato lo
chiedi tu con certbot. Per due clienti va bene. Per venti è un lavoro fisso, e ogni
rinnovo è una cosa che può rompersi di notte.

Con il proxy davanti: **zero configurazione per dominio**. Il cliente punta il DNS, il CRM
conosce il dominio, il resto succede da solo.

### Il pezzo che rende tutto possibile

nginx di bench passa a Frappe l'intestazione `X-Frappe-Site-Name`, e Frappe risolve il
site da lì prima ancora di guardare l'`Host`. Quindi **un site Frappe può servire
qualunque dominio**: basta che il proxy davanti gli dica sempre di che site si tratta.
Un cliente per site resta vero; i domini sopra sono quanti ne vuole.

## 4. Cosa si costruisce nel CRM

### 4.1 I doctype

| DocType | Cosa |
|---|---|
| **CRM Web Site** | un sito: nome, `slug` (per la modalità cartella), home page, brand (logo, colori, font), menu, footer, SEO, tracciamento, `enabled`. È `CRM Website Settings` di oggi, ma **non più Single** |
| **CRM Web Domain** | un dominio del sito: `domain`, `site` (Link), `is_primary`, `status` (Da configurare / In verifica / Attivo / Errore), `verified_at`, `last_check` |

`Builder Page` prende un campo `crm_site` (Link), così ogni pagina appartiene a un sito.
Builder ha già le sue `Builder Project Folder`: le usiamo come raggruppamento visivo nel
suo editor, ma **la verità è il nostro campo** — le cartelle di Builder non hanno né
dominio né home.

Migrazione: alla prima esecuzione, un patch crea un `CRM Web Site` "Sito principale" con i
valori del Single di oggi e ci assegna tutte le pagine esistenti. Nessuno perde niente.

### 4.2 La risoluzione Host → sito

Un `website_path_resolver` (lo stesso aggancio che usa Builder) che, a ogni richiesta:

1. legge `frappe.request.host`;
2. cerca un `CRM Web Domain` attivo con quel nome;
3. se lo trova, mette il sito in `frappe.local` e **riscrive il percorso**: `/` diventa la
   home di quel sito, e le rotte delle sue pagine restano quelle;
4. se non lo trova, lascia fare al risolutore di Builder come oggi.

In modalità cartella la stessa cosa senza DNS: `/cliente-a/...` → sito "cliente-a".

### 4.3 ⚠️ Il CRM non deve rispondere sul dominio del cliente

Questo è il punto che va fatto bene: se `www.cliente.it` arriva allo stesso site Frappe,
allora `www.cliente.it/crm` servirebbe il CRM e `www.cliente.it/app` la scrivania. Il
cliente vedrebbe il nostro prodotto sul suo dominio, e chiunque potrebbe tentare il login lì.

Serve una guardia a livello di richiesta: **su un dominio di sito, esistono solo le pagine
di quel sito**. `/crm`, `/app`, `/login`, `/api` (tranne gli endpoint pubblici che servono
alle pagine: form, prenotazioni, tracciamento) rispondono 404, o rimandano al dominio del CRM.

È lo stesso confine che GHL ha per costruzione, avendo un servizio separato per i siti.
Noi ce lo dobbiamo scrivere — ed è una decina di righe in un `before_request`, ma non è
opzionale.

### 4.4 L'endpoint `ask`

```python
@frappe.whitelist(allow_guest=True, methods=["GET"])
@rate_limit(limit=60, seconds=60)
def check_domain(domain: str) -> str:
    """Il proxy chiede se può emettere un certificato per questo nome."""
```

200 se esiste un `CRM Web Domain` attivo con quel dominio e il sito è acceso; 404 in ogni
altro caso. Niente di più: è l'unica cosa che il proxy deve sapere.

### 4.5 Cosa vede l'utente nel CRM

`Sito` in sidebar diventa un elenco di **siti**; dentro ognuno, le pagine di oggi.
Nelle impostazioni di un sito, la scheda **Domini**:

- "Aggiungi dominio" → il CRM mostra **il CNAME da copiare**, con le avvertenze che
  contano (togli i record vecchi sullo stesso host; su Cloudflare metti DNS only);
- un pulsante **Verifica** che risolve il DNS e dice cosa vede davvero;
- lo stato del dominio, con il certificato che compare da solo entro qualche minuto;
- il promemoria che GHL ripete e che è vero anche qui: **prima pubblica la pagina**,
  altrimenti il dominio funziona e la pagina è 404.

## 5. Cosa serve fuori dall'applicazione

Poco, ma va fatto una volta:

1. Un **proxy davanti a nginx** (Caddy, per l'on-demand TLS) sul server che ospita i site
   dei clienti.
2. Un **A record** del nostro `sites.tuobrand.it` verso quell'IP: è il bersaglio dei CNAME
   dei clienti.
3. La `Caddyfile` con `on_demand_tls { ask <url del CRM>/api/method/crm.api.domains.check_domain }`
   e il proxy verso nginx con `X-Frappe-Site-Name` fisso.

Da mettere negli script di provisioning ([modulo 06](./06-white-label-saas.md)), accanto a
`provision_tenant.sh`.

### Il limite da conoscere

Let's Encrypt: 300 nuovi ordini per account ogni 3 ore, 50 certificati per dominio
registrato a settimana. Per il nostro volume non è un problema, ma è il motivo per cui
l'endpoint `ask` non è facoltativo.

## 6. La decisione da prendere

**Quale proxy davanti**, perché cambia cosa consegniamo come infrastruttura (il lato
applicativo è identico nei tre casi):

| | **Caddy davanti a nginx** | **nginx + certbot automatizzato** | **Cloudflare for SaaS** |
|---|---|---|---|
| Certificati | automatici, on-demand | uno script che chiama certbot e ricarica nginx a ogni dominio | gestiti da Cloudflare |
| Configurazione per dominio | **nessuna** | rigenerare e ricaricare nginx | chiamata API |
| Cosa aggiungiamo al server | un binario e un file | cron, hook, gestione errori | niente |
| Dipendenze esterne | Let's Encrypt | Let's Encrypt | Cloudflare (a pagamento sopra i 100 host) |
| Rischio | un pezzo nuovo nello stack | la parte che si rompe di notte | vincolo a un fornitore |

**Raccomandazione: Caddy.** È il modo per cui l'on-demand TLS esiste, l'endpoint `ask` è
un contratto di due righe, e il giorno che si cambia idea il lato applicativo non si tocca.

## 7. Cosa è stato fatto: i siti in cartella

Implementato senza toccare nulla fuori dall'applicazione, perché **la cartella è la rotta**:
una pagina del sito `studio-rossi` ha rotta `studio-rossi/chi-siamo`, e la sua home è
`studio-rossi` e basta. Frappe e Builder la risolvono da soli — non esiste riscrittura di
percorsi da nessuna parte, e questo è il motivo per cui costa poco ed è difficile romperla.

| | |
|---|---|
| `CRM Web Site` | un sito: nome, cartella, home, brand, menu, footer, SEO, tracciamento, acceso/spento |
| `CRM Website Settings` | resta Single, ma tiene solo l'interruttore generale e quale sito apre il CRM |
| `Builder Page.crm_site` | campo custom: a quale sito appartiene la pagina |
| patch `split_website_settings_into_sites` | gira **prima** del sync dei modelli, quando le vecchie colonne esistono ancora: crea "Sito principale" con i valori di oggi, gli assegna le pagine esistenti, e gli lascia la cartella **vuota** — le rotte già in circolazione non si toccano |

**La radice.** Un sito può prendersi anche `/` (`serve_at_root`), e Builder ha un solo
interruttore per quello: prenderselo lo toglie a chi ce l'aveva, che continua a funzionare
sotto la sua cartella. È una riga di regola, non un caso limite lasciato al caso.

**Il `<head>` per sito.** Builder applica `Builder Settings.head_html` a *tutte* le pagine,
che con più siti è lo scopo sbagliato: brand, analytics e consenso cambiano da sito a sito.
Nella voce globale ora c'è una sola riga — `{{ crm_site_head(page_name) }}` — e la chiamata
guarda a quale sito appartiene quella pagina. Stesso trucco per il blocco Contatti.

## 8. Ordine dei lavori (domini custom)

| Fase | Cosa | Stima |
|---|---|---|
| **1** | `CRM Web Site` + `CRM Web Domain`, patch di migrazione dal Single, `crm_site` sulle pagine, elenco siti nel CRM | 4–5 gg |
| **2** | Risoluzione Host → sito, modalità cartella, **guardia sul dominio del cliente** (§4.3), endpoint `ask` | 3–4 gg |
| **3** | Scheda Domini: istruzioni CNAME, verifica DNS, stato certificato | 2–3 gg |
| **4** | `Caddyfile` e script di provisioning, documentati nel modulo 06 | 1–2 gg |

Le fasi 1–3 sono lavoro applicativo e si possono fare subito: non dipendono da quale proxy
si sceglie. La 4 sì.
