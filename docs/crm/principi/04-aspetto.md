# 4. Aspetto: leggi della UX, gerarchia, tipografia, colore, movimento

<!-- Copyright (c) 2026, NPM2 Solutions Srl and contributors -->

Una delle famiglie dei [principi di esperienza e interfaccia](../66-principi-di-esperienza.md) (doc 66): come leggerle, la lista di controllo per una schermata e come sono state verificate le fonti sono lì.

Questa famiglia raccoglie le 30 leggi elencate nella pagina iniziale di Laws of UX (Aesthetic-Usability Effect, Choice Overload, Chunking, Cognitive Bias, Cognitive Load, Doherty Threshold, Fitts's Law, Flow, Goal-Gradient Effect, Hick's Law, Jakob's Law, Law of Common Region, Law of Proximity, Law of Prägnanz, Law of Similarity, Law of Uniform Connectedness, Mental Model, Miller's Law, Occam's Razor, Paradox of the Active User, Pareto Principle, Parkinson's Law, Peak-End Rule, Postel's Law, Selective Attention, Serial Position Effect, Tesler's Law, Von Restorff Effect, Working Memory, Zeigarnik Effect), riunite in 23 principi dove esprimono la stessa idea e ciascuna con la sua ricerca d'origine, e 18 principi di aspetto: gerarchia visiva, tipografia, spaziatura, colore e temi, icone, movimento e grafici. Per DottorCloud contano perché il gestionale si usa in fretta allo sportello, da professionisti con il paziente davanti e da pazienti spesso anziani sul telefono: un bersaglio piccolo, un colore ambiguo, una riga troppo lunga o un'animazione fuori luogo diventano errori su persone, appuntamenti e fatture. Ogni principio dice come si applica con Espresso (tokens.css, espresso.css, espresso-componenti.css, marchio.css, telefono.css) e con i componenti che esistono, come si verifica e quali errori ha trovato davvero lo studio UX di ottobre 2026. Nella verifica del 12/10/2026 ogni fonte è stata riaperta e confrontata con ciò che le si attribuisce. I testi di W3C (WCAG 2.2, Understanding, Techniques, Media Queries 5, il tutorial WAI sulle immagini complesse), di axe-core, MDN, web.dev, Designers Italia e Design Tokens Italia, GOV.UK, Material Components, Carbon e USWDS sono stati letti dai loro sorgenti su GitHub, che i link citano; quelli di Apple dai dati della pagina e quelli di Android dal sito. Le pagine di Laws of UX e di NN/g, gli articoli scientifici e le RFC non si aprivano durante la ricerca e sono stati letti dai risultati di WebSearch limitati al loro dominio: le fonti lo dicono con «via WebSearch». Il budget di ricerca si è esaurito prima di poter riaprire otto pagine di NN/g (gerarchia visiva, colore, tema scuro, usabilità delle icone, durata delle animazioni, scopo delle animazioni, contrasto nei grafici, cruscotti) e la pagina sul tema scuro di Material 2: sono state tolte, con le affermazioni che reggevano solo su di esse. Le affermazioni sul codice valgono per il commit 6552bbe del repository.

La soglia di Doherty, una delle leggi di Laws of UX, sta nella famiglia 1 con i limiti dei tempi di risposta: [UX-DOHERTY](01-interazione.md#ux-doherty--soglia-di-doherty-sotto-i-400-ms) e [UX-TEMPI](01-interazione.md#ux-tempi--limiti-dei-tempi-di-risposta-01-s-1-s-10-s).

## I principi

- [UX-ESTETICA · Effetto estetica-usabilità: bello non vuol dire usabile](#ux-estetica--effetto-estetica-usabilità-bello-non-vuol-dire-usabile)
- [UX-SCELTE · Legge di Hick e sovraccarico di scelta: poche opzioni per decisione](#ux-scelte--legge-di-hick-e-sovraccarico-di-scelta-poche-opzioni-per-decisione)
- [UX-MILLER · Legge di Miller e chunking: gruppi significativi, niente da ricordare](#ux-miller--legge-di-miller-e-chunking-gruppi-significativi-niente-da-ricordare)
- [UX-BIAS · Bias cognitivi: predefiniti e ordine orientano le scelte](#ux-bias--bias-cognitivi-predefiniti-e-ordine-orientano-le-scelte)
- [UX-CARICO · Carico cognitivo e memoria di lavoro: riconoscere, non ricordare](#ux-carico--carico-cognitivo-e-memoria-di-lavoro-riconoscere-non-ricordare)
- [UX-FITTS · Legge di Fitts: bersagli grandi, vicini, e i distruttivi lontani](#ux-fitts--legge-di-fitts-bersagli-grandi-vicini-e-i-distruttivi-lontani)
- [UX-FLOW · Flusso: compiti ripetuti senza attrito](#ux-flow--flusso-compiti-ripetuti-senza-attrito)
- [UX-GRADIENTE · Gradiente dell'obiettivo ed effetto Zeigarnik: avanzamento visibile](#ux-gradiente--gradiente-dellobiettivo-ed-effetto-zeigarnik-avanzamento-visibile)
- [UX-JAKOB · Legge di Jakob e modelli mentali: convenzioni e parole note](#ux-jakob--legge-di-jakob-e-modelli-mentali-convenzioni-e-parole-note)
- [GS-REGIONE · Regione comune e connessione uniforme: contenitori e legami](#gs-regione--regione-comune-e-connessione-uniforme-contenitori-e-legami)
- [GS-PROSSIMITA · Legge di prossimità: la distanza dice che cosa va insieme](#gs-prossimita--legge-di-prossimità-la-distanza-dice-che-cosa-va-insieme)
- [GS-PRAGNANZ · Legge di Prägnanz: la forma più semplice](#gs-pragnanz--legge-di-prägnanz-la-forma-più-semplice)
- [GS-SOMIGLIANZA · Legge di somiglianza: stessa funzione, stesso aspetto](#gs-somiglianza--legge-di-somiglianza-stessa-funzione-stesso-aspetto)
- [UX-OCCAM · Rasoio di Occam: togliere finché funziona](#ux-occam--rasoio-di-occam-togliere-finché-funziona)
- [UX-UTENTE-ATTIVO · Paradosso dell'utente attivo: l'aiuto dentro il lavoro](#ux-utente-attivo--paradosso-dellutente-attivo-laiuto-dentro-il-lavoro)
- [UX-PARETO · Principio di Pareto: il meglio alle azioni di ogni giorno](#ux-pareto--principio-di-pareto-il-meglio-alle-azioni-di-ogni-giorno)
- [UX-PARKINSON · Legge di Parkinson: non far gonfiare i compiti](#ux-parkinson--legge-di-parkinson-non-far-gonfiare-i-compiti)
- [UX-PICCO-FINE · Regola del picco e della fine: momenti forti e chiusure chiare](#ux-picco-fine--regola-del-picco-e-della-fine-momenti-forti-e-chiusure-chiare)
- [UX-POSTEL · Legge di Postel: accettare come scrivono le persone, restituire in forma rigorosa](#ux-postel--legge-di-postel-accettare-come-scrivono-le-persone-restituire-in-forma-rigorosa)
- [UX-ATTENZIONE · Attenzione selettiva: ciò che conta non deve sembrare pubblicità](#ux-attenzione--attenzione-selettiva-ciò-che-conta-non-deve-sembrare-pubblicità)
- [UX-POSIZIONE · Effetto posizione seriale: l'essenziale apre la riga](#ux-posizione--effetto-posizione-seriale-lessenziale-apre-la-riga)
- [UX-TESLER · Legge di Tesler: la complessità la assorbe il sistema](#ux-tesler--legge-di-tesler-la-complessità-la-assorbe-il-sistema)
- [UX-RESTORFF · Effetto Von Restorff: una sola cosa in risalto, con più segnali](#ux-restorff--effetto-von-restorff-una-sola-cosa-in-risalto-con-più-segnali)
- [VIS-GERARCHIA · Gerarchia visiva: un ordine di lettura voluto](#vis-gerarchia--gerarchia-visiva-un-ordine-di-lettura-voluto)
- [TIPO-RIGA · Lunghezza della riga: 45–75 caratteri, mai oltre 80](#tipo-riga--lunghezza-della-riga-4575-caratteri-mai-oltre-80)
- [TIPO-DIMENSIONI · Dimensioni e pesi del testo](#tipo-dimensioni--dimensioni-e-pesi-del-testo)
- [TIPO-INTERLINEA · Interlinea e spaziatura del testo che reggono gli override](#tipo-interlinea--interlinea-e-spaziatura-del-testo-che-reggono-gli-override)
- [TIPO-FORMA · Allineamento, maiuscole, enfasi e cifre](#tipo-forma--allineamento-maiuscole-enfasi-e-cifre)
- [SPAZIO-GRIGLIA · Spaziatura su una scala di 4 px](#spazio-griglia--spaziatura-su-una-scala-di-4-px)
- [COL-RUOLI · Il colore ha un ruolo e un solo significato](#col-ruoli--il-colore-ha-un-ruolo-e-un-solo-significato)
- [COL-NON-SOLO · Mai il colore da solo](#col-non-solo--mai-il-colore-da-solo)
- [COL-TESTO · Contrasto del testo, nei due temi](#col-testo--contrasto-del-testo-nei-due-temi)
- [COL-NONTESTO · Contrasto di controlli, stati e segni grafici: 3:1](#col-nontesto--contrasto-di-controlli-stati-e-segni-grafici-31)
- [COL-TEMI · Tema chiaro e scuro: un token per tema, verificato nei due](#col-temi--tema-chiaro-e-scuro-un-token-per-tema-verificato-nei-due)
- [ICO-ETICHETTE · Icone con parole, coerenti e con un nome](#ico-etichette--icone-con-parole-coerenti-e-con-un-nome)
- [MOT-SCOPO · Movimento con uno scopo, breve e coerente](#mot-scopo--movimento-con-uno-scopo-breve-e-coerente)
- [MOT-RIDOTTO · Rispettare «riduci movimento»](#mot-ridotto--rispettare-riduci-movimento)
- [MOT-AUTOMATICO · Movimento automatico, lampeggi, aggiornamenti e messaggi a tempo](#mot-automatico--movimento-automatico-lampeggi-aggiornamenti-e-messaggi-a-tempo)
- [DATI-SEGNI · Grafici: serie distinguibili senza colore e segni a 3:1](#dati-segni--grafici-serie-distinguibili-senza-colore-e-segni-a-31)
- [DATI-TESTO · Grafici: messaggio in parole, valori leggibili, tabella alternativa](#dati-testo--grafici-messaggio-in-parole-valori-leggibili-tabella-alternativa)
- [DATI-TIPO · Grafici: il tipo comune e una sola enfasi](#dati-tipo--grafici-il-tipo-comune-e-una-sola-enfasi)

### UX-ESTETICA · Effetto estetica-usabilità: bello non vuol dire usabile

**Regola.** Curare l'aspetto con Espresso, ma giudicare ogni schermata dai compiti riusciti, dagli errori e dai tempi, mai dal gradimento: nei test e nelle revisioni si tiene separato «mi piace» da «ci riesco» e si cercano apposta i problemi che una bella interfaccia nasconde.

**Perché.** Laws of UX: le persone tendono a percepire come più facili da usare i design esteticamente gradevoli. L'effetto fu studiato nel 1995 da Masaaki Kurosu e Kaori Kashimura dello Hitachi Design Center: 26 varianti dell'interfaccia di un bancomat, giudicate da 252 partecipanti per facilità d'uso e per aspetto; il giudizio estetico seguiva la facilità d'uso percepita più di quella reale. NN/g (Kate Moran): una risposta emotiva positiva all'aspetto rende le persone tolleranti verso i problemi d'uso minori, non verso quelli gravi, e può nasconderli nei test: in uno studio una partecipante fatica nei compiti ma giudica il sito facile, parlando solo dell'aspetto. Per questo si guarda che cosa fanno le persone, oltre ad ascoltare che cosa dicono.

**In DottorCloud.** In DottorCloud l'aspetto è già curato dal marchio (token di Espresso, coda della nuvola, croce, blocchi pieni): proprio per questo una schermata non è finita perché è bella. Le revisioni usano la rubrica dello studio UX (ogni rilievo con una gravità da 0 a 4 e il principio violato) e i test usano scenari reali per ruolo: segreteria (registrare l'arrivo, prenotare, emettere la fattura, chiudere la cassa), professionista (aprire la scheda giusta, scrivere la visita), direzione (leggere la dashboard), paziente (entrare nell'area, prenotare da /prenota). L'anteprima del design system (brand/dottorcloud/design-system/espresso/anteprima.html) serve a decidere l'aspetto, non a dimostrare l'usabilità.

**Come si verifica.** Test con 3–5 persone per ruolo sugli scenari critici, misurando compiti riusciti, errori (persona sbagliata, dato fiscale sbagliato) e tempo; nel rapporto i giudizi sull'aspetto stanno separati dai problemi d'uso; ogni rilievo con gravità 0–4 e principio, come nello studio UX.

**Errori da evitare.** Schermate ordinate e coerenti con problemi gravi nascosti (studio UX, ottobre 2026): «Nuova fattura» apriva con «Bonifico» già scelto (gravità 3; oggi il metodo resta segnato come non confermato, con tre modi rapidi, in InvoiceDialog.vue); i campi #f1f4f3 senza bordo su bianco, a 1,11:1, puliti ma quasi invisibili; all'ingresso dell'area clienti il pulsante spento «Mandami il codice» identico al campo email (gravità 3); sul telefono «Emetti la fattura» che crea solo una bozza (gravità 3; corretto il 12/10/2026 in «Prepara la fattura»). Mai chiudere una revisione con «è bello».

**Fonti.**

- [Aesthetic-Usability Effect](https://lawsofux.com/aesthetic-usability-effect/) — definizione; origini (Kurosu e Kashimura, Hitachi Design Center, 1995: 26 varianti di un bancomat, 252 partecipanti); takeaways (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [The Aesthetic-Usability Effect](https://www.nngroup.com/articles/aesthetic-usability-effect/) — tolleranza verso i problemi minori e non verso quelli gravi; l'effetto che nasconde i problemi nei test (studio sul sito FitBit); guardare che cosa fanno le persone (via WebSearch) · Nielsen Norman Group (Kate Moran) · consultato il 12/10/2026

### UX-SCELTE · Legge di Hick e sovraccarico di scelta: poche opzioni per decisione

**Regola.** Ogni decisione presenta poche opzioni, ordinate e raggruppate, con la scelta consigliata indicata o spiegata; le opzioni rare stanno dietro una rivelazione progressiva («Altre opzioni»), i compiti complessi si dividono in passi e in ogni vista ci sono al massimo uno o due pulsanti prominenti.

**Perché.** Hick (1952, «On the Rate of Gain of Information», Quarterly Journal of Experimental Psychology, vol. 4, pp. 11–26): in un atto percettivo-motorio l'informazione si acquisisce a un ritmo in media costante, dell'ordine di cinque bit al secondo, in esperimenti con fino a dieci alternative. Hyman (1953, Journal of Experimental Psychology, vol. 45, pp. 188–196) replicò il risultato e variò anche la frequenza relativa degli stimoli. Laws of UX riassume la legge di Hick-Hyman: il tempo per decidere cresce con il numero e la complessità delle scelte, RT = a + b·log2(n). Proctor e Schneider (2018) la indicano come una delle poche leggi largamente riconosciute in psicologia e ne discutono i limiti (compatibilità tra stimolo e risposta, pratica, insiemi molto grandi). Il sovraccarico di scelta («overchoice») fu introdotto da Alvin Toffler in «Future Shock» (1970), secondo Laws of UX, che consiglia confronti affiancati, priorità a ciò che serve in quel momento e ricerca o filtri per restringere le scelte. NN/g: più scelte richiedono più sforzo per informarsi e decidere bene, e possono portare affaticamento, insoddisfazione e abbandono; davanti a un distributore di bibite con oltre 100 gusti il tempo sul compito crebbe di oltre il 500% (un'osservazione informale dell'autore). Apple: uno o due pulsanti prominenti per vista, perché troppi aumentano il carico cognitivo; la rivelazione progressiva rende i layout più semplici, mentre troppi contenuti e troppe scelte rendono più difficile trovare le informazioni. Cautela: l'evidenza sul sovraccarico è mista. Dean, Ravindran e Stoye (arXiv 2212.03931) ricordano che una meta-analisi (Scheibehenne e colleghi, 2010) trova un effetto medio nullo, un'altra (Chernev e colleghi, 2015) lo trova dipendente dal contesto, e sostengono che i test fatti finora sono poco potenti: l'obiettivo è ridurre lo sforzo di decidere, non fissare un numero.

**Soglie ed eccezioni.** Apple: 1–2 pulsanti prominenti per vista. Nessun numero massimo universale di opzioni: Laws of UX sconsiglia di usare il «7» per giustificare limiti.

**In DottorCloud.** Il menu è un dato (MENU in frontend/src/utils/menu.js): prima il gruppo della giornata, poi il marketing; sul telefono `barraDelTelefono()` dà quattro posti (Agenda, Persone, Conversazioni e Fatture per primi) e il resto va in «Altro» (pages/Altro.vue); le pagine che vivono insieme stanno in `SORELLE` invece di diventare voci. Le impostazioni sono gruppi, voci e schede (utils/impostazioni.js). Nel pannello del nuovo appuntamento (AppointmentPanel.vue) le opzioni rare stanno sotto «Altre opzioni»; /prenota propone e spiega «Qualsiasi sede — Il primo orario libero in tutte le sedi». Un solo pulsante pieno per vista (la variante solid, che marchio.css colora con --brand-action); le altre azioni subtle, outline o nel menu «⋯».

**Come si verifica.** Per ogni schermata contare i pulsanti pieni (la variante solid di frappe-ui porta la classe bg-surface-gray-10, che marchio.css ricolora) e le opzioni di ogni scelta; verificare che ogni scelta abbia un predefinito sensato o una raccomandazione spiegata; nei test misurare il tempo di scelta e le scelte annullate.

**Errori da evitare.** (studio UX, ottobre 2026) Tre pulsanti pieni verdi in competizione nella scheda persona («Chiama», l'azione della scheda, «Continua» dei primi passi); «Crea una trattativa» che parte da dieci campi d'azienda prima della persona (gravità 3); la firma email con la barra di un editor di documenti, 20 comandi; il kanban delle trattative che mescola tutte le pipeline e fa scegliere la pipeline in due posti; l'interruttore generale della fatturazione in mezzo alle opzioni minori; due pulsanti per la stessa azione nella pagina vuota degli script.

**Vedi anche.** [UX-DISCLOSURE](01-interazione.md#ux-disclosure--divulgazione-progressiva)

**Fonti.**

- [Hick's Law](https://lawsofux.com/hicks-law/) — definizione; formula RT = a + b log2(n); origini (William Edmund Hick e Ray Hyman, 1952) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [Choice Overload](https://lawsofux.com/choice-overload/) — definizione; origini (Alvin Toffler, «Future Shock», 1970); takeaways (confronti affiancati, priorità, ricerca e filtri) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [On the Rate of Gain of Information](https://journals.sagepub.com/doi/10.1080/17470215208416600) — abstract: ritmo costante, dell'ordine di cinque bit al secondo; esperimenti con fino a dieci alternative; vol. 4, pp. 11–26 (via WebSearch) · Quarterly Journal of Experimental Psychology (SAGE), W. E. Hick · 1952
- [Stimulus information as a determinant of reaction time](https://pubmed.ncbi.nlm.nih.gov/13052851/) — scheda PubMed: Journal of Experimental Psychology, vol. 45, n. 3, pp. 188–196 (via WebSearch) · Journal of Experimental Psychology (APA), R. Hyman · 1953
- [Hick's law for choice reaction time: A review](https://journals.sagepub.com/doi/abs/10.1080/17470218.2017.1322622) — abstract: «one of the few widely acknowledged laws in psychology»; limiti discussi (via WebSearch) · Quarterly Journal of Experimental Psychology (SAGE), R. W. Proctor e D. W. Schneider · 2018
- [Simplicity Wins over Abundance of Choice](https://www.nngroup.com/articles/simplicity-vs-choice/) — sommario (sforzo per decidere); affaticamento, insoddisfazione e abbandono; il distributore con oltre 100 gusti e il tempo sul compito oltre il +500% (via WebSearch) · Nielsen Norman Group · 2015
- [Buttons (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/buttons#Style) — «Style»: «Keep the number of prominent buttons to one or two per view» (testo letto dai dati JSON della pagina) · Apple · aggiornata il 16/12/2025, consultata il 12/10/2026
- [Layout (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/layout#Visual-hierarchy) — «Visual hierarchy»: «Use progressive disclosure to make layouts cleaner and easier to interact with» (dati JSON della pagina) · Apple · aggiornata il 9/9/2026, consultata il 12/10/2026
- [A Better Test of Choice Overload](https://arxiv.org/abs/2212.03931) — introduzione: Scheibehenne e colleghi (2010) effetto medio nullo; Chernev e colleghi (2015) dipende dal contesto; test esistenti poco potenti (via WebSearch) · arXiv, M. Dean, D. Ravindran e J. Stoye · 2022

### UX-MILLER · Legge di Miller e chunking: gruppi significativi, niente da ricordare

**Regola.** Codici e numeri lunghi si mostrano a gruppi significativi (telefono, IBAN, codice fiscale, importi con il separatore delle migliaia), gli elenchi lunghi si dividono in sezioni con un titolo e nessuna informazione va ricordata da uno schermo all'altro; il «7±2» non è un limite per menu o schede.

**Perché.** Miller (1956, «The Magical Number Seven, Plus or Minus Two») stimò in circa sette elementi lo span della memoria immediata; Laws of UX ricorda che il suo interesse vero era il chunking, parola che viene da quell'articolo: scomporre un insieme di informazioni e raggrupparlo in unità significative, che si scorrono più in fretta. Laws of UX: non usare il «numero magico» per giustificare limiti inutili, organizzare i contenuti in piccoli gruppi, ricordare che la capacità della memoria a breve termine varia da persona a persona. Nell'articolo «The Psychology of Design» (Laws of UX, 2018) il formato dei numeri di telefono è l'esempio più semplice di chunking: senza gruppi un numero è più difficile da leggere e da ricordare. Cowan (2010, «The Magical Mystery Four») riassume le stime successive: un magazzino centrale limitato a 3–5 elementi significativi nei giovani adulti. Designers Italia (Linguaggio): i numeri di telefono si scrivono con il prefisso internazionale e le cifre raggruppate da spazi; il punto separa le migliaia da 10 mila in su.

**Soglie ed eccezioni.** Circa 7 elementi (Miller 1956); 3–5 elementi significativi (Cowan 2010). I gruppi italiani di `leggibile()`: cellulare 3-3-4 o 3-3-3 («+39 333 123 4567»), fissi di Milano e Roma dopo il prefisso («+39 02 1234 5678»).

**In DottorCloud.** `leggibile()` in frontend/src/utils/telefono.js scrive i numeri a gruppi nelle liste, nel kanban e nelle conversazioni (una correzione sistemica dello studio) e lascia l'E.164 nei dati; importi all'italiana («10.359 €»); sul telefono le cose da fare sono raggruppate per scadenza (scadute, oggi, domani, «Più avanti», senza data: `GRUPPI_DI_COSE` in utils/sulTelefono.js) e le notifiche per giorno (utils/notifiche.js); codice fiscale e IBAN vanno scritti a gruppi in lettura e copiati senza spazi. La testata della persona (PersonHeader.vue) evita di dover ricordare chi si sta guardando.

**Come si verifica.** Test unitari di `leggibile()` (frontend/tests/unit/telefono.test.js); ricerca nelle schermate di sequenze di oltre 8 cifre senza separatori; prova di dettatura: leggere a voce un numero dallo schermo a un collega.

**Errori da evitare.** (studio UX, ottobre 2026) Numeri «+393895552045» nelle liste prima della correzione; la durata della chiamata «3:29» senza unità accanto all'ora «11:35»; nei numeri grandi in grassetto la virgola di «87,3%» quasi uguale al punto di «20.294 €»; nei turni del team sul telefono la prima colonna non resta ferma e, scorrendo di lato, non si sa più di chi è la riga.

**Vedi anche.** [GS-PROSSIMITA](#gs-prossimita--legge-di-prossimità-la-distanza-dice-che-cosa-va-insieme)

**Fonti.**

- [Miller's Law](https://lawsofux.com/millers-law/) — takeaways (non usare il «numero magico» per limiti inutili; piccoli gruppi; capacità variabile); origini (Miller, 1956) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [Chunking](https://lawsofux.com/chunking/) — definizione; takeaways (gruppi distinti con una gerarchia chiara) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [The Psychology of Design](https://lawsofux.com/articles/2018/the-psychology-of-design/) — sezione sugli esempi della legge di Miller: il formato dei numeri di telefono come esempio di chunking (via WebSearch) · Laws of UX (Jon Yablonski) · 2018
- [The Magical Mystery Four: How is Working Memory Capacity Limited, and Why?](https://journals.sagepub.com/doi/abs/10.1177/0963721409359277) — abstract: magazzino centrale limitato a 3–5 elementi significativi nei giovani adulti; vol. 19, n. 1, pp. 51–57 (via WebSearch) · Current Directions in Psychological Science (SAGE), N. Cowan · 2010
- [Linguaggio (Design system, Fondamenti)](https://designers.italia.it/design-system/fondamenti/linguaggio/) — «Formatta il testo in modo coerente e accessibile» → «Numeri» (punto delle migliaia da 10 mila) e «Numeri di telefono» (prefisso internazionale, cifre a gruppi); pubblicata su designers.italia.it/design-system/fondamenti/linguaggio/ · Designers Italia (repository italia/designers.italia.it) · consultato il 12/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/linguaggio.yaml))

### UX-BIAS · Bias cognitivi: predefiniti e ordine orientano le scelte

**Regola.** Ogni valore predefinito è vero per tutti o manca: niente dati plausibili ma inventati, nessuna opzione rischiosa preselezionata né resa la più evidente; l'ordine delle opzioni e le parole di una conferma descrivono le conseguenze in modo neutro, senza spingere.

**Perché.** Laws of UX: un bias cognitivo è un errore sistematico di pensiero o di giudizio che influenza come percepiamo il mondo e come decidiamo; secondo Laws of UX Amos Tversky e Daniel Kahneman introdussero la nozione nel 1972, spiegando le differenze di giudizio con le euristiche, scorciatoie mentali che fanno risparmiare sforzo ma possono introdurre errori gravi e sistematici (per esempio il bias di conferma). Apple (Buttons, «Role»): non dare il ruolo principale a un pulsante distruttivo, nemmeno se è la scelta più probabile, perché per la sua evidenza le persone a volte lo scelgono senza leggerlo. In un modulo lasciare il valore già presente è la scorciatoia più comune: se il valore è falso, diventa un dato falso.

**In DottorCloud.** I nuovi record partono dai predefiniti del DocType (DocFields): per ogni modulo va verificato che siano veri per un centro medico. Nella fattura (InvoiceDialog.vue) il metodo predefinito (MP05, bonifico) resta segnato come non ancora confermato finché non si tocca uno dei tre modi rapidi (contanti, carta o app, bonifico), perché la chiusura di cassa conta su quel dato. Un valore sconosciuto resta vuoto (una trattativa senza importo non vale «0,00 €»); l'orario proposto rispetta gli orari del centro; le conferme dicono che cosa succede.

**Come si verifica.** Tabella campo → predefinito → «è vero per ogni centro e per ogni persona?»; nei dati reali misurare quante volte un predefinito resta invariato (per esempio i metodi di pagamento confrontati con la cassa); nei test osservare se l'utente nota e cambia il predefinito.

**Errori da evitare.** (studio UX, ottobre 2026) «Nuova fattura» con «Bonifico» (MP05, «Tracciabile») già scelto: il dato arriva al Sistema TS e la chiusura di cassa non torna (gravità 3); «1-10» dipendenti e «0,00 €» di ricavi già compilati nella nuova persona e nella nuova trattativa; l'orario proposto che cade quando il centro è chiuso; «DottorCloud» come responsabile predefinito della nuova trattativa, letto come se il lavoro fosse del programma; una trattativa senza importo mostrata come «0,00 €» (corretto).

**Vedi anche.** [UX-DEFAULT](01-interazione.md#ux-default--valori-predefiniti), [PRIV-NIENTE-INGANNI](08-persone-e-dati-personali.md#priv-niente-inganni--scelte-sulla-privacy-senza-trucchi)

**Fonti.**

- [Cognitive Bias](https://lawsofux.com/cognitive-bias/) — definizione; origini (Tversky e Kahneman, 1972: euristiche ed errori sistematici; bias di conferma) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [Buttons (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/buttons#Role) — «Role»: «Don't assign the primary role to a button that performs a destructive action, even if that action is the most likely choice» (dati JSON della pagina) · Apple · aggiornata il 16/12/2025, consultata il 12/10/2026

### UX-CARICO · Carico cognitivo e memoria di lavoro: riconoscere, non ricordare

**Regola.** Ogni schermata mostra ciò che serve alla decisione presente — chi è la persona, che cosa è già stato inserito, quali sono le opzioni — e toglie ciò che consuma attenzione senza servire al compito; ciò che è già stato detto nello stesso processo si propone o si precompila, non si chiede di nuovo.

**Perché.** Laws of UX (Cognitive Load): è la quantità di risorse mentali necessarie per capire e usare un'interfaccia; quando l'informazione supera lo spazio disponibile i compiti diventano più difficili, si perdono dettagli e ci si sente sopraffatti; il carico intrinseco è lo sforzo per tenere a mente ciò che serve all'obiettivo, quello estraneo consuma risorse senza aiutare a capire. Laws of UX (Working Memory): la memoria di lavoro tiene 4–7 chunk alla volta, che svaniscono dopo 20–30 secondi; riconosciamo ciò che abbiamo già visto meglio di quanto ricordiamo, e conviene portare le informazioni critiche da una schermata all'altra. NN/g: riconoscere è più facile che ricordare (euristica 6), quindi elementi, azioni e opzioni restano visibili e nessuno deve ricordare informazioni da una parte all'altra dell'interfaccia; per ridurre il carico si evita il disordine visivo, ci si appoggia a modelli mentali noti e si scaricano i compiti sul sistema. WCAG 3.3.7 (A): l'informazione già fornita nello stesso processo è precompilata o selezionabile.

**Soglie ed eccezioni.** 4–7 chunk che svaniscono in 20–30 s (Laws of UX). WCAG 3.3.7, livello A; eccezioni: reinserimento essenziale, sicurezza del contenuto, informazione non più valida.

**In DottorCloud.** La testata della persona (PersonHeader.vue) dice chi è: nome, rapporto con il centro («Paziente dal…»), età e data di nascita a chi legge i dati fiscali (`persone.dati_fiscali`), l'ultima visita; le righe dell'Accoglienza (pages/Today.vue) portano ora, servizio, professionista e persona; la fattura nasce dall'appuntamento (`_fattura_da_appuntamento` in crm/invoicing/api.py) senza ricopiare cliente e servizio; le etichette restano visibili sopra i campi, mai il solo segnaposto; `DescrizioneRipiegata` per le spiegazioni lunghe; `aRichiesta()` per ciò che si apre di rado.

**Come si verifica.** Per ogni schermata chiedersi «che cosa deve ricordare l'utente da un'altra pagina?» (risposta attesa: niente); prova con interruzione (lasciare il compito per 30 s e riprenderlo); axe `label`; verifica manuale di WCAG 3.3.7 nei percorsi appuntamento → fattura e prenotazione → dati.

**Errori da evitare.** (studio UX, ottobre 2026) «Ancora senza esito» con il solo nome, senza ora, servizio né professionista; le note che non dicono di quale persona parlano (gravità 3); i campi del nuovo appuntamento con solo icona e segnaposto (oggi «Inizio» e «Fine» hanno l'etichetta, persona, servizio e professionista ancora no); paragrafi introduttivi sempre aperti in Moduli e Piani; sul telefono un riquadro di divieti alto circa 206 px che spinge il piano della paziente in fondo allo schermo.

**Vedi anche.** [NN-H6](01-interazione.md#nn-h6--riconoscere-invece-di-ricordare)

**Fonti.**

- [Cognitive Load](https://lawsofux.com/cognitive-load/) — definizione; takeaways (sovraccarico; carico intrinseco ed estraneo) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [Working Memory](https://lawsofux.com/working-memory/) — definizione (4–7 chunk, 20–30 secondi); takeaways (riconoscere invece di ricordare; portare le informazioni critiche da una schermata all'altra) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [Memory Recognition and Recall in User Interfaces](https://www.nngroup.com/articles/recognition-and-recall/) — riconoscere contro ricordare; euristica 6 «Recognition Rather than Recall» (via WebSearch) · Nielsen Norman Group · consultato il 12/10/2026
- [Minimize Cognitive Load to Maximize Usability](https://www.nngroup.com/articles/minimize-cognitive-load/) — carico intrinseco ed estraneo; i tre consigli: evitare il disordine visivo, appoggiarsi ai modelli mentali, scaricare i compiti (via WebSearch) · Nielsen Norman Group · consultato il 12/10/2026
- [WCAG 2.2 — Success Criterion 3.3.7 Redundant Entry](https://www.w3.org/TR/WCAG22/#redundant-entry) — testo del criterio, livello A, con le eccezioni (numero ricavato da guidelines/index.html; pubblicato su www.w3.org/TR/WCAG22/#redundant-entry) · W3C, Accessibility Guidelines Working Group (repository w3c/wcag) · WCAG 2.2, ultima pubblicazione 12/12/2024; sorgente consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/22/redundant-entry.html))

### UX-FITTS · Legge di Fitts: bersagli grandi, vicini, e i distruttivi lontani

**Regola.** Le azioni frequenti sono grandi e vicine al punto in cui si trova già la mano (pollice, cursore, riga); ogni bersaglio rispetta le misure minime, con uno spazio che eviti il tocco sbagliato; le azioni distruttive o rare stanno lontane da quelle frequenti e mai sotto il punto in cui si tocca di solito.

**Perché.** Fitts (1954, Journal of Experimental Psychology, vol. 47, pp. 381–391): il tempo per raggiungere un bersaglio dipende dalla distanza e dalla dimensione. NN/g: T = a + b·log2(2D/W), dove W è la dimensione del bersaglio lungo il movimento (per i bersagli rettangolari si usa la minore delle due) e a e b dipendono dal dispositivo (mouse, dito). Laws of UX: per il compromesso tra velocità e precisione, movimenti rapidi e bersagli piccoli aumentano gli errori; i bersagli devono essere grandi abbastanza, ben distanziati e in zone facili da raggiungere. NN/g (bersagli touch, sulla base di uno studio di Parhi, Karlson e Bederson): almeno 1 cm × 1 cm di misura fisica, con spazio dagli altri bersagli, e di più per le azioni principali o per le app usate in movimento.

**Soglie ed eccezioni.** WCAG 2.5.8 (AA): almeno 24×24 CSS px, oppure, per un bersaglio più piccolo, un cerchio di 24 px centrato sul bersaglio che non interseca altri bersagli né i loro cerchi; eccezioni: un controllo equivalente nella pagina, in linea nel testo, deciso dallo user agent, essenziale o richiesto per legge. WCAG 2.5.5 (AAA): 44×44 CSS px. Apple: iOS e iPadOS 44×44 pt (minimo 28×28), macOS 28×28 pt (minimo 20×20); circa 12 pt di spazio attorno ai controlli con bordo, 24 pt senza. Android: almeno 48 dp. NN/g: almeno 1 cm × 1 cm. Regola DottorCloud (telefono.css): 44 px con pointer coarse e per le azioni dei fogli, 48 px per le righe dei fogli.

**In DottorCloud.** frontend/src/telefono.css: `.touch-target` aggiunge un anello invisibile fino a 44 px; `icone-a-dito` e `strumenti-compositore` portano le icone affiancate a 40 px; i fogli dal basso hanno righe da 48 px e azioni alte 44 px. `PulsanteAggiungi` (56 px, in basso a destra, nella zona del pollice) richiede spazio libero in fondo alle liste; MeseAgenda.vue dà agli appuntamenti del mese almeno 24 px (`min-h-6`, cioè 1,5 rem) e `quantiNelGiorno()` in utils/agenda.js decide quanti ne stanno nell'altezza del giorno, calcolata in rem, quindi anche con il testo del browser ingrandito; le azioni distruttive vanno in un gruppo separato, con una conferma o un Annulla.

**Come si verifica.** axe `target-size` (regola WCAG 2.2 disattivata di default: va accesa con il tag wcag22aa); in Playwright misurare i riquadri dei controlli a 360 px con pointer coarse; prova a una mano su un telefono vero; in revisione: che cosa c'è subito sopra e sotto ogni azione distruttiva?

**Errori da evitare.** (studio UX, ottobre 2026) «Togli i dati di prova», in rosso, 32 px sopra «Impostazioni» nella barra laterale (una conferma c'è; in AppSidebar.vue corretto il 12/10/2026: in testa al gruppo in basso, separato da una linea); «Elimina il listino» attaccato a «Nuova regola»; il cestino di ambulatori e link tracciati che eliminava con un tocco (gravità 3, corretto con una conferma); il «+» da 56 px che copriva «Chiama» ed «Emetti la fattura» delle righe; voci del mese alte 18–20 px (92 bersagli in una schermata, corretto a 24 px); pulsanti a icona da 34×40 px; «⋯», «↗» e «›» attaccati, con i centri a circa 30 px; caselle di selezione da 14 px dentro righe cliccabili (292 bersagli su 10 schermate, ancora da fare); sul telefono «Nuovo» dell'agenda nell'angolo in alto a destra, il più lontano dal pollice.

**Vedi anche.** [MOB-SPAZIO](05-telefono-e-tocco.md#mob-spazio--spazio-tra-i-bersagli-azioni-rischiose-a-distanza), [WCAG-2.5.8](03-wcag-utilizzabile-e-comprensibile.md#wcag-258--bersagli-di-almeno-2424-px-o-ben-distanziati-258-aa)

**Fonti.**

- [Fitts's Law](https://lawsofux.com/fittss-law/) — definizione; takeaways (bersagli grandi, ben distanziati, facili da raggiungere); origini (Paul Fitts, 1954; compromesso tra velocità e precisione) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [Fitts's Law and Its Applications in UX](https://www.nngroup.com/articles/fitts-law/) — formula T = a + b log2(2D/W); W lungo il movimento, la minore delle dimensioni per i rettangoli; a e b dipendono dal dispositivo (via WebSearch) · Nielsen Norman Group · consultato il 12/10/2026
- [Touch Targets on Touchscreens](https://www.nngroup.com/articles/touch-target-size/) — almeno 1 cm × 1 cm di misura fisica (studio di Parhi, Karlson e Bederson); spazio dagli altri bersagli; bersagli più grandi per le azioni principali (via WebSearch) · Nielsen Norman Group · consultato il 12/10/2026
- [The information capacity of the human motor system in controlling the amplitude of movement](https://pubmed.ncbi.nlm.nih.gov/13174710/) — scheda PubMed: Journal of Experimental Psychology, vol. 47, n. 6, pp. 381–391 (via WebSearch) · Journal of Experimental Psychology (APA), P. M. Fitts · 1954
- [WCAG 2.2 — Success Criterion 2.5.8 Target Size (Minimum)](https://www.w3.org/TR/WCAG22/#target-size-minimum) — testo del criterio, livello AA, con le eccezioni Spacing, Equivalent, Inline, User Agent Control ed Essential (pubblicato su www.w3.org/TR/WCAG22/#target-size-minimum) · W3C, Accessibility Guidelines Working Group (repository w3c/wcag) · WCAG 2.2, ultima pubblicazione 12/12/2024; sorgente consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/22/target-size-minimum.html))
- [WCAG 2.2 — Success Criterion 2.5.5 Target Size (Enhanced)](https://www.w3.org/TR/WCAG22/#target-size-enhanced) — testo del criterio, livello AAA: 44×44 CSS px, con le eccezioni (pubblicato su www.w3.org/TR/WCAG22/#target-size-enhanced) · W3C, Accessibility Guidelines Working Group (repository w3c/wcag) · WCAG 2.2, ultima pubblicazione 12/12/2024; sorgente consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/21/target-size-enhanced.html))
- [Accessibility (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/accessibility#Mobility) — «Mobility»: tabella «Default control size / Minimum control size»; circa 12 pt di spazio con bordo e 24 pt senza (dati JSON della pagina) · Apple · aggiornata il 9/6/2025, consultata il 12/10/2026
- [Accessibility (Mobile design guides)](https://developer.android.com/design/ui/mobile/guides/foundations/accessibility#design-motor) — «Design for motor skill»: «Ensure all touch targets are at least 48 dp» · Google, Android Developers · aggiornata l'8/5/2023, consultata il 12/10/2026
- [axe-core Rule Descriptions](https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md) — «WCAG 2.2 Level A & AA Rules»: target-size (tag wcag22aa, wcag258); «These rules are disabled by default» · Deque Systems (repository dequelabs/axe-core) · regole 4.14, ramo develop, consultato il 12/10/2026

### UX-FLOW · Flusso: compiti ripetuti senza attrito

**Regola.** I lavori di tutti i giorni (accogliere, prenotare, fatturare, scrivere una visita) scorrono senza interruzioni inutili: difficoltà proporzionata a chi li fa, riscontro immediato su ciò che è stato fatto, nessun cambio di pagina, attesa o conferma che non serva; chi è esperto ha scorciatoie che non intralciano chi impara.

**Perché.** Laws of UX: il flusso è lo stato mentale di chi è immerso in un'attività con una concentrazione energica, un pieno coinvolgimento e il piacere di farla (il termine è dello psicologo Mihály Csíkszentmihályi, 1975); è fatto di concentrazione intensa sul presente e di un senso di pieno controllo; nasce quando la difficoltà del compito è bilanciata dall'abilità (un compito troppo difficile frustra, uno troppo facile annoia); per favorirlo servono riscontri su che cosa si è fatto e ottenuto, e la rimozione dell'attrito inutile.

**In DottorCloud.** L'Accoglienza (pages/Today.vue) tiene nella stessa pagina arrivi, sala d'attesa, esiti, ciò che resta da fatturare e la chiusura di cassa (CashClosingDialog.vue); «Trova un orario libero» nel nuovo appuntamento; le viste salvate (composables/visteSalvate.js) per chi è esperto; le pagine sorelle con l'interruttore nella testata (`SORELLE`); le azioni nella riga invece che in una pagina nuova; nessuna finestra modale che blocchi quando basta un messaggio in linea.

**Come si verifica.** Osservare un'ora di lavoro reale in segreteria contando, per ogni compito, interruzioni, attese oltre 1 s, ritorni indietro e conferme; ripetere dopo la modifica; prova di efficienza con utenti esperti (tempo per registrare 10 arrivi).

**Errori da evitare.** (studio UX, ottobre 2026) Per passare a una pagina vicina delle impostazioni bisogna sempre tornare al gruppo; il salvataggio cambia posto e comportamento tra pagine sorelle; sul telefono, sotto il nuovo appuntamento, la barra in basso resta attiva e un tocco fa perdere quanto scritto; dalla lista d'attesa non si può aggiungere nessuno.

**Vedi anche.** [NN-H7](01-interazione.md#nn-h7--flessibilità-ed-efficienza-duso)

**Fonti.**

- [Flow](https://lawsofux.com/flow/) — definizione (Csíkszentmihályi, 1975); concentrazione sul presente e senso di controllo; takeaways (equilibrio tra difficoltà e abilità, riscontro, attrito) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026

### UX-GRADIENTE · Gradiente dell'obiettivo ed effetto Zeigarnik: avanzamento visibile

**Regola.** Ogni percorso a più passi (prenotazione, configurazione, primi passi, ciclo di sedute, attivazione della fatturazione) dice dove si è, quanti passi mancano e che cosa resta, con il nome di ogni passo e uno stato per voce («Fatto», «Da fare», «Lo fa l'agenzia»); il lavoro interrotto si ritrova dove era stato lasciato.

**Perché.** Laws of UX (Goal-Gradient Effect): secondo l'ipotesi del comportamentista Clark Hull (1932) la tendenza ad avvicinarsi a un obiettivo cresce con la vicinanza all'obiettivo; nel 1934 Hull osservò che i ratti correvano sempre più veloci man mano che si avvicinavano al cibo; più si è vicini a finire, più si va veloci, e un'indicazione chiara dell'avanzamento motiva a completare. Laws of UX (Zeigarnik Effect): si ricordano meglio i compiti incompiuti o interrotti di quelli completati (Bluma Zeigarnik); conviene segnalare che c'è altro contenuto e rendere visibile l'avanzamento. L'enciclopedia di psicologia Corsini (Wiley, 2010) riassume lo studio del 1927: i compiti non finiti si ricordano più facilmente di quelli completati, in partecipanti di età diverse.

**In DottorCloud.** `FirstStepsCard.vue` e `FirstStepsPanel.vue` dicono «N di M fatti» con una barra role=progressbar che ha un nome; `dc-steps` segna le sedute di un ciclo («Seduta 3 di 5»: CyclesSection.vue e, nell'area, CycleCard.vue); lo stepper di /prenota va lasciato con il nome di ogni passo anche sul telefono; «Prima di attivarla» va scritto come elenco di passi con il loro stato e un conteggio; `useRitorno` (composables/ritorno.js) ritrova una lista com'era stata lasciata.

**Come si verifica.** Ogni flusso con più di due passi ha un indicatore «Passo N di M» con i nomi dei passi; axe `aria-progressbar-name`; prova: interrompere il flusso a metà (indietro, ricarica, cambio di pagina) e verificare che riprenda da dove era.

**Errori da evitare.** (studio UX, ottobre 2026) «Attiva la fatturazione» sta sopra le cose da fare prima, presentate come facoltative e senza stato né conteggio (gravità 3, ancora da fare); in /prenota sul telefono si vede il nome del solo passo attuale e i tondi numerati sembrano toccabili (sotto i 480 px gli altri nomi restano solo per il lettore di schermo); Telefonia non dice che Twilio manca e lo mette per ultimo; un appuntamento scritto a metà spariva con il tasto indietro di Android (corretto).

**Vedi anche.** [FORM-PASSI](06-moduli.md#form-passi--più-passi-dire-dove-si-è-e-tornare-indietro-senza-perdere-nulla)

**Fonti.**

- [Goal-Gradient Effect](https://lawsofux.com/goal-gradient-effect/) — definizione; origini (Hull, 1932 e 1934); takeaways (avanzamento chiaro) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [Zeigarnik Effect](https://lawsofux.com/zeigarnik-effect/) — definizione; origini (Bluma Zeigarnik); takeaways (segnalare altro contenuto, avanzamento visibile) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [Zeigarnik Effect](https://onlinelibrary.wiley.com/doi/abs/10.1002/9780470479216.corpsy0924) — abstract della voce: lo studio del 1927, compiti non finiti ricordati più facilmente, partecipanti di età diverse (via WebSearch) · The Corsini Encyclopedia of Psychology (Wiley) · 2010

### UX-JAKOB · Legge di Jakob e modelli mentali: convenzioni e parole note

**Regola.** Si usano i modelli che personale e pazienti conoscono già — calendari come quelli più diffusi, chat ordinate come nei messenger, la X in alto a destra per chiudere, la lente per la ricerca, le icone comuni — e le parole del loro lavoro; una convenzione si cambia solo con un guadagno dimostrato, e allora si spiega e per un periodo si lascia tornare alla versione nota.

**Perché.** Laws of UX (Jakob's Law): le persone passano la maggior parte del tempo su altri siti e preferiscono che il tuo funzioni come quelli che già conoscono; il nome viene da Jakob Nielsen; nei grandi cambiamenti si riduce lo spaesamento lasciando per un periodo la versione nota, come fece YouTube nel 2017 con il nuovo design, che si poteva provare e da cui si poteva tornare indietro. Laws of UX (Mental Model): un modello mentale è un modello compresso di ciò che pensiamo di sapere di un sistema e di come funziona, che applichiamo alle situazioni simili; l'idea è attribuita a Kenneth Craik («The Nature of Explanation»); l'esperienza migliora quando il design si allinea al modello dell'utente. NN/g (euristica 4): seguire le convenzioni della piattaforma e del settore; la coerenza esterna (il testo blu sottolineato cliccabile, la lente per la ricerca) è legata alla legge di Jakob, e non rispettarla aumenta il carico cognitivo; un'incoerenza è accettabile solo se il problema è davvero diverso.

**In DottorCloud.** Agenda con ‹ Oggi › e Giorno · Settimana · Mese, e la settimana da lunedì; un giorno tolto dalla settimana va detto (oggi `giorniDellaSettimana()` in utils/agenda.js mostra sabato e domenica solo se qualcuno lavora o ha un appuntamento); nella Chat il messaggio più recente sta in basso, accanto al compositore, come nei messenger (composables/chatAperta.js); finestre che si chiudono con la X e con Esc; le parole del centro secondo il glossario (doc 40) e lo stesso nome per la stessa funzione in ogni pagina (WCAG 3.2.4); con la clinica le parole del verticale (crm/clinica/parole.py).

**Come si verifica.** Per ogni nuovo pattern, confrontarlo con due o tre prodotti che lo staff usa; prova del primo clic; revisione delle parole contro il glossario e ricerca di nomi diversi per la stessa funzione.

**Errori da evitare.** (studio UX, ottobre 2026) Nella Chat il futuro sta in fondo, sotto il passato, dove i messenger mettono l'ultimo messaggio (ancora da fare); la settimana salta il sabato, cioè oggi, senza dirlo; la finestra delle Impostazioni senza X sul computer (corretto); ✓ e ✓✓ per «segna come letta», che nei messenger vogliono dire inviato e letto; sul telefono «Emetti la fattura» che crea solo una bozza (gravità 3; corretto il 12/10/2026 in «Prepara la fattura»); in alto a destra una «C» senza parole che è il responsabile della persona.

**Vedi anche.** [NN-H4](01-interazione.md#nn-h4--coerenza-e-standard)

**Fonti.**

- [Jakob's Law](https://lawsofux.com/jakobs-law/) — definizione; takeaways (lasciare per un periodo la versione nota); esempio di YouTube, 2017; origini (Jakob Nielsen) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [Mental Model](https://lawsofux.com/mental-model/) — definizione; takeaways (allineare il design ai modelli degli utenti); origini (Kenneth Craik) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [Maintain Consistency and Adhere to Standards (Usability Heuristic #4)](https://www.nngroup.com/articles/consistency-and-standards/) — coerenza interna ed esterna; legge di Jakob; carico cognitivo; quando l'incoerenza è accettabile (via WebSearch) · Nielsen Norman Group · consultato il 12/10/2026

### GS-REGIONE · Regione comune e connessione uniforme: contenitori e legami

**Regola.** Ciò che va insieme sta in un contenitore comune (carta, sfondo, bordo) o è unito da un segno visibile (linea, freccia, segmenti di avanzamento); l'identità della persona è una regione propria, sempre nello stesso posto; i contenitori si usano con misura, provando prima lo spazio bianco, e mai uno dentro l'altro senza motivo.

**Perché.** Laws of UX (Common Region): gli elementi che condividono un'area con un confine chiaro sono percepiti come gruppo; il gruppo dà struttura e fa capire in fretta le relazioni tra elementi e sezioni; basta un bordo o uno sfondo. Laws of UX (Uniform Connectedness): gli elementi collegati visivamente sono percepiti più correlati di quelli senza collegamento; si raggruppano funzioni simili con colori, linee, cornici o forme, o con un riferimento tangibile come una linea o una freccia. NN/g (Common Region): gli elementi entro un confine sono percepiti come gruppo e si presume che abbiano caratteristiche o funzioni comuni; il confine è un segnale forte che può prevalere sulla prossimità e sulla somiglianza; i bordi aggiunti per prudenza rendono il design affollato, quindi prima si prova con il solo spazio bianco. NN/g (Cards): la carta raggruppa informazioni correlate grazie alla regione comune, con un bordo e uno sfondo diverso dalla tela; le carte servono a sfogliare più che a cercare un elemento preciso.

**In DottorCloud.** Le carte di Espresso (`:is(div, label).rounded-lg.border` e `.rounded-xl.border`, con la coda della nuvola: sezione 15 di espresso.css); `PersonHeader.vue` come regione dell'identità della persona; `dc-steps` e lo stepper di /prenota come collegamento tra i passi; `dc-list-bar` (la barra delle righe scelte, un blocco profondo) come regione delle azioni sulla selezione; gli StatTile come regioni dei numeri.

**Come si verifica.** Revisione: ogni gruppo logico usa un solo tipo di contenitore e non ci sono carte dentro carte senza motivo; prova di raggruppamento (chiedere a cinque persone quali elementi vanno insieme); i titoli dei gruppi descrivono ciò che contengono (WCAG 2.4.6).

**Errori da evitare.** (studio UX, ottobre 2026) Il gruppo «Dati dell'azienda» della trattativa contiene data di chiusura, probabilità, prossimo passo e responsabile; la testata della persona non mostrava data di nascita, età, sesso né codice fiscale (gravità 3; oggi età e data di nascita compaiono a chi legge i dati fiscali); in ogni scheda della persona cambiano il contenitore (carte con bordo, sezioni pieghevoli, elenco libero, righe con barra colorata) e il posto dell'azione per aggiungere; titoli ripetuti due o tre volte di fila (scheda → titolo → sezione).

**Fonti.**

- [Law of Common Region](https://lawsofux.com/law-of-common-region/) — definizione; takeaways (struttura chiara; bordo; sfondo) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [Law of Uniform Connectedness](https://lawsofux.com/law-of-uniform-connectedness/) — definizione; takeaways (colori, linee, cornici, forme; linea o freccia tra gli elementi) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [The Principle of Common Region: Containers Create Groupings](https://www.nngroup.com/articles/common-region/) — definizione; esempio della finestra di stampa; il confine prevale su prossimità e somiglianza; prima lo spazio bianco (via WebSearch) · Nielsen Norman Group · 2020
- [Cards: UI-Component Definition](https://www.nngroup.com/articles/cards-component/) — la carta e la regione comune (bordo, sfondo, prevalenza sulla prossimità); carte per sfogliare, liste per cercare (via WebSearch) · Nielsen Norman Group · consultato il 12/10/2026

### GS-PROSSIMITA · Legge di prossimità: la distanza dice che cosa va insieme

**Regola.** Lo spazio esprime le relazioni: un'etichetta sta più vicina al suo campo che al campo precedente, l'aiuto sotto il proprio campo, i controlli accanto a ciò su cui agiscono; dentro un gruppo gli spazi sono più piccoli che tra gruppi diversi.

**Perché.** Laws of UX: gli oggetti vicini tendono a essere raggruppati; la prossimità stabilisce una relazione, fa presumere funzioni o tratti comuni e aiuta a elaborare l'informazione più in fretta (principi della Gestalt). NN/g (Proximity): la prossimità può prevalere su segnali in competizione come la somiglianza di colore o di forma; gli elementi lontani sembrano non correlati e sono facilmente trascurati. NN/g (moduli e spazio bianco): ogni etichetta va più vicina al suo campo che agli altri campi; se tra un campo e l'etichetta successiva c'è poco spazio non si capisce che cosa va con che cosa. Designers Italia (Spaziature): spazi più ampi tra le sezioni di una pagina e più stretti dentro una sezione o un componente.

**Soglie ed eccezioni.** Regola verificabile: lo spazio tra un'etichetta e il suo campo è minore dello spazio tra il campo e l'etichetta successiva; lo spazio dentro un gruppo è minore dello spazio tra gruppi (scala in SPAZIO-GRIGLIA).

**In DottorCloud.** `SettingsRow.vue` (gap-y-2 tra le parole e il controllo quando va sotto, py-3 tra una riga e l'altra); `FieldLayout/Section.vue` e `Column.vue` per i moduli; i filtri vicini alla lista che filtrano; le azioni della riga dentro la riga; l'aiuto subito sotto il suo campo, non in un paragrafo lontano.

**Come si verifica.** Misurare in DevTools gli spazi etichetta → campo → etichetta in ogni modulo; screenshot con le distanze annotate; prova di raggruppamento con gli utenti.

**Errori da evitare.** (studio UX, ottobre 2026) Nella lista d'attesa i filtri di servizio e professionista stanno a sinistra e la scelta «In fila | Chiuso» a circa 900 px; nelle impostazioni della lista d'attesa l'aiuto di un campo sta quasi alla stessa distanza dall'etichetta sotto che dal suo campo; sul telefono, in Nome e logo, il riquadro del logo sta sopra la sua etichetta e sembra appartenere al nome del centro; nelle notifiche un selettore largo 1.175 px con segmenti di circa 390 px; nella carta della trattativa l'iniziale del responsabile sta davanti al nome dell'azienda.

**Vedi anche.** [UX-MILLER](#ux-miller--legge-di-miller-e-chunking-gruppi-significativi-niente-da-ricordare), [SPAZIO-GRIGLIA](#spazio-griglia--spaziatura-su-una-scala-di-4-px)

**Fonti.**

- [Law of Proximity](https://lawsofux.com/law-of-proximity/) — definizione; takeaways; origini (Gestalt) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [Proximity Principle in Visual Design](https://www.nngroup.com/articles/gestalt-proximity/) — la prossimità prevale sulla somiglianza di colore o forma; sezione «Far-Away Elements Appear Unrelated, Are Easily Overlooked» (via WebSearch) · Nielsen Norman Group · consultato il 12/10/2026
- [Group Form Elements Effectively Using White Space](https://www.nngroup.com/articles/form-design-white-space/) — suggerimento 1: ogni etichetta più vicina al suo campo che agli altri; esempio del modulo di Uber (via WebSearch) · Nielsen Norman Group · consultato il 12/10/2026
- [Spaziature (Design system, Fondamenti)](https://designers.italia.it/design-system/fondamenti/spaziature/) — «Come usarle»: «definisci una gerarchia»; pubblicata su designers.italia.it/design-system/fondamenti/spaziature/ · Designers Italia (repository italia/designers.italia.it) · consultato il 12/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/spaziature.yaml))

### GS-PRAGNANZ · Legge di Prägnanz: la forma più semplice

**Regola.** Icone, segni, grafici e layout usano la forma più semplice che porta il significato: geometrie regolari, pochi assi di allineamento, niente dettagli o decorazioni che rendano ambiguo un segno; ogni segno si legge al primo sguardo anche a 16 px.

**Perché.** Laws of UX: le persone percepiscono e interpretano le immagini ambigue o complesse nella forma più semplice possibile, perché richiede il minimo sforzo cognitivo; Laws of UX racconta che nel 1910 Max Wertheimer ebbe l'intuizione guardando le luci di un passaggio a livello che si accendevano e si spegnevano, lette come una sola luce in movimento. Apple (Icons): un'icona efficace esprime un solo concetto in modo immediatamente comprensibile; il design va reso riconoscibile e molto semplificato, perché troppi dettagli rendono un'icona confusa o illeggibile; tutte le icone hanno la stessa dimensione, lo stesso livello di dettaglio, lo stesso spessore del tratto e la stessa prospettiva.

**In DottorCloud.** Il marchio è fatto di forme semplici: la nuvola-D (`radius-tail`, 2 px), la croce (bracci uguali, larghi un terzo), i blocchi pieni; `EmptyArt` compone pochi blocchi; icone Lucide da 16 px con tratto 1,5–2 nel colore del testo (README di Espresso, «Iconografia»); grafici piani, senza effetti 3D (dashboardCharts.js).

**Come si verifica.** Prova di riconoscimento delle icone con le persone, anche fuori dal contesto (Designers Italia raccomanda di testarne la riconoscibilità); prova dei segni a 16 px su uno schermo non retina; in revisione: due icone diverse che si somigliano?

**Errori da evitare.** (studio UX, ottobre 2026) Un libro aperto per «Parti da un modello pronto» (di solito vuol dire guida) e un ingranaggio per «Profili» (di solito impostazioni); sul telefono «Dashboard» e «Amministrazione» con icone a griglia quasi identiche; nei listini lo sfondo della carta scelta che esce dagli angoli arrotondati.

**Fonti.**

- [Law of Prägnanz](https://lawsofux.com/law-of-pr%C3%A4gnanz/) — definizione; origini (Max Wertheimer, 1910, le luci del passaggio a livello) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [Icons (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/icons#Best-practices) — introduzione («An effective icon is a graphic asset that expresses a single concept»); «Best practices»: design riconoscibile e semplificato, coerenza visiva (dati JSON della pagina) · Apple · aggiornata il 9/6/2025, consultata il 12/10/2026

### GS-SOMIGLIANZA · Legge di somiglianza: stessa funzione, stesso aspetto

**Regola.** Ciò che funziona allo stesso modo ha lo stesso aspetto e ciò che funziona in modo diverso si vede diverso: link e pulsanti non sembrano testo, ciò che non agisce non sembra un pulsante, la stessa funzione usa sempre lo stesso controllo, la stessa icona e la stessa parola in tutto il prodotto.

**Perché.** Laws of UX: l'occhio percepisce gli elementi simili come un tutto anche se sono separati; colore, forma, dimensione, orientamento e movimento dicono che appartengono allo stesso gruppo e probabilmente hanno lo stesso significato o la stessa funzione; link e navigazione vanno distinti dal testo normale. NN/g: la somiglianza è uno dei principi di raggruppamento scoperti dagli psicologi della Gestalt; ogni interazione crea aspettative su come funzioneranno gli elementi che si somigliano. Apple (Color): non usare lo stesso colore per significati diversi; se il colore del marchio indica che un pulsante senza bordo è interattivo, usarlo per un testo non interattivo confonde. WCAG 3.2.4 (AA): i componenti che hanno la stessa funzione in un insieme di pagine sono identificati in modo coerente.

**Soglie ed eccezioni.** WCAG 3.2.4, livello AA.

**In DottorCloud.** Le varianti dei pulsanti di frappe-ui hanno un significato fisso (solid: l'azione principale, nel colore --brand-action; subtle con `dc-brand`: l'azione per la persona; ghost: secondaria); `CategoryTag` per il tipo di cosa e un badge per lo stato, come vuole Espresso; l'interruttore per accendere una funzione, la casella per scegliere in un elenco; una riga che si apre si apre da tutta la riga (utils/rigaCliccabile.js).

**Come si verifica.** Inventario funzione → controllo, icona e parola su tutte le pagine (più valori per la stessa funzione sono un difetto); axe non lo rileva, serve la revisione manuale; prova con gli utenti: «questo si può toccare?» su dieci elementi.

**Errori da evitare.** (studio UX, ottobre 2026) «Apri i primi passi» grigio su grigio (#f1f4f3 su #f1f4f3), letto come testo; la pastiglia «+ Adesso» della dashboard che sembra un pulsante; caselle senza bordo e pulsante disattivato con lo stesso grigio; funzioni automatiche accese con una casella nelle pagine di fatturazione e con un interruttore nelle altre; nella dashboard del telefono tre filtri con tre aspetti diversi; nel riepilogo una carta con la freccia e l'altra senza.

**Vedi anche.** [NN-H4](01-interazione.md#nn-h4--coerenza-e-standard)

**Fonti.**

- [Law of Similarity](https://lawsofux.com/law-of-similarity/) — definizione; takeaways (colore, forma, dimensione, orientamento, movimento; link e navigazione distinti dal testo) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [Similarity Principle in Visual Design](https://www.nngroup.com/articles/gestalt-similarity/) — origine gestaltica; le aspettative create dagli elementi simili (via WebSearch) · Nielsen Norman Group · consultato il 12/10/2026
- [Color (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/color#Best-practices) — «Best practices»: «Avoid using the same color to mean different things» (dati JSON della pagina) · Apple · aggiornata il 16/12/2025, consultata il 12/10/2026
- [WCAG 2.2 — Success Criterion 3.2.4 Consistent Identification](https://www.w3.org/TR/WCAG22/#consistent-identification) — testo del criterio, livello AA (pubblicato su www.w3.org/TR/WCAG22/#consistent-identification) · W3C, Accessibility Guidelines Working Group (repository w3c/wcag) · WCAG 2.2, ultima pubblicazione 12/12/2024; sorgente consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/consistent-identification.html))

### UX-OCCAM · Rasoio di Occam: togliere finché funziona

**Regola.** Tra soluzioni equivalenti si sceglie quella con meno elementi: ogni campo, colonna, pulsante e paragrafo deve servire a un compito del centro; si analizza ogni elemento e si toglie finché togliere ancora romperebbe la funzione o la chiarezza.

**Perché.** Laws of UX: tra ipotesi che predicono ugualmente bene si sceglie quella con meno assunzioni (Guglielmo di Ockham, c. 1287–1347); il modo migliore per ridurre la complessità è non crearla; si analizza ogni elemento e se ne toglie il più possibile senza compromettere la funzione; si considera finito solo quando non si può togliere altro. La pagina di Laws of UX sulla legge di Hick avverte però di non semplificare fino all'astrazione.

**In DottorCloud.** Moduli di inserimento rapido con i soli campi che servono a un centro medico (la persona prima dell'azienda); colonne e filtri delle liste dalle regole di crm/liste (regole.py, e `SOLO_PER_LA_MACCHINA` in campi.py tiene fuori ciò che serve solo alla macchina); campi nascosti dalle loro dipendenze quando non servono; barra della firma email ridotta al necessario; Espresso: «Ognuno vede solo quello che gli serve» (voci, campi e azioni senza permesso non si mostrano).

**Come si verifica.** Per ogni elemento: chi lo usa, quando, che cosa succede se manca? Dati d'uso: campi mai compilati, colonne mai lette, pulsanti mai premuti; confronto dei tempi prima e dopo la semplificazione.

**Errori da evitare.** (studio UX, ottobre 2026) «Aggiungi una persona» con «Titolo» per primo, «Azienda» e «Territorio», e senza data di nascita; nelle trattative la colonna «Azienda» vuota e «Ricavi annuali» a «0,00 €» su tutte le righe (gravità 3); il badge «Attivo» ripetuto su tutte le sette righe degli ambulatori; due pulsanti per la stessa azione nella pagina vuota degli script; «Contratto» ripetuto nel titolo e nel tipo di un documento. Togliere troppo è l'errore opposto: un'icona senza parole o un campo senza etichetta non sono una semplificazione.

**Vedi anche.** [NN-H8](01-interazione.md#nn-h8--design-estetico-e-minimalista)

**Fonti.**

- [Occam's Razor](https://lawsofux.com/occams-razor/) — definizione; takeaways (non creare complessità; togliere ogni elemento possibile; finito quando non si può togliere altro); origini (Guglielmo di Ockham) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [Hick's Law](https://lawsofux.com/hicks-law/) — takeaways: non semplificare fino all'astrazione (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026

### UX-UTENTE-ATTIVO · Paradosso dell'utente attivo: l'aiuto dentro il lavoro

**Regola.** L'aiuto sta dove e quando serve — testo sotto il campo, stato vuoto con il primo passo, primi passi nella barra, spiegazione accanto a un pulsante che non si può usare — mai solo in un manuale o in un tour obbligatorio; i valori predefiniti funzionano per chi non configura nulla.

**Perché.** Laws of UX: gli utenti non leggono i manuali e cominciano subito a usare il software; il concetto fu definito da Mary Beth Rosson e John Carroll nel 1987 («Interfacing Thought»), dopo studi all'IBM User Interface Institute in cui i nuovi utenti partivano subito, anche a costo di errori e blocchi; la guida va resa accessibile in tutto il prodotto e pensata per il contesto d'uso, per esempio con suggerimenti. NN/g (Nielsen): è un paradosso perché imparare prima farebbe risparmiare tempo; non si progetta per un utente ideale e razionale ma per come le persone si comportano davvero. NN/g (tutorial e aiuto contestuale, 2023): i tutorial iniziali interrompono, non migliorano per forza le prestazioni e si dimenticano in fretta; l'aiuto nel contesto evita questi problemi, se si attiva senza disturbare.

**In DottorCloud.** `EmptyState` (titolo, perché è vuoto, che cosa apparirà, azione); `DescrizioneRipiegata` (due righe e «Mostra altro»); `FirstStepsCard` e `FirstStepsPanel` con i passi segnati fatti dai dati, non da un clic (crm/primi_passi.py); testi d'aiuto dei campi; predefiniti sensati (la vista dell'agenda, la lingua e la valuta del centro); AGENTS.md: ciò che dice un tooltip non è mai l'unico posto dove è detto.

**Come si verifica.** Prova con utenti nuovi senza istruzioni: tempo al primo successo per ruolo; revisione degli stati vuoti (niente ancora, nessun risultato, non consentito); nessun aiuto disponibile solo in un tooltip.

**Errori da evitare.** (studio UX, ottobre 2026) Uno stato vuoto in inglese senza spiegazione né azione nella scheda dell'azienda; «Ancora nessun modulo» proprio sotto un modulo da firmare; Recensioni rimanda a un'automazione da accendere senza portarci; Meta chiede un'app per sviluppatori senza istruzioni; «Completa dal sito» spento, con il motivo solo in un suggerimento che sul telefono non appare.

**Vedi anche.** [NN-H10](01-interazione.md#nn-h10--aiuto-e-documentazione)

**Fonti.**

- [Paradox of the Active User](https://lawsofux.com/paradox-of-the-active-user/) — definizione; origini (Rosson e Carroll, 1987, IBM User Interface Institute); takeaways (guida nel contesto) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [Paradox of the Active User](https://www.nngroup.com/articles/paradox-of-the-active-user/) — origine (Carroll e Rosson, IBM); il paradosso; progettare per come le persone si comportano davvero (via WebSearch) · Nielsen Norman Group (Jakob Nielsen) · consultato il 12/10/2026
- [Onboarding Tutorials vs. Contextual Help](https://www.nngroup.com/articles/onboarding-tutorials/) — sommario: i tutorial interrompono, non migliorano per forza le prestazioni e si dimenticano; l'aiuto contestuale, attivato senza disturbare (via WebSearch) · Nielsen Norman Group · 2023

### UX-PARETO · Principio di Pareto: il meglio alle azioni di ogni giorno

**Regola.** Posizione, dimensione, velocità e cura vanno alle poche azioni che la maggior parte delle persone fa ogni giorno (cercare una persona, prenotare, registrare l'arrivo, emettere la fattura, rispondere a un messaggio); il resto resta raggiungibile senza fare concorrenza.

**Perché.** Laws of UX: per molti eventi circa l'80% degli effetti viene dal 20% delle cause; l'economista Vilfredo Pareto osservò che l'80% della terra in Italia apparteneva al 20% della popolazione; input e output spesso non sono distribuiti in modo uniforme, un grande gruppo può avere pochi contributori significativi, e conviene concentrare la maggior parte dello sforzo dove porta più benefici al maggior numero di utenti.

**Soglie ed eccezioni.** 80/20 è un'euristica, non una proporzione da rispettare.

**In DottorCloud.** Il menu (MENU in utils/menu.js) mette per primo il gruppo della giornata; `barraDelTelefono()` ha quattro posti (Agenda, Persone, Conversazioni e Fatture per primi); `SORELLE` tiene insieme Accoglienza, Agenda e Lista d'attesa; `PulsanteAggiungi` porta sul telefono l'azione principale della pagina; le regole di prestazione di AGENTS.md (aRichiesta, DopoIlDisegno) proteggono prima le pagine di ogni giorno.

**Come si verifica.** Dati d'uso o osservazione: le dieci azioni più frequenti per ruolo confrontate con numero di tocchi e posizione; obiettivo: le cinque principali a uno o due tocchi dalla pagina in cui si è.

**Errori da evitare.** (studio UX, ottobre 2026) Nella scheda persona «Prenota», l'azione più frequente della segreteria, è grigia mentre «Chiama» è piena; dalla lista d'attesa non si può aggiungere nessuno; sul telefono le notifiche sono a due tocchi, segnalate da un pallino senza numero su «Altro».

**Fonti.**

- [Pareto Principle](https://lawsofux.com/pareto-principle/) — definizione; takeaways; origini (Vilfredo Pareto, la terra in Italia) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026

### UX-PARKINSON · Legge di Parkinson: non far gonfiare i compiti

**Regola.** Ogni compito dura il minimo: il sistema precompila ciò che sa (i dati dell'appuntamento nella fattura, la persona già in archivio, la visita precedente), chiede la tastiera giusta e il riempimento automatico, toglie passaggi e attese superflue.

**Perché.** Laws of UX: ogni compito si gonfia fino a occupare tutto il tempo disponibile; Cyril Northcote Parkinson lo scrisse nella prima frase di un saggio umoristico pubblicato su The Economist nel 1955, poi ripreso nel libro «Parkinson's Law: The Pursuit of Progress» (1958); conviene limitare la durata di un compito a quella che l'utente si aspetta, e funzioni come il riempimento automatico fanno risparmiare tempo nei moduli e impediscono al compito di gonfiarsi. WCAG 3.3.7 (A): l'informazione già fornita nello stesso processo è precompilata o selezionabile.

**Soglie ed eccezioni.** WCAG 3.3.7, livello A.

**In DottorCloud.** La fattura nasce dall'appuntamento (`_fattura_da_appuntamento` in crm/invoicing/api.py) senza ricopiare cliente e servizio; «Inizia dall'ultima visita» per le schede cliniche (`start_sheet(from_last=1)` in crm/clinica/cartella.py); `autocomplete` sui dati della persona in /prenota (name, email, tel), nei moduli di /modulo (crm/public/js/moduli_campi.js) e all'ingresso dell'area; `tastieraDi()` e `tastiera()` (utils/tastiera.js) per la tastiera giusta; nella nuova trattativa la persona già in archivio va proposta prima di crearne una nuova.

**Come si verifica.** Cronometrare i compiti principali prima e dopo; per ogni campo chiesto: il sistema lo sa già? Verifica di WCAG 3.3.7 nei percorsi appuntamento → fattura e prenotazione → registrazione.

**Errori da evitare.** (studio UX, ottobre 2026) In «Crea una trattativa» «Scegli una persona esistente» è spento per impostazione: si riscrivono nome e cognome e si crea un doppione (gravità 3); il cursore va da solo in «Nome dell'azienda» e sul telefono apre la tastiera sul campo sbagliato; la data di nascita non è chiesta nella nuova persona.

**Fonti.**

- [Parkinson's Law](https://lawsofux.com/parkinsons-law/) — definizione; origini (The Economist, 1955; il libro del 1958); takeaways (durata attesa, riempimento automatico) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [WCAG 2.2 — Success Criterion 3.3.7 Redundant Entry](https://www.w3.org/TR/WCAG22/#redundant-entry) — testo del criterio, livello A (pubblicato su www.w3.org/TR/WCAG22/#redundant-entry) · W3C, Accessibility Guidelines Working Group (repository w3c/wcag) · WCAG 2.2, ultima pubblicazione 12/12/2024; sorgente consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/22/redundant-entry.html))

### UX-PICCO-FINE · Regola del picco e della fine: momenti forti e chiusure chiare

**Regola.** I momenti più intensi di un percorso (un errore, un pagamento, una firma, una disdetta) e la sua fine si progettano con cura: la fine dice che cosa è stato fatto, con quale riferimento e che cosa succede dopo; i momenti negativi danno causa, rimedio e rassicurazione, dicendo se i dati sono salvi.

**Perché.** Laws of UX: le persone giudicano un'esperienza soprattutto da come si sono sentite al suo picco e alla sua fine, non dalla somma o dalla media dei momenti. Lo studio di Kahneman, Fredrickson, Schreiber e Redelmeier («When More Pain Is Preferred to Less: Adding a Better End», Psychological Science, 1993): una mano in acqua a 14 °C per 60 s, contro gli stessi 60 s più altri 30 s mentre l'acqua saliva a 15 °C; i partecipanti erano più disposti a ripetere la prova più lunga. NN/g: la memoria si concentra sui momenti più intensi, positivi o negativi, e sul modo in cui l'esperienza finisce.

**In DottorCloud.** La conferma di /prenota dice quando e dove, che è partita un'email con i dettagli, dà il link per gestire o annullare la prenotazione e l'aggiunta al calendario; un toast di riuscita con «Annulla» per le azioni reversibili; la firma dei moduli chiude con il PDF e la sua pagina di evidenza; la chiusura di cassa con il riepilogo e la quadratura al centesimo; gli errori dicono causa, rimedio e se i dati sono salvi (README di Espresso: errori che dicono come rimediare).

**Come si verifica.** Mappa di ogni percorso con i picchi (errori, attese, pagamenti) e la fine; al termine delle prove chiedere che cosa si ricorda e com'è andata; revisione delle schermate finali: c'è il riferimento? c'è il passo successivo?

**Errori da evitare.** (studio UX, ottobre 2026) Una cosa segnata fatta per sbaglio si recupera solo per pochi secondi; «Nuova fattura» mostra un errore rosso ed «Emetti» spento prima di qualsiasi inserimento; la pagina d'errore senza titolo né intestazione; sul telefono «Emetti la fattura» che alla fine non emette (corretto il 12/10/2026 in «Prepara la fattura»).

**Fonti.**

- [Peak-End Rule](https://lawsofux.com/peak-end-rule/) — definizione; origini (Kahneman e colleghi, 1993: 14 °C per 60 s contro 60 + 30 s fino a 15 °C) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [The Peak–End Rule: How Impressions Become Memories](https://www.nngroup.com/articles/peak-end-rule/) — la memoria si concentra sui picchi, positivi o negativi, e sulla fine (via WebSearch) · Nielsen Norman Group · consultato il 12/10/2026

### UX-POSTEL · Legge di Postel: accettare come scrivono le persone, restituire in forma rigorosa

**Regola.** Ogni campo accetta l'input come lo scrivono le persone (spazi, trattini, punti, +39 o 0039, virgola decimale, maiuscole o minuscole, testo incollato da altre app), lo normalizza e lo mostra subito nella forma canonica; ciò che è ambiguo non si indovina in silenzio: si chiede o si mostra l'interpretazione.

**Perché.** Jon Postel scrisse il principio di robustezza nelle specifiche di TCP: RFC 761 (1980) ha la sezione 2.10 «Robustness Principle», e RFC 793 (1981, § 2.10) dice «be conservative in what you do, be liberal in what you accept from others». Laws of UX: essere aperti a qualsiasi azione e input dell'utente, anticipare quasi ogni input, accesso e capacità mantenendo l'interfaccia affidabile e accessibile; accettare input variabile, tradurlo in ciò che serve al sistema, fissare confini chiari e dare un riscontro evidente. RFC 9413 («Maintaining Robust Protocols», 2023) osserva che il principio è stato interpretato in modi diversi, alcuni dannosi per l'interoperabilità, e che la tolleranza verso gli errori si accumula quando una specifica resta ferma a lungo: si tollera, ma si normalizza e lo si dichiara.

**In DottorCloud.** `leggibile()` (utils/telefono.js) legge un numero comunque sia scritto — spazi, punti, trattini, barre, parentesi, +39 o 0039 — e lo mostra a gruppi, mentre nei dati resta l'E.164; `flt()` (utils/numberFormat.js) legge «12,5» come 12,5 anche dove il sito scrive 12.5, mentre «1,234» resta letto secondo il formato del sito; crm/api/sul_telefono.py confronta le ultime nove cifre di un numero scritto in qualsiasi modo; l'importazione (crm/importazione/regole.py) legge date e «ROSSI MARIO» come li scrive un foglio italiano e accetta il codice fiscale con spazi e in minuscolo.

**Come si verifica.** Test unitari con le varianti reali (frontend/tests/unit/telefono.test.js, numberFormat.test.js); prove di incolla da Excel, WhatsApp ed email; per ogni campo con un formato: l'errore dice come scriverlo, con un esempio?

**Errori da evitare.** Rifiutare un formato comune invece di normalizzarlo; normalizzare senza mostrare il risultato (la persona non vede che «01/02» è diventato il 1° febbraio); (studio UX, ottobre 2026) nelle impostazioni «Formati» le scelte erano codici invece di esempi e «Precisione valuta» suggeriva 3 decimali mentre gli importi ne usano 2.

**Vedi anche.** [FORM-POSTEL](06-moduli.md#form-postel--accettare-i-formati-reali-normalizzare-dopo)

**Fonti.**

- [Postel's Law](https://lawsofux.com/postels-law/) — definizione; takeaways (input variabile, confini, riscontro); origini (Jon Postel, TCP) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [RFC 761: DoD Standard Transmission Control Protocol](https://www.rfc-editor.org/rfc/rfc761.html) — indice: § 2.10 «Robustness Principle» (via WebSearch) · IETF / RFC Editor (J. Postel) · 1980
- [RFC 793: Transmission Control Protocol](https://www.rfc-editor.org/rfc/rfc793.html) — § 2.10 «Robustness Principle»: «be conservative in what you do, be liberal in what you accept from others» (via WebSearch) · IETF / RFC Editor (J. Postel) · 1981
- [RFC 9413: Maintaining Robust Protocols](https://datatracker.ietf.org/doc/html/rfc9413) — interpretazioni del principio e loro effetti sull'interoperabilità; la tolleranza che si accumula (via WebSearch) · IETF (IAB) · 2023

### UX-ATTENZIONE · Attenzione selettiva: ciò che conta non deve sembrare pubblicità

**Regola.** Le informazioni importanti stanno nel flusso del compito, vicino all'azione e con parole chiare, mai in riquadri che sembrano promozioni né nei posti tipici dei banner; un cambiamento importante si dice in modo esplicito (testo, stato, annuncio) e non si fanno competere più cambiamenti nello stesso momento.

**Perché.** Laws of UX: l'attenzione selettiva è il processo con cui ci concentriamo su una parte degli stimoli, di solito quelli legati ai nostri obiettivi, filtrando il resto; banner blindness: si ignora ciò che somiglia a una pubblicità, sta vicino a una pubblicità o occupa i posti tradizionali delle pubblicità; change blindness: cambiamenti significativi passano inosservati per i limiti dell'attenzione e la mancanza di segnali forti, quindi vanno evitati cambiamenti in competizione nello stesso momento. NN/g (2018): la cecità ai banner è ancora diffusa, è una forma di attenzione selettiva legata alla capacità limitata di attenzione, e le persone saltano anche contenuti non pubblicitari che sembrano pubblicità (posizione tipica, animazione, vicinanza a promozioni).

**In DottorCloud.** Gli avvisi del lavoro (fatturazione in prova, consenso mancante, modulo da firmare per l'appuntamento) vanno dentro la riga o la scheda interessata, con icona e parole; le carte promozionali (mettere l'app sulla schermata Home, Mobile/InstallaApp.vue) sono separate e si chiudono con «Non ora»; gli stati sono annunciati con role=status o aria-live (WCAG 4.1.3); il messaggio aperto da una notifica è segnato con `dc-segnato` (composables/conversationScroll.js).

**Come si verifica.** Prova «trova l'avviso»: in quanto tempo si nota l'informazione critica? Revisione: ogni cambiamento importante ha testo e annuncio? Contare i riquadri colorati per schermata.

**Errori da evitare.** (studio UX, ottobre 2026) L'informativa privacy mai firmata da una paziente già visitata è una riga grigia come le altre, con «Mai firmato» a 12 px; sul telefono, in «Altro», le notifiche (5) stanno sotto «Primi passi» e la carta «Metti DottorCloud sulla schermata Home», a 527 px su 844; il pallino verde su «Altro» non dice se riguarda le notifiche o i primi passi.

**Fonti.**

- [Selective Attention](https://lawsofux.com/selective-attention/) — definizione; takeaways (filtrare, banner blindness, change blindness) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [Banner Blindness Revisited: Users Dodge Ads on Mobile and Desktop](https://www.nngroup.com/articles/banner-blindness-old-and-new-findings/) — ancora diffusa; attenzione selettiva e capacità limitata; i segni di ciò che sembra pubblicità (via WebSearch) · Nielsen Norman Group · 2018

### UX-POSIZIONE · Effetto posizione seriale: l'essenziale apre la riga

**Regola.** In ogni riga ed elenco l'informazione chiave sta all'inizio — il nome della persona apre la riga, anche per il lettore di schermo — e nei menu e nelle barre le voci più importanti stanno ai due estremi; le meno importanti vanno nel mezzo e l'azione principale resta sempre allo stesso estremo.

**Perché.** Laws of UX: si ricordano meglio il primo e l'ultimo elemento di una serie (effetti di primacy e recency); il termine è attribuito a Hermann Ebbinghaus; gli elementi meno importanti vanno a metà delle liste e le azioni chiave agli estremi, per esempio della navigazione. Apple (Layout): ordinare i contenuti per importanza; si legge dall'alto e dal lato iniziale, quindi le cose più importanti vanno in alto e all'inizio.

**In DottorCloud.** AGENTS.md: in agenda un appuntamento legge prima la persona, poi che cosa e dove (`testoDelBlocco()` in utils/agenda.js); nelle righe del telefono (ElencoPersone.vue, AgendaDelGiorno.vue) il nome viene per primo; nella barra del telefono il lavoro del giorno sta al primo posto e «Altro» all'ultimo; nelle righe la persona viene prima del servizio e il numero del documento dopo il nome.

**Come si verifica.** Per ogni lista: il primo testo letto, a vista e dal lettore di schermo (ordine del DOM), è l'identificativo umano? Prova di ricordo dopo uno sguardo di pochi secondi alla barra di navigazione.

**Errori da evitare.** (studio UX, ottobre 2026) In Accoglienza la riga mostra il servizio prima del paziente e sul telefono il nome è al terzo rigo; nelle chiamate la persona cambia colonna a seconda della direzione; sul telefono le fatture «Da inviare» hanno il numero prima del nome; nella Chat gli appuntamenti futuri stavano in fondo, dove si cerca l'ultimo messaggio (corretto il 12/10/2026).

**Fonti.**

- [Serial Position Effect](https://lawsofux.com/serial-position-effect/) — definizione; takeaways (meno importanti a metà, azioni chiave agli estremi); origini (Ebbinghaus) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [Layout (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/layout#Visual-hierarchy) — «Visual hierarchy»: «Order content by relative importance» (dati JSON della pagina) · Apple · aggiornata il 9/9/2026, consultata il 12/10/2026

### UX-TESLER · Legge di Tesler: la complessità la assorbe il sistema

**Regola.** La complessità che non si può togliere (IVA e nature, bollo, cassa, ritenuta, Sistema TS, disponibilità, omonimi, fusi orari) la gestisce DottorCloud con calcoli, predefiniti, controlli e parole semplici; alla persona si chiede solo ciò che solo lei sa.

**Perché.** Laws of UX: ogni processo ha un nucleo di complessità che non si può eliminare e che deve essere assunto dal sistema o dall'utente (legge di conservazione della complessità); Larry Tesler, a Xerox PARC a metà degli anni Ottanta, sosteneva che nella maggior parte dei casi un ingegnere dovrebbe passare una settimana in più a ridurre la complessità piuttosto che far passare a milioni di utenti un minuto in più; Laws of UX riporta anche l'osservazione di Bruce Tognazzini: quando un'applicazione si semplifica, gli utenti affrontano compiti più complessi.

**In DottorCloud.** Il motore di fatturazione: `preview` (crm/invoicing/emissione.py) classifica e somma in memoria, `da_correggere()` (crm/invoicing/documento.py) dice che cosa ferma una bozza; la preimpostazione sanitaria in tre domande (HealthcareSetup.vue); i codici non si mostrano mai, si nominano in parole (`scelte.CAMPI`, `voci.py`); la numerazione delle fatture si sceglie tra esempi; «Trova un orario libero» sul motore della disponibilità; le ore nel fuso del centro con `oraDelCentro()` (utils/scheduler.js).

**Come si verifica.** Per ogni campo: il sistema potrebbe dedurlo o calcolarlo? Prova con dieci fatture tipo: zero errori fiscali dell'utente? Revisione delle sigle: spiegate alla prima comparsa?

**Errori da evitare.** (studio UX, ottobre 2026) «Formati» con codici invece di esempi; SdI, Sistema TS, PAdES, art. 10 e 15 mai spiegati; due impostazioni di valuta e le impostazioni regionali sparse in tre schede; numeri della dashboard che si contraddicono con quelli di Fatture, lasciando la riconciliazione all'utente.

**Fonti.**

- [Tesler's Law](https://lawsofux.com/teslers-law/) — definizione; origini (Larry Tesler, Xerox PARC, metà degli anni Ottanta; la settimana dell'ingegnere e il minuto degli utenti); nota su Bruce Tognazzini (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026

### UX-RESTORFF · Effetto Von Restorff: una sola cosa in risalto, con più segnali

**Regola.** In ogni vista un solo elemento è messo in risalto (l'azione principale o l'informazione critica: un'allergia, un consenso mancante, una scadenza superata) con più di un segnale — forma, peso, posizione, icona e parole — mai con il solo colore; il risalto si usa con parsimonia e ha sempre un significato.

**Perché.** Laws of UX: quando sono presenti più oggetti simili, si ricorda meglio quello diverso (effetto di isolamento); Hedwig von Restorff (1906–1962) lo mostrò in uno studio del 1933; conviene rendere visivamente distinte le informazioni e le azioni chiave, con misura, perché i risalti non si facciano concorrenza e non sembrino pubblicità; non affidarsi al solo colore, che esclude chi ha un deficit della visione dei colori o ipovisione; prudenza con il movimento per chi vi è sensibile. Hunt (1995, Psychonomic Bulletin & Review, vol. 2, pp. 105–112) rilegge i dati di von Restorff: la salienza percettiva non è necessaria all'effetto, conta la distinzione rispetto alla somiglianza degli altri elementi. Apple: uno o due pulsanti prominenti per vista; è lo stile, non la dimensione, a distinguere la scelta preferita. Espresso: i blocchi pieni sono «uno per vista dove serve attenzione, non di più».

**Soglie ed eccezioni.** Un blocco pieno per vista (Espresso); 1–2 pulsanti prominenti (Apple).

**In DottorCloud.** Gli StatTile e `dc-numero--blocco`: il primo numero di una riga è il blocco profondo (`highlightedNumbers()` in utils/dashboard.js); il toast e la barra delle righe scelte sono blocchi; la prima visita in agenda è il blocco del marchio (`dc-evento--prima`); le cose scadute vanno in cima, con colore, icona e parola.

**Come si verifica.** Contare per schermata i blocchi pieni e i pulsanti solid; prova in scala di grigi: l'elemento in risalto si distingue ancora? Chiedere, dopo uno sguardo breve, che cosa si è notato per primo.

**Errori da evitare.** (studio UX, ottobre 2026) Sul telefono i riquadri scuri della dashboard finiscono in posti casuali, tre per schermata: `highlightedNumbers()` sceglie il primo di ogni riga del layout del computer e DashboardGrid.vue usa la stessa scelta anche quando le carte si impilano (verificato nel codice il 12/10/2026); tre pulsanti pieni verdi nella scheda persona; un tondo verde pieno con «0» accanto a «Trattative» e «Contatti», il segno più forte della pagina per dire che non c'è niente; cose da fare scadute nello stesso colore e con la stessa icona delle future (gravità 3).

**Vedi anche.** [MOB-AZIONE-PRINCIPALE](05-telefono-e-tocco.md#mob-azione-principale--il--una-sola-azione-principale-in-basso-a-destra)

**Fonti.**

- [Von Restorff Effect](https://lawsofux.com/von-restorff-effect/) — definizione; takeaways (misura, non solo colore, movimento); origini (Hedwig von Restorff, 1933) (via WebSearch) · Laws of UX (Jon Yablonski) · consultato il 12/10/2026
- [The subtlety of distinctiveness: What von Restorff really did](https://link.springer.com/article/10.3758/BF03214414) — abstract: la salienza percettiva non è necessaria all'effetto di isolamento; distinzione e somiglianza; vol. 2, pp. 105–112 (via WebSearch) · Psychonomic Bulletin & Review (Springer), R. R. Hunt · 1995
- [Buttons (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/buttons#Style) — «Style»: uno o due pulsanti prominenti per vista; «Use style — not size — to visually distinguish the preferred choice» (dati JSON della pagina) · Apple · aggiornata il 16/12/2025, consultata il 12/10/2026

### VIS-GERARCHIA · Gerarchia visiva: un ordine di lettura voluto

**Regola.** Ogni schermata si legge in un ordine voluto — titolo, informazione o azione principale, poi il resto — ottenuto con poche dimensioni di testo della scala di Espresso, peso, colore, posizione e raggruppamento; la stessa gerarchia è nel codice (un h1, poi h2 e h3 senza salti, al massimo quattro livelli) e resta quando il testo si ingrandisce.

**Perché.** Apple (Typography): regolare peso, dimensione e colore per far vedere la gerarchia, e mantenerla quando le persone cambiano la dimensione del testo; usare pochi caratteri tipografici, perché mescolarne troppi oscura la gerarchia e rende l'interfaccia incoerente. Apple (Layout): ordinare per importanza; allineare per rendere gli elementi facili da scorrere e indentare per subordinare; raggruppare le cose correlate con lo spazio, i contenitori o i separatori. Designers Italia (Tipografia): non superare quattro livelli di intestazione (H1–H4) per pagina. WCAG 1.3.1 (A): struttura e relazioni veicolate dalla presentazione sono determinabili dal codice o disponibili nel testo; WCAG 2.4.6 (AA): titoli ed etichette descrivono argomento o scopo.

**Soglie ed eccezioni.** Al massimo 4 livelli di titolo (Designers Italia); WCAG 1.3.1 (A) e 2.4.6 (AA).

**In DottorCloud.** La scala di Espresso: `dc-page-title` (20 px, grassetto) per il titolo delle pagine principali, `text-xl-semibold` (17 px) per le finestre, `text-lg-semibold` (16 px) per carte e sezioni, `text-base` (14 px) per il testo, `text-sm` (13 px) per i metadati, `text-xs` (12 px) per badge e orari (le misure sono quelle di frappe-ui 1.0.0-beta.29); Inter come unico carattere; in `SettingsRow.vue` l'etichetta (`text-p-base-medium`, ink-gray-7) si distingue dalla descrizione (`text-p-sm`, ink-gray-5); App.vue dà a ogni pagina il titolo per il lettore di schermo (`titoloDellaPagina()` e `CON_UN_TITOLO` in utils/menu.js).

**Come si verifica.** axe `page-has-heading-one`, `heading-order` ed `empty-heading` (regole di buona pratica) e `p-as-heading` (sperimentale); prova in scala di grigi e con la pagina sfocata (che cosa emerge per primo?); elenco dei titoli letto con VoiceOver o TalkBack.

**Errori da evitare.** (studio UX, ottobre 2026) Titoli ripetuti due o tre volte di fila («Abbonamenti» → «Abbonamenti» → «Abbonamenti 1»); in Richieste di recensione etichette con lo stesso colore e la stessa dimensione del testo d'aiuto accanto ad altre scure, più un terzo stile nella stessa pagina; «OGGI» delle notifiche è un h3 senza h2, a 11 px; le schede della persona erano h3 subito sotto il nome (corrette in h2); la pagina di accesso senza h1 (ancora da fare).

**Vedi anche.** [WCAG-1.3.1-TITOLI](02-wcag-percepibile-e-robusto.md#wcag-131-titoli--titoli-veri-uno-che-nomina-la-pagina-gli-altri-in-ordine)

**Fonti.**

- [Typography (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/typography#Conveying-hierarchy) — «Conveying hierarchy» (dati JSON della pagina) · Apple · aggiornata il 16/12/2025, consultata il 12/10/2026
- [Layout (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/layout#Visual-hierarchy) — «Visual hierarchy»: ordinare per importanza, allineare, indentare, raggruppare (dati JSON della pagina) · Apple · aggiornata il 9/9/2026, consultata il 12/10/2026
- [Tipografia (Design system, Fondamenti)](https://designers.italia.it/design-system/fondamenti/tipografia/) — «Consigli d'uso» → «Gerarchia visiva»: non più di quattro livelli di intestazione; pubblicata su designers.italia.it/design-system/fondamenti/tipografia/ · Designers Italia (repository italia/designers.italia.it) · consultato il 12/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/tipografia.yaml))
- [WCAG 2.2 — Success Criterion 1.3.1 Info and Relationships](https://www.w3.org/TR/WCAG22/#info-and-relationships) — testo del criterio, livello A (pubblicato su www.w3.org/TR/WCAG22/#info-and-relationships) · W3C, Accessibility Guidelines Working Group (repository w3c/wcag) · WCAG 2.2, ultima pubblicazione 12/12/2024; sorgente consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/info-and-relationships.html))
- [WCAG 2.2 — Success Criterion 2.4.6 Headings and Labels](https://www.w3.org/TR/WCAG22/#headings-and-labels) — testo del criterio, livello AA (pubblicato su www.w3.org/TR/WCAG22/#headings-and-labels) · W3C, Accessibility Guidelines Working Group (repository w3c/wcag) · WCAG 2.2, ultima pubblicazione 12/12/2024; sorgente consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/headings-and-labels.html))

### TIPO-RIGA · Lunghezza della riga: 45–75 caratteri, mai oltre 80

**Regola.** Ogni testo che va su più righe (descrizioni delle impostazioni, avvisi, note, testi dell'area pazienti e delle pagine pubbliche) ha righe tra 45 e 75 caratteri e mai oltre 80; la larghezza massima si dà in unità relative (ch o rem), non in px, e lo spazio che avanza resta vuoto.

**Perché.** WCAG 1.4.8 (AAA): per i blocchi di testo dev'essere possibile una larghezza non superiore a 80 caratteri (40 in cinese, giapponese e coreano). Understanding 1.4.8: per chi ha alcune disabilità di lettura o della vista le righe lunghe sono una barriera, perché fa fatica a tenere il segno e a seguire il testo; un blocco stretto aiuta a passare alla riga successiva. Tecnica C20: larghezze relative, perché le righe possano stare in media entro 80 caratteri e la colonna si allarghi con il testo. Designers Italia: lunghezza massima raccomandata di 75 caratteri per riga. GOV.UK: il layout a due terzi evita righe troppo lunghe, di solito non più di 75 caratteri. web.dev, citando Bringhurst: tra 45 e 75 caratteri la misura è soddisfacente e 66 è considerato l'ideale; si limita la larghezza con max-inline-size in ch o rem, non in px, perché le persone ingrandiscono il testo.

**Soglie ed eccezioni.** Al massimo 80 caratteri (WCAG 1.4.8, AAA; 40 in CJK); al massimo 75 (Designers Italia, GOV.UK); 45–75, ideale 66 (Bringhurst, via web.dev).

**In DottorCloud.** Le descrizioni di `SettingsRow.vue` (`text-p-sm`, oggi senza larghezza massima) e gli avvisi prendono una classe come `max-w-[65ch]`; nello stato vuoto la frase (`.dc-empty__text`) è già limitata a 320 px; i testi dell'area pazienti e di /prenota stanno in colonne di circa 65 caratteri; fogli e finestre larghe non stendono i paragrafi a tutta larghezza.

**Come si verifica.** Script Playwright a 1280 e 1440 px: per ogni testo su più righe calcolare i caratteri per riga (lunghezza del testo divisa per il numero di righe di getClientRects) e segnalare quelli oltre 80; revisione manuale dei paragrafi più lunghi.

**Errori da evitare.** (studio UX, ottobre 2026) Descrizioni delle impostazioni da 13 px su tutta la larghezza del pannello: 128 caratteri per riga in «Porta qui le tue persone», 103–105 in Conversazioni e Notifiche; all'opposto, in /prenota le carte delle sedi larghe 190 px con indirizzo e orari su 5–6 righe mentre metà della pagina resta vuota.

**Vedi anche.** [WCAG-1.4.8-AAA](02-wcag-percepibile-e-robusto.md#wcag-148-aaa--obiettivo-aaa-blocchi-di-testo-comodi-da-leggere), [I18N-ESPANSIONE](07-lingua-e-norme.md#i18n-espansione--spazio-per-litaliano-più-lungo-dellinglese)

**Fonti.**

- [WCAG 2.2 — Success Criterion 1.4.8 Visual Presentation](https://www.w3.org/TR/WCAG22/#visual-presentation) — testo del criterio, livello AAA: larghezza non oltre 80 caratteri (pubblicato su www.w3.org/TR/WCAG22/#visual-presentation) · W3C, Accessibility Guidelines Working Group (repository w3c/wcag) · WCAG 2.2, ultima pubblicazione 12/12/2024; sorgente consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/visual-presentation.html))
- [Understanding Success Criterion 1.4.8: Visual Presentation](https://www.w3.org/WAI/WCAG22/Understanding/visual-presentation.html) — «Intent»: righe lunghe e perdita del segno (pubblicato su www.w3.org/WAI/WCAG22/Understanding/visual-presentation.html#intent) · W3C WAI (repository w3c/wcag) · consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/understanding/20/visual-presentation.html))
- [C20: Using relative measurements to set column widths so that lines can average 80 characters or less when the browser is resized](https://www.w3.org/WAI/WCAG22/Techniques/css/C20) — «Description», «Examples» e «Tests» (pubblicata su www.w3.org/WAI/WCAG22/Techniques/css/C20) · W3C WAI (repository w3c/wcag) · consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/techniques/css/C20.html))
- [Tipografia (Design system, Fondamenti)](https://designers.italia.it/design-system/fondamenti/tipografia/) — «Consigli d'uso» → «Lunghezza dei paragrafi»: «una lunghezza massima di 75 caratteri per riga»; pubblicata su designers.italia.it/design-system/fondamenti/tipografia/ · Designers Italia (repository italia/designers.italia.it) · consultato il 12/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/tipografia.yaml))
- [Layout](https://design-system.service.gov.uk/styles/layout/) — «Screen size»: due terzi, «no more than 75 characters per line»; pubblicata su design-system.service.gov.uk/styles/layout/ · GOV.UK Design System (repository alphagov/govuk-design-system) · consultato il 12/10/2026 ([sorgente letto](https://github.com/alphagov/govuk-design-system/blob/main/src/styles/layout/index.md))
- [Typography (Learn Design)](https://github.com/GoogleChrome/web.dev/blob/main/src/site/content/en/learn/design/typography/index.md) — «Line length»: Bringhurst 45–75, 66 ideale; max-inline-size in rem o ch, non in px; pubblicata su web.dev/learn/design/typography · Google, web.dev (Jeremy Keith; repository GoogleChrome/web.dev) · 2021

### TIPO-DIMENSIONI · Dimensioni e pesi del testo

**Regola.** Il testo da leggere è grande abbastanza per il dispositivo e per chi lo usa: nel gestionale 14 px per l'interfaccia e mai sotto 12 px per un'informazione; sul telefono 16 px nei campi; nell'area pazienti e nelle pagine pubbliche testo corrente di almeno 16 px; niente pesi sottili; dimensioni in unità relative, così che lo zoom al 200% non perda nulla.

**Perché.** Apple: dimensioni predefinite e minime del testo, iOS e iPadOS 17 e 11 pt, macOS 13 e 10 pt; evitare i pesi Ultralight, Thin e Light, difficili da vedere soprattutto quando il testo è piccolo; dare la possibilità di ingrandire il testo almeno del 200% (140% su watchOS); con il testo grande mantenere la gerarchia e ridurre al minimo i troncamenti. Android: il corpo del testo mai sotto 12 sp. Designers Italia (Tipografia, «Corpo del testo»): interlinea di 24 px, corpo 16/18 px per il testo serif (la stessa tabella indica 12/18 px per il sans). GOV.UK: paragrafo predefinito di 19 px, 16 px da usare con parsimonia; dalla versione 6.0.0 di GOV.UK Frontend la scala ingrandisce il testo sugli schermi piccoli. WCAG 1.4.4 (AA): testo ridimensionabile fino al 200% senza tecnologie assistive e senza perdita di contenuto o funzioni, esclusi sottotitoli e immagini di testo. WCAG (definizione di testo grande): almeno 18 pt, o 14 pt in grassetto, cioè circa 24 px e 18,5 px (Understanding 1.4.3); i caratteri a tratto molto sottile si leggono peggio, soprattutto con poco contrasto.

**Soglie ed eccezioni.** Apple: iOS 17/11 pt, macOS 13/10 pt; Android: almeno 12 sp; GOV.UK: 19 px; WCAG 1.4.4: 200% (AA); testo grande: almeno 24 px, o circa 18,5 px in grassetto.

**In DottorCloud.** Espresso: `text-base` 14 px per l'interfaccia, `text-sm` 13 px per i metadati, `text-xs` 12 px per badge e orari; `text-tiny` (11 px, maiuscolo) solo per poche etichette di gruppo che non portano informazioni; telefono.css porta i campi a 16 px, altrimenti iOS ingrandisce la pagina; l'area pazienti usa titoli da 28 px (`area-title`) e controlli da 40 px; `dc-metric` (28 px) per i numeri; nel CSS nuovo le dimensioni in rem.

**Come si verifica.** Zoom del browser al 200% e al 400% su ogni schermata (WCAG 1.4.4 e 1.4.10); axe `meta-viewport`; script che elenca i nodi di testo visibili con una dimensione calcolata sotto 12 px; prova su iPhone con «Testo più grande» e su Android con i caratteri al 130% (le pagine di ogni giorno devono reggere a 280 px).

**Errori da evitare.** (studio UX, ottobre 2026) Etichette tutte maiuscole a 11 px («MARKETING» nella barra laterale, «OGGI» nelle notifiche); orari dei blocchi d'agenda e date sull'asse dei grafici a 11 px (`dc-evento__ora` ed `fontSize: 11` in dashboardCharts.js: ancora così); un documento che si apre solo da un titolo alto 16 px. Verificato nel codice il 12/10/2026: nel blocco sottile dell'agenda (`dc-evento--sottile`) ora e nome sono a 10,5 px, e i contatori sul pulsante del telefono (PhoneButton.vue) e nella barra dell'area (area/App.vue) a 10 px.

**Fonti.**

- [Typography (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/typography#Ensuring-legibility) — «Ensuring legibility»: tabella delle dimensioni predefinite e minime; pesi sottili da evitare; «Supporting Dynamic Type»: troncamenti al minimo, gerarchia coerente (dati JSON della pagina) · Apple · aggiornata il 16/12/2025, consultata il 12/10/2026
- [Accessibility (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/accessibility#Vision) — «Vision»: ingrandimento del testo almeno del 200% (dati JSON della pagina) · Apple · aggiornata il 9/6/2025, consultata il 12/10/2026
- [Accessibility (Mobile design guides)](https://developer.android.com/design/ui/mobile/guides/foundations/accessibility#design-vision) — «Design for vision»: «Don't make the body size any smaller than 12 sp» · Google, Android Developers · aggiornata l'8/5/2023, consultata il 12/10/2026
- [Tipografia (Design system, Fondamenti)](https://designers.italia.it/design-system/fondamenti/tipografia/) — «Stili tipografici» → «Corpo del testo» (Body text serif 16/18 px, Body text sans 12/18 px, interlinea 24 px); pubblicata su designers.italia.it/design-system/fondamenti/tipografia/ · Designers Italia (repository italia/designers.italia.it) · consultato il 12/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/tipografia.yaml))
- [Paragraphs](https://design-system.service.gov.uk/styles/paragraphs/) — paragrafo predefinito di 19 px; «Body small» 16 px con parsimonia; avviso sulla nuova scala di GOV.UK Frontend 6.0.0; pubblicata su design-system.service.gov.uk/styles/paragraphs/ · GOV.UK Design System (repository alphagov/govuk-design-system) · consultato il 12/10/2026 ([sorgente letto](https://github.com/alphagov/govuk-design-system/blob/main/src/styles/paragraphs/index.md))
- [WCAG 2.2 — Success Criterion 1.4.4 Resize Text](https://www.w3.org/TR/WCAG22/#resize-text) — testo del criterio, livello AA (pubblicato su www.w3.org/TR/WCAG22/#resize-text) · W3C, Accessibility Guidelines Working Group (repository w3c/wcag) · WCAG 2.2, ultima pubblicazione 12/12/2024; sorgente consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/resize-text.html))
- [WCAG 2.2 — definizione «large scale (text)»](https://www.w3.org/TR/WCAG22/) — almeno 18 pt o 14 pt in grassetto; nota sui caratteri a tratto molto sottile (pubblicata su www.w3.org/TR/WCAG22/#dfn-large-scale) · W3C, Accessibility Guidelines Working Group (repository w3c/wcag) · WCAG 2.2, ultima pubblicazione 12/12/2024; sorgente consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/terms/20/large-scale.html))
- [Understanding Success Criterion 1.4.3: Contrast (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) — «Intent»: 14 pt e 18 pt equivalgono a circa 18,5 px e 24 px (pubblicato su www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html#intent) · W3C WAI (repository w3c/wcag) · consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/understanding/20/contrast-minimum.html))

### TIPO-INTERLINEA · Interlinea e spaziatura del testo che reggono gli override

**Regola.** I paragrafi hanno un'interlinea di almeno 1,5 (le classi text-p-\*), le etichette su una riga possono stare a 1,15; nessun contenitore di testo ha un'altezza fissa che tagli o sovrapponga il testo quando l'utente porta l'interlinea a 1,5, lo spazio dopo i paragrafi a 2, la spaziatura delle lettere a 0,12 e quella delle parole a 0,16 volte il corpo.

**Perché.** WCAG 1.4.12 (AA): nessuna perdita di contenuto o di funzione impostando un'interlinea di almeno 1,5 volte il corpo, uno spazio dopo i paragrafi di almeno 2 volte, una spaziatura delle lettere di almeno 0,12 volte e delle parole di almeno 0,16 volte. Understanding 1.4.12: i valori vengono dallo studio di McLeish sulla velocità di lettura in funzione della spaziatura delle lettere; i puntini di sospensione comparsi con la nuova spaziatura sono ammessi solo se il testo troncato resta leggibile in altro modo (per esempio al fuoco o all'attivazione); il testo tagliato o sovrapposto è un fallimento. WCAG 1.4.8 (AAA): interlinea di almeno uno spazio e mezzo nei paragrafi e spazio tra paragrafi di almeno 1,5 volte l'interlinea. web.dev: interlinea senza unità, perché segua il corpo; le righe corte sopportano un'interlinea maggiore, quelle lunghe con troppa interlinea fanno perdere la riga successiva. Apple: con tre o più righe evitare l'interlinea stretta, anche dove l'altezza è limitata.

**Soglie ed eccezioni.** WCAG 1.4.12 (AA): 1,5 / 2 / 0,12 / 0,16 volte il corpo; WCAG 1.4.8 (AAA): 1,5 e paragrafi a 1,5 volte l'interlinea.

**In DottorCloud.** frappe-ui: `text-base` ha interlinea 1,15 (una riga), `text-p-base` e `text-p-sm` 1,5: si usano le text-p-\* per tutto ciò che può andare a capo; min-h invece di un'altezza fissa sui contenitori di testo; `righeDelBlocco()` (utils/agenda.js) disegna nei blocchi dell'agenda solo righe intere da 16 px; AGENTS.md: una frase va a capo invece di fermarsi a metà, un nome si legge intero e i suoi chip vanno sotto.

**Come si verifica.** Bookmarklet o foglio di stile utente con i valori di 1.4.12 su ogni schermata (fallimento F104: testo tagliato o sovrapposto); axe `avoid-inline-spacing`; controllo a 280 px di larghezza.

**Errori da evitare.** (studio UX, ottobre 2026) «Proposta/Preventivo» va a capo a metà parola nell'imbuto della dashboard; menu a tendina troppo stretti tagliano il valore senza puntini («Come il centro (Italianc»); il titolo del certificato si ferma a «non a…» e nasconde l'informazione che conta (non agonistica); date spezzate a metà («fino al 23 / nov»).

**Vedi anche.** [WCAG-1.4.12](02-wcag-percepibile-e-robusto.md#wcag-1412--spaziatura-del-testo-modificabile-senza-perdite)

**Fonti.**

- [WCAG 2.2 — Success Criterion 1.4.12 Text Spacing](https://www.w3.org/TR/WCAG22/#text-spacing) — testo del criterio, livello AA (pubblicato su www.w3.org/TR/WCAG22/#text-spacing) · W3C, Accessibility Guidelines Working Group (repository w3c/wcag) · WCAG 2.2, ultima pubblicazione 12/12/2024; sorgente consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/21/text-spacing.html))
- [WCAG 2.2 — Success Criterion 1.4.8 Visual Presentation](https://www.w3.org/TR/WCAG22/#visual-presentation) — testo del criterio, livello AAA: interlinea e spazio tra paragrafi (pubblicato su www.w3.org/TR/WCAG22/#visual-presentation) · W3C, Accessibility Guidelines Working Group (repository w3c/wcag) · WCAG 2.2, ultima pubblicazione 12/12/2024; sorgente consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/visual-presentation.html))
- [Understanding Success Criterion 1.4.12: Text Spacing](https://www.w3.org/WAI/WCAG22/Understanding/text-spacing.html) — «Intent» → «Use of ellipses» ed «Effects of Not Allowing for Spacing Override»; «Resources» → «Research» (studio di McLeish) (pubblicato su www.w3.org/WAI/WCAG22/Understanding/text-spacing.html) · W3C WAI (repository w3c/wcag) · consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/understanding/21/text-spacing.html))
- [F104: Failure of Success Criterion 1.4.12 due to clipped or overlapped content when text spacing is adjusted](https://www.w3.org/WAI/WCAG22/Techniques/failures/F104) — «Description» e «Tests» (procedura di prova) · W3C WAI (repository w3c/wcag) · consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/techniques/failures/F104.html))
- [Typography (Learn Design)](https://github.com/GoogleChrome/web.dev/blob/main/src/site/content/en/learn/design/typography/index.md) — «Line height»: valori senza unità; righe corte e interlinea; pubblicata su web.dev/learn/design/typography · Google, web.dev (Jeremy Keith; repository GoogleChrome/web.dev) · 2021
- [Typography (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/typography#Using-system-fonts) — «Using system fonts»: «If you need to display three or more lines of text, avoid tight leading» (dati JSON della pagina) · Apple · aggiornata il 16/12/2025, consultata il 12/10/2026

### TIPO-FORMA · Allineamento, maiuscole, enfasi e cifre

**Regola.** Il testo è allineato a sinistra e mai giustificato; le maiuscole solo come iniziale di frase; il grassetto solo per parole chiave; il sottolineato solo per i link; i numeri in colonna con cifre tabulari, allineati a destra e con gli stessi decimali; un testo che non entra va a capo, e se proprio si tronca ha i puntini e il testo intero raggiungibile.

**Perché.** Designers Italia (Linguaggio, «Formatta il testo in modo coerente e accessibile»): allineare sempre a sinistra, perché un testo giustificato è molto difficile da leggere; i testi in maiuscolo sono difficili da leggere, quindi il maiuscolo solo per la prima lettera della frase; il grassetto solo per le parole chiave, non per frasi intere; niente sottolineato se non è un link; preferire le cifre per i dati; giorni della settimana e mesi in minuscolo. WCAG 1.4.8 (AAA): testo non giustificato; Understanding 1.4.8: la spaziatura irregolare del testo giustificato crea «fiumi di bianco» e rende difficile trovare i confini delle parole. Understanding 1.4.12: i puntini sono ammessi solo se il testo troncato si può leggere in altro modo. Apple (Typography): con il testo grande ridurre al minimo i troncamenti.

**In DottorCloud.** `tabular-nums` di Tailwind (la classe `tabular` del design system) e `dc-metric` (font-variant-numeric: tabular-nums) per importi, orari e numeri in colonna; colonne numeriche allineate a destra; AGENTS.md: il nome si legge intero (`max-w-full truncate` solo come ultima risorsa) e i chip vanno a capo (`flex-wrap`); il `text-tiny` maiuscolo previsto da Espresso per le etichette di sezione resta per poche etichette di gruppo e mai per i dati; date italiane in minuscolo («mar 20 ott»).

**Come si verifica.** Grep di `text-justify`, `uppercase` e `capitalize` nei componenti; revisione delle colonne numeriche (allineamento e decimali); prova a 280 px di larghezza; elenco dei testi troncati e verifica che il testo intero sia leggibile.

**Errori da evitare.** (studio UX, ottobre 2026) Titoli di sezione in maiuscolo nelle automazioni («FILTRI DELL'EVENTO», «ATTIVAZIONE»); date con le maiuscole («Dom 4 Ott») per la classe capitalize; i numeri delle colonne Fasi e Trattative allineati a sinistra; il nome dell'azienda nel titolo tagliato senza puntini; un numero che va a capo staccato dal suo nome; testi d'aiuto telegrafici con simboli e grassetti.

**Fonti.**

- [Linguaggio (Design system, Fondamenti)](https://designers.italia.it/design-system/fondamenti/linguaggio/) — «Formatta il testo in modo coerente e accessibile»: Corsivo, Grassetto, Testo sottolineato, Allineamento, Uso delle maiuscole, Numeri, Date; pubblicata su designers.italia.it/design-system/fondamenti/linguaggio/ · Designers Italia (repository italia/designers.italia.it) · consultato il 12/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/linguaggio.yaml))
- [Understanding Success Criterion 1.4.8: Visual Presentation](https://www.w3.org/WAI/WCAG22/Understanding/visual-presentation.html) — «Intent»: testo giustificato e «rivers of white» (pubblicato su www.w3.org/WAI/WCAG22/Understanding/visual-presentation.html#intent) · W3C WAI (repository w3c/wcag) · consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/understanding/20/visual-presentation.html))
- [Understanding Success Criterion 1.4.12: Text Spacing](https://www.w3.org/WAI/WCAG22/Understanding/text-spacing.html) — «Intent» → «Use of ellipses» (pubblicato su www.w3.org/WAI/WCAG22/Understanding/text-spacing.html) · W3C WAI (repository w3c/wcag) · consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/understanding/21/text-spacing.html))
- [Typography (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/typography#Supporting-Dynamic-Type) — «Supporting Dynamic Type»: «Keep text truncation to a minimum as font size increases» (dati JSON della pagina) · Apple · aggiornata il 16/12/2025, consultata il 12/10/2026

### SPAZIO-GRIGLIA · Spaziatura su una scala di 4 px

**Regola.** Spazi, margini e dimensioni usano solo i passi della scala (4, 8, 12, 16, 24, 32, 40, 48 px) attraverso token o classi Tailwind, con spazi più ampi tra le sezioni che dentro un gruppo; le pagine sorelle condividono margini e allineamenti, e i token semantici prevalgono sui valori sparsi.

**Perché.** Designers Italia (Spaziature): le spaziature organizzano il layout, danno respiro e coerenza; si definisce una gerarchia con spazi più ampi tra le sezioni di una pagina e più stretti dentro una sezione o un componente; i token globali non si usano direttamente ma attraverso token semantici di spazio verticale (stack), orizzontale (inline) e interno (inset). Design Tokens Italia (il pacchetto dei token del design system .italia): la linea di base è di 4 px e le spaziature sono suoi multipli, da 4 a 96 px; la scala nominale va da 3xs (4 px) a xxl (48 px). Designers Italia (Tipografia): linea di base di 4 px, ogni spazio è un suo multiplo. GOV.UK: una scala di spaziatura reattiva, più ampia sopra i 640 px, e interlinee multiple di 5 px, per un ritmo verticale coerente che rende le pagine più facili da scorrere e leggere; il CSS usa unità relative. Apple (Layout): l'allineamento rende ordinato, aiuta a seguire il contenuto e dice che gli elementi sono correlati.

**Soglie ed eccezioni.** Passo di 4 px (Designers Italia, Design Tokens Italia, Espresso); Espresso da `--space-0-5` (2 px) a `--space-8` (32 px); controlli da 24, 28, 32 e 40 px.

**In DottorCloud.** Espresso (tokens.css): `--space-1` 4 px, `--space-2` 8, `--space-3` 12, `--space-4` 16, `--space-6` 24, `--space-8` 32; Tailwind a passi di 4 px (p-1 = 4 px); controlli `control-xs` 24, `control-sm` 28, `control-md` 32, `control-lg` 40; `SettingsRow.vue` (py-3, px-2, gap-x-4, gap-y-2) come riga standard delle impostazioni; niente valori arbitrari come p-[13px].

**Come si verifica.** Grep delle classi arbitrarie in px e dei margini fuori scala; in Playwright confrontare le coordinate x dei contenuti tra pagine sorelle (lo studio misurava 472 contro 480 px); screenshot con una griglia di 4 px sovrapposta.

**Errori da evitare.** (studio UX, ottobre 2026) In «Lingua e fuso orario» le righe rientrano di 8 px sul computer e di 16 px sul telefono rispetto alle pagine sorelle; in Promemoria, Lista d'attesa e Area pazienti il riquadro grigio parte a x=472 mentre titoli di sezione e interruttori partono a 480 e finiscono a 1192 invece di 1200; sul telefono l'interruttore delle pagine sorelle non è allineato al contenuto.

**Vedi anche.** [GS-PROSSIMITA](#gs-prossimita--legge-di-prossimità-la-distanza-dice-che-cosa-va-insieme)

**Fonti.**

- [Spaziature (Design system, Fondamenti)](https://designers.italia.it/design-system/fondamenti/spaziature/) — «A cosa servono»; «Come usarle»; «I token per le spaziature» (globali e semantici); pubblicata su designers.italia.it/design-system/fondamenti/spaziature/ · Designers Italia (repository italia/designers.italia.it) · consultato il 12/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/spaziature.yaml))
- [Design Tokens Italia — variables.css](https://github.com/italia/design-tokens-italia/blob/main/dist/css/variables.css) — --it-spacing-1x (4 px, «Dimensione baseline») … --it-spacing-24x (96 px); scala --it-spacing-3xs (4 px) … --it-spacing-xxl (48 px) e --it-spacing-3xl (96 px) · Dipartimento per la trasformazione digitale, design-tokens-italia 1.3.3 (repository italia/design-tokens-italia) · consultato il 12/10/2026
- [Tipografia (Design system, Fondamenti)](https://designers.italia.it/design-system/fondamenti/tipografia/) — «Consigli d'uso» → «Ritmo verticale»: linea di base di 4 px; pubblicata su designers.italia.it/design-system/fondamenti/tipografia/ · Designers Italia (repository italia/designers.italia.it) · consultato il 12/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/tipografia.yaml))
- [Spacing](https://design-system.service.gov.uk/styles/spacing/) — «Responsive spacing» (scala, soglia dei 640 px) e «Static spacing»; pubblicata su design-system.service.gov.uk/styles/spacing/ · GOV.UK Design System (repository alphagov/govuk-design-system) · consultato il 12/10/2026 ([sorgente letto](https://github.com/alphagov/govuk-design-system/blob/main/src/styles/spacing/index.md))
- [Type scale](https://design-system.service.gov.uk/styles/type-scale/) — «How it works»: interlinee a multipli di 5 px, ritmo verticale, unità relative; pubblicata su design-system.service.gov.uk/styles/type-scale/ · GOV.UK Design System (repository alphagov/govuk-design-system) · consultato il 12/10/2026 ([sorgente letto](https://github.com/alphagov/govuk-design-system/blob/main/src/styles/type-scale/index.md))
- [Layout (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/layout#Visual-hierarchy) — «Visual hierarchy»: «Align elements to make them easier to scan» (dati JSON della pagina) · Apple · aggiornata il 9/9/2026, consultata il 12/10/2026

### COL-RUOLI · Il colore ha un ruolo e un solo significato

**Regola.** Ogni colore ha un ruolo fisso e lo stesso colore non dice due cose: il verde acqua del marchio è l'azione e il marchio, gli accenti cat-\* il tipo di cosa, success/warning/danger/info come sta; la palette resta piccola e ogni colore arriva da un token con un ruolo, mai da un esadecimale scritto nel componente.

**Perché.** Apple (Color): non usare lo stesso colore per significati diversi, soprattutto per stato e interattività; i colori devono funzionare in chiaro, in scuro e con il contrasto aumentato; non fissare i valori dei colori di sistema e non ridefinire il significato dei colori dinamici; il significato dei colori cambia tra culture (il rosso è pericolo in alcune, positivo in altre). Android (Color): usare i colori con un significato e una palette limitata — troppi colori semantici confondono, troppi decorativi sopraffanno; ripetere i modelli di colore stabiliti; assegnare i colori con token che dicono il ruolo, invece di valori fissi. Designers Italia (Colori): ogni colore ha un ruolo e una funzione (il primario per l'azione, i neutri per supporto e sfondi); i colori si applicano con parsimonia, perché creano la gerarchia e non sono decorazione. GOV.UK (Colour): i colori funzionali si usano per lo scopo per cui sono pensati e non se ne copiano gli esadecimali.

**Soglie ed eccezioni.** Espresso: 4 famiglie di stato (green, amber, red, blue) più 5 categorie (cat-blue, cat-violet, cat-amber, cat-rose, cat-green).

**In DottorCloud.** I token di tokens.css ed espresso.css: `--brand-action` (marchio.css) e `--brand-solid` per ciò con cui si agisce; `--brand-subtle` per righe scelte e azioni per la persona; `--brand` solo come segno (3,07:1 sul bianco: mai per il testo); `--brand-segno` per l'avanzamento; `--cat-*` con le varianti -subtle e -text per i tipi; `COLORI_DEGLI_STATI` (utils/agenda.js) per gli stati degli appuntamenti; AGENTS.md: un nuovo segno del marchio va in espresso.css per tutti gli schermi, mai come colori di una sola schermata.

**Come si verifica.** Grep di esadecimali e di classi come bg-[#…] nei file .vue; tabella colore → significato per tutto il prodotto (un colore con due significati è un difetto); revisione dei chip di stato tra le pagine.

**Errori da evitare.** (studio UX, ottobre 2026) Il chip «Prova» di «Nuova fattura» rosso come un errore, mentre nella pagina sotto lo stesso stato è un riquadro ambra; i pallini delle colonne del kanban colorati per posizione («Fatto» rosso come la priorità «Alta»); nel calendario dei post un puntino rosso con due significati; «Niente SdI» in rosso per una condizione normale; il tema scelto segnato in grigio scuro invece che nel colore delle scelte (in ThemeSwitcher.vue è ancora così).

**Fonti.**

- [Color (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/color#Best-practices) — «Best practices»; «Inclusive color»; «System colors» (dati JSON della pagina) · Apple · aggiornata il 16/12/2025, consultata il 12/10/2026
- [Color (Mobile design guides)](https://developer.android.com/design/ui/mobile/guides/styles/color#takeaways) — «Takeaways»: palette limitata, schemi di colore ripetuti, schema chiaro e scuro, token di ruolo · Google, Android Developers · aggiornata il 12/12/2024, consultata il 12/10/2026
- [Colori (Design system, Fondamenti)](https://designers.italia.it/design-system/fondamenti/colori/) — «Principi» → «Rispetta i ruoli» e «Applica con parsimonia»; pubblicata su designers.italia.it/design-system/fondamenti/colori/ · Designers Italia (repository italia/designers.italia.it) · consultato il 12/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/colori.yaml))
- [Colour](https://design-system.service.gov.uk/styles/colour/) — «Functional colours»: «Do not copy the specific hexadecimal (hex) colour values»; pubblicata su design-system.service.gov.uk/styles/colour/ · GOV.UK Design System (repository alphagov/govuk-design-system) · consultato il 12/10/2026 ([sorgente letto](https://github.com/alphagov/govuk-design-system/blob/main/src/styles/colour/index.md))

### COL-NON-SOLO · Mai il colore da solo

**Regola.** Nessuna informazione, azione, richiesta o distinzione dipende solo dal colore: stati, errori, appuntamenti, campi obbligatori, serie dei grafici e link hanno anche testo, icona, forma, motivo o posizione; i link nel testo sono sottolineati, oppure hanno almeno 3:1 di contrasto con il testo vicino e un altro segnale.

**Perché.** WCAG 1.4.1 (A): il colore non è l'unico mezzo visivo per dare un'informazione, indicare un'azione, sollecitare una risposta o distinguere un elemento. Understanding 1.4.1: due colori che differiscono anche per luminosità con un rapporto di almeno 3:1 contano come distinzione in più, ma se bisogna riconoscere un colore preciso (il verde di un campo valido, il rosso di uno sbagliato) serve un altro indicatore, qualunque sia il contrasto. Tecnica G183: un link distinto dal testo vicino solo dal colore deve avere almeno 3:1 di contrasto con quel testo; resta consigliato un altro segno, come la sottolineatura. USWDS: secondo i dati NIH l'insensibilità ai colori riguarda circa lo 0,5% delle donne e l'8% degli uomini adulti; il colore va usato solo come miglioramento progressivo. web.dev: circa 300 milioni di persone sono daltoniche; molti grafici e tabelle usano solo il colore, e serve un altro identificatore (motivo, testo, icona); rivedere i prodotti in scala di grigi aiuta a trovare i problemi. Apple: le coppie rosso-verde e blu-arancio sono difficili per chi è daltonico, servono forme o icone. Android: più di un segnale visivo per azioni come i link. Espresso (principio 5): gli stati hanno sempre una parola o un'icona.

**Soglie ed eccezioni.** WCAG 1.4.1, livello A; una differenza di luminosità di almeno 3:1 come segnale in più (Understanding 1.4.1 e G183), ma non basta quando si deve riconoscere un colore preciso.

**In DottorCloud.** `segniDelBlocco()` (utils/agenda.js) dà a ogni stato dell'appuntamento icona e parole; AGENTS.md: un segno è un'icona con le sue parole, mai un colore da solo; i campi obbligatori hanno la croce `segno-obbligatorio` (una forma) oltre al colore; le ore chiuse dell'agenda sono a righe diagonali (`dc-agenda-chiuso`); le variazioni dei numeri hanno freccia, segno e confronto in parole («contro 109 prima»).

**Come si verifica.** axe `link-in-text-block`; simulazione di deuteranopia, protanopia e acromatopsia (Chrome DevTools, Rendering) e scala di grigi su ogni schermata con stati, legende e grafici; checklist: per ogni colore che significa qualcosa, qual è il secondo segnale?

**Errori da evitare.** (studio UX, ottobre 2026) Nel mese dell'agenda il servizio si legge solo dalla barretta colorata, senza legenda; nel Social Planner rete e stato del post solo dal colore, con la legenda nascosta sotto i 640 px (`hidden … sm:flex` in SocialPlanner.vue: ancora così); nel grafico «Andamento delle vendite» le tre linee si distinguono solo dal colore; le caselle della griglia dei servizi senza legenda.

**Vedi anche.** [WCAG-1.4.1](02-wcag-percepibile-e-robusto.md#wcag-141--il-colore-non-è-mai-lunico-segno)

**Fonti.**

- [WCAG 2.2 — Success Criterion 1.4.1 Use of Color](https://www.w3.org/TR/WCAG22/#use-of-color) — testo del criterio, livello A (pubblicato su www.w3.org/TR/WCAG22/#use-of-color) · W3C, Accessibility Guidelines Working Group (repository w3c/wcag) · WCAG 2.2, ultima pubblicazione 12/12/2024; sorgente consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/use-of-color.html))
- [Understanding Success Criterion 1.4.1: Use of Color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html) — «Intent»: luminosità a 3:1 e riconoscimento di un colore preciso (pubblicato su www.w3.org/WAI/WCAG22/Understanding/use-of-color.html#intent) · W3C WAI (repository w3c/wcag) · consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/understanding/20/use-of-color.html))
- [G183: Using a contrast ratio of at least 3:1 to distinguish inline text links from surrounding text](https://www.w3.org/WAI/WCAG22/Techniques/general/G183) — «Description» e «Tests» (pubblicata su www.w3.org/WAI/WCAG22/Techniques/general/G183) · W3C WAI (repository w3c/wcag) · consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/techniques/general/G183.html))
- [Using color (U.S. Web Design System)](https://designsystem.digital.gov/design-tokens/color/overview/) — «Color and accessibility» (0,5% delle donne e 8% degli uomini adulti, dati NIH); «General color guidance»; pubblicata su designsystem.digital.gov/design-tokens/color/overview/ · U.S. General Services Administration, USWDS (repository uswds/uswds-site) · consultato il 12/10/2026 ([sorgente letto](https://github.com/uswds/uswds-site/blob/main/pages/design-tokens/color/overview.md))
- [Color and contrast (Learn Accessibility)](https://github.com/GoogleChrome/web.dev/blob/main/src/site/content/en/learn/accessibility/color-contrast/index.md) — introduzione (300 milioni di persone daltoniche) e «Using color» (motivo, testo o icona; scala di grigi); pubblicata su web.dev/learn/accessibility/color-contrast · Google, web.dev (Carie Fisher; repository GoogleChrome/web.dev) · 2022
- [Accessibility (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/accessibility#Vision) — «Vision»: «Convey information with more than color alone» (dati JSON della pagina) · Apple · aggiornata il 9/6/2025, consultata il 12/10/2026
- [Accessibility (Mobile design guides)](https://developer.android.com/design/ui/mobile/guides/foundations/accessibility#design-vision) — «Design for vision»: «Use more than one visual affordance for actions like links» · Google, Android Developers · aggiornata l'8/5/2023, consultata il 12/10/2026

### COL-TESTO · Contrasto del testo, nei due temi

**Regola.** Ogni testo — compresi segnaposto, testi mostrati al passaggio o al fuoco, parole su blocchi colorati e su fondi di stato — ha almeno 4,5:1 sul suo sfondo reale (3:1 se grande), in tema chiaro e scuro, calcolato sui token senza arrotondare; per il testo piccolo e critico si punta a 7:1 dove si può.

**Perché.** WCAG 1.4.3 (AA): almeno 4,5:1, 3:1 per il testo grande; esclusi i componenti inattivi, la decorazione e i loghi. Understanding 1.4.3: 3:1 è il minimo raccomandato da ISO 9241-3 e ANSI/HFES 100 per la visione normale; 4,5:1 compensa la perdita di sensibilità al contrasto che accompagna un'acuità di 20/40 (3 × 1,5), mentre per 20/80 serve circa 7:1 (WCAG 1.4.6, AAA); le soglie non si arrotondano (4,499:1 non raggiunge 4,5:1); il criterio vale anche per il testo segnaposto e per quello mostrato al passaggio del puntatore o al fuoco; un contrasto insufficiente per regole del marchio non è esentato, salvo i loghi. Apple (Dark Mode): contrasto mai sotto 4,5:1 e, per i colori personalizzati, l'obiettivo di 7:1, soprattutto nel testo piccolo; Apple (Accessibility): verificare il contrasto minimo nei due aspetti, chiaro e scuro. Android: testo almeno 4,5:1 sul fondo.

**Soglie ed eccezioni.** AA: 4,5:1 per il testo normale, 3:1 per il grande (almeno 24 px, o circa 18,5 px in grassetto); AAA (1.4.6): 7:1 e 4,5:1; nessun arrotondamento.

**In DottorCloud.** Espresso: `ink-gray-5` (#6a716f) per le etichette, circa 5:1 sul bianco (4,99:1) e 4,51:1 su `surface-gray-2` (#f1f4f3); espresso.css (sezioni 3 e 3b) ridefinisce rossi, ambra, verdi, blu, ciano e teal ad almeno 4,6:1 su bianco, grigio della barra laterale, grigio dei campi e i loro fondi tenui, e il tema scuro ha valori propri; AGENTS.md: il testo non usa mai gli inchiostri più chiari (ink-\*-4) e un avviso prende il settimo passo; i testi secondari del blocco della prima visita al 90% di `on-brand-solid`; il controllo dei token in brand/dottorcloud/design-system/espresso/controllo-contrasti.txt (81 colori, 0 fallimenti).

**Come si verifica.** axe `color-contrast` in tema chiaro e scuro (Playwright con colorScheme light e dark, come lo script dello studio); `color-contrast-enhanced` (AAA, disattivata di default) per i testi piccoli critici; calcolo delle coppie di token con la formula WCAG della luminanza relativa; prova dello schermo al sole.

**Errori da evitare.** (studio UX, ottobre 2026) I testi d'esempio dei campi tra 2,5 e 2,8:1: `ink-gray-4` (#959b99) è a 2,83:1 sul bianco e 2,56:1 su #f1f4f3 (calcolato il 12/10/2026), e il README di Espresso assegna proprio questo grigio ai segnaposto, che però sono testo e ricadono in 1.4.3; in /prenota i nomi dei passi #999 su #f7f7f7 a 2,65:1; all'accesso le etichette #7c7c7c a 4,17:1; gli orari dei blocchi della prima visita a 4,48:1 (corretto); il grigio delle etichette sul fondo che un campo prende al passaggio del mouse, circa 4,3:1 (ancora da decidere); dopo la correzione sistemica gli elementi sotto soglia sono scesi da 242 a 3.

**Vedi anche.** [WCAG-1.4.3](02-wcag-percepibile-e-robusto.md#wcag-143--testo-leggibile-451-31-se-grande-in-ogni-stato-e-in-entrambi-i-temi), [CONTRASTO-APCA](02-wcag-percepibile-e-robusto.md#contrasto-apca--apca-solo-come-informazione-mai-come-prova-di-conformità)

**Fonti.**

- [WCAG 2.2 — Success Criterion 1.4.3 Contrast (Minimum)](https://www.w3.org/TR/WCAG22/#contrast-minimum) — testo del criterio, livello AA, con le eccezioni (pubblicato su www.w3.org/TR/WCAG22/#contrast-minimum) · W3C, Accessibility Guidelines Working Group (repository w3c/wcag) · WCAG 2.2, ultima pubblicazione 12/12/2024; sorgente consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/contrast-minimum.html))
- [WCAG 2.2 — Success Criterion 1.4.6 Contrast (Enhanced)](https://www.w3.org/TR/WCAG22/#contrast-enhanced) — testo del criterio, livello AAA: 7:1 e 4,5:1 (pubblicato su www.w3.org/TR/WCAG22/#contrast-enhanced) · W3C, Accessibility Guidelines Working Group (repository w3c/wcag) · WCAG 2.2, ultima pubblicazione 12/12/2024; sorgente consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/contrast-enhanced.html))
- [WCAG 2.2 — definizione «contrast ratio»](https://www.w3.org/TR/WCAG22/) — (L1 + 0,05) / (L2 + 0,05); fondo bianco se non specificato (pubblicata su www.w3.org/TR/WCAG22/#dfn-contrast-ratio) · W3C, Accessibility Guidelines Working Group (repository w3c/wcag) · WCAG 2.2, ultima pubblicazione 12/12/2024; sorgente consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/terms/20/contrast-ratio.html))
- [Understanding Success Criterion 1.4.3: Contrast (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) — «Intent» (soglie non arrotondate, segnaposto e testo al passaggio o al fuoco, regole del marchio) e «Rationale for the Ratios Chosen» (pubblicato su www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html#intent) · W3C WAI (repository w3c/wcag) · consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/understanding/20/contrast-minimum.html))
- [Dark Mode (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/dark-mode#Dark-Mode-colors) — «Dark Mode colors»: «no lower than 4.5:1»; «strive for a contrast ratio of 7:1, especially in small text» (dati JSON della pagina) · Apple · aggiornata il 6/8/2024, consultata il 12/10/2026
- [Accessibility (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/accessibility#Vision) — «Vision»: tabella dei contrasti minimi; verificare il contrasto in chiaro e in scuro (dati JSON della pagina) · Apple · aggiornata il 9/6/2025, consultata il 12/10/2026
- [Accessibility (Mobile design guides)](https://developer.android.com/design/ui/mobile/guides/foundations/accessibility#design-vision) — «Design for vision»: testo almeno 4,5:1 · Google, Android Developers · aggiornata l'8/5/2023, consultata il 12/10/2026
- [axe-core Rule Descriptions](https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md) — color-contrast (WCAG 2.0 AA); color-contrast-enhanced (WCAG 2.x AAA, disattivata di default) · Deque Systems (repository dequelabs/axe-core) · regole 4.14, ramo develop, consultato il 12/10/2026

### COL-NONTESTO · Contrasto di controlli, stati e segni grafici: 3:1

**Regola.** Tutto ciò che serve a vedere un controllo e il suo stato — il bordo di un campo che non ha altro segno, il binario dell'interruttore spento, la spunta, l'anello di fuoco, un'icona che significa qualcosa, le linee e le aree dei grafici — ha almeno 3:1 rispetto ai colori adiacenti, in entrambi i temi.

**Perché.** WCAG 1.4.11 (AA): almeno 3:1 contro i colori adiacenti per l'informazione visiva necessaria a identificare i componenti e i loro stati (esclusi quelli inattivi e quelli disegnati dallo user agent) e per le parti di un grafico necessarie a capirlo. Understanding 1.4.11: un controllo con testo visibile non ha bisogno di bordo, ma se il confine è l'unico segno della sua presenza deve avere 3:1; ogni controllo ha comunque bisogno di un indicatore di fuoco che contrasti con ciò che lo circonda; le linee di un grafico devono avere 3:1 sul loro fondo, e le fette di una torta vanno distinte tra loro; le soglie non si arrotondano (2,999:1 non raggiunge 3:1); i grafici non sono «necessari a capire» se i valori sono anche in testo o in una tabella. Tecnica G207: 3:1 per le icone necessarie a capire. Tecnica G209: dove due colori adiacenti hanno meno di 3:1 si aggiunge un bordo con almeno 3:1 rispetto a ciascuno. Android: 3:1 tra superfici ed elementi non testuali.

**Soglie ed eccezioni.** 3:1 (AA); esenti i componenti inattivi e quelli dello user agent non modificati; nessun arrotondamento.

**In DottorCloud.** espresso.css, sezione 6b: il binario dell'interruttore spento è #858c8a (3,43:1 sul bianco) e #757c7a nel tema scuro (4,19:1 sulla superficie #151817); l'anello di fuoco `--focus-outline-default` è di 2 px #0e8a7c (4,25:1 sul bianco), menta #5fe0cc nel tema scuro; la sezione 25 dà lo stesso colore ai controlli che disegnano un anello proprio; `--brand` #12a594 (3,07:1) solo per segni non testuali; i campi che stanno su un fondo simile al loro hanno un bordo outline-gray-\*.

**Come si verifica.** axe non misura il contrasto non testuale: campionare i colori con il contagocce e calcolare il rapporto; percorso con il tasto Tab su ogni pagina nei due temi; prova «trova il campo» su uno schermo luminoso; per i grafici, calcolo di ogni colore della palette contro la superficie della carta.

**Errori da evitare.** (studio UX, ottobre 2026) L'interruttore spento a 1,29:1 (corretto a 3:1 e oltre); i campi #f1f4f3 senza bordo su bianco a 1,11:1 e il campo email dell'area su #f6f9f8 a 1,04:1 (gravità 3); l'anello di fuoco grigio a 1,7:1 e il bordo della riga attiva a 2,8:1 (corretti); nei dati di prova la spunta #6bbf96 su #e4faeb, circa 2:1. Calcolato il 12/10/2026 con la formula WCAG: nella PALETTE chiara dei grafici (utils/dashboardCharts.js, che il commento dice «validata» anche sul contrasto) il verde #1baf7a, il rosa #e87ba4 e l'ambra #eda100 stavano a circa 2,8:1, 2,7:1 e 2,2:1 sul bianco della carta (corretti il 12/10/2026: 3:1 e oltre); nel tema scuro tutti gli otto colori superano 3:1 su #1d201f.

**Vedi anche.** [WCAG-1.4.11](02-wcag-percepibile-e-robusto.md#wcag-1411--controlli-stati-fuoco-icone-e-grafici-a-31)

**Fonti.**

- [WCAG 2.2 — Success Criterion 1.4.11 Non-text Contrast](https://www.w3.org/TR/WCAG22/#non-text-contrast) — testo del criterio, livello AA (pubblicato su www.w3.org/TR/WCAG22/#non-text-contrast) · W3C, Accessibility Guidelines Working Group (repository w3c/wcag) · WCAG 2.2, ultima pubblicazione 12/12/2024; sorgente consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/21/non-text-contrast.html))
- [Understanding Success Criterion 1.4.11: Non-text Contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html) — «Intent» (2,999:1); «User Interface Components» → «Boundaries», «Relationship with Focus Visible»; «Graphical Objects» → «Required for understanding» (pubblicato su www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html#graphical-objects) · W3C WAI (repository w3c/wcag) · consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/understanding/21/non-text-contrast.html))
- [G207: Ensuring that a contrast ratio of 3:1 is provided for icons](https://www.w3.org/WAI/WCAG22/Techniques/general/G207) — «Description» e «Tests» · W3C WAI (repository w3c/wcag) · consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/techniques/general/G207.html))
- [G209: Provide sufficient contrast at the boundaries between adjoining colors](https://www.w3.org/WAI/WCAG22/Techniques/general/G209) — «Description»; esempi con i grafici a torta e la mappa · W3C WAI (repository w3c/wcag) · consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/techniques/general/G209.html))
- [Accessibility (Mobile design guides)](https://developer.android.com/design/ui/mobile/guides/foundations/accessibility#design-vision) — «Design for vision»: «Use a 3:1 ratio between surfaces and non-text elements» · Google, Android Developers · aggiornata l'8/5/2023, consultata il 12/10/2026

### COL-TEMI · Tema chiaro e scuro: un token per tema, verificato nei due

**Regola.** Ogni colore è un token con un valore per il tema chiaro e uno per lo scuro, e ogni coppia testo/sfondo si verifica in entrambi; nel tema scuro si usano grigi scuri (non il nero) e superfici più chiare per ciò che sta sopra; il tema parte dalla scelta del sistema finché la persona non sceglie Chiaro o Scuro.

**Perché.** Apple (Dark Mode): le persone scelgono spesso il tema scuro come predefinito e si aspettano che le app rispettino la loro scelta; i colori del tema scuro non sono semplici inversioni di quelli chiari; usare colori che si adattano all'aspetto corrente, non valori fissi; contrasto mai sotto 4,5:1 e, per i colori personalizzati, l'obiettivo di 7:1; provare la leggibilità nei due aspetti, anche con Aumenta contrasto e Riduci trasparenza; su iOS le interfacce in primo piano usano colori elevati, più chiari della base. Sulla scelta nell'app le due guide divergono: Apple sconsiglia un'impostazione dell'aspetto propria dell'app, che costringe a cambiarne due e fa sembrare l'app rotta se non segue il sistema; Android consiglia di offrire Chiaro, Scuro e Predefinito di sistema, quest'ultimo come scelta predefinita; entrambe partono dalla scelta del sistema. Apple (Color): fornire per ogni colore personalizzato una variante chiara e una scura, più una con contrasto aumentato. Material Components (Dark theme): fondo e superfici del tema scuro sono grigio scuro invece che nero, per vedere le ombre e ridurre l'affaticamento con il testo chiaro; le ombre funzionano meno sul fondo scuro, quindi le superfici più elevate diventano più chiare (oggi con i colori tonali delle superfici).

**Soglie ed eccezioni.** Apple: almeno 4,5:1, obiettivo 7:1 per i colori personalizzati; WCAG uguale nei due temi.

**In DottorCloud.** tokens.css ed espresso.css: i blocchi `:root[data-marchio='dottorcloud']` e `[data-theme='dark']`; la superficie scura #151817 con il bianco a 17,87:1 e `ink-gray-9` (#f6f9f8) a 16,87:1; `surface-elevation-1` #1d201f e `-2` #222524, più chiari della base; AGENTS.md: un token impostato per il chiaro va anche nel blocco scuro, perché `:root[data-marchio]` pesa più di `[data-theme=dark]`, e una cornice dentro la pagina (l'iframe di un'email) dichiara color-scheme: dark nel tema scuro; `ThemeSwitcher.vue` offre Chiaro, Scuro e Sistema; l'area pazienti segue il telefono (utils/temaDelTelefono.js).

**Come si verifica.** Script che confronta i nomi delle variabili del blocco chiaro e di quello scuro (ogni token chiaro ha il suo scuro); Playwright con colorScheme dark più axe `color-contrast`; prova con Aumenta contrasto su macOS e iOS; immagini e loghi controllati su fondo scuro.

**Errori da evitare.** Revisioni dello studio (studio UX, ottobre 2026): blu, ciano e teal scuriti per arrivare a 4,5:1 sul bianco scendevano a 2:1 nel tema scuro, anche nel testo dei badge blu (corretti con valori propri). Verificato nel codice il 12/10/2026: App.vue imposta «light» quando non c'è una preferenza salvata, quindi chi ha il sistema in scuro vede il gestionale chiaro finché non sceglie, mentre Apple e Android partono dalla scelta del sistema.

**Fonti.**

- [Dark Mode (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/dark-mode#Best-practices) — introduzione; «Best practices» (niente impostazione dell'aspetto propria dell'app; prove nei due aspetti); «Dark Mode colors»; «iOS, iPadOS» (colori base ed elevati) (dati JSON della pagina) · Apple · aggiornata il 6/8/2024, consultata il 12/10/2026
- [Color (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/color#Best-practices) — «Best practices»: colori che funzionano in chiaro, in scuro e con contrasto aumentato (dati JSON della pagina) · Apple · aggiornata il 16/12/2025, consultata il 12/10/2026
- [Implement dark theme](https://developer.android.com/develop/ui/views/theming/darktheme#change-themes) — «Change themes in-app»: Light, Dark, System default («the recommended default option») · Google, Android Developers · aggiornata l'1/10/2026, consultata il 12/10/2026
- [Dark theme (Material Components for Android)](https://github.com/material-components/material-components-android/blob/master/docs/theming/Dark.md) — «Color palette» (grigio scuro invece del nero); «Elevation overlays» (superfici più chiare in alto; sostituiti dai colori tonali) · Google, Material Components (repository material-components/material-components-android) · consultato il 12/10/2026

### ICO-ETICHETTE · Icone con parole, coerenti e con un nome

**Regola.** Un'icona accompagna una parola visibile; da sola solo se il simbolo è chiaro e non ambiguo, e sempre con un nome accessibile; un concetto ha una sola icona e un'icona un solo concetto; tutte della stessa famiglia, dimensione e tratto, e con almeno 3:1 se portano un significato.

**Perché.** Apple (Icons): un'icona efficace esprime un solo concetto in modo immediatamente comprensibile; un design semplice e familiare, con metafore legate all'azione o al contenuto; la stessa dimensione, lo stesso dettaglio, lo stesso tratto e la stessa prospettiva per tutte; un peso uguale a quello del testo vicino; un'alternativa testuale per le icone personalizzate. Apple (Buttons): usare il testo quando una breve etichetta comunica meglio di un'icona. Designers Italia (Icone): usarle solo quando è strettamente necessario e in modo coerente; abbinarle a un'etichetta di testo che ne chiarisce la funzione; da sole solo se il simbolo è chiaro e non ambiguo, con l'etichetta comunque leggibile dal lettore di schermo; testare con gli utenti la riconoscibilità. NN/g (euristica 4): alcune icone sono convenzioni esterne, come la lente per la ricerca. WCAG 1.1.1 (A): ogni controllo ha un nome che ne descrive lo scopo; WCAG 2.5.3 (A): il nome contiene il testo visibile; WCAG 1.4.11 e la tecnica G207: 3:1 per le icone necessarie a capire.

**Soglie ed eccezioni.** 3:1 per le icone che portano un significato; Lucide da 16 px con tratto 1,5–2 (Espresso).

**In DottorCloud.** Lucide come in frappe-ui, 16 px, nel colore del testo (README di Espresso, «Iconografia»); `Icon.vue` e utils/icone.js disegnano un'icona per nome, `ScegliIcona.vue` serve solo a sceglierla; AGENTS.md: a frappe-ui si danno nomi Feather (crm/fcrm/feather_icons.json) o lucide-…, altrimenti appare un cerchio vuoto; un pulsante solo icona ha `:aria-label`, un tooltip non è un nome e al tocco non si apre (utils/puntatore.js); la croce del marchio non è `lucide-plus`.

**Come si verifica.** axe `button-name`, `link-name`, `svg-img-alt` e `role-img-alt`; prova di riconoscimento delle icone senza etichetta con cinque persone; inventario icona → significato su tutto il prodotto.

**Errori da evitare.** (studio UX, ottobre 2026) «Segna tutte come lette» è solo una doppia spunta, la stessa icona che in agenda vuol dire «Completato»; lo stato degli appuntamenti affidato a icone di circa 10 px, con le parole solo nel tooltip; il «+» in basso crea una cosa diversa in ogni pagina e non lo dice; un'icona persona isolata a fine riga porta altrove; «⋯», «↗» e «›» attaccati; sul telefono filtri della Chat e canale di scrittura solo con icone, così l'email alla persona e la nota interna si confondono.

**Vedi anche.** [UX-ICONE](01-interazione.md#ux-icone--icone-con-le-loro-parole)

**Fonti.**

- [Icons (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/icons#Best-practices) — introduzione e «Best practices» (semplicità, coerenza, peso del testo vicino, testo alternativo) (dati JSON della pagina) · Apple · aggiornata il 9/6/2025, consultata il 12/10/2026
- [Buttons (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/buttons#Content) — «Content»: «Consider using text when a short label communicates more clearly than an icon» (dati JSON della pagina) · Apple · aggiornata il 16/12/2025, consultata il 12/10/2026
- [Icone (Design system, Fondamenti)](https://designers.italia.it/design-system/fondamenti/icone/) — «A cosa servono» e «Come usarle»; pubblicata su designers.italia.it/design-system/fondamenti/icone/ · Designers Italia (repository italia/designers.italia.it) · consultato il 12/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/icone.yaml))
- [Maintain Consistency and Adhere to Standards (Usability Heuristic #4)](https://www.nngroup.com/articles/consistency-and-standards/) — coerenza esterna: la lente per la ricerca (via WebSearch) · Nielsen Norman Group · consultato il 12/10/2026
- [WCAG 2.2 — Success Criterion 1.1.1 Non-text Content](https://www.w3.org/TR/WCAG22/#non-text-content) — testo del criterio, livello A, caso «Controls, Input» (pubblicato su www.w3.org/TR/WCAG22/#non-text-content) · W3C, Accessibility Guidelines Working Group (repository w3c/wcag) · WCAG 2.2, ultima pubblicazione 12/12/2024; sorgente consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/non-text-content.html))
- [WCAG 2.2 — Success Criterion 2.5.3 Label in Name](https://www.w3.org/TR/WCAG22/#label-in-name) — testo del criterio, livello A (pubblicato su www.w3.org/TR/WCAG22/#label-in-name) · W3C, Accessibility Guidelines Working Group (repository w3c/wcag) · WCAG 2.2, ultima pubblicazione 12/12/2024; sorgente consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/21/label-in-name.html))
- [G207: Ensuring that a contrast ratio of 3:1 is provided for icons](https://www.w3.org/WAI/WCAG22/Techniques/general/G207) — «Description» e «Tests» · W3C WAI (repository w3c/wcag) · consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/techniques/general/G207.html))

### MOT-SCOPO · Movimento con uno scopo, breve e coerente

**Regola.** Si anima solo per dare un riscontro, mostrare un cambio di stato o una relazione nello spazio (da dove viene un foglio, dove va un elemento); le microinterazioni (pulsanti, interruttori, dissolvenze) stanno sotto i 150 ms, finestre, fogli e toast tra 200 e 300 ms, le grandi espansioni intorno ai 400 ms; la durata cresce con l'area e il percorso, si decelera in entrata e si accelera in uscita; più un'animazione è frequente, più è breve e sobria, e nessuno aspetta un'animazione per agire.

**Perché.** Apple (Motion): aggiungere movimento con uno scopo, mai per il gusto di farlo, perché un'animazione gratuita o eccessiva distrae e può mettere a disagio; non usarlo come unico modo per comunicare qualcosa di importante; riscontri brevi e precisi; evitare il movimento nelle interazioni frequenti; lasciare che le persone lo interrompano, senza farle aspettare la fine. Material Components (Motion): sette curve e 16 durate da 50 a 1000 ms; la durata cresce con l'area e il percorso dell'animazione; la curva standard cubic-bezier(0.2, 0, 0, 1) per ciò che comincia e finisce sullo schermo, (0, 0, 0, 1) per ciò che entra, (0.3, 0, 1, 1) per ciò che esce. Carbon (IBM): 70 ms per pulsanti e interruttori, 110 ms per le dissolvenze, 150 ms per piccole espansioni e brevi spostamenti, 240 ms per espansioni, comunicazioni di sistema e toast, 400 ms per grandi espansioni e notifiche importanti, 700 ms per oscurare lo sfondo; la durata dipende dallo stile e dalla dimensione del movimento.

**Soglie ed eccezioni.** Material 50–1000 ms; Carbon 70–700 ms; Espresso 120–300 ms.

**In DottorCloud.** Espresso: curve da 120 a 300 ms; l'interruttore in 100 ms, con la croce che entra con un piccolo rimbalzo in 160 ms (cubic-bezier(.34, 1.56, .64, 1)); telefono.css: i fogli salgono in 260 ms (cubic-bezier(0.2, 0.8, 0.2, 1)) e scendono in 180 ms, menu e liste in 220 ms; il pannello delle notifiche in 200 ms con cubic-bezier(0.2, 0, 0, 1), la curva standard di Material; i grafici ECharts con `animationDuration: 400`.

**Come si verifica.** Grep di duration-, transition, animation e dei millisecondi in CSS e Vue, confrontati con la scala; registrazione a 60 fps di aperture e chiusure; prova: si può toccare o scrivere mentre l'animazione è in corso?

**Errori da evitare.** Revisioni dello studio (studio UX, ottobre 2026): il «+» si nascondeva scorrendo anche quando a scorrere era il foglio che lui stesso apriva, e sopra una lista corta non tornava più (corretto). I rimbalzi (curve con valori oltre 1) vanno riservati a segni piccoli come la croce dell'interruttore, mai a pannelli o fogli.

**Fonti.**

- [Motion (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/motion#Best-practices) — «Best practices» e «Providing feedback» (dati JSON della pagina) · Apple · aggiornata il 9/9/2025, consultata il 12/10/2026
- [Motion (Material Components for Android)](https://github.com/material-components/material-components-android/blob/master/docs/theming/Motion.md) — «Curves (easing & duration)»: sette curve, 16 durate da 50 a 1000 ms; la durata cresce con area e percorso · Google, Material Components (repository material-components/material-components-android) · consultato il 12/10/2026
- [Motion overview (Carbon Design System)](https://carbondesignsystem.com/elements/motion/overview/) — «Duration» → «Duration tokens»; pubblicata su carbondesignsystem.com/elements/motion/overview/ · IBM, Carbon Design System (repository carbon-design-system/carbon-website) · consultato il 12/10/2026 ([sorgente letto](https://github.com/carbon-design-system/carbon-website/blob/main/src/pages/elements/motion/overview.mdx))

### MOT-RIDOTTO · Rispettare «riduci movimento»

**Regola.** Con prefers-reduced-motion: reduce si tolgono, o si sostituiscono con dissolvenze, spostamenti, ingrandimenti, rimbalzi, parallasse e scorrimenti animati, in CSS e in JavaScript (grafici, scorrimento fluido); l'informazione che il movimento portava resta, in forma statica.

**Perché.** WCAG 2.3.3 (AAA): l'animazione di movimento attivata da un'interazione si può disattivare, salvo sia essenziale alla funzione o all'informazione. Understanding 2.3.3: elementi che si muovono mentre si scorre e la parallasse possono scatenare disturbi vestibolari (vertigini, nausea, emicrania, fino al bisogno di stare a letto); si può usare l'impostazione di riduzione del movimento dello user agent o del sistema. Tecniche C39 (CSS) e SCR40 (JavaScript): disattivare con prefers-reduced-motion le animazioni attivate dalle interazioni. Media Queries 5: reduce indica che l'utente preferisce un'interfaccia che toglie o sostituisce le animazioni di movimento che danno disagio a chi ha sensibilità vestibolare o distraggono chi ha deficit di attenzione; la nota cita lo scorrimento fluido tra ciò che la preferenza può spegnere. web.dev: entro i 40 anni oltre il 35% degli adulti ha avuto una qualche disfunzione vestibolare. MDN: ingrandire o spostare oggetti grandi può scatenare disturbi; l'esempio sostituisce il movimento con una dissolvenza. Apple: con Riduci movimento si riducono le animazioni automatiche e ripetitive (zoom, scala, movimento periferico), si stringono le molle per togliere i rimbalzi e si sostituiscono le transizioni sugli assi con dissolvenze.

**Soglie ed eccezioni.** WCAG 2.3.3, livello AAA: DottorCloud lo rispetta in tutte le schermate.

**In DottorCloud.** Già presente: espresso.css toglie la transizione dell'interruttore; telefono.css toglie l'animazione dei fogli delle finestre (`.dialog-content`); espresso-componenti.css ferma il caricamento (`dc-respiro`) e l'anello `dc-segnato`; Notifications.vue tiene solo una dissolvenza di 120 ms; PulsanteAggiungi.vue e MobileLead.vue usano motion-reduce:transition-none, ConversationList.vue motion-safe:; il README di Espresso: con prefers-reduced-motion restano solo le dissolvenze. Per ECharts (versione 5.6) si imposta `animation: false` quando matchMedia('(prefers-reduced-motion: reduce)') è vero.

**Come si verifica.** Attivare la preferenza (macOS e iOS: Riduci movimento; Android 9+: Rimuovi animazioni; Windows 11: Effetti di animazione; Firefox: ui.prefersReducedMotion = 1) o emularla in Playwright (page.emulateMedia con reducedMotion: 'reduce'); procedura di C39 e SCR40 per ogni animazione attivata da un'interazione (è essenziale? è soppressa?); grep di animation e transition senza guardia.

**Errori da evitare.** Verificato nel codice il 12/10/2026: in telefono.css la riduzione del movimento ferma solo i fogli delle finestre, mentre menu, liste di scelta e popover a foglio salgono ancora dal basso con `dc-foglio-su` (220 ms); in TwilioCallUI.vue l'animazione `.pulse` (scala da 0,5 a 1,3, 1 s, infinita) non aveva guardia (corretto il 12/10/2026, anche in TelnyxCallUI.vue); non ne ha nemmeno lo scheletro di caricamento di /prenota (crm/www/prenota.html, `animation: sh 1.2s infinite`); i grafici (`animationDuration: 400` in dashboardCharts.js e il resize animato di EChart.vue) si animano comunque; con la riduzione `.dc-segnato` perde anche l'anello, così chi riduce il movimento non vede quale messaggio la notifica ha aperto: un anello fermo per qualche secondo non è movimento.

**Vedi anche.** [WCAG-2.3.3](03-wcag-utilizzabile-e-comprensibile.md#wcag-233--le-animazioni-causate-da-un-gesto-si-possono-spegnere-233-aaa-obiettivo)

**Fonti.**

- [WCAG 2.2 — Success Criterion 2.3.3 Animation from Interactions](https://www.w3.org/TR/WCAG22/#animation-from-interactions) — testo del criterio, livello AAA (pubblicato su www.w3.org/TR/WCAG22/#animation-from-interactions) · W3C, Accessibility Guidelines Working Group (repository w3c/wcag) · WCAG 2.2, ultima pubblicazione 12/12/2024; sorgente consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/21/animation-from-interactions.html))
- [Understanding Success Criterion 2.3.3: Animation from Interactions](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html) — «Intent» (disturbi vestibolari, parallasse, preferenza del sistema); «Examples» (pubblicato su www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html#intent) · W3C WAI (repository w3c/wcag) · consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/understanding/21/animation-from-interactions.html))
- [C39: Using the CSS prefers-reduced-motion query to prevent motion](https://www.w3.org/WAI/WCAG22/Techniques/css/C39) — «Examples» e «Tests» · W3C WAI (repository w3c/wcag) · consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/techniques/css/C39.html))
- [SCR40: Using the CSS prefers-reduced-motion query in JavaScript to prevent motion](https://www.w3.org/WAI/WCAG22/Techniques/client-side-script/SCR40) — «Examples» (matchMedia) e «Tests» · W3C WAI (repository w3c/wcag) · consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/techniques/client-side-script/SCR40.html))
- [Media Queries Level 5](https://drafts.csswg.org/mediaqueries-5/) — § «Detecting the desire for less motion on the page: the prefers-reduced-motion feature» (valore reduce) e la nota sullo scorrimento fluido; pubblicata su www.w3.org/TR/mediaqueries-5/#prefers-reduced-motion · W3C, CSS Working Group (repository w3c/csswg-drafts), Working Draft · 2026 (data del sorgente 19/2/2026), consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/csswg-drafts/blob/main/mediaqueries-5/Overview.bs))
- [prefers-reduced-motion CSS media feature](https://developer.mozilla.org/en-US/docs/web/css/reference/at-rules/@media/prefers-reduced-motion) — introduzione; «User preferences»; «Examples» (la dissolvenza al posto della scala); pubblicata su developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion · MDN Web Docs (repository mdn/content) · consultato il 12/10/2026 ([sorgente letto](https://github.com/mdn/content/blob/main/files/en-us/web/css/reference/at-rules/@media/prefers-reduced-motion/index.md))
- [Animation and motion (Learn Accessibility)](https://github.com/GoogleChrome/web.dev/blob/main/src/site/content/en/learn/accessibility/motion/index.md) — introduzione (oltre il 35% degli adulti entro i 40 anni) e «Use media queries»; pubblicata su web.dev/learn/accessibility/motion · Google, web.dev (Carie Fisher; repository GoogleChrome/web.dev) · 2022
- [Accessibility (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/accessibility#Cognitive) — «Cognitive»: «Be cautious with fast-moving and blinking animations» e le pratiche per ridurre il movimento (dati JSON della pagina) · Apple · aggiornata il 9/6/2025, consultata il 12/10/2026

### MOT-AUTOMATICO · Movimento automatico, lampeggi, aggiornamenti e messaggi a tempo

**Regola.** Nulla lampeggia più di tre volte al secondo; ciò che si muove, lampeggia o scorre da solo per più di 5 secondi accanto ad altro contenuto si può mettere in pausa, fermare o nascondere, e ciò che si aggiorna da solo anche regolarne la frequenza, salvo sia essenziale; gli indicatori di attesa durano solo quanto l'attesa e ogni animazione infinita è legata a uno stato che finisce; un messaggio che porta un'azione (Annulla) non sparisce a tempo.

**Perché.** WCAG 2.2.2 (A): per il contenuto in movimento, lampeggiante o che scorre, che parte da solo, dura più di cinque secondi ed è presentato insieme ad altro, c'è un modo per metterlo in pausa, fermarlo o nasconderlo; per quello che si aggiorna da solo anche per regolarne la frequenza; un'animazione di precaricamento può essere essenziale se nel frattempo nessuno può interagire e senza di essa la pagina sembrerebbe bloccata. WCAG 2.3.1 (A): niente che lampeggi più di tre volte in un secondo, oppure i lampeggi restano sotto le soglie generale e del rosso (l'area dei lampeggi contemporanei entro il 25% di un campo visivo di 10°, stimato con un rettangolo di 341×256 px su uno schermo a 1024×768). WCAG 2.2.1 (A): ogni limite di tempo si può spegnere, regolare o estendere, salvo le eccezioni. web.dev: si stima che il 3% delle persone con epilessia sia fotosensibile; il contenuto con lampeggi o rapide transizioni tra chiaro e scuro va analizzato con PEAT. Apple: cautela con le animazioni veloci e lampeggianti, che distraggono, danno vertigini e in alcuni casi possono causare crisi epilettiche; ridurre al minimo gli elementi che si chiudono da soli a tempo e preferire una chiusura con un'azione esplicita.

**Soglie ed eccezioni.** WCAG 2.2.2 (A): 5 s; WCAG 2.3.1 (A): 3 lampeggi al secondo, 25% di un campo di 10° (341×256 px a 1024×768); WCAG 2.2.1 (A).

**In DottorCloud.** `LoaderMark` (la croce che ruota e respira) solo durante un caricamento; gli aggiornamenti in tempo reale (socket) non spostano il contenuto sotto il dito o il cursore; niente blink né marquee; il toast che porta «Annulla» resta finché la persona non agisce o lo chiude; niente transizioni rapide tra chiaro e scuro a tutto schermo.

**Come si verifica.** axe `blink` e `marquee`; grep di infinite in CSS e Vue, verificando che ogni animazione infinita finisca con il suo stato; analisi con PEAT per video o transizioni rapide; conteggio dei lampeggi in una registrazione; prova del toast con «Annulla»: resta abbastanza a lungo per chi legge lentamente?

**Errori da evitare.** Verificato nel codice il 12/10/2026: animazioni infinite — `.pulse` delle chiamate in TwilioCallUI.vue (fermo con la riduzione del movimento dalla correzione del 12/10/2026), lo scheletro di /prenota, `dc-respiro` del caricamento — da legare al loro stato e alla riduzione del movimento. (studio UX, ottobre 2026) Una cosa segnata fatta per sbaglio si recupera solo per pochi secondi, poi il toast con «Annulla» sparisce.

**Vedi anche.** [WCAG-2.2.2](03-wcag-utilizzabile-e-comprensibile.md#wcag-222--pausa-stop-nascondi-per-ciò-che-si-muove-o-si-aggiorna-222-a), [WCAG-2.3.1](03-wcag-utilizzabile-e-comprensibile.md#wcag-231--non-più-di-tre-lampeggiamenti-al-secondo-231-a)

**Fonti.**

- [WCAG 2.2 — Success Criterion 2.2.2 Pause, Stop, Hide](https://www.w3.org/TR/WCAG22/#pause-stop-hide) — testo del criterio, livello A, e nota sul precaricamento (pubblicato su www.w3.org/TR/WCAG22/#pause-stop-hide) · W3C, Accessibility Guidelines Working Group (repository w3c/wcag) · WCAG 2.2, ultima pubblicazione 12/12/2024; sorgente consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/pause-stop-hide.html))
- [WCAG 2.2 — Success Criterion 2.3.1 Three Flashes or Below Threshold](https://www.w3.org/TR/WCAG22/#three-flashes-or-below-threshold) — testo del criterio, livello A (pubblicato su www.w3.org/TR/WCAG22/#three-flashes-or-below-threshold) · W3C, Accessibility Guidelines Working Group (repository w3c/wcag) · WCAG 2.2, ultima pubblicazione 12/12/2024; sorgente consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/three-flashes-or-below-threshold.html))
- [WCAG 2.2 — definizione «general flash and red flash thresholds»](https://www.w3.org/TR/WCAG22/) — 25% di un campo visivo di 10°; rettangolo di 341 × 256 px a 1024 × 768 (pubblicata su www.w3.org/TR/WCAG22/#dfn-general-flash-and-red-flash-thresholds) · W3C, Accessibility Guidelines Working Group (repository w3c/wcag) · WCAG 2.2, ultima pubblicazione 12/12/2024; sorgente consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/terms/20/general-flash-and-red-flash-thresholds.html))
- [WCAG 2.2 — Success Criterion 2.2.1 Timing Adjustable](https://www.w3.org/TR/WCAG22/#timing-adjustable) — testo del criterio, livello A, con le eccezioni (pubblicato su www.w3.org/TR/WCAG22/#timing-adjustable) · W3C, Accessibility Guidelines Working Group (repository w3c/wcag) · WCAG 2.2, ultima pubblicazione 12/12/2024; sorgente consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/timing-adjustable.html))
- [Animation and motion (Learn Accessibility)](https://github.com/GoogleChrome/web.dev/blob/main/src/site/content/en/learn/accessibility/motion/index.md) — «Flashing and moving content» (3% delle persone con epilessia, PEAT) e «Pause, stop, or hide movement»; pubblicata su web.dev/learn/accessibility/motion · Google, web.dev (Carie Fisher; repository GoogleChrome/web.dev) · 2022
- [Accessibility (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/accessibility#Cognitive) — «Cognitive»: animazioni veloci e lampeggianti; «Minimize use of time-boxed interface elements» (dati JSON della pagina) · Apple · aggiornata il 9/6/2025, consultata il 12/10/2026

### DATI-SEGNI · Grafici: serie distinguibili senza colore e segni a 3:1

**Regola.** In ogni grafico le serie si distinguono anche senza vedere i colori — forma dei marcatori, tratteggio, motivo, etichette dirette alla fine delle linee o sulle barre — e la legenda usa gli stessi segni; linee, barre e aree necessarie a capire hanno almeno 3:1 sul fondo, e le aree contigue sono separate da un bordo.

**Perché.** WCAG 1.4.1 (A) e tecnica G111: quando differenze di colore portano informazioni in un contenuto non testuale si aggiungono motivi che dicono la stessa cosa; per esempio un grafico a barre con un colore e un motivo per ogni regione e la legenda con gli stessi, o una mappa con le fermate di ogni linea segnate da forme diverse. Understanding 1.4.11: le linee di un grafico sono oggetti grafici e devono avere 3:1 sul loro fondo; per capire una torta bisogna distinguere le sue fette; se i valori sono anche in testo o in una tabella, i segni non sono più necessari a capire. Tecnica G209: dove colori adiacenti hanno meno di 3:1 si aggiunge un bordo con almeno 3:1 rispetto a ciascuno. Apple (Charts): non affidarsi al solo colore per distinguere i dati, ma usare forme o motivi diversi (l'app Salute usa due forme per i due valori della pressione) e separatori tra i segmenti impilati. web.dev: molti grafici usano solo il colore; serve un altro identificatore, come un motivo, un testo o un'icona.

**Soglie ed eccezioni.** 3:1 per linee, barre e aree necessarie a capire (WCAG 1.4.11); bordo di almeno 3:1 tra aree contigue sotto 3:1 (G209).

**In DottorCloud.** frontend/src/utils/dashboardCharts.js: oggi ogni linea ha `symbol: 'circle'` e il tratteggio solo se `item.dashed`; va dato a ogni posto della PALETTE anche una forma (circle, rect, triangle, diamond) e un tipo di linea, più un'etichetta diretta sull'ultimo punto. Il tooltip (`key()`) disegna già linea, tratteggio e barra, ma la legenda di ECharts usa pallini (`icon: 'circle'`) o quadratini: va data a ogni serie l'icona del suo tratto. Le barre impilate hanno un bordo nel colore della carta (`SURFACE`), da verificare a 3:1; per i motivi sulle aree ECharts 5.6 offre `aria.decal`.

**Come si verifica.** Simulazione di deuteranopia, protanopia e acromatopsia e scala di grigi su ogni grafico; un test unitario in frontend/tests/unit/dashboard.test.js (che già prova dashboardCharts.js) che calcola il contrasto di ogni colore della PALETTE su #ffffff e su #1d201f (almeno 3:1; c'è dal 12/10/2026); prova di lettura senza colori: «qual è la linea delle trattative vinte?».

**Errori da evitare.** (studio UX, ottobre 2026) In «Andamento delle vendite» tre linee sottili senza marcatori né tratteggi, con la legenda a pallini colorati, si incrociano di continuo e arancio e verde non si separano con la deuteranopia; i colori delle colonne del kanban assegnati per posizione. Calcolato il 12/10/2026 con la formula WCAG: nella PALETTE chiara il verde #1baf7a, il rosa #e87ba4 e l'ambra #eda100 stavano a circa 2,8:1, 2,7:1 e 2,2:1 sul bianco (corretti il 12/10/2026: 3:1 e oltre), e l'arancio #eb6834 e il verde #1baf7a a circa 1,1:1 tra loro.

**Vedi anche.** [WCAG-1.4.1](02-wcag-percepibile-e-robusto.md#wcag-141--il-colore-non-è-mai-lunico-segno)

**Fonti.**

- [G111: Using color and pattern](https://www.w3.org/WAI/WCAG22/Techniques/general/G111) — «Description» ed «Examples» (grafico a barre con motivi e legenda; fermate di forme diverse) · W3C WAI (repository w3c/wcag) · consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/techniques/general/G111.html))
- [Understanding Success Criterion 1.4.11: Non-text Contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html) — «Graphical Objects»: il grafico a linee e la torta; «Required for understanding» (pubblicato su www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html#graphical-objects) · W3C WAI (repository w3c/wcag) · consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/understanding/21/non-text-contrast.html))
- [G209: Provide sufficient contrast at the boundaries between adjoining colors](https://www.w3.org/WAI/WCAG22/Techniques/general/G209) — «Description»; esempi con i grafici a torta · W3C WAI (repository w3c/wcag) · consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/techniques/general/G209.html))
- [Charts (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/charts#Color) — «Color»: non solo colore, forme e motivi, separatori tra aree contigue (dati JSON della pagina) · Apple · 2022 (pagina del 23/9/2022), consultata il 12/10/2026
- [Color and contrast (Learn Accessibility)](https://github.com/GoogleChrome/web.dev/blob/main/src/site/content/en/learn/accessibility/color-contrast/index.md) — «Using color»: grafici e tabelle, motivo, testo o icona; pubblicata su web.dev/learn/accessibility/color-contrast · Google, web.dev (Carie Fisher; repository GoogleChrome/web.dev) · 2022

### DATI-TESTO · Grafici: messaggio in parole, valori leggibili, tabella alternativa

**Regola.** Ogni grafico ha un titolo che dice che cosa misura e in quale periodo, una frase che ne riassume il messaggio, i valori chiave in testo (etichette o elenco) e un'alternativa testuale: un nome accessibile breve e i dati in una tabella raggiungibile da tastiera e lettore di schermo; nessuna informazione necessaria si rivela solo al passaggio del mouse.

**Perché.** WAI (Complex Images): grafici e diagrammi richiedono un'alternativa in due parti — una breve che li identifica e, se serve, dice dove si trova la descrizione lunga, e una lunga che rappresenta in testo le informazioni essenziali, anche con titoli, testo e una tabella; è buona pratica renderla disponibile a tutti e riassumere il grafico nel testo che lo accompagna. Apple (Charts): descrizioni che fanno capire che cosa fa il grafico prima di guardarlo; riassumere il messaggio principale; non richiedere un'interazione per rivelare informazioni critiche; etichette accessibili con valori reali e contesto, senza aggettivi soggettivi e con formati non ambigui («June 6» invece di «6/6»). Apple (Charting data): se basta fornire i dati, offrirli in un elenco o in una tabella da scorrere, cercare e ordinare; titoli, sottotitoli e annotazioni descrittive aiutano a capire. Understanding 1.4.11: se i valori sono in testo o in una tabella, i segni del grafico non sono più necessari a capire.

**In DottorCloud.** ChartWidget.vue: la ciambella ha già accanto l'elenco con valori e percentuali (da tenere); per linee e barre va aggiunto «Mostra i dati» con una tabella vera (intestazioni con scope), e il contenitore di EChart.vue va dotato di role=img e di un aria-label con la sintesi; ECharts 5.6 offre anche `aria.label` (una descrizione generata o scritta da noi), oggi non usato da dashboardCharts.js né da EChart.vue; i tooltip di ECharts non si raggiungono da tastiera né al tocco, quindi i valori stanno anche altrove; il periodo si scrive con le sue date (`periodLabel()` e `formatRange()` in utils/dashboard.js: «Ultimi 30 giorni», «11 set – 10 ott»).

**Come si verifica.** axe `role-img-alt` e `svg-img-alt`; lettura con VoiceOver e NVDA: si capisce il messaggio senza vedere il grafico? Navigazione da tastiera nella tabella dei dati; prova al tocco: nessun valore necessario solo in un tooltip.

**Errori da evitare.** (studio UX, ottobre 2026) La barra del «Tasso di vittoria» è un role=meter senza nome (axe `aria-meter-name`); nel mese i conteggi accanto ai giorni non hanno etichetta («28 … 21» si legge come un'altra data); le date sull'asse del grafico a 11 px; i numeri della dashboard che si contraddicono con quelli di Fatture.

**Vedi anche.** [WCAG-1.1.1](02-wcag-percepibile-e-robusto.md#wcag-111--alternative-testuali-immagini-icone-avatar-grafici)

**Fonti.**

- [Complex Images (Images Tutorial)](https://www.w3.org/WAI/tutorials/images/complex/) — introduzione (alternativa in due parti) e «Long descriptions» (renderle disponibili a tutti; riassumere nel testo); esempio con titoli, testo e tabella; pubblicata su www.w3.org/WAI/tutorials/images/complex/ · W3C WAI (repository w3c/wai-tutorials) · consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/wai-tutorials/blob/master/source/images/complex.html.erb.md))
- [Charts (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/charts#Descriptive-content) — «Descriptive content»; «Best practices» (nessuna interazione per le informazioni critiche); «Enhancing the accessibility of a chart» (dati JSON della pagina) · Apple · 2022 (pagina del 23/9/2022), consultata il 12/10/2026
- [Charting data (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/charting-data#Designing-effective-charts) — introduzione (elenco o tabella quando bastano i dati); «Designing effective charts» (testo descrittivo) (dati JSON della pagina) · Apple · 2022 (pagina del 23/9/2022), consultata il 12/10/2026
- [Understanding Success Criterion 1.4.11: Non-text Contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html) — «Required for understanding»: valori in testo o in una tabella (pubblicato su www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html#graphical-objects) · W3C WAI (repository w3c/wcag) · consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/understanding/21/non-text-contrast.html))

### DATI-TIPO · Grafici: il tipo comune e una sola enfasi

**Regola.** Si usano i tipi di grafico più comuni, scelti per il compito — barre per confrontare categorie o le parti di un tutto (con l'asse dei valori da zero), linee per l'andamento nel tempo, punti per la relazione tra due grandezze — con un solo asse dei valori per grafico e tacche dalla sequenza familiare; la ciambella solo con poche fette e con l'elenco dei valori; si mette in evidenza solo la serie che porta il messaggio.

**Perché.** Apple (Charting data): preferire i tipi di grafico comuni, come barre e linee, che le persone sanno già leggere; tenere il grafico semplice e lasciare scegliere quando vedere più dettagli, perché troppi dati lo rendono opprimente e nascondono le relazioni; mantenere coerenti i grafici che hanno lo stesso scopo e gli stessi dati. Apple (Charts): le barre servono a confrontare valori di categorie diverse o le proporzioni delle parti di un tutto, le linee a mostrare come i valori cambiano nel tempo, i punti a mostrare come due proprietà si relazionano; per le barre l'asse da zero permette di confrontarne le altezze; sequenze di tacche familiari (0, 5, 10); una gerarchia in cui i dati sono la cosa più evidente e descrizioni e assi danno il contesto senza fare concorrenza. USWDS: partire dal bianco e nero, costruire il messaggio con la gerarchia e poi introdurre il colore a sostegno di quel messaggio.

**In DottorCloud.** dashboardCharts.js già prevede un solo asse dei valori per grafico, colori in ordine fisso e mai ripetuti a ciclo, «il resto» di una ciambella in un neutro (`OTHER`) e una scala `SEQUENTIAL` di una sola tinta per le grandezze; nel catalogo dei widget (crm/dashboard/widgets) si scelgono barre o linee secondo il compito; la ciambella solo con poche fette e con l'elenco dei valori (ChartWidget.vue); i titoli nelle parole del centro (visite, incassi, pazienti nuovi).

**Come si verifica.** Revisione del catalogo: per ogni widget il compito (confronto, andamento, composizione, relazione) e il tipo scelto; prova con gli utenti: tempo e correttezza nel rispondere a una domanda tipo («quale servizio ha incassato di più a settembre?»).

**Errori da evitare.** (studio UX, ottobre 2026) L'«Imbuto della pipeline» mostra «Aperto 5 100%» e «Vinta 0 0%» accanto a numeri che dicono altro, senza dire di quale pipeline parla; tre linee sovrapposte che si incrociano di continuo; titoli in gergo commerciale e in inglese in un centro medico («Andamento delle vendite»).

**Fonti.**

- [Charting data (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/charting-data#Best-practices) — «Best practices» (grafico semplice, dettagli a richiesta); «Designing effective charts» (tipi comuni, coerenza) (dati JSON della pagina) · Apple · 2022 (pagina del 23/9/2022), consultata il 12/10/2026
- [Charts (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/charts#Marks) — «Marks»; «Axes» (asse da zero per le barre, sequenze di tacche familiari); «Best practices» (gerarchia visiva) (dati JSON della pagina) · Apple · 2022 (pagina del 23/9/2022), consultata il 12/10/2026
- [Using color (U.S. Web Design System)](https://designsystem.digital.gov/design-tokens/color/overview/) — «General color guidance»: «Start in black and white»; pubblicata su designsystem.digital.gov/design-tokens/color/overview/ · U.S. General Services Administration, USWDS (repository uswds/uswds-site) · consultato il 12/10/2026 ([sorgente letto](https://github.com/uswds/uswds-site/blob/main/pages/design-tokens/color/overview.md))
