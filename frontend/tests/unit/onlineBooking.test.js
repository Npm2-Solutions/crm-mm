import {
  bookingLink,
  capabilityChips,
  connectionFields,
  describeOnlineLimits,
  groupPlatforms,
  onlineFieldsFrom,
  onlineProblems,
  ONLINE_DEFAULTS,
  sourceTag,
} from '@/utils/onlineBooking'

describe('bookingLink', () => {
  it('prefers the website slug and encodes it', () => {
    expect(
      bookingLink('https://studio.it/', {
        website_slug: 'pulizia viso',
        name: 'X',
      }),
    ).toBe('https://studio.it/prenota?servizio=pulizia%20viso')
  })

  it('falls back to the service name, then to the bare page', () => {
    expect(bookingLink('https://s.it', { name: 'Fisioterapia' })).toBe(
      'https://s.it/prenota?servizio=Fisioterapia',
    )
    expect(bookingLink('https://s.it', null)).toBe('https://s.it/prenota')
  })
})

describe('onlineFieldsFrom', () => {
  it('keeps defaults for checks the server did not send', () => {
    const out = onlineFieldsFrom({})
    expect(out).toEqual({ ...ONLINE_DEFAULTS })
  })

  it('turns 0/1 into booleans and trims seconds off the cutoff', () => {
    const out = onlineFieldsFrom({
      allow_online_cancel: 0,
      require_notes: 1,
      same_day_cutoff: '12:30:00',
      max_bookings_per_day: '4',
    })
    expect(out.allow_online_cancel).toBe(false)
    expect(out.require_notes).toBe(true)
    expect(out.same_day_cutoff).toBe('12:30')
    expect(out.max_bookings_per_day).toBe(4)
  })
})

describe('describeOnlineLimits', () => {
  it('is empty for a service not bookable online', () => {
    expect(describeOnlineLimits({ max_bookings_per_day: 3 })).toEqual([])
  })

  it('lists what is set, in plain words', () => {
    const parts = describeOnlineLimits({
      bookable_online: true,
      online_confirmation: 'Manual approval',
      min_notice_hours: 24,
      max_bookings_per_day: 3,
      customer_eligibility: 'New customers only',
      allow_online_cancel: false,
    })
    expect(parts).toEqual([
      'approval',
      '24h notice',
      'max 3/day',
      'new clients',
      'no online cancel',
    ])
  })
})

describe('onlineProblems', () => {
  const base = { bookable_online: true, staff: [{ user: 'a' }] }

  it('flags a window that closes before it opens', () => {
    expect(
      onlineProblems({
        ...base,
        booking_opens_on: '2026-10-10',
        booking_closes_on: '2026-10-01',
      }),
    ).toHaveLength(1)
  })

  it('flags notice longer than the horizon and too many seats', () => {
    const problems = onlineProblems({
      ...base,
      min_notice_hours: 72,
      max_horizon_days: 2,
      max_participants: 4,
      online_max_participants: 6,
    })
    expect(problems).toHaveLength(2)
  })

  it('flags a service nobody can deliver', () => {
    expect(onlineProblems({ bookable_online: true, staff: [] })).toHaveLength(1)
  })

  it('is quiet for a sound configuration or an offline service', () => {
    expect(
      onlineProblems({ ...base, min_notice_hours: 2, max_horizon_days: 30 }),
    ).toEqual([])
    expect(onlineProblems({ staff: [] })).toEqual([])
  })
})

describe('platform helpers', () => {
  it('derives chips from capabilities', () => {
    expect(
      capabilityChips({ capabilities: ['pull', 'webhook', 'cancel', 'block'] }),
    ).toEqual(['api', 'webhook', 'cancel', 'block'])
    expect(
      capabilityChips({ capabilities: ['email', 'webhook', 'pull', 'feed'] }),
    ).toEqual(['ical', 'email'])
  })

  it('orders fields required first without duplicates', () => {
    expect(
      connectionFields({
        required_fields: ['api_key'],
        fields: ['api_base_url', 'api_key', 'webhook_secret'],
      }),
    ).toEqual(['api_key', 'api_base_url', 'webhook_secret'])
    expect(connectionFields({ required_fields: ['ical_url'] })).toEqual([
      'ical_url',
    ])
  })

  it('groups by sector in a fixed order', () => {
    const groups = groupPlatforms([
      { label: 'Cal.com', sector: 'general' },
      { label: 'MioDottore', sector: 'medical' },
      { label: 'Fresha', sector: 'beauty' },
      { label: 'Odd', sector: 'space' },
    ])
    expect(groups.map((g) => g.sector)).toEqual([
      'medical',
      'beauty',
      'general',
    ])
    expect(groups[2].platforms.map((p) => p.label)).toEqual(['Cal.com', 'Odd'])
  })
})

describe('sourceTag', () => {
  it('names the origin briefly', () => {
    expect(sourceTag({ source: 'Internal' })).toBe('')
    expect(sourceTag({})).toBe('')
    expect(sourceTag({ source: 'Online' })).toBe('Online')
    expect(
      sourceTag({ source: 'External', external_platform: 'Treatwell / Uala' }),
    ).toBe('Treatwell')
    expect(
      sourceTag({
        source: 'External',
        external_platform: 'MioDottore (Docplanner)',
      }),
    ).toBe('MioDottore')
    expect(
      sourceTag({ source: 'External', external_platform: 'Cal.com' }),
    ).toBe('Cal.com')
    expect(sourceTag({ source: 'External' })).toBe('External')
  })
})
