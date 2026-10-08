# 61 · Convenzioni, fondi sanitari e assicurazioni

**Stato:** fatto (08/10/2026). Nessuna convenzione finché il centro non ne crea una;
una convenzione compare in /prenota solo se il centro lo sceglie su quella
convenzione.

## Il bisogno

Un centro medico privato lavora con i fondi e le assicurazioni (UniSalute, Fasi,
Previmedical/RBM, Fasdac, Blue Assistance, Generali, Allianz, Casagit,
MetaSalute…) in due modi:

- **forma diretta**: il fondo autorizza prima la prestazione con un numero (la
  «pratica»), la persona paga solo la sua quota (una franchigia fissa, uno
  scoperto in percentuale, o una quota per prestazione) e il centro fattura il
  resto al fondo, di solito con **una fattura al mese**, una riga per pratica,
  caricata poi sul portale delle strutture del fondo;
- **forma indiretta**: la persona paga tutto, al prezzo della convenzione se c'è,
  e chiede il rimborso al fondo con fattura e referto.

E le **convenzioni aziendali**: uno sconto per i dipendenti di un'azienda. Una
palestra o un centro estetico le hanno uguali: per questo è del CRM
(`crm/convenzioni`), non della clinica.

## Cosa c'è

- **La convenzione** (`CRM Convention`, Impostazioni > Fatturazione > Convenzioni e
  fondi, `convenzioni.gestisci`: il responsabile del centro): il tipo (fondo
  sanitario, assicurazione, convenzione aziendale), chi paga (un'azienda di
  DottorCloud con i suoi dati di fatturazione, perché in forma diretta riceve la
  fattura elettronica), le forme (diretta, indiretta o entrambe), i prezzi (un
  **listino dell'agenda** che c'era già, uno sconto in percentuale sui prezzi del
  centro, o i prezzi del centro), la quota a carico del paziente in forma diretta
  (niente, fissa, percentuale, e per prestazione), se il fondo autorizza prima
  ogni appuntamento, le date, le note, se /prenota la propone.
- **La copertura della persona** (`CRM Convention Cover`, nella scheda Dati e nel
  Riepilogo): la convenzione, il numero di tessera o polizza, il titolare quando è
  un'altra persona (un figlio sul fondo del genitore), le date. Segue la persona e
  se ne va con lei.
- **L'appuntamento**: nel pannello dell'agenda «Paga la persona» o una
  convenzione (prima quelle della persona, con la sua tessera), la forma, il
  numero di autorizzazione. Il prezzo diventa quello della convenzione e si divide
  in **quota del paziente** e **quota del fondo**, al centesimo, arrotondando a metà
  in su (`regole.quote`); un preventivo accettato resta il prezzo concordato e si
  divide lo stesso. Senza autorizzazione, quando il fondo la vuole, il pannello e
  l'accoglienza dicono **«Autorizzazione mancante»**.
- **/prenota**: chi prenota può dire che viene con un fondo tra quelli che il
  centro propone online, e scrivere la tessera; la prenotazione aspetta allora il
  sì del centro, non chiede acconti, e la copertura è scritta sulla persona «da
  verificare».
- **La fattura della persona**: in forma diretta è la sua quota sola; se il fondo
  paga tutto non c'è nulla da fatturarle e l'appuntamento non compare tra quelli
  da fatturare. In forma indiretta è il prezzo della convenzione.
- **Le pratiche e l'estratto del mese** (Fatture > Convenzioni, `fatture.vedi`):
  per ogni convenzione in forma diretta e mese, le pratiche con il loro stato (da
  autorizzare, autorizzata, eseguita da fatturare, nella bozza al fondo,
  fatturata, pagata dal fondo, annullata, non presentato), quanto hanno pagato i
  pazienti e quanto resta da fatturare al fondo. **«Fattura al fondo»**
  (`fatture.emetti`) fa la bozza: una fattura dal motore di DottorCloud
  (`emissione`), all'azienda che paga, destinatario con partita IVA, una riga per
  pratica alla quota del fondo con prestazione, paziente, data, numero di
  autorizzazione e tessera; si apre nel dialogo della fattura per controllarla ed
  emetterla. Una bozza eliminata o una fattura annullata rimette le pratiche da
  fatturare. **«Esporta il mese»** dà il CSV per il portale del fondo (punto e
  virgola, virgola decimale, date all'italiana). Le regole della fattura in prova
  valgono come sempre: un'azienda in prova fa fatture di prova.
- **La dashboard**: «Da incassare dai fondi», per convenzione e per da quanto
  aspetta (le stesse fasce di «Da incassare»).
- **I dati di prova**: Salute+, un'assicurazione in forma diretta sul listino
  «Convenzione Salute+» che c'era già (il paziente paga il 20%, autorizzazione
  prima di ogni visita), con cinque persone coperte, le loro visite delle ultime
  settimane autorizzate ed eseguite e una ancora da autorizzare; lo sconto del 10%
  ai dipendenti dello Studio Bianchi, in forma indiretta.

## Il Sistema TS

Il centro comunica al Sistema TS **solo la spesa sostenuta dalla persona**, cioè
la fattura intestata a lei: in forma diretta la sua quota, in forma indiretta il
prezzo intero (che la persona porterà al fondo per il rimborso). La fattura al
fondo va a un soggetto con partita IVA, per lo SdI, e **non va al Sistema TS**: il
Sistema TS conosce solo le persone fisiche.

Dove lo dice il repository:

- `crm/invoicing/engine/classificazione.py`, il ramo «Towards VAT subjects, the
  PA and abroad the channel is always the SdI, and there is no Sistema TS report:
  the Sistema TS only knows natural persons»: una fattura a un'azienda esce per lo
  SdI con `ts_status` «non applicabile»; il test
  `crm/convenzioni/tests/test_convenzioni.py` lo verifica sulla fattura al fondo.
- `docs/verticali/clinica/ricerca.md` §2.1: verso chi ha partita IVA (aziende,
  assicurazioni, fondi) la fattura elettronica via SdI è obbligatoria, **senza
  dati sanitari non necessari** (FAQ dell'Agenzia delle Entrate sulle prestazioni
  sanitarie). Per questo la riga al fondo dice la prestazione, il paziente, il
  giorno, il numero di autorizzazione e la tessera, e niente codice fiscale né
  diagnosi.

Fuori dal repository (una ricerca in rete, 08/10/2026, da verificare con il
commercialista): una spesa documentata da una fattura non intestata all'assistito
non gli è attribuibile e non si comunica; i rimborsi delle prestazioni in
convenzione diretta li comunicano all'Agenzia gli enti e le casse stessi, con il
criterio di cassa (nota Mefop dell'11/07/2016; le specifiche tecniche sono quelle
del D.M. 31/07/2015, Allegato A). Il tracciato che DottorCloud scrive
(`crm/tessera_sanitaria/engine/tracciato.py`, `VoceSpesa`) non ha un campo per la
quota pagata da un terzo nello stesso documento: per questo il centro emette due
documenti, uno alla persona e uno al fondo.

## Le scelte

- **Un appuntamento, una persona**: una convenzione vale per un appuntamento di
  una persona sola (le visite in convenzione lo sono); un posto di un abbonamento
  non si paga con una convenzione.
- **Il listino è quello dell'agenda**: una convenzione con i suoi prezzi usa un
  `CRM Price List` (le regole per professionista, orario, stanza restano); il
  listino «Convenzione Salute+» dei dati di prova è diventato la convenzione
  Salute+. Togliendo la convenzione dall'appuntamento torna il listino del centro.
- **L'estratto mensile prima della fattura per pratica**: è la prassi dei fondi;
  scegliendo un mese con una sola pratica la fattura è comunque di quella sola.
- **Una pratica fatturata non cambia convenzione**: finché la sua fattura al fondo
  esiste, la forma e la quota restano.

## Cosa resta fuori

- **I documenti per il rimborso nell'area** (fattura e referto insieme, in forma
  indiretta): l'area mostra già fatture e referti consegnati online, ognuno al suo
  posto; una sezione che li accoppi non c'è.
- **I PDF dei referti nell'esportazione del mese**: il CSV sì, i referti si
  scaricano dalla scheda della persona.
- **Il portale del fondo**: nessuna integrazione con i portali di UniSalute,
  Previmedical e gli altri (non hanno API pubbliche); l'autorizzazione si scrive a
  mano.
- **La fattura al fondo per ogni singola pratica in automatico** e l'invio da solo:
  la bozza si controlla ed emette dal dialogo.
- **Massimali e plafond** della polizza della persona: non sono tenuti.
