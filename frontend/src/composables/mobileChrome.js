import { onBeforeUnmount, ref, watch } from 'vue'

/**
 * Screens that want the whole phone.
 *
 * A conversation is the case this exists for: the composer wants the bottom
 * edge of the screen, and a tab bar underneath it both steals the space and
 * invites you to leave a reply half-written. Every messenger hides its tabs
 * when you open a chat and gives you a back arrow instead; this is that.
 *
 * Only the mobile shell reads it — on a desktop there is nothing to hide.
 */
export const mobileNavHidden = ref(false)

/**
 * Hide the phone's tab bar while `active` is true, and always put it back when
 * the screen goes away — including when you leave mid-conversation, which a
 * plain `watch` in the page would miss.
 */
export function useHiddenMobileNav(active) {
  watch(active, (on) => (mobileNavHidden.value = !!on), { immediate: true })
  onBeforeUnmount(() => (mobileNavHidden.value = false))
}
