# Nomina a responsabile del trattamento (art. 28 GDPR) — bozza

> ✍️ Bozza del 07/10/2026 da far rivedere a un legale. Una per centro.

**Tra** [ragione sociale del centro], [sede], P.IVA [ ], in persona di [ ]
(il **Titolare**)

**e** NPM2 Solutions Srl, [sede], P.IVA [ ], in persona di [ ] (il **Responsabile**).

## 1. Oggetto

Il Titolare usa DottorCloud, il gestionale del Responsabile, in abbonamento. Per
fornirlo il Responsabile tratta per conto del Titolare i dati personali che il
Titolare vi inserisce o vi riceve, solo per questo scopo e secondo le sue
istruzioni documentate, che sono questa nomina, le condizioni di servizio e le
impostazioni che il Titolare sceglie in DottorCloud.

## 2. I dati e le persone

- **Persone:** pazienti e clienti, i loro familiari e chi li rappresenta,
  contatti, il personale e i collaboratori del Titolare.
- **Dati comuni:** anagrafica, recapiti, codice fiscale, dati di fatturazione,
  appuntamenti, conversazioni (email, WhatsApp, SMS, chiamate e loro
  registrazioni), moduli e consensi, preventivi, documenti.
- **Dati sanitari (art. 9):** cartella clinica, referti, anamnesi, piani di cura,
  diete ed esercizi, immagini e documenti sanitari, la sintesi del paziente.
- **Durata:** quella dell'abbonamento, più quanto serve a restituire i dati
  (punto 9).

## 3. Cosa fa il Responsabile

a. tratta i dati solo su istruzione del Titolare, anche per i trasferimenti fuori
   dall'UE, e lo avvisa se un'istruzione gli sembra contraria alla legge;
b. fa trattare i dati solo a persone autorizzate e tenute alla riservatezza;
c. adotta le misure di sicurezza del punto 5;
d. ricorre a sotto-responsabili solo come al punto 6;
e. aiuta il Titolare a rispondere alle richieste degli interessati (accesso,
   rettifica, cancellazione, portabilità): DottorCloud ha l'esportazione completa
   dei dati (Impostazioni > Il centro > I tuoi dati);
f. aiuta il Titolare con la sicurezza, le violazioni, la DPIA e la consultazione
   preventiva (artt. 32–36);
g. alla fine del servizio restituisce e cancella i dati (punto 9);
h. mette a disposizione quanto serve a dimostrare il rispetto di questa nomina e
   consente le verifiche, con un preavviso di [30] giorni.

## 4. Gli utenti dell'agenzia

Il personale del Responsabile che amministra il sito del Titolare (il livello
«agenzia») **non legge i dati sanitari** per il solo fatto di amministrarlo:
DottorCloud non glieli mostra. Li legge solo se il Titolare gli apre un accesso
a tempo, per un'assistenza, e ogni apertura resta nel registro degli accessi.

## 5. Le misure di sicurezza

Come DottorCloud le applica oggi:

- dati su server nell'Unione europea: l'hosting Frappe Cloud su Hetzner in
  Germania, i file nell'archivio Hetzner Object Storage in Germania o Finlandia
  [da verificare: la regione effettiva di ogni sito];
- connessioni cifrate (HTTPS);
- accesso con livelli e capacità: ognuno legge solo quello che il suo ruolo
  consente; la cartella segue il dossier, l'oscuramento e l'équipe di cura;
- registro degli accessi alla cartella e ai documenti sanitari; registro delle
  modifiche dei documenti firmati, ognuno legato al precedente;
- i file privati si aprono con un link firmato che dura cinque minuti, dopo il
  controllo dei permessi;
- i documenti firmati in PDF/A con il sigillo e la marca temporale del centro e
  l'impronta SHA-256;
- versioni dei file archiviati per 30 giorni [da verificare: la regola di
  lifecycle del bucket];
- backup del database [da verificare: frequenza, conservazione e cifratura dei
  backup di Frappe Cloud];
- chiavi e segreti fuori dal database e dai log.

## 6. I sotto-responsabili

Il Titolare autorizza in generale il Responsabile a ricorrere ai sotto-
responsabili qui sotto. Il Responsabile lo avvisa almeno [30] giorni prima di
aggiungerne o cambiarne uno, e il Titolare può opporsi.

| Sotto-responsabile | Cosa fa | Dove |
|---|---|---|
| Frappe Technologies Pvt. Ltd. (Frappe Cloud) | hosting e backup del sito | server in Germania (Hetzner); società in India [da verificare: clausole tipo] |
| Hetzner Online GmbH | archivio dei file (Object Storage) | Germania o Finlandia |
| [il servizio d'invio email, es. Amazon SES Francoforte o Brevo] | invio delle email di DottorCloud | [da verificare] |
| Itala [ragione sociale] | trasmissione delle fatture al Sistema di Interscambio | Italia |
| [fornitore della firma avanzata, es. Namirial] | firma elettronica avanzata, se attiva | Italia |
| [fornitore del modello dell'assistente] | bozze dell'assistente, se attivo, senza dati identificativi e senza conservazione | [da verificare] |

Non sono sotto-responsabili del Responsabile i servizi che il Titolare contratta
da sé con il proprio account (Twilio, Meta per WhatsApp, Fatture in Cloud,
MioDottore e le altre piattaforme): sono fornitori del Titolare [da verificare
con il legale, domanda 4].

## 7. Violazioni

Il Responsabile comunica al Titolare una violazione dei dati personali senza
ingiustificato ritardo, e comunque entro [24] ore da quando ne viene a
conoscenza, con le informazioni dell'art. 33 par. 3 che ha.

## 8. Trasferimenti

Nessun trasferimento fuori dallo Spazio economico europeo, se non con le
garanzie del Capo V GDPR [da verificare: il caso Frappe Cloud, domanda 3].

## 9. Alla fine

Alla fine dell'abbonamento il Titolare può scaricare l'archivio completo dei suoi
dati per [30] giorni. Poi il Responsabile cancella il sito, i suoi backup entro
[90] giorni e i file dell'archivio, salvo che la legge ne imponga la
conservazione, e lo attesta per iscritto se il Titolare lo chiede.

Luogo e data, firme.
