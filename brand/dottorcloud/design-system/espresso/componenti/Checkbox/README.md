# Checkbox

La casella di spunta: spuntata, vuota, a metà, disabilitata.

## In frappe-ui
`<Checkbox v-model label size="sm|md" :padding :disabled>`: 14px (sm) o 16px (md), `rounded-sm`, bordo `outline-gray-4`; spuntata prende il colore del testo (`ink-gray-9`). Con `padding` diventa una riga cliccabile.

## Personalizzazione DottorCloud
- Spuntata e a metà: fondo `brand-solid` con spunta `on-brand-solid` (in `marchio.css` già `color: var(--brand-action)` sulle checkbox spuntate).
- Vuota: bordo `outline-gray-5`, almeno 3:1 sul bianco e sul fondo delle intestazioni nei due temi (`outline-gray-4` dava 2,83:1; `espresso.css` §5).
- Forma a nuvola: angolo in basso a sinistra a 2px.
- Riga con `padding`: quando è spuntata il fondo diventa `brand-subtle`.

## Regole
I consensi non sono mai pre-spuntati. Per un'impostazione con effetto immediato usa Switch.
