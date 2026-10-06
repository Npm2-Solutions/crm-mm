# 59 · I promemoria degli appuntamenti: WhatsApp con i pulsanti, SMS, email

**Stato:** fatto (06/10/2026). Spenti finché il centro non li accende; il modello
WhatsApp di DottorCloud va approvato da Meta prima del primo invio (vedi «Da
verificare»).

## Il bisogno

- Chi non viene senza avvisare lascia un buco in agenda. Il promemoria del giorno
  prima è il modo più semplice per avere meno assenze, e per liberare in tempo
  l'orario di chi non può venire.
- La persona risponde **con un tocco**: «Confermo», «Devo disdire», «Vorrei
  spostarlo». La reception vede la risposta **in agenda**, senza leggere i messaggi
  uno per uno.
- WhatsApp prima di tutto (lo leggono tutti), poi l'SMS, poi l'email: la stessa
  cosa per la via che la persona riceve.

## Cosa permette WhatsApp (verificato il 06/10/2026)

- Fuori dalla finestra di 24 ore dall'ultimo messaggio della persona si scrive
  solo con un **modello approvato da Meta**. Un promemoria è un modello
  **Utility** (doc 12).
- Un modello può avere fino a 10 pulsanti; le **risposte rapide** vengono prima,
  25 caratteri al massimo ciascuna (le regole in `modelli_regole.py`, doc 12).
- Un tocco arriva come un messaggio con le parole del pulsante, **in risposta** al
  messaggio del modello: frappe_whatsapp lo salva come `WhatsApp Message` in
  entrata, `content_type` «button», con l'id del messaggio a cui risponde
  (`reply_to_message_id`).
- Il webhook di frappe_whatsapp **non controlla la firma** di Meta: una risposta
  vale solo se risponde a un nostro promemoria (il suo id) e arriva dal numero a
  cui era andato.
- **I costi** sono quelli del doc 12: si paga il modello consegnato, per categoria
  e paese; un Utility consegnato mentre la finestra è aperta non si paga. Il
  promemoria del giorno prima di solito arriva a finestra chiusa, e si paga come
  Utility. Alcune fonti non ufficiali parlano di un cambio dal 1° ottobre 2026
  dentro la finestra: il listino di Meta per l'Italia va riletto prima di dare una
  cifra a un centro. Rispondere con un tocco apre la finestra: il «grazie» che
  segue è un testo, gratis.

## Com'è fatto

### Quando parte (`crm/scheduling/promemoria_regole.py`, pure)

- **24 ore prima**, o quante il centro sceglie tra 2 e 72.
- **Di notte no** (dalle 21 alle 8): parte alle 8 del mattino se è almeno un'ora
  prima dell'appuntamento, altrimenti alle 20 della sera prima.
- **Mai nell'ultima ora**, né per ciò che è stato prenotato meno di due ore prima
  del momento di partire: la prenotazione ha già detto tutto.
- Ogni quarto d'ora un giro (`promemoria.ogni_quarto_d_ora`) manda quelli dovuti;
  uno che un server spento ha saltato parte al giro dopo, fino all'ultima ora.
- **Uno per persona e per orario**: in una lezione ognuno ha il suo; un
  appuntamento spostato si ricorda di nuovo per il nuovo orario.
- **Non partono**: gli appuntamenti dei dati di prova (`guardie.mai_fuori`), quelli
  di una piattaforma (MioDottore, Treatwell… lo ricordano loro), una prenotazione
  online ancora da approvare, un posto disdetto.

### Per quale via (`crm/scheduling/promemoria.py`)

- La prima che funziona tra quelle che il centro ha acceso e che la persona può
  ricevere: **WhatsApp** con il modello scelto, poi **SMS** dal mittente unico del
  centro (doc 52; chi ha scritto STOP non lo riceve), poi **email** con il pulsante
  «Conferma, sposta o disdici».
- A chi: l'email e il cellulare scritti sulla prenotazione (una famiglia
  condivide un telefono), altrimenti quelli della persona. Chi ha prenotato per un
  altro, un genitore per il figlio, riceve il promemoria «Visita per Marco».
- Il **registro** (`CRM Appointment Reminder`) è scritto **prima** che parta, così
  non parte mai due volte: via, destinatario, com'è andata, perché no, la risposta.
  Senza un modo di raggiungere la persona resta nel registro con il motivo
  («Nessuna email né cellulare: chiamala»).
- Un WhatsApp che Meta dice di **non aver consegnato** va per SMS o email al giro
  dopo, con la nota «WhatsApp non l'ha consegnato» (`ricontrolla`).
- Le parole sono nella lingua del centro (`lingue.del_centro`), chiunque sia
  l'utente della sessione.

### Le risposte

- **WhatsApp**: il tocco di un pulsante (`alla_risposta_whatsapp`, dopo
  l'inserimento di un `WhatsApp Message`). La persona riceve una parola nella sua
  conversazione: il grazie, o il link per scegliere un altro orario.
- **SMS**: «SI», «NO», «sposta» e poco altro, anche «ok perfetto grazie»
  (`alla_risposta_sms`, dopo lo STOP di `sms.ascolta`). Un messaggio che dice di più
  resta un messaggio, per la reception; «STOP» resta degli SMS. Il testo chiede di
  rispondere SI o NO solo dove il mittente è un numero (a un nome non si risponde):
  altrimenti dà il link.
- **La pagina di prenotazione**: ogni promemoria porta il link `/prenota?token=…`
  del posto della persona, dove «Confermo che ci sarò» conferma; lì si sposta o si
  disdice dove le regole della prenotazione online lo permettono, e una disdetta lì
  è la risposta al promemoria («Non può venire», disdetto). Riaperta da quel link
  la pagina non dice più «Prenotazione confermata, ti abbiamo inviato un'email»:
  dice com'è la prenotazione.
- **«Non posso venire»** disdice il posto della persona (in una lezione solo il
  suo) e l'orario va a chi è in lista d'attesa. Con «Un “non posso venire” disdice
  l'appuntamento» spento, la reception riceve la notifica e decide.
- **«Vorrei spostarlo»**: la notifica, e il link per scegliere un altro orario dove
  il servizio si prenota online.
- Le notifiche («Anna Bianchi non può venire mercoledì 7 ottobre alle 09:30:
  l'appuntamento è disdetto») vanno a chi riceve quelle dell'agenda e a chi fa
  l'appuntamento, e aprono l'appuntamento in agenda.
- Una risposta vale **finché l'appuntamento è quello**: spostato dopo il
  promemoria, la risposta a quello vecchio non tocca il nuovo, e la persona lo
  legge.

### Cosa vede il centro

- **In agenda**: sul blocco il segno della risposta, icona e parole come gli altri
  (pollice in su «Ha confermato», calendario barrato «Non può venire», calendario
  con l'orologio «Vorrebbe spostarlo», campanella barrata «Promemoria non
  arrivato»); nel pannello, sotto i recapiti della persona, «Promemoria inviato
  su WhatsApp · Ha confermato».
- **La conferma della persona non cambia lo stato** dell'appuntamento: «Confermato»
  è il sì del centro a una richiesta online. È un segno del posto, per persona.
- **Impostazioni > Agenda > Agenda e promemoria > Promemoria degli appuntamenti**
  (`agenda.configura`): acceso o spento, le ore prima, cosa fa un «non posso
  venire», il modello WhatsApp (solo uno approvato con i pulsanti per confermare e
  per disdire), SMS ed email, gli ultimi promemoria con com'è andata.
- **«Crea il modello dei promemoria»**: il modello di DottorCloud, in italiano o in
  inglese come il centro, con i tre pulsanti, fatto sull'account WhatsApp del
  numero che invia. Meta lo esamina, di solito entro un giorno; poi si sceglie.
  Su un secondo account prende il nome `promemoria_appuntamento_2`: i nomi di Meta
  sono per account, quelli del sito uno per tutti.
- **Primi passi**: «Promemoria degli appuntamenti», fatto quando sono accesi.
- **Nei dati di prova** (doc 53): gli appuntamenti di domani il cui promemoria è
  già dovuto lo hanno ricevuto per email, e circa metà ha confermato dalla pagina.

## Da sapere

- **Spenti all'inizio**: il responsabile del centro li accende quando ha scelto
  come mandarli. L'email c'è sempre; l'SMS serve il telefono (doc 52); WhatsApp il
  modello approvato.
- Un modello del centro va bene se ha due risposte rapide che dicono «confermo» e
  «non posso venire» (`ha_i_pulsanti`): le sue variabili, in ordine, sono il nome,
  cosa, quando, dove. Senza quei pulsanti le risposte non arriverebbero in agenda,
  e la pagina non lo fa scegliere.
- Le prenotazioni delle piattaforme le ricordano le piattaforme: DottorCloud non
  ne manda un secondo.

## Da verificare con un account vero

- Che Meta approvi il modello come **Utility** con quel testo e i tre pulsanti, e
  non lo sposti in Marketing.
- Il prezzo per l'Italia di un Utility a finestra chiusa, e se dal 1° ottobre 2026
  cambia qualcosa dentro la finestra.
- Che il tocco arrivi a frappe_whatsapp come messaggio «button» con l'id del
  messaggio a cui risponde, nella versione dell'app installata dai centri.
- Che Twilio passi a DottorCloud la risposta a un SMS mandato da un numero
  italiano (a un mittente alfanumerico non si risponde: lì il promemoria dà il
  link).
