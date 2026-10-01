# AgendaEvent

La visita nella griglia dell'agenda. Componente DottorCloud.

## In frappe-ui
Nel gestionale è l'evento del calendario (frappe-ui `Calendar`, slot dell'evento): fondo e barretta vengono dalla categoria della prestazione.

## Personalizzazione DottorCloud
- `rounded` (8px) con la coda della nuvola, `text-sm`, orario `text-xs` tabulare nel colore della categoria.
- **Prima visita** e prestazioni del centro: blocco pieno `brand-solid`.
- **Adesso**: anello `brand` e la croce prima dell'orario.
- **Slot libero**: a strisce ambra con contorno, per proporlo alla lista d'attesa.
- **Annullato**: grigio e barrato.
