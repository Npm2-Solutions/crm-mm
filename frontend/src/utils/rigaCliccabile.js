// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// A row that opens something on a click, reached and opened from the keyboard
// too (WCAG 2.1.1): `v-riga-cliccabile` gives it a button's role, a place in
// the tab order and Enter and Space, and a focus ring (`index.css`). The rows
// of the settings - rooms, the team's shifts, locations, tracked links, the
// invoicing registers - were divs a mouse opened and a keyboard never reached:
// nobody could change a colleague's shifts without a mouse.
//
// Only a key pressed on the row itself opens it: one pressed on a control
// inside it (a switch, a bin) is that control's.
export function tastoDellaRiga(evento, riga) {
  if (evento.target !== riga) return false
  return evento.key === 'Enter' || evento.key === ' '
}

export const vRigaCliccabile = {
  mounted(riga) {
    if (!riga.hasAttribute('role')) riga.setAttribute('role', 'button')
    if (!riga.hasAttribute('tabindex')) riga.setAttribute('tabindex', '0')
    riga.setAttribute('data-riga-cliccabile', '')
    riga._apriConITasti = (evento) => {
      if (!tastoDellaRiga(evento, riga)) return
      evento.preventDefault()
      riga.click()
    }
    riga.addEventListener('keydown', riga._apriConITasti)
  },
  unmounted(riga) {
    riga.removeEventListener('keydown', riga._apriConITasti)
  },
}
