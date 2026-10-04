// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// The Lucide icons drawn by name: only the ones drawn go into the page, all of
// them for the picker (src/utils/icone.js)
import fs from 'node:fs'
import path from 'node:path'
import {
  simbolo,
  simboli,
  mettiIcona,
  mettiTutteLeIcone,
  inPagina,
} from '@/utils/icone'

const SPRITE = fs.readFileSync(
  path.resolve(
    import.meta.dirname,
    '../../node_modules/lucide-static/sprite.svg',
  ),
  'utf8',
)

const PICCOLO = `<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg"><defs>
<symbol id="phone-call" viewBox="0 0 24 24"><path d="a" /></symbol>
<symbol id="phone" viewBox="0 0 24 24"><path d="b" /></symbol>
</defs></svg>`

describe('one icon out of the sprite', () => {
  it('takes the symbol with that very name', () => {
    expect(simbolo(PICCOLO, 'phone')).toBe(
      '<symbol id="phone" viewBox="0 0 24 24"><path d="b" /></symbol>',
    )
    // not the first that starts with it
    expect(simbolo(PICCOLO, 'phone-call')).toContain('d="a"')
  })

  it('gives nothing for a name it has not, or without a sprite', () => {
    expect(simbolo(PICCOLO, 'phon')).toBe('')
    expect(simbolo(PICCOLO, '')).toBe('')
    expect(simbolo('', 'phone')).toBe('')
    expect(simbolo(PICCOLO, 'x" onload="')).toBe('')
  })

  it('finds the icons the everyday screens draw in lucide-static', () => {
    for (const nome of [
      'settings',
      'info',
      'log-out',
      'layout-dashboard',
      'phone',
    ]) {
      const pezzo = simbolo(SPRITE, nome)
      expect(pezzo.startsWith(`<symbol id="${nome}"`)).toBe(true)
      expect(pezzo.endsWith('</symbol>')).toBe(true)
    }
  })
})

describe('every icon, for the picker', () => {
  it('keeps all the symbols and nothing around them', () => {
    const tutti = simboli(SPRITE)
    expect(tutti.startsWith('<symbol')).toBe(true)
    expect(tutti.endsWith('</symbol>')).toBe(true)
    expect(tutti.match(/<symbol /g).length).toBe(
      SPRITE.match(/<symbol /g).length,
    )
    expect(simboli('')).toBe('')
  })
})

describe('the sprite in the page', () => {
  it('holds only the icons drawn, then all of them for the picker', async () => {
    await mettiIcona('settings')
    await mettiIcona('settings')
    await mettiIcona('a-name-lucide-has-not')
    const sprite = document.getElementById('lucide-sprite')
    expect(sprite.style.display).toBe('none')
    const svg = sprite.firstElementChild
    expect(svg.namespaceURI).toBe('http://www.w3.org/2000/svg')
    expect([...svg.querySelectorAll('symbol')].map((s) => s.id)).toEqual([
      'settings',
    ])
    expect(inPagina('settings')).toBe(true)
    expect(inPagina('phone')).toBe(false)

    await mettiTutteLeIcone()
    expect(svg.querySelectorAll('symbol').length).toBe(
      SPRITE.match(/<symbol /g).length,
    )
    expect(svg.querySelectorAll('#settings').length).toBe(1)
    expect(inPagina('phone')).toBe(true)
  })
})
