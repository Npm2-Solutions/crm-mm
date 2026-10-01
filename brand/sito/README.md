# Il sito con il design system

- `sito-marchio.css`: lo strato del marchio. `sito/build.mjs` lo mette in fondo a `css/sito.css`, dopo tutte le regole del sito (le sovrascrive senza toccarle; toglierlo riporta il sito com'era). Si cambia qui, non nel sito.
- `modifiche-html.diff`: le uniche modifiche all'HTML (già in `sito/pagine/index.html` e `sito/parti/cta.html`), due elementi decorativi (`aria-hidden`): i blocchi dietro al prodotto nella home (`.showcase__art`) e il blocco menta nelle chiusure (`.closing__mint`).
- `sito.md`: le regole del sito accanto a quelle del gestionale.
- `screenshot/prima` e `screenshot/dopo`: ogni pagina a 1366px e la home a 390px.
