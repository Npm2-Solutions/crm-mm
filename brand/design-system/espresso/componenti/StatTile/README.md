# StatTile

Il numero della dashboard. Il primo della fila è un blocco pieno con il motivo delle croci, come la copertina.

## In frappe-ui
Nel gestionale è il widget numerico della dashboard (`components/Dashboard/`); in frappe-ui si costruisce con un `div` `rounded-xl`.

## Personalizzazione DottorCloud
- `rounded-xl` (16px) con la coda della nuvola; numero `metric` (28px bold, cifre tabulari), etichetta `text-sm` `ink-gray-6`.
- Il motivo delle **croci** nell'angolo in alto a destra: in `brand-subtle` sui riquadri chiari, in menta sul blocco.
- Il numero più importante della fila è un **blocco** `block-deep` (`dc-stat--brand`): uno per fila.

## Regole
Altezza minima 96px; 3–4 per fila.
