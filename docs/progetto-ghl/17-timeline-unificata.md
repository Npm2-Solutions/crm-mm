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

## Un flusso, quattro canali, un selettore

Email, WhatsApp, SMS e commenti erano quattro tab. La domanda che si fa a una
scheda — **cosa e' stato detto a questa persona, e in che ordine** — con quattro
tab si poteva rispondere solo tre quarti alla volta.

Adesso la tab **Activity** e' la conversazione, e sopra c'e' un selettore:
`Tutto · Email · WhatsApp · SMS · Commenti`. Cambia **due cose insieme**: il
flusso che leggi e la casella in cui scrivi. Un selettore che cambia solo la
lettura e non la scrittura e' un selettore che viene ignorato.

### Due forme, e non e' decorazione

| Cosa | Come |
|---|---|
| un messaggio **fra due persone** | bolla, con un lato: inviato a destra, ricevuto a sinistra |
| un commento, una nota, un campo cambiato | **larghezza piena** |

La regola non e' estetica. Un messaggio ha una direzione, e una chat la fa
leggere a colpo d'occhio. Un commento non e' indirizzato a nessuno: dargli un
lato inventerebbe un mittente e un destinatario che non esistono.

### L'icona del canale sta sulla bolla

Era una colonna di icone a sinistra. Una colonna funziona finche' tutto e'
allineato a sinistra: nel momento in cui metа' delle righe stanno a destra,
l'icona e' lontana dalla cosa che descrive. Ora sta **sull'angolo esterno della
bolla** e viaggia con il messaggio, leggibile su entrambi i lati.

### Chi disegna cosa

Il componente nuovo (`ConversationView.vue`) fa **la disposizione** e nient'altro:
quali righe, in che ordine, su quale lato, con quale pastiglia. Com'e' fatto un
messaggio dentro la bolla resta il componente del suo canale — quelli sanno gia'
di risposte, reazioni, allegati, invii falliti e ritenta, e riscriverli per
guadagnare un layout avrebbe perso tutto quello.

La parte che decide — cos'e' un canale, da che parte e' andato un messaggio, cosa
ha una direzione e cosa no — sta in `frontend/src/utils/conversation.js`, pura e
sotto test: 18 casi, perche' leggere il campo sbagliato e' esattamente come una
risposta finisce dalla parte da cui e' stata mandata (`type` su un messaggio,
`sent_or_received` su una mail, niente su un commento, e le chiamate che lo
dicono al contrario dei messaggi).

### La chat WhatsApp

Sfondo di WhatsApp — disegnato con tre gradienti radiali invece di spedire un
asset a mosaico — e le sue due tinte: bianco in arrivo, verde in uscita. Prima
erano dello stesso grigio, e l'allineamento faceva tutto il lavoro da solo: che
e' la prima cosa che salta quando una bolla e' larga. I colori sono scritti come
letterali e non come token del tema, perche' sono il marchio di qualcun altro e
spacciarli per nostri vorrebbe dire che un cambio di tema ristila WhatsApp.

### Gli SMS erano fuori dalla storia

`get_activities()` metteva nel flusso i messaggi WhatsApp ma non gli SMS: una
conversazione proseguita per SMS **spariva dalla cronologia della scheda** e si
vedeva solo nella sua tab. Ora ci sono.

### Tre cose viste solo guardandola

Dopo il deploy, col browser:

1. **Ogni vocale compariva due volte.** Un file mandato come messaggio viene
   anche scritto fra gli allegati della scheda, e in un flusso unico si vedevano
   tutti e due: la bolla che qualcuno ha mandato, e una riga che dice che e'
   stato allegato un file. La bolla e' il fatto; la riga e' contabilita' su quel
   fatto. Ora la riga sparisce quando il file e' gia' un messaggio — e il
   confronto legge il nome **anche dentro l'URL firmato**, perche' i media in
   uscita non passano piu' da `/files/…` e leggendo solo il percorso il nome
   sarebbe `media` per tutti.

2. **La pastiglia del canale sbatteva contro «failed / Retry».** Stava
   nell'angolo in alto, che su un messaggio in uscita e' esattamente dove
   WhatsAppArea mette la coppia fallito/ritenta. Ora e' centrata verticalmente
   sul lato esterno, dove non c'e' niente.

3. **Nella vista di un singolo canale la pastiglia non serve.** Sono tutte
   uguali: ripetuta lungo tutta la pagina non dice niente e occupa l'angolo.
   Compare solo su «Tutto».

### Quattro correzioni alla vista «Tutto»

**La data appiccicata in alto.** Una conversazione lunga e' un muro di orari
senza date: «12:57» non dice se era oggi o ad aprile, e scorrere in su per
scoprirlo fa perdere il segno. Un separatore per giorno, fissato in alto finche'
quel giorno e' quello sullo schermo — come fa WhatsApp, e come lo fanno tutti,
perche' costa **una riga al giorno** invece di una data su ogni messaggio.
`Oggi` e `Ieri` a parole, tutto il resto con la data; il giorno di riferimento
si passa alla funzione invece di leggerlo dall'orologio, cosi' «oggi» significa
la stessa cosa in un test e sullo schermo.

**La pastiglia del canale e' diventata una didascalia.** Sull'angolo non aveva
niente su cui sedersi che non fosse gia' occupato — la coppia fallito/ritenta da
una parte, una reazione dall'altra — e sbatteva contro qualunque cosa
incontrasse. Sotto la bolla non puo' sbattere contro niente, si legge come
**parole** invece che come un simbolo da decifrare, e sta dalla parte da cui e'
andato il messaggio.

**Le chiamate sono bolle.** Stessa forma, stesso lato, cosi' l'occhio segue una
conversazione sola. Superficie diversa, non un verde diverso: prendere in
prestito il colore di WhatsApp per una telefonata direbbe che la chiamata e'
avvenuta su WhatsApp.

**Il pulsante «New» su «Tutto» e' tornato il menu.** Su un flusso misto non c'e'
un canale in cui si stia scrivendo, quindi la domanda «cosa vuoi creare» e'
ancora aperta: email, commento, evento, chiamata, attivita', nota, file.
Scegliendo un canale il menu si stringe all'unico pulsante di quel canale,
perche' li' la domanda ha gia' una risposta.

## La chat rifatta: chi, dove, quando (28/09/2026)

Le sezioni sopra raccontano come la vista «Tutto» e' diventata una chat. Questa
racconta cosa non funzionava ancora guardandola, e cosa si e' deciso — anche
dove una decisione precedente e' stata rovesciata, con il perche'.

### Il riempimento dice chi, l'icona dice il canale

Due commit di fila avevano dato al colore due significati opposti: prima «il
riempimento dice chi, il colore del canale sta sul bordo», poi «la tinta dice il
canale, la nostra e' un tono sotto la loro». Sullo schermo la seconda regola
dava due verdi a un punto percentuale di luminosita' di distanza
(`surface-green-1` contro `-2`): in una conversazione quasi tutta WhatsApp ogni
bolla era dello stesso verde, e a dire chi aveva parlato restava solo il lato.

Chi ha parlato e' la domanda a cui una chat risponde a colpo d'occhio, e ogni
messenger ci risponde col riempimento. Quindi:

| Cosa | Come |
|---|---|
| **loro** | a sinistra, sulla superficie rialzata (bianco; in scuro un grigio sopra il fondo) |
| **noi** | a destra, nel blu di casa (`surface-blue-3`) — uguale su ogni canale |
| **il canale** | il suo glifo accanto all'ora, nel suo colore: verde WhatsApp, blu email, viola SMS |
| **la nota** | ambra, in mezzo: l'unica cosa che il cliente non vedra' mai |

La vista WhatsApp tiene i colori di WhatsApp (bianco/verde sulla carta da
parati): li' e' casa sua, e la differenza fra le due viste e' proprio questa.

### La serie e' una voce

La coda della nuvoletta e il nome stanno sulla prima di una serie; le altre si
stringono sotto, a due pixel, come in ogni messenger. La serie si spezza quando
cambia il lato, il canale, il giorno, o quando in mezzo succede altro. Il nome
compare solo dove il lato non basta: un'email scritta da qualcun altro dalla loro
parte, o un collega che ha risposto per noi — mai chi sta leggendo, mai
«Administrator».

L'ora sta accanto al testo quando ci sta, sotto quando il messaggio e' lungo: una
riga flex che va a capo, cosi' un «ok» non occupa piu' due righe.

### Un invio fallito lo dice dentro la nuvoletta

Il badge «failed» e il pulsante «Retry» erano posizionati in assoluto sull'angolo
alto: coprivano la prima parola del messaggio e l'ora. Ora «Non consegnato ·
Riprova» sta nel piede della nuvoletta, con un bordo rosso sottile. Rispondi,
reagisci e riprova vivono in un composable solo (`useWhatsAppActions`), usato
dalla vista WhatsApp e dalla chat mista: erano due copie, ed e' cosi' che il
badge era finito sopra le parole in una e non nell'altra.

Nella vista «Tutto» un SMS inviato risultava ricevuto: la routine che prepara le
righe dei cambi di campo azzerava `type`, che per un messaggio e' la direzione.
Gli SMS ora ne sono esclusi come gia' lo erano WhatsApp, email e chiamate.

### Le date nella lingua di chi legge

«2026-08-16» sui separatori e' diventato «Domenica 16 agosto»: Oggi, Ieri, il
giorno della settimana per l'ultima settimana, la data (con l'anno solo se non e'
quest'anno) dopo. Le parole vengono da `Intl`, nella lingua dell'utente del CRM
(`appLocale()`, dal boot) come le date della dashboard: «Yesterday» nel catalogo
italiano non aveva nemmeno una traduzione. Una prima versione usava la lingua del
browser, e un account inglese su un browser italiano leggeva le date in italiano
sotto parole inglesi.
Gli orari si leggono sul fuso di chi guarda, e le stringhe del server non passano
piu' da `new Date(...)`, che Safari vecchio legge come data non valida.

Il separatore sta dove il giorno comincia e non copre niente. La data appiccicata
in alto c'e' solo mentre si scorre e sparisce appena ci si ferma: prima restava
sopra il primo messaggio anche a riposo, sulle sue parole.

### Si risponde dove ti hanno scritto

La regola di questo documento — «nella vista Tutto il composer parte dal canale
dell'ultimo messaggio ricevuto» — non era mai stata applicata: il composer
partiva sempre dall'email, anche per un cliente che ha sempre e solo scritto su
WhatsApp. Ora `replyChannel()` sceglie l'ultimo canale da cui hanno scritto,
poi quello dove la conversazione e' andata per ultima, poi il primo che la
persona puo' ricevere (niente numero, niente WhatsApp).

Leggere e scrivere sono tornati due domande. Scegliere un canale nelle pillole
imposta anche il composer; ma scegliere un canale nel composer, stando su
«Tutto», non ti porta via «Tutto». Il composer e' una scheda sola con i canali
come linguette; la nota la tinge di ambra, cosi' nessuno scrive un commento
interno credendo di rispondere, o viceversa.

Due difetti trovati facendolo: i pulsanti «Rispondi» delle email dentro la chat
non aprivano niente (ricevevano un oggetto vuoto al posto del composer), e
l'oggetto proposto diventava «(#undefined)» quando l'editor si montava prima che
la scheda fosse caricata. Il contatore dei caratteri SMS chiesto sopra c'e': un
«È» — che l'alfabeto SMS non ha — porta ogni messaggio da 160 a 70 caratteri, e
il composer lo dice.

### Conversazioni: il nome sopra il filo

Aperta da un link, una conversazione mostrava «CRM-LEAD-2026-00128» dove va il
nome, perche' la persona veniva cercata solo fra le quaranta righe caricate. Ora
c'e' `crm.api.conversations.person`. Il nome sta nell'intestazione sopra il
filo, con accanto le decisioni che prima erano sul bordo opposto dello schermo:
segna come letta, rimanda, gestita. Il pannello a destra resta per chi e' e come
raggiungerlo, e compare solo sopra i 1400 pixel: a 1280 lasciava alla
conversazione 430 pixel e tagliava il nome; sotto, e' dietro un pulsante.

Assegnare una conversazione rimandata la riportava in lista: passava dalla stessa
porta di «apri». Ora l'assegnazione tiene lo stato che trova.

Nella lista: l'ora di un messenger (14:32, Ieri, sab, 12 ago) invece di «3 days
ago» su ogni riga; iniziali su una tinta che resta alla persona invece di
quaranta cerchi grigi con una lettera; il contatore dei non letti in un blu
leggibile — era testo scuro su verde chiaro, perche' `text-ink-white` non esiste.

### I token che non esistono

`bg-surface-white` e `text-ink-white` non sono token di frappe-ui e non generano
CSS: la pillola selezionata, le schede degli appuntamenti, i pannelli e i badge
che li usavano erano trasparenti. Nella chat ora ci sono i token veri
(`surface-elevation-2`, `surface-base`, `ink-base`). E la carta da parati di
WhatsApp segue il tema dell'app (`[data-theme="dark"]`) invece di quello del
computer.

### Leggere è un momento solo

Nel pannello delle conversazioni «letto» voleva dire due cose, in due momenti
diversi. Le spunte blu partivano quando la chat veniva *aperta*, se
l'impostazione era accesa; il badge restava finché qualcuno premeva «segna come
letta». Così il cliente sapeva di essere stato letto mentre il CRM diceva che
nessuno l'aveva fatto, e a un collega bastava scorrere la lista per mandare
conferme a nome di tutti. Segnarla letta, poi, spostava la riga: l'ordine
metteva i non letti in cima, e la conversazione appena letta finiva sotto tutte
le altre, fuori dallo schermo.

Ora letto è un momento solo, e ha tre porte: il pulsante «Segna come letta»,
una risposta scritta dal CRM (WhatsApp, template, reazione, SMS, email; non una
nota interna, non un messaggio mandato da un'automazione) e «Gestita». Aprire
una conversazione non è una di queste.

| Quando | Badge (per tutto il team) | La riga nella lista | Spunte blu al cliente, se attive |
|---|---|---|---|
| Apri la conversazione | Non cambia | Non si muove | No |
| Arriva un loro messaggio | Si accende; il numero conta quelli arrivati dall'ultima lettura | Sale in cima; se era gestita o rimandata torna fra le Aperte | No |
| Rispondi dal CRM | Si spegne: «Letta da te · ora» | Sale in cima, perché è un messaggio | Sì |
| «Segna come letta» | Si spegne | Resta dov'è | Sì |
| «Gestita» | Si spegne, se c'era qualcosa da leggere | Resta velata al suo posto, «Gestita · torna quando scrivono», finché non passi a un'altra; il toast ha Annulla | Sì, se c'era qualcosa da leggere |
| «Rimanda» | Non cambia | Come sopra, «Rimandata a domani 09:00» | No |
| «Segna come da leggere» | Torna il pallino, senza numero | Resta dov'è | Quelle già partite restano |
| Assegni la conversazione | Non cambia | Non si muove | No |
| Scrive un'automazione | Non cambia | Sale in cima | No |

L'ordine della lista è solo per ultimo messaggio, da una parte o dall'altra:
una riga si sposta quando qualcuno dice qualcosa, mai perché qualcuno ha
premuto un pulsante. I non letti sono in grassetto, con il numero o il
pallino, e hanno un filtro loro, «Non lette», accanto al selettore della vista:
restringe la vista aperta (le non lette fra le aperte, fra le rimandate, fra
le gestite), mai una ricerca, perché un nome cercato è qualcuno che serve,
letto o no. Anche il selettore dice cosa contiene ogni vista e cosa fa tornare
una conversazione fuori da lì.

**La riga che se ne va.** Gestita, rimandata, letta mentre la lista mostra solo
le non lette: sul server la conversazione esce dalla vista. Toglierla anche
dallo schermo, sotto il puntatore, faceva scivolare al suo posto quella sotto,
e il clic successivo cadeva su qualcuno che nessuno aveva scelto. Resta
quindi dov'era, velata, con il motivo al posto dell'ultimo messaggio, e se ne
va quando apri un'altra conversazione, cambi vista o cerchi (anche il pulsante
«Aggiorna» la toglie). Gli spostamenti della lista sono animati, perché l'occhio
li possa seguire.

**Annulla.** «Gestita» e «Rimanda» hanno un toast che dice dove è andata la
conversazione e quando torna, con Annulla, che la rimette com'era: stato, letta
o no, da chi e da quando. Tranne le spunte blu, che sono sul telefono del
cliente. E se nel frattempo è arrivato un messaggio l'Annulla non fa nulla, e
lo dice: rimettere «gestita» sopra un messaggio appena arrivato lo
nasconderebbe.

**Dove iniziano i nuovi.** Nel filo una riga «2 nuovi messaggi» sta sopra il
primo messaggio arrivato dopo l'ultima lettura. Il punto si prende quando apri
la conversazione e resta fermo finché è aperta: leggerla o rispondere non tira
via la riga da sotto i messaggi a cui punta. È blu finché la conversazione è
da leggere e grigia dopo. E la conversazione si apre lì, non in fondo: con
quindici messaggi nuovi i primi quattordici stavano sopra lo schermo, senza
niente a dirlo. Solo la prima volta: dopo, uno scorrimento è un messaggio
mandato o arrivato, e il suo posto è in fondo. Quando fra i nuovi c'è WhatsApp dice la cosa che lo
schermo non mostra, cioè se il cliente viene avvisato: «vedrà le spunte blu
quando rispondi o la segni come letta», «letta · ha le spunte blu», oppure,
con le conferme spente, «da questo CRM non riceve spunte blu». Sulle nostre
spunte, un tooltip dice cosa significano: inviato, consegnato, letto.

**Chi l'ha letta.** Nell'intestazione, al posto del pulsante, «Letta da Mario ·
10:32»; il menu sotto ha il momento per intero e «Segna come da leggere»,
che spiega che le spunte già inviate restano. Il pulsante «Segna come letta»
ha il blu del pallino e del contatore che spegne: su telefono, dove sono due
icone, azione da fare e stato raggiunto non si confondono.

**Le spunte blu.** Una sola richiesta per numero WhatsApp, per l'ultimo
messaggio loro (WhatsApp segna letti anche i precedenti della stessa chat),
sull'intera conversazione della persona, trattative comprese. È in coda dopo il
commit, perché il clic non aspetti Meta e perché non parta una conferma per una
lettura poi annullata dal database. Solo per messaggi entro i 30 giorni, oltre
i quali Meta rifiuta. La richiesta la fa il CRM e scrive lo stato sulla riga:
il metodo di frappe_whatsapp risalvava il messaggio in arrivo, e salvarlo
ricerca di nuovo il numero, cosa che può spostarlo su un altro record.

**Rispondere non è gestire.** Dopo una risposta la conversazione è letta, esce
da «In attesa di risposta» perché l'ultima parola è nostra, ma resta fra le
Aperte: si può rispondere a una domanda e dovere ancora la cosa promessa.
Toglierla dal mucchio è «Gestita».
