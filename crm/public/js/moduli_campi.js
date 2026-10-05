// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * A form's questions on a public page, drawn without a framework: the link at
 * home and the desk's tablet (/modulo), a form on the centre's website
 * (/crm-form, and a block in a page of the centre's site). What shows, what is
 * required and what a calculation gives are the engine's (moduli_engine.js), the
 * rules the server applies too: this draws the questions and keeps the answers.
 *
 * The page imports the engine with its version and hands it over, so the two
 * always come from the same release.
 */

/** The words of the questions, in Italian; the page adds its own. */
export const WORDS_IT = {
  Yes: 'Sì',
  No: 'No',
  'I agree': 'Acconsento',
  'I do not agree': 'Non acconsento',
  Clear: 'Cancella',
  'Sign here': 'Firma qui',
  Left: 'Sinistra',
  Right: 'Destra',
  'Add a row': 'Aggiungi una riga',
  Remove: 'Togli',
  'This is required': 'Obbligatorio',
  'To go on, this has to be accepted': 'Per andare avanti va accettato',
  'Stop here and tell the operator': "Fermati qui e avvisa l'operatore",
  'Signed at the desk, when you come.': 'Si firma al banco, quando vieni.',
  'Bring it to the visit, or send it to the centre.':
    'Portalo alla visita, o mandalo al centro.',
}

export function h(tag, attrs, ...children) {
  const el = document.createElement(tag)
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === null || value === undefined || value === false) continue
    if (key.startsWith('on')) el.addEventListener(key.slice(2), value)
    else if (key === 'class') el.className = value
    else el.setAttribute(key, value === true ? '' : value)
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue
    el.append(child instanceof Node ? child : document.createTextNode(String(child)))
  }
  return el
}

// a question that stands for one of the person's fields, on a form of the
// website: the browser may fill it, and a phone shows the right keyboard
// a person's name: a capital to each word, never corrected into a word
const NOME = { autocapitalize: 'words', autocorrect: 'off', spellcheck: 'false' }
const PERSON_INPUT = {
  full_name: { autocomplete: 'name', ...NOME },
  first_name: { autocomplete: 'given-name', ...NOME },
  last_name: { autocomplete: 'family-name', ...NOME },
  email: { type: 'email', autocomplete: 'email', inputmode: 'email' },
  mobile_no: { type: 'tel', autocomplete: 'tel', inputmode: 'tel' },
  organization: { autocomplete: 'organization' },
  job_title: { autocomplete: 'organization-title' },
}

/**
 * Draw ``schema`` with ``answers`` so far. ``engine`` is moduli_engine.js, ``t``
 * the page's words. ``signedAtDesk``: a form filled here and signed at the desk,
 * whose signatures are neither drawn nor asked. ``stopMessage``: what a question
 * that stops the form says, when the template does not say it. ``idPrefix``
 * keeps two forms on one page apart.
 */
export function drawForm({
  schema,
  answers,
  engine,
  t,
  signedAtDesk = false,
  stopMessage = 'Stop here and tell the operator',
  idPrefix = 'q-',
}) {
  const { evaluate, sectionsOf, fieldsOfSection, fieldsOf } = engine
  const values = { ...(answers || {}) }
  const parts = {}
  const signatures = new Set(
    fieldsOf(schema)
      .filter((field) => field.type === 'signature')
      .map((field) => field.id),
  )
  let tried = false

  function set(key, value) {
    values[key] = value
    refresh()
  }

  function pressed(button, on) {
    button.setAttribute('aria-pressed', on ? 'true' : 'false')
  }

  function renderField(field) {
    const wrap = h('div', { class: 'field', 'data-field': field.id })
    if (field.type === 'paragraph') {
      wrap.append(h('div', { class: 'reading' }, field.text || ''))
    } else {
      const id = idPrefix + field.id
      wrap.append(
        // `for` names a control one writes in; `id` names a group of buttons
        h('label', { class: 'label', for: id, id: id + '-q' }, field.label || '', h('span', { class: 'req' })),
      )
      if (field.description) wrap.append(h('div', { class: 'help' }, field.description))
      wrap.append(control(field, id))
    }
    const missing = h('div', { class: 'missing', hidden: true })
    const stop = h('div', { class: 'stop', role: 'alert', hidden: true })
    wrap.append(missing, stop)
    parts[field.id] = { wrap, missing, stop, worked: wrap.querySelector('[data-worked]') }
    return wrap
  }

  function control(field, id) {
    const value = values[field.id]
    switch (field.type) {
      case 'text': {
        const person = PERSON_INPUT[field.person] || {}
        const el = field.multiline
          ? h('textarea', { class: 'in', rows: '4', id }, value || '')
          : h('input', { class: 'in', value: value || '', id, ...person })
        el.addEventListener('input', () => set(field.id, el.value))
        const phrases = (field.phrases || []).map((phrase) =>
          h(
            'button',
            {
              class: 'pill',
              type: 'button',
              onclick: () => {
                el.value = el.value.trim()
                  ? el.value.trimEnd() + (field.multiline ? '\n' : ' ') + phrase
                  : phrase
                set(field.id, el.value)
              },
            },
            phrase,
          ),
        )
        return h('div', { class: 'stack' }, el, phrases.length ? h('div', { class: 'pills' }, phrases) : null)
      }
      case 'number': {
        const el = h('input', { class: 'in', inputmode: 'decimal', value: value ?? '', id, style: 'max-width:12rem' })
        el.addEventListener('input', () => set(field.id, el.value))
        return h('div', { class: 'row' }, el, field.unit ? h('span', { class: 'unit' }, field.unit) : null)
      }
      case 'date': {
        const el = h('input', { class: 'in', type: 'date', value: value || '', id, style: 'max-width:14rem' })
        el.addEventListener('change', () => set(field.id, el.value || null))
        return el
      }
      case 'choice': {
        const labels = (field.options || []).map((o) => o && o.label).filter(Boolean)
        if (field.display === 'dropdown' && !field.multiple) {
          const el = h(
            'select',
            { class: 'in', id },
            h('option', { value: '' }, ''),
            labels.map((l) => h('option', { value: l, selected: value === l }, l)),
          )
          el.addEventListener('change', () => set(field.id, el.value || null))
          return el
        }
        const buttons = labels.map((label) => {
          const on = field.multiple ? (value || []).includes(label) : value === label
          const button = h(
            'button',
            { class: 'opt', type: 'button', 'aria-pressed': on ? 'true' : 'false' },
            h('span', { class: 'mark' + (field.multiple ? ' box' : '') }),
            label,
          )
          button.addEventListener('click', () => {
            if (field.multiple) {
              const now = new Set(values[field.id] || [])
              now.has(label) ? now.delete(label) : now.add(label)
              set(
                field.id,
                labels.filter((l) => now.has(l)),
              )
            } else {
              set(field.id, values[field.id] === label ? null : label)
            }
            buttons.forEach((b, i) =>
              pressed(
                b,
                field.multiple
                  ? (values[field.id] || []).includes(labels[i])
                  : values[field.id] === labels[i],
              ),
            )
          })
          return button
        })
        return h('div', { class: 'options', role: 'group', 'aria-labelledby': id + '-q' }, buttons)
      }
      case 'yesno':
      case 'consent': {
        const consent = field.type === 'consent'
        const choices =
          consent && field.must_accept
            ? [[true, t('I agree')]]
            : [
                [true, consent ? t('I agree') : t('Yes')],
                [false, consent ? t('I do not agree') : t('No')],
              ]
        const buttons = choices.map(([answer, label]) => {
          const button = h(
            'button',
            { class: 'pill', type: 'button', 'aria-pressed': values[field.id] === answer ? 'true' : 'false' },
            label,
          )
          button.addEventListener('click', () => {
            set(field.id, values[field.id] === answer ? null : answer)
            buttons.forEach((b, i) => pressed(b, values[field.id] === choices[i][0]))
          })
          return button
        })
        const pills = h('div', { class: 'pills', role: 'group', 'aria-labelledby': id + '-q' }, buttons)
        return consent ? h('div', { class: 'consent' }, h('p', {}, field.text || ''), pills) : pills
      }
      case 'scale': {
        const least = Number(field.min ?? 0)
        const most = Number(field.max ?? 10)
        const steps = []
        for (let n = least; n <= most && steps.length <= 101; n++) steps.push(n)
        const buttons = steps.map((n) => {
          const button = h(
            'button',
            { class: 'pill', type: 'button', 'aria-pressed': values[field.id] === n ? 'true' : 'false' },
            String(n),
          )
          button.addEventListener('click', () => {
            set(field.id, values[field.id] === n ? null : n)
            buttons.forEach((b, i) => pressed(b, values[field.id] === steps[i]))
          })
          return button
        })
        return h(
          'div',
          { class: 'stack' },
          h('div', { class: 'pills', role: 'group', 'aria-labelledby': id + '-q' }, buttons),
          field.min_label || field.max_label
            ? h('div', { class: 'ends' }, h('span', {}, field.min_label || ''), h('span', {}, field.max_label || ''))
            : null,
        )
      }
      case 'sides': {
        const now = { ...(value || {}) }
        const side = (key, label) => {
          const el = h('input', {
            class: 'in',
            inputmode: field.input === 'text' ? 'text' : 'decimal',
            value: now[key] ?? '',
          })
          el.addEventListener('input', () => {
            now[key] = el.value
            set(field.id, { ...now })
          })
          return h(
            'label',
            { class: 'stack', style: 'gap:.3rem;flex:1;min-width:0' },
            h('span', { class: 'help' }, label),
            h('span', { class: 'row' }, el, field.unit ? h('span', { class: 'unit' }, field.unit) : null),
          )
        }
        return h(
          'div',
          { class: 'row', role: 'group', 'aria-labelledby': id + '-q' },
          side('left', t('Left')),
          side('right', t('Right')),
        )
      }
      case 'table':
        return tableControl(field)
      case 'calc':
      case 'score':
        return h(
          'div',
          { class: 'worked' },
          h('b', { 'data-worked': '' }, '—'),
          field.unit ? h('span', { class: 'unit' }, field.unit) : null,
          h('span', { class: 'band', hidden: true }),
        )
      case 'signature':
        return signedAtDesk
          ? h('p', { class: 'help' }, t('Signed at the desk, when you come.'))
          : padControl(field)
      case 'attachment':
        return h('p', { class: 'help' }, t('Bring it to the visit, or send it to the centre.'))
      default:
        return h('span', {})
    }
  }

  function tableControl(field) {
    const columns = (field.columns || []).filter(Boolean)
    const rows = Array.isArray(values[field.id]) ? values[field.id].map((r) => ({ ...r })) : []
    const holder = h('div', { class: 'stack' })
    const copy = () => rows.map((r) => ({ ...r }))
    const draw = () => {
      holder.innerHTML = ''
      if (rows.length) {
        const table = h(
          'table',
          { class: 'rows' },
          h('tr', {}, columns.map((c) => h('th', {}, c.label)), h('th', {})),
          rows.map((row, index) =>
            h(
              'tr',
              {},
              columns.map((c) => {
                const el = h('input', {
                  class: 'in',
                  type: c.type === 'date' ? 'date' : 'text',
                  inputmode: c.type === 'number' ? 'decimal' : null,
                  value: row[c.id] ?? '',
                  'aria-label': c.label,
                })
                el.addEventListener('input', () => {
                  row[c.id] = el.value
                  set(field.id, copy())
                })
                return h('td', {}, el)
              }),
              h(
                'td',
                {},
                h(
                  'button',
                  {
                    class: 'ghost',
                    type: 'button',
                    onclick: () => {
                      rows.splice(index, 1)
                      set(field.id, copy())
                      draw()
                    },
                  },
                  t('Remove'),
                ),
              ),
            ),
          ),
        )
        holder.append(h('div', { class: 'scroll' }, table))
      }
      holder.append(
        h(
          'button',
          {
            class: 'secondary',
            type: 'button',
            onclick: () => {
              rows.push({})
              draw()
            },
          },
          t('Add a row'),
        ),
      )
    }
    draw()
    return holder
  }

  // the stroke only: no pressure, no timing (they would be biometric data)
  function padControl(field) {
    const canvas = h('canvas', { 'aria-label': field.label || t('Sign here') })
    const pad = h('div', { class: 'pad' }, canvas, h('div', { class: 'line' }, field.label || t('Sign here')))
    let strokes = 0
    let drawing = null
    const pen = () => {
      const c = canvas.getContext('2d')
      c.lineCap = 'round'
      c.lineJoin = 'round'
      c.strokeStyle = '#1f2328'
      c.fillStyle = '#1f2328'
      c.lineWidth = 2.2 * (window.devicePixelRatio || 1)
      return c
    }
    const point = (e) => {
      const r = canvas.getBoundingClientRect()
      const s = window.devicePixelRatio || 1
      return [(e.clientX - r.left) * s, (e.clientY - r.top) * s]
    }
    const clear = () => {
      const s = window.devicePixelRatio || 1
      canvas.width = Math.round(pad.clientWidth * s)
      canvas.height = Math.round(pad.clientHeight * s)
      strokes = 0
      set(field.id, null)
    }
    canvas.addEventListener('pointerdown', (e) => {
      e.preventDefault()
      if (canvas.setPointerCapture) canvas.setPointerCapture(e.pointerId)
      drawing = [point(e)]
      strokes++
      const c = pen()
      const [x, y] = drawing[0]
      c.beginPath()
      c.arc(x, y, c.lineWidth / 2, 0, Math.PI * 2)
      c.fill()
    })
    canvas.addEventListener('pointermove', (e) => {
      if (!drawing) return
      e.preventDefault()
      drawing.push(point(e))
      const n = drawing.length
      if (n < 3) return
      const [x0, y0] = drawing[n - 3]
      const [x1, y1] = drawing[n - 2]
      const [x2, y2] = drawing[n - 1]
      const c = pen()
      c.beginPath()
      c.moveTo((x0 + x1) / 2, (y0 + y1) / 2)
      c.quadraticCurveTo(x1, y1, (x1 + x2) / 2, (y1 + y2) / 2)
      c.stroke()
    })
    const end = () => {
      if (!drawing) return
      drawing = null
      set(field.id, strokes ? canvas.toDataURL('image/png') : null)
    }
    ;['pointerup', 'pointercancel', 'pointerleave'].forEach((kind) => canvas.addEventListener(kind, end))
    requestAnimationFrame(clear)
    return h(
      'div',
      { class: 'stack', style: 'gap:.3rem' },
      pad,
      h('button', { class: 'ghost', type: 'button', onclick: clear }, t('Clear')),
    )
  }

  // the same evaluation the server makes when the form is sent or signed
  function refresh() {
    const state = evaluate(schema, values)
    const skip = signedAtDesk ? signatures : new Set()
    const required = new Set(state.required)
    const missing = new Set(state.missing.filter((key) => !skip.has(key)))
    const stops = new Map(state.stops.map((s) => [s.field, s.message]))
    for (const section of sectionsOf(schema)) {
      const box = parts['§' + section.id]
      if (box) box.hidden = !state.sections[section.id]
    }
    for (const field of fieldsOf(schema)) {
      const part = parts[field.id]
      if (!part) continue
      part.wrap.hidden = !state.visible[field.id]
      const star = part.wrap.querySelector('.req')
      if (star) star.textContent = required.has(field.id) && !skip.has(field.id) ? ' *' : ''
      part.missing.hidden = !(tried && missing.has(field.id))
      part.missing.textContent = field.must_accept
        ? t('To go on, this has to be accepted')
        : t('This is required')
      part.stop.hidden = !stops.has(field.id)
      part.stop.textContent = stops.get(field.id) || t(stopMessage)
      if (part.worked) {
        const worked = state.values[field.id]
        part.worked.textContent = worked === null || worked === undefined ? '—' : String(worked)
        const band = part.wrap.querySelector('.band')
        if (band) {
          band.hidden = !state.bands[field.id]
          band.textContent = state.bands[field.id] || ''
        }
      }
    }
    return { ...state, missing: [...missing] }
  }

  const element = h('div', { class: 'crm-campi' })
  for (const section of sectionsOf(schema)) {
    const box = h(
      'section',
      { 'data-section': section.id },
      section.title ? h('h2', {}, section.title) : null,
      section.description ? h('p', { class: 'section-desc' }, section.description) : null,
    )
    for (const field of fieldsOfSection(section)) box.append(renderField(field))
    parts['§' + section.id] = box
    element.append(box)
  }
  refresh()

  return {
    element,
    values,
    refresh,
    /** From now on what is missing shows; the state, with what is still to answer. */
    check() {
      tried = true
      return refresh()
    },
    /** The answers, without the signatures' strokes. */
    answers() {
      return Object.fromEntries(Object.entries(values).filter(([key]) => !signatures.has(key)))
    },
    /** Each signature drawn, as a PNG. */
    strokes() {
      return Object.fromEntries(
        Object.entries(values).filter(([key, value]) => signatures.has(key) && typeof value === 'string'),
      )
    },
    /** The questions' labels, for the keys given. */
    labels(keys) {
      const all = fieldsOf(schema)
      return keys.map((key) => (all.find((f) => f.id === key) || {}).label || key)
    },
    /** Take the person to a question. */
    reveal(key) {
      const box = element.querySelector(`[data-field="${key}"]`)
      if (box) box.scrollIntoView({ behavior: 'smooth', block: 'center' })
    },
  }
}
