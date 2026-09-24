# Prenotazione dei servizi e piattaforme esterne

Questa guida copre la prenotazione online dei servizi (menu servizi → professionista →
orario), i limiti configurabili e i connettori verso le piattaforme dove i clienti
prenotano già: MioDottore, Treatwell/Uala, Fresha, Elty e le altre.

Il rapporto completo sulle API delle piattaforme, con le fonti e il livello di
verifica di ogni dato, è in [ricerca-piattaforme.md](./ricerca-piattaforme.md).

---

## 1. La pagina `/prenota`

Una pagina pubblica, senza login, che prenota sul **motore completo** dell'agenda:
quello che il cliente prenota è esattamente quello che la reception prenoterebbe dal
calendario, con le stesse regole di conflitto su professionisti, stanze e attrezzature,
posti di gruppo e listini.

Il percorso:

1. **Servizio**: ricerca, categorie, durata, prezzo, badge per le lezioni di gruppo.
2. **Professionista**: solo se il servizio ne ha più di uno e lo permette. C'è sempre
   "Chiunque disponibile".
3. **Data e ora**: calendario mensile con i soli giorni liberi evidenziati e orari divisi
   in Mattina / Pomeriggio / Sera. Per i gruppi si sceglie il numero di persone e si
   vedono i posti rimasti.
4. **Dati**: nome, email, telefono, la domanda del servizio e il consenso privacy.
5. **Conferma**: riepilogo, link per aggiungere a Google Calendar o Outlook, un file
   `.ics` in email e il link per gestire la prenotazione.

Con `?token=…` la stessa pagina diventa la gestione della prenotazione: il cliente vede
lo stato e annulla o sposta **entro i limiti del servizio**.

Link diretti:

| Link | Cosa fa |
|---|---|
| `/prenota` | Menu di tutti i servizi prenotabili online |
| `/prenota?servizio=<slug>` | Apre direttamente il servizio (lo slug è quello del sito, altrimenti il nome) |
| `/prenota?servizio=<slug>&professionista=<id>` | Apre servizio e professionista |
| `/prenota?embed=1` | Sfondo trasparente, per un iframe nel sito |
| `/booking` | Alias inglese |

La pagina è in italiano, con l'inglese automatico per i browser in inglese (`?lang=en`
per forzarlo). Segue il tema chiaro o scuro del dispositivo.

Il link di un servizio si copia dal pannello *Prenotazione online* della sua scheda. Il
link della pagina si copia da *Impostazioni → Booking → Piattaforme di prenotazione*.

## 2. I limiti configurabili

Si impostano in *Impostazioni → Agenda → Servizi → (servizio) → Prenotabile online*. Il
pannello riassume i limiti attivi e segnala le configurazioni contraddittorie prima del
salvataggio: finestra chiusa prima di aprire, preavviso più lungo dell'orizzonte, più
posti del servizio, nessun professionista.

| Gruppo | Limite | Effetto |
|---|---|---|
| Come | Conferma automatica / su approvazione | Con approvazione l'appuntamento nasce *Da confermare*; quando lo staff conferma, il cliente riceve l'email |
| | Il cliente sceglie il professionista | Mostra il passo "Professionista" |
| | Mostra il prezzo | |
| | Orari online ogni N minuti | Lo staff può prenotare ogni 5', il pubblico vede solo :00 e :30 |
| | Posti per prenotazione | Quante persone può portare un cliente in un gruppo |
| Quando | Preavviso minimo (ore), orizzonte (giorni) | Già presenti nel servizio, valgono anche online |
| | Prenotabile dal / fino al | Finestra stagionale |
| | Stesso giorno fino alle | Dopo quell'ora il giorno stesso non si prenota più online |
| Capacità | Max al giorno / alla settimana | Tetti su tutto il servizio |
| | Max contemporanei | Anche se lo staff è libero |
| Clienti | Chi può prenotare | Tutti / solo nuovi / solo già clienti |
| | Prenotazioni future per cliente | Per servizio. C'è anche il tetto globale in *Scheduling* |
| | Per cliente al giorno | |
| | Giorni tra due visite | Per esempio un trattamento laser non prima di 30 giorni |
| Modulo | Telefono obbligatorio, domanda (obbligatoria o no), istruzioni dopo la prenotazione | |
| Modifiche | Annullamento online sì/no + preavviso | |
| | Spostamento online sì/no + preavviso + numero massimo di spostamenti | |

Le impostazioni della pagina sono in *CRM Scheduling Settings → Online Booking Page*:
pagina aperta o chiusa, titolo, testo introduttivo, link all'informativa privacy,
consenso obbligatorio, email al cliente e al professionista, tetto globale per cliente.

Le regole vivono in `crm/scheduling/booking_rules.py` come funzioni pure che restituiscono
un codice (per esempio `too_soon` o `client_active`). Il messaggio per il cliente è in
`crm/api/service_booking.py → limit_message`.

## 3. Piattaforme esterne

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

## 4. Architettura

```
crm/scheduling/booking_rules.py      limiti online (puri)
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

## 5. Test

```bash
# puri, girano ovunque (anche senza Frappe, con un modulo frappe vuoto nel PYTHONPATH)
python -m unittest crm.tests.test_booking_rules crm.tests.test_booking_platforms
# integrazione (bench)
bench --site test_site run-tests --module crm.tests.test_service_booking
bench --site test_site run-tests --module crm.tests.test_booking_platform_sync
# frontend
cd frontend && yarn test:run
```

## 6. Cosa resta fuori

- **MioDottore via API** richiede di diventare *integratore certificato* Docplanner
  (sandbox e test di accettazione). Il connettore è pronto; senza credenziali si usa
  *MioDottore (email)*.
- **Treatwell, Fresha, Elty, Doctolib, iDoctors, Top Doctors e Pazienti.it** non
  pubblicano API né modelli di email: il parser è euristico e va provato sulle email
  reali di ciascuno.
- **Reserve with Google** è aperto solo alle piattaforme di prenotazione partner (bisogna
  ospitare un booking server). Non è una fonte da cui leggere prenotazioni.
- **Pagamenti e caparre** online non sono ancora gestiti.
- Il pulsante **"Prenota"** delle schede servizio del sito punta ancora ai calendari
  Calendly-style. Collegarlo a `/prenota?servizio=` è il passo successivo.
