# 66 — I principi di esperienza e interfaccia

<!-- Copyright (c) 2026, NPM2 Solutions Srl and contributors -->

**Stato:** riferimento (12/10/2026). Sono le regole con cui si disegna, si scrive e
si controlla ogni schermata di DottorCloud: il gestionale su computer, tablet e
telefono, l'area dei clienti e le pagine pubbliche (`/prenota`, `/modulo`). Ogni
regola porta le fonti da cui viene. In tutto sono 302 principi in otto
famiglie, più 11 che valgono solo con la clinica accesa, e citano
719 fonti diverse.

## A che cosa servono

Una schermata nuova, o una che cambia, si confronta con questi principi due volte:
prima di scriverla e prima che vada in `develop`. La
[lista di controllo](#la-lista-di-controllo-per-una-schermata), più sotto, dice
che cosa guardare e rimanda ai principi.

AGENTS.md dice *come* DottorCloud fa le cose: i componenti, i file, le convenzioni.
Questi principi dicono *perché*, da quale fonte, con quale soglia e come lo si
verifica. Se i due non si accordano, uno è sbagliato e si corregge nella stessa
modifica.

I principi nascono dallo studio dell'esperienza d'uso di ottobre 2026. Ogni
schermata è stata resa su un banco di prova, su computer e su telefono, nel tema
chiaro e in quello scuro. È stata controllata con axe e a mano, poi corretta e
ricontrollata. I difetti trovati, con la loro gravità, stanno negli «Errori da
evitare» dei principi che violavano.

Si leggono insieme a:

- il [doc 29](29-telefono.md): le regole di ogni schermata che un telefono vede.
  La famiglia 5 le spiega e ne dà le fonti;
- i [doc 33](33-design-system-espresso.md) e [39](39-design-system-completo.md)
  e il [design system Espresso](../../brand/dottorcloud/design-system/espresso/README.md):
  colori, caratteri e componenti. La famiglia 4 dice le regole che li reggono;
- il [doc 40](40-italiano.md): la voce e le parole di DottorCloud. La famiglia 7
  ne dà le regole e le fonti;
- i [doc 45](45-codici-in-parole.md) e [48](48-controlli-in-parole.md): i codici
  e i controlli detti in parole;
- il [doc 55](55-le-scelte-delle-liste.md): che cosa una lista offre di scegliere;
- il [doc 64](64-collaudo/README.md): il collaudo prima della produzione, con le
  liste da spuntare per ogni ruolo.

## Come si legge un principio

Ogni principio ha un codice, come `WCAG-2.4.7`, `MOB-BERSAGLIO` o `PRIV-STEP-UP`. Il
codice non cambia, e serve a citarlo nel codice, in una revisione o in un altro
documento. Il titolo dice la regola in breve. Poi vengono le sue parti:

- **Regola**: che cosa deve essere vero, detto in modo che si possa verificare.
- **Perché**: le ragioni, con le parole delle fonti tra virgolette.
- **Soglie ed eccezioni**: i numeri (rapporti di contrasto, pixel, millisecondi,
  caratteri) e i casi in cui la regola non vale.
- **In DottorCloud**: dove si applica, con i file e i componenti, e com'era il
  codice il 12/10/2026.
- **Come si verifica**: lo strumento, la prova a mano, il test che lo controlla.
- **Errori da evitare**: gli errori tipici. Ci sono anche quelli trovati nello
  studio, con la gravità e lo stato (corretto o aperto).
- **Vedi anche**: i principi di altre famiglie sulla stessa cosa, vista da un
  altro lato.
- **Fonti**: per ogni fonte il punto preciso (il criterio, la sezione, la pagina),
  chi la pubblica e quando è stata letta.

«In DottorCloud» ed «Errori da evitare» descrivono il codice com'era il 12/10/2026.
Il codice va avanti, la regola resta: chi cambia ciò che descrivono aggiorna anche
loro.

Il prefisso del codice dice di che cosa parla il principio:

| Prefisso | Di che cosa parla |
|---|---|
| `NN-` | le dieci euristiche di Nielsen e la loro scala di gravità |
| `UX-` | le leggi e i modelli dell'esperienza d'uso |
| `PERF-` | le prestazioni: Core Web Vitals e RAIL |
| `WCAG-` | un criterio delle WCAG 2.2 |
| `ARIA-`, `APG-` | che cosa dice un componente al lettore di schermo, e come si usa con la tastiera |
| `FOCUS-`, `CONTRASTO-` | l'indicatore del fuoco e la misura del contrasto |
| `GS-`, `VIS-` | la Gestalt e la gerarchia visiva |
| `TIPO-`, `SPAZIO-`, `COL-`, `ICO-`, `MOT-`, `DATI-` | tipografia, spazio, colore, icone, movimento, grafici |
| `MOB-` | il telefono, il tablet e il tocco |
| `FORM-` | i moduli e l'inserimento dei dati |
| `LING-`, `I18N-` | le parole e le lingue |
| `NORM-` | le norme sull'accessibilità |
| `SAN-` | la sicurezza del paziente |
| `PRIV-` | i dati personali e quelli sanitari |
| `IA-`, `REG-` | l'assistente e il regolamento sui dispositivi medici |

## Quando due principi tirano da parti diverse

Vale quest'ordine.

1. **La legge e la sicurezza della persona**: le norme della famiglia 7, la
   famiglia 8 e i principi sanitari della clinica. Nessuna comodità compensa un
   paziente scambiato con un altro, né un dato sanitario letto da chi non deve.
2. **Le WCAG 2.2 al livello AA** (famiglie 2 e 3). Sono il metro della
   conformità: un criterio non si scambia con un altro.
3. **Le regole di DottorCloud che vanno oltre il minimo.** Per esempio: 44×44 px
   al tocco dove le WCAG chiedono 24 ([WCAG-2.5.5](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-255--al-tocco-4444-px-la-regola-di-dottorcloud-sopra-il-minimo-255-aaa-obiettivo), [MOB-BERSAGLIO](principi/05-telefono-e-tocco.md#mob-bersaglio--bersagli-grandi-quanto-un-dito)), i campi a
   16 px sul telefono ([MOB-CAMPI-16PX](principi/05-telefono-e-tocco.md#mob-campi-16px--campi-a-16-px-niente-zoom-involontario-su-iphone)), frasi intere in ogni lingua
   ([I18N-FRASI-INTERE](principi/07-lingua-e-norme.md#i18n-frasi-intere--frasi-intere-mai-pezzi-incollati)).
4. **Le euristiche e le leggi dell'esperienza d'uso** (famiglie 1 e 4). Orientano
   ma non misurano: servono a scegliere tra due soluzioni che rispettano già tutto
   il resto.

## La gravità

I difetti dello studio e delle revisioni hanno la gravità della scala di Nielsen
([NN-GRAVITA](principi/01-interazione.md#nn-gravita--scala-di-gravità-dei-problemi-04)):

| Gravità | Che cosa vuol dire |
|---|---|
| 0 | Non è un problema di usabilità. |
| 1 | Cosmetico: si corregge se avanza tempo. |
| 2 | Minore: si corregge, con priorità bassa. |
| 3 | Grave: si corregge, con priorità alta. |
| 4 | Catastrofico: si corregge prima di rilasciare. |

Per decidere la gravità si guarda quanto spesso il difetto capita, quanto pesa a chi
lo incontra e se si ripresenta ogni volta. In un centro medico un difetto che può
far scambiare un paziente o mostrare un dato sanitario parte da 3.

## Le fonti, e come sono state controllate

Tra il 10 e il 12 ottobre 2026 ogni famiglia è stata scritta da un agente di
ricerca. Un secondo agente l'ha poi ricontrollata: ha riaperto ogni fonte,
citazione per citazione, e ha cercato nel codice ogni affermazione su DottorCloud.
Ciò che non reggeva è stato corretto o tolto. La data «consultato il…» dice quando
una fonte è stata letta.

Dall'ambiente in cui si faceva la ricerca alcuni siti non si raggiungevano:
w3.org, MDN, web.dev, EUR-Lex, Normattiva, AgID. Dove una fonte pubblica il suo
sorgente ufficiale, si è letto quello:

- le WCAG, le tecniche e le ARIA Authoring Practices dai repository del W3C;
- MDN dal suo repository;
- il GOV.UK Design System e Designers Italia dai loro;
- lo standard HTML dal repository del WHATWG;
- le linee guida di Apple dai dati JSON da cui Apple costruisce le sue pagine.

Il collegamento porta alla pagina pubblica, e accanto c'è il «sorgente letto».

Una fonte trovata solo con una ricerca sul web lo dice: «via WebSearch». Vuol dire
che se n'è letto un estratto, non il testo intero.

Leggi e regolamenti sono citati per articolo: la legge Stanca, l'European
Accessibility Act, il GDPR, l'AI Act e il regolamento sui dispositivi medici.
Prima di decidere su un obbligo si legge il testo in vigore e, se serve, si
chiede a un legale.

## Che cosa non sono

Non sostituiscono una prova con le persone. Una segretaria al bancone, un
fisioterapista con il tablet, un paziente anziano con il suo telefono trovano
quello che nessuna regola prevede ([SAN-SCENARI-CRITICI](../verticali/clinica/principi-sanitari.md#san-scenari-critici--si-provano-gli-scenari-critici-e-si-contano-gli-errori-duso)): per questo c'è il
collaudo del [doc 64](64-collaudo/README.md).

Non sono un parere legale.

E non sono un elenco da spuntare a memoria: un principio si applica sapendo perché
c'è.

## Come si aggiornano

Le pagine delle famiglie si cambiano a mano, come ogni documento.

- Un principio nuovo va nella famiglia della sua fonte, con un codice nuovo e le
  sue fonti.
- Un principio che esiste solo per i dati sanitari o per il lavoro clinico va nei
  [principi sanitari](../verticali/clinica/principi-sanitari.md).
- Il codice di un principio non cambia. Se una regola non vale più, il principio lo
  dice e resta.
- Quando una fonte cambia (le WCAG 3, una nuova versione delle linee guida di
  Apple) si rilegge, e si aggiornano la regola e la data.

## Le famiglie

| Famiglia | Principi | Citazioni |
|---|---|---|
| [1. Interazione, stato e prestazioni](principi/01-interazione.md) | 40 | 188 |
| [2. Percepibile e robusto: WCAG 2.2 e ARIA](principi/02-wcag-percepibile-e-robusto.md) | 37 | 236 |
| [3. Utilizzabile e comprensibile: WCAG 2.2 e tastiera](principi/03-wcag-utilizzabile-e-comprensibile.md) | 47 | 186 |
| [4. Aspetto: leggi della UX, gerarchia, tipografia, colore, movimento](principi/04-aspetto.md) | 41 | 174 |
| [5. Telefono, tablet e tocco](principi/05-telefono-e-tocco.md) | 37 | 206 |
| [6. Moduli e inserimento dei dati](principi/06-moduli.md) | 41 | 203 |
| [7. Parole, lingua e norme](principi/07-lingua-e-norme.md) | 37 | 134 |
| [8. La persona giusta e i suoi dati](principi/08-persone-e-dati-personali.md) | 22 | 84 |
| [I principi sanitari](../verticali/clinica/principi-sanitari.md) (clinica) | 11 | 41 |

## La lista di controllo per una schermata

Prima di chiedere una revisione, una schermata nuova o cambiata passa queste
domande. Ognuna rimanda ai principi che la reggono: lì ci sono la soglia, la prova
e gli errori già fatti.

### Prima di disegnare

- Chi la usa, dove e con che cosa: la segreteria al computer, il professionista
  con il tablet, il paziente con il suo telefono? Si decide per capacità e per
  spazio, mai per dispositivo. [MOB-CAPACITA](principi/05-telefono-e-tocco.md#mob-capacita--decidere-per-capacità-e-per-spazio-non-per-dispositivo) [MOB-TABLET](principi/05-telefono-e-tocco.md#mob-tablet--il-tablet-il-computer-toccato-col-dito)
- Ciò che si fa più spesso sta dove arrivano l'occhio e il pollice? [UX-PARETO](principi/04-aspetto.md#ux-pareto--principio-di-pareto-il-meglio-alle-azioni-di-ogni-giorno)
  [VIS-GERARCHIA](principi/04-aspetto.md#vis-gerarchia--gerarchia-visiva-un-ordine-di-lettura-voluto) [MOB-POLLICE](principi/05-telefono-e-tocco.md#mob-pollice--ciò-che-si-fa-spesso-dove-arriva-il-pollice)
- Si chiede solo ciò che serve, e niente che il sistema sappia già?
  [FORM-NECESSARIO](principi/06-moduli.md#form-necessario--chiedere-solo-ciò-che-serve-sapendo-perché) [FORM-NON-RICHIEDERE](principi/06-moduli.md#form-non-richiedere--ciò-che-il-sistema-sa-già-non-si-chiede-di-nuovo) [PRIV-MINIMO-NEI-MODULI](principi/08-persone-e-dati-personali.md#priv-minimo-nei-moduli--chiedere-solo-ciò-che-serve-compreso-ciò-che-serve-alla-sicurezza)
- Ci sono dati sanitari? Chi li legge lo decide il server, e chi non li legge vede
  un lucchetto, non un vuoto. [PRIV-CHI-PUO-LEGGERE](../verticali/clinica/principi-sanitari.md#priv-chi-puo-leggere--i-dati-sanitari-li-vede-solo-chi-li-legge-e-lo-decide-il-server) [PRIV-LUCCHETTO-E-OSCURATO](../verticali/clinica/principi-sanitari.md#priv-lucchetto-e-oscurato--un-lucchetto-dove-si-può-sapere-nessuna-traccia-di-ciò-che-è-oscurato)

### La persona giusta

- Si vede sempre per chi si sta lavorando? Dove si sceglie una persona ci sono due
  identificativi. [SAN-IDENTITA-TESTATA](principi/08-persone-e-dati-personali.md#san-identita-testata--il-paziente-sempre-identificato-nello-stesso-posto) [SAN-DUE-IDENTIFICATIVI](principi/08-persone-e-dati-personali.md#san-due-identificativi--due-identificativi-in-ogni-scelta-e-in-ogni-risultato)
  [SAN-CONTESTO-GIUSTO](principi/08-persone-e-dati-personali.md#san-contesto-giusto--si-vede-sempre-per-chi-si-sta-scrivendo)
- Prima di creare una persona, la si cerca? Gli omonimi si segnalano.
  [FORM-DOPPIONI](principi/06-moduli.md#form-doppioni--prima-di-creare-cercare-una-persona-non-nasce-due-volte) [SAN-OMONIMI](principi/08-persone-e-dati-personali.md#san-omonimi--gli-omonimi-si-segnalano-prima-che-diventino-un-doppione-o-uno-scambio)
- Il nome non si taglia dove serve a riconoscere la persona? [SAN-NOME-INTERO](principi/08-persone-e-dati-personali.md#san-nome-intero--il-nome-non-si-taglia-dove-serve-a-riconoscere)

### Lo stato

- Caricamento, vuoto, errore e riuscita hanno ognuno il suo aspetto e le sue
  parole? [NN-H1](principi/01-interazione.md#nn-h1--visibilità-dello-stato-del-sistema) [UX-SCHELETRO](principi/01-interazione.md#ux-scheletro--skeleton-screen-per-pagine-e-regioni) [UX-VUOTO](principi/01-interazione.md#ux-vuoto--stati-vuoti) [LING-ESITI-VUOTI](principi/07-lingua-e-norme.md#ling-esiti-vuoti--successi-e-liste-vuote-che-dicono-che-cosa-succede-ora)
- Un errore dice che cosa è successo, perché e come rimediare, accanto a ciò che
  riguarda? [NN-H9](principi/01-interazione.md#nn-h9--aiutare-a-riconoscere-diagnosticare-e-correggere-gli-errori) [UX-ERRORI](principi/01-interazione.md#ux-errori--messaggi-derrore-linee-guida-nng-2023-e-schemi-ostili) [LING-ERRORI](principi/07-lingua-e-norme.md#ling-errori--un-errore-dice-che-cosa-perché-e-come-rimediare) [FORM-MESSAGGIO](principi/06-moduli.md#form-messaggio--il-messaggio-derrore-dice-cosa-fare-con-le-parole-delletichetta)
  [FORM-ERRORE-ACCANTO](principi/06-moduli.md#form-errore-accanto--lerrore-sta-accanto-al-campo-legato-al-campo-e-annunciato)
- Un messaggio che compare si sente anche con il lettore di schermo, senza spostare
  il fuoco? [WCAG-4.1.3](principi/02-wcag-percepibile-e-robusto.md#wcag-413--messaggi-di-stato-annunciati-senza-spostare-il-fuoco) [ARIA-LIVE](principi/02-wcag-percepibile-e-robusto.md#aria-live--regioni-live-cortesi-o-urgenti-sempre-presenti-prima-del-messaggio)
- Un tocco risponde subito? Un'attesa di più di un secondo si vede, una di più di
  dieci si può lasciare. [UX-TEMPI](principi/01-interazione.md#ux-tempi--limiti-dei-tempi-di-risposta-01-s-1-s-10-s) [PERF-INP](principi/01-interazione.md#perf-inp--inp-reattività-di-ogni-tocco) [UX-PROGRESSO](principi/01-interazione.md#ux-progresso--indicatori-di-avanzamento)
- Niente si sposta da solo mentre si legge o si tocca? [PERF-CLS](principi/01-interazione.md#perf-cls--cls-niente-si-sposta-da-solo)

### Le azioni

- Ogni pulsante dice con un verbo che cosa succede? [LING-AZIONI](principi/07-lingua-e-norme.md#ling-azioni--pulsanti-e-link-dicono-che-cosa-succede)
  [FORM-PULSANTE](principi/06-moduli.md#form-pulsante--il-pulsante-dinvio-è-sempre-attivo-e-dice-cosa-fa)
- Ciò che non si ritira si rivede prima, o si annulla dopo? Vale per emettere,
  firmare, inviare ed eliminare. [UX-CONFERMA](principi/01-interazione.md#ux-conferma--dialoghi-di-conferma-e-quando-è-meglio-annulla) [LING-CONFERME](principi/07-lingua-e-norme.md#ling-conferme--conferme-che-nominano-lazione-e-le-conseguenze) [WCAG-3.3.4](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-334--fatture-firme-pagamenti-consensi-ed-eliminazioni-annullabili-controllati-o-confermati-334-aa)
  [FORM-IRREVERSIBILE](principi/06-moduli.md#form-irreversibile--prima-di-un-invio-che-non-si-ritira-rivedere-confermare-o-poter-annullare) [SAN-FIRMA-CONSAPEVOLE](../verticali/clinica/principi-sanitari.md#san-firma-consapevole--prima-di-firmare-oscurare-o-emettere-si-vede-chi-e-che-cosa)
- Un invio parte una volta sola? Il lavoro interrotto non si perde?
  [FORM-DOPPIO-INVIO](principi/06-moduli.md#form-doppio-invio--un-invio-parte-una-volta-sola) [FORM-BOZZE](principi/06-moduli.md#form-bozze--il-lavoro-interrotto-non-si-perde) [SAN-BOZZA-MAI-PERSA](principi/08-persone-e-dati-personali.md#san-bozza-mai-persa--il-lavoro-interrotto-non-si-perde)
- Un pulsante disattivato dice perché lo è? Spesso è meglio lasciarlo attivo e far
  dire all'invio che cosa manca. [UX-DISATTIVATI](principi/01-interazione.md#ux-disattivati--pulsanti-e-controlli-disattivati)
- Ogni gesto e ogni trascinamento ha un'alternativa a un tocco? [WCAG-2.5.1](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-251--ogni-gesto-ha-unalternativa-a-un-solo-tocco-251-a)
  [WCAG-2.5.7](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-257--ogni-trascinamento-ha-unalternativa-senza-trascinare-257-aa) [MOB-GESTI-ALTERNATIVA](principi/05-telefono-e-tocco.md#mob-gesti-alternativa--ogni-gesto-ha-unalternativa-a-un-tocco-visibile)

### La tastiera e il lettore di schermo

- Tutto si fa con la tastiera, nell'ordine in cui si legge? Il fuoco si vede
  sempre? [WCAG-2.1.1](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-211--tutto-si-fa-con-la-tastiera-211-a) [WCAG-2.4.3](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-243--il-focus-segue-un-ordine-che-conserva-il-senso-243-a) [WCAG-2.4.7](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-247--il-focus-da-tastiera-si-vede-sempre-247-aa-e-focus-visible) [FOCUS-1.4.11](principi/03-wcag-utilizzabile-e-comprensibile.md#focus-1411--lindicatore-di-focus-contrasta-almeno-31-con-ciò-che-ha-accanto-1411-aa)
- Ogni controllo ha un nome, un ruolo e uno stato? Il nome contiene le parole che
  si vedono? [WCAG-4.1.2-NOME](principi/02-wcag-percepibile-e-robusto.md#wcag-412-nome--ogni-controllo-ha-un-nome-e-un-ruolo-che-il-lettore-di-schermo-dice) [WCAG-4.1.2-STATO](principi/02-wcag-percepibile-e-robusto.md#wcag-412-stato--stati-e-valori-esposti-e-aggiornati-niente-comandi-dentro-comandi) [WCAG-2.5.3](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-253--il-nome-accessibile-contiene-le-parole-che-si-vedono-253-a)
  [LING-NOME-ACCESSIBILE](principi/07-lingua-e-norme.md#ling-nome-accessibile--il-nome-per-il-lettore-di-schermo-in-italiano-e-uguale-a-quello-che-si-vede)
- Si usa prima l'HTML nativo, senza mai un comando dentro un altro comando?
  [ARIA-NATIVO](principi/02-wcag-percepibile-e-robusto.md#aria-nativo--prima-lhtml-nativo-un-ruolo-aria-è-una-promessa) [ARIA-ACCNAME](principi/02-wcag-percepibile-e-robusto.md#aria-accname--come-nasce-il-nome-accessibile-accname-12)
- La pagina ha un titolo che la nomina, e le intestazioni sono in ordine?
  [WCAG-2.4.2](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-242--ogni-pagina-ha-un-titolo-che-dice-dove-si-è-242-a) [WCAG-1.3.1-TITOLI](principi/02-wcag-percepibile-e-robusto.md#wcag-131-titoli--titoli-veri-uno-che-nomina-la-pagina-gli-altri-in-ordine)
- Una finestra ha un nome, tiene il fuoco dentro di sé e lo restituisce quando si
  chiude? [ARIA-DIALOG](principi/02-wcag-percepibile-e-robusto.md#aria-dialog--finestre-un-nome-una-modalità-vera-il-fuoco-dentro-e-il-ritorno) [APG-DIALOG](principi/03-wcag-utilizzabile-e-comprensibile.md#apg-dialog--finestre-modali-e-richieste-di-conferma-dialog-e-alertdialog)

### Vedere e leggere

- Il testo arriva a 4,5:1, i controlli e il fuoco a 3:1? Vale nei due temi e in
  ogni stato. [WCAG-1.4.3](principi/02-wcag-percepibile-e-robusto.md#wcag-143--testo-leggibile-451-31-se-grande-in-ogni-stato-e-in-entrambi-i-temi) [WCAG-1.4.11](principi/02-wcag-percepibile-e-robusto.md#wcag-1411--controlli-stati-fuoco-icone-e-grafici-a-31) [COL-TEMI](principi/04-aspetto.md#col-temi--tema-chiaro-e-scuro-un-token-per-tema-verificato-nei-due)
- Il colore non è mai il solo segno? [WCAG-1.4.1](principi/02-wcag-percepibile-e-robusto.md#wcag-141--il-colore-non-è-mai-lunico-segno) [COL-NON-SOLO](principi/04-aspetto.md#col-non-solo--mai-il-colore-da-solo)
- A 320 px di larghezza e con il testo al 200% non si perde niente, e si scorre in
  una sola direzione? [WCAG-1.4.10](principi/02-wcag-percepibile-e-robusto.md#wcag-1410--reflow-a-320-px-si-scorre-in-una-sola-direzione) [WCAG-1.4.4](principi/02-wcag-percepibile-e-robusto.md#wcag-144--testo-al-200-senza-perdere-niente) [MOB-REFLOW](principi/05-telefono-e-tocco.md#mob-reflow--una-sola-direzione-di-scorrimento-fino-a-320-px)
  [MOB-TESTO-GRANDE](principi/05-telefono-e-tocco.md#mob-testo-grande--il-testo-ingrandito-non-rompe-nulla-lo-zoom-non-si-blocca)
- Ogni icona ha le sue parole? [UX-ICONE](principi/01-interazione.md#ux-icone--icone-con-le-loro-parole) [ICO-ETICHETTE](principi/04-aspetto.md#ico-etichette--icone-con-parole-coerenti-e-con-un-nome)
- Niente si vede solo al passaggio del mouse? [MOB-NIENTE-HOVER](principi/05-telefono-e-tocco.md#mob-niente-hover--niente-solo-al-passaggio-del-mouse)
  [WCAG-1.4.13](principi/02-wcag-percepibile-e-robusto.md#wcag-1413--tooltip-e-contenuti-al-passaggio-chiudibili-sorvolabili-persistenti-mai-unici)
- Ogni movimento ha uno scopo e si spegne con «riduci movimento»? [MOT-SCOPO](principi/04-aspetto.md#mot-scopo--movimento-con-uno-scopo-breve-e-coerente)
  [MOT-RIDOTTO](principi/04-aspetto.md#mot-ridotto--rispettare-riduci-movimento)

### Sul telefono

- I bersagli sono di 44×44 px e lontani dalle azioni rischiose? Dove una riga si
  apre, si apre da tutta la riga. [MOB-BERSAGLIO](principi/05-telefono-e-tocco.md#mob-bersaglio--bersagli-grandi-quanto-un-dito) [MOB-SPAZIO](principi/05-telefono-e-tocco.md#mob-spazio--spazio-tra-i-bersagli-azioni-rischiose-a-distanza)
  [MOB-RIGA-INTERA](principi/05-telefono-e-tocco.md#mob-riga-intera--tutta-la-riga-è-il-bersaglio)
- I dialoghi sono fogli dal basso? Indietro chiude prima ciò che sta sopra?
  [MOB-FOGLI](principi/05-telefono-e-tocco.md#mob-fogli--il-dialogo-è-un-foglio-dal-basso) [MOB-INDIETRO](principi/05-telefono-e-tocco.md#mob-indietro--indietro-chiude-prima-ciò-che-sta-sopra)
- Con la tastiera aperta resta in vista ciò che serve? Ogni campo apre la sua
  tastiera ed è a 16 px? [MOB-TASTIERA-APERTA](principi/05-telefono-e-tocco.md#mob-tastiera-aperta--con-la-tastiera-aperta-resta-in-vista-ciò-che-serve) [MOB-TASTIERA-GIUSTA](principi/05-telefono-e-tocco.md#mob-tastiera-giusta--ogni-campo-apre-la-sua-tastiera)
  [MOB-CAMPI-16PX](principi/05-telefono-e-tocco.md#mob-campi-16px--campi-a-16-px-niente-zoom-involontario-su-iphone)
- Niente finisce sotto la tacca? Le altezze si misurano sulla parte visibile dello
  schermo, mai su 100vh. [MOB-AREE-SICURE](principi/05-telefono-e-tocco.md#mob-aree-sicure--le-aree-sicure-niente-sotto-la-tacca-e-le-zone-dei-gesti) [MOB-ALTEZZA-VISIBILE](principi/05-telefono-e-tocco.md#mob-altezza-visibile--altezze-sulla-parte-visibile-non-su-100vh)

### I moduli

- Ogni campo ha un'etichetta visibile e legata al campo? Il segnaposto non la
  sostituisce. [FORM-ETICHETTA](principi/06-moduli.md#form-etichetta--ogni-controllo-ha-unetichetta-visibile-legata-nel-codice) [FORM-SEGNAPOSTO](principi/06-moduli.md#form-segnaposto--il-segnaposto-non-è-unetichetta-né-un-aiuto-né-un-valore) [WCAG-3.3.2](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-332--ogni-campo-ha-unetichetta-visibile-e-le-istruzioni-che-servono-332-a)
- Obbligatori e facoltativi si riconoscono, anche con il lettore di schermo?
  [FORM-OBBLIGATORI](principi/06-moduli.md#form-obbligatori--obbligatori-e-facoltativi-una-convenzione-spiegata-e-leggibile-dalle-tecnologie-assistive)
- Nessuna risposta è data per scontata? Un consenso si dà, non si trova già dato.
  [FORM-PREDEFINITI](principi/06-moduli.md#form-predefiniti--nessuna-risposta-data-per-scontata) [FORM-CONSENSI](principi/06-moduli.md#form-consensi--un-consenso-si-dà-non-si-trova-già-dato) [PRIV-PREDEFINITO-PROTETTIVO](principi/08-persone-e-dati-personali.md#priv-predefinito-protettivo--ciò-che-fa-uscire-o-mostrare-dati-parte-spento)
- Si accetta ciò che la persona scrive, come lo scrive? Vale per date, telefoni,
  codici fiscali e importi, e incollare funziona sempre. [FORM-POSTEL](principi/06-moduli.md#form-postel--accettare-i-formati-reali-normalizzare-dopo)
  [FORM-DATE](principi/06-moduli.md#form-date--date-allitaliana-senza-ambiguità) [FORM-TELEFONO](principi/06-moduli.md#form-telefono--un-telefono-in-un-campo-solo-accettato-come-lo-si-scrive) [FORM-CODICE-FISCALE](principi/06-moduli.md#form-codice-fiscale--il-codice-fiscale-accettato-comè-scritto-controllato-con-il-carattere-di-controllo) [FORM-INCOLLA](principi/06-moduli.md#form-incolla--incollare-e-farsi-aiutare-sempre)
- Si controlla al momento giusto? Dopo un invio non riuscito, il riepilogo degli
  errori sta in cima e prende il fuoco. [FORM-VALIDA-QUANDO](principi/06-moduli.md#form-valida-quando--validare-al-momento-giusto)
  [FORM-RIEPILOGO-ERRORI](principi/06-moduli.md#form-riepilogo-errori--dopo-un-invio-fallito-tutto-in-cima-niente-perso-il-fuoco-sul-riepilogo)

### Le parole

- L'italiano è semplice, con il «tu»? C'è un termine per ogni concetto, e niente
  codici né inglese? [LING-CHIARO](principi/07-lingua-e-norme.md#ling-chiaro--italiano-semplice-frasi-attive-e-brevi) [LING-VOCE](principi/07-lingua-e-norme.md#ling-voce--il-tu-una-voce-sola-il-tono-del-momento) [LING-GLOSSARIO](principi/07-lingua-e-norme.md#ling-glossario--un-termine-per-ogni-concetto-in-tutto-il-prodotto)
  [LING-GERGO](principi/07-lingua-e-norme.md#ling-gergo--niente-gergo-inglese-nomi-di-campo-o-codici) [I18N-CODICI-IN-PAROLE](principi/07-lingua-e-norme.md#i18n-codici-in-parole--si-salva-il-codice-si-mostra-la-parola)
- Le frasi sono intere, una per ogni caso del plurale, senza pezzi incollati?
  [I18N-FRASI-INTERE](principi/07-lingua-e-norme.md#i18n-frasi-intere--frasi-intere-mai-pezzi-incollati) [I18N-PLURALI](principi/07-lingua-e-norme.md#i18n-plurali--plurali-secondo-cldr-una-frase-per-caso)
- Date, ore, numeri e prezzi sono scritti come li scrive chi legge? Per esempio
  «12 ottobre 2026», «14:30», «65,00 €». [TIPO-DATE](principi/07-lingua-e-norme.md#tipo-date--date-allitaliana-e-mai-ambigue) [TIPO-ORE-DURATE](principi/07-lingua-e-norme.md#tipo-ore-durate--ore-a-24-ore-durate-con-le-unità)
  [TIPO-NUMERI](principi/07-lingua-e-norme.md#tipo-numeri--numeri-cifre-virgola-decimale-punto-delle-migliaia-una-regola-sola) [TIPO-VALUTA](principi/07-lingua-e-norme.md#tipo-valuta--prezzi-come-li-scrive-chi-legge-6500-) [I18N-FORMATI](principi/07-lingua-e-norme.md#i18n-formati--formati-dalla-lingua-scelta-dallutente-non-dal-browser)
- L'ora è quella del centro? [I18N-FUSO](principi/07-lingua-e-norme.md#i18n-fuso--lora-del-centro-e-i-giorni-che-non-si-spostano)

### I dati personali

- Notifiche, liste e anteprime portano il minimo, mai il contenuto sanitario?
  [PRIV-NOTIFICHE-SENZA-SALUTE](../verticali/clinica/principi-sanitari.md#priv-notifiche-senza-salute--nelle-notifiche-il-chi-e-il-dove-mai-il-contenuto-sanitario) [PRIV-MINIMO-IN-LISTE-E-COPIE](principi/08-persone-e-dati-personali.md#priv-minimo-in-liste-e-copie--liste-anteprime-e-copie-portano-il-minimo)
- Niente di personale resta nel browser? Lo schermo del bancone lo vedono anche i
  pazienti. [PRIV-NULLA-NEL-BROWSER](principi/08-persone-e-dati-personali.md#priv-nulla-nel-browser--nulla-di-personale-resta-nel-browser) [PRIV-BANCONE](principi/08-persone-e-dati-personali.md#priv-bancone--lo-schermo-del-bancone-e-il-tablet-li-vedono-anche-i-pazienti) [SAN-SESSIONE-CONDIVISA](principi/08-persone-e-dati-personali.md#san-sessione-condivisa--sessioni-adatte-a-un-pc-di-segreteria-condiviso)
- Dove scrive l'assistente, la persona sa che è l'assistente, rivede e decide?
  [IA-REVISIONE-UMANA](principi/08-persone-e-dati-personali.md#ia-revisione-umana--lassistente-scrive-bozze-la-persona-decide) [IA-TRASPARENZA](principi/08-persone-e-dati-personali.md#ia-trasparenza--si-dice-sempre-dove-cè-lintelligenza-artificiale)

### Prima della revisione

- axe non segnala violazioni nuove, nei due temi, a 1440 e a 390 px. La tastiera è
  provata a mano, e il lettore di schermo sulle parti nuove. [WCAG-QUADRO](principi/02-wcag-percepibile-e-robusto.md#wcag-quadro--wcag-22-aa-come-metro-in-ogni-variante-della-pagina)
- Sul telefono il primo caricamento non porta librerie pesanti che la pagina non
  usa subito. [PERF-CWV](principi/01-interazione.md#perf-cwv--core-web-vitals-che-cosa-si-misura-e-come) [PERF-LCP](principi/01-interazione.md#perf-lcp--lcp-con-fcp-e-ttfb)
- Una funzione clinica si prova sullo scenario critico, con una persona vera.
  [SAN-SCENARI-CRITICI](../verticali/clinica/principi-sanitari.md#san-scenari-critici--si-provano-gli-scenari-critici-e-si-contano-gli-errori-duso)

## Tutti i principi, in una riga

### 1. Interazione, stato e prestazioni

- [NN-H1](principi/01-interazione.md#nn-h1--visibilità-dello-stato-del-sistema) — Visibilità dello stato del sistema
- [NN-H2](principi/01-interazione.md#nn-h2--corrispondenza-tra-sistema-e-mondo-reale) — Corrispondenza tra sistema e mondo reale
- [NN-H3](principi/01-interazione.md#nn-h3--controllo-e-libertà-dellutente) — Controllo e libertà dell'utente
- [NN-H4](principi/01-interazione.md#nn-h4--coerenza-e-standard) — Coerenza e standard
- [NN-H5](principi/01-interazione.md#nn-h5--prevenzione-degli-errori) — Prevenzione degli errori
- [NN-H6](principi/01-interazione.md#nn-h6--riconoscere-invece-di-ricordare) — Riconoscere invece di ricordare
- [NN-H7](principi/01-interazione.md#nn-h7--flessibilità-ed-efficienza-duso) — Flessibilità ed efficienza d'uso
- [NN-H8](principi/01-interazione.md#nn-h8--design-estetico-e-minimalista) — Design estetico e minimalista
- [NN-H9](principi/01-interazione.md#nn-h9--aiutare-a-riconoscere-diagnosticare-e-correggere-gli-errori) — Aiutare a riconoscere, diagnosticare e correggere gli errori
- [NN-H10](principi/01-interazione.md#nn-h10--aiuto-e-documentazione) — Aiuto e documentazione
- [NN-GRAVITA](principi/01-interazione.md#nn-gravita--scala-di-gravità-dei-problemi-04) — Scala di gravità dei problemi (0–4)
- [UX-TEMPI](principi/01-interazione.md#ux-tempi--limiti-dei-tempi-di-risposta-01-s-1-s-10-s) — Limiti dei tempi di risposta: 0,1 s, 1 s, 10 s
- [UX-DOHERTY](principi/01-interazione.md#ux-doherty--soglia-di-doherty-sotto-i-400-ms) — Soglia di Doherty: sotto i 400 ms
- [PERF-RAIL](principi/01-interazione.md#perf-rail--modello-rail-response-animation-idle-load) — Modello RAIL: Response, Animation, Idle, Load
- [PERF-CWV](principi/01-interazione.md#perf-cwv--core-web-vitals-che-cosa-si-misura-e-come) — Core Web Vitals: che cosa si misura e come
- [PERF-LCP](principi/01-interazione.md#perf-lcp--lcp-con-fcp-e-ttfb) — LCP, con FCP e TTFB
- [PERF-INP](principi/01-interazione.md#perf-inp--inp-reattività-di-ogni-tocco) — INP: reattività di ogni tocco
- [PERF-CLS](principi/01-interazione.md#perf-cls--cls-niente-si-sposta-da-solo) — CLS: niente si sposta da solo
- [UX-OTTIMISTA](principi/01-interazione.md#ux-ottimista--interfaccia-ottimistica-solo-dove-è-sicura) — Interfaccia ottimistica, solo dove è sicura
- [UX-PERCEPITA](principi/01-interazione.md#ux-percepita--prestazioni-percepite) — Prestazioni percepite
- [UX-PROGRESSO](principi/01-interazione.md#ux-progresso--indicatori-di-avanzamento) — Indicatori di avanzamento
- [UX-SCHELETRO](principi/01-interazione.md#ux-scheletro--skeleton-screen-per-pagine-e-regioni) — Skeleton screen per pagine e regioni
- [UX-VUOTO](principi/01-interazione.md#ux-vuoto--stati-vuoti) — Stati vuoti
- [UX-ERRORI](principi/01-interazione.md#ux-errori--messaggi-derrore-linee-guida-nng-2023-e-schemi-ostili) — Messaggi d'errore: linee guida NN/g 2023 e schemi ostili
- [UX-NOTIFICHE](principi/01-interazione.md#ux-notifiche--indicatori-validazioni-e-notifiche-toast) — Indicatori, validazioni e notifiche (toast)
- [UX-CONFERMA](principi/01-interazione.md#ux-conferma--dialoghi-di-conferma-e-quando-è-meglio-annulla) — Dialoghi di conferma, e quando è meglio Annulla
- [UX-SLIP](principi/01-interazione.md#ux-slip--errori-di-distrazione-slip-e-di-valutazione-mistake) — Errori di distrazione (slip) e di valutazione (mistake)
- [UX-MODALE](principi/01-interazione.md#ux-modale--dialoghi-modali-e-non-modali) — Dialoghi modali e non modali
- [UX-DISATTIVATI](principi/01-interazione.md#ux-disattivati--pulsanti-e-controlli-disattivati) — Pulsanti e controlli disattivati
- [UX-SALVA](principi/01-interazione.md#ux-salva--salvare-un-modello-per-tipo-di-pagina-e-il-lavoro-che-sopravvive-alle-interruzioni) — Salvare: un modello per tipo di pagina, e il lavoro che sopravvive alle interruzioni
- [UX-TABELLE](principi/01-interazione.md#ux-tabelle--tabelle-e-liste-di-dati) — Tabelle e liste di dati
- [UX-FILTRI](principi/01-interazione.md#ux-filtri--filtri) — Filtri
- [UX-RICERCA](principi/01-interazione.md#ux-ricerca--ricerca) — Ricerca
- [UX-AZIONI-MULTIPLE](principi/01-interazione.md#ux-azioni-multiple--azioni-su-più-righe) — Azioni su più righe
- [UX-BRICIOLE](principi/01-interazione.md#ux-briciole--briciole-di-pane) — Briciole di pane
- [UX-ICONE](principi/01-interazione.md#ux-icone--icone-con-le-loro-parole) — Icone con le loro parole
- [UX-DISCLOSURE](principi/01-interazione.md#ux-disclosure--divulgazione-progressiva) — Divulgazione progressiva
- [UX-DEFAULT](principi/01-interazione.md#ux-default--valori-predefiniti) — Valori predefiniti
- [UX-RECENTI](principi/01-interazione.md#ux-recenti--riconoscere-recenti-suggerimenti-completamento) — Riconoscere: recenti, suggerimenti, completamento
- [UX-URL](principi/01-interazione.md#ux-url--un-indirizzo-per-ogni-stato-indietro-e-cronologia) — Un indirizzo per ogni stato; Indietro e cronologia

### 2. Percepibile e robusto: WCAG 2.2 e ARIA

- [WCAG-QUADRO](principi/02-wcag-percepibile-e-robusto.md#wcag-quadro--wcag-22-aa-come-metro-in-ogni-variante-della-pagina) — WCAG 2.2 AA come metro, in ogni variante della pagina
- [WCAG-1.1.1](principi/02-wcag-percepibile-e-robusto.md#wcag-111--alternative-testuali-immagini-icone-avatar-grafici) — Alternative testuali: immagini, icone, avatar, grafici
- [WCAG-1.2.1-1.2.5](principi/02-wcag-percepibile-e-robusto.md#wcag-121-125--audio-e-video-quando-servono-trascrizione-sottotitoli-audiodescrizione) — Audio e video: quando servono trascrizione, sottotitoli, audiodescrizione
- [WCAG-1.3.1-TITOLI](principi/02-wcag-percepibile-e-robusto.md#wcag-131-titoli--titoli-veri-uno-che-nomina-la-pagina-gli-altri-in-ordine) — Titoli veri: uno che nomina la pagina, gli altri in ordine
- [WCAG-1.3.1-RELAZIONI](principi/02-wcag-percepibile-e-robusto.md#wcag-131-relazioni--ciò-che-la-grafica-lega-il-codice-lega-etichette-gruppi-obbligatorio-errori) — Ciò che la grafica lega, il codice lega: etichette, gruppi, obbligatorio, errori
- [WCAG-1.3.1-TABELLE](principi/02-wcag-percepibile-e-robusto.md#wcag-131-tabelle--tabelle-e-liste-a-colonne-ogni-cella-con-la-sua-intestazione) — Tabelle e liste a colonne: ogni cella con la sua intestazione
- [WCAG-1.3.2](principi/02-wcag-percepibile-e-robusto.md#wcag-132--lordine-del-codice-è-lordine-di-lettura) — L'ordine del codice è l'ordine di lettura
- [WCAG-1.3.3](principi/02-wcag-percepibile-e-robusto.md#wcag-133--istruzioni-che-non-dipendono-da-forma-posizione-colore-o-suono) — Istruzioni che non dipendono da forma, posizione, colore o suono
- [WCAG-1.3.4](principi/02-wcag-percepibile-e-robusto.md#wcag-134--nessun-blocco-dellorientamento) — Nessun blocco dell'orientamento
- [WCAG-1.3.5](principi/02-wcag-percepibile-e-robusto.md#wcag-135--autocomplete-sui-dati-di-chi-compila) — autocomplete sui dati di chi compila
- [WCAG-1.4.1](principi/02-wcag-percepibile-e-robusto.md#wcag-141--il-colore-non-è-mai-lunico-segno) — Il colore non è mai l'unico segno
- [WCAG-1.4.2](principi/02-wcag-percepibile-e-robusto.md#wcag-142--nessun-suono-automatico-oltre-3-secondi-senza-un-comando-per-fermarlo) — Nessun suono automatico oltre 3 secondi senza un comando per fermarlo
- [WCAG-1.4.3](principi/02-wcag-percepibile-e-robusto.md#wcag-143--testo-leggibile-451-31-se-grande-in-ogni-stato-e-in-entrambi-i-temi) — Testo leggibile: 4,5:1 (3:1 se grande), in ogni stato e in entrambi i temi
- [WCAG-1.4.4](principi/02-wcag-percepibile-e-robusto.md#wcag-144--testo-al-200-senza-perdere-niente) — Testo al 200% senza perdere niente
- [WCAG-1.4.5](principi/02-wcag-percepibile-e-robusto.md#wcag-145--le-parole-si-scrivono-non-si-disegnano) — Le parole si scrivono, non si disegnano
- [WCAG-1.4.10](principi/02-wcag-percepibile-e-robusto.md#wcag-1410--reflow-a-320-px-si-scorre-in-una-sola-direzione) — Reflow a 320 px: si scorre in una sola direzione
- [WCAG-1.4.11](principi/02-wcag-percepibile-e-robusto.md#wcag-1411--controlli-stati-fuoco-icone-e-grafici-a-31) — Controlli, stati, fuoco, icone e grafici a 3:1
- [WCAG-1.4.12](principi/02-wcag-percepibile-e-robusto.md#wcag-1412--spaziatura-del-testo-modificabile-senza-perdite) — Spaziatura del testo modificabile senza perdite
- [WCAG-1.4.13](principi/02-wcag-percepibile-e-robusto.md#wcag-1413--tooltip-e-contenuti-al-passaggio-chiudibili-sorvolabili-persistenti-mai-unici) — Tooltip e contenuti al passaggio: chiudibili, sorvolabili, persistenti, mai unici
- [WCAG-1.4.6-AAA](principi/02-wcag-percepibile-e-robusto.md#wcag-146-aaa--obiettivo-aaa-71-per-il-testo-che-si-legge-a-lungo) — Obiettivo AAA: 7:1 per il testo che si legge a lungo
- [WCAG-1.4.8-AAA](principi/02-wcag-percepibile-e-robusto.md#wcag-148-aaa--obiettivo-aaa-blocchi-di-testo-comodi-da-leggere) — Obiettivo AAA: blocchi di testo comodi da leggere
- [CONTRASTO-APCA](principi/02-wcag-percepibile-e-robusto.md#contrasto-apca--apca-solo-come-informazione-mai-come-prova-di-conformità) — APCA solo come informazione, mai come prova di conformità
- [WCAG-4.1.1](principi/02-wcag-percepibile-e-robusto.md#wcag-411--411-parsing-è-rimosso-che-cosa-resta-da-fare) — 4.1.1 Parsing è rimosso: che cosa resta da fare
- [WCAG-4.1.2-NOME](principi/02-wcag-percepibile-e-robusto.md#wcag-412-nome--ogni-controllo-ha-un-nome-e-un-ruolo-che-il-lettore-di-schermo-dice) — Ogni controllo ha un nome e un ruolo che il lettore di schermo dice
- [WCAG-4.1.2-STATO](principi/02-wcag-percepibile-e-robusto.md#wcag-412-stato--stati-e-valori-esposti-e-aggiornati-niente-comandi-dentro-comandi) — Stati e valori esposti e aggiornati; niente comandi dentro comandi
- [WCAG-4.1.3](principi/02-wcag-percepibile-e-robusto.md#wcag-413--messaggi-di-stato-annunciati-senza-spostare-il-fuoco) — Messaggi di stato annunciati senza spostare il fuoco
- [ARIA-NATIVO](principi/02-wcag-percepibile-e-robusto.md#aria-nativo--prima-lhtml-nativo-un-ruolo-aria-è-una-promessa) — Prima l'HTML nativo: un ruolo ARIA è una promessa
- [ARIA-ACCNAME](principi/02-wcag-percepibile-e-robusto.md#aria-accname--come-nasce-il-nome-accessibile-accname-12) — Come nasce il nome accessibile (accname 1.2)
- [ARIA-LANDMARK](principi/02-wcag-percepibile-e-robusto.md#aria-landmark--punti-di-riferimento-tutto-il-contenuto-in-una-regione-con-un-ruolo-e-un-nome) — Punti di riferimento: tutto il contenuto in una regione con un ruolo e un nome
- [ARIA-LIVE](principi/02-wcag-percepibile-e-robusto.md#aria-live--regioni-live-cortesi-o-urgenti-sempre-presenti-prima-del-messaggio) — Regioni live: cortesi o urgenti, sempre presenti prima del messaggio
- [ARIA-HIDDEN-INERT](principi/02-wcag-percepibile-e-robusto.md#aria-hidden-inert--nascondere-bene-aria-hidden-per-il-doppione-inert-per-ciò-che-è-coperto) — Nascondere bene: aria-hidden per il doppione, inert per ciò che è coperto
- [ARIA-SWITCH](principi/02-wcag-percepibile-e-robusto.md#aria-switch--interruttori-ruolo-switch-stato-acceso-o-spento-nome-che-non-cambia) — Interruttori: ruolo switch, stato acceso o spento, nome che non cambia
- [ARIA-TABS](principi/02-wcag-percepibile-e-robusto.md#aria-tabs--schede-tablist-con-nome-scheda-selezionata-pannello-collegato) — Schede: tablist con nome, scheda selezionata, pannello collegato
- [ARIA-RADIO](principi/02-wcag-percepibile-e-robusto.md#aria-radio--scelte-esclusive-gruppo-con-nome-frecce-stato-selezionato) — Scelte esclusive: gruppo con nome, frecce, stato «selezionato»
- [ARIA-MENU](principi/02-wcag-percepibile-e-robusto.md#aria-menu--menu-solo-per-azioni-aperti-da-un-pulsante-che-dice-se-è-aperto) — Menu: solo per azioni, aperti da un pulsante che dice se è aperto
- [ARIA-DIALOG](principi/02-wcag-percepibile-e-robusto.md#aria-dialog--finestre-un-nome-una-modalità-vera-il-fuoco-dentro-e-il-ritorno) — Finestre: un nome, una modalità vera, il fuoco dentro e il ritorno
- [ARIA-METER](principi/02-wcag-percepibile-e-robusto.md#aria-meter--barre-di-valore-e-di-avanzamento-con-nome-e-valore) — Barre di valore e di avanzamento con nome e valore

### 3. Utilizzabile e comprensibile: WCAG 2.2 e tastiera

- [WCAG-2.1.1](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-211--tutto-si-fa-con-la-tastiera-211-a) — Tutto si fa con la tastiera (2.1.1, A)
- [WCAG-2.1.2](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-212--nessuna-trappola-per-la-tastiera-212-a) — Nessuna trappola per la tastiera (2.1.2, A)
- [WCAG-2.1.4](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-214--scorciatoie-da-un-solo-carattere-214-a) — Scorciatoie da un solo carattere (2.1.4, A)
- [WCAG-2.2.1](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-221--tempi-regolabili-toast-sessioni-codici-posti-tenuti-221-a) — Tempi regolabili: toast, sessioni, codici, posti tenuti (2.2.1, A)
- [WCAG-2.2.2](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-222--pausa-stop-nascondi-per-ciò-che-si-muove-o-si-aggiorna-222-a) — Pausa, stop, nascondi per ciò che si muove o si aggiorna (2.2.2, A)
- [WCAG-2.2.5](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-225--dopo-un-nuovo-accesso-non-si-perde-nulla-225-aaa-obiettivo) — Dopo un nuovo accesso non si perde nulla (2.2.5, AAA, obiettivo)
- [WCAG-2.3.1](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-231--non-più-di-tre-lampeggiamenti-al-secondo-231-a) — Non più di tre lampeggiamenti al secondo (2.3.1, A)
- [WCAG-2.3.3](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-233--le-animazioni-causate-da-un-gesto-si-possono-spegnere-233-aaa-obiettivo) — Le animazioni causate da un gesto si possono spegnere (2.3.3, AAA, obiettivo)
- [WCAG-2.4.1](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-241--saltare-i-blocchi-ripetuti-vai-al-contenuto-e-regioni-241-a) — Saltare i blocchi ripetuti: «Vai al contenuto» e regioni (2.4.1, A)
- [WCAG-2.4.2](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-242--ogni-pagina-ha-un-titolo-che-dice-dove-si-è-242-a) — Ogni pagina ha un titolo che dice dove si è (2.4.2, A)
- [WCAG-2.4.3](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-243--il-focus-segue-un-ordine-che-conserva-il-senso-243-a) — Il focus segue un ordine che conserva il senso (2.4.3, A)
- [WCAG-2.4.4](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-244--lo-scopo-di-ogni-link-si-capisce-dal-testo-o-dal-suo-contesto-244-a) — Lo scopo di ogni link si capisce dal testo o dal suo contesto (2.4.4, A)
- [WCAG-2.4.5](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-245--più-di-un-modo-per-trovare-una-pagina-245-aa) — Più di un modo per trovare una pagina (2.4.5, AA)
- [WCAG-2.4.6](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-246--intestazioni-ed-etichette-dicono-che-cosa-cè-e-che-cosa-scrivere-246-aa) — Intestazioni ed etichette dicono che cosa c'è e che cosa scrivere (2.4.6, AA)
- [WCAG-2.4.7](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-247--il-focus-da-tastiera-si-vede-sempre-247-aa-e-focus-visible) — Il focus da tastiera si vede sempre (2.4.7, AA) e :focus-visible
- [FOCUS-1.4.11](principi/03-wcag-utilizzabile-e-comprensibile.md#focus-1411--lindicatore-di-focus-contrasta-almeno-31-con-ciò-che-ha-accanto-1411-aa) — L'indicatore di focus contrasta almeno 3:1 con ciò che ha accanto (1.4.11, AA)
- [WCAG-2.4.11](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-2411--il-focus-non-resta-nascosto-sotto-barre-pulsanti-fissi-toast-o-tastiera-2411-aa-2412-aaa) — Il focus non resta nascosto sotto barre, pulsanti fissi, toast o tastiera (2.4.11, AA; 2.4.12, AAA)
- [WCAG-2.4.13](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-2413--aspetto-del-focus-area-e-cambio-di-contrasto-2413-aaa-obiettivo) — Aspetto del focus: area e cambio di contrasto (2.4.13, AAA, obiettivo)
- [WCAG-2.5.1](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-251--ogni-gesto-ha-unalternativa-a-un-solo-tocco-251-a) — Ogni gesto ha un'alternativa a un solo tocco (2.5.1, A)
- [WCAG-2.5.2](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-252--un-tocco-si-può-annullare-prima-di-sollevare-il-dito-252-a) — Un tocco si può annullare prima di sollevare il dito (2.5.2, A)
- [WCAG-2.5.3](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-253--il-nome-accessibile-contiene-le-parole-che-si-vedono-253-a) — Il nome accessibile contiene le parole che si vedono (2.5.3, A)
- [WCAG-2.5.4](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-254--nessuna-funzione-solo-scuotendo-o-inclinando-il-telefono-254-a) — Nessuna funzione solo scuotendo o inclinando il telefono (2.5.4, A)
- [WCAG-2.5.7](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-257--ogni-trascinamento-ha-unalternativa-senza-trascinare-257-aa) — Ogni trascinamento ha un'alternativa senza trascinare (2.5.7, AA)
- [WCAG-2.5.8](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-258--bersagli-di-almeno-2424-px-o-ben-distanziati-258-aa) — Bersagli di almeno 24×24 px o ben distanziati (2.5.8, AA)
- [WCAG-2.5.5](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-255--al-tocco-4444-px-la-regola-di-dottorcloud-sopra-il-minimo-255-aaa-obiettivo) — Al tocco 44×44 px: la regola di DottorCloud sopra il minimo (2.5.5, AAA, obiettivo)
- [WCAG-3.1.1](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-311--la-lingua-della-pagina-è-dichiarata-e-giusta-311-a) — La lingua della pagina è dichiarata e giusta (3.1.1, A)
- [WCAG-3.1.2](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-312--le-parti-in-unaltra-lingua-sono-marcate-le-parole-inglesi-rimaste-si-traducono-312-aa) — Le parti in un'altra lingua sono marcate; le parole inglesi rimaste si traducono (3.1.2, AA)
- [WCAG-3.2.1](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-321--il-focus-da-solo-non-cambia-il-contesto-321-a) — Il focus da solo non cambia il contesto (3.2.1, A)
- [WCAG-3.2.2](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-322--cambiare-un-valore-non-porta-altrove-senza-avvisare-322-a) — Cambiare un valore non porta altrove senza avvisare (3.2.2, A)
- [WCAG-3.2.3](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-323--la-navigazione-sta-sempre-nello-stesso-ordine-e-la-voce-attiva-si-vede-323-aa) — La navigazione sta sempre nello stesso ordine e la voce attiva si vede (3.2.3, AA)
- [WCAG-3.2.4](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-324--stessa-funzione-stesso-nome-e-stessa-icona-324-aa) — Stessa funzione, stesso nome e stessa icona (3.2.4, AA)
- [WCAG-3.2.6](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-326--laiuto-sta-sempre-nello-stesso-posto-326-a) — L'aiuto sta sempre nello stesso posto (3.2.6, A)
- [WCAG-3.3.1](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-331--un-errore-dice-in-parole-quale-campo-e-che-cosa-non-va-331-a) — Un errore dice in parole quale campo e che cosa non va (3.3.1, A)
- [WCAG-3.3.2](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-332--ogni-campo-ha-unetichetta-visibile-e-le-istruzioni-che-servono-332-a) — Ogni campo ha un'etichetta visibile e le istruzioni che servono (3.3.2, A)
- [WCAG-3.3.3](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-333--lerrore-dice-come-correggerlo-333-aa) — L'errore dice come correggerlo (3.3.3, AA)
- [WCAG-3.3.4](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-334--fatture-firme-pagamenti-consensi-ed-eliminazioni-annullabili-controllati-o-confermati-334-aa) — Fatture, firme, pagamenti, consensi ed eliminazioni: annullabili, controllati o confermati (3.3.4, AA)
- [WCAG-3.3.7](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-337--non-si-chiede-due-volte-ciò-che-il-sistema-sa-già-337-a) — Non si chiede due volte ciò che il sistema sa già (3.3.7, A)
- [WCAG-3.3.8](principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-338--entrare-senza-test-di-memoria-incolla-gestore-di-password-link-passkey-338-aa) — Entrare senza test di memoria: incolla, gestore di password, link, passkey (3.3.8, AA)
- [APG-TASTIERA](principi/03-wcag-utilizzabile-e-comprensibile.md#apg-tastiera--tab-tra-i-componenti-frecce-dentro-focus-mai-perso-barre-di-strumenti) — Tab tra i componenti, frecce dentro; focus mai perso; barre di strumenti
- [APG-DIALOG](principi/03-wcag-utilizzabile-e-comprensibile.md#apg-dialog--finestre-modali-e-richieste-di-conferma-dialog-e-alertdialog) — Finestre modali e richieste di conferma (dialog e alertdialog)
- [APG-TABS](principi/03-wcag-utilizzabile-e-comprensibile.md#apg-tabs--schede-di-un-record-tablist) — Schede di un record (tablist)
- [APG-RADIO](principi/03-wcag-utilizzabile-e-comprensibile.md#apg-radio--gruppi-di-radio-e-controlli-a-segmenti-mai-per-navigare-tra-pagine) — Gruppi di radio e controlli a segmenti, mai per navigare tra pagine
- [APG-MENU](principi/03-wcag-utilizzabile-e-comprensibile.md#apg-menu--pulsanti--e-menu-di-azioni) — Pulsanti «⋯» e menu di azioni
- [APG-COMBOBOX](principi/03-wcag-utilizzabile-e-comprensibile.md#apg-combobox--cercare-e-scegliere-una-persona-un-servizio-un-professionista-combobox-e-listbox) — Cercare e scegliere una persona, un servizio, un professionista (combobox e listbox)
- [APG-DISCLOSURE](principi/03-wcag-utilizzabile-e-comprensibile.md#apg-disclosure--sezioni-che-si-aprono-e-si-chiudono-disclosure-e-fisarmonica) — Sezioni che si aprono e si chiudono (disclosure e fisarmonica)
- [APG-SWITCH](principi/03-wcag-utilizzabile-e-comprensibile.md#apg-switch--interruttori-che-dicono-che-cosa-accendono) — Interruttori che dicono che cosa accendono
- [APG-TABELLA](principi/03-wcag-utilizzabile-e-comprensibile.md#apg-tabella--liste-come-tabelle-griglie-solo-dove-servono-ordinamento-annunciato) — Liste come tabelle, griglie solo dove servono, ordinamento annunciato

### 4. Aspetto: leggi della UX, gerarchia, tipografia, colore, movimento

- [UX-ESTETICA](principi/04-aspetto.md#ux-estetica--effetto-estetica-usabilità-bello-non-vuol-dire-usabile) — Effetto estetica-usabilità: bello non vuol dire usabile
- [UX-SCELTE](principi/04-aspetto.md#ux-scelte--legge-di-hick-e-sovraccarico-di-scelta-poche-opzioni-per-decisione) — Legge di Hick e sovraccarico di scelta: poche opzioni per decisione
- [UX-MILLER](principi/04-aspetto.md#ux-miller--legge-di-miller-e-chunking-gruppi-significativi-niente-da-ricordare) — Legge di Miller e chunking: gruppi significativi, niente da ricordare
- [UX-BIAS](principi/04-aspetto.md#ux-bias--bias-cognitivi-predefiniti-e-ordine-orientano-le-scelte) — Bias cognitivi: predefiniti e ordine orientano le scelte
- [UX-CARICO](principi/04-aspetto.md#ux-carico--carico-cognitivo-e-memoria-di-lavoro-riconoscere-non-ricordare) — Carico cognitivo e memoria di lavoro: riconoscere, non ricordare
- [UX-FITTS](principi/04-aspetto.md#ux-fitts--legge-di-fitts-bersagli-grandi-vicini-e-i-distruttivi-lontani) — Legge di Fitts: bersagli grandi, vicini, e i distruttivi lontani
- [UX-FLOW](principi/04-aspetto.md#ux-flow--flusso-compiti-ripetuti-senza-attrito) — Flusso: compiti ripetuti senza attrito
- [UX-GRADIENTE](principi/04-aspetto.md#ux-gradiente--gradiente-dellobiettivo-ed-effetto-zeigarnik-avanzamento-visibile) — Gradiente dell'obiettivo ed effetto Zeigarnik: avanzamento visibile
- [UX-JAKOB](principi/04-aspetto.md#ux-jakob--legge-di-jakob-e-modelli-mentali-convenzioni-e-parole-note) — Legge di Jakob e modelli mentali: convenzioni e parole note
- [GS-REGIONE](principi/04-aspetto.md#gs-regione--regione-comune-e-connessione-uniforme-contenitori-e-legami) — Regione comune e connessione uniforme: contenitori e legami
- [GS-PROSSIMITA](principi/04-aspetto.md#gs-prossimita--legge-di-prossimità-la-distanza-dice-che-cosa-va-insieme) — Legge di prossimità: la distanza dice che cosa va insieme
- [GS-PRAGNANZ](principi/04-aspetto.md#gs-pragnanz--legge-di-prägnanz-la-forma-più-semplice) — Legge di Prägnanz: la forma più semplice
- [GS-SOMIGLIANZA](principi/04-aspetto.md#gs-somiglianza--legge-di-somiglianza-stessa-funzione-stesso-aspetto) — Legge di somiglianza: stessa funzione, stesso aspetto
- [UX-OCCAM](principi/04-aspetto.md#ux-occam--rasoio-di-occam-togliere-finché-funziona) — Rasoio di Occam: togliere finché funziona
- [UX-UTENTE-ATTIVO](principi/04-aspetto.md#ux-utente-attivo--paradosso-dellutente-attivo-laiuto-dentro-il-lavoro) — Paradosso dell'utente attivo: l'aiuto dentro il lavoro
- [UX-PARETO](principi/04-aspetto.md#ux-pareto--principio-di-pareto-il-meglio-alle-azioni-di-ogni-giorno) — Principio di Pareto: il meglio alle azioni di ogni giorno
- [UX-PARKINSON](principi/04-aspetto.md#ux-parkinson--legge-di-parkinson-non-far-gonfiare-i-compiti) — Legge di Parkinson: non far gonfiare i compiti
- [UX-PICCO-FINE](principi/04-aspetto.md#ux-picco-fine--regola-del-picco-e-della-fine-momenti-forti-e-chiusure-chiare) — Regola del picco e della fine: momenti forti e chiusure chiare
- [UX-POSTEL](principi/04-aspetto.md#ux-postel--legge-di-postel-accettare-come-scrivono-le-persone-restituire-in-forma-rigorosa) — Legge di Postel: accettare come scrivono le persone, restituire in forma rigorosa
- [UX-ATTENZIONE](principi/04-aspetto.md#ux-attenzione--attenzione-selettiva-ciò-che-conta-non-deve-sembrare-pubblicità) — Attenzione selettiva: ciò che conta non deve sembrare pubblicità
- [UX-POSIZIONE](principi/04-aspetto.md#ux-posizione--effetto-posizione-seriale-lessenziale-apre-la-riga) — Effetto posizione seriale: l'essenziale apre la riga
- [UX-TESLER](principi/04-aspetto.md#ux-tesler--legge-di-tesler-la-complessità-la-assorbe-il-sistema) — Legge di Tesler: la complessità la assorbe il sistema
- [UX-RESTORFF](principi/04-aspetto.md#ux-restorff--effetto-von-restorff-una-sola-cosa-in-risalto-con-più-segnali) — Effetto Von Restorff: una sola cosa in risalto, con più segnali
- [VIS-GERARCHIA](principi/04-aspetto.md#vis-gerarchia--gerarchia-visiva-un-ordine-di-lettura-voluto) — Gerarchia visiva: un ordine di lettura voluto
- [TIPO-RIGA](principi/04-aspetto.md#tipo-riga--lunghezza-della-riga-4575-caratteri-mai-oltre-80) — Lunghezza della riga: 45–75 caratteri, mai oltre 80
- [TIPO-DIMENSIONI](principi/04-aspetto.md#tipo-dimensioni--dimensioni-e-pesi-del-testo) — Dimensioni e pesi del testo
- [TIPO-INTERLINEA](principi/04-aspetto.md#tipo-interlinea--interlinea-e-spaziatura-del-testo-che-reggono-gli-override) — Interlinea e spaziatura del testo che reggono gli override
- [TIPO-FORMA](principi/04-aspetto.md#tipo-forma--allineamento-maiuscole-enfasi-e-cifre) — Allineamento, maiuscole, enfasi e cifre
- [SPAZIO-GRIGLIA](principi/04-aspetto.md#spazio-griglia--spaziatura-su-una-scala-di-4-px) — Spaziatura su una scala di 4 px
- [COL-RUOLI](principi/04-aspetto.md#col-ruoli--il-colore-ha-un-ruolo-e-un-solo-significato) — Il colore ha un ruolo e un solo significato
- [COL-NON-SOLO](principi/04-aspetto.md#col-non-solo--mai-il-colore-da-solo) — Mai il colore da solo
- [COL-TESTO](principi/04-aspetto.md#col-testo--contrasto-del-testo-nei-due-temi) — Contrasto del testo, nei due temi
- [COL-NONTESTO](principi/04-aspetto.md#col-nontesto--contrasto-di-controlli-stati-e-segni-grafici-31) — Contrasto di controlli, stati e segni grafici: 3:1
- [COL-TEMI](principi/04-aspetto.md#col-temi--tema-chiaro-e-scuro-un-token-per-tema-verificato-nei-due) — Tema chiaro e scuro: un token per tema, verificato nei due
- [ICO-ETICHETTE](principi/04-aspetto.md#ico-etichette--icone-con-parole-coerenti-e-con-un-nome) — Icone con parole, coerenti e con un nome
- [MOT-SCOPO](principi/04-aspetto.md#mot-scopo--movimento-con-uno-scopo-breve-e-coerente) — Movimento con uno scopo, breve e coerente
- [MOT-RIDOTTO](principi/04-aspetto.md#mot-ridotto--rispettare-riduci-movimento) — Rispettare «riduci movimento»
- [MOT-AUTOMATICO](principi/04-aspetto.md#mot-automatico--movimento-automatico-lampeggi-aggiornamenti-e-messaggi-a-tempo) — Movimento automatico, lampeggi, aggiornamenti e messaggi a tempo
- [DATI-SEGNI](principi/04-aspetto.md#dati-segni--grafici-serie-distinguibili-senza-colore-e-segni-a-31) — Grafici: serie distinguibili senza colore e segni a 3:1
- [DATI-TESTO](principi/04-aspetto.md#dati-testo--grafici-messaggio-in-parole-valori-leggibili-tabella-alternativa) — Grafici: messaggio in parole, valori leggibili, tabella alternativa
- [DATI-TIPO](principi/04-aspetto.md#dati-tipo--grafici-il-tipo-comune-e-una-sola-enfasi) — Grafici: il tipo comune e una sola enfasi

### 5. Telefono, tablet e tocco

- [MOB-BERSAGLIO](principi/05-telefono-e-tocco.md#mob-bersaglio--bersagli-grandi-quanto-un-dito) — Bersagli grandi quanto un dito
- [MOB-SPAZIO](principi/05-telefono-e-tocco.md#mob-spazio--spazio-tra-i-bersagli-azioni-rischiose-a-distanza) — Spazio tra i bersagli, azioni rischiose a distanza
- [MOB-RIGA-INTERA](principi/05-telefono-e-tocco.md#mob-riga-intera--tutta-la-riga-è-il-bersaglio) — Tutta la riga è il bersaglio
- [MOB-RILASCIO](principi/05-telefono-e-tocco.md#mob-rilascio--si-agisce-al-rilascio-con-un-segno-immediato-di-pressione) — Si agisce al rilascio, con un segno immediato di pressione
- [MOB-NIENTE-HOVER](principi/05-telefono-e-tocco.md#mob-niente-hover--niente-solo-al-passaggio-del-mouse) — Niente solo al passaggio del mouse
- [MOB-CAPACITA](principi/05-telefono-e-tocco.md#mob-capacita--decidere-per-capacità-e-per-spazio-non-per-dispositivo) — Decidere per capacità e per spazio, non per dispositivo
- [MOB-REFLOW](principi/05-telefono-e-tocco.md#mob-reflow--una-sola-direzione-di-scorrimento-fino-a-320-px) — Una sola direzione di scorrimento, fino a 320 px
- [MOB-TESTO-GRANDE](principi/05-telefono-e-tocco.md#mob-testo-grande--il-testo-ingrandito-non-rompe-nulla-lo-zoom-non-si-blocca) — Il testo ingrandito non rompe nulla; lo zoom non si blocca
- [MOB-TESTO-MINIMO](principi/05-telefono-e-tocco.md#mob-testo-minimo--dimensioni-minime-del-testo-sul-telefono) — Dimensioni minime del testo sul telefono
- [MOB-ORIENTAMENTO](principi/05-telefono-e-tocco.md#mob-orientamento--verticale-e-orizzontale-senza-blocchi) — Verticale e orizzontale, senza blocchi
- [MOB-AREE-SICURE](principi/05-telefono-e-tocco.md#mob-aree-sicure--le-aree-sicure-niente-sotto-la-tacca-e-le-zone-dei-gesti) — Le aree sicure: niente sotto la tacca e le zone dei gesti
- [MOB-ALTEZZA-VISIBILE](principi/05-telefono-e-tocco.md#mob-altezza-visibile--altezze-sulla-parte-visibile-non-su-100vh) — Altezze sulla parte visibile, non su 100vh
- [MOB-BARRA-IN-BASSO](principi/05-telefono-e-tocco.md#mob-barra-in-basso--la-barra-in-basso-da-tre-a-cinque-posti-icona-e-parola) — La barra in basso: da tre a cinque posti, icona e parola
- [MOB-INDIETRO](principi/05-telefono-e-tocco.md#mob-indietro--indietro-chiude-prima-ciò-che-sta-sopra) — Indietro chiude prima ciò che sta sopra
- [MOB-RITORNO-VISIBILE](principi/05-telefono-e-tocco.md#mob-ritorno-visibile--una-via-del-ritorno-sempre-visibile-anche-senza-il-browser) — Una via del ritorno sempre visibile, anche senza il browser
- [MOB-SCHEDE](principi/05-telefono-e-tocco.md#mob-schede--le-schede-di-una-scheda-quante-ci-stanno-il-resto-in-altro) — Le schede di una scheda: quante ci stanno, il resto in «Altro»
- [MOB-TESTATE](principi/05-telefono-e-tocco.md#mob-testate--ciò-che-resta-fermo-occupa-poco-e-non-copre) — Ciò che resta fermo occupa poco e non copre
- [MOB-AZIONE-PRINCIPALE](principi/05-telefono-e-tocco.md#mob-azione-principale--il--una-sola-azione-principale-in-basso-a-destra) — Il «+»: una sola azione principale, in basso a destra
- [MOB-POLLICE](principi/05-telefono-e-tocco.md#mob-pollice--ciò-che-si-fa-spesso-dove-arriva-il-pollice) — Ciò che si fa spesso dove arriva il pollice
- [MOB-FOGLI](principi/05-telefono-e-tocco.md#mob-fogli--il-dialogo-è-un-foglio-dal-basso) — Il dialogo è un foglio dal basso
- [MOB-MENU-FOGLIO](principi/05-telefono-e-tocco.md#mob-menu-foglio--menu-e-scelte-un-foglio-di-righe-da-48) — Menu e scelte: un foglio di righe da 48
- [MOB-AVVISI](principi/05-telefono-e-tocco.md#mob-avvisi--avvisi-brevi-sopra-la-barra-mai-lunico-posto) — Avvisi brevi sopra la barra, mai l'unico posto
- [MOB-GESTI-ALTERNATIVA](principi/05-telefono-e-tocco.md#mob-gesti-alternativa--ogni-gesto-ha-unalternativa-a-un-tocco-visibile) — Ogni gesto ha un'alternativa a un tocco, visibile
- [MOB-TRASCINARE-SCORRERE](principi/05-telefono-e-tocco.md#mob-trascinare-scorrere--trascinare-non-ruba-lo-scorrimento-i-bordi-sono-del-sistema) — Trascinare non ruba lo scorrimento; i bordi sono del sistema
- [MOB-TIRA-PER-AGGIORNARE](principi/05-telefono-e-tocco.md#mob-tira-per-aggiornare--tirare-per-aggiornare-la-lista-non-lapp-e-anche-senza-gesto) — Tirare per aggiornare: la lista, non l'app, e anche senza gesto
- [MOB-PRESSIONE-LUNGA](principi/05-telefono-e-tocco.md#mob-pressione-lunga--tenere-premuto-niente-menu-del-browser-sui-comandi-testo-copiabile) — Tenere premuto: niente menu del browser sui comandi, testo copiabile
- [MOB-TASTIERA-GIUSTA](principi/05-telefono-e-tocco.md#mob-tastiera-giusta--ogni-campo-apre-la-sua-tastiera) — Ogni campo apre la sua tastiera
- [MOB-TASTO-INVIO](principi/05-telefono-e-tocco.md#mob-tasto-invio--il-tasto-invio-dice-cosa-fa) — Il tasto Invio dice cosa fa
- [MOB-AUTOCOMPLETAMENTO](principi/05-telefono-e-tocco.md#mob-autocompletamento--il-telefono-compila-ciò-che-sa-solo-dove-i-dati-sono-di-chi-scrive) — Il telefono compila ciò che sa, solo dove i dati sono di chi scrive
- [MOB-MAIUSCOLE-CORREZIONE](principi/05-telefono-e-tocco.md#mob-maiuscole-correzione--maiuscole-e-correttore-secondo-il-dato) — Maiuscole e correttore secondo il dato
- [MOB-CAMPI-16PX](principi/05-telefono-e-tocco.md#mob-campi-16px--campi-a-16-px-niente-zoom-involontario-su-iphone) — Campi a 16 px: niente zoom involontario su iPhone
- [MOB-TASTIERA-APERTA](principi/05-telefono-e-tocco.md#mob-tastiera-aperta--con-la-tastiera-aperta-resta-in-vista-ciò-che-serve) — Con la tastiera aperta resta in vista ciò che serve
- [MOB-UNA-COLONNA](principi/05-telefono-e-tocco.md#mob-una-colonna--sul-telefono-etichetta-sopra-una-colonna-il-valore-va-a-capo) — Sul telefono: etichetta sopra, una colonna, il valore va a capo
- [MOB-LISTE](principi/05-telefono-e-tocco.md#mob-liste--liste-del-telefono-una-riga-per-cosa-lidentità-per-prima) — Liste del telefono: una riga per cosa, l'identità per prima
- [MOB-RICERCA](principi/05-telefono-e-tocco.md#mob-ricerca--ogni-lista-si-trova-scrivendo-e-si-ritrova-comera) — Ogni lista si trova scrivendo, e si ritrova com'era
- [MOB-TABLET](principi/05-telefono-e-tocco.md#mob-tablet--il-tablet-il-computer-toccato-col-dito) — Il tablet: il computer, toccato col dito
- [MOB-APP-INSTALLATA](principi/05-telefono-e-tocco.md#mob-app-installata--dottorcloud-sulla-schermata-home) — DottorCloud sulla schermata Home

### 6. Moduli e inserimento dei dati

- [FORM-NECESSARIO](principi/06-moduli.md#form-necessario--chiedere-solo-ciò-che-serve-sapendo-perché) — Chiedere solo ciò che serve, sapendo perché
- [FORM-UNA-DOMANDA](principi/06-moduli.md#form-una-domanda--una-domanda-alla-volta-nellordine-del-lavoro-reale) — Una domanda alla volta, nell'ordine del lavoro reale
- [FORM-PASSI](principi/06-moduli.md#form-passi--più-passi-dire-dove-si-è-e-tornare-indietro-senza-perdere-nulla) — Più passi: dire dove si è e tornare indietro senza perdere nulla
- [FORM-COLONNA](principi/06-moduli.md#form-colonna--una-colonna-etichette-sopra-i-campi) — Una colonna, etichette sopra i campi
- [FORM-ETICHETTA](principi/06-moduli.md#form-etichetta--ogni-controllo-ha-unetichetta-visibile-legata-nel-codice) — Ogni controllo ha un'etichetta visibile, legata nel codice
- [FORM-SEGNAPOSTO](principi/06-moduli.md#form-segnaposto--il-segnaposto-non-è-unetichetta-né-un-aiuto-né-un-valore) — Il segnaposto non è un'etichetta, né un aiuto, né un valore
- [FORM-AIUTO](principi/06-moduli.md#form-aiuto--laiuto-è-breve-visibile-e-legato-al-campo) — L'aiuto è breve, visibile e legato al campo
- [FORM-OBBLIGATORI](principi/06-moduli.md#form-obbligatori--obbligatori-e-facoltativi-una-convenzione-spiegata-e-leggibile-dalle-tecnologie-assistive) — Obbligatori e facoltativi: una convenzione, spiegata e leggibile dalle tecnologie assistive
- [FORM-LARGHEZZA](principi/06-moduli.md#form-larghezza--il-campo-è-largo-quanto-la-risposta) — Il campo è largo quanto la risposta
- [FORM-CAMPO-VISIBILE](principi/06-moduli.md#form-campo-visibile--un-campo-si-riconosce-come-campo) — Un campo si riconosce come campo
- [FORM-SCELTE](principi/06-moduli.md#form-scelte--il-controllo-giusto-per-ogni-scelta) — Il controllo giusto per ogni scelta
- [FORM-GRUPPI](principi/06-moduli.md#form-gruppi--i-campi-che-vanno-insieme-sono-un-gruppo-con-un-nome) — I campi che vanno insieme sono un gruppo con un nome
- [FORM-PREDEFINITI](principi/06-moduli.md#form-predefiniti--nessuna-risposta-data-per-scontata) — Nessuna risposta data per scontata
- [FORM-CONSENSI](principi/06-moduli.md#form-consensi--un-consenso-si-dà-non-si-trova-già-dato) — Un consenso si dà, non si trova già dato
- [FORM-TASTIERA](principi/06-moduli.md#form-tastiera--la-tastiera-giusta-per-ogni-dato) — La tastiera giusta per ogni dato
- [FORM-AUTOCOMPLETE](principi/06-moduli.md#form-autocomplete--il-browser-compila-i-dati-di-chi-compila-non-quelli-degli-altri) — Il browser compila i dati di chi compila, non quelli degli altri
- [FORM-INCOLLA](principi/06-moduli.md#form-incolla--incollare-e-farsi-aiutare-sempre) — Incollare e farsi aiutare, sempre
- [FORM-NON-RICHIEDERE](principi/06-moduli.md#form-non-richiedere--ciò-che-il-sistema-sa-già-non-si-chiede-di-nuovo) — Ciò che il sistema sa già non si chiede di nuovo
- [FORM-POSTEL](principi/06-moduli.md#form-postel--accettare-i-formati-reali-normalizzare-dopo) — Accettare i formati reali, normalizzare dopo
- [FORM-VALIDA-QUANDO](principi/06-moduli.md#form-valida-quando--validare-al-momento-giusto) — Validare al momento giusto
- [FORM-MESSAGGIO](principi/06-moduli.md#form-messaggio--il-messaggio-derrore-dice-cosa-fare-con-le-parole-delletichetta) — Il messaggio d'errore dice cosa fare, con le parole dell'etichetta
- [FORM-ERRORE-ACCANTO](principi/06-moduli.md#form-errore-accanto--lerrore-sta-accanto-al-campo-legato-al-campo-e-annunciato) — L'errore sta accanto al campo, legato al campo e annunciato
- [FORM-RIEPILOGO-ERRORI](principi/06-moduli.md#form-riepilogo-errori--dopo-un-invio-fallito-tutto-in-cima-niente-perso-il-fuoco-sul-riepilogo) — Dopo un invio fallito: tutto in cima, niente perso, il fuoco sul riepilogo
- [FORM-PULSANTE](principi/06-moduli.md#form-pulsante--il-pulsante-dinvio-è-sempre-attivo-e-dice-cosa-fa) — Il pulsante d'invio è sempre attivo e dice cosa fa
- [FORM-DOPPIO-INVIO](principi/06-moduli.md#form-doppio-invio--un-invio-parte-una-volta-sola) — Un invio parte una volta sola
- [FORM-SALVATAGGIO](principi/06-moduli.md#form-salvataggio--un-modo-di-salvare-per-tipo-di-pagina-e-si-sa-sempre-se-è-salvato) — Un modo di salvare per tipo di pagina, e si sa sempre se è salvato
- [FORM-BOZZE](principi/06-moduli.md#form-bozze--il-lavoro-interrotto-non-si-perde) — Il lavoro interrotto non si perde
- [FORM-IRREVERSIBILE](principi/06-moduli.md#form-irreversibile--prima-di-un-invio-che-non-si-ritira-rivedere-confermare-o-poter-annullare) — Prima di un invio che non si ritira: rivedere, confermare o poter annullare
- [FORM-FUOCO](principi/06-moduli.md#form-fuoco--il-cursore-va-dove-serve-e-non-salta-da-solo) — Il cursore va dove serve e non salta da solo
- [FORM-DATE](principi/06-moduli.md#form-date--date-allitaliana-senza-ambiguità) — Date all'italiana, senza ambiguità
- [FORM-ORE](principi/06-moduli.md#form-ore--orari-a-24-ore-e-sempre-di-un-fuso-detto) — Orari a 24 ore, e sempre di un fuso detto
- [FORM-NUMERI](principi/06-moduli.md#form-numeri--numeri-e-importi-come-li-scrive-un-italiano) — Numeri e importi come li scrive un italiano
- [FORM-TELEFONO](principi/06-moduli.md#form-telefono--un-telefono-in-un-campo-solo-accettato-come-lo-si-scrive) — Un telefono in un campo solo, accettato come lo si scrive
- [FORM-EMAIL](principi/06-moduli.md#form-email--unemail-tastiera-giusta-controllo-leggero-conferma-restituendo-lindirizzo) — Un'email: tastiera giusta, controllo leggero, conferma restituendo l'indirizzo
- [FORM-NOMI](principi/06-moduli.md#form-nomi--nomi-come-li-porta-la-persona) — Nomi come li porta la persona
- [FORM-INDIRIZZI](principi/06-moduli.md#form-indirizzi--indirizzi-italiani-pochi-campi-il-cap-come-testo) — Indirizzi italiani: pochi campi, il CAP come testo
- [FORM-CODICE-FISCALE](principi/06-moduli.md#form-codice-fiscale--il-codice-fiscale-accettato-comè-scritto-controllato-con-il-carattere-di-controllo) — Il codice fiscale: accettato com'è scritto, controllato con il carattere di controllo
- [FORM-PARTITA-IVA](principi/06-moduli.md#form-partita-iva--partita-iva-undici-cifre-con-la-cifra-di-controllo-prefisso-accettato) — Partita IVA: undici cifre con la cifra di controllo, prefisso accettato
- [FORM-IBAN](principi/06-moduli.md#form-iban--iban-incollato-in-maiuscolo-a-gruppi-di-quattro) — IBAN: incollato, in maiuscolo, a gruppi di quattro
- [FORM-CONTEGGIO](principi/06-moduli.md#form-conteggio--limiti-di-lunghezza-dichiarati-contati-mai-tagliati-in-silenzio) — Limiti di lunghezza dichiarati, contati, mai tagliati in silenzio
- [FORM-DOPPIONI](principi/06-moduli.md#form-doppioni--prima-di-creare-cercare-una-persona-non-nasce-due-volte) — Prima di creare, cercare: una persona non nasce due volte

### 7. Parole, lingua e norme

- [LING-CHIARO](principi/07-lingua-e-norme.md#ling-chiaro--italiano-semplice-frasi-attive-e-brevi) — Italiano semplice, frasi attive e brevi
- [LING-LEGGIBILITA](principi/07-lingua-e-norme.md#ling-leggibilita--leggibilità-misurata-e-testi-corti) — Leggibilità misurata e testi corti
- [LING-VOCE](principi/07-lingua-e-norme.md#ling-voce--il-tu-una-voce-sola-il-tono-del-momento) — Il «tu», una voce sola, il tono del momento
- [LING-AZIONI](principi/07-lingua-e-norme.md#ling-azioni--pulsanti-e-link-dicono-che-cosa-succede) — Pulsanti e link dicono che cosa succede
- [LING-ERRORI](principi/07-lingua-e-norme.md#ling-errori--un-errore-dice-che-cosa-perché-e-come-rimediare) — Un errore dice che cosa, perché e come rimediare
- [LING-CONFERME](principi/07-lingua-e-norme.md#ling-conferme--conferme-che-nominano-lazione-e-le-conseguenze) — Conferme che nominano l'azione e le conseguenze
- [LING-ESITI-VUOTI](principi/07-lingua-e-norme.md#ling-esiti-vuoti--successi-e-liste-vuote-che-dicono-che-cosa-succede-ora) — Successi e liste vuote che dicono che cosa succede ora
- [LING-AIUTI](principi/07-lingua-e-norme.md#ling-aiuti--aiuti-segnaposto-e-scelte-specifici) — Aiuti, segnaposto e scelte specifici
- [LING-GLOSSARIO](principi/07-lingua-e-norme.md#ling-glossario--un-termine-per-ogni-concetto-in-tutto-il-prodotto) — Un termine per ogni concetto, in tutto il prodotto
- [LING-SIGLE](principi/07-lingua-e-norme.md#ling-sigle--sigle-sciolte-alla-prima-occorrenza) — Sigle sciolte alla prima occorrenza
- [LING-NORME](principi/07-lingua-e-norme.md#ling-norme--prima-la-regola-in-parole-poi-la-norma) — Prima la regola in parole, poi la norma
- [LING-GERGO](principi/07-lingua-e-norme.md#ling-gergo--niente-gergo-inglese-nomi-di-campo-o-codici) — Niente gergo, inglese, nomi di campo o codici
- [LING-GENERE](principi/07-lingua-e-norme.md#ling-genere--linguaggio-inclusivo-di-genere) — Linguaggio inclusivo di genere
- [LING-ABILISMO](principi/07-lingua-e-norme.md#ling-abilismo--niente-verbi-abilisti-prima-la-persona) — Niente verbi abilisti, prima la persona
- [LING-TITOLI](principi/07-lingua-e-norme.md#ling-titoli--titoli-di-pagina-e-intestazioni-che-dicono-dove-sei) — Titoli di pagina e intestazioni che dicono dove sei
- [LING-NOME-ACCESSIBILE](principi/07-lingua-e-norme.md#ling-nome-accessibile--il-nome-per-il-lettore-di-schermo-in-italiano-e-uguale-a-quello-che-si-vede) — Il nome per il lettore di schermo: in italiano e uguale a quello che si vede
- [TIPO-MAIUSCOLE](principi/07-lingua-e-norme.md#tipo-maiuscole--maiuscola-solo-allinizio-mesi-e-giorni-minuscoli) — Maiuscola solo all'inizio, mesi e giorni minuscoli
- [TIPO-VIRGOLETTE-APOSTROFO](principi/07-lingua-e-norme.md#tipo-virgolette-apostrofo--virgolette-basse-apostrofo-e-puntini-tipografici) — Virgolette basse, apostrofo e puntini tipografici
- [TIPO-DATE](principi/07-lingua-e-norme.md#tipo-date--date-allitaliana-e-mai-ambigue) — Date all'italiana e mai ambigue
- [TIPO-ORE-DURATE](principi/07-lingua-e-norme.md#tipo-ore-durate--ore-a-24-ore-durate-con-le-unità) — Ore a 24 ore, durate con le unità
- [TIPO-NUMERI](principi/07-lingua-e-norme.md#tipo-numeri--numeri-cifre-virgola-decimale-punto-delle-migliaia-una-regola-sola) — Numeri: cifre, virgola decimale, punto delle migliaia, una regola sola
- [TIPO-VALUTA](principi/07-lingua-e-norme.md#tipo-valuta--prezzi-come-li-scrive-chi-legge-6500-) — Prezzi come li scrive chi legge: «65,00 €»
- [TIPO-SPAZI-UNITA](principi/07-lingua-e-norme.md#tipo-spazi-unita--spazi-che-non-si-spezzano-unità-del-sistema-internazionale) — Spazi che non si spezzano, unità del Sistema Internazionale
- [TIPO-RECAPITI](principi/07-lingua-e-norme.md#tipo-recapiti--telefoni-email-e-indirizzi-leggibili-e-cliccabili) — Telefoni, email e indirizzi leggibili e cliccabili
- [I18N-FRASI-INTERE](principi/07-lingua-e-norme.md#i18n-frasi-intere--frasi-intere-mai-pezzi-incollati) — Frasi intere, mai pezzi incollati
- [I18N-PLURALI](principi/07-lingua-e-norme.md#i18n-plurali--plurali-secondo-cldr-una-frase-per-caso) — Plurali secondo CLDR: una frase per caso
- [I18N-LANG](principi/07-lingua-e-norme.md#i18n-lang--la-lingua-dichiarata-della-pagina-e-delle-sue-parti) — La lingua dichiarata: della pagina e delle sue parti
- [I18N-FORMATI](principi/07-lingua-e-norme.md#i18n-formati--formati-dalla-lingua-scelta-dallutente-non-dal-browser) — Formati dalla lingua scelta dall'utente, non dal browser
- [I18N-FUSO](principi/07-lingua-e-norme.md#i18n-fuso--lora-del-centro-e-i-giorni-che-non-si-spostano) — L'ora del centro, e i giorni che non si spostano
- [I18N-RICERCA-ORDINE](principi/07-lingua-e-norme.md#i18n-ricerca-ordine--cercare-e-ordinare-con-le-regole-dellitaliano) — Cercare e ordinare con le regole dell'italiano
- [I18N-ESPANSIONE](principi/07-lingua-e-norme.md#i18n-espansione--spazio-per-litaliano-più-lungo-dellinglese) — Spazio per l'italiano, più lungo dell'inglese
- [I18N-NOMI](principi/07-lingua-e-norme.md#i18n-nomi--i-nomi-delle-persone-come-li-scrivono-loro) — I nomi delle persone come li scrivono loro
- [I18N-CODICI-IN-PAROLE](principi/07-lingua-e-norme.md#i18n-codici-in-parole--si-salva-il-codice-si-mostra-la-parola) — Si salva il codice, si mostra la parola
- [NORM-WCAG22](principi/07-lingua-e-norme.md#norm-wcag22--obiettivo-wcag-22-livello-aa) — Obiettivo WCAG 2.2 livello AA
- [NORM-STANCA](principi/07-lingua-e-norme.md#norm-stanca--legge-stanca-chi-obbliga-e-che-cosa-chiede) — Legge Stanca: chi obbliga e che cosa chiede
- [NORM-EAA](principi/07-lingua-e-norme.md#norm-eaa--european-accessibility-act-quali-servizi-di-chi-lobbligo) — European Accessibility Act: quali servizi, di chi l'obbligo
- [NORM-GDPR-CHIARO](principi/07-lingua-e-norme.md#norm-gdpr-chiaro--informative-e-consensi-in-linguaggio-semplice-e-chiaro) — Informative e consensi in linguaggio semplice e chiaro

### 8. La persona giusta e i suoi dati

- [SAN-IDENTITA-TESTATA](principi/08-persone-e-dati-personali.md#san-identita-testata--il-paziente-sempre-identificato-nello-stesso-posto) — Il paziente sempre identificato, nello stesso posto
- [SAN-DUE-IDENTIFICATIVI](principi/08-persone-e-dati-personali.md#san-due-identificativi--due-identificativi-in-ogni-scelta-e-in-ogni-risultato) — Due identificativi in ogni scelta e in ogni risultato
- [SAN-OMONIMI](principi/08-persone-e-dati-personali.md#san-omonimi--gli-omonimi-si-segnalano-prima-che-diventino-un-doppione-o-uno-scambio) — Gli omonimi si segnalano prima che diventino un doppione o uno scambio
- [SAN-NOME-INTERO](principi/08-persone-e-dati-personali.md#san-nome-intero--il-nome-non-si-taglia-dove-serve-a-riconoscere) — Il nome non si taglia dove serve a riconoscere
- [SAN-CONTESTO-GIUSTO](principi/08-persone-e-dati-personali.md#san-contesto-giusto--si-vede-sempre-per-chi-si-sta-scrivendo) — Si vede sempre per chi si sta scrivendo
- [SAN-STAMPE](principi/08-persone-e-dati-personali.md#san-stampe--ogni-documento-stampato-o-in-pdf-porta-due-identificativi) — Ogni documento stampato o in PDF porta due identificativi
- [SAN-ACCOGLIENZA-VERIFICA](principi/08-persone-e-dati-personali.md#san-accoglienza-verifica--allaccoglienza-lidentità-si-conferma-attivamente) — All'accoglienza l'identità si conferma attivamente
- [SAN-CHI-AGISCE-PER-CHI](principi/08-persone-e-dati-personali.md#san-chi-agisce-per-chi--si-vede-chi-agisce-per-chi-e-chi-è-assistito-ha-la-sua-scheda) — Si vede chi agisce per chi, e chi è assistito ha la sua scheda
- [SAN-BOZZA-MAI-PERSA](principi/08-persone-e-dati-personali.md#san-bozza-mai-persa--il-lavoro-interrotto-non-si-perde) — Il lavoro interrotto non si perde
- [SAN-SESSIONE-CONDIVISA](principi/08-persone-e-dati-personali.md#san-sessione-condivisa--sessioni-adatte-a-un-pc-di-segreteria-condiviso) — Sessioni adatte a un PC di segreteria condiviso
- [PRIV-MINIMO-IN-LISTE-E-COPIE](principi/08-persone-e-dati-personali.md#priv-minimo-in-liste-e-copie--liste-anteprime-e-copie-portano-il-minimo) — Liste, anteprime e copie portano il minimo
- [PRIV-NULLA-NEL-BROWSER](principi/08-persone-e-dati-personali.md#priv-nulla-nel-browser--nulla-di-personale-resta-nel-browser) — Nulla di personale resta nel browser
- [PRIV-ANTEPRIMA-DI-CHI-GUARDA](principi/08-persone-e-dati-personali.md#priv-anteprima-di-chi-guarda--lanteprima-dellarea-mostra-solo-ciò-che-può-leggere-chi-guarda) — L'anteprima dell'area mostra solo ciò che può leggere chi guarda
- [PRIV-CONSENSO-GRANULARE](principi/08-persone-e-dati-personali.md#priv-consenso-granulare--il-consenso-solo-dove-serve-per-finalità-al-momento-giusto-ritirabile-come-si-è-dato) — Il consenso solo dove serve: per finalità, al momento giusto, ritirabile come si è dato
- [PRIV-NIENTE-INGANNI](principi/08-persone-e-dati-personali.md#priv-niente-inganni--scelte-sulla-privacy-senza-trucchi) — Scelte sulla privacy senza trucchi
- [PRIV-PREDEFINITO-PROTETTIVO](principi/08-persone-e-dati-personali.md#priv-predefinito-protettivo--ciò-che-fa-uscire-o-mostrare-dati-parte-spento) — Ciò che fa uscire o mostrare dati parte spento
- [PRIV-MINIMO-NEI-MODULI](principi/08-persone-e-dati-personali.md#priv-minimo-nei-moduli--chiedere-solo-ciò-che-serve-compreso-ciò-che-serve-alla-sicurezza) — Chiedere solo ciò che serve, compreso ciò che serve alla sicurezza
- [PRIV-BANCONE](principi/08-persone-e-dati-personali.md#priv-bancone--lo-schermo-del-bancone-e-il-tablet-li-vedono-anche-i-pazienti) — Lo schermo del bancone e il tablet li vedono anche i pazienti
- [IA-REVISIONE-UMANA](principi/08-persone-e-dati-personali.md#ia-revisione-umana--lassistente-scrive-bozze-la-persona-decide) — L'assistente scrive bozze, la persona decide
- [IA-TRASPARENZA](principi/08-persone-e-dati-personali.md#ia-trasparenza--si-dice-sempre-dove-cè-lintelligenza-artificiale) — Si dice sempre dove c'è l'intelligenza artificiale
- [IA-DATI-MINIMI](principi/08-persone-e-dati-personali.md#ia-dati-minimi--al-modello-va-il-minimo-e-solo-con-il-consenso) — Al modello va il minimo, e solo con il consenso
- [IA-EMERGENZA-E-SALUTE](principi/08-persone-e-dati-personali.md#ia-emergenza-e-salute--unemergenza-va-subito-al-112-una-domanda-di-salute-a-una-persona) — Un'emergenza va subito al 112, una domanda di salute a una persona

### Nel verticale della clinica

- [SAN-ALLERTE-GRADUATE](../verticali/clinica/principi-sanitari.md#san-allerte-graduate--si-interrompe-solo-per-ciò-che-è-grave-e-su-cui-si-può-agire) — Si interrompe solo per ciò che è grave e su cui si può agire
- [SAN-COPIA-CON-PROVENIENZA](../verticali/clinica/principi-sanitari.md#san-copia-con-provenienza--ciò-che-si-copia-dice-da-dove-viene) — Ciò che si copia dice da dove viene
- [SAN-FIRMA-CONSAPEVOLE](../verticali/clinica/principi-sanitari.md#san-firma-consapevole--prima-di-firmare-oscurare-o-emettere-si-vede-chi-e-che-cosa) — Prima di firmare, oscurare o emettere si vede chi e che cosa
- [PRIV-CHI-PUO-LEGGERE](../verticali/clinica/principi-sanitari.md#priv-chi-puo-leggere--i-dati-sanitari-li-vede-solo-chi-li-legge-e-lo-decide-il-server) — I dati sanitari li vede solo chi li legge, e lo decide il server
- [PRIV-LUCCHETTO-E-OSCURATO](../verticali/clinica/principi-sanitari.md#priv-lucchetto-e-oscurato--un-lucchetto-dove-si-può-sapere-nessuna-traccia-di-ciò-che-è-oscurato) — Un lucchetto dove si può sapere, nessuna traccia di ciò che è oscurato
- [PRIV-REGISTRO-ACCESSI](../verticali/clinica/principi-sanitari.md#priv-registro-accessi--ogni-lettura-di-dati-sanitari-lascia-traccia-e-la-traccia-si-può-consultare) — Ogni lettura di dati sanitari lascia traccia, e la traccia si può consultare
- [PRIV-NOTIFICHE-SENZA-SALUTE](../verticali/clinica/principi-sanitari.md#priv-notifiche-senza-salute--nelle-notifiche-il-chi-e-il-dove-mai-il-contenuto-sanitario) — Nelle notifiche il chi e il dove, mai il contenuto sanitario
- [PRIV-CLINICO-AL-SUO-POSTO](../verticali/clinica/principi-sanitari.md#priv-clinico-al-suo-posto--il-dato-clinico-si-scrive-dove-è-protetto) — Il dato clinico si scrive dove è protetto
- [PRIV-STEP-UP](../verticali/clinica/principi-sanitari.md#priv-step-up--prima-di-scaricare-un-dato-sanitario-una-verifica-recente) — Prima di scaricare un dato sanitario, una verifica recente
- [SAN-SCENARI-CRITICI](../verticali/clinica/principi-sanitari.md#san-scenari-critici--si-provano-gli-scenari-critici-e-si-contano-gli-errori-duso) — Si provano gli scenari critici e si contano gli errori d'uso
- [REG-DISPOSITIVO-MEDICO](../verticali/clinica/principi-sanitari.md#reg-dispositivo-medico--prima-di-una-funzione-che-interpreta-i-dati-di-un-paziente-si-valuta-se-è-un-dispositivo-medico) — Prima di una funzione che interpreta i dati di un paziente, si valuta se è un dispositivo medico

## Le fonti

Le 719 fonti citate dai principi, una volta sola, sono in [Le fonti dei principi](principi/fonti.md), divise per chi le pubblica, ciascuna con i principi che la citano. Il punto preciso (il criterio, la sezione, la pagina) sta accanto alla regola che la usa.

| Chi le pubblica | Fonti |
|---|---|
| [W3C: WCAG 2.2](principi/fonti.md#w3c-wcag-22) | 69 |
| [W3C: Understanding WCAG 2.2](principi/fonti.md#w3c-understanding-wcag-22) | 64 |
| [W3C: tecniche e fallimenti WCAG](principi/fonti.md#w3c-tecniche-e-fallimenti-wcag) | 100 |
| [W3C: ARIA, accname e ARIA Authoring Practices](principi/fonti.md#w3c-aria-accname-e-aria-authoring-practices) | 26 |
| [W3C: internazionalizzazione](principi/fonti.md#w3c-internazionalizzazione) | 11 |
| [W3C: altre pagine WAI](principi/fonti.md#w3c-altre-pagine-wai) | 9 |
| [W3C: altri documenti](principi/fonti.md#w3c-altri-documenti) | 26 |
| [WHATWG](principi/fonti.md#whatwg) | 7 |
| [Nielsen Norman Group](principi/fonti.md#nielsen-norman-group) | 65 |
| [Laws of UX (Jon Yablonski)](principi/fonti.md#laws-of-ux-jon-yablonski) | 31 |
| [Apple: Human Interface Guidelines e WebKit](principi/fonti.md#apple-human-interface-guidelines-e-webkit) | 62 |
| [Google: Android, Material Design, web.dev, Chrome](principi/fonti.md#google-android-material-design-webdev-chrome) | 59 |
| [MDN Web Docs (Mozilla)](principi/fonti.md#mdn-web-docs-mozilla) | 42 |
| [Deque: axe-core](principi/fonti.md#deque-axe-core) | 10 |
| [GOV.UK e NHS](principi/fonti.md#govuk-e-nhs) | 28 |
| [Designers Italia e AgID](principi/fonti.md#designers-italia-e-agid) | 26 |
| [Leggi e autorità: Italia e Unione europea](principi/fonti.md#leggi-e-autorità-italia-e-unione-europea) | 14 |
| [Unicode: CLDR e ICU](principi/fonti.md#unicode-cldr-e-icu) | 13 |
| [Sicurezza del paziente e informatica medica](principi/fonti.md#sicurezza-del-paziente-e-informatica-medica) | 18 |
| [Sicurezza e protocolli: NIST, OWASP, IETF](principi/fonti.md#sicurezza-e-protocolli-nist-owasp-ietf) | 13 |
| [Norme tecniche: ISO e IEC](principi/fonti.md#norme-tecniche-iso-e-iec) | 3 |
| [Ricerca](principi/fonti.md#ricerca) | 5 |
| [Altri sistemi di design, librerie e strumenti](principi/fonti.md#altri-sistemi-di-design-librerie-e-strumenti) | 18 |
