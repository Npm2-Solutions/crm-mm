import { ref } from 'vue'

export const mobileSidebarOpened = ref(false)

// Re-exported so the ~15 existing `from '@/composables/settings'` imports keep
// working; the reactive definition lives in one place.
export { isMobileView, MOBILE_BREAKPOINT } from '@/composables/breakpoints'

export const showSettings = ref(false)

export const disableSettingModalOutsideClick = ref(false)

export const activeSettingsPage = ref('')

// Which website the Website settings open on. The Site section sets it before opening the
// modal so you land on the site you were looking at, not on whichever one is the default.
export const activeSettingsSite = ref('')
