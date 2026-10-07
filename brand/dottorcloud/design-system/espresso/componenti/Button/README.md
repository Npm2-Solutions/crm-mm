# Button

Il pulsante di frappe-ui, alle sue misure, con il pieno del marchio e la coda della nuvola.

## In frappe-ui
`<Button variant="solid|subtle|outline|ghost" theme="gray|red" size="sm|md|lg">`. Misure: xs 24px, **sm 28px (predefinito)**, md 32px, lg 40px; raggio `rounded-4` (8px), lg `rounded-5`.

## Personalizzazione DottorCloud
- **solid gray** diventa il pieno del marchio: `brand-solid` (teal-700, menta nel tema scuro), testo `on-brand-solid`, hover `brand-solid-hover`. È già così in `marchio.css` (`--brand-action`).
- **La nuvola-D**: il solid (e il solid rosso) ha l'angolo in basso a sinistra a `radius-tail` (2px). È l'unica differenza di forma: per riconoscere l'azione principale a colpo d'occhio.
- **subtle del marchio** (`dc-btn--brand`): `brand-subtle` / `on-brand-subtle`, per l'azione secondaria che riguarda il paziente (Invia promemoria). In frappe-ui: `variant="subtle"` con la classe `dc-brand`.
- Grigi tinti di verde (subtle, outline, ghost) e anello di focus `focus` vengono dalle variabili, senza toccare il componente.

## Regole
- Un solo solid per vista, in alto a destra (PageHeader) o in fondo alla finestra.
- Nel gestionale: `sm` nelle barre e nelle righe, `md` per l'azione della pagina. `lg` solo su telefono e nell'area paziente.
- Etichette con verbo e oggetto; solo icona: `aria-label` o Tooltip.
