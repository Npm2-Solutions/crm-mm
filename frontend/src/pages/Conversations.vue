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

  <div class="flex flex-1 overflow-hidden">
    <ConversationPicker
      v-model:state="state"
      v-model:search="search"
      :rows="rows"
      :unread="unread.data || {}"
      :loading="people.loading"
      :active="chosen"
      @open="choose"
      @loadMore="loadMore"
    />

    <div v-if="chosen" class="flex min-w-0 flex-1 flex-col overflow-hidden">
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
    <div
      v-else
      class="flex flex-1 flex-col items-center justify-center gap-2 text-ink-gray-4"
    >
      <InboxIcon class="h-8 w-8" />
      <span class="text-lg font-medium">{{ __('Pick a conversation') }}</span>
      <span class="text-sm">
        {{ __('Everything said to this business, in one place.') }}
      </span>
    </div>

    <ConversationAside
      v-if="chosen"
      :person="personOf(chosen)"
      @changed="reload()"
    />
  </div>
</template>

<script setup>
import Activities from '@/components/Activities/Activities.vue'
import ConversationAside from '@/components/Conversations/ConversationAside.vue'
import ConversationPicker from '@/components/Conversations/ConversationPicker.vue'
import InboxIcon from '@/components/Icons/InboxIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { globalStore } from '@/stores/global'
import { Breadcrumbs, createResource, debounce } from 'frappe-ui'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const { $socket } = globalStore()

// Which conversation is open lives in the address, so the browser's back button
// works and a conversation can be linked to — without the page being rebuilt
// around it, which is the whole point of this screen.
const chosen = computed(() => route.query.person || '')
const state = ref('open')
const search = ref('')
const pageLength = ref(40)

const people = createResource({
  url: 'crm.api.conversations.people',
  makeParams: () => ({
    search: search.value,
    state: state.value,
    limit: pageLength.value,
  }),
  auto: true,
})

const rows = computed(() => people.data || [])

const unread = createResource({
  url: 'crm.api.conversations.unread',
  makeParams: () => ({
    records: rows.value.map((row) => ['CRM Lead', row.name]),
  }),
})

function personOf(name) {
  return rows.value.find((row) => row.name === name) || { name }
}

const seen = createResource({ url: 'crm.api.conversations.mark_seen' })

function choose(row) {
  if (row.name === chosen.value) return
  router.replace({ name: 'Conversations', query: { person: row.name } })
}

// Opening one is reading it. Told to the server because the list is shared: a
// colleague looking at the same screen should see the same thing.
watch(
  chosen,
  (name) => {
    if (!name) return
    seen
      .submit({ reference_doctype: 'CRM Lead', reference_name: name })
      .then(() => unread.fetch())
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
watch(state, () => {
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
