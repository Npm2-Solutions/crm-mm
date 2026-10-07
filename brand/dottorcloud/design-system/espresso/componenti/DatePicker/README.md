# DatePicker

La scelta di una data.

## In frappe-ui
`<DatePicker v-model>` / `<DateTimePicker>`: campo come TextInput, calendario in un popover (`rounded-lg`, `shadow-lg`), giorni in griglia, oggi evidenziato, scelto in `surface-gray-10`.

## Personalizzazione DottorCloud
- Giorno scelto: `brand-solid` con la coda della nuvola.
- **Oggi**: numero in `brand-solid` con una piccola **croce** sotto, al posto del punto.
- Pallino ambra sui giorni con posti dalla lista d'attesa (facoltativo, solo nell'agenda).

## Regole
Formato `gg/mm/aaaa`, settimana che parte dal lunedì.
