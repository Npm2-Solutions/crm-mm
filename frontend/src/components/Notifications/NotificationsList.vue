<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The notifications under their days - today, yesterday, this week, earlier -
  newest first, the day's label staying on top while its rows scroll. The same
  list in the panel and on the phone's page.
-->
<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <div
      v-if="!notifications.fetched && notifications.loading"
      class="flex flex-1 items-center justify-center py-10"
    >
      <LoaderMark />
    </div>
    <div
      v-else-if="!righe.length"
      class="flex flex-1 items-center justify-center px-6 py-10"
    >
      <EmptyState
        :title="filtro === 'unread' ? __('All read') : __('No notifications')"
        :text="
          filtro === 'unread'
            ? __('The notifications you have read stay under All.')
            : __(
                'Here you find who mentions you, what is assigned to you and the messages of the people you follow.',
              )
        "
      />
    </div>
    <div v-else class="min-h-0 flex-1 overflow-y-auto px-2 pb-3">
      <section v-for="s in giorni" :key="s.key" :aria-label="__(s.label)">
        <h3
          class="sticky top-0 z-[1] bg-surface-base px-2 pb-1 pt-3 text-[11px] font-medium uppercase tracking-wide text-ink-gray-5"
        >
          {{ __(s.label) }}
        </h3>
        <NotificationRow
          v-for="riga in s.rows"
          :key="riga.name"
          :riga="riga"
          :adesso="adesso"
          @opened="apri"
          @read="segnaLetta"
          @unread="segnaDaLeggere"
        />
      </section>
      <div v-if="notifications.data?.more" class="flex justify-center pt-2">
        <Button
          variant="subtle"
          :label="__('Show more')"
          :loading="notifications.loading"
          @click="mostraAltre"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import EmptyState from '@/components/Espresso/EmptyState.vue'
import LoaderMark from '@/components/Espresso/LoaderMark.vue'
import NotificationRow from '@/components/Notifications/NotificationRow.vue'
import { apriImpostazioni } from '@/composables/settings'
import { notifications, notificationsStore } from '@/stores/notifications'
import { sezioni } from '@/utils/notifiche'
import { dayjsLocal } from 'frappe-ui'
import { computed } from 'vue'

const store = notificationsStore()
const { segnaLetta, segnaDaLeggere, mostraAltre } = store
const filtro = computed(() => store.filtro)

const righe = computed(() => notifications.data?.rows || [])

// the reader's clock: the server's moments are moved onto it before the days
// are cut, as the conversations' list does
const adesso = computed(() => {
  // a new page of rows is a new now
  void righe.value
  return dayjsLocal().format('YYYY-MM-DD HH:mm:ss')
})
const giorni = computed(() =>
  sezioni(righe.value, adesso.value, (riga) =>
    dayjsLocal(riga.creation).format('YYYY-MM-DD HH:mm:ss'),
  ),
)

// a row is a link: the browser goes where it leads; here it is read and the
// panel closes. A row about the settings opens them; one that leads nowhere is
// only read
function apri(riga) {
  segnaLetta(riga)
  if (riga.route) store.close()
  else if (riga.settings) {
    store.close()
    apriImpostazioni(riga.settings)
  }
}
</script>
