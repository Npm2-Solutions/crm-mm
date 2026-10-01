# TextInput

Il campo di testo di frappe-ui, compatto, con l'etichetta piccola sopra.

## In frappe-ui
`<TextInput variant="subtle|outline" size="sm|md|lg" label="…" :required>` (anche dentro `FormControl`). Predefinito **subtle**: fondo `surface-gray-2`, alto 28px, `rounded`; al focus fondo `surface-base`, bordo `outline-gray-4`, `shadow-sm`. Etichetta `text-xs` in `ink-gray-5`.

## Personalizzazione DottorCloud
- **Obbligatorio**: una piccola **croce** rossa dopo l'etichetta, al posto dell'asterisco.
- Al focus l'icona iniziale prende `brand-solid`; l'anello di focus è `focus`.
- **Errore**: fondo `danger-subtle`, bordo `danger` e sotto una frase in `danger` con l'icona `circle-alert` (in frappe-ui: `ErrorMessage`).
- Grigi tinti dalle variabili.

## Regole
- `subtle` nei moduli del gestionale; `outline` quando il campo sta su `surface-gray-*` o in un filtro.
- L'errore dice come rimediare ("Mancano due caratteri.").
