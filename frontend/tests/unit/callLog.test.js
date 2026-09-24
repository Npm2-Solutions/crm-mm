// callLog.js pulls in unrelated heavy dependencies (icon-resolving imports,
// a live createResource network call) that aren't wired up for vitest —
// stub them so this test exercises only the pure logic below.
vi.mock('@/utils', () => ({ formatDate: vi.fn() }))
vi.mock('@/stores/meta', () => ({
  getMeta: () => ({
    getFormattedPercent: vi.fn(),
    getFormattedFloat: vi.fn(),
    getFormattedCurrency: vi.fn(),
  }),
}))
vi.mock('@/composables/useTimelinePreferences', () => ({
  timestampCell: vi.fn(),
}))

import { callParties, numberOf } from '@/utils/callLog'

describe('callParties', () => {
  const both = {
    theirNumber: '+393331112233',
    myNumber: '+390451234567',
    me: 'io@crm.it',
  }

  it('puts them on the calling end of an incoming call', () => {
    const parties = callParties({ direction: 'Incoming', ...both })
    expect(parties.from).toBe('+393331112233')
    expect(parties.to).toBe('+390451234567')
  })

  it('turns it round for an outgoing one', () => {
    const parties = callParties({ direction: 'Outgoing', ...both })
    expect(parties.from).toBe('+390451234567')
    expect(parties.to).toBe('+393331112233')
  })

  it('credits the one role the call actually had', () => {
    // somebody who answered is not also the one who dialled
    expect(callParties({ direction: 'Incoming', ...both }).receiver).toBe(
      'io@crm.it',
    )
    expect(callParties({ direction: 'Incoming', ...both }).caller).toBe('')
    expect(callParties({ direction: 'Outgoing', ...both }).caller).toBe(
      'io@crm.it',
    )
    expect(callParties({ direction: 'Outgoing', ...both }).receiver).toBe('')
  })

  it('leaves an end empty rather than guessing', () => {
    const parties = callParties({
      direction: 'Outgoing',
      theirNumber: '',
      myNumber: '',
      me: '',
    })
    expect(parties.from).toBe('')
    expect(parties.to).toBe('')
  })
})

describe('numberOf', () => {
  it('finds the number wherever the record keeps it', () => {
    expect(numberOf({ mobile_no: '+39333' })).toBe('+39333')
    expect(numberOf({ actual_mobile_no: '+39444' })).toBe('+39444')
    expect(numberOf({ phone: '+39555' })).toBe('+39555')
  })

  it('prefers the mobile, which is the one people answer', () => {
    expect(numberOf({ mobile_no: '+39333', phone: '+39555' })).toBe('+39333')
  })

  it('says nothing when the record has no number', () => {
    expect(numberOf({})).toBe('')
    expect(numberOf(null)).toBe('')
  })
})
