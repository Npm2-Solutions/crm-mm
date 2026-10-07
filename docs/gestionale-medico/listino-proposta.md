# Il listino per il lancio — proposta

**Stato:** 📝 proposta del 07/10/2026, da approvare. Quando è approvata sostituisce
[il listino del 01/10](./listino.md) e il codice si adegua ([cosa cambia](#cosa-cambia-nel-codice)).

Cosa cambia rispetto al listino del 01/10:

1. **La fatturazione è compresa in ogni piano**, con il Sistema TS. Non è più un extra.
2. **C'è un piano per chi lavora da solo**: un utente, fino a 3 ambulatori.
3. **I team pagano per ambulatori**, con utenti illimitati, come prima.
4. **I prezzi sono al mese; l'anno pagato in anticipo costa 10 mensilità.**
5. **Al lancio c'è l'offerta per i centri fondatori** invece di un listino più basso.

## I piani

| Piano | Per chi | Utenti | Ambulatori | Al mese | L'anno | Crediti SdI l'anno |
|---|---|---|---|---|---|---|
| **Professionista** | chi lavora da solo, anche su più sedi | 1 | fino a 3 | **59 €** | 590 € | 300 |
| **Studio** | 2 o 3 professionisti insieme | illimitati | fino a 3 | **99 €** | 990 € | 600 |
| **Centro** | centri e piccoli poliambulatori | illimitati | fino a 5 | **149 €** | 1.490 € | 1.200 |
| **Poliambulatorio** | strutture con molti specialisti | illimitati | fino a 10 | **249 €** | 2.490 € | 2.400 |
| Oltre 10 ambulatori | | illimitati | | +25 € ad ambulatorio | +250 € | 2.400 |

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

### Variante B: i piani più grandi comprendono più cose

Come fanno molti software in abbonamento (e Claude, con Pro e Max): pochi piani,
e salendo ognuno ha dentro più cose, non solo più spazio. La taglia la danno
ancora gli ambulatori. Gli extra si comprano a parte sui piani piccoli e sono
compresi in quelli grandi.

| | Professionista | Studio | Centro | Poliambulatorio |
|---|---|---|---|---|
| Al mese | 59 € | 99 € | **169 €** | **299 €** |
| L'anno | 590 € | 990 € | 1.690 € | 2.990 € |
| Fatture e Sistema TS | ✓ | ✓ | ✓ | ✓ |
| Telefono | +50 € l'anno | ✓ | ✓ | ✓ |
| Marketing | +29 € | +39 € | ✓ | ✓ |
| Firma avanzata | +39 € | +39 € | +39 € | ✓ (2.000 l'anno) |
| Assistente | +19 € a professionista | +19 € | +19 € | 3 professionisti compresi, poi +19 € |

**Perché così:**

- **Ogni piano ha un motivo per salire.** Il Professionista lavora da solo, lo
  Studio ha la segreteria al telefono, il Centro fa crescere i pazienti con il
  marketing, il Poliambulatorio ha tutto.
- **Costa poco a noi.**
  - telefono e marketing hanno i consumi pagati dal centro a Twilio e a Meta, e
    dentro un piano pesano solo l'assistenza;
  - la firma avanzata costa circa 30 € al mese a centro (Namirial), quindi entra
    solo dal Poliambulatorio;
  - l'assistente consuma il modello a ogni uso, quindi è compreso solo per 3
    professionisti.
- **Il centro paga meno che con gli extra a parte:**
  - il Centro varrebbe 149 + 59 + telefono = circa 212 € al mese, e costa 169 €;
  - il Poliambulatorio varrebbe 249 + 89 + 39 + 57 = 434 €, e costa 299 €.
- **Chi non vuole il marketing paga 20 € in più al Centro, 50 € al
  Poliambulatorio.** Nelle taglie grandi, però, il marketing è il motivo per cui
  arrivano dall'agenzia.

La variante B incassa di più a centro e si spiega con una frase per piano.
La variante A (tutto a parte) costa meno per chi vuole solo il gestionale.
**Proposta: la B**, perché il lancio passa dall'agenzia e i suoi centri vogliono
marketing e telefono.

### Gli extra (variante A)

| Extra | Professionista | Studio | Centro | Poliambulatorio |
|---|---|---|---|---|
| Marketing | 29 € | 39 € | 59 € | 89 € |
| Telefono | 50 € l'anno | 50 € l'anno | 50 € l'anno | 50 € l'anno |
| Assistente | 19 € al mese per ogni professionista che lo usa | | | |
| Firma avanzata | 39 € al mese, 2.000 firme l'anno | | | |

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
| 4 | La pagina Funzionalità con i nuovi piani | ✅ fatto per taglie e utenti; da rivedere se si sceglie la variante B (gli extra compresi nei piani grandi) |
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
| 13 | Prezzo del piano sito di Frappe Cloud su server dedicato | ✅ chiuso: sul proprio server i siti non costano niente in più, si paga solo il server (70 $ al mese il cpx32, circa 3 € a centro con 20–25 centri; [doc 25](../progetto-ghl/25-costo-hosting.md)) |
| 14 | **Prezzi sul sito**: oggi `sito/` non mostra piani né prezzi, per scelta | i prezzi pubblici sono un vantaggio sui concorrenti: va deciso se cambiare la regola |

## Cosa cambia nel codice

Quando la proposta è approvata:

- `crm/fcrm/doctype/crm_plan/crm_plan.py`:
  - `AMBULATORI = {"Solo": 3, "Studio": 3, "Centre": 5, "Polyclinic": 10, "Large": None}`;
  - `UTENTI = {"Solo": 1}`;
  - `CREDITI_SDI = 300 / 600 / 1.200 / 2.400`;
  - «Solo» si legge «Professionista».
- `crm/api/plan.py` conta gli utenti accanto alle sale. `invite_by_email`
  (`crm/api/__init__.py`) non manda il secondo invito di un Professionista.
- La fatturazione esce dagli extra e entra in ciò che il piano comprende
  (`compresi()`), con una patch che riaccende `fatturazione` dove era spenta.
- `Settings/PlanSettings.vue`, `utils/funzionalita.js`, `it.po`.
- [listino.md](./listino.md) prende il posto di questa proposta, e il
  [doc 36](../progetto-ghl/36-funzionalita.md) si aggiorna.

## Da decidere

1. Come sono fatti i piani:
   - variante A, tutto a parte: 59 / 99 / 149 / 249 €, oppure il Centro a 139 €;
   - variante B, i piani grandi comprendono più cose: 59 / 99 / 169 / 299 €.
2. Il Professionista con una segretaria. Le possibilità:
   - (a) si passa allo Studio;
   - (b) un utente di segreteria a 15 € al mese, con il solo livello Accoglienza.

   La proposta è (b).
3. I centri fondatori: quanti (25?) e quanto sconto (30%?).
4. I prezzi sul sito (punto 14).
5. Chi non è una clinica (centri estetici, palestre): stesso listino, oppure un
   piano senza la parte clinica.
