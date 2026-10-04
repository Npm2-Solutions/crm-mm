// Modifications copyright (c) 2026, NPM2 Solutions Srl

import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDebounceFn, useStorage } from '@vueuse/core'

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

  function setActiveTabInUrl(tabName) {
    let hash = '#' + tabName.toLowerCase()
    if (route.hash === hash) return
    // a link to one message keeps its hash while the conversation shows it:
    // the conversation lands on what it names
    if (hash === '#activity' && nominaUnMessaggio(route.hash)) return
    router.push({ ...route, hash })
  }

  // A hash that names no tab names a message of the conversation - a
  // notification's link -, which the Activity tab shows: the first tab, taken
  // instead, is Details on a phone, where the message was nowhere.
  function nominaUnMessaggio(hash) {
    const nome = (hash || '').replace('#', '')
    return Boolean(nome) && findTabIndex(nome) === -1
  }

  function tabOrConversation(tabName) {
    let index = findTabIndex(tabName)
    if (index !== -1) return index
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
