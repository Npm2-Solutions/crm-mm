# 13 — Google Calendar, connesso in un click

> ✅ **IMPLEMENTATO (03/09/2026)**. Stesso schema del Meta: un solo progetto
> Google Cloud dell'agenzia, il cliente preme un bottone e autorizza. Nessun
> Client ID da incollare, nessun progetto da creare per cliente.
>
> ✅ **Gli appuntamenti su Google, in sola uscita (25/09/2026)**. Chi collega il
> proprio account vede i propri appuntamenti del CRM nel proprio Google
> Calendar. Dal Google al CRM non torna niente. Vedi
> [più sotto](#gli-appuntamenti-su-google-in-sola-uscita).

## Come funziona

Google, come Meta, pretende che il redirect URI combaci **esattamente** e non
ammette wildcard: stesso problema, stessa soluzione. Il redirect punta all'hub,
che rilancia il code al site del cliente con lo state firmato; il site scambia
il code e salva il refresh token.

```
cliente.it → Settings → Google Calendar → "Connetti"
           → schermata Google (scelta account + consenso)
           → Google redirige all'HUB
HUB        → verifica la firma, rilancia il code a cliente.it
cliente.it → scambia il code → refresh token salvato sul suo Google Calendar
```

Il token finisce nel doctype **`Google Calendar` del framework**, uno per
utente. Da lì il CRM copia gli appuntamenti su Google (sotto) e, se un manager
l'ha acceso, il controllo "quando sono occupato" del booking chiede a Google gli
orari liberi. `Google Settings` viene compilato con le credenziali del bench
**prima** di creare il record: il framework non salva un `Google Calendar`
finché `Google Settings` è spento, e su un sito nuovo lo è fino alla prima
connessione. Prima di questa correzione la prima connessione di un sito falliva
con "Enable Google API in Google Settings".

Il codice chiede `access_type=offline` **e** `prompt=consent`: senza entrambi
Google non restituisce il refresh token alla seconda autorizzazione, e il
collegamento morirebbe alla prima scadenza.

## Il popup

Il pulsante apre una finestra popup, non porta via l'intero CRM: la pagina
dietro resta dov'e' con il suo stato. Alla fine del giro Google atterra su
`/oauth_connected?provider=google`, che comunica l'esito alla finestra che
l'ha aperta e si chiude; la schermata ricarica il proprio stato da sola. Se il
browser blocca il popup si naviga come prima e la stessa pagina rimanda alle
impostazioni. E' la stessa pagina che chiude il login di Facebook, con
`provider` diverso.


## Configurazione (una volta sola)

`common_site_config.json`, accanto alle chiavi Meta:

```json
{
  "google_client_id": "....apps.googleusercontent.com",
  "google_client_secret": "..."
}
```

`meta_hub_url` e `meta_relay_secret` sono riusati: **un hub solo per tutto**.

Su console.cloud.google.com, una volta:
1. Progetto + **API Google Calendar** abilitata.
2. **Schermata consenso OAuth**: tipo *Esterno*, nome e logo dell'agenzia
   (li vede il cliente), email di supporto, dominio autorizzato.
3. **Credenziali → ID client OAuth → Applicazione web**, con un solo
   *URI di reindirizzamento autorizzato*:
   `https://<hub>/api/method/crm.integrations.google.oauth.callback`

## La verifica Google (più leggera di Meta)

Lo scope Calendar è **sensibile**, non *restricted*: serve la verifica OAuth
ma **non** il security assessment CASA (quello vale per Gmail e Drive). Servono
nome/logo coerenti con la schermata di consenso, la proprietà del dominio
verificata in Search Console e un video dimostrativo del flusso. Tempi
dichiarati: circa 10 giorni dalla domanda completa.

⚠️ **Prima della verifica** l'app mostra la schermata "app non verificata" ed è
limitata a **100 utenti per la vita del progetto**. E soprattutto: in modalità
*Testing* Google **invalida i refresh token dopo 7 giorni** — il calendario si
scollegherebbe ogni settimana. Quindi il progetto va messo in **Produzione**
(anche non ancora verificato) prima di darlo ai clienti.

## Dove si connette

Settings → **Booking → Google Calendar**, non sotto Meta: è una connessione
**per utente**, non per sito — ogni commerciale collega il proprio calendario.
Per questo la voce è visibile a tutti, non solo ai manager, e il banner nelle
impostazioni del Booking porta allo stesso flusso. Anche il pulsante in alto
nella pagina Calendario apre lo stesso popup; a connessione fatta porta alla
pagina delle impostazioni, dove si vede come va la copia.

## Gli appuntamenti su Google, in sola uscita

Ognuno vede **i propri** appuntamenti (quelli in cui è tra i professionisti) nel
**proprio** account Google, anche sul telefono. La copia va in un senso solo:
il CRM scrive, Google mostra. Un appuntamento si prende, si sposta e si annulla
nel CRM. Un evento cancellato su Google torna al riallineamento orario; uno
modificato su Google viene riscritto alla prossima modifica dell'appuntamento.

### Dove finiscono

In un **calendario a parte** nell'account Google dell'utente, creato dalla
prima sincronizzazione e chiamato come il CRM ("Studio Bianchi (CRM)", dal
nome in Impostazioni → Branding). L'utente può colorarlo, nasconderlo o
condividerlo, e i suoi eventi personali non si mescolano con quelli del CRM.
Il suo id sta nel campo `crm_calendar_id` aggiunto al `Google Calendar` del
framework, non in `google_calendar_id`: quello appartiene alla sincronizzazione
del framework e condividerlo riporterebbe le copie nel CRM come Event.

### Cosa c'è nell'evento

| Campo Google | Dal CRM |
|---|---|
| Titolo | il titolo dell'appuntamento ("Pulizia viso — Mario Rossi") |
| Inizio / fine | gli orari, nel fuso della pianificazione |
| Luogo | il luogo o il link della riunione |
| Descrizione | i clienti con telefono ed e-mail, gli altri professionisti, le note, le note del cliente, il link che apre l'appuntamento nel CRM |

**Nessun invitato**: i clienti non ricevono niente da Google. Gli appuntamenti
annullati spariscono; completati e "non presentato" restano, come nell'agenda.
Un appuntamento senza professionisti va a chi l'ha creato, come il suo Event.

### Quando

- **Subito**: salvare o eliminare un appuntamento mette in coda una scrittura per
  le persone coinvolte, dopo il commit. Chi viene tolto da un appuntamento perde
  la sua copia.
- **Alla connessione**: parte una sincronizzazione completa, dalla quale nasce il
  calendario.
- **Ogni ora** (`hourly_long`): ogni calendario collegato viene riallineato al
  CRM. Recupera quello che una scrittura fallita, un worker riavviato o un
  evento cancellato su Google hanno lasciato indietro. Scrive solo gli eventi
  cambiati nel CRM (ognuno porta un'impronta di quello che il CRM ha scritto),
  prima i prossimi e poi i passati.

La finestra del riallineamento va da 14 giorni fa a 180 giorni avanti. Oltre, gli
eventi già su Google restano come sono, e un appuntamento salvato viene
comunque scritto.

### Perché non la sincronizzazione del framework

Frappe ha la sua (`Event` ↔ `Google Calendar`), ma manda i partecipanti
dell'Event, cioè i clienti, come invitati Google con `sendUpdates="all"`: ogni
appuntamento farebbe partire un invito via e-mail da Google. In più rilegge
Google dentro il CRM. Per questo il pull del framework resta spento sui
calendari collegati (lo spegne anche la patch `google_calendar_only_goes_out`)
e la copia la fa il CRM con chiamate sue (`crm/integrations/google/`).

### Quando qualcosa non va

La pagina delle impostazioni mostra quanti appuntamenti ci sono su Google,
l'ultimo aggiornamento, l'errore se c'è, e ha un pulsante "Sincronizza ora".
Se Google revoca l'accesso (password cambiata, accesso tolto dall'account, o il
progetto è ancora in *Testing*: vedi sopra) la copia si ferma e chiede di
ricollegarsi; si riaccende da sola alla nuova connessione. Un errore finisce nel
log degli errori una volta sola, non a ogni passaggio orario.

Se l'utente cancella il calendario del CRM da Google, al passaggio successivo
ne viene creato uno nuovo con tutti gli appuntamenti. Per smettere si usa
"Disconnetti" nel CRM: gli eventi già su Google restano dove sono.

### File

| File | Cosa fa |
|---|---|
| `crm/integrations/google/calendar_mirror.py` | Puro: chi riceve la copia, com'è fatto l'evento, il riallineamento, il client REST |
| `crm/integrations/google/sync.py` | Hook sugli appuntamenti, job, token, calendario, stato |
| `crm/integrations/google/oauth.py` | Il popup di connessione; accende la copia in sola uscita |
| `crm/integrations/google/api.py` | Stato, "Sincronizza ora", disconnessione |
| `crm/tests/test_google_calendar_mirror.py` | Test puri, con un finto Google |
| `crm/tests/test_google_calendar_sync.py` | Test d'integrazione (bench) della copia |
| `crm/tests/test_google_calendar_connection.py` | Test d'integrazione della connessione |
