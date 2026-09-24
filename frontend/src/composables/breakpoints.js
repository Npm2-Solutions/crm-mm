import { computed, ref } from 'vue'

/**
 * One source of truth for "are we on a phone-sized viewport".
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

export const viewportWidth = ref(getWidth())

function getWidth() {
  return typeof window === 'undefined' ? MOBILE_BREAKPOINT : window.innerWidth
}

function sync() {
  viewportWidth.value = getWidth()
}

if (typeof window !== 'undefined') {
  window.addEventListener('resize', sync, { passive: true })
  // iOS Safari reports the pre-rotation width during `orientationchange` and only
  // settles on the next `resize`. Listening to both covers the browsers that fire
  // one but not the other; a duplicate sync is a no-op because the ref is equal.
  window.addEventListener('orientationchange', sync, { passive: true })
}

export const isMobileView = computed(
  () => viewportWidth.value < MOBILE_BREAKPOINT,
)
