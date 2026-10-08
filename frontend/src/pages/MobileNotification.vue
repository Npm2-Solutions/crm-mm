<!--
  The notifications on a phone: the same list as the panel, a page of its own
  (docs/crm/43-notifiche.md).
-->
<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs
        :items="[
          { label: __('Notifications'), route: { name: 'Notifications' } },
        ]"
      />
    </template>
    <template #right-header>
      <Button
        v-if="unreadNotificationsCount && scheda !== 'events'"
        variant="ghost"
        :tooltip="__('Mark all as read')"
        :aria-label="__('Mark all as read')"
        @click="segnaTutte"
      >
        <template #icon><LucideCheckCheck class="size-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <!-- the empty state centres in what is below the header, not in 106px -->
  <div class="flex min-h-0 flex-1 flex-col text-ink-gray-9">
    <div class="px-3 pb-1 pt-2">
      <TabButtons
        v-model="scheda"
        :buttons="schede"
        class="[&_button]:w-full [&_div]:w-full [&_button>span]:w-full"
      />
    </div>
    <EventNotificationsArea v-if="scheda === 'events'" />
    <NotificationsList v-else />
  </div>
</template>

<script setup>
import EventNotificationsArea from '@/components/EventNotificationsArea.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import NotificationsList from '@/components/Notifications/NotificationsList.vue'
import {
  notificationsStore,
  unreadNotificationsCount,
} from '@/stores/notifications'
import { Breadcrumbs, TabButtons } from 'frappe-ui'
import { computed, ref } from 'vue'
import LucideCheckCheck from '~icons/lucide/check-check'

const store = notificationsStore()
const { scegli, segnaTutte } = store

const eventi = ref(false)
const scheda = computed({
  get: () => (eventi.value ? 'events' : store.filtro),
  set: (valore) => {
    eventi.value = valore === 'events'
    if (!eventi.value) scegli(valore)
  },
})
const schede = computed(() => [
  { label: __('All', null, 'Notifications'), value: 'all' },
  { label: __('Unread'), value: 'unread' },
  { label: __('Events'), value: 'events' },
])
</script>
