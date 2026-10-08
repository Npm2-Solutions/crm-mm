# 27 — Impostazioni: WhatsApp, Social Planner e Integrazioni, ognuno al suo posto

> ✅ **FATTO (24/09/2026)**. Il gruppo unico "Meta & Messaging" (sette voci
> miste: connessione, form, spesa, qualità, profili social, WhatsApp, template)
> è diventato tre spazi separati. I dettagli tecnici — id dell'app, webhook,
> token, permessi Facebook, log grezzi — li vedono solo gli amministratori, e
> il server non li manda a nessun altro.

## Il problema

Tutto ciò che toccava Meta stava in un gruppo solo, perché passava dalla stessa
app. Ma per chi usa il CRM sono cose diverse:

- **WhatsApp** è un canale, come l'email: numeri da cui si scrive e modelli da
  mandare fuori dalle 24 ore. Non dipende nemmeno dalla connessione Facebook
  (usa Embedded Signup e può stare in un'app Meta tutta sua).
- **Meta** è un'integrazione: la connessione all'account Facebook e le tre cose
  che alimenta (lead dai moduli, spesa delle inserzioni, qualità dei lead).
- **Il Social Planner** è uno strumento di lavoro che oggi pubblica tramite Meta
  ma che domani potrà prendere profili anche da altre sorgenti.

In più, "Lead quality" o "Social profiles" nell'elenco non dicevano a che cosa
appartenessero, e la pagina dei profili aveva un proprio "Connect with Facebook"
(con redirect a tutta pagina, mentre quello vero apre un popup) e un messaggio
"App ID and secret live in Settings → Meta" mostrato anche ai clienti la cui
app è fornita centralmente — un bug, perché controllava solo il doctype e non il
config del bench.

## La nuova struttura

```
Email                 Accounts · Templates
WhatsApp              Numbers · Templates            ← accanto all'Email, stessa forma
…
Social Planner        Profiles                       ← sorgenti + profili
…
Integrations          Meta · Telephony · ERPNext     ← Meta è una pagina con schede
                      └─ Meta: Connection · Lead Ads · Ad performance · Lead quality
```

- **WhatsApp → Numbers**: i numeri collegati, quello che invia, "Connetti" in
  alto a destra, "Smetti di usarlo" dal menu della riga — ora **con conferma**
  (prima bastava un clic sull'icona). Un numero non più in uso resta in elenco,
  grigio, con la cronologia attaccata.
- **WhatsApp → Templates**: invariata, ma l'eliminazione chiede conferma: un
  modello cancellato va fatto riapprovare da Meta.
- **Integrations → Meta**: una pagina sola con quattro schede e lo stato della
  connessione nel titolo. Lo stato si carica una volta e le schede lo
  condividono. La scelta delle Pagine che portano lead sta **solo** in
  *Connection* (in *Lead Ads* c'era un secondo interruttore per la stessa cosa);
  *Lead Ads* resta sui moduli: mappatura, "Importa gli ultimi 90 giorni" dal
  menu del modulo, i lead non importati con "Riprova".
- **Social Planner → Profiles**: in alto le **sorgenti** (oggi Meta: collegata o
  no, con quale account, quanti profili sono nel planner), sotto i **profili**
  con l'interruttore "nel planner". Il collegamento non si fa qui: "Collega" /
  "Gestisci" porta all'integrazione. Niente più cestino: i profili li riporta
  la sincronizzazione, spegnerli è il modo giusto di toglierli dal planner.

### I link che esistevano restano validi

La modale apre le pagine per chiave non tradotta. Le chiavi usate da fuori
(callback OAuth, pulsanti di altre schermate) non cambiano:

| Chiave | Apre |
|---|---|
| `Meta connection` | Integrations → Meta, scheda Connection (callback OAuth di Facebook) |
| `Lead forms`, `Ad performance`, `Lead quality` | la pagina Meta, sulla scheda giusta (alias) |
| `WhatsApp` | WhatsApp → Numbers (ritorno dal collegamento sull'hub) |
| `WhatsApp Templates` | WhatsApp → Templates |
| `Social profiles` | Social Planner → Profiles |

Due voci si chiamano ora "Templates" (Email e WhatsApp): la voce attiva si
riconosce dalla chiave, non più dall'etichetta tradotta.

Trovato e sistemato strada facendo: il ritorno a `/crm?settings=WhatsApp` dopo il
collegamento apriva il Profilo quando il ruolo o "WhatsApp installato" non erano
ancora arrivati dal server. Ora, quando i gruppi cambiano, la pagina richiesta
viene cercata di nuovo.

## Chi vede cosa

Tre ruoli, con i nomi che il CRM già usa nella pagina Utenti:

| | Admin (System Manager) | Manager (Sales Manager) | Commerciale (Sales User) |
|---|---|---|---|
| Collegare Facebook, scegliere le Pagine, mappare i moduli | ✅ | ✅ | — |
| Collegare/fermare numeri WhatsApp, template | ✅ | ✅ | — |
| Profili del Social Planner | ✅ | ✅ | — |
| App Meta (App ID/Secret), webhook e "Sistemalo" | ✅ | — | — |
| Permessi concessi da Facebook (elenco), ultima chiamata di Meta, scadenza del token in chiaro | ✅ | — (solo "riconnetti" quando serve) | — |
| Log grezzi dei lead non importati, "Controlla webhook", "Invia lead di prova" | ✅ | — (solo "N lead non importati · Riprova") | — |
| WhatsApp: app in uso, configurazione Embedded Signup, ultimi tentativi, numero con credenziali, "Controlla messaggi in arrivo", Phone number ID | ✅ | — | — |
| Codice evento di test (qualità dei lead) | ✅ | solo in lettura se impostato | — |
| Stato di consegna dell'inserzione sulla scheda del lead | ✅ | ✅ | — |
| Motivo per cui un post non è uscito | ✅ | ✅ | "Non pubblicato: un manager può vedere perché" |

Quello che non è per il manager sta in un riquadro **"Dettagli tecnici · Solo
amministratori"**, chiuso di default. Il manager legge invece frasi che dicono
**di chi** è il problema: "Meta non è ancora configurato su questo CRM: deve
aggiungerlo un amministratore", "WhatsApp non è ancora configurato…", "La
connessione a Facebook scade il 1 ott 2026: riconnetti per rinnovarla" (10 giorni
prima; nessuno rinnova il token da solo e, scaduto, spesa e qualità dei lead si
fermano in silenzio mentre i lead continuano ad arrivare).

**Non è solo grafica.** Il server decide cosa mandare:

- `meta.api.get_status` e `whatsapp.api.get_status` mandano la parte tecnica
  solo a un System Manager (e il `verify_token` del webhook non lo mandano più a
  nessuno: nessuna schermata lo usava).
- Solo amministratori: `save_app_settings`, `configure_webhook`,
  `get_webhook_subscription`, `verify_webhook_subscriptions`, `create_test_lead`,
  `test_connection` (Meta); `save_whatsapp_app`, `get_webhook`,
  `configure_webhook`, `add_account`, `recheck_delivery`,
  `recent_signup_attempts` (WhatsApp).
- `get_failure_logs` restituisce solo i fallimenti (prima anche i "Synced",
  mostrati sotto "Sync failures") e il payload con il traceback solo all'admin.
- `get_record_ad` toglie lo stato di consegna per chi non è manager;
  `social.get_accounts` non manda più gli id dei profili al composer.

Fuori dalle impostazioni, per i commerciali: il Social Planner non dice più
"Collega Facebook e Instagram" a chi non può farlo; il selettore dei template
WhatsApp non offre "Crea nuovo template" (aprirebbe una pagina che per loro non
esiste); nel tracciamento non compare "Apri le impostazioni di tracciamento" né
"installa lo script sul sito".

## Un token dentro un messaggio d'errore

Ogni chiamata Graph si autentica nella query string (`access_token`,
`appsecret_proof`, e negli scambi di codice `client_secret`). Quando la rete
cade prima che Meta risponda, `requests` descrive l'errore **con l'URL**, query
compresa — e quel testo finiva nell'errore del post del Social Planner (visibile
a chi l'ha scritto), nella pagina dell'hub durante il collegamento WhatsApp, nei
log. Ora `crm/integrations/meta/redact.py` sostituisce i valori con `***` in
`graph_request` e nella paginazione, l'eccezione originale non viene più
concatenata al traceback, e il publisher ripulisce comunque ciò che salva.
Test puri in `crm/tests/test_meta_redact.py`.

## Social Planner: le sorgenti

`crm/social/sources.py` è il registro: una sorgente risponde a tre domande —
`status()` (collegata? con quale account?), `sync()` (i suoi account diventano
`CRM Social Account`), `publish()` (un post su un profilo). Il publisher passa
dalla sorgente del profilo; la pagina impostazioni elenca le sorgenti;
`social.sync_profiles` le sincronizza tutte. Aggiungere LinkedIn, TikTok o
Google Business Profile vuol dire scrivere quelle tre funzioni e una riga in
`SOURCES` (più l'opzione nel campo `platform` e il colore in `utils/social.js`).

La sincronizzazione dei profili non legge più le Pagine da Facebook dentro la
richiesta (un account con molte Pagine andava in timeout): allinea subito i
profili alle Pagine già note e fa partire in background la lettura da Facebook,
che alla fine riallinea di nuovo. "Nessuna Pagina" non è più un errore.

### L'approvazione non si salta dalla REST API

`save_post` trasformava già il "Programma" di un commerciale in "In attesa di
approvazione", ma il doctype è scrivibile dai Sales User: un post salvato via
`/api/resource` andava in programmazione — e fuori — senza approvazione. Ora la
regola sta nel controller (`CRMSocialPost.validate`): solo un manager mette un
post in programma, e un post approvato modificato da un commerciale torna in
approvazione.

## Test

- `crm/tests/test_meta_redact.py` — puro, gira anche senza bench.
- `crm/tests/test_social.py` — approvazione via REST, errore nascosto al
  commerciale e senza token per il manager, sorgenti, profili con la loro
  sorgente, "nessuna Pagina" senza errore, endpoint solo manager.
- `frontend/tests/unit/metaConnection.test.js` — quando avvisare della scadenza.

## Rimasto fuori (da valutare a parte)

- `crm/api/whatsapp.py:add_roles` dà ai Sales User scrittura ed eliminazione su
  `WhatsApp Templates` e `WhatsApp Settings` via REST: servirebbe solo la
  lettura, ma va verificato con la versione di `frappe_whatsapp` installata.
- La chiave del webhook delle automazioni (`CRM Automation.webhook_key`) e la
  chiave dell'API dei cambi (`FCRM Settings.access_key`, campo Data) sono
  leggibili dai Sales User.
