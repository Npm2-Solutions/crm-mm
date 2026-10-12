# I principi sanitari dell'interfaccia

<!-- Copyright (c) 2026, NPM2 Solutions Srl and contributors -->

**Stato:** riferimento (12/10/2026). I principi di esperienza e interfaccia che valgono solo dove la clinica è accesa: perché ci sono dati sanitari e lavoro clinico. Tutti gli altri, compresi l'identità della persona, le bozze, i consensi e l'assistente, sono quelli del CRM: [doc 66](../../crm/66-principi-di-esperienza.md) e [8. La persona giusta e i suoi dati](../../crm/principi/08-persone-e-dati-personali.md). Si leggono come quelli: regola, perché, soglie, come si applicano qui, come si verificano, gli errori da evitare e le fonti.

## I principi

- [SAN-ALLERTE-GRADUATE · Si interrompe solo per ciò che è grave e su cui si può agire](#san-allerte-graduate--si-interrompe-solo-per-ciò-che-è-grave-e-su-cui-si-può-agire)
- [SAN-COPIA-CON-PROVENIENZA · Ciò che si copia dice da dove viene](#san-copia-con-provenienza--ciò-che-si-copia-dice-da-dove-viene)
- [SAN-FIRMA-CONSAPEVOLE · Prima di firmare, oscurare o emettere si vede chi e che cosa](#san-firma-consapevole--prima-di-firmare-oscurare-o-emettere-si-vede-chi-e-che-cosa)
- [PRIV-CHI-PUO-LEGGERE · I dati sanitari li vede solo chi li legge, e lo decide il server](#priv-chi-puo-leggere--i-dati-sanitari-li-vede-solo-chi-li-legge-e-lo-decide-il-server)
- [PRIV-LUCCHETTO-E-OSCURATO · Un lucchetto dove si può sapere, nessuna traccia di ciò che è oscurato](#priv-lucchetto-e-oscurato--un-lucchetto-dove-si-può-sapere-nessuna-traccia-di-ciò-che-è-oscurato)
- [PRIV-REGISTRO-ACCESSI · Ogni lettura di dati sanitari lascia traccia, e la traccia si può consultare](#priv-registro-accessi--ogni-lettura-di-dati-sanitari-lascia-traccia-e-la-traccia-si-può-consultare)
- [PRIV-NOTIFICHE-SENZA-SALUTE · Nelle notifiche il chi e il dove, mai il contenuto sanitario](#priv-notifiche-senza-salute--nelle-notifiche-il-chi-e-il-dove-mai-il-contenuto-sanitario)
- [PRIV-CLINICO-AL-SUO-POSTO · Il dato clinico si scrive dove è protetto](#priv-clinico-al-suo-posto--il-dato-clinico-si-scrive-dove-è-protetto)
- [PRIV-STEP-UP · Prima di scaricare un dato sanitario, una verifica recente](#priv-step-up--prima-di-scaricare-un-dato-sanitario-una-verifica-recente)
- [SAN-SCENARI-CRITICI · Si provano gli scenari critici e si contano gli errori d'uso](#san-scenari-critici--si-provano-gli-scenari-critici-e-si-contano-gli-errori-duso)
- [REG-DISPOSITIVO-MEDICO · Prima di una funzione che interpreta i dati di un paziente, si valuta se è un dispositivo medico](#reg-dispositivo-medico--prima-di-una-funzione-che-interpreta-i-dati-di-un-paziente-si-valuta-se-è-un-dispositivo-medico)

### SAN-ALLERTE-GRADUATE · Si interrompe solo per ciò che è grave e su cui si può agire

**Regola.** Un avviso che interrompe (finestra, blocco, toast che chiede di agire) si usa solo se l'evento è grave, riguarda chi legge e richiede un'azione subito. Tutto il resto è informazione passiva, al suo posto: una riga o un segno con parole. Gli avvisi hanno livelli (informazione, attenzione, blocco), sono adatti al ruolo di chi li riceve e non si ripetono per la stessa cosa. Si misura quante volte vengono chiusi senza agire.

**Perché.** Il primer «Alert Fatigue» di AHRQ PSNet (2019) spiega che la grande maggioranza degli avvisi dei sistemi di prescrizione è clinicamente irrilevante e che i clinici finiscono per ignorare insieme quelli inutili e quelli critici. Propone di rendere gli avvisi più specifici, togliendo quelli irrilevanti e adattandoli al paziente, di graduarli per gravità e di rendere interruttivi solo quelli gravi, mostrando il resto senza interrompere. Il commento PSNet «Finding Fault With the Default Alert» (2013) riporta che i medici ignorano gli avvisi computerizzati fino al 95% delle volte. Una revisione sistematica (Hussain, Reynolds, Zheng, JAMIA 2019) conclude che l'affaticamento si può ridurre riprogettando il comportamento degli avvisi e adattandoli al ruolo clinico, per esempio con avvisi a livelli o mandando certi avvisi al farmacista. Apple HIG (Notifications, Best practices) dice di non mandare più notifiche per la stessa cosa e di usare un alert, non una notifica, per un messaggio d'errore.

**Soglie ed eccezioni.** È interruttivo solo il livello più alto. Obiettivo di DottorCloud, non una soglia delle fonti: un avviso interruttivo che quasi sempre viene chiuso senza azione diventa passivo o si toglie.

**In DottorCloud.** `crm/notifiche/avvisi.py` (`avvisa`) non scrive due volte la stessa notifica non letta e raccoglie in una i messaggi della stessa persona: ogni modulo deve passare di lì. Esempi passivi giusti:

- «Autorizzazione mancante» nel pannello dell'appuntamento (`convention_info` in `crm.api.appointments.get_appointment`) e in Accoglienza (`nelle_righe` in `crm/convenzioni/convenzioni.py`);
- i moduli dovuti (`crm/moduli/dovuti.py`), mostrati come riga «Da firmare per l'appuntamento del 18 ott, 10:00».

Da correggere:

- nei Piani il riquadro delle qualifiche, alto circa 206 px, spinge il piano della paziente in fondo (`api.tipi_bloccati`; studio UX, ottobre 2026): diventa una riga che si può chiudere;
- un modulo dovuto prima della visita deve distinguersi dalle altre righe (vedi le insidie).

Il livello dell'avviso si sceglie in base al ruolo (`livelli.puo`).

**Come si verifica.** Per ogni avviso interruttivo, registrare quante volte viene chiuso senza azione (un contatore lato server, letto dal responsabile) e rivederlo periodicamente. Test di usabilità: chi lavora in accoglienza nota un modulo dovuto prima della visita?

**Errori da evitare.**

- Trasformare ogni promemoria in un modale o in un toast rosso.
- Un avviso che torna a ogni salvataggio: «Metodo di pagamento da confermare» si rimetteva da solo anche dopo la scelta (trovato dalla revisione del codice dello studio; corretto).
- Un avviso critico che vive solo in un toast che svanisce (WCAG 2.2.1 e 4.1.3, famiglia dell'accessibilità).
- Il colore come unico segno di gravità.
- L'errore opposto: un modulo dovuto mostrato in grigio come le altre righe. Nella scheda di una paziente già visitata l'informativa privacy «Mai firmato» non si notava (studio UX, ottobre 2026, gravità 2).

**Fonti.**

- [Alert Fatigue (primer)](https://psnet.ahrq.gov/primer/alert-fatigue) — Avvisi in maggioranza irrilevanti, anche i critici ignorati; specificità, livelli di gravità, solo i gravi interruttivi (letto via WebSearch) · AHRQ PSNet · 2019; letto via WebSearch il 12/10/2026
- [Finding Fault With the Default Alert (WebM&M)](https://psnet.ahrq.gov/web-mm/finding-fault-default-alert) — Commento: i medici ignorano gli avvisi computerizzati fino al 95% delle volte (letto via WebSearch) · AHRQ PSNet (commento di M. Baysari) · 2013; letto via WebSearch il 12/10/2026
- [Medication safety alert fatigue may be reduced via interaction design and clinical role tailoring: a systematic review](https://escholarship.org/uc/item/4v79x7m6) — Conclusioni (letto via WebSearch) · Journal of the American Medical Informatics Association (M. I. Hussain, T. L. Reynolds, K. Zheng) · 2019; letto via WebSearch il 12/10/2026
- [Human Interface Guidelines — Notifications](https://developer.apple.com/design/human-interface-guidelines/notifications#Best-practices) — Best practices: niente notifiche ripetute per la stessa cosa; un alert, non una notifica, per un errore · Apple · consultato il 12/10/2026

### SAN-COPIA-CON-PROVENIENZA · Ciò che si copia dice da dove viene

**Regola.** Quando una visita, un piano o un testo parte da uno precedente («Inizia dall'ultima visita», un modello), la bozza dice da dove viene, di quando e chi l'ha copiata («Copiata dalla visita del 3 ott»), e ogni campo copiato si distingue finché non lo si rivede. Non si copiano mai firme, allegati, consensi né dati di un'altra persona.

**Perché.** La NISTIR 8166 (NIST con ECRI, 2017) ha studiato come i clinici usano il copia-incolla nelle cartelle elettroniche e ne ha tratto tre problemi. Copiare troppo confonde e fa perdere informazioni importanti. I clinici devono sapere da dove viene il testo copiato, chi l'ha copiato, che cosa è stato aggiunto o cambiato e quando. L'errore più comune è non rivedere e correggere tutto ciò che si è copiato, spesso per le interruzioni, anche perché il sistema non aiuta a farlo. Il rapporto dà raccomandazioni specifiche per l'interfaccia.

**In DottorCloud.** `crm/clinica/cartella.py` (`start_sheet(from_last=1)`, `ultima_visita`) copia le risposte dell'ultima visita firmata della stessa scheda, solo tra quelle che la sessione può leggere (senza episodi oscurati né «solo io», con la lettura nel registro degli accessi) e attraverso la versione pubblicata oggi; non copia mai firma, allegati o consensi. La bozza registra `copied_from` e lo dice («Copied from the visit of {0}» in `Clinic/ClinicArea.vue`); `utils/cartella.js` (`ultimaVisitaSu`, `vociDelleSchede`) decide quando offrire «Inizia dall'ultima visita». Va mantenuto così: niente copia-incolla tra persone diverse, il segno resta finché la visita non è firmata, e nel riepilogo clinico (`crm/clinica/sintesi.py`) il sistema propone e un professionista conferma.

**Come si verifica.** Test sul sito (`crm/clinica/tests/test_cartella.py`): iniziare dall'ultima visita, verificare che il segno ci sia e che firma e allegati non vengano copiati, e che `ultima_visita` escluda gli episodi oscurati e quelli «solo io». Test unitario di `ultimaVisitaSu`.

**Errori da evitare.**

- Copiare dalla visita di un'altra persona aperta in un'altra scheda.
- Un segno «copiato» che sparisce appena si tocca il campo, anche se il contenuto non è stato rivisto.
- Copiare senza dirlo valori clinici che cambiano nel tempo (pressione, peso, punteggi).

**Vedi anche.** [IA-REVISIONE-UMANA](../../crm/principi/08-persone-e-dati-personali.md#ia-revisione-umana--lassistente-scrive-bozze-la-persona-decide)

**Fonti.**

- [NISTIR 8166 — Examining the Copy and Paste Function in the Use of Electronic Health Records](https://nvlpubs.nist.gov/nistpubs/ir/2017/NIST.IR.8166.pdf) — Abstract: «Length of information», «Attribution of information», «Wrong information» (testo letto dai metadati della pubblicazione in relaton-data-nist su GitHub; il PDF non si apriva durante la ricerca) · NIST, con ECRI (L. Z. Lowry e altri) · 2017; consultato il 12/10/2026

### SAN-FIRMA-CONSAPEVOLE · Prima di firmare, oscurare o emettere si vede chi e che cosa

**Regola.** Le azioni cliniche o legali che non si annullano mostrano prima una conferma con la persona e i suoi due identificativi, l'oggetto e la conseguenza («Diventa immutabile», «Va al Sistema TS»), e il verbo sul pulsante. Sono: firmare una visita o un modulo, oscurare un episodio, emettere o trasmettere una fattura, consegnare un referto online. Quando invece si può tornare indietro, si offre di farlo invece di chiedere conferma.

**Perché.** WCAG 2.2, criterio 3.3.4 Error Prevention (Legal, Financial, Data) (AA): per le pagine che creano impegni legali o transazioni finanziarie, o che modificano o cancellano dati, vale almeno una di tre condizioni: l'invio si può annullare; i dati vengono controllati e si possono correggere; c'è un modo per rivedere, confermare e correggere prima di inviare. La NISTIR 7804 (2012) chiama errore d'identificazione documentare un'azione nella cartella del paziente sbagliato: una firma sulla persona sbagliata è proprio quell'errore, e dopo non si corregge. La SAFER Guide (revisione 2024, raccomandazione 2.5) indica, dove manca la foto, di far riscrivere identificativi del paziente (le iniziali, il nome) prima di firmare gli ordini.

**In DottorCloud.** Le azioni interessate e i loro punti nel codice:

- firma della visita: `crm/clinica/referto.py` (PDF/A fatto una volta sola);
- firma del modulo: `crm/moduli/compilazioni.py`;
- oscuramento: `Clinic/ObscureDialog.vue` e `crm/clinica/dossier.py`;
- emissione della fattura: `crm/invoicing/emissione.py` e `Invoices/InvoiceDialog.vue`;
- consegna online: `Documents/DeliverDialog.vue` e `crm/documenti/consegna.py`.

In ognuna la conferma nomina «Noemi Carbone, nata il 2 giu 1961» e dice cosa succede. Le altre regole delle conferme (titolo «Vuoi…?», verbi sui pulsanti) sono della famiglia dei microtesti.

**Come si verifica.** Rivedere ogni dialogo di firma ed emissione: deve avere nome, secondo identificativo, conseguenza e verbo. Test di scenario: firmare con due pazienti aperti in due schede del browser.

**Errori da evitare.**

- «Sei sicuro?» senza dire di chi.
- La stessa conferma ovunque, che si clicca senza leggere (vedi SAN-ALLERTE-GRADUATE).
- Un pulsante «Emetti la fattura» che non emette ma prepara una bozza (studio UX, ottobre 2026, gravità 3): l'etichetta era ancora questa («Invoice it» in `crm/locale/it.po`), corretta il 12/10/2026 in «Prepara la fattura»; «Emetti» resta al dialogo, che emette.

**Fonti.**

- [Web Content Accessibility Guidelines (WCAG) 2.2 — 3.3.4 Error Prevention (Legal, Financial, Data)](https://www.w3.org/TR/WCAG22/#error-prevention-legal-financial-data) — Criterio 3.3.4 (AA): Reversible, Checked, Confirmed · W3C · 2023 (Raccomandazione W3C); testo letto dal repository w3c/wcag su GitHub il 12/10/2026
- [NISTIR 7804 — Technical Evaluation, Testing and Validation of the Usability of Electronic Health Records](https://nvlpubs.nist.gov/nistpubs/ir/2012/NIST.IR.7804.pdf) — Principio 1A «patient identification error» (letto via WebSearch) · NIST · 2012; letto via WebSearch il 12/10/2026
- [Appendix C. 2024 Patient Identification SAFER Guide (materiale supplementare di «Developing updated and new guidance to promote reliable patient identification»)](https://pmc-oa-opendata.s3.amazonaws.com/PMC12772641.1/ooaf160_supplementary_data.docx) — Recommended Practice 2.5, Implementation Guidance (riscrivere gli identificativi prima di firmare gli ordini) · JAMIA Open (Oxford University Press), dal dataset Open Access di PubMed Central · 2026; letto il 12/10/2026

### PRIV-CHI-PUO-LEGGERE · I dati sanitari li vede solo chi li legge, e lo decide il server

**Regola.** Ogni schermata riceve dal server solo ciò che chi la apre può leggere. Per i dati sanitari (cartella, referti, piani e documenti con il segno `clinical`) contano il dossier, la disciplina, l'impostazione «solo io», l'oscuramento e la presa in carico. Nascondere un campo nel browser non è mai un controllo di accesso.

**Perché.** Per il GDPR i dati relativi alla salute sono una categoria particolare: trattarli è vietato salvo le eccezioni dell'art. 9, par. 2, tra cui la diagnosi, l'assistenza o la terapia sanitaria sulla base del diritto dell'Unione o nazionale o di un contratto con un professionista sanitario (lett. h), purché da parte di professionisti soggetti al segreto professionale o sotto la loro responsabilità (par. 3). L'art. 25, par. 2, chiede misure perché, per impostazione predefinita, i dati non siano resi accessibili a un numero indefinito di persone senza l'intervento dell'interessato. Le Linee guida del Garante sul dossier sanitario (4/6/2015) legano la consultazione delle informazioni scritte da altri professionisti al consenso del paziente al dossier: senza, il medico vede solo ciò che riguarda la prestazione in corso o le sue precedenti. OWASP ASVS 5.0.0 chiede accesso ai singoli dati solo a chi ha i permessi su quei dati (8.2.2), un accesso limitato anche per campo (8.2.3), regole applicate in un servizio fidato e mai in controlli che il client può manipolare, come il JavaScript (8.3.1), e di restituire il minimo di dati sensibili necessario (14.2.6). Le Privacy Principles del W3C TAG (2.4) ricordano che la sensibilità di un'informazione dipende dalle circostanze e dal contesto.

**In DottorCloud.** Dove stanno le regole oggi:

- `crm/clinica/dossier.py` (`legge_le_altre`, `condizione_condivisa`): la stessa regola per la scheda e per la lista;
- `crm/permissions/sanitari.py` (`Lettore`, segno `clinical`);
- `crm/permissions/org_hierarchy.py`: chi vede quali persone;
- `crm.api.doc.get_fields`: non disegna un campo che l'utente non può leggere.

La segreteria sa che una visita c'è stata ma non cosa è stato detto; manager, commerciale e marketing non la vedono (docstring di `crm/clinica/cartella.py`). Il marketing riceve email e telefono mascherati (il ruolo `RUOLO_RECAPITI` manca al suo livello), e il codice che invia legge il valore vero con `crm.utils.stored_value`.

**Come si verifica.** Test del server per ogni ruolo (`crm/clinica/tests/test_dossier.py`, `test_cartella.py`): lista e scheda devono dare lo stesso risultato. Chiamare direttamente l'API con un utente senza permesso. Nella revisione di sicurezza, verificare che nessun dato sanitario sia filtrato solo nel frontend.

**Errori da evitare.**

- Scaricare tutto e filtrare nel browser.
- Una lista con una regola diversa dalla scheda, per esempio un conteggio che include ciò che non si può leggere.
- Il dato clinico scritto fuori dalla cartella (vedi PRIV-CLINICO-AL-SUO-POSTO).

**Fonti.**

- [Regolamento (UE) 2016/679 (GDPR)](https://eur-lex.europa.eu/eli/reg/2016/679/oj) — Art. 9, par. 1, 2 lett. h, e par. 3; art. 25, par. 2 (testo inglese della GU L 119 del 4/5/2016 letto dalla copia GDPRtEXT dell'ADAPT Centre su GitHub, coolharsh55/GDPRtEXT; EUR-Lex non si apriva durante la ricerca) · Unione europea (Gazzetta ufficiale) · 2016; consultato il 12/10/2026
- [Linee guida in materia di Dossier sanitario - 4 giugno 2015 \[doc. web n. 4084632\]](https://www.garanteprivacy.it/web/guest/home/docweb/-/docweb-display/docweb/4084632) — Consenso al dossier; senza consenso, solo le informazioni della prestazione in corso o delle precedenti dello stesso professionista (letto via WebSearch, dall'infografica del Garante) · Garante per la protezione dei dati personali · 2015 (GU n. 164 del 17/7/2015); letto via WebSearch il 12/10/2026
- [OWASP ASVS 5.0.0 — V8 Authorization](https://github.com/OWASP/ASVS/blob/master/5.0/en/0x17-V8-Authorization.md) — Requisiti 8.2.2, 8.2.3, 8.3.1 · OWASP Foundation · 2025 (versione 5.0.0, maggio 2025); consultato il 12/10/2026
- [OWASP ASVS 5.0.0 — V14 Data Protection](https://github.com/OWASP/ASVS/blob/master/5.0/en/0x23-V14-Data-Protection.md) — Requisito 14.2.6 (livello 3) · OWASP Foundation · 2025 (versione 5.0.0, maggio 2025); consultato il 12/10/2026
- [Privacy Principles (W3C TAG, Editor's Draft)](https://w3ctag.github.io/privacy-principles/#hl-sensitive-information) — 2.4 Sensitive Information, principio 2.4 · W3C Technical Architecture Group · Editor's Draft del 24/11/2025, letto dal ramo gh-pages di w3ctag/privacy-principles su GitHub il 12/10/2026

### PRIV-LUCCHETTO-E-OSCURATO · Un lucchetto dove si può sapere, nessuna traccia di ciò che è oscurato

**Regola.** Se chi legge può sapere che esistono dati che non è autorizzato a leggere, la lista mostra un lucchetto con parole e conteggio («2 documenti con dati sanitari che non leggi»), mai «Ancora niente». Un indirizzo che porta a una scheda chiusa dice perché, a parole. Ciò che il paziente ha fatto oscurare e ciò che è segnato «solo io», per gli altri invece non esiste: niente lucchetto, conteggio, fonte di riepilogo o spazio vuoto che lo tradisca.

**Perché.** Le Linee guida del Garante sul dossier (4/6/2015) danno al paziente il diritto di non far confluire alcune informazioni nel dossier: l'oscuramento è revocabile e deve avvenire in modo che chi è abilitato all'accesso non possa sapere automaticamente che il paziente ha fatto quella scelta (il cosiddetto «oscuramento dell'oscuramento»). Le due metà della regola sono già scritte nel codice. `crm/permissions/sanitari.py` vuole che chi può sapere di dati sanitari che non legge veda «their padlock in the list, never an empty one». `crm/clinica/dossier.py` stabilisce che gli altri non vedano un episodio oscurato, «not a padlock, not a count, not the source of a line of the summary», perché non devono poter capire che qualcosa è stato oscurato. OWASP ASVS 5.0.0 chiede un accesso per campo limitato (8.2.3) e regole applicate nel servizio fidato (8.3.1); le Privacy Principles del W3C TAG (2.11.1) chiedono di dare alle persone spiegazioni pertinenti sull'uso dei dati quando vi si accede.

**In DottorCloud.** Cosa c'è già:

- `sanitari.nascosti` conta ciò che il lettore non legge ma può conoscere (`dossier.sa_che_c_e`: mai «solo io» né episodi oscurati, salvo per chi li vede);
- nell'anteprima dell'area `area/components/HiddenCard.vue` dice «Qui {0} vede qualcosa che in DottorCloud tu non leggi»;
- `utils/schedaChiusa.js` spiega a parole perché una persona o una trattativa non si apre.

Cosa manca: per chi non ha la scheda Clinica, il collegamento a `#clinic` apre la Chat senza dire nulla (`useActiveTabManager.js`, `tabOrConversation`). Deve dire «La cartella clinica la leggono i professionisti che hanno in cura la persona» (studio UX, ottobre 2026).

**Come si verifica.** Test del server: un episodio oscurato non entra nel conteggio della lista di un collega e il riepilogo non ne cita la fonte (`dossier.fonti_nascoste`); per un documento clinico non letto il conteggio è giusto. Test a mano dell'indirizzo `#clinic` con un utente senza capacità cliniche. Il lucchetto ha un testo leggibile dal lettore di schermo.

**Errori da evitare.**

- «Ancora nessun modulo» proprio sotto un modulo da firmare (studio UX, ottobre 2026).
- Un lucchetto su un episodio oscurato: rivela proprio ciò che il paziente ha chiesto di nascondere.
- Un buco nella numerazione o nella linea del tempo che fa intuire un episodio oscurato.
- Un riquadro di divieti che occupa lo schermo (nei Piani misurava circa 206 px: studio UX, ottobre 2026).

**Fonti.**

- [Linee guida in materia di Dossier sanitario - 4 giugno 2015 \[doc. web n. 4084632\]](https://www.garanteprivacy.it/web/guest/home/docweb/-/docweb-display/docweb/4084632) — Oscuramento revocabile, senza che gli abilitati possano saperlo (letto via WebSearch, da estratti e sintesi) · Garante per la protezione dei dati personali · 2015 (GU n. 164 del 17/7/2015); letto via WebSearch il 12/10/2026
- [OWASP ASVS 5.0.0 — V8 Authorization](https://github.com/OWASP/ASVS/blob/master/5.0/en/0x17-V8-Authorization.md) — Requisiti 8.2.3, 8.3.1 · OWASP Foundation · 2025 (versione 5.0.0, maggio 2025); consultato il 12/10/2026
- [Privacy Principles (W3C TAG, Editor's Draft)](https://w3ctag.github.io/privacy-principles/#transparency) — 2.11 Transparency, principio 2.11.1 · W3C Technical Architecture Group · Editor's Draft del 24/11/2025, letto dal ramo gh-pages di w3ctag/privacy-principles su GitHub il 12/10/2026

### PRIV-REGISTRO-ACCESSI · Ogni lettura di dati sanitari lascia traccia, e la traccia si può consultare

**Regola.** Ogni volta che una schermata mostra dati sanitari, il server registra chi, cosa e quando, senza copiare il dato. Vale per l'apertura di una visita, per una lista di documenti clinici, per l'anteprima dell'area e per un download. Chi ne ha il diritto consulta il registro dalla scheda («Chi l'ha aperta»), e il registro si conserva per il tempo stabilito. Aprire la cartella di qualcuno che non si ha in cura richiede un motivo, che viene scritto e resta visibile, e l'apertura scade.

**Perché.** Le Linee guida del Garante sul dossier (4/6/2015) vogliono che ogni accesso e ogni operazione sul dossier, anche la sola consultazione, siano registrati automaticamente in file di log da conservare per almeno 24 mesi, e che il paziente possa sapere quale reparto ha consultato il suo dossier, in che data e a che ora. OWASP ASVS 5.0.0 chiede di registrare i tentativi di accesso non autorizzati e, al livello 3, tutte le decisioni di autorizzazione, compreso l'accesso a dati sensibili, senza registrare i dati stessi (16.3.2), e di trattare nei log i dati sensibili secondo il loro livello di protezione (16.2.5). Il GDPR (considerando 78) indica tra le misure di protezione fin dalla progettazione il permettere all'interessato di controllare il trattamento.

**Soglie ed eccezioni.** Il registro si conserva per almeno 730 giorni (`GIORNI_REGISTRO` in `crm/clinica/cartella.py`), i 24 mesi del Garante. Se qualcuno aggiunge View Log e Access Log a Log Settings, il framework li cancellerebbe per impostazione predefinita dopo 180 e 30 giorni (`clear_old_logs`): `proteggi_registro_accessi` e `valida_impostazioni_log` alzano quel minimo a 730. L'apertura fuori équipe dura 24 ore (`ORE_FUORI_EQUIPE` in `crm/clinica/dossier.py`).

**In DottorCloud.** Come funziona oggi:

- `crm/clinica/cartella.py` scrive un View Log per ogni voce restituita (il framework lo farebbe solo dalla Desk), e Frappe scrive un Access Log per ogni download di un file privato;
- «Chi l'ha aperta» (`Clinic/ClinicArea.vue`) li mostra insieme al manager e al direttore sanitario;
- `Clinic/OutOfCareDialog.vue` con `Clinic Access Grant` gestisce l'apertura con motivo;
- l'anteprima dell'area registra i dati sanitari letti (`crm/area/anteprima.py`).

Ogni nuova schermata che legge dati con il segno `clinical` deve chiamare lo stesso registro. Da valutare: oggi il paziente non vede dalla sua area chi ha consultato la sua cartella.

**Come si verifica.** Test del server: ogni chiamata che restituisce dati clinici crea un View Log; ogni download crea un Access Log; Log Settings non scende sotto 730 giorni. Nella revisione delle nuove API, cercare le chiamate che leggono `Clinic Record` o dati `clinical` senza registrare.

**Errori da evitare.**

- Scrivere nel registro il contenuto letto: diventa una seconda copia del dato.
- Un registro che nessuno può leggere dall'app.
- Una nuova lista (telefono, dashboard) che mostra dati clinici senza scrivere nel registro.

**Fonti.**

- [Linee guida in materia di Dossier sanitario - 4 giugno 2015 \[doc. web n. 4084632\]](https://www.garanteprivacy.it/web/guest/home/docweb/-/docweb-display/docweb/4084632) — Tracciamento degli accessi, log conservati almeno 24 mesi, conoscenza degli accessi da parte del paziente (letto via WebSearch, da estratti e sintesi) · Garante per la protezione dei dati personali · 2015 (GU n. 164 del 17/7/2015); letto via WebSearch il 12/10/2026
- [OWASP ASVS 5.0.0 — V16 Security Logging and Error Handling](https://github.com/OWASP/ASVS/blob/master/5.0/en/0x25-V16-Security-Logging-and-Error-Handling.md) — Requisiti 16.2.5 e 16.3.2 · OWASP Foundation · 2025 (versione 5.0.0, maggio 2025); consultato il 12/10/2026
- [Regolamento (UE) 2016/679 (GDPR)](https://eur-lex.europa.eu/eli/reg/2016/679/oj) — Considerando 78 (testo inglese della GU L 119 del 4/5/2016 letto dalla copia GDPRtEXT dell'ADAPT Centre su GitHub) · Unione europea (Gazzetta ufficiale) · 2016; consultato il 12/10/2026

### PRIV-NOTIFICHE-SENZA-SALUTE · Nelle notifiche il chi e il dove, mai il contenuto sanitario

**Regola.** Notifiche push, email, SMS, WhatsApp e toast dicono che c'è qualcosa e dove aprirlo, non il contenuto sanitario. Sulla schermata di blocco non compaiono diagnosi, servizi che rivelano uno stato di salute, testi di note cliniche o messaggi dei pazienti: il contenuto si legge solo dopo aver aperto DottorCloud con la propria sessione. Il permesso per le notifiche si chiede quando serve, dicendo che cosa arriverà e come spegnerle.

**Perché.** Per il GDPR sono dati relativi alla salute anche le informazioni raccolte quando una persona si registra per prestazioni sanitarie o le riceve (art. 4, punto 15, e considerando 35): un promemoria che nomina la prestazione, o il nome di chi scrive a un centro medico, può già rivelare uno stato di salute. Apple HIG (Notifications, Best practices) dice di evitare informazioni sensibili, personali o riservate in una notifica: non si può prevedere che cosa stiano facendo le persone quando la ricevono, e altri potrebbero vederla. Android (Create a notification › Set lock screen visibility) prevede VISIBILITY_PRIVATE, che sulla schermata di blocco mostra solo icona e titolo, e setPublicVersion per una versione senza dettagli: l'esempio è un'app di SMS che mostra «Hai 3 nuovi messaggi» senza contenuti né mittenti. Le notifiche web non hanno questa scelta: tra le opzioni di showNotification (MDN) non c'è una visibilità sulla schermata di blocco. Le Privacy Principles del W3C TAG (2.13.2) chiedono notifiche solo per ciò che le persone hanno chiesto, dicendo quando si chiede il permesso che tipo di informazioni arriveranno e come spegnerle.

**Soglie ed eccezioni.** Il corpo di una push non contiene parole del messaggio per i tipi che possono portare dati sanitari, salvo una scelta esplicita dell'utente per il proprio dispositivo personale.

**In DottorCloud.** Cosa funziona già: le novità dell'area via email dicono solo «Novità nella tua area presso {0}» (`crm/area/collegamento.py`); una domanda o un messaggio nella bacheca avvisa chi deve rispondere solo con il nome di chi ha scritto («the words stay on the board»: `crm/area/messaggi.py`, `pass_on` in `crm/area/chat.py`).

Cosa rivedere:

- `crm/notifiche/spinta.py` (`messaggio`) mette nel corpo della push le prime parole del messaggio (`regole.anteprima`, 160 caratteri; corpo fino a `TESTO` = 240) per i tipi di `CON_ANTEPRIMA` in `crm/notifiche/api.py` (menzioni, WhatsApp, SMS, email, fatturazione), e nel titolo il nome di chi ha scritto («💬 Laura Bassi (3)»). Così un paziente che descrive i sintomi su WhatsApp finisce sulla schermata di blocco del telefono del professionista. Proposta: corpo vuoto o «Nuovo messaggio» per questi tipi, e una scelta «Mostra l'anteprima su questo dispositivo», spenta all'inizio, in Impostazioni › Notifiche (`NotificationsSettings.vue`).
- Il modello del promemoria (`MODELLO` in `crm/scheduling/promemoria_regole.py`: «Ciao {{1}}, ti ricordiamo l'appuntamento: {{2}}, {{3}}, presso {{4}}.») mette in {{2}} il servizio («Visita di controllo» nell'esempio): per i servizi che rivelano uno stato di salute serve un nome da usare nei messaggi (per esempio «Visita»).

**Come si verifica.** Test unitario di `spinta.messaggio` (`crm/notifiche/tests/test_spinta.py`) per ogni tipo: nessun `body` con parole del messaggio per i tipi a rischio. Prova su un iPhone e un Android bloccati per vedere cosa si legge. Revisione dei modelli dei promemoria, delle liste d'attesa e dei solleciti.

**Errori da evitare.**

- Notifiche push che restano legate al browser dopo l'uscita: nessun `on_logout` in `crm/hooks.py` toglie l'abbonamento (`CRM Push Subscription`) e il service worker (`crm/notifiche/spinta_sw.js`) mostra tutto ciò che arriva. Su un PC condiviso arrivano le notifiche di chi è uscito finché un altro utente non apre DottorCloud su quel browser: allora `sincronizza()` (`composables/spinta.js`) passa l'abbonamento a lui, senza chiederglielo.
- Un avviso in tempo reale pubblicato senza destinatario: `frappe.publish_realtime` senza `user` va a tutti gli utenti della scrivania collegati. `crm/api/event.py` (`_send_system_notification`) manda così gli avvisi degli eventi del calendario, con oggetto e descrizione (per un appuntamento copiato: servizio, persona e note), e il browser li tiene in localStorage (`eventNotificationAlerts` in `data/notifications.js`) (verifica del codice, 12/10/2026).
- Il nome della persona e il servizio nell'oggetto dell'email a un collega.
- Un toast con un contenuto clinico che resta sullo schermo mentre il paziente guarda.

**Fonti.**

- [Regolamento (UE) 2016/679 (GDPR)](https://eur-lex.europa.eu/eli/reg/2016/679/oj) — Art. 4, punto 15 («data concerning health»); considerando 35 (testo inglese della GU L 119 del 4/5/2016 letto dalla copia GDPRtEXT dell'ADAPT Centre su GitHub) · Unione europea (Gazzetta ufficiale) · 2016; consultato il 12/10/2026
- [Human Interface Guidelines — Notifications](https://developer.apple.com/design/human-interface-guidelines/notifications#Best-practices) — Best practices: «Avoid including sensitive, personal, or confidential information in a notification.» · Apple · consultato il 12/10/2026
- [Create a notification](https://developer.android.com/develop/ui/compose/notifications/create-notification#lockscreenNotification) — Set lock screen visibility: VISIBILITY_PUBLIC, VISIBILITY_SECRET, VISIBILITY_PRIVATE; setPublicVersion() (il vecchio indirizzo …/views/notifications/build-notification rimanda qui) · Android Developers (Google) · pagina aggiornata il 07/10/2026; consultata il 12/10/2026
- [ServiceWorkerRegistration: showNotification() method](https://developer.mozilla.org/en-US/docs/Web/API/ServiceWorkerRegistration/showNotification) — Syntax › Parameters › options (elenco completo delle opzioni) · MDN Web Docs (Mozilla) · consultato il 12/10/2026 (sorgente mdn/content su GitHub)
- [Privacy Principles (W3C TAG, Editor's Draft)](https://w3ctag.github.io/privacy-principles/#interruptions) — 2.13 Notifications and Interruptions, principio 2.13.2 · W3C Technical Architecture Group · Editor's Draft del 24/11/2025, letto dal ramo gh-pages di w3ctag/privacy-principles su GitHub il 12/10/2026

### PRIV-CLINICO-AL-SUO-POSTO · Il dato clinico si scrive dove è protetto

**Regola.** Un'osservazione clinica si scrive nella cartella (visita, scheda, documento con il segno), dove valgono dossier, oscuramento e registro degli accessi. Le note interne, le cose da fare, la chat e i messaggi non sono il posto per sintomi, esiti o terapie. Quando un professionista sanitario scrive una nota libera, lo schermo gli propone di scriverla nella cartella.

**Perché.** OWASP ASVS 5.0.0 chiede di identificare tutti i dati sensibili creati e trattati e di classificarli per livello di protezione (14.1.1); i controlli seguono poi quel livello (14.2.4). Le Privacy Principles del W3C TAG (2.4) ricordano che la sensibilità dipende dal contesto. Il GDPR permette di trattare i dati sanitari per la cura solo da parte di professionisti soggetti al segreto o sotto la loro responsabilità (art. 9, par. 3). In DottorCloud le protezioni dei dati sanitari (dossier, oscuramento, registro, segno `clinical`) valgono per la cartella e per ciò che porta il segno, non per le note: le note le legge tutta la segreteria e il manager del centro (`note.vedi` in `crm/permissions/catalogo.py`).

**In DottorCloud.** Nel compositore delle note (`Activities/`), per chi ha una qualifica sanitaria (la qualifica del suo `CRM Service Provider`, `disciplina_di` in `crm/clinica/dossier.py`, con `is_healthcare` in `CRM Professional Qualification`), aggiungere un collegamento «Scrivi nella cartella» accanto a «Salva nota». Nei dati di prova (`crm/demo/dati.py`) note come «Dolore lombare» («peggiora la sera») o quella sulla risonanza del ginocchio vanno trasformate in visite, perché la demo insegna le abitudini. Ciò che un professionista sanitario scrive in un piano o in un documento prende già il segno (`sanitari.per_chi_scrive`, che con la clinica accesa usa `dossier.e_sanitario`).

**Come si verifica.** Cercare periodicamente parole cliniche nelle note del sito di prova. Rivedere i dati di prova. Test di usabilità con un professionista: dove scrive un'osservazione al volo?

**Errori da evitare.**

- Una nota «interna» che legge tutta la segreteria.
- Una cosa da fare con la diagnosi nel titolo, che poi finisce nelle notifiche.
- Un referto arrivato via WhatsApp lasciato nella conversazione invece di archiviarlo tra i documenti (`DocumentDialog`, apribile da un messaggio).

**Fonti.**

- [OWASP ASVS 5.0.0 — V14 Data Protection](https://github.com/OWASP/ASVS/blob/master/5.0/en/0x23-V14-Data-Protection.md) — Requisiti 14.1.1 e 14.2.4 · OWASP Foundation · 2025 (versione 5.0.0, maggio 2025); consultato il 12/10/2026
- [Privacy Principles (W3C TAG, Editor's Draft)](https://w3ctag.github.io/privacy-principles/#hl-sensitive-information) — 2.4 Sensitive Information · W3C Technical Architecture Group · Editor's Draft del 24/11/2025, letto dal ramo gh-pages di w3ctag/privacy-principles su GitHub il 12/10/2026
- [Regolamento (UE) 2016/679 (GDPR)](https://eur-lex.europa.eu/eli/reg/2016/679/oj) — Art. 9, par. 3 (testo inglese della GU L 119 del 4/5/2016 letto dalla copia GDPRtEXT dell'ADAPT Centre su GitHub) · Unione europea (Gazzetta ufficiale) · 2016; consultato il 12/10/2026

### PRIV-STEP-UP · Prima di scaricare un dato sanitario, una verifica recente

**Regola.** Nell'area e nelle pagine dei collegamenti, aprire o scaricare un referto o un documento con dati sanitari, o firmare un preventivo, richiede una verifica recente: un codice appena ricevuto o una passkey, anche se la sessione è già aperta. Il codice si può incollare, i gestori di password funzionano, e la verifica vale per pochi minuti.

**Perché.** OWASP ASVS 5.0.0 (7.5.3, livello 3) chiede un'ulteriore autenticazione con almeno un fattore, o una verifica secondaria, prima delle operazioni altamente sensibili. NIST SP 800-63B-4 (sez. 5.2) usa la riautenticazione per confermare che chi ha la sessione è ancora presente. WCAG 2.2, criterio 3.3.8 Accessible Authentication (Minimum) (AA): nessun test cognitivo (ricordare, trascrivere) in un passo dell'autenticazione senza un'alternativa o un aiuto; il copia-incolla e i gestori di password sono aiuti validi, e l'Understanding porta WebAuthn come metodo senza test cognitivo.

**Soglie ed eccezioni.** In `crm/area/accesso.py` il codice vale 10 minuti (`MINUTI_CODICE`) e la verifica 15 minuti (`MINUTI_VERIFICA`). Il collegamento nell'email dell'area entra una volta sola, entro 7 giorni (`GIORNI` in `crm/area/collegamento.py`).

**In DottorCloud.** `accesso.verificato_da_poco()` è già richiesto per scaricare un documento consegnato online (`download_document` in `crm/documenti/area.py`), per firmare un preventivo nell'area (`accept_in_area` in `crm/preventivi/firma.py`) e per scaricare il PDF di un preventivo con dati sanitari (`area_quote_pdf`). Il codice e la passkey (`crm/area/passkey.py`) segnano la verifica (`segna_verificato`); in anteprima la verifica non si chiede (`anteprima.in_anteprima`). I campi del codice hanno già `autocomplete=one-time-code` e la tastiera numerica (`area/components/CodeDialog.vue`, `area/pages/Login.vue`, `crm/www/documento.html`, `crm/www/modulo.html`): va mantenuto così, senza bloccare l'incolla.

**Come si verifica.** Test del server: senza una verifica recente il download risponde chiedendo il codice; dopo 15 minuti lo chiede di nuovo. Test a mano: incollare il codice copiato dall'email; entrare con una passkey. axe `label` sul campo del codice.

**Errori da evitare.**

- Bloccare l'incolla nel campo del codice: viola WCAG 3.3.8.
- Chiedere la verifica a ogni clic: affatica e fa abbandonare.
- Un collegamento diretto al file privato che salta la verifica.

**Vedi anche.** [WCAG-3.3.8](../../crm/principi/03-wcag-utilizzabile-e-comprensibile.md#wcag-338--entrare-senza-test-di-memoria-incolla-gestore-di-password-link-passkey-338-aa)

**Fonti.**

- [OWASP ASVS 5.0.0 — V7 Session Management](https://github.com/OWASP/ASVS/blob/master/5.0/en/0x16-V7-Session-Management.md) — Requisito 7.5.3 (livello 3) · OWASP Foundation · 2025 (versione 5.0.0, maggio 2025); consultato il 12/10/2026
- [NIST SP 800-63B-4 — Digital Identity Guidelines: Authentication and Authenticator Management](https://pages.nist.gov/800-63-4/sp800-63b.html#sessionreauthn) — Sez. 5.2 Reauthentication · NIST · 2025 (pagina del 26/08/2025), letta dal repository usnistgov/800-63-4 su GitHub il 12/10/2026
- [Web Content Accessibility Guidelines (WCAG) 2.2 — 3.3.8 Accessible Authentication (Minimum)](https://www.w3.org/TR/WCAG22/#accessible-authentication-minimum) — Criterio 3.3.8 (AA): Alternative, Mechanism (gestori di password, copia e incolla) · W3C · 2023 (Raccomandazione W3C); testo letto dal repository w3c/wcag su GitHub il 12/10/2026
- [Understanding SC 3.3.8 Accessible Authentication (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication-minimum.html) — Copy and paste; esempio con WebAuthn · W3C · consultato il 12/10/2026 (sorgente nel repository w3c/wcag su GitHub)

### SAN-SCENARI-CRITICI · Si provano gli scenari critici e si contano gli errori d'uso

**Regola.** Ogni schermata che tocca la sicurezza del paziente o i suoi dati si prova prima del rilascio con utenti rappresentativi: segreteria, professionisti, pazienti. Gli scenari sono realistici e critici: riconoscere la persona giusta, prenotare per un familiare, scrivere e firmare una visita, emettere e inviare una fattura, consegnare un referto, ritirare un consenso. Si contano gli errori d'uso, non solo la soddisfazione.

**Perché.** La NISTIR 7804 (NIST, 2012) descrive un protocollo in tre passi (EUP): analisi dell'applicazione, revisione esperta dell'interfaccia e test di validazione in cui utenti reali svolgono i compiti critici per la sicurezza del paziente individuati nei passi precedenti, condotto da professionisti di usabilità o fattori umani prima del rilascio. La NIST GCR 15-996 (2015) è una guida per chi sviluppa cartelle cliniche elettroniche, con i principi di progettazione dell'interfaccia adattati a quell'ambiente. La IEC 62366-1:2015 (con l'emendamento 1 del 2020) specifica il processo con cui il fabbricante analizza, specifica, sviluppa e valuta l'usabilità di un dispositivo medico in relazione alla sicurezza: valuta e riduce i rischi dell'uso corretto e degli errori d'uso, mentre l'uso anomalo lo identifica soltanto. La ISO 9241-11:2018 definisce l'usabilità come la misura in cui un sistema, prodotto o servizio può essere usato da utenti specifici per raggiungere obiettivi specifici con efficacia, efficienza e soddisfazione in un contesto d'uso specifico, e la tratta come un esito dell'uso, senza prescrivere metodi. La ISO 9241-210:2019 dà requisiti e raccomandazioni per la progettazione centrata sull'utente lungo tutto il ciclo di vita dei sistemi interattivi; la clausola 5 ne elenca i principi: comprensione esplicita di utenti, compiti e ambienti; utenti coinvolti in tutta la progettazione; progetto guidato e affinato dalla valutazione centrata sull'utente; processo iterativo; attenzione all'intera esperienza; gruppo con competenze e prospettive multidisciplinari. La SAFER Guide (revisione 2024, raccomandazione 1.1) chiede test di usabilità anche per le procedure contro i doppioni.

**Soglie ed eccezioni.** Ogni scenario critico passa almeno un giro di test con utenti rappresentativi di ciascun ruolo prima del rilascio. Per scelta di DottorCloud, un errore d'uso che porta alla persona sbagliata o a un dato fuori posto vale gravità 4 sulla scala 0-4 usata dallo studio.

**In DottorCloud.** Lo studio di ottobre 2026 (`/home/frappe/ux/rubrica-ux.md`, rilievi in `/home/frappe/ux/revisione/`) è stato una revisione esperta su schermate catturate: mancano i test con le persone. Scenari tratti dai flussi di DottorCloud:

- l'arrivo in Accoglienza (`pages/Today.vue`);
- la prenotazione per un figlio da /prenota;
- una visita scritta su una scheda con «Inizia dall'ultima visita»;
- la firma di un modulo (`crm/moduli/compilazioni.py`);
- «Emetti» e l'invio allo SdI;
- la consegna online di un referto;
- il ritiro di un consenso dall'area.

**Come si verifica.** Un protocollo scritto per ogni scenario: compito, criterio di successo, errori critici. Un registro degli errori d'uso con la gravità da 0 a 4. Il confronto tra un rilascio e l'altro.

**Errori da evitare.**

- Misurare solo il gradimento.
- Fare le prove con l'utente amministratore, che vede tutto.
- Fare le prove solo sul computer, quando metà del lavoro si fa sul telefono.

**Fonti.**

- [NISTIR 7804 — Technical Evaluation, Testing and Validation of the Usability of Electronic Health Records](https://nvlpubs.nist.gov/nistpubs/ir/2012/NIST.IR.7804.pdf) — Protocollo EUP in tre passi: analisi, revisione esperta, test di validazione (letto via WebSearch) · NIST · 2012; letto via WebSearch il 12/10/2026
- [NIST GCR 15-996 — Technical Basis for User Interface Design of Health IT](https://nvlpubs.nist.gov/nistpubs/gcr/2015/NIST.GCR.15-996.pdf) — Scopo del rapporto: guida per chi sviluppa cartelle elettroniche, con i principi di progettazione dell'interfaccia adattati a quell'ambiente; autori e DOI 10.6028/NIST.GCR.15-996 (letto via WebSearch) · NIST (M. E. Wiklund, J. Kendler, L. Hochberg, M. B. Weinger) · 2015; letto via WebSearch il 12/10/2026
- [IEC 62366-1:2015 — Medical devices — Part 1: Application of usability engineering to medical devices](https://webstore.iec.ch/publication/21863) — Abstract (letto dai metadati del catalogo in relaton-data-iec su GitHub); emendamento IEC 62366-1:2015/AMD1:2020 (https://webstore.iec.ch/publication/59980) · IEC · 2015 (emendamento 2020); consultato il 12/10/2026
- [ISO 9241-11:2018 — Ergonomics of human-system interaction — Part 11: Usability: Definitions and concepts](https://www.iso.org/standard/63500.html) — Abstract (letto dai metadati del catalogo in relaton-data-iso su GitHub); definizione di usabilità (letta via WebSearch) · ISO · 2018; consultato il 12/10/2026
- [ISO 9241-210:2019 — Ergonomics of human-system interaction — Part 210: Human-centred design for interactive systems](https://www.iso.org/standard/77520.html) — Abstract (letto dai metadati del catalogo in relaton-data-iso su GitHub); clausola 5, principi 5.2–5.7 (letta via WebSearch) · ISO · 2019; consultato il 12/10/2026
- [Appendix C. 2024 Patient Identification SAFER Guide (materiale supplementare di «Developing updated and new guidance to promote reliable patient identification»)](https://pmc-oa-opendata.s3.amazonaws.com/PMC12772641.1/ooaf160_supplementary_data.docx) — Recommended Practice 1.1, Implementation Guidance (test di usabilità) · JAMIA Open (Oxford University Press), dal dataset Open Access di PubMed Central · 2026; letto il 12/10/2026

### REG-DISPOSITIVO-MEDICO · Prima di una funzione che interpreta i dati di un paziente, si valuta se è un dispositivo medico

**Regola.** Le funzioni amministrative e di comunicazione di DottorCloud non hanno uno scopo medico. Prima di rilasciare una funzione che calcola, interpreta o suggerisce qualcosa per un singolo paziente a fini medici, si fa e si mette per iscritto la valutazione della qualificazione secondo le linee guida MDCG 2019-11. Esempi: punteggi con fasce, calcoli nutrizionali per un piano, riepiloghi clinici, segnalazioni. Testi, schermate e materiali non promettono diagnosi né terapie.

**Perché.** Le linee guida MDCG 2019-11 (2019) dicono che il software destinato solo a scopi non medici, come fatturazione, pianificazione del personale, email, messaggistica, analisi di dati, elaborazione testi, backup o app di benessere, non è software dispositivo medico; che i sistemi informativi ospedalieri, fatti per accettazione, appuntamenti, assicurazioni e fatturazione, non sono in sé dispositivi medici, ma possono avere moduli che lo sono; che il software che elabora, analizza, crea o modifica informazioni mediche può esserlo se lo fa per uno scopo medico. Il passo 3 del loro albero decisionale chiede se il software compie sui dati un'azione diversa da archiviazione, comunicazione, ricerca semplice o compressione senza perdita: se sì, può essere un dispositivo e si passa al passo 4; la ricerca semplice è recuperare record confrontando i loro metadati con criteri di ricerca, come in una biblioteca. A giugno 2025 il Medical Device Coordination Group ne ha pubblicato la revisione 1, che va letta prima di decidere. Se una funzione risulta un dispositivo, la IEC 62366-1 è il processo di riferimento per l'ingegneria dell'usabilità legata alla sicurezza. E se una funzione con l'IA fosse un dispositivo medico soggetto alla valutazione di un organismo terzo, l'AI Act la tratterebbe come sistema ad alto rischio (art. 6, par. 1), con gli obblighi del capo III dal 2 agosto 2028 (art. 113, come modificato dal Regolamento (UE) 2026/1744).

**In DottorCloud.** Agenda, accoglienza, fatturazione, conversazioni, area e archivio dei documenti rientrano negli esempi di scopi non medici o nei sistemi che archiviano e comunicano. La regola c'è già nel progetto: «Ogni funzione nuova passa la verifica delle linee guida MDCG 2019-11, messa per iscritto» (`docs/verticali/clinica/design.md`, «L'assistente»), e il dispositivo medico è la prima domanda per il legale (`docs/marchi/dottorcloud/legale/README.md`). Vanno valutati uno per uno, prima del rilascio:

- gli andamenti dei punteggi con le loro fasce (`crm/moduli/andamenti.py`, `Moduli/ScoreTrends.vue`);
- i nutrienti e gli obiettivi del menu (`crm/clinica/menu.py`);
- il riepilogo dell'assistente (`crm/clinica/riassunto.py`) e la visita dettata (`crm/clinica/dettatura.py`);
- la cartella odontoiatrica (`crm/clinica/cure.py`).

La valutazione si scrive in `docs/verticali/clinica/`. I testi delle schermate restano quelli del «supporto alla documentazione» (`SCOPO` in `crm/assistente/regole.py`).

**Come si verifica.** Una scheda di qualificazione per ogni nuova funzione del verticale clinico: scopo dichiarato, passo dell'albero MDCG, conclusione, chi l'ha decisa. Rivedere i testi di marketing (`siti/dottorcloud/`) in cerca di promesse cliniche.

**Errori da evitare.**

- Concludere che «un gestionale non è mai un dispositivo»: dipende dallo scopo dichiarato di ogni modulo.
- Un testo di marketing che promette «diagnosi più accurate».
- Aggiungere a un punteggio una soglia d'allarme clinica senza valutazione.

**Fonti.**

- [MDCG 2019-11 — Guidance on Qualification and Classification of Software in Regulation (EU) 2017/745 – MDR and Regulation (EU) 2017/746 – IVDR](https://health.ec.europa.eu/system/files/2020-09/md_mdcg_2019_11_guidance_en_0.pdf) — Software per soli scopi non medici; sistemi informativi ospedalieri e moduli; passo 3 dell'albero decisionale; «simple search» (letto via WebSearch) · Medical Device Coordination Group, Commissione europea · 2019; letto via WebSearch il 12/10/2026
- [MDCG 2019-11 rev.1 — Qualification and classification of software - Regulation (EU) 2017/745 and Regulation (EU) 2017/746](https://health.ec.europa.eu/document/download/b45335c5-1679-4c71-a91c-fc7a4d37f12b_en?filename=mdcg_2019_11_en.pdf) — Revisione 1 del giugno 2025 (esistenza e data lette via WebSearch; il testo della revisione non si è potuto aprire) · Medical Device Coordination Group, Commissione europea · 2025; letto via WebSearch il 12/10/2026
- [IEC 62366-1:2015 — Medical devices — Part 1: Application of usability engineering to medical devices](https://webstore.iec.ch/publication/21863) — Abstract (letto dai metadati del catalogo in relaton-data-iec su GitHub) · IEC · 2015; consultato il 12/10/2026
- [Regolamento (UE) 2024/1689 (AI Act)](https://eur-lex.europa.eu/eli/reg/2024/1689/oj) — Art. 6, par. 1; art. 113 come modificato (testo letto dalla copia superuserkalo/eu-ai-act su GitHub, generata dai documenti dell'Ufficio delle pubblicazioni CELEX 32024R1689 e 32026R1744) · Unione europea (Gazzetta ufficiale) · 2024; consultato il 12/10/2026
