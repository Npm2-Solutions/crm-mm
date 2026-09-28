import { firstFocusable, firstTypable } from '@/utils/focus'
import { nextTick, onBeforeUnmount, toValue, watch } from 'vue'

// Long enough for a layout fetched when the dialog opens; a form that has not
// drawn a single field by then is not one to keep waiting on.
const PATIENCE = 3000

/**
 * Put the cursor in the first field of a dialog, once there is one.
 *
 * frappe-ui's Dialog takes over the first focus when its content carries an
 * `[autofocus]` marker, and it looks under the marker at the moment the dialog
 * opens. These forms draw their fields a moment later — the layout is fetched
 * when the dialog opens — so at that moment there was nothing to focus, and
 * nothing was: the cursor stayed on the button that had opened the dialog,
 * behind it. What was typed went nowhere, and Tab walked the page underneath.
 *
 * So this waits for the first field somebody can type into, focuses it once,
 * and stops. Meanwhile the focus is kept inside the dialog. Where somebody has
 * already clicked or tabbed to, theirs wins.
 *
 * @param {import('vue').Ref<HTMLElement|null>} container  the marked wrapper
 * @param {import('vue').Ref<boolean>} open                whether it is open
 */
export function useFirstFieldFocus(container, open) {
  let observer = null
  let timer = 0

  function stop() {
    observer?.disconnect()
    observer = null
    clearTimeout(timer)
  }

  function dialogOf(root) {
    return root.closest('[role="dialog"]') || root
  }

  // Focus somebody put there — a click, a Tab — as opposed to where a dialog
  // opening leaves it: the dialog itself, or the first control, which is what
  // frappe-ui picks when the fields happen to be drawn in time.
  function chosen(root) {
    const now = document.activeElement
    const dialog = dialogOf(root)
    return (
      dialog.contains(now) && now !== dialog && now !== firstFocusable(root)
    )
  }

  // true once there is nothing left to do
  function settle(last = false) {
    const root = toValue(container)
    if (!root) return false
    if (chosen(root)) return true
    const field = firstTypable(root) || (last ? firstFocusable(root) : null)
    if (field) {
      field.focus({ preventScroll: true })
      return true
    }
    const dialog = dialogOf(root)
    if (!dialog.contains(document.activeElement)) {
      dialog.focus?.({ preventScroll: true })
    }
    return false
  }

  watch(
    () => [toValue(open), toValue(container)],
    ([isOpen, root]) => {
      stop()
      if (!isOpen || !root) return
      // after frappe-ui's own attempt, which runs a frame after opening
      nextTick(() =>
        requestAnimationFrame(() =>
          requestAnimationFrame(() => {
            if (settle()) return
            observer = new MutationObserver(() => settle() && stop())
            observer.observe(root, { childList: true, subtree: true })
            timer = setTimeout(() => {
              settle(true)
              stop()
            }, PATIENCE)
          }),
        ),
      )
    },
    { immediate: true },
  )

  onBeforeUnmount(stop)
}
