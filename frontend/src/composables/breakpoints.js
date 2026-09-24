import { computed, ref } from 'vue'

/**
 * One source of truth for "are we on a phone".
 *
 * Before this there were three answers and none of them agreed: `App.vue` picked
 * the layout shell at 640px, `isMobileView` switched components at 768px, and the
 * router picked the Mobile* detail pages at 768px. Between 640px and 767px that
 * meant the desktop shell wrapped a mobile page.
 *
 * They were also all `window.innerWidth` read once — a plain `computed` over it
 * has no reactive dependency, so it caches the first value for the life of the
 * tab. Rotating a phone or resizing a window never changed anything.
 *
 * 768px is Tailwind's `md`, which is what the `sm:` / `md:` classes throughout
 * the app are already written against.
 */
export const MOBILE_BREAKPOINT = 768

/**
 * A phone turned sideways is 844px wide and 390px tall: wide enough to be called
 * a desktop by width alone, and far too short to be one. The three-column
 * conversation screen would get 236px for the conversation itself.
 *
 * Height alone would be wrong — a short desktop window is still a desktop — so
 * it only counts on a touch screen. `(pointer: coarse)` is how a browser says
 * "this is a finger, not a mouse".
 */
export const SHORT_VIEWPORT = 500

export const viewportWidth = ref(read('innerWidth', MOBILE_BREAKPOINT))
export const viewportHeight = ref(read('innerHeight', SHORT_VIEWPORT * 2))

function read(prop, fallback) {
  return typeof window === 'undefined' ? fallback : window[prop]
}

const coarsePointer =
  typeof window !== 'undefined' && window.matchMedia
    ? window.matchMedia('(pointer: coarse)')
    : null

const isTouch = ref(coarsePointer?.matches ?? false)

function sync() {
  viewportWidth.value = read('innerWidth', MOBILE_BREAKPOINT)
  viewportHeight.value = read('innerHeight', SHORT_VIEWPORT * 2)
  if (coarsePointer) isTouch.value = coarsePointer.matches
}

if (typeof window !== 'undefined') {
  window.addEventListener('resize', sync, { passive: true })
  // iOS Safari reports the pre-rotation size during `orientationchange` and only
  // settles on the next `resize`. Listening to both covers the browsers that fire
  // one but not the other; a duplicate sync is a no-op because the refs are equal.
  window.addEventListener('orientationchange', sync, { passive: true })
  coarsePointer?.addEventListener?.('change', sync)
}

export const isMobileView = computed(
  () =>
    viewportWidth.value < MOBILE_BREAKPOINT ||
    (isTouch.value && viewportHeight.value < SHORT_VIEWPORT),
)
