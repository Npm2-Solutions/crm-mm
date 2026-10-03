// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// DottorCloud on the phone's home screen: what the More page offers.
import { comeInstallare, questoDispositivo } from '@/utils/installa'

describe('comeInstallare', () => {
  it('asks the browser when it offers to install', () => {
    expect(comeInstallare({ offerta: true, android: true })).toBe('pulsante')
  })

  it('tells an iPhone the taps in Safari, and Android its menu', () => {
    expect(comeInstallare({ ios: true })).toBe('ios')
    expect(comeInstallare({ android: true })).toBe('android')
  })

  it('says nothing once installed, after «Not now», or on a computer', () => {
    expect(comeInstallare({ installata: true, offerta: true })).toBe('nulla')
    expect(comeInstallare({ scartata: true, ios: true })).toBe('nulla')
    expect(comeInstallare({})).toBe('nulla')
  })
})

describe('questoDispositivo', () => {
  function finestra({
    agente = '',
    standalone,
    piattaforma,
    tocchi = 0,
    schermo = false,
  }) {
    return {
      navigator: {
        userAgent: agente,
        standalone,
        platform: piattaforma,
        maxTouchPoints: tocchi,
      },
      matchMedia: () => ({ matches: schermo }),
    }
  }

  it('knows an iPhone, an iPad that says it is a Mac, and Android', () => {
    expect(
      questoDispositivo(
        finestra({ agente: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5)' }),
      ).ios,
    ).toBe(true)
    expect(
      questoDispositivo(finestra({ piattaforma: 'MacIntel', tocchi: 5 })).ios,
    ).toBe(true)
    expect(
      questoDispositivo(finestra({ agente: 'Mozilla/5.0 (Linux; Android 14)' }))
        .android,
    ).toBe(true)
  })

  it('knows it is installed, on an iPhone or anywhere else', () => {
    expect(questoDispositivo(finestra({ standalone: true })).installata).toBe(
      true,
    )
    expect(questoDispositivo(finestra({ schermo: true })).installata).toBe(true)
    expect(questoDispositivo(finestra({})).installata).toBe(false)
  })
})
