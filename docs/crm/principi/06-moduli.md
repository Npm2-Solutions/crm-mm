# 6. Moduli e inserimento dei dati

<!-- Copyright (c) 2026, NPM2 Solutions Srl and contributors -->

Una delle famiglie dei [principi di esperienza e interfaccia](../66-principi-di-esperienza.md) (doc 66): come leggerle, la lista di controllo per una schermata e come sono state verificate le fonti sono lì.

Questa famiglia riguarda ogni punto in cui qualcuno scrive o sceglie un dato in DottorCloud: i dialoghi e le schede del gestionale (persona, appuntamento, fattura, impostazioni), l'area clienti e le pagine pubbliche /prenota e /modulo. In un centro medico un dato sbagliato non resta un refuso: diventa un paziente doppio, una fattura con il codice fiscale di un altro, un pagamento dichiarato tracciato che non lo è, una spesa che finisce nella dichiarazione precompilata di un altro. I principi uniscono il GOV.UK Design System (e govuk-frontend), W3C/WAI (WCAG 2.2 con Understanding e Techniques, il tutorial sui moduli, COGA, APG, l'articolo sui nomi di persona), WHATWG, MDN, web.dev, Designers Italia, Unicode CLDR, l'IAB (RFC 9413) e le librerie di riferimento per telefoni, indirizzi e codici (libphonenumber, libaddressinput, python-stdnum) ai difetti trovati nello studio UX di ottobre 2026 e a quelli verificati sul codice l'11/10/2026. Durante la ricerca i siti pubblici non erano raggiungibili: ogni fonte è stata letta, e poi riletta da una seconda revisione, l'11/10/2026 dal suo sorgente ufficiale su GitHub (alphagov/govuk-design-system e govuk-frontend, w3c/wcag, w3c/wai-tutorials, w3c/aria-practices, w3c/coga, w3c/i18n-drafts, whatwg/html, mdn/content, italia/designers.italia.it, GoogleChrome/web.dev, intarchboard/draft-protocol-maintenance, unicode-org/cldr, google/libphonenumber, google/libaddressinput, arthurdejong/python-stdnum, dequelabs/axe-core). Dove il sito pubblico è costruito da quel sorgente si cita l'indirizzo pubblico; dove la pagina pubblica può essere diversa si cita il file su GitHub: COGA (la bozza dell'editor; la versione pubblicata è su https://www.w3.org/TR/coga-usable/), web.dev (il sorgente archiviato, aggiornato al 30/11/2021) e la RFC 9413. NN/g, Baymard, Wroblewski e Penzo, il Service Manual di GOV.UK, l'Agenzia delle Entrate, il registro IBAN di SWIFT, EUR-Lex e Normattiva non erano raggiungibili e non sono citati: nessuna affermazione qui dipende da loro, e il fondamento giuridico di consensi e dati sanitari sta nella famiglia sulla privacy. In «apply» e «pitfalls», «aperto» e «corretto» descrivono il codice all'11/10/2026.

## I principi

- [FORM-NECESSARIO · Chiedere solo ciò che serve, sapendo perché](#form-necessario--chiedere-solo-ciò-che-serve-sapendo-perché)
- [FORM-UNA-DOMANDA · Una domanda alla volta, nell'ordine del lavoro reale](#form-una-domanda--una-domanda-alla-volta-nellordine-del-lavoro-reale)
- [FORM-PASSI · Più passi: dire dove si è e tornare indietro senza perdere nulla](#form-passi--più-passi-dire-dove-si-è-e-tornare-indietro-senza-perdere-nulla)
- [FORM-COLONNA · Una colonna, etichette sopra i campi](#form-colonna--una-colonna-etichette-sopra-i-campi)
- [FORM-ETICHETTA · Ogni controllo ha un'etichetta visibile, legata nel codice](#form-etichetta--ogni-controllo-ha-unetichetta-visibile-legata-nel-codice)
- [FORM-SEGNAPOSTO · Il segnaposto non è un'etichetta, né un aiuto, né un valore](#form-segnaposto--il-segnaposto-non-è-unetichetta-né-un-aiuto-né-un-valore)
- [FORM-AIUTO · L'aiuto è breve, visibile e legato al campo](#form-aiuto--laiuto-è-breve-visibile-e-legato-al-campo)
- [FORM-OBBLIGATORI · Obbligatori e facoltativi: una convenzione, spiegata e leggibile dalle tecnologie assistive](#form-obbligatori--obbligatori-e-facoltativi-una-convenzione-spiegata-e-leggibile-dalle-tecnologie-assistive)
- [FORM-LARGHEZZA · Il campo è largo quanto la risposta](#form-larghezza--il-campo-è-largo-quanto-la-risposta)
- [FORM-CAMPO-VISIBILE · Un campo si riconosce come campo](#form-campo-visibile--un-campo-si-riconosce-come-campo)
- [FORM-SCELTE · Il controllo giusto per ogni scelta](#form-scelte--il-controllo-giusto-per-ogni-scelta)
- [FORM-GRUPPI · I campi che vanno insieme sono un gruppo con un nome](#form-gruppi--i-campi-che-vanno-insieme-sono-un-gruppo-con-un-nome)
- [FORM-PREDEFINITI · Nessuna risposta data per scontata](#form-predefiniti--nessuna-risposta-data-per-scontata)
- [FORM-CONSENSI · Un consenso si dà, non si trova già dato](#form-consensi--un-consenso-si-dà-non-si-trova-già-dato)
- [FORM-TASTIERA · La tastiera giusta per ogni dato](#form-tastiera--la-tastiera-giusta-per-ogni-dato)
- [FORM-AUTOCOMPLETE · Il browser compila i dati di chi compila, non quelli degli altri](#form-autocomplete--il-browser-compila-i-dati-di-chi-compila-non-quelli-degli-altri)
- [FORM-INCOLLA · Incollare e farsi aiutare, sempre](#form-incolla--incollare-e-farsi-aiutare-sempre)
- [FORM-NON-RICHIEDERE · Ciò che il sistema sa già non si chiede di nuovo](#form-non-richiedere--ciò-che-il-sistema-sa-già-non-si-chiede-di-nuovo)
- [FORM-POSTEL · Accettare i formati reali, normalizzare dopo](#form-postel--accettare-i-formati-reali-normalizzare-dopo)
- [FORM-VALIDA-QUANDO · Validare al momento giusto](#form-valida-quando--validare-al-momento-giusto)
- [FORM-MESSAGGIO · Il messaggio d'errore dice cosa fare, con le parole dell'etichetta](#form-messaggio--il-messaggio-derrore-dice-cosa-fare-con-le-parole-delletichetta)
- [FORM-ERRORE-ACCANTO · L'errore sta accanto al campo, legato al campo e annunciato](#form-errore-accanto--lerrore-sta-accanto-al-campo-legato-al-campo-e-annunciato)
- [FORM-RIEPILOGO-ERRORI · Dopo un invio fallito: tutto in cima, niente perso, il fuoco sul riepilogo](#form-riepilogo-errori--dopo-un-invio-fallito-tutto-in-cima-niente-perso-il-fuoco-sul-riepilogo)
- [FORM-PULSANTE · Il pulsante d'invio è sempre attivo e dice cosa fa](#form-pulsante--il-pulsante-dinvio-è-sempre-attivo-e-dice-cosa-fa)
- [FORM-DOPPIO-INVIO · Un invio parte una volta sola](#form-doppio-invio--un-invio-parte-una-volta-sola)
- [FORM-SALVATAGGIO · Un modo di salvare per tipo di pagina, e si sa sempre se è salvato](#form-salvataggio--un-modo-di-salvare-per-tipo-di-pagina-e-si-sa-sempre-se-è-salvato)
- [FORM-BOZZE · Il lavoro interrotto non si perde](#form-bozze--il-lavoro-interrotto-non-si-perde)
- [FORM-IRREVERSIBILE · Prima di un invio che non si ritira: rivedere, confermare o poter annullare](#form-irreversibile--prima-di-un-invio-che-non-si-ritira-rivedere-confermare-o-poter-annullare)
- [FORM-FUOCO · Il cursore va dove serve e non salta da solo](#form-fuoco--il-cursore-va-dove-serve-e-non-salta-da-solo)
- [FORM-DATE · Date all'italiana, senza ambiguità](#form-date--date-allitaliana-senza-ambiguità)
- [FORM-ORE · Orari a 24 ore, e sempre di un fuso detto](#form-ore--orari-a-24-ore-e-sempre-di-un-fuso-detto)
- [FORM-NUMERI · Numeri e importi come li scrive un italiano](#form-numeri--numeri-e-importi-come-li-scrive-un-italiano)
- [FORM-TELEFONO · Un telefono in un campo solo, accettato come lo si scrive](#form-telefono--un-telefono-in-un-campo-solo-accettato-come-lo-si-scrive)
- [FORM-EMAIL · Un'email: tastiera giusta, controllo leggero, conferma restituendo l'indirizzo](#form-email--unemail-tastiera-giusta-controllo-leggero-conferma-restituendo-lindirizzo)
- [FORM-NOMI · Nomi come li porta la persona](#form-nomi--nomi-come-li-porta-la-persona)
- [FORM-INDIRIZZI · Indirizzi italiani: pochi campi, il CAP come testo](#form-indirizzi--indirizzi-italiani-pochi-campi-il-cap-come-testo)
- [FORM-CODICE-FISCALE · Il codice fiscale: accettato com'è scritto, controllato con il carattere di controllo](#form-codice-fiscale--il-codice-fiscale-accettato-comè-scritto-controllato-con-il-carattere-di-controllo)
- [FORM-PARTITA-IVA · Partita IVA: undici cifre con la cifra di controllo, prefisso accettato](#form-partita-iva--partita-iva-undici-cifre-con-la-cifra-di-controllo-prefisso-accettato)
- [FORM-IBAN · IBAN: incollato, in maiuscolo, a gruppi di quattro](#form-iban--iban-incollato-in-maiuscolo-a-gruppi-di-quattro)
- [FORM-CONTEGGIO · Limiti di lunghezza dichiarati, contati, mai tagliati in silenzio](#form-conteggio--limiti-di-lunghezza-dichiarati-contati-mai-tagliati-in-silenzio)
- [FORM-DOPPIONI · Prima di creare, cercare: una persona non nasce due volte](#form-doppioni--prima-di-creare-cercare-una-persona-non-nasce-due-volte)

### FORM-NECESSARIO · Chiedere solo ciò che serve, sapendo perché

**Regola.** Ogni campo di un modulo ha un uso che si sa dire: chi lo legge, in quale passo del lavoro, per fare cosa. Un dato che nessuno usa in quel momento non si chiede lì: resta nella scheda o dietro un «Aggiungi altri dati» facoltativo. Quando non è ovvio, il modulo dice perché chiede un dato (telefono, email, codice fiscale) e lascia scegliere come essere contattati.

**Perché.** GOV.UK (Question pages): «You should make sure you know why you’re asking every question and only ask users for information you really need», con il «question protocol» per decidere campo per campo. web.dev: «The simplest way to reduce form complexity is to remove unnecessary fields. That's also good for customer privacy». Il W3C (COGA, pattern «Design Forms to Prevent Mistakes») mette al primo posto «Requiring the user to enter as little information as possible». Designers Italia (Form) chiede, per un modulo lungo e complesso, di valutare se alcuni dati si hanno già «da altre fonti» e di farli solo validare. Per il telefono GOV.UK aggiunge: chiederlo solo se serve davvero, perché non tutti hanno o possono usare un telefono, e lasciare una scelta su come essere contattati. Nello studio UX di ottobre 2026 i campi superflui non erano solo rumore: spingevano sotto la piega quelli necessari e facevano creare doppioni.

**In DottorCloud.** Dialoghi rapidi del gestionale: i layout Quick Entry spediti da crm/install.py (LEAD_QUICK_ENTRY, DEAL_QUICK_ENTRY), disegnati da Modals/LeadModal.vue e Modals/DealModal.vue. Dal 10/10/2026 «Aggiungi una persona» chiede Nome e Cognome, Cellulare ed Email, Genere e Titolo, l'Azienda solo per nome e il Responsabile (patch crm/patches/v1_0/a_person_is_added_without_a_company.py); «Crea una trattativa» si apre con «Scegli una persona esistente» acceso e mostra i dieci campi d'azienda solo se si spegne «Scegli un'azienda esistente». Data di nascita e codice fiscale non si chiedono ancora: vivono nel profilo di fatturazione, ed è una decisione di prodotto aperta. Pagine pubbliche: /prenota chiede il telefono solo dove il servizio lo vuole (svc.require_phone in crm/www/prenota.html) e i moduli del sito (crm/moduli/sito.py) solo le domande del modello. Ogni modulo nuovo si progetta con una tabella «campo → chi lo usa → in quale passo»: un campo senza riga si toglie. Per i dati sanitari vale doppio: ciò che non si chiede non va protetto.

**Come si verifica.** Revisione del layout prima del merge con la tabella campo/uso. Prova su telefono a 390×844 px: nel dialogo rapido i campi necessari si vedono senza scorrere oltre campi facoltativi. Nessun campo nuovo senza la sua riga nella tabella. crm/tests/test_inserimento_rapido.py controlla l'ordine dei layout spediti.

**Errori da evitare.** Studio UX, ottobre 2026: «Aggiungi una persona» aveva 14 campi, con un intero blocco aziendale (Sito web, N. di dipendenti, Territorio, Ricavi annuali, Settore, Descrizione dell'azienda) e senza data di nascita né codice fiscale (gravità 3: il blocco aziendale è stato tolto durante lo studio, data di nascita e codice fiscale restano fuori); «Crea una trattativa» si apriva su dieci campi d'azienda e lasciava la persona sotto la piega, così la si riscriveva a mano e nasceva un doppione (gravità 3, corretto); «Azienda emittente» chiede Nome e Cognome anche a una «Struttura sanitaria autorizzata dalla Regione», perché first_name e last_name di CRM Invoicing Company non hanno depends_on (gravità 2, aperto). Da evitare: aggiungere un campo «perché potrebbe servire», che è un errore possibile in più e un dato in più da custodire.

**Vedi anche.** [PRIV-MINIMO-NEI-MODULI](08-persone-e-dati-personali.md#priv-minimo-nei-moduli--chiedere-solo-ciò-che-serve-compreso-ciò-che-serve-alla-sicurezza)

**Fonti.**

- [Question pages](https://design-system.service.gov.uk/patterns/question-pages/) — sezione «When to use this pattern» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Payment and address form best practices](https://github.com/GoogleChrome/web.dev/blob/main/src/site/content/en/blog/payment-and-address-form-best-practices/index.md) — «Only ask for the data you need» · web.dev (Google), Sam Dutton; sorgente archiviato del sito su GitHub · pubblicato il 09/12/2020, aggiornato il 30/11/2021
- [Making Content Usable for People with Cognitive and Learning Disabilities, pattern «Design Forms to Prevent Mistakes»](https://github.com/w3c/coga/blob/main/design-guide/o4p04-supportive-forms.html) — «What to Do» · W3C, COGA Task Force (bozza dell'editor, sorgente su GitHub) · consultato l'11/10/2026; versione pubblicata: https://www.w3.org/TR/coga-usable/
- [Form](https://designers.italia.it/design-system/componenti/form/) — «Come usarlo» › «Attenzione a» · Designers Italia · consultato l'11/10/2026
- [Phone numbers](https://design-system.service.gov.uk/patterns/phone-numbers/) — sezione «When to use this pattern» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026

### FORM-UNA-DOMANDA · Una domanda alla volta, nell'ordine del lavoro reale

**Regola.** Nelle pagine pubbliche (/prenota, /modulo, area clienti) si parte da una domanda per passo, con un titolo che è la domanda stessa (la legend o la label del campo fanno da h1). Nel gestionale, dove chi lavora ripete gli stessi compiti, più domande stanno nella stessa vista ma raggruppate in sezioni che sono domande del lavoro («Per chi è», «Cosa è stato fatto», «Come è stata pagata») e seguono il flusso vero: persona → servizio → quando → pagamento. Nessuna pagina riusa il titolo di un'altra; una domanda che chiede spiegazioni ha un titolo-affermazione e il testo sopra, non un aiuto lungo sotto il campo.

**Perché.** GOV.UK: «Asking just one question per question page helps users understand what you’re asking them to do, and focus on the specific question and its answer»; usare il contenuto della legend o della label come titolo fa sì che chi usa un lettore di schermo lo senta una volta sola. La stessa pagina ammette più domande insieme quando la ricerca lo mostra, per esempio in «an internal service for government users who need to repeat and switch between tasks quickly», e allora il titolo è un'affermazione. Il tutorial W3C sui moduli in più pagine chiede di dividere il modulo «according to its logical groups of controls». Nello studio UX la «Nuova fattura» è stata indicata come esempio positivo proprio perché le sue sezioni sono le domande del lavoro reale.

**In DottorCloud.** /prenota (crm/www/prenota.html) è già a passi: Sede (solo con più sedi) → Servizio → Professionista (se il servizio lo lascia scegliere) → Data e ora → I tuoi dati → Conferma; ogni vista ha il suo h2 («In quale sede?», «Con chi vuoi prenotare?», «Scegli giorno e orario», «I tuoi dati»), mentre il titolo della pagina resta lo stesso in tutti i passi: va aggiunto il nome del passo. Nel gestionale: Invoices/InvoiceDialog.vue ha sezioni-domanda («Per chi è», «Cosa è stato fatto», «Come è stata pagata»); Calendar/AppointmentPanel.vue mette i campi nell'ordine in cui la segreteria li decide (Servizio, Per chi, Data, Inizio e Fine, Professionista, Ambulatorio); Moduli/FormRenderer.vue disegna le sezioni del modello con titolo (h3) e descrizione. Le spiegazioni lunghe vanno sopra il gruppo (sul telefono Mobile/DescrizioneRipiegata.vue), non nell'aiuto del campo.

**Come si verifica.** Leggere ad alta voce i titoli di ogni passo: sono domande, o affermazioni sul solo contenuto del passo. Con VoiceOver o NVDA: un titolo principale per pagina o passo, la domanda letta una volta. Confronto dei `<title>` dei passi: nessuno uguale.

**Errori da evitare.** Studio UX, ottobre 2026: al primo passo di /prenota la carta «Riepilogo» diceva «Scegli un servizio per iniziare» mentre il passo chiedeva la sede (gravità 2, corretto: ora dice «Scegli una sede per iniziare.»); «Crea una trattativa» partiva dall'azienda in un centro dove 3 trattative su 4 non ne hanno una (gravità 3, corretto); «Nuova persona» chiedeva «Titolo» per primo (gravità 2, corretto: ora viene dopo «Genere»). Da evitare: un aiuto di più frasi sotto un campo al posto di una spiegazione sopra la domanda, che il lettore di schermo rilegge a ogni ingresso nel campo.

**Fonti.**

- [Question pages](https://design-system.service.gov.uk/patterns/question-pages/) — «Start by asking one question per page», «Asking multiple questions on a page», «Asking complex questions without using hint text» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Multi-page Forms](https://www.w3.org/WAI/tutorials/forms/multi-page/) — principi in apertura della pagina («Split the form up according to its logical groups of controls») · W3C WAI, Forms Tutorial · 2019 (ultimo aggiornamento 27/07/2019)

### FORM-PASSI · Più passi: dire dove si è e tornare indietro senza perdere nulla

**Regola.** Un modulo in più passi dice al primo passo quanti sono (solo se il numero è certo), scrive «Passo N di M» nel titolo della pagina e nell'intestazione, segna il passo corrente anche per il lettore di schermo (aria-current=step, testo nascosto per i passi completati), ha un «Indietro» che riporta al passo precedente con le risposte com'erano, e il pulsante indietro del browser o di Android fa lo stesso. Prima dell'invio finale mostra un riepilogo delle risposte, ciascuna con il modo di cambiarla.

**Perché.** W3C, Multi-page Forms: «If possible, the first step of a form should explain how many steps will follow. Each step should inform the user about the progress they are making»; il titolo della pagina con il progresso dà un riscontro immediato a chi usa un lettore di schermo («Step 2 of 4: Shipping Address – …»); l'indicatore a passi usa testo nascosto per il passo completato e per quello corrente. GOV.UK (Question pages): sempre un back link, perché alcuni non si fidano del pulsante indietro del browser, e non rompere quel pulsante, che deve riportare «in the state they last saw it»; provare prima senza indicatore, mettere il totale solo se affidabile; il servizio Carer’s Allowance ha tolto un indicatore a 12 passi «with no effect on completion rates or times». GOV.UK (Check answers): il riepilogo riduce gli errori perché dà una seconda occasione di accorgersene prima dell'invio. COGA: «I need to check my work and go back without losing the work I have just done».

**Soglie ed eccezioni.** «Passo N di M» solo con M certo (GOV.UK). GOV.UK sconsiglia gli indicatori che insieme mostrano tutte le domande, permettono di tornare alle precedenti e segnano quella corrente: spesso non si notano, prendono spazio e non stanno sugli schermi piccoli.

**In DottorCloud.** /prenota (crm/www/prenota.html): l'elenco dei passi è un `<nav>` chiamato «Passi della prenotazione», il passo corrente ha aria-current=step, i passi fatti sono pulsanti che riportano al passo con le scelte com'erano, i nomi dei passi a venire superano 4,5:1 (--faint, circa 4,7:1 sul fondo della pagina); restano da fare il titolo della pagina con «Passo N di M» e, sotto i 480 px, un modo di leggere i nomi dei passi a venire, oggi nascosti alla vista. Il «Riepilogo» accanto ai passi mostra sede, servizio, professionista, quando, durata e prezzo prima di «Conferma prenotazione»; il passo «Conferma» viene dopo l'invio. Nel gestionale l'indietro di Android chiude ciò che sta sopra (utils/indietro.js, chiudeConIndietro in pages/Calendar.vue) e Calendar/AppointmentPanel.vue chiede una volta sola prima di scartare.

**Come si verifica.** Compilare il passo 2, premere indietro nel browser e poi avanti: le risposte restano. VoiceOver: entrando in ogni passo si sente «Passo 2 di 4». axe-core color-contrast sui nomi dei passi. Su Android, indietro con un appuntamento scritto a metà: una sola domanda.

**Errori da evitare.** Studio UX, ottobre 2026: i nomi dei passi di /prenota erano #999 su #f7f7f7 (2,65:1) e il suggerimento del riepilogo 2,85:1 (gravità 3, corretto); l'elenco dei passi era un `<ol aria-label=progress>` letto in inglese a chi usa VoiceOver in italiano (gravità 1, corretto); sul telefono si legge il nome del solo passo corrente (gravità 1, aperto). Revisioni del codice: l'indietro di Android faceva perdere un appuntamento scritto a metà e, corretto quello, un secondo indietro apriva una seconda domanda sopra la prima (entrambi corretti). Da evitare: indicatori a molti passi che non stanno sul telefono, totali che cambiano a metà strada, un «Indietro» che riparte dal primo passo.

**Vedi anche.** [UX-GRADIENTE](04-aspetto.md#ux-gradiente--gradiente-dellobiettivo-ed-effetto-zeigarnik-avanzamento-visibile)

**Fonti.**

- [Multi-page Forms](https://www.w3.org/WAI/tutorials/forms/multi-page/) — «Indicating progress», «Using the page title», «Using step-by-step indicator» · W3C WAI, Forms Tutorial · 2019 (ultimo aggiornamento 27/07/2019)
- [Question pages](https://design-system.service.gov.uk/patterns/question-pages/) — «Back link», «Using progress indicators» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Check answers](https://design-system.service.gov.uk/patterns/check-answers/) — «How it works», «Let users go back and change their answers» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Making Content Usable for People with Cognitive and Learning Disabilities, pattern «Make it Easy to Undo Form Errors»](https://github.com/w3c/coga/blob/main/design-guide/o4p05-form-undo.html) — «User Need» · W3C, COGA Task Force (bozza dell'editor, sorgente su GitHub) · consultato l'11/10/2026; versione pubblicata: https://www.w3.org/TR/coga-usable/

### FORM-COLONNA · Una colonna, etichette sopra i campi

**Regola.** I campi stanno uno sotto l'altro, ciascuno con la sua etichetta sopra; si affiancano solo coppie corte che si leggono insieme (Nome e Cognome, CAP e Comune, Inizio e Fine). Sul telefono tutto è in una colonna, anche nelle schede: l'etichetta sopra il valore, il valore che va a capo invece di troncarsi. Tra un gruppo etichetta-campo-aiuto e il successivo c'è più spazio che tra un'etichetta e il suo campo.

**Perché.** GOV.UK (Text input): «You should align labels above the text input they refer to»; GOV.UK (Layout): «Design for small screens first, starting with a single-column layout». Il tutorial W3C sulle etichette: «placing labels above the form fields helps reduce horizontal scrolling for people with low vision and mobile device users», mantenendo un legame visivo stretto tra etichetta e campo. COGA: l'etichetta va «visible and next to the relevant control». WCAG 1.4.10 chiede che a 320 px CSS di larghezza non serva scorrere in due direzioni. Nello studio UX i moduli su tre colonne si leggevano a zig-zag tra anagrafica e recapiti.

**Soglie ed eccezioni.** WCAG 1.4.10 (AA): nessuno scorrimento in due dimensioni a 320 px CSS di larghezza (salvo le parti che hanno bisogno di due dimensioni, come le tabelle di dati); affiancate al massimo coppie brevi.

**In DottorCloud.** FieldLayout (Section.vue e Column.vue: le colonne si affiancano dove ciascuna ha 11rem, sm:basis-44, e sul telefono stanno una sotto l'altra), i layout Quick Entry di crm/install.py (dal 10/10/2026 a due per riga: Nome e Cognome, Cellulare ed Email, Genere e Titolo), le pagine delle Impostazioni con la variante impostazioni-strette (riquadro sotto 40rem). SidePanelLayout.vue mette ancora l'etichetta a sinistra del valore (w-[35%]) anche sul telefono: lì l'etichetta va sopra e il valore a tutta larghezza.

**Come si verifica.** Prova visiva a 1280 px, su tablet in verticale, a 360 e a 320 px. L'ordine del Tab segue quello visivo (WCAG 2.4.3). Nelle schede sul telefono nessun valore troncato con i puntini.

**Errori da evitare.** Studio UX, ottobre 2026: «Aggiungi una persona» e «Crea una trattativa» su tre colonne da circa 230 px, con «Descrizione dell'azienda» sola nella colonna centrale (gravità 2, corretti); «Orari e regole» con tre campi in fila e il fuso orario che andava a capo dentro la select, «Lista d'attesa» su due colonne con l'aiuto quasi alla stessa distanza da due campi (gravità 1); sul telefono le schede tengono l'etichetta a sinistra, circa il 36% della larghezza, e troncano email e nomi (gravità 2, aperto). Da evitare: affiancare campi solo per riempire lo spazio del desktop.

**Fonti.**

- [Text input](https://design-system.service.gov.uk/components/text-input/) — «How it works» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Layout](https://design-system.service.gov.uk/styles/layout/) — «Screen size» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Labeling Controls](https://www.w3.org/WAI/tutorials/forms/labels/) — «Visual position of label text» · W3C WAI, Forms Tutorial · 2024 (ultimo aggiornamento 13/05/2024)
- [Making Content Usable for People with Cognitive and Learning Disabilities, pattern «Use Clear Visible Labels»](https://github.com/w3c/coga/blob/main/design-guide/o4p06-clear-labels.html) — «What to Do» · W3C, COGA Task Force (bozza dell'editor, sorgente su GitHub) · consultato l'11/10/2026; versione pubblicata: https://www.w3.org/TR/coga-usable/
- [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/#reflow) — criterio di successo 1.4.10 Reflow (AA) · W3C · consultato l'11/10/2026

### FORM-ETICHETTA · Ogni controllo ha un'etichetta visibile, legata nel codice

**Regola.** Ogni campo, select, data, ora, selettore di persona, interruttore e gruppo di scelte ha un'etichetta testuale visibile: corta, iniziale maiuscola e resto minuscolo, senza due punti, nelle parole di chi lavora (mai un fieldname o un codice). L'etichetta è legata al controllo (label for, aria-labelledby verso quel testo, legend per i gruppi) e il nome accessibile contiene le parole visibili. Un'icona può accompagnare l'etichetta, non sostituirla; due campi diversi non hanno la stessa etichetta.

**Perché.** WCAG 3.3.2 (A): «Labels or instructions are provided when content requires user input»; l'Understanding ammette immagini come etichette solo se «widely understood» e ricorda che l'associazione nel codice è materia di 1.3.1 e il nome del controllo di 4.1.2. 2.5.3 Label in Name (A) vuole che il nome contenga il testo mostrato. Il tutorial W3C: «Whenever possible, use the label element»; il title come etichetta è «generally less reliable and not recommended». GOV.UK: «All text inputs must have labels, and in most cases the label should be visible»; le etichette sono «short, direct and written in sentence case. Do not use colons at the end of labels». COGA racconta chi non ritrova lo scopo di un controllo quando l'etichetta sparisce al cambio di fuoco. Designers Italia (Input): «Scegliere sempre etichette (label) testuali univoche per ogni campo».

**Soglie ed eccezioni.** WCAG 3.3.2, 1.3.1, 4.1.2 e 2.5.3: livello A.

**In DottorCloud.** Field.vue disegna l'etichetta e la lega al controllo con useEtichettaDelCampo (aria-labelledby, composables/nomeAlControllo.js); le righe delle Impostazioni con SettingsRow e useNomeAlControllo (label for); i pannelli laterali con useEtichetteDeiCampi (SidePanelLayout.vue); i filtri rapidi portano il nome del campo (QuickFilterField.vue, aria-label, corretto nello studio). Nel nuovo appuntamento (Calendar/AppointmentPanel.vue) «Inizio» e «Fine» hanno la loro etichetta visibile (corretto nello studio); Servizio ha solo un aria-label, Per chi solo il segnaposto «Per chi è?», Professionista solo i nomi: vogliono un'etichetta visibile sopra. Le pagine pubbliche usano `<label for>` (field() in crm/www/prenota.html). Le parole stanno in it.po; un campo di fatturazione non mostra mai il suo codice (scelte.CAMPI).

**Come si verifica.** axe-core 4.14: label (critico), select-name, button-name (le select di frappe-ui sono pulsanti), aria-input-field-name, aria-toggle-field-name, form-field-multiple-labels, label-content-name-mismatch (2.5.3) e label-title-only (best practice). A mano con VoiceOver e TalkBack: ogni campo si annuncia come «etichetta, tipo, valore».

**Errori da evitare.** Studio UX, ottobre 2026: nel nuovo appuntamento i campi avevano solo un'icona e il segnaposto («Scegli un servizio…», «Per chi è?»), la stessa icona-persona per paziente e professionista, due orari senza «Inizio» e «Fine» (gravità 2; «Inizio» e «Fine» corretti, il resto aperto); cinque select dei Formati senza nome, lette «pulsante, 3» (gravità 3); un'area di testo di «Aggiungi una persona» nominata solo dal title (axe label-title-only); «Dov'è» come etichetta della scelta del gestore email (gravità 2); due campi diversi chiamati «Azienda predefinita» con valori opposti (gravità 2); la seconda select dei filtri di Esercizi e Alimenti che dice solo «Tutti» (gravità 2).

**Vedi anche.** [WCAG-3.3.2](03-wcag-utilizzabile-e-comprensibile.md#wcag-332--ogni-campo-ha-unetichetta-visibile-e-le-istruzioni-che-servono-332-a)

**Fonti.**

- [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/#labels-or-instructions) — criterio 3.3.2 Labels or Instructions (A); criteri 1.3.1, 2.5.3 Label in Name, 4.1.2 · W3C · consultato l'11/10/2026
- [Understanding SC 3.3.2: Labels or Instructions](https://www.w3.org/WAI/WCAG22/Understanding/labels-or-instructions.html) — «Intent of Labels or Instructions» · W3C WAI · consultato l'11/10/2026
- [Labeling Controls](https://www.w3.org/WAI/tutorials/forms/labels/) — «Associating labels explicitly», «Using the title attribute» · W3C WAI, Forms Tutorial · 2024 (ultimo aggiornamento 13/05/2024)
- [Text input](https://design-system.service.gov.uk/components/text-input/) — «How it works» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Making Content Usable for People with Cognitive and Learning Disabilities, pattern «Use Clear Visible Labels»](https://github.com/w3c/coga/blob/main/design-guide/o4p06-clear-labels.html) — «How it Helps» · W3C, COGA Task Force (bozza dell'editor, sorgente su GitHub) · consultato l'11/10/2026; versione pubblicata: https://www.w3.org/TR/coga-usable/
- [Input](https://designers.italia.it/design-system/componenti/input/) — «Come usarlo» › «Attenzione a» · Designers Italia · consultato l'11/10/2026
- [axe-core Rule Descriptions](https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md) — «WCAG 2.0 Level A & AA Rules», «WCAG 2.1 Level A & AA Rules», «Best Practices Rules» · Deque Systems · axe-core 4.14, consultato l'11/10/2026

### FORM-SEGNAPOSTO · Il segnaposto non è un'etichetta, né un aiuto, né un valore

**Regola.** Il testo segnaposto non sostituisce l'etichetta, non porta istruzioni né esempi di formato, e non imita un valore: un campo vuoto si vede vuoto. È ammesso nei campi di ricerca libera, che hanno comunque un'etichetta (anche nascosta), e nei «Scegli…» dei selettori, purché dica che cosa si sceglie («Scegli il servizio»), si legga (4,5:1 sul fondo del campo) e stia tutto nello spazio. Un valore in vigore si scrive come testo, non come segnaposto pallido.

**Perché.** GOV.UK: «Do not use placeholder text in place of a label, or for hints or examples», perché sparisce quando si scrive (un problema per chi ha difficoltà di memoria e per chi rilegge le risposte), non tutti i lettori di schermo lo leggono e gli stili predefiniti dei browser spesso non raggiungono il contrasto di 1.4.3. Il tutorial W3C: «placeholder text is not a replacement for labels» e di solito è sotto il contrasto minimo. Designers Italia (Microtesti): i segnaposto servono per i campi liberi senza validazione, «come le barre di ricerca»; per le istruzioni di compilazione «usa invece l'helper text fisso posto sotto il componente»; nei menu di selezione si dice che cosa scegliere («Seleziona una regione»), non il generico «Seleziona un'opzione». La pagina Input di Designers Italia ammette anche il segnaposto per indicazioni sul formato: DottorCloud segue la regola più prudente dei Microtesti e di GOV.UK.

**Soglie ed eccezioni.** Testo del segnaposto almeno 4,5:1 sul fondo del campo (WCAG 1.4.3, AA); i componenti inattivi sono esenti.

**In DottorCloud.** getPlaceholder() di Field.vue scrive «Scegli…» per ogni Select e Link (Controls/Link.vue): va reso specifico o tolto, perché l'etichetta sta già sopra. Ricerche delle liste del telefono (components/Mobile/Elenco\*.vue): un'etichetta anche se nascosta e una frase corta che sta nella larghezza. Impostazioni (DefaultsSettings.vue, SealSettings.vue, AssistantSettings.vue, Telephony/TranscriptionSettings.vue, Invoicing/OnlinePayments.vue, ReviewSettings.vue): il comportamento reale si scrive come testo («2 (predefinito)»), un campo password non salvato resta vuoto e, quando una password c'è, si scrive «Password salvata · Cambia». Colore: ink-gray-4 (#959b99), che il design system riserva ai segnaposto e alle icone di contorno, fa 2,83:1 sul bianco e 2,56:1 sul fondo dei campi (#f1f4f3); per un segnaposto che dice qualcosa serve almeno ink-gray-5 (#6a716f, 4,99:1 sul bianco, 4,51:1 su #f1f4f3).

**Come si verifica.** Misurare il contrasto del segnaposto sul fondo del campo nei due temi e al passaggio del puntatore. Rileggere ogni campo compilato: si capisce ancora che cosa contiene senza il segnaposto? Cercare nel codice segnaposto che contengono formati, esempi o asterischi (sk\_, https://, \*\*\*).

**Errori da evitare.** Studio UX, ottobre 2026: «Precisione valuta» mostra un «3» segnaposto (:placeholder=3 in DefaultsSettings.vue) mentre gli importi usano 2 decimali (gravità 2, aperto); le password vuote mostrano «\*\*\*\*\*\*\*\*\*\*\*\*» come se fossero già salvate (gravità 2, aperto); «sk_live\_…» contraddice il passo che consiglia di partire con la chiave di prova (gravità 2, aperto); l'esempio del link per le recensioni Google sta dentro il campo (gravità 2, aperto); «Cerca un nome, un'azienda, un num» tagliato (gravità 1); segnaposto a 2,56:1 e 2,83:1, in due grigi diversi, così un campo vuoto sembrava compilato (gravità 2); «La valuta del paese del centro», il valore effettivo, scritto come segnaposto pallido (gravità 1). Ancora aperto: il grigio delle etichette (#6a716f) sul fondo che il campo prende al passaggio del puntatore (#ebeeed) scende a circa 4,3:1.

**Fonti.**

- [Text input](https://design-system.service.gov.uk/components/text-input/) — «Avoid placeholder text» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Form Instructions](https://www.w3.org/WAI/tutorials/forms/instructions/) — «Placeholder text», «Styling» · W3C WAI, Forms Tutorial · 2024 (ultimo aggiornamento 13/05/2024)
- [Microtesti](https://designers.italia.it/design-system/fondamenti/microtesti/) — «Includi aiuti contestuali di valore» · Designers Italia · consultato l'11/10/2026
- [Input](https://designers.italia.it/design-system/componenti/input/) — «Come usarlo» › «Buone pratiche sui contenuti» · Designers Italia · consultato l'11/10/2026
- [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/#contrast-minimum) — criterio 1.4.3 Contrast (Minimum) (AA), eccezione «Incidental» · W3C · consultato l'11/10/2026

### FORM-AIUTO · L'aiuto è breve, visibile e legato al campo

**Regola.** Un testo d'aiuto serve alla maggior parte di chi compila: a cosa serve il dato, dove trovarlo, in che formato. Sta tra l'etichetta e il campo o subito sotto, sempre visibile, è una frase breve e completa senza link, ed è legato al controllo con aria-describedby. Le spiegazioni lunghe vanno sopra il modulo o la sezione. Un tooltip porta solo informazioni accessorie: ciò che serve a compilare non vive solo lì.

**Perché.** GOV.UK: «Use hint text for help that’s relevant to the majority of users, like how their information will be used, or where to find it»; una sola frase breve; niente link, perché i lettori di schermo li leggono senza dire che sono link; niente spiegazioni lunghe, perché «Screen readers read out the entire text when users interact with the form element». Il tutorial W3C (Form Instructions): con aria-describedby l'istruzione arriva «after the label and other information is announced»; le istruzioni generali vanno prima del `<form>`, perché in «Forms Mode» i lettori di schermo leggono soprattutto i controlli. Designers Italia: istruzioni «utili e specifiche» («Inserisci una password di almeno 8 caratteri e con almeno una maiuscola», non «Inserisci una password sicura») nell'helper text fisso sotto il componente; tooltip «solo per indicazioni secondarie o accessorie».

**In DottorCloud.** La prop description di FormControl (frappe-ui) disegna l'aiuto con un id e lo mette in aria-describedby; quando c'è un errore, frappe-ui nasconde l'aiuto e lega l'errore. Field.vue la passa a testo, select, password, numeri e caselle, non a Link, DatePicker, DateTimePicker e TimePicker, dove l'aiuto va aggiunto e legato a mano. SettingsRow per le impostazioni; Mobile/DescrizioneRipiegata.vue per le spiegazioni lunghe sul telefono. Sui dispositivi touch i tooltip non si aprono (utils/puntatore.js): la regola del progetto vuole che ciò che dice un tooltip sia detto anche altrove. Etichetta e aiuto hanno stili diversi e l'aiuto sta più vicino al suo campo che al successivo: oggi in Field.vue l'etichetta è text-sm text-ink-gray-5, lo stesso grigio degli aiuti, mentre Moduli/FormFieldInput.vue la scrive già in ink-gray-8 di peso medio.

**Come si verifica.** Ispezione del DOM: aria-describedby del controllo punta all'id dell'aiuto. Lettore di schermo: si sente l'etichetta e poi l'aiuto. Nessun `<a>` negli aiuti. Sul telefono ogni informazione di un tooltip compare anche senza puntatore.

**Errori da evitare.** Studio UX, ottobre 2026: aiuti telegrafici, senza soggetto, con simboli e grassetti («Vuoto = il nome del tuo marchio», gravità 2); «Completa dal sito» spiegato solo da un tooltip che sul telefono non si apre (gravità 2, corretto: il pulsante compare solo quando c'è un sito web); etichette e aiuti nello stesso grigio e corpo, così non si distingue la domanda dalla spiegazione (gravità 2, aperto). Verifica sul codice (11/10/2026): in Activities/SMSBox.vue la spiegazione di «Caratteri speciali» (un carattere fuori dall'alfabeto SMS riduce ogni messaggio a 70 caratteri invece di 160) sta solo in un Tooltip; in Moduli/FormFieldInput.vue la descrizione di una domanda è uno `<span>` senza id, non legato al controllo.

**Fonti.**

- [Text input](https://design-system.service.gov.uk/components/text-input/) — «Hint text», «When not to use hint text», «Avoid links» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Question pages](https://design-system.service.gov.uk/patterns/question-pages/) — «Hint text» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Form Instructions](https://www.w3.org/WAI/tutorials/forms/instructions/) — «Overall instructions», «Using aria-describedby» · W3C WAI, Forms Tutorial · 2024 (ultimo aggiornamento 13/05/2024)
- [Microtesti](https://designers.italia.it/design-system/fondamenti/microtesti/) — «Includi aiuti contestuali di valore» · Designers Italia · consultato l'11/10/2026

### FORM-OBBLIGATORI · Obbligatori e facoltativi: una convenzione, spiegata e leggibile dalle tecnologie assistive

**Regola.** In DottorCloud un campo obbligatorio porta la croce del marchio dopo l'etichetta (segno-obbligatorio), e il controllo ha aria-required=true (o required, con novalidate sul modulo perché non compaiano i fumetti del browser) e il testo nascosto «(obbligatorio)»; il significato della croce si dice prima del primo uso («I campi con la croce sono obbligatori»). Nelle pagine pubbliche i campi facoltativi scrivono anche «(facoltativo)» nell'etichetta. Mai il solo colore, mai un simbolo senza spiegazione, mai un'abbreviazione come «obbl.».

**Perché.** Le fonti non concordano su che cosa segnare. GOV.UK: nella maggior parte dei casi «add ‘(optional)’ to the labels of optional fields» e «Never mark mandatory fields with asterisks»; spegne la validazione HTML5 (novalidate) e non mette required sui campi, perché i messaggi del browser non si possono rendere coerenti con i suoi. web.dev: un asterisco su ogni campo obbligatorio e una nota all'inizio del modulo che spiega l'asterisco. Designers Italia (Input): «Indicare chiaramente se la compilazione è opzionale oppure obbligatoria per l'invio del modulo»; i suoi Microtesti portano come esempio corretto «I campi con asterisco sono obbligatori». La tecnica H90 del W3C: se si usa un simbolo, «the user is advised of its meaning before the first use», e abbreviare «required» in «req.» confonde. La tecnica ARIA2: aria-required da solo non si vede, ma insieme a un segno visivo fa arrivare l'informazione alle tecnologie assistive. Il tutorial W3C mette «(required)» nell'etichetta e l'attributo required. Il design system Espresso ha scelto la croce al posto dell'asterisco (espresso.css, §7): ciò che conta è applicarla ovunque e renderla leggibile.

**Soglie ed eccezioni.** WCAG 3.3.2 (A) e 1.3.1 (A). Per 3.3.2 H90 è una delle tecniche sufficienti, insieme a etichette descrittive (G131); ARIA2 è solo consultiva per 3.3.2, 3.3.1 e 1.3.1, perché aria-required da solo non si vede.

**In DottorCloud.** espresso.css (§7) disegna la croce sia per il RequiredIndicator di frappe-ui sia per la classe segno-obbligatorio. frappe-ui fa già tutto se riceve required: TextInput mette required e aria-required, e RequiredIndicator aggiunge il testo nascosto «(required)», che vite/frappeUi.js rende traducibile al build e il catalogo (crm/locale/it.po) scrive «(obbligatorio)». Field.vue e Moduli/FormFieldInput.vue devono quindi dare al controllo aria-required (o required, senza fumetti del browser) e, per i selettori Link, data e ora, il testo nascosto, invece di disegnare solo una croce aria-hidden. /prenota (field() in crm/www/prenota.html) mette required sui campi, ha novalidate sul form e scrive «(facoltativo)» sui facoltativi, ma segna gli obbligatori con un asterisco rosso (span.req) che nessuna frase spiega.

**Come si verifica.** Ispezione del DOM: ogni controllo con la croce ha aria-required=true o required. VoiceOver e TalkBack dicono «obbligatorio». axe-core non lo verifica: controllo a mano o test d'unità sul rendering di un campo reqd in Field.vue.

**Errori da evitare.** Verifica sul codice (11/10/2026): in Field.vue e Moduli/FormFieldInput.vue la croce è uno span aria-hidden e il controllo non ha né required né aria-required (tranne le caselle di Field.vue): chi usa un lettore di schermo non sa che il campo è obbligatorio. Studio UX, ottobre 2026: nel nuovo appuntamento nessun segno diceva che servizio e paziente sono obbligatori, lo si scopriva solo premendo «Prenota l'appuntamento» (gravità 2). Da evitare: due convenzioni nella stessa pagina senza spiegarle; abbreviazioni come «obbl.»; il rosso come unico segno; required senza novalidate, che fa comparire i messaggi del browser al posto dei nostri.

**Vedi anche.** [WCAG-1.3.1-RELAZIONI](02-wcag-percepibile-e-robusto.md#wcag-131-relazioni--ciò-che-la-grafica-lega-il-codice-lega-etichette-gruppi-obbligatorio-errori)

**Fonti.**

- [Question pages](https://design-system.service.gov.uk/patterns/question-pages/) — «When to use this pattern» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Recover from validation errors](https://design-system.service.gov.uk/patterns/validation/) — «Turn off HTML5 validation» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Payment and address form best practices](https://github.com/GoogleChrome/web.dev/blob/main/src/site/content/en/blog/payment-and-address-form-best-practices/index.md) — «Help users avoid missing required data» · web.dev (Google), Sam Dutton; sorgente archiviato del sito su GitHub · pubblicato il 09/12/2020, aggiornato il 30/11/2021
- [Input](https://designers.italia.it/design-system/componenti/input/) — «Come usarlo» › «Attenzione a» · Designers Italia · consultato l'11/10/2026
- [Microtesti](https://designers.italia.it/design-system/fondamenti/microtesti/) — «Usa un linguaggio semplice e conciso», tabella VA BENE / NON VA BENE · Designers Italia · consultato l'11/10/2026
- [H90: Indicating required form controls using label or legend](https://www.w3.org/WAI/WCAG22/Techniques/html/H90) — «Description», «Using text to indicate required state» · W3C WAI, WCAG Techniques · consultato l'11/10/2026
- [ARIA2: Identifying a required field with the aria-required property](https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA2) — «Description», con la nota «This technique is set as advisory for meeting 3.3.2 Labels or Instructions» · W3C WAI, WCAG Techniques · consultato l'11/10/2026
- [Validating Input](https://www.w3.org/WAI/tutorials/forms/validation/) — «Validating required input» · W3C WAI, Forms Tutorial · 2019 (ultimo aggiornamento 27/07/2019)
- [WCAG — understanding/understanding.11tydata.js (le tecniche associate a ogni criterio, da cui sono costruite le pagine Understanding)](https://github.com/w3c/wcag/blob/main/understanding/understanding.11tydata.js) — voci «labels-or-instructions» (3.3.2: sufficient G131 con H90; advisory G13 e ARIA2), «error-identification» (3.3.1: advisory ARIA2), «info-and-relationships» (1.3.1: advisory ARIA2) · W3C, Accessibility Guidelines Working Group (sorgente su GitHub) · consultato l'11/10/2026

### FORM-LARGHEZZA · Il campo è largo quanto la risposta

**Regola.** La larghezza di un campo suggerisce che cosa scriverci: CAP 5 caratteri, provincia 2, codice fiscale 16, partita IVA 11, IBAN 27 più gli spazi dei gruppi, ore e piccoli numeri 6-8 caratteri con l'unità accanto, email almeno 30 caratteri visibili, nomi e indirizzi larghi. Una select è larga quanto la sua opzione più lunga o manda a capo il valore; sul telefono i campi lunghi occupano tutta la larghezza e quelli corti restano corti.

**Perché.** GOV.UK: «Help users understand what they should enter by making text inputs the right size for the content they’re intended for»; per i dati di lunghezza nota, campi a larghezza fissa: «Postcode inputs should be postcode-sized, phone number inputs should be phone number-sized»; le larghezze fisse restano tali su ogni schermo e si restringono solo se più larghe dello schermo. Per l'email: «make sure you can see at least 30 characters at once». Per gli indirizzi: il campo del codice postale più corto di quello della via. Designers Italia (Radio button): «Non troncare le etichette per le opzioni con i puntini di sospensione».

**Soglie ed eccezioni.** GOV.UK: l'esempio «Fixed width inputs» mostra larghezze per 20, 10, 5, 4, 3 e 2 caratteri; email almeno 30 caratteri visibili. Lunghezze italiane (python-stdnum e libaddressinput): CAP 5 cifre, provincia 2 lettere, codice fiscale 16 caratteri (11 cifre per chi non è persona fisica), partita IVA 11 cifre, IBAN 27 caratteri (33 con gli spazi dei gruppi di quattro).

**In DottorCloud.** Larghezze in ch o classi fisse: le ripetizioni nell'appuntamento sono già w-16 (Calendar/AppointmentPanel.vue), le ore del rimborso w-28 (Settings/Invoicing/OnlinePayments.vue); nei moduli pubblici (crm/public/js/moduli_campi.js) i numeri hanno max-width 12rem e le date 14rem. Le select delle Impostazioni prendono la larghezza dell'opzione più lunga o vanno a capo: il fuso orario in Settings/CentreLanguageSettings.vue è w-80 con la classe dc-valore-intero (index.css), che manda a capo il valore invece di tagliarlo; la lingua in Settings/PreferencesSettings.vue è ancora w-48 (192 px). Sul telefono i campi delle Impostazioni sono a tutta larghezza (max-md:w-full).

**Come si verifica.** Scrivere in ogni campo il valore reale più lungo: niente troncato. A 320 px i campi a larghezza fissa si restringono senza scorrimento orizzontale.

**Errori da evitare.** Studio UX, ottobre 2026: la select Lingua delle Preferenze, 192 px, mostrava «Come il centro (Italianc» e quella della Dashboard «La valuta del paese del» (gravità 2, aperto); campi per «24», «30», «2» larghi 350-384 px (gravità 1); «Scegli N. di dipendenti..» tagliato nel pannello della trattativa sul telefono. Da evitare: un CAP largo come la via; una select che tronca il valore scelto senza puntini e senza il valore intero nel nome accessibile.

**Fonti.**

- [Text input](https://design-system.service.gov.uk/components/text-input/) — «Use appropriately-sized text inputs», «Fixed width inputs» (esempio con le larghezze da 20 a 2 caratteri) · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Email addresses](https://design-system.service.gov.uk/patterns/email-addresses/) — «Help users to enter a valid email address» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Addresses](https://design-system.service.gov.uk/patterns/addresses/) — «How multiple text inputs work» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Radio button](https://designers.italia.it/design-system/componenti/radio-button/) — «Come usarlo» › «Buone pratiche sui contenuti» · Designers Italia · consultato l'11/10/2026
- [python-stdnum — stdnum/it/codicefiscale.py](https://github.com/arthurdejong/python-stdnum/blob/master/stdnum/it/codicefiscale.py) — docstring del modulo (16 caratteri per le persone fisiche, 11 cifre per gli altri soggetti) · Arthur de Jong e contributori (libreria open source) · consultato l'11/10/2026
- [python-stdnum — stdnum/it/iva.py](https://github.com/arthurdejong/python-stdnum/blob/master/stdnum/it/iva.py) — docstring del modulo («consists of 11 digits») · Arthur de Jong e contributori (libreria open source) · consultato l'11/10/2026
- [python-stdnum — stdnum/iban.dat](https://github.com/arthurdejong/python-stdnum/blob/master/stdnum/iban.dat) — riga IT (bban 1!a5!n5!n12!c: 23 caratteri, 27 con il paese e le due cifre di controllo) · Arthur de Jong e contributori (dati dal registro IBAN di SWIFT) · consultato l'11/10/2026
- [libaddressinput — testdata/countryinfo.txt](https://github.com/google/libaddressinput/blob/master/testdata/countryinfo.txt) — riga data/IT: zip «\d{5}», sub_keys (le sigle delle province, di due lettere) · Google · consultato l'11/10/2026

### FORM-CAMPO-VISIBILE · Un campo si riconosce come campo

**Regola.** Il contorno di un campo da compilare (bordo o fondo) ha almeno 3:1 sul colore accanto, nel tema chiaro e nello scuro; il campo si distingue dal pulsante (forma, colore, testo) e dal testo statico; un valore che non si può cambiare si mostra come testo in sola lettura, non come un campo spento indistinguibile dagli altri.

**Perché.** WCAG 1.4.11 (AA): le informazioni visive necessarie a identificare i componenti e i loro stati hanno almeno 3:1 sui colori adiacenti. L'Understanding chiarisce che il bordo serve «when there is no other visual way to identify the presence of the control» (ed è il caso di un campo vuoto) e porta come esempio conforme un campo con bordo grigio #767676 su bianco. I componenti inattivi sono esenti, e l'esempio dell'Understanding è proprio il pulsante d'invio disattivato finché mancano campi: può essere illeggibile pur essendo conforme. Nello studio UX i campi grigi senza bordo erano quasi invisibili.

**Soglie ed eccezioni.** 3:1 per il contorno del campo e i suoi stati (WCAG 1.4.11, AA); 4,5:1 per il testo dentro (1.4.3). axe-core 4.14 non ha regole per 1.4.11: si misura a mano.

**In DottorCloud.** FormControl di frappe-ui usa per default la variante subtle: fondo surface-gray-2 (#f1f4f3) con un bordo dello stesso colore, 1,11:1 sul bianco. La variante outline non basta: il suo bordo è outline-gray-2 (#e0e3e2), 1,29:1; il pannello del nuovo appuntamento la usa, quindi ha un bordo, ma sotto 3:1. Serve un bordo dato da un token in espresso.css di almeno 3:1: outline-gray-5 (#777e7c) fa 4,15:1 sul bianco, mentre outline-gray-3 (#c4c8c7) fa solo 1,69:1 e outline-gray-4 (#959b99) 2,83:1. Il token va ridefinito anche nel blocco del tema scuro, come chiede AGENTS: lì outline-gray-5 (#757c7a) fa 4,19:1 su surface-base (#151817).

**Come si verifica.** Misurare con un contrast checker il bordo o il fondo del campo contro la pagina, nei due temi. Prova a colpo d'occhio: in una schermata con campi vuoti si contano i campi senza cercarli.

**Errori da evitare.** Studio UX, ottobre 2026: nel dialogo «Nuova fattura» e nei filtri della lista d'attesa i campi erano rettangoli #f1f4f3 senza bordo su bianco (1,11:1) e «Emetti» disattivato aveva lo stesso grigio dei campi (gravità 2, aperto); all'ingresso dell'area clienti il campo email era a 1,04:1 sulla pagina e il pulsante spento sembrava un altro campo (gravità 3, corretto); sul telefono i campi delle schede non hanno bordo, e uno compilato sembra testo (gravità 2, aperto). Un bordo in outline-gray-2, outline-gray-3 o ink-gray-4 non basta (1,29:1, 1,69:1 e 2,83:1 sul bianco).

**Fonti.**

- [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/#non-text-contrast) — criterio 1.4.11 Non-text Contrast (AA) · W3C · consultato l'11/10/2026
- [Understanding SC 1.4.11: Non-text Contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html) — «Inactive User Interface Components», «Boundaries», «Adjacent colors» · W3C WAI · consultato l'11/10/2026
- [axe-core Rule Descriptions](https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md) — elenco completo delle regole: nessuna con l'etichetta wcag1411 · Deque Systems · axe-core 4.14, consultato l'11/10/2026
- [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/#contrast-minimum) — criterio 1.4.3 Contrast (Minimum) (AA) · W3C · consultato l'11/10/2026

### FORM-SCELTE · Il controllo giusto per ogni scelta

**Regola.** Una sola scelta fra poche opzioni: radio in un gruppo con legenda (fieldset e legend, o role=radiogroup con nome). Più scelte: caselle in un gruppo con legenda. Elenchi lunghi o che crescono (persone, servizi, comuni): combobox con ricerca, che per le persone mostra un secondo identificativo. Select solo come ultima risorsa per elenchi lunghi e stabili. Un controllo fatto a mano segue il pattern APG, tastiera compresa; una scelta esclusiva non si fa con pulsanti premuti/non premuti (aria-pressed); un interruttore serve per un'impostazione che vale subito, non per rispondere a una domanda.

**Perché.** GOV.UK: radio quando si può scegliere una sola opzione, caselle per più opzioni o per accendere e spegnere una cosa; radio affiancati solo con due opzioni corte; la select «should only be used as a last resort in public-facing services because research shows that some users find selects very difficult to use»: non riescono a chiuderla, provano a scriverci, confondono l'opzione a fuoco con quella scelta, non capiscono che si scorre. Designers Italia (Select): un gruppo di radio è da preferire, «in particolare se il numero di scelte è limitato»; (Radio button): il componente dà solo l'aspetto, la semantica va implementata seguendo i pattern del W3C o il fieldset. Pattern APG Radio Group: Tab entra nel gruppo sull'opzione scelta (o sulla prima), le frecce spostano e scelgono, Spazio sceglie; pattern Combobox: Freccia giù porta nell'elenco dei suggerimenti, Esc lo chiude, Invio accetta il suggerimento. Il tutorial W3C: «Radio button groups should always be grouped using `<fieldset>`».

**Soglie ed eccezioni.** Radio affiancati solo con 2 opzioni corte (GOV.UK). Tastiera APG: il gruppo è una sola fermata di Tab, frecce per cambiare, Spazio per scegliere.

**In DottorCloud.** Moduli/FormFieldInput.vue disegna le scelte singole come `<button role=radio>` in un role=radiogroup con nome: ogni opzione è una fermata di Tab e le frecce non fanno nulla; servono input nativi in un fieldset, come Settings/Invoicing/SceltaRadio.vue in HealthcareSetup.vue, o il roving tabindex dell'APG. /prenota esprime «Per me / Per un'altra persona» con due pulsanti aria-pressed, e i moduli pubblici (crm/public/js/moduli_campi.js) fanno lo stesso per le scelte singole, per Sì/No e per i consensi facoltativi: sono scelte esclusive, quindi gruppi di radio (un consenso necessario, che ha il solo «Acconsento», è una casella). In Invoices/InvoiceDialog.vue «Come è stata pagata» offre «Contanti», «Carta o app» e «Bonifico» come pulsanti aria-pressed in un role=group, accanto alla lista completa: anche lì la semantica giusta è un gruppo di radio. Controls/Link.vue (persone, servizi) è un combobox: nei risultati delle persone va mostrata la data di nascita o il telefono. Settings/ThemeSwitcher.vue è già un radiogroup di input radio nativi (corretto nello studio).

**Come si verifica.** Solo tastiera: il gruppo è una fermata di Tab, le frecce cambiano, Spazio sceglie. Lettore di schermo: «pulsante di opzione, 2 di 3, selezionato» e il nome del gruppo. axe-core: aria-required-attr, aria-toggle-field-name, nested-interactive.

**Errori da evitare.** Verifica sul codice (11/10/2026): i radio del motore dei moduli non rispondono alle frecce e ogni opzione è una fermata di Tab; /prenota, i moduli pubblici e la fattura esprimono scelte esclusive con pulsanti aria-pressed. Studio UX, ottobre 2026: il tema si sceglieva con tre riquadri che il Tab non raggiungeva (corretto con un radiogroup); il metodo di pagamento era una select già posata su «Bonifico» (gravità 3, corretto in parte: ora è una proposta dichiarata, vedi FORM-PREDEFINITI). Da evitare: uno switch per una risposta con effetti legali; select multiple; opzioni troncate.

**Fonti.**

- [Radios](https://design-system.service.gov.uk/components/radios/) — «When to use this component», «How it works», «Inline radios» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Checkboxes](https://design-system.service.gov.uk/components/checkboxes/) — «When to use this component», «How it works» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Select](https://design-system.service.gov.uk/components/select/) — «When to use this component», «Known issues and gaps» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Select](https://designers.italia.it/design-system/componenti/select/) — «Quando usarlo» › «Alternative a questo componente» · Designers Italia · consultato l'11/10/2026
- [Radio button](https://designers.italia.it/design-system/componenti/radio-button/) — «Come usarlo» › «Attenzione a» · Designers Italia · consultato l'11/10/2026
- [Radio Group Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/radio/) — «Keyboard Interaction» › «For Radio Groups Not Contained in a Toolbar» · W3C WAI, ARIA Authoring Practices Guide · consultato l'11/10/2026
- [Combobox Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/) — «Keyboard Interaction» › «Combobox Keyboard Interaction», «Listbox Popup Keyboard Interaction» · W3C WAI, ARIA Authoring Practices Guide · consultato l'11/10/2026
- [Grouping Controls](https://www.w3.org/WAI/tutorials/forms/grouping/) — «Associating related controls with fieldset» › «Radio buttons» · W3C WAI, Forms Tutorial · 2019 (ultimo aggiornamento 27/07/2019)

### FORM-GRUPPI · I campi che vanno insieme sono un gruppo con un nome

**Regola.** Più controlli che rispondono a una sola domanda o formano un solo dato (le opzioni di una scelta, giorno-mese-anno, le righe di un indirizzo, i dati di fatturazione accanto a quelli della persona) stanno in un fieldset con legend, o in un contenitore role=group (role=radiogroup per i radio) con aria-labelledby verso un titolo visibile. La legenda è breve; quando due gruppi hanno etichette uguali («Nome», «Indirizzo»), il gruppo le distingue. Niente fieldset annidati senza bisogno, niente role=group attorno a tutto il modulo.

**Perché.** Il tutorial W3C (Grouping Controls): raggruppare i controlli correlati rende il modulo più comprensibile per tutti, e va fatto «visually and in the code»; alcuni lettori di schermo leggono la legenda a ogni campo, una volta sola o, di rado, mai: quindi legende brevi ed etichette che si capiscono anche da sole. La tecnica H71: la legend è il primo elemento del fieldset, i fieldset non si annidano senza bisogno, il gruppo conta soprattutto per radio e caselle, ma serve anche ad altri controlli correlati, come i campi di un indirizzo. La tecnica ARIA17: role=group con aria-labelledby dove il fieldset non si può usare, role=radiogroup per i radio, e mai un role=group che avvolge tutto il modulo. GOV.UK (Date input): i tre campi di una data stanno in un fieldset con una legend che fa la domanda. WCAG 1.3.1 (A): struttura e relazioni mostrate a vista si determinano anche nel codice.

**Soglie ed eccezioni.** WCAG 1.3.1 (A) e 3.3.2 (A): H71 e ARIA17 sono tra le tecniche sufficienti di entrambi (per 3.3.2 ARIA17 vale insieme a etichette descrittive, G131).

**In DottorCloud.** Modello: Settings/Invoicing/HealthcareSetup.vue (fieldset con legend «Chi emette le fatture?» e radio nativi di SceltaRadio.vue). Moduli/FormFieldInput.vue dà già nome ai gruppi (role=radiogroup o role=group con aria-labelledby verso la domanda). /prenota («Per chi è») e i moduli pubblici (crm/public/js/moduli_campi.js) usano role=group con aria-labelledby, ma intorno a pulsanti aria-pressed: per una scelta esclusiva serve role=radiogroup con radio. In FieldLayout (Section.vue) il nome di una sezione è uno `<span>` dentro un `<div>` di CollapsibleSection.vue: non è un titolo né il nome di un gruppo; dove una sezione ripete le etichette di un'altra (i dati di fatturazione accanto a quelli della persona) il suo titolo va legato al gruppo (role=group con aria-labelledby) o reso un titolo. Una data di nascita in tre campi, se le pagine pubbliche la chiederanno, sta in un fieldset con la legend «Data di nascita».

**Come si verifica.** Ispezione del DOM: ogni gruppo ha fieldset e legend, o role=group o radiogroup con aria-labelledby verso un testo visibile. Con NVDA o VoiceOver: entrando nel gruppo si sente il suo nome, e due campi «Nome» di gruppi diversi si distinguono. axe-core non chiede i gruppi: si verifica a mano.

**Errori da evitare.** Verifica sul codice (11/10/2026): scelte esclusive dentro role=group fatte di pulsanti aria-pressed in /prenota, nei moduli pubblici e nella fattura; i nomi delle sezioni di FieldLayout non sono né titoli né nomi di gruppo. Da evitare: una legenda lunga, letta a ogni campo; fieldset annidati per sole ragioni di stile; un role=group attorno a tutto il dialogo, che ARIA17 esclude.

**Vedi anche.** [WCAG-1.3.1-RELAZIONI](02-wcag-percepibile-e-robusto.md#wcag-131-relazioni--ciò-che-la-grafica-lega-il-codice-lega-etichette-gruppi-obbligatorio-errori)

**Fonti.**

- [Grouping Controls](https://www.w3.org/WAI/tutorials/forms/grouping/) — introduzione; «Associating related controls with fieldset» › «Related fields» e nota sulle legende; «Associating related controls with WAI-ARIA» · W3C WAI, Forms Tutorial · 2019 (ultimo aggiornamento 27/07/2019)
- [H71: Providing a description for groups of form controls using fieldset and legend elements](https://www.w3.org/WAI/WCAG22/Techniques/html/H71) — «Description» · W3C WAI, WCAG Techniques · consultato l'11/10/2026
- [ARIA17: Using grouping roles to identify related form controls](https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA17) — «Description» · W3C WAI, WCAG Techniques · consultato l'11/10/2026
- [Date input](https://design-system.service.gov.uk/components/date-input/) — «How it works» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/#info-and-relationships) — criterio 1.3.1 Info and Relationships (A) · W3C · consultato l'11/10/2026
- [WCAG — understanding/understanding.11tydata.js (le tecniche associate a ogni criterio, da cui sono costruite le pagine Understanding)](https://github.com/w3c/wcag/blob/main/understanding/understanding.11tydata.js) — voci «info-and-relationships» (1.3.1: ARIA17 e H71 tra le sufficienti) e «labels-or-instructions» (3.3.2: G131 con ARIA17; H71) · W3C, Accessibility Guidelines Working Group (sorgente su GitHub) · consultato l'11/10/2026

### FORM-PREDEFINITI · Nessuna risposta data per scontata

**Regola.** In una domanda (fattura, appuntamento, persona, modulo, prenotazione) nessun radio, casella, select o data parte già scelto, e un numero vuoto resta vuoto: mai un «0» o un «0,00 €» che nessuno ha detto. Un valore predefinito si usa nelle impostazioni, o quando è vero quasi sempre, e si mostra come proposta da confermare. Se il dato manca, il campo resta vuoto e il controllo prima dell'invio lo dice.

**Perché.** GOV.UK (Radios e Checkboxes): «Do not pre-select radio options as this makes it more likely that users will» non accorgersi di aver saltato una domanda («not realise they've missed a question») o dare la risposta sbagliata («submit the wrong answer»). GOV.UK (Select): nelle impostazioni un'opzione può essere preselezionata, nelle domande no, «in case it influences users' answers». Designers Italia (Select): «Non preselezionare nessuna delle opzioni se il componente serve all'utente per rispondere a domande, ne influenzerebbe la risposta». L'APG ricorda che un gruppo di radio può partire senza scelta proprio per obbligare a scegliere. Nello studio UX un predefinito falso finiva nei dati fiscali.

**In DottorCloud.** I predefiniti dei DocType non devono arrivare come risposta. Oggi una fattura nuova parte ancora su «Bonifico» (payment_method MP05, il predefinito del DocType), ma Invoices/InvoiceDialog.vue lo dichiara («È il modo predefinito, non ancora confermato: tocca come ha pagato davvero, la chiusura di cassa conta su questo.») e offre tre scelte rapide finché nessuno sceglie: è la proposta da confermare che lo studio ha introdotto, non ancora il campo vuoto che la regola chiede. Field.vue disegna un intero vuoto come «0» (data[field.fieldname] || '0') e flt() di utils/numberFormat.js legge una stringa vuota come 0: un numero non detto deve restare vuoto. I selettori di data con clearable spento (Calendar/AppointmentPanel.vue, Modals/EventModal.vue, Calendar/CalendarEventPanel.vue) trasformano un campo svuotato nella data di oggi secondo il browser (dayjsLocal di frappe-ui), non secondo il centro (oggiDelCentro). Le pagine delle Impostazioni possono partire dai predefiniti del DocType (DocFields), perché sono impostazioni.

**Come si verifica.** Aprire ogni dialogo di creazione e salvare senza toccare nulla: nel database nessun valore che nessuno ha scelto. Test d'unità sul rendering di un intero vuoto. Elenco dei default dei DocType che toccano fattura, persona e appuntamento, con chi li ha decisi.

**Errori da evitare.** Studio UX, ottobre 2026: «Modalità di pagamento» partiva su «Bonifico» («Tracciabile.»), così una visita pagata in contanti risultava pagata con un mezzo tracciato, il dato del pagamento tracciato che DottorCloud manda al Sistema TS, e la chiusura di cassa non tornava (gravità 3, corretto in parte: ora è una proposta dichiarata da confermare); «Ricavi annuali 0,00 €» e «N. di dipendenti 1-10» già scelti (gravità 2, corretto); «Responsabile della persona» proposto su «DottorCloud», cioè l'utente Administrator (gravità 1). Revisioni del codice: una trattativa senza importo si leggeva «0,00 €» nella lista e nel kanban; l'avviso sul metodo di pagamento si rimetteva da solo a ogni salvataggio (corretti).

**Vedi anche.** [UX-DEFAULT](01-interazione.md#ux-default--valori-predefiniti), [PRIV-PREDEFINITO-PROTETTIVO](08-persone-e-dati-personali.md#priv-predefinito-protettivo--ciò-che-fa-uscire-o-mostrare-dati-parte-spento)

**Fonti.**

- [Radios](https://design-system.service.gov.uk/components/radios/) — «How it works» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Checkboxes](https://design-system.service.gov.uk/components/checkboxes/) — «How it works» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Select](https://design-system.service.gov.uk/components/select/) — «How it works» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Select](https://designers.italia.it/design-system/componenti/select/) — «Come usarlo» › «Attenzione a» · Designers Italia · consultato l'11/10/2026
- [Radio Group Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/radio/) — «About This Pattern» · W3C WAI, ARIA Authoring Practices Guide · consultato l'11/10/2026

### FORM-CONSENSI · Un consenso si dà, non si trova già dato

**Regola.** Ogni consenso (informativa, marketing, richieste di recensione, assistente) è una scelta separata e mai già fatta: una casella non spuntata, o «Acconsento» e «Non acconsento» senza nessuno dei due scelto; accanto c'è il testo che la persona legge e il collegamento all'informativa completa; il consenso necessario al servizio è distinto da quelli facoltativi; il testo letto finisce nel registro insieme alla risposta. Nelle Impostazioni un consenso non si spegne con un tocco silenzioso: si dice cosa succede e si chiede conferma.

**Perché.** GOV.UK (Checkboxes): «Do not pre-select checkbox options as this makes it more likely that users will» non accorgersi di aver saltato una domanda («not realise they’ve missed a question») o dare la risposta sbagliata («submit the wrong answer»). COGA, tra i bisogni di chi ha disabilità cognitive (user story «Assistance and Support»): «I need to understand the consequences of what I do online». WCAG 3.3.4 copre le pagine che creano impegni legali per chi le usa. Il fondamento giuridico del consenso appartiene alla famiglia sulla privacy: qui c'è la regola d'interfaccia.

**Soglie ed eccezioni.** WCAG 3.3.4 (AA) dove l'invio crea un impegno legale per chi compila.

**In DottorCloud.** In /prenota (personFields in crm/www/prenota.html) la casella dell'informativa è richiesta e porta il collegamento, quella del marketing è facoltativa e mai spuntata («a consent has to be given, not left in place»), e il testo letto (l'innerText dell'etichetta) va al registro con la prenotazione (consent_text). I moduli pubblici (crm/public/js/moduli_campi.js) chiedono un consenso facoltativo con «Acconsento» e «Non acconsento», nessuno dei due scelto, e uno necessario con il solo «Acconsento», non premuto. Il registro è crm/moduli/consensi.py; i modelli dei moduli congelano le parole dei consensi alla pubblicazione (crm/moduli/modelli.py). In Impostazioni > Clienti > Consensi l'interruttore deve dire che cosa accende («Chiesto alle persone») e chiedere conferma prima di spegnere l'informativa.

**Come si verifica.** Caricare /prenota e ogni modulo con consensi: nessuna scelta già fatta. Nel registro c'è il testo esatto mostrato. Spegnere un consenso nelle Impostazioni chiede conferma e dice la conseguenza.

**Errori da evitare.** Studio UX, ottobre 2026: nelle Impostazioni l'interruttore di ogni consenso non dice che cosa accende e salva al tocco, anche per l'informativa privacy (gravità 2, aperto); un'informativa mai firmata da una paziente già visitata non si notava (gravità 2). Da evitare: un'unica casella per informativa e marketing; un consenso spuntato «per comodità».

**Vedi anche.** [PRIV-CONSENSO-GRANULARE](08-persone-e-dati-personali.md#priv-consenso-granulare--il-consenso-solo-dove-serve-per-finalità-al-momento-giusto-ritirabile-come-si-è-dato)

**Fonti.**

- [Checkboxes](https://design-system.service.gov.uk/components/checkboxes/) — «How it works» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Making Content Usable for People with Cognitive and Learning Disabilities](https://github.com/w3c/coga/blob/main/content-usable/index.html) — Objective 4, user story «Assistance and Support» · W3C, COGA Task Force (bozza dell'editor, sorgente su GitHub) · consultato l'11/10/2026; versione pubblicata: https://www.w3.org/TR/coga-usable/
- [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/#error-prevention-legal-financial-data) — criterio 3.3.4 Error Prevention (Legal, Financial, Data) (AA) · W3C · consultato l'11/10/2026

### FORM-TASTIERA · La tastiera giusta per ogni dato

**Regola.** Ogni campo chiede la tastiera del suo dato: type=tel per i telefoni, type=email per le email, inputmode=numeric per numeri interi e codici di sole cifre, inputmode=decimal per importi e misure, autocapitalize=characters per codice fiscale, partita IVA, IBAN e codice destinatario, autocapitalize=words per i nomi, spellcheck=false e autocorrect=off su nomi, codici ed email, type=search o enterkeyhint=search per le ricerche. type=number solo dove ha senso far salire e scendere il valore (quantità, giorni); mai per codici, CAP, telefoni o tessere, e con cautela per gli importi.

**Perché.** HTML (WHATWG): numeric «is useful for PIN entry», con decimal vanno mostrati i numeri e «the format separator for the locale»; il tipo number «is not appropriate for input that happens to only consist of numbers but isn't strictly speaking a number», con la prova dello spinbox («Getting a credit card number wrong by 1 in the last digit isn't a minor mistake»). GOV.UK: inputmode=numeric per gli interi e decimal per i decimali; «Do not use `<input type=number>` unless your user research shows that there’s a need for it», perché il valore può cambiare scorrendo la pagina e non c'è riscontro se si scrive altro; alcuni dispositivi non danno il segno meno con decimal; spellcheck=false su codici, nomi ed email. MDN: type=number ha ruolo implicito spinbutton; se lo spinbox non serve, meglio inputmode=numeric con pattern. web.dev: type=number «makes no sense» per telefoni, carte e numeri di conto.

**In DottorCloud.** utils/tastiera.js: tastiera('telefono' | 'email' | 'url' | 'intero' | 'decimale' | 'codice' | 'cifre' | 'nome' | 'cerca') e tastieraDi(field) dai metadati del DocType, che Field.vue applica a testi e numeri (Int → numeric; Float, Currency, Percent → decimal; fiscal_code, tax_id, vat_number, recipient_code, iban → maiuscole senza correttore; first_name, middle_name, last_name, lead_name, full_name → nome); le pagine pubbliche usano lo stesso oggetto NOME (crm/www/prenota.html, crm/public/js/moduli_campi.js). Convenzione di AGENTS: un intero su type=number porta inputmode=numeric; un importo su type=number tiene la tastiera del browser (la tastiera decimale dell'iPhone ha solo la virgola) e un importo di un DocType legge il separatore della tastiera con flt().

**Come si verifica.** tests/unit/tastiera.test.js. A mano su un iPhone e un Android: ogni campo apre la tastiera attesa (telefono con +, email con @, decimali con la virgola in italiano). Ricerca nel codice di type=number su campi che contengono codici, CAP, telefoni o importi.

**Errori da evitare.** Da evitare: inputmode=numeric su un telefono (manca il +); type=number per un CAP o un codice (zeri iniziali persi, frecce, rotella del mouse); un importo che può essere negativo con inputmode=decimal (GOV.UK); il correttore ortografico acceso su un cognome. Verifica sul codice (11/10/2026): type=number è usato per conteggi e percentuali, ma anche per prezzi (ServicesSettings.vue default_price, PriceListsSettings.vue, SubscriptionTypesSettings.vue, CycleDialog.vue, ConventionsSettings.vue share_amount): AGENTS lo ammette per gli importi purché tengano la tastiera del browser, ma restano lo spinbox e la rotella che GOV.UK segnala.

**Vedi anche.** [MOB-TASTIERA-GIUSTA](05-telefono-e-tocco.md#mob-tastiera-giusta--ogni-campo-apre-la-sua-tastiera)

**Fonti.**

- [HTML Living Standard](https://html.spec.whatwg.org/multipage/interaction.html#input-modalities:-the-inputmode-attribute) — § «Input modalities: the inputmode attribute», tabella delle parole chiave · WHATWG · consultato l'11/10/2026
- [HTML Living Standard](https://html.spec.whatwg.org/multipage/input.html#when-number-is-not-appropriate) — § «Number state (type=number)», nota sullo spinbox («Getting a credit card number wrong by 1…») · WHATWG · consultato l'11/10/2026
- [Text input](https://design-system.service.gov.uk/components/text-input/) — «Numbers» («Asking for whole numbers», «Asking for decimal numbers», «Avoid using inputs with a type of number»), «How and when to spellcheck a user’s input» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [`<input type=number>` HTML attribute value](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/number) — «Using number inputs», «Accessibility» · MDN Web Docs (Mozilla) · consultato l'11/10/2026
- [Payment and address form best practices](https://github.com/GoogleChrome/web.dev/blob/main/src/site/content/en/blog/payment-and-address-form-best-practices/index.md) — «Make it easy for users to enter data» · web.dev (Google), Sam Dutton; sorgente archiviato del sito su GitHub · pubblicato il 09/12/2020, aggiornato il 30/11/2021

### FORM-AUTOCOMPLETE · Il browser compila i dati di chi compila, non quelli degli altri

**Regola.** Dove la persona scrive i propri dati (/prenota, /modulo e i moduli del sito, area clienti, accesso, primo avvio del centro) ogni campo porta il suo token autocomplete: name, oppure given-name e family-name, email, tel, bday (o bday-day, bday-month, bday-year), street-address o address-line1, postal-code, address-level2 (comune), address-level1 (provincia), country, organization, one-time-code. Nel gestionale, dove un operatore scrive i dati di un'altra persona, i campi non propongono i dati dell'operatore (autocomplete=off, come fa frappe-ui), salvo il suo profilo. Mai valori inventati per aggirare il riempimento.

**Perché.** WCAG 1.3.5 (AA): lo scopo di ogni campo «collecting information about the user» si determina programmaticamente quando corrisponde a uno degli scopi elencati nella sezione «Input Purposes for User Interface Components». L'Understanding precisa che il criterio è «specifically scoped to inputs collecting information about the user»: un campo che non riguarda l'utente non è tenuto a esporre lo scopo. I token sono quelli dell'HTML (WHATWG, «Autofill»), dove tel è il numero completo con il prefisso del paese e bday una data valida. GOV.UK li chiede per nomi, telefoni, email, indirizzi e data di nascita. MDN avverte che i browser possono ignorare autocomplete=off sui campi d'accesso e che valori inventati rendono lo scopo non determinabile; la tecnica H98 è una tecnica sufficiente per 1.3.5.

**Soglie ed eccezioni.** WCAG 1.3.5 livello AA (dalla 2.1).

**In DottorCloud.** Già fatto: /prenota (name, email, tel; il nome di chi viene, quando si prenota per un altro, ha autocomplete=off perché non è dell'utente), crm/public/js/moduli_campi.js (PERSON_INPUT: name, given-name, family-name, email, tel, organization, organization-title), area/pages/Login.vue (email, one-time-code), pages/Benvenuto.vue (organization). Nel gestionale frappe-ui mette autocomplete=off sui suoi TextInput, e utils/tastiera.js non lo cambia. Da valutare: Settings/LocationsSettings.vue usa street-address, postal-code e address-level2 per l'indirizzo della sede, che non è dell'operatore, e il browser può proporgli il suo indirizzo di casa.

**Come si verifica.** axe-core: autocomplete-valid. A mano con Chrome e Safari: /prenota e l'area si compilano dal riempimento automatico. Nel gestionale, nel campo email di un paziente, il browser non propone l'email dell'operatore.

**Errori da evitare.** Da evitare: autocomplete=email sul campo email del paziente nel gestionale (il browser propone quella dell'operatore e si salva il dato sbagliato); token inventati come autocomplete=nope, che rompono 1.3.5; un campo pubblico per la data di nascita senza i token bday.

**Vedi anche.** [WCAG-1.3.5](02-wcag-percepibile-e-robusto.md#wcag-135--autocomplete-sui-dati-di-chi-compila), [MOB-AUTOCOMPLETAMENTO](05-telefono-e-tocco.md#mob-autocompletamento--il-telefono-compila-ciò-che-sa-solo-dove-i-dati-sono-di-chi-scrive)

**Fonti.**

- [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/#identify-input-purpose) — criterio 1.3.5 Identify Input Purpose (AA) e sezione «Input Purposes for User Interface Components» · W3C · consultato l'11/10/2026
- [Understanding SC 1.3.5: Identify Input Purpose](https://www.w3.org/WAI/WCAG22/Understanding/identify-input-purpose.html) — «Intent of this Success Criterion» · W3C WAI · consultato l'11/10/2026
- [HTML Living Standard](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#autofill) — § «Autofill» › «Autofilling form controls: the autocomplete attribute», tabella dei nomi dei campi · WHATWG · consultato l'11/10/2026
- [Text input](https://design-system.service.gov.uk/components/text-input/) — «Use the autocomplete attribute» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [autocomplete HTML attribute](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/autocomplete) — «Value» (nota sui gestori di password), «Accessibility» › «Avoid disabling autocomplete», «Avoid invalid autocomplete values» · MDN Web Docs (Mozilla) · consultato l'11/10/2026
- [H98: Using HTML autocomplete attributes](https://www.w3.org/WAI/WCAG22/Techniques/html/H98) — intestazione (Type: sufficient) e «Description» · W3C WAI, WCAG Techniques · consultato l'11/10/2026

### FORM-INCOLLA · Incollare e farsi aiutare, sempre

**Regola.** Nessun campo blocca l'incolla, il trascinamento o i gestori di password. Un codice monouso sta in un solo campo (autocomplete=one-time-code, inputmode=numeric) che accetta spazi e trattini incollati e li toglie, nel browser e sul server: niente sei caselle con salto automatico, niente maxlength che tronca in silenzio. C'è sempre un modo di entrare che non chiede di ricordare o ricopiare (link via email, passkey).

**Perché.** WCAG 3.3.8 (AA): nessun test di funzione cognitiva in un passo dell'autenticazione senza un'alternativa o un meccanismo d'aiuto; tra i meccanismi, i gestori di password e il copia-incolla. L'Understanding mostra come esempio da evitare il codice a sei cifre in sei campi, dove incollare il codice intero riempie solo la prima casella, e dice che un servizio che obbliga a ricopiare a mano il codice non è conforme: deve almeno lasciarlo incollare e lasciare che il browser riempia i campi. GOV.UK (Text input): «Do not disable copy and paste»; con maxlength non c'è riscontro quando il testo incollato viene troncato. GOV.UK (Confirm a phone number): «Let the user enter the code in whatever format is familiar to them. Allow additional spaces, hyphens and dashes». GOV.UK (Date input): «Never automatically tab users between the fields». L'HTML definisce il token one-time-code («One-time code used for verifying user identity»).

**Soglie ed eccezioni.** WCAG 3.3.8 livello AA (nuovo nella 2.2). GOV.UK: nel suo pattern il codice vale 15 minuti (in DottorCloud la durata la dice il server).

**In DottorCloud.** area/pages/Login.vue: un solo input sotto sei caselle disegnate, one-time-code, inputmode=numeric, le non-cifre tolte nel browser; passkey; link via email che entra con un tocco (crm/area/collegamento.py); la frase «Se questo indirizzo ha un’area, il codice sta arrivando. Vale {0} minuti.». In /modulo (crm/www/modulo.html) e /documento (crm/www/documento.html) il campo è uno solo, con one-time-code e inputmode=numeric, e dal 12/10/2026 il codice è ripulito: il browser ne tiene le cifre e il server (verify_code in crm/area/accesso.py e crm/moduli/richieste.py, open_document in crm/documenti/consegna.py) legge solo quelle. L'email del codice (crm/posta/aspetto.py, codice()) separa le cifre con la spaziatura delle lettere e non con spazi veri, così la copia resta pulita.

**Come si verifica.** Incollare «123456», «123 456», «123-456» e « 123456» (spazio davanti) in ogni campo codice: entrano tutte e sei le cifre e il codice è accettato. Un gestore di password riempie email e password della pagina d'accesso. Ricerca nel codice di gestori di paste che chiamano preventDefault.

**Errori da evitare.** Verifica sul codice (11/10/2026): i campi codice hanno maxlength=6 (Login.vue, modulo.html, documento.html): il browser tronca il testo incollato prima che lo script tolga gli spazi, così «123 456» o un codice con uno spazio davanti diventano cinque cifre; in /modulo e /documento un trattino o uno spazio in mezzo fanno rifiutare un codice giusto. Meglio un limite largo e la pulizia nello script e sul server (corretto il 12/10/2026: nessun maxlength, le cifre tenute nel browser e lette sul server). Da evitare: sei input separati con salto automatico; un codice che scade senza dire quanto dura.

**Vedi anche.** [WCAG-3.3.8](03-wcag-utilizzabile-e-comprensibile.md#wcag-338--entrare-senza-test-di-memoria-incolla-gestore-di-password-link-passkey-338-aa)

**Fonti.**

- [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/#accessible-authentication-minimum) — criterio 3.3.8 Accessible Authentication (Minimum) (AA) · W3C · consultato l'11/10/2026
- [Understanding SC 3.3.8: Accessible Authentication (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication-minimum.html) — «Login forms», «Copy and paste», «Two-factor authentication systems (verification codes)» · W3C WAI · consultato l'11/10/2026
- [Text input](https://design-system.service.gov.uk/components/text-input/) — «Do not disable copy and paste», «Avoid restricting the length of a user's input» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Confirm a phone number](https://design-system.service.gov.uk/patterns/confirm-a-phone-number/) — «When the user creates an account» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Date input](https://design-system.service.gov.uk/components/date-input/) — «How it works» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [HTML Living Standard](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#autofill) — tabella dei nomi dei campi, riga «one-time-code» · WHATWG · consultato l'11/10/2026

### FORM-NON-RICHIEDERE · Ciò che il sistema sa già non si chiede di nuovo

**Regola.** Nello stesso processo un dato già scritto o già noto arriva compilato o si sceglie con un tocco: dall'appuntamento alla fattura (persona, servizio, professionista, prezzo, convenzione), dal codice fiscale la data di nascita e il sesso (mostrati, e da confermare perché il secolo non è nel codice), dalla persona scelta il profilo di fatturazione e chi paga, dall'area i recapiti di chi prenota. Si richiede solo un dato che non vale più o un segreto, come una password.

**Perché.** WCAG 3.3.7 (A, nuovo nella 2.2): ciò che è stato inserito o fornito e serve di nuovo nello stesso processo è «auto-populated» o «available for the user to select», salvo usi essenziali, sicurezza o dato non più valido. L'Understanding aggiunge che il riempimento automatico del browser non basta, che un processo può attraversare domini diversi e che chi conserva dati per riproporli deve proteggerli, anche se solo per la durata del processo. GOV.UK: «Make sure to only ask for a piece of information once within a single journey», riproponendo le risposte già date. Designers Italia (Form): i dati che si possiedono già da altre fonti si fanno validare invece di farli reinserire.

**Soglie ed eccezioni.** WCAG 3.3.7 livello A.

**In DottorCloud.** Fattura dall'appuntamento (crm/invoicing/api.py, \_fattura_da_appuntamento e issue_from_appointment); profilo di fatturazione e chi paga (crm/invoicing/anagrafica.py); data di nascita e sesso letti dal codice fiscale (CRMBillingProfile.leggi_il_codice e anagrafica.dati_dal_codice, che oggi li scrivono senza chiedere conferma); la prenotazione trova la persona per email o telefono (find_or_create_person in crm/api/booking.py) e l'area passa a /prenota i dati della sessione (per_la_pagina_di_prenotazione in crm/area/api.py); la scheda clinica può ripartire dall'ultima visita (start_sheet con from_last=1, crm/clinica/cartella.py). Nella nuova trattativa si sceglie la persona esistente invece di riscriverla.

**Come si verifica.** Percorrere appuntamento → fattura → incasso: nessun campo già noto è vuoto. Prenotare dall'area: nome ed email già scritti. Con il lettore di schermo i valori precompilati si sentono.

**Errori da evitare.** Studio UX, ottobre 2026: in «Crea una trattativa» «Scegli una persona esistente» partiva spento, così si riscrivevano nome e cognome e nascevano doppioni (gravità 3, corretto); la data di nascita vive solo nel profilo fiscale e il dialogo di una persona nuova non può chiederla (aperto, decisione di prodotto). Revisioni del codice: la data di nascita restava nella cache del browser su un computer di segreteria condiviso (corretto): ciò che si ripropone non si conserva nel browser.

**Vedi anche.** [WCAG-3.3.7](03-wcag-utilizzabile-e-comprensibile.md#wcag-337--non-si-chiede-due-volte-ciò-che-il-sistema-sa-già-337-a)

**Fonti.**

- [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/#redundant-entry) — criterio 3.3.7 Redundant Entry (A) · W3C · consultato l'11/10/2026
- [Understanding SC 3.3.7: Redundant Entry](https://www.w3.org/WAI/WCAG22/Understanding/redundant-entry.html) — «Intent of Redundant Entry», «Exceptions» · W3C WAI · consultato l'11/10/2026
- [Question pages](https://design-system.service.gov.uk/patterns/question-pages/) — «How it works» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Form](https://designers.italia.it/design-system/componenti/form/) — «Come usarlo» › «Attenzione a» · Designers Italia · consultato l'11/10/2026

### FORM-POSTEL · Accettare i formati reali, normalizzare dopo

**Regola.** Un campo accetta il dato come lo scrive una persona (spazi, trattini, punti, barre, parentesi, maiuscole o minuscole, +39 o 0039, virgola o punto decimale, il simbolo € digitato, il mese in lettere) e il sistema lo normalizza prima di controllarlo e salvarlo. Rifiuta, dicendolo, solo ciò che è ambiguo o impossibile, senza indovinare in silenzio; dopo il salvataggio mostra la forma normalizzata. È il principio di robustezza dei protocolli Internet, detto anche legge di Postel («be conservative in what you send, and liberal in what you accept»), con il limite che l'IAB gli dà: tolleranza per i formati, non per i dati difettosi.

**Perché.** GOV.UK (Validation): si riducono gli errori «accepting information in different formats, as long as it’s not ambiguous» e si usa la validazione per ignorare «spaces, invisible characters or punctuation, like hyphens, brackets, dashes and full stops», dentro numeri e codici, prima o dopo una risposta incollata e quelli aggiunti dai programmi di dettatura. GOV.UK (Text input): chi digita il prefisso o il suffisso che il campo mostra già non riceve un errore. Il tutorial W3C: «Be forgiving of different input formats». COGA («Accept different input formats»): da evitare «Insisting on specific separator characters if they are not required and can be ignored» e il telefono che non accetta + o parentesi. GOV.UK (Date input): nel servizio Apply for teacher training, dopo aver accettato i mesi in lettere, gli errori sono calati «dramatically». L'IAB (RFC 9413, 2023) ricorda che la prima forma del principio è nella RFC 760 e che, per i protocolli, accettare in silenzio un input difettoso accumula problemi nel tempo: in un modulo vuol dire accettare spazi, separatori e maiuscole, ma non indovinare un dato ambiguo.

**In DottorCloud.** Server: crm/invoicing/engine/anagrafica.py normalizza (codici in maiuscolo senza spazi, punti e trattini; PEC in minuscolo; CAP senza spazi), codice_fiscale.\_pulisci, crm/utils/\_\_init\_\_.py to_e164 (regione del sito, Italia dove non è detta), crm/importazione/regole.py (date gg/mm/aaaa, gg-mm-aaaa, gg.mm.aaaa, ISO e anni a due cifre; telefoni con 00 o senza prefisso; CAP riportati a 5 cifre). Browser: utils/numberFormat.js flt() con puntoDellaTastiera (un solo separatore del sito seguito da una o due cifre è il punto decimale della tastiera) e il simbolo di valuta digitato; utils/telefono.js daComporre ed eNumero; il codice dell'area ripulito dalle non-cifre (area/pages/Login.vue).

**Come si verifica.** Test esistenti: tests/unit/numberFormat.test.js e telefono.test.js; crm/invoicing/tests/test_identificativi.py e test_anagrafica.py; crm/importazione/tests/test_regole.py. Per ogni codice, casi con spazi, trattini e minuscole; per gli importi «1 250» e «1,250.50» su un sito con il formato italiano.

**Errori da evitare.** Verifica sul codice (11/10/2026): crm/utils/\_\_init\_\_.py tiene ancora parse_phone_number con default_country IN e are_same_phone_number con default_region IN, il presupposto indiano che to_e164 ha corretto (\_phone_search in crm/integrations/api.py lo usa; corretto il 12/10/2026: leggono il paese del sito, come to_e164); Modals/LeadModal.vue toglie tutte le virgole da un importo scritto come testo (giusto per «1,250.50», sbagliato per «12,5»); validatePhone (utils/index.js) e LeadModal rifiutano i punti di «333.123.4567», che eNumero e to_e164 accettano; flt() legge «1 250» come 1 e, sul formato italiano, «1,250.50» come 1,2505, invece di accettare lo spazio delle migliaia o dire che il numero è ambiguo; il selettore di data legge «1/10/2026» come 10 gennaio (vedi FORM-DATE); l'importazione scrive «Mcnamara» per «MCNAMARA», perché riscrive i nomi tutti maiuscoli (vedi FORM-NOMI).

**Vedi anche.** [UX-POSTEL](04-aspetto.md#ux-postel--legge-di-postel-accettare-come-scrivono-le-persone-restituire-in-forma-rigorosa)

**Fonti.**

- [Recover from validation errors](https://design-system.service.gov.uk/patterns/validation/) — «When to use this pattern», «How it works» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Text input](https://design-system.service.gov.uk/components/text-input/) — «Prefixes and suffixes» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Validating Input](https://www.w3.org/WAI/tutorials/forms/validation/) — «Be forgiving of different input formats» · W3C WAI, Forms Tutorial · 2019 (ultimo aggiornamento 27/07/2019)
- [Making Content Usable for People with Cognitive and Learning Disabilities, pattern «Accept different input formats»](https://github.com/w3c/coga/blob/main/design-guide/o4p08-input-formats.html) — «Examples» › «Avoid» · W3C, COGA Task Force (bozza dell'editor, sorgente su GitHub) · consultato l'11/10/2026; versione pubblicata: https://www.w3.org/TR/coga-usable/
- [Date input](https://design-system.service.gov.uk/components/date-input/) — «Research on this component» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Maintaining Robust Protocols (sorgente della RFC 9413)](https://github.com/intarchboard/draft-protocol-maintenance/blob/main/draft-iab-protocol-maintenance.md) — «Abstract», «Protocol Robustness», «Fallibility of Specifications» · IAB (Internet Architecture Board), M. Thomson e D. Schinazi · RFC 9413, giugno 2023; sorgente consultato l'11/10/2026

### FORM-VALIDA-QUANDO · Validare al momento giusto

**Regola.** Nessun errore prima che la persona abbia agito: niente riquadri rossi all'apertura, niente aria-invalid su un campo intatto. I campi obbligatori vuoti si segnalano all'invio. Un formato sbagliato si può segnalare quando si lascia un campo compilato con un formato noto (codice fiscale, IBAN, email, telefono, data), mai mentre si scrive. L'errore sparisce appena il valore è corretto. Il server valida sempre, con le stesse regole del browser.

**Perché.** Le fonti divergono sul momento. GOV.UK: «Do not validate when the user moves away from a field. Wait until they try to move to the next part of the service», e niente controlli prima che si sia finito di scrivere, «especially for users who type more slowly». Il tutorial W3C presenta invece il controllo «On focus change» per i dati con un formato preciso, come una data, dove controllare durante la digitazione «would display error messages most of the time». web.dev consiglia di validare in linea mentre si inseriscono i dati, invece di elencare gli errori solo all'invio. Concordano su tre cose: niente errori prematuri (tecnica ARIA21: «The aria-invalid attribute should not be set to true before input validation is performed»), validazione sul server sempre («You’ll always need to carry out server side validation»), regole del browser e del server che non si contraddicono. DottorCloud prende il punto comune: formato all'uscita solo se il campo è compilato, completezza all'invio.

**In DottorCloud.** Moduli/FormRenderer.vue mostra i mancanti solo dopo il primo tentativo (showMissing): è il modello. Field.vue valuta il telefono sul valore già cambiato, cioè all'uscita dal campo: va bene. Invoices/InvoiceDialog.vue mostra il riquadro «Prima di emetterla» appena si apre: va reso un elenco neutro di ciò che manca, rosso solo dopo un tentativo. Le stesse regole nei due lati esistono già per i moduli (utils/moduli.js e crm/moduli/schema.py, con i casi condivisi di crm/moduli/tests/casi_schema.json) e vanno estese a codice fiscale, partita IVA e IBAN.

**Come si verifica.** Aprire ogni dialogo: nessun errore visibile, nessun aria-invalid. Scrivere un codice fiscale parziale e lasciare il campo: compare l'errore; correggerlo: sparisce senza reinviare. Inviare scavalcando il controllo del browser: il server risponde con lo stesso messaggio.

**Errori da evitare.** Studio UX, ottobre 2026: «Nuova fattura» si apre con un riquadro rosso e «Emetti» disattivato prima di qualsiasi inserimento (gravità 2, aperto). Verifica sul codice (11/10/2026): l'importazione (crm/importazione/regole.py) controlla il codice fiscale solo con lo schema dei caratteri, la fatturazione anche con il carattere di controllo: due regole diverse per lo stesso dato. Da evitare: errori mentre si scrive un'email o un telefono; un errore che resta dopo la correzione finché non si reinvia.

**Vedi anche.** [UX-NOTIFICHE](01-interazione.md#ux-notifiche--indicatori-validazioni-e-notifiche-toast)

**Fonti.**

- [Recover from validation errors](https://design-system.service.gov.uk/patterns/validation/) — «When to tell the user about validation errors», «Client side and server side validation» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [User Notification](https://www.w3.org/WAI/tutorials/forms/notifications/) — «In-line feedback» › «During typing», «On focus change» · W3C WAI, Forms Tutorial · 2022 (ultimo aggiornamento 03/06/2022)
- [Payment and address form best practices](https://github.com/GoogleChrome/web.dev/blob/main/src/site/content/en/blog/payment-and-address-form-best-practices/index.md) — «Help users enter the right data» · web.dev (Google), Sam Dutton; sorgente archiviato del sito su GitHub · pubblicato il 09/12/2020, aggiornato il 30/11/2021
- [ARIA21: Using aria-invalid to Indicate An Error Field](https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA21) — «Description» · W3C WAI, WCAG Techniques · consultato l'11/10/2026

### FORM-MESSAGGIO · Il messaggio d'errore dice cosa fare, con le parole dell'etichetta

**Regola.** Ogni errore ha un messaggio per il caso preciso (vuoto, troppo lungo, troppo corto, formato, fuori intervallo, data impossibile), che riprende le parole dell'etichetta e dice come rimediare: «Scrivi il cognome», «Scegli come ha pagato», «Il CAP ha 5 cifre», «La data di nascita deve essere nel passato», «Scrivi il telefono con il prefisso, come +39 333 123 4567». Niente «non valido», «per favore», «errore», «ops», codici o frasi del framework; lo stesso testo accanto al campo e nel riepilogo; un'istruzione («Scrivi…») per i campi vuoti e una descrizione («… deve…») per il resto, sempre allo stesso modo.

**Perché.** GOV.UK (Error message): «explain what went wrong and how to fix it»; «Error messages should directly include language from the question or fieldset label»; da non usare il gergo tecnico, «forbidden», «illegal», «you forgot», «prohibited», «please», «sorry», «valid» e «invalid», «oops»; «Be specific»: messaggi generici come «This field is required» o «Select an option» non hanno senso fuori contesto; istruzioni e descrizioni usate con coerenza; modelli per testo, data, radio, caselle, email e telefono. WCAG 3.3.1 (A) vuole l'errore descritto in testo, 3.3.3 (AA) il suggerimento quando è noto; l'Understanding 3.3.1 porta proprio l'esempio di «Email is not valid», che passa 3.3.1 ma non 3.3.3. Designers Italia: un titolo che descrive il problema «senza incolpare l'utente», la causa, il rimedio, un'azione; nel campo l'aiuto lascia il posto a un microtesto d'errore «enfatizzando la soluzione e non l'errore».

**Soglie ed eccezioni.** WCAG 3.3.1 (A), 3.3.3 (AA). axe-core 4.14 non ha regole per 3.3.1, 3.3.3, 3.3.4, 3.3.7 e 3.3.8: la verifica è manuale.

**In DottorCloud.** Modelli italiani: vuoto → «Scrivi…» o «Scegli…»; troppo lungo → «Le note possono avere al massimo 500 caratteri»; numero → «La durata deve essere un numero di minuti, come 30»; data → «La data di nascita deve essere una data vera»; codice → «Il codice fiscale non torna: controlla l'ultima lettera». Già vicini al modello: i messaggi del profilo di fatturazione (\_ERRORI in crm/invoicing/doctype/crm_billing_profile/crm_billing_profile.py): «An Italian postal code has five digits», «The province is written with two letters, for example MI». Le frasi stanno in it.po; quelle del motore di fatturazione sono Messaggio; nessun codice si ricava da una frase tradotta (AGENTS).

**Come si verifica.** Cercare in crm/locale/it.po «non valid», «obbligatorio» generico, «per favore», «Errore»; per ogni validatore un messaggio per caso; rilettura dei messaggi con chi lavora allo sportello.

**Errori da evitare.** Verifica sul codice (11/10/2026): Moduli/FormFieldInput.vue dice «Questo campo è obbligatorio», che GOV.UK cita tra i messaggi da evitare; Modals/LeadModal.vue dice «Indirizzo email non valido», «Il numero di cellulare deve contenere solo cifre» (mentre + e spazi sono accettati) e «I ricavi annuali devono essere un numero»; Field.vue «Inserisci un numero di telefono valido»; /prenota «Compila i campi obbligatori.» senza dire quali, e «Inserisci un'email valida.»; il messaggio del codice fiscale del profilo di fatturazione comincia con «non è valido», prima di spiegare che l'ultimo carattere non corrisponde; data/document.js ricava i nomi dei campi mancanti spezzando la frase del server su «: », cioè legge una frase tradotta. Studio UX, ottobre 2026: la pagina d'errore diceva «il tuo livello apre» (gravità 1).

**Vedi anche.** [WCAG-3.3.3](03-wcag-utilizzabile-e-comprensibile.md#wcag-333--lerrore-dice-come-correggerlo-333-aa)

**Fonti.**

- [Error message](https://design-system.service.gov.uk/components/error-message/) — «Match up error messages to labels», «Be clear and concise», «Be consistent», «Be specific», «Use instructions and descriptions», «Use error message templates» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Text input](https://design-system.service.gov.uk/components/text-input/) — «Error messages» (modelli per vuoto, lunghezza, numeri, importi) · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/#error-identification) — criteri 3.3.1 Error Identification (A) e 3.3.3 Error Suggestion (AA) · W3C · consultato l'11/10/2026
- [Understanding SC 3.3.1: Error Identification](https://www.w3.org/WAI/WCAG22/Understanding/error-identification.html) — «Intent of Error Identification» · W3C WAI · consultato l'11/10/2026
- [Understanding SC 3.3.3: Error Suggestion](https://www.w3.org/WAI/WCAG22/Understanding/error-suggestion.html) — «Intent of Error Suggestion», «Examples of Error Suggestion» · W3C WAI · consultato l'11/10/2026
- [Microtesti](https://designers.italia.it/design-system/fondamenti/microtesti/) — «Aiuta nella risoluzione degli errori» · Designers Italia · consultato l'11/10/2026
- [Input](https://designers.italia.it/design-system/componenti/input/) — «Come usarlo» › «Buone pratiche sui contenuti» · Designers Italia · consultato l'11/10/2026
- [axe-core Rule Descriptions](https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md) — elenco delle regole per criterio: nessuna con le etichette wcag331, wcag333, wcag334, wcag337, wcag338 · Deque Systems · axe-core 4.14, consultato l'11/10/2026

### FORM-ERRORE-ACCANTO · L'errore sta accanto al campo, legato al campo e annunciato

**Regola.** Il messaggio compare accanto al suo campo, dopo etichetta e aiuto, con un segno oltre al colore (icona, bordo più spesso); il controllo ha aria-invalid=true e aria-describedby (o aria-errormessage) verso il messaggio, che comincia con «Errore:» nascosto per il lettore di schermo; l'errore viene annunciato. Un errore non vive mai solo in un toast che scompare, né solo nel colore.

**Perché.** GOV.UK: il messaggio va in rosso «after the question text and hint text», un bordo rosso lo collega alla domanda e si nomina il campo; il componente aggiunge un «Error:» nascosto, che in un'altra lingua si traduce. Il tutorial W3C: i campi si possono legare ai messaggi con aria-describedby; icone e bordi accompagnano il testo. La tecnica ARIA21 mette aria-invalid sui campi che non hanno passato la validazione; ARIA19 annuncia con role=alert o una regione live, il cui contenitore deve esistere già nel DOM al caricamento perché la maggior parte dei lettori di schermo lo legga. L'Understanding 3.3.1 ammette colore e icone «in addition to the text description». Designers Italia: il microtesto d'errore prende il posto dell'aiuto sotto il campo. La rubrica dello studio UX di ottobre 2026 lo dice in una riga: mai un errore che vive solo in un toast che scompare.

**Soglie ed eccezioni.** WCAG 3.3.1 (A), 1.4.1 (A), 4.1.2 (A); 4.1.3 (AA) per gli annunci. Per 3.3.1 ARIA21 (aria-invalid) è una tecnica sufficiente sia quando manca un dato obbligatorio sia quando un dato deve avere un formato o valori precisi; ARIA19 (role=alert o regione live) nel secondo caso.

**In DottorCloud.** frappe-ui fa tutto se riceve la prop error: TextInput mette aria-invalid, aria-errormessage e aria-describedby, e il messaggio (InputError) ha role=alert. Field.vue la usa solo per il telefono: per gli altri errori di campo (obbligatori, formati, risposte del server) deve passare error al campo invece di mandare un toast. I toast di frappe-ui sono annunciati (reka-ui li legge da una regione con role=alert), ma spariscono e non stanno accanto al campo. In Moduli/FormFieldInput.vue il paragrafo del dato mancante va legato al controllo (id e aria-describedby) con aria-invalid. In /prenota e /modulo il messaggio va sotto il suo campo. Il prefisso «Errore:» nascosto si scrive in italiano. Per portare la vista sull'errore si usa inVista (utils/inVista.js), non scrollIntoView (AGENTS).

**Come si verifica.** VoiceOver e TalkBack: entrando nel campo si sente etichetta, valore, «non valido» e il messaggio. axe-core: aria-valid-attr-value sui riferimenti di aria-describedby e aria-errormessage. Ricerca di toast.error usato dopo una validazione di campo.

**Errori da evitare.** Verifica sul codice (11/10/2026): data/document.js trasforma gli obbligatori mancanti e ogni messaggio del server in toast.error; pages/FormFill.vue dice «Da rispondere ancora: …» in un toast e scorre con scrollIntoView; Modals/LeadModal.vue mostra l'errore in fondo, dopo tutti i campi del dialogo; il «Questo campo è obbligatorio» del motore dei moduli non è legato al controllo; nell'area clienti (area/pages/Login.vue) l'errore sotto l'email è un ErrorMessage a parte, non legato al campo. Studio UX, ottobre 2026: il motivo di «Completa dal sito» spento stava solo in un tooltip (gravità 2, corretto).

**Vedi anche.** [WCAG-3.3.1](03-wcag-utilizzabile-e-comprensibile.md#wcag-331--un-errore-dice-in-parole-quale-campo-e-che-cosa-non-va-331-a)

**Fonti.**

- [Error message](https://design-system.service.gov.uk/components/error-message/) — «How it works» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [User Notification](https://www.w3.org/WAI/tutorials/forms/notifications/) — «Listing errors» (aria-describedby), «In-line feedback» · W3C WAI, Forms Tutorial · 2022 (ultimo aggiornamento 03/06/2022)
- [ARIA21: Using aria-invalid to Indicate An Error Field](https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA21) — «Description», esempio «Using aria-invalid on required fields» · W3C WAI, WCAG Techniques · consultato l'11/10/2026
- [ARIA19: Using ARIA role=alert or Live Regions to Identify Errors](https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA19) — «Description», primo esempio · W3C WAI, WCAG Techniques · consultato l'11/10/2026
- [Understanding SC 3.3.1: Error Identification](https://www.w3.org/WAI/WCAG22/Understanding/error-identification.html) — «Intent of Error Identification» · W3C WAI · consultato l'11/10/2026
- [Input](https://designers.italia.it/design-system/componenti/input/) — «Come usarlo» › «Buone pratiche sui contenuti» · Designers Italia · consultato l'11/10/2026
- [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/#use-of-color) — criteri 1.4.1 Use of Color (A), 4.1.2 Name, Role, Value (A) e 4.1.3 Status Messages (AA) · W3C · consultato l'11/10/2026
- [WCAG — understanding/understanding.11tydata.js (le tecniche associate a ogni criterio, da cui sono costruite le pagine Understanding)](https://github.com/w3c/wcag/blob/main/understanding/understanding.11tydata.js) — voce «error-identification» (3.3.1: ARIA21 sufficiente nelle situazioni A e B, ARIA19 nella B) · W3C, Accessibility Guidelines Working Group (sorgente su GitHub) · consultato l'11/10/2026

### FORM-RIEPILOGO-ERRORI · Dopo un invio fallito: tutto in cima, niente perso, il fuoco sul riepilogo

**Regola.** Se un invio non passa, il modulo resta con tutti i valori scritti, giusti e sbagliati, e mostra in cima un riepilogo con un titolo («C'è un problema», «Mancano 2 risposte») e un collegamento per ogni errore che porta al campo; il fuoco va al riepilogo; nelle pagine pubbliche il titolo della pagina comincia con «Errore: ». Tutti gli errori insieme, non uno per tentativo; gli errori trovati dal server arrivano sui loro campi.

**Perché.** GOV.UK (Error summary): «Always show an error summary when there is a validation error, even if there’s only one»; si sposta il fuoco sul riepilogo, il titolo è «There is a problem», c'è un collegamento per ogni risposta sbagliata (al primo campo sbagliato se la risposta ha più campi, al primo radio o casella per un gruppo), con le stesse parole dei messaggi accanto ai campi, in cima al main e sopra l'h1. GOV.UK (Validation): la pagina si mostra di nuovo «with the form fields as the user filled them in» e «Error: » va all'inizio del `<title>`. GOV.UK (Error message): «Do not clear any form fields when showing the Error message component. Keep both passing and failing answers». Il tutorial W3C («Listing errors»): un titolo riconoscibile, l'etichetta del campo, come correggere, un collegamento interno, role=alert se il riepilogo arriva senza ricaricare. La tecnica G139 descrive il collegamento agli errori. L'Understanding 3.3.1 nota che la validazione nativa del browser espone solo il primo errore e costringe a reinviare più volte. Designers Italia (Form): all'invio, «un messaggio di alert complessivo e riferimenti visivi e informativi puntuali sulla validità di ogni campo».

**In DottorCloud.** Un componente condiviso per il riepilogo, usato da Modals/FieldLayoutDialog.vue (oggi una riga «Mancano dei campi obbligatori: …» senza collegamenti), Modals/LeadModal.vue e DealModal.vue (oggi un errore alla volta), pages/FormFill.vue (oggi un toast), Invoices/InvoiceDialog.vue (dopo un tentativo «Prima di emetterla» diventa il riepilogo, con i collegamenti ai campi) e le pagine pubbliche /prenota e /modulo. findMissingMandatory (utils/fieldTransforms.js) restituisce le etichette: deve restituire anche i fieldname per i collegamenti. Il server sa già quali campi sono sbagliati (anagrafica.errori restituisce i nomi dei campi): va restituito per campo, invece di unire i messaggi con `<br>` in un solo frappe.throw.

**Come si verifica.** Inviare vuoto: il fuoco va sul riepilogo, i collegamenti portano ai campi, i valori restano. Con NVDA o VoiceOver si sente il titolo del riepilogo. Nelle pagine pubbliche il `<title>` comincia con «Errore:».

**Errori da evitare.** Verifica sul codice (11/10/2026): LeadModal.vue e DealModal.vue si fermano al primo errore (validate() esce al primo caso); /prenota aggiunge il messaggio dopo il modulo, sotto il pulsante d'invio; il profilo di fatturazione lancia un unico errore con i messaggi uniti da `<br>` pur conoscendo i campi. Da evitare: svuotare i campi sbagliati; un riepilogo con parole diverse da quelle accanto ai campi.

**Fonti.**

- [Error summary](https://design-system.service.gov.uk/components/error-summary/) — «When to use this component», «How it works», «Linking from the error summary to each answer», «Where to put the error summary» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Recover from validation errors](https://design-system.service.gov.uk/patterns/validation/) — «How to tell the user about validation errors» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Error message](https://design-system.service.gov.uk/components/error-message/) — «How it works» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [User Notification](https://www.w3.org/WAI/tutorials/forms/notifications/) — «Listing errors», «Using the page title» · W3C WAI, Forms Tutorial · 2022 (ultimo aggiornamento 03/06/2022)
- [G139: Creating a mechanism that allows users to jump to errors](https://www.w3.org/WAI/WCAG22/Techniques/general/G139) — «Description» · W3C WAI, WCAG Techniques · consultato l'11/10/2026
- [Understanding SC 3.3.1: Error Identification](https://www.w3.org/WAI/WCAG22/Understanding/error-identification.html) — «User agent native HTML form validation» · W3C WAI · consultato l'11/10/2026
- [Form](https://designers.italia.it/design-system/componenti/form/) — «Comportamento» · Designers Italia · consultato l'11/10/2026

### FORM-PULSANTE · Il pulsante d'invio è sempre attivo e dice cosa fa

**Regola.** Il pulsante che invia (Salva, Emetti, Prenota, Invia, Mandami il codice) resta attivo: se manca qualcosa, al tocco lo dice accanto alla causa e porta lì il cursore. Il suo testo è verbo più oggetto e corrisponde all'azione: «Emetti la fattura» solo se emette, «Salva la bozza» se salva una bozza, «Continua» se non salva nulla. Una sola azione primaria piena per vista, nello stesso posto in tutte le pagine dello stesso tipo.

**Perché.** GOV.UK (Button): «Disabled buttons have poor contrast and can confuse some users, so avoid them if possible. Only use disabled buttons if research shows it makes the user interface easier to understand»; il testo descrive l'azione («Continue» quando il servizio non salva, «Save and continue» quando salva, «Save and come back later»); «Avoid using multiple default buttons on a single page». L'Understanding 1.4.11 esenta dal contrasto i componenti inattivi e porta proprio l'esempio del pulsante d'invio disattivato finché mancano campi: è conforme, ma illeggibile. Designers Italia: «Inizia le call-to-action con un verbo» («Invia», non «OK»). WCAG 3.2.4 (AA): la stessa funzione ha lo stesso nome.

**Soglie ed eccezioni.** WCAG 3.2.4 (AA), 2.4.6 (AA).

**In DottorCloud.** Corretti nello studio: «Mandami il codice» dell'area resta attivo e, senza email, dice «Scrivi l'email che hai dato al centro.» portando il cursore nel campo (area/pages/Login.vue); «Trova un orario libero» chiede di scegliere prima il servizio e porta lì il cursore (Calendar/AppointmentPanel.vue); «Crea» delle liste è diventato «Nuova persona», «Nuova trattativa». Ancora disattivati: «Emetti» in Invoices/InvoiceDialog.vue (finché vista.errors non è vuoto), «Aggiorna» e «Salva» delle Impostazioni finché non si cambia qualcosa, «Manda gli inviti» (Settings/InviteUserPage.vue), «Pubblica» nel riquadro dei messaggi dell'area (Area/AreaMessagesCard.vue), «Entra» dell'area finché non ci sono sei cifre. AzioneImpostazioni.vue ha come testo predefinito «Aggiorna», che si legge anche come «ricarica».

**Come si verifica.** Ricerca dei pulsanti d'invio con :disabled nei componenti Vue: ognuno, premuto, dice cosa manca. Un solo pulsante pieno per vista. Elenco dei testi dei pulsanti confrontato con le azioni che fanno.

**Errori da evitare.** Studio UX, ottobre 2026: «Emetti» grigio come i campi e senza dire che mancano paziente e servizio (gravità 2, aperto); «Manda gli inviti» e il «Salva» della firma spenti (gravità 1, aperto); «Collega Facebook», «Sigilla una pagina di prova» e «Aggiorna» spenti senza motivo (gravità 2, aperto); «Pubblica» spento e diverso da «Invia» per la stessa azione (gravità 1, aperto); «Emetti la fattura» sulla riga di un appuntamento salva una bozza e apre la fattura, dove l'emissione è un secondo «Emetti» (gravità 3: lo studio ha corretto la bozza che spariva dalle liste, ma il pulsante si chiama ancora così). Da evitare: un pulsante spento spiegato solo da un tooltip, che sul telefono non si apre.

**Vedi anche.** [UX-DISATTIVATI](01-interazione.md#ux-disattivati--pulsanti-e-controlli-disattivati)

**Fonti.**

- [Button](https://design-system.service.gov.uk/components/button/) — «How it works», «Default buttons», «Disabled buttons» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Understanding SC 1.4.11: Non-text Contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html) — «Inactive User Interface Components» · W3C WAI · consultato l'11/10/2026
- [Microtesti](https://designers.italia.it/design-system/fondamenti/microtesti/) — «Usa azioni specifiche» · Designers Italia · consultato l'11/10/2026
- [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/#consistent-identification) — criterio 3.2.4 Consistent Identification (AA) · W3C · consultato l'11/10/2026
- [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/#headings-and-labels) — criterio 2.4.6 Headings and Labels (AA): «Headings and labels describe topic or purpose» · W3C · consultato l'11/10/2026

### FORM-DOPPIO-INVIO · Un invio parte una volta sola

**Regola.** Dal tocco alla risposta il pulsante mostra che sta lavorando («Prenotazione in corso…», stato di caricamento) e ignora i tocchi successivi; il server rende l'operazione idempotente (chiave d'idempotenza, controllo «già fatto»), così un doppio tocco, una rete lenta o un ritorno indietro non creano due prenotazioni, due fatture, due pagamenti o due inviti. Dopo un'azione che si fa una volta sola, tornare indietro mostra cosa è successo invece di rifarla.

**Perché.** GOV.UK (Button): si fa doppio clic per abitudine del proprio sistema operativo, per una connessione lenta che non dà riscontro o per un tremore della mano; il team di GOV.UK Notify ha scoperto inviti ricevuti due volte perché chi li mandava faceva doppio clic su «send»; data-prevent-double-click ignora il secondo clic, ma «you should also think about the issue server-side to protect against attacks»; con le connessioni lente, prima di tutto mostrare cosa sta succedendo. Nel codice di govuk-frontend il secondo clic è ignorato per un secondo (DEBOUNCE_TIMEOUT_IN_SECONDS = 1). GOV.UK (Question pages): dopo un pagamento o un invio il pulsante indietro funziona ma mostra un messaggio sensato invece di permettere di ripetere l'azione.

**Soglie ed eccezioni.** govuk-frontend: secondo clic ignorato per 1 secondo. La protezione vera è sul server.

**In DottorCloud.** Il Button di frappe-ui con la prop loading è disabled e aria-busy pur mantenendo il suo aspetto: va usato su ogni invio (area/pages/Login.vue e Invoices/InvoiceDialog.vue lo fanno). /prenota disattiva il pulsante durante l'invio e scrive «Prenotazione in corso…». Sul server: gli addebiti Stripe hanno una chiave d'idempotenza per tentativo, scritta prima di chiamare Stripe (crm/pagamenti/addebiti.py, Idempotency-Key in crm/pagamenti/cliente.py); l'emissione con Fatture in Cloud ritrova il documento di una risposta persa dal marcatore nell'oggetto (crm/invoicing/fic/emissione.py); la prenotazione online (book in crm/api/service_booking.py) serializza le prenotazioni dello stesso servizio con un lock sulla sua riga e ricontrolla il posto: protegge dalle prenotazioni concorrenti, non è una chiave d'idempotenza, e il doppio invio va provato anche dove i posti sono più d'uno.

**Come si verifica.** Rete rallentata (strumenti del browser, Slow 3G) e doppio tocco veloce su ogni invio: un solo record. Test sul server: due chiamate uguali, un solo effetto. Dopo l'invio, indietro e poi avanti: nessun secondo invio.

**Errori da evitare.** Da evitare: affidarsi solo al pulsante disattivato (se il JavaScript fallisce o la richiesta parte due volte, deve fermarla il server); un «Salvato» che arriva due volte; un invio ripetuto dopo un errore di rete che crea un secondo documento invece di ritrovare il primo.

**Fonti.**

- [Button](https://design-system.service.gov.uk/components/button/) — «Stop users from accidentally sending information more than once» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [govuk-frontend: button.mjs](https://github.com/alphagov/govuk-frontend/blob/main/packages/govuk-frontend/src/govuk/components/button/button.mjs) — costante DEBOUNCE_TIMEOUT_IN_SECONDS e metodo debounce() · GOV.UK Design System, Government Digital Service · govuk-frontend 6.5.1, consultato l'11/10/2026
- [Question pages](https://design-system.service.gov.uk/patterns/question-pages/) — «Back link» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026

### FORM-SALVATAGGIO · Un modo di salvare per tipo di pagina, e si sa sempre se è salvato

**Regola.** Ogni tipo di pagina ha un solo modello di salvataggio e lo dice. O tutto vale al cambio, e accanto al campo compare «Salvato» annunciato con role=status mentre la pagina dice «Le modifiche valgono subito»; oppure c'è un pulsante «Salva» sempre visibile nello stesso posto (AzioneImpostazioni), con «Modifiche non salvate» quando ce ne sono. Cambiare un campo o un interruttore non cambia pagina né chiude la finestra; uscire con modifiche non salvate chiede che cosa fare.

**Perché.** WCAG 3.2.4 (AA): funzioni uguali identificate allo stesso modo. WCAG 3.2.2 (A): cambiare l'impostazione di un controllo non provoca un cambio di contesto senza averlo detto prima; l'Understanding precisa che spuntare una casella, scrivere in un campo o cambiare l'opzione di un elenco è «changing its setting». WCAG 4.1.3 (AA): i messaggi di stato arrivano alle tecnologie assistive senza prendere il fuoco, e tra gli esempi c'è «Saved in 'Wedding' album». GOV.UK: il testo del pulsante dice se il servizio salva («Save and continue») o no («Continue»). COGA (user story «Assistance and Support»): «I need to save my work as I go or be sure all my work is saved automatically».

**Soglie ed eccezioni.** WCAG 3.2.2 (A), 3.2.4 (AA), 4.1.3 (AA).

**In DottorCloud.** Impostazioni: Settings/AzioneImpostazioni.vue (accanto al titolo su desktop, nella barra in fondo sul telefono), Settings/Invoicing/DocFields.vue per i DocType di fatturazione, SettingsRow per gli interruttori che salvano subito; Prenotazione online lo dice già («Ogni interruttore qui vale subito.»). Il «Salvato» di data/document.js è un toast di frappe-ui: reka-ui lo annuncia da una regione con role=alert, ma scompare e non sta accanto al campo. Settings/CalendarSettings.vue chiude tutta la finestra delle Impostazioni con «Aggiorna» (showSettings.value = false): un salvataggio non chiude niente. composables/useUnsavedChangesWarning.ts (beforeunload, su persona e trattativa) e la domanda di Calendar/AppointmentPanel.vue coprono l'uscita.

**Come si verifica.** Per ogni pagina delle Impostazioni una riga: modello di salvataggio, testo e posto del pulsante; due pagine sorelle con modelli diversi sono un difetto. Il lettore di schermo sente «Salvato». Chiudere con modifiche non salvate: si chiede.

**Errori da evitare.** Studio UX, ottobre 2026: tra pagine sorelle si salva in cinque modi diversi (al tocco con un toast; «Aggiorna» che compare solo dopo una modifica; «Salva» sempre attivo; «Aggiorna» disattivato; «Aggiorna» che chiude la finestra senza «Salvato»), gravità 2, ancora aperto; la firma email aveva un «Salva» spento in mezzo alla pagina che salvava solo la firma (gravità 2); i consensi salvano al tocco dell'interruttore senza dirlo (gravità 2).

**Vedi anche.** [UX-SALVA](01-interazione.md#ux-salva--salvare-un-modello-per-tipo-di-pagina-e-il-lavoro-che-sopravvive-alle-interruzioni)

**Fonti.**

- [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/#on-input) — criteri 3.2.2 On Input (A), 3.2.4 Consistent Identification (AA), 4.1.3 Status Messages (AA) · W3C · consultato l'11/10/2026
- [Understanding SC 3.2.2: On Input](https://www.w3.org/WAI/WCAG22/Understanding/on-input.html) — «Intent of On Input» · W3C WAI · consultato l'11/10/2026
- [Understanding SC 4.1.3: Status Messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html) — «Status message examples» · W3C WAI · consultato l'11/10/2026
- [Button](https://design-system.service.gov.uk/components/button/) — «How it works» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Making Content Usable for People with Cognitive and Learning Disabilities](https://github.com/w3c/coga/blob/main/content-usable/index.html) — Objective 4, user story «Assistance and Support» · W3C, COGA Task Force (bozza dell'editor, sorgente su GitHub) · consultato l'11/10/2026; versione pubblicata: https://www.w3.org/TR/coga-usable/

### FORM-BOZZE · Il lavoro interrotto non si perde

**Regola.** Allo sportello si viene interrotti: un modulo lungo (visita, fattura, appuntamento, messaggio, modulo da firmare) conserva quanto scritto, dice quando l'ha salvato e chiede prima di scartare modifiche; la bozza sta dove la si cerca (le liste delle cose da fare la mostrano come bozza da completare). Le bozze con dati sanitari o fiscali stanno sul server; nel browser restano solo testi non sensibili, per utente e per scheda, cancellati all'invio. Una scadenza della sessione avvisa prima e non fa perdere i dati.

**Perché.** COGA («Avoid Data Loss and “Timeouts”»): «Avoid timeouts and let the user save their work as they go»; se non si può, dire all'inizio che cosa fa scadere la sessione, quanto tempo c'è, come estenderlo e se si perdono i dati. WCAG 2.2.1 (A): un limite di tempo si spegne, si regola o si estende (avviso con almeno 20 secondi per estenderlo con un'azione semplice, almeno dieci volte), salvo eccezioni come un limite oltre 20 ore. WCAG 2.2.5 (AAA): dopo una nuova autenticazione si continua «without loss of data». WCAG 2.2.6 (AAA): si avvisa della durata dell'inattività che fa perdere dati, salvo che siano conservati oltre 20 ore, e la nota ricorda i vincoli della privacy. L'Understanding 3.3.7: chi conserva dati, anche temporaneamente, deve proteggerli.

**Soglie ed eccezioni.** WCAG 2.2.1 (A): avviso con almeno 20 secondi per estendere, almeno 10 estensioni, oppure limite oltre 20 ore. WCAG 2.2.6 (AAA): dati conservati oltre 20 ore, oppure durata dell'inattività dichiarata.

**In DottorCloud.** Già c'è: pages/FormFill.vue «Salvato: si può finire più tardi» (save_answers in crm/moduli/compilazioni.py salva a metà sul server); Invoices/InvoiceDialog.vue «Salva la bozza», e le bozze degli appuntamenti tornano in Accoglienza e in Fatture con «Completa la bozza di fattura»; Calendar/AppointmentPanel.vue chiede «Scartare le modifiche non salvate?» alla X, a Esc, all'indietro e cambiando pagina (onBeforeRouteLeave, utils/indietro.js); composables/useUnsavedChangesWarning.ts (beforeunload) su persona e trattativa; composables/drafts.js conserva nel localStorage, per utente e scheda, le bozze di email, note, WhatsApp e SMS.

**Come si verifica.** Cominciare una scheda di visita, chiudere la scheda del browser, riaprire: la bozza c'è. Su Android, indietro a metà appuntamento: una domanda sola. Strumenti del browser › Archiviazione locale: nessun dato sanitario o fiscale. Lasciare scadere la sessione a metà modulo: dopo il nuovo accesso i dati ci sono.

**Errori da evitare.** Studio UX, ottobre 2026: «Emetti la fattura» salvava una bozza che spariva sia da «Da fare» sia dai «37 appuntamenti da fatturare», così una prestazione poteva restare senza fattura (gravità 3, corretto). Revisioni del codice: la dashboard contava le bozze come fatturate; la data di nascita restava nel database del browser su un computer di segreteria condiviso; l'indietro di Android perdeva un appuntamento scritto a metà (tutti corretti). Da valutare: le bozze di note e messaggi nel localStorage possono contenere dati sanitari su un computer condiviso, e la loro chiave porta l'email dell'utente.

**Vedi anche.** [SAN-BOZZA-MAI-PERSA](08-persone-e-dati-personali.md#san-bozza-mai-persa--il-lavoro-interrotto-non-si-perde), [UX-SALVA](01-interazione.md#ux-salva--salvare-un-modello-per-tipo-di-pagina-e-il-lavoro-che-sopravvive-alle-interruzioni)

**Fonti.**

- [Making Content Usable for People with Cognitive and Learning Disabilities, pattern «Avoid Data Loss and “Timeouts”»](https://github.com/w3c/coga/blob/main/design-guide/o4p09-data-loss.html) — «What to do», «How it Helps» · W3C, COGA Task Force (bozza dell'editor, sorgente su GitHub) · consultato l'11/10/2026; versione pubblicata: https://www.w3.org/TR/coga-usable/
- [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/#timing-adjustable) — criteri 2.2.1 Timing Adjustable (A), 2.2.5 Re-authenticating (AAA), 2.2.6 Timeouts (AAA) · W3C · consultato l'11/10/2026
- [Understanding SC 3.3.7: Redundant Entry](https://www.w3.org/WAI/WCAG22/Understanding/redundant-entry.html) — «Intent of Redundant Entry», paragrafo su privacy e dati personali · W3C WAI · consultato l'11/10/2026

### FORM-IRREVERSIBILE · Prima di un invio che non si ritira: rivedere, confermare o poter annullare

**Regola.** Un invio con effetti legali, fiscali o sui dati (emettere una fattura, che prende il numero; trasmetterla allo SdI; mandare una spesa al Sistema TS; firmare un modulo o un preventivo; eliminare una persona o un ambulatorio; spegnere un consenso; addebitare una carta) è reversibile, o controllato con la possibilità di correggere, o preceduto da un riepilogo da confermare. La conferma ha un titolo «Vuoi + verbo…?», dice oggetto e conseguenza, il pulsante ripete il verbo, l'alternativa è «Annulla», e il fuoco non parte sul pulsante distruttivo. Dove si può annullare dopo, si preferisce «Annulla» a una domanda prima; le conferme restano per i casi seri.

**Perché.** WCAG 3.3.4 (AA): per le pagine che creano impegni legali o transazioni finanziarie, o che modificano o cancellano dati controllati dall'utente, l'invio è reversibile, controllato o confermato. L'Understanding: lo scopo è evitare perdite serie (un file, un record), non chiedere conferma «for each save command». Il tutorial W3C: conferma per le azioni irreversibili, annullamento per quelle reversibili (il cestino, l'invio di un'email annullabile per qualche secondo). GOV.UK: il pulsante di avviso solo per conseguenze gravi difficili da annullare, con un passo di conferma, senza affidarsi al solo rosso; «Confirm and send», o «Accept and send» se c'è un contenuto legale da accettare. Designers Italia: titolo «Vuoi + verbo», non «Attenzione!» né «Sei sicuro di voler...?»; descrizione delle conseguenze; lo stesso verbo nel pulsante principale; «Annulla» come secondario; nei casi ambigui «No, mantieni pratica / Sì, annulla pratica». COGA: per le transazioni importanti, poter annullare facilmente e sapere entro quando.

**Soglie ed eccezioni.** WCAG 3.3.4 livello AA.

**In DottorCloud.** Invoices/InvoiceDialog.vue è il riepilogo della fattura (righe, totali, «Prima di emetterla», avvisi); «Emetti» dà il numero e una fattura emessa si corregge con la nota di credito; «Correggila» compare solo per una fattura che lo SdI ha scartato (il permesso reopen calcolato in crm/invoicing/emissione.py). Gli invii automatici allo SdI e al Sistema TS partono spenti (crm/invoicing/automatico.py, crm/tessera_sanitaria/automatico.py). Firme: pages/FormFill.vue e la firma del preventivo nell'area (crm/preventivi/firma.py) mostrano ciò che si firma. Eliminazioni: ambulatori e collegamenti tracciati chiedono conferma nominando l'oggetto (corretto nello studio). Le conferme di $dialog hanno il titolo in it.po.

**Come si verifica.** Elenco delle azioni irreversibili per modulo, ciascuna con il suo rimedio (riepilogo, conferma o annullamento). I titoli delle conferme in it.po cominciano con «Vuoi». Da tastiera: Esc annulla, il fuoco iniziale non è sul pulsante distruttivo.

**Errori da evitare.** Studio UX, ottobre 2026: un ambulatorio si eliminava con un tocco, senza conferma né annulla (gravità 3, corretto); «Attiva la fatturazione» sta sopra l'elenco degli obblighi da sistemare prima, presentati come facoltativi (gravità 3, aperto); i consensi si spengono con un tocco (gravità 2, aperto). Verifica sul codice (11/10/2026): la domanda dell'appuntamento si intitola «Scartare le modifiche non salvate?», non «Vuoi scartare…?», con «Continua a modificare» e «Scarta». Da evitare: conferme ovunque, che si cliccano senza leggerle.

**Vedi anche.** [WCAG-3.3.4](03-wcag-utilizzabile-e-comprensibile.md#wcag-334--fatture-firme-pagamenti-consensi-ed-eliminazioni-annullabili-controllati-o-confermati-334-aa)

**Fonti.**

- [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/#error-prevention-legal-financial-data) — criterio 3.3.4 Error Prevention (Legal, Financial, Data) (AA) · W3C · consultato l'11/10/2026
- [Understanding SC 3.3.4: Error Prevention (Legal, Financial, Data)](https://www.w3.org/WAI/WCAG22/Understanding/error-prevention-legal-financial-data.html) — «Intent of Error Prevention (Legal, Financial, Data)» · W3C WAI · consultato l'11/10/2026
- [Validating Input](https://www.w3.org/WAI/tutorials/forms/validation/) — «Validation by the user» › «Require user confirmation», «Provide undo functionality» · W3C WAI, Forms Tutorial · 2019 (ultimo aggiornamento 27/07/2019)
- [Button](https://design-system.service.gov.uk/components/button/) — «How it works», «Warning buttons» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Microtesti](https://designers.italia.it/design-system/fondamenti/microtesti/) — «Chiedi conferma prima di azioni importanti» · Designers Italia · consultato l'11/10/2026
- [Making Content Usable for People with Cognitive and Learning Disabilities, pattern «Make it Easy to Undo Form Errors»](https://github.com/w3c/coga/blob/main/design-guide/o4p05-form-undo.html) — «What to Do» · W3C, COGA Task Force (bozza dell'editor, sorgente su GitHub) · consultato l'11/10/2026; versione pubblicata: https://www.w3.org/TR/coga-usable/

### FORM-FUOCO · Il cursore va dove serve e non salta da solo

**Regola.** All'apertura di un dialogo su computer il cursore va nel primo campo da compilare, non in un campo secondario; sul telefono la tastiera si apre solo se il primo gesto è scrivere. Dopo un invio fallito il fuoco va al riepilogo degli errori (o al primo campo sbagliato). L'ordine del Tab segue quello visivo. Nessun passaggio automatico da un campo all'altro mentre si scrive.

**Perché.** GOV.UK (Error summary): spostare il fuoco sul riepilogo. Il tutorial W3C («After submit»): «it is convenient to set the focus to the first `<input>` element that contains an error». GOV.UK (Date input): «Never automatically tab users between the fields of the date input because this can be confusing and may clash with normal keyboard controls». L'Understanding 3.2.2 porta l'esempio dei campi del telefono che avanzano da soli: ammessi solo se lo si dice all'inizio del modulo. WCAG 2.4.3 (A): l'ordine del fuoco conserva significato e funzionamento.

**Soglie ed eccezioni.** WCAG 2.4.3 (A), 3.2.2 (A).

**In DottorCloud.** composables/firstFieldFocus.js (useFirstFieldFocus) aspetta il primo campo in cui si può scrivere e rispetta il fuoco messo da chi usa la pagina: è il layout che deve mettere per primo il campo giusto. /prenota mette il cursore nel nome; il Login dell'area lo porta nel campo del codice dopo l'invio. Sull'iPhone il fuoco non fa scorrere la pagina (preventScroll) e il campo si mostra con inVista (AGENTS).

**Come si verifica.** Percorso solo da tastiera di ogni modulo; dopo un invio fallito, dove sta il fuoco. Sul telefono, aprendo un dialogo, la tastiera non copre il modulo per un campo secondario.

**Errori da evitare.** Studio UX, ottobre 2026: nel foglio della nuova trattativa il cursore andava da solo in «Nome dell'azienda» e sul telefono apriva la tastiera sul campo sbagliato (gravità 3, corretto con il riordino del foglio). Da evitare: le sei caselle del codice con salto automatico; il fuoco che resta dietro un dialogo aperto.

**Vedi anche.** [WCAG-3.2.1](03-wcag-utilizzabile-e-comprensibile.md#wcag-321--il-focus-da-solo-non-cambia-il-contesto-321-a)

**Fonti.**

- [Error summary](https://design-system.service.gov.uk/components/error-summary/) — «How it works» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [User Notification](https://www.w3.org/WAI/tutorials/forms/notifications/) — «In-line feedback» › «After submit» · W3C WAI, Forms Tutorial · 2022 (ultimo aggiornamento 03/06/2022)
- [Date input](https://design-system.service.gov.uk/components/date-input/) — «How it works» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Understanding SC 3.2.2: On Input](https://www.w3.org/WAI/WCAG22/Understanding/on-input.html) — «Examples of On Input» · W3C WAI · consultato l'11/10/2026
- [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/#focus-order) — criterio 2.4.3 Focus Order (A) · W3C · consultato l'11/10/2026

### FORM-DATE · Date all'italiana, senza ambiguità

**Regola.** Una data si scrive e si legge gg/mm/aaaa. Il campo accetta anche g/m/aa, trattini, punti e il mese in lettere («1 ott 2026») e non legge mai «1/10/2026» come 10 gennaio; se una data è ambigua, lo chiede. La data di nascita si digita (in un campo, o in tre, giorno, mese e anno, nelle pagine pubbliche), non si cerca sfogliando un calendario; il calendario serve per le date vicine, come gli appuntamenti, e non è mai l'unico modo di inserire. Un campo data vuoto resta vuoto; un testo che non si capisce produce un messaggio, non un ritorno silenzioso al valore di prima. Gli esempi usano un giorno di almeno 13 e un mese di al massimo 9 («27/3/2007»). Le date impossibili (nascita nel futuro, fine prima dell'inizio) si fermano con un messaggio.

**Perché.** CLDR per l'italiano: data breve «dd/MM/yy», media «d MMM y», lunga «d MMMM y»; la settimana comincia di lunedì (firstDay mon per IT). GOV.UK (Date input): tre campi per le date che si conoscono o si trovano senza calendario, mesi accettati anche in lettere (nel servizio Apply for teacher training, dopo averlo fatto, gli errori sono calati «dramatically»), autocomplete bday-day, bday-month e bday-year per la nascita, nessun salto automatico tra i campi, messaggi come «must be a real date» e «must be in the past». GOV.UK (Dates): il calendario solo per date vicine nel futuro o nel passato recente e mai come unico modo; negli esempi un giorno di 13 o più e un mese di 9 o meno, per mostrare l'ordine. COGA: chi scrive «1/3/1996» dove si voleva «01/03/1996» riceve un errore; se la correzione non è sicura si chiede «Did you mean the first of February (01/02) or the second of January (02/01)?». web.dev: per l'anno di nascita un input con inputmode=numeric è più facile e meno soggetto a errori di una select lunga. L'Understanding 3.3.1: anche quando il codice corregge da solo un valore fuori intervallo, l'errore va detto.

**Soglie ed eccezioni.** Formato gg/mm/aaaa (crm/lingue.py imposta date_format dd/mm/yyyy per l'Italia); settimana dal lunedì; esempio con giorno ≥13 e mese ≤9 (GOV.UK).

**In DottorCloud.** Field.vue usa il DatePicker di frappe-ui con il formato del sito (getFormat → DD/MM/YYYY); Calendar/AppointmentPanel.vue lo usa con il formato «ddd, D MMM YYYY». vite/frappeUi.js riscrive già il selettore (nomi dei mesi, settimana dal lunedì) e, dal 12/10/2026, legge g/m/aaaa, g-m-aa e g.m.aaaa prima della lettura libera di dayjs (giornoScritto, con i suoi casi in tests/unit/frappeUi.test.js); va aggiunta la lettura dei mesi italiani. Le pagine pubbliche (crm/public/js/moduli_campi.js) usano `<input type=date>` nativo, adatto alle date vicine; per la nascita servono i tre campi con i token bday. crm/importazione/regole.py data() legge già le forme italiane e porta «80» a 1980. Limiti min e max sulle date; «oggi» con oggiDelCentro() (utils/scheduler.js).

**Come si verifica.** Test d'unità: «1/10/2026», «01-10-26», «1.10.2026» e «1 ott 2026» danno 2026-10-01; «31/02/2026» dà un messaggio; un campo vuoto dà nulla. Prova a mano su iPhone e Android. Nessun selettore che costringe a sfogliare decenni per una data di nascita.

**Errori da evitare.** Verifica sul codice (11/10/2026): il DatePicker di frappe-ui prova il formato in modo stretto e poi lascia leggere il testo a dayjs, che segue l'ordine americano: «1/10/2026» non passa il controllo stretto di DD/MM/YYYY e diventa il 10 gennaio 2026 (provato con il dayjs 1.11.20 del repository; corretto il 12/10/2026: ora è l'1 ottobre); un testo che non si capisce, come «18/10/2026» nel campo dell'appuntamento, fa tornare in silenzio la data di prima; con clearable spento un campo svuotato diventa la data di oggi del browser. Modals/EventModal.vue e Calendar/CalendarEventPanel.vue hanno come segnaposto il formato americano «May 1, 2025» (tradotto «1 maggio 2025»). Da evitare: «oggi» come valore predefinito di una data di nascita; esempi ambigui come «01/02/2026».

**Vedi anche.** [TIPO-DATE](07-lingua-e-norme.md#tipo-date--date-allitaliana-e-mai-ambigue)

**Fonti.**

- [Unicode CLDR — common/main/it.xml](https://github.com/unicode-org/cldr/blob/main/common/main/it.xml) — calendario gregoriano, `<dateFormats>`: full «EEEE d MMMM y», long «d MMMM y», medium «d MMM y», short «dd/MM/yy» · Unicode Consortium · consultato l'11/10/2026
- [Unicode CLDR — common/supplemental/supplementalData.xml](https://github.com/unicode-org/cldr/blob/main/common/supplemental/supplementalData.xml) — `<weekData>`, `<firstDay day=mon>` (elenco dei territori che comprende IT) · Unicode Consortium · consultato l'11/10/2026
- [Date input](https://design-system.service.gov.uk/components/date-input/) — «When to use this component», «How it works», «Use the autocomplete attribute for a date of birth», «Error messages», «Research on this component» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Dates](https://design-system.service.gov.uk/patterns/dates/) — «Asking for memorable dates», «Helping users to pick a date», «How to write dates» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Making Content Usable for People with Cognitive and Learning Disabilities, pattern «Design Forms to Prevent Mistakes»](https://github.com/w3c/coga/blob/main/design-guide/o4p04-supportive-forms.html) — «How it Helps» e «More Details» · W3C, COGA Task Force (bozza dell'editor, sorgente su GitHub) · consultato l'11/10/2026; versione pubblicata: https://www.w3.org/TR/coga-usable/
- [Payment and address form best practices](https://github.com/GoogleChrome/web.dev/blob/main/src/site/content/en/blog/payment-and-address-form-best-practices/index.md) — «Make it easy for users to enter data» · web.dev (Google), Sam Dutton; sorgente archiviato del sito su GitHub · pubblicato il 09/12/2020, aggiornato il 30/11/2021
- [Understanding SC 3.3.1: Error Identification](https://www.w3.org/WAI/WCAG22/Understanding/error-identification.html) — «Intent of Error Identification» (valore fuori intervallo corretto dal codice) · W3C WAI · consultato l'11/10/2026

### FORM-ORE · Orari a 24 ore, e sempre di un fuso detto

**Regola.** Un orario si scrive e si mostra HH:mm a 24 ore, mai con AM e PM; il campo accetta anche «9.30», «930» e «9:30» e li porta a «09:30», e «9» a «09:00». Nel gestionale gli orari di appuntamenti, turni e scadenze sono quelli del centro, non del dispositivo di chi guarda; dove chi guarda può essere in un altro fuso (la pagina pubblica di prenotazione) l'orario dice in quale fuso è. «Inizio», «Fine» e una durata («in minuti») hanno la loro etichetta.

**Perché.** CLDR: l'italiano eredita dalla radice il formato orario breve «HH:mm», a 24 ore. Le regole di DottorCloud (AGENTS, doc 40): gli orari sono HH:mm, l'orologio del sistema; un orologio Intl porta hourCycle h23; giorno e ore di un appuntamento sono quelli del centro e «adesso» e «oggi» si prendono con adessoDelCentro() e oggiDelCentro(). COGA chiede di accettare le varianti di formato, fusi orari compresi. Nello studio UX due orari senza «Inizio» e «Fine» non si distinguevano.

**Soglie ed eccezioni.** 24 ore, HH:mm.

**In DottorCloud.** TimePicker di frappe-ui in Field.vue con il formato orario del sistema; utils/scheduler.js (oraDelCentro, sulCentro, adessoDelCentro, oggiDelCentro, prossimoQuarto); gli orologi Intl portano hourCycle h23 (utils/scheduler.js, utils/sulTelefono.js, utils/conversation.js). /prenota mostra gli orari nel fuso del telefono di chi prenota e, quando è diverso da quello del centro, lo scrive sopra gli orari («Orari nel tuo fuso orario: …», altroFuso e tzNote in crm/www/prenota.html); utils/fusiOrari.js nomina il fuso con la città («Roma · Ora dell'Europa centrale»).

**Come si verifica.** tests/unit/scheduler.test.js. Telefono impostato su un altro fuso: gli orari dell'agenda non cambiano, quelli di /prenota dicono il fuso. Scrivere «930» o «9.30»: diventa 09:30.

**Errori da evitare.** Studio UX, ottobre 2026: nel nuovo appuntamento «16:45» e «17:15» non dicevano quale fosse l'inizio e quale la fine (gravità 2, corretto con le etichette). Da evitare (AGENTS): dayjs() o new Date().toISOString() per «adesso», che vicino a mezzanotte spostano il giorno; un orario con AM e PM; un orario senza fuso letto da chi sta altrove.

**Vedi anche.** [TIPO-ORE-DURATE](07-lingua-e-norme.md#tipo-ore-durate--ore-a-24-ore-durate-con-le-unità), [I18N-FUSO](07-lingua-e-norme.md#i18n-fuso--lora-del-centro-e-i-giorni-che-non-si-spostano)

**Fonti.**

- [Unicode CLDR — common/main/root.xml](https://github.com/unicode-org/cldr/blob/main/common/main/root.xml) — calendario gregoriano, `<timeFormats>`: short «HH:mm» (it.xml lo eredita) · Unicode Consortium · consultato l'11/10/2026
- [Making Content Usable for People with Cognitive and Learning Disabilities, pattern «Accept different input formats»](https://github.com/w3c/coga/blob/main/design-guide/o4p08-input-formats.html) — «What to Do» · W3C, COGA Task Force (bozza dell'editor, sorgente su GitHub) · consultato l'11/10/2026; versione pubblicata: https://www.w3.org/TR/coga-usable/

### FORM-NUMERI · Numeri e importi come li scrive un italiano

**Regola.** Un campo numerico accetta la virgola decimale e il punto o lo spazio delle migliaia («1.250,50», «1 250,5», «1250,5») e il punto che una tastiera inglese dà per «12.5»; mostra l'unità o la valuta fuori dal campo e anche nell'etichetta («Prezzo, in euro»), accetta che qualcuno la digiti dentro, legge un campo vuoto come vuoto (non zero), dice quando un numero è ambiguo invece di indovinarlo, e mostra gli importi con due decimali e il simbolo dopo la cifra («65,00 €»). I limiti (minimo, massimo, decimali) stanno nell'aiuto e nei messaggi.

**Perché.** CLDR per l'italiano: separatore decimale «,», delle migliaia «.», modello della valuta «#,##0.00 ¤» (simbolo dopo la cifra, con uno spazio) e minimumGroupingDigits 2, per cui i formattatori Intl scrivono «1250» e «12.500» (verificato con Node 22: «1250,00 €», «65,00 €», «12.500,00 €»). HTML (WHATWG, Number state): il browser può accettare il numero nel formato locale, con separatori di gruppo e decimali diversi («3,99» o «3.99»), e convertirlo; è una possibilità, non un obbligo. GOV.UK: inputmode=decimal; prefissi e suffissi fuori dal campo ma non da soli, perché «screen readers will not read them out», quindi «Cost, in pounds» nell'etichetta; chi digita il simbolo non riceve un errore; messaggi come «must be a number, like 30». COGA: campi che accettano «various currency symbols» e unità di misura che la persona conosce.

**Soglie ed eccezioni.** Due decimali per gli importi in euro. CLDR: con Intl il separatore delle migliaia compare da 5 cifre (minimumGroupingDigits 2); il formato del sito (#.###,##, impostato da crm/lingue.py) lo mette già da 4.

**In DottorCloud.** utils/numberFormat.js: flt() con puntoDellaTastiera (un solo separatore del sito seguito da una o due cifre è il punto decimale della tastiera) e il simbolo di valuta digitato, formatCurrency e conIlSimbolo (il simbolo dove lo mette la lingua di chi legge); utils/valute.js prezzo() (Intl); Controls/CampoValuta.vue (la valuta per nome, il codice salvato); Field.vue con FormattedInput per Float, Currency e Percent; il numero con unità del motore dei moduli (Moduli/FormFieldInput.vue, crm/public/js/moduli_campi.js), dove l'unità va legata al campo (nell'etichetta o con aria-describedby).

**Come si verifica.** tests/unit/numberFormat.test.js e valute.test.js. In un campo Currency con il formato del sito #.###,##: «12,5», «12.5», «1.250,50» e «12,50 €» diventano 12,5 · 12,5 · 1250,5 · 12,5 (oggi è così); «1 250» deve diventare 1250 e un campo vuoto restare vuoto (oggi danno 1 e 0). Il lettore di schermo legge l'unità insieme al campo.

**Errori da evitare.** Verifica sul codice (11/10/2026): flt() legge «1 250» come 1, «1,250.50» come 1,2505 e una stringa vuota come 0; due formattatori scrivono lo stesso importo in due modi, prezzo() «1250,00 €» e formatCurrency() «1.250,00 €»; il README di Espresso (brand/dottorcloud/design-system/espresso/README.md) porta l'esempio «€ 1.250,00», con il simbolo davanti, contro CLDR e AGENTS («65,00 €»); le unità dei moduli (kg, cm) sono uno span accanto al campo che il lettore di schermo non lega al campo; Field.vue mostra «0» in un intero vuoto. Studio UX, ottobre 2026: «Precisione valuta» suggeriva 3 decimali (gravità 2); nei numeri grandi in grassetto la virgola di «87,3%» si confondeva con il punto di «20.294 €» (gravità 1).

**Vedi anche.** [TIPO-NUMERI](07-lingua-e-norme.md#tipo-numeri--numeri-cifre-virgola-decimale-punto-delle-migliaia-una-regola-sola)

**Fonti.**

- [Unicode CLDR — common/main/it.xml](https://github.com/unicode-org/cldr/blob/main/common/main/it.xml) — `<numbers>`: minimumGroupingDigits 2; `<symbols numberSystem=latn>` decimal «,» e group «.»; `<currencyFormats>` pattern «#,##0.00 ¤» · Unicode Consortium · consultato l'11/10/2026
- [HTML Living Standard](https://html.spec.whatwg.org/multipage/input.html#number-state) — § «Number state (type=number)», esempio dopo la descrizione dello stato: input nel formato locale, con i separatori di gruppo e i decimali («3,99» contro «3.99») · WHATWG · consultato l'11/10/2026
- [Text input](https://design-system.service.gov.uk/components/text-input/) — «Asking for decimal numbers», «Prefixes and suffixes», «Error messages» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Making Content Usable for People with Cognitive and Learning Disabilities, pattern «Accept different input formats»](https://github.com/w3c/coga/blob/main/design-guide/o4p08-input-formats.html) — «Examples» › «Use» · W3C, COGA Task Force (bozza dell'editor, sorgente su GitHub) · consultato l'11/10/2026; versione pubblicata: https://www.w3.org/TR/coga-usable/
- [Making Content Usable for People with Cognitive and Learning Disabilities, pattern «Use Familiar Metrics and Units»](https://github.com/w3c/coga/blob/main/design-guide/o4p12-familiar-metrics.html) — «User Need», «What to Do» · W3C, COGA Task Force (bozza dell'editor, sorgente su GitHub) · consultato l'11/10/2026; versione pubblicata: https://www.w3.org/TR/coga-usable/

### FORM-TELEFONO · Un telefono in un campo solo, accettato come lo si scrive

**Regola.** Il telefono è un campo unico type=tel (con autocomplete=tel se è di chi compila) che accetta spazi, trattini, punti, parentesi, +39 o 0039 e il numero senza prefisso. Lo si valida con libphonenumber nella regione del centro (Italia dove non è detta), lo si salva in E.164 (+39…, con lo 0 dei fissi) e lo si mostra a gruppi. Si dice se serve un cellulare (per SMS e WhatsApp) e perché lo si chiede; niente maschere di inserimento né campi divisi, e il numero non si riformatta mentre la persona lo sta ancora controllando.

**Perché.** GOV.UK (Phone numbers): «Let users enter phone numbers in whatever format is familiar to them. Allow for additional spaces, hyphens, dashes and brackets, and be able to accommodate country and area codes»; validare con libphonenumber; autocomplete=tel; dire se serve un numero mobile o internazionale e perché lo si chiede; evitare le maschere; il team di GOV.UK Notify ha visto persone confuse davanti al proprio numero riformattato con il prefisso aggiunto. libphonenumber («Falsehoods»): un numero di telefono non va trattato come un numero, perché lo 0 iniziale può farne parte; in Italia dal 1998 il prefisso è parte del numero e si compone anche dall'estero, come «+39012345». I metadati di libphonenumber per IT: prefisso internazionale 00, fissi da 6 a 12 cifre (esempio 0212345678), cellulari da 9 o 10 (esempio 3123456789). Il token tel dell'HTML è il numero completo con il prefisso del paese. web.dev: un solo campo per il numero di telefono.

**Soglie ed eccezioni.** Italia (libphonenumber): cellulari di 9 o 10 cifre nazionali, fissi da 6 a 12, lo 0 iniziale fa parte del numero; salvataggio in E.164.

**In DottorCloud.** crm/utils/\_\_init\_\_.py: to_e164 con default_region (Italia dove il sito non ha paese), usato da normalise_numbers in crm/api/contact.py; utils/telefono.js: leggibile (gruppi), daComporre, eNumero; utils/index.js validatePhone (un'espressione regolare, non libphonenumber) e l'errore di Field.vue; tastiera('telefono'); /prenota con type=tel, autocomplete=tel e il telefono richiesto solo dove il servizio lo vuole; l'importazione confronta le ultime nove cifre (ultime_nove in crm/importazione/regole.py).

**Come si verifica.** tests/unit/telefono.test.js. A mano: «333 123 4567», «+39 333-123-4567», «0039 02 1234 5678», «(02) 12345678» e «333.123.4567» si salvano in E.164 e si mostrano a gruppi. Test Python di to_e164 con un sito senza paese.

**Errori da evitare.** Verifica sul codice (11/10/2026): parse_phone_number e are_same_phone_number in crm/utils/\_\_init\_\_.py restano con la regione India come predefinita (il difetto che to_e164 ha corretto: i numeri senza prefisso letti come indiani; corretto il 12/10/2026, e un fisso tiene ora il suo 0); validatePhone e LeadModal.vue rifiutano «333.123.4567»; il messaggio «Inserisci un numero di telefono valido» non dà un esempio. Studio UX, ottobre 2026: le liste mostrano ora i numeri a gruppi, «+39 389 555 2045» invece di «+393895552045» (corretto).

**Vedi anche.** [TIPO-RECAPITI](07-lingua-e-norme.md#tipo-recapiti--telefoni-email-e-indirizzi-leggibili-e-cliccabili)

**Fonti.**

- [Phone numbers](https://design-system.service.gov.uk/patterns/phone-numbers/) — «Allow different formats», «Validate phone numbers», «Use the autocomplete attribute», «Error messages», «Make it clear what type of phone number you need», «Explain why you need a phone number», «Avoid input masking», «Avoid reformatting phone numbers» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Falsehoods Programmers Believe About Phone Numbers](https://github.com/google/libphonenumber/blob/master/FALSEHOODS.md) — «A leading zero in numbers formatted for domestic usage can always be discarded when dialing from abroad»; «Phone numbers are numbers» · Google, libphonenumber · consultato l'11/10/2026
- [PhoneNumberMetadata.xml](https://github.com/google/libphonenumber/blob/master/resources/PhoneNumberMetadata.xml) — `<territory id=IT>`: internationalPrefix 00; fixedLine possibleLengths 6-12, mobile possibleLengths 9 e 10, numeri d'esempio · Google, libphonenumber · consultato l'11/10/2026
- [HTML Living Standard](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#autofill) — tabella dei nomi dei campi, righe «tel» e «tel-national» · WHATWG · consultato l'11/10/2026
- [Payment and address form best practices](https://github.com/GoogleChrome/web.dev/blob/main/src/site/content/en/blog/payment-and-address-form-best-practices/index.md) — «Use a single input for payment card and phone numbers» · web.dev (Google), Sam Dutton; sorgente archiviato del sito su GitHub · pubblicato il 09/12/2020, aggiornato il 30/11/2021

### FORM-EMAIL · Un'email: tastiera giusta, controllo leggero, conferma restituendo l'indirizzo

**Regola.** Il campo email è type=email (o testo con inputmode=email), con autocomplete=email quando è di chi compila, spellcheck=false e autocapitalize=none, largo da mostrare almeno 30 caratteri e capace di contenerne 254. Il controllo è leggero (una @ e un dominio con un punto) e avvisa senza bloccare sui refusi dei domini comuni; non si chiede di riscriverla due volte; dopo l'invio si mostra l'indirizzo usato e lo si può correggere; si dice a cosa servirà.

**Perché.** GOV.UK (Email addresses): dire perché la si chiede; «Make sure the field can accommodate up to 254 characters»; permettere di incollarla; type=email; spellcheck=false; restituire l'indirizzo perché la persona lo controlli e lo cambi; autocomplete=email; almeno 30 caratteri visibili; segnalare i refusi di domini noti ma lasciar proseguire; far ripetere l'email solo se la ricerca lo giustifica; messaggio «Enter an email address in the correct format, like name@example.com». L'HTML definisce l'indirizzo email valido con una grammatica che si discosta volutamente dalla RFC 5322, la cui sintassi l'HTML giudica insieme troppo severa, troppo vaga e troppo permissiva per l'uso pratico.

**Soglie ed eccezioni.** 254 caratteri al massimo; almeno 30 visibili (GOV.UK).

**In DottorCloud.** tastiera('email') in utils/tastiera.js; area/pages/Login.vue (type=email, autocomplete=email, «Ti mandiamo un codice: nessuna password da ricordare.», poi «Un altro indirizzo» per correggere, e una risposta che non rivela se l'indirizzo ha un'area); /prenota (type=email, autocomplete=email, inputmode=email, controllo leggero); crm/importazione/regole.py (EMAIL); la PEC portata in minuscolo da anagrafica.normalizza.

**Come si verifica.** Provare «nome.cognome+tag@studio.it», «Maria@Example.IT» e un indirizzo con uno spazio finale; incollare un indirizzo di 60 caratteri. Rileggere i messaggi d'errore.

**Errori da evitare.** Verifica sul codice (11/10/2026): crm/www/book.html (le prenotazioni dei vecchi calendari) ha maxlength=140 sull'email, sotto i 254, e tronca in silenzio; i messaggi «Inserisci un'email valida.» (/prenota) e «Indirizzo email non valido» (LeadModal.vue) non dicono il formato atteso, e LeadModal controlla solo che ci sia una @. Studio UX, ottobre 2026: all'ingresso dell'area il campo email era a 1,04:1 e il pulsante spento sembrava un altro campo (gravità 3, corretto).

**Fonti.**

- [Email addresses](https://design-system.service.gov.uk/patterns/email-addresses/) — «Tell users why you want the email address», «Make sure the field works for all of your users», «Help users to enter a valid email address», «Error messages» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [HTML Living Standard](https://html.spec.whatwg.org/multipage/input.html#valid-e-mail-address) — § «Email state (type=email)», definizione di «valid email address» e nota sulla RFC 5322 · WHATWG · consultato l'11/10/2026

### FORM-NOMI · Nomi come li porta la persona

**Regola.** Nome e cognome stanno in due campi solo dove servono separati (codice fiscale, fattura, Sistema TS, ordinamento), con le etichette «Nome» e «Cognome», abbastanza lunghi, accettando ogni lettera e segno (apostrofi, accenti, trattini, spazi, particelle: «D'Amico», «De Luca», «Nicolò», «Maria Grazia»), senza imporre le maiuscole né cambiare quelle scritte, senza correttore ortografico. Il titolo («Dott.», «Sig.ra») non si chiede, o è un campo di testo facoltativo; se serve, si chiede come chiamare la persona.

**Perché.** GOV.UK (Names): chiedere il nome solo se serve; campi abbastanza lunghi; «Support all the characters users may need to enter»; i campi multipli aumentano il rischio che un nome non ci stia; etichette «First name» e «Last name»; autocomplete name, given-name e family-name; spellcheck=false; «Avoid asking users for their title», perché costringe a rivelare genere e stato civile, e se serve va in un campo di testo facoltativo, non in una select. W3C («Personal names around the world»): campi lunghi; punteggiatura e spazi ammessi; «Don’t require names to be entered all in upper case»; «Don't normalize the casing in names» (McNamara, van der Waals); il titolo non obbligatorio. web.dev: non validare i nomi con espressioni limitate all'alfabeto latino, ma con le lettere Unicode, e niente campo separato per il titolo, che rompe il riempimento automatico.

**In DottorCloud.** tastiera('nome') in utils/tastiera.js (autocapitalize=words, autocorrect=off, spellcheck=false), applicata da tastieraDi a first_name, middle_name, last_name, lead_name e full_name; /prenota chiede «Nome e cognome» in un campo con autocomplete=name e trova la persona con find_or_create_person (crm/api/booking.py); anagrafica.incoerenze confronta nome e cognome con il codice fiscale senza bloccare; l'importazione legge «paziente» e «nominativo» con il cognome per primo (COGNOME_PRIMA in crm/importazione/regole.py).

**Come si verifica.** Creare le persone «Anna-Lisa D'Amico», «José Núñez», «Ngọc Lan», «O'Brien»: si salvano come scritte. Un codice fiscale che non torna con il nome dà un avviso, non un blocco.

**Errori da evitare.** Studio UX, ottobre 2026: «Nuova persona» chiedeva «Titolo» per primo (gravità 2, corretto spostandolo dopo «Genere»). Verifica sul codice (11/10/2026): l'importazione porta «MCNAMARA» a «Mcnamara», perché riscrive i nomi tutti maiuscoli o tutti minuscoli (nome_proprio in crm/importazione/regole.py): è un compromesso per i vecchi programmi che scrivono in maiuscolo, e un cognome come McNamara va corretto a mano. Da evitare: un'espressione regolare solo ASCII che rifiuta gli accenti; un limite di lunghezza stretto.

**Vedi anche.** [MOB-MAIUSCOLE-CORREZIONE](05-telefono-e-tocco.md#mob-maiuscole-correzione--maiuscole-e-correttore-secondo-il-dato), [I18N-NOMI](07-lingua-e-norme.md#i18n-nomi--i-nomi-delle-persone-come-li-scrivono-loro)

**Fonti.**

- [Names](https://design-system.service.gov.uk/patterns/names/) — «Make sure the fields work for most of your users», «Single or multiple name fields», «Labelling name fields», «Use the autocomplete attribute on name fields», «Do not spellcheck user's names», «Avoid asking for a person’s title» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Personal names around the world](https://www.w3.org/International/questions/qa-personal-names) — «To split or not to split?», «Other things» · W3C Internationalization · prima pubblicazione 17/08/2011, ultima modifica 24/01/2016; consultato l'11/10/2026
- [Payment and address form best practices](https://github.com/GoogleChrome/web.dev/blob/main/src/site/content/en/blog/payment-and-address-form-best-practices/index.md) — «Use a single name input», «Allow international names» · web.dev (Google), Sam Dutton; sorgente archiviato del sito su GitHub · pubblicato il 09/12/2020, aggiornato il 30/11/2021

### FORM-INDIRIZZI · Indirizzi italiani: pochi campi, il CAP come testo

**Regola.** Un indirizzo italiano si chiede con: via e numero civico (un campo, o due solo se il tracciato li vuole separati), CAP (cinque cifre, campo di testo largo cinque caratteri, lo 0 iniziale conservato), Comune, Provincia (sigla di due lettere, scritta o scelta), Paese (Italia come predefinito solo dove è vero). Con i token autocomplete (street-address o address-line1, postal-code, address-level2, address-level1, country) quando è l'indirizzo di chi compila; obbligatori solo i campi che servono davvero, per esempio alla fattura elettronica.

**Perché.** I dati per paese di Google libaddressinput (il progetto aiuta a raccogliere indirizzi postali di tutto il mondo; la sua libreria C++ è usata nei progetti di Chromium che trattano indirizzi) per IT: formato «%N%n%O%n%A%n%Z %C %S» (CAP, Comune e Provincia sulla stessa riga), campi richiesti indirizzo, comune, provincia e CAP (require ACSZ), comune e provincia in maiuscolo, CAP di cinque cifre, con gli esempi 00144, 47037 e 39049. GOV.UK (Addresses): più campi solo quando si sa da quali paesi vengono gli indirizzi; obbligatorio solo ciò che serve; campi della lunghezza giusta (CAP più corto della via); codici postali accettati in maiuscolo o minuscolo, con o senza spazi e punteggiatura; autocomplete su ogni campo. Il tutorial W3C: i codici postali in molti paesi non sono solo numeri, «so using an input of the type number can easily become a problem». web.dev: indirizzi flessibili, senza imporre via e numero civico in campi separati.

**Soglie ed eccezioni.** CAP: cinque cifre; provincia: due lettere.

**In DottorCloud.** crm/invoicing/engine/anagrafica.py: errori() controlla CAP di cinque cifre e provincia di due lettere solo per l'Italia, e il paese di due lettere sempre; normalizza() toglie gli spazi dal CAP e scrive provincia e paese in maiuscolo; crm/importazione/regole.py riporta il CAP a cinque cifre con lo zero davanti e la provincia alle prime due lettere; Settings/LocationsSettings.vue usa i token d'indirizzo; i dati di fatturazione stanno nel profilo (crm/invoicing/anagrafica.py).

**Come si verifica.** crm/invoicing/tests/test_anagrafica.py. A mano: «00185» resta «00185»; «mi» diventa «MI»; un indirizzo estero non chiede la provincia italiana.

**Errori da evitare.** Da evitare: il CAP in un campo numerico, che perde lo 0 iniziale (00144 è uno degli esempi italiani di libaddressinput); un CAP letto da Excel come «144.0» (l'importazione lo corregge); una provincia obbligatoria per un indirizzo estero; l'etichetta «ZIP».

**Fonti.**

- [libaddressinput — testdata/countryinfo.txt](https://github.com/google/libaddressinput/blob/master/testdata/countryinfo.txt) — riga data/IT: fmt, require, upper, zip, zipex · Google · consultato l'11/10/2026
- [libaddressinput — README](https://github.com/google/libaddressinput/blob/master/README.md) — paragrafo introduttivo e «C++» · Google · consultato l'11/10/2026
- [Addresses](https://design-system.service.gov.uk/patterns/addresses/) — «Allow different postcode formats», «When to use multiple text inputs», «How multiple text inputs work», «Use the autocomplete attribute on multiple address fields» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Validating Input](https://www.w3.org/WAI/tutorials/forms/validation/) — «Be forgiving of different input formats» · W3C WAI, Forms Tutorial · 2019 (ultimo aggiornamento 27/07/2019)
- [Payment and address form best practices](https://github.com/GoogleChrome/web.dev/blob/main/src/site/content/en/blog/payment-and-address-form-best-practices/index.md) — «Make address forms flexible» · web.dev (Google), Sam Dutton; sorgente archiviato del sito su GitHub · pubblicato il 09/12/2020, aggiornato il 30/11/2021
- [HTML Living Standard](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#autofill) — tabella dei nomi dei campi: street-address, address-line1, address-level2, address-level1, postal-code, country · WHATWG · consultato l'11/10/2026

### FORM-CODICE-FISCALE · Il codice fiscale: accettato com'è scritto, controllato con il carattere di controllo

**Regola.** Il campo accetta 16 caratteri (o 11 cifre per chi non è persona fisica) scritti anche in minuscolo o con spazi, li porta in maiuscolo senza separatori, controlla il carattere di controllo e le lettere dell'omocodia e, se non torna, lo dice («Il codice fiscale non torna: controlla l'ultima lettera») senza cancellarlo. Dal codice si mostrano data di nascita e sesso; la data va confermata, perché il secolo non è nel codice. Se il codice non corrisponde a nome, cognome o data già scritti, si avvisa senza bloccare. Tastiera in maiuscolo, senza correttore.

**Perché.** python-stdnum, la libreria di riferimento usata qui per questi identificativi (le pagine dell'Agenzia delle Entrate non erano raggiungibili): il codice fiscale è «an alphanumeric code of 16 characters» per le persone fisiche, «or 11 digits for non-individuals»; tre caratteri dal cognome, tre dal nome, cinque per sesso e data di nascita, quattro per il luogo di nascita, uno di controllo; alcune cifre possono essere sostituite da lettere in caso di omocodia; dell'anno di nascita sono conservate solo le ultime due cifre. Il motore di DottorCloud (crm/invoicing/engine/codice_fiscale.py): «validate the check character, not the length», perché il confronto con l'anagrafica scopre il paziente scambiato, l'errore più costoso, quello che porta la spesa nella dichiarazione precompilata di un altro. WCAG 3.3.3: proporre la correzione quando è nota; WCAG 3.3.7: ciò che si ricava dal codice non si richiede.

**Soglie ed eccezioni.** 16 caratteri alfanumerici (persone fisiche); 11 cifre (soggetti diversi dalle persone fisiche); ultimo carattere di controllo; anno a due cifre.

**In DottorCloud.** crm/invoicing/engine/codice_fiscale.py (carattere_controllo, normalizza per l'omocodia, valido, analizza, coerente_con_anagrafica); crm/invoicing/engine/anagrafica.py (errori, dati_dal_codice, incoerenze); CRMBillingProfile.leggi_il_codice; crm/importazione/regole.py (nascita_dal_codice, sesso); tastiera('codice') per fiscal_code e tax_id; il messaggio del profilo di fatturazione spiega già che l'ultimo carattere si calcola dagli altri.

**Come si verifica.** crm/invoicing/tests/test_identificativi.py. A mano: un codice scritto in minuscolo con spazi diventa maiuscolo e compatto; un'ultima lettera sbagliata dà il messaggio; per una persona nata nel 1925 la data proposta va confermata.

**Errori da evitare.** Verifica sul codice (11/10/2026): analizza() sceglie il secolo che non dà un anno futuro, così nel 2026 chi è nato nel 1925 risulta nato nel 2025, e il profilo di fatturazione scrive quella data di nascita senza chiedere; l'importazione controlla il codice fiscale solo con lo schema dei caratteri, la fatturazione anche con il carattere di controllo; il messaggio del profilo comincia con «Il codice fiscale … non è valido» (GOV.UK sconsiglia «valid» e «invalid») e solo dopo dice che l'ultimo carattere non corrisponde. Studio UX, ottobre 2026: il dialogo di una persona nuova non chiedeva il codice fiscale (gravità 3: tolto il blocco d'azienda, codice fiscale e data di nascita restano fuori, decisione di prodotto aperta).

**Fonti.**

- [python-stdnum — stdnum/it/codicefiscale.py](https://github.com/arthurdejong/python-stdnum/blob/master/stdnum/it/codicefiscale.py) — docstring del modulo; commento su \_date_digits; calc_check_digit(); get_birth_date() · Arthur de Jong e contributori (libreria open source) · consultato l'11/10/2026
- [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/#error-suggestion) — criteri 3.3.3 Error Suggestion (AA) e 3.3.7 Redundant Entry (A) · W3C · consultato l'11/10/2026
- [Recover from validation errors](https://design-system.service.gov.uk/patterns/validation/) — «How it works» (caratteri da ignorare in numeri e codici) · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026

### FORM-PARTITA-IVA · Partita IVA: undici cifre con la cifra di controllo, prefisso accettato

**Regola.** Il campo accetta la partita IVA con o senza «IT» e con spazi, la normalizza in undici cifre e controlla la cifra di controllo; per un cliente dell'Unione accetta il prefisso del paese e controlla il formato di quel paese; il codice fiscale di undici cifre di un ente si controlla allo stesso modo. Il messaggio dice che cosa non torna. Mai un campo numerico: lo zero iniziale fa parte del numero.

**Perché.** python-stdnum (le pagine dell'Agenzia delle Entrate non erano raggiungibili): la partita IVA «consists of 11 digits. The first 7 digits are a company identifier, the next 3 refer to the province of residence and the last is a check digit»; la libreria toglie spazi, trattini e il prefisso IT prima del controllo, e nel suo esempio «IT 00743110157» diventa «00743110157», che comincia con due zeri. Il motore di DottorCloud usa lo stesso tipo di controllo (partita_iva_valida) e avverte che il codice di undici cifre che il Sistema TS assegna ai medici senza partita IVA non lo supera. GOV.UK (Validation): ignorare spazi e punteggiatura dentro i codici. HTML: il tipo number non è adatto a ciò che è fatto di cifre ma non è, a rigore, un numero.

**Soglie ed eccezioni.** Undici cifre; l'ultima di controllo.

**In DottorCloud.** crm/invoicing/engine/codice_fiscale.py: partita_iva_valida, separa_partita_iva_ue, partita_iva_ue_valida (formati dei paesi dell'Unione e di Svizzera, Regno Unito, Norvegia e San Marino; un paese sconosciuto non passa), identificativo_ts_valido per il tracciato del Sistema TS; anagrafica.errori (tax_id); il messaggio del profilo di fatturazione «The VAT number {0} is not well formed for country {1}».

**Come si verifica.** crm/invoicing/tests/test_identificativi.py. A mano: «IT 00743110157» e «00743 110 157» (l'esempio di python-stdnum) passano allo stesso modo; «00743110158», con l'ultima cifra sbagliata, dà il messaggio.

**Errori da evitare.** Da evitare: confondere il codice di undici cifre del Sistema TS per i medici senza partita IVA con una partita IVA (lo segnala il motore); un campo type=number che perde gli zeri iniziali; rifiutare il prefisso «IT» incollato.

**Fonti.**

- [python-stdnum — stdnum/it/iva.py](https://github.com/arthurdejong/python-stdnum/blob/master/stdnum/it/iva.py) — docstring del modulo; compact(); validate() · Arthur de Jong e contributori (libreria open source) · consultato l'11/10/2026
- [Recover from validation errors](https://design-system.service.gov.uk/patterns/validation/) — «How it works» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [HTML Living Standard](https://html.spec.whatwg.org/multipage/input.html#when-number-is-not-appropriate) — § «Number state (type=number)», nota su ciò che è fatto di cifre ma non è un numero · WHATWG · consultato l'11/10/2026

### FORM-IBAN · IBAN: incollato, in maiuscolo, a gruppi di quattro

**Regola.** Il campo IBAN accetta il codice incollato con o senza spazi e in minuscolo, lo normalizza, controlla la lunghezza del paese (27 caratteri per l'Italia) e il controllo modulo 97, e lo mostra a gruppi di quattro; per un conto estero chiede il BIC solo se serve. L'errore dice che cosa controllare: la lunghezza o le cifre di controllo. Nessun maxlength che tagli un IBAN incollato con gli spazi.

**Perché.** python-stdnum (il registro IBAN di SWIFT e la norma ISO 13616 non erano raggiungibili; i dati della libreria sono generati dal registro di SWIFT, versione 101): le prime due lettere sono il paese, le due cifre seguenti il controllo ISO 7064 Mod 97, 10, il resto ha il formato del paese; per l'Italia il formato nazionale è una lettera, cinque cifre, cinque cifre e dodici caratteri alfanumerici, cioè 23 caratteri più i 4 iniziali: 27; format() lo scrive a gruppi di quattro. GOV.UK (Bank details): per i conti esteri di solito IBAN e BIC, mostrando solo i campi del paese scelto. GOV.UK (Text input): per i codici che non si ricordano a memoria, separare visivamente i caratteri aiuta a controllarli. COGA: dividere i numeri lunghi in gruppi. Il motore di DottorCloud: un IBAN troncato può superare per caso il controllo modulo 97, quindi conta anche la lunghezza.

**Soglie ed eccezioni.** Italia: 27 caratteri (IT, 2 cifre di controllo, 1 lettera, 5 cifre, 5 cifre, 12 caratteri alfanumerici); a gruppi di quattro sono 33 caratteri con gli spazi.

**In DottorCloud.** crm/invoicing/engine/codice_fiscale.py iban_valido (lunghezza per paese e modulo 97), usato per l'azienda emittente (crm_invoicing_company.py); l'IBAN di una riga di pagamento (CRM Invoice Payment) non passa da iban_valido; nell'XML gli spazi si tolgono (crm/invoicing/engine/fatturapa.py). tastiera('codice') per il campo iban (utils/tastiera.js, insieme CODICI). Nelle viste in sola lettura l'IBAN va mostrato a gruppi.

**Come si verifica.** crm/invoicing/tests/test_identificativi.py. A mano: incollare un IBAN con gli spazi e in minuscolo; cambiare una cifra: messaggio sulle cifre di controllo; togliere un carattere: messaggio sulla lunghezza.

**Errori da evitare.** Da evitare: maxlength=27, che taglia un IBAN incollato con gli spazi (33 caratteri); un campo numerico; rifiutare le minuscole invece di convertirle; controllare l'IBAN dell'azienda e non quello scritto sulla riga di pagamento.

**Fonti.**

- [python-stdnum — stdnum/iban.py](https://github.com/arthurdejong/python-stdnum/blob/master/stdnum/iban.py) — docstring del modulo (paese, cifre di controllo ISO 7064 Mod 97, 10, format() a gruppi) · Arthur de Jong e contributori (libreria open source) · consultato l'11/10/2026
- [python-stdnum — stdnum/iban.dat](https://github.com/arthurdejong/python-stdnum/blob/master/stdnum/iban.dat) — intestazione («generated from iban-registry-v101.txt») e riga IT (bban 1!a5!n5!n12!c) · Arthur de Jong e contributori (dati dal registro IBAN di SWIFT) · consultato l'11/10/2026
- [Bank details](https://design-system.service.gov.uk/patterns/bank-details/) — «International bank account details» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Text input](https://design-system.service.gov.uk/components/text-input/) — «Codes and sequences» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Making Content Usable for People with Cognitive and Learning Disabilities, pattern «Design Forms to Prevent Mistakes»](https://github.com/w3c/coga/blob/main/design-guide/o4p04-supportive-forms.html) — «What to Do» · W3C, COGA Task Force (bozza dell'editor, sorgente su GitHub) · consultato l'11/10/2026; versione pubblicata: https://www.w3.org/TR/coga-usable/

### FORM-CONTEGGIO · Limiti di lunghezza dichiarati, contati, mai tagliati in silenzio

**Regola.** Se un campo ha un limite (note, SMS, testo in fattura, causale), lo si dice prima, si mostra un conteggio sotto il campo mentre si scrive, annunciato a chi usa un lettore di schermo quando smette di scrivere, si lascia scrivere oltre e si segnala l'eccesso con un errore («Le note possono avere al massimo 500 caratteri»). Niente maxlength che taglia; i limiti si scelgono larghi.

**Perché.** GOV.UK (Character count): solo se c'è una buona ragione per limitare; il componente «does not restrict the user from entering information», così si può scrivere o incollare tutto e poi accorciare; il conteggio sta sotto il campo; chi usa un lettore di schermo lo sente quando smette di scrivere; si può mostrare da una soglia; limiti più alti di quanto serve ai più; il componente è stato provato nel 2017 con 17 persone, anche con poca dimestichezza digitale o con disabilità. GOV.UK (Text input): con maxlength «there is no feedback to users that their text input is truncated», soprattutto quando si incolla; se serve un limite, dirlo nell'aiuto, lasciar scrivere di più e dare errore solo dopo la normalizzazione. COGA: da evitare «Restricting entries to arbitrary lengths».

**Soglie ed eccezioni.** GOV.UK: con data-threshold il conteggio può comparire da una percentuale del limite (nell'esempio, il 75%).

**In DottorCloud.** Activities/SMSBox.vue mostra già i caratteri e il numero di messaggi (smsSegments in utils/conversation.js), con l'avviso «Caratteri speciali»; il conteggio va annunciato (aria-live polite) e la spiegazione detta anche fuori dal tooltip. I limiti di crm/www/book.html (maxlength 140 su nome ed email, 30 sul telefono, 1000 sulle note) e quello delle parole di un punto del disegno sul corpo (maxlength 120 in crm/public/js/moduli_campi.js) diventano limiti dichiarati con un errore.

**Come si verifica.** Incollare un testo più lungo del limite: niente viene tagliato e l'errore dice di quanto si è oltre. Il lettore di schermo annuncia il conteggio. tests/unit/conversation.test.js per smsSegments.

**Errori da evitare.** Verifica sul codice (11/10/2026): in SMSBox.vue il perché di «Caratteri speciali» sta solo in un tooltip, che sul telefono non si apre, e il conteggio non è in una regione viva; maxlength in book.html e in moduli_campi.js (nei campi codice tolto il 12/10/2026). Da evitare: un limite stretto scelto senza dati; un conteggio che si legge a ogni tasto premuto.

**Fonti.**

- [Character count](https://design-system.service.gov.uk/components/character-count/) — «When to use this component», «How it works», «Avoid narrow limits», «Error messages», «Research on this component» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Text input](https://design-system.service.gov.uk/components/text-input/) — «Avoid restricting the length of a user's input» · GOV.UK Design System, Government Digital Service · consultato l'11/10/2026
- [Making Content Usable for People with Cognitive and Learning Disabilities, pattern «Accept different input formats»](https://github.com/w3c/coga/blob/main/design-guide/o4p08-input-formats.html) — «Examples» › «Avoid» · W3C, COGA Task Force (bozza dell'editor, sorgente su GitHub) · consultato l'11/10/2026; versione pubblicata: https://www.w3.org/TR/coga-usable/

### FORM-DOPPIONI · Prima di creare, cercare: una persona non nasce due volte

**Regola.** Un modulo che crea una persona o un'azienda parte dalla ricerca: si sceglie chi c'è già e, solo se non c'è, si crea. Prima di salvare, il sistema confronta i dati scritti con quelli esistenti (codice fiscale, email, cellulare, nome con data di nascita) e, se trova una corrispondenza, la propone senza bloccare («C'è già Maria Rossi, nata il 12/05/1980: è lei?»). Nei risultati di ricerca ogni persona porta un secondo identificativo, come la data di nascita o il telefono.

**Perché.** COGA («Design Forms to Prevent Mistakes»): «Using an interface where only valid input can be selected» e «Providing the user with known suggestions and corrections». WCAG 3.3.3 (AA): quando la correzione è nota, va proposta. Designers Italia (Form): i dati che si possiedono già si fanno validare invece di farli reinserire. Nello studio UX una trattativa creata da zero riscriveva una persona già presente.

**Soglie ed eccezioni.** WCAG 3.3.3 (AA).

**In DottorCloud.** chiavi() in crm/importazione/regole.py (codice fiscale, email, ultime nove cifre del cellulare, nome con data di nascita) e la regola dell'importazione di una sola corrispondenza sono il criterio da riusare nei dialoghi; find_or_create_person (crm/api/booking.py) e trova_per_nome (crm/persone/collegate.py) nelle prenotazioni; Controls/Link.vue per scegliere la persona esistente; in Modals/DealModal.vue «Scegli una persona esistente» viene per primo ed è acceso.

**Come si verifica.** Creare una persona con lo stesso codice fiscale o la stessa email di una esistente: il dialogo la propone. Cercare due omonimi: si distinguono nei risultati.

**Errori da evitare.** Studio UX, ottobre 2026: in «Crea una trattativa» si scriveva la persona a mano invece di sceglierla, creando doppioni (gravità 3, corretto); gli elenchi di persone non mostrano un secondo identificativo (gravità 2, aperto). Da evitare: bloccare la creazione per un omonimo (due persone diverse possono chiamarsi allo stesso modo); confrontare i telefoni come testo invece che in E.164 o sulle ultime cifre.

**Vedi anche.** [SAN-OMONIMI](08-persone-e-dati-personali.md#san-omonimi--gli-omonimi-si-segnalano-prima-che-diventino-un-doppione-o-uno-scambio)

**Fonti.**

- [Making Content Usable for People with Cognitive and Learning Disabilities, pattern «Design Forms to Prevent Mistakes»](https://github.com/w3c/coga/blob/main/design-guide/o4p04-supportive-forms.html) — «What to Do» · W3C, COGA Task Force (bozza dell'editor, sorgente su GitHub) · consultato l'11/10/2026; versione pubblicata: https://www.w3.org/TR/coga-usable/
- [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/#error-suggestion) — criterio 3.3.3 Error Suggestion (AA) · W3C · consultato l'11/10/2026
- [Form](https://designers.italia.it/design-system/componenti/form/) — «Come usarlo» › «Attenzione a» · Designers Italia · consultato l'11/10/2026
