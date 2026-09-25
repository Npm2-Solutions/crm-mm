<!--
  Where you answer people.

  The Inbox used to be a view of the People list, and clicking a row took you
  away to that person's record — which is the trip every messenger exists to
  remove. Answering five people meant five trips, and each one lost your place.

  So this is a place you stay: the list on the left, the conversation in the
  middle, the person on the right. Nothing navigates; choosing somebody swaps
  the middle and the right, and the left column keeps its scroll, its search and
  its filter.

  The rows are the same rows as the People list, from the same fields — the two
  are still one list underneath. What changed is that this one is a screen for
  reading and replying, not a table you click out of.
-->
<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs
        :items="[
          { label: __('Conversations'), route: { name: 'Conversations' } },
        ]"
      />
    </template>
    <template #right-header>
      <Button
        variant="ghost"
        icon="lucide-refresh-ccw"
        :loading="people.loading"
        :tooltip="__('Refresh')"
        @click="reload()"
      />
    </template>
  </LayoutHeader>

  <!--
    Three panes side by side is a desk, not a phone. At 390 pixels the list
    alone took 320 of them and the conversation got a sliver — so on a phone the
    three become one at a time: the list, then the thread with a way back, and
    the person behind a button.
  -->
  <div class="flex flex-1 overflow-hidden">
    <ConversationPicker
      v-if="!isMobileView || !chosen"
      v-model:view="view"
      v-model:search="search"
      :rows="rows"
      :unread="unread.data || {}"
      :counts="counts.data || {}"
      :loading="people.loading"
      :active="chosen"
      @open="choose"
      @loadMore="loadMore"
    />

    <div v-if="chosen" class="flex min-w-0 flex-1 flex-col overflow-hidden">
      <!-- the way back, and the way to the person: on a phone they are the only
         two things the other panes can be reached by -->
      <div
        v-if="isMobileView"
        class="flex h-11 shrink-0 items-center gap-2 border-b px-2"
      >
        <Button variant="ghost" icon="arrow-left" @click="back()" />
        <span class="min-w-0 flex-1 truncate text-base font-medium">
          {{ nameOf(personOf(chosen)) }}
        </span>
        <Button variant="ghost" icon="info" @click="showPerson = true" />
      </div>
      <!--
        The Activity tab of that person, whole: the channel picker, the stream
        and the composer, with everything they already know about replies,
        templates, voice notes and failed sends. Rebuilding a chat here to gain
        a layout would have lost all of it.
      -->
      <Activities
        :key="chosen"
        doctype="CRM Lead"
        :docname="chosen"
        @afterSave="reload()"
      />
    </div>
    <!-- on a phone the list *is* the empty state, so there is nothing to say -->
    <div
      v-else-if="!isMobileView"
      class="flex flex-1 flex-col items-center justify-center gap-2 text-ink-gray-4"
    >
      <InboxIcon class="h-8 w-8" />
      <span class="text-lg font-medium">{{ __('Pick a conversation') }}</span>
      <span class="text-sm">
        {{ __('Everything said to this business, in one place.') }}
      </span>
    </div>

    <ConversationAside
      v-if="chosen && !isMobileView"
      :person="personOf(chosen)"
      @changed="reload()"
    />
  </div>

  <!-- and on a phone it slides in over the conversation, because there is no
     third column to put it in -->
  <Dialog v-model="showPerson" :options="{ size: 'sm' }">
    <template #body>
      <ConversationAside
        v-if="chosen"
        class="!w-full !border-l-0"
        :person="personOf(chosen)"
        @changed="reload()"
      />
    </template>
  </Dialog>
</template>

<script setup>
import Activities from '@/components/Activities/Activities.vue'
import ConversationAside from '@/components/Conversations/ConversationAside.vue'
import ConversationPicker from '@/components/Conversations/ConversationPicker.vue'
import InboxIcon from '@/components/Icons/InboxIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { globalStore } from '@/stores/global'
import { isMobileView } from '@/composables/settings'
import { Breadcrumbs, Dialog, createResource, debounce } from 'frappe-ui'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const { $socket } = globalStore()

// Which conversation is open lives in the address, so the browser's back button
// works and a conversation can be linked to — without the page being rebuilt
// around it, which is the whole point of this screen.
const chosen = computed(() => route.query.person || '')
const view = ref('open')
const search = ref('')
const pageLength = ref(40)

const people = createResource({
  url: 'crm.api.conversations.people',
  makeParams: () => ({
    search: search.value,
    view: view.value,
    limit: pageLength.value,
  }),
  auto: true,
})

const rows = computed(() => people.data || [])

// How many are in each view, for the numbers in the selector. One sweep over
// the table for all of them, not one query per line of the menu.
const counts = createResource({
  url: 'crm.api.conversations.counts',
  auto: true,
})

const unread = createResource({
  url: 'crm.api.conversations.unread',
  makeParams: () => ({
    records: rows.value.map((row) => ['CRM Lead', row.name]),
  }),
})

const showPerson = ref(false)

function personOf(name) {
  return rows.value.find((row) => row.name === name) || { name }
}

function nameOf(person) {
  return person?.lead_name || person?.organization || person?.name || ''
}

// Back to the list, which on a phone is the pane this one replaced.
function back() {
  showPerson.value = false
  router.replace({ name: 'Conversations' })
}

// Opening a chat does not mark it read — looking is not dealing with it. What
// it can do, if the site has said so, is tell WhatsApp the messages have been
// read, which is a different promise made to a different person.
const acknowledge = createResource({
  url: 'crm.api.conversations.acknowledge',
})

function choose(row) {
  if (row.name === chosen.value) return
  router.replace({ name: 'Conversations', query: { person: row.name } })
}

watch(
  chosen,
  (name) => {
    if (!name) return
    acknowledge.submit({
      reference_doctype: 'CRM Lead',
      reference_name: name,
    })
  },
  { immediate: true },
)

watch(
  () => rows.value.map((row) => row.name).join(','),
  (names) => names && unread.fetch(),
  { immediate: true },
)

const searchLater = debounce(() => {
  pageLength.value = 40
  people.reload()
}, 300)

watch(search, searchLater)
watch(view, () => {
  pageLength.value = 40
  people.reload()
})

function loadMore() {
  if (people.loading) return
  if (rows.value.length < pageLength.value) return
  pageLength.value += 40
  people.reload()
}

function reload() {
  people.reload()
  unread.fetch()
  counts.reload()
}

// a message arriving reorders this list, so it has to be told
const refresh = debounce(() => reload(), 400)

onMounted(() => {
  $socket.on('crm_sms_message', refresh)
  $socket.on('whatsapp_message', refresh)
})

onBeforeUnmount(() => {
  $socket.off('crm_sms_message', refresh)
  $socket.off('whatsapp_message', refresh)
})
</script>
