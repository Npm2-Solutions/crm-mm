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
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import SMSIcon from '@/components/Icons/SMSIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import MenuIcon from '@/components/Icons/MenuIcon.vue'
import { mobileSidebarOpened } from '@/composables/settings'
import { bottomNavTabFor } from '@/utils/navigation'
import { MobileNav, MobileNavItem } from 'frappe-ui'
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

// What a phone is opened for, in the order a thumb reaches them. Conversations
// is the screen people live in; the calendar is the other half of the day. The
// People list is not here on purpose — you get to a person from the conversation
// you are having with them, not by going to look them up.
const tabs = [
  {
    key: 'Conversations',
    label: 'Chat',
    icon: SMSIcon,
    to: { name: 'Conversations' },
  },
  {
    key: 'Calendar',
    label: 'Calendar',
    icon: CalendarIcon,
    to: { name: 'Calendar' },
  },
  { key: 'Tasks', label: 'Tasks', icon: TaskIcon, to: { name: 'Tasks' } },
  { key: 'Deals', label: 'Deals', icon: DealsIcon, to: { name: 'Deals' } },
]

// `MobileNavItem` lights itself up on an exact route match, which leaves a tab
// dark the moment you open a record inside its section.
const activeTab = computed(() => bottomNavTabFor(route))
</script>
