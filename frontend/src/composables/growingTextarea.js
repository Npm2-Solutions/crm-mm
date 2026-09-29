import { nextTick, onBeforeUnmount, onMounted, toValue, watch } from 'vue'

/**
 * A textarea as tall as what is written in it, up to `most` lines.
 *
 * Its height used to be counted in Enter presses: a sentence long enough to
 * wrap onto a third line stayed one line tall and scrolled inside itself, so
 * the beginning of what was being written slid out of sight while it was
 * written. Now it is measured: one line for «ok», as many as the words take,
 * and past `most` it scrolls — the conversation above is the thing it must not
 * swallow.
 *
 * @param {import('vue').Ref} field  the frappe-ui Textarea (its `el`) or the element
 * @param {import('vue').Ref<string>} content  what is written
 * @param {{ most?: number }} options
 */
export function useGrowingTextarea(field, content, { most = 6 } = {}) {
  function element() {
    const value = toValue(field)
    return value?.el ?? value ?? null
  }

  function fit() {
    const el = element()
    // hidden (another channel's box): nothing to measure, and a height of 0
    // would be kept when it comes back
    if (!el || !el.getClientRects().length) return
    const style = getComputedStyle(el)
    const lineHeight = parseFloat(style.lineHeight) || 21
    const padding =
      parseFloat(style.paddingTop) + parseFloat(style.paddingBottom)
    const border = el.offsetHeight - el.clientHeight
    const limit = lineHeight * most + padding
    el.style.height = 'auto'
    const needed = el.scrollHeight
    el.style.height = `${Math.min(needed, limit) + border}px`
    el.style.overflowY = needed > limit ? 'auto' : 'hidden'
  }

  let frame = 0
  function refit() {
    cancelAnimationFrame(frame)
    frame = requestAnimationFrame(fit)
  }

  watch(content, () => nextTick(fit))

  // Measured again when its width changes: a narrower window wraps the same
  // words onto more lines, and a box that was hidden — a draft on another
  // channel, the composer opening on it — has a width again once it shows.
  // Only the width: the height is this code's own doing, and answering it
  // would be a loop. The measuring waits for the next frame for the same
  // reason, outside the observer's own turn.
  let widths = null
  let width = -1
  onMounted(() => {
    nextTick(fit)
    const el = element()
    if (!el) return
    widths = new ResizeObserver(([entry]) => {
      const now = Math.round(entry.contentRect.width)
      if (now === width) return
      width = now
      refit()
    })
    widths.observe(el)
  })

  onBeforeUnmount(() => {
    cancelAnimationFrame(frame)
    widths?.disconnect()
  })

  return { fit }
}
