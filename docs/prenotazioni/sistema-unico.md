# Il sistema di prenotazione unico — progetto

Sintesi delle tre ricerche nella stessa cartella: `modelli-scheduler.md` (GHL, Calendly,
Cal.com, Acuity, Zoho, MS Bookings, SimplyBook, Setmore, Square),
`modelli-gestionali.md` (Fresha, Treatwell, Booksy, Phorest, Timely, Mindbody, Zenoti,
Vagaro, Jane, Cliniko, Doctolib, MioDottore/GipoNext, AlfaDocs, TIMIFY, Planity, Shore,
WeGest) e `modelli-ux-configurazione.md` (ereditarietà delle regole, viste d'insieme,
troubleshooter).

---

## 1. La scelta di fondo

Il mercato usa due modelli:

| | A. "Un calendario per link" | B. "Catalogo di servizi" |
|---|---|---|
| Chi | Calendly, Cal.com, GHL (vecchi calendari) | Fresha, Phorest, Jane, Cliniko, Acuity, Zoho, Square, GHL Services v2 |
| Cosa condividi | un calendario / tipo di evento | una pagina sola, con link filtrati |
| Dove stanno le regole | tutte sul calendario | azienda → servizio → professionista×servizio |
| Problema | proliferazione: "migliaia di calendari", prenotazioni divise, nessuna vista d'insieme, regole per persona impossibili | se le regole stanno su un solo livello si duplicano i servizi (Square, Jane, MS Bookings) |

**GHL stesso è passato da A a B** (Services v2): il modello A non regge per studi e saloni.

**Scelta: modello B, con regole su tre livelli ed eredità visibile.** Nel CRM c'è già il
motore giusto (`CRM Service` + staff + risorse + listini + `CRM Appointment`). I "Booking
Calendars" Calendly-style (`CRM Booking Calendar` / `CRM Booking`) sono il modello A e
vengono assorbiti.

## 2. Il modello dati definitivo

```
Impostazioni agenda (azienda)      orari di apertura, festività, regole online predefinite
 └─ Servizio                       durata, pausa prima/dopo, prezzo, categoria, risorse,
     │                             fasce orarie, modalità staff, regole online (vuoto = eredita)
     └─ Professionista × Servizio  durata, prezzo, prenotabile online, priorità (vuoto = eredita)
Professionista                     orario settimanale, eccezioni, ferie, tetto giornaliero
                                   e settimanale, visibile online, profilo pubblico
Risorsa                            stanza/attrezzatura, capacità, posti, orari
```

- **Un servizio, mai duplicati**: prezzo e durata diversi per professionista sono un'eccezione
  sulla riga professionista×servizio (Fresha, Vagaro, Booksy), non un servizio in più.
- **Regole online su due livelli + eccezione per persona**: le regole (preavviso, orizzonte,
  passo orari, conferma, annullamento/spostamento, tetti per cliente…) hanno un valore
  predefinito in *Impostazioni → Pagina di prenotazione*; il servizio le **eredita** e può
  sovrascriverle. Vuoto = eredita, mai copiato (evita il bug "salvo e tutto diventa
  sovrascritto"). Il risolutore restituisce valore **e provenienza**.
- **Il limite più severo vince** quando due livelli pongono un tetto (Cal.com): tetto del
  servizio, tetto del professionista, tetto globale per cliente.
- **Disponibilità** = orario del professionista ∩ fasce del servizio − ferie/eccezioni −
  impegni (appuntamenti, eventi, Google) ∩ risorsa libera ∩ regole online. Calcolata sempre
  dal vivo (niente copie di slot: è la lamentela n.1 su MioDottore).

## 3. Un solo sito di prenotazione

`/prenota` è l'unica pagina. Tutto il resto sono **link filtrati**, non calendari:

| Link | Apre |
|---|---|
| `/prenota` | menu completo |
| `/prenota?categoria=Estetica` | solo una categoria |
| `/prenota?servizio=pulizia-viso` | un servizio |
| `/prenota?professionista=<id>` | pagina del professionista: solo i suoi servizi, lui preselezionato |
| `/prenota?servizio=…&professionista=…` | entrambi |
| `…&nome=&email=&telefono=` | dati precompilati (campagne, CRM) |
| `…&utm_*` | attribuzione campagne (già tracciata) |
| `&embed=1` | per iframe nel sito |

- **Generatore di link** nelle impostazioni: sceglie categoria/servizio/professionista, dà
  URL, QR code e codice di incorporamento.
- **Compatibilità**: ogni vecchio `/book/<calendario>` reindirizza a
  `/prenota?servizio=<servizio migrato>`; `/book` reindirizza a `/prenota`. Nessun link
  già inviato si rompe.

## 4. Le viste d'insieme (quello che GHL non ha)

1. **Matrice "Chi fa cosa"** — servizi (raggruppati per categoria) × professionisti. Ogni
   cella: non lo fa / lo fa / lo fa con eccezioni (prezzo/durata propri, non online).
   Spunta di riga e colonna in blocco, clic sulla cella per le eccezioni. Avvisi: servizio
   che nessuno fa, servizio che fa una sola persona. *Nessun gestionale analizzato ce l'ha.*
2. **Turni del team** — professionisti × giorni della settimana con i loro orari, ferie ed
   eccezioni in evidenza; modifica rapida.
3. **"Perché non è disponibile?"** — scegli servizio, giorno e ora: per ogni professionista
   il primo motivo che blocca (fuori orario, ferie, già impegnato con…, tetto giornaliero,
   stanza occupata, preavviso, tetto del servizio…) e da quale impostazione viene, con il
   link per cambiarla. Stile Calendly Troubleshoot.
4. **Regole effettive** — in ogni servizio l'elenco delle regole online in vigore con la
   provenienza ("predefinita" / "di questo servizio").

## 5. Cosa assorbe cosa

| Oggi | Diventa |
|---|---|
| Booking Calendar (durata, membri, orari, prezzo, pause, preavviso, orizzonte, luogo) | un Servizio prenotabile online con quei valori; membri = professionisti del servizio |
| Pagina `/book/<route>` e `/book` | redirect a `/prenota` |
| `CRM Booking` (prenotazioni fatte) | restano come storico e continuano a occupare l'agenda; le nuove sono Appuntamenti |
| Automazioni "Booking creato/annullato/…" | scattano anche per gli appuntamenti prenotati online |
| Blocco "Prenota" del sito (`booking_calendar`) | punta al link `/prenota` del servizio |
| Impostazioni → Booking Calendars | sostituita da Pagina di prenotazione + Chi fa cosa + Link |

## 6. Fasi

**Fase 1 — sistema unico — FATTA**
- eccezioni professionista×servizio (durata, prezzo, online, priorità) nel motore
- regole online predefinite + eredità con provenienza
- tetto settimanale e visibilità online per professionista
- `/prenota` con categoria, pagina professionista, precompilazione
- migrazione Booking Calendars → Servizi, redirect `/book`, automazioni, blocco sito
- impostazioni riorganizzate: Pagina di prenotazione (con regole predefinite e generatore
  di link), matrice Chi fa cosa, turni del team, "Perché non è disponibile?"

**Fase 2**
- tempi di posa / fasi del servizio (il professionista è libero durante la posa)
- più servizi in una prenotazione (carrello), con stesso o diverso professionista
- fasce orarie riservate a certi servizi dentro l'orario del professionista (es. "solo prime
  visite il martedì mattina", come Doctolib/MioDottore)
- sedi multiple

**Fase 3**
- caparre / carta a garanzia contro i no-show, lista d'attesa, moduli di consenso
  pre-visita, questionario "aiutami a scegliere", app/Reserve with Google
