# Progetto GHL-Parity — Frappe CRM come piattaforma all-in-one

> **Obiettivo**: portare questo fork di Frappe CRM (`crm-mm`) alla parità funzionale
> con GoHighLevel — funnel, marketing automation omnicanale, telefonia/SMS/inbox
> unificata, corsi & membership, calendari di prenotazione, white-label SaaS e
> reputation management — riusando al massimo l'ecosistema open-source Frappe.
>
> Ricerca condotta online ad **agosto 2026** (repo, docs ufficiali, changelog API);
> ogni modulo cita le fonti.

## ⚖️ Decisioni di scope (31/08/2026)

Scope ridotto rispetto alla parità completa, su decisione del committente:

- ✅ **IN SCOPE**: Workflow automation (02), SMS 2-way + inbox unificata + power
  dialer (03), Booking/calendari (05) — **si parte dal Booking**. Del modulo 06
  restano solo gli **script di provisioning + snapshot** (golden site) come
  strumento interno: ogni cliente ha già il proprio site, gestito manualmente.
- ❌ **FUORI SCOPE**: funnel builder (01), corsi/LMS (04), reputation (07),
  canali Meta Messenger/IG (parte di 03), signup pubblico/billing/rebilling e
  white-label aggiuntivo (parte di 06). I documenti restano come riferimento
  se lo scope dovesse riaprirsi.

### Aggiornamento (06/09/2026) — sito vetrina

Riapertura **parziale e ridotta** del modulo 01: non il funnel builder, ma un **sito
web semplice alimentato dai dati del CRM** (servizi, prodotti, form, prenotazioni).
Proposta e alternative in [16](./16-sito-web-vetrina.md); funnel, A/B test e checkout
restano fuori scope.

L'architettura scelta è quella già anticipata qui sopra: **Frappe Builder come app
accanto al CRM**, con i componenti collegati al CRM spediti da `crm/builder_files/`.

## Indice dei documenti

| Doc | Modulo | Stato | Verdetto sintetico |
|---|---|---|---|
| [00](./00-analisi-stato-attuale.md) | Analisi stato attuale del repo | — | Non si parte da zero: Twilio Voice browser, WhatsApp, scheduler, round-robin nativi |
| [01](./01-funnel-landing-builder.md) | Funnel & Landing Page | ❌ fuori scope | Adottare Frappe Builder (MIT da v1.31) + layer funnel custom |
| [02](./02-marketing-automation.md) | Marketing Automation | ✅ in scope | **Da costruire** (motore enrollment Python + canvas Vue Flow); i canali esistono già |
| [03](./03-telefonia-sms-inbox.md) | Telefonia, SMS, Inbox | ✅ in scope (no Meta) | SMS two-way + inbox unificata + power dialer su Twilio già integrato |
| [04](./04-corsi-membership.md) | Corsi & Membership | ❌ fuori scope | Adottare Frappe LMS; costruire solo drip/abbonamenti/ponte |
| [05](./05-calendari-prenotazioni.md) | Calendari & Booking | ✅ **in scope, primo** | Booking pubblico con disponibilità, buffer, round-robin, reschedule/cancel |
| [06](./06-white-label-saas.md) | White-Label / SaaS | ⚠️ solo provisioning+snapshot | Script interni per creare site clienti preconfigurati; niente billing |
| [07](./07-reputazione-recensioni.md) | Reputation | ❌ fuori scope | Solo Google via GBP API; Facebook API morta (v22) |
| [08](./08-roadmap.md) | Roadmap & effort | aggiornata | Fasi, dipendenze, stime — ricalibrata sullo scope ridotto |
| [13](./13-google-calendar.md) | Google Calendar collegato in un click | ✅ implementato | OAuth gestito dall'agenzia: nessuna credenziale da incollare sul sito cliente |
| [14](./14-agenda-appuntamenti.md) | Agenda interna: multi-persona, stanze, attrezzature, listini | ✅ implementato | Staffing collective/round-robin/per-ruolo, capacità delle risorse, sessioni di gruppo, prezzi condizionati |
| [15](./15-tracciamento-lead.md) | Tracciamento del lead e attribuzione | ✅ implementato | Script esterno, sessioni, primo/ultimo contatto, percorso pagina per pagina |
| [16](./16-sito-web-vetrina.md) | Sito web vetrina integrato nel CRM | ✅ implementato | Frappe Builder installato accanto come **tela**; il CRM resta guscio e dati: componenti spediti da noi con data script, impostazioni e publish nel modale |
| [17](./17-timeline-unificata.md) | Timeline unificata sulla scheda | 📐 proposta | Una schermata al posto di dodici tab: i chip non filtrano soltanto, cambiano vista — chat WhatsApp, thread email — con un solo composer che segue il canale |
| [18](./18-persona-unica.md) | Una persona sola: lead e contatto smettono di essere due | 📐 proposta | Il lead e' la persona, il deal la relazione, il contatto la rubrica: i recapiti vivono in un posto solo e il campo sul lead diventa uno specchio, cosi' i 201 punti che lo leggono non cambiano |
| [19](./19-trattativa-magra.md) | La trattativa magra, come l'opportunita' di GHL | ✅ fatto | L'opportunita' di GHL e' un pannello con i campi, le note, i task e un appuntamento: la nostra trattativa scende da otto tab a quattro, e i file finiscono accanto alle note |
| [20](./20-domini-dei-clienti.md) | Più siti, sul dominio del cliente | 🟡 proposta | Un cliente per site, tanti domini sopra: CNAME come GHL e certificati on-demand, senza configurare nginx a ogni dominio |
| [21](./21-lead-contatto-trattativa.md) | Lead, contatto, azienda, trattativa: cosa significano davvero | ✅ fatto | Verifica contro Salesforce, HubSpot, Pipedrive e GHL: la persona e' unica e permanente, "lead" e' uno stadio. Sei punti dove il codice seguiva ancora il modello opposto |

## Architettura complessiva

```
                       ┌────────────────────────────────────────────────┐
                       │                UN SITO FRAPPE (per tenant)     │
                       │                                                │
  Frappe Builder ──────│──  pagine/funnel pubblici, form → CRM Lead     │
  (app ufficiale, MIT) │                                                │
                       │  ┌──────────────┐   ┌───────────────────────┐  │
  Frappe LMS ──────────│─▶│  crm (fork)  │◀──│  crm_suite (NUOVA app)│  │
  (app ufficiale)      │  │  lead/deal   │   │  ├─ automation  (02)  │  │
                       │  │  twilio voice│   │  ├─ funnels     (01)  │  │
  frappe_whatsapp ─────│─▶│  whatsapp api│   │  ├─ inbox/sms   (03)  │  │
  (community, MIT)     │  │  email       │   │  ├─ dialer      (03)  │  │
                       │  └──────────────┘   │  ├─ membership  (04)  │  │
  frappe/payments ─────│──  gateway          │  ├─ booking     (05)  │  │
  (app ufficiale, MIT) │                     │  ├─ reputation  (07)  │  │
                       │                     │  └─ saas        (06)* │  │
                       └─────────────────────┴───────────────────────┴──┘
                              * il modulo saas vive sul sito "agency" centrale

  Infrastruttura: frappe_docker + bench multi-sito + DNS wildcard + TLS wildcard
  Provisioning nuovi tenant: bench new-site + restore del golden site ("snapshot")
```

### Principi decisi

1. **Estendere, non forkare oltre**: tutto il codice nuovo va nella nuova app
   `crm_suite`, installata accanto a `crm`. Il fork del CRM resta minimo
   (branding + hook points) per poter continuare a fare pull da upstream.
2. **Adottare le app ufficiali dove esistono** (Builder, LMS, payments,
   frappe_whatsapp): il costo diventa integrazione, non sviluppo.
3. **Un solo channel-adapter layer** (`send(channel, recipient, payload)`)
   condiviso da workflow engine, inbox, booking e reputation.
4. **Il workflow engine (modulo 02) è la spina dorsale**: quasi ogni altro modulo
   vi si aggancia come trigger o come azione. Va costruito per primo.
5. Stack invariato: Python/Frappe backend, Vue 3 + frappe-ui frontend, MariaDB,
   Redis/scheduler per i job.

### Licenze (sintesi)

- Frappe Framework, Builder ≥1.31, payments, frappe_whatsapp, Vue Flow: **MIT/BSD**.
- CRM (questo fork), LMS, telephony, frappe-appointment: **AGPL-3.0** → l'app
  `crm_suite` va considerata AGPL; il modello di business (vendere il servizio
  hosted, non licenze) è pienamente compatibile, con obbligo di rendere
  disponibile il sorgente modificato agli utenti del servizio (dettagli nel
  [modulo 06](./06-white-label-saas.md), inclusa la questione trademark).

## Azioni con lead time lungo — da avviare SUBITO

Ricalibrate sullo scope ridotto:

1. **Twilio**: numeri SMS-capable per i clienti, e A2P 10DLC solo se si punta al
   mercato USA; registrazione mittente alfanumerico dove applicabile in EU.
2. **Google OAuth (Google Calendar)**: credenziali OAuth per il busy-block dei
   calendari di booking (già supportato dal framework).
3. ~~GBP API, Meta Business Verification~~ — non più necessarie (reputation e
   canali Meta fuori scope).
