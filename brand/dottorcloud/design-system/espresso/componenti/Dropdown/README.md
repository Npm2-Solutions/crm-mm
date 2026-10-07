# Dropdown

Il menu a tendina per le azioni di una riga o di una pagina, e la lista aperta di Select e Autocomplete.

## In frappe-ui
`<Dropdown :options="[{ label, icon, onClick, theme }]">` con gruppi (`group`); la stessa superficie per `Select` e `Autocomplete`. Voci alte 28px, `rounded-3`, menu `rounded-lg` su `surface-elevation-1` con `shadow-lg`.

## Personalizzazione DottorCloud
- La voce scelta è segnata dalla **croce** in `brand` a destra, al posto della spunta.
- Il menu ha la coda della nuvola (angolo in basso a sinistra 2px).
- Voci distruttive in `danger` (`theme: 'red'`), sempre ultime e dopo un separatore.

## Regole
Al massimo 7 voci per gruppo; scorciatoie a destra in `ink-gray-5`.
