<template>
  <MobileNav>
    <MobileNavItem
      v-for="tab in tabs"
      :key="tab.key"
      :to="{ name: tab.key }"
      :label="__(tab.label)"
      :icon="tab.icon"
      :active="isActive(tab)"
    />
    <MobileNavItem
      :label="__('More')"
      :icon="MenuIcon"
      :active="mobileSidebarOpened"
      @click="mobileSidebarOpened = true"
    />
  </MobileNav>
</template>

<script setup>
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import SMSIcon from '@/components/Icons/SMSIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import MenuIcon from '@/components/Icons/MenuIcon.vue'
import { mobileSidebarOpened } from '@/composables/settings'
import { MobileNav, MobileNavItem } from 'frappe-ui'
import { useRoute } from 'vue-router'

const route = useRoute()

// The four a phone actually opens all day. Everything else — Organizations,
// Notes, Call Logs, Automations, the saved views — stays one tap away behind
// "More", which is the existing drawer.
const tabs = [
  { key: 'Leads', label: 'People', icon: LeadsIcon },
  { key: 'Deals', label: 'Deals', icon: DealsIcon },
  { key: 'Inbox', label: 'Inbox', icon: SMSIcon },
  { key: 'Tasks', label: 'Tasks', icon: TaskIcon },
]

// `MobileNavItem` lights itself up on an exact route match, which is not enough
// here: `Lead` and `Deal` are the detail pages of the `Leads` / `Deals` tabs, so
// the tab has to stay lit while you are inside a record.
function isActive(tab) {
  return [tab.key, tab.key.replace(/s$/, '')].includes(route.name)
}
</script>
