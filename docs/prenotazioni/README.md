# Prenotazione dei servizi e piattaforme esterne

Questa guida copre la prenotazione online dei servizi (menu servizi → professionista →
orario), i limiti configurabili e i connettori verso le piattaforme dove i clienti
prenotano già: MioDottore, Treatwell/Uala, Fresha, Elty e le altre.

Il rapporto completo sulle API delle piattaforme, con le fonti e il livello di
verifica di ogni dato, è in [ricerca-piattaforme.md](./ricerca-piattaforme.md).

---

## 1. Un solo sistema di prenotazione

C'è **una sola pagina**, `/prenota`, e un solo motore (quello dell'agenda: servizi,
professionisti, stanze, listini, conflitti). Non esistono più "calendari" da moltiplicare:
ogni link è un **filtro** della stessa pagina. Il perché della scelta, con il confronto tra
GHL, Calendly, Cal.com, Fresha, Phorest, Cliniko e gli altri, è in
[sistema-unico.md](./sistema-unico.md).

I vecchi *Booking Calendars* (stile Calendly) sono stati convertiti in servizi dalla patch
`one_booking_system`: stessa durata, stessi membri, stessi orari, stesso prezzo e luogo;
quelli che non comparivano nel menu `/book` diventano servizi *solo tramite link*.
`/book/<calendario>` reindirizza a `/prenota?servizio=…`, `/book` a `/prenota`; le
prenotazioni fatte prima restano gestibili dal loro link e continuano a occupare l'agenda.
Le automazioni *Booking …* scattano per le prenotazioni online dei clienti.

### Link

| Link | Apre |
|---|---|
| `/prenota` | il menu dei servizi (categorie, ricerca) |
| `/prenota/<servizio>` o `?servizio=<slug>` | direttamente un servizio |
| `/prenota/p/<id>` o `?professionista=<id>` | la pagina del professionista: foto, titolo, bio, solo i suoi servizi |
| `/prenota/c/<categoria>` o `?categoria=` | una categoria |
| `&nome=&email=&telefono=` | modulo precompilato (campagne, CRM) |
| `&utm_source=…` | attribuzione (già tracciata dal CRM) |
| `&embed=1` | per un iframe nel sito (il tracker gli passa il visitatore) |
| `?token=…` | gestione della prenotazione: annulla / sposta entro le regole |

Il **generatore di link** (*Impostazioni → Booking → Pagina di prenotazione*) costruisce il
link, il **QR code** scaricabile e il **codice da incorporare**. Il blocco *Prenota* del sito
accetta un servizio, un vecchio calendario o niente (tutto il menu).

### Il percorso del cliente

Servizio → professionista (o "chiunque", o già scelto dal link) → giorno e ora (solo i
giorni liberi, orari per fascia, scorciatoia *Primo orario libero*) → dati e consenso →
conferma con Google/Outlook e `.ics`. Prezzi "da …" e durate min–max quando i
professionisti differiscono.

## 2. Dove stanno le regole

Tre livelli, sempre visibili, mai copiati:

1. **Pagina di prenotazione** (*Impostazioni → Booking*): le regole online predefinite
   (preavviso, orizzonte, passo degli orari, conferma automatica o su approvazione,
   stesso giorno fino a, telefono obbligatorio, annullamento/spostamento e loro
   preavviso, spostamenti massimi, prenotazioni per cliente al giorno). Accanto a ognuna:
   quanti servizi la seguono e quali hanno un valore proprio.
2. **Servizio** (*Agenda → Servizi → Prenotabile online*): ogni regola mostra il valore
   predefinito in grigio oppure è *personalizzata*, con *Usa predefinita* per tornare
   indietro. In più le regole solo del servizio: finestra stagionale, tetti al giorno /
   settimana / contemporanei, chi può prenotare (nuovi/già clienti), prenotazioni future
   per cliente, giorni tra due visite, domanda e istruzioni, posti per prenotazione,
   scelta del professionista, prezzo visibile, *solo tramite link*.
3. **Professionista × servizio** (*Agenda → Chi fa cosa*, o l'editor del servizio): durata
   e prezzo propri, prenotabile online sì/no, priorità, ruolo. Mai duplicare un servizio
   per cambiare prezzo o durata a una persona.

Il **professionista** (*Agenda → Turni del team*) ha orario settimanale, eccezioni e ferie,
tetto giornaliero e settimanale, visibile online sì/no, titolo e bio pubblici.

Quando più livelli pongono un tetto vince **il più severo** (es. tetto del servizio e tetto
globale per cliente).

## 3. Le viste d'insieme

- **Chi fa cosa** — matrice servizi × professionisti: clic su una cella vuota per
  assegnare, su una piena per durata/prezzo/online propri; spunta di riga (tutti/nessuno),
  menu di colonna (assegna tutto, togli tutto, *copia i servizi di…*). Avvisi: servizio
  che nessuno fa, che fa una sola persona, online ma nessuno lo prende online.
- **Turni del team** — la settimana di tutti: orari, ferie, ore extra e quanto è pieno
  ogni giorno.
- **Perché non è disponibile?** — servizio + giorno + ora (come cliente online o come
  reception): per ogni professionista il primo motivo che blocca (fuori orario, ferie,
  impegnato con…, tetto, stanza occupata, preavviso, tetto del servizio…) e dove
  cambiarlo.

## 4. Piattaforme esterne

Si configurano in *Impostazioni → Booking → Piattaforme di prenotazione → Collega una
piattaforma*. Ogni connessione ha:

- **credenziali**, diverse per piattaforma; la schermata mostra solo i campi necessari e
  le istruzioni per ottenerli;
- **mappatura**: quale servizio, professionista o stanza del CRM corrisponde a ogni
  elemento della piattaforma. Se l'API lo permette, *Carica dalla piattaforma* compila
  l'elenco. Un servizio con lo stesso nome non ha bisogno di mappatura; gli altri usano il
  servizio predefinito;
- **opzioni**: importa le prenotazioni, collega il cliente come lead, blocca sulla
  piattaforma gli orari già occupati nel CRM, annulla anche sulla piattaforma.

### Che cosa è possibile con ciascuna

| Piattaforma | Settore | Accesso | Entrata prenotazioni | Uscita (blocchi / annullamenti) |
|---|---|---|---|---|
| **MioDottore (Docplanner)** | medico | solo partner certificati | API + notifiche push | pause (*breaks*), annullamento |
| MioDottore (email) | medico | nessuno | email di notifica | feed "Occupato" |
| **Treatwell / Uala** | bellezza | chiuso | email di notifica | feed "Occupato" in *Calendario esterno* |
| **Fresha** | bellezza | chiuso | email (o link di esportazione) | feed "Occupato" importato come tempo bloccato |
| Booksy | bellezza | partner | API + webhook | *time off*, annullamento |
| **Elty** | medico | chiuso (solo gestionali partner) | email di notifica | feed "Occupato" |
| iDoctors | medico | chiuso | email + Google Calendar | via Google Calendar |
| Doctolib (ex Dottori.it) | medico | partner | email di notifica | — |
| Top Doctors, Pazienti.it | medico | chiuso | email di notifica | — |
| SimplyBook.me | generale | pubblico | API + webhook (verificato rileggendo dall'API) | note di calendario bloccanti, annullamento |
| Calendly | generale | pubblico | API + webhook firmato | annullamento (i blocchi passano da Google Calendar) |
| Cal.com | generale | pubblico | API + webhook firmato | registra il feed "Occupato" come calendario, annullamento |
| Acuity Scheduling | benessere | pubblico | API + webhook firmato | blocchi, annullamento |
| Microsoft Bookings | generale | pubblico (Graph) | API (polling) | annullamento |
| TIMIFY | generale | pubblico | API + webhook | annullamento |
| Setmore | generale | beta su richiesta | API (polling) | — |
| Easy!Appointments | generale | self-hosted | API + webhook | indisponibilità, annullamento |
| Feed iCal | qualsiasi | — | feed `.ics` della piattaforma | — |
| Email di notifica | qualsiasi | — | casella dedicata o webhook email | — |
| Webhook generico | qualsiasi | — | Zapier, Make, n8n, sistemi propri | — |

*"Elti"* nella richiesta originale è **Elty** (elty.it). Planity non è attiva in Italia e
Square Appointments non è disponibile in Italia; per questo non hanno un connettore.

### Le tre vie di ingresso

1. **API**: il CRM interroga la piattaforma ogni 15 minuti (`sync_all` nel
   programmatore) e riceve i webhook in tempo reale su
   `/api/method/crm.api.booking_platforms.webhook?token=…`. Ogni webhook è verificato con
   lo schema della sua piattaforma: HMAC di Calendly (`t.body`), di Cal.com (corpo), di
   Acuity (base64), header segreti di TIMIFY, Easy!Appointments e MioDottore. SimplyBook
   non firma i webhook, quindi il CRM rilegge la prenotazione dall'API.
2. **Feed iCal**: si incolla l'indirizzo privato `.ics`. Una prenotazione che sparisce dal
   feed viene annullata.
3. **Email di notifica**: si crea un *Email Account* per una casella dedicata e la si
   aggiunge come indirizzo di notifica (o di inoltro) sulla piattaforma. Le email di
   prenotazione, modifica e annullamento diventano appuntamenti. Il parser legge date e
   orari in italiano e in inglese, i campi etichettati (Cliente, Servizio, Operatore,
   Telefono, Codice prenotazione…) e riconosce annullamenti e spostamenti. Senza una data
   e un orario riconoscibili non crea nulla. Un'email senza codice di prenotazione viene
   abbinata all'appuntamento del cliente quando annulla o sposta.

### La via di uscita: il feed "Occupato"

Ogni connessione pubblica un calendario `.ics` degli orari già occupati nel CRM, uno per
tutto il team e uno per ogni professionista mappato (si copiano dalla scheda della
connessione). Contiene **solo gli orari**, senza nomi, servizi o clienti, perché
un'agenda medica o estetica è un dato personale. Si incolla:

- **Treatwell**: *Connect → Team → collaboratore → Calendario esterno*;
- **Fresha**: *Calendar → Sync*, importazione come tempo bloccato;
- **Cal.com**: lo registra il CRM stesso durante il *Test connessione*;
- **Google Calendar**, e da lì Calendly, iDoctors e chiunque legga Google.

Il feed non ripete le prenotazioni della piattaforma stessa, così non si raddoppiano.
Le piattaforme lo rileggono ogni 15–60 minuti.

### Regole dell'import

- La chiave è `(connessione, id esterno)`: la prima volta crea l'appuntamento, poi lo
  sposta o ne cambia lo stato, e lo annulla quando lo annulla la piattaforma.
- Una prenotazione esterna **non viene mai rifiutata** per conflitto, perché esiste già
  sulla piattaforma. Il conflitto resta scritto sull'appuntamento, con l'avviso in
  agenda, per chi deve risolverlo.
- Il cliente viene trovato o creato come lead (stessa logica della pagina `/prenota`),
  con la piattaforma come fonte.
- Se lo staff ha già segnato l'appuntamento come Completato o Assente, un "confermato"
  della piattaforma non lo sovrascrive.
- Appuntamento con provenienza *Esterno*: in calendario appare il nome della piattaforma,
  si può filtrare per *Provenienza*, e il dettaglio mostra le note del cliente e il link
  alla piattaforma.

## 5. Architettura

```
crm/scheduling/booking_rules.py      limiti online ed ereditarietà delle regole (puri)
crm/scheduling/availability.py       motore: durata per professionista, online, tetti
crm/scheduling/unify.py              Booking Calendars → servizi, link del servizio
crm/api/booking_admin.py             Chi fa cosa, Turni del team, Perché non è disponibile
crm/api/service_booking.py           API pubblica di /prenota
crm/www/prenota.{py,html}            la pagina
crm/booking_platforms/
  base.py                            ExternalBooking, BookingPlatform, helper
  docplanner.py                      MioDottore / Docplanner
  schedulers.py                      Cal.com, Calendly, SimplyBook, Acuity, MS Bookings,
                                     TIMIFY, Setmore, Easy!Appointments, Booksy
  ical.py                            feed iCal (parser RFC 5545 senza dipendenze)
  email_parser.py                    email di notifica + preset per piattaforme chiuse
  generic_webhook.py                 Zapier / Make / n8n
  sync.py                            upsert, polling, webhook, email, blocchi in uscita
  __init__.py                        registro (le etichette = Select di CRM Booking Connection)
crm/api/booking_platforms.py         webhook, feed "Occupato", API delle impostazioni
DocType: CRM Booking Connection (+ Map), CRM Booking Platform Block
```

Per aggiungere una piattaforma basta una classe che estende `BookingPlatform`,
implementando `fetch_bookings` e/o `parse_webhook` (più `cancel_booking`, `block_time` e
`fetch_catalog` se l'API li offre), una riga in `PROVIDERS` e la sua etichetta nella
Select `platform`. Il test `test_every_platform_is_a_select_option` controlla che le due
restino allineate.

## 6. Test

```bash
# puri, girano ovunque (anche senza Frappe, con un modulo frappe vuoto nel PYTHONPATH)
python -m unittest crm.tests.test_booking_rules crm.tests.test_booking_platforms
# integrazione (bench)
bench --site test_site run-tests --module crm.tests.test_service_booking
bench --site test_site run-tests --module crm.tests.test_booking_platform_sync
bench --site test_site run-tests --module crm.tests.test_booking_unified
# frontend
cd frontend && yarn test:run
```

## 7. Cosa resta fuori

- **MioDottore via API** richiede di diventare *integratore certificato* Docplanner
  (sandbox e test di accettazione). Il connettore è pronto; senza credenziali si usa
  *MioDottore (email)*.
- **Treatwell, Fresha, Elty, Doctolib, iDoctors, Top Doctors e Pazienti.it** non
  pubblicano API né modelli di email: il parser è euristico e va provato sulle email
  reali di ciascuno.
- **Reserve with Google** è aperto solo alle piattaforme di prenotazione partner (bisogna
  ospitare un booking server). Non è una fonte da cui leggere prenotazioni.
- **Pagamenti e caparre** online non sono ancora gestiti.
- **Fase 2** del progetto (vedi `sistema-unico.md`): tempi di posa, più servizi in una
  prenotazione, fasce orarie riservate a certi servizi, sedi multiple.
