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
  Front: 'Davanti',
  Back: 'Dietro',
  R: 'D',
  L: 'S',
  'Mark a point': 'Segna un punto',
  Draw: 'Disegna',
  'Tap the body where it hurts: each tap is a numbered point':
    'Tocca il corpo dove fa male: ogni tocco è un punto numerato',
  'Draw on the body with your finger, or with the mouse':
    'Disegna sul corpo con il dito, o con il mouse',
  'Undo the last stroke': "Togli l'ultimo tratto",
  'Clear all': 'Azzera tutto',
  'Point {0}': 'Punto {0}',
  'Remove the point': 'Togli il punto',
  'What it feels like, where': 'Cosa senti, dove',
  'Burning, down the leg': 'Bruciore, scende lungo la gamba',
  'How much, from 0 (nothing) to 10 (the worst)': 'Quanto, da 0 (niente) a 10 (il peggio)',
  'Drawn by hand: {0}': 'Disegnato a mano: {0}',
}

const SVG = 'http://www.w3.org/2000/svg'

/** An element of a drawing: the body chart's outlines and marks. */
function svg(tag, attrs, ...children) {
  const el = document.createElementNS(SVG, tag)
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === null || value === undefined || value === false) continue
    if (key.startsWith('on')) el.addEventListener(key.slice(2), value)
    else el.setAttribute(key, value)
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue
    el.append(child instanceof Node ? child : document.createTextNode(String(child)))
  }
  return el
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
        // the mark is for the eye: a screen reader hears «required» from the control
        h('label', { class: 'label', for: id, id: id + '-q' }, field.label || '', h('span', { class: 'req', 'aria-hidden': 'true' })),
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
      case 'body_chart':
        return bodyControl(field, id)
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

  // where it hurts: points tapped on the body's outlines, strokes drawn on them,
  // kept as fractions of the outline (the engine's cleanBodyChart, the server's
  // too). A tap leaves the page to the finger; drawing keeps it.
  function bodyControl(field, id) {
    const { BODY_OUTLINES, bodyViews, smoothPath, roundHalfUp } = engine
    const PAPER = '#ffffff'
    const MARK = '#c2410c'
    const OUTLINE = '#5f6368'
    const INSIDE = '#f3f4f6'
    const DETAIL = '#a3a7ad'
    const views = bodyViews(field)
    const start = values[field.id] && typeof values[field.id] === 'object' ? values[field.id] : {}
    let marks = Array.isArray(start.marks) ? start.marks.map((m) => ({ ...m })) : []
    let strokes = Array.isArray(start.strokes) ? start.strokes.map((s) => ({ ...s })) : []
    let mode = 'points'
    let chosen = null
    let drawing = null
    const viewName = (view) => (view === 'back' ? t('Back') : t('Front'))
    const holder = h('div', { class: 'stack corpo', role: 'group', 'aria-labelledby': id + '-q' })

    const keep = () => {
      const value = {}
      if (marks.length) value.marks = marks.map((m) => ({ ...m }))
      if (strokes.length) value.strokes = strokes.map((s) => ({ view: s.view, points: s.points }))
      set(field.id, Object.keys(value).length ? value : null)
    }
    const where = (outline, e) => {
      const r = outline.getBoundingClientRect()
      const f = (v) => roundHalfUp(Math.min(1, Math.max(0, v)), 3)
      return [f((e.clientX - r.left) / r.width), f((e.clientY - r.top) / r.height)]
    }

    function figure(view) {
      const outline = svg(
        'svg',
        {
          viewBox: '0 0 200 460',
          class: 'sagoma' + (mode === 'draw' ? ' disegna' : ''),
          role: 'img',
          'aria-label': viewName(view),
          'data-disegno': '',
        },
        svg('path', { d: BODY_OUTLINES.body, fill: INSIDE, stroke: OUTLINE, 'stroke-width': '1.4' }),
        svg('path', { d: BODY_OUTLINES.head, fill: INSIDE, stroke: OUTLINE, 'stroke-width': '1.4' }),
        BODY_OUTLINES[view].map((d) => svg('path', { d, fill: 'none', stroke: DETAIL, 'stroke-width': '1' })),
        // whose right is on which side: from the front, on the reader's left
        svg('text', { x: '8', y: '40', 'font-size': '13', fill: DETAIL }, view === 'front' ? t('R') : t('L')),
        svg(
          'text',
          { x: '192', y: '40', 'font-size': '13', fill: DETAIL, 'text-anchor': 'end' },
          view === 'front' ? t('L') : t('R'),
        ),
        strokes
          .filter((s) => s.view === view)
          .map((s) =>
            svg('path', {
              d: smoothPath(s.points),
              fill: 'none',
              stroke: MARK,
              'stroke-opacity': '0.75',
              'stroke-width': '3',
              'stroke-linecap': 'round',
              'stroke-linejoin': 'round',
            }),
          ),
        marks.map((m, i) =>
          m.view !== view
            ? null
            : svg(
                'g',
                {
                  class: 'segno',
                  onclick: (e) => {
                    e.stopPropagation()
                    chosen = chosen === i ? null : i
                    draw()
                  },
                },
                svg('circle', { cx: m.x * 200, cy: m.y * 460, r: '16', fill: 'transparent' }),
                svg('circle', {
                  cx: m.x * 200,
                  cy: m.y * 460,
                  r: '9',
                  fill: MARK,
                  stroke: chosen === i ? '#1f2328' : PAPER,
                  'stroke-width': chosen === i ? '2.5' : '1.5',
                }),
                svg(
                  'text',
                  {
                    x: m.x * 200,
                    y: m.y * 460 + 3.8,
                    'font-size': '11',
                    'font-weight': '700',
                    'text-anchor': 'middle',
                    fill: PAPER,
                  },
                  String(i + 1),
                ),
              ),
        ),
      )
      outline.addEventListener('click', (e) => {
        if (mode !== 'points' || marks.length >= 40) return
        const [x, y] = where(outline, e)
        marks.push({ view, x, y })
        chosen = marks.length - 1
        keep()
        draw()
      })
      outline.addEventListener('pointerdown', (e) => {
        if (mode !== 'draw' || strokes.length >= 40) return
        e.preventDefault()
        if (outline.setPointerCapture) outline.setPointerCapture(e.pointerId)
        drawing = { view, points: [where(outline, e)], line: null }
        drawing.line = svg('path', {
          fill: 'none',
          stroke: MARK,
          'stroke-opacity': '0.75',
          'stroke-width': '3',
          'stroke-linecap': 'round',
        })
        outline.append(drawing.line)
      })
      outline.addEventListener('pointermove', (e) => {
        if (!drawing) return
        e.preventDefault()
        if (drawing.points.length >= 500) return
        const [x, y] = where(outline, e)
        const [px, py] = drawing.points[drawing.points.length - 1]
        if (Math.abs(x - px) + Math.abs(y - py) < 0.008) return
        drawing.points.push([x, y])
        drawing.line.setAttribute('d', smoothPath(drawing.points))
      })
      const end = () => {
        if (!drawing) return
        strokes.push({ view: drawing.view, points: drawing.points })
        drawing = null
        keep()
        draw()
      }
      outline.addEventListener('pointerup', end)
      outline.addEventListener('pointercancel', end)
      return h('figure', { class: 'figura' }, outline, h('figcaption', {}, viewName(view)))
    }

    function editor() {
      if (chosen === null || !marks[chosen]) return null
      const m = marks[chosen]
      const words = h('input', {
        class: 'in',
        value: m.label || '',
        maxlength: '120',
        enterkeyhint: 'done',
        placeholder: t('Burning, down the leg'),
        'aria-label': t('What it feels like, where'),
      })
      words.addEventListener('input', () => {
        if (words.value) m.label = words.value
        else delete m.label
        keep()
      })
      // the list below says the words once they are written
      words.addEventListener('change', draw)
      const levels = Array.from({ length: 11 }, (_, n) => {
        const b = h('button', { class: 'pill', type: 'button', 'aria-pressed': m.intensity === n ? 'true' : 'false' }, String(n))
        b.addEventListener('click', () => {
          if (m.intensity === n) delete m.intensity
          else m.intensity = n
          keep()
          draw()
        })
        return b
      })
      return h(
        'div',
        { class: 'punto' },
        h(
          'div',
          { class: 'row', style: 'justify-content:space-between' },
          h('b', {}, t('Point {0}').replace('{0}', chosen + 1) + ' · ' + viewName(m.view)),
          h(
            'button',
            {
              class: 'ghost',
              type: 'button',
              onclick: () => {
                marks.splice(chosen, 1)
                chosen = null
                keep()
                draw()
              },
            },
            t('Remove the point'),
          ),
        ),
        h('label', { class: 'stack', style: 'gap:.3rem' }, h('span', { class: 'help' }, t('What it feels like, where')), words),
        h('span', { class: 'help' }, t('How much, from 0 (nothing) to 10 (the worst)')),
        h('div', { class: 'pills' }, levels),
      )
    }

    function list() {
      const lines = marks.map((m, i) =>
        [`${i + 1}. ${viewName(m.view)}`, m.label, m.intensity === undefined || m.intensity === null ? null : `${m.intensity}/10`]
          .filter(Boolean)
          .join(' · '),
      )
      if (!lines.length) return null
      return h(
        'div',
        { class: 'options' },
        lines.map((line, i) =>
          h(
            'button',
            {
              class: 'opt',
              type: 'button',
              'aria-pressed': chosen === i ? 'true' : 'false',
              onclick: () => {
                mode = 'points'
                chosen = chosen === i ? null : i
                draw()
              },
            },
            line,
          ),
        ),
      )
    }

    function draw() {
      holder.innerHTML = ''
      if (field.drawing) {
        const modeButton = (key, label) =>
          h(
            'button',
            {
              class: 'pill',
              type: 'button',
              'aria-pressed': mode === key ? 'true' : 'false',
              onclick: () => {
                mode = key
                draw()
              },
            },
            label,
          )
        holder.append(h('div', { class: 'pills' }, modeButton('points', t('Mark a point')), modeButton('draw', t('Draw'))))
      }
      holder.append(
        h(
          'p',
          { class: 'help', style: 'margin:0' },
          mode === 'draw'
            ? t('Draw on the body with your finger, or with the mouse')
            : t('Tap the body where it hurts: each tap is a numbered point'),
        ),
        h('div', { class: 'carta' + (views.length === 1 ? ' una' : '') }, views.map(figure)),
      )
      if (marks.length || strokes.length) {
        holder.append(
          h(
            'div',
            { class: 'pills' },
            strokes.length
              ? h(
                  'button',
                  {
                    class: 'secondary',
                    type: 'button',
                    onclick: () => {
                      strokes.pop()
                      keep()
                      draw()
                    },
                  },
                  t('Undo the last stroke'),
                )
              : null,
            h(
              'button',
              {
                class: 'ghost',
                type: 'button',
                onclick: () => {
                  marks = []
                  strokes = []
                  chosen = null
                  keep()
                  draw()
                },
              },
              t('Clear all'),
            ),
          ),
        )
      }
      const open = editor()
      if (open) holder.append(open)
      const words = list()
      if (words) holder.append(words)
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
      const needed = required.has(field.id) && !skip.has(field.id)
      const star = part.wrap.querySelector('.req')
      if (star) star.textContent = needed ? ' *' : ''
      // the control one writes or picks in says it is required (a group of buttons has no such word)
      const own = part.wrap.querySelector('input.in[id], textarea.in[id], select.in[id]')
      if (own) {
        if (needed) own.setAttribute('aria-required', 'true')
        else own.removeAttribute('aria-required')
      }
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
