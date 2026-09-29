import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

// How close to the end still counts as being at it.
const NEAR = 80

/**
 * Whether somebody reading at `scrollTop` is at the end of the conversation.
 * Pure, so the rule is the same in a test as on screen.
 */
export function atTheEnd(scrollTop, scrollHeight, clientHeight, near = NEAR) {
  return scrollHeight - scrollTop - clientHeight < near
}

/**
 * Where a conversation sits in its scroller.
 *
 * It opens where you read it: at its end, or on the line where its new
 * messages begin — straight there, before it is shown. It used to be drawn
 * from the top and scrolled down half a second later, smoothly, so every chat
 * began with its whole history sliding past.
 *
 * After that it follows the conversation only while you are at its end: a
 * message arriving, a picture that finishes loading, the composer growing as
 * you type — the last message stays in sight. Somebody who has scrolled back
 * to read is left where they are, except when they send something: then they
 * are taken to it, as in every messenger.
 *
 * Its parts arrive one after the other — the history, then WhatsApp, then
 * SMS — so it is shown only once all of them have (`arrived`), already placed:
 * shown as soon as the first part came in, it jumped when the rest did.
 *
 * @param {import('vue').Ref<HTMLElement|null>} scroller
 * @param {{ newestFirst: import('vue').Ref<boolean>,
 *           readsFromTheEnd: import('vue').Ref<boolean>,
 *           arrived?: import('vue').Ref<boolean> }} options
 */
export function useConversationScroll(
  scroller,
  { newestFirst, readsFromTheEnd, arrived },
) {
  // placed at least once: until then the conversation is not shown
  const settled = ref(false)
  // they have scrolled, clicked or keyed in it since it opened
  let moved = false
  // at the end, and to be kept there as the conversation grows
  let pinned = true

  function isAtEnd(el) {
    return atTheEnd(el.scrollTop, el.scrollHeight, el.clientHeight)
  }

  function toEnd(el, smooth = false) {
    el.scrollTo({
      top: newestFirst.value ? 0 : el.scrollHeight,
      behavior: smooth ? 'smooth' : 'instant',
    })
  }

  // Opening: the line where the new messages begin, when there is one and the
  // thread reads down; otherwise the end.
  function land(el) {
    const line = !newestFirst.value && el.querySelector('[data-new-line]')
    if (line) {
      const top =
        line.getBoundingClientRect().top -
        el.getBoundingClientRect().top +
        el.scrollTop
      el.scrollTo({ top: Math.max(0, top - 12), behavior: 'instant' })
      pinned = isAtEnd(el)
    } else {
      toEnd(el)
      pinned = true
    }
  }

  /**
   * Something in the conversation changed. Until they have moved, it lands
   * again — its parts arrive one after the other, WhatsApp after the rest;
   * then it follows only while they are at the end, or when it is `mine`.
   */
  function follow({ mine = false } = {}) {
    nextTick(() =>
      requestAnimationFrame(() => {
        const el = scroller.value
        if (!el) return
        if (!readsFromTheEnd.value) {
          settled.value = true
          return
        }
        if (!moved || !settled.value) land(el)
        else if (mine || pinned) toEnd(el, true)
        if (arrived?.value ?? true) settled.value = true
      }),
    )
  }

  // Another tab, another channel: a different list, opened afresh.
  function reopen() {
    moved = false
    pinned = true
    settled.value = false
    follow()
  }

  function onScroll() {
    const el = scroller.value
    if (el && moved) pinned = isAtEnd(el)
  }

  function onUser() {
    moved = true
  }

  // the end moved under somebody reading at it — a picture loaded, the
  // composer grew — and they stay at it
  function keep() {
    const el = scroller.value
    if (!el || !settled.value || !readsFromTheEnd.value) return
    if (!moved) land(el)
    else if (pinned) toEnd(el)
  }

  const USER = ['wheel', 'touchmove', 'keydown', 'mousedown']
  let resizes = null

  onMounted(() => {
    const el = scroller.value
    if (!el) return
    el.addEventListener('scroll', onScroll, { passive: true })
    for (const type of USER)
      el.addEventListener(type, onUser, { passive: true })
    // `load` does not bubble, but it can be caught on its way down
    el.addEventListener('load', keep, true)
    resizes = new ResizeObserver(keep)
    resizes.observe(el)
  })

  onBeforeUnmount(() => {
    const el = scroller.value
    resizes?.disconnect()
    if (!el) return
    el.removeEventListener('scroll', onScroll)
    for (const type of USER) el.removeEventListener(type, onUser)
    el.removeEventListener('load', keep, true)
  })

  return { settled, follow, reopen }
}
