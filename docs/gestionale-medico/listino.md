# Il listino: una base, i moduli, i servizi dell'agenzia

**Stato:** 🟡 proposta (29/09/2026), da verificare con i primi centri. Prezzi al
mese, IVA esclusa. Come il CRM legge il piano (moduli attivi, prova, sola lettura)
è nel [doc 30](../progetto-ghl/30-ruoli-e-permessi.md#il-piano-del-centro-la-seconda-chiave).

## In una pagina

Si parte dal minimo e si aggiunge. Gli strati sono tre:

1. **Il software**: una Base per tutti, pagata per agenda, più i moduli.
2. **I consumi**: WhatsApp, SMS, telefono e firme, al costo più un margine.
3. **I servizi dell'agenzia**: segreteria, campagne, avvio. Finché sono attivi
   sbloccano i moduli con cui l'agenzia lavora.

Il prezzo è per centro e pubblico, senza un salto per ogni operatore in più. Il
centro amplia il piano da solo, dal CRM.

## Cosa costano le alternative

| Prodotto | Prezzo al mese | Nota |
|---|---|---|
| Doctolib | da 139 € | su preventivo, SMS a parte |
| MioDottore | circa 69 €, stimati | su preventivo; gestionale e telefonia a parte |
| AlfaDocs | da 109 € con 3 accessi | con i moduli si arriva a 1.500–2.000 € l'anno |
| Gestionali per una sola professione | 30–80 € | FisioDesk 0–44 €, OsteoEasy circa 31 €, Nutrium 28–50 €, MètaDieta 79 € |
| Poliambulatori | 100–300 € per 5–10 specialisti | oltre 500 € per le strutture grandi |
| GoHighLevel | 97–497 $ | solo CRM e marketing: niente cartella, niente Sistema TS |

Un centro che oggi usa MioDottore o Doctolib, più un gestionale, più uno
strumento per WhatsApp, spende facilmente 250–450 € al mese.

## 1. Il software

**La Base** serve a tutti e comprende:

- persone e agenda con le sale, cicli di sedute, abbonamenti e liste d'attesa;
- prenotazione online e collegamento alle piattaforme (MioDottore…);
- promemoria;
- conversazioni (email, WhatsApp, SMS);
- fatture e Sistema TS, preventivi;
- moduli con firma e registro dei consensi, documenti della persona;
- dashboard, utenti e livelli.

Si paga per agenda, cioè per ogni professionista che riceve appuntamenti. Conta
chi ha almeno un appuntamento nel mese, anche se non entra mai nel CRM; sale,
attrezzature, segreterie e manager no, quindi gli altri utenti sono illimitati
([doc 30](../progetto-ghl/30-ruoli-e-permessi.md#il-piano-del-centro-la-seconda-chiave)).

| Taglia | Agende | Base | + Clinica | + Marketing | + Telefono |
|---|---|---|---|---|---|
| Solo | 1 | 39 € | 29 € | 39 € | 19 € |
| Studio | fino a 3 | 69 € | 49 € | 59 € | 29 € |
| Centro | fino a 8 | 129 € | 89 € | 89 € | 49 € |
| Poliambulatorio | fino a 15 | 219 € | 149 € | 129 € | 79 € |
| Oltre 15 | | +12 € ad agenda | | | |

- **Area clienti**: l'app della persona (appuntamenti, fatture, moduli, documenti,
  messaggi, chat), con i piani di allenamento e di abitudini e i programmi a tappe.
  Prezzo da decidere.
- **Clinica**: cartella e referti, dossier, sintesi, odontogramma, piani
  alimentari e di riabilitazione, l'assistente in cartella. Comprende l'Area
  clienti.
- **Marketing**: automazioni, campagne, Meta (lead e spesa), social,
  tracciamento, costo per nuovo paziente, sito.
- **Telefono**: centralino nel browser, dialer, registrazioni e trascrizioni.
- **Assistente**: 19 € per professionista.
- **Firma avanzata**: 39 € per centro. Il fornitore costa circa 30 € al mese
  (Namirial, 360 € l'anno per 2.000 documenti,
  [ricerca](./ricerca-design.md#34-i-fornitori)).
- **Base, Clinica e Marketing insieme**: 15% di sconto. Uno Studio completo
  costa 150 €, un Centro 261 €.
- **Pagando un anno in anticipo**, due mesi gratis.

### Il Sistema TS sta nella Base

Chi fattura prestazioni sanitarie a privati le deve comunicare al Sistema TS, e
non le può mandare allo SdI. È il modulo TS a saperlo: il suo registro delle
professioni (`crm/tessera_sanitaria/engine/professioni.py`) tiene quelle fatture
fuori dallo SdI. Se il TS arrivasse solo con la Clinica, un fisioterapista con le
sole fatture le manderebbe allo SdI, cioè commetterebbe un errore fiscale.

Nel codice il TS resta agganciato alla fatturazione e si attiva da solo quando
l'azienda ha professioni sanitarie; la clinica è un modulo a parte
([i tre strati](./design.md#tre-strati-crm-fatturazione-clinica)). Come
offerta, Base più Clinica è il pacchetto per i centri medici. Il TS però c'è
anche senza la Clinica.

## 2. I consumi

WhatsApp, SMS, minuti di telefono e firme oltre la soglia: al costo più un
margine, uguali per tutti. Il CRM li conta e li manda all'agenzia ogni mese per la
fattura.

## 3. I servizi dell'agenzia, e cosa sbloccano

| Servizio | Prezzo indicativo | Sblocca finché è attivo |
|---|---|---|
| Segreteria: l'agenzia risponde a telefono e WhatsApp, prenota, richiama | da 250 € fino a circa 100 appuntamenti al mese, circa 490 € fino a 250 | Base e Telefono, più gli account per la segreteria dell'agenzia |
| Campagne e lead: inserzioni, moduli, automazioni di contatto e richiamo, report | 390–890 € più il budget pubblicitario | Marketing |
| Crescita: campagne più la segreteria che richiama i lead | i due servizi insieme, scontati | Base, Telefono, Marketing |
| Avvio: importazione, configurazione, modelli, formazione | 290–1.490 € una volta sola, gratis con 12 mesi di servizio | — |

Come funziona lo sblocco:

- **La Base è inclusa fino alla taglia Studio.** Oltre, il centro paga la
  differenza.
- **Nella pagina del piano** il centro vede i moduli sbloccati con la scritta
  "incluso nel servizio dell'agenzia".
- **Quando un servizio finisce**, i moduli restano attivi 30 giorni. Poi il centro
  li paga a listino, oppure diventano di sola lettura: non si cancella niente, e
  campagne e automazioni vanno in pausa.
- **Oltre a quello che il servizio include**, il centro aggiunge da solo quello
  che vuole, per esempio la Clinica.

## Come si amplia il piano

In Impostazioni → Piano il centro vede:

- la taglia e i moduli attivi;
- i consumi del mese;
- un pulsante "Attiva" per ogni altro modulo, con il prezzo.

"Attiva" apre subito 14 giorni di prova e manda la richiesta all'agenzia; si paga
dal mese dopo. Se le agende superano la taglia, il CRM avvisa e propone la taglia
sopra, ma non blocca mai né appuntamenti né fatture.

## Quattro esempi

| Chi | Cosa prende | Al mese |
|---|---|---|
| Fisioterapista da solo, vuole agenda e fatture | Base Solo | 39 € |
| Studio di nutrizione, 2 professioniste, cartella e piani | Base Studio + Clinica | 118 € |
| Poliambulatorio con 8 medici, le campagne le fa l'agenzia | Base Centro + Clinica; Marketing incluso nel servizio | 218 € più il servizio campagne |
| Centro estetico con la segreteria dell'agenzia | servizio Segreteria, che include Base e Telefono | 250–490 €, +59 € se vuole anche il marketing |

## Perché regge

- **A 39 € si parte al livello dei prodotti di settore**, che costano 30–50 €. Il
  professionista che lavora da solo è il punto debole: lì la Base deve bastare.
- **Chi prende tutto spende meno di oggi.** Gestionale, MioDottore e strumenti di
  marketing messi insieme costano di più.
- **Nessun salto di prezzo per ogni operatore in più.** È la lamentela più comune
  sui concorrenti ([ricerca](./ricerca-design.md#12-di-cosa-si-lamentano-i-clienti)),
  e le taglie larghe la evitano.
- **Prezzi pubblici.** Doctolib, MioDottore, GipoNext e AlfaDocs lavorano tutti su
  preventivo: un listino chiaro è già un vantaggio.
- **I costi vivi sono bassi.** Il server costa circa 4 € al mese per sito
  ([doc 25](../progetto-ghl/25-costo-hosting.md)); con backup e dati clinici si
  contano 10 €. Il costo vero è l'assistenza e l'avvio.
- **I servizi dell'agenzia fanno usare il software.** Se il rapporto con l'agenzia
  finisce, i moduli si possono continuare a pagare invece di sparire.

## Come si verifica

Con 3–5 centri pilota e un "prezzo fondatori", per esempio il 30% in meno
bloccato per 12 mesi. Poi si guarda quali moduli e servizi prendono davvero, e si
rifanno i numeri.

## Da decidere

1. I prezzi, dopo i centri pilota.
2. Il prezzo dell'Area clienti da sola, e quello della Clinica, che ora comprende
   l'area. *Deciso il 30/09/2026* il resto: moduli con firma, consensi, documenti,
   preventivi, abbonamenti e liste d'attesa vanno nella Base, perché la privacy e i
   contratti firmati servono a tutti; l'area e i piani non medici sono un modulo a
   sé ([i tre strati](./design.md#tre-strati-crm-fatturazione-clinica)).

## Fonti

- [Appuntoo, confronto prezzi 2026](https://appuntoo.com/blog/confronto-prezzi-gestionali/)
  (è un concorrente, dati del 14/07/2026)
- [MioDottore, prezzi per i centri](https://pro.miodottore.it/prezzi-centri-medici)
  (solo su richiesta)
- [Ambulatorio Facile](https://www.ambulatoriofacile.it/blog/gestionale-poliambulatorio)
- [GoHighLevel, piani 2026](https://www.ghlexperts.com/gohighlevel-plans-pricing)
- [Namirial eSignAnyWhere](https://www.namirial.it/dettagli/esignanywhere/)
- [SegretariaVirtualeMedico, offerta](https://www.segretariavirtualemedico.it/offerta/)
  (250 € fino a 100 appuntamenti, 490 € fino a 250)
- [Segreterie virtuali per medici](https://www.segreterievirtuali.it/assistente-virtuale/segretaria-virtuale-medici-di-base/)
  (da 39 €)
- [WebNovis](https://www.webnovis.com/blog/quanto-costa-campagna-facebook-ads.html)
  e [Giuseppe Basile](https://giuseppebasileweb.it/costi-pubblicita-facebook/) sul
  costo di gestione delle campagne Meta
