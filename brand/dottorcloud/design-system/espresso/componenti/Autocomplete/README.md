# Autocomplete

Il campo che cerca mentre scrivi: pazienti, prestazioni del listino, medici.

## In frappe-ui
`<Autocomplete :options placeholder>` / `<Combobox>`: campo come TextInput, lista come Dropdown, voci 28px.

## Personalizzazione DottorCloud
- Le persone hanno l'avatar a nuvola; il testo cercato è in grassetto; a destra un dato che distingue gli omonimi (codice fiscale) in `ink-gray-5`.
- L'ultima voce crea il nuovo record ed è segnata dalla **croce** in `on-brand-subtle`: è il "+" del marchio dove si crea qualcosa.
