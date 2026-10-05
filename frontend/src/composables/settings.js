import { ref } from 'vue'

// Re-exported so the ~15 existing `from '@/composables/settings'` imports keep
// working; the reactive definition lives in one place.
export { isMobileView, MOBILE_BREAKPOINT } from '@/composables/breakpoints'

export const showSettings = ref(false)

export const disableSettingModalOutsideClick = ref(false)

export const activeSettingsPage = ref('')

// The field a settings page opens on: «Set up» beside what is still missing lands
// on the tab that holds it and brings it into view, not on the record's first tab.
export const campoDaAprire = ref('')

// Which website the Website settings open on. The Site section sets it before opening the
// modal so you land on the site you were looking at, not on whichever one is the default.
export const activeSettingsSite = ref('')

// Which step of the Telephony page opens: a notification about a new number
// opens Twilio's, not the list of the lines.
export const activeTelephonyStep = ref('')

/** Open the settings on a page, and on a step of it: `{ page, step }`. */
export function apriImpostazioni({ page, step } = {}) {
  if (page === 'Telephony') activeTelephonyStep.value = step || ''
  activeSettingsPage.value = page || ''
  showSettings.value = true
}
