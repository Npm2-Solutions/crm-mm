// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The actions of a dialog made with $dialog (utils/dialogs.jsx). A confirmation
// that offers only the red button of what it does (delete, disconnect, remove)
// was left only by the X, Escape or a tap outside: «Cancel» goes in front of
// it, without an `onClick`, so frappe-ui's Dialog closes on it and the dialog's
// `onClose` hears it end. A dialog that offers a way back of its own («Keep
// editing», «Cancel it instead») keeps its actions as they are.

/** The actions, with «Cancel» (`annulla`, translated) first where all are red. */
export function conAnnulla(azioni, annulla) {
  const soloRosse =
    Array.isArray(azioni) &&
    azioni.length > 0 &&
    azioni.every((azione) => azione?.theme === 'red')
  return soloRosse ? [{ label: annulla }, ...azioni] : azioni
}
