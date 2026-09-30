import { describe, expect, it } from 'vitest'
import {
  aBase64url,
  daBase64url,
  inJSON,
  opzioniDiAccesso,
  opzioniDiCreazione,
} from '@/area/passkey'

const byte = (...n) => new Uint8Array(n).buffer

describe('base64url, both ways', () => {
  it('round-trips any bytes, without padding', () => {
    const dati = byte(0, 1, 2, 250, 251, 252, 253, 254, 255)
    const testo = aBase64url(dati)
    expect(testo).not.toMatch(/[+/=]/)
    expect([...new Uint8Array(daBase64url(testo))]).toEqual([
      0, 1, 2, 250, 251, 252, 253, 254, 255,
    ])
  })

  it('reads what Python wrote', () => {
    // base64.urlsafe_b64encode(b"\xfb\xff").rstrip(b"=") == b"-_8"
    expect([...new Uint8Array(daBase64url('-_8'))]).toEqual([251, 255])
  })
})

describe('the options, for the browser', () => {
  it('turns the ids and the challenge into bytes', () => {
    const creazione = opzioniDiCreazione({
      challenge: 'AQID',
      rp: { id: 'centro.it', name: 'Centro' },
      user: { id: 'BAU', name: 'anna@example.com', displayName: 'Anna' },
      excludeCredentials: [{ id: 'Bwg', type: 'public-key' }],
    })
    expect([...new Uint8Array(creazione.challenge)]).toEqual([1, 2, 3])
    expect([...new Uint8Array(creazione.user.id)]).toEqual([4, 5])
    expect(creazione.user.name).toBe('anna@example.com')
    expect([...new Uint8Array(creazione.excludeCredentials[0].id)]).toEqual([
      7, 8,
    ])
    const accesso = opzioniDiAccesso({ challenge: 'AQID', rpId: 'centro.it' })
    expect(accesso.allowCredentials).toEqual([])
    expect(accesso.rpId).toBe('centro.it')
  })
})

describe("the phone's answer, for the server", () => {
  it('writes an assertion in base64url', () => {
    const risposta = inJSON({
      id: 'Bwg',
      rawId: byte(7, 8),
      type: 'public-key',
      response: {
        clientDataJSON: byte(1),
        authenticatorData: byte(2),
        signature: byte(3),
        userHandle: byte(4),
      },
      getClientExtensionResults: () => ({}),
    })
    expect(risposta).toMatchObject({
      id: 'Bwg',
      rawId: 'Bwg',
      type: 'public-key',
      response: {
        clientDataJSON: 'AQ',
        authenticatorData: 'Ag',
        signature: 'Aw',
        userHandle: 'BA',
      },
    })
  })

  it('writes an attestation with its transports', () => {
    const risposta = inJSON({
      id: 'Bwg',
      rawId: byte(7, 8),
      type: 'public-key',
      response: {
        clientDataJSON: byte(1),
        attestationObject: byte(5),
        getTransports: () => ['internal'],
      },
    })
    expect(risposta.response).toEqual({
      clientDataJSON: 'AQ',
      attestationObject: 'BQ',
      transports: ['internal'],
    })
    expect(risposta.clientExtensionResults).toEqual({})
  })
})
