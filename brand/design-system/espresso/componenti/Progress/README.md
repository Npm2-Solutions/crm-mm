# Progress

Avanzamento e attesa.

## In frappe-ui
`<Progress :value size="sm|md|lg" label>`: binario `surface-gray-2`, riempimento `surface-gray-10`, `rounded-xl`. `<Spinner>` / `<LoadingIndicator>` per l'attesa.

## Personalizzazione DottorCloud
- Riempimento in `brand` (il verde del logo).
- A tappe (cicli di sedute): segmenti separati, i fatti in `brand`.
- Spinner con l'arco `brand-solid`; per i caricamenti di pagina la **croce** che ruota (`dc-loader-mark`).
