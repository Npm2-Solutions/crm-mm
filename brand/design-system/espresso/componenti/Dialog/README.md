# Dialog

La finestra per una decisione o un modulo breve.

## In frappe-ui
`<Dialog v-model :options="{ title, message, icon, size, actions }">`: `rounded-xl`, `bg-surface-elevation-1`, `px-6 pt-5 pb-6`; icona in un cerchio da 28px; azioni a destra.

## Personalizzazione DottorCloud
- Forma: `rounded-xl` con la coda della nuvola; anche l'icona sta in una piccola nuvola.
- Velo `overlay` tinto di verde.
- L'azione: `solid` (o `solid` rosso se distruttiva) con verbo e oggetto; "Indietro" `subtle`.

## Regole
`size: 'md'` per le conferme, `'xl'`/`'2xl'` per i moduli. Esc chiude.
