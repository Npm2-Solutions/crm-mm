// Pure helpers behind the online-booking settings of a service and the
// booking-platform connections. Kept free of Vue so they are unit-tested.

/** Public booking link of a service: /prenota?servizio=<slug or name>. */
export function bookingLink(origin, service) {
  const key = service?.website_slug || service?.name || service?.service_name
  const base = `${(origin || '').replace(/\/$/, '')}/prenota`
  return key ? `${base}?servizio=${encodeURIComponent(key)}` : base
}

/** Fields the online panel edits, with the defaults a new service starts from. */
export const ONLINE_DEFAULTS = Object.freeze({
  online_confirmation: 'Automatic',
  allow_staff_choice: true,
  show_price_online: true,
  online_slot_interval: 0,
  online_max_participants: 1,
  booking_opens_on: '',
  booking_closes_on: '',
  same_day_cutoff: '',
  require_phone: true,
  require_notes: false,
  online_question: '',
  booking_instructions: '',
  max_bookings_per_day: 0,
  max_bookings_per_week: 0,
  max_concurrent: 0,
  customer_eligibility: 'Everyone',
  max_active_per_customer: 0,
  max_per_customer_per_day: 0,
  min_days_between: 0,
  allow_online_cancel: true,
  cancel_notice_hours: 0,
  allow_online_reschedule: true,
  reschedule_notice_hours: 0,
  max_reschedules: 0,
})

const ONLINE_FLAGS = [
  'allow_staff_choice',
  'show_price_online',
  'require_phone',
  'require_notes',
  'allow_online_cancel',
  'allow_online_reschedule',
]

/**
 * Online fields of a loaded service, normalised for the form: checks as
 * booleans (a missing check keeps its default), empty dates/times as ''.
 */
export function onlineFieldsFrom(data = {}) {
  const out = {}
  for (const [key, fallback] of Object.entries(ONLINE_DEFAULTS)) {
    const value = data[key]
    if (ONLINE_FLAGS.includes(key)) {
      out[key] =
        value === undefined || value === null ? fallback : Boolean(value)
    } else if (typeof fallback === 'number') {
      out[key] =
        value === undefined || value === null || value === ''
          ? fallback
          : Number(value) || 0
    } else {
      out[key] = value ?? fallback
    }
  }
  if (out.same_day_cutoff && out.same_day_cutoff.length > 5) {
    out.same_day_cutoff = out.same_day_cutoff.slice(0, 5)
  }
  out.online_overrides = Array.isArray(data.online_overrides)
    ? [...data.online_overrides]
    : []
  out.online_defaults = { ...(data.online_defaults || {}) }
  out.hide_from_menu = Boolean(data.hide_from_menu)
  return out
}

/**
 * One-line summary of the limits a service applies online, for the service
 * list and the panel header. `t` is the translator (`__` in the app).
 */
export function describeOnlineLimits(form, t = (s, a) => format(s, a)) {
  if (!form?.bookable_online) return []
  form = effectiveForm(form)
  const parts = []
  if (form.online_confirmation === 'Manual approval') parts.push(t('approval'))
  if (form.min_notice_hours)
    parts.push(t('{0}h notice', [form.min_notice_hours]))
  if (form.max_horizon_days)
    parts.push(t('{0} days ahead', [form.max_horizon_days]))
  if (form.same_day_cutoff)
    parts.push(t('same day until {0}', [form.same_day_cutoff]))
  if (form.max_bookings_per_day)
    parts.push(t('max {0}/day', [form.max_bookings_per_day]))
  if (form.max_bookings_per_week)
    parts.push(t('max {0}/week', [form.max_bookings_per_week]))
  if (form.max_concurrent)
    parts.push(t('max {0} at once', [form.max_concurrent]))
  if (form.max_active_per_customer) {
    parts.push(t('{0} upcoming per client', [form.max_active_per_customer]))
  }
  if (form.min_days_between)
    parts.push(t('{0} days apart', [form.min_days_between]))
  if (form.customer_eligibility === 'New customers only')
    parts.push(t('new clients'))
  if (form.customer_eligibility === 'Returning customers only') {
    parts.push(t('returning clients'))
  }
  if (form.allow_online_cancel === false) parts.push(t('no online cancel'))
  else if (form.cancel_notice_hours) {
    parts.push(t('cancel {0}h before', [form.cancel_notice_hours]))
  }
  if (form.allow_online_reschedule === false) parts.push(t('no online move'))
  return parts
}

/**
 * Problems that make an online configuration contradictory — shown before
 * Save so a service never goes live unbookable.
 */
export function onlineProblems(form, t = (s, a) => format(s, a)) {
  if (!form?.bookable_online) return []
  form = effectiveForm(form)
  const problems = []
  if (
    form.booking_opens_on &&
    form.booking_closes_on &&
    form.booking_closes_on < form.booking_opens_on
  ) {
    problems.push(t('The online window closes before it opens.'))
  }
  if (
    form.max_horizon_days &&
    form.min_notice_hours &&
    form.min_notice_hours >= form.max_horizon_days * 24
  ) {
    problems.push(t('The minimum notice is longer than the booking horizon.'))
  }
  if (
    form.max_participants > 1 &&
    form.online_max_participants > form.max_participants
  ) {
    problems.push(
      t('Seats per online booking exceed the seats of the service ({0}).', [
        form.max_participants,
      ]),
    )
  }
  if (!(form.staff || []).length) {
    problems.push(t('Add at least one professional, or nobody can be booked.'))
  }
  return problems
}

/** `format('a {0} b', [1])` → 'a 1 b' — the default translator for tests. */
export function format(text, args = []) {
  return String(text).replace(/\{(\d+)\}/g, (_, i) => args[i] ?? '')
}

/** Capabilities of a connector, as the chips of the platforms screen. */
export function capabilityChips(info = {}) {
  const caps = new Set(info.capabilities || [])
  const chips = []
  if (caps.has('pull') && !caps.has('feed')) chips.push('api')
  if (caps.has('webhook') && !caps.has('email')) chips.push('webhook')
  if (caps.has('feed')) chips.push('ical')
  if (caps.has('email')) chips.push('email')
  if (caps.has('cancel')) chips.push('cancel')
  if (caps.has('block') || caps.has('busy_feed')) chips.push('block')
  return chips
}

/** Fields a platform's form shows, required first. */
export function connectionFields(info = {}) {
  const required = info.required_fields || []
  const all = info.fields?.length ? info.fields : required
  return [...required, ...all.filter((f) => !required.includes(f))]
}

/** Platforms grouped by sector, in the registry's order. */
export function groupPlatforms(platforms = []) {
  const order = ['medical', 'beauty', 'wellness', 'general']
  const groups = {}
  for (const platform of platforms) {
    const sector = order.includes(platform.sector) ? platform.sector : 'general'
    ;(groups[sector] ||= []).push(platform)
  }
  return order
    .filter((s) => groups[s])
    .map((s) => ({ sector: s, platforms: groups[s] }))
}

/**
 * Short tag telling where an appointment came from, or '' when it was typed in
 * the CRM: 'Online' for the booking page, the platform's first word otherwise
 * ('Treatwell / Uala' → 'Treatwell', 'MioDottore (Docplanner)' → 'MioDottore').
 */
export function sourceTag(appointment = {}) {
  if (appointment.source === 'Online') return 'Online'
  if (appointment.source !== 'External') return ''
  const platform = (appointment.external_platform || '').trim()
  return platform.split(/\s[/(]/)[0].trim() || 'External'
}

/**
 * A link to the one booking page, narrowed as asked: a service, a professional
 * (their own page), a category, prefilled client details, campaign tags.
 * `staff` is the public id the booking page uses, never an e-mail address.
 */
export function buildBookingLink(origin, options = {}) {
  const base = `${(origin || '').replace(/\/$/, '')}/prenota`
  const params = new URLSearchParams()
  if (options.service) params.set('servizio', options.service)
  if (options.staff) params.set('professionista', options.staff)
  if (options.category && !options.service)
    params.set('categoria', options.category)
  for (const [key, value] of Object.entries(options.prefill || {})) {
    if (value) params.set(key, value)
  }
  for (const [key, value] of Object.entries(options.utm || {})) {
    if (value) params.set(`utm_${key}`, value)
  }
  if (options.embed) params.set('embed', '1')
  const query = params.toString()
  return query ? `${base}?${query}` : base
}

/** HTML to paste in a website: the booking page as an iframe, full width. */
export function embedSnippet(url, height = 820) {
  const src = url.includes('embed=1')
    ? url
    : `${url}${url.includes('?') ? '&' : '?'}embed=1`
  return `<iframe src="${src.replace(/"/g, '&quot;')}" style="width:100%;height:${height}px;border:0" loading="lazy" title="Prenota"></iframe>`
}

/** Label for where an online rule's value comes from. */
export function ruleSourceLabel(source, t = (s) => s) {
  return source === 'service' ? t('own') : t('default')
}

/**
 * The online rules a service inherits from the booking-page defaults. Same
 * keys as `crm.scheduling.booking_rules.INHERITED` on the server.
 */
export const INHERITED_RULES = Object.freeze([
  { key: 'online_confirmation', type: 'select', label: 'Confirmation' },
  { key: 'min_notice_hours', type: 'number', label: 'Minimum notice (hours)' },
  { key: 'max_horizon_days', type: 'number', label: 'Booking horizon (days)' },
  {
    key: 'online_slot_interval',
    type: 'number',
    label: 'Online start times every (min)',
  },
  { key: 'same_day_cutoff', type: 'time', label: 'Same-day bookings until' },
  { key: 'require_phone', type: 'check', label: 'Phone required' },
  {
    key: 'max_per_customer_per_day',
    type: 'number',
    label: 'Max per client per day',
  },
  {
    key: 'allow_online_cancel',
    type: 'check',
    label: 'Client can cancel online',
  },
  {
    key: 'cancel_notice_hours',
    type: 'number',
    label: 'Cancel up to (hours before)',
  },
  {
    key: 'allow_online_reschedule',
    type: 'check',
    label: 'Client can move online',
  },
  {
    key: 'reschedule_notice_hours',
    type: 'number',
    label: 'Move up to (hours before)',
  },
  { key: 'max_reschedules', type: 'number', label: 'Max moves (0 = any)' },
])

/** Is this rule customised on the service (true) or inherited (false)? */
export function isCustomised(form, key) {
  return (form?.online_overrides || []).includes(key)
}

/**
 * Customise a rule (starting from the default value, so nothing jumps) or give
 * it back to the default. Returns the new overrides list; mutates `form`.
 */
export function setCustomised(form, key, on) {
  const current = new Set(form.online_overrides || [])
  if (on) {
    if (!current.has(key)) {
      current.add(key)
      const fallback = form.online_defaults?.[key]
      if (fallback !== undefined && fallback !== null) {
        form[key] = normaliseRuleValue(key, fallback)
      }
    }
  } else {
    current.delete(key)
  }
  form.online_overrides = [...current].sort()
  return form.online_overrides
}

/** The value shown for an inherited rule: the default, in the form's shape. */
export function inheritedValue(form, key) {
  const value = form?.online_defaults?.[key]
  return value === undefined || value === null
    ? ''
    : normaliseRuleValue(key, value)
}

function normaliseRuleValue(key, value) {
  const rule = INHERITED_RULES.find((r) => r.key === key)
  if (!rule) return value
  if (rule.type === 'check') return Boolean(Number(value))
  if (rule.type === 'number') return Number(value) || 0
  if (rule.type === 'time') return String(value || '').slice(0, 5)
  return value
}

/**
 * The form with every inherited rule replaced by the default in force — what
 * the summaries and checks must judge, not the stale value stored on the service.
 */
export function effectiveForm(form) {
  if (!form?.online_defaults || !Object.keys(form.online_defaults).length)
    return form
  const out = { ...form }
  for (const rule of INHERITED_RULES) {
    if (!isCustomised(form, rule.key) && rule.key in form.online_defaults) {
      out[rule.key] = inheritedValue(form, rule.key)
    }
  }
  return out
}
