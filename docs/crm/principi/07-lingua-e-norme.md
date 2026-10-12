# 7. Parole, lingua e norme

<!-- Copyright (c) 2026, NPM2 Solutions Srl and contributors -->

Una delle famiglie dei [principi di esperienza e interfaccia](../66-principi-di-esperienza.md) (doc 66): come leggerle, la lista di controllo per una schermata e come sono state verificate le fonti sono lì.

Questa famiglia raccoglie le regole sulle parole di DottorCloud: l'italiano dei microtesti, la tipografia e i formati italiani (date, ore, numeri, prezzi, recapiti), l'internazionalizzazione (frasi intere, plurali, lingua dichiarata, formati, fusi orari, nomi delle persone) e il quadro normativo che fissa l'obiettivo di accessibilità, WCAG 2.2 AA. In un gestionale sanitario le parole sono metà dell'interfaccia: un'etichetta in inglese, una sigla non sciolta, un «1 appuntamenti» o un prezzo scritto in due modi costano tempo alla segreteria e fiducia al paziente, e i criteri WCAG 2.4.6, 2.5.3, 3.1 e 3.2.4 le rendono verificabili. Le fonti sono state lette l'11/10/2026 e riaperte una per una il 12/10/2026 dai repository ufficiali (W3C, Unicode CLDR e ICU, MDN, Designers Italia, AgID) e dalle pagine di Apple. Normattiva, EUR-Lex e il sito di AgID non erano raggiungibili durante la ricerca: la Legge 4/2004 e il DL 76/2020 sono letti nei dati aperti del Senato della Repubblica (i testi in Akoma Ntoso che il Senato pubblica su GitHub), la direttiva (UE) 2019/882 nelle note del W3C che ne citano il testo. Ciò che non si è potuto aprire, come il decreto italiano che recepisce la direttiva e le linee guida AgID che ne derivano, non è citato: va letto sulle fonti ufficiali prima di parlarne a un cliente. I conteggi sul catalogo (crm/locale/it.po) e sul codice si riferiscono al commit 19cea4a dell'11/10/2026.

## I principi

- [LING-CHIARO · Italiano semplice, frasi attive e brevi](#ling-chiaro--italiano-semplice-frasi-attive-e-brevi)
- [LING-LEGGIBILITA · Leggibilità misurata e testi corti](#ling-leggibilita--leggibilità-misurata-e-testi-corti)
- [LING-VOCE · Il «tu», una voce sola, il tono del momento](#ling-voce--il-tu-una-voce-sola-il-tono-del-momento)
- [LING-AZIONI · Pulsanti e link dicono che cosa succede](#ling-azioni--pulsanti-e-link-dicono-che-cosa-succede)
- [LING-ERRORI · Un errore dice che cosa, perché e come rimediare](#ling-errori--un-errore-dice-che-cosa-perché-e-come-rimediare)
- [LING-CONFERME · Conferme che nominano l'azione e le conseguenze](#ling-conferme--conferme-che-nominano-lazione-e-le-conseguenze)
- [LING-ESITI-VUOTI · Successi e liste vuote che dicono che cosa succede ora](#ling-esiti-vuoti--successi-e-liste-vuote-che-dicono-che-cosa-succede-ora)
- [LING-AIUTI · Aiuti, segnaposto e scelte specifici](#ling-aiuti--aiuti-segnaposto-e-scelte-specifici)
- [LING-GLOSSARIO · Un termine per ogni concetto, in tutto il prodotto](#ling-glossario--un-termine-per-ogni-concetto-in-tutto-il-prodotto)
- [LING-SIGLE · Sigle sciolte alla prima occorrenza](#ling-sigle--sigle-sciolte-alla-prima-occorrenza)
- [LING-NORME · Prima la regola in parole, poi la norma](#ling-norme--prima-la-regola-in-parole-poi-la-norma)
- [LING-GERGO · Niente gergo, inglese, nomi di campo o codici](#ling-gergo--niente-gergo-inglese-nomi-di-campo-o-codici)
- [LING-GENERE · Linguaggio inclusivo di genere](#ling-genere--linguaggio-inclusivo-di-genere)
- [LING-ABILISMO · Niente verbi abilisti, prima la persona](#ling-abilismo--niente-verbi-abilisti-prima-la-persona)
- [LING-TITOLI · Titoli di pagina e intestazioni che dicono dove sei](#ling-titoli--titoli-di-pagina-e-intestazioni-che-dicono-dove-sei)
- [LING-NOME-ACCESSIBILE · Il nome per il lettore di schermo: in italiano e uguale a quello che si vede](#ling-nome-accessibile--il-nome-per-il-lettore-di-schermo-in-italiano-e-uguale-a-quello-che-si-vede)
- [TIPO-MAIUSCOLE · Maiuscola solo all'inizio, mesi e giorni minuscoli](#tipo-maiuscole--maiuscola-solo-allinizio-mesi-e-giorni-minuscoli)
- [TIPO-VIRGOLETTE-APOSTROFO · Virgolette basse, apostrofo e puntini tipografici](#tipo-virgolette-apostrofo--virgolette-basse-apostrofo-e-puntini-tipografici)
- [TIPO-DATE · Date all'italiana e mai ambigue](#tipo-date--date-allitaliana-e-mai-ambigue)
- [TIPO-ORE-DURATE · Ore a 24 ore, durate con le unità](#tipo-ore-durate--ore-a-24-ore-durate-con-le-unità)
- [TIPO-NUMERI · Numeri: cifre, virgola decimale, punto delle migliaia, una regola sola](#tipo-numeri--numeri-cifre-virgola-decimale-punto-delle-migliaia-una-regola-sola)
- [TIPO-VALUTA · Prezzi come li scrive chi legge: «65,00 €»](#tipo-valuta--prezzi-come-li-scrive-chi-legge-6500-)
- [TIPO-SPAZI-UNITA · Spazi che non si spezzano, unità del Sistema Internazionale](#tipo-spazi-unita--spazi-che-non-si-spezzano-unità-del-sistema-internazionale)
- [TIPO-RECAPITI · Telefoni, email e indirizzi leggibili e cliccabili](#tipo-recapiti--telefoni-email-e-indirizzi-leggibili-e-cliccabili)
- [I18N-FRASI-INTERE · Frasi intere, mai pezzi incollati](#i18n-frasi-intere--frasi-intere-mai-pezzi-incollati)
- [I18N-PLURALI · Plurali secondo CLDR: una frase per caso](#i18n-plurali--plurali-secondo-cldr-una-frase-per-caso)
- [I18N-LANG · La lingua dichiarata: della pagina e delle sue parti](#i18n-lang--la-lingua-dichiarata-della-pagina-e-delle-sue-parti)
- [I18N-FORMATI · Formati dalla lingua scelta dall'utente, non dal browser](#i18n-formati--formati-dalla-lingua-scelta-dallutente-non-dal-browser)
- [I18N-FUSO · L'ora del centro, e i giorni che non si spostano](#i18n-fuso--lora-del-centro-e-i-giorni-che-non-si-spostano)
- [I18N-RICERCA-ORDINE · Cercare e ordinare con le regole dell'italiano](#i18n-ricerca-ordine--cercare-e-ordinare-con-le-regole-dellitaliano)
- [I18N-ESPANSIONE · Spazio per l'italiano, più lungo dell'inglese](#i18n-espansione--spazio-per-litaliano-più-lungo-dellinglese)
- [I18N-NOMI · I nomi delle persone come li scrivono loro](#i18n-nomi--i-nomi-delle-persone-come-li-scrivono-loro)
- [I18N-CODICI-IN-PAROLE · Si salva il codice, si mostra la parola](#i18n-codici-in-parole--si-salva-il-codice-si-mostra-la-parola)
- [NORM-WCAG22 · Obiettivo WCAG 2.2 livello AA](#norm-wcag22--obiettivo-wcag-22-livello-aa)
- [NORM-STANCA · Legge Stanca: chi obbliga e che cosa chiede](#norm-stanca--legge-stanca-chi-obbliga-e-che-cosa-chiede)
- [NORM-EAA · European Accessibility Act: quali servizi, di chi l'obbligo](#norm-eaa--european-accessibility-act-quali-servizi-di-chi-lobbligo)
- [NORM-GDPR-CHIARO · Informative e consensi in linguaggio semplice e chiaro](#norm-gdpr-chiaro--informative-e-consensi-in-linguaggio-semplice-e-chiaro)

### LING-CHIARO · Italiano semplice, frasi attive e brevi

**Regola.** Ogni testo dell'interfaccia (etichette, aiuti, errori, email, pagine pubbliche, area pazienti) va dritto al punto: ordine soggetto-verbo-oggetto, verbi in forma attiva, nessuna nominalizzazione dove basta il verbo, nessuna doppia negazione, nessun burocratese o impersonale («si è deciso di procedere all'annullamento»). A parità di significato si sceglie il testo più corto.

**Perché.** Designers Italia: online «leggiamo in fretta e cerchiamo risposte immediate», quindi il linguaggio dei servizi digitali deve essere «chiaro, essenziale, mirato all'azione», con una sintassi semplice, forme verbali attive e senza nominalizzazioni (sì: «L'ente ha annullato la pratica»; no: «Si è deciso di procedere all'annullamento della pratica»). Nei microtesti chiede di evitare «il più possibile nominalizzazioni, negazioni e forme passive» e di ridurre il testo a parità di significato; nei contenuti ricorda che sullo schermo «consultiamo solo il 20-28% di una pagina». La sua «Guida alle parole della Pubblica Amministrazione» propone alternative più semplici ai termini burocratici (per esempio «offrire» o «fornire» un servizio invece di «erogarlo»). L'Understanding di WCAG 3.1.5 spiega che parole brevi e comuni e frasi brevi sono più facili da decodificare, in particolare per chi ha disturbi della lettura come la dislessia, e tra le risorse indica la norma ISO 24495-1:2023 sul linguaggio semplice (plain language). Apple (HIG, Writing): «If you can use fewer words, do so»; (Inclusion) un linguaggio semplice e inclusivo accoglie tutti e si traduce meglio.

**Soglie ed eccezioni.** Nessuna soglia numerica sulla frase nelle fonti consultate; i limiti di titoli, sommari, paragrafi e righe sono in LING-LEGGIBILITA.

**In DottorCloud.** Vale per ogni \_\_() del frontend, \_() del server, crm/locale/it.po, frontend/src/area/it.js, le email (crm/templates/emails, crm/posta), le description del menu delle impostazioni (frontend/src/utils/impostazioni.js) e dei DocType (una descrizione cambiata deve spostare il modified del JSON, altrimenti migrate tiene le parole vecchie). La voce è già nel doc 40 («La voce e le parole»: frasi brevi, niente «effettuare» e «si prega di», niente «con successo»; un errore dice cosa non è successo). Una descrizione dice l'effetto che la persona vede, mai il campo del database che cambia.

**Come si verifica.** In ogni PR: grep -nE 'effettu|si prega|procedere a|con successo' crm/locale/it.po frontend/src/area/it.js deve restare vuoto (all'11/10/2026 lo è); lettura ad alta voce di ogni frase nuova (Apple); confronto dell'indice Gulpease prima e dopo una riscrittura (LING-LEGGIBILITA); test di comprensione con persone del centro sulle pagine pubbliche e sull'area.

**Errori da evitare.** Studio UX (ottobre 2026): descrizioni contorte nelle impostazioni («La lingua in cui DottorCloud scrive per il centro - le email e le pagine che leggono i clienti, i documenti, gli schermi di chi non ne ha scelta una sua - e l'ora della sua agenda»; «chiede cosa sono qui ogni servizio, professionista e ambulatorio»); un effetto detto come un campo («Aggiorna la data di ultima modifica di persone e trattative» invece di «Porta in cima alle liste chi ha appena scritto»); aiuti senza soggetto («Di notte, dalle 21 alle 8, parte la mattina, o la sera prima…»; «I posti che si liberano si propongono da soli»); un simbolo al posto di una frase («Vuoto = il nome del tuo marchio (Centro Medico Aurora)» invece di «Se lo lasci vuoto, la pagina usa il nome del centro»).

**Fonti.**

- [Linguaggio (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/linguaggio/) — sezioni «Parlare la lingua delle persone per servizi più utili e accessibili» e «Linguaggio semplice e naturale» (pubblicato su designers.italia.it/design-system/fondamenti/linguaggio/) · Designers Italia · 2025 (file del 14/04/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/linguaggio.yaml))
- [Microtesti (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/microtesti/) — sezione «Usa un linguaggio semplice e conciso» · Designers Italia · 2025 (file del 14/04/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/microtesti.yaml))
- [Contenuti (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/contenuti/) — sezione «Progetta contenuti adatti alla consultazione su schermo» · Designers Italia · 2025 (file del 05/09/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/contenuti.yaml))
- [Guida alle parole della Pubblica Amministrazione](https://github.com/italia/writing-toolkit/blob/master/le-parole-della-pubblica-amministrazione/e.rst) — voce «erogare» (introduzione della guida in index.rst dello stesso repository; pubblicata su docs.italia.it/italia/designers-italia/writing-toolkit/) · Designers Italia · 2025 (file del 14/04/2025); consultato il 12/10/2026
- [Understanding Reading Level](https://www.w3.org/WAI/WCAG22/Understanding/reading-level.html) — Intent of Reading Level; Resources («ISO 24495-1:2023 – Plain language») (pubblicato su w3.org/WAI/WCAG22/Understanding/reading-level.html) · W3C WAI · consultato l'11/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/understanding/20/reading-level.html))
- [Writing (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/writing) — Getting started, «Be clear» (pubblicato su developer.apple.com/design/human-interface-guidelines/writing) · Apple · 2025 (ultima modifica 16/12/2025); consultato l'11/10/2026 ([sorgente letto](https://developer.apple.com/tutorials/data/design/human-interface-guidelines/writing.json))
- [Inclusion (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/inclusion) — Welcoming language (pubblicato su developer.apple.com/design/human-interface-guidelines/inclusion) · Apple · consultato l'11/10/2026 ([sorgente letto](https://developer.apple.com/tutorials/data/design/human-interface-guidelines/inclusion.json))

### LING-LEGGIBILITA · Leggibilità misurata e testi corti

**Regola.** I testi lunghi (descrizioni delle impostazioni, email, pagine pubbliche, consensi, aiuti di più righe) si misurano con l'indice Gulpease prima e dopo ogni riscrittura e puntano al livello della scuola secondaria di primo grado; i titoli stanno entro 70 caratteri, i sommari entro 160 caratteri e finiscono con il punto, i paragrafi hanno al massimo 5 frasi, le righe al massimo 75 caratteri.

**Perché.** Designers Italia raccomanda «test di leggibilità (tramite formula di Flesch-Vacca e l'indice Gulpease)» accanto a test di comprensione, cloze test e test d'uso; fissa titoli «in massimo 70 caratteri (inclusi spazi)», sommari che non superano i 160 caratteri e finiscono con il punto, «per aiutare le persone che usano tecnologie assistive», paragrafi di non più di 5 frasi, e ricorda che «il carico cognitivo aumenta ogni 100 parole»; la tipografia raccomanda «una lunghezza massima di 75 caratteri per riga». WCAG 3.1.5 (AAA) prende come soglia il livello di istruzione secondaria inferiore (7-9 anni di scuola): oltre serve un contenuto supplementare o una versione più semplice; l'Understanding porta l'esempio delle informazioni mediche per il pubblico. L'indice Gulpease è una formula di leggibilità per i testi in italiano: la libreria textstat lo calcola come 89 + 300 × frasi/parole − 10 × caratteri/parole, contando nei caratteri tutto ciò che non è spazio, punteggiatura compresa; più basso il valore, più istruzione serve per leggere il testo con facilità.

**Soglie ed eccezioni.** WCAG 3.1.5 (AAA): livello di istruzione secondaria inferiore, fino a 9 anni di scuola, esclusi nomi propri e titoli. Designers Italia: titolo ≤ 70 caratteri, sommario ≤ 160 caratteri con punto finale, paragrafo ≤ 5 frasi, riga ≤ 75 caratteri. Le fonti consultate non danno soglie Gulpease: l'indice si usa per confronto (un testo riscritto non deve scendere).

**In DottorCloud.** Descrizioni delle pagine delle impostazioni (SettingsHub, campo description in frontend/src/utils/impostazioni.js) e paragrafi delle pagine pubbliche (/prenota, /modulo, /lista-attesa, /documento, area): larghezza massima di lettura (max-w-prose, circa 65 caratteri) e dettagli lunghi dietro «Come funziona». I testi dei consensi spediti da DottorCloud (crm/moduli/registro.py) e le email ai pazienti sono i primi da misurare: li legge un paziente, spesso dal telefono.

**Come si verifica.** Script in sola lettura sul catalogo: per ogni msgstr di almeno 25 parole calcolare textstat.gulpease_index(testo) e allegare al PR la lista dei 30 valori più bassi; misura dei caratteri per riga delle descrizioni a 1280 px; controllo che i sommari finiscano con il punto.

**Errori da evitare.** Studio UX (ottobre 2026): descrizioni da 13 px a tutta larghezza, 128 caratteri per riga in «Porta qui le tue persone» e 103-105 in Conversazioni e Notifiche; un paragrafo di 5 righe in «I tuoi dati». L'indice non vede termini tecnici, sigle e ordine delle informazioni: Designers Italia lo affianca a test di comprensione e d'uso. textstat conta la punteggiatura tra i caratteri: i suoi valori servono a confrontare due versioni dello stesso testo, non come soglia assoluta.

**Fonti.**

- [Linguaggio (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/linguaggio/) — sezione «Ricerca e testa il linguaggio del tuo servizio» · Designers Italia · 2025 (file del 14/04/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/linguaggio.yaml))
- [Contenuti (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/contenuti/) — «Organizza le informazioni su pagina»: «Titoli», «Sommari», «Corpo di pagina» · Designers Italia · 2025 (file del 05/09/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/contenuti.yaml))
- [Tipografia (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/tipografia/) — Consigli d'uso, «Lunghezza dei paragrafi» · Designers Italia · 2025 (file del 05/11/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/tipografia.yaml))
- [Success Criterion 3.1.5 Reading Level (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#reading-level) — testo del criterio, livello AAA (w3.org/TR/WCAG22/#reading-level) · W3C · 2023 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/reading-level.html))
- [Understanding Reading Level](https://www.w3.org/WAI/WCAG22/Understanding/reading-level.html) — Intent; tabella «Levels of education»; esempio «Medical information for members of the public» · W3C WAI · consultato l'11/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/understanding/20/reading-level.html))
- [textstat, backend/metrics/\_gulpease_index.py](https://github.com/textstat/textstat/blob/main/textstat/backend/metrics/_gulpease_index.py) — funzione gulpease_index (formula implementata) · textstat (progetto open source) · file del 25/12/2024; consultato il 12/10/2026
- [textstat, backend/metrics/\_chars_per_word.py](https://github.com/textstat/textstat/blob/main/textstat/backend/metrics/_chars_per_word.py) — funzione chars_per_word (caratteri senza spazi, punteggiatura compresa) · textstat (progetto open source) · consultato il 12/10/2026
- [textstat 0.7.13 (descrizione del pacchetto)](https://pypi.org/project/textstat/) — README, «Gulpease Index (Italian)» · Python Package Index · versione pubblicata il 18/02/2026; consultato l'11/10/2026 ([sorgente letto](https://pypi.org/pypi/textstat/json))

### LING-VOCE · Il «tu», una voce sola, il tono del momento

**Regola.** DottorCloud si rivolge a chi legge con il «tu» e l'imperativo per le istruzioni («Scegli», «Salva»), mai con il «Lei», l'infinito («Selezionare») o l'impersonale; il «noi» non compare nei messaggi d'errore se non è chiaro chi è. Il tono segue lo stato d'animo del momento: rassicurante dove c'è ansia (un pagamento non riuscito, i dati personali, un referto), diretto dove c'è fretta (una prenotazione), mai colpevolizzante né scherzoso; niente punti esclamativi, interiezioni («ops») o emoji nell'interfaccia.

**Perché.** Designers Italia: «Parla all'interlocutore in modo diretto usando il “tu”, evitando tanto il “lei” e i formalismi quanto la forma impersonale»; il tono va modulato in base al contesto, con una tabella di situazioni: prenotazione di un appuntamento («Cortese, orientato al servizio»: «Scegli data e orario tra quelli disponibili»), pagamento non andato a buon fine («Rassicurante, professionale, proattivo»: «Il pagamento non è andato a buon fine e non ti è stato addebitato alcun importo»), registrazione («Trasparente, rassicurante, affidabile»); nei microtesti il tono «colpevolizzante» è l'esempio da non seguire. Apple (Writing): evitare il «we» perché non è chiaro chi sia, soprattutto nei messaggi d'errore («Unable to load content» è più chiaro di «We're having trouble loading this content»), e interiezioni come «oops!», che «can sound insincere»; (Inclusion) rivolgersi alle persone con «you» e «your», riservare «we» e «our» al prodotto o all'azienda, e pesare l'umorismo, che si traduce male e può irritare. Il divieto dei punti esclamativi è una scelta di DottorCloud, più severa di Designers Italia (che nella sua tabella scrive «Richiesta inviata!»): è nel doc 40 e nel README di Espresso («Niente punti esclamativi, niente emoji nell'interfaccia»).

**In DottorCloud.** Catalogo crm/locale/it.po, comprese le traduzioni del framework che DottorCloud sovrascrive (il suo catalogo vince); frontend/src/area/it.js (area pazienti: tono più caldo, sempre «tu»); email (crm/posta, crm/templates/emails); SMS e WhatsApp dei promemoria (crm/scheduling/promemoria_regole.py, modello). Dove il paziente può essere in ansia (pagamenti online in crm/pagamenti, esiti, documenti consegnati) la prima frase dice che cosa non è successo («Non ti è stato addebitato niente»).

**Come si verifica.** Conteggio dei msgstr con «!» (all'11/10/2026: 12 voci, 2 delle quali sono il nome del prodotto Easy!Appointments); grep -nE '(Lei|Suo|Sua)[ ,.]|^msgstr .(Selezionare|Inserire|Cliccare)' crm/locale/it.po deve restare vuoto (oggi lo è); lettura dei messaggi negativi accanto alla tabella dei toni di Designers Italia.

**Errori da evitare.** Le stringhe ereditate dal framework portavano esclamativi e maschile: «Welcome to Frappe!» tradotto «Benvenuto in DottorCloud!», «Poor!» → «Debole!», «Great!» → «Ottima!», «Copiato!», «Ti diamo il benvenuto! Accedi per continuare.»; anche frasi nate in DottorCloud li avevano: «Invio dell'email non riuscito!», «Il centro è pronto. Buon lavoro!», e sulla vecchia pagina /book (crm/www/book.html, che resta per le prenotazioni fatte prima del passaggio a /prenota) «Prenotato! {0}: ti arriva un'email di conferma.» e «Spostata! Ti arriva una nuova email di conferma.». Corretto il 12/10/2026 nel catalogo di DottorCloud («Ti diamo il benvenuto in DottorCloud», «Debole», «Ottima», «Copiato», «Ti diamo il benvenuto: accedi per continuare.») e nelle frasi stesse («L'email non è stata inviata», «Il centro è pronto: tutti i primi passi sono fatti.», «Prenotato per {0}: ti arriva un'email di conferma.», «Spostata: ti arriva una nuova email di conferma.»). Un «noi» senza soggetto chiaro: «Questo tipo di messaggio non è supportato. Tocca a noi correggerlo.» (chi è «noi», il centro o l'assistenza di DottorCloud?). Un tono scherzoso o allarmato in un errore fa sembrare il prodotto inaffidabile proprio quando serve fiducia.

**Fonti.**

- [Tono di voce (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/tono-di-voce/) — sezioni «Rivolgiti a chi legge con il “tu”» e «Modula il tono di voce in base al contesto» (tabella Esempi) · Designers Italia · 2025 (file del 21/08/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/tono-di-voce.yaml))
- [Microtesti (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/microtesti/) — sezione «Usa un tono di voce appropriato al contesto» · Designers Italia · 2025 (file del 14/04/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/microtesti.yaml))
- [Writing (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/writing) — Best practices: «Use possessive pronouns sparingly», «Write clear error messages» · Apple · 2025 (ultima modifica 16/12/2025); consultato l'11/10/2026 ([sorgente letto](https://developer.apple.com/tutorials/data/design/human-interface-guidelines/writing.json))
- [Inclusion (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/inclusion) — Welcoming language: «Pay attention to how you refer to people», «Consider carefully before including humor» · Apple · consultato il 12/10/2026 ([sorgente letto](https://developer.apple.com/tutorials/data/design/human-interface-guidelines/inclusion.json))

### LING-AZIONI · Pulsanti e link dicono che cosa succede

**Regola.** Ogni pulsante comincia con un verbo all'imperativo che fa prevedere l'effetto e nomina l'oggetto quando il verbo da solo non basta («Emetti la fattura», «Prenota la visita»); mai «OK», «Sì» o un verbo generico come «Conferma» da soli; la stessa azione ha lo stesso verbo in tutte le pagine, e lo stesso verbo non nomina due azioni diverse; il testo di un link dice dove porta, mai «clicca qui» o «Vai all'inizio»; i verbi valgono per mouse e dito («Apri», «Scegli»), non «Clicca» o «Tocca» dove l'azione è la stessa su computer e telefono.

**Perché.** Designers Italia: «Inizia le call-to-action con un verbo che indichi chiaramente l'azione da svolgere e consenta all'utente di prevedere l'effetto dell'interazione» (sì «Invia», no «OK»; sì «Aggiungi un nuovo provider», no «Nuovo provider»); per i link «assicurati che sia chiara la destinazione di ogni link o lo scopo del collegamento». Apple: «When labeling buttons and links, it's almost always best to use a verb»; evitare «Click here»; non dire «click» su un dispositivo a tocco dove si intende «tap». WCAG 2.4.4 (A): lo scopo di un link si capisce dal suo testo o dal contesto; 2.4.6 (AA): intestazioni ed etichette descrivono argomento o scopo; 3.2.4 (AA): i componenti con la stessa funzione sono identificati allo stesso modo. Il design system di DottorCloud lo chiede già: «Pulsanti con verbo e oggetto: “Prenota la visita”, “Annulla la visita”. Mai “OK”» (README di Espresso, «Linguaggio»).

**Soglie ed eccezioni.** WCAG 2.4.4 livello A; 2.4.6 e 3.2.4 livello AA.

**In DottorCloud.** label dei Button di frappe-ui; pulsanti delle email con pulsante(url, testo) di crm/posta/aspetto.py (il testo è l'azione: «Apri la tua area»); link alle pagine delle impostazioni (?settings=). Il «+» delle liste sul telefono (PulsanteAggiungi in pages/\*.vue) dice «Nuova persona», «Nuova trattativa», «Nuova cosa da fare» (correzione dello studio): è la formula nominale che Designers Italia sconsiglia («Nuovo provider»), tenuta per coerenza tra le liste; un pulsante nuovo usa il verbo con l'oggetto («Aggiungi una persona»). Nel dialogo della fattura (InvoiceDialog.vue) il pulsante che dà il numero dice «Emetti», mentre sulle righe di Fatture e Accoglienza il pulsante che prepara solo la bozza e apre il dialogo (msgid «Invoice it», in Invoices.vue e Today.vue) diceva «Emetti la fattura»: dal 12/10/2026 dice «Prepara la fattura», come proponeva lo studio.

**Come si verifica.** axe-core button-name, link-name, input-button-name (nome presente); grep -nE '^msgstr .(OK|Conferma|Crea|Nuovo|Nuova).$' crm/locale/it.po (all'11/10/2026: «Conferma» 2 volte, «Crea» 1, «Nuovo» 1, usato da più pagine delle impostazioni); grep -n 'Clicca|clicca qui|Tocca per' sul catalogo; elenco dei link di una pagina con il lettore di schermo (rotore di VoiceOver, elenco dei link di NVDA): ognuno si capisce da solo.

**Errori da evitare.** Studio UX (ottobre 2026): «Crea» da solo (corretto in «Nuova persona», «Nuova trattativa», «Nuova cosa da fare», «Nuova nota», «Nuova automazione»); «Nuovo» generico in Moduli, Pipeline, Regole di assegnazione, Tempi di risposta e Modelli email, mentre le pagine accanto dicono «Nuova risorsa» o «Aggiungi una casella» (corretto il 12/10/2026: «Nuovo modulo», «Nuova pipeline», «Nuova regola», «Nuovo livello di servizio», «Nuovo modello», e in Utenti «Aggiungi un utente»); «Emetti la fattura» sulle righe, che non emette ma crea una bozza, contro il secondo «Emetti» del dialogo che dà il numero: lo stesso verbo per due azioni (corretto il 12/10/2026: le righe dicono «Prepara la fattura»), e una bozza abbandonata sparisce dalle cose da fare; «Invia a un elenco» che non dice che cosa manda né a chi; «Vai all'inizio» nella pagina d'errore (meglio «Vai all'Accoglienza»). Nel catalogo: «Tocca per assegnare» in Turni del team, una pagina usata col mouse; link delle email «Aprila da qui», «Entra da qui», «Aprilo qui», che si capiscono solo leggendo il paragrafo (passano 2.4.4 grazie al contesto, ma nell'elenco dei link non dicono niente).

**Fonti.**

- [Microtesti (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/microtesti/) — sezione «Usa azioni specifiche» · Designers Italia · 2025 (file del 14/04/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/microtesti.yaml))
- [Contenuti (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/contenuti/) — «Organizza le informazioni su pagina», «Link» · Designers Italia · 2025 (file del 05/09/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/contenuti.yaml))
- [Writing (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/writing) — Best practices: «Be action oriented», «Write for how people use each device» · Apple · 2025 (ultima modifica 16/12/2025); consultato l'11/10/2026 ([sorgente letto](https://developer.apple.com/tutorials/data/design/human-interface-guidelines/writing.json))
- [Success Criterion 2.4.4 Link Purpose (In Context)](https://www.w3.org/TR/WCAG22/#link-purpose-in-context) — testo del criterio, livello A (w3.org/TR/WCAG22/#link-purpose-in-context) · W3C · 2023 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/link-purpose-in-context.html))
- [Success Criterion 2.4.6 Headings and Labels](https://www.w3.org/TR/WCAG22/#headings-and-labels) — testo del criterio, livello AA (w3.org/TR/WCAG22/#headings-and-labels) · W3C · 2023 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/headings-and-labels.html))
- [Success Criterion 3.2.4 Consistent Identification](https://www.w3.org/TR/WCAG22/#consistent-identification) — testo del criterio, livello AA (w3.org/TR/WCAG22/#consistent-identification) · W3C · 2023 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/consistent-identification.html))

### LING-ERRORI · Un errore dice che cosa, perché e come rimediare

**Regola.** Un messaggio d'errore ha un titolo che nomina il problema senza dare colpa, la causa, il rimedio e, se possibile, un'azione o una via d'uscita; dice se i dati sono salvati; sta accanto alla causa; non mostra codici, nomi tecnici o la frase del server; non si ferma a «non valido» e non usa «ops» o «per favore».

**Perché.** Designers Italia: un messaggio d'errore utile «aiuta a riconoscere il problema e dà indicazioni per correggerlo»: un titolo che descrive il problema «senza incolpare l'utente», la causa, il modo di risolvere, una call-to-action per una soluzione immediata o «una via d'uscita alternativa». Apple: mostrare l'errore «as close to the problem as possible, avoid blame, and be clear about what someone can do to fix it» («Choose a password with at least 8 characters» è più utile di «That password is too short»); evitare messaggi robotici come «Invalid name». WCAG 3.3.1 (A): l'elemento in errore è identificato e l'errore descritto a parole; 3.3.3 (AA): se la correzione è nota, va suggerita.

**Soglie ed eccezioni.** WCAG 3.3.1 livello A; 3.3.3 livello AA.

**In DottorCloud.** Il motore di fatturazione parla per Messaggio e Rilievo (doc 45 e 48: il codice SdI in coda tra parentesi, mai come messaggio); Twilio e Stripe hanno i loro errori in parole (crm/telephony/errori_regole.py, crm/pagamenti/regole.py); una scheda che non si apre lo dice con utils/schedaChiusa.js, mai con la frase del server o il codice del record; le chiamate rifiutate passano da chiedi() (utils/chiedi.js). Su /prenota e nell'area il messaggio dice anche che cosa resta valido («La prenotazione non è partita: nessun addebito»).

**Come si verifica.** Prova manuale di ogni errore previsto (campi obbligatori vuoti, rete staccata, carta rifiutata nella modalità di prova di Stripe, codice dell'area scaduto); conteggio dei msgstr con «non valid» (all'11/10/2026: 40 voci) e grep -nE 'Si è verificato un errore|Qualcosa è andato storto' (5 voci): ognuna va riscritta con causa e rimedio; test unitari che le frasi del motore e di Twilio non contengano codici nudi.

**Errori da evitare.** Studio UX (ottobre 2026): un riquadro rosso «Prima di emetterla» già all'apertura del dialogo della fattura, prima di qualsiasi inserimento; «Emetti» e «Salva» del dialogo spenti senza dire che cosa manca (ancora da fare); l'errore lungo di una piattaforma di prenotazione leggibile solo nel suggerimento al passaggio del mouse (corretto dopo due revisioni del codice: l'editor lo mostra intero sotto «Ultimo errore», e il messaggio sulla riga apre la riga). Nel catalogo: «Numero non valido», «Non è stato possibile creare l'account email: credenziali non valide», «Il file “{0}” è stato ignorato a causa di un tipo di file non valido» (non dice quali tipi vanno bene), «Si è verificato un errore», «Qualcosa è andato storto».

**Vedi anche.** [UX-ERRORI](01-interazione.md#ux-errori--messaggi-derrore-linee-guida-nng-2023-e-schemi-ostili)

**Fonti.**

- [Microtesti (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/microtesti/) — sezione «Aiuta nella risoluzione degli errori» · Designers Italia · 2025 (file del 14/04/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/microtesti.yaml))
- [Writing (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/writing) — Best practices: «Write clear error messages», «Show hints in text fields» · Apple · 2025 (ultima modifica 16/12/2025); consultato l'11/10/2026 ([sorgente letto](https://developer.apple.com/tutorials/data/design/human-interface-guidelines/writing.json))
- [Success Criterion 3.3.1 Error Identification](https://www.w3.org/TR/WCAG22/#error-identification) — testo del criterio, livello A · W3C · 2023 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/error-identification.html))
- [Success Criterion 3.3.3 Error Suggestion](https://www.w3.org/TR/WCAG22/#error-suggestion) — testo del criterio, livello AA · W3C · 2023 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/error-suggestion.html))

### LING-CONFERME · Conferme che nominano l'azione e le conseguenze

**Regola.** Prima di un'azione rilevante o irreversibile la domanda è «Vuoi + verbo + oggetto?», il testo dice le conseguenze e come rimediare, il pulsante principale ripete lo stesso verbo e il secondario è «Annulla»; quando il verbo dell'azione è proprio «annullare» (una visita, una prenotazione) i pulsanti diventano «No, mantieni la visita» e «Sì, annulla la visita» o, come nel pannello dell'appuntamento, «Non annullare» e «Annulla l'appuntamento». Niente «Attenzione!», «Sei sicuro…?» o «Sì/No» senza oggetto.

**Perché.** Designers Italia: un titolo «sotto forma di domanda», nella forma «Vuoi + [Verbo dell'azione]», evitando «Attenzione!» o «Sei sicuro di voler...?» che non danno contesto; una descrizione completa dell'azione, delle conseguenze e di come rimediare; «Usa lo stesso verbo che hai usato nel titolo come call-to-action principale»; «Usa “Annulla” come call-to-action secondaria»; nei casi di forte ambiguità si cambiano i verbi, si aggiungono sostantivi e Sì/No («Vuoi annullare la pratica? No, mantieni pratica / Sì, annulla pratica»).

**In DottorCloud.** Il pannello dell'appuntamento (Calendar/AppointmentPanel.vue) segue già quasi lo schema: «Annullare questo appuntamento?», «Il suo orario torna libero per altri.», un campo per il motivo, «Non annullare» e «Annulla l'appuntamento»; il titolo diventa «Vuoi annullare questo appuntamento?». /prenota usa «No, mantieni» e «Sì, annulla» (crm/www/prenota.html), da completare con l'oggetto. Le altre conferme: eliminare un ambulatorio o un link tracciato (corrette dallo studio: la conferma li nomina e dice cosa si perde), emettere una nota di credito (emissione.credit_note), revocare un consenso, togliere i dati di prova (composables/demoData.js: «Togli i dati di prova», con ciò che va e ciò che resta). Le conferme restano per i casi gravi: dove l'azione si può disfare, meglio un «Annulla» subito dopo.

**Come si verifica.** Revisione dei dialoghi: titolo con «Vuoi», primario con lo stesso verbo, secondario «Annulla» o la coppia No/Sì; elenco con grep -c '^msgstr .Vuoi ' sul catalogo (all'11/10/2026: 46 voci che cominciano con «Vuoi», 33 con «Vuoi davvero»); prova da tastiera che il fuoco iniziale non stia sul pulsante distruttivo.

**Errori da evitare.** Due «Annulla» con significati opposti nello stesso riquadro quando l'azione è annullare una visita: il pannello dell'appuntamento lo evita con «Non annullare». «Vuoi davvero…?» non sostituisce le conseguenze: «Vuoi davvero cancellare le assegnazioni degli elementi scelti ({0})?» (ListBulkActions.vue) non dice che cosa succede alle persone a cui erano assegnati. Studio UX (ottobre 2026): ambulatori e link tracciati sparivano con un tocco (corretto con una conferma che nomina l'oggetto e dice che cosa fare invece per tenerlo).

**Vedi anche.** [UX-CONFERMA](01-interazione.md#ux-conferma--dialoghi-di-conferma-e-quando-è-meglio-annulla)

**Fonti.**

- [Microtesti (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/microtesti/) — sezione «Chiedi conferma prima di azioni importanti» · Designers Italia · 2025 (file del 14/04/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/microtesti.yaml))

### LING-ESITI-VUOTI · Successi e liste vuote che dicono che cosa succede ora

**Regola.** Un messaggio di successo dice che cosa è stato fatto (senza «con successo»), il riferimento (numero della fattura, giorno e ora della visita) e che cosa succede dopo; uno stato vuoto dice perché è vuoto, che cosa ci sarà e il primo passo, con un pulsante lì; il vuoto di «ancora niente» e quello di «nessun risultato con questi filtri» hanno parole diverse; il tono non è mai negativo.

**Perché.** Designers Italia: un messaggio di conferma ha un titolo che descrive l'azione appena conclusa, spiega gli effetti con «eventuali numeri di riferimento», dice «cosa succede dopo ed eventuali tempi di attesa» e può proporre il passo successivo; tra gli esempi di testo conciso preferisce «Hai salvato il documento. Vai alla sezione “...” per visualizzarlo» a «Il documento è stato salvato con successo nella sezione “...”». Per gli stati vuoti chiede un messaggio che li spieghi «evitando parole e tono di voce “negativi”», come avviare l'interazione e, se possibile, una call-to-action. Apple: «Provide clear next steps on any blank screens», con un pulsante o un link per farlo, e mai informazioni cruciali in uno stato vuoto, che poi sparisce.

**In DottorCloud.** EmptyState ed EmptyArt (doc 39), con titolo e descrizione tradotti dove si disegnano (Espresso/EmptyState.vue li passa a \_\_()); lo stato vuoto di Account email, con spiegazione e pulsante «Aggiungi una casella», è il modello per le altre pagine delle impostazioni. Toast di frappe-ui per i successi brevi: oggi dopo l'emissione il dialogo della fattura dice solo «Fattura emessa» (InvoiceDialog.vue); secondo la regola nomina il numero («Fattura 2026/12 emessa»). La pagina finale di /prenota dice «Prenotazione confermata» e «Ti abbiamo inviato un'email con tutti i dettagli» (crm/www/prenota.html): secondo la regola ripete anche servizio, giorno, ora e sede. Il riquadro della modalità di prova delle fatture, che lo studio ha lodato perché dice la conseguenza e la via d'uscita.

**Come si verifica.** Elenco degli stati vuoti (grep -rn '<EmptyState' frontend/src) e verifica dei tre elementi (perché, che cosa ci sarà, primo passo); svuotare i filtri di una lista per vedere il secondo tipo di vuoto; il conteggio di «con successo» nei msgstr resta 0 (oggi 0).

**Errori da evitare.** Studio UX (ottobre 2026): «No deals yet» in inglese su un'azienda, perché il titolo passava come prop senza \_\_() (corretto il 10/10/2026); «Per cominciare, usa il pulsante in alto.» in Regole di assegnazione, Tempi di risposta e Modelli email, che non dice a che cosa serve la pagina e non offre il pulsante lì; «Ancora nessun modulo» proprio sotto un modulo da firmare; lo stato vuoto dei cicli che finisce con «…sei di laser…» e sembra tagliato; «Abbonamenti 1» sopra tre righe.

**Vedi anche.** [UX-VUOTO](01-interazione.md#ux-vuoto--stati-vuoti)

**Fonti.**

- [Microtesti (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/microtesti/) — sezioni «Comunica l'esito positivo di un'azione», «Sfrutta gli stati vuoti per incentivare le interazioni» e «Usa un linguaggio semplice e conciso» (tabella) · Designers Italia · 2025 (file del 14/04/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/microtesti.yaml))
- [Writing (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/writing) — Best practices: «Provide clear next steps on any blank screens» · Apple · 2025 (ultima modifica 16/12/2025); consultato l'11/10/2026 ([sorgente letto](https://developer.apple.com/tutorials/data/design/human-interface-guidelines/writing.json))

### LING-AIUTI · Aiuti, segnaposto e scelte specifici

**Regola.** Le istruzioni per compilare stanno in un testo d'aiuto fisso sotto il campo, specifico e scritto come una frase intera (soggetto, verbo, punto finale); il segnaposto serve solo a ricerche e campi liberi e non è mai l'etichetta né un valore che sembra già scelto; la richiesta di una tendina nomina che cosa si sceglie («Scegli una sede», mai «Seleziona un'opzione»); il suggerimento al passaggio del mouse porta solo informazioni secondarie, dette anche altrove.

**Perché.** Designers Italia: i segnaposto suggeriscono come usare campi liberi come la ricerca («Cerca servizi e uffici») e «scompaiono quando l'utente inizia a digitare»; per le istruzioni di compilazione «usa invece l'helper text fisso posto sotto il componente», con istruzioni specifiche («Inserisci una password di almeno 8 caratteri e con almeno una maiuscola», non «Inserisci una password sicura»); nei menu a tendina «specifica cosa bisogna selezionare» («Seleziona una sede») e non il generico «Seleziona un'opzione»; i tooltip solo «per indicazioni secondarie o accessorie». WCAG 3.3.2 (A): etichette o istruzioni quando si chiede un dato.

**Soglie ed eccezioni.** WCAG 3.3.2 livello A.

**In DottorCloud.** FieldLayout/Field.vue (descrizione del campo), SettingsRow nelle impostazioni, filtri rapidi (QuickFilterField.vue, che dopo lo studio portano il nome del campo che filtrano), testi vuoti di select e combobox di frappe-ui (tradotti alla build in frontend/vite/frappeUi.js). Un segnaposto numerico mostra il comportamento reale in parole: per «Precisione valuta» lo studio propone «2 (predefinito)», mentre DefaultsSettings.vue mostra ancora un «3». Sul telefono un suggerimento non si apre al tocco (AGENTS: quello che dice un tooltip non è mai l'unico posto in cui è detto).

**Come si verifica.** Revisione campo per campo dei moduli; axe-core label, select-name, label-title-only (quest'ultima è una buona pratica, non un criterio WCAG); ricerca dei segnaposto non tradotti: grep -rn 'placeholder=' frontend/src --include=\*.vue | grep -v '\_\_('.

**Errori da evitare.** Studio UX (ottobre 2026): «Precisione valuta» e «Precisione decimale» con un «3» grigio come segnaposto mentre gli importi usano 2 decimali; nel nuovo appuntamento persona, servizio e professionista con solo icona e segnaposto, che sparisce appena si scrive (ancora da fare); il testo d'esempio della ricerca tagliato; la tendina dei professionisti della lista d'attesa chiamata «Con» dal lettore di schermo; il riquadro «Solo amministratori» nel collegamento a Meta, dove va detto chi è (AGENTS: si nomina l'agenzia o il responsabile del centro, mai «un amministratore»).

**Fonti.**

- [Microtesti (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/microtesti/) — sezione «Includi aiuti contestuali di valore» · Designers Italia · 2025 (file del 14/04/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/microtesti.yaml))
- [Success Criterion 3.3.2 Labels or Instructions](https://www.w3.org/TR/WCAG22/#labels-or-instructions) — testo del criterio, livello A · W3C · 2023 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/labels-or-instructions.html))

### LING-GLOSSARIO · Un termine per ogni concetto, in tutto il prodotto

**Regola.** Ogni concetto ha un solo nome, scritto nel glossario del doc 40 e usato uguale in menu, titoli, pulsanti, filtri, stati, notifiche, email e area pazienti; la stessa azione ha lo stesso verbo; con la clinica accesa le parole del verticale (paziente, visita, area pazienti) valgono dovunque si nominano le persone; un termine nuovo entra prima nel glossario e poi nel codice.

**Perché.** Designers Italia chiede di definire e applicare «in maniera consistente, la terminologia usata, gli ingombri di testo, i copy delle call to action», anche con librerie di microtesti; il Manuale operativo: «non si progettano singole label, ma sistemi di label», coerenti per stile, sintassi e granularità (non «Scarica il documento» accanto a «Documenti scaricabili»). Apple: «Create a list of common terms, and reference that list to keep your language consistent». WCAG 3.2.4 (AA): componenti con la stessa funzione identificati allo stesso modo; l'Understanding spiega che chi usa un lettore di schermo riconosce i controlli dal nome annunciato e chi ha disabilità cognitive dal loro aspetto coerente, e che nomi diversi fanno pensare a funzioni diverse.

**Soglie ed eccezioni.** WCAG 3.2.4 livello AA.

**In DottorCloud.** Glossario: tabella «Inglese | Italiano» del doc 40 (docs/crm/40-italiano.md, «La voce e le parole»); parole del verticale in crm/clinica/parole.py, registrate con crm/verticali.py (parola(), traduttore()); una pagina nuova che nomina le persone aggiunge la sua coppia (AGENTS). I passi della persona («Lead», «Cliente», «Paziente») vengono da frontend/src/utils/rapporto.js con il contesto «Relationship». Uno stato acceso o spento ha una sola coppia di parole per distintivo, filtro e interruttore.

**Come si verifica.** Per ogni termine conteso, conteggio delle varianti nel catalogo (grep -ciE 'reception|segreteria|accoglienza', 'promemoria|notifich|avvis', 'contatti|persone'); revisione delle pagine sorelle con le stesse azioni; test che il nome di ogni filtro coincida con l'etichetta di stato che filtra.

**Errori da evitare.** Studio UX (ottobre 2026): «promemoria», «notifiche degli eventi» e «avviso» per due cose diverse nella stessa voce delle impostazioni; «reception», «segreteria» e «Accoglienza» per lo stesso banco; cinque nomi per chi viene al centro (resta da fare: glossario breve e giro sulle stringhe); «Spente» nel filtro e «In pausa» sul distintivo delle automazioni (corretto: il distintivo ora dice «Spenta», come il filtro «Spente»); «Contatti» e «Persone» per le stesse persone; «Attesi» e «In attesa» affiancati con significati diversi; le carte del Riepilogo con nomi diversi dalle schede che aprono.

**Fonti.**

- [Microtesti (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/microtesti/) — sezione «Rispetta la consistenza delle tue scelte di scrittura» · Designers Italia · 2025 (file del 14/04/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/microtesti.yaml))
- [Manuale operativo di design: Scrittura e linguaggio](https://github.com/italia/manuale-operativo-design-docs/blob/versione-corrente/doc/progettazione-dei-contenuti/scrittura-e-linguaggio.rst) — Microtesti, approfondimento «Le etichette di navigazione» (stile, sintassi, granularità) · Designers Italia · 2025 (file del 06/02/2025); consultato l'11/10/2026
- [Writing (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/writing) — Getting started, «Determine your app's voice» · Apple · 2025 (ultima modifica 16/12/2025); consultato l'11/10/2026 ([sorgente letto](https://developer.apple.com/tutorials/data/design/human-interface-guidelines/writing.json))
- [Understanding Consistent Identification](https://www.w3.org/WAI/WCAG22/Understanding/consistent-identification.html) — Intent of Consistent Identification · W3C WAI · consultato l'11/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/understanding/20/consistent-identification.html))

### LING-SIGLE · Sigle sciolte alla prima occorrenza

**Regola.** Una sigla compare per esteso alla prima occorrenza in ogni pagina, seguita dalla sigla tra parentesi («Sistema di Interscambio (SdI) dell'Agenzia delle Entrate», «Sistema Tessera Sanitaria (Sistema TS)»), poi si usa la sigla; le sigle che il lettore non usa (PAdES, SHA-256) restano nei dettagli tecnici; una sigla con lettere ambigue nel carattere del prodotto si rende leggibile.

**Perché.** Designers Italia: «Gli acronimi e le sigle non aiutano la comprensione del testo: evitali il più possibile»; se servono, il nome completo per esteso seguito dall'acronimo tra parentesi alla prima ricorrenza. WCAG 3.1.4 (AAA) chiede un meccanismo per conoscere la forma estesa delle abbreviazioni; l'Understanding esenta solo quelle entrate nella lingua («laser») e i nomi di organizzazioni o marchi usati come parole (IBM, NASA). Nel carattere Inter la I maiuscola e la l minuscola sono uguali: lo studio UX ha visto «SdI» letto «Sdl» ingrandendo; Inter ha una variante della I con le grazie (funzione OpenType cv08, file cv08-i-serif.fea, che sostituisce I con I.1).

**Soglie ed eccezioni.** WCAG 3.1.4 livello AAA (obiettivo di scrittura, non obbligo AA).

**In DottorCloud.** Pagine di fatturazione e Sistema TS (Impostazioni › Fatturazione, ProviderConnection.vue, HealthcareSetup.vue), righe del vocabolario (crm/invoicing/engine/voci.py, scelte.CAMPI), email. Per Inter: il carattere tagliato di DottorCloud (frontend/src/assets/fonts/README.md) tiene le funzioni che il browser applica da sé più tnum, pnum, case, zero, ordn, sups, subs e sinf, e lascia fuori le varianti stilistiche; per usare cv08 va aggiunta a --layout-features quando si rifà il taglio, poi font-feature-settings 'cv08' dove compaiono sigle. In alternativa si sceglie nel glossario una grafia senza ambiguità.

**Come si verifica.** Conteggio nel catalogo all'11/10/2026: «SdI» 111 volte, «Sistema di Interscambio» 6; «Sistema TS» 142, «Sistema Tessera Sanitaria» 0: ogni pagina che usa una sigla deve avere la forma estesa una volta; controllo visivo delle sigle con I e l a 200%.

**Errori da evitare.** Studio UX (ottobre 2026): «SdI», «Sistema TS», «PAdES», «SHA-256», «agente IA», «Lead Ads», «Place ID di Google» mai spiegati, proprio nelle pagine dove il centro decide come fatturare (resta da fare). Il doc 40 scrive «SDI» tra i nomi da non tradurre mentre l'interfaccia scrive «SdI»: va scelta una grafia sola. Mettere cv08 nel CSS senza rifare il taglio del carattere non cambia niente.

**Vedi anche.** [LING-GERGO](#ling-gergo--niente-gergo-inglese-nomi-di-campo-o-codici)

**Fonti.**

- [Linguaggio (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/linguaggio/) — sezione «Acronimi e sigle» · Designers Italia · 2025 (file del 14/04/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/linguaggio.yaml))
- [Success Criterion 3.1.4 Abbreviations](https://www.w3.org/TR/WCAG22/#abbreviations) — testo del criterio, livello AAA (w3.org/TR/WCAG22/#abbreviations) · W3C · 2023 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/abbreviations.html))
- [Understanding Abbreviations](https://www.w3.org/WAI/WCAG22/Understanding/abbreviations.html) — Intent of Abbreviations · W3C WAI · consultato l'11/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/understanding/20/abbreviations.html))
- [Inter, src/features/cv08-i-serif.fea](https://github.com/rsms/inter/blob/master/src/features/cv08-i-serif.fea) — sostituzione «sub I by I.1» · The Inter Project · consultato l'11/10/2026

### LING-NORME · Prima la regola in parole, poi la norma

**Regola.** Quando un testo dipende da una norma, dice prima che cosa comporta per chi legge e poi il riferimento tra parentesi o in una nota, con il link al testo ufficiale; un articolo non si usa mai come spiegazione («Esente (art. 10)»).

**Perché.** Designers Italia: «Evita troppi riferimenti normativi, rendono il testo complicato»; quando serve citare una legge, spiegarne sinteticamente il contenuto invece di citarla testualmente, introdurre il titolo della norma solo dopo una spiegazione, tra parentesi, e aggiungere sempre il link alla norma (per esempio su Normattiva). La checklist del Manuale operativo: «Hai inserito i riferimenti normativi nelle note invece che nel testo?».

**In DottorCloud.** Voci della fatturazione (crm/invoicing/engine/voci.py: ogni Voce ha già il nome e la riga su quando si applica; la riga dice l'effetto, il riferimento va in coda), registro delle qualifiche, Sistema TS, consensi e informative (crm/moduli/registro.py). Esempio dello studio: «Esente IVA: prestazione sanitaria», con l'articolo in una nota o in un link.

**Come si verifica.** grep -nE '[(]art[.] ?[0-9]+[)]' crm/locale/it.po per trovare articoli usati come spiegazione (all'11/10/2026: 5 voci, tra cui «Esente (art. 10)» e «Anticipazioni (art. 15)»); ogni riferimento normativo nuovo ha un link a Normattiva o EUR-Lex.

**Errori da evitare.** Studio UX (ottobre 2026): «Esente (art. 10)», «Chinesiologo (art. 41 D.Lgs. 36/2021)», «anticipazioni art. 15 … nota 2 lett. a)» nelle pagine dove il centro sceglie come fatturare, senza una parola su che cosa vogliono dire.

**Fonti.**

- [Linguaggio (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/linguaggio/) — sezione «Riferimenti normativi» · Designers Italia · 2025 (file del 14/04/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/linguaggio.yaml))
- [Manuale operativo di design: Scrittura e linguaggio](https://github.com/italia/manuale-operativo-design-docs/blob/versione-corrente/doc/progettazione-dei-contenuti/scrittura-e-linguaggio.rst) — «Checklist per il linguaggio e i contenuti» · Designers Italia · 2025 (file del 06/02/2025); consultato l'11/10/2026

### LING-GERGO · Niente gergo, inglese, nomi di campo o codici

**Regola.** Lo schermo usa le parole di chi lavora in un centro: niente nomi di DocType o di campo, codici, maschere di formato, termini inglesi o di marketing, nomi di funzioni inventati; un termine tecnico necessario si spiega la prima volta; le funzioni hanno nomi descrittivi («Calendario dei social», non «Social Planner»).

**Perché.** Designers Italia: usare termini complessi solo quando si è certi che il pubblico li capisca, altrimenti sinonimi o una spiegazione «chiara e concisa»; «Non serve creare un marchio per ogni nuovo servizio, ma è meglio usare diciture descrittive e di immediata comprensione». WCAG 3.1.3 (AAA): un meccanismo per le definizioni di parole usate in modo insolito o ristretto, gergo compreso. Apple (Inclusion): «Avoid using specialized or technical terms without defining them». La rubrica dello studio (euristica H2) lo chiede in chiaro: le parole sono l'italiano del personale, niente nomi di DocType, nomi di campo, codici o inglese.

**Soglie ed eccezioni.** WCAG 3.1.3 livello AAA (obiettivo).

**In DottorCloud.** Riassunti delle automazioni (frontend/src/utils/automation.js, triggerSummary: l'etichetta del campo dalla meta, una frase intera per caso); scelte di formato in Impostazioni › Il centro (esempi con dati veri, «31/12/2026», «1.234,56», «14:30», al posto di «dd/mm/yyyy», «#.###,##», «HH:mm:ss»); titoli e fasi della dashboard (crm/dashboard/widgets); codici della fatturazione mostrati in parole (scelte.CAMPI, doc 45); nomi delle viste e delle pagine.

**Come si verifica.** Il giro nel browser del doc 40 («Come si trovano le frasi in inglese»: Proxy su window.translated_messages e lettura del testo visibile con parole solo inglesi); grep -n -A1 'msgid .Social Planner' crm/locale/it.po (all'11/10/2026 tradotto con sé stesso); script sul DOM che segnala parole con trattino basso o in camelCase nel testo visibile.

**Errori da evitare.** Studio UX (ottobre 2026): «last_visit 60 after» nel nodo di un'automazione (corretto: ora si legge 60 giorni dopo «Ultima visita», una frase per caso con il nome del campo); «Benvenuto a chi diventa patient» nei dati di prova; titoli della dashboard «Ricavi vinti», «Tasso di vittoria», «Valore della pipeline», «Imbuto della pipeline» e fasi da venditore di software («Dimostrazione», «Negoziazione»); le maschere «#.###,##» e «dd/mm/yyyy» con le lettere inglesi; «Dashboard» nel menu e «Panoramica» nella scheda del browser.

**Vedi anche.** [LING-SIGLE](#ling-sigle--sigle-sciolte-alla-prima-occorrenza), [I18N-CODICI-IN-PAROLE](#i18n-codici-in-parole--si-salva-il-codice-si-mostra-la-parola)

**Fonti.**

- [Linguaggio (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/linguaggio/) — sottosezioni «Termini tecnici, burocratici e stranieri» e «Nomi di organizzazioni, servizi e progetti» · Designers Italia · 2025 (file del 14/04/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/linguaggio.yaml))
- [Success Criterion 3.1.3 Unusual Words](https://www.w3.org/TR/WCAG22/#unusual-words) — testo del criterio, livello AAA · W3C · 2023 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/unusual-words.html))
- [Inclusion (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/inclusion) — Welcoming language (pubblicato su developer.apple.com/design/human-interface-guidelines/inclusion) · Apple · consultato l'11/10/2026 ([sorgente letto](https://developer.apple.com/tutorials/data/design/human-interface-guidelines/inclusion.json))

### LING-GENERE · Linguaggio inclusivo di genere

**Regola.** Non si usa il maschile sovraesteso per parlare a tutti: si scelgono forme senza genere («Ti diamo il benvenuto», «chi ha prenotato», «la persona», «il personale»), si costruisce la frase intorno al verbo invece di accordare un participio al nome di una persona («{0} è in sala d'attesa», non «{0} è arrivato»), si usa il femminile per una donna («la dottoressa», «la direttrice sanitaria») e si evitano stereotipi negli esempi e nei dati di prova.

**Perché.** Designers Italia elenca tra le cose da non usare il «maschile sovresteso» e gli stereotipi, con gli esempi «Ti diamo il benvenuto, Ricevi aggiornamenti» (non «Benvenuto, Rimani aggiornato») e «La ministra, la sindaca, la dirigente (quando la persona è donna)»; nel tono di voce preferisce «le persone» a «i cittadini». Apple (Inclusion): evitare riferimenti di genere non necessari, per esempio con un sostantivo plurale al posto di «his or her», il che aiuta anche le traduzioni in lingue con pronomi di genere. Il W3C mostra che un nome di persona inserito in una frase spesso obbliga ad accordare altre parole al suo genere («The patient `<person's_name>` is ready» diventa in spagnolo «El enfermo Richard está listo» o «La enferma Julia está lista»).

**In DottorCloud.** Catalogo e frontend/src/area/it.js; frasi delle notifiche (crm/notifiche/regole.py, già costruite intorno al verbo: «{0} è in sala d'attesa: ha segnalato l'arrivo dal telefono»); email ai pazienti; dati di prova (crm/demo/dati.py). I nomi epiceni («paziente», «responsabile», «professionista») restano neutri se la frase lo permette («ogni paziente», «chi è responsabile»).

**Come si verifica.** grep -nE 'Benvenut[oi]|[Ss]ei (sicuro|pronto|stato)' crm/locale/it.po frontend/src/area/it.js; revisione delle voci con «il paziente» (43 all'11/10/2026), «operatore» o «operatori» (48), «utente» o «utenti» (77); per ogni frase che ha il nome di una persona come soggetto, verificare che nessun participio o aggettivo si accordi a quel nome.

**Errori da evitare.** «Benvenuto in DottorCloud!» (la stringa del framework) conviveva con «Ti diamo il benvenuto in {brand}», che è già la forma giusta; la ricetta delle automazioni «Welcome a new lead» era tradotta «Benvenuto a un nuovo contatto» (maschile, e il verbo inglese era diventato un saluto). Corretti il 12/10/2026: «Ti diamo il benvenuto in DottorCloud» e «Dai il benvenuto a chi ti contatta». Studio UX (ottobre 2026): «mettila in lista e il posto … va a lei», riferito a «persona», si legge al femminile anche per un paziente uomo (proposta: «metti la persona in lista»). Riempire una frase con una parola del verticale («Benvenuto a chi diventa {cliente}») non permette di accordare nulla (I18N-FRASI-INTERE).

**Fonti.**

- [Linguaggio (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/linguaggio/) — sezione «Inclusività» (tabella Va bene / Non va bene) · Designers Italia · 2025 (file del 14/04/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/linguaggio.yaml))
- [Tono di voce (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/tono-di-voce/) — sezione «Rispetta le differenze» · Designers Italia · 2025 (file del 21/08/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/tono-di-voce.yaml))
- [Inclusion (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/inclusion) — Gender identity · Apple · consultato l'11/10/2026 ([sorgente letto](https://developer.apple.com/tutorials/data/design/human-interface-guidelines/inclusion.json))
- [Working with Composite Messages](https://www.w3.org/International/articles/composite-messages/) — «Gender agreement and runtime-defined substrings» (pubblicato su w3.org/International/articles/composite-messages/) · W3C Internationalization (Richard Ishida) · 2006, ultimo aggiornamento sostanziale 24/08/2021 ([sorgente letto](https://github.com/w3c/i18n-drafts/blob/gh-pages/articles/composite-messages/index.en.html))

### LING-ABILISMO · Niente verbi abilisti, prima la persona

**Regola.** Le azioni non presuppongono un senso: «Apri», «Scopri», «Vai a», «Mostra» invece di «Vedi», «Guarda», «Ascolta»; si scrive «persone con disabilità», mai «disabili» o «diversamente abili»; una disabilità non si usa come metafora di qualcosa che non va.

**Perché.** Designers Italia mette i «verbi abilisti» tra le cose da non usare («Scopri / Vai a / Approfondisci» sì, «Vedi / leggi» no) e scrive «Persone con disabilità», non «Disabili»; nel tono di voce: «l'accesso delle persone con disabilità», non «dei disabili». Apple (Inclusion): «avoid language that uses a disability to express a negative quality» e «Take a people-first approach when writing about people with disabilities».

**In DottorCloud.** Pulsanti e link («Vedi tutti i partecipanti» → «Mostra tutti i partecipanti»; «Vedi la posizione» → «Apri la mappa»), area pazienti, email. In un prodotto sanitario vale per i testi dell'interfaccia; la cartella clinica è scritta dal professionista e resta sua.

**Come si verifica.** grep -nE '^msgstr .(Vedi|Guarda|Ascolta) ' crm/locale/it.po (all'11/10/2026: 8 voci che cominciano con «Vedi» e «Guarda nella tua email.»); grep -niE 'disabili[ .,]|diversamente abil|handicap' crm/locale/it.po frontend/src/area/it.js (oggi vuoto).

**Errori da evitare.** Nel catalogo: «Vedi tutti i partecipanti», «Vedi il registro degli errori», «Vedi o esci dalla lista d'attesa», «Vedi la posizione», «Vedi chi ha aperto questa cartella e quando…», «Vedi l'area come la vede questa persona…», «Vedi le tue fatture», «Vedi cosa»; «Guarda nella tua email.» (meglio «Apri la tua email: ti abbiamo mandato il codice»).

**Fonti.**

- [Linguaggio (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/linguaggio/) — sezione «Inclusività» · Designers Italia · 2025 (file del 14/04/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/linguaggio.yaml))
- [Tono di voce (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/tono-di-voce/) — sezione «Rispetta le differenze» · Designers Italia · 2025 (file del 21/08/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/tono-di-voce.yaml))
- [Inclusion (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/inclusion) — Accessibility · Apple · consultato l'11/10/2026 ([sorgente letto](https://developer.apple.com/tutorials/data/design/human-interface-guidelines/inclusion.json))

### LING-TITOLI · Titoli di pagina e intestazioni che dicono dove sei

**Regola.** Ogni vista ha un titolo del documento che nomina prima la cosa specifica e poi il contesto («Silvia Fontana · Trattativa · DottorCloud», «Promemoria degli appuntamenti · Impostazioni · DottorCloud»; nelle pagine pubbliche anche il nome del centro), aggiornato a ogni cambio di vista; intestazioni ed etichette descrivono argomento o scopo; una pagina ha lo stesso nome nel menu, nel titolo e nella scheda del browser; i titoli stanno entro 70 caratteri.

**Perché.** WCAG 2.4.2 (A): le pagine hanno titoli che ne descrivono argomento o scopo; l'Understanding precisa che nelle applicazioni a pagina singola «the title of the page should also be changed dynamically to reflect the content or topic of the current view» e porta l'esempio di una banca che genera titoli come «Bank XYZ, accounts for Alex Smith». WCAG 2.4.6 (AA): intestazioni ed etichette descrivono argomento o scopo; l'Understanding ricorda che possono essere brevi, anche una parola. Designers Italia: titoli chiari e descrittivi «in massimo 70 caratteri (inclusi spazi)».

**Soglie ed eccezioni.** WCAG 2.4.2 livello A; 2.4.6 livello AA; Designers Italia: titolo ≤ 70 caratteri.

**In DottorCloud.** frontend/src/router.js scrive document.title dal nome della pagina; le pagine dei record usano usePageMeta di frappe-ui; Settings/Settings.vue scrive «Turni del team · Impostazioni» mentre le impostazioni sono aperte (correzione dello studio); frontend/src/App.vue disegna, invisibile, l'intestazione per il lettore di schermo da titoloDellaPagina (frontend/src/utils/menu.js), e le pagine con un titolo proprio stanno in CON_UN_TITOLO; pagine pubbliche: nome del centro accanto al prodotto (marchio.per_le_pagine, nome_scelto). Il nome di una pagina è uno solo tra menu, titolo e scheda.

**Come si verifica.** axe-core document-title (WCAG), page-has-heading-one, empty-heading e heading-order (buone pratiche); due record con lo stesso nome (una persona e la sua trattativa) aperti in due schede del browser si distinguono; la cronologia del browser si legge.

**Errori da evitare.** Studio UX (ottobre 2026): il `<title>` inglese «Login» per la pagina d'accesso; persona e trattativa «Silvia Fontana» con lo stesso titolo; l'editor di un'automazione intitolato solo «Automazione»; tutte le pagine delle Impostazioni intitolate «Accoglienza» (corretto); «Dashboard» nel menu e «Panoramica» nella scheda.

**Vedi anche.** [WCAG-2.4.2](03-wcag-utilizzabile-e-comprensibile.md#wcag-242--ogni-pagina-ha-un-titolo-che-dice-dove-si-è-242-a), [WCAG-2.4.6](03-wcag-utilizzabile-e-comprensibile.md#wcag-246--intestazioni-ed-etichette-dicono-che-cosa-cè-e-che-cosa-scrivere-246-aa)

**Fonti.**

- [Success Criterion 2.4.2 Page Titled](https://www.w3.org/TR/WCAG22/#page-titled) — testo del criterio, livello A · W3C · 2023 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/page-titled.html))
- [Understanding Page Titled](https://www.w3.org/WAI/WCAG22/Understanding/page-titled.html) — Intent (Single Page Applications); Examples («A web application») · W3C WAI · consultato l'11/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/understanding/20/page-titled.html))
- [Understanding Headings and Labels](https://www.w3.org/WAI/WCAG22/Understanding/headings-and-labels.html) — Intent of Headings and Labels · W3C WAI · consultato l'11/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/understanding/20/headings-and-labels.html))
- [Contenuti (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/contenuti/) — «Organizza le informazioni su pagina», «Titoli» · Designers Italia · 2025 (file del 05/09/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/contenuti.yaml))

### LING-NOME-ACCESSIBILE · Il nome per il lettore di schermo: in italiano e uguale a quello che si vede

**Regola.** Il nome accessibile di ogni controllo (pulsante solo icona, casella di una riga, tendina, scheda, interruttore) è in italiano, passa dal traduttore, dice che cosa fa e su che cosa («Seleziona Maria Rossi», «Segna fatta: Richiamare il laboratorio») e contiene parola per parola il testo visibile, possibilmente all'inizio; mai un aria-label inglese o un nome che contraddice l'etichetta.

**Perché.** WCAG 2.5.3 (A): per i componenti con un'etichetta di testo, il nome contiene il testo presentato visivamente; «A best practice is to have the text of the label at the start of the name». L'Understanding spiega che chi usa il controllo vocale pronuncia l'etichetta che vede («move to Password»): se il nome è diverso il comando fallisce, e le discrepanze aumentano il carico cognitivo. WCAG 4.1.2 (A): il nome di ogni componente è determinabile dal programma. L'Understanding di 3.1.2 nota che i nomi accessibili sono stringhe piatte: un cambio di lingua al loro interno non arriva alle tecnologie assistive, che leggono tutto con una voce sola.

**Soglie ed eccezioni.** WCAG 2.5.3 livello A; WCAG 4.1.2 livello A per la presenza del nome.

**In DottorCloud.** aria-label sempre con \_\_() (AGENTS: un pulsante che è solo un'icona dice che cosa fa); useEtichettaDelCampo e useEtichetteDeiCampi (frontend/src/composables/nomeAlControllo.js) legano la parola del campo al controllo; caselle di riga «Seleziona {nome}» e «Seleziona tutto» (frontend/vite/frappeUi.js, correzione dello studio); gli Switch fuori da SettingsRow hanno :aria-label con le parole accanto.

**Come si verifica.** axe-core label-content-name-mismatch (2.5.3), button-name, aria-command-name, select-name; prova con VoiceOver o NVDA in italiano: nessuna parola letta con la pronuncia inglese; controllo vocale (Accesso vocale di Apple o Voice Access di Android) che usa l'etichetta visibile.

**Errori da evitare.** Studio UX (ottobre 2026): il passo di /prenota con aria-label «progress», letto in inglese a chi usa VoiceOver in italiano (corretto: ora «Passi della prenotazione», crm/www/prenota.html); l'ingranaggio dei social chiamato «Profili»; la tendina dei professionisti della lista d'attesa chiamata «Con»; le caselle di riga lette «casella di controllo» 20 volte per pagina (corretto); il pulsante dell'account che si chiamava come il prodotto (corretto).

**Vedi anche.** [WCAG-2.5.3](03-wcag-utilizzabile-e-comprensibile.md#wcag-253--il-nome-accessibile-contiene-le-parole-che-si-vedono-253-a), [ARIA-ACCNAME](02-wcag-percepibile-e-robusto.md#aria-accname--come-nasce-il-nome-accessibile-accname-12)

**Fonti.**

- [Success Criterion 2.5.3 Label in Name](https://www.w3.org/TR/WCAG22/#label-in-name) — testo del criterio e nota, livello A · W3C · 2023 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/21/label-in-name.html))
- [Understanding Label in Name](https://www.w3.org/WAI/WCAG22/Understanding/label-in-name.html) — Intent · W3C WAI · consultato l'11/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/understanding/21/label-in-name.html))
- [Success Criterion 4.1.2 Name, Role, Value](https://www.w3.org/TR/WCAG22/#name-role-value) — testo del criterio, livello A · W3C · 2023 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/name-role-value.html))
- [Understanding Language of Parts](https://www.w3.org/WAI/WCAG22/Understanding/language-of-parts.html) — Intent (paragrafi sui nomi accessibili come stringhe piatte) · W3C WAI · consultato l'11/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/understanding/20/language-of-parts.html))
- [axe-core Rule Descriptions](https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md) — regole label-content-name-mismatch, button-name, aria-command-name, select-name · Deque Systems · axe-core 4.14, consultato l'11/10/2026

### TIPO-MAIUSCOLE · Maiuscola solo all'inizio, mesi e giorni minuscoli

**Regola.** Titoli, etichette, pulsanti e voci di menu hanno la maiuscola solo all'inizio e nei nomi propri («Regole di assegnazione»); niente testo tutto maiuscolo, né scritto né con text-transform uppercase; giorni e mesi sempre minuscoli dentro una data («dom 4 ott», «lunedì 25 gennaio»), quindi niente capitalize sulle date; il nome di un campo dentro una frase perde la maiuscola («Aggiungi il codice fiscale»), mentre sigle e nomi con maiuscole interne restano come sono.

**Perché.** Designers Italia: «I testi in maiuscolo sono difficili da leggere. Usa il maiuscolo soltanto per la prima lettera della frase (sentence case)»; mese e giorno della settimana in lettere «con l'iniziale minuscola». Il Manuale operativo indica le varianti «CHI SIAMO», «Chi siamo», «Chi Siamo» come un'incoerenza da evitare in un sistema di etichette. CLDR scrive minuscoli i nomi di mesi e giorni dell'italiano, anche nelle forme isolate («gen», «lun», «gennaio»).

**In DottorCloud.** Doc 40 («La voce e le parole»: le maiuscole all'italiana); inFrase() in frontend/src/utils/locale.js e in_frase() sul server (crm_fields_layout.py): «Codice fiscale» diventa «codice fiscale» dentro una frase, «IVA», «PEC», «WhatsApp», «N.» restano. Le etichette di gruppo della barra laterale (AppSidebar.vue, oggi 11 px uppercase) e le etichette di sezione dell'area (area-label in frontend/src/area/area.css, 12 px in maiuscolo) vanno decise con il design system: il README di Espresso prevede text-tiny, 11 px in maiuscolo, per le etichette di sezione, che contraddice Designers Italia.

**Come si verifica.** grep -rn 'capitalize' frontend/src --include=\*.vue (all'11/10/2026 come classe in MeseAgenda.vue, GrigliaAgenda.vue e SocialPlanner.vue: verificare che non tocchi date); grep -rn 'uppercase' frontend/src --include=\*.vue --include=\*.css; test unitari di inFrase in frontend/tests/unit/locale.test.js.

**Errori da evitare.** Studio UX (ottobre 2026): «MARKETING» e «OGGI» a 11 px in maiuscolo; le date «Dom 4 Ott», «Mar 13 Ott» per la classe capitalize, mentre le cose da fare scrivono «mar 20 ott». Prima del doc 40 le traduzioni ereditate avevano le maiuscole all'inglese («Data Di Scadenza»). capitalize mette la maiuscola a ogni parola, mese compreso.

**Fonti.**

- [Linguaggio (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/linguaggio/) — «Formatta il testo in modo coerente e accessibile»: «Uso delle maiuscole», «Date» · Designers Italia · 2025 (file del 14/04/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/linguaggio.yaml))
- [Manuale operativo di design: Scrittura e linguaggio](https://github.com/italia/manuale-operativo-design-docs/blob/versione-corrente/doc/progettazione-dei-contenuti/scrittura-e-linguaggio.rst) — «Le etichette di navigazione», punto «Stile e ortografia» · Designers Italia · 2025 (file del 06/02/2025); consultato l'11/10/2026
- [CLDR 48, main/it/ca-gregorian.json](https://github.com/unicode-org/cldr-json/blob/main/cldr-json/cldr-dates-full/main/it/ca-gregorian.json) — months e days, forme format e stand-alone · Unicode CLDR · CLDR 48 (cldr-json 48.2.3), consultato l'11/10/2026

### TIPO-VIRGOLETTE-APOSTROFO · Virgolette basse, apostrofo e puntini tipografici

**Regola.** Nelle frasi italiane le citazioni e i nomi di pagine, pulsanti e campi stanno tra virgolette basse «…», con le alte “…” solo dentro una citazione; niente virgolette dritte nel testo; i puntini di sospensione sono il carattere … (U+2026); l'apostrofo delle frasi dell'interfaccia è uno solo in tutto il prodotto, e quello raccomandato da Unicode e ICU è ’ (U+2019); i dati (cognomi come D'Angelo) restano come sono stati scritti, e la ricerca tratta ' e ’ come uguali.

**Perché.** CLDR, il riferimento dei dati di lingua, dà per l'italiano quotationStart «, quotationEnd » e come virgolette interne “ ”. Unicode (NamesList 17.0.0): sotto U+0027 «2019 is preferred for apostrophe», sotto U+2019 «this is the preferred character to use for apostrophe»; U+2026 è HORIZONTAL ELLIPSIS. La guida di ICU raccomanda l'apostrofo vero ’ (U+2019) nel testo leggibile e l'ASCII ' solo nella sintassi dei programmi, come le citazioni di MessageFormat.

**In DottorCloud.** Catalogo crm/locale/it.po all'11/10/2026: 2134 apostrofi dritti e nessuno tipografico; 158 coppie di caporali, 6 di virgolette alte, 42 voci con virgolette dritte (in parte attributi HTML come href, che restano dritti); 103 puntini … e 20 voci con tre punti. frontend/src/area/it.js usa invece ’ (39 volte nelle traduzioni, nessun apostrofo dritto): area e scrivania hanno due apostrofi diversi. conLApostrofo (frontend/src/utils/locale.js) e lingue.con_l_apostrofo (crm/lingue.py) inseriscono un apostrofo dritto: vanno allineati alla scelta, e l'espressione del browser, che esclude solo ' prima dell'articolo, va estesa a ’ come quella del server.

**Come si verifica.** Script sul catalogo e su area/it.js: conteggio di ' e ’ nei testi, di virgolette dritte fuori dagli attributi HTML, dei tre punti; test unitari di conLApostrofo con una frase che usa ’; ricerca di una persona salvata come «D’Angelo» digitando «D'Angelo».

**Errori da evitare.** L'apostrofo misto nella stessa frase: nell'area «L’addebito del {0} non è riuscito: {1}» con {0} = «1 ott» diventa «L’addebito dell'1 ott…», il primo apostrofo tipografico dal dizionario e il secondo dritto da conLApostrofo. Nel catalogo convivono un nome tra virgolette dritte («Preventivo consegnato» nella descrizione della pipeline) e altri tra caporali; «Caricamento...», «Squilla...», «Scegli un'icona...» con tre punti. Convertire anche i dati delle persone o i msgid romperebbe ricerche e traduzioni.

**Fonti.**

- [CLDR 48, main/it/delimiters.json](https://github.com/unicode-org/cldr-json/blob/main/cldr-json/cldr-misc-full/main/it/delimiters.json) — quotationStart, quotationEnd, alternateQuotationStart, alternateQuotationEnd · Unicode CLDR · CLDR 48 (cldr-json 48.2.3), consultato l'11/10/2026
- [Unicode 17.0.0 NamesList.txt](https://github.com/unicode-org/unicodetools/blob/main/unicodetools/data/ucd/17.0.0/NamesList.txt) — voci 0027 APOSTROPHE, 2019 RIGHT SINGLE QUOTATION MARK, 2026 HORIZONTAL ELLIPSIS · Unicode Consortium · 2025
- [ICU User Guide: Formatting Messages](https://github.com/unicode-org/icu/blob/main/docs/userguide/format_parse/messages/index.md) — «Quoting/Escaping», raccomandazione sull'apostrofo (pubblicato su unicode-org.github.io/icu/userguide/format_parse/messages/) · Unicode ICU · consultato l'11/10/2026

### TIPO-DATE · Date all'italiana e mai ambigue

**Regola.** Nel testo una data ha il mese in lettere minuscole e l'anno in cifre («25 gennaio 2026», «lunedì 25 gennaio 2026»); nelle righe dense si usa la forma breve di CLDR («25 gen», con l'anno quando non è quello in corso); la forma numerica «25/01/2026» resta per campi e tabelle, sempre con l'anno a quattro cifre; un separatore di giorno ha sempre la data («domenica 18 ottobre», mai «Domenica» da sola); una cosa senza ora (una fattura) non mostra «00:00»; una vista usa un formato solo; davanti al giorno 1, 8 e 11 l'articolo si elide («l'1 ottobre», «dall'8», «all'11»).

**Perché.** Designers Italia: «Scrivi i giorni del mese e l'anno in cifre, mentre scrivi il mese e, se necessario, il giorno della settimana in lettere (con l'iniziale minuscola)» («25 gennaio 2018», «lunedì 25 gennaio 2018»). Il W3C spiega che «03/04/02» si legge in modi diversi secondo il paese e che un mese in lettere con l'anno a quattro cifre è «completely unambiguous». CLDR 48 per l'italiano: forma completa «EEEE d MMMM y», lunga «d MMMM y», media «d MMM y», breve «dd/MM/yy»; mesi abbreviati «gen…dic», giorni «dom…sab». La regola dell'elisione è di DottorCloud (AGENTS e doc 40) e si applica dopo il riempimento della frase.

**Soglie ed eccezioni.** CLDR it: full «EEEE d MMMM y», long «d MMMM y», medium «d MMM y», short «dd/MM/yy»; anno a 4 cifre (W3C) nei formati numerici.

**In DottorCloud.** Intl.DateTimeFormat(appLocale(), …) con dateStyle o le opzioni di CLDR; frontend/src/utils/schedaPersona.js aggiunge l'anno solo se diverso dall'anno corrente (modello da seguire); conLApostrofo nel traduttore del browser (frontend/src/translation.js) e dell'area (frontend/src/area/translation.js), lingue.con_l_apostrofo sul server (email, pagine pubbliche); formatoDellaScadenza in frontend/src/utils/quando.js per le cose da fare, con o senza ora; il formato numerico del sito (dd/mm/yyyy) scritto da lingue.per_l_italia dove nessuno ha scelto.

**Come si verifica.** frontend/tests/unit/locale.test.js (elisione davanti a 1, 8, 11 e a 01, 08); test per i separatori della Chat (giorno con data: frontend/tests/unit/conversation.test.js, dal 12/10/2026) e, da aggiungere, per i documenti senza ora; revisione di ogni lista con date: un formato per vista; un appuntamento di gennaio dell'anno dopo mostra l'anno.

**Errori da evitare.** Studio UX (ottobre 2026): «20/07/2026» accanto a «10 ott, 11:30» nella stessa pagina delle fatture; la fattura con «00:00» nella Chat, ordinata prima della visita che l'ha generata (ancora da fare); separatori «Domenica» e «Mercoledì» senza data, con due «Domenica» diverse (corretto il 12/10/2026); tempi solo relativi («16 minuti fa», «59 minuti fa») nella Cronologia e sulle carte delle cose da fare; date spezzate a fine riga sul telefono («fino al 23 / nov», TIPO-SPAZI-UNITA).

**Vedi anche.** [FORM-DATE](06-moduli.md#form-date--date-allitaliana-senza-ambiguità)

**Fonti.**

- [Linguaggio (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/linguaggio/) — «Formatta il testo in modo coerente e accessibile»: «Date» · Designers Italia · 2025 (file del 14/04/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/linguaggio.yaml))
- [Date formats](https://www.w3.org/International/questions/qa-date-format/) — Answer, «Option Two: Make the month and year obvious» (pubblicato su w3.org/International/questions/qa-date-format) · W3C Internationalization (Lloyd Honomichl) · 2003, aggiornato nel 2007, rivisto il 22/01/2016 ([sorgente letto](https://github.com/w3c/i18n-drafts/blob/gh-pages/questions/qa-date-format.en.html))
- [CLDR 48, main/it/ca-gregorian.json](https://github.com/unicode-org/cldr-json/blob/main/cldr-json/cldr-dates-full/main/it/ca-gregorian.json) — dateFormats, months, days, availableFormats (MMMd, yMMMd, MMMEd) · Unicode CLDR · CLDR 48 (cldr-json 48.2.3), consultato l'11/10/2026

### TIPO-ORE-DURATE · Ore a 24 ore, durate con le unità

**Regola.** Le ore si scrivono a 24 ore, con i due punti e senza spazi («09:00», «14:30»); ogni formattazione con Intl porta hourCycle h23 e mai «AM/PM», anche in inglese; una durata non si scrive come un'ora ma con le unità («3 min 29 s», «1 h 02 min», «55 min»); un intervallo è «10:00–10:55».

**Perché.** Designers Italia: «Usa le cifre e separa ore e minuti con i due punti, senza spazi» («23:59»); le unità di misura in cifre, spazio e simbolo del Sistema Internazionale. CLDR 48 per l'italiano: ora breve «HH:mm», separatore «:». MDN: hourCycle accetta h11, h12, h23, h24 e il predefinito dipende dalla lingua; con Node 22 un'ora in en senza opzioni esce con PM («4:30 PM»), in en-GB «16:30» (prova del 12/10/2026).

**In DottorCloud.** AGENTS: le ore sono quelle a 24 ore del sistema (HH:mm, l'unico formato che Frappe ha), mai hh:mm a; appLocale() dà en-GB all'inglese; le dieci chiamate Intl con un'ora trovate nel codice hanno già hourCycle h23. durataDellaChiamata() in frontend/src/utils/sulTelefono.js restituisce ancora «3:29» e «1:02:05»: va portata alle unità, con spazi non separabili.

**Come si verifica.** grep -rn -A3 'hour: .2-digit.' frontend/src: ogni chiamata ha hourCycle h23; test unitario di durataDellaChiamata con 209 secondi atteso «3 min 29 s»; utente in inglese: nessun AM/PM in agenda, notifiche e cose da fare.

**Errori da evitare.** Studio UX (ottobre 2026): la durata «3:29» accanto all'ora «11:35» nella riga di una chiamata, leggibile come un orario, e «2:11» che va a capo da sola. Prima del doc 40 le cose da fare, gli eventi e le notifiche scrivevano «02:30 pm».

**Vedi anche.** [FORM-ORE](06-moduli.md#form-ore--orari-a-24-ore-e-sempre-di-un-fuso-detto)

**Fonti.**

- [Linguaggio (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/linguaggio/) — «Formatta il testo in modo coerente e accessibile»: «Orari», «Unità di misura» · Designers Italia · 2025 (file del 14/04/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/linguaggio.yaml))
- [CLDR 48, main/it/ca-gregorian.json](https://github.com/unicode-org/cldr-json/blob/main/cldr-json/cldr-dates-full/main/it/ca-gregorian.json) — timeFormats (short «HH:mm») · Unicode CLDR · CLDR 48 (cldr-json 48.2.3), consultato l'11/10/2026
- [Intl.DateTimeFormat() constructor](https://developer.mozilla.org/en-US/docs/web/javascript/reference/global_objects/intl/datetimeformat/datetimeformat) — Locale options: hour12, hourCycle, timeZone (pubblicato su developer.mozilla.org) · MDN Web Docs (Mozilla) · consultato l'11/10/2026 ([sorgente letto](https://github.com/mdn/content/blob/main/files/en-us/web/javascript/reference/global_objects/intl/datetimeformat/datetimeformat/index.md))

### TIPO-NUMERI · Numeri: cifre, virgola decimale, punto delle migliaia, una regola sola

**Regola.** I dati si scrivono in cifre; la virgola separa i decimali e il punto le migliaia; la percentuale è attaccata («87,3%»); i numeri grandi e approssimativi si scrivono con le parole («4 milioni e 325 mila», «circa 10 mila»; in forma compatta «2,8 Mln»); ogni numero esce da un formattatore nella lingua dell'utente, mai da concatenazioni o toFixed; per i numeri da 1000 a 9999 si decide una regola sola e la si usa ovunque: gli importi e le colonne raggruppano sempre («1.250,00 €»), la prosa può seguire CLDR («8700 persone»).

**Perché.** Designers Italia: «Prediligi l'uso delle cifre, soprattutto quando i numeri indicano un dato preciso»; «Usa il punto per separare le migliaia a partire dai 10 mila in su» («8700», «11.800»); «Usa la virgola per separare i decimali»; «mila», «milione», «miliardo» in lettere per valori molto alti e indicativi. CLDR 48 per l'italiano: decimale «,», migliaia «.», minimumGroupingDigits 2 (nessun separatore sotto 10.000), percentuale «#,##0%», compatto «0 Mln». Con i dati di Node 22 (ICU 77, CLDR 47) Intl.NumberFormat('it') scrive «8700», «11.800» e «1250,00 €» (prova del 12/10/2026), mentre il formato del sito di Frappe (#.###,##) e fmt_money del server raggruppano sempre («1.250,00»). MDN: useGrouping «always» mostra i separatori «even if the locale prefers otherwise».

**Soglie ed eccezioni.** CLDR it: minimumGroupingDigits = 2; Designers Italia: punto delle migliaia da 10.000; euro con 2 decimali (TIPO-VALUTA).

**In DottorCloud.** DottorCloud ha due motori: Intl.NumberFormat (prezzo() in frontend/src/utils/valute.js, preventivi, cicli, abbonamenti, dashboard) e formatNumber/formatCurrency di frontend/src/utils/numberFormat.js con fmt_money del server (liste, PDF, email), che seguono il number_format del sito. Perché lo stesso importo non si legga «1234,50 €» nel preventivo e «1.234,50 €» in lista e nel PDF, il formattatore degli importi del browser usa useGrouping 'always'. formatCompactNumber è fisso su en-US («10.4K») e oggi non ha chiamanti: un compatto si chiede a Intl nella lingua dell'utente.

**Come si verifica.** Test in frontend/tests/unit/valute.test.js e numberFormat.test.js con importi di 4 cifre (oggi, con il formato del sito «#.###,##», formatCurrency(1234.5, '', 'EUR', 2) dà «1.234,50 €», mentre prezzo(1234.5, 'EUR', 'it') dà «1234,50 €»); grep -rn 'toFixed(' frontend/src per numeri mostrati senza formattatore; numeri allineati a destra con decimali coerenti nelle colonne.

**Errori da evitare.** L'incoerenza di raggruppamento tra Intl e Frappe sugli importi da 1.000 a 9.999 (verificata nel codice). Studio UX (ottobre 2026): «Precisione valuta» suggerisce 3 decimali mentre gli importi ne usano 2 (ancora così in DefaultsSettings.vue); una trattativa senza importo mostrava «0,00 €» (vuoto è vuoto, non zero: corretto); la virgola di «87,3%» quasi uguale al punto delle migliaia di «20.294 €» nei numeri grandi in grassetto.

**Vedi anche.** [FORM-NUMERI](06-moduli.md#form-numeri--numeri-e-importi-come-li-scrive-un-italiano)

**Fonti.**

- [Linguaggio (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/linguaggio/) — «Formatta il testo in modo coerente e accessibile»: «Numeri» · Designers Italia · 2025 (file del 14/04/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/linguaggio.yaml))
- [CLDR 48, main/it/numbers.json](https://github.com/unicode-org/cldr-json/blob/main/cldr-json/cldr-numbers-full/main/it/numbers.json) — minimumGroupingDigits, symbols-numberSystem-latn, percentFormats, decimalFormats short · Unicode CLDR · CLDR 48 (cldr-json 48.2.3), consultato l'11/10/2026
- [Intl.NumberFormat() constructor](https://developer.mozilla.org/en-US/docs/web/javascript/reference/global_objects/intl/numberformat/numberformat) — opzione useGrouping (always, auto, min2) · MDN Web Docs (Mozilla) · consultato l'11/10/2026 ([sorgente letto](https://github.com/mdn/content/blob/main/files/en-us/web/javascript/reference/global_objects/intl/numberformat/numberformat/index.md))

### TIPO-VALUTA · Prezzi come li scrive chi legge: «65,00 €»

**Regola.** In italiano un importo ha il simbolo dopo la cifra, separato da uno spazio non separabile, e due decimali per l'euro («65,00 €», «1.250,00 €»); in inglese il simbolo va prima («€65.00»); sullo schermo mai «65 EUR», «€ 65,00» o un codice ISO; una valuta si sceglie e si legge per nome («Euro») e si salva il codice; nel testo «euro» è minuscolo e invariabile («10 euro»).

**Perché.** CLDR 48 per l'italiano: formato valuta «#,##0.00 ¤» con U+00A0 tra cifra e simbolo; nome «euro», uguale al plurale (displayName-count-other «euro»); due decimali per le valute senza eccezione propria (currencyData, DEFAULT \_digits 2). Intl.NumberFormat('it', valuta EUR) dà «65,00 €», en-GB «€12.50» (test valute.test.js). Il W3C ricorda che posizione e spaziatura del simbolo cambiano con la lingua e che Intl.NumberFormat le gestisce. Il README di Espresso scrive invece «€ 1.250,00»: è la forma che il codice ha eliminato (lingue.euro_come_si_scrive mette il simbolo a destra per l'italiano perché /prenota, le trattative e le aziende leggevano «€ 60,00»).

**Soglie ed eccezioni.** CLDR: 2 decimali per l'euro; spazio U+00A0 tra cifra e simbolo.

**In DottorCloud.** prezzo(), nomeDellaValuta(), valuteDaScegliere() (frontend/src/utils/valute.js); conIlSimbolo() (frontend/src/utils/numberFormat.js, spazio non separabile); components/Controls/CampoValuta.vue; lingue.euro_come_si_scrive() e lingue.valuta() sul server. Il README del design system (brand/dottorcloud/design-system/espresso/README.md, sezione «Linguaggio») va corretto in «1.250,00 €», perché documentazione e codice dicano la stessa cosa. La precisione degli importi in euro è 2.

**Come si verifica.** frontend/tests/unit/valute.test.js e numberFormat.test.js (già: «65,00 €», «€12.50», «1.234,50 €»); grep -rn 'EUR' sui testi visibili per codici mostrati; un importo non va mai a capo staccato dal simbolo (prova a 320 px).

**Errori da evitare.** Il README di Espresso con «€ 1.250,00» contro il codice; «0 USD» sulla dashboard di un centro italiano prima di lingue.valuta() (lo racconta il suo commento); il codice «EUR» al posto del nome nelle scelte (corretto con CampoValuta); gli importi di 4 cifre raggruppati in due modi (TIPO-NUMERI).

**Fonti.**

- [CLDR 48, main/it/numbers.json](https://github.com/unicode-org/cldr-json/blob/main/cldr-json/cldr-numbers-full/main/it/numbers.json) — currencyFormats-numberSystem-latn (standard) · Unicode CLDR · CLDR 48 (cldr-json 48.2.3), consultato l'11/10/2026
- [CLDR 48, main/it/currencies.json](https://github.com/unicode-org/cldr-json/blob/main/cldr-json/cldr-numbers-full/main/it/currencies.json) — EUR: displayName, displayName-count-other, symbol · Unicode CLDR · CLDR 48 (cldr-json 48.2.3), consultato l'11/10/2026
- [CLDR 48, supplemental/currencyData.json](https://github.com/unicode-org/cldr-json/blob/main/cldr-json/cldr-core/supplemental/currencyData.json) — fractions DEFAULT (\_digits 2) · Unicode CLDR · CLDR 48 (cldr-json 48.2.3), consultato l'11/10/2026
- [Number, currency, and unit formatting](https://www.w3.org/International/questions/qa-number-format/) — «Currency symbol display» (Placement and spacing) e «The Intl.NumberFormat object» · W3C Internationalization (Fuqiao Xue) · 12/03/2026 ([sorgente letto](https://github.com/w3c/i18n-drafts/blob/gh-pages/questions/qa-number-format.en.html))

### TIPO-SPAZI-UNITA · Spazi che non si spezzano, unità del Sistema Internazionale

**Regola.** Tra un numero e ciò che misura o conta (unità, simbolo di valuta, mese abbreviato, nome: «2 ambulatori», «23 nov», «15 kg», «65,00 €») va uno spazio non separabile (U+00A0), così la riga non va a capo nel mezzo; le unità sono quelle del Sistema Internazionale, con il simbolo dopo uno spazio («3 km», «25 °C», «55 min»); le misure sono metriche.

**Perché.** Unicode (NamesList 17.0.0): U+00A0 NO-BREAK SPACE, «commonly abbreviated as NBSP», della stessa larghezza dello spazio; CLDR lo usa nel formato italiano della valuta e nel compatto («0 Mln»). Designers Italia: «Scrivi il numero in cifre, seguito dal simbolo dell'unità di misura nel Sistema Internazionale, separato da uno spazio» («3 km», «15 kg», «25 °C»). AGENTS: una misura è metrica.

**In DottorCloud.** conIlSimbolo() usa già lo spazio non separabile; le righe composte nei componenti (sedi «2 ambulatori», abbonamenti «4 venduti», lista d'attesa «fino al 23 nov») vanno composte con U+00A0 o con white-space: nowrap sul gruppo numero-parola; i piani alimentari usano g, kg e kcal (frontend/src/utils/piani.js).

**Come si verifica.** Prova a 320 px e con lo zoom del testo del doc 29 (280 punti) delle righe con numeri: nessun numero resta solo a fine riga; ricerca nei componenti delle concatenazioni di un numero e di una parola con lo spazio normale.

**Errori da evitare.** Studio UX (ottobre 2026): «· 2 / ambulatori» e «· 4 / venduti» con il numero a fine riga e il nome sotto; «fino al 23 / nov» e «in lista dal 7 / ott» nella lista d'attesa sul telefono; «2:11» a capo da solo.

**Fonti.**

- [Unicode 17.0.0 NamesList.txt](https://github.com/unicode-org/unicodetools/blob/main/unicodetools/data/ucd/17.0.0/NamesList.txt) — voce 00A0 NO-BREAK SPACE · Unicode Consortium · 2025
- [CLDR 48, main/it/numbers.json](https://github.com/unicode-org/cldr-json/blob/main/cldr-json/cldr-numbers-full/main/it/numbers.json) — currencyFormats e decimalFormats short (U+00A0) · Unicode CLDR · CLDR 48 (cldr-json 48.2.3), consultato l'11/10/2026
- [Linguaggio (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/linguaggio/) — «Formatta il testo in modo coerente e accessibile»: «Unità di misura» · Designers Italia · 2025 (file del 14/04/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/linguaggio.yaml))

### TIPO-RECAPITI · Telefoni, email e indirizzi leggibili e cliccabili

**Regola.** Un numero di telefono si mostra con il prefisso internazionale e le cifre a gruppi separati da spazi («+39 333 123 4567») ed è un link tel:, mentre si salva in formato E.164 senza spazi; «email» si scrive minuscola, senza trattino, e un indirizzo email è un link mailto:; un indirizzo postale ha una forma sola in tutto il prodotto («Via Roma 1, 20900 Monza (MB)»).

**Perché.** Designers Italia: per i numeri di telefono «Usa sempre anche il prefisso internazionale e raggruppa le cifre separandole con degli spazi», con link tel: («+39 06 123 456 78»); «La parola “email” si scrive senza trattini o spazi, in minuscolo», gli indirizzi email come link mailto:; gli indirizzi con le virgole tra via, CAP e città («Via Giulia 25, 00185, Roma»). Lo studio UX ha portato i numeri a gruppi in tutte le liste perché si leggono e si confrontano senza contare le cifre.

**In DottorCloud.** leggibile() in frontend/src/utils/telefono.js (cellulari «+39 333 123 4567», fissi di Milano e Roma «+39 02 1234 5678», gli altri fissi italiani con il prefisso del paese a parte, numeri esteri o mascherati lasciati come sono, E.164 in archivio); tastiera('telefono') per digitarli; indirizzo() e dove() in crm/scheduling/sedi_regole.py («Via Roma 1, 20900 Monza (MB)», la forma della busta: è quella di DottorCloud, diversa per una virgola da quella di Designers Italia, e resta l'unica).

**Come si verifica.** frontend/tests/unit/telefono.test.js; ricerca dei numeri mostrati senza leggibile() nei componenti; numeri ed email nelle pagine pubbliche e nelle email sono link.

**Errori da evitare.** Studio UX (ottobre 2026): «+393895552045» nelle liste e nelle carte del kanban (corretto in «+39 389 555 2045»). Un numero estero o mascherato riformattato a forza sarebbe sbagliato: leggibile() lo lascia com'era.

**Vedi anche.** [FORM-TELEFONO](06-moduli.md#form-telefono--un-telefono-in-un-campo-solo-accettato-come-lo-si-scrive)

**Fonti.**

- [Linguaggio (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/linguaggio/) — «Formatta il testo in modo coerente e accessibile»: «Numeri di telefono», «Email», «Indirizzi» · Designers Italia · 2025 (file del 14/04/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/linguaggio.yaml))

### I18N-FRASI-INTERE · Frasi intere, mai pezzi incollati

**Regola.** Ogni frase è una stringa sola da tradurre, con segnaposto numerati che il traduttore può spostare ({0}, {1}); non si incollano pezzi, parole tradotte a parte o nomi di DocType dentro una frase; se un sostantivo inserito cambierebbe articoli e accordi si scrive una frase per caso o la forma «argomento: valore»; una parola breve che in italiano ha due traduzioni prende un contesto (msgctxt); il nome del prodotto entra come {brand}.

**Perché.** ICU: un messaggio va scritto e tradotto «as a single unit»; se la stringa visibile fosse concatenata da frammenti, i traduttori non potrebbero riordinare i pezzi e faticherebbero a tradurre ciascun frammento; per le scelte (plurale, genere) «write full sentences in their sub-messages». Il W3C (Working with Composite Messages): le frasi composte da pezzi creano problemi di ordine delle parole e di accordo di genere e numero; con «The %s has been disabled» il francese avrebbe bisogno di tre frasi diverse; meglio stringhe separate o la forma argomento-commento («Disabled function: printer»); nelle frasi le variabili devono poter essere riordinate.

**In DottorCloud.** \_\_() del browser (frontend/src/translation.js: il contesto cercato come frase:contesto, {brand} con conMarchio, l'elisione dopo il riempimento); \_() e con_nome() sul server, prima di .format(); Messaggio e Rilievo del motore di fatturazione (doc 45 e 48); le frasi delle notifiche come costanti di crm/notifiche/regole.py, una per caso; testo(\_) per Problema ed Errore. Test esistenti: crm/tests/test_frasi_del_motore.py, crm/tests/test_frasi_delle_regole.py, frontend/tests/unit/paroleDaTradurre.test.js, frontend/tests/unit/areaParole.test.js.

**Come si verifica.** Revisione in PR di ogni \_\_() con segnaposto: il segnaposto è un valore (nome, numero, data), mai una parola da tradurre; ricerca delle concatenazioni di traduzioni (\_\_ seguito da + o + seguito da \_\_) nei .vue e .js; i test elencati sopra.

**Errori da evitare.** Studio UX (ottobre 2026): «Benvenuto a chi diventa {cliente}» nei dati di prova (crm/demo/dati.py), riempito con «patient» perché la traduzione cercata con \_(…, lang='it') in crm/demo/marketing.py restituiva l'inglese; il riassunto «last_visit 60 after» fatto di pezzi (corretto con una frase per caso); «ti ha menzionato in lead Mario Rossi» nelle notifiche (corretto, doc 40); «Twilio non è collegato: niente proposte via SMS», tradotto fuori contesto (la frase inglese, condivisa da tre pagine, dice che l'SMS non è tra i canali). Nel codice: AssignTo.vue compone «Hai tolto il {0} dagli assegnatari, quindi anche il {0} è stato tolto.» con {0} = «responsabile della persona» o «responsabile della trattativa», tradotto a parte e messo in minuscolo: funziona solo perché la parola è maschile e singolare.

**Fonti.**

- [ICU User Guide: Formatting Messages](https://github.com/unicode-org/icu/blob/main/docs/userguide/format_parse/messages/index.md) — «Overview» e «Complex Argument Types» · Unicode ICU · consultato l'11/10/2026
- [Working with Composite Messages](https://www.w3.org/International/articles/composite-messages/) — «Sentence-like arrangements», «Inflexible syntax», «Gender agreement», «Recommendations» · W3C Internationalization (Richard Ishida) · 2006, ultimo aggiornamento sostanziale 24/08/2021 ([sorgente letto](https://github.com/w3c/i18n-drafts/blob/gh-pages/articles/composite-messages/index.en.html))

### I18N-PLURALI · Plurali secondo CLDR: una frase per caso

**Regola.** Una frase con un numero ha almeno due versioni, scelte dal numero con le regole di plurale della lingua: in italiano «one» per 1 e «other» per 0, 2, 1,5 e il resto, più «many» per i milioni tondi («1 milione di persone»); lo 0 ha di solito una frase sua («Nessun appuntamento»); dove una frase per caso non basta si usa la forma argomento-valore («Appuntamenti senza esito: 3»); mai «{0} giorni» con 1, mai «giorno/i».

**Perché.** CLDR 48, regole cardinali per l'italiano: one «i = 1 and v = 0», many «e = 0 and i != 0 and i % 1000000 = 0 and v = 0 or e != 0..5», other per il resto; con Node 22 Intl.PluralRules('it') dà one per 1, other per 0, 2 e 1,5, many per 1.000.000 (prova del 12/10/2026). Regole ordinali: many per 8, 11, 80, 800, other per il resto. MDN: select() restituisce zero, one, two, few, many o other, e la forma plurale può cambiare nomi, verbi e pronomi. ICU: argomenti plural con frasi intere in ogni ramo. Il W3C nota che «%d page(s)» non risolve il problema nelle lingue con più forme di plurale e raccomanda, per i messaggi con un numero, la forma argomento-commento («Pages printed: %d»).

**Soglie ed eccezioni.** CLDR it: cardinale one / many / other; ordinale many (8, 11, 80, 800) / other.

**In DottorCloud.** Il traduttore di DottorCloud non ha la sintassi plurale di ICU: la regola del progetto è una frase per caso (commit 025e715: «the day after/before» al posto di «1 days», «1 year · {0}»; frontend/src/utils/quando.js separa «in 1 week» da «in {0} weeks»; crm/notifiche/regole.py ha WHATSAPP e WHATSAPP_MOLTI). Per scegliere il caso basta n === 1 in italiano e inglese; per una lingua futura new Intl.PluralRules(appLocale()).select(n).

**Come si verifica.** Script sul catalogo: msgid con un segnaposto seguito da un sostantivo plurale e senza variante al singolare (un'euristica grossolana ne trova alcune centinaia, molte false, protette dal chiamante: vanno viste una per una); test unitari con n = 0, 1, 2 per ogni helper che compone un conteggio (frontend/tests/unit/quando.test.js è il modello).

**Errori da evitare.** Studio UX (ottobre 2026): «1 giorni», «1 anni», «i suoi 1 clic», «in 1 weeks» (corretti); «Abbonamenti 1» sopra tre righe. Corretto il 12/10/2026: ESITI_OGGI ed ESITI_IERI di crm/notifiche/regole.py erano chiamati da crm/scheduling/esiti.py con il numero degli appuntamenti senza esito anche quando era 1, e la notifica diceva «1 appuntamenti di oggi sono senza esito: le persone sono venute?»; ora un appuntamento solo ha la sua frase (ESITO_OGGI, ESITO_IERI).

**Fonti.**

- [CLDR 48, supplemental/plurals.json](https://github.com/unicode-org/cldr-json/blob/main/cldr-json/cldr-core/supplemental/plurals.json) — plurals-type-cardinal, it · Unicode CLDR · CLDR 48 (cldr-json 48.2.3), consultato l'11/10/2026
- [CLDR 48, supplemental/ordinals.json](https://github.com/unicode-org/cldr-json/blob/main/cldr-json/cldr-core/supplemental/ordinals.json) — plurals-type-ordinal, it · Unicode CLDR · CLDR 48 (cldr-json 48.2.3), consultato l'11/10/2026
- [Intl.PluralRules](https://developer.mozilla.org/en-US/docs/web/javascript/reference/global_objects/intl/pluralrules) — Description (categorie e che cosa cambia con il plurale) · MDN Web Docs (Mozilla) · consultato l'11/10/2026 ([sorgente letto](https://github.com/mdn/content/blob/main/files/en-us/web/javascript/reference/global_objects/intl/pluralrules/index.md))
- [ICU User Guide: Formatting Messages](https://github.com/unicode-org/icu/blob/main/docs/userguide/format_parse/messages/index.md) — «Complex Argument Types» (plural, select, frasi intere) · Unicode ICU · consultato l'11/10/2026
- [Working with Composite Messages](https://www.w3.org/International/articles/composite-messages/) — «Number agreement» · W3C Internationalization (Richard Ishida) · 2006, ultimo aggiornamento sostanziale 24/08/2021 ([sorgente letto](https://github.com/w3c/i18n-drafts/blob/gh-pages/articles/composite-messages/index.en.html))

### I18N-LANG · La lingua dichiarata: della pagina e delle sue parti

**Regola.** Ogni pagina dichiara la sua lingua con l'attributo lang sull'elemento html, uguale alla lingua in cui l'utente legge (tag BCP 47 brevi: «it», «en»); un passaggio in un'altra lingua (il nome di una lingua scritto nella sua lingua, un testo rimasto in inglese, una citazione) ha il suo lang; nomi propri e termini entrati nell'uso non ne hanno bisogno; nomi accessibili e title non mescolano lingue.

**Perché.** WCAG 3.1.1 (A): la lingua predefinita di ogni pagina è determinabile dal programma, così i lettori di schermo caricano le regole di pronuncia giuste. WCAG 3.1.2 (AA): anche la lingua di ogni passaggio o frase, salvo nomi propri, termini tecnici, parole di lingua indeterminata e parole entrate nell'uso del testo intorno. Il W3C: «Always use a language attribute on the html tag», tenere il tag di lingua «as short as possible», e nel title o in un attributo non si possono marcare parti in un'altra lingua. MDN: lang vuoto rende la lingua sconosciuta, un valore non valido la rende invalida; il menu delle lingue di MDN mette lang su ogni voce. L'Understanding di 3.1.2: nei nomi accessibili il cambio di lingua si perde.

**Soglie ed eccezioni.** WCAG 3.1.1 livello A; 3.1.2 livello AA.

**In DottorCloud.** frontend/index.html e crm/www/crm.html (lang da boot.lang, con ripiego en; crm.py lo riempie con la lingua della sessione), frontend/area.html, crm/www/area.html, prenota.html, modulo.html, documento.html, lista_attesa.html, crm_form.html (lang da boot.lang, che i loro .py riempiono con la lingua della sessione o l'italiano): la lingua viene dall'utente o dal centro (lingue.del_centro(), solo italiano e inglese, LINGUE). Benvenuto.vue scrive i nomi delle lingue ognuno nella sua lingua con :lang. Se la lingua cambia senza ricaricare la pagina, si aggiorna anche document.documentElement.lang.

**Come si verifica.** axe-core html-has-lang, html-lang-valid, valid-lang, html-xml-lang-mismatch; prova con NVDA o VoiceOver in italiano su /crm, /area, /prenota, /modulo: nessuna parola letta con la voce inglese; cambio della lingua in Preferenze e verifica di lang dopo il ricaricamento.

**Errori da evitare.** Il ripiego en di index.html e crm.html: se un giorno il boot non portasse la lingua, la pagina si dichiarerebbe inglese anche a un utente italiano e il lettore di schermo leggerebbe l'italiano con la pronuncia inglese. Studio UX (ottobre 2026): «Social Planner» letto con la voce italiana; un aria-label inglese («progress») letto in inglese in una pagina italiana (corretto).

**Vedi anche.** [WCAG-3.1.1](03-wcag-utilizzabile-e-comprensibile.md#wcag-311--la-lingua-della-pagina-è-dichiarata-e-giusta-311-a), [WCAG-3.1.2](03-wcag-utilizzabile-e-comprensibile.md#wcag-312--le-parti-in-unaltra-lingua-sono-marcate-le-parole-inglesi-rimaste-si-traducono-312-aa)

**Fonti.**

- [Success Criterion 3.1.1 Language of Page](https://www.w3.org/TR/WCAG22/#language-of-page) — testo del criterio, livello A · W3C · 2023 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/language-of-page.html))
- [Success Criterion 3.1.2 Language of Parts](https://www.w3.org/TR/WCAG22/#language-of-parts) — testo del criterio ed eccezioni, livello AA · W3C · 2023 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/language-of-parts.html))
- [Understanding Language of Page](https://www.w3.org/WAI/WCAG22/Understanding/language-of-page.html) — Intent of Language of Page · W3C WAI · consultato l'11/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/main/understanding/20/language-of-page.html))
- [Declaring language in HTML](https://www.w3.org/International/questions/qa-html-language-declarations/) — Quick answer · W3C Internationalization (Richard Ishida) · 2011, aggiornato il 23/06/2021 ([sorgente letto](https://github.com/w3c/i18n-drafts/blob/gh-pages/questions/qa-html-language-declarations.en.html))
- [Choosing a language tag](https://www.w3.org/International/questions/qa-choosing-language-tags/) — «keep your language tag as short as possible»; «Decision 4: Region subtags» · W3C Internationalization (Richard Ishida) · 2009, aggiornato nel 2011, rivisto il 25/03/2026 ([sorgente letto](https://github.com/w3c/i18n-drafts/blob/gh-pages/questions/qa-choosing-language-tags.en.html))
- [lang HTML global attribute](https://developer.mozilla.org/en-US/docs/web/html/reference/global_attributes/lang) — Values; Accessibility concerns · MDN Web Docs (Mozilla) · consultato l'11/10/2026 ([sorgente letto](https://github.com/mdn/content/blob/main/files/en-us/web/html/reference/global_attributes/lang/index.md))

### I18N-FORMATI · Formati dalla lingua scelta dall'utente, non dal browser

**Regola.** Date, ore, numeri, valute, nomi di lingue e di fusi si formattano con Intl (dati CLDR) nella lingua che l'utente ha scelto in DottorCloud (appLocale()), mai in quella del browser o del sistema; l'inglese è quello europeo (en-GB: il giorno prima del mese, le 24 ore); la settimana comincia di lunedì ovunque; l'intestazione Accept-Language vale solo come primo indizio per chi non ha ancora scelto.

**Perché.** Il W3C: usare l'intestazione Accept-Language da sola per la località dell'utente «is not a good idea», perché molti non cambiano mai l'impostazione del browser e i computer si prestano: va usata al più come primo indizio, si lascia scegliere e si ricorda la scelta. Sui numeri: «Hardcoding formats is a brittle and unsustainable approach», l'oggetto Intl gestisce separatori, simboli e posizioni, di solito nella lingua della pagina. CLDR per l'Italia: firstDay mon, minDays 4; new Intl.Locale('it-IT').getWeekInfo() dà firstDay 1 (prova con Node 22). Il commento di appLocale() racconta il caso reale: «Domenica 16 agosto» sotto «Appointment», «2,8 Mio USD» su una dashboard inglese.

**Soglie ed eccezioni.** CLDR weekData: firstDay IT = mon, minDays IT = 4.

**In DottorCloud.** appLocale() (frontend/src/utils/locale.js) in ogni Intl; la lingua di ciascuno in Il tuo account › Preferenze («Come il centro» o la propria) e quella del centro in Impostazioni › Il centro › Generale › Lingua e fuso orario (CentreLanguageSettings.vue, lingue.save_centre_language); frontend/vite/frappeUi.js per i calendari di frappe-ui (lunedì, mesi in italiano); lingue.per_l_italia per System Settings. Su /prenota la lingua del browser vale solo se il boot non ne porta una con dizionario (crm/www/prenota.html).

**Come si verifica.** grep -rn 'navigator.language|toLocaleDateString()|toLocaleString()' frontend/src deve restare vuoto (all'11/10/2026 lo è; crm/www/prenota.html usa navigator.language solo come ripiego); frontend/tests/unit/locale.test.js (inglese all'europea); un utente in inglese con il browser in italiano, e viceversa: date e numeri seguono la lingua scelta.

**Errori da evitare.** Prima di appLocale(): date nella lingua del browser accanto a parole nella lingua dell'utente. Restano fissi su en-US formatCompactNumber (senza chiamanti) e getCurrencySymbol (che serve solo a estrarre il simbolo) in numberFormat.js. Un sito mai configurato restava sulla settimana da domenica e sul fuso di Kolkata (corretto da lingue.italia_dove_nessuno_ha_scelto).

**Fonti.**

- [Accept-Language used for locale setting](https://www.w3.org/International/questions/qa-accept-lang-locales/) — Answer (pubblicato su w3.org/International/questions/qa-accept-lang-locales) · W3C Internationalization (Lloyd Honomichl) · 2003, rivisto il 26/02/2016 ([sorgente letto](https://github.com/w3c/i18n-drafts/blob/gh-pages/questions/qa-accept-lang-locales.en.html))
- [Number, currency, and unit formatting](https://www.w3.org/International/questions/qa-number-format/) — Answer; «Choosing the right locale» · W3C Internationalization (Fuqiao Xue) · 12/03/2026 ([sorgente letto](https://github.com/w3c/i18n-drafts/blob/gh-pages/questions/qa-number-format.en.html))
- [CLDR 48, supplemental/weekData.json](https://github.com/unicode-org/cldr-json/blob/main/cldr-json/cldr-core/supplemental/weekData.json) — firstDay e minDays, IT · Unicode CLDR · CLDR 48 (cldr-json 48.2.3), consultato l'11/10/2026
- [Intl.Locale.prototype.getWeekInfo()](https://developer.mozilla.org/en-US/docs/web/javascript/reference/global_objects/intl/locale/getweekinfo) — Return value (firstDay, weekend, minimalDays) · MDN Web Docs (Mozilla) · consultato l'11/10/2026 ([sorgente letto](https://github.com/mdn/content/blob/main/files/en-us/web/javascript/reference/global_objects/intl/locale/getweekinfo/index.md))

### I18N-FUSO · L'ora del centro, e i giorni che non si spostano

**Regola.** Giorno e ora di un appuntamento, di un turno, di «oggi» e di «adesso» sono quelli dell'orologio del centro (il fuso del sito), mai quelli del telefono; una data senza ora (nascita, scadenza di un documento, giorno di una fattura) è una data fluttuante: si tratta come testo AAAA-MM-GG e non si converte mai in un istante (niente new Date('2026-10-11') mostrato in un altro fuso, niente toISOString() di una mezzanotte locale); un fuso si mostra con il nome della città nella lingua di chi legge.

**Perché.** Il W3C (Floating times): date come la nascita o la data di pubblicazione non sono legate a un fuso e «should never be attached to a particular time zone»; convertite in un Date e mostrate in un altro fuso slittano al giorno prima (l'edizione del 30 aprile 2017 letta come 29 aprile a Buenos Aires). MDN: timeZone accetta i nomi IANA. Il commento di oraDelCentro() in frontend/src/utils/scheduler.js (e il doc 29) registra il caso di DottorCloud: un istante UTC era l'orologio del telefono, e su un telefono in un altro fuso, o su un sito senza fuso, ogni salvataggio spostava l'appuntamento («00:00 became 03:30»). In Italia la mezzanotte locale è alle 23:00 UTC del giorno prima d'inverno e alle 22:00 d'estate: un toISOString() di quel momento porta il giorno prima.

**In DottorCloud.** sulCentro(), oraDelCentro(), adessoDelCentro(), oggiDelCentro() in frontend/src/utils/scheduler.js (AGENTS: mai dayjs() o new Date().toISOString() per ciò che il browser manda); nomeDelFuso() e fusiOrari() in frontend/src/utils/fusiOrari.js («Roma · Ora dell'Europa centrale», mai «Europe/Rome»); lingue.fusi_europei(); data di nascita e scadenze tenute come stringhe del server.

**Come si verifica.** Prove con il fuso del browser diverso da quello del centro (Chrome DevTools › Sensors › Location, per esempio America/New_York): prenotare, spostare, segnare un arrivo, aprire l'agenda di oggi; grep -rn 'toISOString()|dayjs()' frontend/src e verifica di ogni uso; frontend/tests/unit/fusiOrari.test.js e i test di scheduler.

**Errori da evitare.** Il fuso di ripiego del framework (Asia/Kolkata) dato a un sito mai configurato e ai suoi utenti: «adesso» e i promemoria tre ore e mezza avanti d'estate, quattro e mezza d'inverno (corretto da lingue.italia_dove_nessuno_ha_scelto e lingue.utenti_sul_fuso_del_centro); un giorno scelto nel calendario passato da toISOString() diventa il giorno prima.

**Vedi anche.** [FORM-ORE](06-moduli.md#form-ore--orari-a-24-ore-e-sempre-di-un-fuso-detto)

**Fonti.**

- [Floating times](https://www.w3.org/International/questions/qa-floating-times/) — Quick answer; Details, «An Example: Martina's Newspaper» (articolo in stato «review») · W3C Internationalization (Addison Phillips) · 2016, aggiornato il 03/06/2021 ([sorgente letto](https://github.com/w3c/i18n-drafts/blob/gh-pages/questions/qa-floating-times.en.html))
- [Intl.DateTimeFormat() constructor](https://developer.mozilla.org/en-US/docs/web/javascript/reference/global_objects/intl/datetimeformat/datetimeformat) — Locale options: timeZone · MDN Web Docs (Mozilla) · consultato l'11/10/2026 ([sorgente letto](https://github.com/mdn/content/blob/main/files/en-us/web/javascript/reference/global_objects/intl/datetimeformat/datetimeformat/index.md))

### I18N-RICERCA-ORDINE · Cercare e ordinare con le regole dell'italiano

**Regola.** Gli elenchi mostrati si ordinano dopo la traduzione, con Intl.Collator nella lingua dell'utente (accenti e maiuscole al posto giusto: «ape, Àrea, eco, Elena, èrba»); la ricerca nel browser ignora maiuscole e accenti (sensibilità base), come già fa il database, così «nicolo» trova «Nicolò»; ' e ’ valgono uguali in una ricerca.

**Perché.** MDN (Intl.Collator): con sensitivity «base» «a = á, a = A»; poiché la funzione centrale di una ricerca è filtrare senza badare ad accenti e maiuscole, «setting it to “base” makes the most sense». Il W3C (Sorting select options): un elenco tradotto va riordinato dopo la traduzione, lingua per lingua, perché l'ordine dell'originale non vale nella lingua di arrivo. Prove del 12/10/2026: con Node 22 l'ordinamento italiano dà «ape, Àrea, eco, Elena, èrba, zucca»; 'nicolò'.toLowerCase().includes('nicolo') è falso, mentre il confronto base li dà uguali; su MariaDB 10.11.14 con la collazione utf8mb4_unicode_ci che Frappe usa (frappe/database/mariadb/database.py) «nicolò» = «Nicolo» è vero, «D'Angelo» = «D’Angelo» è falso.

**In DottorCloud.** valuteDaScegliere() e fusiOrari() ordinano già con Intl.Collator; i filtri locali (frontend/src/components/frappe-ui/Autocomplete.vue, Settings/Hierarchy/UserMultiSelect.vue, Hierarchy.vue, Scheduling/TeamMatrix.vue) usano toLowerCase().includes, che distingue gli accenti: vanno portati su un confronto base (Collator con usage 'search', o normalize('NFD') senza i segni diacritici, come già fanno fold() in frontend/src/utils/dashboard.js e semplice() in frontend/src/utils/emoji.js, che porta anche ’ a '). Lato server la collazione di Frappe ignora accenti e maiuscole ma non l'apostrofo: le ricerche per nome normalizzano ' e ’.

**Come si verifica.** Test unitari della ricerca locale con «nicolo»/«Nicolò», «citta»/«città», «D'Angelo»/«D’Angelo»; elenchi di scelta tradotti in ordine alfabetico italiano; grep -rn 'toLowerCase().includes' frontend/src --include=\*.vue --include=\*.js per l'elenco dei filtri da controllare.

**Errori da evitare.** Filtri del browser che non trovano un nome accentato scritto senza accento, mentre la ricerca del server lo trova: lo stesso nome trovato in una pagina e non in un'altra. Un cognome salvato con l'apostrofo tipografico (da una tastiera che lo sostituisce da sé) non si trova cercando con quello dritto. Elenchi tradotti ma lasciati nell'ordine delle chiavi inglesi.

**Vedi anche.** [UX-RICERCA](01-interazione.md#ux-ricerca--ricerca)

**Fonti.**

- [Intl.Collator() constructor](https://developer.mozilla.org/en-US/docs/web/javascript/reference/global_objects/intl/collator/collator) — Parameters, options: usage, sensitivity · MDN Web Docs (Mozilla) · consultato l'11/10/2026 ([sorgente letto](https://github.com/mdn/content/blob/main/files/en-us/web/javascript/reference/global_objects/intl/collator/collator/index.md))
- [Sorting select options](https://www.w3.org/International/questions/qa-select-sorting/) — Answer · W3C Internationalization (Russ Rolfe) · 2003, rivisto il 05/11/2019 ([sorgente letto](https://github.com/w3c/i18n-drafts/blob/gh-pages/questions/qa-select-sorting.en.html))

### I18N-ESPANSIONE · Spazio per l'italiano, più lungo dell'inglese

**Regola.** Nessun testo dell'interfaccia sta in un contenitore di larghezza fissa pensato per l'inglese: pulsanti, schede, colonne, chip e intestazioni vanno a capo o si allargano, e un testo che serve a capire non si tronca con «…»; ogni schermata si prova in italiano, la lingua più lunga delle due, a 320 px e con lo zoom del testo; il database non limita la lunghezza dei testi tradotti.

**Perché.** Il W3C (Text size in translation) riporta i tassi medi di espansione dall'inglese alle lingue europee pubblicati da IBM: fino a 10 caratteri 200-300%, da 11 a 20 caratteri 180-200%, da 21 a 30 160-180%, da 31 a 50 140-160%, da 51 a 70 151-170%, oltre 70 130%; l'esempio di Flickr: «views» diventa «visualizzazioni», 3 volte più lungo. Raccomanda layout flessibili, testo che può andare a capo, niente contenitori stretti di larghezza fissa, e di pensarci anche nella lunghezza dei campi del database. Apple: scrivere «with accessibility and localization in mind». WCAG 1.4.4 (AA): il testo si ingrandisce fino al 200% senza perdere contenuto o funzioni.

**Soglie ed eccezioni.** Espansione media dall'inglese (IBM, citata dal W3C): ≤ 10 caratteri 200-300%; 11-20: 180-200%; 21-30: 160-180%; 31-50: 140-160%; 51-70: 151-170%; > 70: 130%. WCAG 1.4.4 (AA): testo al 200%.

**In DottorCloud.** Le regole del telefono di AGENTS lo prevedono già (nome intero e chip che vanno a capo con flex-wrap e min-w-0, una frase va a capo invece di fermarsi a metà, schede quante ne entrano accanto ad «Altro» con quanteNellaBarra in frontend/src/utils/sulTelefono.js, zoom fino a 280 punti). Le stringhe nascono in inglese nel codice: la prova si fa sempre in italiano. Le colonne delle tabelle hanno una larghezza minima e scorrono di lato.

**Come si verifica.** Giro delle schermate in italiano a 320 e 360 px e con lo zoom del testo al 200% (WCAG 1.4.4); elenco dei truncate su etichette che non sono nomi (grep -rn 'truncate' frontend/src --include=\*.vue); script sul catalogo che segnala le traduzioni più lunghe del doppio dell'originale sotto i 10 caratteri.

**Errori da evitare.** Studio UX (ottobre 2026): il testo d'esempio della ricerca tagliato; «Come il centro (Italianc» tagliato senza puntini nel campo Lingua delle Preferenze; date e numeri spezzati a fine riga sul telefono; le schede di persona e trattativa che uscivano dallo schermo sul computer (corretto: ora vanno sotto «Altro»).

**Vedi anche.** [TIPO-RIGA](04-aspetto.md#tipo-riga--lunghezza-della-riga-4575-caratteri-mai-oltre-80)

**Fonti.**

- [Text size in translation](https://www.w3.org/International/articles/article-text-size/) — introduzione e tabella «No. of characters in English source / Average expansion» (pubblicato su w3.org/International/articles/article-text-size) · W3C Internationalization (Richard Ishida) · 2007, rivisto il 01/02/2016 ([sorgente letto](https://github.com/w3c/i18n-drafts/blob/gh-pages/articles/article-text-size.en.html))
- [Writing (Human Interface Guidelines)](https://developer.apple.com/design/human-interface-guidelines/writing) — Getting started, «Write for everyone» · Apple · 2025 (ultima modifica 16/12/2025); consultato l'11/10/2026 ([sorgente letto](https://developer.apple.com/tutorials/data/design/human-interface-guidelines/writing.json))
- [Success Criterion 1.4.4 Resize Text](https://www.w3.org/TR/WCAG22/#resize-text) — testo del criterio, livello AA · W3C · 2023 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/sc/20/resize-text.html))

### I18N-NOMI · I nomi delle persone come li scrivono loro

**Regola.** Un nome si salva e si mostra come la persona lo scrive: apostrofi, trattini, spazi, accenti, maiuscole interne («D'Angelo», «Dell'Acqua», «De Luca», «McNamara»), anche di una sola lettera; le maiuscole si cambiano solo quando il testo arriva tutto maiuscolo o tutto minuscolo da un altro programma; un nome completo non si divide in nome e cognome indovinando il confine; i campi si chiamano «Nome» e «Cognome» e aprono la tastiera con la maiuscola a ogni parola e senza correzione automatica.

**Perché.** Il W3C (Personal names around the world): «Don't forget to allow people to use punctuation such as hyphens, apostrophes, etc. in names»; «Don't require names to be entered all in upper case»; «Don't normalize the casing in names» (McNamara, van der Waals): un modulo conserva le maiuscole che la persona scrive; «Don't assume that a single letter name is an initial»; prudenza con gli algoritmi che estraggono da soli le parti di un nome; campi abbastanza lunghi e nessun limite di lunghezza nel database.

**In DottorCloud.** tastiera('nome') in frontend/src/utils/tastiera.js (autocapitalize words, autocorrect off, spellcheck false) e tastieraDi() per nome, cognome e nome completo; nome_proprio() in crm/importazione/regole.py cambia le maiuscole solo a un testo tutto maiuscolo o tutto minuscolo («ROSSI» → «Rossi», «D'AMICO» → «D'Amico») e lascia com'è un nome scritto con le sue maiuscole; la ricerca per nome (crm/api/sul_telefono.py) e gli omonimi (due identificativi, rubrica dello studio).

**Come si verifica.** Test unitari di nome_proprio e dividi con «DE LUCA MARIO», «Maria Grazia De Luca», «DELL'ACQUA ANNA», «van der berg»; anteprima dell'importazione con un foglio di cognomi composti; ricerca di «D'Angelo» scritto con ' e con ’.

**Errori da evitare.** dividi() in crm/importazione/regole.py prende come cognome solo la prima parola quando la colonna mette il cognome prima, e solo l'ultima negli altri casi: «DE LUCA MARIO» diventa cognome «De» e nome «Luca Mario», «Maria Grazia De Luca» nome «Maria Grazia De» e cognome «Luca» (l'anteprima lo mostra prima di scrivere, ma il caso va gestito); nome_proprio() su un testo tutto minuscolo scrive «Van Der Berg»; un apostrofo tipografico non è uguale a quello dritto per il database (I18N-RICERCA-ORDINE).

**Vedi anche.** [FORM-NOMI](06-moduli.md#form-nomi--nomi-come-li-porta-la-persona)

**Fonti.**

- [Personal names around the world](https://www.w3.org/International/questions/qa-personal-names/) — Implications for field design: «To split or not to split?», «Strategies for splitting up names», «Other things» (pubblicato su w3.org/International/questions/qa-personal-names) · W3C Internationalization (Richard Ishida) · 2011, rivisto il 24/01/2016 ([sorgente letto](https://github.com/w3c/i18n-drafts/blob/gh-pages/questions/qa-personal-names.en.html))

### I18N-CODICI-IN-PAROLE · Si salva il codice, si mostra la parola

**Regola.** Valute, fusi orari, paesi, lingue, stati, priorità, modalità di pagamento e codici fiscali si salvano come codici e si mostrano sempre con il loro nome nella lingua di chi legge: «Euro» e non «EUR», «Roma · Ora dell'Europa centrale» e non «Europe/Rome», «Carta o app» e non «MP08», «inglese» e non «en»; il nome viene da Intl.DisplayNames e CLDR o dal vocabolario di DottorCloud, e un valore salvato che non è più tra le scelte resta visibile con il suo nome.

**Perché.** MDN: Intl.DisplayNames dà in modo coerente i nomi tradotti di lingue, regioni e scritture, e negli esempi anche delle valute. CLDR per l'italiano: «euro», «inglese» (con Node 22 new Intl.DisplayNames(['it'], {type: 'currency'}).of('EUR') dà «euro»). Designers Italia chiede di evitare o spiegare i termini tecnici; per la fatturazione AGENTS ne fa una regola (un campo che salva un codice non lo mostra mai), e lo stesso per valute e fusi.

**In DottorCloud.** nomeDellaValuta(), valuteDaScegliere() (frontend/src/utils/valute.js) e components/Controls/CampoValuta.vue; nomeDelFuso() e fusiOrari() (frontend/src/utils/fusiOrari.js); scelte.CAMPI, voci.py e scelte.PAESI per la fatturazione (doc 45); i valori delle liste passano da \_\_() (doc 40: «Da fare · In sospeso · In corso · Fatto»).

**Come si verifica.** frontend/tests/unit/valute.test.js, fusiOrari.test.js, scelte.test.js; giro delle liste con colonne a scelta: nessun codice visibile; ricerca nel testo visibile di codici tipici (tre maiuscole accanto a un importo, Europe/, MP seguito da due cifre).

**Errori da evitare.** Studio UX (ottobre 2026): maschere di formato mostrate come scelte («dd/mm/yyyy», «#.###,##»); la colonna «Stato» dei moduli che mostrava la versione («Versione 1») e la riga un percorso tecnico («/crm-form/…»). Nella storia del codice: la pagina dei pagamenti online mostrava il codice della valuta di Stripe e l'id dell'account (corretto nel commit e50b853).

**Vedi anche.** [LING-GERGO](#ling-gergo--niente-gergo-inglese-nomi-di-campo-o-codici)

**Fonti.**

- [Intl.DisplayNames](https://developer.mozilla.org/en-US/docs/web/javascript/reference/global_objects/intl/displaynames) — introduzione; Examples, «Currency Code Display Names» · MDN Web Docs (Mozilla) · consultato l'11/10/2026 ([sorgente letto](https://github.com/mdn/content/blob/main/files/en-us/web/javascript/reference/global_objects/intl/displaynames/index.md))
- [CLDR 48, main/it/currencies.json](https://github.com/unicode-org/cldr-json/blob/main/cldr-json/cldr-numbers-full/main/it/currencies.json) — EUR displayName · Unicode CLDR · CLDR 48 (cldr-json 48.2.3), consultato l'11/10/2026
- [Linguaggio (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/linguaggio/) — sottosezione «Termini tecnici, burocratici e stranieri» · Designers Italia · 2025 (file del 14/04/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/linguaggio.yaml))

### NORM-WCAG22 · Obiettivo WCAG 2.2 livello AA

**Regola.** Ogni schermata di DottorCloud (scrivania /crm, area pazienti /area, pagine pubbliche /prenota, /modulo, /lista-attesa, /documento) punta alla conformità WCAG 2.2 livello AA, che comprende la 2.1 AA chiesta oggi da EN 301 549 e dalle Linee guida AgID; i criteri AAA di questa famiglia (3.1.3 parole insolite, 3.1.4 abbreviazioni, 3.1.5 livello di lettura) sono obiettivi di scrittura, non promesse.

**Perché.** W3C: «Content that conforms to WCAG 2.2 also conforms to WCAG 2.0 and WCAG 2.1»; il gruppo di lavoro «recommends that sites adopt WCAG 2.2 as their new conformance target, even if formal obligations mention previous versions, to provide improved accessibility and to anticipate future policy changes». WCAG 2.2 è pubblicata il 5 ottobre 2023 e ripubblicata con errata il 12 dicembre 2024; aggiunge 2.4.11 Focus Not Obscured (Minimum) (AA), 2.5.7 Dragging Movements (AA), 2.5.8 Target Size (Minimum) (AA), 3.2.6 Consistent Help (A), 3.3.7 Redundant Entry (A), 3.3.8 Accessible Authentication (Minimum) (AA), più tre criteri AAA, e toglie 4.1.1 Parsing. La scheda del W3C WAI sull'Unione europea indica per la direttiva 2016/2102 la norma EN 301 549, che «Includes WCAG 2.1 Level AA verbatim without modifications for Web content», ed elenca la decisione di esecuzione (UE) 2021/1339 sulla norma armonizzata. Designers Italia: UNI CEI EN 301549:2021 corrisponde ai livelli A e AA di WCAG 2.1, e conviene lavorare già in ottica WCAG 2.2 per la norma attuale e per la futura norma armonizzata dell'European Accessibility Act. Le Linee guida AgID: quando l'UE recepisce un aggiornamento di EN 301 549, i loro riferimenti tecnici «sono automaticamente aggiornati».

**Soglie ed eccezioni.** Livelli A e AA di WCAG 2.2 (nuovi: 2.4.11, 2.5.7, 2.5.8, 3.2.6, 3.3.7, 3.3.8); 4.1.1 tolto in 2.2 ma ancora da verificare dove una norma chiede 2.0 o 2.1.

**In DottorCloud.** I criteri nuovi toccano i punti deboli di un gestionale usato al telefono: fuoco coperto da barre e fogli (2.4.11), trascinamenti in agenda e kanban (2.5.7), bersagli di almeno 24 px (2.5.8; DottorCloud punta a 44 px al tocco, frontend/src/telefono.css), dati da non chiedere due volte tra appuntamento e fattura (3.3.7), accesso all'area con un codice senza vietare l'incolla (3.3.8). Per questa famiglia: 2.4.2, 2.4.4, 2.4.6, 2.5.3, 3.1.1, 3.1.2, 3.2.4, 3.3.1, 3.3.2, 3.3.3.

**Come si verifica.** axe-core con i tag wcag2a, wcag2aa, wcag21a, wcag21aa, wcag22aa su ogni schermata (lo studio UX li ha usati con axe-core 4.10.3 nel suo giro, /home/frappe/ux/cattura.mjs); prove manuali per ciò che axe non vede (linguaggio, nomi coerenti, errori); dichiarazione di accessibilità con lo stato reale dove è dovuta (NORM-STANCA).

**Errori da evitare.** Dichiarare la conformità sulla base dei soli test automatici: Designers Italia avverte che non sono soddisfacenti per molti criteri di successo e che servono test manuali condotti da esperti qualificati. Confondere AA con AAA: i criteri di linguaggio AAA si inseguono ma non si promettono.

**Vedi anche.** [WCAG-QUADRO](02-wcag-percepibile-e-robusto.md#wcag-quadro--wcag-22-aa-come-metro-in-ogni-variante-della-pagina)

**Fonti.**

- [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/) — Introduzione; «Comparison with WCAG 2.1»; «New Features in WCAG 2.2»; Change Log (pubblicato su w3.org/TR/WCAG22/) · W3C · 2023, ripubblicata il 12/12/2024 ([sorgente letto](https://github.com/w3c/wcag/blob/main/guidelines/index.html))
- [Web Accessibility Laws & Policies: European Union](https://www.w3.org/WAI/policies/european-union/) — Web and Mobile Accessibility Directive (2016/2102): standard EN 301 549; documenti: decisione di esecuzione (UE) 2021/1339 · W3C WAI · aggiornato il 23/07/2025 ([sorgente letto](https://github.com/w3c/wai-policies-prototype/blob/master/_policies/european-union.md))
- [Accessibilità (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/accessibilita/) — «Linee guida e criteri di successo», «Nota sulle nuove WCAG 2.2», «Test automatici» e «Test manuali» · Designers Italia · 2025 (file del 28/01/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/accessibilita.yaml))
- [Linee guida sull'accessibilità degli strumenti informatici: Introduzione](https://github.com/AgID/lg-accessibilita-docs/blob/master/introduzione.rst) — «Riferimenti normativi tecnici e abrogazioni» · AgID · testo del repository ufficiale (file del 03/12/2019); consultato l'11/10/2026

### NORM-STANCA · Legge Stanca: chi obbliga e che cosa chiede

**Regola.** Prima di scrivere che la Legge 9 gennaio 2004, n. 4 (Legge Stanca) «si applica» a un centro o a NPM2 si verifica la categoria del soggetto. L'art. 3, comma 1, nomina le pubbliche amministrazioni dell'art. 1, comma 2, del D.Lgs. 165/2001, gli enti pubblici economici, le aziende private concessionarie di servizi pubblici, le aziende municipalizzate regionali, gli enti di assistenza e di riabilitazione pubblici, le aziende di trasporto e di telecomunicazione a prevalente partecipazione di capitale pubblico, le aziende appaltatrici di servizi informatici, gli organismi di diritto pubblico e tutti i soggetti che usufruiscono di contributi pubblici o agevolazioni per l'erogazione dei propri servizi tramite sistemi informativi o internet. Il comma 1-bis, inserito dall'art. 29 del DL 16 luglio 2020, n. 76, convertito con modificazioni dalla Legge 11 settembre 2020, n. 120, aggiunge gli altri soggetti che offrono servizi al pubblico attraverso siti web o applicazioni mobili con un fatturato medio, negli ultimi tre anni di attività, superiore a cinquecento milioni di euro. Per chi è obbligato, le Linee guida AgID chiedono WCAG 2.1 livello AA (EN 301 549), una dichiarazione di accessibilità riesaminata entro il 23 settembre di ogni anno e un meccanismo di feedback.

**Perché.** Il testo dell'art. 3, comma 1, è riportato nelle Linee guida AgID sull'accessibilità degli strumenti informatici («Soggetti destinatari»), scritte secondo l'art. 11 della legge dopo la riforma del D.Lgs. 10 agosto 2018, n. 106. Il comma 1-bis si legge nei dati aperti del Senato: il DL 76/2020 presentato per la conversione (Atto Senato n. 1883) lo inseriva con una soglia di «novecento milioni di euro», il testo approvato dal Senato sostituisce «novecento» con «cinquecento», e la scheda del disegno di legge registra la Legge n. 120 dell'11/09/2020; lo stesso articolo 29 rende «soggetti erogatori» anche quelli del comma 1-bis (art. 2, comma 1, lettera a-quinquies) e affida all'AgID l'accertamento e la sanzione delle loro violazioni, fino al 5 per cento del fatturato se non rimediano dopo la diffida (art. 9, comma 1-bis). Le Linee guida AgID chiedono la conformità WCAG 2.1 livello AA, equivalente ai punti da 9.1 a 9.4 e ai requisiti di conformità del punto 9.5 di UNI EN 301549:2018, per tutti i siti dal 23 settembre 2020, anche per le applicazioni rese disponibili su reti Intranet; il riesame della dichiarazione «Entro il 23 settembre di ogni anno» sulla piattaforma di AgID (la mancata pubblicazione è un inadempimento con la responsabilità dell'art. 9); un «Meccanismo di feedback»; e, se il soggetto non risponde o risponde in modo insoddisfacente entro trenta giorni, il ricorso al Difensore civico per il digitale. Le Linee guida di design AgID ricordano che le Linee guida sull'accessibilità sono state adottate con la Determinazione n. 396 dell'8 settembre 2020.

**Soglie ed eccezioni.** Comma 1-bis: fatturato medio superiore a 500 milioni di euro negli ultimi tre anni di attività (900 milioni nel testo originario del DL 76/2020, portati a 500 dalla conversione); sanzione per i soggetti del comma 1-bis fino al 5% del fatturato; dichiarazione riesaminata entro il 23 settembre di ogni anno; ricorso al Difensore civico per il digitale se manca una risposta soddisfacente entro 30 giorni.

**In DottorCloud.** Un centro medico privato non è obbligato per il solo fatto di fare sanità: lo è se rientra in una categoria dell'art. 3 (per esempio se usa contributi pubblici o agevolazioni per erogare i servizi online, o se è concessionario di un servizio pubblico). L'accreditamento con il Servizio sanitario non è nominato nel testo dell'articolo: è un caso da valutare con un legale. Il comma 1-bis riguarda solo chi supera i 500 milioni di fatturato medio. Il testo nomina le «aziende appaltatrici di servizi informatici»: NPM2 va considerata tale almeno quando fornisce DottorCloud in appalto a una pubblica amministrazione (per esempio un'azienda sanitaria pubblica), e allora le schermate fornite, anche quelle usate solo dal personale, devono rispettare le Linee guida AgID; la portata esatta va verificata con un legale. Tenere tutte le schermate a WCAG 2.2 AA (NORM-WCAG22) evita di dover distinguere cliente per cliente.

**Come si verifica.** Per ogni cliente pubblico o finanziato: verifica della categoria dell'art. 3 e della dichiarazione di accessibilità richiesta; lettura del testo vigente della Legge 4/2004 su Normattiva (non raggiungibile da questa revisione) prima di citarlo in un documento ai clienti, insieme alle regole che AgID dà per i soggetti del comma 1-bis; nei contratti con una PA, il riferimento alle Linee guida AgID.

**Errori da evitare.** Scrivere che la Legge Stanca vale per tutti i siti (vale per le categorie dell'art. 3) o che non vale mai per i privati (i commi 1 e 1-bis ne comprendono alcuni). Citare la soglia di 900 milioni del testo originario del decreto, che la conversione ha portato a 500. Prendere il testo del 2019 delle Linee guida AgID come ultima parola sui requisiti tecnici: si aggiornano con EN 301 549.

**Fonti.**

- [Linee guida sull'accessibilità degli strumenti informatici: Introduzione](https://github.com/AgID/lg-accessibilita-docs/blob/master/introduzione.rst) — «Soggetti destinatari» (art. 3, comma 1, della Legge 4/2004), «Riferimenti normativi internazionali e nazionali», «Tempi di attuazione» · AgID · testo del repository ufficiale (file del 03/12/2019); consultato l'11/10/2026
- [Linee guida sull'accessibilità degli strumenti informatici: Requisiti tecnici](https://github.com/AgID/lg-accessibilita-docs/blob/master/requisiti-tecnici-accessibilita-strumenti-informatici.rst) — requisiti per il web: applicazioni su reti Intranet; conformità WCAG 2.1 livello AA = punti da 9.1 a 9.4 e requisiti del punto 9.5 di UNI EN 301549:2018, per tutti i siti dal 23 settembre 2020 · AgID · testo del repository ufficiale (file del 03/12/2019); consultato l'11/10/2026
- [Linee guida sull'accessibilità degli strumenti informatici: Dichiarazione di accessibilità](https://github.com/AgID/lg-accessibilita-docs/blob/master/dichiarazione-accessibilita-e-pubblicazione-obiettivi-accessibilita.rst) — «Siti web e applicazioni mobili»: riesame entro il 23 settembre; responsabilità dell'art. 9 · AgID · testo del repository ufficiale (file del 03/12/2019); consultato l'11/10/2026
- [Linee guida sull'accessibilità degli strumenti informatici: Procedura di attuazione](https://github.com/AgID/lg-accessibilita-docs/blob/master/procedura-di-attuazione.rst) — «Meccanismo di feedback», «Difensore civico digitale» · AgID · testo del repository ufficiale (file del 08/08/2019); consultato l'11/10/2026
- [Linee guida di design per i siti internet e i servizi digitali della PA: 4.1 Accessibilità](https://designers.italia.it/normativa/linee-guida-di-design/requisito-4-1/) — Azione 1 e Riferimenti normativi (Determinazione n. 396 dell'8 settembre 2020) · AgID (pubblicato da Designers Italia) · 2025 (file del 08/10/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/normativa/linee-guida-di-design/requisito-4-1.yaml))
- [Atto Senato n. 1883 (XVIII legislatura): conversione in legge del decreto-legge 16 luglio 2020, n. 76, testo presentato](https://github.com/SenatoDellaRepubblica/AkomaNtosoBulkData/blob/master/Leg18/Atto00053158/ddlpres/01161385-ft.akn.xml) — testo del decreto, art. 29, comma 1, lettere b), c) e f) (artt. 2, 3, comma 1-bis, e 9, comma 1-bis, della Legge 4/2004) · Senato della Repubblica (dati aperti in Akoma Ntoso) · 2020; consultato il 12/10/2026
- [Atto Senato n. 1883 (XVIII legislatura): testo approvato dal Senato e trasmesso alla Camera](https://github.com/SenatoDellaRepubblica/AkomaNtosoBulkData/blob/master/Leg18/Atto00053158/ddlmess/01170597-ft.akn.xml) — modificazioni all'articolo 29, comma 1, lettera c): «la parola: “novecento” è sostituita dalla seguente: “cinquecento”» · Senato della Repubblica (dati aperti in Akoma Ntoso) · 2020; consultato il 12/10/2026
- [Dati aperti del Senato: disegni di legge della XVIII legislatura (dump-ddl-18)](https://github.com/SenatoDellaRepubblica/OpenData/blob/master/Leg18/dump-ddl-18.zip) — scheda http://dati.senato.it/ddl/53158 (S.1883): numeroLegge 120, dataLegge 2020-09-11 · Senato della Repubblica · estrazione del 12/10/2022; consultato il 12/10/2026
- [Web Accessibility Laws & Policies: Italy](https://www.w3.org/WAI/policies/italy/) — voce «Legge 9 gennaio 2004, n. 4 (Legge Stanca)» e voce sul D.Lgs. 106/2018 (la scheda non riporta il comma 1-bis) · W3C WAI · scheda del 30/05/2017, voce sul D.Lgs. 106/2018 del 14/03/2023; consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/wai-policies-prototype/blob/master/_policies/italy.md))

### NORM-EAA · European Accessibility Act: quali servizi, di chi l'obbligo

**Regola.** La Direttiva (UE) 2019/882 (European Accessibility Act) si applica dal 28 giugno 2025 ai prodotti e ai servizi che elenca, tra cui il commercio elettronico; le microimprese che forniscono servizi ne sono esentate. Prima di dire che riguarda DottorCloud si distingue: la scrivania usata dal personale del centro non vende e non fa pagare niente a chi la usa, quindi non è un servizio di commercio elettronico; /prenota con l'acconto, «Acquista online» e «Paga online» dell'area fanno concludere o pagare online un contratto alle persone e possono rientrarvi; in quel caso l'obbligo è di chi fornisce il servizio, cioè il centro, se non è una microimpresa. Il decreto italiano di recepimento e le linee guida AgID sull'EAA si citano solo dopo averli letti su Normattiva e sul sito di AgID.

**Perché.** La nota del W3C che mappa EPUB sull'EAA lo riassume così: la direttiva fissa requisiti di accessibilità per diversi tipi di prodotti e servizi, «including e-books, dedicated e-reading devices and software, digital rights management software, and e-commerce», ed è «enacted on 27 June 2019 to be forced from 28 June 2025». La nota del W3C sulla proprietà EPUB di esenzione cita il testo della direttiva: microimpresa è «an enterprise which employs fewer than 10 persons and which has an annual turnover not exceeding EUR 2 million or an annual balance sheet total not exceeding EUR 2 million»; l'art. 4, par. 5 dice che «Microenterprises providing services shall be exempt from complying with the accessibility requirements … and any obligations relating to the compliance with those requirements», segno che gli obblighi sui servizi ricadono su chi li fornisce; l'art. 14, par. 1 limita i requisiti dove imporrebbero una modifica sostanziale del servizio o un onere sproporzionato. La scheda del W3C WAI sull'Unione europea indica come ambito dell'EAA il settore pubblico e quello privato. Designers Italia: la norma armonizzata per l'EAA è ancora attesa, conviene lavorare già in ottica WCAG 2.2. Il testo della direttiva su EUR-Lex, il decreto italiano di recepimento e le pagine di AgID non erano raggiungibili da questa revisione.

**Soglie ed eccezioni.** Applicazione: dal 28 giugno 2025. Microimpresa: meno di 10 persone e fatturato annuo non superiore a 2 milioni di euro o totale di bilancio annuo non superiore a 2 milioni di euro.

**In DottorCloud.** /prenota con l'acconto su Stripe (crm/pagamenti, doc 60), «Acquista online» dell'area (crm/area/api.py, get_shop e buy_subscription) e «Paga online» delle fatture (pay_invoice) sono le pagine che possono concludere un contratto o un pagamento online: vanno tenute a WCAG 2.2 AA, pagamento compreso. Le pagine solo informative e la prenotazione senza pagamento sono casi da valutare con un legale. Nessun documento di DottorCloud dice che l'EAA «si applica» o «non si applica» senza questa analisi.

**Come si verifica.** Elenco aggiornato delle pagine pubbliche e dell'area che concludono un contratto o un pagamento; per ognuna axe-core con i tag wcag22aa ed EN-301-549 (axe-core li riporta nelle sue regole) e la prova completa da tastiera e con lettore di schermo, pagamento incluso; prima di dare un parere a un cliente, lettura degli artt. 2 e 3 della direttiva su EUR-Lex e del decreto italiano su Normattiva.

**Errori da evitare.** Dire che DottorCloud «è soggetto all'EAA» (per i servizi l'obbligo è del fornitore del servizio, cioè del centro) o che «non lo riguarda» (le sue pagine sono lo strumento con cui il centro fornisce il servizio); dimenticare l'esenzione delle microimprese; invocare l'onere sproporzionato senza documentarlo; leggere l'EAA come una legge su tutti i siti: vale per i prodotti e i servizi che elenca.

**Fonti.**

- [EPUB Accessibility - EU Accessibility Act Mapping](https://github.com/w3c/epub-specs/blob/main/wg-notes/epub-a11y-eaa-mapping/index.html) — introduzione (ambito dell'EAA e date) · W3C Publishing Maintenance Working Group (Editor's Draft) · consultato il 12/10/2026
- [The EPUB Accessibility exemption property](https://github.com/w3c/epub-specs/blob/main/wg-notes/a11y-exemption/index.html) — Introduction, «Overview»; valori eaa-microenterprise (definizione di microimpresa, art. 4, par. 5), eaa-disproportionate-burden e eaa-fundamental-alteration (art. 14, par. 1) · W3C Publishing Maintenance Working Group (Editor's Draft) · consultato il 12/10/2026
- [Web Accessibility Laws & Policies: European Union](https://www.w3.org/WAI/policies/european-union/) — voce «European Accessibility Act» (ambito: settore pubblico e privato; misure nazionali di recepimento) · W3C WAI · aggiornato il 23/07/2025 ([sorgente letto](https://github.com/w3c/wai-policies-prototype/blob/master/_policies/european-union.md))
- [Accessibilità (Fondamenti del design system .italia)](https://designers.italia.it/design-system/fondamenti/accessibilita/) — «Nota sulle nuove WCAG 2.2» · Designers Italia · 2025 (file del 28/01/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/design-system/fondamenti/accessibilita.yaml))
- [axe-core Rule Descriptions](https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md) — colonna Tags (EN-301-549, wcag22aa) · Deque Systems · axe-core 4.14, consultato l'11/10/2026

### NORM-GDPR-CHIARO · Informative e consensi in linguaggio semplice e chiaro

**Regola.** Le informazioni sul trattamento dei dati e le richieste di consenso che DottorCloud mostra per il centro (moduli da firmare, /prenota, area pazienti, iscrizione alla lista d'attesa, consenso all'assistente) sono concise, trasparenti, comprensibili e facili da trovare, scritte in linguaggio semplice e chiaro, e ancora più semplici quando sono destinate ai minori; il link all'informativa sta dove si raccolgono i dati.

**Perché.** Le Linee guida di design AgID (requisito 4.2, azione 5) riportano l'art. 12 del GDPR: informazioni «concise, trasparenti, intelligibili, facilmente accessibili, formulate con un linguaggio semplice e chiaro, specialmente nel caso d'informazioni destinate ai minori»; l'azione 7 chiede il link all'informativa «al momento della raccolta dei dati personali in ambiente online», o le informazioni sulla stessa pagina; l'azione 14 chiede che i fornitori di servizi informatici che trattano dati per conto dell'amministrazione siano nominati responsabili del trattamento (art. 28 GDPR). Il Manuale operativo di design rimanda alle icone del concorso «Informative chiare» del Garante e alle linee guida sulla trasparenza WP260 rev.01, fatte proprie dal Comitato europeo per la protezione dei dati con l'«Endorsement 1/2018» del 25 maggio 2018.

**In DottorCloud.** Le informazioni sono un obbligo di chi decide del trattamento, il centro; chi fornisce il servizio informatico, come NPM2, di regola tratta i dati per conto del centro (lo schema dell'azione 14). DottorCloud dà al centro gli strumenti: il registro dei consensi (crm/moduli/registro.py, consensi.py) con i testi nella lingua del centro (lingue.del_centro()), i moduli che congelano le parole firmate (crm/moduli/modelli.py), la riga sulla privacy dei pagamenti online. I testi di partenza scritti da DottorCloud seguono LING-CHIARO e LING-LEGGIBILITA; quelli riscritti dal centro restano suoi.

**Come si verifica.** Indice Gulpease e lettura ad alta voce dei testi di consenso spediti da DottorCloud; in ogni pagina che raccoglie dati personali il link all'informativa sta accanto al modulo; prova con un genitore che prenota per un figlio.

**Errori da evitare.** Doc 40: un modulo pubblicato mostrava i consensi in inglese («I have read the privacy notice.») accanto alle etichette italiane, perché il registro li aveva scritti nella lingua del sito al momento dell'installazione (corretto con lingue.del_centro() e la patch the_consents_speak_the_centres_language, che dà ai moduli già pubblicati una nuova versione). Un consenso riscritto dal centro non si traduce né si cambia da DottorCloud, e un testo firmato non si modifica: se ne fa una nuova versione.

**Vedi anche.** [PRIV-CONSENSO-GRANULARE](08-persone-e-dati-personali.md#priv-consenso-granulare--il-consenso-solo-dove-serve-per-finalità-al-momento-giusto-ritirabile-come-si-è-dato)

**Fonti.**

- [Linee guida di design per i siti internet e i servizi digitali della PA: 4.2 Affidabilità, trasparenza e sicurezza](https://designers.italia.it/normativa/linee-guida-di-design/requisito-4-2/) — Azioni 5, 7, 9 e 14 · AgID (pubblicato da Designers Italia) · 2025 (file del 08/10/2025); consultato l'11/10/2026 ([sorgente letto](https://github.com/italia/designers.italia.it/blob/main/src/data/content/normativa/linee-guida-di-design/requisito-4-2.yaml))
- [Manuale operativo di design: Privacy](https://github.com/italia/manuale-operativo-design-docs/blob/versione-corrente/doc/introduzione-design-servizi-pubblici-digitali/privacy.rst) — «Informativa privacy» · Designers Italia · 2025 (file del 07/02/2025); consultato l'11/10/2026
