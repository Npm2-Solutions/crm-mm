import { computed, ref } from 'vue'

export const mobileSidebarOpened = ref(false)

export const isMobileView = computed(() => window.innerWidth < 768)

export const showSettings = ref(false)

export const disableSettingModalOutsideClick = ref(false)

export const activeSettingsPage = ref('')

// Which website the Website settings open on. The Site section sets it before opening the
// modal so you land on the site you were looking at, not on whichever one is the default.
export const activeSettingsSite = ref('')
