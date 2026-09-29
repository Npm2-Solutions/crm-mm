import { describe, expect, it } from 'vitest'
import { atTheEnd } from '@/composables/conversationScroll'

describe('atTheEnd', () => {
  it('is at the end when the last pixel is in sight', () => {
    // 1000 tall, 400 shown, scrolled 600 down: nothing left below
    expect(atTheEnd(600, 1000, 400)).toBe(true)
  })

  it('still is a little short of it: a finger is not a pixel', () => {
    expect(atTheEnd(530, 1000, 400)).toBe(true)
  })

  it('is not, scrolled back to read', () => {
    expect(atTheEnd(300, 1000, 400)).toBe(false)
    expect(atTheEnd(520, 1000, 400)).toBe(false)
  })

  it('is, for a conversation shorter than its window', () => {
    expect(atTheEnd(0, 300, 400)).toBe(true)
  })

  it('takes how near counts as there', () => {
    expect(atTheEnd(590, 1000, 400, 5)).toBe(false)
    expect(atTheEnd(596, 1000, 400, 5)).toBe(true)
  })
})
