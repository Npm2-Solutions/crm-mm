# 17 — Timeline unificata: una schermata, non dodici tab

> 📐 **Proposta.** Da realizzare **dopo** che WhatsApp è chiuso e stabile, e
> **dopo** [18](./18-persona-unica.md): questa schermata poggia su "la
> conversazione appartiene alla persona", e chi sia la persona lo stabilisce quello.
>
> Risponde a una domanda che oggi il CRM sa rispondere solo a pezzi:
> **cosa è successo con questo lead?** Per saperlo bisogna aprire dodici tab e
> ricomporre la storia a mente.

## Il problema, misurato

Sulla scheda di un lead ci sono **dodici tab**: Activity, Emails, Comments, Data,
Events, Calls, Tasks, Notes, Attachments, Tracking, WhatsApp, SMS
(`frontend/src/pages/Lead.vue`, `tabs`).

Due difetti, e il secondo è peggiore del primo.

**Le tab spezzano la conversazione per canale.** Un cliente che scrive su
WhatsApp, riceve una email e poi risponde di nuovo su WhatsApp produce due storie
separate che nessuna schermata rimette insieme. Ma è *una* conversazione.

**"Activity" promette tutto e mantiene poco.** Conteneva solo le `versions`
(modifiche ai campi, commenti, email) e le chiamate — si legge in
`Activities.vue`, `get_activities()`. Non conteneva WhatsApp, non contiene SMS,
non contiene task, note, appuntamenti né automazioni. Chi la apre crede di vedere
tutto e ne vede metà, che è peggio di una tab onesta chiamata "Modifiche".

> **Primo pezzo fatto (08/09/2026).** WhatsApp è dentro Activity, e la barra in
> fondo ha il suo pulsante accanto a Reply e Comment — la stessa casella della
> tab WhatsApp, non una seconda. Era il passo che si poteva fare senza la
> schermata nuova: il pulsante da solo avrebbe inviato in un posto dove il
> messaggio non compariva. Restano fuori SMS, task, note, appuntamenti e
> automazioni, che è il resto di questo documento.

## L'idea: il filtro non filtra, cambia vista

Una schermata sola: dei **chip** in alto, il **flusso** al centro, un
**composer** in fondo.

Il punto non ovvio è cosa fa il chip. Non nasconde soltanto delle righe: cambia
la **forma** della schermata. È questo che gli permette di sostituire le tab —
i chip *sono* le viste per canale.

| Chip | Cosa mostra | Che forma prende la schermata |
|---|---|---|
| **Tutto** | ogni evento, in ordine di tempo | flusso misto, ogni riga con la sua forma |
| **WhatsApp** | solo i messaggi WhatsApp | una chat: bolle, reazioni, spunte di consegna, avviso della finestra 24 ore |
| **Email** | solo le email | un thread: mittente e oggetto, citazioni collassate, allegati |
| **SMS** | solo gli SMS | una chat sobria, con il contatore dei caratteri |
| **Chiamate** | solo le chiamate | elenco con player, durata, trascrizione |
| **Sistema** | automazioni, cambi di stato, appuntamenti | righe compatte, senza composer |

Entri su **Tutto** e vedi la storia intera; ti serve la chat WhatsApp e clicchi
il chip, ottenendo esattamente la chat che avresti aperto in una tab. Stessa
schermata, stesso posto, nessuna navigazione persa.

## Il composer: uno solo, che cambia forma

In fondo c'è **un** composer, non quattro. Cambia in base al canale, e ogni
canale mantiene ciò che gli serve:

- **WhatsApp** — avviso quando la finestra di 24 ore è chiusa, bottone dei
  template, risposta a un messaggio, allegati, messaggi vocali;
- **Email** — oggetto, cc/ccn, firma, allegati, editor ricco;
- **SMS** — contatore dei caratteri e conteggio dei segmenti;
- **Nota / Commento** — nessun destinatario, resta interno.

Due regole che tengono insieme chip e composer:

1. **In una vista per canale il composer è quel canale.** Sei nella chat
   WhatsApp: scrivi su WhatsApp. Nessun selettore, nessun equivoco.
2. **Nella vista "Tutto" il selettore è libero**, e parte dal canale
   **dell'ultimo messaggio ricevuto**: si risponde dove ti hanno scritto, senza
   doverci pensare.

## Cosa compare nel flusso

| Riga | Da dove viene | Forma |
|---|---|---|
| Messaggio WhatsApp | `WhatsApp Message` | bolla con reazioni, stato di consegna, allegato |
| Email | `Communication` (dentro le `versions`) | scheda con mittente, oggetto, corpo espandibile |
| SMS | `CRM SMS Message` | bolla sobria |
| Chiamata | `CRM Call Log` | player, durata, esito, trascrizione |
| Nota | `FCRM Note` | riquadro giallino |
| Task | `CRM Task` | riga con scadenza e assegnatario |
| Commento | `versions` | riga con autore |
| Cambio di campo o di stato | `versions` | riga di sistema: "Stato: Nuovo → Contattato" |
| **Appuntamento** | `CRM Appointment` | "Appuntamento prenotato per giovedì 14:30" |
| **Azione di automazione** | `CRM Automation Step Log` | "Automazione *Nurturing*: aggiunto tag cliente-caldo" |
| Allegato | `attachments` | nome file e anteprima |

Le ultime due sono le uniche che oggi non appaiono da nessuna parte: esistono
come dati e non come racconto.

## Quanto costa davvero: meno di quanto sembri

I pezzi ci sono già, separati e funzionanti.

**Per mostrare** — `WhatsAppArea`, `EmailArea`, `SMSArea`, `CallArea`,
`CommentArea`, `TaskArea`, `NoteArea`, `EventArea`, `AttachmentArea`. Il flusso
misto è un dispatch: ogni riga sceglie il suo componente. Non c'è niente da
riscrivere.

**Per scrivere** — `WhatsAppBox`, `CommunicationArea` (email), `SMSBox`. Il
composer unico li monta a turno.

**I dati** sono già in memoria nella stessa schermata: `all_activities`
(`crm.api.activities.get_activities`), `whatsappMessages`
(`crm.api.whatsapp.get_whatsapp_messages`) e `smsMessages`
(`crm.api.sms.get_sms_messages`) sono tre risorse già caricate da
`Activities.vue`. Fonderle per data è lavoro di frontend, non un nuovo endpoint.

Restano da aggiungere: appuntamenti e passi di automazione come sorgenti, la
fusione ordinata, i chip, e il composer che cambia forma.

## Cosa sparisce dalla barra

Le tab per canale (Emails, WhatsApp, SMS, Calls, Comments) **diventano chip**.
Quelle che non sono conversazione né racconto — **Data, Events, Tasks, Notes,
Attachments, Tracking** — vanno in un menu **"Altro"**: sono consultazione, non
lavoro quotidiano, e non meritano un posto fisso.

Da dodici tab a una schermata con sei chip e un menu.

## Cosa non faremo

**Non fonderemo i composer in uno generico.** Un campo di testo unico che
"indovina" il canale perderebbe l'oggetto dell'email, l'avviso della finestra
WhatsApp, il contatore SMS. Il composer si scambia, non si annacqua.

**Non nasconderemo il canale.** Ogni riga dice sempre di che cosa è fatta:
un'email che sembra un messaggio WhatsApp è una bugia che si paga quando il
cliente chiede "ma questo dove me l'hai scritto?".

## Le tappe

1. **Il flusso diventa vero** — fusione delle tre risorse per data, più
   appuntamenti e automazioni. Già solo questo rende "Activity" onesta.
2. **I chip** — filtro sul flusso, ancora senza cambio di forma.
3. **Le viste per canale** — chat WhatsApp, thread email, elenco chiamate.
4. **Il composer unico** con il selettore e il canale predefinito.
5. **Pulizia della barra** — tab rimosse, menu "Altro".

Ogni tappa è rilasciabile da sola: dopo la 1 la schermata è già migliore di oggi,
e se ci fermassimo lì non avremmo lasciato niente a metà.

## Rischi da tenere d'occhio

- **Volume.** Un lead vecchio può avere centinaia di righe fra le tre sorgenti.
  La fusione client-side va paginata, o la schermata si siede.
- **Ordinamento.** Le tre sorgenti hanno campi data diversi (`creation`,
  `modified`); serve una chiave sola e coerente, o l'ordine sembrerà casuale.
- **Realtime.** WhatsApp e SMS pubblicano già i loro eventi
  (`whatsapp_message`, `crm_sms_message`); il flusso misto deve ascoltarli tutti,
  non solo quello del canale visibile.

## Riferimenti

- `frontend/src/pages/Lead.vue` — le dodici tab
- `frontend/src/components/Activities/Activities.vue` — il flusso e le risorse
- `frontend/src/components/Activities/*Area.vue` — i componenti di rendering
- `frontend/src/components/Activities/WhatsAppBox.vue`, `SMSBox.vue`,
  `frontend/src/components/CommunicationArea.vue` — i composer
- `crm/api/activities.py` — `versions`, chiamate, note, task, allegati
