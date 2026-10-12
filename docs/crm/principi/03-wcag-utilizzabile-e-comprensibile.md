# 3. Utilizzabile e comprensibile: WCAG 2.2 e tastiera

<!-- Copyright (c) 2026, NPM2 Solutions Srl and contributors -->

Una delle famiglie dei [principi di esperienza e interfaccia](../66-principi-di-esperienza.md) (doc 66): come leggerle, la lista di controllo per una schermata e come sono state verificate le fonti sono lì.

Questa famiglia raccoglie tutti i criteri di successo A e AA dei principi 2 (Utilizzabile) e 3 (Comprensibile) delle WCAG 2.2, quattro obiettivi AAA che DottorCloud adotta (2.2.5, 2.3.3, 2.4.13, 2.5.5; 2.4.12 sta accanto a 2.4.11), il contrasto 3:1 dell'indicatore di focus (1.4.11) e i modelli di tastiera delle WAI-ARIA Authoring Practices per i componenti che l'app usa. Per ciascuno: il testo normativo in parole nostre, le eccezioni, l'intento dell'Understanding, le tecniche e i fallimenti che contano, i punti del codice di DottorCloud dove si applica e come verificarlo. Conta perché la segreteria lavora da tastiera al banco, i professionisti con il dito sul tablet e i pazienti sul telefono in /area, /prenota e /modulo, e molte azioni hanno effetti legali, fiscali o sanitari (fatture allo SdI, firme, pagamenti, consensi) che una svista non deve produrre. Gli errori già trovati sono citati come (studio UX, ottobre 2026), (revisione del codice, ottobre 2026) o (rilevato nel codice, con la data), distinti dalle regole; «corretto» dice che è stato sistemato. Le fonti W3C sono citate dai file sorgente dei repository in cui il W3C sviluppa WCAG 2, l'Understanding e le Techniques (w3c/wcag) e le Authoring Practices (w3c/aria-practices, pubblicate in w3.org/WAI/ARIA/apg), fissati a un commit, perché www.w3.org non era raggiungibile durante la ricerca; le tecniche di ogni criterio vengono da understanding.11tydata.js, i dati da cui l'Understanding genera l'elenco. Le regole di axe-core citate sono quelle della versione 4.10.3 usata nello studio.

## I principi

- [WCAG-2.1.1 · Tutto si fa con la tastiera (2.1.1, A)](#wcag-211--tutto-si-fa-con-la-tastiera-211-a)
- [WCAG-2.1.2 · Nessuna trappola per la tastiera (2.1.2, A)](#wcag-212--nessuna-trappola-per-la-tastiera-212-a)
- [WCAG-2.1.4 · Scorciatoie da un solo carattere (2.1.4, A)](#wcag-214--scorciatoie-da-un-solo-carattere-214-a)
- [WCAG-2.2.1 · Tempi regolabili: toast, sessioni, codici, posti tenuti (2.2.1, A)](#wcag-221--tempi-regolabili-toast-sessioni-codici-posti-tenuti-221-a)
- [WCAG-2.2.2 · Pausa, stop, nascondi per ciò che si muove o si aggiorna (2.2.2, A)](#wcag-222--pausa-stop-nascondi-per-ciò-che-si-muove-o-si-aggiorna-222-a)
- [WCAG-2.2.5 · Dopo un nuovo accesso non si perde nulla (2.2.5, AAA, obiettivo)](#wcag-225--dopo-un-nuovo-accesso-non-si-perde-nulla-225-aaa-obiettivo)
- [WCAG-2.3.1 · Non più di tre lampeggiamenti al secondo (2.3.1, A)](#wcag-231--non-più-di-tre-lampeggiamenti-al-secondo-231-a)
- [WCAG-2.3.3 · Le animazioni causate da un gesto si possono spegnere (2.3.3, AAA, obiettivo)](#wcag-233--le-animazioni-causate-da-un-gesto-si-possono-spegnere-233-aaa-obiettivo)
- [WCAG-2.4.1 · Saltare i blocchi ripetuti: «Vai al contenuto» e regioni (2.4.1, A)](#wcag-241--saltare-i-blocchi-ripetuti-vai-al-contenuto-e-regioni-241-a)
- [WCAG-2.4.2 · Ogni pagina ha un titolo che dice dove si è (2.4.2, A)](#wcag-242--ogni-pagina-ha-un-titolo-che-dice-dove-si-è-242-a)
- [WCAG-2.4.3 · Il focus segue un ordine che conserva il senso (2.4.3, A)](#wcag-243--il-focus-segue-un-ordine-che-conserva-il-senso-243-a)
- [WCAG-2.4.4 · Lo scopo di ogni link si capisce dal testo o dal suo contesto (2.4.4, A)](#wcag-244--lo-scopo-di-ogni-link-si-capisce-dal-testo-o-dal-suo-contesto-244-a)
- [WCAG-2.4.5 · Più di un modo per trovare una pagina (2.4.5, AA)](#wcag-245--più-di-un-modo-per-trovare-una-pagina-245-aa)
- [WCAG-2.4.6 · Intestazioni ed etichette dicono che cosa c'è e che cosa scrivere (2.4.6, AA)](#wcag-246--intestazioni-ed-etichette-dicono-che-cosa-cè-e-che-cosa-scrivere-246-aa)
- [WCAG-2.4.7 · Il focus da tastiera si vede sempre (2.4.7, AA) e :focus-visible](#wcag-247--il-focus-da-tastiera-si-vede-sempre-247-aa-e-focus-visible)
- [FOCUS-1.4.11 · L'indicatore di focus contrasta almeno 3:1 con ciò che ha accanto (1.4.11, AA)](#focus-1411--lindicatore-di-focus-contrasta-almeno-31-con-ciò-che-ha-accanto-1411-aa)
- [WCAG-2.4.11 · Il focus non resta nascosto sotto barre, pulsanti fissi, toast o tastiera (2.4.11, AA; 2.4.12, AAA)](#wcag-2411--il-focus-non-resta-nascosto-sotto-barre-pulsanti-fissi-toast-o-tastiera-2411-aa-2412-aaa)
- [WCAG-2.4.13 · Aspetto del focus: area e cambio di contrasto (2.4.13, AAA, obiettivo)](#wcag-2413--aspetto-del-focus-area-e-cambio-di-contrasto-2413-aaa-obiettivo)
- [WCAG-2.5.1 · Ogni gesto ha un'alternativa a un solo tocco (2.5.1, A)](#wcag-251--ogni-gesto-ha-unalternativa-a-un-solo-tocco-251-a)
- [WCAG-2.5.2 · Un tocco si può annullare prima di sollevare il dito (2.5.2, A)](#wcag-252--un-tocco-si-può-annullare-prima-di-sollevare-il-dito-252-a)
- [WCAG-2.5.3 · Il nome accessibile contiene le parole che si vedono (2.5.3, A)](#wcag-253--il-nome-accessibile-contiene-le-parole-che-si-vedono-253-a)
- [WCAG-2.5.4 · Nessuna funzione solo scuotendo o inclinando il telefono (2.5.4, A)](#wcag-254--nessuna-funzione-solo-scuotendo-o-inclinando-il-telefono-254-a)
- [WCAG-2.5.7 · Ogni trascinamento ha un'alternativa senza trascinare (2.5.7, AA)](#wcag-257--ogni-trascinamento-ha-unalternativa-senza-trascinare-257-aa)
- [WCAG-2.5.8 · Bersagli di almeno 24×24 px o ben distanziati (2.5.8, AA)](#wcag-258--bersagli-di-almeno-2424-px-o-ben-distanziati-258-aa)
- [WCAG-2.5.5 · Al tocco 44×44 px: la regola di DottorCloud sopra il minimo (2.5.5, AAA, obiettivo)](#wcag-255--al-tocco-4444-px-la-regola-di-dottorcloud-sopra-il-minimo-255-aaa-obiettivo)
- [WCAG-3.1.1 · La lingua della pagina è dichiarata e giusta (3.1.1, A)](#wcag-311--la-lingua-della-pagina-è-dichiarata-e-giusta-311-a)
- [WCAG-3.1.2 · Le parti in un'altra lingua sono marcate; le parole inglesi rimaste si traducono (3.1.2, AA)](#wcag-312--le-parti-in-unaltra-lingua-sono-marcate-le-parole-inglesi-rimaste-si-traducono-312-aa)
- [WCAG-3.2.1 · Il focus da solo non cambia il contesto (3.2.1, A)](#wcag-321--il-focus-da-solo-non-cambia-il-contesto-321-a)
- [WCAG-3.2.2 · Cambiare un valore non porta altrove senza avvisare (3.2.2, A)](#wcag-322--cambiare-un-valore-non-porta-altrove-senza-avvisare-322-a)
- [WCAG-3.2.3 · La navigazione sta sempre nello stesso ordine e la voce attiva si vede (3.2.3, AA)](#wcag-323--la-navigazione-sta-sempre-nello-stesso-ordine-e-la-voce-attiva-si-vede-323-aa)
- [WCAG-3.2.4 · Stessa funzione, stesso nome e stessa icona (3.2.4, AA)](#wcag-324--stessa-funzione-stesso-nome-e-stessa-icona-324-aa)
- [WCAG-3.2.6 · L'aiuto sta sempre nello stesso posto (3.2.6, A)](#wcag-326--laiuto-sta-sempre-nello-stesso-posto-326-a)
- [WCAG-3.3.1 · Un errore dice in parole quale campo e che cosa non va (3.3.1, A)](#wcag-331--un-errore-dice-in-parole-quale-campo-e-che-cosa-non-va-331-a)
- [WCAG-3.3.2 · Ogni campo ha un'etichetta visibile e le istruzioni che servono (3.3.2, A)](#wcag-332--ogni-campo-ha-unetichetta-visibile-e-le-istruzioni-che-servono-332-a)
- [WCAG-3.3.3 · L'errore dice come correggerlo (3.3.3, AA)](#wcag-333--lerrore-dice-come-correggerlo-333-aa)
- [WCAG-3.3.4 · Fatture, firme, pagamenti, consensi ed eliminazioni: annullabili, controllati o confermati (3.3.4, AA)](#wcag-334--fatture-firme-pagamenti-consensi-ed-eliminazioni-annullabili-controllati-o-confermati-334-aa)
- [WCAG-3.3.7 · Non si chiede due volte ciò che il sistema sa già (3.3.7, A)](#wcag-337--non-si-chiede-due-volte-ciò-che-il-sistema-sa-già-337-a)
- [WCAG-3.3.8 · Entrare senza test di memoria: incolla, gestore di password, link, passkey (3.3.8, AA)](#wcag-338--entrare-senza-test-di-memoria-incolla-gestore-di-password-link-passkey-338-aa)
- [APG-TASTIERA · Tab tra i componenti, frecce dentro; focus mai perso; barre di strumenti](#apg-tastiera--tab-tra-i-componenti-frecce-dentro-focus-mai-perso-barre-di-strumenti)
- [APG-DIALOG · Finestre modali e richieste di conferma (dialog e alertdialog)](#apg-dialog--finestre-modali-e-richieste-di-conferma-dialog-e-alertdialog)
- [APG-TABS · Schede di un record (tablist)](#apg-tabs--schede-di-un-record-tablist)
- [APG-RADIO · Gruppi di radio e controlli a segmenti, mai per navigare tra pagine](#apg-radio--gruppi-di-radio-e-controlli-a-segmenti-mai-per-navigare-tra-pagine)
- [APG-MENU · Pulsanti «⋯» e menu di azioni](#apg-menu--pulsanti--e-menu-di-azioni)
- [APG-COMBOBOX · Cercare e scegliere una persona, un servizio, un professionista (combobox e listbox)](#apg-combobox--cercare-e-scegliere-una-persona-un-servizio-un-professionista-combobox-e-listbox)
- [APG-DISCLOSURE · Sezioni che si aprono e si chiudono (disclosure e fisarmonica)](#apg-disclosure--sezioni-che-si-aprono-e-si-chiudono-disclosure-e-fisarmonica)
- [APG-SWITCH · Interruttori che dicono che cosa accendono](#apg-switch--interruttori-che-dicono-che-cosa-accendono)
- [APG-TABELLA · Liste come tabelle, griglie solo dove servono, ordinamento annunciato](#apg-tabella--liste-come-tabelle-griglie-solo-dove-servono-ordinamento-annunciato)

### WCAG-2.1.1 · Tutto si fa con la tastiera (2.1.1, A)

**Regola.** Ogni funzione si usa da tastiera, senza tempi richiesti tra un tasto e l'altro. Fa eccezione solo la funzione che dipende dal percorso del movimento (il tratto della firma, il disegno a mano libera sul corpo), non i comandi attorno ad essa. Non serve che ogni controllo visibile sia raggiungibile da tastiera, ma ogni azione deve avere un modo da tastiera per ottenere lo stesso risultato.

**Perché.** La segreteria al banco lavora con la tastiera; chi non vede, chi ha un tremore e chi usa programmi vocali, sensori a soffio, tastiere a schermo o software a scansione passa dalla tastiera o da un suo emulatore (Understanding, Intent). L'Understanding precisa che MouseKeys non vale come equivalente, perché emula il mouse; che il disegno a mano libera è l'eccezione, mentre trascinare un oggetto in un punto quando il percorso non conta non lo è; che non serve rendere focalizzabile ogni controllo visibile, basta un modo comparabile da tastiera; che seguire le convenzioni della piattaforma è consigliato, non obbligatorio.

**Soglie ed eccezioni.** Livello A. Nessun tempo minimo tra i tasti né tasti da tenere premuti a lungo. Sufficienti: G202; H91 (controlli HTML nativi); G90 con SCR20, SCR35, SCR2. Consigliata: SCR29. Fallimenti: F54 (solo gestori di eventi del puntatore), F55 (focus tolto via script appena arriva), F42 (link emulati).

**In DottorCloud.** Usare elementi nativi (button, a href, input, select). Una riga che apre qualcosa e non contiene altri controlli usa vRigaCliccabile (utils/rigaCliccabile.js: role=button, tabindex=0, Invio e Spazio solo se il tasto è premuto sulla riga stessa, tastoDellaRiga); una riga che contiene altri comandi si apre dal pulsante steso .riga-stesa (index.css, ::after con inset 0), con i suoi comandi dopo, sopra di esso. Ogni @click su div o span ha un'alternativa da tastiera. L'agenda offre «Nuovo», Ctrl/⌘+E e il pannello dove si cambiano data e orari al posto del trascinamento. La firma e il tratto sul corpo restano l'eccezione; i punti sul corpo, le intensità e i pulsanti attorno (cancella, conferma, le altre vie per firmare) si usano da tastiera.

**Come si verifica.** Percorrere con Tab, Shift+Tab, Invio, Spazio, frecce ed Esc i flussi interi: prenotazione online, fattura dall'appuntamento, firma di un modulo, ogni pagina delle Impostazioni. axe copre solo casi stretti di 2.1.1 (scrollable-region-focusable, frame-focusable-content, server-side-image-map); nested-interactive, mappata su 4.1.2, segnala controlli dentro controlli. Cercare nel codice @click su div o span senza tabindex né ruolo.

**Errori da evitare.** Righe delle Impostazioni come div @click in nove liste (turni, ambulatori, pipeline, modelli email, regole di assegnazione, tempi di risposta, piattaforme, fatturazione, link tracciati); in Turni del team non c'era altra via, perché «Imposta gli orari» escludeva chi aveva già orari propri (studio UX, ottobre 2026; corretto con utils/rigaCliccabile.js). Righe di RecordList.vue e TrackedLinksSettings.vue come div @click (studio UX, ottobre 2026). Tema scelto da tre riquadri che il Tab non raggiungeva (studio UX, ottobre 2026; ora radio native in ThemeSwitcher.vue). Righe dei documenti come div role=button con dentro «Apri», «Trasmetti», «Comunica»: 200 nodi nested-interactive (studio UX, ottobre 2026). La prima direttiva aveva fatto pulsanti di righe che contenevano «Sincronizza» ed «Elimina» (revisione del codice, ottobre 2026), da qui .riga-stesa. CollapsibleSection.vue: intestazione div @click senza tabindex, ruolo né aria-expanded (rilevato nel codice l'11/10/2026, ancora così il 12/10/2026).

**Fonti.**

- [Success Criterion 2.1.1 Keyboard (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#keyboard) — Criterio 2.1.1, livello A: testo normativo e note · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/20/keyboard.html))
- [Understanding Keyboard](https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html) — sezioni Intent of Keyboard (MouseKeys, percorso, convenzioni della piattaforma) ed Examples of Keyboard · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/20/keyboard.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'keyboard', righe 593-615 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-2.1.2 · Nessuna trappola per la tastiera (2.1.2, A)

**Regola.** Se il focus entra in un componente con la tastiera, ne esce con la tastiera; se per uscire servono tasti diversi da frecce, Tab o altri metodi standard (di solito Esc), l'utente è avvisato di come si esce.

**Perché.** Chi usa solo la tastiera, intrappolato, deve ricaricare la pagina e perde ciò che ha scritto. Il criterio vale per tutta la pagina (requisito di conformità 5, non interferenza): una trappola rende non conforme la pagina anche se il componente non serve alla conformità. L'Understanding accetta la finestra modale che tiene il focus dentro, purché l'utente sappia come uscirne; con una tastiera fisica indica Esc come un metodo di uscita standard di uso comune; porta l'esempio dell'editor che usa Tab per indentare e, quando riceve il focus, dice che Alt+F10 (Option+F10) riporta alla barra degli strumenti.

**Soglie ed eccezioni.** Livello A. Sufficiente: G21. Fallimento: F10 (formati di contenuto combinati in modo da intrappolare l'utente in uno di essi).

**In DottorCloud.** Il Dialog di frappe-ui (DialogContent di reka-ui, con FocusScope) tiene il focus dentro di proposito: la conformità sta in Esc e in un pulsante visibile per chiudere. Un editor che usa Tab per indentare deve dire come si esce. Gli iframe (l'anteprima di un'email) restano attraversabili. useKeyboardShortcuts (composables/useKeyboardShortcuts.js) ignora chi sta scrivendo e le finestre aperte: nessuna scorciatoia deve prendersi Tab.

**Come si verifica.** Entrare con Tab in ogni finestra, foglio, editor, menu, iframe e nella griglia dell'agenda e uscirne con Tab, Shift+Tab o Esc. Nessuno strumento automatico lo rileva.

**Errori da evitare.** Sul computer le Impostazioni non avevano la X: si usciva solo con Esc o con un clic sullo sfondo, che alcune pagine disattivano (disableOutsideClickToClose in Settings.vue) (studio UX, ottobre 2026; ora c'è il pulsante per chiudere).

**Fonti.**

- [Success Criterion 2.1.2 No Keyboard Trap (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#no-keyboard-trap) — Criterio 2.1.2, livello A, e nota sul requisito di conformità 5 (non interferenza) · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/20/no-keyboard-trap.html))
- [Understanding No Keyboard Trap](https://www.w3.org/WAI/WCAG22/Understanding/no-keyboard-trap.html) — sezioni Intent of No Keyboard Trap ed Examples (A modal dialog box; A WYSIWYG rich text editor) · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/20/no-keyboard-trap.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'no-keyboard-trap', righe 617-621 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-2.1.4 · Scorciatoie da un solo carattere (2.1.4, A)

**Regola.** Una scorciatoia fatta solo di lettere, numeri, punteggiatura o simboli si può spegnere, si può rimappare aggiungendo un tasto non stampabile (Ctrl, Alt) oppure è attiva solo quando il suo componente ha il focus. Le scorciatoie con un modificatore non coprono quelle del sistema, del browser e delle tecnologie assistive.

**Perché.** Chi usa la tastiera può premere un carattere per sbaglio, e alcuni programmi di comando vocale che non distinguono la dettatura dai comandi (l'Understanding cita Talon Voice) trasformano le parole in pressioni di tasti: una scorciatoia da un carattere scatta senza volerlo. Contano anche le sequenze (G poi A); sono esclusi listbox e menu a discesa, attivi solo con il focus, e le access key, che usano un modificatore (Understanding, Intent).

**Soglie ed eccezioni.** Livello A. Sufficiente: G217; fallimento: F99. Authoring Practices: evitare Caps Lock, Insert, Scroll Lock e, su macOS, Control+Option con qualunque altro tasto (sono delle tecnologie assistive); evitare le scorciatoie del browser per barra degli indirizzi, barra delle notifiche, ricarica, preferiti e cronologia, ricerca; a livello di sistema evitare un modificatore con Tab, Invio, Spazio o Esc e il tasto Meta (⌘ o Windows) con un singolo tasto. Apple elenca ⌘E «Use the selection for a find operation» tra le scorciatoie standard di macOS e chiede di non riusarle per azioni proprie.

**In DottorCloud.** DottorCloud usa solo combinazioni con un modificatore: Ctrl/⌘+E nuovo appuntamento (pages/Calendar.vue), Ctrl/⌘+D duplica nel pannello di un evento (Calendar/CalendarEventPanel.vue), Ctrl/⌘+S salva (Settings/Profile/ProfileSettings.vue, Settings/PreferencesSettings.vue, pages/AutomationEditor.vue). Esc, Invio e Canc/Backspace del pannello di un evento sono tasti non stampabili, fuori da 2.1.4: useKeyboardShortcuts li ascolta su window finché il pannello è aperto e li ignora mentre si scrive o con una finestra aperta; Canc chiede conferma (deleteEvent in pages/Calendar.vue). Nessuna nuova scorciatoia globale da un carattere; se servisse (j/k nelle liste), un interruttore in Preferenze e la rimappatura. Ogni scorciatoia è anche un pulsante visibile.

**Come si verifica.** Elencare i listener (useKeyboardShortcuts, @keydown, addEventListener('keydown')). Con il focus sul corpo della pagina premere lettere e numeri: non deve succedere nulla. Provare con Controllo vocale (macOS, iOS) e Accesso vocale (Android).

**Errori da evitare.** Ctrl/⌘+E sull'agenda e Ctrl/⌘+D nel pannello chiamano preventDefault (useKeyboardShortcuts): su macOS ⌘E toglie «usa la selezione per cercare», una scorciatoia standard (Apple, Keyboards); prima di aggiungerne altre verificarle contro le scorciatoie dei browser in uso, che le Authoring Practices chiedono di non coprire (rilevato nel codice il 12/10/2026).

**Fonti.**

- [Success Criterion 2.1.4 Character Key Shortcuts (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#character-key-shortcuts) — Criterio 2.1.4, livello A: Turn off, Remap, Active only on focus · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/21/character-key-shortcuts.html))
- [Understanding Character Key Shortcuts](https://www.w3.org/WAI/WCAG22/Understanding/character-key-shortcuts.html) — sezioni Intent e Background on the mechanics of speech input; Examples · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/21/character-key-shortcuts.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'character-key-shortcuts', righe 635-639 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026
- [Developing a Keyboard Interface](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/) — sezione Keyboard Shortcuts > Assigning Keyboard Shortcuts: Operating System Key Conflicts, Assistive Technology Key Conflicts, Browser Key Conflicts · W3C WAI – Authoring Practices Task Force dell'ARIA Working Group · sorgente al commit 0f765e4 del 29/09/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/aria-practices/blob/0f765e4dc33e966026114ac12a8380db1de3b787/content/practices/keyboard-interface/keyboard-interface-practice.html))
- [Accessibility (Human Interface Guidelines), dati della pagina](https://developer.apple.com/design/human-interface-guidelines/accessibility) — sezione Speech: «Avoid overriding system-defined keyboard shortcuts» (pagina developer.apple.com/design/human-interface-guidelines/accessibility) · Apple · pagina aggiornata il 09/06/2025 (registro delle modifiche); consultata il 12/10/2026 ([sorgente letto](https://developer.apple.com/tutorials/data/design/human-interface-guidelines/accessibility.json))
- [Keyboards (Human Interface Guidelines), dati della pagina](https://developer.apple.com/design/human-interface-guidelines/keyboards) — Best practices: «Respect standard keyboard shortcuts»; Standard keyboard shortcuts: «Command-E Use the selection for a find operation» (pagina developer.apple.com/design/human-interface-guidelines/keyboards) · Apple · pagina aggiornata il 09/06/2025 (registro delle modifiche); consultata il 12/10/2026 ([sorgente letto](https://developer.apple.com/tutorials/data/design/human-interface-guidelines/keyboards.json))

### WCAG-2.2.1 · Tempi regolabili: toast, sessioni, codici, posti tenuti (2.2.1, A)

**Regola.** Per ogni limite di tempo posto dal contenuto vale almeno una: si può spegnere prima di incontrarlo; si può regolare prima, fino ad almeno dieci volte il valore predefinito; oppure si è avvisati prima della scadenza e si hanno almeno 20 secondi per prolungarlo con un gesto semplice, almeno dieci volte. Eccezioni: evento in tempo reale senza alternative, limite essenziale, limite oltre le 20 ore. Un messaggio che sparisce da solo è un limite di tempo, salvo che la stessa informazione resti disponibile altrove.

**Perché.** Chi non vede, vede poco, ha difficoltà motorie o cognitive può aver bisogno di più tempo per leggere e agire (Understanding, Intent). L'Understanding conta come limite ogni processo che avviene da solo dopo un tempo, anche un contenuto che cambia o sparisce, e porta l'esempio del toast che sparisce dopo 5 secondi: va bene solo perché la nuova email si ritrova nella casella. Tratta i limiti messi per sicurezza come posti dal contenuto e ammette che alcuni, come i codici a tempo a due fattori, possano essere considerati essenziali; nell'esempio del biglietto tenuto due minuti il sito sposta fuori dalla fase a tempo tutto ciò che può (nome, modalità di pagamento). Dieci volte e 20 secondi vengono dall'esperienza clinica; 20 ore superano una giornata da svegli.

**Soglie ed eccezioni.** Livello A. Avviso con almeno 20 s per prolungare, almeno 10 prolungamenti, regolazione fino a 10 volte, limiti oltre 20 ore esclusi. Sufficienti: G133, G198 (limiti di sessione); G198, G180, SCR16 con SCR1 (limite gestito da uno script); G4, G198, SCR33, SCR36 (tempi di lettura). Fallimenti: F40, F41, F58. Valori nel codice: TOAST_LIFETIME 4000 ms in vue-sonner 2.0.9 e nessuna durata propria nel ToastProvider di frappe-ui, quindi ogni toast dura 4 s; UNDO = 7000 ms in CommunicationArea.vue (il cestino accanto a Invia); MINUTI_CODICE 10, TENTATIVI 5 e MINUTI_VERIFICA 15 in crm/area/accesso.py; MINUTI_ACCONTO 30 in crm/pagamenti/regole.py.

**In DottorCloud.** Un toast che porta un'azione (Annulla) o un'informazione che non si ritrova altrove resta finché non si chiude (duration: Infinity, come suggerisce la documentazione del Toast di frappe-ui per i messaggi che aspettano una decisione) oppure la stessa cosa resta disponibile in un altro posto (il pannello delle notifiche, una riga da cui si riapre). Un errore non vive solo in un toast. Il codice dell'area scade per sicurezza: «Mandalo di nuovo» e «Un altro indirizzo» (area/pages/Login.vue) ne chiedono un altro senza perdere nulla. Su /prenota nome e recapiti si scrivono prima che il posto venga tenuto e la scadenza si dice in parole («Il posto è tenuto per 30 minuti: paga … per confermare la prenotazione.»): è il modello dell'Understanding.

**Come si verifica.** Cercare setTimeout che nascondono o cambiano contenuto, i toast con un'azione, le scadenze di sessione, codice e pagamento; per ognuno chiedersi se si spegne, si allunga o si ritrova altrove. Leggere ogni messaggio con uno screen reader e vedere se resta.

**Errori da evitare.** Una cosa da fare segnata fatta per sbaglio si recupera solo con «Annulla» nel toast, che sparisce dopo pochi secondi (ElencoCose.vue, fatta()); sul telefono la lista mostra solo le cose aperte e non c'è altro modo di riaprirla (studio UX, ottobre 2026). Da tastiera l'«Annulla» di un toast si raggiunge con Tab solo dopo tutta la pagina (FrappeUIProvider mette ToastProvider dopo l'app) o con Alt+T, la scorciatoia di vue-sonner che apre la pila e ferma il tempo: nessuna delle due è detta (rilevato nel codice il 12/10/2026). I campi obbligatori mancanti sono detti solo in un toast da checkMandatory in data/document.js (rilevato nel codice l'11/10/2026).

**Vedi anche.** [SAN-SESSIONE-CONDIVISA](08-persone-e-dati-personali.md#san-sessione-condivisa--sessioni-adatte-a-un-pc-di-segreteria-condiviso)

**Fonti.**

- [Success Criterion 2.2.1 Timing Adjustable (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#timing-adjustable) — Criterio 2.2.1, livello A: Turn off, Adjust, Extend; eccezioni Real-time, Essential, 20 Hour · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/20/timing-adjustable.html))
- [Understanding Timing Adjustable](https://www.w3.org/WAI/WCAG22/Understanding/timing-adjustable.html) — Intent of Timing Adjustable (toast di 5 secondi); Notes regarding time limits (limiti di sicurezza, dieci volte, 20 secondi, 20 ore); Examples (acquisto di biglietti) · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/20/timing-adjustable.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'timing-adjustable', righe 641-658 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-2.2.2 · Pausa, stop, nascondi per ciò che si muove o si aggiorna (2.2.2, A)

**Regola.** Ciò che si muove, lampeggia o scorre partendo da solo, dura più di 5 secondi e sta accanto ad altro contenuto ha un modo per metterlo in pausa, fermarlo o nasconderlo; ciò che si aggiorna da solo accanto ad altro contenuto ha un modo per metterlo in pausa, fermarlo, nasconderlo o sceglierne la frequenza. Salvo che sia essenziale.

**Perché.** Il movimento distrae, in particolare chi ha disturbi dell'attenzione, ostacola chi legge lentamente o fatica a seguire ciò che si muove e crea problemi agli screen reader (Understanding, Intent). Cinque secondi bastano ad attirare l'attenzione e si possono aspettare; gli aggiornamenti automatici non hanno questa eccezione. Un'animazione di caricamento che è l'unico contenuto della pagina non chiede comandi; fermare un'animazione solo finché il focus ci sta sopra non vale come pausa.

**Soglie ed eccezioni.** Livello A, per tutta la pagina (requisito di conformità 5). 5 secondi per movimento, lampeggio e scorrimento; nessuna soglia per l'aggiornamento automatico. Sufficienti: G4, SCR33, G11, G152, SCR22, G186, G191. Fallimenti: F16, F112, F50, F7.

**In DottorCloud.** LoaderMark (dc-respiro, 1,2 s all'infinito, espresso-componenti.css) è un indicatore di caricamento e si ferma con prefers-reduced-motion: non lasciarlo girare per più di 5 secondi accanto a contenuto da leggere. Gli anelli .pulse di Telephony/TwilioCallUI.vue (1 s all'infinito) e animate-pulse sul pulsante «Accetta» durano finché una chiamata in arrivo squilla, accanto ai comandi: fermarli dopo pochi cicli e lasciare ferme un'icona e una parola. Le liste che si aggiornano dal socket (conversazioni, attività, notifiche) non spostano le righe sotto il dito o il cursore: «3 nuovi messaggi, mostra» oppure inserimento sopra senza spostare la vista.

**Come si verifica.** Inventario delle animazioni infinite e delle transizioni lunghe (cercare 'infinite' nei CSS e nei componenti); aprire una pagina che si aggiorna da sola e verificare che ciò che si legge non si sposti; ripetere con la riduzione del movimento attiva. axe copre solo blink e marquee.

**Errori da evitare.** .pulse in TwilioCallUI.vue senza fine, per tutto lo squillo di una chiamata in arrivo, e senza prefers-reduced-motion fino alla correzione del 12/10/2026 (rilevato nel codice l'11/10/2026; precisato il 12/10/2026).

**Vedi anche.** [MOT-AUTOMATICO](04-aspetto.md#mot-automatico--movimento-automatico-lampeggi-aggiornamenti-e-messaggi-a-tempo)

**Fonti.**

- [Success Criterion 2.2.2 Pause, Stop, Hide (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#pause-stop-hide) — Criterio 2.2.2, livello A: Moving, blinking, scrolling; Auto-updating; note · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/20/pause-stop-hide.html))
- [Understanding Pause, Stop, Hide](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html) — Intent of Pause, Stop, Hide; Examples (A «loading» animation) · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/20/pause-stop-hide.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'pause-stop-hide', righe 660-664 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-2.2.5 · Dopo un nuovo accesso non si perde nulla (2.2.5, AAA, obiettivo)

**Regola.** Quando la sessione scade, chi rientra continua ciò che stava facendo senza perdere i dati inseriti.

**Perché.** Moduli, schede cliniche, preventivi e fatture chiedono minuti; perderli per una scadenza colpisce chi è più lento: chi legge lentamente, chi usa uno screen reader, chi ha difficoltà motorie (Understanding, Benefits). Gli esempi dell'Understanding: il carrello che il server conserva e ripristina dopo il nuovo accesso; la posta che scade dopo 30 minuti, avvisa qualche minuto prima e lascia intatto il messaggio in corso. L'Understanding di 3.3.7 aggiunge che chi conserva dati per non farli riscrivere deve proteggerli.

**Soglie ed eccezioni.** Livello AAA, adottato come obiettivo. Sufficienti: G105, G181. Fallimento: F12.

**In DottorCloud.** I moduli si salvano a metà sul server (crm/moduli/compilazioni.py, save_answers); i messaggi in scrittura (email, nota, WhatsApp, SMS) restano nel browser con useDraft (composables/drafts.js, localStorage per utente, doctype e record); Lead.vue, Deal.vue e le pagine delle regole di assegnazione e degli SLA avvisano prima di lasciare la pagina (useUnsavedChangesWarning, beforeunload). Su un computer condiviso al banco una bozza nel browser espone dati personali o sanitari: in locale solo ciò che non è sensibile, bozze cancellate all'uscita, meglio bozze sul server legate all'utente.

**Come si verifica.** A metà di un modulo cancellare il cookie di sessione, rientrare e verificare che tutto ci sia; controllare che cosa resta nel localStorage dopo l'uscita.

**Errori da evitare.** La testata della persona teneva in cache il profilo fiscale: la data di nascita restava nel database del browser anche dopo l'uscita, su un computer di segreteria condiviso (revisione del codice, ottobre 2026; corretto).

**Vedi anche.** [SAN-SESSIONE-CONDIVISA](08-persone-e-dati-personali.md#san-sessione-condivisa--sessioni-adatte-a-un-pc-di-segreteria-condiviso)

**Fonti.**

- [Success Criterion 2.2.5 Re-authenticating (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#re-authenticating) — Criterio 2.2.5, livello AAA · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/20/re-authenticating.html))
- [Understanding Re-authenticating](https://www.w3.org/WAI/WCAG22/Understanding/re-authenticating.html) — Intent; Benefits; Examples (A shopping site checkout; Authentication in an email program) · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/20/re-authenticating.html))
- [Understanding Redundant Entry](https://www.w3.org/WAI/WCAG22/Understanding/redundant-entry.html) — Intent of Redundant Entry: paragrafo sulla protezione dei dati conservati durante un processo · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/22/redundant-entry.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 're-authenticating', righe 677-690 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-2.3.1 · Non più di tre lampeggiamenti al secondo (2.3.1, A)

**Regola.** Nessun contenuto lampeggia più di tre volte in un secondo, oppure il lampeggio resta sotto le soglie del lampeggio generale e del lampeggio rosso.

**Perché.** I lampeggiamenti possono scatenare crisi in chi ha epilessia fotosensibile o altri disturbi convulsivi fotosensibili; il rosso è più pericoloso. Spegnere il lampeggio non è un rimedio: la crisi può arrivare prima che lo si spenga (Understanding, Intent).

**Soglie ed eccezioni.** Livello A, per tutta la pagina (requisito di conformità 5). Al massimo 3 lampeggi in qualunque secondo; altrimenti l'area dei lampeggi contemporanei non supera 0,006 steradianti, il 25% di qualunque campo visivo di 10 gradi. Un rettangolo di 341×256 px su uno schermo visto a 1024×768 stima un campo di 10 gradi (definizione); l'Understanding, passando ai pixel CSS, scrive che l'area combinata dei lampeggi diventa 341×256 px CSS, cioè 87.296 px CSS. Lampeggio generale: coppia di variazioni opposte di luminanza relativa di almeno il 10% del massimo, con l'immagine più scura sotto 0,80. Lampeggio rosso: transizione da o verso uno stato con R/(R+G+B) almeno 0,8 e differenza oltre 0,2 nel diagramma CIE 1976 UCS. Esclusi i motivi fini e bilanciati (rumore bianco, scacchiera con quadrati sotto 0,1 gradi). Si analizza alla scala più grande a cui si può vedere (un video a schermo intero) e, per le animazioni brevi, in loop. Sufficienti: G19, G176, G15.

**In DottorCloud.** Nessun avviso che lampeggia (chiamata in arrivo, errore, scadenza): un'icona e una parola. I video del sito (siti/dottorcloud) e del marchio (brand/dottorcloud/video) si analizzano a schermo intero e in loop prima di pubblicarli.

**Come si verifica.** Cercare animazioni con periodo sotto 333 ms che alternano luminanza o colore; analizzare i video con uno strumento di analisi del lampeggio sulla registrazione dello schermo (l'Understanding ricorda che sotto i 3 lampeggi al secondo non serve).

**Errori da evitare.** Nessun caso trovato: la regola vale per ciò che si aggiungerà.

**Vedi anche.** [MOT-AUTOMATICO](04-aspetto.md#mot-automatico--movimento-automatico-lampeggi-aggiornamenti-e-messaggi-a-tempo)

**Fonti.**

- [Success Criterion 2.3.1 Three Flashes or Below Threshold (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#three-flashes-or-below-threshold) — Criterio 2.3.1, livello A · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/20/three-flashes-or-below-threshold.html))
- [general flash and red flash thresholds (definizione)](https://www.w3.org/TR/WCAG22/) — definizione: 0,006 sr, 25% del campo di 10 gradi, rettangolo di 341×256 px a 1024×768, lampeggio rosso · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/terms/20/general-flash-and-red-flash-thresholds.html))
- [Understanding Three Flashes or Below Threshold](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html) — Intent of Three Flashes or Below Threshold (pixel CSS e 87.296 px CSS; analisi alla scala più grande; GIF in loop) · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/20/three-flashes-or-below-threshold.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'three-flashes-or-below-threshold', righe 701-704 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-2.3.3 · Le animazioni causate da un gesto si possono spegnere (2.3.3, AAA, obiettivo)

**Regola.** Un'animazione di movimento causata da un'interazione si può disattivare, salvo che sia essenziale; DottorCloud la disattiva da sé quando il sistema chiede meno movimento (prefers-reduced-motion).

**Perché.** Chi ha disturbi vestibolari prova vertigini, nausea, emicrania, fino a dover restare a letto, davanti a movimenti non essenziali come la parallasse (Understanding, Intent). Per la definizione WCAG l'animazione di movimento aggiunge passaggi tra due stati per dare l'illusione del moto o di una transizione morbida; i cambi di colore o di opacità che non alterano dimensione, forma, posizione o profondità non lo sono. Lo scorrimento comandato dall'utente è essenziale; un movimento aggiunto allo scorrimento no.

**Soglie ed eccezioni.** Livello AAA, adottato come obiettivo. Sufficienti: C39 (prefers-reduced-motion), SCR40.

**In DottorCloud.** Rispettano già la riduzione: la manopola degli interruttori (espresso.css), il foglio che sale (telefono.css), PulsanteAggiungi.vue e la testata di MobileLead.vue (motion-reduce), ConversationList.vue (motion-safe), LoaderMark e dc-segnato (espresso-componenti.css). Da allineare gli scorrimenti morbidi fatti dal codice: tieniInVista in utils/inVista.js, allaCimaConLaScheda in utils/schedaAttiva.js, pages/FormFill.vue, pages/Dashboard.vue, Invoices/InvoiceDialog.vue, Activities/WhatsAppArea.vue, Clinic/ClinicArea.vue, FieldLayoutEditor.vue, Calendar/Attendee.vue, toEnd di composables/conversationScroll.js, reveal in crm/public/js/moduli_campi.js (/modulo) e window.scrollTo in crm/www/prenota.html; poi la transizione di altezza di CollapsibleSection.vue (300 ms). Una funzione unica che restituisce 'auto' invece di 'smooth' quando matchMedia('(prefers-reduced-motion: reduce)') è vero.

**Come si verifica.** Attivare «Riduci movimento» nel sistema e ripercorrere agenda, fattura, chat, scheda clinica, cruscotto, /modulo e /prenota: nessuno scorrimento morbido né transizione di posizione o dimensione. Cercare behavior: 'smooth' e le transizioni di transform, translate e max-height.

**Errori da evitare.** Scorrimenti morbidi che ignorano la riduzione del movimento in una dozzina di punti, /prenota e /modulo compresi (rilevato nel codice l'11/10/2026; elenco completato il 12/10/2026).

**Vedi anche.** [MOT-RIDOTTO](04-aspetto.md#mot-ridotto--rispettare-riduci-movimento)

**Fonti.**

- [Success Criterion 2.3.3 Animation from Interactions (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#animation-from-interactions) — Criterio 2.3.3, livello AAA · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/21/animation-from-interactions.html))
- [motion animation (definizione)](https://www.w3.org/TR/WCAG22/) — definizione e nota sui cambi di colore e di opacità · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/terms/21/motion-animation.html))
- [Understanding Animation from Interactions](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html) — Intent; Examples (Transitions that support the reduce motion preference) · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/21/animation-from-interactions.html))
- [C39: Using the CSS prefers-reduced-motion query to prevent motion](https://www.w3.org/WAI/WCAG22/Techniques/css/C39) — Description, Examples, Tests · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/css/C39.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'animation-from-interactions', righe 711-718 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-2.4.1 · Saltare i blocchi ripetuti: «Vai al contenuto» e regioni (2.4.1, A)

**Regola.** C'è un modo per saltare i blocchi che si ripetono su più pagine: un link «Vai al contenuto» come primo elemento raggiungibile, visibile almeno quando ha il focus, che porta il focus all'inizio del contenuto principale; e regioni (header, nav, main, aside, footer) che contengono tutto il contenuto.

**Perché.** Senza salto chi usa la tastiera attraversa a ogni pagina tutte le voci del menu: l'Understanding ricorda che decine di tasti richiedono tempo e possono causare a qualcuno dolore fisico, e porta l'esempio di 40 link e 200 parole prima della notizia. Le regioni aiutano chi usa una tecnologia assistiva, ma la tecnica ARIA11 avverte che i browser non le mostrano direttamente agli utenti: chi vede e usa solo la tastiera ha bisogno del link (o di un'estensione del browser).

**Soglie ed eccezioni.** Livello A. Sufficienti: G1, G123, G124 (link di salto); ARIA11, H69, H64, SCR28 (raggruppare i blocchi ripetuti). Consigliate: C6, H97. G1: il link è il primo elemento che riceve il focus, dice che porta al contenuto, è visibile sempre o almeno al focus e sposta davvero il focus. Authoring Practices: banner, main, complementary e contentinfo al primo livello; tutto il contenuto in una regione; regioni dello stesso tipo con nomi diversi.

**In DottorCloud.** App.vue disegna un h1 nascosto (#titolo-pagina, tabindex -1) dalle parole del menu; DesktopLayout.vue e MobileLayout.vue hanno main; AppSidebar.vue è un aside con nome «Menu» e una nav per gruppo. Manca il link: come primo elemento un «Vai al contenuto» (sr-only che si mostra al focus, nei colori del marchio, come nel sito: siti/dottorcloud/parti/layout.html) che porta il focus all'inizio di main. Non a #titolo-pagina: sul computer l'h1 nascosto sta dopo l'intestazione della pagina (#app-header in AppHeader.vue, con titolo e azioni della pagina) e il salto la scavalcherebbe. Il titolo che riceve il focus da un salto non è un controllo e non chiede l'aspetto del focus di 2.4.13. In /prenota ci sono già header, nav (i passi), main e footer; /modulo, /documento, /lista-attesa e /crm-form hanno solo main.

**Come si verifica.** Dal caricamento premere Tab: il primo arresto è il link di salto, visibile; Invio porta il focus nel contenuto e il Tab seguente entra nella pagina. axe: bypass (2.4.1), più region, skip-link, landmark-one-main e landmark-unique (buone pratiche).

**Errori da evitare.** Nessun link di salto in /crm, /area e nelle pagine pubbliche, mentre la barra laterale precede il contenuto con decine di voci (rilevato nel codice l'11/10/2026, ancora così il 12/10/2026).

**Vedi anche.** [ARIA-LANDMARK](02-wcag-percepibile-e-robusto.md#aria-landmark--punti-di-riferimento-tutto-il-contenuto-in-una-regione-con-un-ruolo-e-un-nome)

**Fonti.**

- [Success Criterion 2.4.1 Bypass Blocks (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#bypass-blocks) — Criterio 2.4.1, livello A · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/20/bypass-blocks.html))
- [Understanding Bypass Blocks](https://www.w3.org/WAI/WCAG22/Understanding/bypass-blocks.html) — Intent; Benefits (decine di tasti, dolore fisico); Examples (40 link, 200 parole) · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/20/bypass-blocks.html))
- [G1: Adding a link at the top of each page that goes directly to the main content area](https://www.w3.org/WAI/WCAG22/Techniques/general/G1) — Description e Tests · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/general/G1.html))
- [ARIA11: Using ARIA landmarks to identify regions of a page](https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA11) — Description: «Landmarks are interpretable by WAI-ARIA-aware assistive technologies and are not exposed by browsers directly to users» · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/aria/ARIA11.html))
- [Landmark Regions](https://www.w3.org/WAI/ARIA/apg/practices/landmark-regions/) — General Principles of Landmark Design, Step 2 e Step 3 · W3C WAI – Authoring Practices Task Force dell'ARIA Working Group · sorgente al commit 0f765e4 del 29/09/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/aria-practices/blob/0f765e4dc33e966026114ac12a8380db1de3b787/content/practices/landmark-regions/landmark-regions-practice.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'bypass-blocks', righe 720-733 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-2.4.2 · Ogni pagina ha un titolo che dice dove si è (2.4.2, A)

**Regola.** Ogni pagina ha un titolo che ne dice l'argomento o lo scopo; in un'app a pagina singola il titolo cambia a ogni vista. In DottorCloud il particolare viene prima del generale: «`<record>` · `<tipo>` · DottorCloud».

**Perché.** Il titolo identifica dove si è senza leggere la pagina: il browser lo mostra nella barra e nella scheda, e serve a distinguere più pagine aperte a chi vede poco, a chi ha difficoltà cognitive o di memoria e a chi naviga ascoltando (Understanding, Intent e Benefits). Con più schede aperte (una persona e la sua trattativa) titoli uguali fanno lavorare sul record sbagliato. L'Understanding chiede che in una SPA il titolo cambi con la vista e mostra, come insieme di pagine, i titoli dell'APG dal particolare al generale («Alert and Message Dialogs Pattern | APG | WAI | W3C»).

**Soglie ed eccezioni.** Livello A. Sufficiente: G88 con H25; consigliata: G127; fallimento: F25. Dopo un invio con errori il titolo può dirlo: il tutorial WAI mostra «3 Errors – Billing Address», GOV.UK antepone «Error: » (in italiano «Errore: »).

**In DottorCloud.** router.js (afterEach) scrive document.title con il nome della pagina; Settings.vue scrive «`<pagina>` · Impostazioni» e rimette il titolo di prima alla chiusura; i record lo scrivono con usePageMeta di frappe-ui (Lead.vue, Deal.vue, Contact.vue, Organization.vue). Schema: «Silvia Fontana · Trattativa · DottorCloud», «Richiamo dopo due mesi · Automazione · DottorCloud», «Pagina non trovata · DottorCloud», «Accedi · DottorCloud», con il nome del prodotto preso dal marchio ({brand}). Le pagine pubbliche nominano il centro accanto al prodotto.

**Come si verifica.** axe document-title verifica solo che il titolo ci sia. A mano: aprire più schede (persona, trattativa, automazione, pagina che non c'è) e confrontarle; con lo screen reader ascoltare il titolo a ogni cambio di vista.

**Errori da evitare.** Titolo fermo su «Accoglienza» in tutte le 40 misure delle Impostazioni (studio UX, ottobre 2026; corretto). Persona e trattativa entrambe «Silvia Fontana»; tutte le schede di una persona «Noemi Carbone»; editor «Automazione» senza il nome; pagina di accesso «Login» in inglese; pagina che non c'è solo «DottorCloud»; h1 nascosto «Dashboard» con titolo «Panoramica» (studio UX, ottobre 2026).

**Vedi anche.** [LING-TITOLI](07-lingua-e-norme.md#ling-titoli--titoli-di-pagina-e-intestazioni-che-dicono-dove-sei)

**Fonti.**

- [Success Criterion 2.4.2 Page Titled (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#page-titled) — Criterio 2.4.2, livello A · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/20/page-titled.html))
- [Understanding Page Titled](https://www.w3.org/WAI/WCAG22/Understanding/page-titled.html) — Intent (Single Page Applications); Benefits; Examples (A set of web pages) · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/20/page-titled.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'page-titled', righe 735-745 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026
- [User Notification (Forms Tutorial)](https://www.w3.org/WAI/tutorials/forms/notifications/) — Overall feedback > Using the page title · W3C WAI – Education and Outreach Working Group · repository archiviato l'11/07/2024 (commit ef7a612); consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/wai-tutorials/blob/ef7a612c0014bd1514bcd7e1d8d5f02fa5ed43d7/content/forms/notifications.md))
- [Recover from validation errors (GOV.UK Design System)](https://design-system.service.gov.uk/patterns/validation/) — How to tell the user about validation errors · Government Digital Service (GOV.UK Design System) · ramo main, consultato il 12/10/2026 ([sorgente letto](https://github.com/alphagov/govuk-design-system/blob/main/src/patterns/validation/index.md))

### WCAG-2.4.3 · Il focus segue un ordine che conserva il senso (2.4.3, A)

**Regola.** Quando l'ordine di navigazione conta, i componenti ricevono il focus in un ordine che ne conserva senso e uso: ordine del DOM coerente con quello visivo; il focus dentro una finestra quando si apre e di nuovo sul comando che l'ha aperta quando si chiude; mai lasciato sul body dopo una chiusura o un'eliminazione; niente elementi focalizzabili annidati.

**Perché.** Un focus che salta o si perde disorienta chi usa la tastiera, uno screen reader o un ingranditore: chi ingrandisce vede una piccola parte e può leggere un campo nel contesto sbagliato (Understanding, Benefits). L'Understanding non impone di seguire l'ordine visivo, ma chiede che l'ordine non sembri saltare né a chi vede né a chi ascolta; boccia il controllo che sembra ricevere il focus due volte per elementi annidati (un div con tabindex 0 che contiene un pulsante); nella finestra modale il focus va dentro all'apertura e torna al pulsante, o all'elemento dopo, alla chiusura. Le Authoring Practices chiedono che ci sia sempre un elemento attivo diverso dal body: dopo la chiusura di una finestra il focus va al pulsante che l'ha aperta, dopo un'eliminazione alla voce successiva.

**Soglie ed eccezioni.** Livello A. Sufficienti: G59; C27; SCR26, H102, SCR27. Fallimenti: F44 (tabindex che crea un ordine senza senso), F85 (finestre o menu non adiacenti al loro comando nell'ordine). Authoring Practices: tabindex maggiore di 0 fortemente sconsigliato.

**In DottorCloud.** useFirstFieldFocus (composables/firstFieldFocus.js) porta il focus nel primo campo in cui si scrive, aspettando fino a 3000 ms (PATIENCE) che il modulo si disegni. Il FocusScope di reka-ui rimette il focus sull'elemento di prima o sul body: se quell'elemento non c'è più (una riga eliminata), portarlo sulla riga successiva o sul titolo della lista. Il modello è già in pages/Calendar.vue: all'apertura del pannello il focus va al suo titolo, alla chiusura all'elemento di prima o a #titolo-pagina. Dopo fatta() in Mobile/ElencoCose.vue il focus va alla riga successiva. In /prenota render() rifà main con replaceChildren: dopo ogni passo il focus va al titolo del nuovo passo (tabindex -1). Sul telefono il focus iniziale di una pagina delle Impostazioni va al titolo, non al pulsante indietro.

**Come si verifica.** Tab attraverso ogni pagina; dopo ogni azione (chiudere, eliminare, salvare, cambiare passo) controllare document.activeElement. axe: tabindex e focus-order-semantics (buone pratiche, la seconda sperimentale), nested-interactive (4.1.2).

**Errori da evitare.** Prima di useFirstFieldFocus il focus restava sul pulsante dietro la finestra: ciò che si scriveva andava perso e Tab girava nella pagina sotto (commento in composables/firstFieldFocus.js). /prenota perde il focus a ogni passo, salvo i passi che lo portano su un campo (la ricerca dei servizi con il mouse, il nome nei dati) (rilevato nel codice l'11/10/2026, ancora così il 12/10/2026). Sul telefono, all'apertura di una pagina delle Impostazioni, il pulsante indietro mostra l'anello come se fosse premuto (studio UX, ottobre 2026).

**Vedi anche.** [WCAG-1.3.2](02-wcag-percepibile-e-robusto.md#wcag-132--lordine-del-codice-è-lordine-di-lettura)

**Fonti.**

- [Success Criterion 2.4.3 Focus Order (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#focus-order) — Criterio 2.4.3, livello A · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/20/focus-order.html))
- [Understanding Focus Order](https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html) — Intent (elementi annidati, ordine visivo); Benefits; Examples (modal dialogs) · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/20/focus-order.html))
- [F85: Failure of Success Criterion 2.4.3 due to using dialogs or menus that are not adjacent to their trigger control in the sequential navigation order](https://www.w3.org/WAI/WCAG22/Techniques/failures/F85) — Description e Tests · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/failures/F85.html))
- [Developing a Keyboard Interface](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/) — Discernible and Predictable Keyboard Focus (Persistence of focus); Keyboard Navigation Between Components (The Tab Sequence) · W3C WAI – Authoring Practices Task Force dell'ARIA Working Group · sorgente al commit 0f765e4 del 29/09/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/aria-practices/blob/0f765e4dc33e966026114ac12a8380db1de3b787/content/practices/keyboard-interface/keyboard-interface-practice.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'focus-order', righe 747-762 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-2.4.4 · Lo scopo di ogni link si capisce dal testo o dal suo contesto (2.4.4, A)

**Regola.** Lo scopo di un link si capisce dal suo testo, oppure dal testo insieme al contesto determinabile dal programma: la stessa frase, paragrafo, voce di elenco o cella, l'intestazione della cella, o testo collegato con aria-labelledby (ARIA7) o aria-label (ARIA8). Il contesto va prima del link.

**Perché.** Le tecnologie assistive offrono l'elenco dei link della pagina e chi va da un link all'altro con Tab li incontra fuori contesto: dieci «Apri» non dicono nulla; chi ha difficoltà motorie salta i link che non servono senza visitarli (Understanding, Intent e Benefits). L'Understanding osserva che è utile dare un testo coerente ai link con la stessa destinazione (in un insieme di pagine lo esige 3.2.4) e che aiuta dare testi diversi ai link con scopi e destinazioni diversi.

**Soglie ed eccezioni.** Livello A. Eccezione: lo scopo sarebbe ambiguo per tutti. Sufficienti tra le altre: G91, H30, H24, G53, ARIA7, ARIA8, H77, H78, H79, H81. Fallimenti: F63 (contesto in contenuto non collegato al link), F89 (link fatto solo di un'immagine senza nome).

**In DottorCloud.** Il testo del link è la destinazione: «Roberto Coppola ↗» invece di «Persona ↗». Un link di sola icona ha un nome con l'oggetto (nella lista d'attesa l'icona persona ha già «Apri `<nome>`»), ma dove chi vede ha solo l'icona è meglio il nome della persona come link. Un «Apri» ripetuto in ogni riga si toglie quando la riga stessa apre (.riga-stesa) o prende il nome della riga. Un rimando a una pagina delle Impostazioni è un link vero (apriImpostazioni in composables/settings.js), non un percorso da seguire a mente.

**Come si verifica.** axe link-name verifica solo che il nome ci sia (identical-links-same-purpose è AAA ed è spenta). Con lo screen reader scorrere l'elenco dei link: ognuno ha senso da solo o con la sua riga.

**Errori da evitare.** Le carte delle cose da fare nel kanban hanno sempre il link generico «Persona ↗» (studio UX, ottobre 2026). Nella lista d'attesa un'icona persona a fine riga porta alla scheda e lo dice a chi vede solo nel tooltip, mentre il resto della riga apre la richiesta (studio UX, ottobre 2026). Rimandi scritti «Impostazioni > WhatsApp» come testo semplice verso un gruppo che, senza WhatsApp, non c'è (studio UX, ottobre 2026).

**Fonti.**

- [Success Criterion 2.4.4 Link Purpose (In Context) (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#link-purpose-in-context) — Criterio 2.4.4, livello A, ed eccezione · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/20/link-purpose-in-context.html))
- [Understanding Link Purpose (In Context)](https://www.w3.org/WAI/WCAG22/Understanding/link-purpose-in-context.html) — Intent (contesto prima del link; stessa destinazione, stesso testo); Benefits; Examples · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/20/link-purpose-in-context.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'link-purpose-in-context', righe 764-788 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-2.4.5 · Più di un modo per trovare una pagina (2.4.5, AA)

**Regola.** Ogni pagina di un insieme si trova in almeno due modi (menu, ricerca, link dalle pagine correlate, mappa o elenco delle pagine), salvo le pagine che sono un passo o il risultato di un processo.

**Perché.** Ognuno trova le cose a modo suo: chi usa uno screen reader o un ingranditore fa prima con una ricerca che scorrendo un menu lungo; chi ha difficoltà cognitive può preferire la ricerca, o un elenco d'insieme, a una gerarchia di menu difficile da capire (Understanding, Benefits).

**Soglie ed eccezioni.** Livello AA. Sufficienti, combinandone due o più: G125, G64, G63, G161 (ricerca), G126, G185.

**In DottorCloud.** Le pagine del lavoro quotidiano: menu (utils/menu.js), ricerca delle persone, link dalle notifiche e dalle schede. Le Impostazioni: il menu a due livelli e, da aggiungere, una casella di ricerca sulle parole del menu (etichette e descrizioni in utils/impostazioni.js): oggi trova() apre una pagina solo dal suo nome esatto (chiave, alias o etichetta) e serve agli indirizzi. Le pagine sorelle (SORELLE in utils/menu.js) si raggiungono anche dal loro interruttore. I passi di /prenota e /modulo sono esenti.

**Come si verifica.** Per ogni tipo di pagina elencare le vie per arrivarci: nessuna pagina raggiungibile da un solo pulsante o solo dall'indirizzo.

**Errori da evitare.** Il registro delle chiamate si raggiunge solo dal telefono in alto a destra e nessuna voce del menu si accende (studio UX, ottobre 2026; utils/navigation.js non lo mette in nessuna sezione). La lista Contatti non ha l'interruttore delle sorelle (studio UX, ottobre 2026; Contacts non è in SORELLE). Le Impostazioni non hanno una ricerca (rilevato nel codice l'11/10/2026).

**Fonti.**

- [Success Criterion 2.4.5 Multiple Ways (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#multiple-ways) — Criterio 2.4.5, livello AA, ed eccezione dei processi · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/20/multiple-ways.html))
- [Understanding Multiple Ways](https://www.w3.org/WAI/WCAG22/Understanding/multiple-ways.html) — Intent; Benefits; Examples · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/20/multiple-ways.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'multiple-ways', righe 790-800 (due o più tecniche) · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-2.4.6 · Intestazioni ed etichette dicono che cosa c'è e che cosa scrivere (2.4.6, AA)

**Regola.** Dove ci sono intestazioni ed etichette, descrivono argomento o scopo: un'intestazione dice che cosa contiene la sezione, un'etichetta che cosa va inserito o che cosa fa il controllo; due campi diversi non hanno la stessa etichetta.

**Perché.** Titoli chiari fanno prevedere che cosa c'è in ogni sezione, cosa che aiuta chi legge lentamente o ha poca memoria a breve termine; un'etichetta chiara dice come completare il modulo; con il markup giusto (1.3.1) chi usa uno screen reader ritrova le intestazioni nell'elenco che ne genera (Understanding, Benefits). Il criterio non obbliga ad averle (le etichette dei campi le chiede 3.3.2) e non riguarda il markup (1.3.1) né il nome accessibile (4.1.2): chiede che siano chiare. Possono essere brevi: anche una parola.

**Soglie ed eccezioni.** Livello AA. Sufficienti: G130 (intestazioni descrittive), G131 (etichette descrittive); consigliate: G201, SCR24.

**In DottorCloud.** Un h1 per pagina (App.vue lo disegna dalle parole del menu; i record in CON_UN_TITOLO usano il loro nome), h2 per le carte delle schede, senza salti di livello. Etichette con l'oggetto: «Nuova persona», non «Crea»; «Mostra: solo gli esercizi accesi», non «Tutti». Un gruppo contiene solo ciò che il titolo promette.

**Come si verifica.** Elenco delle intestazioni dello screen reader; axe empty-heading, heading-order, page-has-heading-one (buone pratiche); etichette uguali per campi diversi cercate nel catalogo crm/locale/it.po.

**Errori da evitare.** Il gruppo «Dati dell'azienda» nel pannello della trattativa contiene data di chiusura, probabilità, prossimo passo e responsabile; due «Azienda predefinita» con valori opposti; il filtro degli Esercizi mostra solo «Tutti»; il chip «C Chiara Romano» non dice che è l'assegnazione (studio UX, ottobre 2026). Salti da h1 a h3 nelle carte della persona, ora h2 (studio UX, ottobre 2026; corretto), nel gruppo «OGGI» delle notifiche e in «No deals yet» della scheda azienda (studio UX, ottobre 2026). «Crea» da solo, ora «Nuova persona», «Nuova trattativa» (studio UX, ottobre 2026; corretto).

**Vedi anche.** [LING-TITOLI](07-lingua-e-norme.md#ling-titoli--titoli-di-pagina-e-intestazioni-che-dicono-dove-sei)

**Fonti.**

- [Success Criterion 2.4.6 Headings and Labels (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#headings-and-labels) — Criterio 2.4.6, livello AA · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/20/headings-and-labels.html))
- [Understanding Headings and Labels](https://www.w3.org/WAI/WCAG22/Understanding/headings-and-labels.html) — Intent (rapporto con 3.3.2, 1.3.1 e 4.1.2); Benefits · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/20/headings-and-labels.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'headings-and-labels', righe 802-810 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-2.4.7 · Il focus da tastiera si vede sempre (2.4.7, AA) e :focus-visible

**Regola.** Ogni interfaccia usabile da tastiera ha un modo d'uso in cui l'indicatore del focus si vede, sempre, senza limiti di tempo. Si disegna con outline e :focus-visible; un anello fatto di box-shadow porta con sé un outline trasparente per i colori forzati; non si toglie mai l'indicatore senza sostituirlo, e non è mai solo un cambio di colore del testo o dell'icona.

**Perché.** Senza indicatore chi usa la tastiera non sa dove si trova (Understanding, Intent). L'indicatore non può essere a tempo e resta soggetto al contrasto 3:1 di 1.4.11. La tecnica C40 avverte che i browser sopprimono box-shadow nei colori forzati e, se serve un anello di sola ombra, consiglia di aggiungere outline: 2px transparent solid. Le euristiche di :focus-visible (Selectors 4, non normative): il focus si indica sempre sugli elementi che ricevono testo e quando si usa la tastiera; non dopo un clic del puntatore su un elemento che non riceve testo; un focus spostato da uno script segue ciò che faceva l'elemento di prima; un elemento appena mostrato che prende il focus da solo (il pulsante di una finestra appena aperta) dovrebbe indicarlo.

**Soglie ed eccezioni.** Livello AA. Sufficienti: G149, C15, G165, G195, C40, C45, SCR31. Fallimenti: F55 (focus tolto via script), F78 (outline o bordi che nascondono l'indicatore).

**In DottorCloud.** frappe-ui (tailwind/plugin.js) applica :focus-visible { outline: var(--focus-outline-default); outline-offset: 0 }; espresso.css fissa --focus-outline-default a 2px solid #0e8a7c nel tema chiaro e #5fe0cc nello scuro, e lo stesso colore (--colore-del-fuoco) per gli anelli disegnati con ring (§25, che ricolora focus-visible:ring-outline-gray-3 e -4). Le righe cliccabili: [data-riga-cliccabile]:focus-visible con outline e offset -2px; .riga-stesa disegna l'anello sul suo ::after; le voci del menu con [data-slot='sidebar-item']:has(> :focus-visible) (index.css). In Tailwind 3 (3.4.19 nel progetto) outline-none vale outline: 2px solid transparent, come chiede C40: un anello fatto con ring più outline-none resta visibile nei colori forzati; non scrivere a mano outline: none o outline-style: none senza un sostituto.

**Come si verifica.** Tab su ogni pagina nei due temi e con i colori forzati (Contrasto elevato di Windows, o l'emulazione forced-colors degli strumenti del browser); cercare outline: none e outline-style: none e, per ogni focus-visible:, verificare che resti un anello. Nessuna regola di axe copre 2.4.7.

**Errori da evitare.** Voci del menu senza indicatore; anelli grigio chiaro a 1,7:1 sul bianco; righe e titoli delle Impostazioni segnati solo da uno sfondo appena più grigio (studio UX, ottobre 2026; corretti con l'anello del marchio). Anello delle righe grigio a 2,8:1 (revisione del codice, ottobre 2026; corretto). Convenzioni con solo uno sfondo quasi bianco (studio UX, ottobre 2026; ora c'è anche l'anello). Nella lista d'attesa l'icona persona a fine riga cambia solo colore al focus (focus-visible:text-ink-gray-8 con outline-none in pages/WaitingList.vue) (studio UX, ottobre 2026; ancora così il 12/10/2026).

**Vedi anche.** [FOCUS-1.4.11](#focus-1411--lindicatore-di-focus-contrasta-almeno-31-con-ciò-che-ha-accanto-1411-aa)

**Fonti.**

- [Success Criterion 2.4.7 Focus Visible (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#focus-visible) — Criterio 2.4.7, livello AA · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/20/focus-visible.html))
- [Understanding Focus Visible](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html) — Intent of Focus Visible (mode of operation, nessun limite di tempo, rapporto con 1.4.11) · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/20/focus-visible.html))
- [C40: Creating a two-color focus indicator to ensure sufficient contrast with all components](https://www.w3.org/WAI/WCAG22/Techniques/css/C40) — Description (box-shadow nei colori forzati, outline trasparente) · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/css/C40.html))
- [C45: Using CSS :focus-visible to provide keyboard focus indication](https://www.w3.org/WAI/WCAG22/Techniques/css/C45) — Description · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/css/C45.html))
- [Selectors Level 4 (Editor's Draft), sorgente](https://drafts.csswg.org/selectors-4/) — sezione The Focus-Indicated Pseudo-class: :focus-visible (id the-focus-visible-pseudo, riga 3089 e seguenti), esempio con le euristiche non normative · W3C – CSS Working Group · Editor's Draft al commit 5033732 dell'11/10/2026; consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/csswg-drafts/blob/50337328484f7fcdd9ab6fe9ded6011815b1707e/selectors-4/Overview.bs))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'focus-visible', righe 812-816 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### FOCUS-1.4.11 · L'indicatore di focus contrasta almeno 3:1 con ciò che ha accanto (1.4.11, AA)

**Regola.** L'indicatore di focus è un'informazione visiva sullo stato: contrasta almeno 3:1 con i colori adiacenti. Se sta fuori dal componente si misura contro lo sfondo su cui il componente poggia; se sta dentro, contro i colori del componente; se è il bordo del componente, contro entrambi; se è in parte dentro e in parte fuori, basta una delle due parti.

**Perché.** Un anello pallido non si vede su schermi lucidi, con luce forte o con poca vista. 1.4.11 chiede 3:1 per l'informazione visiva necessaria a riconoscere uno stato, focus compreso, ed esclude solo l'aspetto deciso dal browser e non modificato (Understanding, Relationship with Focus Visible). Un focus fatto solo di un cambio di sfondo dentro il componente è fuori dall'ambito di 1.4.11, ma per l'Understanding non passa 1.4.1 (uso del colore). C40 mostra che due colori a 9:1 tra loro garantiscono 3:1 su qualunque sfondo uniforme.

**Soglie ed eccezioni.** 3:1. Calcoli con la formula WCAG sui gettoni di Espresso. Anello chiaro #0e8a7c: su bianco 4,25:1, su #f6f9f8 4,01:1, su #f1f4f3 3,84:1, su #ebeeed 3,64:1, sul blocco scuro #0b2e2a (toast, barra delle liste) 3,44:1; contro il verde pieno del marchio #0b6f64 solo 1,42:1. Anello scuro #5fe0cc: su #151817 11,08:1, #1d201f 10,18:1, #272a29 8,98:1, #353938 7,26:1, blocco #123b36 7,64:1. Bocciati: grigio #c4c8c7 su bianco 1,69:1, #959b99 su bianco 2,83:1, uno sfondo bianco contro #f6f9f8 1,06:1 e contro #f1f4f3 1,11:1. Sufficienti per lo stato di focus: G195, C40; fallimento: F78.

**In DottorCloud.** Sempre il gettone --focus-outline-default (o --colore-del-fuoco). Sui pulsanti pieni del marchio l'anello resta fuori dal bordo (outline con offset 0 o positivo), mai dentro: dentro, contro #0b6f64, varrebbe 1,42:1. Un nuovo colore di superficie si prova contro l'anello nei due temi prima di usarlo. Il binario dell'interruttore spento è #858c8a: 3,43:1 sul bianco, 3,10:1 su #f1f4f3.

**Come si verifica.** Contagocce degli strumenti del browser sull'anello e sui pixel accanto, nei due temi; axe color-contrast misura solo il testo, non l'indicatore.

**Errori da evitare.** Anelli grigio chiaro a 1,7:1 e anello delle righe #959b99 a 2,8:1; Convenzioni con il focus di solo sfondo; binario dell'interruttore spento a 1,29:1 (studio UX e revisione del codice, ottobre 2026; tutti corretti).

**Vedi anche.** [WCAG-1.4.11](02-wcag-percepibile-e-robusto.md#wcag-1411--controlli-stati-fuoco-icone-e-grafici-a-31), [WCAG-2.4.7](#wcag-247--il-focus-da-tastiera-si-vede-sempre-247-aa-e-focus-visible)

**Fonti.**

- [Success Criterion 1.4.11 Non-text Contrast (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#non-text-contrast) — Criterio 1.4.11, livello AA: User Interface Components · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/21/non-text-contrast.html))
- [Understanding Non-text Contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html) — Intent: User Interface Components; Adjacent colors; Relationship with Focus Visible (indicatori fuori, dentro, sul bordo; cambio di sfondo fuori ambito) · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/21/non-text-contrast.html))
- [C40: Creating a two-color focus indicator to ensure sufficient contrast with all components](https://www.w3.org/WAI/WCAG22/Techniques/css/C40) — Description (9:1 tra i due colori) · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/css/C40.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'non-text-contrast', righe 532-570 (Situation B: stato di focus) · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-2.4.11 · Il focus non resta nascosto sotto barre, pulsanti fissi, toast o tastiera (2.4.11, AA; 2.4.12, AAA)

**Regola.** Quando un componente riceve il focus da tastiera non è nascosto del tutto da contenuto dell'autore: intestazioni o piè di pagina fissi, il «+» flottante, toast, banner, pannelli non modali. Come obiettivo (2.4.12, AAA) nessuna parte resta nascosta.

**Perché.** Chi usa la tastiera, un sensore o la voce segue il focus con gli occhi: se finisce sotto un elemento fisso non sa come proseguire e può credere che il sistema non risponda (Understanding, Intent). L'Understanding: si valuta il componente, non l'indicatore (che, se coperto del tutto, fa probabilmente fallire 2.4.7); per il contenuto che l'utente può spostare conta la posizione iniziale; un contenuto aperto dall'utente può coprire se lo si toglie senza spostare il focus (Esc, scorrere); una finestra modale fatta bene passa sempre; un avviso che compare senza un gesto dell'utente non deve impedire di vedere l'elemento con il focus; scroll-padding è il rimedio indicato per i piè di pagina fissi.

**Soglie ed eccezioni.** AA: non nascosto del tutto. AAA (2.4.12): nessuna parte nascosta. Sufficiente: C43 (scroll-padding); fallimento: F110 (piè di pagina o intestazione fissi che coprono del tutto l'elemento con il focus). scroll-padding (CSS Scroll Snap, valido per ogni contenitore che scorre) definisce la zona di vista ottimale, togliendo le parti coperte da barre fisse, e conta quando un elemento viene portato in vista per il focus.

**In DottorCloud.** Sul telefono la barra in basso (MobileNav di frappe-ui, dopo main nella colonna di MobileLayout.vue) non copre il contenuto; lo coprono il «+» (Mobile/PulsanteAggiungi.vue: fisso, 56 px, a 5rem dal fondo più l'area sicura, z-20) e i toast (telefono.css §6: sopra la barra, a 4,25rem più l'area sicura; sopra un foglio scendono dall'alto). Sul contenitore che scorre (main di MobileLayout.vue) serve scroll-padding-bottom almeno quanto il «+» più il suo margine, e in fondo alle liste uno spazio alto quanto il «+». Nei fogli .dialog-content ha già scroll-padding 4rem 0 5rem (telefono.css), nell'area scroll-padding-bottom 5rem (area/area.css): un campo portato in vista non finisce sotto titolo e azioni che restano. Con la tastiera su iPhone utils/tastieraAperta.js dà il focus con preventScroll e poi chiama inVista, che rispetta lo scroll-padding del contenitore; su Android la pagina si accorcia da sola (interactive-widget=resizes-content in index.html e area.html). Il «+» non si nasconde mentre ha il focus.

**Come si verifica.** A larghezza di telefono e di tablet, con il «+» e un toast visibili, Tab fino all'ultima riga di ogni lista, avanti e indietro (F110); ripetere con la tastiera virtuale aperta e dentro i fogli.

**Errori da evitare.** Il «+» da 56 px copriva «Emetti la fattura» di due righe e le date delle carte delle fatture (studio UX, ottobre 2026); ora si fa da parte mentre la lista scende, ma lo spazio in fondo alle liste è ancora da fare e, quando il «+» c'è, copre il «Chiama» della riga sotto (studio UX, ottobre 2026; da fare). Il «+» non tornava dopo essere sparito (revisione del codice, ottobre 2026; corretto).

**Vedi anche.** [MOB-TESTATE](05-telefono-e-tocco.md#mob-testate--ciò-che-resta-fermo-occupa-poco-e-non-copre), [MOB-TASTIERA-APERTA](05-telefono-e-tocco.md#mob-tastiera-aperta--con-la-tastiera-aperta-resta-in-vista-ciò-che-serve)

**Fonti.**

- [Success Criterion 2.4.11 Focus Not Obscured (Minimum) (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#focus-not-obscured-minimum) — Criterio 2.4.11, livello AA, e note · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/22/focus-not-obscured-minimum.html))
- [Success Criterion 2.4.12 Focus Not Obscured (Enhanced) (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#focus-not-obscured-enhanced) — Criterio 2.4.12, livello AAA · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/22/focus-not-obscured-enhanced.html))
- [Understanding Focus Not Obscured (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html) — Intent; User-movable content; User-opened content; Modal dialogs; Examples · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/22/focus-not-obscured-minimum.html))
- [C43: Using CSS scroll-padding to un-obscure content](https://www.w3.org/WAI/WCAG22/Techniques/css/C43) — Description, Examples, Tests · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/css/C43.html))
- [F110: Failure of Success Criterion 2.4.11 Focus Not Obscured (Minimum) due to a sticky footer or header completely hiding focused elements](https://www.w3.org/WAI/WCAG22/Techniques/failures/F110) — Description e Tests · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/failures/F110.html))
- [CSS Scroll Snap Module Level 1 (Editor's Draft), sorgente](https://drafts.csswg.org/css-scroll-snap-1/) — sezione Scroll Snapport: the scroll-padding property (optimal viewing region) · W3C – CSS Working Group · Editor's Draft al commit 5033732 dell'11/10/2026; consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/csswg-drafts/blob/50337328484f7fcdd9ab6fe9ded6011815b1707e/css-scroll-snap-1/Overview.bs))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocchi 'focus-not-obscured-minimum' e 'focus-not-obscured-enhanced', righe 853-866 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-2.4.13 · Aspetto del focus: area e cambio di contrasto (2.4.13, AAA, obiettivo)

**Regola.** Quando l'indicatore di focus è visibile, una sua area almeno pari a un perimetro spesso 2 px CSS del componente senza focus cambia di almeno 3:1 tra lo stato con focus e quello senza, sugli stessi pixel; conta solo la parte che cambia abbastanza.

**Perché.** Un indicatore grande e ben diverso si vede anche con poca vista, con l'ingrandimento o di sfuggita. L'Understanding misura l'area: per un pulsante di 90×30 il perimetro di 2 px vale (92×32) − (88×28) = 480 px²; il più piccolo indicatore che vale ancora come perimetro è una linea di 2 px dentro il componente, a filo del suo bordo esterno (per esempio un outline), mentre uno rientrato più all'interno deve essere più spesso (l'esempio da 3 px vale 612 px²). Un cambio di sfondo che contrasta meno di 3:1 con il colore di prima non passa.

**Soglie ed eccezioni.** Livello AAA, adottato come obiettivo. Area minima: rettangolo 4h + 4w; cerchio 4πr; rettangolo arrotondato 4h + 4w − (16 − 4π)r. Cambio di contrasto 3:1 tra gli stessi pixel. Eccezioni: indicatore deciso dal browser e non modificabile (il select nativo), oppure indicatore e suo sfondo non modificati dall'autore. In un elenco di schede con l'anello solo sulla scheda si valuta l'anello di ogni scheda. Non si applica a ciò che riceve il focus senza essere un controllo (il titolo raggiunto da un link di salto). Sufficienti: G195, C40, C41; fallimenti: F55, F78.

**In DottorCloud.** L'outline di Espresso (2 px, offset 0, appena fuori dal bordo) soddisfa l'area. Le righe cliccabili hanno l'outline di 2 px con offset −2 px, dentro la riga e a filo del bordo: per l'Understanding è il più piccolo indicatore ammesso; non va rientrato oltre. Il cambio #0e8a7c contro il bianco vale 4,25:1 e contro #ebeeed 3,64:1: passa; un cambio del solo sfondo (1,06–1,11:1) no, e nemmeno il solo colore di un'icona di 16 px (pages/WaitingList.vue).

**Come si verifica.** Misurare spessore e offset dell'anello e confrontare l'area con la formula; contagocce sugli stessi pixel con e senza focus.

**Errori da evitare.** Focus fatti di solo sfondo nelle vecchie righe delle Impostazioni e in Convenzioni (studio UX, ottobre 2026; corretti); l'icona persona della lista d'attesa che cambia solo colore (ancora così il 12/10/2026).

**Fonti.**

- [Success Criterion 2.4.13 Focus Appearance (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#focus-appearance) — Criterio 2.4.13, livello AAA, eccezioni e note · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/22/focus-appearance.html))
- [perimeter (definizione)](https://www.w3.org/TR/WCAG22/) — definizione e formule 4h+4w, 4πr · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/terms/22/perimeter.html))
- [Understanding Focus Appearance](https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html) — Minimum area (Using a solid outline; Other indicator shapes); Change of contrast (Partially contrasting indicators); Component keyboard focus; Exceptions · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/22/focus-appearance.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'focus-appearance', righe 868-872 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-2.5.1 · Ogni gesto ha un'alternativa a un solo tocco (2.5.1, A)

**Regola.** Ciò che si fa con un gesto a più punti (pizzico, tocco con due dita) o con un percorso (scorrimento rapido in una direzione, tirare giù per ricaricare, tracciare una forma) si fa anche con un solo puntatore senza percorso: tocco, doppio tocco, pressione lunga, clic. Salvo che il percorso o i più punti siano essenziali (la firma).

**Perché.** Chi usa un dito solo, una bacchetta, un puntatore a testa o a sguardo, un mouse comandato a voce, o ha un tremore, non riesce a fare un percorso preciso (Understanding, Intent). L'Understanding esclude i gesti del sistema operativo, del browser (lo scorrimento della pagina, il tirare per ricaricare del browser) e delle tecnologie assistive, e chiarisce che un'alternativa da tastiera non basta: serve un'alternativa per il puntatore, che a sua volta non può essere un trascinamento (2.5.7). Apple chiede la stessa cosa: se uno scorrimento chiude una vista, ci sia anche un pulsante.

**Soglie ed eccezioni.** Livello A. Sufficienti: G215, G216; fallimento: F105 (gesto a percorso senza alternativa a un solo puntatore).

**In DottorCloud.** Accoglienza (pages/Today.vue): lo scorrimento tra i giorni (composables/scorriGiorni.js, SOGLIA_SCORRI 60 px, un bordo di 24 px lasciato al sistema) ha i pulsanti «Giorno prima» e «Giorno dopo». Agenda del telefono (Mobile/AgendaDelGiorno.vue): il giorno si cambia anche toccandolo nella striscia della settimana, la settimana con «Settimana prima/dopo». Tirare giù per aggiornare (composables/tiraPerAggiornare.js, SOGLIA_TIRATA 64, MASSIMO_TIRATA 96) è fatto dal prodotto, perché quello del browser è spento: serve un comando a un tocco o un aggiornamento automatico equivalente. I fogli che si chiudono trascinando (utils/trascinaFoglio.js) si chiudono anche con la X, Esc e Indietro. La firma e il tratto sul corpo sono essenziali; i punti sul corpo si mettono con un tocco.

**Come si verifica.** Elencare i gestori touchstart, pointermove e di scorrimento; per ognuno trovare il comando a un tocco sulla stessa pagina.

**Errori da evitare.** Le liste del telefono con useTiraPerAggiornare si aggiornano a comando solo tirando giù; per il resto si rinfrescano al ritorno sulla pagina o quando la connessione torna: verificare lista per lista che ci sia un modo a un tocco (rilevato nel codice l'11/10/2026).

**Vedi anche.** [MOB-GESTI-ALTERNATIVA](05-telefono-e-tocco.md#mob-gesti-alternativa--ogni-gesto-ha-unalternativa-a-un-tocco-visibile)

**Fonti.**

- [Success Criterion 2.5.1 Pointer Gestures (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#pointer-gestures) — Criterio 2.5.1, livello A, e nota · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/21/pointer-gestures.html))
- [Understanding Pointer Gestures](https://www.w3.org/WAI/WCAG22/Understanding/pointer-gestures.html) — Intent; The difference between path-based Pointer Gestures and Dragging; Relationship to keyboard accessibility requirements; Examples · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/21/pointer-gestures.html))
- [Accessibility (Human Interface Guidelines), dati della pagina](https://developer.apple.com/design/human-interface-guidelines/accessibility) — sezione Mobility: «Offer alternatives to gestures» · Apple · pagina aggiornata il 09/06/2025 (registro delle modifiche); consultata il 12/10/2026 ([sorgente letto](https://developer.apple.com/tutorials/data/design/human-interface-guidelines/accessibility.json))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'pointer-gestures', righe 874-878 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-2.5.2 · Un tocco si può annullare prima di sollevare il dito (2.5.2, A)

**Regola.** Per ciò che si attiva con un solo puntatore vale almeno una: la pressione non esegue nessuna parte della funzione; la funzione si completa al rilascio e si può interrompere prima o annullare dopo; il rilascio inverte ciò che la pressione ha fatto; agire alla pressione è essenziale (le funzioni che emulano un tasto lo sono).

**Perché.** Chi ha difficoltà motorie avvia per sbaglio tocchi e clic: con l'attivazione al rilascio può spostarsi fuori dal bersaglio e alzare il dito senza conseguenze. L'evento click di JavaScript scatta al rilascio ed è indipendente dal dispositivo (Understanding, Intent). Nel trascinamento serve poter annullare, o rimettere tutto com'era rilasciando dove non si può.

**Soglie ed eccezioni.** Livello A. Sufficienti: G210 (trascinamenti che si possono annullare), G212 (controlli nativi, attivazione al rilascio: premere, uscire dal bersaglio, rilasciare: non succede nulla, o si annulla). Fallimento: F101 (attivazione alla pressione), che si ha solo se non c'è modo di annullare, il rilascio non inverte e agire alla pressione non è essenziale.

**In DottorCloud.** Agire su click, mai su mousedown, pointerdown o touchstart. mousedown.prevent serve solo a non far perdere il focus al campo, mentre la scelta avviene al click. La pressione lunga di ListViews/MobileListRows.vue (tieni(), su pointerdown, TENUTA 450 ms) sceglie la riga con il dito ancora giù: si inverte con un altro tocco, ma è meglio completarla al rilascio. Il trascinamento lasciato fuori da una destinazione rimette tutto com'era.

**Come si verifica.** G212 su ogni comando di righe, chip, liste di scelta e schede; dove qualcosa avviene alla pressione, verificare che si possa annullare.

**Errori da evitare.** Calendar/Attendee.vue e Controls/EmailMultiSelect.vue scelgono alla pressione (@mousedown.prevent con onSelect); TabsTrigger di reka-ui (SchedeDelRecord.vue) cambia scheda alla pressione del tasto sinistro: casi reversibili, quindi non bocciati, ma da portare al click (rilevato nel codice l'11/10/2026).

**Vedi anche.** [MOB-RILASCIO](05-telefono-e-tocco.md#mob-rilascio--si-agisce-al-rilascio-con-un-segno-immediato-di-pressione)

**Fonti.**

- [Success Criterion 2.5.2 Pointer Cancellation (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#pointer-cancellation) — Criterio 2.5.2, livello A: No Down-Event, Abort or Undo, Up Reversal, Essential · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/21/pointer-cancellation.html))
- [Understanding Pointer Cancellation](https://www.w3.org/WAI/WCAG22/Understanding/pointer-cancellation.html) — Intent: Up-Event activation or completion; Up-Event Abort or Undo; Up Reversal; Down-Event · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/21/pointer-cancellation.html))
- [F101: Failure of Success Criterion 2.5.2 due to activating a control on the down-event](https://www.w3.org/WAI/WCAG22/Techniques/failures/F101) — Description e Tests · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/failures/F101.html))
- [G212: Using native controls to ensure functionality is triggered on the up-event.](https://www.w3.org/WAI/WCAG22/Techniques/general/G212) — Description e Tests · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/general/G212.html))
- [G210: Ensuring that drag-and-drop actions can be cancelled](https://www.w3.org/WAI/WCAG22/Techniques/general/G210) — titolo e Description · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/general/G210.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'pointer-cancellation', righe 880-888 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-2.5.3 · Il nome accessibile contiene le parole che si vedono (2.5.3, A)

**Regola.** Per i controlli con un'etichetta di testo visibile, il nome accessibile contiene quel testo, meglio se all'inizio. aria-label e aria-labelledby sostituiscono il testo visibile nel calcolo del nome: se ci sono, devono ripeterlo.

**Perché.** Chi usa il comando vocale dice ciò che vede («tocca Prenota»): se il nome è un altro il comando non funziona, e un nome diverso può diventare un comando nascosto che scatta per sbaglio; chi vede e ascolta uno screen reader si confonde se sente parole diverse da quelle che legge (Understanding, Intent). Maiuscole e punteggiatura non contano; il criterio non si applica dove non c'è testo visibile (un'icona sola) e i simboli (›, +) non sono etichette.

**Soglie ed eccezioni.** Livello A. Buona pratica scritta nel criterio: il testo dell'etichetta all'inizio del nome. Sufficienti: G208, G211; consigliata: G162. Fallimenti: F96 (nome che non contiene il testo visibile), F111 (controllo con etichetta visibile e senza nome).

**In DottorCloud.** Un pulsante «Prenota» può chiamarsi «Prenota un appuntamento per Silvia Fontana», non «Nuovo evento». Il blocco dell'agenda prende il nome dalle parole che mostra, ore e persona per prime (paroleDelBlocco in utils/agenda.js, aria-label di Calendar/BloccoAgenda.vue). Un campo che mostra un valore ha come nome la sua etichetta, mai il testo d'esempio. SchedeDelRecord.vue chiama «Altro» il pulsante che mostra «Altro» e, con una scheda nascosta aperta, mette per primo il nome di quella scheda: è il modello.

**Come si verifica.** axe label-content-name-mismatch è sperimentale e va accesa (tag experimental); prova con Controllo vocale di iOS e macOS o Accesso vocale di Android dicendo le parole visibili.

**Errori da evitare.** Il campo del titolo dell'automazione mostra «Richiamo dopo due mesi» ma si chiama «Automazione senza titolo»; cinque select di Formati lette solo come «pulsante, 3»; la select degli Esercizi mostra «Tutti» e si chiama «Mostra» (studio UX, ottobre 2026).

**Vedi anche.** [LING-NOME-ACCESSIBILE](07-lingua-e-norme.md#ling-nome-accessibile--il-nome-per-il-lettore-di-schermo-in-italiano-e-uguale-a-quello-che-si-vede)

**Fonti.**

- [Success Criterion 2.5.3 Label in Name (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#label-in-name) — Criterio 2.5.3, livello A, e nota sulla buona pratica · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/21/label-in-name.html))
- [Understanding Label in Name](https://www.w3.org/WAI/WCAG22/Understanding/label-in-name.html) — Intent; Identifying label text for components; Symbolic text characters; Punctuation and capitalization; Accessible Name and Description Computation specification · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/21/label-in-name.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'label-in-name', righe 890-903 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-2.5.4 · Nessuna funzione solo scuotendo o inclinando il telefono (2.5.4, A)

**Regola.** Ciò che si attiva muovendo il dispositivo (scuotere, inclinare) o con gesti davanti alla fotocamera si fa anche con un comando dell'interfaccia, e la risposta al movimento si può spegnere; salvo che il movimento passi per un'interfaccia supportata dalle tecnologie assistive o sia essenziale.

**Perché.** Chi ha il dispositivo fissato (per esempio a una sedia a rotelle) o ha difficoltà motorie non può scuotere né inclinare, e chi ha un tremore attiverebbe comandi per sbaglio (Understanding, Intent). Non rientrano lo spostamento nello spazio rilevato dalla geolocalizzazione né il movimento per inquadrare un codice QR o un documento.

**Soglie ed eccezioni.** Livello A. Sufficiente: G213; fallimento: F106 (movimento che non si può disattivare).

**In DottorCloud.** Oggi nessun ascolto di devicemotion o deviceorientation nel prodotto. Una funzione futura (scuoti per annullare, inclina per scorrere) avrà un pulsante equivalente e un interruttore in Preferenze.

**Come si verifica.** Cercare devicemotion, deviceorientation, DeviceMotionEvent e i gesti letti dalla fotocamera prima di ogni rilascio.

**Errori da evitare.** Nessun caso trovato (rilevato nel codice l'11/10/2026 e il 12/10/2026).

**Fonti.**

- [Success Criterion 2.5.4 Motion Actuation (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#motion-actuation) — Criterio 2.5.4, livello A: Supported Interface, Essential · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/21/motion-actuation.html))
- [Understanding Motion Actuation](https://www.w3.org/WAI/WCAG22/Understanding/motion-actuation.html) — Intent of this Success Criterion; Examples · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/21/motion-actuation.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'motion-actuation', righe 905-915 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-2.5.7 · Ogni trascinamento ha un'alternativa senza trascinare (2.5.7, AA)

**Regola.** Ciò che si fa trascinando si fa anche con un solo puntatore senza trascinare (tocchi, un menu «Sposta su/giù» o «Sposta in…», un campo da scrivere), sulla stessa pagina; salvo che il trascinamento sia essenziale o sia del browser e non modificato.

**Perché.** Non tutti riescono a tenere premuto e muovere insieme: chi ha un tremore, usa una trackball, un puntatore a testa o a sguardo o un mouse comandato a voce (Understanding, Intent). L'Understanding: un'alternativa da tastiera non basta se non si può usare anche con tocchi o clic; l'alternativa non può essere un gesto a percorso (2.5.1); lo scorrimento e il «tira per ricaricare» del browser sono esclusi, ma rientrano se il contenuto sopprime quelli del browser e ne implementa di propri; un campo di testo accanto a un cursore è un'alternativa valida. Tra gli esempi: una lista ordinabile con pulsanti su e giù accanto all'elemento toccato, una bacheca che sposta la carta in un'altra colonna da un menu o da una freccia.

**Soglie ed eccezioni.** Livello AA. Sufficiente: G219 (alternativa al trascinamento); fallimento: F108.

**In DottorCloud.** Ogni lista che si riordina ha nel suo «⋯» «Sposta su», «Sposta giù» (e «Togli»), come già Automations/StepNode.vue, Plans/ProgrammeDialog.vue, Settings/Booking/BookingPageSettings.vue, Settings/CallScriptsSettings.vue e Settings/Website/WebsiteSettings.vue. Da aggiungere: sulla carta del kanban un menu «Sposta in…» con le colonne; nel cruscotto larghezza e altezza come scelte e «Sposta prima/dopo» (oggi la pagina dice «Trascina per spostare, tira l'angolo per ridimensionare», pages/Dashboard.vue); un comando a un tocco per ricaricare dove c'è il «tira giù» (composables/tiraPerAggiornare.js). L'appuntamento si sposta dal pannello, scrivendo data e orari.

**Come si verifica.** Inventario degli usi di vuedraggable (Draggable) e di grid-layout-plus: per ognuno l'alternativa a tocchi sulla stessa pagina.

**Errori da evitare.** Riordino o spostamento solo trascinando in Settings/HomeActions.vue (il Menu: la maniglia «Sposta» non sposta con un tocco), Settings/Pipelines/PipelineView.vue (le fasi), Settings/Forms/TemplateBuilder.vue (sezioni e domande), FieldLayoutEditor.vue (i campi), SidePanelLayoutEditor.vue, ColumnSettings.vue, Kanban/KanbanSettings.vue, Kanban/KanbanView.vue (carte e colonne), Controls/Grid.vue, Controls/GridFieldsEditorModal.vue, ViewControls.vue (filtri rapidi) e Dashboard/DashboardGrid.vue (rilevato nel codice l'11/10/2026, elenco completato il 12/10/2026). Nel Menu delle Impostazioni il separatore standard non si toglie (studio UX, ottobre 2026).

**Vedi anche.** [MOB-GESTI-ALTERNATIVA](05-telefono-e-tocco.md#mob-gesti-alternativa--ogni-gesto-ha-unalternativa-a-un-tocco-visibile), [MOB-TRASCINARE-SCORRERE](05-telefono-e-tocco.md#mob-trascinare-scorrere--trascinare-non-ruba-lo-scorrimento-i-bordi-sono-del-sistema)

**Fonti.**

- [Success Criterion 2.5.7 Dragging Movements (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#dragging-movements) — Criterio 2.5.7, livello AA, e nota · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/22/dragging-movements.html))
- [Understanding Dragging Movements](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html) — Intent; Relationship to keyboard accessibility requirements; Alternatives for dragging movements on the same page; Examples · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/22/dragging-movements.html))
- [G219: Ensuring an alternative to dragging movements](https://www.w3.org/WAI/WCAG22/Techniques/general/G219) — Description, Examples, Tests · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/general/G219.html))
- [F108: Failure of Success Criterion 2.5.7 Dragging Movements due to not providing a single pointer method that does not require a dragging movement](https://www.w3.org/WAI/WCAG22/Techniques/failures/F108) — Description e Tests · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/failures/F108.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'dragging-movements', righe 935-939 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-2.5.8 · Bersagli di almeno 24×24 px o ben distanziati (2.5.8, AA)

**Regola.** Ogni bersaglio del puntatore misura almeno 24×24 px CSS, salvo: spaziatura (un cerchio di 24 px centrato sul riquadro del bersaglio piccolo non tocca altri bersagli né i cerchi di altri bersagli piccoli); un controllo equivalente sulla stessa pagina che rispetta la misura; link dentro una frase o limitato dall'interlinea del testo; controllo del browser non modificato; presentazione essenziale o imposta per legge.

**Perché.** Chi ha un tremore, spasticità, tetraplegia o usa dispositivi di puntamento poco precisi attiva il bersaglio accanto; anche il tocco ne guadagna (Understanding, Intent). Esempi dell'Understanding: 20×20 con 4 px di spazio passa, senza spazio no; pulsanti alti 16 px passano se nulla sta sopra o sotto, impilati no; voci di menu alte 18 px non passano, alte 24 sì; un bersaglio di 16×16 attaccato a uno grande non passa senza almeno 4 px di distanza. La misura non dipende dallo zoom.

**Soglie ed eccezioni.** 24×24 px CSS: dentro il bersaglio deve stare un quadrato di 24×24 allineato alla pagina. Le aree che si sovrappongono a un altro bersaglio non contano, salvo che facciano la stessa azione o aprano la stessa pagina (definizione di bersaglio). Un cursore o una tavolozza sono un solo bersaglio. Non si applica ai bersagli mentre sono coperti da contenuto aperto dall'utente. Sufficiente: C42 (min-height e min-width sul contenitore).

**In DottorCloud.** Le caselle di selezione delle righe stanno in una cella-etichetta di almeno 24×24 (meglio 32) che porta il nome «Seleziona `<persona>`» (il nome c'è già, da vite/frappeUi.js). Le voci del mese a 24 px (Calendar/MeseAgenda.vue), quante ne stanno nel giorno, il resto in «altri». Gli interruttori di 26×16 stanno dentro un'etichetta che rende cliccabile tutta la riga (SettingsRow.vue) o arrivano a 24 di altezza. «Copia» e i link soli come «Apri Stripe» hanno padding fino a 24. Sul telefono l'anello invisibile di .touch-target (telefono.css §1, inset −10px −8px) allarga il bersaglio, purché non invada quello accanto.

**Come si verifica.** axe target-size è spenta per impostazione (enabled: false, tag wcag22aa): accenderla esplicitamente. Misure a mano con gli strumenti del browser, a 1440 px e sul tablet.

**Errori da evitare.** 292 bersagli sotto misura su 10 schermate, soprattutto le caselle da 14×14 dentro righe cliccabili (studio UX, ottobre 2026; da fare): le caselle ora hanno un nome, non ancora la misura. Voci del mese alte 18–20 px, 92 bersagli in una schermata (studio UX, ottobre 2026; corrette a 24 px). Interruttori 26×16 sul computer; «Copia» del codice di tracciamento 16×16; «Apri Stripe» 83×20; il titolo di un documento 256×16 come unico link della riga; etichette dei post alte 23 px; nomi dei pazienti alti 16 px nell'elenco di /crm/altro (studio UX, ottobre 2026).

**Vedi anche.** [MOB-BERSAGLIO](05-telefono-e-tocco.md#mob-bersaglio--bersagli-grandi-quanto-un-dito), [UX-FITTS](04-aspetto.md#ux-fitts--legge-di-fitts-bersagli-grandi-vicini-e-i-distruttivi-lontani)

**Fonti.**

- [Success Criterion 2.5.8 Target Size (Minimum) (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#target-size-minimum) — Criterio 2.5.8, livello AA: Spacing, Equivalent, Inline, User Agent Control, Essential; note · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/22/target-size-minimum.html))
- [target (definizione)](https://www.w3.org/TR/WCAG22/) — definizione e nota sui bersagli sovrapposti · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/terms/21/target.html))
- [Understanding Target Size (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html) — Intent; Exceptions; Size requirement; Spacing · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/22/target-size-minimum.html))
- [C42: Using min-height and min-width on target container to ensure sufficient target spacing](https://www.w3.org/WAI/WCAG22/Techniques/css/C42) — Description e Tests · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/css/C42.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'target-size-minimum', righe 941-944 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-2.5.5 · Al tocco 44×44 px: la regola di DottorCloud sopra il minimo (2.5.5, AAA, obiettivo)

**Regola.** Dove si tocca con il dito ((pointer: coarse)) ogni bersaglio misura almeno 44×44 px CSS, anello invisibile compreso, con spazio tra i bersagli vicini; eccezioni come in WCAG: un equivalente sulla stessa pagina, un link dentro un blocco di testo, un controllo del browser non modificato, una presentazione essenziale.

**Perché.** Il dito è grande, impreciso e copre il punto che tocca (Understanding, Intent). L'Understanding consiglia bersagli più grandi del minimo per i controlli usati spesso, con effetti difficili da annullare, vicini al bordo o difficili da raggiungere, o parte di un compito a passi. Apple indica 44×44 pt come misura predefinita dei controlli su iOS e iPadOS (minimo 28×28) e uno spazio di circa 12 pt attorno ai controlli con bordo, 24 pt attorno a quelli senza; Android raccomanda almeno 48×48 dp per ogni elemento che si tocca.

**Soglie ed eccezioni.** WCAG 2.5.5 (AAA): 44×44 px CSS; sufficiente C44. Apple (dimensione predefinita e minima): iOS e iPadOS 44×44 e 28×28 pt; macOS 28×28 e 20×20; tvOS 66×66 e 56×56; visionOS 60×60 e 28×28; watchOS 44×44 e 28×28. Android: almeno 48×48 dp (più piccoli per mouse e trackpad).

**In DottorCloud.** telefono.css §1 (pointer: coarse): .touch-target::after e button[role='switch']::after con inset −10px −8px; button.h-7::after −8px −3px e button.h-8::after −6px −2px, per arrivare a 44 px di altezza; lo stesso per i link disegnati come pulsanti. I controlli a segmenti (TabButtons, [data-slot='tab-button']) sono alti 2,75rem (44 px); le azioni dei fogli e i pulsanti a icona nella loro testata 44 px. Restano a 40 px (2,5rem) icone-a-dito e strumenti-compositore: da portare a 44. Il «+» (56 px) e l'azione a tutta larghezza di un modulo (min-height 2,75rem) rispettano già la regola. Una briciola che porta alla pagina stessa diventa testo.

**Come si verifica.** Misurare a 390 px di larghezza contando l'anello: ogni bersaglio almeno 44×44 e senza sovrapposizioni.

**Errori da evitare.** Pulsanti a icona da 34×40 (Chiudi, Giorno prima/dopo, Opzioni, Elimina, Togli la riga, Segna come letta), controlli a segmenti alti 36 px, briciole alte 26 px che portano alla pagina stessa, il link «Non è in DottorCloud? Scrivi un nome» di 229×28, tre icone da 34–38 px attaccate nella riga del contatto (studio UX, ottobre 2026). Dopo le correzioni i bersagli sotto 44 px sul telefono sono scesi di un terzo e i segmenti sono alti 44 px (studio UX, ottobre 2026).

**Vedi anche.** [MOB-BERSAGLIO](05-telefono-e-tocco.md#mob-bersaglio--bersagli-grandi-quanto-un-dito)

**Fonti.**

- [Success Criterion 2.5.5 Target Size (Enhanced) (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#target-size-enhanced) — Criterio 2.5.5, livello AAA, ed eccezioni · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/21/target-size-enhanced.html))
- [Understanding Target Size (Enhanced)](https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced.html) — Intent (quando usare bersagli più grandi) · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/21/target-size-enhanced.html))
- [C44: Using CSS to ensure targets are at least 44 by 44 CSS pixels](https://www.w3.org/WAI/WCAG22/Techniques/css/C44) — Description · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/css/C44.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'target-size-enhanced', righe 917-924 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026
- [Accessibility (Human Interface Guidelines), dati della pagina](https://developer.apple.com/design/human-interface-guidelines/accessibility) — sezione Mobility: «Offer sufficiently sized controls» (tabella per piattaforma) e «Consider spacing between controls as important as size» · Apple · pagina aggiornata il 09/06/2025 (registro delle modifiche); consultata il 12/10/2026 ([sorgente letto](https://developer.apple.com/tutorials/data/design/human-interface-guidelines/accessibility.json))
- [Make apps more accessible](https://developer.android.com/guide/topics/ui/accessibility/apps#large-controls) — sezione Use large, simple controls (48dp × 48dp) · Google (Android Developers) · ultimo aggiornamento del 22/09/2026; consultata il 12/10/2026

### WCAG-3.1.1 · La lingua della pagina è dichiarata e giusta (3.1.1, A)

**Regola.** La lingua principale di ogni pagina è determinabile dal programma: l'attributo lang dell'elemento html dice la lingua in cui la pagina è scritta, e cambia se la lingua cambia senza ricaricare.

**Perché.** Con la lingua giusta gli screen reader caricano le regole di pronuncia, i browser mostrano bene caratteri e scritture, i lettori multimediali le didascalie (Understanding, Intent). Ne beneficiano chi usa la sintesi vocale, chi fatica a leggere, chi ha disabilità cognitive, del linguaggio o dell'apprendimento. Se la pagina usa più lingue, vale quella usata di più.

**Soglie ed eccezioni.** Livello A. Sufficiente: H57 (lang sull'elemento html); consigliata: SVR5.

**In DottorCloud.** frontend/index.html e crm/www/crm.html scrivono lang='{{ boot.lang or 'en' }}', con boot.lang preso da frappe.local.lang: il ripiego dovrebbe essere la lingua del centro (lingue.del_centro()), non l'inglese. area.html, prenota.html, modulo.html, documento.html, lista_attesa.html e crm_form.html usano boot.lang; book.html usa frappe.lang or 'it'. Se l'utente cambia lingua in Preferenze senza ricaricare, aggiornare document.documentElement.lang. Le email dichiarano la loro lingua.

**Come si verifica.** axe html-has-lang, html-lang-valid, html-xml-lang-mismatch; ascolto con VoiceOver e TalkBack impostati in italiano.

**Errori da evitare.** Ripiego 'en' nelle due pagine dell'app, che entra solo se manca la lingua della sessione (rilevato nel codice l'11/10/2026).

**Vedi anche.** [I18N-LANG](07-lingua-e-norme.md#i18n-lang--la-lingua-dichiarata-della-pagina-e-delle-sue-parti)

**Fonti.**

- [Success Criterion 3.1.1 Language of Page (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#language-of-page) — Criterio 3.1.1, livello A · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/20/language-of-page.html))
- [Understanding Language of Page](https://www.w3.org/WAI/WCAG22/Understanding/language-of-page.html) — Intent of Language of Page; Benefits · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/20/language-of-page.html))
- [H57: Using the language attribute on the HTML element](https://www.w3.org/WAI/WCAG22/Techniques/html/H57) — Description e Tests · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/html/H57.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'language-of-page', righe 946-950 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-3.1.2 · Le parti in un'altra lingua sono marcate; le parole inglesi rimaste si traducono (3.1.2, AA)

**Regola.** La lingua di ogni brano o frase in una lingua diversa da quella della pagina è determinabile dal programma (lang sull'elemento); fanno eccezione nomi propri, termini tecnici, parole di lingua indeterminata e parole entrate nell'uso della lingua circostante. In DottorCloud una parola inglese rimasta in un'interfaccia italiana non si marca: si traduce.

**Perché.** Screen reader e browser applicano pronuncia e scrittura della lingua di ogni brano solo se è marcato; anche una sola parola rientra, salvo le eccezioni (Understanding, Intent). L'Understanding avverte che i nomi accessibili sono stringhe piatte: un cambio di lingua dentro un elemento può perdersi quando lo screen reader legge il nome, e mettere lang sull'elemento stesso aiuta in alcuni casi.

**Soglie ed eccezioni.** Livello AA. Sufficiente: H58 (lang sul brano).

**In DottorCloud.** Nella pagina di benvenuto ogni lingua è scritta nelle sue parole e il suo pulsante porta il suo lang (pages/Benvenuto.vue, :lang). Un testo che il centro ha scritto in un'altra lingua (un consenso in inglese, il messaggio di un paziente straniero) porta il suo lang. Le etichette per lo screen reader passano da \_\_() come il resto: /prenota chiama la navigazione dei passi «Passi della prenotazione» (stepsLabel), non 'progress'.

**Come si verifica.** axe valid-lang; ascoltare con lo screen reader titoli ed etichette nascoste; cercare nel catalogo crm/locale/it.po le stringhe tradotte uguali all'inglese.

**Errori da evitare.** «Social Planner» tradotto con sé stesso in it.po (studio UX, ottobre 2026; ancora così il 12/10/2026). In /prenota un ol aria-label='progress' era letto in inglese a chi usa VoiceOver in italiano (studio UX, ottobre 2026; corretto con stepsLabel).

**Vedi anche.** [I18N-LANG](07-lingua-e-norme.md#i18n-lang--la-lingua-dichiarata-della-pagina-e-delle-sue-parti)

**Fonti.**

- [Success Criterion 3.1.2 Language of Parts (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#language-of-parts) — Criterio 3.1.2, livello AA, ed eccezioni · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/20/language-of-parts.html))
- [Understanding Language of Parts](https://www.w3.org/WAI/WCAG22/Understanding/language-of-parts.html) — Intent of Language of Parts (nomi accessibili piatti, nomi propri, parole entrate nell'uso) · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/20/language-of-parts.html))
- [H58: Using language attributes to identify changes in the human language](https://www.w3.org/WAI/WCAG22/Techniques/html/H58) — Description e Tests · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/html/H58.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'language-of-parts', righe 952-955 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-3.2.1 · Il focus da solo non cambia il contesto (3.2.1, A)

**Regola.** Ricevere il focus non avvia un cambio di contesto: niente navigazione, finestre aperte, invii o spostamenti del focus solo perché un elemento è stato raggiunto.

**Perché.** Chi esplora con Tab o con le frecce deve poter guardare senza agire: chi ha disabilità visive, cognitive o motorie non deve trovarsi altrove all'improvviso (Understanding, Benefits). Per la definizione WCAG un cambio di contesto è un cambio grande di programma utente, area di visualizzazione, focus o di contenuto che cambia il senso della pagina; una sezione che si apre, un menu dinamico o una scheda non lo sono per forza. L'esempio di fallimento dell'Understanding: una finestra d'aiuto che si apre quando un campo riceve il focus e glielo porta via.

**Soglie ed eccezioni.** Livello A. Sufficiente: G107; fallimento: F55.

**In DottorCloud.** Controls/Link.vue chiede le opzioni quando la lista si apre, non al focus. I tooltip al focus sono ammessi. Le schede ad attivazione automatica cambiano contenuto, non contesto. Ma un gruppo di radio i cui elementi sono link cambia pagina appena le frecce spostano il focus: per passare tra pagine sorelle servono link in una nav con aria-current='page'.

**Come si verifica.** Tab e frecce su ogni controllo: nulla deve navigare, aprirsi, inviarsi o portare via il focus.

**Errori da evitare.** ViewBreadcrumbs.vue: sul computer l'interruttore delle pagine sorelle è un TabButtons di frappe-ui, cioè un RadioGroup di reka-ui con RouterLink dentro; RadioGroupItem fa click sull'elemento raggiunto con le frecce, quindi la freccia cambia pagina, e i link sono annunciati come radio (rilevato nel codice l'11/10/2026).

**Vedi anche.** [FORM-FUOCO](06-moduli.md#form-fuoco--il-cursore-va-dove-serve-e-non-salta-da-solo)

**Fonti.**

- [Success Criterion 3.2.1 On Focus (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#on-focus) — Criterio 3.2.1, livello A · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/20/on-focus.html))
- [changes of context (definizione)](https://www.w3.org/TR/WCAG22/) — definizione e note · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/terms/20/changes-of-context.html))
- [Understanding On Focus](https://www.w3.org/WAI/WCAG22/Understanding/on-focus.html) — Intent of On Focus; Benefits; Examples (Example of a Failure: A help dialog) · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/20/on-focus.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'on-focus', righe 1058-1066 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-3.2.2 · Cambiare un valore non porta altrove senza avvisare (3.2.2, A)

**Regola.** Cambiare l'impostazione di un controllo (select, radio, casella, interruttore, testo in un campo) non provoca da solo un cambio di contesto, salvo che l'utente ne sia avvisato prima.

**Perché.** Chi scorre le opzioni di una select con le frecce, se ogni opzione naviga, non arriva mai alla sua; chi non vede non si accorge di essere stato portato altrove (Understanding, Benefits). L'Understanding distingue: spuntare, scrivere, cambiare l'opzione o premere un pulsante a due stati (aria-pressed) cambia un'impostazione; attivare un link o un pulsante che invia o sposta il focus no. Mostrare campi diversi secondo il tipo di voce scelto in un calendario non è un cambio di contesto: la struttura resta.

**Soglie ed eccezioni.** Livello A. Sufficienti: G80 (pulsante di invio, con H32, H84), G13 (dire prima che cosa succederà), SCR19. Fallimenti: F36 (invio automatico alla fine dell'ultimo campo), F37 (nuova finestra al cambio di radio, casella o select senza avviso).

**In DottorCloud.** Nessuna select o radio che naviga o invia. «Appuntamento | Evento» nel pannello (Calendar/KindSwitch.vue) cambia i campi: è il caso dell'esempio del calendario, ammesso. Il codice dell'area non si invia da solo alla sesta cifra: c'è il pulsante (area/pages/Login.vue, area/components/CodeDialog.vue). Le pagine sorelle si cambiano con link, non con radio. Un interruttore che salva subito non cambia contesto, ma se ha effetti legali chiede conferma (3.3.4).

**Come si verifica.** Con la tastiera cambiare ogni select, radio, casella e interruttore: niente navigazione, nuova finestra, salto del focus o invio.

**Errori da evitare.** Le frecce sull'interruttore delle pagine sorelle (ViewBreadcrumbs.vue) cambiano pagina (rilevato nel codice l'11/10/2026).

**Fonti.**

- [Success Criterion 3.2.2 On Input (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#on-input) — Criterio 3.2.2, livello A · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/20/on-input.html))
- [Understanding On Input](https://www.w3.org/WAI/WCAG22/Understanding/on-input.html) — Intent of On Input (Buttons that change state); Benefits; Examples (calendario) · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/20/on-input.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'on-input', righe 1068-1083 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-3.2.3 · La navigazione sta sempre nello stesso ordine e la voce attiva si vede (3.2.3, AA)

**Regola.** I meccanismi di navigazione ripetuti su più pagine compaiono nello stesso ordine relativo ogni volta, salvo che l'utente lo cambi; si possono inserire voci (un sottomenu), non rimescolarle.

**Perché.** Chi usa un ingranditore vede una parte dello schermo e ritrova le cose ripetute dalla loro posizione; chi vede usa la memoria spaziale; chi non vede le incontra nello stesso ordine nel flusso della pagina (Understanding, Intent). Gli esempi dell'Understanding: la ricerca sempre ultima, un sottomenu inserito nella voce scelta, il link di salto sempre primo.

**Soglie ed eccezioni.** Livello AA. Sufficiente: G61; fallimento: F66 (link di navigazione in un ordine relativo diverso).

**In DottorCloud.** Il menu nasce dai dati (utils/menu.js), uguale in ogni pagina; la barra del telefono ha i suoi posti fissi più «Altro» (barraDelTelefono). L'interruttore delle sorelle sta sempre nell'intestazione. La barra dell'agenda è la stessa in tutte le viste, con il selettore della vista nello stesso punto. L'azione principale di una lista sta sempre nello stesso posto sul telefono. Ogni pagina accende la sua voce (aria-current='page'; utils/navigation.js decide la sezione).

**Come si verifica.** Confrontare menu, barre e intestazioni tra pagine e tra larghezze; per ogni pagina verificare quale voce è accesa.

**Errori da evitare.** Sul telefono la barra dell'agenda cambia tra le viste e il selettore della vista salta dall'altra parte; «Nuovo…» ora nella barra in basso ora sotto il titolo; il registro delle chiamate non accende nessuna voce; Contatti accende «Persone» ma non ha l'interruttore delle sorelle; la pagina che non c'è accende «Altro» (studio UX, ottobre 2026). La voce Notifiche ora si accende sulla sua pagina (studio UX, ottobre 2026; corretto).

**Fonti.**

- [Success Criterion 3.2.3 Consistent Navigation (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#consistent-navigation) — Criterio 3.2.3, livello AA · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/20/consistent-navigation.html))
- [Understanding Consistent Navigation](https://www.w3.org/WAI/WCAG22/Understanding/consistent-navigation.html) — Intent; Examples (A consistently located control; An expanding navigation menu; skip navigation) · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/20/consistent-navigation.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'consistent-navigation', righe 1085-1090 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-3.2.4 · Stessa funzione, stesso nome e stessa icona (3.2.4, AA)

**Regola.** I componenti che hanno la stessa funzione e si ripetono in un insieme di pagine si identificano in modo coerente: stessa parola, stesso nome accessibile, stessa icona; coerente, non per forza identico.

**Perché.** Chi usa uno screen reader riconosce i controlli dal nome che sente, chi ha difficoltà cognitive dall'aspetto: se la stessa funzione cambia nome si crede che faccia altro, o si perde tempo a capirlo (Understanding, Intent). L'Understanding precisa che il criterio riguarda i componenti ripetuti (navigazione, ricerca, account, piè di pagina), che le etichette possono adattarsi al contesto («Pagina 4» che diventa «Pagina precedente») e che componenti con funzioni diverse non sono obbligati a distinguersi, anche se distinguerli è buona pratica.

**Soglie ed eccezioni.** Livello AA. Sufficiente: G197, con le tecniche di 1.1.1 e 4.1.2 per etichette, nomi e alternative testuali; fallimento: F31 (due etichette diverse per la stessa funzione).

**In DottorCloud.** Un glossario applicato (doc 40): «Conversazioni» nel menu, nella barra e nel titolo; un nome per ciascun «Altro» («Azioni», «Altre schede», «Altro»); una coppia di stati per le automazioni; «Presente»/«Assente» per l'esito; «Da arrivare» e «In sala d'attesa» all'Accoglienza, «In fila» nella lista d'attesa; il salvataggio delle Impostazioni con Settings/AzioneImpostazioni.vue. Per DottorCloud un'icona ha un solo significato: regola nostra, oltre il minimo di 3.2.4.

**Come si verifica.** Inventario delle etichette per funzione nel catalogo crm/locale/it.po; confronto delle icone tra pagine sorelle.

**Errori da evitare.** «Chat» nella barra e «Conversazioni» nella pagina; tre «Altro» con significati diversi sulla stessa schermata; «In pausa», «Spente», «Bozza», «Attiva» per lo stesso stato; «Venuti», «Presente», «Completato» per lo stesso fatto; «Attesi» accanto a «In attesa»; il salvataggio in cinque modi tra pagine sorelle; «Appuntamento» nella scheda che fa ciò che fa «Prenota» nell'intestazione; l'icona persona per paziente e professionista nello stesso pannello (studio UX, ottobre 2026).

**Vedi anche.** [NN-H4](01-interazione.md#nn-h4--coerenza-e-standard)

**Fonti.**

- [Success Criterion 3.2.4 Consistent Identification (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#consistent-identification) — Criterio 3.2.4, livello AA · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/20/consistent-identification.html))
- [Understanding Consistent Identification](https://www.w3.org/WAI/WCAG22/Understanding/consistent-identification.html) — Intent of Consistent Identification; Examples 4, 5 e 6 · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/20/consistent-identification.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'consistent-identification', righe 1092-1121 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-3.2.6 · L'aiuto sta sempre nello stesso posto (3.2.6, A)

**Regola.** Se più pagine offrono un aiuto (recapiti di una persona, un modo per contattarla, un aiuto da sé, un contatto automatico), lo offrono nello stesso ordine rispetto al resto della pagina, salvo che l'utente cambi la presentazione; il criterio non obbliga ad averlo.

**Perché.** Chi si blocca a metà di un compito cerca aiuto dove l'ha visto prima; senza aiuto può abbandonare, sbagliare o chiedere a chi non tiene riservati i suoi dati (Understanding, Intent). Tra gli esempi dell'Understanding c'è proprio la prenotazione di una visita medica con una chat sempre nello stesso posto. Per l'Understanding un assistente automatico funziona anche per chi ha disabilità cognitive se capisce le parole scritte male, dà i recapiti di una persona dopo 3 tentativi senza una risposta soddisfacente e si chiude con una sola interazione, per poi richiamarlo con un link o un pulsante.

**Soglie ed eccezioni.** Livello A. Conta l'ordine nel contenuto serializzato, a parità di zoom e di orientamento. Sufficiente: G220 (un link ai contatti in una posizione coerente).

**In DottorCloud.** Nell'area «Messaggi» è sempre l'ultimo dei posti della barra (area/App.vue); la chat (crm/area/chat.py) passa a una persona sulle domande di salute e dà il 112 sulle parole d'emergenza. Se si aggiungono i recapiti del centro a /prenota, /modulo e /documento, stanno nello stesso punto a ogni passo (per esempio sopra il piede «Powered by»): oggi queste pagine non ne mostrano. Nel prodotto i primi passi e l'aiuto restano nello stesso posto della barra laterale.

**Come si verifica.** Percorrere tutti i passi di /prenota e /modulo e le pagine dell'area: l'aiuto è sempre nella stessa posizione relativa.

**Errori da evitare.** Nessun caso misurato: le pagine pubbliche oggi non mostrano telefono né email del centro (rilevato nel codice il 12/10/2026).

**Fonti.**

- [Success Criterion 3.2.6 Consistent Help (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#consistent-help) — Criterio 3.2.6, livello A: tipi di aiuto e note · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/22/consistent-help.html))
- [Understanding Consistent Help](https://www.w3.org/WAI/WCAG22/Understanding/consistent-help.html) — Intent; Limitations and Exceptions; Help Mechanisms; Support for people with cognitive and learning disabilities (chatbot); Examples (Medical appointment scheduling form) · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/22/consistent-help.html))
- [G220: Provide a contact-us link in a consistent location](https://www.w3.org/WAI/WCAG22/Techniques/general/G220) — titolo e Description · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/general/G220.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'consistent-help', righe 1158-1162 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-3.3.1 · Un errore dice in parole quale campo e che cosa non va (3.3.1, A)

**Regola.** Quando un errore di inserimento è rilevato automaticamente, il campo in errore è identificato e l'errore è descritto in testo. In DottorCloud il messaggio sta accanto al campo, legato al campo (aria-invalid, aria-describedby) e, nei moduli lunghi, riassunto in cima con un link a ciascun campo; non vive solo in un toast.

**Perché.** Un bordo rosso, un modulo ripresentato senza spiegazioni o un toast che sparisce non bastano a chi non distingue i colori, usa lo screen reader o legge piano (Understanding, Intent e Benefits). L'Understanding non impone dove mostrare gli errori (in cima, accanto ai campi, in un avviso o in una finestra) ma chiede il testo; un valore corretto in automatico va detto; la validazione nativa del browser ha limiti (messaggi che spariscono, non ingranditi, generici, uno alla volta). Il tutorial WAI consiglia di elencare gli errori in cima, ognuno con l'etichetta del campo, una descrizione breve, come correggere e un link al campo, in un contenitore con role='alert' se compaiono senza ricaricare la pagina; i campi si legano al loro messaggio con aria-describedby e, se i dati inviati hanno errori, è comodo portare il focus al primo campo sbagliato. GOV.UK mette il riepilogo in cima a main, gli dà il focus, lo intitola «There is a problem» e antepone «Error: » al titolo della pagina.

**Soglie ed eccezioni.** Livello A. Sufficienti: G83, ARIA21 (aria-invalid), SCR18 per i campi obbligatori; ARIA18, ARIA19, ARIA21, G84, G85, SCR18, SCR32 per formato e valori ammessi. Consigliate: G139 (elenco degli errori), G199, ARIA2. aria-invalid non è richiesto da 3.3.1; in DottorCloud sì.

**In DottorCloud.** Ogni campo in errore ha aria-invalid='true' e il messaggio collegato con aria-describedby; un riepilogo in cima con un link a ogni campo riceve il focus all'invio (in un dialogo breve basta portare il focus al primo campo in errore) e il titolo diventa «Errore: …». FieldLayoutDialog.vue (findMissingMandatory) mostra «Mandatory fields required: …» in un messaggio del dialogo, checkMandatory di data/document.js in un toast: entrambi passano a messaggi sui campi. Un pulsante resta attivo e, premuto, dice che cosa manca e porta lì il cursore, come fa già «Trova un orario libero». Il modello c'è nel sito del marchio: siti/dottorcloud/pagine/demo.html e siti/dottorcloud/risorse/js/sito.js (aria-invalid, aria-describedby).

**Come si verifica.** Inviare ogni modulo vuoto e sbagliato con lo screen reader: si sente quale campo e che cosa fare; nessun errore solo a colori o solo in un toast.

**Errori da evitare.** Nessun aria-invalid, aria-describedby né aria-errormessage in frontend/src e in crm/www; checkMandatory mostra solo il toast «Mandatory fields required: …»; /prenota dice «Compila i campi obbligatori.» in fondo, con role='alert', senza dire quali (rilevato nel codice l'11/10/2026, ancora così il 12/10/2026). «Emetti» e «Salva» spenti senza dire che cosa manca; il riquadro rosso «Prima di emetterla» compare prima di aver scritto nulla (studio UX, ottobre 2026).

**Vedi anche.** [FORM-ERRORE-ACCANTO](06-moduli.md#form-errore-accanto--lerrore-sta-accanto-al-campo-legato-al-campo-e-annunciato)

**Fonti.**

- [Success Criterion 3.3.1 Error Identification (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#error-identification) — Criterio 3.3.1, livello A · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/20/error-identification.html))
- [Understanding Error Identification](https://www.w3.org/WAI/WCAG22/Understanding/error-identification.html) — Intent of Error Identification; User agent native HTML form validation; Benefits · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/20/error-identification.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'error-identification', righe 1164-1179 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026
- [User Notification (Forms Tutorial)](https://www.w3.org/WAI/tutorials/forms/notifications/) — Overall feedback > Listing errors; In-line feedback > After submit · W3C WAI – Education and Outreach Working Group · repository archiviato l'11/07/2024 (commit ef7a612); consultato il 12/10/2026 ([sorgente letto](https://github.com/w3c/wai-tutorials/blob/ef7a612c0014bd1514bcd7e1d8d5f02fa5ed43d7/content/forms/notifications.md))
- [Error summary (GOV.UK Design System)](https://design-system.service.gov.uk/components/error-summary/) — How it works; Linking from the error summary to each answer; Where to put the error summary · Government Digital Service (GOV.UK Design System) · ramo main, consultato il 12/10/2026 ([sorgente letto](https://github.com/alphagov/govuk-design-system/blob/main/src/components/error-summary/index.md))
- [Recover from validation errors (GOV.UK Design System)](https://design-system.service.gov.uk/patterns/validation/) — How to tell the user about validation errors · Government Digital Service (GOV.UK Design System) · ramo main, consultato il 12/10/2026 ([sorgente letto](https://github.com/alphagov/govuk-design-system/blob/main/src/patterns/validation/index.md))

### WCAG-3.3.2 · Ogni campo ha un'etichetta visibile e le istruzioni che servono (3.3.2, A)

**Regola.** Quando si chiede un inserimento ci sono etichette o istruzioni visibili a tutti: il nome del campo resta visibile mentre si scrive (il testo d'esempio non è un'etichetta), obbligo e formato sono detti prima; vale anche per i campi facoltativi e per ogni opzione di radio, caselle e liste.

**Perché.** Lo standard HTML dice che placeholder non va usato al posto di un'etichetta: il suggerimento si vede solo finché il campo è vuoto, l'etichetta sempre. Per l'Understanding un aria-label può dare il nome (4.1.2) e fallire comunque 3.3.2, perché non è presentato a tutti; il criterio vale per ogni campo, obbligatorio o facoltativo, e non chiede di riempire la pagina: troppe istruzioni fanno male quanto troppo poche.

**Soglie ed eccezioni.** Livello A. Sufficienti: G131 con ARIA1, ARIA9, ARIA17, G89, G184, G162, G83 o H90; H44 (label); H71 (fieldset e legend); G167 (tra le ultime risorse). Consigliate: G13, ARIA2. Fallimento: F82 (numero di telefono diviso in più campi senza etichetta).

**In DottorCloud.** Etichette brevi sopra o accanto ai campi, come nella Nuova fattura («Cliente», «Servizio», «Professionista», «Quantità», «Prezzo unitario», «Modalità di pagamento»); per il nuovo appuntamento lo studio propone «Servizio», «Paziente», «Data», «Dalle», «Alle», «Professionista», «Ambulatorio», «Luogo», «Note». Il segno degli obbligatori (segno-obbligatorio) con la spiegazione in testa. Inizio e fine in un fieldset con legenda. Le parole accanto a un interruttore sono il suo label (SettingsRow.vue); fuori da SettingsRow e Field si usano useEtichettaDelCampo e useEtichetteDeiCampi (composables/nomeAlControllo.js).

**Come si verifica.** axe label, select-name, form-field-multiple-labels, aria-input-field-name, aria-toggle-field-name e label-title-only (buona pratica); a vista, i campi con il solo testo d'esempio.

**Errori da evitare.** Nuovo appuntamento con icone e testo d'esempio al posto delle etichette: «Inizio» e «Fine» ora etichettati, persona, servizio e professionista ancora no (studio UX, ottobre 2026; in parte corretto). Filtri rapidi con il solo testo d'esempio a 2,56:1 (studio UX, ottobre 2026; ora hanno un nome). Riquadro del codice di tracciamento senza etichetta; «Azienda predefinita» con il solo title («Scegli…»); parole degli interruttori della nuova trattativa in un div invece che in un label (studio UX, ottobre 2026).

**Vedi anche.** [FORM-ETICHETTA](06-moduli.md#form-etichetta--ogni-controllo-ha-unetichetta-visibile-legata-nel-codice)

**Fonti.**

- [Success Criterion 3.3.2 Labels or Instructions (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#labels-or-instructions) — Criterio 3.3.2, livello A · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/20/labels-or-instructions.html))
- [Understanding Labels or Instructions](https://www.w3.org/WAI/WCAG22/Understanding/labels-or-instructions.html) — Intent of Labels or Instructions (aria-label non presentato a tutti; campi facoltativi) · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/20/labels-or-instructions.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'labels-or-instructions', righe 1181-1201 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026
- [HTML Living Standard, sorgente](https://html.spec.whatwg.org/) — sezione «The placeholder attribute»: «The placeholder attribute should not be used as an alternative to a label» · WHATWG · Living Standard, ramo main; consultato il 12/10/2026 ([sorgente letto](https://github.com/whatwg/html/blob/main/source))

### WCAG-3.3.3 · L'errore dice come correggerlo (3.3.3, AA)

**Regola.** Quando un errore è rilevato e si sa come correggerlo, il messaggio lo dice, salvo che ciò comprometta la sicurezza o lo scopo del contenuto; i dati scritti restano nei campi.

**Perché.** Sapere che c'è un errore non basta: chi ha difficoltà cognitive o non vede può non capire come correggerlo e abbandonare il modulo (Understanding, Intent). GOV.UK chiede messaggi specifici, che dicano che cosa è successo e come rimediare, con le parole dell'etichetta e un «Error:» nascosto davanti, senza svuotare i campi; vieta il gergo tecnico, «forbidden», «illegal», «you forgot», «prohibited», «please», «sorry», «valid» e «invalid», «oops»; chiede di accettare più formati e di non validare quando si esce da un campo.

**Soglie ed eccezioni.** Livello AA. Sufficienti: ARIA18, G85, G177 (formato); ARIA18, G84, G177 (insieme di valori). Consigliate: G139, G199, SCR18, SCR32.

**In DottorCloud.** «Scrivi l'email come nome@esempio.it»; «La data di nascita deve essere nel passato»; «Il codice fiscale ha 16 caratteri: ne hai scritti 15». Si accettano +39, spazi e trattini nel telefono. Per il codice dell'area: «Il codice è scaduto: te ne mandiamo un altro», senza rivelare se un'email è registrata (eccezione di sicurezza). Un rifiuto del server arriva con le parole del prodotto, mai con la frase tecnica.

**Come si verifica.** Per ogni regola di validazione leggere il messaggio: dice che cosa fare? I campi restano compilati dopo l'errore?

**Errori da evitare.** Messaggi generici in /prenota («Compila i campi obbligatori.», «Inserisci un'email valida.») (rilevato nel codice l'11/10/2026). Eliminando un ambulatorio usato da appuntamenti arrivava la frase tecnica del framework in un toast (studio UX, ottobre 2026).

**Vedi anche.** [FORM-MESSAGGIO](06-moduli.md#form-messaggio--il-messaggio-derrore-dice-cosa-fare-con-le-parole-delletichetta)

**Fonti.**

- [Success Criterion 3.3.3 Error Suggestion (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#error-suggestion) — Criterio 3.3.3, livello AA, ed eccezione di sicurezza · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/20/error-suggestion.html))
- [Understanding Error Suggestion](https://www.w3.org/WAI/WCAG22/Understanding/error-suggestion.html) — Intent of Error Suggestion; Examples · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/20/error-suggestion.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'error-suggestion', righe 1203-1220 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026
- [Error message (GOV.UK Design System)](https://design-system.service.gov.uk/components/error-message/) — How it works; Match up error messages to labels; Be clear and concise; Be specific · Government Digital Service (GOV.UK Design System) · ramo main, consultato il 12/10/2026 ([sorgente letto](https://github.com/alphagov/govuk-design-system/blob/main/src/components/error-message/index.md))
- [Recover from validation errors (GOV.UK Design System)](https://design-system.service.gov.uk/patterns/validation/) — When to use this pattern (formati diversi); How it works (caratteri da ignorare); When to tell the user about validation errors · Government Digital Service (GOV.UK Design System) · ramo main, consultato il 12/10/2026 ([sorgente letto](https://github.com/alphagov/govuk-design-system/blob/main/src/patterns/validation/index.md))

### WCAG-3.3.4 · Fatture, firme, pagamenti, consensi ed eliminazioni: annullabili, controllati o confermati (3.3.4, AA)

**Regola.** Dove un'azione crea un impegno legale o una transazione finanziaria per chi la compie, modifica o elimina dati che l'utente controlla, o invia le risposte di un test, vale almeno una: si può annullare; i dati sono controllati e si possono correggere; prima di concludere si rivede, si conferma e si corregge.

**Perché.** Chi ha difficoltà di lettura inverte cifre e lettere, chi ha difficoltà motorie preme tasti per sbaglio: un errore su un'operazione irreversibile costa caro (Understanding, Intent). Per la definizione WCAG un impegno legale è un'operazione con cui si assume un obbligo o un beneficio legale, «un contratto di qualunque tipo» compreso. L'Understanding non chiede una conferma per ogni salvataggio o modifica, ma protegge dalla perdita di dati come l'eliminazione di un record. G168: la richiesta di conferma dice l'azione scelta e le sue conseguenze.

**Soglie ed eccezioni.** Livello AA. Sufficienti per gli atti legali: G164 (un tempo dichiarato entro cui modificare o annullare la richiesta), G98 (rivedere e correggere prima di inviare), G155 (casella di conferma oltre al pulsante); per le eliminazioni: G99 (recuperare ciò che si è eliminato), G168 (chiedere conferma), G155. Consigliate: SCR18, G199.

**In DottorCloud.** Emettere una fattura: il dialogo controlla la bozza (da_correggere) e tiene spento «Emetti» finché ci sono errori, ma «Emetti» parte senza conferma (emetti() in Invoices/InvoiceDialog.vue): aggiungere una conferma che dica la conseguenza («Avrà il numero 2026/45 e partirà per lo SdI»). La modalità di pagamento non deve avere un valore già scelto. Firmare un modulo o un preventivo: rivedere prima di firmare. Eliminare: una conferma con il nome e la conseguenza, oppure Annulla, oppure un cestino. Spegnere un consenso (l'informativa privacy) chiede conferma dicendo che cosa cambia. Il pulsante di una riga dice ciò che fa davvero («Prepara la fattura» se crea una bozza). Per il paziente: l'acconto pagato su /prenota e gli acquisti dall'area sono transazioni finanziarie, il preventivo firmato nell'area un impegno legale.

**Come si verifica.** Elenco delle azioni irreversibili (emissione, invio allo SdI e al Sistema TS, firma, pagamento, eliminazione, consenso); per ognuna trovare la revisione, la conferma o l'annullamento.

**Errori da evitare.** «Modalità di pagamento» già su «Bonifico» (MP05, predefinito del DocType CRM Invoice) prima di sapere come ha pagato la persona (studio UX, ottobre 2026; ora una riga avvisa che va confermata, il valore resta). «Emetti la fattura» crea una bozza che esce dalle cose da fare (studio UX, ottobre 2026). Un ambulatorio si eliminava con un tocco, senza conferma (studio UX, ottobre 2026; corretto con una conferma che lo nomina). L'interruttore dei consensi salva subito, anche per l'informativa privacy (studio UX, ottobre 2026). «Attiva la fatturazione» sta sopra prerequisiti presentati come facoltativi (studio UX, ottobre 2026; da decidere).

**Vedi anche.** [FORM-IRREVERSIBILE](06-moduli.md#form-irreversibile--prima-di-un-invio-che-non-si-ritira-rivedere-confermare-o-poter-annullare)

**Fonti.**

- [Success Criterion 3.3.4 Error Prevention (Legal, Financial, Data) (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#error-prevention-legal-financial-data) — Criterio 3.3.4, livello AA: Reversible, Checked, Confirmed · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/20/error-prevention-legal-financial-data.html))
- [legal commitments (definizione)](https://www.w3.org/TR/WCAG22/) — definizione ed esempi («a contract of any type») · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/terms/20/legal-commitments.html))
- [Understanding Error Prevention (Legal, Financial, Data)](https://www.w3.org/WAI/WCAG22/Understanding/error-prevention-legal-financial-data.html) — Intent (nessuna conferma per ogni salvataggio); Examples · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/20/error-prevention-legal-financial-data.html))
- [G168: Requesting confirmation to continue with selected action](https://www.w3.org/WAI/WCAG22/Techniques/general/G168) — Description · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/general/G168.html))
- [G98: Providing the ability for the user to review and correct answers before submitting](https://www.w3.org/WAI/WCAG22/Techniques/general/G98) — Description · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/general/G98.html))
- [G99: Providing the ability to recover deleted information](https://www.w3.org/WAI/WCAG22/Techniques/general/G99) — Description · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/general/G99.html))
- [G164: Providing a stated time within which an online request (or transaction) may be amended or canceled by the user after making the request](https://www.w3.org/WAI/WCAG22/Techniques/general/G164) — titolo e Description · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/general/G164.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'error-prevention-legal-financial-data', righe 1222-1240 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-3.3.7 · Non si chiede due volte ciò che il sistema sa già (3.3.7, A)

**Regola.** Nello stesso processo, ciò che l'utente ha già inserito o che gli è stato fornito e serve di nuovo è proposto già compilato o si sceglie sulla stessa pagina, salvo quando reinserirlo è essenziale, serve alla sicurezza o il dato non è più valido.

**Perché.** Ricordare ciò che si è già scritto pesa su chi ha difficoltà cognitive o di memoria e porta a errori o all'abbandono (Understanding, Intent). L'Understanding: il criterio riguarda un processo, non sessioni diverse; il completamento automatico del browser non basta, perché è il sito a dover offrire il dato; ciò che si sceglie deve stare sulla stessa pagina; non chiede di conservare dati tra le sessioni e, se si conservano per non farli riscrivere, vanno protetti.

**Soglie ed eccezioni.** Livello A. Sufficiente: G221 (dati del passo precedente).

**In DottorCloud.** Già oggi: /prenota parte da BOOT.prefill (nome, email, telefono, per chi; crm/www/prenota.py); la fattura nasce dall'appuntamento (issue_from_appointment in crm/invoicing/api.py); i dati di fatturazione vengono dal profilo di fatturazione (CRM Billing Profile). Da fare: «Crea una trattativa» parte dalla scelta di una persona esistente, con una ricerca che mostra anche telefono o data di nascita, e solo dopo «Nuova persona».

**Come si verifica.** Percorrere ogni processo a più passi (prenotazione, trattativa, fattura, modulo) e contare i dati chiesti due volte.

**Errori da evitare.** «Crea una trattativa» apre per primi i campi dell'azienda (dieci sul telefono, dal layout DEAL_QUICK_ENTRY) con «Scegli una persona esistente» spento sotto la piega: chi compila riscrive il nome e crea un doppione (studio UX, ottobre 2026).

**Vedi anche.** [FORM-NON-RICHIEDERE](06-moduli.md#form-non-richiedere--ciò-che-il-sistema-sa-già-non-si-chiede-di-nuovo)

**Fonti.**

- [Success Criterion 3.3.7 Redundant Entry (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#redundant-entry) — Criterio 3.3.7, livello A, ed eccezioni · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/22/redundant-entry.html))
- [Understanding Redundant Entry](https://www.w3.org/WAI/WCAG22/Understanding/redundant-entry.html) — Intent of Redundant Entry; Exceptions · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/22/redundant-entry.html))
- [G221: Provide data from a previous step in a process](https://www.w3.org/WAI/WCAG22/Techniques/general/G221) — Description e Tests · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/general/G221.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'redundant-entry', righe 1264-1270 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### WCAG-3.3.8 · Entrare senza test di memoria: incolla, gestore di password, link, passkey (3.3.8, AA)

**Regola.** Nessun passo dell'accesso chiede un test di funzione cognitiva (ricordare una password, risolvere un enigma, ricopiare caratteri) senza un'alternativa o un aiuto: incollare e i gestori di password funzionano, il codice si incolla tutto insieme, un link via email o una passkey evitano di ricordare.

**Perché.** Ricordare una password o ricopiare un codice è un ostacolo molto alto per alcune persone con disabilità cognitive (Understanding, Intent). Per la definizione WCAG ricordare, trascrivere, scrivere senza errori, fare calcoli e risolvere enigmi sono test cognitivi, mentre nome, email e telefono no. L'Understanding: un codice da ricopiare a mano non basta, deve potersi incollare; i campi separati per cifra falliscono se incollare il codice intero non li riempie tutti (F109); le chiavi hardware e lo sblocco del sistema (Touch ID, Face ID, Windows Hello) non sono test cognitivi; un comando per mostrare la password aiuta.

**Soglie ed eccezioni.** Livello AA. Eccezioni AA: riconoscere oggetti, riconoscere contenuto personale fornito dall'utente. Sufficienti: G218 (link via email), H100 (campi marcati: nell'esempio autocomplete='email' e 'current-password'; incolla e gestori di password non bloccati). Fallimento: F109.

**In DottorCloud.** Modello da tenere: l'area ha un solo campo sotto sei caselle disegnate, inputmode='numeric', autocomplete='one-time-code', maxlength=6, che accetta l'incolla intero e toglie ciò che non è cifra (area/pages/Login.vue, area/components/CodeDialog.vue); il link nelle email dell'area entra senza codice (crm/area/collegamento.py); le passkey (crm/area/passkey.py); /modulo e /documento hanno lo stesso campo per il codice (crm/www/modulo.html, crm/www/documento.html) e un pulsante esplicito. L'accesso dello staff (la pagina del framework) deve accettare l'incolla e i gestori di password, con l'autocomplete giusto. Nessun CAPTCHA a enigma.

**Come si verifica.** Provare un gestore di password e l'incolla su ogni campo di accesso e di codice; ispezionare gli attributi autocomplete.

**Errori da evitare.** Da verificare l'accesso dello staff: etichette a 4,17:1, nessun h1, titolo «Login» (studio UX, ottobre 2026).

**Vedi anche.** [FORM-INCOLLA](06-moduli.md#form-incolla--incollare-e-farsi-aiutare-sempre), [PRIV-STEP-UP](../../verticali/clinica/principi-sanitari.md#priv-step-up--prima-di-scaricare-un-dato-sanitario-una-verifica-recente)

**Fonti.**

- [Success Criterion 3.3.8 Accessible Authentication (Minimum) (WCAG 2.2)](https://www.w3.org/TR/WCAG22/#accessible-authentication-minimum) — Criterio 3.3.8, livello AA: Alternative, Mechanism, Object Recognition, Personal Content; note · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/sc/22/accessible-authentication-minimum.html))
- [cognitive function test (definizione)](https://www.w3.org/TR/WCAG22/) — definizione ed esempi · W3C – Accessibility Guidelines Working Group (AG WG) · WCAG 2.2, Raccomandazione W3C ripubblicata il 12/12/2024; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/guidelines/terms/22/cognitive-function-test.html))
- [Understanding Accessible Authentication (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication-minimum.html) — Intent; Login forms; Copy and paste; Two-factor authentication systems; Hiding characters · W3C – Accessibility Guidelines Working Group (AG WG) · documento informativo; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/22/accessible-authentication-minimum.html))
- [F109: Failure of Success Criterion 3.3.8 and 3.3.9 due to preventing password or code re-entry in the same format](https://www.w3.org/WAI/WCAG22/Techniques/failures/F109) — Description ed Examples · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/failures/F109.html))
- [H100: Providing properly marked up email and password inputs](https://www.w3.org/WAI/WCAG22/Techniques/html/H100) — Description ed Examples · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/html/H100.html))
- [G218: Email link authentication](https://www.w3.org/WAI/WCAG22/Techniques/general/G218) — Description · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/general/G218.html))
- [understanding.11tydata.js (tecniche associate a ogni criterio)](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/understanding/understanding.11tydata.js) — blocco 'accessible-authentication-minimum', righe 1272-1282 · W3C – Accessibility Guidelines Working Group (AG WG) · sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026

### APG-TASTIERA · Tab tra i componenti, frecce dentro; focus mai perso; barre di strumenti

**Regola.** Tab e Shift+Tab passano da un componente all'altro; dentro un componente composto (schede, gruppo di radio, menu, listbox, griglia, barra di strumenti) ci si muove con le frecce, con un solo arresto di Tab, gestito con tabindex mobile o con aria-activedescendant. Il focus non finisce mai sul body; le scorciatoie si aggiungono alla navigazione, non la sostituiscono.

**Perché.** Le Authoring Practices riprendono le convenzioni dei sistemi operativi perché chi usa una tecnologia assistiva se le aspetta: un solo arresto per componente accorcia il giro dei Tab, le frecce muovono dentro. Avvertono che far seguire la selezione al focus è dannoso quando ogni spostamento chiede dati alla rete; che nelle convenzioni dei loro esempi le voci disattivate di listbox, menu, schede e alberi restano raggiungibili (aria-disabled), perché chi usa uno screen reader scopre gli elementi soprattutto muovendo il focus; che il focus iniziale al caricamento della pagina si mette solo se la pagina ha una funzione principale che quasi tutti usano subito e se la si usa spesso.

**Soglie ed eccezioni.** Tabindex mobile: un elemento a 0, gli altri a −1, aggiornati anche al clic e al tocco; aria-activedescendant con il focus DOM sul contenitore. Barra di strumenti: un arresto, frecce, Home ed End facoltativi, solo con almeno 3 controlli, al massimo un controllo che usa le stesse frecce (un campo di testo) e per ultimo, un nome (aria-label o aria-labelledby), una scorciatoia documentata per raggiungerla dove serve (dall'area di testo di un editor alla sua barra).

**In DottorCloud.** I componenti di reka-ui (Tabs, RadioGroup, DropdownMenu, Toolbar) hanno già il tabindex mobile: usarli invece di costruirne. Le righe di una lista restano arresti separati (modello tabella). Components/PersonHeader.vue dichiara role='toolbar' (con aria-label) ma ogni tasto è un arresto di Tab e le frecce non fanno nulla: o la navigazione a frecce della barra di strumenti, o niente ruolo. La barra dell'editor di frappe-ui (data-slot='fixed-menu') non ha il ruolo: se lo prende, prende anche le frecce. useKeyboardShortcuts ignora chi scrive.

**Come si verifica.** Contare i Tab per attraversare la pagina; dentro ogni componente composto verificare frecce, Home, End e dove torna il focus. axe: aria-required-children, aria-required-parent, tabindex.

**Errori da evitare.** PersonHeader.vue: role='toolbar' senza frecce né tabindex mobile (rilevato nel codice il 12/10/2026). Voci di menu e schede disattivate con disabled invece di aria-disabled spariscono dalla navigazione: verificarle quando si aggiungono (regola per i nuovi componenti).

**Fonti.**

- [Developing a Keyboard Interface](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/) — Fundamental Keyboard Navigation Conventions; Discernible and Predictable Keyboard Focus; Deciding When to Make Selection Automatically Follow Focus; Keyboard Navigation Inside Components (roving tabindex, aria-activedescendant, Note); Focusability of disabled controls; Keyboard Shortcuts > Ensure Basic Access Via Navigation · W3C WAI – Authoring Practices Task Force dell'ARIA Working Group · sorgente al commit 0f765e4 del 29/09/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/aria-practices/blob/0f765e4dc33e966026114ac12a8380db1de3b787/content/practices/keyboard-interface/keyboard-interface-practice.html))
- [Toolbar Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/toolbar/) — About This Pattern; Keyboard Interaction (e Note); WAI-ARIA Roles, States, and Properties · W3C WAI – Authoring Practices Task Force dell'ARIA Working Group · sorgente al commit 0f765e4 del 29/09/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/aria-practices/blob/0f765e4dc33e966026114ac12a8380db1de3b787/content/patterns/toolbar/toolbar-pattern.html))

### APG-DIALOG · Finestre modali e richieste di conferma (dialog e alertdialog)

**Regola.** Una finestra modale ha role dialog (o è l'elemento dialog nativo), un nome dal suo titolo visibile (aria-labelledby) ed è davvero modale: il resto della pagina è inerte. All'apertura il focus va al primo elemento, oppure a un elemento statico in cima con tabindex −1 se il contenuto è lungo o strutturato, oppure all'azione meno distruttiva se l'azione è difficile da annullare; Tab e Shift+Tab girano dentro; Esc chiude; alla chiusura il focus torna al comando che l'ha aperta, salvo che non esista più. Una richiesta di conferma è un alertdialog con aria-describedby sul messaggio.

**Perché.** Lo screen reader deve sapere che il resto è inerte e che cosa chiede la finestra; chi usa la tastiera deve ritrovarsi dove era. Le Authoring Practices raccomandano fortemente un pulsante visibile per chiudere; chiedono di marcare una finestra con aria-modal solo se il resto è davvero bloccato e coperto per tutti, e ammettono, nelle implementazioni precedenti, aria-hidden sul resto della pagina. H102 elenca ciò che l'elemento dialog nativo fa da sé: focus dentro all'apertura, ritorno al comando, resto inerte, Esc che chiude.

**Soglie ed eccezioni.** Esc chiude; il focus resta dentro; per un'azione irreversibile il focus iniziale va all'azione meno distruttiva (per esempio «Annulla»).

**In DottorCloud.** Il Dialog di frappe-ui usa DialogContent di reka-ui: role='dialog', aria-labelledby dal titolo (DialogTitle), il resto della pagina nascosto con aria-hidden (useHideOthers), il focus tenuto dentro (FocusScope) e rimesso all'elemento di prima o al body alla chiusura; rispetta [autofocus]; useFirstFieldFocus sceglie il primo campo. Quando l'elemento di prima non c'è più, portare il focus dove ha senso (pages/Calendar.vue lo fa già: elemento di prima o #titolo-pagina). Le conferme di createDialog (utils/dialogs.jsx, per esempio «Are you sure you want to delete this event?» in pages/Calendar.vue) mettono il messaggio nel corpo, non come descrizione: diventano alertdialog con aria-describedby sul messaggio e il focus iniziale su «Annulla». Sul telefono la finestra è un foglio con titolo e azioni che restano; Indietro la chiude (chiudeConIndietro in utils/indietro.js).

**Come si verifica.** Aprire ogni finestra da tastiera: titolo annunciato, Tab che gira dentro, Esc che chiude, focus che torna. axe aria-dialog-name (buona pratica), aria-hidden-focus.

**Errori da evitare.** Le Impostazioni sul computer non avevano la X (studio UX, ottobre 2026; corretto). Sul telefono il focus iniziale cadeva sul pulsante indietro, con l'anello (studio UX, ottobre 2026). Sotto il pannello del nuovo appuntamento la barra in basso restava attiva e un tocco perdeva i dati (studio UX, ottobre 2026; corretto: ora la pagina chiede prima di lasciarla, onBeforeRouteLeave in Calendar/AppointmentPanel.vue). Indietro di Android perdeva l'appuntamento, poi chiedeva due volte (revisione del codice, ottobre 2026; corretto).

**Vedi anche.** [ARIA-DIALOG](02-wcag-percepibile-e-robusto.md#aria-dialog--finestre-un-nome-una-modalità-vera-il-fuoco-dentro-e-il-ritorno)

**Fonti.**

- [Dialog (Modal) Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/) — About This Pattern; Keyboard Interaction (note sul focus iniziale e sul ritorno, pulsante per chiudere); WAI-ARIA Roles, States, and Properties (note su aria-modal e aria-hidden) · W3C WAI – Authoring Practices Task Force dell'ARIA Working Group · sorgente al commit 0f765e4 del 29/09/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/aria-practices/blob/0f765e4dc33e966026114ac12a8380db1de3b787/content/patterns/dialog-modal/dialog-modal-pattern.html))
- [Alert and Message Dialogs Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/alertdialog/) — About This Pattern; Keyboard Interaction; WAI-ARIA Roles, States, and Properties (aria-describedby sul messaggio) · W3C WAI – Authoring Practices Task Force dell'ARIA Working Group · sorgente al commit 0f765e4 del 29/09/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/aria-practices/blob/0f765e4dc33e966026114ac12a8380db1de3b787/content/patterns/alertdialog/alertdialog-pattern.html))
- [H102: Creating modal dialogs with the HTML dialog element](https://www.w3.org/WAI/WCAG22/Techniques/html/H102) — Description · W3C – Accessibility Guidelines Working Group (AG WG) · tecnica informativa; sorgente al commit 23bad59 del 04/10/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/wcag/blob/23bad5904949904275a08f1c6e395b78a02aa6f3/techniques/html/H102.html))

### APG-TABS · Schede di un record (tablist)

**Regola.** Ruoli tablist, tab e tabpanel; aria-selected sulla scheda attiva, aria-controls verso il pannello, il pannello etichettato dalla sua scheda, la tablist con un nome; Tab entra sulla scheda attiva e poi va al pannello; frecce sinistra e destra tra le schede, che ricominciano dai capi; Home ed End facoltativi; attivazione automatica solo se il pannello compare senza ritardi percepibili, altrimenti manuale con Spazio o Invio.

**Perché.** Lo screen reader annuncia ruolo, posizione e stato («scheda 2 di 7, selezionata») e chi usa la tastiera attraversa la barra con un solo Tab. Le Authoring Practices raccomandano l'attivazione automatica solo se i pannelli si mostrano senza latenza (di solito perché precaricati): altrimenti rallenta lo spostamento del focus e ostacola molto chi naviga tra le schede.

**Soglie ed eccezioni.** Un arresto di Tab per tutta la barra; attivazione automatica solo senza latenza; un pannello che non comincia con un elemento focalizzabile prende tabindex 0.

**In DottorCloud.** SchedeDelRecord.vue (computer) usa TabsRoot, TabsList (aria-label «Sezioni») e TabsTrigger di reka-ui con l'attivazione automatica predefinita: ogni freccia apre la scheda, e reka smonta i pannelli nascosti (unmountOnHide), quindi la scheda raggiunta si rimonta e può chiedere dati. Per le schede pesanti valutare activation-mode='manual'. Le schede che non ci stanno vanno sotto «Altro», che dice il nome della scheda aperta. Sul telefono le schede di un record sono due pannelli montati alla prima apertura e tenuti (v-show, MobileLead.vue, MobileDeal.vue), le altre dietro «Altro» (SchedeDelTelefono). L'anello delle schede è un ring nel colore d'azione con outline-none, che in Tailwind 3 è un outline trasparente: resta visibile nei colori forzati.

**Come si verifica.** Frecce tra le schede senza attese; annuncio di ruolo, posizione e stato; Tab porta nel pannello.

**Errori da evitare.** TabsTrigger di reka-ui cambia scheda alla pressione del tasto sinistro (mousedown), non al rilascio (rilevato nel codice l'11/10/2026).

**Vedi anche.** [ARIA-TABS](02-wcag-percepibile-e-robusto.md#aria-tabs--schede-tablist-con-nome-scheda-selezionata-pannello-collegato), [MOB-SCHEDE](05-telefono-e-tocco.md#mob-schede--le-schede-di-una-scheda-quante-ci-stanno-il-resto-in-altro)

**Fonti.**

- [Tabs Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/) — About This Pattern; Keyboard Interaction (nota sull'attivazione automatica); WAI-ARIA Roles, States, and Properties · W3C WAI – Authoring Practices Task Force dell'ARIA Working Group · sorgente al commit 0f765e4 del 29/09/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/aria-practices/blob/0f765e4dc33e966026114ac12a8380db1de3b787/content/patterns/tabs/tabs-pattern.html))
- [Developing a Keyboard Interface](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/) — Deciding When to Make Selection Automatically Follow Focus · W3C WAI – Authoring Practices Task Force dell'ARIA Working Group · sorgente al commit 0f765e4 del 29/09/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/aria-practices/blob/0f765e4dc33e966026114ac12a8380db1de3b787/content/practices/keyboard-interface/keyboard-interface-practice.html))

### APG-RADIO · Gruppi di radio e controlli a segmenti, mai per navigare tra pagine

**Regola.** Un gruppo di scelte esclusive è un radiogroup con un nome; Tab entra sulla radio scelta (o sulla prima); Spazio sceglie; le frecce spostano e scelgono, ricominciando dai capi; dentro una barra di strumenti le frecce spostano senza scegliere. Per passare da una pagina all'altra si usano link (con aria-current='page'), non radio.

**Perché.** Una radio annuncia uno stato da scegliere, non una destinazione: se ogni freccia cambia pagina chi usa la tastiera non può scorrere le opzioni (3.2.1, 3.2.2).

**Soglie ed eccezioni.** Un arresto di Tab per gruppo; nome del gruppo visibile o aria-label; sul telefono 44 px di altezza (telefono.css).

**In DottorCloud.** Modello: Settings/ThemeSwitcher.vue, con role='radiogroup' e aria-label «Tema», radio native nascoste dentro le etichette e l'anello sull'etichetta con has-[:focus-visible]. I TabButtons di frappe-ui (RadioGroup di reka-ui) vanno bene per i filtri che cambiano il contenuto della pagina (Tutti, Lead, Clienti, Pazienti; Mie e Di tutti; Appuntamento ed Evento); per le pagine sorelle di ViewBreadcrumbs.vue servono link in una nav.

**Come si verifica.** Frecce dentro il gruppo: cambia la scelta, non la pagina; nome del gruppo annunciato.

**Errori da evitare.** ViewBreadcrumbs.vue: pagine sorelle come radio che contengono RouterLink, annunciate come radio e cambiate dalle frecce (rilevato nel codice l'11/10/2026). I controlli a segmenti erano alti 36 px sul telefono (studio UX, ottobre 2026; ora 44 px).

**Vedi anche.** [ARIA-RADIO](02-wcag-percepibile-e-robusto.md#aria-radio--scelte-esclusive-gruppo-con-nome-frecce-stato-selezionato)

**Fonti.**

- [Radio Group Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/radio/) — Keyboard Interaction: For Radio Groups Not Contained in a Toolbar; For Radio Group Contained in a Toolbar; WAI-ARIA Roles, States, and Properties · W3C WAI – Authoring Practices Task Force dell'ARIA Working Group · sorgente al commit 0f765e4 del 29/09/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/aria-practices/blob/0f765e4dc33e966026114ac12a8380db1de3b787/content/patterns/radio/radio-group-pattern.html))

### APG-MENU · Pulsanti «⋯» e menu di azioni

**Regola.** Il pulsante che apre un menu ha aria-haspopup='menu' (o true) e aria-expanded; Invio e Spazio (e, facoltativa, freccia giù) aprono e portano sulla prima voce, freccia su (facoltativa) sull'ultima. Nel menu: frecce su e giù, Home ed End, ricerca per iniziale (facoltativa), Invio attiva e chiude, Esc chiude e riporta il focus al pulsante, Tab esce e chiude; le voci disattivate si raggiungono ma non si attivano, i separatori no.

**Perché.** Il menu raccoglie azioni secondarie: se si comporta come quelli del sistema, chi usa la tastiera o lo screen reader lo usa senza imparare nulla.

**Soglie ed eccezioni.** Focus sulla prima voce all'apertura; ritorno al pulsante con Esc; Tab e Shift+Tab non spostano tra le voci.

**In DottorCloud.** Il Dropdown di frappe-ui (DropdownMenu di reka-ui) implementa il modello: usarlo per ogni «⋯». Ogni pulsante di sola icona ha un nome con l'oggetto («Opzioni di Studio 1»), e i tre «Altro» della scheda persona hanno nomi diversi. Sul telefono il menu è un foglio di righe da 48 px (telefono.css), con lo stesso comportamento da tastiera.

**Come si verifica.** Da tastiera ogni «⋯»: apertura, frecce, Esc, ritorno del focus; nome del pulsante annunciato.

**Errori da evitare.** Tre «Altro» con significati diversi sulla stessa schermata del telefono; il «…» del cruscotto si chiama «Altro» come la voce della barra in basso (studio UX, ottobre 2026).

**Vedi anche.** [ARIA-MENU](02-wcag-percepibile-e-robusto.md#aria-menu--menu-solo-per-azioni-aperti-da-un-pulsante-che-dice-se-è-aperto), [MOB-MENU-FOGLIO](05-telefono-e-tocco.md#mob-menu-foglio--menu-e-scelte-un-foglio-di-righe-da-48)

**Fonti.**

- [Menu Button Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/menu-button/) — Keyboard Interaction; WAI-ARIA Roles, States, and Properties · W3C WAI – Authoring Practices Task Force dell'ARIA Working Group · sorgente al commit 0f765e4 del 29/09/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/aria-practices/blob/0f765e4dc33e966026114ac12a8380db1de3b787/content/patterns/menu-button/menu-button-pattern.html))
- [Menu and Menubar Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/menubar/) — Keyboard Interaction e Note (voci disattivate, separatori) · W3C WAI – Authoring Practices Task Force dell'ARIA Working Group · sorgente al commit 0f765e4 del 29/09/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/aria-practices/blob/0f765e4dc33e966026114ac12a8380db1de3b787/content/patterns/menubar/menu-and-menubar-pattern.html))

### APG-COMBOBOX · Cercare e scegliere una persona, un servizio, un professionista (combobox e listbox)

**Regola.** Un campo che propone scelte è un combobox con un popup listbox: il focus DOM resta nel campo e l'opzione attiva è indicata con aria-activedescendant; freccia giù apre o entra nella lista, Invio accetta, Esc chiude (e può svuotare), Alt+freccia giù e Alt+freccia su aprono e chiudono (facoltativi); aria-autocomplete dice il tipo di completamento; le opzioni hanno nomi brevi che non cominciano tutti con le stesse parole; una listbox non contiene elementi interattivi (per quelli serve una griglia).

**Perché.** Scegliere la persona giusta è il gesto più frequente del banco: lo screen reader deve annunciare nome e valore del campo, l'opzione attiva e che cosa distingue due omonimi; la tastiera non deve lasciare il campo. Le Authoring Practices avvertono che nomi lunghi o che cominciano tutti uguali costringono a riascoltare la stessa parte prima di sentire ciò che distingue.

**Soglie ed eccezioni.** Completamento: nessuno, lista a scelta manuale, lista a scelta automatica, in linea (aria-autocomplete none, list, both). Listbox: Home ed End fortemente raccomandati oltre 5 opzioni; ricerca per iniziale raccomandata, soprattutto oltre 7.

**In DottorCloud.** Controls/Link.vue usa la copia locale components/frappe-ui/Autocomplete.vue: un pulsante con aria-haspopup='listbox' e aria-expanded apre un Popover di frappe-ui con il Combobox di @headlessui/vue e il suo campo di ricerca; verificare che pulsante, popover e campo siano annunciati come un solo combobox. Le opzioni degli omonimi portano nel testo un secondo dato (telefono, data di nascita); il numero di risultati in una regione role='status'. Le opzioni si chiedono quando la lista si apre (Link.vue).

**Come si verifica.** Con VoiceOver e NVDA: annuncio di ruolo, numero di risultati e opzione attiva; solo tastiera dall'apertura alla scelta.

**Errori da evitare.** Doppioni creati perché nella nuova trattativa la persona esistente non si sceglieva per prima (studio UX, ottobre 2026). Calendar/Attendee.vue e Controls/EmailMultiSelect.vue scelgono alla pressione (rilevato nel codice l'11/10/2026).

**Fonti.**

- [Combobox Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/) — About This Pattern (popup e forme di completamento); Keyboard Interaction; WAI-ARIA Roles, States, and Properties · W3C WAI – Authoring Practices Task Force dell'ARIA Working Group · sorgente al commit 0f765e4 del 29/09/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/aria-practices/blob/0f765e4dc33e966026114ac12a8380db1de3b787/content/patterns/combobox/combobox-pattern.html))
- [Listbox Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/listbox/) — About This Pattern (nomi brevi, niente elementi interattivi); Keyboard Interaction (Home, End, ricerca per iniziale) · W3C WAI – Authoring Practices Task Force dell'ARIA Working Group · sorgente al commit 0f765e4 del 29/09/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/aria-practices/blob/0f765e4dc33e966026114ac12a8380db1de3b787/content/patterns/listbox/listbox-pattern.html))

### APG-DISCLOSURE · Sezioni che si aprono e si chiudono (disclosure e fisarmonica)

**Regola.** Il comando che apre e chiude una sezione è un pulsante vero con aria-expanded true o false (e, se serve, aria-controls); Invio e Spazio lo azionano. Se la sezione ha un titolo (una fisarmonica), il pulsante sta dentro l'intestazione ed è l'unico elemento dentro di essa: le azioni della sezione restano fuori.

**Perché.** Una sezione che si apre con un div cliccabile non si raggiunge da tastiera e lo screen reader non sa che si apre: il contenuto resta nascosto a chi non usa il mouse.

**Soglie ed eccezioni.** Un arresto di Tab per sezione; stato annunciato «compresso» o «espanso».

**In DottorCloud.** CollapsibleSection.vue: l'intestazione predefinita diventa un button type='button' con aria-expanded dentro il titolo, e lo slot actions resta fuori dall'intestazione; vale per FieldLayout/Section.vue, SidePanelLayout.vue, Calendar/AppointmentPanel.vue, Calendar/CalendarEventPanel.vue, Waiting/WaitingSection.vue, BillingProfileSection.vue, ConsentsSection.vue, CyclesSection.vue e gli altri che la usano. Lo stesso per le intestazioni scritte a mano nello slot header: il gruppo delle viste salvate in AppSidebar.vue (SidebarLabel con @click), i contatti di pages/Deal.vue e pages/MobileDeal.vue, EventNotificationsArea.vue. Modelli già giusti: EmailEditor.vue, Plans/PlanItemEditor.vue, Plans/LibraryPicker.vue.

**Come si verifica.** Tab raggiunge ogni intestazione; Invio e Spazio aprono e chiudono; lo screen reader annuncia lo stato.

**Errori da evitare.** CollapsibleSection.vue con l'intestazione div @click, senza tabindex, ruolo né aria-expanded, e le intestazioni scritte a mano con lo stesso difetto (rilevato nel codice l'11/10/2026, elenco completato il 12/10/2026).

**Vedi anche.** [UX-DISCLOSURE](01-interazione.md#ux-disclosure--divulgazione-progressiva)

**Fonti.**

- [Disclosure (Show/Hide) Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/) — Keyboard Interaction; WAI-ARIA Roles, States, and Properties · W3C WAI – Authoring Practices Task Force dell'ARIA Working Group · sorgente al commit 0f765e4 del 29/09/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/aria-practices/blob/0f765e4dc33e966026114ac12a8380db1de3b787/content/patterns/disclosure/disclosure-pattern.html))
- [Accordion Pattern (Sections With Show/Hide Functionality)](https://www.w3.org/WAI/ARIA/apg/patterns/accordion/) — WAI-ARIA Roles, States, and Properties (pulsante dentro l'intestazione, unico elemento al suo interno) · W3C WAI – Authoring Practices Task Force dell'ARIA Working Group · sorgente al commit 0f765e4 del 29/09/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/aria-practices/blob/0f765e4dc33e966026114ac12a8380db1de3b787/content/patterns/accordion/accordion-pattern.html))

### APG-SWITCH · Interruttori che dicono che cosa accendono

**Regola.** Un interruttore ha role switch con aria-checked (o è una casella nativa); Spazio lo aziona (Invio facoltativo); il suo nome non cambia quando cambia lo stato; più interruttori insieme stanno in un gruppo (fieldset o role='group') con un nome; una spiegazione si lega con aria-describedby.

**Perché.** Per le Authoring Practices è critico che l'etichetta resti uguale nei due stati: «Attiva» che diventa «Disattiva» non dice più se è acceso. Chi non vede il colore deve sentire lo stato e capire che cosa accende; per un'impostazione «acceso/spento» si legge meglio di «selezionato».

**Soglie ed eccezioni.** Binario spento almeno 3:1 con lo sfondo (1.4.11); la riga intera come bersaglio quando le parole sono il suo label.

**In DottorCloud.** Lo Switch di frappe-ui è sistemato alla compilazione (vite/frappeUi.js: il nome va al suo pulsante, l'1 del server è disegnato acceso); dentro SettingsRow le parole sono il suo label, fuori serve aria-label con le parole accanto. Accanto all'interruttore la frase dice l'effetto («Chiesto alle persone»); spegnere ciò che ha effetti legali chiede conferma (3.3.4). Il binario spento #858c8a fa 3,43:1 sul bianco; la manopola rispetta la riduzione del movimento (espresso.css).

**Come si verifica.** Annuncio di nome, ruolo e stato; Spazio aziona; toccare le parole accanto aziona l'interruttore.

**Errori da evitare.** Interruttore dei consensi con il solo titolo del consenso come nome, che salva subito anche l'informativa; profili social accesi con Meta non collegata; parole degli interruttori della nuova trattativa in un div; binario spento a 1,29:1 (studio UX, ottobre 2026; il binario è corretto).

**Vedi anche.** [ARIA-SWITCH](02-wcag-percepibile-e-robusto.md#aria-switch--interruttori-ruolo-switch-stato-acceso-o-spento-nome-che-non-cambia)

**Fonti.**

- [Switch Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/switch/) — About This Pattern («Important: it is critical the label on a switch does not change when its state changes»); Keyboard Interaction; WAI-ARIA Roles, States, and Properties · W3C WAI – Authoring Practices Task Force dell'ARIA Working Group · sorgente al commit 0f765e4 del 29/09/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/aria-practices/blob/0f765e4dc33e966026114ac12a8380db1de3b787/content/patterns/switch/switch-pattern.html))

### APG-TABELLA · Liste come tabelle, griglie solo dove servono, ordinamento annunciato

**Regola.** Una lista di record con colonne è una tabella (table, o role='table' con row, columnheader, cell) e non un componente composto: ogni controllo dentro è un arresto di Tab. La colonna ordinata porta aria-sort (ascending, descending, other) sulla sua intestazione, di norma una sola. Una griglia (role='grid') si usa quando serve muoversi tra le celle con le frecce o quando i controlli sono tanti: un arresto, frecce, Pagina su e giù, Home ed End, Ctrl+Home e Ctrl+End.

**Perché.** Lo screen reader legge una tabella per righe e colonne e annuncia l'intestazione di ogni cella; senza ruoli una lista è una fila di testi senza relazione. Le Authoring Practices: una tabella non è un widget, quindi ogni controllo dentro è un arresto; se i controlli sono molti, una griglia accorcia molto il giro dei Tab; ARIA non sa dire più livelli di ordinamento, quindi aria-sort su più colonne vale poco.

**Soglie ed eccezioni.** aria-sort su una colonna alla volta; intestazioni di colonna con un nome; la tabella con un nome (aria-labelledby o aria-label) e, se serve, una descrizione (aria-describedby).

**In DottorCloud.** La ListView di frappe-ui usata dalle liste (components/ListViews/\*ListView.vue) non ha ruoli di tabella; la nuova molecola list di frappe-ui ha l'ordinamento con aria-sort (molecules/list/ListHeaderCellSort.vue): aggiungere i ruoli o passare a quella. L'ordinamento oggi si sceglie da ViewControls.vue (SortBy): dirlo anche sull'intestazione con aria-sort e in una didascalia («Ordinate per data di creazione, dalla più recente»). Le caselle di selezione hanno già il nome della riga («Seleziona `<persona>`», vite/frappeUi.js); la riga si apre dal pulsante steso (.riga-stesa) con gli altri controlli sopra.

**Come si verifica.** axe td-headers-attr, th-has-data-cells, aria-required-children, nested-interactive; scope-attr-valid ed empty-table-header (buone pratiche); navigazione per tabella dello screen reader.

**Errori da evitare.** Righe di Da fare e Chiamate come button che contengono la casella (20 nodi nested-interactive); 21 caselle senza nome per lista (studio UX, ottobre 2026; i nomi sono stati aggiunti); ListView senza ruoli di tabella (rilevato nel codice l'11/10/2026).

**Vedi anche.** [UX-TABELLE](01-interazione.md#ux-tabelle--tabelle-e-liste-di-dati)

**Fonti.**

- [Table Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/table/) — About This Pattern; WAI-ARIA Roles, States, and Properties · W3C WAI – Authoring Practices Task Force dell'ARIA Working Group · sorgente al commit 0f765e4 del 29/09/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/aria-practices/blob/0f765e4dc33e966026114ac12a8380db1de3b787/content/patterns/table/table-pattern.html))
- [Grid (Interactive Tabular Data and Layout Containers) Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/grid/) — Data Grids For Presenting Tabular Information; Keyboard Interaction For Data Grids · W3C WAI – Authoring Practices Task Force dell'ARIA Working Group · sorgente al commit 0f765e4 del 29/09/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/aria-practices/blob/0f765e4dc33e966026114ac12a8380db1de3b787/content/patterns/grid/grid-pattern.html))
- [Grid and Table Properties](https://www.w3.org/WAI/ARIA/apg/practices/grid-and-table-properties/) — Indicating sort order with aria-sort · W3C WAI – Authoring Practices Task Force dell'ARIA Working Group · sorgente al commit 0f765e4 del 29/09/2026, consultata il 12/10/2026 ([sorgente letto](https://github.com/w3c/aria-practices/blob/0f765e4dc33e966026114ac12a8380db1de3b787/content/practices/grid-and-table-properties/grid-and-table-properties-practice.html))
