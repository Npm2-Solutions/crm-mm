# 09 — Social Planner (agenda social)

> ✅ **IMPLEMENTATO**. Semplificato il 03/09/2026: **un solo modo per
> pubblicare**, direttamente da Frappe verso Meta. Postiz, Ayrshare e il
> provider "Manual" sono stati rimossi (con patch che elimina
> `CRM Social Settings` dai site esistenti).

## Come funziona

Frappe pubblica da sé con la **Graph API**, riusando i page token ottenuti
dall'unica connessione Meta (Settings → Integrations → Meta, la stessa dei Lead Ads):

| Destinazione | Chiamata |
|---|---|
| Facebook Page — solo testo | `POST /{page}/feed` |
| Facebook Page — immagine | `POST /{page}/photos` |
| Facebook Page — video | `POST /{page}/videos` |
| Instagram Business | `POST /{ig}/media` (container) → polling `status_code` fino a `FINISHED` → `POST /{ig}/media_publish` |

Instagram richiede sempre un media; i video vengono pubblicati come **Reels**.
Scope OAuth aggiunti per la pubblicazione: `pages_manage_posts`,
`instagram_basic`, `instagram_content_publish`.

## Collegamento profili (zero id da incollare)

I profili arrivano **da sé** al termine dell'OAuth Meta: un `CRM Social
Account` per ogni pagina Facebook e per ogni account Instagram Business
collegato (letto da `instagram_business_account` in `/me/accounts`). L'upsert è
idempotente (match per piattaforma + id) e ogni profilo tiene il link alla
`Facebook Page` da cui prende il token per pubblicare.

Settings → **Social Planner → Profiles** (dal 24/09/2026, vedi
[27](./27-impostazioni-canali-integrazioni.md)) elenca le **sorgenti** — oggi
solo Meta, registro in `crm/social/sources.py` — e sotto i profili con
l'interruttore "nel planner". **"Refresh profiles"** (`crm.api.social.sync_profiles`)
riallinea subito i profili alle Pagine già note e fa rileggere le Pagine da
Facebook in background.

## Componenti

- DocType: `CRM Social Account` (piattaforma Facebook/Instagram, id e pagina
  in sola lettura: li scrive l'import), `CRM Social Post` (contenuto, media,
  stato, schedule, ricorrenza, approvazioni) + child `CRM Social Post Target`
  (profilo, override per profilo, esito).
- `crm/social/publisher.py`: pubblicazione + scheduler ogni 2 minuti
  (`process_due_posts`), esiti per target, **ricorrenze** (clona la prossima
  occorrenza), notifica realtime.
- `crm/social/accounts.py`: import/upsert dei profili dalle pagine Meta.
- **Flusso approvazioni**: Sales User → bozza / "Request approval";
  Sales Manager → Approva / Programma / Pubblica subito.
- Pagina **`/social`**: calendario mensile Espresso (header giorni, oggi
  evidenziato, chip con pallino per piattaforma e bordo colorato per stato,
  overflow "+N" con dialog del giorno, legenda, CTA "Connect profiles");
  composer con chip profilo, contatore caratteri, anteprima media, errori
  per-target sui post falliti.
- Test: `crm/tests/test_social.py` (pubblicazione, fallimento con errore,
  ricorrenza, import profili FB/IG, IG senza media).

## Setup

1. Settings → **Integrations → Meta**: App ID/Secret, solo se l'app non è
   fornita centralmente (il webhook leadgen si configura da solo). Lo vede solo
   un amministratore.
2. **"Connect with Facebook"** → autorizza pagine e account IG collegati.
3. Settings → **Social Planner → Profiles**: i profili ci sono già; si spengono
   quelli da non offrire nel planner.
4. Si pubblica.

## Limiti noti

- **Solo Facebook e Instagram.** LinkedIn, TikTok, YouTube, GBP, Threads,
  Bluesky richiederebbero ognuno app e review dedicate (LinkedIn Community
  Management API: 1–4 mesi, solo entità legali; TikTok audit; YouTube audit
  con quota 6 upload/giorno). Da valutare come fase 2, se servono davvero.
- Instagram: niente pubblicazione di caroselli/storie (solo post singolo e
  Reels), come da limiti della Content Publishing API.
- Non incluso: bulk CSV, RSS-to-post, gestione commenti, analytics per post,
  viste settimana/lista.
