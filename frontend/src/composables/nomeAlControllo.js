// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import {
  getCurrentInstance,
  onBeforeUnmount,
  onMounted,
  onUpdated,
  ref,
} from 'vue'

// what a row of settings may hold to be named by its words: frappe-ui's switch
// (a button), a field, a select, a picker's button
const CONTROLLI =
  "[role='switch'], input:not([type='hidden']), select, textarea, [role='combobox'], button[aria-haspopup]"

// what a form's field may hold: the same, a text editor, and the button a link
// field or a person's picker draws its value on
const CAMPI =
  "input:not([type='hidden']), textarea, select, [contenteditable='true'], [role='combobox'], [role='switch'], [role='checkbox'], button"

// a control one writes in: a screen reader reads its value apart
const SCRIVE = "input, textarea, select, [contenteditable='true']"

let contatore = 0

function idDi(elemento, prefisso) {
  if (!elemento.id) elemento.id = `${prefisso}-${++contatore}`
  return elemento.id
}

/** What an element says to a screen reader: its words, less what is hidden. */
function testoLetto(elemento) {
  let testo = ''
  for (const nodo of elemento.childNodes) {
    if (nodo.nodeType === 3) testo += nodo.textContent
    else if (nodo.nodeType === 1 && nodo.getAttribute('aria-hidden') !== 'true')
      testo += testoLetto(nodo)
  }
  return testo
}

const comeParole = (testo) =>
  testo
    .replace(/[.…]+$/, '')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase()

/**
 * The field's words name its control. A button or a select is read with what
 * it shows, «Azienda, Scegli azienda…», «Stato, Nuovo»: its own words alone
 * never said which field they were, and a select said nothing at all. An
 * empty one showing the field's own words is read once, not «Titolo Titolo».
 */
function collega(etichetta, controllo) {
  const parole = idDi(etichetta, 'etichetta')
  const ripete =
    comeParole(testoLetto(controllo)) === comeParole(testoLetto(etichetta))
  const nome =
    controllo.matches(SCRIVE) || ripete
      ? parole
      : `${parole} ${idDi(controllo, 'campo')}`
  if (controllo.getAttribute('aria-labelledby') !== nome)
    controllo.setAttribute('aria-labelledby', nome)
}

/**
 * `fai` once the box is drawn, and again whenever something inside it is drawn
 * anew: a field's control is a child component's, which redraws it without
 * telling the parent.
 */
function seguiLaScatola(scatola, fai) {
  let osservatore = null
  let osservata = null
  let previsto = false
  const presto = () => {
    if (previsto) return
    previsto = true
    requestAnimationFrame(() => {
      previsto = false
      fai()
    })
  }
  // the box may come later (a field drawn once it is visible) or anew
  function guarda() {
    const box = scatola.value
    if (!box || box === osservata || typeof MutationObserver === 'undefined')
      return
    osservatore?.disconnect()
    osservatore = new MutationObserver(presto)
    // characterData too: a chosen value changes the words a button shows
    osservatore.observe(box, {
      childList: true,
      subtree: true,
      characterData: true,
    })
    osservata = box
  }
  function ancora() {
    guarda()
    fai()
  }
  onMounted(ancora)
  onUpdated(ancora)
  onBeforeUnmount(() => osservatore?.disconnect())
}

/**
 * The words of a setting's row name the control beside them: the row draws
 * them as `<label :for="id">`, with the id of the first control in `scatola`
 * (given one when it has none). frappe-ui's Switch put an `aria-label` on its
 * outer box, not on its button, so VoiceOver read «switch» and nothing else;
 * a label for it also flips it when its words are tapped.
 */
export function useNomeAlControllo(scatola) {
  const perId = ref('')
  const uid = getCurrentInstance()?.uid ?? Math.random().toString(36).slice(2)

  function trova() {
    const controllo = scatola.value?.querySelector(CONTROLLI)
    if (!controllo) {
      perId.value = ''
      return
    }
    if (!controllo.id) controllo.id = `riga-${uid}`
    perId.value = controllo.id
  }

  onMounted(trova)
  onUpdated(trova)
  return perId
}

/** A form's field: its words (`etichetta`) name the first control after them in `scatola`. */
export function useEtichettaDelCampo(scatola, etichetta) {
  seguiLaScatola(scatola, () => {
    const parole = etichetta.value
    if (!parole) return
    const controllo = [...(scatola.value?.querySelectorAll(CAMPI) || [])].find(
      (elemento) => !parole.contains(elemento),
    )
    if (controllo) collega(parole, controllo)
  })
}

/**
 * A list of fields, a record's side panel: in each `[data-campo-riga]` the
 * words (`[data-etichetta]`) name the first control of the value
 * (`[data-valore]`).
 */
export function useEtichetteDeiCampi(scatola) {
  seguiLaScatola(scatola, () => {
    for (const riga of scatola.value?.querySelectorAll('[data-campo-riga]') ||
      []) {
      const parole = riga.querySelector('[data-etichetta]')
      const controllo = riga
        .querySelector('[data-valore]')
        ?.querySelector(CAMPI)
      if (parole && controllo) collega(parole, controllo)
    }
  })
}
