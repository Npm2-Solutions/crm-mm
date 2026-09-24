import { describe, it, expect } from 'vitest'
import { tokenExpiry, EXPIRY_WARNING_DAYS } from '@/utils/metaConnection'

const NOW = new Date('2026-09-24T10:00:00')

describe('tokenExpiry', () => {
  it('has nothing to say without a date', () => {
    expect(tokenExpiry('', NOW)).toBeNull()
    expect(tokenExpiry(null, NOW)).toBeNull()
    expect(tokenExpiry('not a date', NOW)).toBeNull()
  })

  it('reads the date the way the server writes it, microseconds included', () => {
    const expiry = tokenExpiry('2026-11-20 10:00:00.123456', NOW)
    expect(expiry.date.getFullYear()).toBe(2026)
    expect(expiry.date.getMonth()).toBe(10)
    expect(expiry.date.getDate()).toBe(20)
  })

  it('is quiet while the token has weeks left', () => {
    const expiry = tokenExpiry('2026-11-20 10:00:00', NOW)
    expect(expiry.expired).toBe(false)
    expect(expiry.soon).toBe(false)
    expect(expiry.days).toBe(57)
  })

  it('warns in the last days', () => {
    const expiry = tokenExpiry('2026-09-30 09:00:00', NOW)
    expect(expiry.days).toBeLessThan(EXPIRY_WARNING_DAYS)
    expect(expiry.soon).toBe(true)
    expect(expiry.expired).toBe(false)
  })

  it('says so once it has run out', () => {
    const expiry = tokenExpiry('2026-09-20 10:00:00', NOW)
    expect(expiry.expired).toBe(true)
    expect(expiry.soon).toBe(false)
  })
})
