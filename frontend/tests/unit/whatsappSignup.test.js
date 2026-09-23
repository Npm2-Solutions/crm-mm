import { describe, expect, it } from 'vitest'
import { initOptions, loginOptions, runsHere } from '@/utils/whatsappSignup'

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

  it('says where Facebook may redirect, so the SDK does not choose', () => {
    // the SDK's own source: `e.fallback_redirect_uri ||
    // (e.fallback_redirect_uri = document.location.href)` — left out, it sends
    // the page you are on, and Facebook blocks an address it has not been given
    expect(
      loginOptions('123', 'https://hub.example.com/whatsapp-connect')
        .fallback_redirect_uri,
    ).toBe('https://hub.example.com/whatsapp-connect')
  })

  it('returns a code, not a token', () => {
    const options = loginOptions('123')
    expect(options.config_id).toBe('123')
    expect(options.response_type).toBe('code')
    expect(options.override_default_response_type).toBe(true)
  })
})

describe('initOptions', () => {
  it('turns FedCM off', () => {
    // with it on, the SDK opens a window of its own before ours —
    // response_type=token&scope=openid&dialog_source=fedcm, redirecting to the
    // site root, which the app does not have registered — and Facebook refuses
    // it on sight. That was the «URL bloccato» window.
    expect(initOptions('123').fedCM).toBe(false)
  })

  it('still passes the app and a pinned version', () => {
    const options = initOptions('123')
    expect(options.appId).toBe('123')
    expect(options.version).toMatch(/^v\d+\.\d+$/)
  })
})
