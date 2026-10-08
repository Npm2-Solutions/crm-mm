# Badge

Lo stato di una cosa, in una pillola.

## In frappe-ui
`<Badge theme="gray|blue|green|amber|red|violet" variant="solid|subtle|outline|ghost" size="sm|md|lg" label>`: altezze 16/20/24, `rounded-full`, `text-xs`.

## Personalizzazione DottorCloud
- Stati: `green` confermato/pagato, `amber` da confermare, `red` annullato/errore, `blue` in attesa, `gray` bozza. I colori del testo sono `success`, `warning`, `danger`, `info` (più scuri dell'Espresso dove serviva per arrivare a 4.5:1).
- **In corso** (in visita, in chiamata): `brand-subtle` con la **croce** al posto del pallino. Uno solo per riga.

## Regole
Sempre la parola; il colore da solo non basta.
