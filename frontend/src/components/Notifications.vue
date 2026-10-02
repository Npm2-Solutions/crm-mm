<!--
  The notifications panel, beside the sidebar: what is new for you in the
  centre (docs/progetto-ghl/43-notifiche.md). All of them or only the unread
  ones, under their days, each with its kind's mark; your upcoming events in a
  tab of their own. Escape, a click outside or the cross close it.
-->
<template>
  <Transition name="dc-pannello">
    <aside
      v-if="visible"
      ref="target"
      class="absolute top-0 z-20 flex h-screen w-[400px] max-w-[calc(100vw-1rem)] flex-col border-r border-outline-gray-1 bg-surface-base shadow-2xl focus:outline-none"
      :style="{ left: 'calc(100% + 1px)' }"
      role="dialog"
      :aria-label="__('Notifications')"
      tabindex="-1"
    >
      <header class="flex items-center gap-2 px-4 pb-2 pt-3">
        <h2 class="text-lg-semibold text-ink-gray-9">
          {{ __('Notifications') }}
        </h2>
        <span
          v-if="unreadNotificationsCount"
          class="rounded-full bg-[var(--brand-subtle)] px-1.5 text-xs font-medium leading-5 text-[var(--on-brand-subtle)]"
        >
          {{ unreadNotificationsCount }}
        </span>
        <div class="ml-auto flex items-center gap-1">
          <Button
            v-if="unreadNotificationsCount && scheda !== 'events'"
            variant="ghost"
            :tooltip="__('Mark all as read')"
            :aria-label="__('Mark all as read')"
            @click="segnaTutte"
          >
            <template #icon><LucideCheckCheck class="size-4" /></template>
          </Button>
          <Button
            variant="ghost"
            :tooltip="__('Close')"
            :aria-label="__('Close')"
            @click="close"
          >
            <template #icon><LucideX class="size-4" /></template>
          </Button>
        </div>
      </header>
      <div class="px-4 pb-1">
        <TabButtons
          v-model="scheda"
          :buttons="schede"
          class="[&_button]:w-full [&_div]:w-full [&_button>span]:w-full"
        />
      </div>
      <EventNotificationsArea v-if="scheda === 'events'" />
      <NotificationsList v-else />
    </aside>
  </Transition>
</template>

<script setup>
import EventNotificationsArea from '@/components/EventNotificationsArea.vue'
import NotificationsList from '@/components/Notifications/NotificationsList.vue'
import {
  notificationsStore,
  unreadNotificationsCount,
  visible,
} from '@/stores/notifications'
import { onClickOutside, useEventListener } from '@vueuse/core'
import { TabButtons } from 'frappe-ui'
import { computed, nextTick, ref, watch } from 'vue'
import LucideCheckCheck from '~icons/lucide/check-check'
import LucideX from '~icons/lucide/x'

const store = notificationsStore()
const { close, scegli, segnaTutte } = store

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

const target = ref(null)
onClickOutside(target, () => visible.value && close(), {
  ignore: ['#notifications-btn'],
})

// opened, the keyboard is in it - the panel, not its first button, whose
// tooltip would cover the tabs - and Escape closes it from anywhere
watch(visible, (aperto) => {
  if (aperto) nextTick(() => target.value?.focus({ preventScroll: true }))
})
useEventListener(document, 'keydown', (event) => {
  if (event.key === 'Escape' && visible.value) close()
})
</script>

<style scoped>
.dc-pannello-enter-active,
.dc-pannello-leave-active {
  transition:
    transform 200ms cubic-bezier(0.2, 0, 0, 1),
    opacity 200ms ease;
}
.dc-pannello-enter-from,
.dc-pannello-leave-to {
  transform: translateX(-12px);
  opacity: 0;
}
@media (prefers-reduced-motion: reduce) {
  .dc-pannello-enter-active,
  .dc-pannello-leave-active {
    transition: opacity 120ms ease;
  }
  .dc-pannello-enter-from,
  .dc-pannello-leave-to {
    transform: none;
  }
}
</style>
