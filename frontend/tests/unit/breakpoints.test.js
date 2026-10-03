import { describe, it, expect, beforeEach } from 'vitest'
import {
  MOBILE_BREAKPOINT,
  PHONE_LANDSCAPE_HEIGHT,
  isMobileView,
  isPhoneSize,
  viewportWidth,
} from '@/composables/breakpoints'

function setWidth(width, event = 'resize') {
  window.innerWidth = width
  window.dispatchEvent(new Event(event))
}

describe('breakpoints', () => {
  beforeEach(() => setWidth(1440))

  it('treats anything narrower than the breakpoint as mobile', () => {
    setWidth(MOBILE_BREAKPOINT - 1)
    expect(isMobileView.value).toBe(true)
  })

  it('treats the breakpoint itself as desktop', () => {
    setWidth(MOBILE_BREAKPOINT)
    expect(isMobileView.value).toBe(false)
  })

  // The bug this replaces: `computed(() => window.innerWidth < 768)` reads a
  // non-reactive global, so it cached the width the tab was opened at forever.
  it('follows the viewport instead of caching the first read', () => {
    expect(isMobileView.value).toBe(false)
    setWidth(390)
    expect(isMobileView.value).toBe(true)
    setWidth(1024)
    expect(isMobileView.value).toBe(false)
  })

  it('also updates on orientationchange, which iOS fires without a resize', () => {
    setWidth(390, 'orientationchange')
    expect(viewportWidth.value).toBe(390)
    expect(isMobileView.value).toBe(true)
  })

  // 640 was the layout shell's old cutoff while the router used 768, so a 700px
  // viewport rendered the desktop shell around a Mobile* page.
  it('puts the old 640-767 dead zone on the mobile side', () => {
    setWidth(700)
    expect(isMobileView.value).toBe(true)
  })

  // a phone held sideways: 844 wide, 390 tall, touched; it got the desktop
  it('keeps a phone held sideways on the phone, not a short desktop window', () => {
    expect(isPhoneSize({ width: 844, height: 390, coarse: true })).toBe(true)
    expect(isPhoneSize({ width: 844, height: 390, coarse: false })).toBe(false)
    // a tablet held sideways is tall enough for the desktop
    expect(isPhoneSize({ width: 1180, height: 820, coarse: true })).toBe(false)
    expect(
      isPhoneSize({
        width: 900,
        height: PHONE_LANDSCAPE_HEIGHT,
        coarse: true,
      }),
    ).toBe(false)
    expect(isPhoneSize({ width: 390, height: 844, coarse: false })).toBe(true)
  })
})
