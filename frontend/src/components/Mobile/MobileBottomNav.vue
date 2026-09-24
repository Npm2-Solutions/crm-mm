<template>
  <!-- `pb-safe` keeps the row clear of the home indicator; without it the last
       few pixels of every tab sit under it and the bar reads as cut off. -->
  <nav
    class="flex shrink-0 items-stretch border-t border-outline-gray-1 bg-surface-base pb-safe"
    :aria-label="__('Main')"
  >
    <component
      :is="item.to ? 'router-link' : 'button'"
      v-for="item in items"
      :key="item.key"
      v-bind="item.to ? { to: item.to } : { type: 'button' }"
      class="flex min-h-[52px] flex-1 flex-col items-center justify-center gap-0.5 py-1.5 active:bg-surface-gray-2"
      :class="item.active ? 'text-ink-gray-9' : 'text-ink-gray-5'"
      :aria-current="item.active ? 'page' : undefined"
      @click="item.onClick?.()"
    >
      <component :is="item.icon" class="size-5" />
      <span class="max-w-full truncate px-1 text-xs leading-none">
        {{ __(item.label) }}
      </span>
    </component>
  </nav>
</template>

<script setup>
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import SMSIcon from '@/components/Icons/SMSIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import MenuIcon from '@/components/Icons/MenuIcon.vue'
import { mobileSidebarOpened } from '@/composables/settings'
import { computed } from 'vue'
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

const items = computed(() => [
  ...tabs.map((tab) => ({
    ...tab,
    to: { name: tab.key },
    // `Lead` and `Deal` are the detail pages of the `Leads` / `Deals` tabs, so
    // the tab stays lit while you are inside a record.
    active: [tab.key, tab.key.replace(/s$/, '')].includes(route.name),
  })),
  {
    key: 'more',
    label: 'More',
    icon: MenuIcon,
    active: mobileSidebarOpened.value,
    onClick: () => (mobileSidebarOpened.value = true),
  },
])
</script>
