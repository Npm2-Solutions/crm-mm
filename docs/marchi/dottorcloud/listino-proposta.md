# Il listino per il lancio — proposta

**Stato:** 📝 proposta del 07/10/2026, da approvare. Quando è approvata sostituisce
[il listino del 01/10](./listino.md) e il codice si adegua ([cosa cambia](#cosa-cambia-nel-codice)).

Cosa cambia rispetto al listino del 01/10:

1. **La fatturazione è compresa in ogni piano**, con il Sistema TS. Non è più un extra.
2. **C'è un piano per chi lavora da solo**: un utente, fino a 3 ambulatori.
3. **I team pagano per ambulatori**, con utenti illimitati, come prima.
4. **I prezzi sono al mese; l'anno pagato in anticipo costa 10 mensilità.**
5. **Al lancio c'è l'offerta per i centri fondatori** invece di un listino più basso.
6. **Livelli e aggiunte (deciso il 07/10):** i livelli cambiano solo per la taglia,
   le aggiunte costano uguale su ogni livello e si prendono solo se servono.

## I piani

| Piano | Per chi | Utenti | Ambulatori | Al mese | L'anno | Crediti SdI l'anno | Archivio |
|---|---|---|---|---|---|---|---|
| **Professionista** | chi lavora da solo, anche su più sedi | 1 | fino a 3 | **59 €** | 590 € | 300 | 300 GB |
| **Studio** | 2 o 3 professionisti insieme | illimitati | fino a 3 | **99 €** | 990 € | 300 | 600 GB |
| **Centro** | centri e piccoli poliambulatori | illimitati | fino a 5 | **149 €** | 1.490 € | 600 | 1 TB |
| **Poliambulatorio** | strutture con molti specialisti | illimitati | fino a 10 | **249 €** | 2.490 € | 1.200 | 2 TB |
| Oltre 10 ambulatori | | illimitati | | +25 € ad ambulatorio | +250 € | 1.200 | 2 TB |

I crediti SdI servono per le fatture alle aziende e a chi ha la partita IVA, e per
quelle ricevute: le fatture sanitarie ai pazienti vanno al Sistema TS e non li
consumano. Per questo il Professionista e lo Studio ne hanno gli stessi.

Prezzi IVA esclusa. Pagando l'anno in anticipo il mese costa 49, 82, 124 e 207 €.

**Tutti i piani comprendono le stesse funzioni**, e cambia solo la taglia:

- agenda con le sale, prenotazione online, MioDottore e le altre piattaforme,
  promemoria che si confermano con un tocco;
- persone, conversazioni (email, WhatsApp, SMS), preventivi;
- **fatture elettroniche e Sistema TS**;
- cartella clinica e referti, moduli e consensi firmati, documenti;
- cicli di sedute, abbonamenti, liste d'attesa;
- l'app del paziente: appuntamenti, moduli, documenti, piani;
- dashboard.

### Il Professionista, come si presenta

> **Professionista — 59 € al mese**
> Tutto quello che serve a chi lavora da solo:
> - l'agenda, con la prenotazione online e i promemoria su WhatsApp;
> - la cartella e i moduli firmati;
> - le fatture elettroniche e l'invio al Sistema TS;
> - l'app per i tuoi pazienti.
>
> Un utente, fino a 3 studi. Il mese pagando l'anno: 49 €.

Quattro righe e un prezzo: nessun elenco di moduli, niente crediti, niente
ambulatori in prima riga. Il resto (crediti SdI, extra) sta sotto, per chi lo cerca.

### Perché quattro piani

- **Il Professionista e lo Studio hanno gli stessi ambulatori (fino a 3).** Cambiano
  solo le persone: chi prende un collega paga 40 € in più e non deve ripensare
  niente. Con lo Studio a 2 ambulatori, come nel listino del 01/10, un professionista
  con 3 sedi che prende un collega sarebbe saltato dritto al Centro.
- **Senza lo Studio il secondo utente costerebbe 90 € in più** (da 59 a 149): troppo
  per chi lavora in due. Lo Studio a 99 € resta sotto GipoNext multispecialistico
  (180 €).
- **Il prezzo per ambulatorio scende salendo:** 33 € allo Studio, 30 € al Centro,
  25 € al Poliambulatorio e oltre. Ogni passaggio conviene.

### Le aggiunte

Costano uguale su ogni livello: si prendono solo se servono, e ognuna si prova
14 giorni prima di comprarla.

| Aggiunta | Prezzo | Cosa comprende | Perché è a parte |
|---|---|---|---|
| **Telefono** | 15 € al mese (150 € l'anno) | il centralino nel browser e sul telefono per tutti gli utenti, lo squillo a tutti insieme, la segreteria con il messaggio, i richiami, il giro di chiamate | non tutti vogliono il centralino; numeri, chiamate e SMS li paga il centro a Twilio |
| **Marketing** | 29 € al mese | automazioni, campagne, Meta, social, 5.000 email al mese; oltre, pacchetti | serve solo a chi cerca pazienti nuovi |
| **Assistente** | 19 € al mese per ogni professionista che lo usa | la prova ha **50 richieste**, per tutto il centro; finite, si compra | costa a noi a ogni richiesta |
| **Firma avanzata** | 39 € al mese | 2.000 firme l'anno; oltre, pacchetti | costa a noi (circa 30 € al mese a centro) e la vuole chi lo chiede il suo lavoro |

**Il telefono e Twilio (deciso il 07/10).** Il centro collega il suo account Twilio
(Impostazioni > Telefono) e paga a Twilio numero, chiamate e SMS: DottorCloud non
rivende traffico, finché NPM2 non è abilitata alla rivendita. Per un centro che
risponde a 50 chiamate al giorno e ne fa 20 la spesa a Twilio è sui 30-50 € al mese
(stima: in uscita 0,0168 $/min verso un fisso, 0,0445 $/min verso un cellulare; il
resto da verificare sul listino di Twilio). Più avanti, da abilitati, il credito
DottorCloud: ricariche prepagate al costo di Twilio più il 15% circa, sul nostro
account.

Nessuna aggiunta è compresa in un livello: la firma avanzata e l'assistente
nemmeno nel Poliambulatorio.

### Perché livelli e aggiunte

- **Si spiega in due righe:** «Scegli il piano per quanto è grande il tuo centro.
  Aggiungi solo quello che ti serve.»
- **Si torna indietro in un verso solo.** Un'aggiunta che quasi tutti prendono
  può entrare in un livello domani, ed è un regalo; una cosa compresa che esce
  per diventare un'aggiunta fa andare via i clienti. Senza ancora un cliente,
  si parte da dove si può solo migliorare.
- **È quello che il codice fa già:** gli extra (telefono, marketing, assistente,
  firma) con la loro prova di 14 giorni.

Fra sei mesi si guardano i dati: se quasi tutti i Centri prendono il marketing,
entra nel Centro con 10-20 € in più, annunciato come una novità.

La variante B (i piani grandi comprendono più cose: 59 / 99 / 169 / 299 €) è
scartata per questo.

I consumi sono come nel listino del 01/10: WhatsApp a Meta, chiamate e SMS a
Twilio, crediti SdI oltre gli inclusi a 0,10 € (pacchetti da 500), spazio oltre
l'incluso.

## Le regole

- **Un utente** è una persona attiva che entra in DottorCloud con un livello. Non
  contano gli account dell'agenzia (System Manager), i pazienti dell'area e le
  persone dei dati di prova.
- **Il Professionista ha un utente.** Il secondo invito non parte: DottorCloud
  propone lo Studio con 14 giorni di prova, come gli extra.
- **Gli ambulatori** sono le sale attive dell'agenda, come oggi. Superarli non blocca
  niente: la pagina lo dice e propone il piano sopra.
- **Annuale:** 10 mensilità, pagate all'inizio. Si passa al piano sopra in qualunque
  momento, pagando la differenza per i mesi che restano; al piano sotto si scende
  alla scadenza.
- **Centri fondatori**, i primi 25:
  - il 30% di sconto sull'annuale, bloccato per 24 mesi;
  - l'avvio gratis (importazione, configurazione, formazione);
  - in cambio una testimonianza e il confronto sulle soglie.

  Un Centro fondatore paga 1.043 € l'anno, 87 € al mese. Dopo i 24 mesi passa al
  listino, senza aumenti da annunciare.

## I concorrenti

Verificato il 07/10/2026. Dove la fonte è un concorrente o una stima, lo dice
la colonna.

| Prodotto | Prezzo | Fatture e TS | Fonte |
|---|---|---|---|
| GipoNext | 1.080 € l'anno per un fisioterapista (90 € al mese), 2.160 € per un poliambulatorio fino a 15 specialisti (180 €), attivazione 300 € | compresi | [convenzione ADOCT, OFI Brescia](https://www.fnofi.it/ofi-brescia/wp-content/uploads/sites/9/2025/12/Locandina-Convenzione-ADOCT-per-OFI-BS-MN.pdf) |
| Doctolib | da 139 € al mese, su preventivo | no | [Appuntoo](https://appuntoo.com/blog/confronto-prezzi-gestionali/) (concorrente) |
| AlfaDocs | da 109 € al mese con 3 accessi, i moduli a parte | a parte | Appuntoo (concorrente) |
| MioDottore | non pubblicato, stimato da 69 € | no | Appuntoo (stima) |
| Nutrium | 25 € (10 pazienti attivi) o 39 € al mese | no | [Capterra](https://www.capterra.it/software/173803/nutrium) |
| FisioDesk | piani Smart, Premium, Unlimited; PhysioDesk da 69 € | sì, contabilità | [Capterra](https://www.capterra.com/p/10044705/PhysioDesk/), [convenzioni OFI](https://www.fnofi.it/ofi-bolzano/wp-content/uploads/sites/2/2024/02/Convenzioni-17.02.24.pdf) |

Il listino del 01/10 dava FisioDesk a 0–44 € e Nutrium a 28–50 €: i numeri qui
sopra sono più recenti.

- **Sconto annuale nel software in abbonamento:** 15–20% di mediana, 10–20% nel
  software di settore ([CostBench 2026](https://costbench.com/reports/software-pricing-findings-2026-q3/),
  [Monetizely](https://www.getmonetizely.com/articles/how-to-structure-the-perfect-annual-discount-a-guide-for-saas-leaders)).
  Due mesi gratis fanno il 17%.
- **Il confronto più vicino è GipoNext**, che ha fatture e TS dentro come noi:
  - il Professionista costa 31 € al mese in meno di GipoNext per un fisioterapista;
  - il Centro costa 31 € al mese in meno di GipoNext per un poliambulatorio;
  - noi non chiediamo l'attivazione, e in più ci sono WhatsApp, prenotazione
    online, area pazienti e marketing.

### Dove siamo più forti, dove più deboli

**Più forti:**
- tutto in un prezzo che si legge;
- si paga per stanze, non per medici;
- le cose dei centri di oggi: WhatsApp, l'app del paziente, i moduli firmati dal
  telefono;
- un'agenzia vicina che porta pazienti.

**Più deboli:**
- non siamo un portale: DottorCloud non porta pazienti da sé. Si presenta *sopra*
  MioDottore (la sincronizzazione c'è già), non al suo posto;
- nessuno ci conosce, e sui dati sanitari si sceglie chi sembra solido;
- cambiare gestionale fa paura se i pazienti non arrivano con te.

## Cosa manca prima del lancio

### Nel prodotto

| # | Cosa | Stato oggi |
|---|---|---|
| 1 | Il Professionista, il conteggio degli utenti, il secondo invito che propone lo Studio | ✅ fatto: `UTENTI`, `chi_conta()`, `verifica_utenti()` all'invito e a chi prende un livello, «Chiedi il piano Studio» nella pagina Funzionalità |
| 2 | La fatturazione compresa in ogni piano | ✅ fatto: la base la comprende (`catalogo.BASE`), una riga «spenta» del vecchio listino non la toglie più |
| 3 | I numeri del listino nel codice: ambulatori, crediti SdI | ✅ fatto (`crm_plan.py`: 3 / 3 / 5 / 10 ambulatori, 300 / 600 / 1.200 / 2.400 crediti); i prezzi non stanno nel codice |
| 4 | La pagina Funzionalità con i nuovi piani | ✅ fatto per taglie, utenti e la prova dell'assistente; le aggiunte sono gli extra che c'erano già |
| 5 | **Portare via i propri dati**: un archivio con persone, appuntamenti, cartelle, documenti e fatture | ✅ fatto: Impostazioni > Il centro > I tuoi dati (`crm/esportazione`), solo il responsabile, registro degli accessi, una settimana e poi sparisce |
| 6 | **Importare dal vecchio gestionale**: anagrafiche, appuntamenti futuri e saldi | 🟡 le persone sì: Impostazioni > Il centro > I tuoi dati (`crm/importazione`) legge un Excel o CSV di qualunque gestionale, riconosce le colonne, mostra riga per riga cosa succede, non crea doppioni (codice fiscale, email, cellulare), tiene i dati di fatturazione e le note; con la clinica sono pazienti per la regola «importazione». Da fare: appuntamenti futuri e saldi, e la prova con un'esportazione vera di GipoNext e AlfaDocs |
| 7 | Annuale, mensile e fondatore sul piano del centro, per fatturarli | da decidere dove: dipende da chi emette le fatture di NPM2 |

### Fuori dal prodotto

| # | Cosa | Perché |
|---|---|---|
| 8 | Nomina a responsabile del trattamento (art. 28 GDPR) da firmare con ogni centro | ✍️ bozza: [legale/nomina-responsabile.md](./legale/nomina-responsabile.md), da far rivedere |
| 9 | Valutazione d'impatto (DPIA) del modulo clinico | ✍️ bozza: [legale/dpia-cartella.md](./legale/dpia-cartella.md), da far rivedere |
| 10 | Parere legale su dispositivo medico ed EHDS (regolamento UE 2025/327) | da chiedere: le domande sono pronte in [legale/README.md](./legale/README.md#le-domande-per-il-legale) |
| 11 | Una pagina «I tuoi dati»: dove stanno (Hetzner, Germania), backup cifrati, chi legge la cartella, come si esce | ✍️ testo pronto: [legale/i-tuoi-dati.md](./legale/i-tuoi-dati.md); da confermare i backup |
| 12 | Condizioni di servizio e pagamento (carta o SEPA, rinnovo, disdetta) | ✍️ bozza: [legale/condizioni.md](./legale/condizioni.md); da scegliere il fornitore dei pagamenti |
| 13 | Prezzo del piano sito di Frappe Cloud su server dedicato | ✅ chiuso: sul proprio server i siti non costano niente in più, si paga solo il server (70 $ al mese il cpx32, circa 3 € a centro con 20–25 centri; [doc 25](../../crm/25-costo-hosting.md)) |
| 14 | **Prezzi sul sito**: oggi `siti/dottorcloud/` non mostra piani né prezzi, per scelta | i prezzi pubblici sono un vantaggio sui concorrenti: va deciso se cambiare la regola |

## Cosa cambia nel codice

Quando la proposta è approvata:

- `crm/fcrm/doctype/crm_plan/crm_plan.py`:
  - `AMBULATORI = {"Solo": 3, "Studio": 3, "Centre": 5, "Polyclinic": 10, "Large": None}`;
  - `UTENTI = {"Solo": 1}`;
  - `CREDITI_SDI = 300 / 300 / 600 / 1.200` (fatto);
  - `RICHIESTE_DI_PROVA = 50`: l'assistente in prova le conta e, finite,
    rimanda alle Funzionalità (`crm/assistente/modello.py`, fatto);
  - «Solo» si legge «Professionista».
- `crm/archivio/regole.py`: `SPAZIO_COMPRESO` 300 GB / 600 GB / 1 TB / 2 TB (fatto).
- Il contatore delle email di marketing (5.000 al mese) e i pacchetti: da fare.
- `crm/api/plan.py` conta gli utenti accanto alle sale. `invite_by_email`
  (`crm/api/__init__.py`) non manda il secondo invito di un Professionista.
- La fatturazione esce dagli extra e entra in ciò che il piano comprende
  (`compresi()`), con una patch che riaccende `fatturazione` dove era spenta.
- `Settings/PlanSettings.vue`, `utils/funzionalita.js`, `it.po`.
- [listino.md](./listino.md) prende il posto di questa proposta, e il
  [doc 36](../../crm/36-funzionalita.md) si aggiorna.

## Da decidere

1. Il Centro a 149 € o a 139 €.
2. Il Professionista con una segretaria. Le possibilità:
   - (a) si passa allo Studio;
   - (b) un utente di segreteria a 15 € al mese, con il solo livello Accoglienza.

   La proposta è (b).
3. I centri fondatori: quanti (25?) e quanto sconto (30%?).
4. I prezzi sul sito (punto 14).
5. Chi non è una clinica (centri estetici, palestre): stesso listino, oppure un
   piano senza la parte clinica.
