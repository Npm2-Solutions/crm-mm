import { describe, expect, it } from 'vitest'
import {
  linkValido,
  mesiValidi,
  placeIdValido,
  problemiDelleRecensioni,
} from '@/utils/recensioni'

describe('the review settings, checked where they are typed', () => {
  it('months from 1 to 60, never 0 read as 12', () => {
    expect(mesiValidi(12)).toBe(true)
    expect(mesiValidi('1')).toBe(true)
    expect(mesiValidi(60)).toBe(true)
    for (const sbagliato of [0, -1, 61, 1.5, '', null, 'x']) {
      expect(mesiValidi(sbagliato)).toBe(false)
    }
  })

  it('a link the browser opens, a place id Google would know, or nothing', () => {
    expect(linkValido('')).toBe(true)
    expect(linkValido('https://g.page/r/abc/review')).toBe(true)
    expect(linkValido('g.page/r/abc')).toBe(false)
    expect(linkValido('http://g.page/r')).toBe(false)
    expect(placeIdValido('ChIJN1t_tDeuEmsRUsoyG83frY4')).toBe(true)
    expect(placeIdValido('a b')).toBe(false)
  })

  it('each problem under its own field', () => {
    expect(
      problemiDelleRecensioni({
        google_review_link: 'g.page',
        google_place_id: '',
        months_between: 0,
      }),
    ).toEqual({
      google_review_link: [
        'The review link is a web address starting with https://',
      ],
      months_between: ['From {0} to {1} months', [1, 60]],
    })
  })
})
