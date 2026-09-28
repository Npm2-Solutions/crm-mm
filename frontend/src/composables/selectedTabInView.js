import { nextTick, watch } from 'vue'

/**
 * Keeps the selected tab on screen.
 *
 * On a phone a record's eight tabs are twice as wide as the screen, and opening
 * one on «Tracking» — from a link, a notification, the last tab visited — left
 * the strip scrolled to its start: the selected tab was off to the right and no
 * tab looked selected. Watching the element as well as the index covers the
 * first render, which happens after the record has loaded.
 */
export function useSelectedTabInView(tabs, index) {
  watch(
    [index, () => tabs.value],
    () =>
      nextTick(() => {
        const root = tabs.value?.$el ?? tabs.value
        root
          ?.querySelector?.(
            ':scope > [role="tablist"] > [role="tab"][aria-selected="true"]',
          )
          ?.scrollIntoView({ inline: 'center', block: 'nearest' })
      }),
    { immediate: true },
  )
}
