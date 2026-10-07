# 33 — Il design system nel gestionale: DottorCloud su Espresso

> ✅ **FATTO (01/10/2026)**. Il design system del gestionale
> ([`brand/dottorcloud/design-system/espresso`](../../brand/dottorcloud/design-system/espresso/README.md))
> è applicato: i grigi di Espresso tinti del verde del marchio, il focus e le ombre
> nel suo colore, la menta come azione nel tema scuro, la coda della nuvola su
> quello con cui si agisce, la croce dove si sceglie e dove si deve compilare.
> Applicandolo il sistema è stato verificato e, dove serviva, sistemato.

## Come è applicato

Senza riscrivere nessun componente di frappe-ui: [`frontend/src/espresso.css`](../../frontend/src/espresso.css),
importato dal gestionale (`index.css`) e dall'area clienti (`area/area.css`) dopo
`marchio.css`.

- **Le variabili di frappe-ui** (`--surface-gray-*`, `--ink-gray-*`,
  `--outline-gray-*`, `--elevation-*`, `--focus-outline-default`…) prendono i valori
  del sistema, in chiaro e in scuro. Ogni pagina, ogni componente, ogni classe
  Tailwind che le usa cambia da sé.
- **Poche regole sul markup di frappe-ui** mettono i segni del marchio: la coda
  della nuvola (pulsante solid, finestre, voce attiva della barra, segmentato), la
  croce (pomello dello switch acceso, radio scelto, campi obbligatori), la linea e
  l'icona della scheda aperta, il riempimento dell'avanzamento, il toast in verde
  profondo. Sono segnate **(markup)**: dopo un aggiornamento di frappe-ui vanno
  ricontrollate ([`frappe-ui.md`](../../brand/dottorcloud/design-system/espresso/frappe-ui.md)).
- **Tutto sta sotto `[data-marchio='dottorcloud']`**: `indossa()` (`utils/marchio.js`)
  mette sulla pagina la chiave del marchio acceso. Un altro verticale, con un altro
  marchio, tiene i grigi neutri di Espresso e il suo colore d'azione.
- **Il colore dell'azione** resta in `marchio.css`, per ogni marchio
  (`--brand-action`); nel tema scuro ora è il colore del marchio su fondo scuro
  (`--brand-on-dark`, la menta), come dice il sistema. `--brand-segno` è il marchio
  come segno, mai sotto il testo: i riempimenti di cicli e abbonamenti.
- **I componenti nostri** che facevano un'azione o una scelta con il pieno grigio
  (i pulsanti dei programmi nell'area, il giorno scelto del piano e della spesa, la
  tappa aperta) prendono il colore dell'azione; i campi obbligatori di DottorCloud
  portano `segno-obbligatorio`, e la croce.

## Sistemato applicandolo

Il sistema era preciso: le luminosità dei grigi tinti coincidono con quelle di
Espresso entro 0,2 punti in entrambi i temi, e le coppie di colore degli stati e
delle categorie stanno sopra 4,5:1. Le correzioni, tutte scritte anche nel sistema
([`frappe-ui.md`](../../brand/dottorcloud/design-system/espresso/frappe-ui.md#sistemato-applicandolo)):

| Cosa | Prima | Ora |
|---|---|---|
| Grigio delle etichette (`ink-gray-5`) | 4,2:1 sul bianco, 3,9:1 sulle carte scure | `#6a716f` / `#858c8a`: ≥4,5:1, come chiede il principio 5 |
| Grigi non elencati (`ink-gray-1`, `outline-gray-6…9`, `outline-elevation-*`, `surface-elevation-3`, ombre `md` e `xl`) | neutri accanto ai tinti | tinti come gli altri |
| Azione nel tema scuro | il verde del logo | la menta |
| Icona della scheda attiva e della voce attiva | solo `svg` | anche le icone a classe `lucide-*` |
| Avanzamento | ogni `bg-surface-gray-10` dentro un binario | solo il riempimento |
| Campo obbligatorio | solo il componente di frappe-ui | anche i campi di DottorCloud |
| Tooltip | `surface-gray-9`, con la freccia di un altro colore | `surface-gray-10` tinto, come la freccia |

## Verificato

Nel browser (Playwright), con gli stili calcolati: la pagina porta il marchio, le
variabili hanno i valori del sistema, il pulsante solid ha la coda e il verde
(`#0b6f64`; menta `#5fe0cc` con il testo scuro nel tema scuro), la voce attiva
della barra la coda e l'icona verde, la checkbox la sua forma, la scheda aperta
la linea e l'icona verdi, la finestra la coda, il campo obbligatorio la croce, lo
switch acceso la croce nel pomello, la linea delle schede delle impostazioni.
Le pagine principali (dashboard, persone, una persona, trattative, agenda, lista
d'attesa, impostazioni) in chiaro e in scuro, l'area clienti sul telefono.

## Dopo

Il sistema ha altri componenti da costruire quando una schermata li chiede, con le
sue classi (`dc-avatar`, `dc-tag`, StatTile, EmptyState, PatientJourney): il
menu principale e le pagine vuote che spiegano cosa fare sono i prossimi.
