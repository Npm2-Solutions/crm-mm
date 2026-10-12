// Modifications copyright (c) 2026, NPM2 Solutions Srl

import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDebounceFn, useStorage } from '@vueuse/core'

// the tabs a record's page may have, by the name its address gives them
const SCHEDE_DEI_RECORD = new Set([
  'summary',
  'activity',
  'data',
  'details',
  'events',
  'subscriptions',
  'tasks',
  'notes',
  'attachments',
  'forms',
  'documents',
  'quotes',
  'plans',
  'area',
  'clinic',
  'tracking',
  'emails',
  'calls',
  'deals',
  'contacts',
])

export function useActiveTabManager(tabs, storageKey) {
  const activeTab = useStorage(storageKey, 'activity')
  const route = useRoute()
  const router = useRouter()

  const changeTabTo = (tabName) => {
    let index = findTabIndex(tabName)
    if (index == -1) return
    tabIndex.value = index
  }

  const preserveLastVisitedTab = useDebounceFn((tabName) => {
    activeTab.value = tabName.toLowerCase()
  }, 300)

  // The address follows the tab once the tab is drawn: the push reads the
  // page's scroll to keep it in the history, and read in the middle of the tap
  // it made the browser lay the page out once more before drawing the tab.
  function setActiveTabInUrl(tabName) {
    const hash = '#' + tabName.toLowerCase()
    const pagina = route.path
    requestAnimationFrame(() =>
      setTimeout(() => {
        if (route.path !== pagina || route.hash === hash) return
        // a link to one message keeps its hash while the conversation shows
        // it: the conversation lands on what it names
        if (hash === '#activity' && nominaUnMessaggio(route.hash)) return
        // a tab already left is not written
        const ora = tabs.value?.[tabIndex.value]?.name?.toLowerCase()
        if (ora !== tabName.toLowerCase()) return
        router.push({ ...route, hash })
      }),
    )
  }

  // A hash that names no tab names a message of the conversation - a
  // notification's link -, which the Activity tab shows: the first tab, taken
  // instead, is Details on a phone, where the message was nowhere.
  function nominaUnMessaggio(hash) {
    const nome = (hash || '').replace('#', '')
    return (
      Boolean(nome) && findTabIndex(nome) === -1 && !SCHEDE_DEI_RECORD.has(nome)
    )
  }

  // An address naming a tab this page does not have for this reader - the
  // Clinic for whoever does not care for the person, Data on a computer, where
  // the data sit beside the tabs - opens the first tab: it opened the Chat,
  // still under «#clinic», as if the record were its messages
  function tabOrConversation(tabName) {
    let index = findTabIndex(tabName)
    if (index !== -1) return index
    if (SCHEDE_DEI_RECORD.has(tabName)) return 0
    index = findTabIndex('activity')
    return index !== -1 ? index : 0
  }

  function getActiveTabFromUrl() {
    return route.hash.replace('#', '')
  }

  function findTabIndex(tabName) {
    return tabs.value?.findIndex(
      (tabOptions) => tabOptions.name.toLowerCase() === tabName,
    )
  }

  function getTabIndex(tabName) {
    let index = findTabIndex(tabName)
    return index !== -1 ? index : 0 // Default to the first tab if not found
  }

  function getActiveTab() {
    let _activeTab = getActiveTabFromUrl()
    if (_activeTab) {
      let index = findTabIndex(_activeTab)
      if (index !== -1) {
        preserveLastVisitedTab(_activeTab)
        return index
      }
      return tabOrConversation(_activeTab)
    }

    let lastVisitedTab = activeTab.value
    if (lastVisitedTab) {
      return getTabIndex(lastVisitedTab)
    }

    return 0 // Default to the first tab if nothing is found
  }

  const tabIndex = ref(getActiveTab())

  watch(tabIndex, (tabIndexValue) => {
    let currentTab = tabs.value?.[tabIndexValue].name
    setActiveTabInUrl(currentTab)
    preserveLastVisitedTab(currentTab)
  })

  watch(
    () => route.hash,
    (tabValue) => {
      if (!tabValue) return

      let tabName = tabValue.replace('#', '')
      let index = tabOrConversation(tabName)

      let currentTab = tabs.value?.[index].name
      preserveLastVisitedTab(currentTab)
      tabIndex.value = index
    },
  )

  watch(tabs, () => {
    tabIndex.value = getActiveTab()
  })

  return { tabIndex, changeTabTo }
}
