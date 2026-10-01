# Switch

L'interruttore con effetto immediato. Acceso, il pomello mostra la croce del marchio, centrata.

## In frappe-ui
`<Switch v-model label size="sm|md">` (reka-ui): sm 26×16 con pomello 12px, md 32×20 con pomello 14px; acceso `bg-surface-gray-10`.

## Personalizzazione DottorCloud
- Acceso: binario `brand-solid` (già in `marchio.css`), pomello `surface-base` con la **croce** `brand-solid` centrata (6px nel sm, 7px nel md); nel tema scuro pomello `teal-950` e croce menta.
- La croce è disegnata come sfondo del pomello (`background-position: center`), così resta al centro a ogni taglia; entra con un piccolo rimbalzo.
- Spento: binario `surface-gray-4`.
