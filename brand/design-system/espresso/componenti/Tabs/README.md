# Tabs

Le schede di una pagina (Tabs) e il controllo segmentato (TabButtons).

## In frappe-ui
`<Tabs :tabs v-model>`: schede a `gap-5`, testo `text-base` `ink-gray-5`, attiva `ink-gray-9` con un indicatore che scorre (`bg-surface-gray-10`). `<TabButtons :buttons>`: segmentato su `surface-gray-2`, attivo `surface-base` con `shadow-sm`.

## Personalizzazione DottorCloud
- **Scheda attiva**: testo `ink-gray-9` e una **linea di 2px in `brand-solid`** sotto, a tutta larghezza della scheda (l'indicatore di frappe-ui ricolorato, niente forme in più); l'icona della scheda attiva prende `brand-solid`, il contatore `brand-subtle`.
- **Segmentato**: il pulsante attivo ha la coda della nuvola.
