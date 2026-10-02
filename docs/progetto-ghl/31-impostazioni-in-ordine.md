# 31 — Le impostazioni in ordine: undici gruppi, una voce per cosa

> ✅ **FATTO (01/10/2026)**. Le Impostazioni avevano 48 voci in sedici gruppi (51
> con quelle dell'agenzia), cinque gruppi di una voce sola e voci finite dove
> capitava. Ora il manager ne vede 33 in undici gruppi, e ogni gruppo è una parte
> del lavoro del centro. Nessuna pagina è sparita: le pagine dello stesso
> argomento sono diventate le schede di una voce, come Meta (doc 27), e i vecchi
> nomi aprono ancora la pagina giusta, sulla sua scheda.

## Il problema

Il doc 27 aveva messo in ordine Meta, WhatsApp e il Social Planner, e quella parte
funzionava: un gruppo per canale, Meta una pagina con le sue schede sotto
Integrazioni. Il resto era cresciuto una pagina alla volta, ognuna dove sembrava
giusto il giorno in cui era nata:

- **gruppi di una voce sola**: Piani (Esercizi), Clinica (Alimenti), Social
  Planner (Profili), Sito web (Sito web), Personalizzazione (Home Actions);
- **voci nel gruppo sbagliato**: i Consensi delle persone sotto "Gestione utenti",
  il Piano del centro pure; il Google Calendar *personale* sotto "Prenotazioni";
  le "Novità nell'area clienti" fra le Integrazioni; i Moduli, i link tracciati e
  il tracciamento sotto "Automazioni e regole";
- **un argomento in tante voci**: otto voci nell'Agenda, sei nella Fatturazione,
  quattro nelle Prenotazioni, "Invite User" accanto a "Users" che ha già il suo
  pulsante "Invita";
- **nomi che non dicevano cosa c'era dentro**: "General" erano le regole delle
  conversazioni, "Home Actions" il menu sotto il nome del centro;
- **due lingue nello stesso menu**: in italiano metà delle voci restavano in
  inglese ("Booking", "Team rota", "Issuing company"), e "Accounts" dell'email era
  tradotto "Contabilità".

## La nuova struttura

Il gruppo è una parte del lavoro del centro, quelle del menu dell'app: tu, il
centro, l'agenda, le persone che segue, le trattative, ogni canale, il marketing,
la fatturazione, quello che si collega da fuori. La voce è una cosa da impostare;
una cosa con più lati è una pagina sola con le sue schede in alto, disegnate come
quelle della scheda di una persona (Attività, Email, Note…).

```
Il tuo account     Profilo · Preferenze · Google Calendar
Il centro          Generale [Nome e logo · Conversazioni · Dashboard · Menu · Formati*]
                   Utenti [Utenti · Invita · Gerarchia] · Funzionalità (doc 36)
Agenda             Servizi [Servizi · Listini · Abbonamenti]
                   Orari e turni [Orari e regole · Turni del team]
                   Sale e attrezzature · Calendario e promemoria · Lista d'attesa
                   Prenotazione online [Servizi e persone · Pagina e regole · Piattaforme]
Clienti            Moduli · Consensi · Area clienti · Librerie [Esercizi · Alimenti]
Trattative         Pipeline · Assegnazione [Regole · Tempi di risposta]
E-mail             Account · Modelli
WhatsApp           Numeri · Modelli
Telefono           Telefonia · Script delle chiamate
Marketing          Sito Web · Social Planner · Tracciamento [Tracciamento dei contatti · Link tracciati]
Fatturazione       Azienda emittente · Servizi e professionisti [Servizi fatturabili ·
                   Professionisti · Qualifiche] · Connessione al provider · Opzioni
Integrazioni       Meta · ERPNext* · Sigillo e marca temporale* · Assistente
```

`*` dell'agenzia. Con la clinica accesa "Clienti" si legge **Pazienti** e "Area
clienti" **Area pazienti** (`crm/clinica/parole.py`); *Deals* si legge
"Trattative" ([doc 50](./50-trattative-e-preventivi.md)).

- **Email, WhatsApp e Telefono hanno la stessa forma**: da dove si scrive, cosa si
  manda. Telefonia è uscita dalle Integrazioni, gli script delle chiamate dalle
  Vendite.
- **Il tuo account** tiene quello che è di ognuno: il Google Calendar si collega
  persona per persona.
- **Il centro**: chi è (nome e logo), come si comporta l'app (conversazioni,
  dashboard, menu, formati), chi ci lavora (utenti, inviti, gerarchia), cosa ha
  (il piano).
- **Clienti**: quello che le persone compilano e firmano, a cosa acconsentono, la
  loro area, con cosa si scrivono i loro piani.
- **Fatturazione**: l'azienda ha già le sue schede (azienda, fatturazione,
  documenti, trasmissione, sanitario), quindi resta una voce sola, senza una
  seconda fila sopra; la connessione al provider è una voce sua.
- **I titoli delle pagine dicono il nome della voce o della scheda**: "Brand
  Settings" è diventato "Nome e logo", "General Settings" "Conversazioni", "Home
  Actions" "Menu", "System Defaults" "Formati", "SLA Policies" "Tempi di
  risposta".

### Chi vede cosa

Ogni voce e ogni scheda chiede la capacità della sua schermata (doc 30), come
prima. Una voce resta se resta almeno una scheda; con una scheda sola non c'è la
fila delle schede, la voce è quella pagina.

| Livello | Cosa vede |
|---|---|
| Manager | 33 voci, tutto tranne le pagine dell'agenzia |
| Segreteria | Il tuo account; Agenda: Orari e turni (i turni del team), Sale e attrezzature; Telefono |
| Operatore | Il tuo account; Agenda: Orari e turni (i suoi turni); Telefono |
| Marketing | Il tuo account; Clienti: Moduli; i modelli di Email e WhatsApp; Telefono; Marketing; Integrazioni: Meta |
| Amministrazione | Il tuo account; Telefono; Fatturazione |
| Direzione sanitaria | Il tuo account; Clienti: Moduli, Librerie; Telefono; Integrazioni: Assistente |
| Agenzia | Come il manager, più Formati, ERPNext, Sigillo e marca temporale |

### La voce dell'operatore si apre

Percorrendo il menu di ogni livello è venuto fuori che l'operatore aveva una
voce sola nell'Agenda, i turni, e ogni chiamata dietro quella pagina lo
rifiutava (`agenda.turni` chiesto per tutto il centro). La capacità gli dà i
suoi turni e il permesso del documento pure (`documenti.DI_CHI`): ora la pagina
gli mostra **I tuoi turni**, la sua settimana, il pulsante degli orari apre i suoi, e il
server gli lascia cambiare orari e giorni liberi suoi e di nessun altro
(`appointments.turni`); come lo mostra la pagina di prenotazione resta del
manager.

### I link che esistevano restano validi

Ogni pagina tiene il nome che aveva, come chiave di una voce o di una scheda (o
come alias): `?settings=Price Lists` apre Servizi sulla scheda Listini,
`?settings=Invite User` Utenti sulla scheda Invita, `?settings=Lead quality` Meta
sulla sua scheda. Valgono quindi i link costruiti sul server (il ritorno da
Facebook e da Google, la connessione di WhatsApp, i suggerimenti della dashboard)
e i pulsanti dell'app che portano a una pagina delle impostazioni. Scegliere una
scheda è come aprire quel link: il nome della pagina diventa quello della scheda.

I testi che indicano una strada nelle impostazioni la indicano nuova: "Agenda →
Orari e turni → Turni del team", "Impostazioni → Telefono → Script delle
chiamate", "Impostazioni > Agenda > Servizi > Abbonamenti".

## Come è fatto

| File | Cosa fa |
|---|---|
| `frontend/src/utils/impostazioni.js` | Il menu come dati: gruppi, voci, schede, chi vede cosa (`condition` sulla sessione: `puo`, `ambito`, `whatsapp`, `verticale`). `menuDi()` il menu di una persona, `trova()` la voce e la scheda che un nome apre, `pagine()` tutte le pagine — puro, testato |
| `frontend/src/components/Settings/Settings.vue` | Il modale: con cosa si disegna ogni pagina (`PAGINE`) e ogni categoria (`ICONE`, dal doc 35), il resto lo legge dai dati |
| `frontend/src/components/Settings/SettingsHub.vue` | Una voce con più schede: la fila in alto (frecce comprese), la pagina sotto che scorre; la scheda aperta è `activeSettingsPage` |
| `crm/tests/test_impostazioni.py` | Ogni pagina che il server nomina esiste nel menu |

Una pagina nuova: una riga nel menu (`utils/impostazioni.js`, nel gruppo della
parte del lavoro a cui appartiene, come voce o come scheda di una voce che c'è
già), una in `PAGINE`, la sua riga di descrizione (doc 35), la traduzione. Un gruppo nuovo solo
per una parte del lavoro che l'app non ha ancora.

## Test

- `tests/unit/impostazioni.test.js`: il menu di ogni livello parola per parola,
  le 51 pagine tutte presenti e una volta sola, i 54 nomi vecchi che aprono la
  voce e la scheda giuste, WhatsApp solo dove c'è, gli Alimenti solo con la
  clinica, l'operatore che ha una scheda sola.
- `crm/tests/test_impostazioni.py`: i nomi delle pagine nelle `Feature` della
  dashboard, nei ritorni OAuth, nella connessione di WhatsApp, nelle sorgenti del
  Social Planner, nel widget delle piattaforme.
- Nel browser (Playwright): ogni voce e ogni scheda aperte dal manager, i nomi
  vecchi dall'indirizzo, il menu di ogni livello, il telefono in chiaro e in
  scuro.
