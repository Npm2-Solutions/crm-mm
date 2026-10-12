// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

import { describe, expect, it } from 'vitest'
import {
  PAESI_PROPOSTI,
  TASTI,
  bloccataInItalia,
  cercaChiChiama,
  comeSalvati,
  conIlPaese,
  finestraOccupata,
  nomeDelPaese,
  nomeDiChiChiama,
  numeroIniziale,
  paesi,
  paesiDaAggiungere,
  senzaIlPaese,
  siSceglie,
} from '@/utils/chiamate'

// Calls going out (doc 52): the page reads the countries as the server does
// (crm/telephony/uscita_regole.py) and starts each call from the right number.

const NUMERI = [
  { number: '+390212345678', own: true },
  { number: '+390687654321', own: false },
]

describe('the countries that can be called', () => {
  it('as stored, as the server reads them', () => {
    expect(paesi('it, ch')).toEqual(['CH', 'IT'])
    expect(paesi('["IT", "FR"]')).toEqual(['FR', 'IT'])
    expect(paesi('IT\nSM;VA')).toEqual(['IT', 'SM', 'VA'])
    expect(paesi('Italia, 39')).toEqual(['IT'])
  })

  it('Italy when nothing is left', () => {
    expect(paesi('')).toEqual(['IT'])
    expect(paesi(null)).toEqual(['IT'])
    expect(paesi([])).toEqual(['IT'])
  })

  it('kept as the settings keep them', () => {
    expect(comeSalvati(['ch', 'IT', 'IT'])).toBe('CH, IT')
  })

  it('by their name in the reader’s language', () => {
    expect(nomeDelPaese('CH', 'it')).toBe('Svizzera')
    expect(nomeDelPaese('GB', 'en')).toBe('United Kingdom')
  })

  it('Italy among those offered to add', () => {
    expect(PAESI_PROPOSTI).toContain('IT')
    expect(new Set(PAESI_PROPOSTI).size).toBe(PAESI_PROPOSTI.length)
  })

  it('one added, one taken away, never none', () => {
    expect(conIlPaese('IT', 'ch')).toEqual(['CH', 'IT'])
    expect(conIlPaese('IT, CH', 'CH')).toEqual(['CH', 'IT'])
    expect(senzaIlPaese('IT, CH', 'IT')).toEqual(['CH'])
    expect(senzaIlPaese('IT', 'IT')).toEqual(['IT'])
  })

  it('the ones to add, without those chosen, by name', () => {
    const opzioni = paesiDaAggiungere('IT, CH', 'it')
    const codici = opzioni.map((o) => o.value)
    expect(codici).not.toContain('IT')
    expect(codici).not.toContain('CH')
    expect(opzioni.find((o) => o.value === 'DE').label).toBe('Germania')
    const nomi = opzioni.map((o) => o.label)
    expect(nomi).toEqual([...nomi].sort((a, b) => a.localeCompare(b, 'it')))
  })
})

describe('the number a call shows', () => {
  it('the one used last, while it is still the centre’s', () => {
    expect(numeroIniziale(NUMERI, '+390687654321')).toBe('+390687654321')
  })

  it('else one’s own line, else the first', () => {
    expect(numeroIniziale(NUMERI, '+390299999999')).toBe('+390212345678')
    expect(numeroIniziale([{ number: '+390687654321' }])).toBe('+390687654321')
    expect(numeroIniziale([])).toBe('')
  })

  it('is asked only when there is a choice', () => {
    expect(siSceglie(NUMERI)).toBe(true)
    expect(siSceglie(NUMERI.slice(0, 1))).toBe(false)
  })

  it('an Italian mobile shown on a call to Italy is blocked', () => {
    const numeri = [...NUMERI, { number: '+393331234567', mobile: true }]
    expect(bloccataInItalia(numeri, '+393331234567', 'IT')).toBe(true)
    expect(bloccataInItalia(numeri, '+393331234567', 'CH')).toBe(false)
    expect(bloccataInItalia(numeri, '+390212345678', 'IT')).toBe(false)
    expect(bloccataInItalia(numeri, '', 'IT')).toBe(false)
  })
})

describe('who calls', () => {
  const ANNA = { full_name: 'Anna Bianchi', mobile_no: '+393331234567' }
  const MARCO = { full_name: 'Marco Neri', mobile_no: '+393407654321' }
  // what the server answers for a number nobody has
  const NESSUNO = { mobile_no: '+390212345678' }

  // the server, answering when the test says so
  function server() {
    const attese = {}
    const chiesti = []
    const chiedi = (numero) => {
      chiesti.push(numero)
      return new Promise((risolvi, rifiuta) => {
        attese[numero] = { risolvi, rifiuta }
      })
    }
    return { chiedi, chiesti, attese }
  }

  // what the window was told, in order
  function finestra() {
    const detto = []
    const aggiorna = (contatto, cercando) => detto.push([contatto, cercando])
    return { detto, aggiorna, ultimo: () => detto.at(-1) }
  }

  it('says nobody at once, then whom the server found', async () => {
    const { chiedi, chiesti, attese } = server()
    const { detto, aggiorna } = finestra()
    const cerca = cercaChiChiama(chiedi, aggiorna)
    const fatto = cerca('+393331234567')
    expect(detto).toEqual([[null, true]])
    expect(chiesti).toEqual(['+393331234567'])
    attese['+393331234567'].risolvi(ANNA)
    await fatto
    expect(detto).toEqual([
      [null, true],
      [ANNA, false],
    ])
  })

  it('never shows the last call’s caller on the next one', async () => {
    const { chiedi, attese } = server()
    const { aggiorna, ultimo } = finestra()
    const cerca = cercaChiChiama(chiedi, aggiorna)
    const prima = cerca('+393331234567')
    attese['+393331234567'].risolvi(ANNA)
    await prima
    expect(ultimo()).toEqual([ANNA, false])
    // the next call, the server not answered yet: nobody, never Anna
    cerca('+393407654321')
    expect(ultimo()).toEqual([null, true])
  })

  it('asks again for the same number at the next call', async () => {
    const { chiedi, chiesti, attese } = server()
    const { aggiorna, ultimo } = finestra()
    const cerca = cercaChiChiama(chiedi, aggiorna)
    const prima = cerca('+393331234567')
    attese['+393331234567'].risolvi(ANNA)
    await prima
    const seconda = cerca('+393331234567')
    expect(ultimo()).toEqual([null, true])
    attese['+393331234567'].risolvi(ANNA)
    await seconda
    expect(chiesti).toEqual(['+393331234567', '+393331234567'])
    expect(ultimo()).toEqual([ANNA, false])
  })

  it('drops an answer about a number the call no longer has', async () => {
    const { chiedi, attese } = server()
    const { detto, aggiorna, ultimo } = finestra()
    const cerca = cercaChiChiama(chiedi, aggiorna)
    // Telnyx: the centre's own number shown first, then the caller's
    const prima = cerca('+390212345678')
    const seconda = cerca('+393407654321')
    attese['+393407654321'].risolvi(MARCO)
    await seconda
    // nobody has the centre's number: said late, it would be «Unknown»
    attese['+390212345678'].risolvi(NESSUNO)
    await prima
    expect(ultimo()).toEqual([MARCO, false])
    expect(detto.some(([contatto]) => contatto === NESSUNO)).toBe(false)
  })

  it('drops it when it comes first, too', async () => {
    const { chiedi, attese } = server()
    const { aggiorna, ultimo } = finestra()
    const cerca = cercaChiChiama(chiedi, aggiorna)
    const prima = cerca('+390212345678')
    const seconda = cerca('+393407654321')
    attese['+390212345678'].risolvi(NESSUNO)
    await prima
    // still asking about the caller
    expect(ultimo()).toEqual([null, true])
    attese['+393407654321'].risolvi(MARCO)
    await seconda
    expect(ultimo()).toEqual([MARCO, false])
  })

  it('leaves nobody where the server could not answer', async () => {
    const { chiedi, attese } = server()
    const { aggiorna, ultimo } = finestra()
    const cerca = cercaChiChiama(chiedi, aggiorna)
    const prima = cerca('+393331234567')
    attese['+393331234567'].risolvi(ANNA)
    await prima
    const seconda = cerca('+393407654321')
    attese['+393407654321'].rifiuta(new Error('502'))
    await seconda
    // the call goes on with nobody named, never with Anna
    expect(ultimo()).toEqual([null, false])
  })

  it('asks nothing without a number', async () => {
    const { chiedi, chiesti } = server()
    const { detto, aggiorna } = finestra()
    await cercaChiChiama(chiedi, aggiorna)('')
    expect(chiesti).toEqual([])
    expect(detto).toEqual([[null, false]])
  })

  it('is named by the server’s name, nothing while asked, else «Unknown»', () => {
    const t = (parola) => `«${parola}»`
    expect(nomeDiChiChiama(ANNA, false, t)).toBe('Anna Bianchi')
    expect(nomeDiChiChiama(null, true, t)).toBe('')
    expect(nomeDiChiChiama(null, false, t)).toBe('«Unknown»')
    expect(nomeDiChiChiama(NESSUNO, false, t)).toBe('«Unknown»')
    expect(nomeDiChiChiama({ full_name: '' }, false, t)).toBe('«Unknown»')
  })
})

describe('one call at a time', () => {
  const SQUILLA = { id: 'in arrivo' }
  const ALTRA = { id: "un'altra" }

  it('the window is free with no call and none being placed', () => {
    expect(finestraOccupata(null, '')).toBe(false)
    expect(finestraOccupata(null, '', ALTRA)).toBe(false)
  })

  it('is taken by a call it shows, ringing or on', () => {
    expect(finestraOccupata(SQUILLA, '')).toBe(true)
    expect(finestraOccupata(SQUILLA, 'ringing', ALTRA)).toBe(true)
  })

  it('is taken by a call being placed, before the carrier has one', () => {
    // a call coming in then rings on the centre's other phones
    expect(finestraOccupata(null, 'initiating', ALTRA)).toBe(true)
    expect(finestraOccupata(null, 'initiating')).toBe(true)
  })

  it('a call is never in its own way', () => {
    // Telnyx tells of the ringing call again: still the one shown
    expect(finestraOccupata(SQUILLA, '', SQUILLA)).toBe(false)
    expect(finestraOccupata(SQUILLA, 'initiating', SQUILLA)).toBe(false)
  })
})

describe('the keypad', () => {
  it('twelve keys, as on a phone', () => {
    expect(TASTI.flat()).toEqual([
      '1',
      '2',
      '3',
      '4',
      '5',
      '6',
      '7',
      '8',
      '9',
      '*',
      '0',
      '#',
    ])
  })
})
