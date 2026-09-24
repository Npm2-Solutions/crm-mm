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
  return out
}

/**
 * One-line summary of the limits a service applies online, for the service
 * list and the panel header. `t` is the translator (`__` in the app).
 */
export function describeOnlineLimits(form, t = (s, a) => format(s, a)) {
  if (!form?.bookable_online) return []
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
