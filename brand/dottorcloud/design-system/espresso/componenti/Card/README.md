# Card

Il riquadro di un argomento: blocchi della scheda paziente, riepiloghi.

## In frappe-ui
Non c'è un Card in frappe-ui 1.0: è un `div` con `rounded-lg border border-outline-gray-1 p-4` (o `shadow` per le carte che galleggiano).

## Personalizzazione DottorCloud
- `rounded-lg` (12px) con la coda della nuvola; filetto `outline-gray-1`.
- Titolo `lg-semibold` con un piccolo segno a nuvola (24px) in `brand-subtle` o nel colore della categoria.
- Dati come coppie etichetta/valore (`ink-gray-5` / `ink-gray-8`).
