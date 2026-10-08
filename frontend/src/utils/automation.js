// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * Automation builder: catalogue and pure helpers.
 *
 * One source of truth for what a step is called, how it looks on the canvas and
 * what an empty one contains — the palette, the flow nodes and the side panel
 * all read from here. Everything in this file is pure (no Vue, no network) so
 * the tree surgery and the validation can be unit tested.
 *
 * Step shapes are the ones `crm/automation/engine.py` compiles; the only thing
 * this layer adds is a stable `id` per node, which the backend keeps.
 */

export const STEP_CATEGORIES = [
  { name: 'communication', label: 'Talk to the contact', icon: 'send' },
  { name: 'contact', label: 'Update the record', icon: 'user' },
  { name: 'deal', label: 'Deal (opportunity)', icon: 'briefcase' },
  { name: 'flow', label: 'Logic and timing', icon: 'git-branch' },
  { name: 'data', label: 'Data and other automations', icon: 'share-2' },
]

/**
 * type → how the builder presents it. `defaults` is cloned into every new step;
 * `gateable` marks the steps that accept a "run only if" condition and a label.
 */
export const STEP_CATALOG = {
  send_email: {
    label: 'Send Email',
    icon: 'mail',
    theme: 'blue',
    category: 'communication',
    description: 'Emails the address on the record.',
    defaults: { email_template: '', subject: '', message: '' },
    gateable: true,
  },
  send_sms: {
    label: 'Send SMS',
    icon: 'message-square',
    theme: 'blue',
    category: 'communication',
    description: 'Texts the mobile number on the record.',
    defaults: { message: '' },
    gateable: true,
  },
  send_whatsapp_template: {
    label: 'Send WhatsApp Template',
    icon: 'message-circle',
    theme: 'green',
    category: 'communication',
    description: 'Sends an approved WhatsApp template.',
    defaults: { template: '', template_parameters: [] },
    gateable: true,
  },
  // a form's link: a survey after a visit, or any published form
  // (crm/moduli/richieste.py); {{ form_link }} is the link in an SMS or WhatsApp
  send_form: {
    label: 'Send a Form',
    icon: 'clipboard',
    theme: 'blue',
    category: 'communication',
    description:
      'Sends the link to fill a published form: a survey after a visit opens with the link alone.',
    defaults: {
      template: '',
      template_title: '',
      via: 'email',
      message: '',
      whatsapp_template: '',
      template_parameters: [],
    },
    gateable: true,
  },
  notify: {
    label: 'Internal Notification',
    icon: 'bell',
    theme: 'blue',
    category: 'communication',
    // {brand} as written: `__()` fills it where it is drawn, after it found
    // the sentence in the catalogue
    description: 'Notifies the owner and the assignees inside {brand}.',
    defaults: { message: '' },
    gateable: true,
  },
  create_task: {
    label: 'Create Task',
    icon: 'check-square',
    theme: 'gray',
    category: 'contact',
    description: 'Opens a task on the record.',
    defaults: { title: '', due_in_days: 1, assigned_to: '' },
    gateable: true,
  },
  assign: {
    label: 'Assign User',
    icon: 'user-plus',
    theme: 'gray',
    category: 'contact',
    description: 'One user, or several for an even round robin.',
    defaults: { users: [], only_if_unassigned: false },
    gateable: true,
  },
  add_note: {
    label: 'Add Note',
    icon: 'file-text',
    theme: 'gray',
    category: 'contact',
    description: 'Leaves a note in the record timeline.',
    defaults: { comment: '' },
    gateable: true,
  },
  add_tag: {
    label: 'Add Tag',
    icon: 'tag',
    theme: 'gray',
    category: 'contact',
    description: 'Tags the record — other automations can listen for it.',
    defaults: { tag: '' },
    gateable: true,
  },
  remove_tag: {
    label: 'Remove Tag',
    icon: 'tag',
    theme: 'gray',
    category: 'contact',
    description: 'Takes a tag off the record.',
    defaults: { tag: '' },
    gateable: true,
  },
  set_field: {
    label: 'Update Field',
    icon: 'edit-3',
    theme: 'gray',
    category: 'contact',
    description: 'Writes a value on the person or the deal.',
    defaults: { field: '', value: '' },
    gateable: true,
  },
  convert_to_deal: {
    label: 'Convert Lead to Deal',
    icon: 'briefcase',
    theme: 'green',
    category: 'deal',
    description: 'Opens a deal for the person, to follow the sale.',
    defaults: {},
    gateable: true,
  },
  webhook: {
    label: 'Webhook',
    icon: 'globe',
    theme: 'green',
    category: 'data',
    description: 'Calls an external URL with the record data.',
    defaults: { method: 'POST', url: '', body: '' },
    gateable: true,
  },
  add_to_workflow: {
    label: 'Add to Automation',
    icon: 'log-in',
    theme: 'green',
    category: 'data',
    description: 'Enrols the record in another automation.',
    defaults: { automation: '' },
    gateable: true,
  },
  remove_from_workflow: {
    label: 'Remove from Automation',
    icon: 'log-out',
    theme: 'red',
    category: 'data',
    description: 'Pulls the record out of another automation.',
    defaults: { automation: '' },
    gateable: true,
  },
  wait: {
    label: 'Wait',
    icon: 'clock',
    theme: 'orange',
    category: 'flow',
    description: 'Holds here for a delay, a time of day or an answer.',
    defaults: { mode: 'duration', days: 0, hours: 4, minutes: 0 },
    gateable: false,
  },
  if_else: {
    label: 'If / Else',
    icon: 'git-branch',
    theme: 'orange',
    category: 'flow',
    description: 'Splits the flow on conditions, with a "None" branch.',
    defaults: {},
    gateable: false,
    branching: true,
  },
  split: {
    label: 'Split Test',
    icon: 'shuffle',
    theme: 'blue',
    category: 'flow',
    description: 'Sends a percentage of records down each path.',
    defaults: {},
    gateable: false,
    branching: true,
  },
  goal: {
    label: 'Goal',
    icon: 'target',
    theme: 'purple',
    category: 'flow',
    description: 'A checkpoint records jump forward to when they reach it.',
    defaults: { event: 'reply', value: '', outcome: 'continue' },
    gateable: false,
  },
  go_to: {
    label: 'Go To',
    icon: 'corner-down-right',
    theme: 'purple',
    category: 'flow',
    description: 'Jumps to a labelled step.',
    defaults: { target: '' },
    gateable: false,
  },
  stop_if: {
    label: 'Stop If',
    icon: 'x-octagon',
    theme: 'red',
    category: 'flow',
    description: 'Leaves the automation when a condition is met.',
    defaults: {},
    gateable: false,
  },
  exit: {
    label: 'Exit',
    icon: 'log-out',
    theme: 'red',
    category: 'flow',
    description: 'Ends the automation for this record.',
    defaults: {},
    gateable: false,
  },
  // legacy alias kept for automations saved before "add_note" existed
  add_tag_comment: {
    label: 'Add Note',
    icon: 'file-text',
    theme: 'gray',
    category: 'contact',
    description: 'Leaves a note in the record timeline.',
    defaults: { comment: '' },
    gateable: true,
    hidden: true,
  },
}

/**
 * The palette. Mostly one entry per step type, plus a few presets: the same
 * step type with fields already filled in, which is how "move the deal to a
 * stage" reads on the canvas without inventing a step type for it.
 */
export const PALETTE = [
  ...Object.entries(STEP_CATALOG)
    .filter(([, definition]) => !definition.hidden)
    .map(([type, definition]) => ({
      key: type,
      type,
      label: definition.label,
      description: definition.description,
      icon: definition.icon,
      theme: definition.theme,
      category: definition.category,
    })),
  {
    key: 'deal_stage',
    type: 'set_field',
    label: 'Move Deal to Stage',
    description: 'Moves the deal to another stage of its pipeline.',
    icon: 'flag',
    theme: 'green',
    category: 'deal',
    values: { field: 'status', value: '' },
  },
  {
    key: 'deal_value',
    type: 'set_field',
    label: 'Set Deal Value',
    description: 'Writes the expected value of the deal.',
    icon: 'dollar-sign',
    theme: 'green',
    category: 'deal',
    values: { field: 'expected_deal_value', value: '' },
  },
  {
    key: 'deal_close_date',
    type: 'set_field',
    label: 'Set Expected Closing Date',
    description: 'Writes the expected closing date of the deal.',
    icon: 'calendar',
    theme: 'green',
    category: 'deal',
    values: { field: 'expected_closure_date', value: '' },
  },
  {
    key: 'deal_next_step',
    type: 'set_field',
    label: 'Set Next Step',
    description: 'Writes the next step agreed with the customer.',
    icon: 'arrow-right',
    theme: 'green',
    category: 'deal',
    values: { field: 'next_step', value: '' },
  },
]

export const TRIGGER_CATEGORIES = [
  { name: 'lead', label: 'Person', icon: 'user' },
  { name: 'deal', label: 'Deal (opportunity)', icon: 'briefcase' },
  { name: 'appointment', label: 'Appointments', icon: 'calendar' },
  { name: 'messaging', label: 'Conversations', icon: 'message-square' },
  { name: 'record', label: 'Activity on the record', icon: 'activity' },
  { name: 'other', label: 'Time and integrations', icon: 'globe' },
]

/** trigger event → category, icon, which record it enrols and its filters. */
export const TRIGGER_CATALOG = {
  'Lead Created': { category: 'lead', icon: 'user-plus', doctype: 'CRM Lead' },
  // a person is created once; a form can be filled in again by somebody the
  // CRM already knows, and that submission still has to start something
  'Lead Form Submitted': {
    category: 'lead',
    icon: 'clipboard',
    doctype: 'CRM Lead',
    hint: "A form is filled in, an ad's or one on the website — by a new person or by one {brand} already knows.",
  },
  'Lead Status Changed': {
    category: 'lead',
    icon: 'refresh-cw',
    doctype: 'CRM Lead',
    hint: 'The person moves to another status.',
  },
  // the first time the person comes, or buys (crm.clienti): a Pilates class too
  'Became Client': {
    category: 'lead',
    icon: 'user-check',
    doctype: 'CRM Lead',
    hint: 'The person becomes a client of the centre: the first time they come, or their first invoice.',
  },
  // with the clinic: a health service, or health data the centre keeps
  // (crm.clinica.paziente); offered only where the clinic is on
  'Became Patient': {
    category: 'lead',
    icon: 'heart',
    doctype: 'CRM Lead',
    hint: 'The person becomes a patient of the centre: a health service, or health data the centre keeps.',
  },
  'Deal Created': {
    category: 'deal',
    icon: 'briefcase',
    doctype: 'CRM Deal',
  },
  'Deal Status Changed': {
    category: 'deal',
    icon: 'flag',
    doctype: 'CRM Deal',
    hint: 'The deal moves to another stage of the pipeline.',
  },
  // bookings made by the client on the booking page; "Appointment …" covers all
  'Booking Created': {
    category: 'appointment',
    icon: 'calendar',
    hint: 'The client books online, on the booking page.',
  },
  'Booking Cancelled': {
    category: 'appointment',
    icon: 'x-circle',
    hint: 'An online booking is cancelled.',
  },
  'Booking No Show': { category: 'appointment', icon: 'user-x' },
  'Booking Completed': { category: 'appointment', icon: 'check-circle' },
  'Appointment Created': { category: 'appointment', icon: 'calendar' },
  'Appointment Rescheduled': { category: 'appointment', icon: 'repeat' },
  'Appointment Cancelled': { category: 'appointment', icon: 'x-circle' },
  'Appointment No Show': { category: 'appointment', icon: 'user-x' },
  'Appointment Completed': { category: 'appointment', icon: 'check-circle' },
  // a call nobody answered, from somebody the centre knows (crm.telephony.persa)
  'Missed Call': {
    category: 'messaging',
    icon: 'phone-missed',
    hint: 'Somebody the centre knows called and nobody answered.',
  },
  'Incoming SMS': { category: 'messaging', icon: 'message-square' },
  'Customer Replied': {
    category: 'messaging',
    icon: 'corner-up-left',
    hint: 'The contact answers by SMS, WhatsApp or email.',
  },
  'Email Opened': {
    category: 'messaging',
    icon: 'mail',
    hint: 'Read tracking on an email sent by {brand}.',
  },
  'Trigger Link Clicked': {
    category: 'messaging',
    icon: 'mouse-pointer',
    config: 'link',
    hint: 'A click on a tracked link inside a message.',
  },
  'Tag Added': { category: 'record', icon: 'tag', config: 'tag' },
  'Tag Removed': { category: 'record', icon: 'tag', config: 'tag' },
  'Task Completed': { category: 'record', icon: 'check-square' },
  'Note Added': { category: 'record', icon: 'file-text' },
  'Date Reminder': {
    category: 'other',
    icon: 'clock',
    config: 'date',
    hint: 'A date field comes up — birthdays, renewals, anything.',
  },
  'Inbound Webhook': {
    category: 'other',
    icon: 'globe',
    config: 'webhook',
    hint: 'An external system posts to a URL and enrols the contact.',
  },
}

/** Palette entries for the trigger picker, in the order the backend allows. */
export function triggerEntries(events) {
  return (events || []).map((event) => {
    const definition = triggerDefinition(event)
    return {
      key: event,
      label: event,
      description: definition.hint || '',
      icon: definition.icon,
      theme: 'gray',
      category: definition.category,
    }
  })
}

export const CONDITION_OPERATORS = [
  { value: 'equals', label: 'is' },
  { value: 'not_equals', label: 'is not' },
  { value: 'contains', label: 'contains' },
  { value: 'is_set', label: 'is set' },
  { value: 'is_not_set', label: 'is empty' },
  { value: 'greater_than', label: '>' },
  { value: 'less_than', label: '<' },
]

const NUMERIC_FIELDTYPES = [
  'Int',
  'Float',
  'Currency',
  'Percent',
  'Duration',
  'Rating',
]

const VALUELESS_OPERATORS = ['is_set', 'is_not_set']

export const GOAL_EVENTS = [
  { value: 'reply', label: 'Contact replied' },
  { value: 'link_clicked', label: 'Tracked link clicked' },
  { value: 'tag_added', label: 'Tag added' },
  { value: 'status_is', label: 'Status becomes' },
  { value: 'booking_booked', label: 'Appointment booked' },
]

export const WAIT_MODES = [
  { value: 'duration', label: 'A period of time' },
  { value: 'until_time', label: 'A time of day' },
  { value: 'until_reply', label: 'The contact to reply' },
  { value: 'until_link_click', label: 'A tracked link click' },
]

export const WEEKDAYS = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
]

/** Placeholders offered by the merge-field menu next to every text input. */
export const MERGE_FIELDS = [
  { token: '{{ first_name }}', label: 'First name' },
  { token: '{{ last_name }}', label: 'Last name' },
  { token: '{{ lead_name }}', label: 'Full name' },
  { token: '{{ organization }}', label: 'Organization' },
  { token: '{{ email }}', label: 'Email' },
  { token: '{{ mobile_no }}', label: 'Mobile number' },
  { token: '{{ status }}', label: 'Status' },
  { token: '{{ tracked_link("slug") }}', label: 'Tracked link' },
  { token: '{{ booking_link }}', label: 'Booking page link' },
  // asks for a review on Google: the server sends it only to who agreed, once
  // in a while (crm/recensioni), and writes the request first
  { token: '{{ review_link }}', label: 'Google review link' },
]

/** Full class strings per theme — Tailwind only sees literals, not templates. */
export const ICON_CLASSES = {
  blue: 'bg-surface-blue-2 text-ink-blue-7',
  green: 'bg-surface-green-2 text-ink-green-7',
  red: 'bg-surface-red-2 text-ink-red-7',
  orange: 'bg-surface-amber-2 text-ink-amber-7',
  purple: 'bg-surface-violet-2 text-ink-violet-7',
  gray: 'bg-surface-gray-2 text-ink-gray-7',
}

// --- catalogue lookups -----------------------------------------------------

const FALLBACK = {
  label: 'Step',
  icon: 'circle',
  theme: 'gray',
  category: 'data',
  description: '',
  defaults: {},
  gateable: true,
}

export function stepDefinition(type) {
  return STEP_CATALOG[type] || { ...FALLBACK, label: type || 'Step' }
}

export function stepLabel(step) {
  const type = typeof step === 'string' ? step : step?.type
  const definition = stepDefinition(type)
  if (typeof step === 'object' && step?.label) return step.label
  return __(definition.label)
}

export function stepIcon(type) {
  return stepDefinition(type).icon
}

export function stepTheme(type) {
  return stepDefinition(type).theme
}

export function isBranching(type) {
  return Boolean(stepDefinition(type).branching)
}

export function triggerDefinition(event) {
  return TRIGGER_CATALOG[event] || { category: 'other', icon: 'zap' }
}

/** The doctype a trigger enrols, or null when it can be either. */
export function triggerDoctype(event) {
  return triggerDefinition(event).doctype || null
}

/** Which extra filter panel the trigger needs: tag, link, date, webhook. */
export function triggerConfigKind(event) {
  return triggerDefinition(event).config || null
}

// --- ids and construction --------------------------------------------------

let counter = 0

export function newId() {
  counter += 1
  return `n${Date.now().toString(36)}${counter.toString(36)}`
}

export function newCondition() {
  return { field: '', operator: 'equals', value: '' }
}

export function newConditionGroup() {
  return [newCondition()]
}

/** A trigger row: the event, its event filters and its own record conditions. */
export function newTrigger(event = 'Lead Created') {
  return {
    id: newId(),
    event,
    config: {},
    condition_groups: [newConditionGroup()],
  }
}

/** API shape → editor shape, with the pre-table single trigger folded in. */
export function normalizeTriggers(data) {
  const rows = data?.triggers?.length
    ? data.triggers
    : [
        {
          event: data?.trigger_event || 'Lead Created',
          config: data?.trigger_config || {},
          condition: data?.trigger_condition,
        },
      ]
  return rows.map((row) => ({
    id: newId(),
    event: row.event || row.trigger_event,
    config: row.config || {},
    condition_groups: normalizeGroups(row.condition),
  }))
}

/** Editor shape → API payload; empty conditions are dropped, not sent as noise. */
export function serializeTriggers(triggers) {
  return (triggers || []).map((trigger) => ({
    event: trigger.event,
    config: trigger.config || {},
    condition: cleanGroups(trigger.condition_groups),
  }))
}

/** The record every trigger agrees on, or null when they disagree (or don't say). */
export function sharedTriggerDoctype(triggers) {
  const doctypes = new Set((triggers || []).map((t) => triggerDoctype(t.event)))
  if (doctypes.size !== 1) return null
  return [...doctypes][0]
}

export function newBranch(label = '') {
  return {
    id: newId(),
    label,
    condition_groups: [newConditionGroup()],
    steps: [],
  }
}

export function newPath(label, percent) {
  return { id: newId(), label, percent, steps: [] }
}

export function newStep(type, values = {}) {
  const step = {
    id: newId(),
    type,
    ...structuredClone(stepDefinition(type).defaults || {}),
    ...structuredClone(values),
  }
  if (type === 'if_else') {
    step.branches = [newBranch()]
    step.else_steps = []
  }
  if (type === 'split') {
    step.paths = [newPath('A', 50), newPath('B', 50)]
  }
  if (type === 'stop_if') {
    step.condition_groups = [newConditionGroup()]
  }
  return step
}

/** A palette entry becomes a step: its type plus the preset values. */
export function stepFromPalette(entry) {
  return newStep(entry.type, entry.values || {})
}

/** Deep copy with brand new ids, so a pasted step never shares statistics. */
export function cloneStep(step) {
  const copy = structuredClone(step)
  const reid = (node) => {
    node.id = newId()
    for (const branch of node.branches || []) {
      branch.id = newId()
      ;(branch.steps || []).forEach(reid)
    }
    ;(node.else_steps || []).forEach(reid)
    for (const path of node.paths || []) {
      path.id = newId()
      ;(path.steps || []).forEach(reid)
    }
  }
  reid(copy)
  return copy
}

/**
 * Automations saved before the visual editor carry no ids and use the single
 * `condition` shape. Normalising on load keeps the rest of the editor simple.
 */
export function normalizeSteps(steps) {
  for (const step of steps || []) {
    if (!step.id) step.id = newId()
    if (step.condition && !step.condition_groups) {
      step.condition_groups = step.condition.field ? [[step.condition]] : []
      delete step.condition
    }
    if (step.condition_groups && !step.condition_groups.length) {
      delete step.condition_groups
    }
    if (step.type === 'if_else') {
      if (!step.branches?.length) step.branches = [newBranch()]
      if (!step.else_steps) step.else_steps = []
    }
    if (step.type === 'split' && !step.paths?.length) {
      step.paths = [newPath('A', 50), newPath('B', 50)]
    }
    for (const branch of step.branches || []) {
      if (!branch.id) branch.id = newId()
      if (!branch.steps) branch.steps = []
      if (!branch.condition_groups?.length) {
        branch.condition_groups = [newConditionGroup()]
      }
      normalizeSteps(branch.steps)
    }
    normalizeSteps(step.else_steps || [])
    for (const path of step.paths || []) {
      if (!path.id) path.id = newId()
      if (!path.steps) path.steps = []
      normalizeSteps(path.steps)
    }
  }
  return steps
}

/** Enrolment filters: one condition (legacy) or a list of AND groups. */
export function normalizeGroups(value) {
  if (Array.isArray(value)) return value.length ? value : [newConditionGroup()]
  if (value && value.field) return [[value]]
  return [newConditionGroup()]
}

/** Drop empty rows and groups; returns null when nothing is left to send. */
export function cleanGroups(groups) {
  const cleaned = (groups || [])
    .map((group) => (group || []).filter((condition) => condition?.field))
    .filter((group) => group.length)
  return cleaned.length ? cleaned : null
}

// --- tree surgery ----------------------------------------------------------

/** Every list of steps hanging off a node: branches, the else block, paths. */
export function childLists(step) {
  const lists = []
  for (const branch of step?.branches || []) lists.push(branch.steps)
  if (step?.else_steps) lists.push(step.else_steps)
  for (const path of step?.paths || []) lists.push(path.steps)
  return lists
}

/** Depth-first visit of every node with the list holding it. */
export function walkSteps(steps, visit) {
  const walk = (list) => {
    list?.forEach((step, index) => {
      if (visit({ step, list, index }) === false) return
      childLists(step).forEach(walk)
    })
  }
  walk(steps)
}

export function findStep(steps, id) {
  let found = null
  walkSteps(steps, (entry) => {
    if (entry.step.id === id) {
      found = entry
      return false
    }
    return true
  })
  return found
}

export function removeStep(steps, id) {
  const entry = findStep(steps, id)
  if (!entry) return null
  return entry.list.splice(entry.index, 1)[0]
}

/** Copy of a step, dropped right after the original. Returns the new node. */
export function duplicateStep(steps, id) {
  const entry = findStep(steps, id)
  if (!entry) return null
  const copy = cloneStep(entry.step)
  entry.list.splice(entry.index + 1, 0, copy)
  return copy
}

export function moveStep(list, index, delta) {
  const target = index + delta
  if (target < 0 || target >= list.length) return false
  const [step] = list.splice(index, 1)
  list.splice(target, 0, step)
  return true
}

export function countSteps(steps) {
  let total = 0
  walkSteps(steps, () => {
    total += 1
    return true
  })
  return total
}

/** Labels available as Go To targets. */
export function stepLabels(steps) {
  const labels = []
  walkSteps(steps, ({ step }) => {
    if (step.label) labels.push(step.label)
    return true
  })
  return labels
}

// --- summaries -------------------------------------------------------------

export function operatorLabel(operator) {
  const found = CONDITION_OPERATORS.find((o) => o.value === operator)
  return __(found ? found.label : operator || 'is')
}

export function needsValue(operator) {
  return !VALUELESS_OPERATORS.includes(operator)
}

export function operatorsForFieldtype(fieldtype) {
  // a file, a table, a signature: given or not, nothing to compare
  if (fieldtype === 'Attach') {
    return CONDITION_OPERATORS.filter((o) =>
      VALUELESS_OPERATORS.includes(o.value),
    )
  }
  if (fieldtype === 'Check') {
    return CONDITION_OPERATORS.filter((o) =>
      ['equals', 'not_equals'].includes(o.value),
    )
  }
  if (NUMERIC_FIELDTYPES.includes(fieldtype) || fieldtype === 'Date') {
    return CONDITION_OPERATORS.filter((o) => o.value !== 'contains')
  }
  return CONDITION_OPERATORS
}

/** A condition in words: the field by its label where the editor's fields know it,
 * never its fieldname (`mobile_no`). */
export function conditionSummary(condition, fields = []) {
  if (!condition?.field) return ''
  const campo = (fields || []).find((f) => f.fieldname === condition.field)
  const nome = campo?.label || condition.field
  const operator = operatorLabel(condition.operator)
  if (!needsValue(condition.operator)) return `${nome} ${operator}`
  return `${nome} ${operator} ${condition.value ?? ''}`.trim()
}

export function groupsSummary(groups, fields = []) {
  const cleaned = cleanGroups(groups)
  if (!cleaned) return __('Always')
  return cleaned
    .map((group) =>
      group.map((c) => conditionSummary(c, fields)).join(` ${__('and')} `),
    )
    .join(` ${__('or')} `)
}

export function waitSummary(step) {
  if (step.mode === 'until_time') {
    return __('until {0}', [step.time || '09:00'])
  }
  const timeout = step.timeout_hours
    ? ` · ${__('max {0}h', [step.timeout_hours])}`
    : ''
  if (step.mode === 'until_reply')
    return __('until the contact replies') + timeout
  if (step.mode === 'until_link_click') {
    return __('until a click on {0}', [step.link || __('any link')]) + timeout
  }
  const parts = [
    step.days && __('{0}d', [step.days]),
    step.hours && __('{0}h', [step.hours]),
    step.minutes && __('{0}m', [step.minutes]),
  ].filter(Boolean)
  return parts.length ? parts.join(' ') : __('no delay')
}

/** What a trigger listens to, in one line: its filters and its conditions. */
export function triggerSummary(trigger, fields = []) {
  const parts = []
  const config = trigger?.config || {}
  if (config.tag) parts.push(__('tag «{0}»', [config.tag]))
  if (config.link) parts.push(__('link «{0}»', [config.link]))
  if (config.date_field) {
    // nothing to translate in «{0} {1} {2}»: the words are in the parts, and
    // the direction is already translated on its own
    parts.push(
      [
        config.date_field,
        config.offset_days || 0,
        __(config.direction || 'before'),
      ].join(' '),
    )
  }
  const groups = cleanGroups(trigger?.condition_groups)
  if (groups) parts.push(groupsSummary(groups, fields))
  return parts.join(' · ') || __('every record')
}

/**
 * A step's words as the canvas shows them: a field's placeholder
 * («{{ first_name }}») reads as the field's name the builder offers it by
 * («Nome»). The step keeps what was written; a placeholder the builder does
 * not offer stays as it is.
 */
export function segnapostiInParole(testo) {
  if (!testo) return testo
  return testo.replace(
    /\{\{\s*([a-z_]+)\s*(?:\([^)]*\))?\s*\}\}/g,
    (tutto, campo) => {
      const voce = MERGE_FIELDS.find(
        (v) => v.token.replace(/[{}\s]/g, '').split('(')[0] === campo,
      )
      return voce ? `«${__(voce.label)}»` : tutto
    },
  )
}

export function stepSummary(step, fields = []) {
  switch (step.type) {
    case 'send_email':
      return (
        segnapostiInParole(step.subject) ||
        step.email_template ||
        __('No subject')
      )
    case 'send_sms':
    case 'notify':
      return segnapostiInParole(step.message) || __('No message')
    case 'send_whatsapp_template':
      return step.template || __('No template selected')
    case 'send_form':
      return step.template_title || step.template || __('No form selected')
    case 'create_task':
      return segnapostiInParole(step.title) || __('Follow up')
    case 'assign':
      return (
        (step.users || []).join(', ') || step.user || __('No user selected')
      )
    case 'add_note':
    case 'add_tag_comment':
      return segnapostiInParole(step.comment) || __('No note')
    case 'add_tag':
    case 'remove_tag':
      return step.tag || __('No tag')
    case 'set_field':
      return `${step.field || '?'} → ${step.value ?? ''}`
    case 'convert_to_deal':
      return __('Creates a deal from this lead')
    case 'webhook':
      return `${step.method || 'POST'} ${step.url || '?'}`
    case 'wait':
      return waitSummary(step)
    case 'goal': {
      const event = GOAL_EVENTS.find((g) => g.value === step.event)
      return `${__(event ? event.label : step.event || '?')}${
        step.value ? ` = ${step.value}` : ''
      }`
    }
    case 'go_to':
      return step.target ? `→ ${step.target}` : __('No target')
    case 'exit':
      return __('The record leaves here')
    case 'stop_if':
      return groupsSummary(step.condition_groups, fields)
    case 'if_else':
      return __('{0} branch(es) + None', [(step.branches || []).length])
    case 'split':
      return (step.paths || [])
        .map((path) => `${path.label || '?'} ${path.percent || 0}%`)
        .join(' · ')
    case 'add_to_workflow':
    case 'remove_from_workflow':
      return step.automation || '?'
    default:
      return ''
  }
}

// --- validation ------------------------------------------------------------

/**
 * Problems found in the draft, most severe first.
 *
 * `error` is what the backend would refuse — saving is blocked. `warning` is a
 * step that would run but do nothing useful (an SMS with no text, a webhook
 * with no URL): the draft saves, going live does not.
 */
export function validateAutomation(draft) {
  const issues = []
  const add = (level, message, node = null) =>
    issues.push({ level, message, node })

  if (!draft.title?.trim()) add('error', __('The automation needs a title'))
  if (!draft.steps?.length) add('error', __('Add at least one step'))
  if (!draft.triggers?.length) add('error', __('Add at least one trigger'))

  const seen = new Set()
  for (const trigger of draft.triggers || []) {
    const where = __(trigger.event)
    const node = `trigger:${trigger.id}`
    if (
      triggerConfigKind(trigger.event) === 'date' &&
      !trigger.config?.date_field
    ) {
      add(
        'warning',
        `${where}: ${__('pick the date field the reminder watches')}`,
        node,
      )
    }
    // two triggers on the same event with the same filters: the second never fires
    const fingerprint = `${trigger.event}|${JSON.stringify(trigger.config || {})}`
    if (seen.has(fingerprint)) {
      add(
        'warning',
        `${where}: ${__('a trigger with the same filters is already there')}`,
        node,
      )
    }
    seen.add(fingerprint)
  }

  const labels = stepLabels(draft.steps || [])

  walkSteps(draft.steps || [], ({ step }) => {
    const where = stepLabel(step)
    const problem = (level, message) =>
      add(level, `${where}: ${message}`, step.id)

    switch (step.type) {
      case 'send_email':
        if (!step.email_template && !step.subject) {
          problem('warning', __('no subject and no template'))
        }
        if (!step.email_template && !step.message) {
          problem('warning', __('empty body'))
        }
        break
      case 'send_sms':
      case 'notify':
        if (!step.message) problem('warning', __('empty message'))
        break
      case 'send_whatsapp_template':
        if (!step.template) problem('warning', __('no template selected'))
        break
      case 'send_form':
        if (!step.template) problem('warning', __('no form selected'))
        if (step.via === 'whatsapp' && !step.whatsapp_template) {
          problem('warning', __('no template selected'))
        }
        break
      case 'create_task':
        if (!step.title) problem('warning', __('no task title'))
        break
      case 'assign':
        if (!(step.users || []).length) problem('warning', __('no user picked'))
        break
      case 'add_note':
      case 'add_tag_comment':
        if (!step.comment) problem('warning', __('empty note'))
        break
      case 'add_tag':
      case 'remove_tag':
        if (!step.tag?.trim()) problem('warning', __('no tag'))
        break
      case 'set_field':
        if (!step.field) problem('warning', __('no field selected'))
        break
      case 'webhook':
        if (!/^https?:\/\//.test(step.url || '')) {
          problem('warning', __('the URL must start with http(s)://'))
        }
        break
      case 'add_to_workflow':
      case 'remove_from_workflow':
        if (!step.automation) problem('warning', __('no automation selected'))
        break
      case 'wait': {
        const mode = step.mode || 'duration'
        if (mode === 'duration') {
          const minutes =
            (Number(step.days) || 0) * 1440 +
            (Number(step.hours) || 0) * 60 +
            (Number(step.minutes) || 0)
          if (minutes <= 0) problem('error', __('the delay must be positive'))
        }
        if (mode === 'until_time' && !step.time) {
          problem('warning', __('no time of day set'))
        }
        break
      }
      case 'goal':
        if (!GOAL_EVENTS.some((g) => g.value === step.event)) {
          problem('error', __('pick a goal event'))
        }
        break
      case 'go_to':
        if (!step.target) problem('error', __('no target step'))
        else if (!labels.includes(step.target)) {
          problem('error', __('no step is labelled «{0}»', [step.target]))
        }
        break
      case 'stop_if':
        if (!cleanGroups(step.condition_groups)) {
          problem('error', __('a stop needs a condition'))
        }
        break
      case 'if_else': {
        const branches = step.branches || []
        if (!branches.length) problem('error', __('needs at least one branch'))
        branches.forEach((branch, index) => {
          if (!cleanGroups(branch.condition_groups)) {
            problem(
              'warning',
              __('branch «{0}» has no condition and always matches', [
                branch.label || index + 1,
              ]),
            )
          }
        })
        break
      }
      case 'split': {
        const paths = step.paths || []
        const total = paths.reduce(
          (sum, path) => sum + (Number(path.percent) || 0),
          0,
        )
        if (!paths.length || Math.abs(total - 100) > 0.01) {
          problem('error', __('the percentages must add up to 100'))
        }
        break
      }
      default:
        break
    }
    return true
  })

  return issues.sort((a, b) =>
    a.level === b.level ? 0 : a.level === 'error' ? -1 : 1,
  )
}

export function hasErrors(issues) {
  return issues.some((issue) => issue.level === 'error')
}

// --- recipes ---------------------------------------------------------------

/** Ready-made flows, the GHL "recipes": a starting point, not a black box. */
export const RECIPES = [
  {
    key: 'welcome',
    title: 'Welcome a new lead',
    description:
      'Email straight away, reminder after two days, task for the owner.',
    icon: 'mail',
    trigger_event: 'Lead Created',
    build: () => [
      newStep('send_email', {
        subject: __('Nice to meet you, {{ first_name }}'),
        message: __('Hi {{ first_name }}, thanks for getting in touch.'),
      }),
      newStep('wait', { mode: 'duration', days: 2, hours: 0, minutes: 0 }),
      newStep('goal', { event: 'reply', outcome: 'end' }),
      newStep('send_email', {
        subject: __('Still interested, {{ first_name }}?'),
        message: __('Just checking you got my message.'),
      }),
      newStep('create_task', {
        title: __('Call {{ lead_name }}'),
        due_in_days: 1,
      }),
    ],
  },
  {
    // the second seam: from the centre to marketing, only with the yes
    key: 'recall',
    title: 'Recall after a year',
    description:
      'Whoever last came a year ago, and agreed to marketing, is invited to book again.',
    icon: 'rotate-ccw',
    trigger_event: 'Date Reminder',
    trigger_config: {
      doctype: 'CRM Lead',
      date_field: 'last_visit',
      direction: 'after',
      offset_days: 365,
    },
    marketing_consent: true,
    build: () => [
      newStep('send_email', {
        subject: __('Time for your check-up, {{ first_name }}'),
        message:
          'Hi {{ first_name }}, it has been a year since your last visit. Shall we book the next one?',
      }),
      newStep('wait', { mode: 'duration', days: 7, hours: 0, minutes: 0 }),
      newStep('goal', { event: 'booking_booked', outcome: 'end' }),
      newStep('create_task', {
        title: __('Call {{ lead_name }} for the recall'),
        due_in_days: 1,
      }),
    ],
  },
  {
    key: 'no_show',
    title: 'No-show follow-up',
    description:
      'Texts whoever missed the appointment and asks them to rebook.',
    icon: 'user-x',
    trigger_event: 'Appointment No Show',
    build: () => [
      newStep('send_sms', {
        message: __(
          'Hi {{ first_name }}, we missed you today. Shall we rebook?',
        ),
      }),
      newStep('wait', { mode: 'duration', days: 1, hours: 0, minutes: 0 }),
      newStep('create_task', {
        title: __('Rebook {{ lead_name }}'),
        due_in_days: 0,
      }),
    ],
  },
  {
    // off until the centre switches it on, as every recipe: an SMS a minute after
    // a call nobody answered, with the booking page on a line of its own (left out
    // where the centre takes no booking online); STOP is never written to
    key: 'missed_call',
    title: 'We missed you… missed call',
    description:
      'A minute after a call nobody answered, texts the caller the link to book online.',
    icon: 'phone-missed',
    trigger_event: 'Missed Call',
    build: () => [
      newStep('wait', { mode: 'duration', days: 0, hours: 0, minutes: 1 }),
      newStep('send_sms', {
        message: __(
          'Hi {{ first_name }}, sorry we missed your call. We will call you back.\nTo book now: {{ booking_link }}',
        ),
      }),
    ],
  },
  {
    // off until the centre switches it on, as every recipe: two hours after a
    // visit, the same words to everybody (Google forbids choosing who is asked);
    // the server lets it leave only to who agreed, once in so many months, and
    // never after a service the settings exclude
    key: 'review_after_visit',
    title: 'Ask for a review after the visit',
    description:
      'Two hours after a visit, the link to review the centre on Google: by SMS, or by email to who has no mobile.',
    icon: 'star',
    trigger_event: 'Appointment Completed',
    build: () => {
      const domanda = newStep('if_else')
      domanda.branches[0].label = __('Has a mobile')
      domanda.branches[0].condition_groups = [
        [{ field: 'mobile_no', operator: 'is_set', value: '' }],
      ]
      domanda.branches[0].steps = [
        newStep('send_sms', {
          message: __(
            'Hi {{ first_name }}, thank you for coming. If you have a minute, tell others how it went: {{ review_link }}',
          ),
        }),
      ]
      domanda.else_steps = [
        newStep('send_email', {
          subject: __('How did it go, {{ first_name }}?'),
          message: __(
            'Hi {{ first_name }}, thank you for coming. If you have a minute, tell others how it went with a review on Google: {{ review_link }}',
          ),
        }),
      ]
      return [
        newStep('wait', { mode: 'duration', days: 0, hours: 2, minutes: 0 }),
        domanda,
      ]
    },
  },
  {
    // off until the centre switches it on: the day after a visit, the link to
    // a survey of the centre's (a starter in Settings > Clients > Forms), whose
    // 0 to 10 question makes the dashboard's «Satisfaction (NPS)»
    key: 'satisfaction_survey',
    title: 'Satisfaction survey after the visit',
    description:
      'The day after a visit, the link to a short survey: how likely they are to recommend the centre, from 0 to 10.',
    icon: 'smile',
    trigger_event: 'Appointment Completed',
    build: () => [
      newStep('wait', { mode: 'duration', days: 1, hours: 0, minutes: 0 }),
      newStep('send_form', {
        via: 'sms',
        message: __(
          'Hi {{ first_name }}, how did your visit go? It takes a minute: {{ form_link }}',
        ),
      }),
    ],
  },
  {
    key: 'deal_won',
    title: 'Deal moved stage',
    description: 'Notifies the team and tags the deal when the stage changes.',
    icon: 'briefcase',
    trigger_event: 'Deal Status Changed',
    build: () => [
      newStep('notify', {
        message: __('Deal {{ organization }} is now {{ status }}'),
      }),
      newStep('add_tag', { tag: __('stage-changed') }),
    ],
  },
  {
    key: 'nurture',
    title: 'Long nurture with a split test',
    description:
      'Two subject lines, 50/50, and a goal that stops the sequence.',
    icon: 'shuffle',
    trigger_event: 'Tag Added',
    build: () => {
      const split = newStep('split')
      split.paths[0].steps = [
        newStep('send_email', { subject: __('A tip for you'), message: '…' }),
      ]
      split.paths[1].steps = [
        newStep('send_email', {
          subject: __('{{ first_name }}, one idea'),
          message: '…',
        }),
      ]
      return [
        newStep('goal', { event: 'reply', outcome: 'end' }),
        split,
        newStep('wait', { mode: 'duration', days: 3, hours: 0, minutes: 0 }),
        newStep('send_sms', {
          message: __('Did you get my email, {{ first_name }}?'),
        }),
      ]
    },
  },
]
