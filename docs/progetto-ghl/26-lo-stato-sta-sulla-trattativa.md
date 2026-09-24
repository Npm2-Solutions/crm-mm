# 26 — Lo stato della vendita sta sulla trattativa, e solo lì

*23/09/2026 — la crepa lasciata aperta dal [documento 21](./21-lead-contatto-trattativa.md),
e come la chiudiamo.*

## Cosa era rimasto storto

Il doc 21 ha stabilito la cosa giusta — la persona è unica e permanente, la
vendita è ripetibile — e ha tolto i pezzi di codice che seguivano ancora
Salesforce. Ma avendo fatto coincidere la persona con il record `CRM Lead`, ha
reso **singleton anche il ciclo di qualifica**.

Su una persona che vive per sempre stavano cose che appartengono a *una singola
richiesta*: `status`, `lost_reason`, l'SLA con il suo `first_responded_on`, la
`source`, il primo e l'ultimo contatto.

In concreto, e non in teoria: `_merge_submission` riempie solo i campi vuoti, e
`status` non è vuoto. Una persona segnata **Lost** otto mesi fa che compila un
nuovo modulo restava Lost, non faceva ripartire nessun cronometro — il first
response era già stato dato, l'anno prima — e non compariva in nessuna coda di
lavoro. Scattava solo il trigger `Lead Form Submitted`, e nessuno se ne
accorgeva.

## La decisione

**Lo stato della vendita vive sulla trattativa. La persona non ne ha uno.**

È il modello di GoHighLevel, dove il contatto non ha stato e ce l'ha soltanto
l'opportunità. HubSpot arriva allo stesso posto per un'altra strada: dal 2024 ha
un oggetto Leads vero, e un contatto può portarne **più d'uno** — la qualifica è
ripetibile esattamente come la vendita. Noi non aggiungiamo un terzo doctype:
quella parte la fa la trattativa, che esiste già ed è già ripetibile.

Il guadagno è una scala sola di stati invece di due che si sovrapponevano
(la persona aveva *Qualified* e *Converted*, la trattativa apriva con
*Qualification*: due modi di raccontare la stessa vendita, e nessuno dei due la
raccontava bene).

## Una richiesta apre una trattativa

`crm.api.lead.open_deal_for_inquiry` è l'unico posto che lo decide, e decide
due cose:

- **non** una seconda trattativa mentre la prima è aperta. Due schede per la
  stessa conversazione è come si chiama un cliente due volte per la stessa cosa;
- **sì** una nuova quando l'ultima è chiusa. Vinta un anno fa, persa in
  primavera: chi torna è una vendita nuova, con il suo stage, il suo cronometro e
  il suo esito. È precisamente ciò che lo stato unico sulla persona impediva.

Chiamata da chi porta una richiesta vera:

| Da dove | Perché |
|---|---|
| Import Meta, persona nuova | un lead che hai pagato sta in pipeline dal momento in cui atterra |
| Import Meta, persona che torna | la persona ha mesi, la richiesta no |
| Modulo pubblico (`CRM Lead`) | è una richiesta, non una visita |

E **non** da chi non la porta: uno sconosciuto che scrive su WhatsApp diventa una
persona e resta nell'Inbox — `adopt_unknown_number` non apre niente. Aprire una
trattativa a ogni messaggio riempirebbe la board di gente che ha sbagliato
numero. Chi risponde la apre con un click quando serve.

Non blocca mai chi arriva: la funzione fallisce in silenzio e scrive
nell'error log, perché una persona che ci ha raggiunti va salvata anche se la
trattativa non si riesce a creare.

## Cosa succede ai dati che ci sono *(decisione del committente, 23/09/2026)*

**Nessuna trattativa viene creata dalla migrazione.** La pipeline riparte
vuota e si riempie da qui in avanti.

- le persone in uno stato aperto (New, Contacted, Nurture, Qualified) non
  ricevono una trattativa: lo stato che avevano viene scritto in un commento
  sulla persona, così l'informazione non sparisce, e la board resta pulita;
- **Unqualified e Junk** non entrano in board. Trasformare gli scartati in
  trattative Perse avrebbe sporcato pipeline e report con storia vecchia: anche
  qui il motivo resta sulla persona.

Il prezzo, dichiarato: il lunedì dopo il rilascio i venditori non trovano in
board quello che stavano lavorando. È stato scelto sapendolo, in cambio di una
pipeline che non nasce già piena di roba di provenienza incerta.

## Se un domani servirà diversamente

Il campo `CRM Lead.status` **non viene cancellato dalla tabella**: esce dalle
schermate e smette di essere scritto, ma resta un ciclo di rilascio, così le
viste salvate che lo nominano non esplodono e un ripensamento non ha bisogno di
un restore. Quello che andrebbe rifatto è l'assegnazione automatica in
`validate_status` e i punti che lo mostrano.

## Test

- `crm/tests/test_inquiry_deal.py`: una richiesta apre una trattativa nel primo
  stage; una seconda richiesta si unisce a quella aperta; chi torna dopo una
  trattativa chiusa ne apre **una nuova**, che è il motivo di tutto il resto.

## Fonti

- [HighLevel — Understanding Opportunities](https://help.gohighlevel.com/support/solutions/articles/155000001983-understanding-opportunities-in-highlevel)
- [HighLevel — Opportunities FAQ](https://help.gohighlevel.com/support/solutions/articles/155000002000-opportunities-faqs)
- [Hublead — How to use the HubSpot Leads Object](https://www.hublead.io/blog/hubspot-leads-object)
- [HubSpot — Use lifecycle stages](https://knowledge.hubspot.com/records/use-lifecycle-stages)
