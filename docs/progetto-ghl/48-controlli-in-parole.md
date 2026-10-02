# 48 · Il Sistema TS e lo SdI prima di emettere, in parole

**Stato:** fatto (02/10/2026). Segue la fattura fatta dentro DottorCloud
([47](./47-fattura-dentro-dottorcloud.md)): la finestra dice tutto quello che manca
prima di emettere; qui il Sistema TS e lo SdI lo dicono anche loro, prima, e in
italiano.

## Il bisogno

Una fattura emessa non si cambia: si corregge con una nota di credito. Eppure due
controlli arrivavano solo dopo:

- **il tracciato del Sistema TS** si verificava all'emissione, a numero già dato, e
  i problemi finivano in un campo che la finestra non mostrava. Una comunicazione
  che il Sistema TS avrebbe rifiutato a gennaio partiva lo stesso;
- **i rilievi dello SdI sul file XML** comparivano solo quando l'invio veniva
  rifiutato.

E parlavano la lingua dei file: «cfCittadino is missing», «tipoSpesa 'SR' is not
admitted for subject 'professionista_sanitario'», «00400: the CedentePrestatore has
no IdFiscaleIVA». In inglese, con i nomi dei campi del tracciato e i codici al posto
delle parole.

Rileggendo i controlli dello SdI sull'elenco ufficiale ([Elenco dei controlli,
v1.8](https://www.fatturapa.gov.it/export/documenti/Elenco_Controlli_version_1.8.pdf))
alcuni codici non erano quelli che lo SdI avrebbe dato:

- il riepilogo IVA che non torna con le righe era «00423», che è invece il prezzo
  totale di una riga: è «00422», per aliquota, contando anche i contributi della
  cassa, con la tolleranza di un euro;
- «00000» non esiste: un file che lo schema rifiuta è «00200»;
- il totale del documento e una ritenuta senza righe soggette non sono controlli
  dello SdI: venivano bloccati come se lo fossero. I controlli veri sulla ritenuta
  sono l'opposto, «00411» e «00415»: una riga o un contributo soggetto a ritenuta
  e nessuna ritenuta nel documento;
- l'imposta si arrotonda per eccesso dal cinque, come chiede lo SdI, non alla pari.

## Cosa cambia

- **Il Sistema TS si controlla sulla bozza.** Mentre si scrive la fattura:
  - quello che riguarda il documento (un tipo di spesa che chi emette non può
    usare, un importo oltre il massimo, una riga senza aliquota né natura) ferma
    l'emissione, nella lista «Prima di emetterla»;
  - quello che riguarda l'azienda (il codice fiscale, i codici della struttura) si
    dice e non ferma la fattura che il paziente aspetta: «il Sistema TS rifiuterà
    la comunicazione finché l'azienda emittente non è completa: …»;
  - quello che la fatturazione dice già sul paziente e sul pagamento non si ripete.
- **Ogni messaggio in parole**, senza i nomi dei campi:
  - i tipi di spesa e le categorie con il loro nome («Prestazioni del professionista
    sanitario», «Professionista sanitario, a suo nome»);
  - gli importi come li scrivono le schermate (99.999,99 €), le aliquote come numeri
    (22%);
  - tutto nella lingua di chi legge.
- **I rilievi dello SdI** dicono cosa non va e, in fondo, il codice con cui lo SdI
  risponderebbe: «manca la partita IVA di chi emette (SdI 00200)». Il codice resta
  uguale in ogni lingua: l'assistenza lo cerca nell'elenco ufficiale, e l'invio si
  ferma solo sui rilievi che lo hanno. Un messaggio salvato prima («00400: …») si
  legge ancora.
- **Nella finestra della fattura**:
  - su una fattura emessa, quello che si è trovato all'emissione (la comunicazione
    al Sistema TS) e, prima dell'invio allo SdI, i rilievi del file;
  - «Pagata prima della fattura», quando la data di pagamento è precedente: un
    pacchetto prepagato, un acconto. Senza, la bozza restava ferma senza modo di
    sbloccarla;
  - su una nota di credito niente data di pagamento né opposizione: un rimborso si
    paga il giorno della nota, e la comunicazione al Sistema TS lo dice da sola.
- **Una fattura alla pubblica amministrazione** senza il codice ufficio di sei
  caratteri si ferma sulla bozza, invece di fallire all'emissione a numero già dato.

## Come è fatta

- `crm/invoicing/engine/messaggi.py`:
  - `Messaggio`: una frase con il suo modello e i suoi valori;
  - `Nome`: un nome di un vocabolario, tradotto con la frase;
  - `Rilievo`: un rilievo con il codice dello SdI in coda (`coda_sdi`).
- `crm/invoicing/documento.py`:
  - `in_parole()` traduce il modello, i nomi, le frasi dentro le frasi; scrive gli
    importi in euro;
  - `da_correggere()`: quello che ferma una bozza e quello che vale la pena dire, per
    l'emissione, l'anteprima e la finestra.
- `crm/invoicing/estensioni.py`: `registra_controllo_bozza`, con cui un modulo dice
  cosa rifiuterebbe più tardi.
- `crm/tessera_sanitaria/__init__.py`: `controlla_bozza`, il tracciato sulla bozza.
  `engine/tracciato.py` e `engine/classificazione.py` danno frasi in parole, e
  `GIA_DETTI` sono le frasi che la fatturazione dice già.
- `crm/invoicing/engine/fatturapa.py`: i controlli sull'elenco ufficiale (v1.8):
  - `codice_di()` legge il codice di un rilievo, anche salvato;
  - `bloccanti()` tiene i rilievi che lo SdI rifiuterebbe.
- `crm/tests/test_frasi_del_motore.py`: ogni frase dei motori è nel catalogo
  italiano, e nessuna è una f-string.

## Verifiche

- `crm/tessera_sanitaria/tests/test_bozza_ts.py` (sul sito):
  - quello che il Sistema TS rifiuterebbe ferma l'emissione;
  - quello dell'azienda si dice e non ferma;
  - il codice fiscale del paziente si dice una volta;
  - una fattura fuori dal Sistema TS non si controlla;
  - il rimborso si paga il giorno della nota.
- `crm/invoicing/tests/test_fatturapa.py`:
  - il riepilogo torna con le righe e la cassa, entro un euro (00422);
  - l'imposta si arrotonda per eccesso dal cinque (00421);
  - le ritenute (00411, 00415) e i rilievi che non sono dello SdI;
  - i codici letti sia in fondo sia in testa.
- `crm/tests/test_emissione.py`:
  - i nomi e le frasi dentro le frasi si traducono;
  - i rilievi si vedono prima dell'invio, e l'invio si ferma su quelli con il codice.
- `crm/tests/test_frasi_del_motore.py` e le suite della fatturazione e del Sistema
  TS.
- Nel browser, in italiano:
  - una riga oltre il massimo del Sistema TS («riga 1: l'importo supera quello che il
    Sistema TS accetta (99.999,99 €)»), con Emetti spento;
  - un pagamento di tre giorni prima, sbloccato da «Pagata prima della fattura».
