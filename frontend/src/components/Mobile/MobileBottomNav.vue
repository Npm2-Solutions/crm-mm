<template>
  <MobileNav>
    <MobileNavItem
      v-for="tab in tabs"
      :key="tab.key"
      :to="tab.to"
      :label="__(tab.label)"
      :icon="tab.icon"
      :active="activeTab === tab.key"
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
import { INBOX_VIEW_TYPE, bottomNavTabFor } from '@/utils/navigation'
import { MobileNav, MobileNavItem } from 'frappe-ui'
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

// The four a phone actually opens all day. Everything else — Organizations,
// Notes, Call Logs, Automations, the saved views — stays one tap away behind
// "More", which is the existing drawer.
const tabs = [
  { key: 'Leads', label: 'People', icon: LeadsIcon, to: { name: 'Leads' } },
  { key: 'Deals', label: 'Deals', icon: DealsIcon, to: { name: 'Deals' } },
  {
    key: 'Inbox',
    label: 'Inbox',
    icon: SMSIcon,
    // Not a route of its own: the People list, ordered by who wrote last. The
    // `/inbox` path still exists but only redirects here.
    to: { name: 'Leads', params: { viewType: INBOX_VIEW_TYPE } },
  },
  { key: 'Tasks', label: 'Tasks', icon: TaskIcon, to: { name: 'Tasks' } },
]

// `MobileNavItem` lights itself up on an exact route match, which gets both ends
// of the Inbox wrong: People would be lit while reading the Inbox, and the Inbox
// never, since the redirect lands on the `Leads` route.
const activeTab = computed(() => bottomNavTabFor(route))
</script>
