# ListView

L'elenco di pazienti, appuntamenti, fatture.

## In frappe-ui
`<ListView :columns :rows :options="{ selectable }">`: intestazione su `surface-gray-2` alta 32px, righe 40px separate da un filetto, hover `surface-gray-1`, selezione `surface-gray-2`; con righe selezionate compare `ListSelectBanner`.

## Personalizzazione DottorCloud
- Riga selezionata: `brand-subtle` invece del grigio.
- La barra delle righe selezionate è un **blocco** `block-deep` con la coda della nuvola: le azioni in blocco si vedono subito.
- Persone con l'avatar a nuvola; stato con Badge, tipo con Tag; importi a destra con cifre tabulari.

## Regole
Le azioni della singola riga in un Dropdown `more-horizontal`.
