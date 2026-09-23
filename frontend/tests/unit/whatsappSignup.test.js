import { describe, expect, it } from 'vitest'
import { loginOptions, runsHere } from '@/utils/whatsappSignup'

describe('runsHere', () => {
  it('is true when the hub is the domain we are already on', () => {
    expect(runsHere('https://hub.example.com', 'https://hub.example.com')).toBe(
      true,
    )
  })

  it('ignores a trailing slash, which the two sides spell differently', () => {
    expect(
      runsHere('https://hub.example.com/', 'https://hub.example.com'),
    ).toBe(true)
  })

  it('is false for a client CRM on its own domain', () => {
    expect(
      runsHere('https://hub.example.com', 'https://cliente.frappe.cloud'),
    ).toBe(false)
  })

  it('is false when either side is missing', () => {
    expect(runsHere('', 'https://hub.example.com')).toBe(false)
    expect(runsHere('https://hub.example.com', '')).toBe(false)
    expect(runsHere(undefined, undefined)).toBe(false)
  })
})

describe('loginOptions', () => {
  it('asks for Coexistence, which lives in extras', () => {
    const options = loginOptions('123')
    expect(options.extras.featureType).toBe('whatsapp_business_app_onboarding')
    expect(options.extras.sessionInfoVersion).toBe('3')
  })

  it('asks again for what was already granted', () => {
    // without this Facebook skips every screen it has an answer for, and the
    // Coexistence branch is one of those screens
    expect(loginOptions('123').auth_type).toBe('reauthorize')
  })

  it('returns a code, not a token', () => {
    const options = loginOptions('123')
    expect(options.config_id).toBe('123')
    expect(options.response_type).toBe('code')
    expect(options.override_default_response_type).toBe(true)
  })
})
