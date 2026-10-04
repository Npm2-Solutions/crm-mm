// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// The client area wears the phone's theme, and follows it when it changes.
import { seguiIlTemaDelTelefono, temaDi } from '@/utils/temaDelTelefono'

function telefono(scuro) {
  const ascolti = []
  const query = {
    matches: scuro,
    addEventListener: (evento, fai) => evento === 'change' && ascolti.push(fai),
  }
  const radice = {
    attributi: {},
    setAttribute(k, v) {
      this.attributi[k] = v
    },
  }
  return {
    win: { matchMedia: () => query },
    doc: { documentElement: radice },
    cambia(nuovo) {
      query.matches = nuovo
      ascolti.forEach((fai) => fai())
    },
    tema: () => radice.attributi['data-theme'],
  }
}

describe('the client area and the phone theme', () => {
  it('names the theme', () => {
    expect(temaDi(true)).toBe('dark')
    expect(temaDi(false)).toBe('light')
    expect(temaDi(undefined)).toBe('light')
  })

  it('wears the theme the phone is set to', () => {
    const scuro = telefono(true)
    seguiIlTemaDelTelefono(scuro.doc, scuro.win)
    expect(scuro.tema()).toBe('dark')
    const chiaro = telefono(false)
    seguiIlTemaDelTelefono(chiaro.doc, chiaro.win)
    expect(chiaro.tema()).toBe('light')
  })

  it('follows the phone when it changes over', () => {
    const t = telefono(false)
    seguiIlTemaDelTelefono(t.doc, t.win)
    t.cambia(true)
    expect(t.tema()).toBe('dark')
    t.cambia(false)
    expect(t.tema()).toBe('light')
  })

  it('stays light where the browser cannot tell', () => {
    const radice = {
      attributi: {},
      setAttribute(k, v) {
        this.attributi[k] = v
      },
    }
    seguiIlTemaDelTelefono({ documentElement: radice }, {})
    expect(radice.attributi['data-theme']).toBe('light')
  })
})
