<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

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
  <!-- on a phone a chat open is the screen, as in WhatsApp: its own header
       takes the page's row, beside the phone at the top right -->
  <LayoutHeader v-if="filoSulTelefono">
    <ConversationHeader
      :person="current"
      back
      details
      :wide="false"
      inTestata
      @back="back()"
      @details="showPerson = true"
      @changed="reload()"
    />
  </LayoutHeader>
  <LayoutHeader v-else>
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
        :aria-label="__('Refresh')"
        @click="refreshList()"
      />
    </template>
  </LayoutHeader>

  <!--
    Three panes side by side is a desk, not a phone. At 390 pixels the list
    alone took 320 of them and the conversation got a sliver — so on a phone the
    three become one at a time: the list, then the thread with a way back, and
    the person behind a button. And on a laptop the third pane waits behind the
    same button: at 1024 pixels the sidebar, the list and the panel left the
    conversation 176 pixels to be read in.
  -->
  <div class="flex flex-1 overflow-hidden">
    <ConversationPicker
      v-if="!isMobileView || !chosen"
      v-model:view="view"
      v-model:search="search"
      v-model:onlyUnread="onlyUnread"
      :rows="rows"
      :unread="unread.data || {}"
      :counts="counts.data || {}"
      :loading="people.loading"
      :active="chosen"
      :aggiorna="refreshList"
      @open="choose"
      @loadMore="loadMore"
    />

    <div v-if="chosen" class="flex min-w-0 flex-1 flex-col overflow-hidden">
      <!-- a person one does not follow, opened by the address: why, in words,
           and the way back, never their code over an empty thread -->
      <template v-if="nonSiApre">
        <div v-if="isMobileView" class="flex shrink-0 items-center px-2 py-2">
          <Button
            variant="ghost"
            icon="lucide-arrow-left"
            :aria-label="__('Back to the list')"
            @click="back()"
          />
        </div>
        <ErrorPage
          :errorTitle="nonSiApre.titolo"
          :errorMessage="nonSiApre.testo"
        />
      </template>
      <div
        v-else-if="!leggibile"
        class="flex flex-1 items-center justify-center"
      >
        <LoaderMark />
      </div>
      <template v-else>
        <ConversationHeader
          v-if="!filoSulTelefono"
          :person="current"
          :back="isMobileView"
          :details="!roomForPanel"
          :wide="!isMobileView"
          @back="back()"
          @details="showPerson = true"
          @changed="reload()"
        />
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
          :newMessages="newMessages"
          :waitForNew="!opened.ready && !person.error"
          @afterSave="reload()"
        />
      </template>
    </div>
    <!-- on a phone the list *is* the empty state, so there is nothing to say -->
    <div
      v-else-if="!isMobileView"
      class="flex flex-1 flex-col items-center justify-center gap-2 bg-surface-gray-2 text-center dark:bg-surface-base"
    >
      <InboxIcon class="mb-1 size-8 text-ink-gray-4" />
      <span class="text-lg font-medium text-ink-gray-7">
        {{ __('Pick a conversation') }}
      </span>
      <span class="max-w-xs text-p-sm text-ink-gray-5">
        {{ __('Everything said to this business, in one place.') }}
      </span>
    </div>

    <ConversationAside
      v-if="chosen && roomForPanel && leggibile"
      :person="current"
      @changed="reload()"
    />
  </div>

  <!-- and where there is no room for a third column, it comes in over the
     conversation -->
  <Dialog v-model="showPerson" :options="{ size: 'sm' }">
    <template #body>
      <ConversationAside
        v-if="chosen"
        class="!w-full !border-l-0"
        :person="current"
        @changed="reload()"
      />
    </template>
  </Dialog>
</template>

<script setup>
import LoaderMark from '@/components/Espresso/LoaderMark.vue'
import Activities from '@/components/Activities/Activities.vue'
import ConversationAside from '@/components/Conversations/ConversationAside.vue'
import ConversationHeader from '@/components/Conversations/ConversationHeader.vue'
import ConversationPicker from '@/components/Conversations/ConversationPicker.vue'
import ErrorPage from '@/components/ErrorPage.vue'
import InboxIcon from '@/components/Icons/InboxIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { isMobileView, viewportWidth } from '@/composables/breakpoints'
import { readReceipts } from '@/composables/conversationState'
import { useRitorno } from '@/composables/ritorno'
import { useChatAperta } from '@/composables/chatAperta'
import { keepInPlace, laterLabel, whyItLeft } from '@/utils/conversation'
import { appLocale } from '@/utils/locale'
import { alToccoDellaScheda } from '@/utils/schedaAttiva'
import { schedaChiusa } from '@/utils/schedaChiusa'
import {
  Breadcrumbs,
  Button,
  Dialog,
  createResource,
  dayjsLocal,
  debounce,
} from 'frappe-ui'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const { $socket } = globalStore()
const { puo } = usersStore()

// Which conversation is open lives in the address, so the browser's back button
// works and a conversation can be linked to — without the page being rebuilt
// around it, which is the whole point of this screen.
const chosen = computed(() => route.query.person || '')
const view = ref('open')
const search = ref('')
// only the unread, among the view that is open
const onlyUnread = ref(false)
const pageLength = ref(40)
// back to this page from a person's: the list as it was left - the view, the
// search, the unread only, how many it showed - before it is asked for
useRitorno('conversazioni', {
  stato: () => ({
    view: view.value,
    search: search.value,
    onlyUnread: onlyUnread.value,
    pageLength: pageLength.value,
  }),
  rimetti: (salvato) => {
    view.value = salvato.view
    search.value = salvato.search
    onlyUnread.value = salvato.onlyUnread
    pageLength.value = salvato.pageLength
  },
})

const people = createResource({
  url: 'crm.api.conversations.people',
  makeParams: () => ({
    search: search.value,
    view: view.value,
    waiting: onlyUnread.value ? 1 : 0,
    limit: pageLength.value,
  }),
  auto: true,
})

// What the list shows: what the server sent, with the conversation being read
// kept where it was when something just decided about it takes it out of this
// list (`keepInPlace`) — handled, put off, read while only the unread are
// shown. Tied to the list it was kept in: another view, a search or the unread
// filter is another list, one it never was a row of.
const shown = ref([])
const listKey = computed(() =>
  JSON.stringify([view.value, search.value.trim(), onlyUnread.value]),
)
let shownFor = ''
watch(
  () => people.data,
  (next) => {
    shown.value =
      shownFor === listKey.value
        ? keepInPlace(next || [], shown.value, chosen.value)
        : [...(next || [])]
    shownFor = listKey.value
  },
  { immediate: true },
)

// The rows, the open one as it is now rather than as the list last drew it —
// and, when it is leaving, why.
const rows = computed(() =>
  shown.value.map((row) => {
    if (row.name !== chosen.value) return row
    const now =
      person.data?.name === row.name ? { ...row, ...person.data } : row
    if (!row.leaving) return now
    const why = whyItLeft(now, view.value, onlyUnread.value)
    return { ...now, leaving_as: why, why: whyLabel(why, now) }
  }),
)

function whyLabel(why, row) {
  if (why === 'handled') return __('Handled · back when they write')
  if (why === 'snoozed') {
    const local = (at) =>
      dayjsLocal(at || undefined).format('YYYY-MM-DD HH:mm:ss')
    const when = laterLabel(
      local(row.conversation_snoozed_until),
      local(),
      appLocale(),
    )
    return __('Put off until {0}', [when])
  }
  if (why === 'answered') return __('Answered · no longer waiting')
  if (why === 'read') return __('Read', null, 'Conversation read')
  if (why === 'reopened') return __('Back in Open')
  return ''
}

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

// A third column only where it leaves the conversation room to be read in: at
// 1280 pixels the sidebar, the list and the panel left the middle 430, and the
// name in the header was the first thing cut.
const roomForPanel = computed(() => viewportWidth.value >= 1400)

// The person whose conversation is open, read on its own rather than looked up
// among the rows on screen. The list holds the top of one view; a link — from
// the dashboard, a notification, a colleague — can name anybody, and looking
// only there is how the header came to say «CRM-LEAD-2026-00128».
const person = createResource({
  url: 'crm.api.conversations.person',
  makeParams: () => ({ name: chosen.value }),
})

// The freshest of the two copies: the one read for this conversation once it
// has arrived, the row from the list until then, and the bare name before
// either — never somebody else's.
const current = computed(() => {
  if (person.data?.name === chosen.value) return person.data
  return (
    rows.value.find((row) => row.name === chosen.value) || {
      name: chosen.value,
    }
  )
})

// A conversation opened from the list is one the server listed; one opened by
// its address waits for the person, who may not be one's to read (doc 30).
const leggibile = computed(
  () =>
    person.data?.name === chosen.value ||
    rows.value.some((row) => row.name === chosen.value),
)
const nonSiApre = computed(() =>
  !leggibile.value && person.error
    ? schedaChiusa(person.error, 'CRM Lead')
    : null,
)

// a chat open on a phone is the screen, as in WhatsApp: its header takes the
// page's, and the bar at the bottom steps aside for its box to write in
// (composables/chatAperta.js)
const filoSulTelefono = computed(
  () => isMobileView.value && Boolean(chosen.value) && leggibile.value,
)
useChatAperta(() => filoSulTelefono.value && puo('conversazioni.usa'))

// On a phone the chat takes the list's place: opening one is a step forward,
// so Android's back, and the arrow, return to the list, as in WhatsApp. On a
// computer the list stays beside the chat, and changing chat writes no history.
function back() {
  showPerson.value = false
  if (isMobileView.value && vieneDallaLista()) {
    router.back()
    return
  }
  router.replace({ name: 'Conversations' })
}

function vieneDallaLista() {
  const prima = window.history.state?.back
  if (!prima) return false
  const dove = router.resolve(prima)
  return dove.name === 'Conversations' && !dove.query.person
}

function choose(row) {
  if (row.name === chosen.value) return
  const dove = { name: 'Conversations', query: { person: row.name } }
  if (isMobileView.value && !chosen.value) router.push(dove)
  else router.replace(dove)
}

watch(
  chosen,
  (name) => {
    showPerson.value = false
    // moving on is when a row that was leaving finally goes
    shown.value = shown.value.filter((row) => !row.leaving || row.name === name)
    if (!name) return
    // Opening a chat changes nothing, for anybody: not the badge, not the blue
    // ticks. Looking is not reading.
    person.fetch()
  },
  { immediate: true },
)

// What was new when the conversation was opened: the cutoff the line in the
// thread is drawn at, taken once and held while it stays open — reading it, or
// answering, must not pull the line from under the messages it points at. And
// the line shows once there has been something unread while it was open, and
// stays: a message arriving as you read draws it, marking it read greys it.
const opened = ref({ name: '', ready: false, since: null, sawUnread: false })
watch(
  () => [chosen.value, person.data?.name, person.data?.conversation_unread],
  () => {
    const name = chosen.value
    if (opened.value.name !== name) {
      opened.value = { name, ready: false, since: null, sawUnread: false }
    }
    const data = person.data?.name === name ? person.data : null
    if (!data) return
    if (!opened.value.ready) {
      opened.value = {
        name,
        ready: true,
        since: data.conversation_seen_until || null,
        sawUnread: Boolean(data.conversation_unread),
      }
    } else if (data.conversation_unread && !opened.value.sawUnread) {
      opened.value = { ...opened.value, sawUnread: true }
    }
  },
  { immediate: true },
)

const receipts = readReceipts()

// For the line in the thread: where new begins, whether it is still unread, and
// whether the customer is told when it is read.
const newMessages = computed(() =>
  opened.value.ready && opened.value.sawUnread
    ? {
        since: opened.value.since,
        unread: Boolean(current.value.conversation_unread),
        receipts: receipts.value,
      }
    : null,
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
watch([view, onlyUnread], () => {
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
  return Promise.all([
    people.reload(),
    unread.fetch(),
    counts.reload(),
    chosen.value && person.fetch(),
  ])
}

// the button, and the list pulled down on a phone: the list as it is, without
// the row that was on its way out
function refreshList() {
  shown.value = shown.value.filter((row) => !row.leaving)
  return reload()
}

// a message arriving reorders this list, so it has to be told — and so does a
// reply sent from the composer, which is also the moment it was read
const refresh = debounce(() => reload(), 400)

// on a phone the Chat tab, tapped while a conversation is open, goes back to
// the list of them (utils/schedaAttiva.js), as a phone's own apps do
let smettiScheda = () => {}
onMounted(() => {
  smettiScheda = alToccoDellaScheda(() => {
    if (!isMobileView.value || !chosen.value) return false
    back()
    return true
  })
})
onBeforeUnmount(() => smettiScheda())

// …and a conversation read, answered (from the phone too), handled or marked
// unread by somebody else, or on another device: the server says so
// (`crm_conversation`), and the row and its count follow
onMounted(() => {
  $socket.on('crm_sms_message', refresh)
  $socket.on('whatsapp_message', refresh)
  $socket.on('crm_conversation', refresh)
  window.addEventListener('crm:conversation-read', refresh)
})

onBeforeUnmount(() => {
  $socket.off('crm_sms_message', refresh)
  $socket.off('whatsapp_message', refresh)
  $socket.off('crm_conversation', refresh)
  window.removeEventListener('crm:conversation-read', refresh)
})
</script>
