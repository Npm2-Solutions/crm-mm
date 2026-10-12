# 8. La persona giusta e i suoi dati

<!-- Copyright (c) 2026, NPM2 Solutions Srl and contributors -->

Una delle famiglie dei [principi di esperienza e interfaccia](../66-principi-di-esperienza.md) (doc 66): come leggerle, la lista di controllo per una schermata e come sono state verificate le fonti sono lì.

Questa famiglia raccoglie le regole che proteggono il paziente e i suoi dati in ogni schermata di DottorCloud: la scrivania (/crm) su computer, tablet e telefono, l'area dei pazienti (/area) e le pagine pubbliche (/prenota, /modulo). Le regole sono queste: riconoscere sempre la persona giusta, con due identificativi; non perdere il lavoro interrotto; interrompere solo per ciò che è grave; mostrare i dati sanitari solo a chi li legge, mai in notifiche, liste, copie o nel browser; far partire spento ciò che espone dati; chiedere il consenso solo dove serve, in modo onesto e ritirabile; usare l'assistente solo per bozze che una persona rivede. In un centro medico uno scambio di persona o un dato sanitario fuori posto fa danno a qualcuno: lo studio UX di ottobre 2026 ha dato gravità 3 proprio alla testata della persona senza un secondo identificativo, su computer e telefono.

Come sono state verificate le fonti, il 12/10/2026. Durante la ricerca si aprivano solo GitHub, i siti di Apple e Android e il dataset Open Access di PubMed Central; EUR-Lex, Garante, EDPB, Normattiva, NIST, Joint Commission, AHRQ, ISO, IEC e Commissione europea non si aprivano. Perciò:

- i testi di W3C (WCAG 2.2 e Privacy Principles del TAG), NIST SP 800-63B-4, OWASP, MDN, WHATWG e NHS sono letti dai loro repository ufficiali su GitHub, e si cita l'indirizzo pubblico;
- la SAFER Guide sull'identificazione del paziente (revisione 2024) è letta per intero nell'appendice C dell'articolo di JAMIA Open che la presenta, dal dataset Open Access di PubMed Central;
- il GDPR è letto dalla copia GDPRtEXT (ADAPT Centre) del testo inglese della GU L 119 del 4/5/2016; l'AI Act, con le modifiche del Regolamento (UE) 2026/1744, dalla copia superuserkalo/eu-ai-act generata dai documenti dell'Ufficio delle pubblicazioni; gli abstract di ISO, IEC e NIST dai metadati dei cataloghi (relaton);
- NISTIR 7804 e 7804-1, Joint Commission, AHRQ PSNet, EDPB, Garante, MDCG, L. 132/2025 e la clausola 5 della ISO 9241-210 sono letti solo dai risultati di WebSearch: le fonti lo dicono con «via WebSearch» e restano solo le affermazioni che la ricerca ha confermato.

Non si sono potute confermare, e sono state tolte, le cifre della NIST GCR 15-996, le affermazioni attribuite alla NISTIR 7865 e al commento del caso PSNet, e il primato dell'adattamento al ruolo contro gli avvisi. La NISTIR 7865 citata dalla rubrica dello studio è la guida NIST del 2012 sulle interazioni critiche nella cura pediatrica: le linee guida NIST su dove e come mostrare l'identità del paziente sono nella NISTIR 7804-1 (2015), quelle sul copia-incolla nella NISTIR 8166 (2017).

Joint Commission, ONC e NIST non obbligano un centro italiano: qui sono riferimenti di buona pratica. Le leggi europee e italiane sono dette per ciò che chiedono e a chi. Ciò che «apply» e «pitfalls» dicono del codice è verificato sul commit 19cea4a dell'11/10/2026; «(studio UX, ottobre 2026)» indica un rilievo dello studio, «corretto» un rilievo già risolto nel codice.

I principi che esistono solo per i dati sanitari e per il lavoro clinico (chi legge la cartella, il lucchetto e l'oscuramento, il registro degli accessi, le allerte cliniche, la firma di un referto, il regolamento sui dispositivi medici) sono nel verticale della clinica: [I principi sanitari](../../verticali/clinica/principi-sanitari.md).

## I principi

- [SAN-IDENTITA-TESTATA · Il paziente sempre identificato, nello stesso posto](#san-identita-testata--il-paziente-sempre-identificato-nello-stesso-posto)
- [SAN-DUE-IDENTIFICATIVI · Due identificativi in ogni scelta e in ogni risultato](#san-due-identificativi--due-identificativi-in-ogni-scelta-e-in-ogni-risultato)
- [SAN-OMONIMI · Gli omonimi si segnalano prima che diventino un doppione o uno scambio](#san-omonimi--gli-omonimi-si-segnalano-prima-che-diventino-un-doppione-o-uno-scambio)
- [SAN-NOME-INTERO · Il nome non si taglia dove serve a riconoscere](#san-nome-intero--il-nome-non-si-taglia-dove-serve-a-riconoscere)
- [SAN-CONTESTO-GIUSTO · Si vede sempre per chi si sta scrivendo](#san-contesto-giusto--si-vede-sempre-per-chi-si-sta-scrivendo)
- [SAN-STAMPE · Ogni documento stampato o in PDF porta due identificativi](#san-stampe--ogni-documento-stampato-o-in-pdf-porta-due-identificativi)
- [SAN-ACCOGLIENZA-VERIFICA · All'accoglienza l'identità si conferma attivamente](#san-accoglienza-verifica--allaccoglienza-lidentità-si-conferma-attivamente)
- [SAN-CHI-AGISCE-PER-CHI · Si vede chi agisce per chi, e chi è assistito ha la sua scheda](#san-chi-agisce-per-chi--si-vede-chi-agisce-per-chi-e-chi-è-assistito-ha-la-sua-scheda)
- [SAN-BOZZA-MAI-PERSA · Il lavoro interrotto non si perde](#san-bozza-mai-persa--il-lavoro-interrotto-non-si-perde)
- [SAN-SESSIONE-CONDIVISA · Sessioni adatte a un PC di segreteria condiviso](#san-sessione-condivisa--sessioni-adatte-a-un-pc-di-segreteria-condiviso)
- [PRIV-MINIMO-IN-LISTE-E-COPIE · Liste, anteprime e copie portano il minimo](#priv-minimo-in-liste-e-copie--liste-anteprime-e-copie-portano-il-minimo)
- [PRIV-NULLA-NEL-BROWSER · Nulla di personale resta nel browser](#priv-nulla-nel-browser--nulla-di-personale-resta-nel-browser)
- [PRIV-ANTEPRIMA-DI-CHI-GUARDA · L'anteprima dell'area mostra solo ciò che può leggere chi guarda](#priv-anteprima-di-chi-guarda--lanteprima-dellarea-mostra-solo-ciò-che-può-leggere-chi-guarda)
- [PRIV-CONSENSO-GRANULARE · Il consenso solo dove serve: per finalità, al momento giusto, ritirabile come si è dato](#priv-consenso-granulare--il-consenso-solo-dove-serve-per-finalità-al-momento-giusto-ritirabile-come-si-è-dato)
- [PRIV-NIENTE-INGANNI · Scelte sulla privacy senza trucchi](#priv-niente-inganni--scelte-sulla-privacy-senza-trucchi)
- [PRIV-PREDEFINITO-PROTETTIVO · Ciò che fa uscire o mostrare dati parte spento](#priv-predefinito-protettivo--ciò-che-fa-uscire-o-mostrare-dati-parte-spento)
- [PRIV-MINIMO-NEI-MODULI · Chiedere solo ciò che serve, compreso ciò che serve alla sicurezza](#priv-minimo-nei-moduli--chiedere-solo-ciò-che-serve-compreso-ciò-che-serve-alla-sicurezza)
- [PRIV-BANCONE · Lo schermo del bancone e il tablet li vedono anche i pazienti](#priv-bancone--lo-schermo-del-bancone-e-il-tablet-li-vedono-anche-i-pazienti)
- [IA-REVISIONE-UMANA · L'assistente scrive bozze, la persona decide](#ia-revisione-umana--lassistente-scrive-bozze-la-persona-decide)
- [IA-TRASPARENZA · Si dice sempre dove c'è l'intelligenza artificiale](#ia-trasparenza--si-dice-sempre-dove-cè-lintelligenza-artificiale)
- [IA-DATI-MINIMI · Al modello va il minimo, e solo con il consenso](#ia-dati-minimi--al-modello-va-il-minimo-e-solo-con-il-consenso)
- [IA-EMERGENZA-E-SALUTE · Un'emergenza va subito al 112, una domanda di salute a una persona](#ia-emergenza-e-salute--unemergenza-va-subito-al-112-una-domanda-di-salute-a-una-persona)

### SAN-IDENTITA-TESTATA · Il paziente sempre identificato, nello stesso posto

**Regola.** Ogni schermata che legge o scrive qualcosa di una persona mostra, sempre nello stesso punto e senza dover scorrere, il nome completo e un secondo identificativo stabile: la data di nascita con l'età, più il sesso dove serve alla cura. La riga resta visibile quando la testata si ripiega, dentro i dialoghi che agiscono sulla persona e per qualunque ruolo apra la persona. Se la data manca, la riga lo dice («Data di nascita mancante») e offre il modo di aggiungerla.

**Perché.** La NISTIR 7804 (NIST, 2012) apre l'elenco dei suoi principi di progettazione con l'errore d'identificazione del paziente (1A): azioni eseguite per un paziente, o documentate nella sua cartella, che erano destinate a un altro. La NISTIR 7804-1 (NIST, 2015) dà linee guida per tre aree di rischio d'uso critico; contro l'errore di paziente sbagliato chiede un'area riservata all'identificazione, separata dal resto, in alto a sinistra di ogni schermata e finestra, che resti nello stesso posto qualunque scorrimento o navigazione (linea guida 1.2), con nome, data di nascita, età, sesso e numero di cartella in quest'ordine; sugli schermi piccoli la stessa sequenza in orizzontale. La SAFER Guide sull'identificazione del paziente (ONC/ASTP, revisione 2024) dà forza «Strong» alla raccomandazione 1.3: le informazioni per identificare il paziente sono ben visibili in tutte le parti dell'interfaccia (nome completo, data di nascita con l'età calcolata, sesso, numero di cartella, una foto recente), in caratteri grandi, con poco intorno, nello stesso posto in tutte le schermate e preferibilmente in alto a sinistra; il solo nome non basta. Lo studio UX di ottobre 2026 ha trovato una testata della persona con solo il nome, «Paziente dal…» e l'ultima visita: il genere era il sesto campo della sezione Persona e il codice fiscale stava a circa 887 px dall'alto, quindi chi scriveva una visita non aveva un secondo identificativo davanti (gravità 3, su computer e telefono).

**Soglie ed eccezioni.** Due identificativi come minimo: il nome completo e la data di nascita con l'età in anni compiuti (sotto l'anno: «meno di un anno»). Visibili senza scorrere a 1280, 360 e 320 px, anche con la tastiera aperta. In alto a sinistra e sempre nello stesso posto (NISTIR 7804-1, linea guida 1; SAFER 1.3). La SAFER Guide ammette eccezioni per chi un dato mostrato metterebbe a rischio (per esempio chi ha subito violenza domestica).

**In DottorCloud.** `frontend/src/components/PersonHeader.vue` mostra già età e data nella riga sotto il nome (`etaENascita` in `frontend/src/utils/schedaPersona.js`). Però le legge dal profilo di fatturazione (`crm.invoicing.anagrafica.get_billing_profile`) e solo per chi ha `persone.dati_fiscali` (`fiscali ? etaENascita(...) : null`), perché `CRM Lead` non ha una data di nascita propria: il dato vive in `CRM Billing Profile.birth_date`. Va reso un dato della persona, che legge chiunque apra la scheda: lo studio lo lascia come decisione di prodotto (gravità 1). Sul computer la testata sta nel pannello di destra (`pages/Lead.vue`, il `Resizer` a destra) e in alto a sinistra le briciole mostrano solo il nome: età e data vanno portate lì, oppure ripetute in testa alla colonna delle schede, dove si scrive. Sul telefono `composables/testataRaccolta.js` ripiega la scheda mentre si scorre e lascia il nome nella testata: va aggiunta l'età («Noemi Carbone · 65 anni»). I dialoghi che agiscono sulla persona ripetono nome e data in testa (`Calendar/AppointmentPanel.vue`, `Invoices/InvoiceDialog.vue`, la visita in `Clinic/ClinicArea.vue`, `pages/FormFill.vue`): chi lavora dentro un foglio non vede la pagina che sta sotto. Dove il centro raccoglie una foto, la SAFER Guide la vuole nelle testate, nelle liste e nella ricerca (raccomandazione 2.5).

**Come si verifica.** Rivedere a mano ogni schermata clinica a 1280, 360 e 320 px, nel tema chiaro e scuro: nome e data devono essere visibili senza scorrere, anche dopo aver scorso una scheda e con la tastiera aperta. Ripetere con un utente senza `persone.dati_fiscali` e con una persona senza profilo di fatturazione. Test unitari di `etaENascita` in `tests/unit/schedaPersona.test.js`: compleanno non ancora arrivato, 29 febbraio, data futura, data assente. Uno script Playwright apre `/crm/persone/<nome>#clinic` e cerca l'età nella testata e nella riga in alto a sinistra.

**Errori da evitare.**

- Legare l'identificativo a un permesso fiscale: chi non lo ha vede solo il nome (com'è oggi in `PersonHeader.vue`).
- Mostrare l'età senza la data, o la data senza l'età: in accoglienza si confronta la data che la persona dice a voce.
- Lasciare che la testata, ripiegandosi, porti via il secondo identificativo proprio mentre si scrive la visita.
- Affidare la data, o il nome intero, a un tooltip: sul telefono non si apre. In `PersonHeader.vue` il nome è un `h1` con `truncate`, e un nome lungo finisce in «…».
- Tenere il profilo in cache per mostrarlo prima. La prima versione dell'età in testata metteva il profilo fiscale in IndexedDB: su un PC di segreteria condiviso un collega senza permesso sui dati fiscali vedeva la data letta dall'utente precedente. La revisione del codice dello studio l'ha trovato e ha tolto `cache` (studio UX, ottobre 2026; corretto).

**Fonti.**

- [NISTIR 7804 — Technical Evaluation, Testing and Validation of the Usability of Electronic Health Records](https://nvlpubs.nist.gov/nistpubs/ir/2012/NIST.IR.7804.pdf) — Principi 1A–1H, 1A «patient identification error» (letto via WebSearch) · NIST · 2012; letto via WebSearch il 12/10/2026
- [NISTIR 7804-1 — Technical Evaluation, Testing, and Validation of the Usability of Electronic Health Records: Empirically Based Use Cases for Validating Safety-Enhanced Usability and Guidelines for Standardization](https://nvlpubs.nist.gov/nistpubs/ir/2015/nist.ir.7804-1.pdf) — Abstract (tre aree di rischio d'uso critico; letto dai metadati relaton-data-nist su GitHub); linea guida 1 sull'identificazione del paziente: area riservata in alto a sinistra, stesso posto qualunque scorrimento (1.2), ordine nome, data di nascita, età, sesso, numero di cartella (letta via WebSearch) · NIST · 2015; linea guida letta via WebSearch il 12/10/2026
- [Appendix C. 2024 Patient Identification SAFER Guide (materiale supplementare di «Developing updated and new guidance to promote reliable patient identification»)](https://pmc-oa-opendata.s3.amazonaws.com/PMC12772641.1/ooaf160_supplementary_data.docx) — Recommended Practice 1.3 (Strong) con la sua Implementation Guidance; Recommended Practice 2.5 (foto) · JAMIA Open (Oxford University Press), dal dataset Open Access di PubMed Central · 2026; letto il 12/10/2026
- [SAFER Guides — Patient Identification](https://healthit.gov/wp-content/uploads/2025/01/Safer-Guide-6.-Patient-Identification-Final.pdf) — La guida pubblicata (indirizzo confermato via WebSearch; il testo è letto nell'appendice C indicata sopra) · ONC/ASTP, U.S. Department of Health and Human Services · 2025; letto via WebSearch il 12/10/2026

### SAN-DUE-IDENTIFICATIVI · Due identificativi in ogni scelta e in ogni risultato

**Regola.** Dove si sceglie o si riconosce una persona, ogni riga mostra il nome e almeno un secondo identificativo stabile: data o anno di nascita, età o codice fiscale, e non solo telefono o email. Vale per la ricerca, il selettore della persona nell'appuntamento e nella fattura, le liste, l'agenda, l'accoglienza, le conversazioni, le chiamate e le note. Anche dopo la scelta, la persona scelta resta scritta con i due identificativi. Le liste di persone seguono l'ordine del lavoro (l'ora, la data), non quello alfabetico.

**Perché.** La Joint Commission chiede almeno due identificativi del paziente quando si presta cura, trattamento o servizi: per il programma ambulatoriale è NPSG.01.01.01, in vigore da gennaio 2026, e ammette come identificativi il nome, un numero assegnato, il numero di telefono o un altro identificativo personale; la versione per i pazienti dice «per esempio nome e data di nascita». Per gli ospedali, dal 1° gennaio 2026 gli obiettivi sono diventati National Performance Goals, e NPG.01.01.01 chiede un processo per identificare correttamente i pazienti. La Quick Safety 45 della Joint Commission (2018) ricorda che l'identificazione avviene dal foglio firme alla prenotazione online alla cartella elettronica. La SAFER Guide (revisione 2024, raccomandazione 1.2, forza «Strong») vuole due o più identificativi per ogni paziente nelle liste, il nome completo, i cognomi uguali o simili resi visivamente distinti e un ordine utile al lavoro (per esempio l'ora dell'appuntamento) invece di quello alfabetico, che avvicina i nomi simili; vuole la foto, dove c'è, nelle testate, nelle liste, nell'agenda, nella ricerca e nei messaggi (2.5); e avverte che verificare l'identità solo confermando nome e data di nascita è soggetto a errore umano (1.4). Sono norme e guide statunitensi, usate qui come riferimento.

**Soglie ed eccezioni.** Almeno 2 identificativi per riga. Il telefono è ammesso dalla Joint Commission, ma in DottorCloud spesso è condiviso in famiglia: non basta come unico secondo identificativo. Ordine predefinito delle liste del giorno: per ora o data (SAFER 1.2).

**In DottorCloud.** Il selettore della persona è il `Link` su `CRM Lead` (`components/Controls/Link.vue`); la riga di descrizione viene da `search_fields: mobile_no,email` del DocType (`crm/fcrm/doctype/crm_lead/crm_lead.json`). Va aggiunta la data o l'anno di nascita, il che richiede di avere la data sulla persona oppure di leggerla dal profilo durante la ricerca. Nel pannello dell'appuntamento, dopo la scelta, sotto il nome compaiono solo telefono ed email (`AppointmentPanel.vue`, `leggibile(row.phone)`): va aggiunta la data. Nella lista Persone e sul telefono (`Mobile/ElencoPersone.vue`, `crm/api/sul_telefono.py`, `utils/sulTelefono.js`) va aggiunta l'età o l'anno alla riga, almeno quando lo stesso nome compare due volte. In agenda la persona apre già il blocco (`testoDelBlocco` in `utils/agenda.js`); in Accoglienza no: `pages/Today.vue` mostra prima l'ora e la riga «servizio · seduta · professionista» (`appointmentLine`), e solo sotto il nome (`Today/ParticipantRow.vue`), da invertire. Nelle chiamate serve una prima colonna «Persona» uguale per entrata e uscita.

**Come si verifica.** Per ogni selettore e lista, cercare un cognome ripetuto nei dati di prova (Barbieri, Fabbri) e verificare che le righe si distinguano senza aprirle. Test unitari delle funzioni che compongono le righe (`contattoDi`, `rigaDellaNota` in `tests/unit/sulTelefono.test.js`), con la data presente e assente. Rivedere le colonne e l'ordine predefiniti delle liste di persone, conversazioni e chiamate.

**Errori da evitare.**

- Il cellulare come unico secondo identificativo: un genitore e i figli che prenota condividono il numero (studio UX, ottobre 2026).
- La riga della nota sul telefono «Giulia Ferri · Emma D'Angelo · ieri», con due nomi e nessun ruolo: il dolore lombare si può attribuire alla persona sbagliata (`rigaDellaNota` mette prima l'autore; studio UX, ottobre 2026).
- Le chiamate che mettono il paziente in «Chiamante» o in «Destinatario» a seconda della direzione (studio UX, ottobre 2026).
- «Ancora senza esito» in Accoglienza con solo il nome, senza ora, servizio né professionista: due appuntamenti della stessa persona nello stesso giorno danno righe identiche (studio UX, ottobre 2026).
- Riconoscere qualcuno dal posto in cui sta («quella delle 9:30 in ambulatorio 2»): nei suoi obiettivi per gli ospedali la Joint Commission esclude il numero di stanza e il luogo fisico come identificativo.

**Vedi anche.** [SAN-ACCOGLIENZA-VERIFICA](#san-accoglienza-verifica--allaccoglienza-lidentità-si-conferma-attivamente), [SAN-STAMPE](#san-stampe--ogni-documento-stampato-o-in-pdf-porta-due-identificativi)

**Fonti.**

- [National Patient Safety Goals® Effective January 2026 for the Ambulatory Health Care Program](https://digitalassets.jointcommission.org/api/public/content/92c95c4e94304b2084e7e039d916719b?v=3c64fe83) — NPSG.01.01.01: almeno due identificativi; ammessi nome, numero assegnato, telefono, altro identificativo personale (letto via WebSearch) · The Joint Commission · 2026; letto via WebSearch il 12/10/2026
- [2026 Ambulatory Health Care National Patient Safety Goals (versione di facile lettura)](https://digitalassets.jointcommission.org/api/public/content/3103ce682c16469a8d8d5425e9082df9?v=1912053f) — Obiettivo 1: nome e data di nascita come esempio (letto via WebSearch) · The Joint Commission · 2026; letto via WebSearch il 12/10/2026
- [National Performance Goals™ Effective January 2026 for the Hospital Program](https://digitalassets.jointcommission.org/api/public/content/9ca80055182b4274842a5780a94f2c82) — NPG.01.01.01; i National Performance Goals sostituiscono il capitolo NPSG per ospedali dal 1/1/2026 (letto via WebSearch) · The Joint Commission · 2026; letto via WebSearch il 12/10/2026
- [National Patient Safety Goals® Effective January 2025 for the Hospital Program](https://digitalassets.jointcommission.org/api/public/content/9be383450fc941df806b76c5fbdd9ae6?v=3c600c3a) — NPSG.01.01.01: il numero di stanza o il luogo fisico non si usano come identificativo (letto via WebSearch) · The Joint Commission · 2025; letto via WebSearch il 12/10/2026
- [Quick Safety Issue 45: People, processes, health IT and accurate patient identification](https://digitalassets.jointcommission.org/api/public/content/2dc4cad7bdc34451b85a2be5431f09ef?v=c9afdcd7) — Introduzione: l'identificazione avviene dal foglio firme alla prenotazione online alla cartella elettronica (letto via WebSearch) · The Joint Commission · 2018; letto via WebSearch il 12/10/2026
- [Appendix C. 2024 Patient Identification SAFER Guide (materiale supplementare di «Developing updated and new guidance to promote reliable patient identification»)](https://pmc-oa-opendata.s3.amazonaws.com/PMC12772641.1/ooaf160_supplementary_data.docx) — Recommended Practice 1.2 (Strong) e Implementation Guidance; 1.4 (Rationale); 2.5 (Implementation Guidance) · JAMIA Open (Oxford University Press), dal dataset Open Access di PubMed Central · 2026; letto il 12/10/2026

### SAN-OMONIMI · Gli omonimi si segnalano prima che diventino un doppione o uno scambio

**Regola.** Quando si crea, si importa o si prenota una persona, DottorCloud cerca chi ha lo stesso nome e cognome, anche scritti in modo simile, e la stessa data di nascita, oppure lo stesso codice fiscale. Se lo trova, lo dice prima di salvare, con i dati che servono a decidere (data di nascita, telefono, ultima visita), e propone di aprire la scheda che esiste già. Nelle liste e nei risultati di ricerca, quando lo stesso nome compare due volte, le righe si distinguono a colpo d'occhio. Un abbinamento automatico per nome si fa solo quando la corrispondenza è unica.

**Perché.** La SAFER Guide (revisione 2024, raccomandazione 1.6, forza «Medium») vuole avvisato chi crea una persona nuova con lo stesso nome e cognome di un'altra e chi cerca e trova più persone con nomi uguali o simili: con un algoritmo fonetico per i nomi che suonano uguali, con i dati in più che aiutano a confermare o escludere che sia la stessa persona, guardando anche alle varianti del nome e ai cognomi cambiati. Per la raccomandazione 1.1 chi registra deve vedere i possibili doppioni prima di creare una scheda nuova; la 3.2 chiama doppione due cartelle della stessa persona e «overlay» una persona registrata o documentata nella cartella di un'altra. L'articolo che presenta la revisione (JAMIA Open, 2026) ricorda che alla registrazione un abbinamento sbagliato crea un doppione o mette la persona nella cartella di un'altra. Nel caso PSNet «New Patient Mistakenly Checked in as Another» un uomo di 55 anni, nuovo, aveva lo stesso nome, cognome ed età di un paziente già noto, nato in un altro giorno: una receptionist nuova, alle prese con un sistema appena installato, lo registrò sulla cartella dell'altro, e i suoi esami arrivarono all'altro paziente attraverso il portale.

**Soglie ed eccezioni.** Stesso nome e cognome (confrontati per parole, senza accenti né maiuscole) più la stessa data di nascita: l'avviso chiede una scelta («È questa persona» / «È un'altra persona»). Nome e cognome uguali o simili con date diverse: avviso informativo con le due date affiancate (SAFER 1.6).

**In DottorCloud.** Oggi il modulo rapido della persona (`LEAD_QUICK_ENTRY` in `crm/install.py`) non chiede la data di nascita e nessun controllo avvisa degli omonimi. Altre parti si comportano già bene: l'importazione abbina per nome e nascita solo se trova un'unica corrispondenza (`_per_nome_e_nascita` in `crm/importazione/importa.py`, con le chiavi di `crm/importazione/regole.py`); le prenotazioni trovano il titolare del contatto per email o telefono e la persona per nome tra le persone collegate (`trova_per_nome` in `crm/persone/collegate.py`; `find_or_create_person` in `crm/api/booking.py`); il confronto dei nomi per parole esiste in `crm/persone/legami.py` (`parole`, `stesso_nome`). Cosa aggiungere:

- al modulo rapido, la data di nascita (proposta; facoltativa dove il centro non è sanitario);
- un controllo lato server che restituisca i candidati prima dell'inserimento, con data di nascita e ultima visita;
- nei risultati del `Link` e nelle liste, gli omonimi resi distinti (grassetto o un segno con parole);
- sulla pagina della persona, un segno «C'è anche Maria Rossi, nata il …».

**Come si verifica.** Test unitari della regola di somiglianza: accenti, apostrofi, doppio nome, cognome scritto per primo (accanto a `crm/persone/tests/test_legami.py`). Test sul sito: creare due volte «Mario Rossi, 1/1/1980» e verificare l'avviso; importare un foglio con due omonimi e verificare che nessuno venga abbinato a caso (`crm/importazione/tests/test_importa.py`). Scenario in accoglienza con un paziente nuovo omonimo di uno già noto.

**Errori da evitare.**

- Un avviso che arriva dopo il salvataggio, quando il doppione esiste già e qualcuno ci scrive sopra.
- Unire due schede «uguali» senza controllare la data di nascita.
- Prendere la scheda del genitore per il figlio perché email e telefono coincidono.
- Il dialogo «Crea una trattativa» con «Scegli una persona esistente» spento all'apertura: chi scrive nome e cognome crea un doppione invece di scegliere la persona già in archivio (studio UX, ottobre 2026, gravità 3, su computer e telefono).

**Vedi anche.** [FORM-DOPPIONI](06-moduli.md#form-doppioni--prima-di-creare-cercare-una-persona-non-nasce-due-volte)

**Fonti.**

- [Appendix C. 2024 Patient Identification SAFER Guide (materiale supplementare di «Developing updated and new guidance to promote reliable patient identification»)](https://pmc-oa-opendata.s3.amazonaws.com/PMC12772641.1/ooaf160_supplementary_data.docx) — Recommended Practice 1.6 (Medium, «Name alert») e Implementation Guidance; 1.1 (Implementation Guidance); 3.2 (Rationale) · JAMIA Open (Oxford University Press), dal dataset Open Access di PubMed Central · 2026; letto il 12/10/2026
- [Developing updated and new guidance to promote reliable patient identification](https://pmc.ncbi.nlm.nih.gov/articles/PMC12772641/) — Discussion (errori alla registrazione); Table 1 · JAMIA Open, vol. 9, n. 1, ooaf160 (E. Weatherford e altri, tra cui D. F. Sittig, H. Singh, J. S. Adelman) · 2026; testo letto dal dataset Open Access di PubMed Central (PMC12772641.1) il 12/10/2026
- [New Patient Mistakenly Checked in as Another (WebM&M)](https://psnet.ahrq.gov/web-mm/new-patient-mistakenly-checked-another) — Il caso (letto via WebSearch; il commento non si è potuto leggere) · AHRQ PSNet · letto via WebSearch il 12/10/2026

### SAN-NOME-INTERO · Il nome non si taglia dove serve a riconoscere

**Regola.** Dove lo spazio è poco (blocchi dell'agenda, vista del mese, righe sul telefono, chip, testate) il nome della persona viene prima di ora, servizio e segni, e va a capo invece di finire in «…». Se proprio deve accorciarsi, tiene il cognome intero e l'iniziale del nome («Fontana M.»). Servizio e stato non si affidano al solo colore.

**Perché.** La SAFER Guide (revisione 2024, raccomandazione 1.2, forza «Strong») vuole il nome completo del paziente nelle liste, caratteri e spaziature che riducano il rischio di scegliere la riga sbagliata, e i cognomi uguali o simili resi visivamente distinti. La NISTIR 7804-1 (2015) chiede che l'identificazione stia sempre nello stesso posto e nello stesso ordine. Lo studio UX di ottobre 2026 ha trovato due casi concreti: nella vista del mese, con il pannello del nuovo appuntamento aperto, restava «09:00 Maria F…» o «08:30 Giorgia …», e due pazienti con lo stesso nome nello stesso giorno non si distinguevano; nella vista giorno del telefono «09:00 Daniela Catta…» rendeva uguali Cattaneo e Cattani.

**Soglie ed eccezioni.** Il cognome è sempre intero. Nei blocchi brevi la prima riga intera è del nome. Una voce toccabile è alta almeno 24 px (WCAG 2.5.8, trattato nella famiglia dell'accessibilità).

**In DottorCloud.** `frontend/src/utils/agenda.js` (`righeDelBlocco`, `testoDelBlocco`, `paroleDelBlocco`) mette già la persona per prima e disegna solo righe intere. Manca una forma corta «Cognome I.» per le celle strette di `Calendar/MeseAgenda.vue`, `BloccoAgenda.vue` e `VistaDelTelefono.vue`. In Accoglienza (`pages/Today.vue`) il nome deve aprire la riga, con sotto «servizio · seduta · professionista». Nella testata della persona (`PersonHeader.vue`) il nome è un `h1` con `truncate`: un nome lungo finisce in «…» e si legge intero solo nel tooltip, che sul telefono non si apre; meglio che vada a capo, al massimo su due righe.

**Come si verifica.** Test unitari della forma corta in `tests/unit/agenda.test.js`: «De Luca», «D'Angelo», nomi doppi, cognomi composti. Revisione visiva a 360 e 320 px con il pannello del nuovo appuntamento aperto, usando dati di prova che contengano omonimi e cognomi simili.

**Errori da evitare.**

- `truncate` sul nome e `break-words` sul servizio: esattamente il contrario di ciò che serve.
- Tagliare il cognome per far posto all'ora.
- Un servizio leggibile solo dal colore della barretta, senza legenda (studio UX, ottobre 2026).

**Vedi anche.** [MOB-LISTE](05-telefono-e-tocco.md#mob-liste--liste-del-telefono-una-riga-per-cosa-lidentità-per-prima)

**Fonti.**

- [Appendix C. 2024 Patient Identification SAFER Guide (materiale supplementare di «Developing updated and new guidance to promote reliable patient identification»)](https://pmc-oa-opendata.s3.amazonaws.com/PMC12772641.1/ooaf160_supplementary_data.docx) — Recommended Practice 1.2 (Strong), Implementation Guidance: nome completo, caratteri e spaziature, cognomi simili resi distinti · JAMIA Open (Oxford University Press), dal dataset Open Access di PubMed Central · 2026; letto il 12/10/2026
- [NISTIR 7804-1 — Technical Evaluation, Testing, and Validation of the Usability of Electronic Health Records: Empirically Based Use Cases for Validating Safety-Enhanced Usability and Guidelines for Standardization](https://nvlpubs.nist.gov/nistpubs/ir/2015/nist.ir.7804-1.pdf) — Linea guida 1 sull'identificazione del paziente (letta via WebSearch) · NIST · 2015; letto via WebSearch il 12/10/2026

### SAN-CONTESTO-GIUSTO · Si vede sempre per chi si sta scrivendo

**Regola.** Ogni contesto in cui si scrive dice di chi è:

- il titolo della scheda del browser nomina la persona e la pagina;
- il compositore dice a parole se si sta scrivendo un messaggio alla persona o una nota interna;
- i pannelli laterali, come quello delle Conversazioni, si aprono con nome ed età;
- prima di un'azione verso l'esterno (inviare, firmare, emettere) la conferma nomina la persona con il secondo identificativo.

Non si limita quante persone si tengono aperte insieme: si rende chiaro chi c'è in ciascuna.

**Perché.** L'articolo che presenta la revisione della SAFER Guide (JAMIA Open, 2026) riporta che uno studio del 2013 attribuiva la maggior parte degli ordini al paziente sbagliato alle interruzioni: passati a un'altra cartella per gestirle, i medici a volte restavano in quella sbagliata. Limitare le cartelle aperte però non aiuta: uno studio randomizzato e diversi studi quasi sperimentali non hanno trovato legami tra il numero di cartelle aperte e gli errori, e i limiti hanno creato rischi nuovi, come usare le credenziali di un collega o dare ordini a voce; per questo la revisione 2024 ha tolto la raccomandazione del 2016 di una sola cartella alla volta. Lo studio randomizzato (Adelman e altri, JAMA 2019, sintetizzato da AHRQ PSNet) ha coinvolto 3.356 clinici e quasi 4,5 milioni di sessioni d'ordine, senza differenze significative tra una e fino a quattro cartelle; un'analisi successiva ha però visto più errori quando si ordinava con più cartelle aperte. Quindi non si limita: si rende evidente, in ogni contesto, di chi è.

**Soglie ed eccezioni.** Titolo della scheda del browser: «`<persona>` · `<scheda>` · DottorCloud». I canali del compositore si distinguono per parola, non solo per icona.

**In DottorCloud.** Il titolo della scheda del browser lo scrive `router.afterEach` in `router.js` (il nome della pagina dal menu) e, per persona e trattativa, `usePageMeta` in `pages/Lead.vue`, `pages/Deal.vue` e nelle loro versioni per il telefono: oggi mettono solo il nome, e devono dire anche la scheda e il tipo («Noemi Carbone · Documenti», «Silvia Fontana · Trattativa»). L'intestazione nascosta per il lettore di schermo viene da `titoloDellaPagina` in `App.vue`; le pagine con un titolo proprio sono in `CON_UN_TITOLO` (`utils/menu.js`). Nel compositore (`Activities/ChannelSwitcher.vue`) la nota colora già di ambra tutto il riquadro, ma sul telefono i canali sono solo icone e l'email era il canale proposto: servono pillole con le parole «Email» e «Nota interna», «Visibile solo al centro» sulla nota e il verbo sul pulsante («Invia email», «Salva nota»). In Conversazioni la colonna accanto (`Conversations/ConversationAside.vue`, il riepilogo compatto di `Activities/SummaryArea.vue`) si apre con nome ed età.

**Come si verifica.** Aprire due persone in due schede del browser e controllare i titoli: axe `document-title` verifica che ci siano, il contenuto si controlla a mano. Scenario: interrompere una nota per passare a un'altra persona, poi tornare e verificare a chi va la nota. Sul telefono: scrivere una nota interna e verificare che non parta un'email.

**Errori da evitare.**

- Persona e trattativa con lo stesso titolo nella scheda del browser (studio UX, ottobre 2026).
- L'email come canale proposto, indicata solo da un'icona: una nota pensata come interna parte come email alla paziente (studio UX, ottobre 2026).
- Limitare a una sola scheda aperta «per sicurezza»: le prove non lo sostengono e spinge a stratagemmi.
- Sul telefono, con la scheda ripiegata, il nome che resta solo nelle briciole.

**Fonti.**

- [Developing updated and new guidance to promote reliable patient identification](https://pmc.ncbi.nlm.nih.gov/articles/PMC12772641/) — Discussion (interruzioni e ordini nella cartella sbagliata; raccomandazione sulle cartelle aperte tolta, con i suoi motivi); Table 2 (Deletion) · JAMIA Open, vol. 9, n. 1, ooaf160 (E. Weatherford e altri, tra cui D. F. Sittig, H. Singh, J. S. Adelman) · 2026; testo letto dal dataset Open Access di PubMed Central (PMC12772641.1) il 12/10/2026
- [Effect of restriction of the number of concurrently open records in an electronic health record on wrong-patient order errors: a randomized clinical trial (sintesi)](https://psnet.ahrq.gov/issue/effect-restriction-number-concurrently-open-records-electronic-health-record-wrong-patient) — Sintesi dello studio di Adelman e altri (JAMA 2019): 3.356 clinici, quasi 4,5 milioni di sessioni d'ordine, analisi post hoc (letto via WebSearch) · AHRQ PSNet · 2019; letto via WebSearch il 12/10/2026

### SAN-STAMPE · Ogni documento stampato o in PDF porta due identificativi

**Regola.** Referti, moduli firmati, preventivi, piani consegnati ed etichette portano su ogni pagina, sempre nello stesso punto, il nome completo, la data di nascita (o il codice fiscale dove il documento lo richiede) e la data del documento.

**Perché.** La SAFER Guide (revisione 2024, raccomandazione 1.4, forza «Strong») vuole che ciò che si stampa dalla cartella, come braccialetti, etichette e referti, porti più identificativi, perché la persona si possa verificare quando riceve il foglio: tutti i materiali stampati per un paziente riportano nome completo e data di nascita, insieme a un codice a barre. La stessa raccomandazione avverte che verificare l'identità solo confermando nome e data di nascita è soggetto a errore umano. Un PDF esce dall'app: lo leggono un altro medico, il paziente o un familiare, senza la testata dello schermo.

**Soglie ed eccezioni.** Due identificativi su ogni pagina, nell'intestazione o in un margine ripetuto. Il mezzo elettronico di verifica (codice a barre o QR) la SAFER Guide lo chiede per il ricovero; per un ambulatorio è un'opzione.

**In DottorCloud.** Oggi i tre modelli mettono solo il nome, in alto a destra della prima pagina: il referto (`crm/clinica/templates/referto.html`, `persona` = `lead_name` in `crm/clinica/referto.py`), il modulo firmato (`crm/moduli/templates/modulo_firmato.html`) e il preventivo (`crm/preventivi/templates/preventivo.html`). Il margine che si ripete su ogni pagina (`@page`, `@bottom-left`) porta solo il codice del documento: è il posto per «Noemi Carbone · nata il 2 giu 1961». Il PDF si genera una volta sola (PDF/A con impronta SHA-256): la modifica vale per i documenti nuovi e non si rigenerano mai quelli già firmati.

**Come si verifica.** Test di rendering dei modelli con una persona che ha la data di nascita e una che non ce l'ha. Su un PDF di più pagine, controllare il secondo identificativo su ogni pagina. Rivedere ogni modello in `crm/**/templates/` quando si aggiunge un nuovo documento.

**Errori da evitare.**

- Rigenerare un PDF firmato per aggiungere la data: cambiano l'impronta e la prova.
- Stampare il codice fiscale per intero ovunque «per sicurezza»: è un dato in più che esce (vedi PRIV-MINIMO-NEI-MODULI).
- Mettere l'identificativo solo sulla prima pagina, com'è oggi.

**Vedi anche.** [SAN-DUE-IDENTIFICATIVI](#san-due-identificativi--due-identificativi-in-ogni-scelta-e-in-ogni-risultato)

**Fonti.**

- [Appendix C. 2024 Patient Identification SAFER Guide (materiale supplementare di «Developing updated and new guidance to promote reliable patient identification»)](https://pmc-oa-opendata.s3.amazonaws.com/PMC12772641.1/ooaf160_supplementary_data.docx) — Recommended Practice 1.4 (Strong): testo, Rationale e Implementation Guidance · JAMIA Open (Oxford University Press), dal dataset Open Access di PubMed Central · 2026; letto il 12/10/2026
- [SAFER Guides — Patient Identification](https://healthit.gov/wp-content/uploads/2025/01/Safer-Guide-6.-Patient-Identification-Final.pdf) — La guida pubblicata (indirizzo confermato via WebSearch; il testo è letto nell'appendice C indicata sopra) · ONC/ASTP, U.S. Department of Health and Human Services · 2025; letto via WebSearch il 12/10/2026

### SAN-ACCOGLIENZA-VERIFICA · All'accoglienza l'identità si conferma attivamente

**Regola.** Quando una persona arriva o telefona, lo schermo aiuta a chiederle nome e data di nascita e a confrontarli con ciò che mostra, invece di portare a chiedere «È lei Maria Rossi?». L'azione «Presente» sta sulla riga che mostra i due identificativi. Una persona nuova si registra con la data di nascita. Se una ricerca per numero trova più persone, lo dice e chiede quale.

**Perché.** La Quick Safety 45 della Joint Commission (2018) raccomanda un processo di conferma attiva che faccia combaciare la persona con i suoi documenti e un unico processo standard di identificazione e registrazione, ovunque si registri. La SAFER Guide (revisione 2024) vuole una registrazione standard su un unico archivio, con la persona che conferma i propri dati quando torna (raccomandazione 2.1), e la conferma dell'identità con due identificativi, come nome e data di nascita, nei momenti chiave della cura, detta a voce dalla persona o da chi la rappresenta (2.3). L'articolo su JAMIA Open (2026) ricorda che alla registrazione un abbinamento sbagliato crea doppioni o mette la persona nella cartella di un'altra. Nel caso PSNet «New Patient Mistakenly Checked in as Another» l'errore nacque al banco: una receptionist nuova, un sistema appena installato e un omonimo della stessa età.

**In DottorCloud.** In Accoglienza (`pages/Today.vue`, `crm/api/oggi.py`) la riga di chi arriva deve leggersi «Maria Fontana · nata il 2 giu 1961 · 09:30 · Fisioterapia · Giulia Ferri», con l'azione «Presente» (`crm/scheduling/esiti.py`, `segna`) su quella riga: oggi il nome viene dopo la riga del servizio (`Today/ParticipantRow.vue`). Il «Sono qui» dell'area (`check_in` in `crm/area/api.py`) parte da una sessione già identificata; l'avviso che arriva alla segreteria (`ARRIVATO_DALL_AREA`) deve portare nome ed età. Al telefono la ricerca per numero confronta le ultime nove cifre (`crm/api/sul_telefono.py`) e può trovare più persone della stessa famiglia: l'elenco le mostra con l'età.

**Come si verifica.** Test di usabilità con la segreteria su uno scenario con un omonimo, contando quante volte viene segnata la persona sbagliata (il terzo passo del protocollo della NISTIR 7804: utenti rappresentativi su compiti critici). Test della ricerca per numero (`crm/tests/test_sul_telefono.py`) con due persone sullo stesso cellulare.

**Errori da evitare.**

- «Annulla l'esito» come unico pulsante della riga, al posto dell'azione principale: si legge come «annulla l'appuntamento» (studio UX, ottobre 2026).
- Una riga che mostra il servizio prima del nome (studio UX, ottobre 2026).
- Trattare un numero di famiglia come identificativo univoco quando si cerca chi sta chiamando.

**Vedi anche.** [SAN-DUE-IDENTIFICATIVI](#san-due-identificativi--due-identificativi-in-ogni-scelta-e-in-ogni-risultato)

**Fonti.**

- [Quick Safety Issue 45: People, processes, health IT and accurate patient identification](https://digitalassets.jointcommission.org/api/public/content/2dc4cad7bdc34451b85a2be5431f09ef?v=c9afdcd7) — Azioni raccomandate: conferma attiva; processo standard di identificazione e registrazione ovunque si registri (letto via WebSearch) · The Joint Commission · 2018; letto via WebSearch il 12/10/2026
- [Appendix C. 2024 Patient Identification SAFER Guide (materiale supplementare di «Developing updated and new guidance to promote reliable patient identification»)](https://pmc-oa-opendata.s3.amazonaws.com/PMC12772641.1/ooaf160_supplementary_data.docx) — Recommended Practice 2.1 (registrazione standard) e 2.3 (Rationale e Implementation Guidance) · JAMIA Open (Oxford University Press), dal dataset Open Access di PubMed Central · 2026; letto il 12/10/2026
- [Developing updated and new guidance to promote reliable patient identification](https://pmc.ncbi.nlm.nih.gov/articles/PMC12772641/) — Discussion (errori alla registrazione) · JAMIA Open, vol. 9, n. 1, ooaf160 (E. Weatherford e altri, tra cui D. F. Sittig, H. Singh, J. S. Adelman) · 2026; testo letto dal dataset Open Access di PubMed Central (PMC12772641.1) il 12/10/2026
- [New Patient Mistakenly Checked in as Another (WebM&M)](https://psnet.ahrq.gov/web-mm/new-patient-mistakenly-checked-another) — Il caso (letto via WebSearch; il commento non si è potuto leggere) · AHRQ PSNet · letto via WebSearch il 12/10/2026
- [NISTIR 7804 — Technical Evaluation, Testing and Validation of the Usability of Electronic Health Records](https://nvlpubs.nist.gov/nistpubs/ir/2012/NIST.IR.7804.pdf) — Protocollo EUP, terzo passo: test di validazione con utenti su compiti critici (letto via WebSearch) · NIST · 2012; letto via WebSearch il 12/10/2026

### SAN-CHI-AGISCE-PER-CHI · Si vede chi agisce per chi, e chi è assistito ha la sua scheda

**Regola.** Quando una persona prenota, paga, firma o legge per un'altra (genitore, tutore, familiare), ogni riga e ogni conferma dicono per chi è la cosa e chi agisce, con il suo ruolo («Prenotato da Anna Bianchi, madre»). La persona assistita ha sempre la sua scheda, mai quella di chi la accompagna. Nell'area, chi agisce per un'altra persona vede solo ciò che serve al suo ruolo.

**Perché.** Le Privacy Principles del W3C TAG (1.2.1 Guardians) ricordano che chi ha un tutore resta titolare delle decisioni sulla propria riservatezza e che il tutore ha il dovere di aiutarlo; le tecnologie del web non devono aggravare il rischio di un tutore che non agisce nel suo interesse, e i programmi utente possono dare informazioni sul pupillo al tutore solo per aiutarlo nelle sue responsabilità. La SAFER Guide (revisione 2024, raccomandazione 2.3) prevede che a confermare l'identità a voce sia il paziente o chi lo rappresenta, per esempio per un neonato. La Joint Commission ammette il telefono come identificativo, ma un numero di famiglia non distingue il genitore dal figlio.

**In DottorCloud.** `crm/persone/collegate.py` (`CRM Related Person`: chi paga, chi prenota, chi rappresenta) e `crm/persone/legami.py` sanno già chi agisce per chi, e `AppointmentPanel.vue` scrive «Booked by {0}». Lo stesso segno, con il ruolo, va esteso:

- alla fattura (chi paga);
- alla firma (`crm/preventivi/firma.py` registra già chi firma e in quale veste);
- all'area (`per_la_pagina_di_prenotazione` in `crm/area/api.py`: i propri dati, oppure quelli di un genitore con il nome del figlio).

Un nome senza ruolo sulla scheda di un paziente («Marco Fontana») diventa «di Marco Fontana (dentista)» o «scritto da Davide Marino».

**Come si verifica.** Test sul sito: un genitore prenota per il figlio da /prenota; verificare che nasca la scheda del figlio collegata al genitore e che agenda e fattura nominino entrambi. Test unitari di `legami.py` (`crm/persone/tests/test_legami.py`): relazioni inverse, età.

**Errori da evitare.**

- Usare la scheda del genitore perché email e telefono coincidono.
- Mostrare a chi accompagna dati sanitari dell'assistito che il suo ruolo non prevede.
- Nomi di professionisti o di chi paga senza ruolo sulla scheda di una paziente, che si possono scambiare per familiari (studio UX, ottobre 2026).

**Fonti.**

- [Privacy Principles (W3C TAG, Editor's Draft)](https://w3ctag.github.io/privacy-principles/#guardians) — 1.2.1 Guardians · W3C Technical Architecture Group · Editor's Draft del 24/11/2025, letto dal ramo gh-pages di w3ctag/privacy-principles su GitHub il 12/10/2026
- [Appendix C. 2024 Patient Identification SAFER Guide (materiale supplementare di «Developing updated and new guidance to promote reliable patient identification»)](https://pmc-oa-opendata.s3.amazonaws.com/PMC12772641.1/ooaf160_supplementary_data.docx) — Recommended Practice 2.3, Implementation Guidance (il paziente o chi lo rappresenta conferma a voce) · JAMIA Open (Oxford University Press), dal dataset Open Access di PubMed Central · 2026; letto il 12/10/2026
- [National Patient Safety Goals® Effective January 2026 for the Ambulatory Health Care Program](https://digitalassets.jointcommission.org/api/public/content/92c95c4e94304b2084e7e039d916719b?v=3c64fe83) — NPSG.01.01.01: il telefono tra gli identificativi ammessi (letto via WebSearch) · The Joint Commission · 2026; letto via WebSearch il 12/10/2026

### SAN-BOZZA-MAI-PERSA · Il lavoro interrotto non si perde

**Regola.** Ciò che si sta scrivendo su una persona (visita, appuntamento, fattura, messaggio, modulo) sopravvive a qualunque interruzione: il tasto Indietro, un cambio di pagina dalla barra, la chiusura della finestra, la scadenza della sessione, un nuovo accesso. Le bozze cliniche e amministrative stanno sul server e appartengono al loro autore. Chi lascia una schermata con modifiche non salvate se lo sente chiedere una volta sola. Dopo un nuovo accesso si riprende da dove si era rimasti.

**Perché.** WCAG 2.2, criterio 2.2.5 Re-authenticating (AAA): quando una sessione autenticata scade, l'utente può continuare l'attività senza perdere dati dopo essersi autenticato di nuovo. Criterio 2.2.6 Timeouts (AAA): gli utenti sono avvisati di quanto tempo di inattività può far perdere i dati, salvo che i dati si conservino per più di 20 ore; l'Understanding indica come soluzione migliore conservarli almeno 20 ore, e chiede di avvisare una volta all'inizio del compito, non a ogni passo. Interrompersi è normale al banco e in ambulatorio: l'articolo su JAMIA Open (2026) riporta che uno studio del 2013 attribuiva la maggior parte degli ordini al paziente sbagliato alle interruzioni.

**Soglie ed eccezioni.** La bozza resta per più di 20 ore (WCAG 2.2.6); altrimenti si dice all'inizio del compito quanto tempo di inattività la fa perdere. Uscendo si chiede una sola volta. Il salvataggio automatico non sposta il fuoco né la pagina.

**In DottorCloud.** Cosa funziona già:

- la visita è una bozza del suo autore salvata sul server (`crm/clinica/cartella.py`, `start_sheet`);
- il pannello dell'appuntamento chiede conferma prima di chiudersi con X, Esc o Indietro (`discardFirst`; `utils/indietro.js`, `chiudeConIndietro`) e, dopo lo studio, anche quando si cambia pagina dalla barra in basso del telefono (`onBeforeRouteLeave` in `AppointmentPanel.vue`; corretto);
- una fattura lasciata a metà si riprende: l'appuntamento con una bozza resta tra quelli da fatturare (`appointments_to_invoice` in `crm/invoicing/api.py`) e «Emetti la fattura» riapre quella bozza invece di farne una seconda (`fatturaDellIncontro` in `composables/fattura.js`; corretto).

Cosa manca: i messaggi in corso li tiene `composables/drafts.js` (`useDraft`) nel `localStorage` del browser, per utente e per scheda: non si perdono, ma restano sul PC condiviso (vedi PRIV-NULLA-NEL-BROWSER). Meglio una bozza sul server dell'utente, oppure cancellarli all'uscita.

**Come si verifica.** Scenario a mano a metà di una visita: premere Indietro su Android, toccare un'altra voce della barra, lasciar scadere la sessione (con una scadenza breve sul sito di prova) e rientrare. Ogni volta il testo deve esserci ancora. Un test E2E per `onBeforeRouteLeave`. Un test del server sulle regole che decidono cosa resta da fatturare, bozze comprese.

**Errori da evitare.**

- Due domande sovrapposte quando si preme Indietro (studio UX, ottobre 2026; corretto).
- Salvare una bozza che poi nessuna lista mostra: con «Emetti la fattura» la bozza usciva da tutte le liste e la prestazione restava senza fattura (studio UX, ottobre 2026, gravità 3; corretto).
- Tenere le bozze nel browser per non perderle e lasciarle a chi usa il PC dopo.
- Un salvataggio automatico che sposta il fuoco o la pagina mentre si scrive.

**Vedi anche.** [FORM-BOZZE](06-moduli.md#form-bozze--il-lavoro-interrotto-non-si-perde)

**Fonti.**

- [Web Content Accessibility Guidelines (WCAG) 2.2 — 2.2.5 Re-authenticating](https://www.w3.org/TR/WCAG22/#re-authenticating) — Criterio 2.2.5 (AAA) e Understanding, «Intent of Re-authenticating» · W3C · 2023 (Raccomandazione W3C); testo letto dal repository w3c/wcag su GitHub il 12/10/2026
- [Understanding SC 2.2.6 Timeouts](https://www.w3.org/WAI/WCAG22/Understanding/timeouts.html) — Testo del criterio (AAA) e «Intent»: conservare i dati almeno 20 ore, o avvisare all'inizio del compito · W3C · consultato il 12/10/2026 (sorgente nel repository w3c/wcag su GitHub)
- [Developing updated and new guidance to promote reliable patient identification](https://pmc.ncbi.nlm.nih.gov/articles/PMC12772641/) — Discussion (lo studio del 2013 sulle interruzioni) · JAMIA Open, vol. 9, n. 1, ooaf160 (E. Weatherford e altri, tra cui D. F. Sittig, H. Singh, J. S. Adelman) · 2026; testo letto dal dataset Open Access di PubMed Central (PMC12772641.1) il 12/10/2026

### SAN-SESSIONE-CONDIVISA · Sessioni adatte a un PC di segreteria condiviso

**Regola.** La sessione scade dopo un tempo di inattività proporzionato al rischio. Prima di scadere avvisa e offre il modo di prolungarla; dopo la scadenza, il nuovo accesso riporta al lavoro lasciato. L'uscita è sempre visibile in ogni pagina, e su un PC condiviso cambiare utente è rapido. Il tempo di scadenza scelto è scritto e motivato.

**Perché.** NIST SP 800-63B-4 (2025) è una linea guida scritta per i sistemi delle agenzie federali statunitensi, che OWASP ASVS prende come riferimento (7.1.1). Dice:

- sez. 2.2.3: al livello AAL2 il timeout complessivo DOVREBBE (SHOULD) essere al massimo di 24 ore e quello di inattività al massimo di 1 ora; se è scaduta solo l'inattività, si può rientrare con la sola password o la biometria insieme al segreto della sessione;
- sez. 5.1: le sessioni DOVREBBERO offrire un modo facile per uscire quando si è finito, che dà più controllo «in particolare se il dispositivo può essere accessibile ad altri»;
- sez. 5.2: la riautenticazione serve a confermare che l'utente non se ne sia andato senza uscire; prima della scadenza si può avvisare e lasciar riattivare la sessione.

OWASP ASVS 5.0.0 (maggio 2025) chiede di documentare il timeout di inattività e la durata massima, motivando gli scostamenti dal NIST (7.1.1), di applicarli entrambi (7.3.1 e 7.3.2) e un'uscita facile e visibile in ogni pagina autenticata (7.4.4). WCAG 2.2, criterio 2.2.1 (A): per ogni limite di tempo una delle soluzioni ammesse è avvisare prima della scadenza e dare almeno 20 secondi per prolungarlo con un'azione semplice, almeno dieci volte; il criterio non si applica se il limite supera le 20 ore.

**Soglie ed eccezioni.** Inattività al massimo 1 ora e sessione al massimo 24 ore: i valori che NIST SP 800-63B-4 raccomanda al livello AAL2; quelli di DottorCloud vanno decisi e scritti (ASVS 7.1.1). Avviso con almeno 20 secondi per prolungare (WCAG 2.2.1). Dopo la scadenza, ripresa senza perdita di dati (WCAG 2.2.5). Oggi il campo «Session Expiry (idle timeout)» di System Settings ha come predefinito 170:00 (170 ore); se è vuoto, il framework usa 240:00:00.

**In DottorCloud.** Frappe calcola la scadenza per inattività da `System Settings.session_expiry` (`get_expiry_period` in `frappe/sessions.py`): il campo ha come predefinito 170:00 e, vuoto, vale 240 ore. DottorCloud non lo imposta (nessun riferimento a `session_expiry` in `crm/`), quindi una sessione di segreteria resta viva da 7 a 10 giorni senza uso. Interventi:

- impostarla all'installazione e a ogni migrate, come `crm/telemetria.py` fa per la telemetria;
- mostrarla in Impostazioni › Il centro;
- avvisare nella pagina prima della scadenza, con un dialogo annunciato come `role=alertdialog`.

Già a posto: l'uscita è nel menu dell'account (`composables/vociAccount.js`, che `UserDropdown.vue` e, sul telefono, «Altro» disegnano); quando si passa il tablet al paziente, la sessione dell'operatore si chiude prima della consegna (`Moduli/SendFormsDialog.vue`, `call('logout')`).

**Come si verifica.** Sul sito di prova impostare una scadenza di 2 minuti, lasciare una visita a metà e aspettare l'avviso e poi la scadenza: al rientro il testo deve esserci ancora. Verificare l'annuncio con NVDA e con VoiceOver. Dopo ogni migrate controllare il valore con `frappe.get_system_settings('session_expiry')`.

**Errori da evitare.**

- Timeout brevi senza conservare il lavoro: la segreteria li aggira. NIST SP 800-63B-4 (sez. 5) nota che dover presentare di continuo le credenziali, per la sua scarsa usabilità, spinge a stratagemmi che annullano l'autenticazione; la revisione della SAFER Guide racconta che i limiti alle cartelle aperte portavano a usare le credenziali di un collega.
- Uscire senza ripulire il browser (vedi PRIV-NULLA-NEL-BROWSER).
- Un avviso di scadenza che compare solo come toast e svanisce.
- Dare all'area del paziente, su un telefono condiviso, la stessa scadenza della scrivania.

**Vedi anche.** [WCAG-2.2.1](03-wcag-utilizzabile-e-comprensibile.md#wcag-221--tempi-regolabili-toast-sessioni-codici-posti-tenuti-221-a), [WCAG-2.2.5](03-wcag-utilizzabile-e-comprensibile.md#wcag-225--dopo-un-nuovo-accesso-non-si-perde-nulla-225-aaa-obiettivo), [PRIV-BANCONE](#priv-bancone--lo-schermo-del-bancone-e-il-tablet-li-vedono-anche-i-pazienti)

**Fonti.**

- [NIST SP 800-63B-4 — Digital Identity Guidelines: Authentication and Authenticator Management](https://pages.nist.gov/800-63-4/sp800-63b.html#aal2reauth) — Sez. 2.2.3 Reauthentication (AAL2: complessivo al massimo 24 ore, inattività al massimo 1 ora) · NIST · 2025 (pagina del 26/08/2025), letta dal repository usnistgov/800-63-4 su GitHub il 12/10/2026
- [NIST SP 800-63B-4 — Digital Identity Guidelines: Authentication and Authenticator Management](https://pages.nist.gov/800-63-4/sp800-63b.html#bindings) — Sez. 5 Session Management (introduzione: usabilità e stratagemmi) e 5.1 Session Bindings (uscita facile, dispositivo accessibile ad altri) · NIST · 2025 (pagina del 26/08/2025), letta dal repository usnistgov/800-63-4 su GitHub il 12/10/2026
- [NIST SP 800-63B-4 — Digital Identity Guidelines: Authentication and Authenticator Management](https://pages.nist.gov/800-63-4/sp800-63b.html#sessionreauthn) — Sez. 5.2 Reauthentication · NIST · 2025 (pagina del 26/08/2025), letta dal repository usnistgov/800-63-4 su GitHub il 12/10/2026
- [OWASP ASVS 5.0.0 — V7 Session Management](https://github.com/OWASP/ASVS/blob/master/5.0/en/0x16-V7-Session-Management.md) — Requisiti 7.1.1, 7.3.1, 7.3.2, 7.4.4 (livello 2) · OWASP Foundation · 2025 (versione 5.0.0, maggio 2025); consultato il 12/10/2026
- [Web Content Accessibility Guidelines (WCAG) 2.2 — 2.2.1 Timing Adjustable](https://www.w3.org/TR/WCAG22/#timing-adjustable) — Criterio 2.2.1 (A): Turn off, Adjust, Extend (almeno 20 secondi, almeno dieci volte), eccezione delle 20 ore · W3C · 2023 (Raccomandazione W3C); testo letto dal repository w3c/wcag su GitHub il 12/10/2026
- [Developing updated and new guidance to promote reliable patient identification](https://pmc.ncbi.nlm.nih.gov/articles/PMC12772641/) — Discussion (stratagemmi dovuti ai limiti sulle cartelle aperte) · JAMIA Open, vol. 9, n. 1, ooaf160 (E. Weatherford e altri, tra cui D. F. Sittig, H. Singh, J. S. Adelman) · 2026; testo letto dal dataset Open Access di PubMed Central (PMC12772641.1) il 12/10/2026

### PRIV-MINIMO-IN-LISTE-E-COPIE · Liste, anteprime e copie portano il minimo

**Regola.** Una lista, l'anteprima di una conversazione, una dashboard, un calendario condiviso o una copia verso un servizio esterno mostrano solo ciò che serve per riconoscere e scegliere. Il dettaglio sanitario si vede aprendo la cosa, ed è visibile solo a chi è autorizzato a leggerlo. Ciò che esce da DottorCloud (calendari esterni, piattaforme, modelli di IA) porta il minimo indispensabile e mai le note cliniche.

**Perché.** Il GDPR vuole dati adeguati, pertinenti e limitati a quanto necessario per le finalità (art. 5, par. 1, lett. c, «minimizzazione») e, per impostazione predefinita, non accessibili a un numero indefinito di persone senza l'intervento dell'interessato (art. 25, par. 2); sono dati sanitari anche le informazioni raccolte nel registrarsi o nel ricevere prestazioni (considerando 35). Le Privacy Principles del W3C TAG chiedono di limitare i dati trasferiti a quelli necessari agli scopi degli utenti o conformi ai loro desideri e interessi (2.2.1) e di non presumere che una categoria di dati non sia sensibile (2.4). OWASP ASVS 5.0.0 chiede di restituire il minimo dei dati sensibili e di mascherarli nell'interfaccia, salvo quando l'utente li apre espressamente (14.2.6), e di non inviarli a parti non fidate (14.2.3). Apple HIG (Privacy, Best practices) dice di chiedere solo i dati che servono davvero.

**In DottorCloud.** Cosa funziona già: in agenda gli impegni dei colleghi arrivano solo come tempo occupato, «when, never what» (`engaged` in `crm.api.appointments.get_calendar`); le prime parole dei messaggi le vede nelle notifiche solo chi può leggere le conversazioni (`_anteprima` in `crm/notifiche/api.py`).

Cosa rivedere:

- la copia dell'appuntamento nel calendario del framework (`sync_event` in `crm/fcrm/doctype/crm_appointment/crm_appointment.py`, accesa per impostazione predefinita: `CRM Scheduling Settings.sync_to_event` = 1) mette nell'`Event` il titolo (servizio e persona) e le note (`description: self.notes`); l'Event è privato, ma da lì passa alla sincronizzazione con Google Calendar di ciascun utente che la usa. Le note non dovrebbero uscire, e il titolo può limitarsi al servizio o a «Appuntamento»;
- la lista Note mostra il testo delle note a chiunque possa leggerle: la segreteria e il manager su tutto il centro (`note.vedi` in `crm/permissions/catalogo.py`), e lì finiscono anche note cliniche (vedi PRIV-CLINICO-AL-SUO-POSTO).

**Come si verifica.** Rivedere le colonne predefinite delle liste (`get_list_fields` in `crm/api/doc.py`), i campi delle anteprime e i dati che escono verso l'esterno (Event, piattaforme, assistente). Test del server di `sync_event`: la descrizione non contiene le note.

**Errori da evitare.**

- Una colonna «Note» o «Diagnosi» tra quelle predefinite.
- Esportare l'agenda in un calendario personale con il nome del paziente e la prestazione.
- Una dashboard che mostra nomi di pazienti accanto a prestazioni sensibili a chi guarda solo i numeri.

**Vedi anche.** [IA-DATI-MINIMI](#ia-dati-minimi--al-modello-va-il-minimo-e-solo-con-il-consenso)

**Fonti.**

- [Regolamento (UE) 2016/679 (GDPR)](https://eur-lex.europa.eu/eli/reg/2016/679/oj) — Art. 5, par. 1, lett. c; art. 25, par. 2; considerando 35 (testo inglese della GU L 119 del 4/5/2016 letto dalla copia GDPRtEXT dell'ADAPT Centre su GitHub) · Unione europea (Gazzetta ufficiale) · 2016; consultato il 12/10/2026
- [Privacy Principles (W3C TAG, Editor's Draft)](https://w3ctag.github.io/privacy-principles/#data-minimization) — 2.2 Data Minimization, principio 2.2.1; 2.4 Sensitive Information · W3C Technical Architecture Group · Editor's Draft del 24/11/2025, letto dal ramo gh-pages di w3ctag/privacy-principles su GitHub il 12/10/2026
- [OWASP ASVS 5.0.0 — V14 Data Protection](https://github.com/OWASP/ASVS/blob/master/5.0/en/0x23-V14-Data-Protection.md) — Requisiti 14.2.3 e 14.2.6 · OWASP Foundation · 2025 (versione 5.0.0, maggio 2025); consultato il 12/10/2026
- [Human Interface Guidelines — Privacy](https://developer.apple.com/design/human-interface-guidelines/privacy#Best-practices) — Best practices: «Request access only to data that you actually need.» · Apple · consultato il 12/10/2026

### PRIV-NULLA-NEL-BROWSER · Nulla di personale resta nel browser

**Regola.** DottorCloud non lascia nel browser dati personali o sanitari oltre la durata della sessione:

- nessuna cache persistente (IndexedDB, localStorage) con dati di persone;
- bozze cancellate all'uscita oppure tenute sul server;
- risposte e file con dati sanitari serviti con `Cache-Control: no-store`;
- un'uscita che ripulisce i dati del sito (`Clear-Site-Data`) e toglie l'abbonamento alle notifiche;
- `autocomplete=off` sui campi che contengono dati di altre persone.

Dopo l'uscita, il tasto Indietro non mostra la pagina di prima.

**Perché.** OWASP ASVS 5.0.0 chiede: alla fine della sessione i dati autenticati si cancellano dal client, con l'aiuto dell'header Clear-Site-Data ma anche quando il server non risponde (14.3.1, livello 1); header anti-cache come Cache-Control: no-store (14.3.2, livello 2); niente dati sensibili in localStorage, sessionStorage, IndexedDB o cookie, salvo i token di sessione (14.3.3, livello 2). L'HTML Standard (Web storage › Sensitivity of data) chiede ai browser di trattare i dati salvati in modo persistente come potenzialmente sensibili: possono contenere email, appuntamenti, cartelle sanitarie o altri documenti riservati. Secondo MDN, Clear-Site-Data con «storage» svuota localStorage, sessionStorage e IndexedDB e annulla le registrazioni dei service worker; con «cache» svuota la cache e, a seconda del browser, la cache avanti/indietro; l'esempio di MDN è proprio la pagina di uscita. Chrome ammette nella cache avanti/indietro anche le pagine con Cache-Control: no-store, ma le toglie quando cambiano i cookie o altri metodi di autorizzazione, così chi è uscito non torna con Indietro a una pagina da autenticato. NIST SP 800-63B-4 (sez. 5.1) dice che i segreti della sessione DOVREBBERO essere cancellati dal dispositivo all'uscita e NON DOVREBBERO stare in luoghi insicuri come il Local Storage. MDN spiega che autocomplete=off impedisce al browser di salvare i valori per i completamenti e di tenerli nella cronologia della sessione. Il GDPR (art. 32, par. 1) chiede misure tecniche e organizzative adeguate al rischio, compresa la capacità di assicurare la riservatezza dei sistemi: su un PC condiviso, ripulire il browser è una di queste.

**Soglie ed eccezioni.** Dopo l'uscita, zero dati di persone in `keyval-store` (IndexedDB) e in localStorage. La risposta di uscita porta `Clear-Site-Data` con «cache» e «storage», oppure il client fa la pulizia equivalente.

**In DottorCloud.** frappe-ui salva in IndexedDB (`idb-keyval`, database `keyval-store`) ogni risorsa creata con `cache:` (`node_modules/frappe-ui/src/resources/local.ts`), e nessuna uscita la svuota: `stores/session.js` porta a `/login` senza alcun `deleteDatabase`. Oggi hanno `cache:` anche risorse con dati di persone:

- la linea del tempo (`Activities.vue`: `['activity', docname]`, `['whatsapp_messages', …]`, `['sms_messages', …]`);
- il riepilogo (`SummaryArea.vue`: `['person-summary', lead]`);
- gli appuntamenti della persona (`PersonHeader.vue`, `EventArea.vue`) e gli eventi del calendario (`composables/event.js`);
- le chiamate (`CallArea.vue`, `pages/CallLogs.vue`), il pannello del telefono (`composables/pannelloTelefono.js`) e il giro di chiamate (`pages/Dialer.vue`);
- le ricerche del `Link` (`Controls/Link.vue`) e il contatto di chi chiama (`TwilioCallUI.vue`).

In localStorage restano le bozze dei messaggi (`useDraft` in `composables/drafts.js`) e gli avvisi degli eventi (`eventNotificationAlerts` in `data/notifications.js`). Cosa fare:

- togliere `cache` da queste risorse, come lo studio ha già fatto per il profilo fiscale in `PersonHeader.vue`;
- ripulire all'uscita: `Clear-Site-Data` dal server, più `indexedDB.deleteDatabase('keyval-store')` e la cancellazione delle chiavi di `useDraft` nel client;
- all'uscita, chiamare `crm.notifiche.spinta.unsubscribe` per il browser in uso.

Già a posto: le risposte del framework hanno `Cache-Control: no-store` se un endpoint non dice altro (`NO_CACHE_HEADERS` in `frappe/app.py`), e un file archiviato si apre da un rimando `private, no-store` (`crm/archivio/archivio.py`). Da controllare: un file privato non ancora archiviato, servito dal framework dietro nginx (`send_private_file` con `X-Accel-Redirect`), porta `Cache-Control: private,max-age=3600,stale-while-revalidate=86400`. Le preferenze di vista (`crmAgenda`, `crmActivityChannel`) possono restare: non sono dati di persone.

**Come si verifica.** Test a mano su un PC condiviso: accedere, aprire una persona, uscire; poi in DevTools › Application controllare IndexedDB `keyval-store`, localStorage e la cache, e premere Indietro. Uno script di build che elenca le `createResource` con `cache:` su chiamate con dati di persone, confrontandole con una lista esplicita di eccezioni ammesse. Controllo degli header della risposta di uscita e del download di un referto appena creato.

**Errori da evitare.**

- Il profilo fiscale in IndexedDB, che mostrava a un collega senza permessi, sullo stesso PC, la data di nascita letta dall'utente precedente (studio UX, ottobre 2026; corretto).
- Dimenticare che `Clear-Site-Data` con «storage» toglie anche il service worker: all'uscita va bene, perché si vuole smettere di ricevere notifiche, ma va saputo.
- Le bozze dei messaggi in localStorage (`useDraft`) che sopravvivono all'uscita.
- Considerare la navigazione in incognito una soluzione: usare la propria sessione su un PC condiviso è la situazione normale.

**Fonti.**

- [OWASP ASVS 5.0.0 — V14 Data Protection](https://github.com/OWASP/ASVS/blob/master/5.0/en/0x23-V14-Data-Protection.md) — V14.3 Client-side Data Protection: requisiti 14.3.1, 14.3.2, 14.3.3 · OWASP Foundation · 2025 (versione 5.0.0, maggio 2025); consultato il 12/10/2026
- [HTML Standard — Web storage](https://html.spec.whatwg.org/multipage/webstorage.html) — Privacy › Sensitivity of data · WHATWG · Living Standard; sorgente whatwg/html letto il 12/10/2026
- [Clear-Site-Data header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Clear-Site-Data) — Directives: «cache», «storage»; Examples › Sign out of a website · MDN Web Docs (Mozilla) · consultato il 12/10/2026 (sorgente mdn/content su GitHub)
- [Cache-Control header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control#no-store) — Response directives › no-store · MDN Web Docs (Mozilla) · consultato il 12/10/2026 (sorgente mdn/content su GitHub)
- [Enabling bfcache for Cache-Control: no-store](https://developer.chrome.com/docs/web-platform/bfcache-ccns) — Uscita dalla bfcache quando cambiano i cookie o altri metodi di autorizzazione (letto via WebSearch) · Chrome for Developers (Google) · letto via WebSearch il 12/10/2026
- [Enabling BFCache for pages that set Cache-Control: no-store (explainer)](https://github.com/fergald/explainer-bfcache-ccns/blob/main/README.md) — Authorization › Secure cookies (cancellare il cookie di autorizzazione corrisponde di solito a un'uscita) · F. Daly, K. Baheux (Chromium) · consultato il 12/10/2026
- [NIST SP 800-63B-4 — Digital Identity Guidelines: Authentication and Authenticator Management](https://pages.nist.gov/800-63-4/sp800-63b.html#bindings) — Sez. 5.1 Session Bindings (segreti cancellati all'uscita; niente HTML5 Local Storage) · NIST · 2025 (pagina del 26/08/2025), letta dal repository usnistgov/800-63-4 su GitHub il 12/10/2026
- [How to turn off form autocompletion](https://developer.mozilla.org/en-US/docs/Web/Security/Practical_implementation_guides/Turning_off_form_autocompletion) — Disabling autocompletion (i due effetti di autocomplete=off) · MDN Web Docs (Mozilla) · consultato il 12/10/2026 (sorgente mdn/content su GitHub)
- [Regolamento (UE) 2016/679 (GDPR)](https://eur-lex.europa.eu/eli/reg/2016/679/oj) — Art. 32, par. 1, lett. b (testo inglese della GU L 119 del 4/5/2016 letto dalla copia GDPRtEXT dell'ADAPT Centre su GitHub) · Unione europea (Gazzetta ufficiale) · 2016; consultato il 12/10/2026

### PRIV-ANTEPRIMA-DI-CHI-GUARDA · L'anteprima dell'area mostra solo ciò che può leggere chi guarda

**Regola.** Quando il centro guarda l'area di una persona «come la vede lei», l'anteprima usa le stesse chiamate dell'area ma con i permessi di chi guarda. Ciò che chi guarda non può leggere resta al suo posto, vuoto e dichiarato. I dati sanitari letti finiscono nel registro degli accessi. L'anteprima non scrive, non invia, non prenota e non scarica nulla.

**Perché.** OWASP ASVS 5.0.0 (8.3.3, livello 3) chiede che l'accesso a un oggetto dipenda dai permessi del soggetto da cui parte la richiesta, non da quelli di un intermediario che agisce per lui; il requisito 8.2.2 chiede permessi espliciti sui singoli dati. Le Privacy Principles del W3C TAG (2.2.1) chiedono di trasferire solo i dati necessari agli scopi degli utenti.

**Soglie ed eccezioni.** L'anteprima resta legata alla sessione per 30 minuti (`MINUTI` in `crm/area/anteprima.py`).

**In DottorCloud.** `crm/area/anteprima.py` gestisce l'anteprima (`start`, `vede`, `filtra`), che apre dalla scheda chi apre le aree (`area.invita`) e legge la persona. Le chiamate di sola lettura passano `anche_in_anteprima=True` a `_mia` o `_utente`; tutte le altre rifiutano l'anteprima. `area/components/HiddenCard.vue` tiene il posto di ciò che non si legge («Qui {0} vede qualcosa che in DottorCloud tu non leggi»); il lato client è in `frontend/src/area/anteprima.js`. Ogni nuova chiamata dell'area che legge dati sanitari deve passare per `anteprima.filtra` e per il registro.

**Come si verifica.** Test del server (`crm/area/tests/test_anteprima.py`): in anteprima ogni chiamata che scrive risponde che si tratta di un'anteprima; un documento clinico che chi guarda non può leggere non compare. Test a mano dall'area di prova.

**Errori da evitare.**

- Un'anteprima che usa i permessi del paziente e mostra al centro più di quanto il centro possa leggere.
- Un pulsante dell'area che in anteprima sembra funzionare e non dice perché non fa nulla.
- Dimenticare `anche_in_anteprima` su una nuova chiamata di sola lettura (l'anteprima si rompe), oppure metterlo su una chiamata che scrive.

**Fonti.**

- [OWASP ASVS 5.0.0 — V8 Authorization](https://github.com/OWASP/ASVS/blob/master/5.0/en/0x17-V8-Authorization.md) — Requisiti 8.2.2 (livello 1) e 8.3.3 (livello 3) · OWASP Foundation · 2025 (versione 5.0.0, maggio 2025); consultato il 12/10/2026
- [Privacy Principles (W3C TAG, Editor's Draft)](https://w3ctag.github.io/privacy-principles/#data-minimization) — Principio 2.2.1 · W3C Technical Architecture Group · Editor's Draft del 24/11/2025, letto dal ramo gh-pages di w3ctag/privacy-principles su GitHub il 12/10/2026

### PRIV-CONSENSO-GRANULARE · Il consenso solo dove serve: per finalità, al momento giusto, ritirabile come si è dato

**Regola.** Per curare non si chiede un consenso: l'informativa si legge, non si «accetta». Dove la base è il consenso (marketing, dossier, assistente, recensioni, referti online), ogni finalità ha il suo, chiesto quando serve e spiegato in una frase. Le caselle partono vuote. Dare e ritirare un consenso richiedono lo stesso numero di gesti e lo stesso canale: se si dà online, si ritira online. Il registro conserva ogni risposta con chi, come e quando, e non si modifica.

**Perché.** Il GDPR permette il trattamento dei dati sanitari per diagnosi, assistenza o terapia da parte di professionisti soggetti al segreto (art. 9, par. 2, lett. h, e par. 3), e il Garante (chiarimenti del 7/3/2019, provvedimento n. 55) ha precisato che per le finalità di cura il consenso non serve, mentre per i trattamenti non strettamente necessari alla cura (per esempio app mediche di titolari autonomi, fidelizzazione, fascicolo sanitario elettronico) occorre un'altra base giuridica o il consenso; per il dossier sanitario il consenso resta richiesto dalle Linee guida del 2015. Dove la base è il consenso, il GDPR chiede di poterlo dimostrare (art. 7, par. 1), una richiesta distinta dal resto, comprensibile e in linguaggio semplice (par. 2), il diritto di revocarlo in ogni momento, sapendo prima che la revoca non tocca il trattamento già fatto, con «It shall be as easy to withdraw as to give consent» (par. 3), e la massima attenzione se un contratto o un servizio dipende da un consenso non necessario (par. 4). Il considerando 32 esclude silenzio, caselle preselezionate e inattività e chiede un consenso per ciascuna finalità; il 43 presume non libero un consenso che non permette scelte separate per trattamenti diversi. Le Linee guida EDPB 05/2020 (versione 1.1) vedono il consenso come una decisione reversibile, che non è libera se non si può rifiutare o ritirare senza pregiudizio. Le Privacy Principles del W3C TAG chiedono richieste fatte per capire cosa vuole la persona, non per ottenere più trattamenti possibili (2.12.1), nessuna interruzione per chiedere un consenso quando c'è un'alternativa (2.12.2), e che verificare, ritirare o opporsi sia facile quanto dare il consenso (2.12.3). Apple HIG (Privacy) chiede richieste il più possibile specifiche, fatte quando la persona usa la funzione che le serve.

**Soglie ed eccezioni.** La revoca usa lo stesso canale e non più passaggi del consenso. Le caselle non sono mai preselezionate.

**In DottorCloud.** Cosa funziona già:

- il registro distingue il consenso dalla presa visione dell'informativa (`CONSENSO` e `PRESA_VISIONE` in `crm/moduli/registro.py`; l'informativa è «Information, not a consent» in `crm/moduli/__init__.py`) e non modifica mai una risposta: ne aggiunge una nuova (`crm/moduli/consensi.py`);
- in /prenota la presa visione e il marketing sono due caselle separate che partono vuote (`crm/www/prenota.html`: `consent: false, marketing: false`);
- `ConsentsSection.vue` ritira un consenso con un gesto («A consent is withdrawn here as easily as it was recorded»);
- uno STOP via SMS toglie il consenso al marketing «By SMS» (`crm/telephony/sms.py`);
- `engine.enroll` salta chi non ha il consenso al marketing.

Cosa manca:

- l'area (`frontend/src/area`, `crm/area`) non ha una pagina dei consensi: chi ha dato il marketing con un tocco da /prenota o da un modulo può ritirarlo solo chiedendo al centro, o con STOP per gli SMS;
- le email delle automazioni (`step_send_email` in `crm/automation/engine.py`) partono senza un collegamento per ritirare il consenso, e l'account del servizio d'invio ha `send_unsubscribe_message: 0` (`crm/posta/servizio.py`);
- in /prenota la casella obbligatoria dice «Ho letto e accetto l'informativa sulla privacy» o, senza l'indirizzo dell'informativa, «Acconsento al trattamento dei miei dati per gestire la prenotazione» (`consentPlain`), mentre il server la registra come presa visione (`privacy_notice` in `_registra_consensi`, `crm/api/service_booking.py`): le parole devono essere quelle del registro, «Ho letto l'informativa…»;
- in Impostazioni › Consensi l'interruttore di un tipo di consenso salva subito senza dire cosa cambia (`ConsentsSettings.vue`; studio UX, ottobre 2026).

**Come si verifica.** Contare i gesti: dare il consenso al marketing da /prenota, poi ritirarlo dall'area; i numeri devono coincidere. Test del server: una risposta non si modifica, se ne aggiunge una nuova. Rivedere il testo di ogni consenso e di ogni presa visione: una frase, la finalità, chi tratta.

**Errori da evitare.**

- Una casella unica «Accetto privacy e marketing».
- Chiedere un consenso per ciò che serve a curare o a gestire la prenotazione, o presentare come consenso la lettura dell'informativa.
- Un consenso dato online e ritirabile solo per telefono o di persona.
- Un interruttore del centro che spegne un tipo di consenso senza dire cosa vedranno le persone (studio UX, ottobre 2026).
- Il consenso al marketing come condizione per prenotare (art. 7, par. 4).

**Vedi anche.** [FORM-CONSENSI](06-moduli.md#form-consensi--un-consenso-si-dà-non-si-trova-già-dato), [NORM-GDPR-CHIARO](07-lingua-e-norme.md#norm-gdpr-chiaro--informative-e-consensi-in-linguaggio-semplice-e-chiaro)

**Fonti.**

- [Regolamento (UE) 2016/679 (GDPR)](https://eur-lex.europa.eu/eli/reg/2016/679/oj) — Art. 7, par. 1–4; art. 9, par. 2 lett. h, e par. 3; considerando 32 e 43 (testo inglese della GU L 119 del 4/5/2016 letto dalla copia GDPRtEXT dell'ADAPT Centre su GitHub) · Unione europea (Gazzetta ufficiale) · 2016; consultato il 12/10/2026
- [Chiarimenti sull'applicazione della disciplina per il trattamento dei dati relativi alla salute in ambito sanitario - 7 marzo 2019 \[doc. web n. 9091942\]](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/9091942) — Consenso non necessario per le finalità di cura; trattamenti non strettamente necessari (app mediche, fidelizzazione, FSE); dossier (letto via WebSearch, da estratti e sintesi) · Garante per la protezione dei dati personali (provvedimento n. 55) · 2019; letto via WebSearch il 12/10/2026
- [Guidelines 05/2020 on consent under Regulation 2016/679 (versione 1.1)](https://www.edpb.europa.eu/system/files/documents/files/file1/edpb_guidelines_202005_consent_en.pdf) — Revoca: il consenso è una decisione reversibile; consenso non libero se non si può rifiutare o ritirare senza pregiudizio (letto via WebSearch) · Comitato europeo per la protezione dei dati (EDPB) · 2020 (adottate il 4/5/2020); letto via WebSearch il 12/10/2026
- [Privacy Principles (W3C TAG, Editor's Draft)](https://w3ctag.github.io/privacy-principles/#consent-principles) — 2.12 Consent, Withdrawal of Consent, Opt-Outs, and Objections: principi 2.12.1, 2.12.2, 2.12.3 · W3C Technical Architecture Group · Editor's Draft del 24/11/2025, letto dal ramo gh-pages di w3ctag/privacy-principles su GitHub il 12/10/2026
- [Human Interface Guidelines — Privacy](https://developer.apple.com/design/human-interface-guidelines/privacy#Requesting-permission) — Best practices (richieste il più possibile specifiche) e Requesting permission (quando la persona usa la funzione) · Apple · consultato il 12/10/2026

### PRIV-NIENTE-INGANNI · Scelte sulla privacy senza trucchi

**Regola.** Nelle scelte sui dati (consensi, tracciamento, notifiche, condivisione, assistente) le alternative hanno lo stesso peso visivo e la stessa distanza. L'impostazione predefinita è quella che protegge. Un'opzione che protegge non sta in fondo alla pagina mentre quella rischiosa sta in alto. Le parole sono quelle di chi legge, non codice né gergo.

**Perché.** Le Privacy Principles del W3C TAG (1.1 Individual Autonomy) chiamano deceptive patterns (o dark patterns) le interazioni che riducono l'autonomia delle persone, anche quando non sono intenzionali; chi costruisce qualcosa che incide sull'autonomia deve farlo controllare da revisori con prospettive indipendenti, e l'autonomia cresce con impostazioni predefinite appropriate e protettive e con scelte facili da capire. Il principio 2.12.1 chiede di formulare la richiesta di consenso per capire cosa vuole la persona, non per ottenere più trattamenti possibili. Le Linee guida EDPB 03/2022 (versione 2.0, adottata il 14/2/2023) raccolgono i trucchi in sei categorie: Overloading, Skipping, Stirring, Obstructing, Fickle e Left in the dark; sono scritte per le interfacce delle piattaforme social, quindi per DottorCloud valgono come catalogo dei trucchi da evitare, non come obbligo specifico. Apple HIG (Privacy) chiede di essere trasparenti su come si raccolgono e si usano i dati.

**In DottorCloud.** In Impostazioni › Tracciamento (`TrackingSettings.vue`) «Traccia i visitatori anonimi» sta in alto ed è acceso (`track_anonymous` = 1 in `CRM Tracking Settings`), mentre «Richiedi il consenso» sta in fondo, spento (`require_consent` = 0), con una descrizione in codice («Collect nothing until your cookie banner calls CRMTracker.consent(true).»). Va portato accanto, descritto a parole e acceso per impostazione predefinita (studio UX, ottobre 2026). Nell'area una scelta sui dati ha il sì e il no con lo stesso aspetto: nelle risposte a un preventivo (`QuoteAnswer.vue`) i due pulsanti stanno affiancati con la stessa larghezza e «Accept and sign» è pieno mentre «I do not accept» no, il che va bene per l'azione principale di un preventivo ma non per un consenso. Nessun conto alla rovescia e nessuna frase colpevolizzante per chi rifiuta.

**Come si verifica.** Far rivedere ogni schermata con una scelta sui dati da due persone, di cui una esterna al progetto: peso dei pulsanti, ordine, impostazione predefinita, parole. Test di usabilità: la persona sa cosa ha scelto?

**Errori da evitare.**

- «Accetta» come pulsante pieno e «Rifiuta» come collegamento grigio.
- Richiedere di nuovo il consenso a ogni accesso dopo un no.
- Gergo tecnico al posto della conseguenza, come «CRMTracker.consent(true)».

**Vedi anche.** [UX-BIAS](04-aspetto.md#ux-bias--bias-cognitivi-predefiniti-e-ordine-orientano-le-scelte)

**Fonti.**

- [Privacy Principles (W3C TAG, Editor's Draft)](https://w3ctag.github.io/privacy-principles/#autonomy) — 1.1 Individual Autonomy (deceptive patterns, revisori indipendenti, impostazioni predefinite protettive); principio 2.12.1 · W3C Technical Architecture Group · Editor's Draft del 24/11/2025, letto dal ramo gh-pages di w3ctag/privacy-principles su GitHub il 12/10/2026
- [Guidelines 03/2022 on deceptive design patterns in social media platform interfaces: how to recognise and avoid them (versione 2.0)](https://www.edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-032022-deceptive-design-patterns-social-media_en) — Le sei categorie e l'ambito (interfacce delle piattaforme social) (letto via WebSearch) · Comitato europeo per la protezione dei dati (EDPB) · 2023 (versione 2.0 adottata il 14/2/2023); letto via WebSearch il 12/10/2026
- [Human Interface Guidelines — Privacy](https://developer.apple.com/design/human-interface-guidelines/privacy#Best-practices) — Best practices: «Be transparent about how your app collects and uses people's data.» · Apple · consultato il 12/10/2026

### PRIV-PREDEFINITO-PROTETTIVO · Ciò che fa uscire o mostrare dati parte spento

**Regola.** Ogni funzione che manda dati fuori da DottorCloud, li mostra a più persone o li tiene più a lungo parte spenta, oppure nella forma che espone meno: il centro la accende sapendo cosa cambia. Vale per le copie verso calendari e servizi esterni, il tracciamento dei visitatori, le anteprime nelle notifiche, gli avvisi automatici ai pazienti, l'assistente. Il predefinito si sceglie pensando a chi non aprirà mai quella pagina delle impostazioni.

**Perché.** Il GDPR (art. 25, par. 2) chiede al titolare del trattamento misure tecniche e organizzative perché, per impostazione predefinita, siano trattati solo i dati necessari a ciascuna finalità: l'obbligo vale per la quantità dei dati raccolti, la portata del trattamento, il periodo di conservazione e l'accessibilità, e i dati non devono essere resi accessibili a un numero indefinito di persone senza l'intervento dell'interessato. L'obbligo è del titolare, cioè del centro; il considerando 78 incoraggia chi produce applicazioni a tenere conto della protezione dei dati fin dalla progettazione, perché i titolari possano rispettare i loro obblighi. Le Privacy Principles del W3C TAG (1.1) osservano che l'autonomia delle persone cresce con impostazioni predefinite appropriate e protettive.

**In DottorCloud.** Già spenti all'inizio: i promemoria degli appuntamenti (`CRM Reminder Settings.enabled`), l'email per i documenti nuovi nell'area (`CRM Area Settings.email_new_documents`), l'SMS a chi ha chiamato senza risposta (`CRM Answering Settings.sms_to_missed_callers`), l'assistente (`CRM Assistant Settings.enabled`), i solleciti di pagamento (`CRM Payment Reminder Settings.enabled`) e le ricette delle automazioni. Da rivedere:

- la copia degli appuntamenti nel calendario del framework, con le note, è accesa (`CRM Scheduling Settings.sync_to_event` = 1; vedi PRIV-MINIMO-IN-LISTE-E-COPIE);
- il tracciamento dei visitatori anonimi è acceso e il consenso è spento (`CRM Tracking Settings`: `track_anonymous` = 1, `require_consent` = 0; vedi PRIV-NIENTE-INGANNI);
- le notifiche push portano tutti i gruppi finché la persona non ne spegne qualcuno, con le prime parole dei messaggi (vedi PRIV-NOTIFICHE-SENZA-SALUTE);
- le note interne le legge tutta la segreteria del centro (`note.vedi` con ambito `CENTRO`).

**Come si verifica.** Un test che legge i predefiniti dei DocType singoli (`crm/**/doctype/*/*.json`) e fallisce se una funzione dell'elenco che espone dati parte accesa senza una motivazione scritta. A ogni nuova impostazione, una domanda nella revisione: chi non la tocca mai, che cosa espone?

**Errori da evitare.**

- Accendere un'opzione per comodità della demo e lasciare così il predefinito.
- Spiegare l'opzione solo con il nome tecnico del campo: il centro, che è il titolare, deve capire cosa sceglie.

**Vedi anche.** [FORM-PREDEFINITI](06-moduli.md#form-predefiniti--nessuna-risposta-data-per-scontata)

**Fonti.**

- [Regolamento (UE) 2016/679 (GDPR)](https://eur-lex.europa.eu/eli/reg/2016/679/oj) — Art. 25, par. 2; considerando 78 (testo inglese della GU L 119 del 4/5/2016 letto dalla copia GDPRtEXT dell'ADAPT Centre su GitHub) · Unione europea (Gazzetta ufficiale) · 2016; consultato il 12/10/2026
- [Privacy Principles (W3C TAG, Editor's Draft)](https://w3ctag.github.io/privacy-principles/#autonomy) — 1.1 Individual Autonomy (impostazioni predefinite appropriate e protettive) · W3C Technical Architecture Group · Editor's Draft del 24/11/2025, letto dal ramo gh-pages di w3ctag/privacy-principles su GitHub il 12/10/2026

### PRIV-MINIMO-NEI-MODULI · Chiedere solo ciò che serve, compreso ciò che serve alla sicurezza

**Regola.** Ogni modulo (nuova persona, prenotazione, modulo del sito, area) chiede solo i dati necessari al suo scopo. Tra questi ci sono quelli che servono a riconoscere la persona con sicurezza, come la data di nascita. I campi da vendita tra aziende (fatturato, dipendenti, settore) non compaiono dove si registra un paziente.

**Perché.** Il GDPR vuole dati adeguati, pertinenti e limitati a quanto necessario per le finalità (art. 5, par. 1, lett. c). Le Privacy Principles del W3C TAG (2.2.1) chiedono di limitare i dati a ciò che serve agli scopi degli utenti; Apple HIG (Privacy, Best practices) dice di chiedere solo i dati che servono davvero: chiederne di più, o chiederli prima che la persona mostri interesse, rende difficile fidarsi. Necessario non vuol dire poco: per curare la persona giusta la data di nascita serve. La SAFER Guide (revisione 2024, raccomandazione 2.1) chiede a ogni organizzazione di stabilire l'insieme minimo di dati anagrafici per identificare in modo affidabile il paziente (per esempio nome, cognome, data di nascita, sesso, indirizzi e numeri di telefono), e la Joint Commission porta nome e data di nascita come esempio dei due identificativi.

**In DottorCloud.** `LEAD_QUICK_ENTRY` (`crm/install.py`) chiede nome, cognome, cellulare, email, genere, titolo, azienda e responsabile, ma non la data di nascita. `DEAL_QUICK_ENTRY` si apre su dieci campi aziendali (studio UX, ottobre 2026, gravità 3). Con la clinica accesa il modulo della persona dovrebbe chiedere nome, cognome, data di nascita (o il codice fiscale da cui ricavarla), cellulare ed email, con l'azienda dietro «Aggiungi dati dell'azienda». /prenota chiede il telefono solo dove il servizio lo vuole (`require_phone`, acceso se il servizio non dice altro). All'assistente va solo ciò che gli serve (vedi IA-DATI-MINIMI).

**Come si verifica.** Per ogni modulo, una tabella che associa ogni campo al suo scopo: un campo senza scopo si toglie. A ogni rilascio, rivedere i layout spediti in `crm/install.py`.

**Errori da evitare.**

- Togliere la data di nascita «per minimizzare»: serve a identificare la persona.
- Chiedere il codice fiscale a chi prenota una prova gratuita.
- Campi facoltativi che sembrano obbligatori.

**Vedi anche.** [FORM-NECESSARIO](06-moduli.md#form-necessario--chiedere-solo-ciò-che-serve-sapendo-perché)

**Fonti.**

- [Regolamento (UE) 2016/679 (GDPR)](https://eur-lex.europa.eu/eli/reg/2016/679/oj) — Art. 5, par. 1, lett. c (testo inglese della GU L 119 del 4/5/2016 letto dalla copia GDPRtEXT dell'ADAPT Centre su GitHub) · Unione europea (Gazzetta ufficiale) · 2016; consultato il 12/10/2026
- [Privacy Principles (W3C TAG, Editor's Draft)](https://w3ctag.github.io/privacy-principles/#data-minimization) — 2.2 Data Minimization, principio 2.2.1 · W3C Technical Architecture Group · Editor's Draft del 24/11/2025, letto dal ramo gh-pages di w3ctag/privacy-principles su GitHub il 12/10/2026
- [Human Interface Guidelines — Privacy](https://developer.apple.com/design/human-interface-guidelines/privacy#Best-practices) — Best practices: «Request access only to data that you actually need.» · Apple · consultato il 12/10/2026
- [Appendix C. 2024 Patient Identification SAFER Guide (materiale supplementare di «Developing updated and new guidance to promote reliable patient identification»)](https://pmc-oa-opendata.s3.amazonaws.com/PMC12772641.1/ooaf160_supplementary_data.docx) — Recommended Practice 2.1, Implementation Guidance (insieme minimo di dati anagrafici) · JAMIA Open (Oxford University Press), dal dataset Open Access di PubMed Central · 2026; letto il 12/10/2026
- [2026 Ambulatory Health Care National Patient Safety Goals (versione di facile lettura)](https://digitalassets.jointcommission.org/api/public/content/3103ce682c16469a8d8d5425e9082df9?v=1912053f) — Obiettivo 1 (nome e data di nascita come esempio) (letto via WebSearch) · The Joint Commission · 2026; letto via WebSearch il 12/10/2026

### PRIV-BANCONE · Lo schermo del bancone e il tablet li vedono anche i pazienti

**Regola.** Sulle schermate usate davanti ai pazienti (Accoglienza, agenda del giorno, tablet consegnato per i moduli) ciò che non serve al gesto in corso resta chiuso. Servizi e note si aprono solo a richiesta. Sul tablet consegnato non compaiono dati di altri pazienti, e chi lo consegna esce prima dalla propria sessione. Nessuno schermo pubblico chiama le persone per nome.

**Perché.** Il Garante (provvedimento del 9 novembre 2005 sul rispetto della dignità nelle strutture sanitarie) chiede, nelle sale d'attesa, un ordine di chiamata che non usi il nome della persona, per esempio un codice numerico o alfanumerico dato alla prenotazione o all'accettazione, salvo nei colloqui con il personale, e distanze di cortesia allo sportello e quando si raccolgono informazioni sulla salute. OWASP ASVS 5.0.0 (14.2.6) chiede di mascherare nell'interfaccia i dati sensibili, salvo quando l'utente li apre espressamente. Le Privacy Principles del W3C TAG (2.4) ricordano che la sensibilità dipende dal contesto; Apple HIG (Notifications) ricorda che non si può prevedere chi c'è accanto quando un'informazione compare sullo schermo.

**In DottorCloud.** Il tablet consegnato (`Moduli/SendFormsDialog.vue`) chiude la sessione dell'operatore prima di mostrare la pagina del paziente (`call('logout')`, poi `handed.url`): va mantenuto così. In Accoglienza (`pages/Today.vue`) la riga mostra ora, servizio, professionista e nome. Per i banconi visibili ai pazienti va valutata una vista «riservata», con l'iniziale del cognome e il servizio indicato per categoria, e nessun testo di nota a schermo intero. DottorCloud non ha schermi per la sala d'attesa: se ne avrà, chiameranno con un codice, non con il nome.

**Come si verifica.** Sopralluogo, o una foto del bancone, in un centro pilota: cosa si legge a un metro di distanza? Test del tablet: dopo la consegna, nessuna pagina dell'operatore si raggiunge con Indietro.

**Errori da evitare.**

- Tenere aperta la cartella di una persona mentre si accoglie un altro paziente.
- Una notifica push con il testo di un messaggio che compare sullo schermo del bancone (vedi PRIV-NOTIFICHE-SENZA-SALUTE).
- Un tablet consegnato con un browser che ricorda le ricerche dell'operatore.

**Vedi anche.** [SAN-SESSIONE-CONDIVISA](#san-sessione-condivisa--sessioni-adatte-a-un-pc-di-segreteria-condiviso)

**Fonti.**

- [Strutture sanitarie: rispetto della dignità - 9 novembre 2005 \[doc. web n. 1191411\]](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/1191411) — Chiamata in sala d'attesa senza il nome (codice numerico o alfanumerico); distanze di cortesia (letto via WebSearch, da copie del testo) · Garante per la protezione dei dati personali · 2005; letto via WebSearch il 12/10/2026
- [OWASP ASVS 5.0.0 — V14 Data Protection](https://github.com/OWASP/ASVS/blob/master/5.0/en/0x23-V14-Data-Protection.md) — Requisito 14.2.6 (mascherare nell'interfaccia salvo apertura espressa) · OWASP Foundation · 2025 (versione 5.0.0, maggio 2025); consultato il 12/10/2026
- [Privacy Principles (W3C TAG, Editor's Draft)](https://w3ctag.github.io/privacy-principles/#hl-sensitive-information) — 2.4 Sensitive Information · W3C Technical Architecture Group · Editor's Draft del 24/11/2025, letto dal ramo gh-pages di w3ctag/privacy-principles su GitHub il 12/10/2026
- [Human Interface Guidelines — Notifications](https://developer.apple.com/design/human-interface-guidelines/notifications#Best-practices) — Best practices (informazioni che altri possono vedere) · Apple · consultato il 12/10/2026

### IA-REVISIONE-UMANA · L'assistente scrive bozze, la persona decide

**Regola.** Ogni testo dell'assistente è una bozza: non si salva da solo, e la persona la accetta, la modifica o la scarta. Il professionista la rivede prima che entri nella cartella o arrivi al paziente. Dove manca un'informazione, la bozza lascia uno spazio «[da completare]» invece di inventare. Una volta accettata, porta il segno «Bozza IA, verificata da … il …», e il registro conserva chi ha fatto cosa.

**Perché.** Apple HIG (Generative AI) dà quattro indicazioni: tenere le persone al controllo, lasciando scartare, annullare o riprovare, e indicare chiaramente quando e dove si usa l'IA (Best practices); dire che i contenuti generati possono contenere errori, non usarli dove un'allucinazione può disinformare e fare danno, chiedere conferma prima di un'azione importante fatta per conto di qualcuno (Inputs); rendere facile correggere o annullare (Outputs). OWASP Top 10 for LLM Applications 2025, voce LLM09 Misinformation, descrive il rischio di fidarsi troppo e propone verifica incrociata e supervisione umana, comunicazione dei rischi e interfacce che etichettano i contenuti generati; il suo scenario 2 è un chatbot per diagnosi senza accuratezza sufficiente, che fa danno ai pazienti. In Italia la L. 132/2025 (art. 7, comma 5) dice che in sanità i sistemi di IA sono un supporto a prevenzione, diagnosi, cura e scelta terapeutica e che la decisione resta sempre ai medici.

**In DottorCloud.** Dove sta nel codice:

- `crm/assistente/regole.py`: `SCOPO` («Documentation support: the professional reviews every draft.»), `SEGNO` («AI draft, checked by {0} on {1}»), `differenza`, `quanto_cambiata`;
- `crm/assistente/modello.py`: `chiedi` scrive un `CRM AI Event` comunque vada; `accetta` e `scarta`; il registro tiene modello, fornitore, regione, impronte, la bozza e quanto il testo finale se ne è allontanato;
- `crm/clinica/assistente.py`: lavora solo dalla nota firmata e dalle risposte della scheda, lascia spazi tra parentesi quadre e non aggiunge diagnosi, consigli, farmaci, dosi, esami o date che la nota non contiene; `keep_draft` salva la bozza come nota da firmare, con il segno;
- `Clinic/AssistantDraftDialog.vue`; `DictationDialog.vue`, dove farmaci, allergie e dosi si spuntano uno per uno; `SummaryDialog.vue`, un riepilogo che cita le fonti numerate e non si conserva.

**Come si verifica.** Test unitari di `crm/assistente/regole.py` (`crm/assistente/tests/test_regole.py`: segno, differenza). Test del server: nessun testo dell'assistente viene salvato senza `accetta`. Rivedere che ogni bozza mostri lo stato «Bozza» finché non viene accettata. Test di usabilità: i professionisti leggono e correggono davvero? Misurare `quanto_cambiata`.

**Errori da evitare.**

- Un pulsante «Inserisci» che salva direttamente nella cartella.
- Una bozza senza segno che, una volta incollata, non si distingue dal testo del medico.
- Spuntare in un colpo solo tutti i farmaci dettati.

**Vedi anche.** [SAN-COPIA-CON-PROVENIENZA](../../verticali/clinica/principi-sanitari.md#san-copia-con-provenienza--ciò-che-si-copia-dice-da-dove-viene)

**Fonti.**

- [Human Interface Guidelines — Generative AI](https://developer.apple.com/design/human-interface-guidelines/generative-ai) — Best practices («Keep people in control»), Inputs (allucinazioni, conferma prima di azioni importanti), Outputs (correggere o annullare) · Apple · pagina aggiornata l'8/6/2026; consultata il 12/10/2026
- [LLM09:2025 Misinformation — OWASP Top 10 for LLM Applications](https://github.com/OWASP/www-project-top-10-for-large-language-model-applications/blob/main/2_0_vulns/LLM09_Misinformation.md) — Description (overreliance); Prevention and Mitigation Strategies 3, 5, 7; Example Attack Scenarios, Scenario #2 · OWASP GenAI Security Project · 2025; consultato il 12/10/2026
- [Legge 23 settembre 2025, n. 132 — Disposizioni e deleghe al Governo in materia di intelligenza artificiale](https://www.normattiva.it/eli/id/2025/09/25/25G00143/CONSOLIDATED) — Art. 7, comma 5 (letto via WebSearch); GU n. 223 del 25/9/2025, in vigore dal 10/10/2025 · Repubblica italiana (Normattiva) · 2025; letto via WebSearch il 12/10/2026

### IA-TRASPARENZA · Si dice sempre dove c'è l'intelligenza artificiale

**Regola.** Chiunque legga o riceva qualcosa fatto dall'assistente lo sa. La chat dell'area dice, sopra la conversazione e in ogni risposta, che risponde un'intelligenza artificiale e non una persona. Le bozze lo dicono finché non sono rivedute, e dopo portano il segno. Le impostazioni dicono a cosa serve l'assistente, dove gira il modello e cosa riceve.

**Perché.** L'AI Act (Regolamento (UE) 2024/1689), all'art. 50, par. 1, chiede al fornitore di un sistema di IA destinato a interagire direttamente con le persone di progettarlo in modo che le persone sappiano di interagire con un'IA, salvo che sia evidente per una persona ragionevolmente informata, attenta e avveduta. Il par. 2 chiede al fornitore di un sistema che genera testo, audio, immagini o video sintetici di marcarne i risultati in un formato leggibile da una macchina e rilevabile come generato dall'IA, salvo le funzioni di assistenza all'editing standard o che non alterano in modo sostanziale i dati in ingresso. Il par. 5 vuole l'informazione chiara e distinguibile al più tardi alla prima interazione, conforme ai requisiti di accessibilità. L'art. 50 si applica dal 2 agosto 2026 (art. 113); il Regolamento (UE) 2026/1744, pubblicato il 24 luglio 2026, dà fino al 2 dicembre 2026 ai sistemi immessi sul mercato prima del 2 agosto 2026 per il par. 2 (nuovo art. 111, par. 4). Fornitore è chi sviluppa il sistema e lo mette in servizio con il proprio nome (art. 3, punto 3): per l'assistente di DottorCloud è NPM2; il centro che lo usa è il deployer (punto 4). In Italia la L. 132/2025 (art. 7, comma 3) dà all'interessato il diritto di essere informato sull'impiego di tecnologie di IA in sanità. Apple HIG (Generative AI, Transparency) chiede di dire dove l'app usa l'IA, di non far mai credere a qualcuno di parlare con una persona o di leggere un testo scritto da una persona quando è l'IA, di adeguare il modo di dirlo alle norme dei paesi in cui l'app è offerta e di chiarire cosa la funzione può e non può fare. OWASP LLM09 chiede di etichettare chiaramente i contenuti generati e di dire i limiti di affidabilità e di campo d'uso.

**Soglie ed eccezioni.** L'informazione arriva al più tardi alla prima interazione (art. 50, par. 5) e, nella chat, in ogni risposta.

**In DottorCloud.** La chat dell'area lo dice già: `crm/area/chat.py` («You are the virtual assistant of {centro}: an AI, not a person») e `frontend/src/area/it.js` («Questo è l'assistente virtuale del centro, un'intelligenza artificiale, non una persona…», «Risposta dell'intelligenza artificiale»). Impostazioni › Assistente (`AssistantSettings.vue`) mostra la frase che ne dichiara lo scopo. Le istruzioni per il paziente generate dall'assistente e pubblicate nella bacheca dell'area portano lo stesso segno della nota (`keep_draft` in `crm/clinica/assistente.py`). Il segno è leggibile da una persona; se serva anche una marcatura leggibile da una macchina (art. 50, par. 2) o se valga l'eccezione per l'editing standard va valutato e scritto: il registro (`CRM AI Event`) tiene già il riferimento della visita e l'impronta del testo uscito.

**Come si verifica.** Rivedere ogni punto in cui un testo dell'assistente esce (bacheca dell'area, email, PDF): deve portare il segno. Test della chat (`crm/area/tests/test_chat.py`): la frase sta sopra la conversazione e in ogni risposta, e il lettore di schermo la legge.

**Errori da evitare.**

- Il segno affidato solo a un'icona o a un colore.
- Un avatar umano o un nome di persona per l'assistente.
- Togliere il segno quando il medico corregge una parola.

**Fonti.**

- [Regolamento (UE) 2024/1689 (AI Act)](https://eur-lex.europa.eu/eli/reg/2024/1689/oj) — Art. 3, punti 3 e 4; art. 50, par. 1, 2 e 5; art. 111 e 113 come modificati (testo letto dalla copia superuserkalo/eu-ai-act su GitHub, generata dai documenti dell'Ufficio delle pubblicazioni CELEX 32024R1689 e 32026R1744; EUR-Lex non si apriva durante la ricerca) · Unione europea (Gazzetta ufficiale) · 2024; consultato il 12/10/2026
- [Regolamento (UE) 2026/1744 (Digital Omnibus sull'IA)](https://eur-lex.europa.eu/eli/reg/2026/1744/oj) — Art. 1, punti 39 e 40 (art. 111, par. 4; art. 113) (stessa copia) · Unione europea (Gazzetta ufficiale) · 2026 (pubblicato il 24/7/2026); consultato il 12/10/2026
- [Legge 23 settembre 2025, n. 132 — Disposizioni e deleghe al Governo in materia di intelligenza artificiale](https://www.normattiva.it/eli/id/2025/09/25/25G00143/CONSOLIDATED) — Art. 7, comma 3 (letto via WebSearch); GU n. 223 del 25/9/2025, in vigore dal 10/10/2025 · Repubblica italiana (Normattiva) · 2025; letto via WebSearch il 12/10/2026
- [Human Interface Guidelines — Generative AI](https://developer.apple.com/design/human-interface-guidelines/generative-ai#Transparency) — Transparency: «Communicate where your app uses AI», «Set clear expectations…» · Apple · pagina aggiornata l'8/6/2026; consultata il 12/10/2026
- [LLM09:2025 Misinformation — OWASP Top 10 for LLM Applications](https://github.com/OWASP/www-project-top-10-for-large-language-model-applications/blob/main/2_0_vulns/LLM09_Misinformation.md) — Prevention and Mitigation Strategies, 7. User Interface Design · OWASP GenAI Security Project · 2025; consultato il 12/10/2026

### IA-DATI-MINIMI · Al modello va il minimo, e solo con il consenso

**Regola.** All'assistente va solo il testo necessario al compito, mai l'identità della persona (nome, codice fiscale, indirizzo, contatti). Dove tratta dati clinici serve il consenso del paziente all'assistente. Fornitore, regione e conservazione dei dati li sceglie l'agenzia, e sono scritti nelle impostazioni. Il registro conserva le impronte di ciò che entra e di ciò che esce.

**Perché.** OWASP Top 10 for LLM Applications 2025, voce LLM02 Sensitive Information Disclosure, raccomanda di ripulire o mascherare i contenuti sensibili prima che entrino nell'addestramento, di dare accesso ai dati secondo il minimo privilegio, di tokenizzare e oscurare i dati sensibili prima dell'elaborazione e di essere trasparenti su uso, conservazione e cancellazione, lasciando rinunciare all'uso per l'addestramento. Apple HIG (Generative AI, Privacy) chiede di elaborare in locale quanto più possibile e ridurre ciò che si condivide, di far sapere che le informazioni possono andare a un server, di chiedere il permesso prima di usare informazioni personali, di usarne il minimo, di offrire un modo chiaro per rinunciare e di dire se il modello usa le informazioni personali per l'addestramento. Le Privacy Principles del W3C TAG (2.2.1) chiedono di limitare i dati trasferiti a quelli necessari.

**Soglie ed eccezioni.** Nessun identificativo diretto nel prompt. Il testo inviato non supera `MAX_TESTO` (60.000 caratteri) in `crm/assistente/regole.py`.

**In DottorCloud.** `crm/clinica/assistente.py` non manda mai nome, codice o indirizzo del paziente e al loro posto lascia uno spazio tra parentesi quadre. Senza il consenso `ai_assistant` rifiuta con «The patient has not agreed to the assistant: record their consent first», e lo stesso fanno `dettatura.py`, `riassunto.py` e `menu.py` in `crm/clinica/`. La chat dell'area manda solo la domanda e gli ultimi turni, non chi la fa (`crm/area/chat.py`). `regole.pronto` controlla fornitore, indirizzo https, modello e un contratto senza conservazione né addestramento. Il registro (`CRM AI Event`) tiene le impronte SHA-256 di ciò che entra ed esce, insieme alla bozza: per questo gli eventi clinici li legge solo il direttore sanitario (`assistente.registro_clinico`).

**Come si verifica.** Test unitario: i prompt costruiti non contengono il nome, il codice fiscale né l'email della persona di prova. Test del server (`crm/clinica/tests/test_assistente_clinico.py`): senza consenso la chiamata viene rifiutata.

**Errori da evitare.**

- Mandare l'intera cartella «per dare contesto».
- Un consenso chiesto una volta dal centro per tutti i pazienti.
- Un fornitore che conserva i dati o ci addestra il modello senza che le impostazioni lo dicano.

**Vedi anche.** [PRIV-MINIMO-IN-LISTE-E-COPIE](#priv-minimo-in-liste-e-copie--liste-anteprime-e-copie-portano-il-minimo)

**Fonti.**

- [LLM02:2025 Sensitive Information Disclosure — OWASP Top 10 for LLM Applications](https://github.com/OWASP/www-project-top-10-for-large-language-model-applications/blob/main/2_0_vulns/LLM02_SensitiveInformationDisclosure.md) — Prevention and Mitigation Strategies: Sanitization, Access Controls, User Education and Transparency, Tokenization and Redaction · OWASP GenAI Security Project · 2025; consultato il 12/10/2026
- [Human Interface Guidelines — Generative AI](https://developer.apple.com/design/human-interface-guidelines/generative-ai#Privacy) — Privacy: ridurre ciò che si condivide, chiedere il permesso, offrire la rinuncia, dire se si usa per l'addestramento · Apple · pagina aggiornata l'8/6/2026; consultata il 12/10/2026
- [Privacy Principles (W3C TAG, Editor's Draft)](https://w3ctag.github.io/privacy-principles/#data-minimization) — Principio 2.2.1 · W3C Technical Architecture Group · Editor's Draft del 24/11/2025, letto dal ramo gh-pages di w3ctag/privacy-principles su GitHub il 12/10/2026

### IA-EMERGENZA-E-SALUTE · Un'emergenza va subito al 112, una domanda di salute a una persona

**Regola.** Nei canali automatici rivolti ai pazienti (la chat dell'area) valgono tre regole:

- le parole di un'emergenza ricevono subito, prima di qualsiasi modello, un messaggio fisso con una sola azione (chiamare il 112) e nessun altro collegamento;
- le domande su sintomi, farmaci o esiti non ricevono una risposta automatica, ma l'offerta di passarle a una persona del centro;
- tutto il resto ha una risposta basata solo su ciò che il centro ha scritto.

**Perché.** Il NHS service manual («Help users decide when and where to get care») prevede tre carte per tre livelli di cura: non urgente, urgente, emergenza. La carta d'emergenza dice di chiamare subito il 999 o di andare subito in pronto soccorso, può avere solo un collegamento d'azione per trovare il pronto soccorso più vicino e nessun altro collegamento, e si usa solo per le emergenze; chi ha disabilità visive può non riconoscere la carta dal colore, quindi è il titolo a dire cosa fare. OWASP LLM09 (scenario 2) descrive un chatbot per diagnosi senza accuratezza sufficiente che fa danno ai pazienti. Apple HIG (Generative AI, Inputs) chiede di non usare contenuti generati dove un'allucinazione può disinformare e fare danno.

**Soglie ed eccezioni.** Il messaggio d'emergenza ha una sola azione e nessun collegamento accanto, e arriva subito, senza aspettare il modello.

**In DottorCloud.** `crm/area/chat_regole.py` (`classifica`) riconosce l'emergenza e risponde con parole fisse: nulla va al modello né a nessuno. A una domanda di salute la chat non risponde e propone di passarla al centro: se la persona accetta (`pass_on` in `crm/area/chat.py`) diventa una «Domanda» nella sua bacheca (`CRM Area Message`), che la segreteria legge e a cui risponde lì; la notifica che riceve dice solo chi ha chiesto (`chi_avvisare`). Il messaggio d'emergenza va mostrato come un blocco con titolo («Chiama subito il 112») e icona, non affidato solo al rosso.

**Come si verifica.** Test unitari di `classifica` (`crm/area/tests/test_chat_regole.py`) con frasi d'emergenza, sintomi, domande amministrative, errori di ortografia e parole in inglese. Test che nessuna richiesta d'emergenza arrivi al modello: il registro deve restare vuoto.

**Errori da evitare.**

- Un elenco di consigli dopo «chiama il 112».
- Un messaggio d'emergenza che dipende da un servizio esterno che potrebbe non rispondere.
- Una risposta del modello a «posso prendere due compresse?».

**Fonti.**

- [Help users decide when and where to get care (care cards)](https://service-manual.nhs.uk/design-system/patterns/help-users-decide-when-and-where-to-get-care) — How it works; Emergency care card; Care card content (titolo con una sola azione, non affidarsi al colore) · NHS England — NHS digital service manual · guida rivista nel 2026; sorgente nhsuk/nhsuk-service-manual letta il 12/10/2026
- [LLM09:2025 Misinformation — OWASP Top 10 for LLM Applications](https://github.com/OWASP/www-project-top-10-for-large-language-model-applications/blob/main/2_0_vulns/LLM09_Misinformation.md) — Example Attack Scenarios, Scenario #2 · OWASP GenAI Security Project · 2025; consultato il 12/10/2026
- [Human Interface Guidelines — Generative AI](https://developer.apple.com/design/human-interface-guidelines/generative-ai#Inputs) — Inputs: «Avoid using AI-generated content in situations where a possible hallucination could misinform and harm someone.» · Apple · pagina aggiornata l'8/6/2026; consultata il 12/10/2026
