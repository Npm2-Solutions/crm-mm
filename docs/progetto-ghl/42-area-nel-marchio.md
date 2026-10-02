# 42 · L'area pazienti come la disegna il marchio

**Stato:** fatto (02/10/2026).

## Il bisogno

Il kit del marchio ha già le schermate del telefono del paziente: il video, le
pubblicità «A casa» e la presentazione (`brand/presentazione/sorgenti/img/
telefono-*.png`). L'area vera era più spoglia: carte grigie senza segni, titoli
piccoli, link sottolineati, la barra in basso in nero. Due cose diverse per lo
stesso prodotto.

## Cosa cambia

L'area segue quelle schermate, con i token di Espresso e i segni del marchio:

- **Titoli grandi e stretti**, le sezioni in maiuscoletto («I TUOI PIANI»).
- **Le carte** bianche, con un filo e la coda della nuvola in basso a sinistra.
- **Il prossimo appuntamento** è il blocco scuro della pagina, le croci nel suo
  angolo: il giorno e l'ora in menta («VEN 2 OTT · 10:00»), cosa, con chi,
  «Sposta o annulla».
- **Ogni tipo di cosa in una nuvola del colore della sua categoria**: un piano
  alimentare in ambra con la mela, un allenamento o gli esercizi a casa in viola
  con il manubrio, le abitudini in verde, i documenti in blu. Il tipo di piano
  dice il suo colore e la sua icona dal server (`TipoPiano.colore`, `icona`):
  un modulo che registra un tipo nuovo sceglie fra le categorie del sistema.
- **Il piano del giorno**: di che tipo è e di chi, il titolo, l'anello di quanto
  è fatto oggi nel colore del tipo; i giorni a tessera (giorno della settimana e
  numero, «OGGI» per oggi); ogni momento una carta («COLAZIONE · 07:30»).
- **La spunta in un tocco**: la nuvola accanto a ogni voce si riempie del verde
  del marchio e la carta del momento finito si tinge. «In parte» e «Saltato»
  restano sotto, come fatti e mai in rosso.
- **Il codice in sei caselle** alla porta («Entra nella tua area»), sopra un
  campo solo, così il telefono lo riempie dall'email e si incolla intero.
- **In basso cinque posti**: Oggi, Agenda, Piani (solo per chi ne segue uno),
  Documenti e Messaggi; quello aperto nel colore del marchio. Le fatture sono
  dentro Documenti, come sul telefono del kit; `/area/invoices` porta lì.
- **Il centro guida in alto**: il suo logo com'è disegnato, o la sua nuvola con le
  iniziali e il nome; il prodotto firma in fondo.

Niente cambia in quello che l'area fa: le stesse chiamate, l'anteprima del centro
(doc 41), le stesse parole.

## Come è fatta

- `frontend/src/area/area.css`: le classi `area-*` nel livello `components` di
  Tailwind, scritte per intero nei file dell'area (una classe composta a pezzi la
  build la toglierebbe).
- `frontend/src/area/aspetto.js`: le date in testa alle carte, i giorni, l'ora dei
  momenti, l'aspetto di un tipo, quanto è fatto oggi; provato in
  `tests/unit/areaAspetto.test.js`.
- `AreaChip.vue` (la nuvola con l'icona) e `NextAppointment.vue` (il blocco).
- `crm/piani/regole.py`: `TipoPiano.colore` e `icona`; `crm/piani/area.py` li
  manda con ogni piano.

## Verifiche

- Nel browser, a 390 px: accesso e codice, Oggi con due piani, il piano alimentare
  con una voce spuntata e una «in parte», agenda, piani, documenti, messaggi, chat.
- L'anteprima del centro con lo stile nuovo: la striscia, le carte vuote al loro
  posto, nessun pulsante che scrive.
- `crm/piani/tests/test_regole.py` (ogni tipo con un colore del sistema),
  `crm/clinica/tests/test_area_piani.py` (il piano alimentare in ambra con la
  mela), 866 test unitari.
